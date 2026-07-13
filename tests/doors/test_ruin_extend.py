"""Tests for doors.plan.ruination.extend.

Each extension rule (A1/B1/C for pits, A2/B2/C for doors), the cooldown and
true-dead-end gates, the forced-exit fast path, deepest-point exit
collection, and stuck diagnosis - on small synthetic worlds.

Run: python3 tests/doors/test_ruin_extend.py
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from doors.model import WorldModel
from doors.plan.ruination.branch import RuinBranch, StuckReason
from doors.plan.ruination.extend import (
    topology, valid_pit_targets, valid_door_targets, extend_branch,
    is_true_dead_end, _deepest_classes,
)


def make(specs, hub='ruin_hub_0'):
    w = WorldModel(specs)
    b = RuinBranch(w, hub, [r for r in specs if r != hub])
    return w, b


def test_pit_rule_A1():
    w, b = make({
        'ruin_hub_0': {'doors': [1], 'traps': [2001], 'pits': [3001]},
        'pito': {'pits': [3010], 'traps': [2010]},
        'noexit': {'pits': [3011]},
        'keyonly': {'pits': [3012], 'locks': {('k',): [12]}},
    })
    w.apply_key('k')                     # door 12 goes live but key-released
    topo = topology(b)
    hub = topo['hub']
    got = valid_pit_targets(b, 2001, hub, topo)
    # Hub's own pit is a legal self-loop (B1/C pass via door 1, as in
    # design); pito qualifies (free exit); noexit has no exit at all;
    # keyonly's only exit was key-released, so a pit entry could trap the
    # player.
    assert got == [3001, 3010], got
    print('PASS: A1 - exits required, key-released-only exits rejected')


def test_pit_rule_A1_hub_entrance_guard():
    # Hub region with NO entrances (trap only): mapping a new room through
    # the hub's trap would leave downstream unable to loop back.
    w, b = make({
        'ruin_hub_0': {'traps': [2001]},
        'pito': {'pits': [3010], 'traps': [2010]},
    })
    topo = topology(b)
    assert valid_pit_targets(b, 2001, topo['hub'], topo) == []
    print('PASS: A1 - hub entrance guard')


def test_pit_rule_A1_forced_downstream():
    # Target has a pit and no exits of its own, but its forced trap (already
    # wired, hence consumed) leads to a cluster with free exits.
    w, b = make({
        'ruin_hub_0': {'doors': [1], 'traps': [2001], 'pits': [3001]},
        'entry': {'pits': [3013], 'traps': [2013]},
        'behind': {'doors': [13, 14], 'pits': [3014]},
    })
    w.connect_oneway(2013, 3014)         # the forced connection, pre-wired
    topo = topology(b)
    got = valid_pit_targets(b, 2001, topo['hub'], topo)
    # 3001 is the legal hub self-loop again; 3014 was consumed by the
    # forced wiring; 3013 is valid because 'behind' holds free exits.
    assert got == [3001, 3013], got
    print('PASS: A1 - exits behind forced downstream count')


def test_pit_rules_B1_C():
    w, b = make({
        'ruin_hub_0': {'doors': [1], 'traps': [2001], 'pits': [3001]},
        'down': {'pits': [3020], 'traps': [2020], 'doors': [21]},
    })
    w.connect_oneway(2001, 3020)         # hub --> down: 'down' is placed
    topo = topology(b)
    down_c = w.cluster_of_room('down')
    # B1: connecting down's trap 2020 to the hub pit - target (hub) must
    # keep an exit besides 2020: hub has door 1. C: entrance region
    # (down + its upstream = hub) must keep an entrance besides 3001:
    # door 1 and door 21 remain. So 3001 is a valid loop target.
    got = valid_pit_targets(b, 2020, down_c, topo)
    assert got == [3001], got
    # Strip the region's other entrances: doors 1 and 21 both protected ->
    # rule C rejects consuming the last entrance (3001 itself).
    w.protected.update({1, 21})
    got = valid_pit_targets(b, 2020, down_c, topo)
    assert got == [], got
    print('PASS: B1 + C - loop allowed only while another entrance remains')


def test_door_rules_A2():
    w, b = make({
        'ruin_hub_0': {'doors': [1, 2], 'traps': [2001], 'pits': [3001]},
        'tde': {'doors': [30]},                      # true dead end: skipped
        'twodoor': {'doors': [31, 32]},
        'keydoor': {'locks': {('k',): [33]}, 'pits': [3033]},
    })
    w.apply_key('k')                     # door 33 live but key-released
    topo = topology(b)
    hub = topo['hub']
    assert is_true_dead_end(b, w.cluster_of_room('tde'))
    got = valid_door_targets(b, 1, hub, topo)
    # Hub's own door 2 is a legal same-class pairing (trap 2001 remains an
    # exit, pit 3001 an entrance); tde skipped; keydoor's door is
    # key-released (never targeted); twodoor offers both doors.
    assert got == [2, 31, 32], got
    # A check room is never a true dead end (313 is a ROOM_REWARD id).
    b.add_room(313, {'doors': [40]})
    assert not is_true_dead_end(b, w.cluster_of_room(313))
    assert 40 in valid_door_targets(b, 1, hub, topo)
    print('PASS: A2 - true-dead-end skip, key-released doors untargetable')


def test_door_rules_B2_C():
    w, b = make({
        'ruin_hub_0': {'doors': [1, 2], 'traps': [2001], 'pits': [3001]},
        'down': {'pits': [3020], 'doors': [21, 22]},
    })
    w.connect_oneway(2001, 3020)
    topo = topology(b)
    down_c = w.cluster_of_room('down')
    # Door 21 (down, placed) connecting back to hub door 1: B2 region keeps
    # exits (door 2, door 22); C entrance region (down + hub) keeps
    # entrances besides door 1 (door 2, pit 3001, door 22). Both hub doors valid.
    got = valid_door_targets(b, 21, down_c, topo)
    assert got == [1, 2], got
    # Exhaust the other entrances: protect 2, 22 and pit 3001. Consuming
    # door 1 would leave the region entrance-less -> rejected by C... but
    # B2 also now fails (no exits besides the pair). Either way: no targets.
    w.protected.update({2, 22, 3001})
    assert valid_door_targets(b, 21, down_c, topo) == []
    print('PASS: B2 + C - hub loop preserved entrances')


def test_cooldown_gating():
    # Room 40 is in WARP_ROOMS; 'ms-wor-59' is in TOWN_ROOMS.
    # (No hub pit here, so the hub self-loop doesn't muddy the assertions.)
    w, b = make({
        'ruin_hub_0': {'doors': [1], 'traps': [2001]},
        40: {'pits': [3040], 'traps': [2040]},
        'ms-wor-59': {'doors': [41, 42]},
    })
    topo = topology(b)
    hub = topo['hub']
    assert valid_pit_targets(b, 2001, hub, topo) == []       # warp on cooldown
    assert valid_door_targets(b, 1, hub, topo) == []         # town on cooldown
    b.warp_cooldown = 0
    b.town_cooldown = 0
    assert valid_pit_targets(b, 2001, hub, topo) == [3040]
    assert valid_door_targets(b, 1, hub, topo) == [41, 42]
    print('PASS: warp/town cooldown gating')


def test_extend_forced_first_and_deepest():
    w, b = make({
        'ruin_hub_0': {'doors': [1], 'traps': [2001], 'pits': [3001]},
        'a': {'pits': [3010], 'traps': [2010]},
        'bb': {'pits': [3011], 'traps': [2011], 'doors': [15]},
        'c': {'pits': [3012], 'traps': [2012]},
    })
    rng = random.Random(7)
    # Forced exit on the active path wins immediately.
    got = extend_branch(b, {2001: [3010]}, rng)
    assert got == (2001, 3010), got
    # Build the chain hub -> a -> bb; active stays hub; exits must be
    # collected from the DEEPEST class (bb), so the chosen exit is bb's.
    w.connect_oneway(2001, 3010)
    w.connect_oneway(2010, 3011)
    hub_c = w.cluster_of_room('ruin_hub_0')
    deep = _deepest_classes(w, hub_c, w.downstream(hub_c))
    assert deep == [w.cluster_of_room('bb')]
    exit_id, target = extend_branch(b, {}, rng)
    assert exit_id in (2011, 15), (exit_id, target)
    assert target == 3012                # only unplaced pit; c has a free trap
    print('PASS: forced-exit fast path + deepest-point exit collection')


def test_stuck_diagnosis():
    w, b = make({
        'ruin_hub_0': {'traps': [2001]},
        'd': {'doors': [31, 32]},
    })
    rng = random.Random(1)
    got = extend_branch(b, {}, rng)
    assert got == (None, None)
    assert b.last_stuck_reason == StuckReason.NEED_PITS
    # No exits at all -> NO_EXITS.
    w2, b2 = make({'ruin_hub_0': {'pits': [3001]},
                   'e': {'pits': [3010]}})
    got = extend_branch(b2, {}, random.Random(1))
    assert got == (None, None)
    assert b2.last_stuck_reason == StuckReason.NO_EXITS
    print('PASS: stuck diagnosis (NEED_PITS, NO_EXITS)')


if __name__ == '__main__':
    test_pit_rule_A1()
    test_pit_rule_A1_hub_entrance_guard()
    test_pit_rule_A1_forced_downstream()
    test_pit_rules_B1_C()
    test_door_rules_A2()
    test_door_rules_B2_C()
    test_cooldown_gating()
    test_extend_forced_first_and_deepest()
    test_stuck_diagnosis()
    print('\nAll ruin-extend tests passed.')
