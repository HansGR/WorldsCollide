# the skull shown in front of negarapa before last rites (final_boss/negarapa.py puts it where final
# kefka's laughing head was: it is shown and fades away). it is his head as it is in the rom, in
# other colors: its four lighter colors are bone and its two darkest the skin that hangs off
# it, as what trails under the head is. an eye socket, a nose hole and teeth are drawn into it
#
# as it is seen in battle: 32x32 pixels, "." is transparent and 1-7 are the colors of PALETTE

PIXELS = [
    ".....77.11.116677...............",
    "....7.11677765456777............",
    "..7711655165553333667...........",
    ".7..161616655551114567766116....",
    "6..7176557676311111376543251....",
    "..6564557435731111136461551.....",
    ".6553667755343111113131541......",
    ".65265677656544111455611751.....",
    "65345676755654333317711117......",
    "654347776736776456776451647.....",
    "76246777564671756141116331......",
    "66364775175767777514233561......",
    "556461417667567171116777711.....",
    "56645131561764745654117771111...",
    "67554152121212121215361777161...",
    "7756316212121212121663611165511.",
    "57676711111111111111765544366461",
    "66676711212121212125756776544671",
    ".167771121212121212346445547711.",
    ".7767155545555717755445561777...",
    "..77176664454467111555617677....",
    "...771666645335666777716777.....",
    "..16761667666666676111777.......",
    "..177617.66.6..6666777777.......",
    "71677717........66776677........",
    "76677676........6.66676.........",
    "66676776.........66.67..........",
    "6666776..........6.666..........",
    "6777776..........6...6..........",
    "6767716..........6...6..........",
    "666777..........................",
    "...77...........................",
]

PALETTE = [
    ( 24,  16,   8),
    (248, 240, 216),
    (224, 208, 168),
    (184, 168, 136),
    (136, 120, 104),
    (136,  48,  72),
    ( 72,  24,  48),
]
# 1 black, 2 to 5 bone (light to dark), 6 and 7 skin

SIZE = 32
TRANSPARENT = "."

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel) for pixel in row] for row in PIXELS]

def palette():
    # the 8 colors of a battle animation palette (15 bit, 5 each of blue, green and red), the first is unused
    return [0] + [(red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10) for red, green, blue in PALETTE]
