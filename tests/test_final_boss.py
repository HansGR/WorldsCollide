import unittest

import final_boss
from final_boss.final_boss import FinalBoss

class TestFinalBosses(unittest.TestCase):
    def test_kefka_is_the_plain_final_boss(self):
        self.assertEqual(final_boss.NAMES[0], final_boss.KEFKA)
        self.assertIs(final_boss._FINAL_BOSSES[final_boss.KEFKA](), FinalBoss)
        self.assertEqual(FinalBoss.LEVELS, 0)

    def test_names(self):
        # the names are -fb values: lower case, and none is the value for a random one
        self.assertEqual(len(set(final_boss.NAMES)), len(final_boss.NAMES))
        self.assertNotIn(final_boss.RANDOM, final_boss.NAMES)
        self.assertTrue(all(name == name.lower() and " " not in name for name in final_boss.NAMES))

    def test_every_final_boss_is_one(self):
        for name, load in final_boss._FINAL_BOSSES.items():
            with self.subTest(name = name):
                final_boss_class = load()
                self.assertTrue(issubclass(final_boss_class, FinalBoss))
                self.assertEqual(final_boss_class.ENEMY, FinalBoss.ENEMY)
                self.assertTrue(0 < len(final_boss_class.NAME) <= 10)   # an enemy's name
                self.assertGreaterEqual(final_boss_class.LEVELS, 0)

if __name__ == "__main__":
    unittest.main()
