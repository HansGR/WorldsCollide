# king pug's crown (final_boss/king_pug.py puts it on his head), after the tonberry king's: a
# gold band with five points, a ball on each, and three jewels
#
# "." is not the crown's, "o" its outline, "g" gold, "h" the gold lit, "d" the gold in shade and
# "r" a jewel: final_boss/king_pug.py has which of his colors each is

PIXELS = [
    "...........ohho...........",
    ".......oo..ohho..oo.......",
    "..oo..ohho.ohdo.ohho..oo..",
    ".ohho.ohho.ohdo.ohho.ohho.",
    ".ohho.ohdoohggdoohdo.ohho.",
    ".ohdo.ohdoohggdoohdo.ohdo.",
    ".ohdoohggdohggdohggdoohdo.",
    "ohggdohggdohggdohggdohggdo",
    "ohggdohggdohggdohggdohggdo",
    "ogggghgggghgggghgggghgggdo",
    "ogggrrggggggrrggggggrrggdo",
    "ogggrrggggggrrggggggrrggdo",
    "ogggggggggggggggggggggggdo",
    "oddddddddddddddddddddddddo",
    ".oooooooooooooooooooooooo.",
]

NOT_CROWN = "."

def pixels(colors):
    # rows of palette indices by {character : palette index}, None where the crown is not
    return [[None if pixel == NOT_CROWN else colors[pixel] for pixel in row] for row in PIXELS]
