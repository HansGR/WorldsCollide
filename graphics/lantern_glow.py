# the glow of king pug's lantern (final_boss/king_pug.py puts it where final kefka's laughing head
# was, before goner, over the lantern of his sprite: it is shown and taken away, so the lantern
# lights up and shines)
#
# the picture can be placed in steps of 16 pixels only, so the glass is 4 pixels above its middle
# (and the rays up are that much shorter) to be over the lantern
#
# the lantern's glass as it is in king pug's sprite (graphics/king_pug.py) at 2x (16x12 pixels, in
# the middle of its width), lit: white and yellows for its colors, a halo around it and 20 rays out of it.
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-5 are the colors of PALETTE

PIXELS = [
    "..3......3.....33.....3......3..",
    "...3......2....22....2......3...",
    "....2.....2....22....2.....2....",
    ".....2.....2...22...2.....2.....",
    "......2....2...22...2....2......",
    "........2222222222222222........",
    ".53....211222222222222112....35.",
    "...32..211222222222222112..23...",
    ".....2221122223333222211222.....",
    ".......211222233332222112.......",
    ".......211223311113322112.......",
    "53322222112233111133221122222335",
    "53322222112233111133221122222335",
    ".......211223311113322112.......",
    ".......211222233332222112.......",
    ".....2221122223333222211222.....",
    "...32..211222222222222112..23...",
    ".53....211222222222222112....35.",
    "........2222222222222222........",
    "......2....2...22...2....2......",
    ".....2.....2...22...2.....2.....",
    "....2.....2....22....2.....2....",
    "...3......2....22....2......3...",
    "..3......3.....33.....3......3..",
    ".5.......3.....33.....3.......5.",
    "........5......55......5........",
    "...............55...............",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
]

PALETTE = [
    (248, 248, 248),        # 1 white
    (248, 248, 168),        # 2 pale yellow
    (248, 224,  72),        # 3 yellow
    (248, 168,  40),        # 4 orange
    (240, 200, 120),        # 5 the ends of the rays
    (  0,   0,   0),
    (  0,   0,   0),
]

SIZE = 32
TRANSPARENT = "."
GLASS_CENTER = (16, 12)         # in the picture: the middle of the glass (left of this column, above this row)

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
