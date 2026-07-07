"""The v2 backtracking walk (rewrite Stage B).

A faithful port of the legacy Network.connect_network sampling algorithm
onto the journaled WorldModel: grow from an active class, offer its and
its downstream classes' exits in random order, try random legal entrances
for each, prune with Rules A-F, and backtrack by journal rollback (no
copies). The deterministic attempted-connection budget from p7 carries
over unchanged.

Deliberate distribution-affecting differences from legacy, both approved:
- the class graph is always DAG-clean (model invariant; legacy could
  carry residual 2-cycles), and
- dead-end attachment offers only live doors as attachment points
  (legacy also offered locked doors and re-parked the dead end's keys
  behind the lock; support pending if parity runs show it matters).
"""

import random

from doors.model import DOOR, TRAP, PIT
from doors.plan.prune import check_invalid, PruneReject


class WalkBudgetExhausted(Exception):
    """Global stop signal: re-raised past every frame (p7 semantics)."""


class WalkFailed(Exception):
    """The walk ran out of options at the top frame."""


def force_connections(world, forcing):
    """Apply forced connections whose partner is present; protect both
    sides either way (legacy ForceConnections)."""
    for d, targets in forcing.items():
        partner = targets[0]
        if partner in world._owner and d in world._owner:
            live = any(d in world.elements[world._owner[d]][k] for k in (DOOR, TRAP))
            plive = any(partner in world.elements[world._owner[partner]][k]
                        for k in (DOOR, PIT))
            if live and plive:
                if world._element_kind(d) == DOOR:
                    world.connect_door(d, partner)
                else:
                    world.connect_oneway(d, partner)
        world.protected.add(d)
        world.protected.update(targets)


def is_attachable(world, c):
    """Legacy Network.is_attachable on a class."""
    doors = len(world.class_elements(c, DOOR, include_locked=True))
    traps = len(world.class_elements(c, TRAP, include_locked=True))
    pits = len(world.class_elements(c, PIT))
    up = [0, 0, 0]
    for u in world.upstream(c):
        rc = _raw_counts(world, u)
        up = [up[i] + rc[i] for i in range(3)]
    down = [0, 0, 0]
    for d in world.downstream(c):
        rc = _raw_counts(world, d)
        down = [down[i] + rc[i] for i in range(3)]
    if up != [0, 0, 0] or down != [0, 0, 0]:
        return doors > 1 or (doors == 1 and (traps + down[0] + down[1]) > 0
                             and (pits + up[0] + up[2]) > 0)
    return doors > 1 or (doors == 1 and traps > 0 and pits > 0)


def _raw_counts(world, c):
    return (len(world.class_elements(c, DOOR, include_locked=True)),
            len(world.class_elements(c, TRAP, include_locked=True)),
            len(world.class_elements(c, PIT, include_locked=True)))


def _is_dead_end(world, c):
    if world.upstream(c) or world.downstream(c):
        return False
    live = tuple(len(world.class_elements(c, k)) for k in (DOOR, TRAP, PIT))
    locks = sum(len(world.locks[h]) for h in world.class_rooms(c))
    return live == (1, 0, 0) and locks == 0


def attach_dead_ends(world, rng):
    """Connect dead-end classes to attachable doors (legacy port, live
    doors only)."""
    for _ in range(21):  # legacy max_loop_number = 20, plus initial pass
        dead = [c for c in world.classes() if _is_dead_end(world, c)]
        if not dead:
            return
        rng.shuffle(dead)
        for dc in dead:
            if not _is_dead_end(world, dc):
                continue  # merged away by an earlier attachment this pass
            dd = world.class_elements(dc, DOOR)[0]
            candidates = []
            for c in world.classes():
                if c != world.find(dc) and is_attachable(world, c):
                    candidates.extend(world.class_elements(c, DOOR))
            rng.shuffle(candidates)
            dead_keys = set(world.class_keys(dc))
            for da in candidates:
                target = world.owner_class(da)
                # Legacy key-safety: don't attach a key into a room whose
                # every other exit is locked only by keys inside these rooms.
                held = dead_keys | set(world.class_keys(target))
                other_doors = [d for d in world.class_elements(target, DOOR,
                                                               include_locked=True)
                               if d != da]
                if dead_keys and other_doors:
                    all_locked_internally = True
                    locked = {}
                    for h in world.class_rooms(target):
                        for kt, items in world.locks[h].items():
                            for it in items:
                                locked[it] = kt
                    for d in other_doors:
                        if d not in locked or not set(locked[d]) <= held:
                            all_locked_internally = False
                            break
                    if all_locked_internally:
                        continue
                world.connect_door(dd, da)
                break
    # Leftover dead ends are tolerated (legacy: "it'll probably get
    # straightened out in the walk").


