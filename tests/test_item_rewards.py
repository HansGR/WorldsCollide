import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from constants.items import name_id, good_items, stronger_items, premium_items, ruin_items

class TestItemRewardPresets(unittest.TestCase):
    def test_preset_names_resolve(self):
        # -ir presets are looked up by exact name; a typo would be a KeyError at generation
        for preset in (good_items, stronger_items, premium_items, ruin_items):
            for name in preset:
                with self.subTest(name = name):
                    self.assertIn(name, name_id)

    def test_ruin_preset(self):
        self.assertEqual(len(ruin_items), 21)
        self.assertEqual(len(set(ruin_items)), len(ruin_items))
        for name in ("Hero Ring", "Megalixir", "Economizer", "Aegis Shld"):
            self.assertIn(name, ruin_items)

if __name__ == "__main__":
    unittest.main()
