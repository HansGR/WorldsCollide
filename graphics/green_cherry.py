# UMAROS COLLIDE: the green cherry ultimaro eats before u'ghaaaa (battle/umaros_collide.py puts it where
# final kefka's laughing head was), drawn after the concept art of umaro's green cherries
#
# as it is seen in battle: the stems meet on the left, toward ultimaro. 32x32 pixels, "." is transparent
# and 1-7 are the colors of PALETTE. the animation has 14 tiles of its own, so at least 2 of the 16
# 8x8 tiles must be left empty

PIXELS = [
    "................................",
    "........76......................",
    "........6666....................",
    "..........7.777.................",
    "...........7...77...............",
    "...........7....77..............",
    "............7....77.............",
    "............7.....77............",
    "............7......7............",
    "............7.......7...........",
    "............7.......7...........",
    "...........7........77..........",
    "...........6.........6..........",
    "...........6.........6..........",
    "..........6..........66.........",
    "..........6.......111111111.....",
    ".......111111....14444433331....",
    ".....1144443311.1444544333331...",
    "....14454443333144455443333321..",
    "...144554443333214454433333321..",
    "...144544433333214444333333221..",
    "..1444444333333221333333333221..",
    "..1444443333332221333333332221..",
    "..1333333333332221333333322221..",
    "..1333333333322221333332222221..",
    "..1333333333222221333322222331..",
    "...13333332222221222222222331...",
    "...1333322222233112222223331....",
    "....122222222331..111333111.....",
    ".....1123333311......111........",
    ".......111111...................",
    "................................",
]

PALETTE = [             # red, green, blue
    ( 16,  32,  16),    # 1 outline
    ( 48,  88,  40),    # 2 dark green
    (104, 144,  80),    # 3 green
    (176, 192, 112),    # 4 light green
    (224, 224, 200),    # 5 highlight
    ( 88,  56,  24),    # 6 stem, dark
    (168, 120,  56),    # 7 stem
]

SIZE = 32
TRANSPARENT = "."

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
