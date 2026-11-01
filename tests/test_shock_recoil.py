import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_flags(*flags):
    # args/arguments.py parses the given flags and prints the canonical flag string
    return subprocess.run([sys.executable, os.path.join("args", "arguments.py"), "-i", "rom.smc", *flags],
                          cwd = REPO_ROOT, capture_output = True, text = True, timeout = 60)

class TestShockRecoilFlag(unittest.TestCase):
    def assert_flag(self, flags, expected):
        result = parse_flags(*flags)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        tokens = result.stdout.split()
        if expected is None:
            self.assertNotIn("-shr", tokens)
            return
        index = tokens.index("-shr")
        value = tokens[index + 1] if index + 1 < len(tokens) and not tokens[index + 1].startswith("-") else None
        self.assertEqual(" ".join(["-shr"] + ([value] if value else [])), expected)

    def test_fractions(self):
        self.assert_flag([], None)
        self.assert_flag(["-shr"], "-shr")                  # the default 1/8 prints bare
        self.assert_flag(["-shr", "1/8"], "-shr")
        self.assert_flag(["-shr", "2/16"], "-shr")          # reduced
        self.assert_flag(["-shr", "3/16"], "-shr 3/16")
        self.assert_flag(["-shr", "0.25"], "-shr 1/4")
        self.assert_flag(["-shr", "1"], "-shr 1")
        # the printed fraction is the one the game uses: the nearest 256th
        self.assert_flag(["-shr", "0.1111"], "-shr 7/64")
        self.assert_flag(["-shr", "1/9"], "-shr 7/64")
        self.assert_flag(["-shr", "0.11"], "-shr 7/64")
        self.assert_flag(["-shr", "1/3"], "-shr 85/256")
        self.assert_flag(["-shr", "-pd"], "-shr")           # a following flag is not a fraction

    def test_rejected(self):
        for bad in ("0", "2", "3/2", "abc", "1/0", "1/1000"):
            result = parse_flags("-shr", bad)
            self.assertNotEqual(result.returncode, 0, msg = bad)
            self.assertIn("-shr", result.stderr)

if __name__ == "__main__":
    unittest.main()
