import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string,
    # which exercises the whole -com interface without needing a rom
    return subprocess.run(
        [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
        cwd = REPO_ROOT,
        capture_output = True,
        text = True,
        timeout = 60,
    )

# drafts 24 skill slots out of a pool of 5 commands, which forces repeated refills and,
# often, a refill triggered by a leftover the drafting character already has
DRAFT_INVARIANTS = """
import sys, types, collections
sys.argv = ["wc.py", "-i", "rom.smc", "-com", "fru", "0.0.0"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

MORPH = name_id["Morph"]
POOL = [MORPH] + list(range(100, 104))
CHARACTERS, SLOTS = list(range(6)), 4

for trial in range(2000):
    skills = Commands([]).draft_skills(CHARACTERS, {c : SLOTS for c in CHARACTERS}, list(POOL))
    for character in CHARACTERS:
        drafted = skills[character]
        assert len(drafted) == SLOTS, f"dropped a slot: {drafted}"
        assert len(set(drafted)) == SLOTS, f"duplicate command: {drafted}"
        assert all(command in POOL for command in drafted), drafted
    assert sum(MORPH in skills[c] for c in CHARACTERS) <= 1, "morph drafted more than once"
print("ok")
"""

# behavioral invariants for the -com pr/pru probability modes, run against fake
# characters (no rom needed). declared: fight/item/magic/possess at 100%, blitz
# at 0%; rage excluded via -rec. every character must therefore hold exactly
# fight/possess/magic/item in menu order, with nothing backfilled.
PR_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-com", "pr", "0.1.2.28.10", "100.100.100.100.0", "-rec", "16"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        assert cmds == [0, 28, 2, 1], f"menu order broken: {cmds}"
print("ok")
"""

# six declarations at equal likelihood: each character rolls exactly four of the
# six (the group cap), never a -rec excluded command, and never a duplicate.
PR_CAP_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-com", "pru", "0.1.2.27.28.29", "50.50.50.50.50.50", "-rec", "16"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

DECLARED = {0, 1, 2, 27, 28, 29}
NONE = name_id["None"]
RAGE = name_id["Rage"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

seen_over_four = False
for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(cmds) == 4, cmds
        assert len(set(real)) == len(real), f"duplicate command: {cmds}"
        assert RAGE not in real, f"excluded command dealt: {cmds}"
        declared_held = [x for x in real if x in DECLARED]
        assert len(declared_held) <= 4, f"cap exceeded: {cmds}"
print("ok")
"""

# a declared None (97) claims a slot and stays empty: with none at 100% and
# three 100% commands, every character has exactly one empty slot, no backfill.
PR_NONE_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-com", "pr", "5.7.13.97", "100.100.100.100"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert sorted(real) == [5, 7, 13], f"expected steal/swdtech/sketch + empty: {cmds}"
print("ok")
"""

# a declared morph is dealt only by its roll: at 50% morph plus unique backfill,
# no character may ever hold two morphs and backfill must never add one.
PR_MORPH_INVARIANTS = """
import sys, types
sys.argv = ["wc.py", "-i", "rom.smc", "-com", "pru", "3", "50"]
import args
sys.modules["objectives"] = types.ModuleType("objectives")
sys.modules["objectives"].suplex_train_condition_exists = False

from constants.commands import name_id
from data.commands import Commands

MORPH = name_id["Morph"]
NONE = name_id["None"]

class FakeChar:
    def __init__(self):
        self.commands = [0, 0, 0, 0]

for trial in range(300):
    chars = [FakeChar() for _ in range(0x20)]
    c = Commands(chars)
    c.mod_probability_random_commands()
    for i in c.full_random_characters():
        cmds = chars[i].commands
        real = [x for x in cmds if x != NONE]
        assert len(real) == 4, f"pru backfill left a hole: {cmds}"
        assert cmds.count(MORPH) <= 1, f"double morph: {cmds}"
print("ok")
"""


class TestCommandsFlag(unittest.TestCase):
    def assert_accepted(self, *flags, expected = None):
        result = parse_flags(*flags)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        if expected is not None:
            self.assertIn(expected, result.stdout)
        return result.stdout

    def assert_rejected(self, *flags, expected = None):
        result = parse_flags(*flags)
        self.assertNotEqual(result.returncode, 0, msg = result.stdout)
        if expected is not None:
            self.assertIn(expected, result.stderr)

    def test_character_command_ids(self):
        self.assert_accepted("-com", "03050708091011121315191617", expected = "-com 03050708091011121315191617")
        self.assert_accepted("-com", "99999999999999999999999999", expected = "-com 99999999999999999999999999")

    def test_full_random_modes(self):
        self.assert_accepted("-com", "fr", "10.50.90", expected = "-com fr 10.50.90")
        self.assert_accepted("-com", "fru", "0.0.0", expected = "-com fru 0.0.0")
        # a single quoted value is equivalent to two separate ones
        self.assert_accepted("-com", "fru 100.100.100", expected = "-com fru 100.100.100")

    def test_no_commands_flag(self):
        self.assertNotIn("-com", self.assert_accepted())
        self.assertNotIn("-com", self.assert_accepted("-com"))

    def test_unique_draft_refills(self):
        result = subprocess.run(
            [sys.executable, "-c", DRAFT_INVARIANTS],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 120,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

    def test_invalid_values_rejected(self):
        self.assert_rejected("-com", "0305070809", expected = "must be 26 digits")
        self.assert_rejected("-com", "03050708091011121315191650", expected = "not a valid command id")
        self.assert_rejected("-com", "fr", expected = "percent chance value")
        self.assert_rejected("-com", "fr", "10.50", expected = "3 percent chances")
        self.assert_rejected("-com", "fr", "10.50.101", expected = "must be between 0 and 100")
        self.assert_rejected("-com", "fru", "10.50.abc", expected = "not a valid Item percent chance")

    def test_probability_modes(self):
        # ids are canonicalized to two digits; percents kept as given
        self.assert_accepted("-com", "pr", "0.1.2.28", "50.50.50.100",
                             expected = "-com pr 00.01.02.28 50.50.50.100")
        self.assert_accepted("-com", "pru", "0.1.2.27.28.29", "50.50.50.50.50.50",
                             expected = "-com pru 00.01.02.27.28.29 50.50.50.50.50.50")
        # 97 declares a chance at an empty slot
        self.assert_accepted("-com", "pr", "97.10", "50.100", expected = "-com pr 97.10 50.100")
        # a single quoted value is equivalent to separate ones
        self.assert_accepted("-com", "pr 3 100", expected = "-com pr 03 100")

    def test_probability_invalid_rejected(self):
        self.assert_rejected("-com", "pr", "0.1.2", expected = "requires dot-separated command ids")
        self.assert_rejected("-com", "pr", "0.1.2", "50.50", expected = "3 command ids but 2 percent chances")
        self.assert_rejected("-com", "pr", "0.25", "50.50", expected = "not a valid probability command id")  # Summon
        self.assert_rejected("-com", "pr", "0.0", "50.50", expected = "duplicate probability command id")
        self.assert_rejected("-com", "pr", "0.abc", "50.50", expected = "not a valid command id")
        self.assert_rejected("-com", "pr", "0.1", "50.101", expected = "must be between 0 and 100")
        # a command cannot both have a probability and be excluded by -rec
        self.assert_rejected("-com", "pr", "0.16", "50.50", "-rec", "16",
                             expected = "both given a probability and excluded by -rec")

    def test_probability_invariants(self):
        for name, script in (("pr", PR_INVARIANTS), ("cap", PR_CAP_INVARIANTS),
                             ("none", PR_NONE_INVARIANTS), ("morph", PR_MORPH_INVARIANTS)):
            with self.subTest(name):
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd = REPO_ROOT,
                    capture_output = True,
                    text = True,
                    timeout = 120,
                )
                self.assertEqual(result.returncode, 0, msg = result.stderr)
                self.assertIn("ok", result.stdout)

    def test_random_exclude_dot_list(self):
        # arbitrary-length dot-separated exclusions, re-emitted canonically
        self.assert_accepted("-rec", "28.27", expected = "-rec 28.27")
        self.assert_accepted("-rec", "05.07.10.16.13", expected = "-rec 05.07.10.16.13")
        # single-digit input normalizes to two-digit canonical form
        self.assert_accepted("-rec", "5.7", expected = "-rec 05.07")
        # the none id (97) is dropped from the canonical string
        self.assertNotIn("-rec", self.assert_accepted("-rec", "97"))

    def test_random_exclude_legacy_wrappers(self):
        # legacy -recN flags still parse and fold into the canonical -rec form
        self.assert_accepted("-rec1", "28", "-rec2", "27", expected = "-rec 28.27")
        self.assert_accepted("-rec3", "10", expected = "-rec 10")
        # mixed usage: -rec values first, then the legacy flags in order
        self.assert_accepted("-rec", "05", "-rec1", "28", expected = "-rec 05.28")

    def test_random_exclude_invalid_rejected(self):
        self.assert_rejected("-rec", "28.abc", expected = "not a valid command id")
        self.assert_rejected("-rec", "01", expected = "not an excludable command id")  # Item
        # excluding the whole random pool is rejected (would empty every draw)
        from constants.commands import RANDOM_POSSIBLE_COMMANDS, name_id
        everything = ".".join(f"{name_id[name]:02}" for name in RANDOM_POSSIBLE_COMMANDS)
        self.assert_rejected("-rec", everything, expected = "cannot exclude every")

if __name__ == "__main__":
    unittest.main()
