"""Branch extension for the ruination planner (rewrite Stage D milestone 2).

Port of the legacy location-aware extension (RuinationBranch.extend_branch_path
with get_valid_pit_targets / get_valid_door_targets) onto WorldModel class
views. Legacy operates on Network nodes, which are rooms or compound rooms
produced by compress_loop; a v2 class IS that compound, so every per-node
count becomes a per-class count, and the forced-connection "downstream rooms"
special cases collapse into ordinary class-graph queries (an unplaced room
already wired to its forced partners is just a small class component with its
own local downstream).

CORE RULE (unchanged from legacy): never make a connection that leaves no
exits downstream of the new active position, and never consume the hub
region's last entrance - downstream nodes must always be able to loop back
during finalize.

Deliberate divergences from legacy, all in compound-node edge cases:
- Warp/town cooldown gating applies if ANY room of the candidate class is a
  warp/town room; legacy tests the node id, so a warp room absorbed into a
  compound node escaped its cooldown.
- The terminus is skipped as a target by CLASS; legacy skips the node id, so
  a terminus absorbed into a compound stopped being skipped (extension never
  runs after the terminus merges, so this is theoretical).
- The no-hub fallback (_extend_branch_path_simple) is not ported: the hub
  room is created with the branch, so the fallback is unreachable in real
  runs.
"""

from doors.model import DOOR, TRAP, PIT
from doors.plan.ruination.branch import StuckReason


def _elements(world, c, kind, exclude=(), free_only=False):
    """Live elements of `kind` in class c, minus protected (and minus
    initially-locked when free_only - exits a key had to release)."""
    out = []
    for e in world.class_elements(c, kind):
        if e in world.protected or e in exclude:
            continue
        if free_only and e in world.initially_locked_exits:
            continue
        out.append(e)
    return out


def _count(world, c, kind, exclude=(), free_only=False):
    return len(_elements(world, c, kind, exclude, free_only))


def member_classes(branch):
    """Distinct classes among the branch's member rooms, insertion order."""
    seen, out = set(), []
    for rid in branch.rooms:
        c = branch.world.class_of_room(rid)
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def topology(branch):
    """The branch trichotomy as class sets (legacy classify_topology)."""
    w = branch.world
    hub = branch.hub_class()
    up = set(w.upstream(hub))
    down = set(w.downstream(hub))
    return {'hub': hub, 'upstream': up, 'downstream': down,
            'hub_and_upstream': {hub} | up,
            'placed': {hub} | up | down}


def _terminus_class(branch):
    if branch.terminus is None:
        return None
    return branch.world.class_of_room(branch.terminus)


def _cooldown_blocks(branch, c):
    """Warp/town rooms may only be mapped once their cooldown reaches zero."""
    w = branch.world
    rooms = [w.room_ids[h] for h in w.class_rooms(c)]
    if branch.warp_cooldown > 0 and any(r in branch.warp_rooms for r in rooms):
        return True
    if branch.town_cooldown > 0 and any(r in branch.town_rooms for r in rooms):
        return True
    return False


def _hub_entrances(branch, topo):
    """Unprotected doors + pits across hub-and-upstream (legacy
    count_entrances_in_region over hub_and_upstream)."""
    w = branch.world
    return sum(_count(w, c, DOOR) + _count(w, c, PIT)
               for c in topo['hub_and_upstream'])


def is_true_dead_end(branch, c):
    """One door, nothing else, nothing behind it - safe to defer to
    finalize, so extension shouldn't waste exits on it (legacy
    is_true_dead_end, per class)."""
    w = branch.world
    if (_count(w, c, DOOR), _count(w, c, TRAP), _count(w, c, PIT)) != (1, 0, 0):
        return False
    if w.downstream(c):                            # forced partners behind it
        return False
    if w.class_keys(c):
        return False
    for h in w.class_rooms(c):
        if w.locks[h]:
            return False
        if w.room_ids[h] in branch.check_rooms:
            return False
    return True


