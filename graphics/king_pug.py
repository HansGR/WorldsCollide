# king pug's sprite (final_boss/king_pug.py shows it at twice this size): pug's at 1.5x, 48x48
# pixels, with 2 rows above it for his crown
#
# the automatic 1.5x of pug's sprite (the scale3x rule, then every 2x2 pixels as one), with these
# drawn by hand: the knife (a cooking knife, its flat back up and its curved edge down), the lantern
# (hanging from a ring he holds, with a crenellated top and bottom and a flame in its glass) and the
# crown (after the tonberry king's: gold for the near points and the band, darker for the far
# points between them)
#
# "." is transparent, and 1-f are colors of pug's palette: but d and e, which are the crown's golds
# (GOLD), the sprite's own being 7 and 8

PIXELS = [
    ".......................1....1....1..............",
    "......................1e1..1e1..1e1.............",
    "......................1e1.11e11.1e1.............",
    ".....................1eee1deeed1eee1............",
    ".....................1eeeddeeeddeee1............",
    ".....................1eeeeeeeeeeeee1............",
    "............111......1ddddddddddddd1............",
    "..........1111111.....1111242441111.............",
    ".........11ccccc11111117222244477711............",
    "........11cccccccc111112222447777711............",
    "........1cc6cc111cccc1122444477777111...........",
    ".......11c66cc11111111722477777777411...........",
    ".......116666c111111177747777777444411..........",
    ".......116666cc11111144774477744422411..........",
    "......1166c6668661117777144777112224a11.........",
    "......116cccc68866117771144471111244111.........",
    "......118ccccc688666c771442411a11aa411..........",
    "......116cccccccc666666c772441112aa71...........",
    "......11c1ccccccccc666667774442222111...........",
    "......11c11ccccccbccc666117444422211............",
    ".......111ccbbbcccbbccc661111444a11c1111........",
    ".......111ccbbbcccbbccc88611174111cc111111......",
    ".......11cccccc666ccbccc86611cc11c6661111111....",
    ".......11ccb66ccc66cc66cbb6611b666681174422111..",
    ".......1ccb6666ccbb6c66bbb861166666811744221111.",
    "......11cbb66886ccb6666bbb88ac66c66811744aaaf11.",
    "......11cbb668a88cbb688666888a11c66a11111aaaa11.",
    "......11cbb188aaccc668886668aa11c66a1111111aa11.",
    "......11cc11118aaccc6668888aa811ccb81111111121..",
    "......11cc1171188cccccc688aaf8c11cc61111111111..",
    "......11c111711888cccc6688aff8c111c66111155551..",
    "......11c111411166ccbb6888affa61111c6111151151..",
    ".......11c11721111cccb66888888611.11111115115111",
    ".......11111222111111111888866611..1111115115111",
    "......11912222a4441111111111111111..111115115111",
    "......11112a77a7115555555555555551...11115555111",
    "......11122a77a11fffffffffffffff51....1111111111",
    "11...111cc27772119ffffffffffffff1.....1313333131",
    "711111111cc77741119fffffffffff551.....1333333331",
    "111111111c11111111199fffffff5511......1111111111",
    "11471188bb11111ccc11199ffff511111.....1faaaaaaf1",
    ".11aa111bbcc666cc1111111111111111.....1faa33aaf1",
    "11144a111ccc66cc111111111ccccc11111...1fa3ff3af1",
    "11144a211c116cc111111111ccbcc666b111.11fa3ff3af1",
    ".11aa44471166c3aa6c11111ccbbb66a366b111faa33aaf1",
    "111a44111166333aa6c11111111111111111111faaaaaaf1",
    "114441111bb66333af3366c1111111111111111111111111",
    "117111111bb66333aaa336cc1111111.......1333333331",
    "11111111111111111111111111111.........1313333131",
    "111....1111111111111111111............1.111111.1",
]

GOLD = {13 : (20, 12, 2), 14 : (31, 23, 4)}     # palette index : (r, g, b), 0 to 31
TRANSPARENT = "."
GLASS_CENTER = (43, 43)     # the middle of the lantern's glass: left of this column, above this row

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel, 16) for pixel in row] for row in PIXELS]
