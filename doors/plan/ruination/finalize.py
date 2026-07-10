"""Branch finalization + map assembly for the ruination planner
(rewrite Stage D milestone 4).

Port of legacy finalize_map (the iterated six-step closer), its rescue
helpers, the full-map assembly tail of generate_map_with_characters, and
_verify_no_character_gated_softlock (BFS instead of networkx).

Legacy nodes are v2 classes throughout: "hub + upstream + downstream"
regions become class sets, compound-id bookkeeping disappears, and the
step-5b/warp-rescue corner cases where legacy could leave a stale merged
id in dead_ends are handled uniformly by trimming non-singleton classes
(a connected room always merges; merged rooms can't serve as dead ends).

Finalize-time connections apply the target class's keys at the model
level only (legacy Network.connect tail): growth is over, so no planner
check bookkeeping happens here.
"""

from data.rooms import room_data
from doors.model import DOOR, TRAP, PIT
from doors.plan.modes import reattach_shared_exits
from doors.plan.ruination.extend import _elements, _count, member_classes
from doors.plan.ruination.growth import RuinPlanError
from event.event_reward import RewardType


# ---------------------------------------------------------------------------
# Region + element helpers (all per class)

def _region(branch):
    """(hub_class, upstream classes, downstream classes)."""
    w = branch.world
    hub = branch.hub_class()
    return hub, w.upstream(hub), w.downstream(hub)


def _collect_region(branch, include_doors=False, exclude_upstream_doors=False):
    """Unprotected traps/pits (and doors) across hub + upstream + downstream
    (legacy collect_network_traps_and_pits)."""
    w = branch.world
    hub, upstream, downstream = _region(branch)
    traps = _elements(w, hub, TRAP)
    pits = _elements(w, hub, PIT)
    doors = _elements(w, hub, DOOR) if include_doors else []
    for c in upstream:
        traps += _elements(w, c, TRAP)
        pits += _elements(w, c, PIT)
        if include_doors and not exclude_upstream_doors:
            doors += _elements(w, c, DOOR)
    for c in downstream:
        traps += _elements(w, c, TRAP)
        pits += _elements(w, c, PIT)
        if include_doors:
            doors += _elements(w, c, DOOR)
    if include_doors:
        return traps, pits, doors
    return traps, pits


def _raw(world, c, kind):
    """Raw live elements of a class (protected included), as legacy room
    lists are."""
    return world.class_elements(c, kind)


def _singleton(world, rid):
    return len(world.class_rooms(world.class_of_room(rid))) == 1


def _is_dead_end_now(branch, rid):
    """Live legacy Network.is_dead_end: unconnected (singleton class, no
    one-way edges), raw counts exactly (1,0,0), no locks."""
    w = branch.world
    c = w.class_of_room(rid)
    if len(w.class_rooms(c)) != 1:
        return False
    if w.downstream(c) or w.upstream(c):
        return False
    h = w._index[rid]
    e = w.elements[h]
    if (len(e[DOOR]), len(e[TRAP]), len(e[PIT])) != (1, 0, 0):
        return False
    return not w.locks[h]


def _trim_dead_ends(branch):
    """Drop dead ends that have been connected (merged classes); legacy
    removes ids that left net.nodes."""
    branch.dead_ends = [d for d in branch.dead_ends
                        if _singleton(branch.world, d)]


def _terminus_separate(branch):
    """True while the terminus hasn't been merged into anything."""
    return branch.terminus is not None and _singleton(branch.world, branch.terminus)


# ---------------------------------------------------------------------------
# Reserve pulls + forced-connection honoring

_EXIT_OWNER = None


def _exit_owner(exit_id):
    """room_data room owning an exit (legacy _exit_to_room_owner)."""
    global _EXIT_OWNER
    if _EXIT_OWNER is None:
        owner = {}
        for rid, data in room_data.items():
            for group in data[:3]:
                if isinstance(group, (list, tuple, set)):
                    for e in group:
                        owner.setdefault(e, rid)
        _EXIT_OWNER = owner
    return _EXIT_OWNER.get(exit_id)


