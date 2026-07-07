"""World model for the door-rando planners (rewrite Stage B).

The mutable state a planner explores: rooms grouped into mutually-reachable
CLASSES (a rollback union-find), one-way reachability edges between classes,
per-room unmatched elements, a keychain, and the growing matching. Exactly
three operations mutate it - connect_door, connect_oneway, apply_key - and
every effect is journaled, so backtracking is checkpoint()/rollback(mark)
instead of the legacy deepcopy-per-attempt (plan flaw F4).

Design notes:
- Room handles are indices into the pool's room list; classes are union-find
  roots. Merged-class identity never appears in ids (F2: no compound ids).
  Display names come from doors.atlas.room_names when needed for logs.
- The union-find uses union-by-size WITHOUT path compression so unions are
  cheaply reversible; depth stays O(log n) and pools are <= ~300 rooms.
- Two-way door connections merge their endpoint classes immediately, and any
  one-way cycle closed by a connection merges every class on it (incremental
  SCC maintenance). The legacy compress_loop merged only the first loop it
  found, occasionally leaving residual 2-cycles; here the invariant "the
  class graph is a DAG" always holds.
- Element containers are lists and all iteration is insertion-ordered, so
  candidate collection feeds the RNG deterministically (no set-order traps).
- Locks follow legacy semantics: apply_key unlocks any lock whose full key
  tuple is on the keychain; released keys join the room's keys, released
  exits go live AND into initially_locked_exits (usable by the planner as
  sources but never targeted - ARCHIVE "Key/Lock Softlock Analysis").
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

    def class_of_room(self, room_id):
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

    def class_rooms(self, c):
        """Room handles in class c (linear scan; pools are small)."""
        c = self.find(c)
        return [h for h in range(len(self.room_ids)) if self.find(h) == c]

    def classes(self):
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
            elif op == 'ile_add':
                self.initially_locked_exits.discard(entry[1])
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
        # Mutual reachability: merge the endpoint classes, then any one-way
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
            # The new edge closes a cycle: merge every class on it.
            self._merge_cycle(c1, c2)
        return self.find(c1)

    def apply_key(self, key):
        """Add `key` to the keychain and open everything it (now) unlocks."""
        if key not in self.keychain:
            self.keychain.add(key)
            self._journal.append(('key_add', key))
        # Remove the key from any room still holding it (legacy semantics).
        for h in range(len(self.room_ids)):
            if key in self.keys[h]:
                pos = self.keys[h].index(key)
                self.keys[h].pop(pos)
                self._journal.append(('rm_key', h, key, pos))
        # Open locks whose full key set is on the keychain; released keys may
        # cascade.
        released_keys = []
        for h in range(len(self.room_ids)):
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
    # Reachability (all BFS, dedup, deterministic order)

    def _neighbors(self, forward):
        """Canonical class adjacency from the edge list."""
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
        """Merge every class on a cycle through the (c1 -> c2) edge."""
        fwd = set(self._bfs(c2, True)) | {c2}     # reachable from c2
        back = set(self._bfs(c1, False)) | {c1}   # can reach c1
        c = self._union(c1, c2)
        for x in fwd & back:
            c = self._union(c, x)
        self._absorb_cycles(c)

    def _absorb_cycles(self, c):
        """Merge any remaining cycles through class c until it is DAG-clean."""
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

    def class_elements(self, c, kind, include_locked=False, unprotected_only=False):
        """Elements of `kind` across all rooms of class c, room order."""
        out = []
        for h in self.class_rooms(c):
            out.extend(self.elements[h][kind])
            if include_locked:
                for items in self.locks[h].values():
                    for item in items:
                        if not isinstance(item, str) and self._element_kind(item) == kind:
                            out.append(item)
        if unprotected_only:
            out = [e for e in out if e not in self.protected]
        return out

    def class_keys(self, c):
        out = []
        for h in self.class_rooms(c):
            out.extend(self.keys[h])
        return out

    def counts(self, c, include_locked=True):
        """(doors, traps, pits) counts for class c, excluding protected -
        the legacy count_unprotected."""
        return tuple(
            len(self.class_elements(c, kind, include_locked=include_locked,
                                    unprotected_only=True))
            for kind in (DOOR, TRAP, PIT))

    def owner_room(self, element):
        return self.room_ids[self._owner[element]]

    def owner_class(self, element):
        return self.find(self._owner[element])

    def total_unmatched(self):
        return sum(len(self.elements[h][k]) for h in range(len(self.room_ids))
                   for k in (DOOR, TRAP, PIT))

    def class_name(self, c):
        """Display name for logs: atlas names of member rooms."""
        try:
            from doors.atlas.room_names import ROOM_NAMES
            return '+'.join(str(ROOM_NAMES.get(self.room_ids[h], self.room_ids[h]))
                            for h in self.class_rooms(c))
        except ImportError:                          # pragma: no cover
            return '+'.join(str(self.room_ids[h]) for h in self.class_rooms(c))

    # ------------------------------------------------------------------
    # Internals

    def _remove_element(self, h, kind, elem):
        pos = self.elements[h][kind].index(elem)
        self.elements[h][kind].pop(pos)
        self._journal.append(('rm_elem', h, kind, elem, pos))

    @staticmethod
    def _element_kind(element):
        """Kind of a locked element id (legacy id ranges; F1 confines the
        arithmetic to this one function)."""
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
