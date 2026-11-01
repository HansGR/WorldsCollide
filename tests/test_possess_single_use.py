import itertools
import json
import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string
    return subprocess.run(
        [sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
        cwd = REPO_ROOT,
        capture_output = True,
        text = True,
        timeout = 60,
    )

class TestPossessSingleUseFlag(unittest.TestCase):
    def test_flag(self):
        result = parse_flags("-psu")
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("-psu", result.stdout.split())

    def test_off_by_default(self):
        result = parse_flags()
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertNotIn("-psu", result.stdout.split())

# the -rc pre-placement is event code generated at build time that decides at run time which
# required characters are available; generating it needs the rom's free space, so this runs the
# generator against a headerless FF3 (US) 1.0 rom at the repository root and walks the
# generated instructions for every combination of available required characters. skipped when
# there is no rom (CI has none)
ROM_PATH = os.path.join(REPO_ROOT, "ff3.smc")

PLACEMENT_SCRIPT = """
import itertools, json, sys
sys.argv = ["wc.py", "-i", sys.argv[1], "-psu", "-rc", "terra", "locke", "edgar", "sabin"]
import args
from memory.memory import Memory
Memory()
import instruction.field.required_characters as required_characters
# (the instruction.field package rebinds its "instructions" attribute to y_npc's, so look the
#  module up directly)
field = sys.modules["instruction.field.instructions"]
import data.event_bit as event_bit
from utils.flatten import flatten

def walk(src, available):
    src = flatten(src)
    labels = {item: index for index, item in enumerate(src) if isinstance(item, str)}
    placed, index = {}, 0
    while index < len(src):
        item = src[index]
        index += 1
        if isinstance(item, field.AddCharacterToParty):
            placed[item.args[0]] = item.args[1]
        elif isinstance(item, field.Branch):
            index = labels[item.destinations[0]]
        elif isinstance(item, field.BranchIfEventBitClear):
            character = item.event_bit - event_bit.character_available(0)
            if character not in available:
                index = labels[item.destinations[0]]
    return placed

required = args.required_character_ids
result = {}
for count in range(len(required) + 1):
    for available in itertools.combinations(required, count):
        key = ",".join(map(str, available))
        result[key] = {
            "one": walk(required_characters.one_party_placement(), available),
            "kt_normal": walk(required_characters.three_party_placement(skip = False), available),
            "kt_skip": walk(required_characters.three_party_placement(skip = True), available),
            "split": walk(required_characters._available_placement(
                list(reversed(required)), [2] + [1] * (len(required) - 1), "SPLIT"), available),
        }
print(json.dumps({"required": required, "result": result}))
"""

@unittest.skipUnless(os.path.isfile(ROM_PATH), "needs ff3.smc at the repository root")
class TestRequiredCharacterPlacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run = subprocess.run(
            [sys.executable, "-c", PLACEMENT_SCRIPT, ROM_PATH],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 120,
        )
        if run.returncode != 0:
            raise AssertionError(run.stderr)
        output = json.loads(run.stdout.strip().splitlines()[-1])
        cls.required = output["required"]
        cls.result = output["result"]

    def placements(self, kind):
        for key, placements in self.result.items():
            available = [int(character) for character in key.split(",") if character]
            # json object keys are strings
            yield available, {int(character): party for character, party in placements[kind].items()}

    def test_one_party_places_only_available(self):
        for available, placed in self.placements("one"):
            self.assertEqual(placed, {character: 1 for character in available}, msg = available)

    def test_kefka_tower_nth_available_takes_nth_party(self):
        for kind, parties in (("kt_normal", [3, 1, 2, 3]), ("kt_skip", [2, 3, 1, 2])):
            for available, placed in self.placements(kind):
                expected = {character: parties[index] for index, character in enumerate(available)}
                self.assertEqual(placed, expected, msg = (kind, available))
                # every party a required character can fill is filled before any doubles up
                self.assertEqual(len(set(placed.values())), min(len(available), 3), msg = (kind, available))

    def test_split_puts_last_available_in_party_two(self):
        for available, placed in self.placements("split"):
            expected = {character: 1 for character in available}
            if available:
                expected[available[-1]] = 2
            self.assertEqual(placed, expected, msg = available)

if __name__ == "__main__":
    unittest.main()
