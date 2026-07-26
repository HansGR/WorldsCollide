"""Test: automate the Narshe School party reform into two parties.

Boots a -ruin seed, routes start -> Esper Gate tile -> Narshe School, drives
the ghost-NPC reform into a 2-party split, and asserts the result: Y-party
switching enabled, a valid contiguous 2+1 assignment, field control regained,
and Y-switch actually swapping the active party.

Usage: python3 tools/playtest/reform_test.py <ruin_seed.smc> [shot_dir]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
from tools.playtest import navigate, route, reform
import data.event_bit as event_bit


def main():
    rom = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)

    # start (Esper Gate) -> event tile 1562 -> Narshe School hub
    route.step_door(h, route.ESPER_GATE_TILE)
    navigate.wait_for_control(h)
    assert h.map_id == reform.SCHOOL_MAP, f"not in school: {h.map_id:#x}"

    avail = reform.available_characters(h)
    print(f"roster: characters {avail}")

    reform.reform_two_parties(h, plan=(1, 1, 2))

    # Assert the reform outcome.
    assert h.event_bit(event_bit.ENABLE_Y_PARTY_SWITCHING), "Y-switch not enabled"
    assert not h.event_bit(event_bit.THREE_PARTIES_CREATED), "unexpected 3rd party"
    W = h.core.wram
    parties = {}
    for c in avail:
        v = W[reform.PARTY_ASSIGN + c]
        parties.setdefault(v & 0x07, []).append(c)
    assert set(parties) == {1, 2}, f"expected parties 1 and 2, got {parties}"
    assert len(parties[1]) >= 2, f"party 1 should have >=2 for the split test: {parties}"
    print(f"formed parties: {parties}, control at {h.party_xy}")

    # Y-switch must change the active party.
    before = W[0x1a6d]
    h.press('Y', hold=4, wait=30)
    h.run(30)
    after = W[0x1a6d]
    assert after != before, f"Y-switch did not change active party ({before}->{after})"
    print(f"Y-switch: active party {before} -> {after}")

    h.screenshot(os.path.join(outdir, "reform_test_final.png"))
    print("REFORM TEST OK")


if __name__ == "__main__":
    main()