def walk(world, active, rng, budget):
    """Recursive worker: returns on success, raises on failure.
    `budget` is a shared [remaining] list (p7 semantics)."""
    if world.total_unmatched() == 0:
        return
    check_invalid(world)

    for k in list(world.class_keys(active)):
        world.apply_key(k)

    exits = list(world.class_elements(active, DOOR, unprotected_only=True)) + \
        list(world.class_elements(active, TRAP, unprotected_only=True))
    for c in world.downstream(active):
        exits += world.class_elements(c, DOOR, unprotected_only=True)
        exits += world.class_elements(c, TRAP, unprotected_only=True)
    rng.shuffle(exits)

    forced = [e for e in exits if e in world.forcing]
    if forced:
        exits = [forced[0]]  # fail fast, as legacy

    while exits:
        d1 = exits.pop()
        c1 = world.owner_class(d1)
        d1_is_door = d1 in world.elements[world._owner[d1]][DOOR]
        # Keys along the trail from the active class down to d1's class.
        if c1 != world.find(active):
            for tc in _trail(world, c1, active):
                for k in list(world.class_keys(tc)):
                    world.apply_key(k)

        if d1 in world.forcing:
            entrances = list(world.forcing[d1])
        else:
            kind = DOOR if d1_is_door else PIT
            entrances = []
            for c in world.classes():
                entrances += [e for e in world.class_elements(c, kind)
                              if e != d1 and e not in world.protected]
            rng.shuffle(entrances)

        while entrances:
            d2 = entrances.pop()
            budget[0] -= 1
            if budget[0] < 0:
                raise WalkBudgetExhausted()
            mark = world.checkpoint()
            try:
                if d1_is_door:
                    new_active = world.connect_door(d1, d2)
                else:
                    world.connect_oneway(d1, d2)
                    new_active = world.owner_class(d2)
                for k in list(world.class_keys(new_active)):
                    world.apply_key(k)
                walk(world, new_active, rng, budget)
                return
            except WalkBudgetExhausted:
                raise
            except (PruneReject, WalkFailed):
                world.rollback(mark)
        raise WalkFailed(f'{d1} ran out of entrances')
    raise WalkFailed('ran out of exits')


def _trail(world, c1, active):
    """Classes on a shortest upstream path from c1 to active, including c1,
    excluding active (legacy key-trail semantics)."""
    active = world.find(active)
    parent = {c1: None}
    queue = [c1]
    qi = 0
    adj = world._neighbors(False)
    while qi < len(queue):
        cur = queue[qi]; qi += 1
        for p in adj.get(cur, ()):
            if p == active:
                chain = [c1] if cur == c1 else []
                node = cur
                while node is not None:
                    chain.append(node)
                    node = parent[node]
                return chain
            if p not in parent:
                parent[p] = cur
                queue.append(p)
    return [c1]


def run(specs, forcing, seed, start_room=None, budget_limit=5000, attempts=5):
    """Full pool run: build model, force, attach dead ends, walk with
    start re-rolls. Returns the solved WorldModel."""
    from doors.model import WorldModel
    rng = random.Random(seed)
    last = None
    for _ in range(attempts):
        world = WorldModel(specs)
        world.forcing = forcing
        force_connections(world, forcing)
        attach_dead_ends(world, rng)
        if start_room is not None:
            starts = [start_room]
        else:
            roots = [r for r in specs if 'root' in str(r)]
            starts = roots or list(specs)
        active = world.class_of_room(rng.choice(starts))
        try:
            walk(world, active, rng, [budget_limit])
            return world
        except (WalkFailed, WalkBudgetExhausted, PruneReject) as e:
            last = e
    raise WalkFailed(f'pool unsolved after {attempts} attempts') from last
