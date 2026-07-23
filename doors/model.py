"""World model for the door-rando planners.

The mutable state a planner explores: rooms grouped into mutually-
reachable CLUSTERS (a rollback union-find), one-way reachability edges
between clusters, per-room unmatched elements, a keychain, and the
growing matching. A small set of operations mutates it - connect_door,
connect_oneway, apply_key, the lock-aware dead-end helpers, and add_room
(dynamic pool growth for the ruination planner) - and every effect is
journaled, so backtracking is checkpoint()/rollback(mark) rather than
copying the world per attempt.

Design notes:
- Room handles are indices into the pool's room list; clusters are
  union-find roots. Merged-cluster identity never appears in ids.
- The union-find uses union-by-size WITHOUT path compression so unions are
  cheaply reversible; depth stays O(log n) and pools are <= ~300 rooms.
- Two-way door connections merge their endpoint clusters immediately, and
  any one-way cycle closed by a connection merges every cluster on it, so
  the invariant "the cluster graph is a DAG" always holds.
- Element containers are lists and all iteration is insertion-ordered, so
  candidate collection feeds the RNG deterministically (no set-order traps).
- Locks: apply_key unlocks any lock whose full key tuple is on the
  keychain; released keys join the room's keys, released exits go live
  AND into initially_locked_exits (usable by the planner as sources but
  never targeted - ARCHIVE "Key/Lock Softlock Analysis").
"""

DOOR, TRAP, PIT = 'doors', 'traps', 'pits'


