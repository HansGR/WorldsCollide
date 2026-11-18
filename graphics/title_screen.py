# the title screen data and the logo in it. graphics/title/README.md is the guide to editing it,
# graphics/tools/title_screen.py the tool
#
# the title screen data is a single compressed block at 18f000-194e95 in the rom (the files in
# graphics/title are that block, data/title_graphics.py writes one of them there). decompressed it is
# 44712 bytes of graphics and tilemaps for the title screen. the logo is one layer of it:
#   LOGO_MAP    32x8 tiles, a little endian word each: the number of the tile shown there
#   LOGO_TILES  the layer's tiles, 8x8 pixels of 4 bits each. tile 0 also fills the rest of the layer
# the layer is 256x64 pixels and is drawn 64 pixels down the screen

import utils.compression as compression

ROM_START = 0x18f000
ROM_END = 0x194e95
BLOCK_SIZE = ROM_END - ROM_START + 1

DATA_SIZE = 44712

LOGO_MAP = 0x8be0
LOGO_TILES = 0x8de0
LOGO_COLUMNS, LOGO_ROWS = 32, 8
LOGO_MAX_TILES = 0x88       # after them are the characters of the copyright lines (the original
                            # game's logo shows the first of those as a tile, so reading allows it)

TILE_PIXELS = 8
TILE_SIZE = 32
COLORS = 16

LOGO_WIDTH = LOGO_COLUMNS * TILE_PIXELS
LOGO_HEIGHT = LOGO_ROWS * TILE_PIXELS
LOGO_SCREEN_Y = 64

# what the logo's colors look like on the title screen. 0 is see-through: the fire behind the logo
# shows there (any color stands for it here). 1 is the color around the logo
FIRE, BACKGROUND = 0, 1
PALETTE = [
    (184, 80, 24),      # 0: the fire
    (24, 24, 33),       # 1: the title screen's background
    (239, 235, 239),    # 2: white
    (0, 0, 0),
    (0, 0, 0),
    (247, 130, 74),     # 5-7: oranges, light to dark
    (222, 97, 41),
    (140, 56, 33),
] + [(0, 0, 0)] * 8

class TitleScreenError(Exception):
    pass

def read_block(path):
    # the compressed block from a title data file or an (unheadered) rom
    with open(path, "rb") as file:
        contents = file.read()
    if len(contents) > ROM_END:
        contents = contents[ROM_START : ROM_END + 1]
    if len(contents) < 2:
        raise TitleScreenError(f"{path} is not title screen data")
    return list(contents)

def unpack(block):
    size = int.from_bytes(bytes(block[:2]), "little")
    if size < 2 or size > len(block):
        raise TitleScreenError(f"not title screen data: it says it is {size} bytes, of {len(block)}")
    try:
        data = compression.decompress(block[:size])
    except (AssertionError, IndexError):
        data = []
    if len(data) != DATA_SIZE:
        raise TitleScreenError(f"not title screen data: {len(data)} bytes decompressed, the title screen's is {DATA_SIZE}")
    return data

def pack(data):
    # the compressed block, as long as the space for it in the rom
    if len(data) != DATA_SIZE:
        raise TitleScreenError(f"the title screen data is {DATA_SIZE} bytes, not {len(data)}")
    block = compression.compress(list(data))
    if len(block) > BLOCK_SIZE:
        raise TitleScreenError(f"the title screen data is {len(block)} bytes compressed, {len(block) - BLOCK_SIZE} more "
                               f"than there is room for ({BLOCK_SIZE}). a simpler logo compresses better")
    return block + [0xff] * (BLOCK_SIZE - len(block))

def tile_pixels(tile):
    return [[sum(((tile[offset] >> (7 - x)) & 1) << plane
                 for plane, offset in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)))
             for x in range(TILE_PIXELS)] for y in range(TILE_PIXELS)]

def tile_data(pixels):
    tile = [0] * TILE_SIZE
    for y in range(TILE_PIXELS):
        for x in range(TILE_PIXELS):
            for plane, offset in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)):
                tile[offset] |= ((pixels[y][x] >> plane) & 1) << (7 - x)
    return tile

def logo_tile_count(data):
    # how many of the tiles the logo uses
    return 1 + max(int.from_bytes(bytes(data[address : address + 2]), "little")
                   for address in range(LOGO_MAP, LOGO_MAP + 2 * LOGO_COLUMNS * LOGO_ROWS, 2))

def read_logo(data):
    # the logo as LOGO_HEIGHT rows of LOGO_WIDTH colors (0-15)
    logo = [[BACKGROUND] * LOGO_WIDTH for _ in range(LOGO_HEIGHT)]
    for row in range(LOGO_ROWS):
        for column in range(LOGO_COLUMNS):
            address = LOGO_MAP + 2 * (row * LOGO_COLUMNS + column)
            tile = int.from_bytes(bytes(data[address : address + 2]), "little")
            if tile > LOGO_MAX_TILES:
                raise TitleScreenError(f"not a logo: tile {tile} at row {row}, column {column}")
            tile_address = LOGO_TILES + tile * TILE_SIZE
            pixels = tile_pixels(data[tile_address : tile_address + TILE_SIZE])
            for y in range(TILE_PIXELS):
                logo[row * TILE_PIXELS + y][column * TILE_PIXELS : (column + 1) * TILE_PIXELS] = pixels[y]
    return logo

def logo_tiles(logo):
    # the tiles of a logo, each different one once, and its tilemap
    if len(logo) != LOGO_HEIGHT or any(len(row) != LOGO_WIDTH for row in logo):
        raise TitleScreenError(f"the logo is {LOGO_WIDTH}x{LOGO_HEIGHT} pixels")
    if any(not 0 <= color < COLORS for row in logo for color in row):
        raise TitleScreenError(f"the logo's colors are 0-{COLORS - 1}")

    tiles = [tile_data([[BACKGROUND] * TILE_PIXELS for _ in range(TILE_PIXELS)])]
    tilemap = []
    for row in range(LOGO_ROWS):
        for column in range(LOGO_COLUMNS):
            tile = tile_data([logo[row * TILE_PIXELS + y][column * TILE_PIXELS : (column + 1) * TILE_PIXELS]
                              for y in range(TILE_PIXELS)])
            if tile not in tiles:
                tiles.append(tile)
            tilemap.append(tiles.index(tile))
    return tiles, tilemap

def write_logo(data, logo):
    # put a logo in the (decompressed) title screen data. returns how many tiles it uses
    tiles, tilemap = logo_tiles(logo)
    if len(tiles) > LOGO_MAX_TILES:
        raise TitleScreenError(f"the logo has {len(tiles)} different 8x8 tiles, {len(tiles) - LOGO_MAX_TILES} more than "
                               f"there is room for ({LOGO_MAX_TILES}). tiles which are the same count once")
    for index, tile in enumerate(tilemap):
        data[LOGO_MAP + 2 * index : LOGO_MAP + 2 * index + 2] = tile.to_bytes(2, "little")
    blank = [0] * TILE_SIZE
    for index in range(LOGO_MAX_TILES):
        tile = tiles[index] if index < len(tiles) else blank
        data[LOGO_TILES + index * TILE_SIZE : LOGO_TILES + (index + 1) * TILE_SIZE] = tile
    return len(tiles)
