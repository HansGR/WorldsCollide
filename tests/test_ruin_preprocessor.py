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
        # easy is the standard flow made softer: character gated, base level
        self.assertIn("-cg", argv)
        self.assertNotIn("-open", argv)
        self.assertEqual(value_after(argv, "-stl"), ["6"])
        # overrides
        self.assertEqual(value_after(argv, "-rce"), ["6.6"])
        self.assertEqual(value_after(argv, "-sc3"), ["random"])
        self.assertEqual(value_after(argv, "-sc4"), ["random"])
        self.assertEqual(value_after(argv, "-lsced"), ["1.5"])
        self.assertEqual(value_after(argv, "-hmced"), ["1.5"])
        self.assertEqual(value_after(argv, "-esr", 2), ["5", "5"])
        self.assertEqual(value_after(argv, "-ebr"), ["100"])
        self.assertEqual(value_after(argv, "-gp"), ["12000"])
        self.assertEqual(value_after(argv, "-ir"), ["premium"])
        self.assertNotIn("-ssf4", argv)
        self.assertEqual(value_after(argv, "-chrm", 2), ["2", "0"])
        # kept from the base
        self.assertEqual(value_after(argv, "-xgced"), ["2"])
        self.assertEqual(value_after(argv, "-sto"), ["1"])
        # extras (no starting espers any more)
        self.assertNotIn("-stesp", argv)
        self.assertEqual(value_after(argv, "-si"), ["233.6.6"])
        self.assertEqual(value_after(argv, "-sws"), ["10"])
        self.assertEqual(value_after(argv, "-sfd"), ["3"])
        self.assertEqual(value_after(argv, "-sj"), ["12"])
        self.assertIn("-rrt", argv)
        # High Tier Item rewards at 2, 4 and 6 espers obtained
        self.assertEqual(value_after(argv, "-oc"), ["58.1.1.4.2.2"])
        self.assertEqual(value_after(argv, "-od"), ["58.1.1.4.4.4"])
        self.assertEqual(value_after(argv, "-oe"), ["58.1.1.4.6.6"])
        # not hard
        self.assertNotIn("-pd", argv)
        # every flag appears once
        flags = [a for a in argv if a.startswith("-")]
        self.assertEqual(len(flags), len(set(flags)), flags)

    def test_easy_honors_no_and_exclusive_groups(self):
        argv = expand(["wc.py", "-ruin", "easy", "-no", "rrt", "chrm"])
        self.assertNotIn("-rrt", argv)
        self.assertNotIn("-chrm", argv)
        # the removed flag took its two values with it: -cms followed -chrm 2 0
        self.assertEqual(argv[argv.index("-cms") - 1], "20")

        # a user flag from an exclusive group replaces the default
        argv = expand(["wc.py", "-ruin", "easy", "-open"])
        self.assertNotIn("-cg", argv)
        self.assertEqual(argv.count("-open"), 1)

    def test_user_starting_party_replaces_all_four(self):
        # any user -scN replaces the whole injected party, -sc4 included
        argv = expand(["wc.py", "-ruin", "easy", "-sc1", "terra"])
        self.assertEqual(value_after(argv, "-sc1"), ["terra"])
        for flag in ("-sc2", "-sc3", "-sc4"):
            self.assertNotIn(flag, argv)

    def test_user_stlr_replaces_injected_stl(self):
        # -stl and -stlr are mutually exclusive: a user -stlr must drop the
        # injected starting level (6), not clash with it
        for mode in ([], ["easy"], ["hard"]):
            argv = expand(["wc.py", "-ruin", *mode, "-stlr", "3", "99"])
            self.assertNotIn("-stl", argv)
            self.assertEqual(value_after(argv, "-stlr", 2), ["3", "99"])

    def test_custom_injects_nothing(self):
        argv = expand(["wc.py", "-ruin", "custom", "-cg"])
        self.assertEqual(argv, ["wc.py", "-ruin", "custom", "-cg"])


if __name__ == "__main__":
    unittest.main()