def valid_pit_targets(branch, trap_exit, exit_class, topo):
    """Pits that `trap_exit` may legally connect to (legacy
    get_valid_pit_targets).

    A1. Unplaced target class: must keep at least one exit (its own, or via
        its local downstream), at least one of them originally free (not
        key-released), and the hub region must keep an entrance when needed.
    B1. Placed target: (target + its downstream) retains an exit besides
        trap_exit.
    C.  Hub/upstream target (loop): (exit class + its upstream) retains an
        entrance besides the chosen pit.
    """
    w = branch.world
    valid = []
    term = _terminus_class(branch)
    exit_is_hub_up = exit_class in topo['hub_and_upstream']
    hub_entrances = _hub_entrances(branch, topo)
    exit_upstream = None                           # lazy, for rule C

    for c in member_classes(branch):
        if c == term:
            continue
        pits = _elements(w, c, PIT)
        if not pits:
            continue

        if c not in topo['placed']:
            # === A1: unplaced target ===
            if _cooldown_blocks(branch, c):
                continue
            exits = _count(w, c, DOOR) + _count(w, c, TRAP)
            if exits > 0:
                free = (_count(w, c, DOOR, free_only=True)
                        + _count(w, c, TRAP, free_only=True))
                if free == 0:
                    continue                       # key-released exits only: trap risk
                if exit_is_hub_up and hub_entrances == 0:
                    continue                       # would orphan the hub region
                valid.extend(pits)
            else:
                # Exits only behind forced connections downstream of the
                # target; acts like a trap exit, so the hub region must
                # retain an entrance to loop back through.
                down = w.downstream(c)
                if down:
                    d_exits = sum(_count(w, x, DOOR) + _count(w, x, TRAP)
                                  for x in down)
                    d_free = sum(_count(w, x, DOOR, free_only=True)
                                 + _count(w, x, TRAP, free_only=True)
                                 for x in down)
                    if d_exits > 0 and d_free > 0 and hub_entrances > 0:
                        valid.extend(pits)
        else:
            # === B1: placed target ===
            region = [c] + w.downstream(c)
            exits = sum(_count(w, x, DOOR, exclude=(trap_exit,))
                        + _count(w, x, TRAP, exclude=(trap_exit,))
                        for x in region)
            if exits <= 0:
                continue
            if c in topo['hub_and_upstream']:
                # === C: loop into the hub region ===
                if exit_upstream is None:
                    exit_upstream = [exit_class] + w.upstream(exit_class)
                for pit in pits:
                    entrances = sum(_count(w, x, DOOR, exclude=(pit,))
                                    + _count(w, x, PIT, exclude=(pit,))
                                    for x in exit_upstream)
                    if entrances > 0:
                        valid.append(pit)
            else:
                valid.extend(pits)
    return valid


def valid_door_targets(branch, door_exit, exit_class, topo):
    """Doors that `door_exit` may legally connect to (legacy
    get_valid_door_targets).

    A2. Unplaced target class: (exit class + target) must retain an exit
        after both doors are consumed - or, if the target's exits are all
        behind its forced downstream, the hub region must keep an entrance.
        True dead ends are skipped (deferred to finalize).
    B2. Placed target: (exit class + target + target's downstream) retains
        an exit after both doors are consumed.
    C.  Hub/upstream target (loop): (exit class + its upstream) retains an
        entrance besides the target door.
    """
    w = branch.world
    valid = []
    term = _terminus_class(branch)
    exit_upstream = None                           # lazy, for rule C
    hub_entrance_count = None                      # lazy, for A2 downstream case

    def get_hub_entrance_count():
        nonlocal hub_entrance_count
        if hub_entrance_count is None:
            hub_entrance_count = _hub_entrances(branch, topo)
            # door_exit will be consumed by the connection; if the exit sits
            # in the hub region it no longer counts as an entrance.
            if exit_class in topo['hub_and_upstream']:
                hub_entrance_count -= 1
        return hub_entrance_count

    for c in member_classes(branch):
        if c == term:
            continue
        # Key-released doors are never targeted: the player may arrive
        # before the key.
        room_doors = _elements(w, c, DOOR, free_only=True)
        if not room_doors:
            continue

        if c not in topo['placed']:
            # === A2: unplaced target ===
            if _cooldown_blocks(branch, c):
                continue
            if is_true_dead_end(branch, c):
                continue
            down = set(w.downstream(c))
            for target_door in room_doors:
                if target_door == door_exit:
                    continue
                exclude = (door_exit, target_door)
                exits = entrances = 0
                for x in {exit_class, c}:
                    d = _count(w, x, DOOR, exclude=exclude)
                    exits += d + _count(w, x, TRAP, exclude=exclude)
                    entrances += d + _count(w, x, PIT, exclude=exclude)
                if exits > 0 and (entrances > 0
                                  or exit_class not in topo['hub_and_upstream']):
                    valid.append(target_door)
                elif exits == 0 and down:
                    d_exits = sum(_count(w, x, DOOR, exclude=exclude)
                                  + _count(w, x, TRAP, exclude=exclude)
                                  for x in down - {exit_class, c})
                    if d_exits > 0 and get_hub_entrance_count() > 0:
                        valid.append(target_door)
        else:
            # === B2: placed target ===
            region = {exit_class, c} | set(w.downstream(c))
            for target_door in room_doors:
                if target_door == door_exit:
                    continue
                exclude = (door_exit, target_door)
                exits = sum(_count(w, x, DOOR, exclude=exclude)
                            + _count(w, x, TRAP, exclude=exclude)
                            for x in region)
                if exits <= 0:
                    continue
                if c in topo['hub_and_upstream']:
                    # === C: loop into the hub region ===
                    if exit_upstream is None:
                        exit_upstream = [exit_class] + w.upstream(exit_class)
                    entrances = sum(
                        _count(w, x, DOOR, exclude=(target_door,))
                        + _count(w, x, PIT, exclude=(target_door,))
                        for x in exit_upstream)
                    if entrances > 0:
                        valid.append(target_door)
                else:
                    valid.append(target_door)
    return valid


