import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# a random natural magic learner should be someone who can cast in battle whenever the
# commands leave anyone who can, and any character at all when they do not
LEARNER_CHOICE = """
import sys
sys.argv = ["wc.py", "-i", "rom.smc", "-nm1", "random"]
import args

from constants.commands import name_id
from data.characters import Characters
from data.natural_magic import NaturalMagic

FIGHT, ITEM, MAGIC, X_MAGIC = name_id["Fight"], name_id["Item"], name_id["Magic"], name_id["X Magic"]
BLITZ, NONE = name_id["Blitz"], name_id["None"]
POSSIBLE = list(range(Characters.CHARACTER_COUNT - 2))

class FakeCharacter:
    def __init__(self, id, commands):
        self.id = id
        self.commands = commands

class FakeCharacters:
    get_characters_with_command = Characters.get_characters_with_command
    def __init__(self, characters):
        self.characters = characters

def learner_picker(magic_users, x_magic_users):
    characters = []
    for id in range(Characters.CHARACTER_COUNT):
        if id in magic_users:
            commands = [FIGHT, BLITZ, MAGIC, ITEM]
        elif id in x_magic_users:
            commands = [FIGHT, X_MAGIC, BLITZ, ITEM]
        else:
            commands = [FIGHT, BLITZ, NONE, ITEM]
        characters.append(FakeCharacter(id, commands))

    natural_magic = object.__new__(NaturalMagic)
    natural_magic.characters = FakeCharacters(characters)
    return natural_magic

# only celes and mog have a magic command
picker = learner_picker(magic_users = [Characters.CELES, Characters.MOG], x_magic_users = [])
picked = {picker.random_learner(POSSIBLE) for _ in range(400)}
assert picked == {Characters.CELES, Characters.MOG}, picked

# x magic counts as being able to cast
picker = learner_picker(magic_users = [Characters.CELES], x_magic_users = [Characters.GAU])
picked = {picker.random_learner(POSSIBLE) for _ in range(400)}
assert picked == {Characters.CELES, Characters.GAU}, picked

# a magic user outside the possible learners must not be picked
picker = learner_picker(magic_users = [Characters.CELES, Characters.GOGO], x_magic_users = [])
picked = {picker.random_learner(POSSIBLE) for _ in range(400)}
assert picked == {Characters.CELES}, picked

# nobody can cast: fall back to any possible learner rather than failing
picker = learner_picker(magic_users = [], x_magic_users = [])
picked = {picker.random_learner(POSSIBLE) for _ in range(2000)}
assert picked == set(POSSIBLE), sorted(picked)

print("ok")
"""

class TestNaturalMagicLearners(unittest.TestCase):
    def test_random_learner_prefers_magic_users(self):
        result = subprocess.run(
            [sys.executable, "-c", LEARNER_CHOICE],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 120,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

if __name__ == "__main__":
    unittest.main()
