import os
import subprocess
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_PATH = os.path.join(REPO_ROOT, "ff3.smc")

# the in-game Flags menu holds at most 255 lines: its line count is an 8-bit
# immediate, so 256 lines wrapped to 0 and the whole menu drew blank (-ruin easy)
FIT_LINES = """
import sys, io, contextlib
sys.argv = ["wc.py", "-i", "ff3.smc", "-o", sys.argv[1], "-s", "1"]
with contextlib.redirect_stdout(io.StringIO()):
    import args
    from memory.memory import Memory
    memory = Memory()
import menus.pregame_track_scroll_area as scroll_area
from menus.flags import Flags

def menu(groups, size):
    flags = Flags.__new__(Flags)
    flags.lines, flags.submenus = [], {}
    for group in range(groups):
        flags.lines.append(scroll_area.Line(f"Group {group}", None))
        for option in range(size):
            if option == 1:
                flags.submenus[len(flags.lines)] = f"sub {group}"
            flags.lines.append(scroll_area.Line(f"  {group}.{option}", None))
        flags.lines.append(scroll_area.Line("", None))
    del flags.lines[-1]
    flags.fit_lines()
    return flags

short = menu(10, 9)                      # 109 lines: untouched
assert len(short.lines) == 109 and "" in [line.text for line in short.lines]
easy = menu(30, 7)                       # 269 lines: the bottom 14 separators dropped
texts = [line.text for line in easy.lines]
assert len(easy.lines) == scroll_area.MAX_LINES
blanks = [index for index, text in enumerate(texts) if text == ""]
assert len(blanks) == 29 - 14
assert "" not in texts[blanks[-1] + 1:] and texts[blanks[-1] + 1] == "Group 15"
for line, submenu in easy.submenus.items():
    assert easy.lines[line].text == "  " + submenu[4:] + ".1", (line, submenu)
huge = menu(20, 20)                      # 400 even without separators: cut
assert len(huge.lines) == scroll_area.MAX_LINES
assert huge.lines[-1].text.strip() == "(more in the log)"
assert all(line < len(huge.lines) - 1 for line in huge.submenus)
# -compr/-compru chances: their own sub-menu, two columns per line
from menus.flags_command_chances import FlagsCommandChances
chances = FlagsCommandChances._format_menu([("Fight", 90), ("MagiTek", 100), ("Shock", 12)])
assert chances == ["Fight    90% MagiTek 100% ", "Shock    12%" + " " * 14], chances
assert all(len(line) <= scroll_area.WIDTH for line in chances)
sys.__stdout__.write("ok\\n")
"""

@unittest.skipUnless(os.path.isfile(ROM_PATH), "needs ff3.smc at the repository root")
class TestFlagsMenuFit(unittest.TestCase):
    def test_fit_lines(self):
        import tempfile
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run([sys.executable, "-c", FIT_LINES, os.path.join(out, "seed.smc")],
                                    cwd = REPO_ROOT, capture_output = True, text = True, timeout = 300)
        self.assertEqual(result.returncode, 0, msg = result.stderr)
        self.assertIn("ok", result.stdout)

if __name__ == "__main__":
    unittest.main()
