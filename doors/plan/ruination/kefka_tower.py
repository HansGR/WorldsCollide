"""Kefka's Tower lane randomizer (-rkt).

Partition the KT rooms into three lanes under cheap necessary
invariants, walk each lane (pre-unlocked platforms, forced crossings),
then verify the joint
three-party system over the shared monotonic keychain: every room
reachable AND every reachable situation can still finish. Returns
[[door pairs], [trap->pit pairs]] with the platform pseudo-ids stripped,
or None (callers keep the vanilla KT layout).

The gated crossings (which rooms, which keys, one- or two-way), the
forced pairs, the platform ids and the key rooms are all DERIVED from
room_data + forced_connections by derive_tower_tables(), using the walk's
own element classifier - edit the room data, never a table here.

Each lane walk carries a generous attempt budget (KT_LANE_BUDGET; healthy
lane walks need well under 200 attempts). A rare partition (~0.3-1% of
rolls) passes the cheap invariants but presents an enormous backtracking
tree; unbounded, such a lane could search for hours (observed: 37 min in
a 1000-seed sweep). The budget aborts it in under a second and a fresh
partition is drawn. This removes no layout from the reachable
distribution: partitions re-draw across KT_MAX_SPLITS tries and the
walk's exploration order is random, so every legal layout keeps a
nonzero find-probability within budget.
"""

from data.rooms import room_data, forced_connections
from doors.model import WorldModel, DOOR, TRAP, PIT
from doors.plan.pools import load_pool
from doors.plan.walk import run, WalkFailed, WalkBudgetExhausted

KT_ENTRIES = ['KTA1', 'KTB1', 'KTC1']
KT_FINALS = ['KTA-final', 'KTB-final', 'KTC-final']
KT_BOSSES = ['KTB4', 'KTB10', 'KTC7', 'KTC12']


def tower_rooms(rooms=None):
    """The vanilla tower rooms, in room_data order. The ruination
    composites share the KTA/KTB/KTC codes but carry a -ruin suffix."""
    rooms = room_data if rooms is None else rooms
    return [r for r in rooms if r.startswith('KT') and not r.endswith('-ruin')]


def derive_tower_tables(rooms=None, forcing=None):
    """Derive the tower's gated crossings from the room data - the ONLY
    place they are defined - so the lane walk and verify() cannot disagree.

    A gated crossing is a pair of LOCKED elements in tower rooms joined by
    a forced connection (switch platform 1565->1566, broken stairs
    1567->1568). Its direction comes from the same element classifier the
    walk uses: a door-range pair is two-way once unlocked, a trap->pit
    pair is one-way. The keys a crossing needs are its two locks' key
    tuples; the rooms granting them are the tower rooms whose key slot
    holds them.

    Returns (crossings, forced, platform_ids, key_rooms, keys):
      crossings    [(room_a, room_b, keys_needed, two_way)] in room order
      forced       {element: [partner]} for the lane walk's forcing
      platform_ids every gated element (stripped from written exits)
      key_rooms    {room: keys granted by visiting it}
      keys         sorted keys the crossings need (pre-applied in the walk)
    Raises ValueError on data the lane randomizer cannot model."""
    rooms = room_data if rooms is None else rooms
    forcing = forced_connections if forcing is None else forcing
    kt = tower_rooms(rooms)
    owner, need = {}, {}
    for r in kt:
        spec = rooms[r]
        locks = spec[4] if len(spec) == 6 else {}
        for key_tuple, items in locks.items():
            keys = key_tuple if isinstance(key_tuple, tuple) else (key_tuple,)
            for e in items:
                if isinstance(e, int):
                    owner[e] = r
                    need[e] = frozenset(keys)
    kind = WorldModel._element_kind
    crossings, forced, paired = [], {}, set()
    for e in owner:                              # room order, lock order
        if e not in forcing:
            continue
        p = forcing[e][0]
        if p not in owner:
            raise ValueError(f'KT gated element {e} is forced to {p}, '
                             f'which is not a locked tower element')
        if (kind(e), kind(p)) == (DOOR, DOOR):
            two_way = True
        elif (kind(e), kind(p)) == (TRAP, PIT):
            two_way = False
        else:
            raise ValueError(f'KT crossing {e}->{p} pairs a {kind(e)} '
                             f'with a {kind(p)}')
        forced[e] = list(forcing[e])
        crossings.append((owner[e], owner[p],
                          tuple(sorted(need[e] | need[p])), two_way))
        paired.update((e, p))
    unpaired = set(owner) - paired
    if unpaired:
        raise ValueError(f'locked KT elements with no forced partner: '
                         f'{sorted(unpaired)}')
    key_rooms = {}
    for r in kt:
        spec = rooms[r]
        if len(spec) == 6 and spec[3]:
            key_rooms[r] = tuple(spec[3])
    keys = sorted({k for _, _, ks, _ in crossings for k in ks})
    granted = {k for ks in key_rooms.values() for k in ks}
    missing = [k for k in keys if k not in granted]
    if missing:
        raise ValueError(f'KT crossing keys granted by no tower room: {missing}')
    return crossings, forced, set(owner), key_rooms, keys


# Derived once from room_data (static tables; no RNG).
KT_CROSSINGS, KT_FORCED, KT_PLATFORM_IDS, KT_KEY_ROOM, KT_KEYS = \
    derive_tower_tables()

KT_MAX_SPLITS = 400
KT_LANE_BUDGET = 20000    # per-lane walk attempts (see module docstring)


