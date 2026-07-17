"""Tests for doors.plan.ruination.branch.

Two branches share one WorldModel: membership is enforced by the model
(no double placement), topology queries are live views of the cluster graph,
and check rooms keep their own ids across class merges.

Run: python3 tests/doors/test_ruin_branch.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from doors.model import WorldModel
from doors.plan.ruination.branch import (
    RuinBranch, HUB, UPSTREAM, DOWNSTREAM, UNPLACED,
    WARP_COOLDOWN_INITIAL, TOWN_COOLDOWN_INITIAL,
)


def two_branch_world():
    w = WorldModel({
        'ruin_hub_0': {'doors': [1]},
        'ruin_hub_1': {'doors': [2]},
        'HUB52-ruin': {'doors': [3, 4]},
        'HUB53-ruin': {'doors': [5, 6]},
    })
    b0 = RuinBranch(w, 'ruin_hub_0', ['HUB52-ruin'])
    b1 = RuinBranch(w, 'ruin_hub_1', ['HUB53-ruin'])
    return w, b0, b1


def test_membership_and_classification():
    w, b0, b1 = two_branch_world()
    assert b0.terminus == 'HUB52-ruin' and b1.terminus == 'HUB53-ruin'
    assert b0.dead_ends == ['ruin_hub_0']          # 1-door room, no locks
    # 'ZOZb21' is a ROOM_REWARD room id; the branch flags it as a check room.
    b0.add_room('ZOZb21', {'doors': [10, 11], 'traps': [2010]})
    assert b0.pending_checks() == ['ZOZb21']
    assert 'ZOZb21' in b0 and 'ZOZb21' not in b1
    # The shared model refuses double placement across branches.
    try:
        b1.add_room('ZOZb21', {'doors': [12]})
        raise AssertionError('double placement accepted')
    except ValueError:
        pass
    # Key-bearing one-door room is a dead end; locked one-door room is not.
    b0.add_room('dd', {'doors': [13], 'keys': ['kX']})
    b0.add_room('locked-dd', {'doors': [14], 'locks': {('kY',): [15]}})
    assert 'dd' in b0.dead_ends and 'locked-dd' not in b0.dead_ends
    print('PASS: membership, check rooms, dead ends, double-placement guard')


def test_hub_topology():
    w, b0, b1 = two_branch_world()
    b0.add_room('mid', {'doors': [20, 21], 'traps': [2020], 'pits': [3020]})
    b0.add_room('below', {'doors': [22], 'pits': [3022]})
    assert b0.level('mid') is UNPLACED
    w.connect_door(1, 20)                          # hub <-> mid: mutual
    assert b0.level('mid') is HUB
    w.connect_oneway(2020, 3022)                   # mid --> below
    assert b0.level('below') is DOWNSTREAM
    b0.add_room('above', {'doors': [23], 'traps': [2023]})
    w.connect_oneway(2023, 3020)                   # above --> mid(=hub cluster)
    assert b0.level('above') is UPSTREAM
    assert b0.placed_rooms() == ['ruin_hub_0', 'mid', 'below', 'above']
    assert b0.unplaced_rooms() == ['HUB52-ruin']
    # Other branch is untouched by all of this.
    assert b1.placed_rooms() == ['ruin_hub_1']
    # No member class holds 3+ live exits: hub cluster has door 21 only,
    # 'below'/'above' one exit each, terminus two doors.
    assert not b0.has_a_hub()
    # Hub capability counts ALL member clusters, placed or not.
    b0.add_room('bighub', {'doors': [30, 31, 32], 'traps': [2030]})
    assert b0.has_a_hub()
    w.connect_door(21, 30)
    assert b0.has_a_hub()                          # placed, retains 2 doors + 1 trap
    print('PASS: hub trichotomy + placed/unplaced views')


def test_rewards_and_cooldowns():
    w, b0, b1 = two_branch_world()
    b0.add_room('ZOZb21', {'doors': [10]})
    b0.add_room('PHT12', {'doors': [11]})
    assert b0.rewards_found() == 0
    b0.claim_check('ZOZb21')
    assert b0.pending_checks() == ['PHT12']
    assert b0.rewards_found() == 1
    assert b1.rewards_found() == 0
    # Cooldowns tick on every mapped room and reset on warp/town rooms.
    b0.update_cooldowns('plain-room')
    assert b0.warp_cooldown == WARP_COOLDOWN_INITIAL - 1
    assert b0.town_cooldown == TOWN_COOLDOWN_INITIAL - 1
    b0.update_cooldowns('UPNr03')                  # a WARP_ROOMS member
    assert b0.warp_cooldown == WARP_COOLDOWN_INITIAL
    assert b0.town_cooldown == TOWN_COOLDOWN_INITIAL - 2
    b0.update_cooldowns('MAPr-KOH')               # Kohlingen: town room
    assert b0.town_cooldown == TOWN_COOLDOWN_INITIAL
    for _ in range(10):
        b0.update_cooldowns('plain-room')
    assert b0.warp_cooldown == 0 and b0.town_cooldown == 0   # clamped
    print('PASS: check claiming + cooldown mechanics')


if __name__ == '__main__':
    test_membership_and_classification()
    test_hub_topology()
    test_rewards_and_cooldowns()
    print('\nAll ruin-branch tests passed.')
