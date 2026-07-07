"""Feasibility pruning for the v2 walk: legacy Rules A-F, ported verbatim
(rewrite Stage B; plan flaw F9 says port first, improve later).

Each class of the world model is classified by what can flow through it
(door-in/door-out, door-in/trap-out, pit-in/door-out, pit-in/trap-out),
and the network is rejected when the classification proves it cannot be
completed. Semantics match data/walks.py check_network_invalidity on the
always-DAG class graph:

  A: network bifurcation - both a DiDo and a PiTo component exist without
     the one-way classes that could join them
  B/C: one-way imbalance (a DiTo with no PiDo, or vice versa)
  D: door in/out count imbalance
  F: a dead-end class whose only exit is locked by a key inside itself
(Rule E is computed but not enforced, as in legacy.)
"""

from doors.model import DOOR, TRAP, PIT


class PruneReject(Exception):
    """The current partial network cannot be completed."""


def check_invalid(world):
    """Raise PruneReject if the world fails Rules A/B/C/D/F."""
    classes = world.classes()
    counts = {c: world.counts(c) for c in classes}  # unprotected, incl locked

    DiDo = DiTo = PiDo = PiTo = False
    doors_in = doors_out = doors_either = 0
    dead_ends = 0
    doors_in_non_dead_ends = 0
    rule_f = False

    for c in classes:
        self_c = counts[c]
        up = [0, 0, 0]
        for u in world.upstream(c):
            uc = counts[u]
            up = [up[i] + uc[i] for i in range(3)]
        down = [0, 0, 0]
        for d in world.downstream(c):
            dc = counts[d]
            down = [down[i] + dc[i] for i in range(3)]

        door_in = (up[0] + self_c[0]) > 0
        door_out = (down[0] + self_c[0]) > 0
        is_dead_end = (sum(up) == 0 and sum(down) == 0
                       and self_c[1] + self_c[2] == 0 and self_c[0] == 1)
        if is_dead_end:
            dead_ends += 1
        else:
            doors_in_non_dead_ends += self_c[0]

        # Rule F: a dead end whose exit is locked by keys held inside it.
        if is_dead_end:
            held = set(world.class_keys(c))
            for h in world.class_rooms(c):
                for key_tuple, items in world.locks[h].items():
                    if set(key_tuple).issubset(held) and any(
                            not isinstance(i, str)
                            and world._element_kind(i) == DOOR for i in items):
                        rule_f = True

        door_in_door_out = ((door_in and down[0] > 0) or
                            (door_out and up[0] > 0) or self_c[0] > 1)
        pit_in = (up[2] + self_c[2]) > 0
        trap_out = (down[1] + self_c[1]) > 0

        delta_in = min(1, self_c[0]) if (sum(up) == 0 and self_c[2] == 0) else 0
        delta_out = min(1, self_c[0]) if (sum(down) == 0 and self_c[1] == 0) else 0
        doors_in += delta_in
        doors_out += delta_out
        doors_either += max(0, self_c[0] - delta_in - delta_out)

        DiDo = DiDo or door_in_door_out
        DiTo = DiTo or (door_in and trap_out)
        PiDo = PiDo or (pit_in and door_out)
        PiTo = PiTo or (pit_in and trap_out)

    rule_a = (not (DiTo and PiDo)) and DiDo and PiTo
    rule_b = DiTo and not PiDo
    rule_c = PiDo and not DiTo
    rule_d = (doors_in + doors_either < doors_out) or \
             (doors_out + doors_either < doors_in)
    if rule_a or rule_b or rule_c or rule_d or rule_f:
        raise PruneReject(
            f"invalid network: A={rule_a} B={rule_b} C={rule_c} "
            f"D={rule_d} F={rule_f}")
