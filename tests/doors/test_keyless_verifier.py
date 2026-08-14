"""Unit tests for verify_no_keyless_oneway_softlock (finalize.py).

Reconstructs the reported softlock (seed 6ddp687hpg3s) with its actual
rooms: PHT01-ruin's trap 2065 randomized onto CDA03's pit 3070, while
CDA03's only door pairs into ZOZr04's zr1-locked door 618 -- a keyless
player who falls in cannot return to the hub. The verifier must reject
exactly that shape and accept lock-free variants of the same map.

Run: python3 tests/doors/test_keyless_verifier.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from data.rooms import room_data
from doors.plan.ruination.finalize import verify_no_keyless_oneway_softlock
from doors.plan.ruination.growth import RuinPlanError


class FakeBranch:
    def __init__(self, hub_room, rooms):
        self.hub_room = hub_room
        self.rooms = rooms


class FakeConfig:
    def __init__(self, party):
        self.party = party
        self.spec_overrides = {}


class FakePlanner:
    def __init__(self, party, hub_room, rooms):
        self.config = FakeConfig(party)
        self.branches = [FakeBranch(hub_room, rooms)]


HUB_DOOR = room_data['HUB50-ruin'][0][0]
HUB = 'FAKE-HUB'
# The incident cast: PHT01-ruin [469 | trap 2065 | pit 3068] is the trap
# room; ZOZr04 [4606, 4607 | lock zr1: 618] holds the lock; CDA03
# [482 | pit 3070] is the landing. UMA02 [732, 733 | pits 3001..] serves
# as a free landing for the control case.
ROOMS = [HUB, 'ZOZr04', 'PHT01-ruin', 'CDA03', 'UMA02']


def expect_raise(pairs, oneways, label):
    planner = FakePlanner(['TERRA', 'LOCKE', 'EDGAR'], HUB, ROOMS)
    try:
        verify_no_keyless_oneway_softlock(planner, pairs, oneways)
    except RuinPlanError as e:
        assert 'keyless one-way softlock' in str(e), str(e)
        print(f'  ok: {label} rejected ({e})')
        return
    raise AssertionError(f'{label}: expected rejection, got pass')


def expect_pass(pairs, oneways, label):
    planner = FakePlanner(['TERRA', 'LOCKE', 'EDGAR'], HUB, ROOMS)
    verify_no_keyless_oneway_softlock(planner, pairs, oneways)
    print(f'  ok: {label} accepted')


def main():
    # 1. The incident: hub <-> ZOZr04 <-> PHT01-ruin all free, trap 2065
    #    randomized onto CDA03's pit 3070, and CDA03's only door pairing
    #    into the zr1-locked 618.
    expect_raise([[4606, HUB_DOOR], [469, 4607], [482, 618]],
                 [[2065, 3070]],
                 'locked-partner landing (the incident)')

    # 2. Control: same trap, landing in UMA02 whose door chain back to
    #    the hub is lock-free.
    expect_pass([[4606, HUB_DOOR], [732, 4607], [469, 733]],
                [[2065, 3001]],
                'free-chain landing')

    # 3. Vanilla-matched one-ways are exempt even with a locked landing
    #    (their escapes are vanilla dungeon design).
    expect_pass([[4606, HUB_DOOR], [469, 4607], [482, 618]],
                [[2070, 3070]],
                'vanilla-matched pair')

    # 4. A trap the keyless player can only reach through the lock is
    #    exempt: whoever falls necessarily holds the key.
    expect_pass([[4606, HUB_DOOR], [469, 618], [4607, 482]],
                [[2065, 3070]],
                'trap room behind the lock')

    print('all keyless-verifier tests passed')


if __name__ == '__main__':
    main()
