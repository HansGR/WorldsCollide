"""Feasibility pruning for the walk: Rules A-H.

Each cluster of the world model is classified by what can flow through it
(door-in/door-out, door-in/trap-out, pit-in/door-out, pit-in/trap-out),
and the network is rejected when the classification proves it cannot be
completed. The rules operate on the always-DAG cluster graph:

  A: network bifurcation - both a DiDo and a PiTo component exist without
     the one-way clusters that could join them
  B/C: one-way imbalance (a DiTo with no PiDo, or vice versa)
  D: door in/out count imbalance
  F: a dead-end cluster whose only exit is locked by a key inside itself
  G: a cluster that can no longer get home (home region out of entrances,
     or a region closed with no exit)
  H: a cluster that can no longer be reached from home (mirror of G)
(Rule E is computed but deliberately not enforced.) A-F are counting
rules and cannot see a fully consumed cluster; G/H enforce reachability
(every cluster reachable from home AND able to get back) as necessary
conditions during the walk, and exactly on the finished map, so the walk
never returns a layout with a region that is unreachable or inescapable.
"""

from doors.model import DOOR, TRAP, PIT


class PruneReject(Exception):
    """The current partial network cannot be completed."""


def check_home_reachable(world, final=False):
    """Rules G and H: every cluster must end up reachable from a home
    cluster (H) and able to get back to one (G). Home = rooms that touch
    the outside world, or the start cluster when a pool has none.

    H mirrors G below: R = home + downstream; a cluster outside R can only
    be reached through a new edge LEAVING R, so while any is outside R,
    R keeps an exit (H2) and each outside cluster (+ its upstream) keeps
    an entrance (H1). With final=True (everything consumed) any cluster
    outside R or E fails outright - the walk's own acceptance check.

    E = home clusters + everything upstream of them (they can already get
    home).  A cluster outside E can only join E through a new edge that
    lands IN E, consuming an entrance there, and only by leaving through an
    exit of its own region.  So, while any cluster is outside E:
      G1  each outside cluster (+ its downstream) keeps an exit;
      G2  E keeps an entrance.
    Both are necessary conditions (locked elements counted, since a key
    may still release them)."""
    homes = getattr(world, 'home_rooms', None)
    if not homes:
        return
    home_c = {world.cluster_of_room(r) for r in homes if r in world._index}
    inert = getattr(world, 'inert_rooms', ())
    clusters = [c for c in world.clusters()
                if not all(world.room_ids[h] in inert
                           for h in world.cluster_rooms(c))]
    # H (mirror of G, for reachability FROM home): R = home + downstream.
    R = set(home_c)
    for c in home_c:
        R.update(world.downstream(c))
    unreached = [c for c in clusters if c not in R]
    if unreached:
        if final:
            raise PruneReject('invalid network: H (finished with clusters unreachable from home)')
        ex = sum(len(world.cluster_elements(c, DOOR, include_locked=True))
                 + len(world.cluster_elements(c, TRAP, include_locked=True))
                 for c in R)
        if ex == 0:
            raise PruneReject('invalid network: H2 (home region has no exit left)')
        for c in unreached:
            region = [c] + world.upstream(c)
            ent = sum(len(world.cluster_elements(x, DOOR, include_locked=True))
                      + len(world.cluster_elements(x, PIT, include_locked=True))
                      for x in region)
            if ent == 0:
                raise PruneReject('invalid network: H1 (sealed from home)')
    E = set(home_c)
    for c in home_c:
        E.update(world.upstream(c))
    outside = [c for c in clusters if c not in E]
    if not outside:
        return
    if final:
        raise PruneReject('invalid network: G (finished with clusters that cannot get home)')
    ent = sum(len(world.cluster_elements(c, DOOR, include_locked=True))
              + len(world.cluster_elements(c, PIT, include_locked=True))
              for c in E)
    if ent == 0:
        raise PruneReject('invalid network: G2 (home region has no entrance left)')
    for c in outside:
        region = [c] + world.downstream(c)
        ex = sum(len(world.cluster_elements(x, DOOR, include_locked=True))
                 + len(world.cluster_elements(x, TRAP, include_locked=True))
                 for x in region)
        if ex == 0:
            raise PruneReject('invalid network: G1 (closed pocket)')


def check_invalid(world):
    """Raise PruneReject if the world fails Rules A/B/C/D/F/G/H."""
    check_home_reachable(world)
    clusters = world.clusters()
    counts = {c: world.counts(c) for c in clusters}  # unprotected, incl locked

    DiDo = DiTo = PiDo = PiTo = False
    doors_in = doors_out = doors_either = 0
    dead_ends = 0
    doors_in_non_dead_ends = 0
    rule_f = False

    for c in clusters:
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
            held = set(world.cluster_keys(c))
            for h in world.cluster_rooms(c):
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
