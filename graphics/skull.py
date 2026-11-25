# the skull shown in front of negarapa before last rites (final_boss/negarapa.py puts it where final
# kefka's laughing head was: it is shown and fades away). the shape of his head is kept: a floating
# head, and what trails under it
#
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-7 are the colors of PALETTE

PIXELS = [
    ".............777777.............",
    ".........77752223337777.........",
    ".......772225233335333377.......",
    "......72222523333335333337......",
    ".....7222222333333353333447.....",
    "....722222233333333353344447....",
    "...72255223333333333334455447...",
    "...72225551553333335515554447...",
    "...72251115115333351151115447...",
    "...72511111111533511111111547...",
    "...72511111111533511111111547...",
    "...73511166111534511166111547...",
    "...73511166111544511166111547...",
    "...73351111115444451111115447...",
    "....733551155441144551155457....",
    ".....7333333441111444444457.....",
    "......73333444111144444457......",
    ".......734444441144444457.......",
    "........7555555555555557........",
    ".........72212212212217.........",
    ".........72212212212217.........",
    "..........731331331337..........",
    "..........777777777777..........",
    ".......577555545545555775.......",
    "........5734555335554375........",
    ".........55344.33.44355.........",
    "..........53.34..43.35..........",
    "..........543.3..3.345..........",
    "..........4...4..4...4..........",
    "..........3...3..3...3..........",
    "................................",
    "................................",
]

PALETTE = [
    ( 16,   8,  16),
    (248, 248, 232),
    (224, 216, 184),
    (176, 160, 136),
    (112,  96, 104),
    (232,  40,  32),
    ( 56,  32,  56),
]
# 1 black (the sockets), 2 white, 3 bone, 4 bone in shadow, 5 dark, 6 red (the glow in the sockets), 7 the outline

SIZE = 32
TRANSPARENT = "."

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
