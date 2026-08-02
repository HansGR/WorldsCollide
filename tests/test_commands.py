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

if __name__ == "__main__":
    unittest.main()
