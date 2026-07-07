"""Structural validation of a solved plan (rewrite Stage B).

The acceptance gate every planner output must pass, independent of how it
was generated (plan section 3.4). Raises ValidationError with specifics.
"""

from doors.model import DOOR, TRAP, PIT


class ValidationError(Exception):
    pass


def check_solved(world, forcing=None):
    """A solved WorldModel must have:
    - every live element consumed (no unmatched doors/traps/pits),
    - every element used at most once across pairs and oneways,
    - door pairs door-to-door and oneways trap-to-pit (by bucket at load),
    - a DAG-clean class graph,
    - every applicable forced connection present,
    - no protected element consumed by a non-forced connection.
    """
    if world.total_unmatched() != 0:
        leftovers = [(k, e) for h in range(len(world.room_ids))
                     for k in (DOOR, TRAP, PIT) for e in world.elements[h][k]]
        raise ValidationError(f'unconsumed elements: {leftovers[:8]}')

    used = [x for p in world.door_pairs for x in p] + \
           [x for p in world.oneways for x in p]
    if len(used) != len(set(used)):
        dupes = sorted({str(x) for x in used if used.count(x) > 1})
        raise ValidationError(f'elements used twice: {dupes[:8]}')

    for c in world.classes():
        if world.find(c) in world.downstream(c):
            raise ValidationError(f'cycle through class {world.class_name(c)}')

    if forcing:
        made = {tuple(p) for p in world.door_pairs} | {tuple(o) for o in world.oneways}
        for d, targets in forcing.items():
            expected = (d, targets[0])
            if d in used or targets[0] in used:
                if expected not in made:
                    raise ValidationError(
                        f'forced connection {expected} missing (found neither side free)')
        forced_pairs = {(d, t[0]) for d, t in forcing.items()}
        for pair in list(world.door_pairs) + list(world.oneways):
            a, b = pair
            if (a in world.protected or b in world.protected) and \
                    (a, b) not in forced_pairs:
                raise ValidationError(f'protected element consumed by {pair}')
