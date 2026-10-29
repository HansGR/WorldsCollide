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

    def test_esper_and_item_reward_defaults(self):
        # standard and hard share the base values; easy overrides the esper ones
        for mode in ([], ["hard"]):
            argv = expand(["wc.py", "-ruin"] + mode)
            self.assertEqual(value_after(argv, "-esr", 2), ["3", "5"])
            self.assertEqual(value_after(argv, "-ebr"), ["88"])
            self.assertEqual(value_after(argv, "-ir"), ["ruin"])
            self.assertEqual(argv.count("-ir"), 1)
        # every flagset: item rewards on character/esper checks at 1%
        for mode in ([], ["hard"], ["easy"]):
            argv = expand(["wc.py", "-ruin"] + mode)
            self.assertEqual(value_after(argv, "-rirc"), ["1"])
            self.assertEqual(argv.count("-rirc"), 1)
        # every flagset: at least 55 treasure chests on the map
        for mode in ([], ["hard"], ["easy"], ["fast"]):
            argv = expand(["wc.py", "-ruin"] + mode)
            self.assertEqual(value_after(argv, "-rrtc"), ["55"])
            self.assertEqual(argv.count("-rrtc"), 1)
        self.assertNotIn("-rrtc", expand(["wc.py", "-ruin", "-no", "rrtc"]))
        # '-no rirc' falls back to the vanilla-rate formula; a user value comes
        # after the injected default, so argparse's last value wins
        self.assertNotIn("-rirc", expand(["wc.py", "-ruin", "-no", "rirc"]))
        argv = expand(["wc.py", "-ruin", "-rirc", "25"])
        self.assertEqual(argv[len(argv) - 1 - argv[::-1].index("-rirc") + 1], "25")

    def test_hard_adds_extras_after_the_mode_token(self):
        argv = expand(["wc.py", "-ruin", "hard"])
        self.assertEqual(argv[argv.index("-ruin") + 1], "hard")
        self.assertIn("-pd", argv)
        self.assertEqual(value_after(argv, "-sfd"), ["3"])
        self.assertIn("-cg", argv)
        # a hard level cap at 48: one value, and the flag after it is intact
        at = argv.index("-lc")
        self.assertEqual(argv[at + 1], "48")
        self.assertTrue(argv[at + 2].startswith("-"), argv[at + 2])
        self.assertEqual(argv.count("-lc"), 1)
        # '-no lc' still removes it cleanly
        argv = expand(["wc.py", "-ruin", "hard", "-no", "lc"])
        self.assertNotIn("-lc", argv)
        self.assertEqual(argv[argv.index("-gpm") + 2], "-lsced")

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
        self.assertEqual(value_after(argv, "-ir"), ["ruin"])        # the base ruin preset
        self.assertNotIn("-ssf4", argv)
        self.assertEqual(value_after(argv, "-chrm", 2), ["2", "0"])
        self.assertNotIn("-lc", argv)                    # no level cap
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
        # High Tier Item rewards at 3 and 6 espers obtained
        self.assertEqual(value_after(argv, "-oc"), ["58.1.1.4.3.3"])
        self.assertEqual(value_after(argv, "-od"), ["58.1.1.4.6.6"])
        self.assertNotIn("-oe", argv)                    # two high tier item objectives
        # not hard
        self.assertNotIn("-pd", argv)
        # every flag appears once
        flags = [a for a in argv if a.startswith("-")]
        self.assertEqual(len(flags), len(set(flags)), flags)

    def test_fast_is_standard_with_easy_map_size(self):
        argv = expand(["wc.py", "-ruin", "fast"])
        self.assertEqual(argv[argv.index("-ruin") + 1], "fast")
        # from easy: map size, party, espers, no cap, towns, the two objectives
        self.assertEqual(value_after(argv, "-rce"), ["6.6"])
        self.assertEqual(value_after(argv, "-sc4"), ["random"])
        self.assertEqual(value_after(argv, "-esr", 2), ["5", "5"])
        self.assertEqual(value_after(argv, "-ebr"), ["100"])
        self.assertNotIn("-lc", argv)
        self.assertIn("-rrt", argv)
        self.assertEqual(value_after(argv, "-oc"), ["58.1.1.4.3.3"])
        self.assertEqual(value_after(argv, "-od"), ["58.1.1.4.6.6"])
        self.assertEqual(value_after(argv, "-sj"), ["12"])
        self.assertEqual(value_after(argv, "-xpm"), ["10"])  # its own: 10x experience (base 8)
        for flag in ("-lsced", "-hmced", "-xgced"):          # steeper scaling (base 2)
            self.assertEqual(value_after(argv, flag), ["2.5"], flag)
        # everything else is standard
        standard = expand(["wc.py", "-ruin"])
        for flag, count in (("-gp", 1), ("-chrm", 2), ("-ir", 1),
                            ("-rrtc", 1), ("-rirc", 1), ("-stl", 1), ("-compru", 2)):
            self.assertEqual(value_after(argv, flag, count), value_after(standard, flag, count), flag)
        self.assertIn("-ssf4", argv)
        self.assertIn("-cg", argv)
        for flag in ("-si", "-sfd", "-sws", "-pd", "-oe"):
            self.assertNotIn(flag, argv)
        flags = [a for a in argv if a.startswith("-")]
        self.assertEqual(len(flags), len(set(flags)), flags)
        self.assertEqual(sorted(set(flags) - set(standard)),
                         ["-oc", "-od", "-rrt", "-sc4", "-sj"])

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

    def test_required_characters_take_the_last_default_slots(self):
        # -rc drops trailing default '-scN random' slots, one per required
        # character, from the slots the mode actually injects
        for mode, left in (([], ["-sc1", "-sc2"]), (["easy"], ["-sc1", "-sc2", "-sc3"]),
                           (["fast"], ["-sc1", "-sc2", "-sc3"])):
            argv = expand(["wc.py", "-ruin", *mode, "-rc", "terra"])
            self.assertEqual([a for a in argv if a in ("-sc1", "-sc2", "-sc3", "-sc4")], left)

    def test_standard_commands_and_level_cap(self):
        argv = expand(["wc.py", "-ruin"])
        ids, percents = value_after(argv, "-compru", 2)
        ids, percents = ids.split("."), percents.split(".")
        self.assertEqual(len(ids), len(percents))
        self.assertEqual(percents[:3], ["90", "90", "90"])
        # every skill declared at 24%, Possess (28) and Shock (27) at 12%
        skills = dict(zip(ids[3:], percents[3:]))
        self.assertEqual(len(skills), 21)
        self.assertEqual(skills.pop("28"), "12")
        self.assertEqual(skills.pop("27"), "12")
        self.assertEqual(set(skills.values()), {"24"})
        # declared skills cannot also be excluded, and -com would reserve the slots
        self.assertNotIn("-rec", argv)
        self.assertNotIn("-com", argv)
        self.assertEqual(value_after(argv, "-lc", 2), ["48", "10"])
        # '-no lc' removes the cap with both of its values
        argv = expand(["wc.py", "-ruin", "-no", "lc"])
        self.assertNotIn("-lc", argv)
        self.assertEqual(argv[argv.index("-gpm") + 2], "-lsced")

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
