import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from doors.plan.ruination.maptest import maptest_doors

# ZOZb08 (Zozo tower outside, 10F/12F/14F) has doors [614, 615, 619]

class TestMaptestDoors(unittest.TestCase):
    def test_defaults(self):
        # first door in; the next door out when the room chains onward
        self.assertEqual(maptest_doors("ZOZb08", chained = True), ("ZOZb08", 614, 615))
        self.assertEqual(maptest_doors("ZOZb08", chained = False), ("ZOZb08", 614, None))

    def test_entry_door(self):
        self.assertEqual(maptest_doors("ZOZb08@615", chained = False), ("ZOZb08", 615, None))
        # out defaults to the first door that isn't the entry
        self.assertEqual(maptest_doors("ZOZb08@615", chained = True), ("ZOZb08", 615, 614))

    def test_entry_and_exit_doors(self):
        self.assertEqual(maptest_doors("ZOZb08@615/619", chained = True), ("ZOZb08", 615, 619))
        self.assertEqual(maptest_doors("ZOZb08/619", chained = True), ("ZOZb08", 614, 619))

    def test_errors(self):
        bad = [
            ("NOPE", False),                # unknown room
            ("ZOZb08@600", False),          # not one of the room's doors
            ("ZOZb08@abc", False),          # not a number
            ("ZOZb08@615/615", True),       # in and out the same
            ("ZOZb08@615/619", False),      # the last room takes no out door
            ("HUB52-ruin", True),           # one door: cannot chain onward
        ]
        for spec, chained in bad:
            with self.subTest(spec = spec, chained = chained):
                with self.assertRaises(ValueError):
                    maptest_doors(spec, chained)

if __name__ == "__main__":
    unittest.main()
