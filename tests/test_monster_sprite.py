import random
import unittest

import graphics.monster_sprite as monster_sprite

class TestMonsterSprite(unittest.TestCase):
    def test_tile_round_trip(self):
        rng = random.Random(1)
        pixels = [[rng.randrange(16) for _ in range(8)] for _ in range(8)]
        data = monster_sprite.tile_data(pixels)
        self.assertEqual(len(data), monster_sprite.TILE_SIZE_4BPP)
        self.assertEqual(monster_sprite.tile_pixels(data), pixels)

    def test_tile_bitplanes(self):
        # the first pixel of the first row is the high bit of each bitplane's first byte
        pixels = [[0] * 8 for _ in range(8)]
        pixels[0][0] = 0b1010
        data = monster_sprite.tile_data(pixels)
        self.assertEqual([data[0], data[1], data[16], data[17]], [0x00, 0x80, 0x00, 0x80])

    def test_three_bpp_tile(self):
        data = [0] * monster_sprite.TILE_SIZE_3BPP
        data[2 * 3] = 0x01          # row 3, last pixel: bitplane 0
        data[16 + 3] = 0x01         # and bitplane 2
        pixels = monster_sprite.tile_pixels(data, three_bpp = True)
        self.assertEqual(pixels[3][7], 0b101)
        self.assertEqual(sum(map(sum, pixels)), 0b101)

    def test_without_shadow(self):
        pixels = [list(map(int, row)) for row in (
            "0011100",      # above the last rows: untouched
            "0155510",
            "0155510",
            "1111111",      # the outline under the feet stays, its ends do not touch them
            "0111110",
        )]
        expected = [list(map(int, row)) for row in (
            "0011100",
            "0155510",
            "0155510",
            "0111110",
            "0000000",
        )]
        self.assertEqual(monster_sprite.without_shadow(pixels, 1, 2), expected)
        self.assertEqual(monster_sprite.without_shadow(pixels, 1, 0), pixels)

    def test_three_bpp_tile_round_trip(self):
        rng = random.Random(3)
        pixels = [[rng.randrange(8) for _ in range(8)] for _ in range(8)]
        data = monster_sprite.tile_data(pixels, three_bpp = True)
        self.assertEqual(len(data), monster_sprite.TILE_SIZE_3BPP)
        self.assertEqual(monster_sprite.tile_pixels(data, three_bpp = True), pixels)

    def test_sprite_round_trip(self):
        rng = random.Random(2)
        size = monster_sprite.SMALL_MOLD_TILES * monster_sprite.TILE_PIXELS
        pixels = [[0] * size for _ in range(size)]
        for y in range(8, 30):      # tiles in rows 1-3, columns 2-4
            for x in range(16, 40):
                pixels[y][x] = rng.randrange(1, 16)

        mold, graphics = monster_sprite.sprite_data(pixels)
        self.assertEqual(mold, [0x00, 0x38, 0x38, 0x38, 0x00, 0x00, 0x00, 0x00])
        self.assertEqual(monster_sprite.mold_tile_count(mold), 9)
        self.assertEqual(len(graphics), 9 * monster_sprite.TILE_SIZE_4BPP)
        self.assertEqual(monster_sprite.sprite_pixels(mold, monster_sprite.SMALL_MOLD_TILES, graphics), pixels)

    def test_scaled_sprite_is_a_large_sprite(self):
        size = monster_sprite.SMALL_MOLD_TILES * monster_sprite.TILE_PIXELS
        pixels = [[0] * size for _ in range(size)]
        pixels[0][0] = 5            # one pixel, top left
        pixels[63][63] = 7          # one pixel, bottom right

        scaled = monster_sprite.scale(pixels, 2)
        self.assertEqual(len(scaled), 2 * size)
        self.assertEqual([scaled[0][0], scaled[0][1], scaled[1][0], scaled[1][1], scaled[0][2], scaled[2][0]],
                         [5, 5, 5, 5, 0, 0])

        mold, graphics = monster_sprite.sprite_data(scaled)
        self.assertEqual(len(mold), monster_sprite.mold_size(monster_sprite.LARGE_MOLD_TILES))
        self.assertEqual(mold[0], 0x80)
        self.assertEqual(mold[-1], 0x01)
        self.assertEqual(monster_sprite.mold_tile_count(mold), 2)
        self.assertEqual(monster_sprite.sprite_pixels(mold, monster_sprite.LARGE_MOLD_TILES, graphics), scaled)

if __name__ == '__main__':
    unittest.main()
