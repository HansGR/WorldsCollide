import random
import unittest

import obfuscation


class TestNonce(unittest.TestCase):
    def test_deterministic(self):
        a = obfuscation.nonce_bytes("seed123", "-cg -sl", "1.2.3", "relocate/chests")
        b = obfuscation.nonce_bytes("seed123", "-cg -sl", "1.2.3", "relocate/chests")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 32)

    def test_inputs_separate(self):
        base = obfuscation.nonce_bytes("seed123", "-cg", "1.2.3", "p")
        self.assertNotEqual(base, obfuscation.nonce_bytes("seed124", "-cg", "1.2.3", "p"))
        self.assertNotEqual(base, obfuscation.nonce_bytes("seed123", "-open", "1.2.3", "p"))
        self.assertNotEqual(base, obfuscation.nonce_bytes("seed123", "-cg", "1.2.4", "p"))
        self.assertNotEqual(base, obfuscation.nonce_bytes("seed123", "-cg", "1.2.3", "q"))

    def test_no_field_confusion(self):
        # field encoding must keep (seed, flags) pairs unambiguous even
        # when concatenations coincide
        a = obfuscation.nonce_bytes("seed:x", "-cg", "1.2.3", "p")
        b = obfuscation.nonce_bytes("seed", "x:-cg", "1.2.3", "p")
        self.assertNotEqual(a, b)
        c = obfuscation.nonce_bytes("ab", "c", "1.2.3", "p")
        d = obfuscation.nonce_bytes("a", "bc", "1.2.3", "p")
        self.assertNotEqual(c, d)


class TestRng(unittest.TestCase):
    def test_deterministic_stream(self):
        r1 = obfuscation.rng("seed123", "-cg", "1.2.3", "mask/shops")
        r2 = obfuscation.rng("seed123", "-cg", "1.2.3", "mask/shops")
        self.assertEqual([r1.randrange(256) for _ in range(64)],
                         [r2.randrange(256) for _ in range(64)])

    def test_purposes_independent(self):
        r1 = obfuscation.rng("seed123", "-cg", "1.2.3", "mask/shops")
        r2 = obfuscation.rng("seed123", "-cg", "1.2.3", "mask/chests")
        self.assertNotEqual([r1.randrange(256) for _ in range(16)],
                            [r2.randrange(256) for _ in range(16)])

    def test_global_stream_untouched(self):
        # drawing from an obfuscation rng must not perturb the gameplay rng
        random.seed("seed123-cg")
        before = [random.randrange(2 ** 16) for _ in range(8)]

        random.seed("seed123-cg")
        r = obfuscation.rng("seed123", "-cg", "1.2.3", "relocate/chests")
        for _ in range(1000):
            r.randrange(2 ** 16)
        after = [random.randrange(2 ** 16) for _ in range(8)]

        self.assertEqual(before, after)


class TestDecoy(unittest.TestCase):
    def test_decoy_independent_of_real(self):
        class FakeArgs:
            seed = "seed123"
            seed_rng_flags = "-cg"

        real = obfuscation.rng_for_args(FakeArgs, "chests")
        decoy = obfuscation.decoy_rng_for_args(FakeArgs, "chests")
        self.assertNotEqual([real.randrange(256) for _ in range(16)],
                            [decoy.randrange(256) for _ in range(16)])


class TestMask(unittest.TestCase):
    class FakeArgs:
        seed = "seed123"
        seed_rng_flags = "-cg"

    def test_pad_deterministic(self):
        from obfuscation import mask
        self.assertEqual(mask.pad_bytes(self.FakeArgs, "shop_data", 64),
                         mask.pad_bytes(self.FakeArgs, "shop_data", 64))

    def test_pads_separated_by_table(self):
        from obfuscation import mask
        self.assertNotEqual(mask.pad_bytes(self.FakeArgs, "shop_data", 64),
                            mask.pad_bytes(self.FakeArgs, "chest_data", 64))

    def test_pad_not_degenerate(self):
        from obfuscation import mask
        pad = mask.pad_bytes(self.FakeArgs, "shop_data", 64)
        self.assertTrue(any(pad))  # the zero pad would leave plaintext


class TestRewards(unittest.TestCase):
    def setUp(self):
        from obfuscation import rewards
        rewards.reset()
        self.rewards = rewards

    def test_kind_values(self):
        r = self.rewards
        self.assertEqual((r.KIND_ITEM, r.KIND_ESPER, r.KIND_CHARACTER),
                         (0x00, 0x01, 0x02))
        self.assertEqual(r.KINDS,
                         {"item": 0x00, "esper": 0x01, "character": 0x02})

    def test_register_slots_sequential(self):
        r = self.rewards
        self.assertEqual(r.register("item", 26), 0)
        self.assertEqual(r.register("esper", 6), 1)
        self.assertEqual(r.register("character", 5), 2)
        self.assertEqual(r.count(), 3)

    def test_register_check_maps_reward_types(self):
        from event.event_reward import RewardType
        r = self.rewards

        class FakeReward:
            def __init__(self, type, id):
                self.type = type
                self.id = id

        r.register_check(FakeReward(RewardType.CHARACTER, 5))
        r.register_check(FakeReward(RewardType.ESPER, 6))
        r.register_check(FakeReward(RewardType.ITEM, 26))
        self.assertEqual(r._rewards,
                         [(0x02, 5), (0x01, 6), (0x00, 26)])

    def test_reset_clears(self):
        r = self.rewards
        r.register("character", 3)
        r.reset()
        self.assertEqual(r.count(), 0)


if __name__ == "__main__":
    unittest.main()
