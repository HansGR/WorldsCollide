import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from data import ruin_constants as RC

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string
    return subprocess.run([sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
                          cwd = REPO_ROOT, capture_output = True, text = True, timeout = 60)

class TestDeadCheckChance(unittest.TestCase):
    def test_standard_rate(self):
        # vanilla WC's item share: 1 - (14 - start chars + 27 - start espers) / 62
        self.assertAlmostEqual(RC.standard_dead_check_chance(3), 1 - 38 / 62)
        self.assertAlmostEqual(RC.standard_dead_check_chance(4), 1 - 37 / 62)
        self.assertAlmostEqual(RC.standard_dead_check_chance(3, 2), 1 - 36 / 62)
        self.assertEqual(RC.standard_dead_check_chance(14, 27), 1.0)

    def test_flag(self):
        for value, written in (("0", "-rdcc 0"), ("25", "-rdcc 25"), ("12.5", "-rdcc 12.5")):
            result = parse_flags("-ruin", "custom", "-rdcc", value)
            self.assertEqual(result.returncode, 0, msg = result.stderr)
            self.assertIn(written, result.stdout)
        result = parse_flags("-ruin", "custom")
        self.assertNotIn("-rdcc", result.stdout)
        for bad in ("-1", "101"):
            result = parse_flags("-ruin", "custom", "-rdcc", bad)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be a percent from 0 to 100", result.stderr)

# every planner reward type must be one the event's slot accepts, or the planner
# can bind a kind the event cannot give (e.g. an item at a character/esper-only
# check); needs a headerless FF3 (US) 1.0 rom at the repository root
ROM_PATH = os.path.join(REPO_ROOT, "ff3.smc")
SLOT_TYPES = """
import sys, io, contextlib
sys.argv = ["wc.py", "-i", "ff3.smc", "-o", sys.argv[1], "-s", "1", "-ruin"]
with contextlib.redirect_stdout(io.StringIO()):
    import args
    from memory.memory import Memory
    memory = Memory()
from event.events import Events
from event.ruination_bind import build_name_to_slot
from data import ruin_constants as RC
found = {}
orig = Events.ruination_mod
def capture(self, events, name_event):
    orig(self, events, name_event)
    planner = self.maps.doors.plan.ruination.planner
    slots = build_name_to_slot(events)
    for rewards in planner.config.room_reward.values():
        for name, flags in rewards.items():
            if name in slots:
                found[name] = (flags.value & 14, slots[name].possible_types.value & 14)
Events.ruination_mod = capture
with contextlib.redirect_stdout(io.StringIO()):
    from data.data import Data
    Events(memory.rom, args, Data(memory.rom, args))
bad = {name: v for name, v in found.items() if v[0] & ~v[1]}
sys.__stdout__.write(f"checked {len(found)} bad {bad}\\n")
"""

@unittest.skipUnless(os.path.isfile(ROM_PATH), "needs ff3.smc at the repository root")
class TestRuinRewardTypes(unittest.TestCase):
    def test_planner_types_fit_event_slots(self):
        import tempfile
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run([sys.executable, "-c", SLOT_TYPES, os.path.join(out, "seed.smc")],
                                    cwd = REPO_ROOT, capture_output = True, text = True, timeout = 300)
        self.assertEqual(result.returncode, 0, msg = result.stderr[-2000:])
        self.assertIn("bad {}", result.stdout)
        self.assertNotIn("checked 0 ", result.stdout)

if __name__ == "__main__":
    unittest.main()
