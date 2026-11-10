import collections
import os
import random
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data.ruin_chests import (ROOM_CHESTS, KT_CHESTS, ROOM_CHEST_IDS, KT_ROOM_CHEST_IDS,
                              KT_PENDING_CHEST_IDS, UNREACHABLE_CHEST_IDS)
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
            planner._final_map = finalize_plan(planner)
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
        ids = collections.defaultdict(list)
        kt_ids = collections.defaultdict(list)
        for chest, rooms, how in rows:
            if len(rooms) == 1:
                (kt_ids if how.startswith("kt") else ids)[rooms[0]].append(chest["id"])
        self.assertEqual({room: sorted(c) for room, c in ids.items()}, ROOM_CHEST_IDS)
        self.assertEqual({room: sorted(c) for room, c in kt_ids.items()}, KT_ROOM_CHEST_IDS)
        self.assertEqual(sum(1 for _, _, how in rows if how.startswith("kt")), KT_CHESTS)
        self.assertEqual(ROOM_CHESTS["MAPr-SFI"], 23)       # 8 outside (WoR), 15 inside
        self.assertEqual(ROOM_CHESTS["THAr01-ruin"], 6)     # copy_thamasa_chests' 5 outside, 1 inside
        self.assertEqual(ROOM_CHESTS["MAPr-ALB"], 6)        # 2 outside, 4 inside
        self.assertEqual(ROOM_CHESTS["MAPr-TZE"], 8)        # collapsing house

class TestChestTables(unittest.TestCase):
    def test_room_tables_consistent(self):
        self.assertEqual(ROOM_CHESTS, {room: len(ids) for room, ids in ROOM_CHEST_IDS.items()})
        room_ids = [c for ids in ROOM_CHEST_IDS.values() for c in ids]
        kt_ids = [c for ids in KT_ROOM_CHEST_IDS.values() for c in ids] + list(KT_PENDING_CHEST_IDS)
        self.assertEqual(len(room_ids), len(set(room_ids)))            # one room per chest
        self.assertEqual(len(kt_ids), KT_CHESTS)
        self.assertEqual(len(kt_ids), len(set(kt_ids)))
        self.assertFalse(set(room_ids) & set(kt_ids))
        self.assertFalse(set(UNREACHABLE_CHEST_IDS) & (set(room_ids) | set(kt_ids)))

    def test_vanilla_tower_lanes(self):
        # the vanilla tower: the left party needs both switches (the platform after KTA5a,
        # the broken stairs after KTA8a), the middle and right ones need none
        from doors.plan.ruination.chests import kefka_tower_lanes
        class Vanilla:
            kt_lane_map = None
        lanes = kefka_tower_lanes(Vanilla(), [], [])
        own, crossed = lanes["A"]
        self.assertEqual(own, {"KTA1", "KTA2", "KTA3", "KTA4", "KTA5a"})
        self.assertIn("KTA8b", crossed - own)
        for lane in "BC":
            own, crossed = lanes[lane]
            self.assertEqual(own, crossed)
            self.assertTrue(all(room.startswith("KT" + lane) for room in own))

    def test_seed_chests(self):
        # every reachable chest is in its room's table, every tower chest is in some lane,
        # and the branches hold no more than the hub regions -rrtc counts
        from doors.plan.ruination.chests import seed_chests
        class Plan:
            pass
        parties = [["TERRA", "LOCKE", "EDGAR"], ["CELES", "SABIN", "GAU"], ["CYAN", "SHADOW", "UMARO"]]
        for i, party in enumerate(parties):
            with self.subTest(seed = i):
                planner = plan(f"chests{i}", party, 0)
                door_plan = Plan()
                door_plan.door_pairs, door_plan.oneways = planner._final_map
                door_plan.ruination = Plan()
                door_plan.ruination.planner = planner
                found = seed_chests(door_plan)
                total = 0
                for bid, rooms in found["branches"].items():
                    for room, ids in rooms.items():
                        self.assertTrue(set(ids) <= set(ROOM_CHEST_IDS[room]), msg = room)
                        total += len(ids)
                self.assertLessEqual(total, _plan_chests(planner, len(planner.branches)))
                self.assertGreater(total, 0)
                tower = set()
                for part in ("kefka_tower", "kefka_tower_after_switches"):
                    for rooms in found[part].values():
                        tower.update(c for ids in rooms.values() for c in ids)
                tower.update(c for ids in found["kefka_tower_back"].values() for c in ids)
                self.assertEqual(tower, {c for ids in KT_ROOM_CHEST_IDS.values() for c in ids})
                self.assertEqual(found["kefka_tower_back"], {"KT-back": [216]})     # the meme chest

if __name__ == "__main__":
    unittest.main()
