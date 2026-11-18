import os
import random
import unittest

import graphics.title_screen as title_screen
import utils.compression as compression

TITLE_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graphics", "title")
TITLES = [os.path.join(TITLE_DIRECTORY, name) for name in sorted(os.listdir(TITLE_DIRECTORY)) if name.endswith(".bin")]

def game_decompress(block):
    # as the game does it: a control byte is read whenever the last one is used up, and only after a
    # value is the end of the data looked for
    size = int.from_bytes(bytes(block[:2]), "little")
    window = [0] * compression.WINDOW_SIZE
    window_index = compression.WINDOW_START
    result = []
    index = 2
    bits_left = 0
    while True:
        if bits_left == 0:
            control, bits_left = block[index], 8
            index += 1
        if control & 1:
            values = [block[index]]
            index += 1
        else:
            position = block[index] | ((block[index + 1] & 0x07) << 8)
            length = (block[index + 1] >> 3) + 3
            index += 2
            values = []
            for offset in range(length):
                # (a copy may read what it has just written)
                value = window[(position + offset) % compression.WINDOW_SIZE]
                window[(window_index + offset) % compression.WINDOW_SIZE] = value
                values.append(value)
        for value in values:
            window[window_index] = value
            window_index = (window_index + 1) % compression.WINDOW_SIZE
        result += values
        control >>= 1
        bits_left -= 1
        if index == size:
            return result
        if index > size:
            raise AssertionError("the game would read past the end of the data")

class TestTitleScreen(unittest.TestCase):
    def setUp(self):
        self.data = title_screen.unpack(title_screen.read_block(TITLES[0]))

    def test_titles_unpack(self):
        self.assertTrue(TITLES)
        for path in TITLES:
            block = title_screen.read_block(path)
            self.assertEqual(len(block), title_screen.BLOCK_SIZE, path)
            data = title_screen.unpack(block)
            self.assertEqual(game_decompress(block), data, path)
            logo = title_screen.read_logo(data)
            self.assertEqual((len(logo), len(logo[0])), (title_screen.LOGO_HEIGHT, title_screen.LOGO_WIDTH))
            self.assertLessEqual(title_screen.logo_tile_count(data), title_screen.LOGO_MAX_TILES)

    def test_logo_round_trip(self):
        for path in TITLES:
            data = title_screen.unpack(title_screen.read_block(path))
            logo = title_screen.read_logo(data)
            changed = list(data)
            tiles = title_screen.write_logo(changed, logo)
            self.assertLessEqual(tiles, title_screen.LOGO_MAX_TILES)
            self.assertEqual(title_screen.read_logo(changed), logo)

            # only the logo's tilemap and tiles are written
            tiles_end = title_screen.LOGO_TILES + title_screen.LOGO_MAX_TILES * title_screen.TILE_SIZE
            self.assertEqual(changed[:title_screen.LOGO_MAP], data[:title_screen.LOGO_MAP])
            self.assertEqual(changed[tiles_end:], data[tiles_end:])

    def test_pack(self):
        logo = title_screen.read_logo(self.data)
        for y in range(8, 40):
            logo[y][16:240] = [title_screen.FIRE] * 224
        title_screen.write_logo(self.data, logo)

        block = title_screen.pack(self.data)
        self.assertEqual(len(block), title_screen.BLOCK_SIZE)
        self.assertEqual(title_screen.unpack(block), self.data)
        self.assertEqual(game_decompress(block), self.data)

    def test_tiles_are_shared(self):
        logo = [[title_screen.BACKGROUND] * title_screen.LOGO_WIDTH for _ in range(title_screen.LOGO_HEIGHT)]
        for x in range(0, title_screen.LOGO_WIDTH, 16):     # the same shape every 16 pixels: 2 tiles
            for y in range(8):
                logo[y][x + 2 : x + 12] = [title_screen.FIRE] * 10
        tiles, tilemap = title_screen.logo_tiles(logo)
        self.assertEqual(len(tiles), 3)
        self.assertEqual(tilemap[:4], [1, 2, 1, 2])
        self.assertEqual(set(tilemap[title_screen.LOGO_COLUMNS:]), {0})

    def test_first_tile_is_the_background(self):
        logo = [[title_screen.FIRE] * title_screen.LOGO_WIDTH for _ in range(title_screen.LOGO_HEIGHT)]
        tiles, tilemap = title_screen.logo_tiles(logo)
        self.assertEqual(title_screen.tile_pixels(tiles[0]), [[title_screen.BACKGROUND] * 8] * 8)
        self.assertEqual(set(tilemap), {1})

    def test_tile_round_trip(self):
        rng = random.Random(3)
        pixels = [[rng.randrange(title_screen.COLORS) for _ in range(8)] for _ in range(8)]
        self.assertEqual(title_screen.tile_pixels(title_screen.tile_data(pixels)), pixels)

    def test_too_many_tiles(self):
        rng = random.Random(4)
        logo = [[rng.randrange(2) for _ in range(title_screen.LOGO_WIDTH)] for _ in range(title_screen.LOGO_HEIGHT)]
        before = list(self.data)
        with self.assertRaises(title_screen.TitleScreenError):
            title_screen.write_logo(self.data, logo)
        self.assertEqual(self.data, before)

    def test_wrong_size_or_color(self):
        logo = title_screen.read_logo(self.data)
        with self.assertRaises(title_screen.TitleScreenError):
            title_screen.write_logo(self.data, logo[:-1])
        logo[0][0] = title_screen.COLORS
        with self.assertRaises(title_screen.TitleScreenError):
            title_screen.write_logo(self.data, logo)

    def test_not_title_data(self):
        with self.assertRaises(title_screen.TitleScreenError):
            title_screen.unpack(compression.compress([1, 2, 3] * 100))
        with self.assertRaises(title_screen.TitleScreenError):
            title_screen.pack(self.data[:-1])

class TestCompressionForTheGame(unittest.TestCase):
    def test_data_ends_with_its_last_value(self):
        # 8 values fill a control byte: nothing may follow them, or the game reads past the end
        rng = random.Random(5)
        for count in range(1, 40):
            data = [rng.randrange(256) for _ in range(count)]
            self.assertEqual(game_decompress(compression.compress(data)), data, count)

    def test_copies(self):
        rng = random.Random(6)
        for length in (1, 2, 3, 34, 35, 2047, 2048, 2049, 5000):
            data = [rng.randrange(4) for _ in range(length)] + [9] * length
            self.assertEqual(game_decompress(compression.compress(data)), data, length)

if __name__ == '__main__':
    unittest.main()
