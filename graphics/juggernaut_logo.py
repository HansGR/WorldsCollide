# what is shown over juggernaut before soul flare (final_boss/juggernaut.py puts it where final
# kefka's laughing head was, over the logo on his nose: it is shown and taken away): the logo glows,
# and rays go up and to the right from it
#
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-6 are the colors of PALETTE

PIXELS = [
    "................................",
    "................................",
    "................................",
    "................................",
    "............................6...",
    "...........................6....",
    ".....................6....55....",
    ".....................5....5.....",
    "....................5....55.....",
    "....................5....4......",
    "....................4...44......",
    "....................4...4.....6.",
    "...................44..44....5..",
    "...................4...3....5...",
    "...................3..3....4....",
    "...................3..3...4.....",
    "...................3.3...45.....",
    "...............5.533.2..34...66.",
    "............5.44442.2..34...56..",
    "...........5.43333242523..44....",
    "............43222222323.34......",
    "...........4322213122333........",
    "..........5432211311224.........",
    "...........4323313331234........",
    "............43443133134.........",
    "...........5.4.431111234........",
    "..............54311122345.......",
    "...............543332345........",
    "................5443234.........",
    ".................5.434..........",
    "..................5.4.5.........",
    "................................",
]

PALETTE = [
    (248, 248, 240),        # 1 white
    (248, 216, 168),        # 2 pale orange
    (248, 136,  88),        # 3 bright red
    (232,  56,  40),        # 4 red
    (168,  24,  24),        # 5 dark red
    (104,  16,  24),        # 6 darker red
    (  0,   0,   0),
]

SIZE = 32
TRANSPARENT = "."
LOGO = (13, 20)             # its top left in the picture

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
