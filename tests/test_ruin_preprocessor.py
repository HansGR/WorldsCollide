import importlib.util
import os
import unittest

# load the module by path: importing the args package parses sys.argv
_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "args", "ruin_preprocessor.py")
_spec = importlib.util.spec_from_file_location("ruin_preprocessor", _path)
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)


def expand(argv):
    rp._preprocessing_done = False
    return rp.preprocess_ruin_flag(list(argv))


def value_after(argv, flag, count = 1):
    at = argv.index(flag)
    return argv[at + 1:at + 1 + count]


class TestRuinPreprocessor(unittest.TestCase):
    def test_default_is_character_gated_base_set(self):
        argv = expand(["wc.py", "-i", "x.smc", "-ruin"])
        self.assertIn("-cg", argv)
        self.assertNotIn("-open", argv)
        self.assertEqual(value_after(argv, "-rce"), ["6.9"])
        self.assertNotIn("-pd", argv)
        self.assertNotIn("-stesp", argv)
        self.assertEqual(argv[argv.index("-ruin") + 1], "-cg")

    def test_hard_adds_extras_after_the_mode_token(self):
        argv = expand(["wc.py", "-ruin", "hard"])
        self.assertEqual(argv[argv.index("-ruin") + 1], "hard")
        self.assertIn("-pd", argv)
        self.assertEqual(value_after(argv, "-sfd"), ["3"])
        self.assertIn("-cg", argv)

    def test_easy_overrides_and_extras(self):
        argv = expand(["wc.py", "-ruin", "easy"])
        self.assertEqual(argv[argv.index("-ruin") + 1], "easy")
        # overrides
        self.assertIn("-open", argv)
        self.assertNotIn("-cg", argv)
        self.assertEqual(value_after(argv, "-rce"), ["6.6"])
        self.assertEqual(value_after(argv, "-stl"), ["12"])
        self.assertEqual(value_after(argv, "-gp"), ["12000"])
        self.assertNotIn("-ssf4", argv)
        self.assertEqual(value_after(argv, "-chrm", 2), ["0", "0"])
        # kept from the base
        self.assertEqual(value_after(argv, "-ir"), ["stronger"])
        self.assertEqual(value_after(argv, "-sto"), ["1"])
        # extras
        self.assertEqual(value_after(argv, "-stesp", 2), ["3", "3"])
        self.assertEqual(value_after(argv, "-si"), ["233.6.6"])
        self.assertEqual(value_after(argv, "-sws"), ["10"])
        self.assertEqual(value_after(argv, "-sfd"), ["3"])
        self.assertEqual(value_after(argv, "-sj"), ["12"])
        self.assertIn("-rrt", argv)
        self.assertEqual(value_after(argv, "-oc"), ["58.1.1.10.3.3"])
        self.assertEqual(value_after(argv, "-od"), ["58.1.1.10.6.6"])
        self.assertEqual(value_after(argv, "-oe"), ["58.1.1.10.9.9"])
        # not hard
        self.assertNotIn("-pd", argv)
        # every flag appears once
        flags = [a for a in argv if a.startswith("-")]
        self.assertEqual(len(flags), len(set(flags)), flags)

    def test_easy_honors_no_and_exclusive_groups(self):
        argv = expand(["wc.py", "-ruin", "easy", "-no", "open", "stesp"])
        self.assertNotIn("-open", argv)
        self.assertNotIn("-stesp", argv)
        # the removed flag took its two values with it: the extras now start at -si
        self.assertEqual(argv[argv.index("-si") - 1], "-oss")

        argv = expand(["wc.py", "-ruin", "easy", "-cg"])
        self.assertNotIn("-open", argv)
        self.assertEqual(argv.count("-cg"), 1)

    def test_custom_injects_nothing(self):
        argv = expand(["wc.py", "-ruin", "custom", "-cg"])
        self.assertEqual(argv, ["wc.py", "-ruin", "custom", "-cg"])


if __name__ == "__main__":
    unittest.main()