def _pull_from_reserve(planner, branch, reserve_areas, score):
    """Add the best-scoring reserve room to this branch (legacy
    _pull_from_reserve); honors any forced connections it carries."""
    if reserve_areas is None:
        return None
    w = planner.world
    best_score, best_rid, best_rooms = 0, None, None
    for area_name, area_rooms in reserve_areas:
        for rid in area_rooms:
            if rid in w._index:
                continue
            data = room_data.get(rid)
            if data is None:
                continue
            doors = [d for d in data[0] if d not in w.protected]
            traps = [t for t in data[1] if t not in w.protected]
            pits = [p for p in data[2] if p not in w.protected]
            s = score(doors, traps, pits)
            if s > best_score:
                best_score, best_rid, best_rooms = s, rid, area_rooms
    if best_rid is None:
        return None
    planner._add_room_to_branch(branch, best_rid)
    best_rooms.remove(best_rid)
    _honor_forced(planner, branch, reserve_areas)
    return best_rid


def _honor_forced(planner, branch, reserve_areas):
    """Wire every live forced exit; pull absent partner rooms from reserve
    while they are still available (legacy _honor_forced_connections +
    ForceConnections)."""
    w = planner.world
    forcing = planner.config.forcing
    if reserve_areas is not None:
        while True:
            pulled = False
            live = set()
            for rid in branch.rooms:
                h = w._index[rid]
                live.update(w.elements[h][DOOR])
                live.update(w.elements[h][TRAP])
            for d in [e for e in live if e in forcing]:
                for df in forcing[d]:
                    if df in w._owner:
                        continue                     # present; will be wired
                    owner = _exit_owner(df)
                    if owner is None or owner in w._index:
                        continue
                    for _area, area_rooms in reserve_areas:
                        if owner in area_rooms:
                            area_rooms.remove(owner)
                            planner._add_room_to_branch(branch, owner)
                            pulled = True
                            break
            if not pulled:
                break
    planner._force_connections(branch)


# ---------------------------------------------------------------------------
# Finalize-time connect

def _connect(planner, branch, exit_id, target):
    """Model connection + target-class key application to fixpoint (legacy
    Network.connect during finalize; no planner check bookkeeping)."""
    w = planner.world
    if w.live_kind(exit_id) == DOOR:
        w.connect_door(exit_id, target)
    else:
        w.connect_oneway(exit_id, target)
    c = w.class_of_room(w.owner_room(target))
    while True:
        keys = w.class_keys(c)
        if not keys:
            break
        for k in list(keys):
            w.apply_key(k)
        c = w.find(c)


# ---------------------------------------------------------------------------
# Warp-room rescue

def _classify_warp_rooms(branch):
    """(connected, unconnected) warp CLASS representatives, reported by a
    member room id (legacy _classify_branch_warp_rooms; compound string
    matching becomes class membership)."""
    w = branch.world
    hub, upstream, downstream = _region(branch)
    region = {hub} | set(upstream) | set(downstream)
    connected, unconnected = [], []
    seen = set()
    for rid in branch.rooms:
        if rid not in branch.warp_rooms:
            continue
        c = w.class_of_room(rid)
        if c in seen:
            continue
        seen.add(c)
        (connected if c in region else unconnected).append(rid)
    return connected, unconnected


def _connect_orphan_warp(planner, branch, unconnected_warps):
    """Wire one hallway warp room into the branch (legacy
    _connect_orphan_warp_room); dead-end warps defer to step 6."""
    w = planner.world
    rng = planner.rng
    hub, _, downstream = _region(branch)
    rng.shuffle(unconnected_warps)
    targets = [hub] + list(downstream)
    for warp_id in unconnected_warps:
        wc = w.class_of_room(warp_id)
        warp_doors = _elements(w, wc, DOOR)
        warp_pits = _elements(w, wc, PIT)
        if not warp_doors and not warp_pits:
            continue
        if _is_dead_end_now(branch, warp_id):
            continue
        shuffled = list(targets)
        rng.shuffle(shuffled)
        for tc in shuffled:
            if tc == wc:
                continue
            t_doors = _elements(w, tc, DOOR)
            t_traps = _elements(w, tc, TRAP)
            if warp_doors and t_doors:
                _connect(planner, branch, rng.choice(t_doors), rng.choice(warp_doors))
                _trim_dead_ends(branch)
                return True
            if warp_pits and t_traps:
                _connect(planner, branch, rng.choice(t_traps), rng.choice(warp_pits))
                _trim_dead_ends(branch)
                return True
    return False


