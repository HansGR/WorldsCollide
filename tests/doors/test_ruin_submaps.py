"""Tests for the ruination sub-map randomizers:
the isolated dream maze and the KT lane randomizer.

Both are rejection samplers that only return verified layouts, so the
tests re-verify independently: maze layouts must be traversable to the
boss room from everywhere with both stooge rooms round-trippable; KT
layouts must use each element once, cover every KT room across lanes,
and strip the platform pseudo-ids.

Run: python3 tests/doors/test_ruin_submaps.py
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from data.rooms import room_data
from doors.plan.ruination.dream_maze import (
    randomize_isolated_maze, MAZE_ROOMS, STOOGE_ROOMS, END_ROOM, ENTRY_PITS,
)
from doors.plan.ruination.kefka_tower import (
    randomize_kefka_tower, derive_tower_tables, KT_PLATFORM_IDS, KT_CROSSINGS,
)


def test_dream_maze():
    door_room, trap_room, pit_room = {}, {}, {}
    for r in MAZE_ROOMS:
        for d in room_data[r][0]:
            door_room[d] = r
        for t in room_data[r][1]:
            trap_room[t] = r
        for p in room_data[r][2]:
            pit_room[p] = r

    for seed in range(10):
        (door_pairs, trap_pits), entry_pit = randomize_isolated_maze(
            random.Random(f'maze{seed}'))
        assert entry_pit in ENTRY_PITS
        # Every door used exactly once; every trap matched; entry pit unused.
        used_doors = [d for m in door_pairs for d in m]
        assert sorted(used_doors) == sorted(door_room)
        assert sorted(t for t, _ in trap_pits) == sorted(trap_room)
        assert entry_pit not in [p for _, p in trap_pits]
        # Independent solvability check.
        adj = {r: set() for r in MAZE_ROOMS}
        for d1, d2 in door_pairs:
            adj[door_room[d1]].add(door_room[d2])
            adj[door_room[d2]].add(door_room[d1])
        for t, p in trap_pits:
            assert trap_room[t] != pit_room[p], 'trap into own room'
            adj[trap_room[t]].add(pit_room[p])

        def reach(start):
            seen, stack = {start}, [start]
            while stack:
                for n in adj[stack.pop()]:
                    if n not in seen:
                        seen.add(n)
                        stack.append(n)
            return seen
        for r in MAZE_ROOMS:
            assert END_ROOM in reach(r), f'room {r} cannot reach boss'
        from_end = reach(END_ROOM)
        assert all(s in from_end for s in STOOGE_ROOMS)
    print('PASS: dream maze - 10 seeds, layouts independently solvable')


def test_kefka_tower():
    KT = [r for r in room_data
          if r.startswith('KT') and not r.endswith('-ruin')]
    all_elements = set()
    for r in KT:
        for group in room_data[r][:3]:
            all_elements.update(group)

    ok = 0
    for seed in range(3):
        result = randomize_kefka_tower(random.Random(f'kt{seed}'))
        if result is None:
            continue
        ok += 1
        pairs, oneways = result
        used = [e for m in pairs for e in m] + [e for m in oneways for e in m]
        assert len(used) == len(set(used)), 'element used twice'
        assert not (set(used) & KT_PLATFORM_IDS), 'platform id leaked'
        assert set(used) <= all_elements | {2070}
        # Room coverage: every KT room touched by some connection or a
        # gated crossing / key room (entries are pit-only landing spots).
        room_of = {}
        for r in KT:
            for group in room_data[r][:3]:
                for e in group:
                    room_of[e] = r
        touched = {room_of[e] for e in used if e in room_of}
        touched.update(x for a, b, _, _ in KT_CROSSINGS for x in (a, b))
        assert touched == set(KT), set(KT) - touched
    assert ok >= 2, f'KT randomization failed too often ({ok}/3)'
    print(f'PASS: KT lanes - {ok}/3 seeds verified, coverage + single-use')


def test_kefka_tower_tables_derived():
    """The crossings come from room_data: the real data gives the two
    two-way gated crossings; a trap->pit pair would give a one-way one;
    malformed data is refused instead of silently mis-modelled."""
    crossings, forced, platforms, key_rooms, keys = derive_tower_tables()
    assert crossings == [('KTA5a', 'KTA5b', ('KT1',), True),
                         ('KTA8a', 'KTA8b', ('KT2',), True)], crossings
    assert forced == {1565: [1566], 1567: [1568]}
    assert platforms == {1565, 1566, 1567, 1568}
    assert key_rooms == {'KTB8': ('KT1',), 'KTC10': ('KT2',)}
    assert keys == ['KT1', 'KT2']

    rooms = dict(room_data)
    rooms['KTA5a'] = [[760], [], [], [], {'KT1': [2990]}, 1]
    rooms['KTA5b'] = [[761], [], [], [], {'KT1': [3990]}, 1]
    forcing = {2990: [3990], 1567: [1568]}
    crossings = derive_tower_tables(rooms, forcing)[0]
    assert crossings[0] == ('KTA5a', 'KTA5b', ('KT1',), False), crossings

    for bad_forcing, why in (({1565: [1566]}, 'unpaired'),
                             ({1565: [3990], 1567: [1568]}, 'foreign partner')):
        try:
            derive_tower_tables(room_data, bad_forcing)
        except ValueError:
            continue
        raise AssertionError(f'{why} crossing data was accepted')
    print('PASS: KT crossings derived from room_data (two-way, one-way, refusals)')


def test_kefka_tower_no_fallbacks():
    """The lane walk and verify() must agree on the gated crossings (both
    two-way once unlocked); a mismatch shows up as vanilla fallbacks
    (18/200 before 2026-09 with verify one-way, 0/200 after)."""
    fallbacks = [s for s in range(20)
                 if randomize_kefka_tower(random.Random(s)) is None]
    assert not fallbacks, f'KT fell back to vanilla for seeds {fallbacks}'
    print('PASS: KT lanes - 0/20 vanilla fallbacks')


if __name__ == '__main__':
    test_dream_maze()
    test_kefka_tower()
    test_kefka_tower_tables_derived()
    test_kefka_tower_no_fallbacks()
    print('\nAll sub-map tests passed.')
