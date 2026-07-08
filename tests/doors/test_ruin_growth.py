"""Integration tests for doors.plan.ruination.growth (Stage D milestone 3).

Runs the v2 growth orchestrator on the REAL room pool across many seeds
and checks the plan invariants:
- requested characters/espers are all placed, kinds match check flags
- a granted character's in-game lock was already on the keychain
- no element is used twice across door pairs + oneways
- every granted character's areas are mapped; forced_same_branch respected
- branch membership is disjoint

Run: python3 tests/doors/test_ruin_growth.py [n_seeds]
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from doors.plan.ruination.growth import (
    RuinConfig, RuinPlanner, RuinPlanError, CHARACTER, ESPER, ITEM,
)

PARTIES = [
    ['TERRA', 'LOCKE', 'EDGAR'],
    ['CELES', 'SABIN', 'GAU'],
    ['MOG', 'STRAGO', 'RELM', 'SETZER'],
    ['CYAN', 'SHADOW', 'UMARO'],
]


def run_one(seed, party, maze=None):
    rng = random.Random(seed)
    cfg = RuinConfig(party, char_range=(2, 6), esper_range=(1, 4),
                     maze=maze, blitz_characters=['SABIN'])
    planner = RuinPlanner(cfg, rng)
    planner.grow()
    return planner


def check_invariants(p):
    w = p.world
    # Reward counts satisfied.
    chars_granted = [v[1] for v in p.assignments.values() if v[0] == 'CHARACTER']
    espers_granted = [1 for v in p.assignments.values() if v[0] == 'ESPER']
    assert len(chars_granted) == len(p.planned_characters), \
        (chars_granted, p.planned_characters)
    assert sorted(chars_granted) == sorted(p.planned_characters)
    assert len(espers_granted) >= p.Requested[1]
    # Kinds legal for their checks.
    for name, (kind, _) in p.assignments.items():
        flags = p.config.check_flags(name)
        expect = {'CHARACTER': CHARACTER, 'ESPER': ESPER, 'ITEM': ITEM}[kind]
        assert flags & expect, (name, kind, flags)
    # Character in-game locks honored in acquisition order.
    seen = set(p.config.party)
    for entry in p.reward_log:
        if entry['kind'] is CHARACTER:
            locker = p.config.rewards_locked_by_character.get(entry['name'])
            assert locker is None or locker in seen, entry
            seen.add(entry['character'])
    # No element reused.
    used = []
    for a, b in w.door_pairs:
        used += [a, b]
    for t, pt in w.oneways:
        used += [t, pt]
    assert len(used) == len(set(used)), 'element used twice'
    # Granted characters' areas are mapped.
    for ch in chars_granted:
        for area in p.config.character_areas.get(ch, []):
            assert area in p.AreasUsed, (ch, area)
    # forced_same_branch respected.
    for area, partners in p.config.forced_same_branch.items():
        if area in p.AreasUsed:
            for partner in partners:
                if partner in p.AreasUsed:
                    assert p.AreasUsed[area] == p.AreasUsed[partner], \
                        (area, partner, p.AreasUsed[area], p.AreasUsed[partner])
    # Branch membership disjoint.
    all_rooms = [r for b in p.branches for r in b.rooms]
    assert len(all_rooms) == len(set(all_rooms)), 'room on two branches'
    # Keychain contains party + granted characters.
    assert set(p.config.party) <= p.keychain
    assert set(chars_granted) <= p.keychain


def main(n=40):
    ok = fail = 0
    failures = []
    for i in range(n):
        party = PARTIES[i % len(PARTIES)]
        maze = [None, 'sep', 'iso'][i % 3]
        try:
            p = run_one(f'growth{i}', party, maze=maze)
            check_invariants(p)
            ok += 1
        except RuinPlanError as e:
            fail += 1
            failures.append((i, str(e)[:100]))
        except RecursionError:
            fail += 1
            failures.append((i, 'recursion'))
    print(f'growth integration: {ok}/{n} plans complete, {fail} failed')
    for i, msg in failures[:5]:
        print(f'  seed {i}: {msg}')
    # Legacy regenerates on failure (~4% observed); the growth stage alone
    # should complete for the large majority of seeds.
    assert ok >= n * 0.8, f'too many failures: {fail}/{n}'
    print('PASS: growth invariants across seeds')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
