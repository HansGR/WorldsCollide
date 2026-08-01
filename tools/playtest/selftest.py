"""Phase 1 self-test: exercise the Harness API on a -ruin seed.

Boots to game start, then checks every accessor against expected
ruination-start state, including the -oss silent objective effects.

The seed must be built with the explicit start-bonus objectives (they are
no longer part of the default -ruin flagset):

    wc.py -i vanilla.smc -o seed.smc -ruin -oc 74.100.100.0.0 -od 55.0.0

Usage: python3 tools/playtest/selftest.py <ruin_seed.smc> [shot_dir]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
import data.event_bit as event_bit

ESPER_GATE_MAPID = 0x0da


def main():
    rom = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    h = Harness(rom)

    frames = h.boot_to_game_start()
    print(f"booted to game start in {frames} frames")

    # Map: ruination begins in the Esper Gate map
    assert h.map_id == ESPER_GATE_MAPID, f"map {h.map_id:#x} != Esper Gate"
    print(f"map_id = {h.map_id:#x} (Esper Gate) OK")

    # Let the start script's objective check run (it fires a few hundred
    # frames into the cinematic).  The default -ruin flagset provides
    # objectives A and B, so the explicit -oc/-od bonuses (MaxHP All +100,
    # Full Heal) land in OBJECTIVE bit slots 2 and 3.
    OBJ_MAXHP = getattr(event_bit, "OBJECTIVE2")
    OBJ_HEAL = getattr(event_bit, "OBJECTIVE3")
    h.run_until(lambda h: h.event_bit(OBJ_MAXHP), timeout=30000, step=10)
    print("objective (MaxHP All) fired OK")
    assert h.event_bit(OBJ_HEAL), "objective (Full Heal) should fire together"
    print("objective (Full Heal) fired OK")

    # -oss effect: +100 max HP everyone; current == max (full heal) for the
    # party members (Full Heal is ApplyToParty; harness slots are character
    # data blocks, so check the actual party membership bits).
    mhp = h.max_hp(0)
    print(f"character 0: max HP = {mhp}")
    assert mhp >= 100, f"max HP {mhp} did not receive +100 bonus"
    current_party = h.core.read_u8(0x1a6d)
    members = [c for c in range(14)
               if h.core.read_u8(0x1850 + c) & current_party]
    assert members, "no characters in the current party"
    for c in members:
        chp, cmhp = h.cur_hp(c), h.max_hp(c)
        assert chp == cmhp, f"char {c}: cur {chp} != max {cmhp} (no full heal)"
    print(f"party characters {members} at full HP OK")

    # Party position accessor + poke round-trip
    x, y = h.party_xy
    print(f"party_xy = ({x}, {y})")
    h.set_party_xy(x + 1, y)
    assert h.party_xy == (x + 1, y), "party_xy poke round-trip failed"
    h.set_party_xy(x, y)
    print("party_xy read/poke OK")

    # Screen-hold accessor is readable (value asserted in the camera test)
    print(f"screen_held = {h.screen_held}")

    # Event word + GP accessors are readable
    print(f"gp = {h.gp}")

    h.screenshot(os.path.join(outdir, "selftest_final.png"))
    print("PHASE 1 SELFTEST OK")


if __name__ == "__main__":
    main()
