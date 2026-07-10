"""Kefka's Tower lane randomizer (-rkt; rewrite Stage D milestone 5).

Port of legacy _randomize_kefka_tower: partition the KT rooms into three
lanes under cheap necessary invariants, walk each lane with the v2 walk
(pre-unlocked platforms, forced crossings), then verify the joint
three-party system over the shared monotonic keychain: every room
reachable AND every reachable situation can still finish. Returns
[[door pairs], [trap->pit pairs]] with the platform pseudo-ids stripped,
or None (callers keep the vanilla KT layout).

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

from data.rooms import room_data
from doors.plan.pools import load_pool
from doors.plan.walk import run, WalkFailed, WalkBudgetExhausted

KT_ENTRIES = ['KTa1', 'KTb1', 'KTc1']
KT_FINALS = ['KTa-final', 'KTb-final', 'KTc-final']
KT_BOSSES = ['KTb4', 'KTb10', 'KTc7', 'KTc12']
# Rooms joined by a key-gated forced crossing share a lane; the crossing
# is a one-way edge a -> b, gated by the named switch key.
KT_GATED = [('KTa5a', 'KTa5b', 'KT1'), ('KTa8a', 'KTa8b', 'KT2')]
KT_FORCED = {1565: [1566], 1567: [1568]}
KT_PLATFORM_IDS = {1565, 1566, 1567, 1568}
KT_KEY_ROOM = {'KTb8': 'KT1', 'KTc10': 'KT2'}
KT_MAX_SPLITS = 400
KT_LANE_BUDGET = 20000    # per-lane walk attempts (see module docstring)


def randomize_kefka_tower(rng):
    KT = [r for r in room_data if isinstance(r, str) and r.startswith('KT')]

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
        glued = {r for a, b, _ in KT_GATED for r in (a, b)}
        units = [[a, b] for a, b, _ in KT_GATED]
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
                        keys=('KT1', 'KT2'))
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
        KEY_BIT = {'KT1': 1, 'KT2': 2}
        adj = {r: [] for r in KT}
        for d1, d2 in door_pairs:
            adj[room_of[d1]].append((room_of[d2], None))
            adj[room_of[d2]].append((room_of[d1], None))
        for t, p in trap_pits:
            adj[room_of[t]].append((room_of[p], None))
        for a, b, k in KT_GATED:
            adj[a].append((b, KEY_BIT[k]))
        grant = {room: KEY_BIT[key] for room, key in KT_KEY_ROOM.items()}

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
                    if need is None or (K & need):
                        nxt = list(pos)
                        nxt[j] = dest
                        yield (nxt[0], nxt[1], nxt[2], K)
                g = grant.get(pos[j])
                if g and not (K & g):
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