# ---------------------------------------------------------------------------
# Terminus door injection (pre-check)

def _inject_door_if_needed(planner, branch, reserve_areas):
    """If the terminus is unconnected and the region has traps but NO doors,
    connect a trap into a (pit, door, other-exit) converter room so step 4
    has a door to give the terminus (legacy _inject_door_if_needed...)."""
    w = planner.world
    rng = planner.rng
    if not _terminus_separate(branch):
        return
    hub, upstream, downstream = _region(branch)
    all_doors = _elements(w, hub, DOOR)
    for c in list(upstream) + list(downstream):
        all_doors += _elements(w, c, DOOR)
    all_traps = _elements(w, hub, TRAP)
    for c in downstream:
        all_traps += _elements(w, c, TRAP)
    if all_doors or not all_traps:
        return

    region = {hub} | set(upstream) | set(downstream)
    suitable = None
    for c in member_classes(branch):
        if c in region:
            continue
        pits = _elements(w, c, PIT)
        doors = _elements(w, c, DOOR)
        traps = _elements(w, c, TRAP)
        if len(pits) >= 1 and len(doors) >= 1 and len(doors) + len(traps) >= 2:
            suitable = c
            break
    if suitable is None:
        pulled = _pull_from_reserve(
            planner, branch, reserve_areas,
            lambda doors, traps, pits: (len(pits) >= 1 and len(doors) >= 1
                                        and len(doors) + len(traps) >= 2))
        if pulled is not None:
            suitable = w.class_of_room(pulled)
    if suitable is None:
        raise RuinPlanError(
            f'inject_door: no (pit, door, other-exit) room available for '
            f'terminus {branch.terminus}')

    # Deepest downstream trap preferred (legacy walks paths deep-first).
    selected_trap = None
    if downstream:
        dist = {c: 0 for c in [hub] + list(downstream)}
        edges = [(w.find(h1), w.find(h2)) for h1, h2 in w.edges]
        for _ in range(len(dist)):
            changed = False
            for a, b in edges:
                if a in dist and b in dist and dist[a] + 1 > dist[b]:
                    dist[b] = dist[a] + 1
                    changed = True
            if not changed:
                break
        for depth in range(max(dist.values()), 0, -1):
            candidates = []
            for c in downstream:
                if dist.get(c) == depth:
                    candidates += _elements(w, c, TRAP)
            if candidates:
                selected_trap = rng.choice(candidates)
                break
    if selected_trap is None:
        selected_trap = rng.choice(all_traps)
    _connect(planner, branch, selected_trap,
             rng.choice(_elements(w, suitable, PIT)))


# ---------------------------------------------------------------------------
# The six-step closer