def _deepest_classes(world, start, downstream):
    """Ends of the LONGEST paths from `start` through the class DAG (legacy
    collects exits from the deepest nodes of get_downstream_paths)."""
    nodes = {start} | set(downstream)
    edges = []
    for h1, h2 in world.edges:
        a, b = world.find(h1), world.find(h2)
        if a != b and a in nodes and b in nodes:
            edges.append((a, b))
    dist = {c: 0 for c in nodes}
    for _ in range(len(nodes)):                    # DAG: relaxes to fixpoint
        changed = False
        for a, b in edges:
            if dist[a] + 1 > dist[b]:
                dist[b] = dist[a] + 1
                changed = True
        if not changed:
            break
    max_d = max(dist[c] for c in downstream)
    return [c for c in downstream if dist[c] == max_d]


def extend_branch(branch, forcing, rng):
    """One extension step: pick (exit_id, target_id) or (None, None) with
    branch.last_stuck_reason set (legacy extend_branch_path).

    The caller performs the connection on the model, updates the active
    room, ticks cooldowns, and applies the target class's keys.
    """
    w = branch.world
    topo = topology(branch)
    active_class = w.class_of_room(branch.active)
    act_downstream = w.downstream(active_class)

    # === STEP 1: forced exits anywhere on the active path go first ===
    for c in [active_class] + act_downstream:
        for e in w.class_elements(c, DOOR) + w.class_elements(c, TRAP):
            if e in forcing:
                return e, forcing[e][0]

    # === STEP 2: collect exits from the deepest point of the active path ===
    # When the active position is downstream, key-released exits are not
    # followed: the player may not hold the keys yet, and collapsing such an
    # exit into the hub could strand them.
    is_down = active_class in topo['downstream']
    if act_downstream:
        exit_classes = _deepest_classes(w, active_class, act_downstream)
    else:
        exit_classes = [active_class]
    available = {'doors': [], 'traps': []}
    for c in exit_classes:
        available['doors'].extend(_elements(w, c, DOOR, free_only=is_down))
        available['traps'].extend(_elements(w, c, TRAP, free_only=is_down))

    # === STEP 3: traps first, unless no pit targets exist anywhere ===
    trap_targets = door_targets = False
    term = _terminus_class(branch)
    for c in member_classes(branch):
        if c in topo['placed'] or c == term:
            continue
        if _count(w, c, PIT) > 0:
            trap_targets = True
        if _count(w, c, DOOR) > 0:
            door_targets = True
        if trap_targets and door_targets:
            break
    for c in topo['hub_and_upstream']:
        if _count(w, c, PIT) > 0:
            trap_targets = True
        if _count(w, c, DOOR) > 0:
            door_targets = True
    order = ['traps', 'doors']
    if not trap_targets and door_targets:
        order = ['doors', 'traps']

    # === STEP 4: shuffle exits, first exit with a valid target wins ===
    for exit_type in order:
        pool = [(e, w.owner_class(e)) for e in available[exit_type]]
        rng.shuffle(pool)
        for exit_id, exit_class in pool:
            if exit_type == 'traps':
                targets = valid_pit_targets(branch, exit_id, exit_class, topo)
            else:
                targets = valid_door_targets(branch, exit_id, exit_class, topo)
            if targets:
                branch.last_stuck_reason = StuckReason.NONE
                return exit_id, rng.choice(targets)

    # === STEP 5: stuck - diagnose for smart area distribution ===
    _diagnose_stuck(branch, available, topo)
    return None, None


def _diagnose_stuck(branch, available, topo):
    """Set branch.last_stuck_reason from what was missing (legacy
    _diagnose_stuck_reason)."""
    w = branch.world
    have_traps = len(available['traps']) > 0
    have_doors = len(available['doors']) > 0
    if not have_traps and not have_doors:
        branch.last_stuck_reason = StuckReason.NO_EXITS
        return

    term = _terminus_class(branch)
    pits_avail = pido_avail = doors_avail = False
    for c in member_classes(branch):
        if c in topo['placed'] or c == term:
            continue
        pits = _count(w, c, PIT)
        doors = _count(w, c, DOOR)
        if pits > 0:
            pits_avail = True
            if doors > 0:
                pido_avail = True
        if doors > 0:
            doors_avail = True

    hub_doors = sum(_count(w, c, DOOR) for c in topo['hub_and_upstream'])
    hub_pits = sum(_count(w, c, PIT) for c in topo['hub_and_upstream'])

    if have_traps and not pits_avail and hub_pits == 0:
        branch.last_stuck_reason = StuckReason.NEED_PITS
    elif have_traps and not pido_avail:
        branch.last_stuck_reason = StuckReason.NEED_PIDO
    elif have_doors and not doors_avail and hub_doors == 0:
        branch.last_stuck_reason = StuckReason.NEED_DOORS
    else:
        branch.last_stuck_reason = StuckReason.NO_SAFE_EXITS
