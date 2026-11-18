"""Make the UMAROS COLLIDE title screen from the Worlds Collide one.

usage (from the repository root): python3 graphics/tools/umaros_collide_title.py [PREVIEW.ppm]

The title screen data (graphics/title/*.bin, written to 18f000 by data/title_graphics.py) is one
compressed block. In it the logo is a mask, 32x8 tiles: a tilemap (a word per tile) at LOGO_MAP and
its 4bpp tiles at LOGO_TILES, color 1 everywhere but the letters (color 0), which let the fire show
through. Rows 0-5 are WORLDS COLLIDE, row 6 the line under it, row 7 the subtitle. The logo has
MAX_TILES tiles; the new one is written over them and nothing after them is touched.

WORLDS becomes UMAROS in the same letters: R, O and S are the title's own, M is its W turned upside
down, U its O with straight sides to the top, and A is drawn with the W's strokes."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import utils.compression as compression

SOURCE = os.path.join(ROOT, "graphics", "title", "WC Spartan Title Data-CDude.bin")
DESTINATION = os.path.join(ROOT, "graphics", "title", "Umaros Collide Title Data.bin")

LOGO_MAP = 0x8be0
LOGO_TILES = 0x8de0
LOGO_COLUMNS, LOGO_ROWS = 32, 8
MAX_TILES = 0x7b            # the worlds collide logo's; what follows them is not the logo's (the (c) is there)
TILE_SIZE = 32

LETTER, BACKGROUND = 0, 1
LETTER_HEIGHT = 48

def tile_pixels(data, tile):
    address = LOGO_TILES + tile * TILE_SIZE
    return [[sum(((data[address + offset] >> (7 - x)) & 1) << plane
                 for plane, offset in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)))
             for x in range(8)] for y in range(8)]

def tile_data(pixels):
    data = [0] * TILE_SIZE
    for y in range(8):
        for x in range(8):
            for plane, offset in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)):
                data[offset] |= ((pixels[y][x] >> plane) & 1) << (7 - x)
    return data

def read_logo(data):
    logo = [[BACKGROUND] * (LOGO_COLUMNS * 8) for _ in range(LOGO_ROWS * 8)]
    for row in range(LOGO_ROWS):
        for column in range(LOGO_COLUMNS):
            address = LOGO_MAP + 2 * (row * LOGO_COLUMNS + column)
            tile = tile_pixels(data, data[address] | (data[address + 1] << 8))
            for y in range(8):
                logo[row * 8 + y][column * 8 : column * 8 + 8] = tile[y]
    return logo

def write_logo(data, logo):
    tiles = [tile_data([[BACKGROUND] * 8 for _ in range(8)])]   # tile 0 fills the rest of the layer
    for row in range(LOGO_ROWS):
        for column in range(LOGO_COLUMNS):
            tile = tile_data([logo[row * 8 + y][column * 8 : column * 8 + 8] for y in range(8)])
            if tile not in tiles:
                tiles.append(tile)
            address = LOGO_MAP + 2 * (row * LOGO_COLUMNS + column)
            data[address : address + 2] = tiles.index(tile).to_bytes(2, "little")
    if len(tiles) > MAX_TILES:
        raise ValueError(f"the logo needs {len(tiles)} tiles, there is room for {MAX_TILES}")
    used = len(tiles)
    tiles += [[0] * TILE_SIZE] * (MAX_TILES - len(tiles))
    for index, tile in enumerate(tiles):
        data[LOGO_TILES + index * TILE_SIZE : LOGO_TILES + (index + 1) * TILE_SIZE] = tile
    return used

def glyph(logo, left, right):
    return [row[left : right + 1] for row in logo[:LETTER_HEIGHT]]

def draw(logo, left, pixels):
    for y, row in enumerate(pixels):
        for x, pixel in enumerate(row):
            if pixel == LETTER:
                logo[y][left + x] = LETTER

def letter_u(letter_o):
    # the O (13 wide, sides 4 wide) with its sides straight up to the top, where they get the
    # serifs the title's other stems have (one pixel to each side)
    STRAIGHT_ROW = 20
    pixels = [[BACKGROUND] + list(letter_o[STRAIGHT_ROW]) + [BACKGROUND] for _ in range(4)]
    pixels += [[BACKGROUND] + list(row) + [BACKGROUND] for row in letter_o[4:]]
    width = len(pixels[0])
    for x in list(range(0, 6)) + list(range(width - 6, width)):
        pixels[0][x] = LETTER
    return pixels

def letter_m(letter_w):
    return [row[::-1] for row in letter_w[::-1]]

def letter_a():
    # the W's strokes: a thin one down to the left and a thick one down to the right, each moving
    # 4 pixels over the letter's height, the feet the title's other stems have and a crossbar
    WIDTH, SLANT, THIN, THICK = 15, 4, 2, 4
    APEX = 6
    CROSSBAR = (31, 32)
    pixels = [[BACKGROUND] * WIDTH for _ in range(LETTER_HEIGHT)]
    for y in range(LETTER_HEIGHT):
        shift = (SLANT * y + (LETTER_HEIGHT - 1) // 2) // (LETTER_HEIGHT - 1)
        thin, thick = APEX - shift, APEX + shift
        for x in range(thin, thin + THIN):
            pixels[y][x] = LETTER
        for x in range(thick, thick + THICK):
            pixels[y][x] = LETTER
        if y in CROSSBAR:
            for x in range(thin + THIN, thick):
                pixels[y][x] = LETTER
    for x in list(range(0, 5)) + list(range(WIDTH - 6, WIDTH)):
        pixels[LETTER_HEIGHT - 1][x] = LETTER
    return pixels

def umaros(logo):
    # WORLDS: W 16-39, O 42-54, R 57-71, L 73-83, D 89-102, S 106-117 (with their serifs)
    letter_w, letter_o = glyph(logo, 16, 39), glyph(logo, 42, 54)
    letter_r, letter_s = glyph(logo, 57, 71), glyph(logo, 104, 119)

    for row in logo[:LETTER_HEIGHT]:
        row[12:124] = [BACKGROUND] * (124 - 12)

    draw(logo, 16, letter_u(letter_o))      # U 17-29
    draw(logo, 32, letter_m(letter_w))      # M 32-55
    draw(logo, 57, letter_a())              # A 57-71
    draw(logo, 73, letter_r)                # R 74-87: as far into its tiles as it was, so they are the same tiles
    draw(logo, 90, letter_o)                # O 90-102: likewise
    draw(logo, 104, letter_s)               # S where it was

def main():
    with open(SOURCE, "rb") as source:
        block = list(source.read())
    size = int.from_bytes(block[:2], "little")
    data = compression.decompress(block[:size])

    logo = read_logo(data)
    umaros(logo)
    tiles = write_logo(data, logo)

    compressed = compression.compress(data)
    if len(compressed) > len(block):
        raise ValueError(f"the title data is {len(compressed)} bytes compressed, there is room for {len(block)}")
    compressed += [0xff] * (len(block) - len(compressed))
    with open(DESTINATION, "wb") as destination:
        destination.write(bytes(compressed))
    print(f"{os.path.relpath(DESTINATION, ROOT)}: {tiles} logo tiles of {MAX_TILES}")

    if len(sys.argv) > 1:
        with open(sys.argv[1], "wb") as preview:
            preview.write(f"P5 {LOGO_COLUMNS * 8} {LOGO_ROWS * 8} 255\n".encode())
            preview.write(bytes(0 if pixel == LETTER else 255 for row in logo for pixel in row))

if __name__ == "__main__":
    main()
