# king pug's sprite (final_boss/king_pug.py shows it at twice this size): pug's at 1.5x, 48x48
# pixels, with his crown
#
# the automatic 1.5x of pug's sprite (the scale3x rule, then every 2x2 pixels as one), with a crown
# drawn by hand at that size, so its pixels are as large as his (after the tonberry king's: gold
# for the near points and the band, darker for the far points between them)
# its black outline, 2 pixels wide at 1.5x, is taken down to 1 (and the gap that leaves between
# the hand of his lantern and his body is filled)
#
# "." is transparent, and 1-f are colors of pug's palette: but d and e, which are the crown's golds
# (GOLD), the sprite's own being 7 and 8

PIXELS = [
    "........................1...1...1...............",
    ".......................1e1.1e1.1e1..............",
    ".......................1e111e111e1..............",
    "......................1ee1deeed1ee1.............",
    "......................1eeddeeeddee1.............",
    "..........1111111.....1eeeeeeeeeee1.............",
    ".........11ccccc111...1ddddddddddd1.............",
    "........11cccccccc11111222244777771.............",
    "........1cc6cc111cccc112244447777711............",
    "........1c66cc11111111722477777777411...........",
    "........16666c11111117774777777744441...........",
    ".......116666cc11111144774477744422411..........",
    ".......166c6668661117777144777112224a1..........",
    ".......16cccc6886611777114447111124411..........",
    ".......18ccccc688666c771442411a11aa41...........",
    ".......16cccccccc666666c772441112aa71...........",
    ".......1c1ccccccccc666667774442222111...........",
    ".......1c11ccccccbccc666117444422211............",
    ".......111ccbbbcccbbccc661111444a11c1...........",
    "........11ccbbbcccbbccc88611174111cc1111........",
    "........1cccccc666ccbccc86611cc11c6661111111....",
    ".......11ccb66ccc66cc66cbb6611b6666811744221....",
    ".......1ccb6666ccbb6c66bbb86116666681174422111..",
    ".......1cbb66886ccb6666bbb88ac66c66811744aaaf1..",
    ".......1cbb668a88cbb688666888a11c66a11111aaaa1..",
    ".......1cbb188aaccc668886668aa11c66a1111111aa1..",
    ".......1cc11118aaccc6668888aa811ccb81111111121..",
    ".......1cc1171188cccccc688aaf8c11cc6111111111...",
    ".......1c111711888cccc6688aff8c111c661111111....",
    ".......1c111411166ccbb6888affa61111c61111555....",
    ".......11c11721111cccb6688888861..111111151151..",
    ".......1111122211111111188886661....111111111111",
    ".......1912222a4441111111b6666c1.....13a11a11aa3",
    ".......1112a77a711195551111bbb11.....11113333111",
    ".......1122a77a1199955551111111.......1111111111",
    "11....11cc277721199955555591111.......f.11111..f",
    "71...1111cc7774111fffff555555111......faaf33faaf",
    "111111111c11111111fffffff5555991......faa3333aaf",
    ".1471188bb11111cccffffffffff5591......faa3aa3aaf",
    ".11aa111bbcc666cc11111111ccccc11......faaf11faaf",
    ".1144a111ccc66cc111111111ccccc1111....111f11f111",
    ".1144a211c116cc111111111ccbcc666b111.1111.cc1111",
    "..1aa44471166c3aa6c11111ccbbb66a366b113a11111aa3",
    ".11a44111166333aa6c11111111111111111111111111113",
    ".14441111bb66333af3366c11111111......1111333311.",
    ".17111111bb66333aaa336cc11111.........111111111.",
    ".111...1111111111111111111.............111111...",
    "................................................",
]

GOLD = {13 : (20, 12, 2), 14 : (31, 23, 4)}     # palette index : (r, g, b), 0 to 31
TRANSPARENT = "."
GLASS_CENTER = (43, 38)     # the middle of the lantern's glass: left of this column, above this row

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel, 16) for pixel in row] for row in PIXELS]
