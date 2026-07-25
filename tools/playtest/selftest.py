"""Phase 1 self-test: exercise the Harness API on a -ruin seed.

Boots to game start, then checks every accessor against expected
ruination-start state, including the -oss silent objective effects.

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
    # frames into the cinematic).  NOTE the ruination reindex: the -oa
    # objective (result 2, Unlock Final Kefka) is filtered out of
    # args.objectives in ruination mode before .id assignment, so the
    # remaining objectives shift down one slot -- the -od/-oe bonuses
    # (MaxHP All +100, Full Heal) land in OBJECTIVE bit slots 2 and 3,
    # not 3 and 4.
    OBJ_MAXHP = getattr(event_bit, "OBJECTIVE2")
    OBJ_HEAL = getattr(event_bit, "OBJECTIVE3")
    h.run_until(lambda h: h.event_bit(OBJ_MAXHP), timeout=30000, step=10)
    print("objective (MaxHP All) fired OK")
    assert h.event_bit(OBJ_HEAL), "objective (Full Heal) should fire together"
    print("objective (Full Heal) fired OK")

    # -oss effect: +100 max HP and current == max (full heal), no dialog box.
    mhp = h.max_hp(0)
    chp = h.cur_hp(0)
    print(f"slot 0: max HP = {mhp}, cur HP = {chp}")
    assert mhp >= 100, f"max HP {mhp} did not receive +100 bonus"
    assert chp == mhp, f"cur HP {chp} != max HP {mhp} (full heal not applied)"

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
