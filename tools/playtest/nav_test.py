"""Phase 2 test: door-step navigation on a real seed.

Boots to control, then teleports to a door on the hub map and steps
through it, asserting the map changed and the camera resynced (not held)
on the far side.

Usage: python3 tools/playtest/nav_test.py <ruin_seed.smc> [shot_dir]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
from tools.playtest import navigate
import data.direction as direction


def main():
    rom = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    h = Harness(rom)

    h.boot_to_game_start()
    navigate.wait_for_control(h)
    start_map = h.map_id
    print(f"control gained on map {start_map:#x} at {h.party_xy}")

    doors = navigate.doors_on_map(start_map)
    print(f"doors on this map: {doors}")
    assert doors, f"no atlas doors on map {start_map:#x} to test with"

    door_id, (dx, dy) = doors[0]
    print(f"stepping into door {door_id} at ({dx},{dy})")
    new_map = navigate.step_through(h, dx, dy, direction.DOWN)

    print(f"transitioned {start_map:#x} -> {new_map:#x}, screen_held={h.screen_held}")
    assert new_map != start_map, "map did not change"
    assert not h.screen_held, "camera left held after a normal transition"

    h.screenshot(os.path.join(outdir, "nav_test_final.png"))
    print("PHASE 2 NAV TEST OK")


if __name__ == "__main__":
    main()
