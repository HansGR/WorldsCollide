# monster (battle) sprites
#
# a monster's graphics are 8x8 tiles, 4 bits per pixel (32 bytes: bitplanes 0 and 1 interleaved by row,
# then bitplanes 2 and 3) or 3 (24 bytes: bitplane 2 alone, a byte per row). a mold is a bitmap of which
# tiles of an 8x8 (small) or 16x16 (large) grid the monster has, a row at a time from the top left, and
# the graphics are those tiles in that order

TILE_PIXELS = 8
TILE_SIZE_3BPP = 24
TILE_SIZE_4BPP = 32

SMALL_MOLD_TILES = 8
LARGE_MOLD_TILES = 16

def mold_size(tiles):
    return tiles * tiles // 8

def tile_pixels(data, three_bpp = False):
    # rows of palette indices of one tile
    pixels = []
    for y in range(TILE_PIXELS):
        planes = [data[2 * y], data[2 * y + 1]]
        if three_bpp:
            planes += [data[16 + y], 0]
        else:
            planes += [data[16 + 2 * y], data[17 + 2 * y]]
        pixels.append([sum(((plane >> (7 - x)) & 1) << index for index, plane in enumerate(planes))
                       for x in range(TILE_PIXELS)])
    return pixels

def tile_data(pixels, three_bpp = False):
    # graphics of one tile
    data = [0] * (TILE_SIZE_3BPP if three_bpp else TILE_SIZE_4BPP)
    for y in range(TILE_PIXELS):
        offsets = (2 * y, 2 * y + 1, 16 + y) if three_bpp else (2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)
        for x in range(TILE_PIXELS):
            for plane, offset in enumerate(offsets):
                data[offset] |= ((pixels[y][x] >> plane) & 1) << (7 - x)
    return data

def mold_tile_count(mold):
    return sum(bin(byte).count("1") for byte in mold)

def sprite_pixels(mold, tiles, graphics, three_bpp = False):
    # rows of palette indices (0 is transparent) of the sprite of tiles x tiles tiles with this mold
    tile_size = TILE_SIZE_3BPP if three_bpp else TILE_SIZE_4BPP
    pixels = [[0] * (tiles * TILE_PIXELS) for _ in range(tiles * TILE_PIXELS)]
    offset = 0
    for row in range(tiles):
        for column in range(tiles):
            bit = row * tiles + column
            if not mold[bit // 8] & (0x80 >> (bit % 8)):
                continue
            tile = tile_pixels(graphics[offset : offset + tile_size], three_bpp)
            offset += tile_size
            for y in range(TILE_PIXELS):
                pixels[row * TILE_PIXELS + y][column * TILE_PIXELS : (column + 1) * TILE_PIXELS] = tile[y]
    return pixels

def sprite_data(pixels, no_empty_rows = False):
    # the mold and 4bpp graphics of a sprite (a square of 8 or 16 tiles a side), without its empty tiles.
    # the battle takes the height of a monster to be the rows of its mold before the first empty one:
    # no_empty_rows keeps an empty tile in each row of tiles that has none, down to the sprite's last
    tiles = len(pixels) // TILE_PIXELS
    mold = [0] * mold_size(tiles)
    graphics = []

    def tile_at(row, column):
        return [pixels[row * TILE_PIXELS + y][column * TILE_PIXELS : (column + 1) * TILE_PIXELS]
                for y in range(TILE_PIXELS)]
    def used(row, column):
        return any(any(tile_row) for tile_row in tile_at(row, column))
    used_rows = [row for row in range(tiles) if any(used(row, column) for column in range(tiles))]

    for row in range(tiles):
        kept_empty = no_empty_rows and used_rows and row < used_rows[-1] and row not in used_rows
        for column in range(tiles):
            if used(row, column) or (kept_empty and column == 0):
                bit = row * tiles + column
                mold[bit // 8] |= 0x80 >> (bit % 8)
                graphics += tile_data(tile_at(row, column))
    return mold, graphics

def without_shadow(pixels, shadow_color, rows):
    # a sprite's shadow is a patch of its outline color under its feet. in these rows of the sprite (a
    # range, or how many of its last rows), the pixels of that color which touch no other color are
    # removed if they are open to the outside of the sprite: what remains outlines the feet, and the
    # dark inside of the sprite stays
    height, width = len(pixels), len(pixels[0])
    if isinstance(rows, int):
        rows = range(height - rows, height)

    def is_shadow(x, y):
        return y in rows and pixels[y][x] == shadow_color and not any(
            pixels[ny][nx] not in (0, shadow_color)
            for ny in range(max(y - 1, 0), min(y + 2, height))
            for nx in range(max(x - 1, 0), min(x + 2, width)))
    shadow = {(x, y) for y in rows for x in range(width) if is_shadow(x, y)}

    def neighbors(x, y):
        return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    def outside(x, y):
        return not (0 <= x < width and 0 <= y < height) or not pixels[y][x]

    # from the shadow's pixels at the edge of the sprite inward
    removed = {pixel for pixel in shadow if any(outside(*neighbor) for neighbor in neighbors(*pixel))}
    frontier = list(removed)
    while frontier:
        for neighbor in neighbors(*frontier.pop()):
            if neighbor in shadow and neighbor not in removed:
                removed.add(neighbor)
                frontier.append(neighbor)

    return [[0 if (x, y) in removed else pixel for x, pixel in enumerate(row)] for y, row in enumerate(pixels)]

def scale(pixels, factor):
    return [[pixel for pixel in row for _ in range(factor)] for row in pixels for _ in range(factor)]
