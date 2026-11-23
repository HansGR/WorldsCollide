# the glow of king pug's lantern (final_boss/king_pug.py puts it where final kefka's laughing head
# was, before goner, over the lantern of his sprite: it is shown and taken away, so the lantern
# lights up and shines)
#
# the lantern's glass as it is in pug's sprite at 3x (21x12 pixels, in the middle), lit: white and
# yellows for its colors and orange for its dark frame, a halo around it and 16 rays out of it.
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-5 are the colors of PALETTE

PIXELS = [
    "................................",
    "...............55...............",
    "......5........55........5......",
    ".......3.......33.......3.......",
    ".......3.......33.......3.......",
    "5.......2......22......2.......5",
    ".3......2......22......2......3.",
    "..2......2.....22.....2......2..",
    "...2.....2.....22.....2.....2...",
    ".....222222222222222222222......",
    "....21114444444444444441112.....",
    "....21114444444444444441112.....",
    "....21114444444444444441112.....",
    "....21112221113331112221112.....",
    "....21112221113331112221112.....",
    "532221112221113331112221112.2235",
    "532221112223332223332221112.2235",
    "....21112223332223332221112.....",
    "....21112223332223332221112.....",
    "....21112221114441112221112.....",
    "....21112221114441112221112.....",
    "....21112221114441112221112.....",
    ".....222222222222222222222......",
    "...2.....2.....22.....2.....2...",
    "..2......2.....22.....2......2..",
    ".3......2......22......2......3.",
    "5.......2......22......2.......5",
    ".......3.......33.......3.......",
    ".......3.......33.......3.......",
    "......5........55........5......",
    "...............55...............",
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
GLASS_CENTER = (15.5, 15.5)     # in the picture: the middle of the glass

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
