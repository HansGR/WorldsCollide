import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Fanatic's Tower (battle menus allow Magic/Item only: someone must be able to cast, or have
# Umaro) and the Veldt (the reward is fed Dried Meat with Item) need a battle command. With the
# probability command modes a character there could be unobtainable. This rolls seeds with
# scarce Magic/Item and checks every character reward at those checks: with -cg, a character
# assigned before it has the command; in open world, another character in the game has it.
# Rolling seeds needs a headerless FF3 (US) 1.0 rom at the repository root; skipped when
# there is none (CI has none).
ROM_PATH = os.path.join(REPO_ROOT, "ff3.smc")

SCRIPT = """
import sys
sys.argv = ["wc.py", "-i", sys.argv[1], "-nro"] + sys.argv[2:]
import args
from memory.memory import Memory
memory = Memory()

import data.characters as characters_module
order = []
set_path = characters_module.Characters.set_character_path
def record_path(self, character, required):
    order.append(character)
    return set_path(self, character, required)
characters_module.Characters.set_character_path = record_path

import event.events as events_module
captured = {}
gating, open_world = events_module.Events.character_gating_mod, events_module.Events.open_world_mod
def record_gating(self, events, name_event, *more):
    captured["start"] = [reward.id for reward in name_event["Start"].rewards]
    gating(self, events, name_event, *more)
    captured["events"] = events
def record_open_world(self, events):
    open_world(self, events)
    captured["events"] = events
events_module.Events.character_gating_mod = record_gating
events_module.Events.open_world_mod = record_open_world

from data.data import Data
data = Data(memory.rom, args)
events_module.Events(memory.rom, args, data)

from event.event_reward import RewardType
from constants.entities import CHARACTER_COUNT
characters = data.characters
casters = set(characters.get_characters_with_command("Magic")) | set(characters.get_characters_with_command("X Magic"))
item_users = set(characters.get_characters_with_command("Item"))
rules = {
    "Fanatic's Tower": lambda chars: any(c in casters for c in chars) or characters.UMARO in chars,
    "Veldt": lambda chars: any(c in item_users for c in chars),
}
events = {event.name(): event for event in captured["events"]}
for name, rule in rules.items():
    for reward in events[name].rewards:
        if reward.type != RewardType.CHARACTER:
            continue
        if "start" in captured:
            before = captured["start"] + order[:order.index(reward.id)]
        else:
            before = [other.id for event in captured["events"] for other in event.rewards
                      if other.type == RewardType.CHARACTER and other.id != reward.id]
        allowed_somewhere = any(rule([c]) for c in range(CHARACTER_COUNT) if c != reward.id)
        # -cg may fall back to the check when nothing else is unlocked; never when the
        # command exists nowhere else in the game
        print(f"{name} {'ok' if rule(before) or not allowed_somewhere else 'VIOLATION'}")
print("done")
"""

@unittest.skipUnless(os.path.isfile(ROM_PATH), "needs ff3.smc at the repository root")
class TestCommandGatedChecks(unittest.TestCase):
    def roll(self, seed, *flags):
        # the seed's log goes next to the output; keep it out of the repository
        import tempfile
        output = os.path.join(tempfile.mkdtemp(), "seed.smc")
        result = subprocess.run(
            [sys.executable, "-c", SCRIPT, ROM_PATH, "-o", output, "-s", seed, *flags],
            cwd = REPO_ROOT,
            capture_output = True,
            text = True,
            timeout = 300,
        )
        self.assertEqual(result.returncode, 0, msg = result.stderr[-2000:])
        self.assertIn("done", result.stdout)
        return result.stdout

    def test_character_gating(self):
        for seed in ("gate1", "gate3", "gate5"):
            output = self.roll(seed, "-cg", "-comfr", "30.15.15")
            self.assertNotIn("VIOLATION", output, msg = (seed, output))

    def test_open_world(self):
        for seed in ("gate2", "gate4", "gate6"):
            output = self.roll(seed, "-comfr", "30.10.10")
            self.assertNotIn("VIOLATION", output, msg = (seed, output))

if __name__ == "__main__":
    unittest.main()