def randomize_kefka_tower(rng):
    KT = tower_rooms()

    doors_of = {r: list(room_data[r][0]) for r in KT}
    traps_of = {r: list(room_data[r][1]) for r in KT}
    pits_of = {r: list(room_data[r][2]) for r in KT}
    room_of = {}
    for r in KT:
        for e in doors_of[r] + traps_of[r] + pits_of[r]:
            room_of[e] = r

    def split_lanes():
        lanes = [{KT_ENTRIES[i]} for i in range(3)]
        fperm = KT_FINALS[:]
        rng.shuffle(fperm)
        for i in range(3):
            lanes[i].add(fperm[i])
        placed = set(KT_ENTRIES) | set(KT_FINALS)
        glued = {r for a, b, _, _ in KT_CROSSINGS for r in (a, b)}
        units = [[a, b] for a, b, _, _ in KT_CROSSINGS]
        units += [[r] for r in KT if r not in placed and r not in glued]
        rng.shuffle(units)
        for u in units:
            rng.choice(lanes).update(u)
        for lane in lanes:
            if (sum(len(traps_of[r]) for r in lane)
                    != sum(len(pits_of[r]) for r in lane)):
                return None
            if sum(len(doors_of[r]) for r in lane) % 2 != 0:
                return None
            if sum(1 for r in lane if r in KT_BOSSES) > 2:
                return None
        return lanes

    def connect_lane(lane):
        """Walk one lane; returns (door_pairs, trap_pits) with the platform
        ids stripped, or None (budget exhaustion included - the caller
        just draws a fresh partition). The platforms are pre-unlocked so
        the walk can rely on the crossings; key timing is verify()'s job."""
        specs = load_pool(sorted(lane))
        try:
            world = run(specs, KT_FORCED, rng=rng, start_rule='most_exits',
                        budget_limit=KT_LANE_BUDGET, attempts=1,
                        keys=tuple(KT_KEYS), home_rule=None)
        except (WalkFailed, WalkBudgetExhausted):
            return None
        dp = [list(m) for m in world.door_pairs
              if m[0] not in KT_PLATFORM_IDS and m[1] not in KT_PLATFORM_IDS]
        tp = [list(m) for m in world.oneways
              if m[0] not in KT_PLATFORM_IDS and m[1] not in KT_PLATFORM_IDS]
        return dp, tp

    def verify(door_pairs, trap_pits, lane_of):
        """Joint (roomA, roomB, roomC, keychain) state-space check: no
        orphan rooms, and every reachable state can still herd all three
        parties onto their endings."""
        KEY_BIT = {k: 1 << i for i, k in enumerate(KT_KEYS)}

        def mask(keys):
            m = 0
            for k in keys:
                m |= KEY_BIT.get(k, 0)
            return m

        adj = {r: [] for r in KT}
        for d1, d2 in door_pairs:
            adj[room_of[d1]].append((room_of[d2], None))
            adj[room_of[d2]].append((room_of[d1], None))
        for t, p in trap_pits:
            adj[room_of[t]].append((room_of[p], None))
        for a, b, keys, two_way in KT_CROSSINGS:
            adj[a].append((b, mask(keys)))
            if two_way:
                adj[b].append((a, mask(keys)))
        grant = {room: mask(keys) for room, keys in KT_KEY_ROOM.items()}
        grant = {room: g for room, g in grant.items() if g}

        entry = tuple(KT_ENTRIES)
        ending = [None, None, None]
        for f in KT_FINALS:
            ending[lane_of[f]] = f
        ending = tuple(ending)

        def successors(state):
            a, b, c, K = state
            pos = (a, b, c)
            for j in range(3):
                for dest, need in adj[pos[j]]:
                    if need is None or (K & need) == need:
                        nxt = list(pos)
                        nxt[j] = dest
                        yield (nxt[0], nxt[1], nxt[2], K)
                g = grant.get(pos[j])
                if g and (K & g) != g:
                    yield (a, b, c, K | g)

        start = (entry[0], entry[1], entry[2], 0)
        forward = {start}
        stack = [start]
        while stack:
            s = stack.pop()
            for ns in successors(s):
                if ns not in forward:
                    forward.add(ns)
                    stack.append(ns)

        visited = set()
        for a, b, c, _K in forward:
            visited.update((a, b, c))
        if visited != set(KT):
            return False

        rev = {}
        for s in forward:
            for ns in successors(s):
                if ns in forward:
                    rev.setdefault(ns, []).append(s)
        goal = [s for s in forward if (s[0], s[1], s[2]) == ending]
        if not goal:
            return False
        can_finish = set(goal)
        stack = list(goal)
        while stack:
            s = stack.pop()
            for pre in rev.get(s, ()):
                if pre not in can_finish:
                    can_finish.add(pre)
                    stack.append(pre)
        return forward <= can_finish

    for _ in range(KT_MAX_SPLITS):
        split = None
        guard = 0
        while split is None and guard < 5000:
            split = split_lanes()
            guard += 1
        if split is None:
            continue
        lane_of = {r: i for i, lane in enumerate(split) for r in lane}
        door_pairs, trap_pits = [], []
        ok = True
        for lane in split:
            res = connect_lane(lane)
            if res is None:
                ok = False
                break
            door_pairs += res[0]
            trap_pits += res[1]
        if ok and verify(door_pairs, trap_pits, lane_of):
            return [door_pairs, trap_pits]
    return None