def finalize_branch(planner, branch, reserve_areas=None):
    """Close one branch: consume every remaining exit so the hub compound
    ends with zero loose doors/traps and the terminus is merged in.

    Steps 1-6 run in a loop because connecting things applies keys, and a
    key can release brand-new exits mid-close; any such release restarts
    the whole sequence so the new exits get topology-aware treatment."""
    w = planner.world
    rng = planner.rng
    _honor_forced(planner, branch, reserve_areas)
    _trim_dead_ends(branch)
    _inject_door_if_needed(planner, branch, reserve_areas)

    max_iterations = 10
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        if reserve_areas is not None:
            _honor_forced(planner, branch, reserve_areas)

        hub, upstream, downstream = _region(branch)

        # Warp rescue (skipped on tiny branches).
        region_size = 1 + len(upstream) + len(downstream)
        connected_warps, unconnected_warps = _classify_warp_rooms(branch)
        if (region_size > 3 and len(connected_warps) < 2 and unconnected_warps):
            if _connect_orphan_warp(planner, branch, unconnected_warps):
                continue

        # (1) While region traps outnumber pits, feed a pit-surplus room.
        def region_traps_pits():
            t, p = _collect_region(branch)
            return t, p
        all_traps, all_pits = region_traps_pits()
        while len(all_traps) > len(all_pits):
            hub, upstream, downstream = _region(branch)
            region = {hub} | set(upstream) | set(downstream)
            winner, diff = None, 0
            for c in member_classes(branch):
                if c in region:
                    continue
                free = (_count(w, c, DOOR, free_only=True)
                        + _count(w, c, TRAP, free_only=True))
                if free == 0:
                    continue
                d = _count(w, c, PIT) - _count(w, c, TRAP)
                if d > diff:
                    diff, winner = d, c
            if winner is None:
                pulled = _pull_from_reserve(
                    planner, branch, reserve_areas,
                    lambda doors, traps, pits: len(pits) - len(traps))
                if pulled is not None:
                    winner = w.class_of_room(pulled)
            if winner is None:
                raise RuinPlanError(
                    f'finalize step 1: no pit-surplus room available '
                    f'(traps={all_traps}, pits={all_pits})')
            _connect(planner, branch, rng.choice(all_traps),
                     rng.choice(_elements(w, winner, PIT)))
            all_traps, all_pits = region_traps_pits()

        # (2) Loop every downstream class back to hub/upstream.
        hub, upstream, downstream = _region(branch)
        def build_delta():
            out = []
            for c in downstream:
                doors = _raw(w, c, DOOR)
                entr = len(doors) + len(_raw(w, c, PIT))
                exits = len(doors) + len(_raw(w, c, TRAP))
                out.append((entr - exits, c))
            # Trap-bearing classes sort last (pop()'d first).
            out.sort(key=lambda item: (
                1 if _count(w, item[1], TRAP) > 0 else 0, item[0]))
            return out
        delta = build_delta()
        restart = False
        while delta:
            _, c = delta.pop()
            room_traps = _elements(w, c, TRAP)
            room_doors = _elements(w, c, DOOR)
            if not room_traps and not room_doors:
                continue                             # pit-only: step 3 handles

            up_doors = _elements(w, hub, DOOR)
            up_pits = _elements(w, hub, PIT)
            for uc in upstream:
                up_pits += _elements(w, uc, PIT)
                up_doors += _elements(w, uc, DOOR)

            this_exit = this_conn = None
            if room_traps:
                this_exit = rng.choice(room_traps)
                if up_pits:
                    if _terminus_separate(branch):
                        # Preserve an accessible exit for the terminus.
                        accessible = (_count(w, hub, DOOR) + _count(w, hub, TRAP))
                        for dc in downstream:
                            accessible += (_count(w, dc, DOOR)
                                           + _count(w, dc, TRAP))
                        accessible -= 1              # this trap
                        if accessible <= 0:
                            region = {hub} | set(upstream) | set(downstream)
                            for nc in member_classes(branch):
                                if (nc in region or nc == w.class_of_room(branch.terminus)
                                        or any(w.room_ids[h] in branch.dead_ends
                                               for h in w.class_rooms(nc))):
                                    continue
                                n_pits = _elements(w, nc, PIT)
                                n_doors = _elements(w, nc, DOOR)
                                n_traps = _elements(w, nc, TRAP)
                                if (len(n_pits) >= 1 and len(n_doors) >= 1
                                        and len(n_doors) + len(n_traps) >= 2):
                                    this_conn = rng.choice(n_pits)
                                    break
                            if this_conn is None:
                                pulled = _pull_from_reserve(
                                    planner, branch, reserve_areas,
                                    lambda doors, traps, pits: (
                                        len(pits) >= 1 and len(doors) >= 1
                                        and len(doors) + len(traps) >= 2))
                                if pulled is not None:
                                    this_conn = rng.choice(_elements(
                                        w, w.class_of_room(pulled), PIT))
                        else:
                            this_conn = rng.choice(up_pits)
                    else:
                        this_conn = rng.choice(up_pits)

            if this_conn is None and room_doors:
                # Fix B: don't consume the branch's last two doors.
                _, _, branch_doors = _collect_region(branch, include_doors=True)
                if len(branch_doors) <= 2:
                    pulled = _pull_from_reserve(
                        planner, branch, reserve_areas,
                        lambda doors, traps, pits: len(doors) >= 3)
                    if pulled is not None:
                        hub_doors = _elements(w, w.class_of_room(pulled), DOOR)
                        _connect(planner, branch, rng.choice(room_doors),
                                 rng.choice(hub_doors))
                        restart = True
                        break
                if this_conn is None:
                    this_exit = rng.choice(room_doors)
                    if up_doors:
                        this_conn = rng.choice(up_doors)

            if this_conn is None:
                # Converter search (PIDO / DITO / any-door).
                region = {hub} | set(upstream) | set(downstream)
                avail = [nc for nc in member_classes(branch)
                         if nc != hub and not any(
                             w.room_ids[h] in branch.dead_ends
                             for h in w.class_rooms(nc))]
                if room_traps and not up_pits and up_doors:
                    pido = [nc for nc in avail
                            if _count(w, nc, PIT) > 0 and _count(w, nc, DOOR) > 0
                            and _count(w, nc, PIT) > _count(w, nc, TRAP)]
                    if pido:
                        this_conn = rng.choice(_elements(w, rng.choice(pido), PIT))
                    else:
                        pulled = _pull_from_reserve(
                            planner, branch, reserve_areas,
                            lambda doors, traps, pits: (
                                len(pits) > 0 and len(doors) > 0
                                and len(pits) > len(traps)))
                        if pulled is not None:
                            this_conn = rng.choice(_elements(
                                w, w.class_of_room(pulled), PIT))
                elif room_doors and not up_doors and up_pits:
                    dito = [nc for nc in avail
                            if _count(w, nc, TRAP) > 0 and _count(w, nc, DOOR) > 0
                            and _count(w, nc, TRAP) > _count(w, nc, PIT)]
                    if dito:
                        this_conn = rng.choice(_elements(w, rng.choice(dito), DOOR))
                    else:
                        pulled = _pull_from_reserve(
                            planner, branch, reserve_areas,
                            lambda doors, traps, pits: (
                                len(traps) > 0 and len(doors) > 0
                                and len(traps) > len(pits)))
                        if pulled is not None:
                            this_conn = rng.choice(_elements(
                                w, w.class_of_room(pulled), DOOR))
                    if this_conn is not None:
                        this_exit = rng.choice(room_doors)
                elif room_doors and not up_doors and not up_pits:
                    for nc in avail:
                        if nc in region:
                            continue
                        n_doors = _elements(w, nc, DOOR)
                        if n_doors:
                            this_conn = rng.choice(n_doors)
                            break
                    if this_conn is None:
                        pulled = _pull_from_reserve(
                            planner, branch, reserve_areas,
                            lambda doors, traps, pits: len(doors) > 0)
                        if pulled is not None:
                            this_conn = rng.choice(_elements(
                                w, w.class_of_room(pulled), DOOR))
                    if this_conn is not None:
                        this_exit = rng.choice(room_doors)

            if this_conn is None:
                raise RuinPlanError(
                    f'finalize step 2: inescapable downstream class '
                    f'(doors={room_doors}, traps={room_traps}, '
                    f'up_doors={up_doors}, up_pits={up_pits})')

            _connect(planner, branch, this_exit, this_conn)
            hub, upstream, downstream = _region(branch)
            delta = build_delta()

        if restart:
            continue

        hub, upstream, downstream = _region(branch)
        if downstream:
            raise RuinPlanError(
                f'finalize step 2 post-check: {len(downstream)} downstream '
                f'class(es) remain')

        # Post-step-2 terminus door check with rescue.
        post2_doors = _elements(w, hub, DOOR)
        if not post2_doors and _terminus_separate(branch):
            r_traps, r_pits = _collect_region(branch)
            if (r_traps or r_pits) and reserve_areas is not None:
                rescued = False
                region = {hub} | set(upstream) | set(downstream)
                hub_traps = _elements(w, hub, TRAP)
                if hub_traps:
                    for nc in member_classes(branch):
                        if nc in region or nc == w.class_of_room(branch.terminus):
                            continue
                        n_pits = _elements(w, nc, PIT)
                        n_doors = _elements(w, nc, DOOR)
                        n_traps = _elements(w, nc, TRAP)
                        if (len(n_pits) >= 1 and len(n_doors) >= 1
                                and len(n_doors) + len(n_traps) >= 2):
                            _connect(planner, branch, rng.choice(hub_traps),
                                     rng.choice(n_pits))
                            rescued = True
                            break
                if not rescued:
                    hub_traps = _elements(w, hub, TRAP)
                    pulled = _pull_from_reserve(
                        planner, branch, reserve_areas,
                        lambda doors, traps, pits: (
                            len(pits) >= 1 and len(doors) >= 1
                            and len(doors) + len(traps) >= 2))
                    if pulled is not None:
                        if hub_traps:
                            _connect(planner, branch, rng.choice(hub_traps),
                                     rng.choice(_elements(
                                         w, w.class_of_room(pulled), PIT)))
                        rescued = True
                if rescued:
                    continue

        # (3) Pair off remaining traps and pits region-wide.
        r_traps, r_pits = _collect_region(branch)
        while r_traps and r_pits:
            rng.shuffle(r_pits)
            _connect(planner, branch, r_traps.pop(), r_pits.pop())
            r_traps, r_pits = _collect_region(branch)
        if r_traps:
            pulled = _pull_from_reserve(
                planner, branch, reserve_areas,
                lambda doors, traps, pits: len(pits) > 0)
            if pulled is not None:
                continue
        if r_traps:
            raise RuinPlanError(
                f'finalize step 3: {len(r_traps)} traps remain with no pits')

        # (4) Connect the terminus to a hub door.
        hub, upstream, downstream = _region(branch)
        remaining_doors = _elements(w, hub, DOOR)
        rng.shuffle(remaining_doors)
        if _terminus_separate(branch) and remaining_doors:
            this_exit = remaining_doors.pop()
            if branch.terminus in branch.dead_ends:
                branch.dead_ends.remove(branch.terminus)
            tc = w.class_of_room(branch.terminus)
            t_doors = _elements(w, tc, DOOR)
            this_conn = t_doors.pop() if t_doors else _raw(w, tc, DOOR)[-1]
            _connect(planner, branch, this_exit, this_conn)
        elif _terminus_separate(branch):
            if branch.terminus not in branch.dead_ends:
                branch.dead_ends.append(branch.terminus)

        # (5) Pair excess hub doors until doors <= dead ends.
        _trim_dead_ends(branch)
        while (len(remaining_doors) > len(branch.dead_ends)
               and len(remaining_doors) >= 2):
            _connect(planner, branch, remaining_doors.pop(), remaining_doors.pop())

        # (5b) Orphan doors: absorb into unconnected door-bearing rooms.
        if len(remaining_doors) > len(branch.dead_ends):
            orphan_count = len(remaining_doors) - len(branch.dead_ends)
            hub, upstream, downstream = _region(branch)
            region = {hub} | set(upstream) | set(downstream)
            avail = [nc for nc in member_classes(branch) if nc not in region]
            for _ in range(orphan_count):
                if len(remaining_doors) <= len(branch.dead_ends):
                    break
                found = False
                for nc in avail:
                    n_doors = _elements(w, nc, DOOR)
                    if n_doors:
                        this_conn = rng.choice(n_doors)
                        target_room = w.owner_room(this_conn)
                        _connect(planner, branch, remaining_doors.pop(), this_conn)
                        # Legacy: the absorbed room joins dead_ends when one
                        # raw door remains (rebalances the step-6 counts).
                        th = w._index[target_room]
                        if (target_room not in branch.dead_ends
                                and len(w.elements[th][DOOR]) == 1):
                            branch.dead_ends.append(target_room)
                        found = True
                        break
                if not found:
                    for nc in member_classes(branch):
                        n_doors = _elements(w, nc, DOOR)
                        if n_doors:
                            _connect(planner, branch, remaining_doors.pop(),
                                     rng.choice(n_doors))
                            found = True
                            break
                if not found:
                    raise RuinPlanError('finalize step 5b: cannot resolve orphan door')

        # (6.0) Dead-end orphan warps get wired against remaining doors.
        connected_warps, unconnected_warps = _classify_warp_rooms(branch)
        while (len(connected_warps) < 2 and remaining_doors
               and any(_is_dead_end_now(branch, x) for x in unconnected_warps)):
            de_warps = [x for x in unconnected_warps if _is_dead_end_now(branch, x)]
            warp_id = rng.choice(de_warps)
            wh = w._index[warp_id]
            this_conn = w.elements[wh][DOOR][-1]
            _connect(planner, branch, remaining_doors.pop(), this_conn)
            if warp_id in branch.dead_ends:
                branch.dead_ends.remove(warp_id)
            connected_warps, unconnected_warps = _classify_warp_rooms(branch)

        # (6) Remaining doors to dead ends, key-bearing first.
        if remaining_doors:
            if len(remaining_doors) > len(branch.dead_ends):
                raise RuinPlanError(
                    f'finalize step 6: more doors ({len(remaining_doors)}) '
                    f'than dead ends ({len(branch.dead_ends)})')
            initial_traps, _, initial_doors = _collect_region(
                branch, include_doors=True, exclude_upstream_doors=True)
            known_doors = set(remaining_doors) | set(initial_doors)

            rng.shuffle(branch.dead_ends)
            selected = [branch.dead_ends.pop() for _ in range(len(remaining_doors))]
            with_keys = [d for d in selected if w.keys[w._index[d]]]
            without_keys = [d for d in selected if not w.keys[w._index[d]]]
            if not without_keys and with_keys and branch.dead_ends:
                for i, cand in enumerate(branch.dead_ends):
                    if not w.keys[w._index[cand]]:
                        branch.dead_ends.append(with_keys.pop())
                        branch.dead_ends.pop(i)
                        without_keys.append(cand)
                        break
            ordered = with_keys + without_keys
            rng.shuffle(remaining_doors)

            for this_exit in remaining_doors:
                rid = ordered.pop(0)
                # Ebot's Rock reaching step 6 as a dead end means its check
                # was never claimed; restrict the backfill to esper/item so a
                # character reward can't teleport into a leaking Thamasa.
                if rid == 'ms-wor-78' and "Ebot's Rock" not in planner.assignments:
                    planner.dead_check_restrictions["Ebot's Rock"] = (
                        RewardType.ESPER | RewardType.ITEM)
                h = w._index[rid]
                de_doors = [d for d in w.elements[h][DOOR]
                            if d not in w.protected]
                this_conn = de_doors.pop() if de_doors else w.elements[h][DOOR][-1]
                _connect(planner, branch, this_exit, this_conn)

                check_traps, _, check_doors = _collect_region(
                    branch, include_doors=True, exclude_upstream_doors=True)
                new_doors = [d for d in check_doors if d not in known_doors]
                if check_traps or new_doors:
                    branch.dead_ends.extend(ordered)
                    break

        new_traps, _, new_doors = _collect_region(
            branch, include_doors=True, exclude_upstream_doors=True)
        if not new_traps and not new_doors:
            break
    else:
        raise RuinPlanError(f'finalize hit max iterations ({max_iterations})')

    if reserve_areas is not None:
        _honor_forced(planner, branch, reserve_areas)


