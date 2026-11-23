# the glow of king pug's lantern (final_boss/king_pug.py puts it where final kefka's laughing head
# was, before goner, over the lantern of his sprite: it is shown and taken away, so the lantern
# lights up and shines)
#
# the picture can be placed in steps of 16 pixels only, so the glass is 4 pixels below its middle
# (and the rays down are that much shorter) to be over the lantern
#
# the lantern's glass as it is in king pug's sprite (graphics/king_pug.py) at 2x (20x8 pixels, in
# the middle of its width), lit: white and yellows for its colors, a halo around it and 20 rays out of it.
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-5 are the colors of PALETTE

PIXELS = [
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "................................",
    "...............55...............",
    "........5......55......5........",
    ".........3.....33.....3.........",
    "5........3.....33.....3........5",
    ".3........2....22....2........3.",
    "..2.......2....22....2.......2..",
    "...2.......2...22...2.......2...",
    "....2......2...22...2......2....",
    "5.....22222222222222222222.....5",
    ".32..2112222113333112222112..23.",
    "...22211222211333311222211222...",
    ".....2112222333333332222112.....",
    "53222211222233333333222211222235",
    "53222211222233222233222211222235",
    ".....2112222332222332222112.....",
    "...22211222211....11222211222...",
    ".32..211222211....112222112..23.",
    "5.....22222222222222222222.....5",
    "....2......2...22...2......2....",
    "...2.......2...22...2.......2...",
    "..2.......2....22....2.......2..",
    ".3........2....22....2........3.",
    "5........3.....33.....3........5",
    ".........3.....33.....3.........",
    "........5......55......5........",
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
GLASS_CENTER = (16, 20)         # in the picture: the middle of the glass (left of this column, above this row)

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
