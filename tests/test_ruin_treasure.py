import collections
import os
import random
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data.ruin_chests import ROOM_CHESTS, KT_CHESTS
from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
from doors.plan.ruination.finalize import finalize_plan, _plan_chests
from event.event_reward import RewardType

ROM_PATH = os.path.join(REPO_ROOT, "ff3.smc")

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string
    return subprocess.run([sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
                          cwd = REPO_ROOT, capture_output = True, text = True, timeout = 60)

def plan(seed, party, minimum):
    # plan.py's retry loop: a plan short of the minimum is re-rolled
    base = random.Random(seed).random()
    for attempt in range(10):
        config = RuinConfig(party, char_range = (6, 6), esper_range = (9, 9), maze = "iso",
                            blitz_characters = ["SABIN"], require_towns = True,
                            require_treasure_count = minimum)
        planner = RuinPlanner(config, random.Random(f"{base}:{attempt}"))
        try:
            planner.grow()
            finalize_plan(planner)
        except RuinPlanError:
            continue
        return planner
    raise AssertionError(f"{seed}: no plan in 10 attempts")

class TestTreasureCount(unittest.TestCase):
    def test_flag(self):
        result = parse_flags("-ruin", "custom", "-rrtc", "90")
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("-rrtc 90", result.stdout)
        result = parse_flags("-ruin", "custom")
        self.assertNotIn("-rrtc", result.stdout)
        for bad in ("-1", str(sum(ROOM_CHESTS.values()) + 1)):
            result = parse_flags("-ruin", "custom", "-rrtc", bad)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("-rrtc:", result.stderr)

    def test_minimum_met(self):
        parties = [["TERRA", "LOCKE", "EDGAR"], ["CELES", "SABIN", "GAU"], ["CYAN", "SHADOW", "UMARO"]]
        for i, party in enumerate(parties):
            with self.subTest(seed = i):
                planner = plan(f"rrtc{i}", party, 100)
                self.assertGreaterEqual(_plan_chests(planner, len(planner.branches)), 100)
                # unclaimed checks in the treasure rooms are held to esper/item
                for name, flags in planner.dead_check_restrictions.items():
                    self.assertFalse(flags & RewardType.CHARACTER, msg = name)

    @unittest.skipUnless(os.path.exists(ROM_PATH), "needs a headerless FF3 (US) 1.0 rom at the repository root")
    def test_chest_table_current(self):
        # data/ruin_chests.py is what tools/ruin_chest_rooms.py generates
        from tools.ruin_chest_rooms import Rom, assign
        rows = assign(Rom(ROM_PATH))
        counts = collections.Counter(rooms[0] for _, rooms, how in rows if how != "kt" and len(rooms) == 1)
        self.assertEqual(dict(counts), ROOM_CHESTS)
        self.assertEqual(sum(1 for _, _, how in rows if how == "kt"), KT_CHESTS)
        self.assertEqual(ROOM_CHESTS["MAPr-SFI"], 23)       # 8 outside (WoR), 15 inside
        self.assertEqual(ROOM_CHESTS["THAr01-ruin"], 6)     # copy_thamasa_chests' 5 outside, 1 inside
        self.assertEqual(ROOM_CHESTS["MAPr-ALB"], 6)        # 2 outside, 4 inside
        self.assertEqual(ROOM_CHESTS["MAPr-TZE"], 8)        # collapsing house

if __name__ == "__main__":
    unittest.main()