# ---------------------------------------------------------------------------
# Whole-plan finalization: close branches, validate, assemble, verify

def finalize_plan(planner):
    """Close all branches and return the full [door pairs, oneways] map
    (legacy generate_map_with_characters tail; -maze iso / -rkt splices are
    later milestones and appended by the caller when present)."""
    w = planner.world
    rng = planner.rng
    reserve_areas = planner.get_reserve_area_rooms()
    for branch in planner.branches:
        finalize_branch(planner, branch, reserve_areas)

    # Hub validation: no live unprotected exits; terminus merged into hub.
    for i, branch in enumerate(planner.branches):
        hub = branch.hub_class()
        loose_doors = _elements(w, hub, DOOR)
        loose_traps = _elements(w, hub, TRAP)
        if loose_doors or loose_traps:
            raise RuinPlanError(
                f'branch {i} hub has unconnected exits after finalize: '
                f'doors={loose_doors}, traps={loose_traps}')
        if w.class_of_room(branch.terminus) != hub:
            raise RuinPlanError(
                f'branch {i} terminus {branch.terminus!r} not merged into hub')

    pairs = [list(m) for m in w.door_pairs]
    oneways = [list(m) for m in w.oneways]
    pairs = [list(m) for m in reattach_shared_exits(pairs, planner.config._shared)]

    # Splice the independent sub-maps (legacy order: maze, then KT lanes).
    if getattr(planner, 'isolated_maze_map', None) is not None:
        pairs.extend(list(m) for m in planner.isolated_maze_map[0])
        oneways.extend(list(m) for m in planner.isolated_maze_map[1])
    if getattr(planner, 'kt_lane_map', None) is not None:
        pairs.extend(list(m) for m in planner.kt_lane_map[0])
        oneways.extend(list(m) for m in planner.kt_lane_map[1])

    # Hub-side KT traps land on the three KT entry pits, shuffled.
    traps_to_kt = [2077, 2078, 2079]
    pits_into_kt = [t + 1000 for t in traps_to_kt]
    rng.shuffle(traps_to_kt)
    for i in range(3):
        oneways.append([traps_to_kt[i], pits_into_kt[i]])

    verify_no_character_gated_softlock(planner, pairs, oneways)
    return [pairs, oneways]


