"""Atlas regression test: the atlas must stay in sync with everything.

Checks, without a ROM:
  1. compile_atlas's full consistency check passes (partner parity with
     data/map_exit_extra.exit_data, honest overrides, reciprocity).
  2. doors/atlas/compiled.py on disk matches what the compiler would emit
     now (catches hand-edits and forgotten re-emits after curation edits).
  3. The doors.atlas API imports ROM-free and answers basic queries.

Run: python3 tests/doors/test_atlas.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))


def main():
    import compile_atlas

    records = compile_atlas.load_exit_records()

    # 1. Full consistency check.
    n_fail = compile_atlas.check(records)
    assert n_fail == 0, f'{n_fail} atlas consistency failure(s)'
    print('PASS: atlas consistency check')

    # 2. compiled.py in sync with a fresh emit.
    extended, final, _ = compile_atlas.build_extended_partners(records)
    traps, event_doors = compile_atlas.load_oneway_records()
    from doors.atlas import compiled
    assert compiled.EXIT_RECORDS == records, 'compiled.EXIT_RECORDS out of date - re-run tools/compile_atlas.py'
    assert compiled.PARTNERS == extended, 'compiled.PARTNERS out of date - re-run tools/compile_atlas.py'
    assert compiled.TRAP_RECORDS == traps, 'compiled.TRAP_RECORDS out of date - re-run tools/compile_atlas.py'
    assert compiled.EVENT_DOOR_RECORDS == event_doors, 'compiled.EVENT_DOOR_RECORDS out of date - re-run tools/compile_atlas.py'
    print('PASS: compiled.py in sync with compiler output')

    # 3. API smoke test.
    import doors.atlas as atlas
    assert atlas.vanilla_partner(4) is not None          # Narshe world tile
    assert atlas.exit_map(360) is not None               # Sabin's house door
    assert atlas.vanilla_partner(884) is None            # unused (p1 finding)
    assert atlas.exit_position(0) is not None
    assert atlas.description(4)                          # exit_data delegate
    assert atlas.trap_record(2001) is not None           # Umaro cave trapdoor
    assert atlas.event_door_record(1556) is not None     # Floating Continent entry
    assert atlas.vanilla_partner(1546) == 78             # event-door layer partner
    assert atlas.vanilla_partner(4658) is not None       # logical-WoR layer partner
    print('PASS: doors.atlas API')

    print('\nAll atlas tests passed.')


if __name__ == '__main__':
    main()
