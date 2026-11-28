# the glow of king pug's lantern (final_boss/king_pug.py puts it where final kefka's laughing head
# was, before goner, over the lantern of his sprite: it is shown and taken away, so the lantern
# lights up and shines)
#
# the picture can be placed in steps of 16 pixels only: his sprite is placed so that its lantern is
# under the glass of this picture, which is in its middle
#
# the lantern's glass as it is in king pug's sprite (graphics/king_pug.py: 21x16 pixels), lit: white
# and yellows for its colors, a halo around it and 20 rays out of it.
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-5 are the colors of PALETTE

PIXELS = [
    "................................",
    "........5......55......5........",
    ".........3.....33.....3.........",
    "5........3.....33.....3........5",
    ".3........2....22....2........3.",
    "..2.......2....22....2.......2..",
    "...2.......2...22...2.......2...",
    "....2222222222222222222222.2....",
    "....2..32223333333322223..2.....",
    "....2..22222222221222223..2.....",
    "5...2..2333211221122333...2....5",
    ".32.2..22..333333333..22..2..23.",
    "...22..22223333233332222..222...",
    "....2..22112221112311122..2.....",
    "....2.2111221113331122112.2.....",
    "53222.2112221133331112112.222235",
    "53222.2122211333331112212.222235",
    "....2.2122112331131122112.2.....",
    "....2.2112113321233112112.2.....",
    "...22.2112213312332112212.222...",
    ".32.2..22222232333322222..2..23.",
    "5...2..222...23333...222..2....5",
    "....2..2.....3333......2..2.....",
    "....2..3.....31112.....3..2.....",
    "....2222222222222222222222.2....",
    "...2.......2...22...2.......2...",
    "..2.......2....22....2.......2..",
    ".3........2....22....2........3.",
    "5........3.....33.....3........5",
    ".........3.....33.....3.........",
    "........5......55......5........",
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
GLASS_CENTER = (15, 15)         # in the picture: the middle of the glass (this column, between this row and the next)

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