class WorldModel:
    def __init__(self, rooms, protected=None):
        """rooms: {room_id: spec} where spec has element lists under
        'doors'/'traps'/'pits', a 'keys' list, and a 'locks' dict mapping a
        key tuple to a list of locked items (elements or key strings) -
        the same shape data.rooms.room_data provides via the pool loader.
        """
        self.room_ids = list(rooms)
        self._index = {rid: i for i, rid in enumerate(self.room_ids)}
        n = len(self.room_ids)

        # Union-find (no path compression: rollback-safe).
        self._parent = list(range(n))
        self._size = [1] * n
        # Mutable per-room element state (lists: deterministic iteration).
        self.elements = []       # per room: {DOOR: [...], TRAP: [...], PIT: [...]}
        self.keys = []           # per room: [key, ...]
        self.locks = []          # per room: {key_tuple: [items]}
        self._owner = {}         # element id -> room handle
        for i, rid in enumerate(self.room_ids):
            spec = rooms[rid]
            self.elements.append({
                DOOR: list(spec.get('doors', ())),
                TRAP: list(spec.get('traps', ())),
                PIT: list(spec.get('pits', ())),
            })
            self.keys.append(list(spec.get('keys', ())))
            self.locks.append({tuple(k) if isinstance(k, tuple) else (k,): list(v)
                               for k, v in spec.get('locks', {}).items()})
            for kind in (DOOR, TRAP, PIT):
                for e in self.elements[i][kind]:
                    if e in self._owner:
                        raise ValueError(f'element {e!r} in two rooms: '
                                         f'{self.room_ids[self._owner[e]]!r} and {rid!r}')
                    self._owner[e] = i
            for items in self.locks[i].values():
                for item in items:
                    if not isinstance(item, str):
                        self._owner.setdefault(item, i)

        self.edges = []               # one-way (h1, h2) room-handle pairs
        self.keychain = set()         # membership only; never iterated for RNG
        self.door_pairs = []          # [(d1, d2)]
        self.oneways = []             # [(trap, pit)]
        self.protected = set(protected or ())
        self.initially_locked_exits = set()
        self._journal = []

    # ------------------------------------------------------------------
    # Union-find

    def find(self, h):
        while self._parent[h] != h:
            h = self._parent[h]
        return h

    def cluster_of_room(self, room_id):
        return self.find(self._index[room_id])

    def _union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if self._size[ra] < self._size[rb]:
            ra, rb = rb, ra
        self._journal.append(('union', rb, self._size[ra]))
        self._parent[rb] = ra
        self._size[ra] += self._size[rb]
        return ra

    def cluster_rooms(self, c):
        """Room handles in cluster c (linear scan; pools are small)."""
        c = self.find(c)
        return [h for h in range(len(self.room_ids)) if self.find(h) == c]

    def clusters(self):
        """Canonical roots, in room order (deterministic)."""
        seen, out = set(), []
        for h in range(len(self.room_ids)):
            r = self.find(h)
            if r not in seen:
                seen.add(r)
                out.append(r)
        return out

    # ------------------------------------------------------------------
    # Journal

    def checkpoint(self):
        return len(self._journal)

    def rollback(self, mark):
        while len(self._journal) > mark:
            entry = self._journal.pop()
            op = entry[0]
            if op == 'union':
                child, old_size = entry[1], entry[2]
                root = self._parent[child]
                self._parent[child] = child
                self._size[root] = old_size
            elif op == 'rm_elem':
                _, h, kind, elem, pos = entry
                self.elements[h][kind].insert(pos, elem)
            elif op == 'add_elem':
                _, h, kind, elem = entry
                assert self.elements[h][kind].pop() == elem
            elif op == 'edge':
                self.edges.pop()
            elif op == 'pair':
                self.door_pairs.pop()
            elif op == 'oneway':
                self.oneways.pop()
            elif op == 'key_add':
                self.keychain.discard(entry[1])
            elif op == 'rm_key':
                _, h, key, pos = entry
                self.keys[h].insert(pos, key)
            elif op == 'add_key':
                _, h, key = entry
                assert self.keys[h].pop() == key
            elif op == 'unlock':
                _, h, key_tuple, items = entry
                self.locks[h][key_tuple] = items
            elif op == 'rm_locked':
                _, h, key_tuple, elem, pos = entry
                self.locks[h][key_tuple].insert(pos, elem)
            elif op == 'parked_key':
                _, h, key_tuple = entry
                self.locks[h][key_tuple].pop()
            elif op == 'ile_add':
                self.initially_locked_exits.discard(entry[1])
            elif op == 'add_room':
                self._rollback_add_room(entry[1])
            else:                                    # pragma: no cover
                raise AssertionError(f'unknown journal op {op!r}')

    # ------------------------------------------------------------------
    # The three mutating operations

    def connect_door(self, d1, d2):
        """Pair two-way door sides d1 and d2 (both become matched)."""
        h1, h2 = self._owner[d1], self._owner[d2]
        self._remove_element(h1, DOOR, d1)
        self._remove_element(h2, DOOR, d2)
        self.door_pairs.append((d1, d2))
        self._journal.append(('pair',))
        # Mutual reachability: merge the endpoint clusters, then any one-way
        # cycles this closes.
        c = self._union(self.find(h1), self.find(h2))
        self._absorb_cycles(c)
        return self.find(c)

    def connect_oneway(self, trap, pit):
        """Send one-way exit `trap` to landing `pit`."""
        h1, h2 = self._owner[trap], self._owner[pit]
        self._remove_element(h1, TRAP, trap)
        self._remove_element(h2, PIT, pit)
        self.oneways.append((trap, pit))
        self._journal.append(('oneway',))
        self.edges.append((h1, h2))
        self._journal.append(('edge',))
        c1, c2 = self.find(h1), self.find(h2)
        if c1 != c2 and self._reaches(c2, c1):
            # The new edge closes a cycle: merge every cluster on it.
            self._merge_cycle(c1, c2)
        return self.find(c1)

    def connect_door_via_lock(self, live_door, locked_door):
        """Pair a live door with a door still inside a lock list.

        Used by dead-end attachment (which runs BEFORE the walk): the dead
        end is physically joined through the locked door, so its cluster
        merges, and the pairing is recorded, but the locked door never
        becomes a live element.
        where da is in Ra.locked('doors')."""
        h1 = self._owner[live_door]
        h2, key_tuple, pos = self._find_locked(locked_door)
        self._remove_element(h1, DOOR, live_door)
        self.locks[h2][key_tuple].pop(pos)
        self._journal.append(('rm_locked', h2, key_tuple, locked_door, pos))
        self.door_pairs.append((live_door, locked_door))
        self._journal.append(('pair',))
        c = self._union(self.find(h1), self.find(h2))
        return self._absorb_cycles(c)

    def park_key_behind_lock(self, key_room, key, lock_room, key_tuple):
        """Move a key from a room's live keys into a lock's item list
        (dead-end keys become reachable only once the lock opens)."""
        h1, h2 = self._index[key_room], self._index[lock_room]
        pos = self.keys[h1].index(key)
        self.keys[h1].pop(pos)
        self._journal.append(('rm_key', h1, key, pos))
        self.locks[h2][key_tuple].append(key)
        self._journal.append(('parked_key', h2, key_tuple))

    def _find_locked(self, element):
        for h in range(len(self.room_ids)):
            for key_tuple, items in self.locks[h].items():
                if element in items:
                    return h, key_tuple, items.index(element)
        raise KeyError(f'{element!r} is not a locked element')

    def locked_doors(self, c):
        """Locked doors across cluster c with their key tuples: [(door, kt)]."""
        out = []
        for h in self.cluster_rooms(c):
            for key_tuple, items in self.locks[h].items():
                for item in items:
                    if not isinstance(item, str) and self._element_kind(item) == DOOR:
                        out.append((item, key_tuple))
        return out

    def apply_key(self, key):
        """Add `key` to the keychain and open everything it (now) unlocks."""
        if key not in self.keychain:
            self.keychain.add(key)
            self._journal.append(('key_add', key))
        # Remove the key from any room still holding it.
        for h in range(len(self.room_ids)):
            if key in self.keys[h]:
                pos = self.keys[h].index(key)
                self.keys[h].pop(pos)
                self._journal.append(('rm_key', h, key, pos))
        # Open locks whose full key set is on the keychain; released keys may
        # cascade.
        released_keys = []
        for h in range(len(self.room_ids)):
            released_keys.extend(self._assess_locks(h))
        return released_keys

    def _assess_locks(self, h):
        """Open every lock in room h whose complete key set is already on the
        keychain; returns the key strings released. Released elements go live
        (doors/traps also into initially_locked_exits); released keys join the
        room's key list but are NOT applied - they apply
        when the room is connected."""
        released_keys = []
        for key_tuple in list(self.locks[h]):
            if key_tuple not in self.locks[h]:
                continue
            if set(key_tuple).issubset(self.keychain):
                items = self.locks[h].pop(key_tuple)
                self._journal.append(('unlock', h, key_tuple, items))
                for item in items:
                    if isinstance(item, str):
                        self.keys[h].append(item)
                        self._journal.append(('add_key', h, item))
                        released_keys.append(item)
                    else:
                        kind = self._element_kind(item)
                        self.elements[h][kind].append(item)
                        self._journal.append(('add_elem', h, kind, item))
                        self._owner[item] = h
                        if kind in (DOOR, TRAP):
                            if item not in self.initially_locked_exits:
                                self.initially_locked_exits.add(item)
                                self._journal.append(('ile_add', item))
        return released_keys

    # ------------------------------------------------------------------
    # Dynamic pool growth (ruination: areas arrive as rewards are found)

    def add_room(self, room_id, spec):
        """Add a room to the pool mid-plan (journaled; rollback removes it).

        The room's locks are assessed against the CURRENT keychain: a room can
        arrive after its lock's key was already applied (character areas are
        distributed only when the character is recruited, but the character
        key is applied first - the Mog->lw1->Lone Wolf bug class). Released
        keys stay in the room's key list until it is connected, exactly as
        apply_key leaves them for unvisited rooms.

        Returns the new room's handle (its own cluster root until connected).
        """
        if room_id in self._index:
            raise ValueError(f'room {room_id!r} already in pool')
        h = len(self.room_ids)
        self.room_ids.append(room_id)
        self._index[room_id] = h
        self._parent.append(h)
        self._size.append(1)
        self.elements.append({
            DOOR: list(spec.get('doors', ())),
            TRAP: list(spec.get('traps', ())),
            PIT: list(spec.get('pits', ())),
        })
        self.keys.append(list(spec.get('keys', ())))
        self.locks.append({tuple(k) if isinstance(k, tuple) else (k,): list(v)
                           for k, v in spec.get('locks', {}).items()})
        for kind in (DOOR, TRAP, PIT):
            for e in self.elements[h][kind]:
                if e in self._owner:
                    self._rollback_add_room(h)
                    raise ValueError(f'element {e!r} in two rooms: '
                                     f'{self.room_ids[self._owner[e]]!r} and {room_id!r}')
                self._owner[e] = h
        for items in self.locks[h].values():
            for item in items:
                if not isinstance(item, str):
                    self._owner.setdefault(item, h)
        self._journal.append(('add_room', h))
        self._assess_locks(h)
        return h

    def add_element(self, room_id, kind, elem):
        """Inject a live element into an existing room (journaled).

        Ruination adds conditional exits mid-plan: LeteRiver3 gives the hub
        a return pit, an Ebot's Rock character reward grows a forced trap
        to Thamasa. The element must be globally new."""
        if elem in self._owner:
            raise ValueError(f'element {elem!r} already owned by '
                             f'{self.room_ids[self._owner[elem]]!r}')
        h = self._index[room_id]
        self.elements[h][kind].append(elem)
        self._journal.append(('add_elem', h, kind, elem))
        self._owner[elem] = h
        return h

    def _rollback_add_room(self, h):
        """Remove the most recently added room (h == len(room_ids) - 1)."""
        rid = self.room_ids.pop()
        del self._index[rid]
        self._parent.pop()
        self._size.pop()
        elems = self.elements.pop()
        self.keys.pop()
        locks = self.locks.pop()
        for kind in (DOOR, TRAP, PIT):
            for e in elems[kind]:
                if self._owner.get(e) == h:
                    del self._owner[e]
        for items in locks.values():
            for item in items:
                if not isinstance(item, str) and self._owner.get(item) == h:
                    del self._owner[item]

    # ------------------------------------------------------------------
    # Reachability (all BFS, dedup, deterministic order)

    def _neighbors(self, forward):
        """Canonical cluster adjacency from the edge list."""
        adj = {}
        for h1, h2 in self.edges:
            a, b = self.find(h1), self.find(h2)
            if a == b:
                continue
            if not forward:
                a, b = b, a
            adj.setdefault(a, []).append(b)
        return adj

    def _bfs(self, start, forward):
        adj = self._neighbors(forward)
        seen = {start}
        order = []
        queue = [start]
        qi = 0
        while qi < len(queue):
            cur = queue[qi]
            qi += 1
            for nxt in adj.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    order.append(nxt)
                    queue.append(nxt)
        return order

    def downstream(self, c):
        """Classes reachable from c via one-way edges (c excluded)."""
        return self._bfs(self.find(c), True)

    def upstream(self, c):
        """Classes that reach c via one-way edges (c excluded)."""
        return self._bfs(self.find(c), False)

    def _reaches(self, src, dst):
        src, dst = self.find(src), self.find(dst)
        return src == dst or dst in self._bfs(src, True)

    def _merge_cycle(self, c1, c2):
        """Merge every cluster on a cycle through the (c1 -> c2) edge."""
        fwd = set(self._bfs(c2, True)) | {c2}     # reachable from c2
        back = set(self._bfs(c1, False)) | {c1}   # can reach c1
        c = self._union(c1, c2)
        for x in fwd & back:
            c = self._union(c, x)
        self._absorb_cycles(c)

    def _absorb_cycles(self, c):
        """Merge any remaining cycles through cluster c until it is DAG-clean."""
        while True:
            c = self.find(c)
            down = set(self._bfs(c, True))
            up = set(self._bfs(c, False))
            both = down & up
            if not both:
                return c
            for x in both:
                c = self._union(c, x)

    # ------------------------------------------------------------------
    # Views for planners / pruners

    def cluster_elements(self, c, kind, include_locked=False, unprotected_only=False):
        """Elements of `kind` across all rooms of cluster c, room order."""
        out = []
        for h in self.cluster_rooms(c):
            out.extend(self.elements[h][kind])
            if include_locked:
                for items in self.locks[h].values():
                    for item in items:
                        if not isinstance(item, str) and self._element_kind(item) == kind:
                            out.append(item)
        if unprotected_only:
            out = [e for e in out if e not in self.protected]
        return out

    def cluster_keys(self, c):
        out = []
        for h in self.cluster_rooms(c):
            out.extend(self.keys[h])
        return out

    def counts(self, c, include_locked=True):
        """(doors, traps, pits) counts for cluster c, excluding protected -
        excluding protected doors."""
        return tuple(
            len(self.cluster_elements(c, kind, include_locked=include_locked,
                                    unprotected_only=True))
            for kind in (DOOR, TRAP, PIT))

    def owner_room(self, element):
        return self.room_ids[self._owner[element]]

    def live_kind(self, element):
        """Kind of a LIVE element by list membership in its owner room -
        the authoritative answer where id ranges lie (door-as-trap ids:
        a door-range id sitting in a trap list is a one-way exit)."""
        h = self._owner[element]
        for kind in (DOOR, TRAP, PIT):
            if element in self.elements[h][kind]:
                return kind
        raise KeyError(f'{element!r} is not live')

    def owner_cluster(self, element):
        return self.find(self._owner[element])

    def total_unmatched(self):
        return sum(len(self.elements[h][k]) for h in range(len(self.room_ids))
                   for k in (DOOR, TRAP, PIT))

    def cluster_name(self, c):
        """Display name for logs: ids of member rooms."""
        return '+'.join(str(self.room_ids[h]) for h in self.cluster_rooms(c))

    # ------------------------------------------------------------------
    # Internals

    def _remove_element(self, h, kind, elem):
        pos = self.elements[h][kind].index(elem)
        self.elements[h][kind].pop(pos)
        self._journal.append(('rm_elem', h, kind, elem, pos))

    @staticmethod
    def _element_kind(element):
        """Kind of a locked element id (numeric id ranges -- the
        authoritative range table is doors/ids.py; the arithmetic is
        confined to this one function)."""
        e = element
        if isinstance(e, str):
            return TRAP                      # '2035a'-style trap variants
        if e < 2000 or 4000 <= e < 6000 or e >= 10000:
            return DOOR
        if e < 3000:
            return TRAP
        if e < 4000 or 6000 <= e < 8000:
            return PIT
        raise ValueError(f'unclassifiable element {element!r}')

    def snapshot(self):
        """Full-state fingerprint for tests: rollback must restore this."""
        return (tuple(self._parent), tuple(self._size),
                tuple(tuple((k, tuple(v)) for k, v in e.items()) for e in self.elements),
                tuple(tuple(k) for k in self.keys),
                tuple(tuple(sorted((k, tuple(v)) for k, v in l.items())) for l in self.locks),
                tuple(self.edges), frozenset(self.keychain),
                tuple(self.door_pairs), tuple(self.oneways),
                frozenset(self.initially_locked_exits))