# ---------------------------------------------------------------------------
# Character-gated softlock verifier (pure BFS)

def _room_data_locks(rid):
    data = room_data.get(rid)
    if not data or len(data) < 6 or not isinstance(data[4], dict):
        return {}
    out = {}
    for k, v in data[4].items():
        out[tuple(k) if isinstance(k, (tuple, list)) else (k,)] = list(v)
    return out


def _room_data_start_keys(rid):
    data = room_data.get(rid)
    if not data or len(data) < 6:
        return []
    return list(data[3])


def _bfs_set(adj, start):
    seen = {start}
    queue = [start]
    qi = 0
    while qi < len(queue):
        cur = queue[qi]
        qi += 1
        for nxt in adj.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def verify_no_character_gated_softlock(planner, pairs, oneways):
    """Free-graph (starting party only) vs full-graph reachability per
    branch: a room enterable without a recruit but leavable only with one
    is a softlock - reject the plan (legacy
    _verify_no_character_gated_softlock, networkx-free)."""
    party = set(planner.config.party)
    for branch_id, branch in enumerate(planner.branches):
        placed = [r for r in branch.rooms if r in room_data]
        hub_id = branch.hub_room

        # Party-only keychain closure.
        keychain = set(party)
        for rid in placed:
            keychain.update(_room_data_start_keys(rid))
        changed = True
        while changed:
            changed = False
            for rid in placed:
                for kt, items in _room_data_locks(rid).items():
                    if set(kt) <= keychain:
                        for item in items:
                            if isinstance(item, str) and item not in keychain:
                                keychain.add(item)
                                changed = True
        blocked = set()
        for rid in placed:
            for kt, items in _room_data_locks(rid).items():
                if set(kt) <= keychain:
                    continue
                for item in items:
                    if isinstance(item, int):
                        blocked.add(item)

        # Exit -> room, from the static room_data (sorted; shared variants).
        # Spec overrides (e.g. the -maze iso composite's rolled entry pit)
        # take precedence - legacy mutates room_data instead.
        overrides = planner.config.spec_overrides
        owner = {}
        for rid in sorted(branch.rooms, key=str):
            if rid in overrides:
                spec = overrides[rid]
                groups = [spec.get('doors', ()), spec.get('traps', ()),
                          spec.get('pits', ())]
            else:
                data = room_data.get(rid)
                if not data:
                    continue
                groups = [data[0], data[1], data[2]]
                groups += list(_room_data_locks(rid).values())
            for group in groups:
                for e in group:
                    if isinstance(e, int):
                        owner.setdefault(e, rid)
        # The synthetic hub rooms aren't in room_data: their single door id
        # comes from room_data['ruin_hub'].
        for i, b2 in enumerate(planner.branches):
            hub_door = room_data['ruin_hub'][0][i]
            owner.setdefault(hub_door, b2.hub_room)

        full_fwd, full_rev = {}, {}
        free_fwd, free_rev = {}, {}

        def add(adj, a, b):
            adj.setdefault(a, []).append(b)

        for d1, d2 in pairs:
            a, b = owner.get(d1), owner.get(d2)
            if a is None or b is None:
                continue
            add(full_fwd, a, b); add(full_fwd, b, a)
            add(full_rev, a, b); add(full_rev, b, a)
            if d1 not in blocked and d2 not in blocked:
                add(free_fwd, a, b); add(free_fwd, b, a)
                add(free_rev, a, b); add(free_rev, b, a)
        for d1, d2 in oneways:
            a, b = owner.get(d1), owner.get(d2)
            if a is None or b is None:
                continue
            add(full_fwd, a, b); add(full_rev, b, a)
            if d1 not in blocked and d2 not in blocked:
                add(free_fwd, a, b); add(free_rev, b, a)

        reachable_free = _bfs_set(free_fwd, hub_id)
        can_return_free = _bfs_set(free_rev, hub_id)
        can_return_full = _bfs_set(full_rev, hub_id)
        stranded = {r for r in reachable_free
                    if r in can_return_full and r not in can_return_free}
        if stranded:
            raise RuinPlanError(
                f'character-gated softlock on branch {branch_id}: '
                f'{sorted(str(s) for s in stranded)} enterable with the '
                f'starting party but not leavable without a recruit')
