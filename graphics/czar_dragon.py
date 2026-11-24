# czardragon's sprite (final_boss/czar_dragon.py): the dragon with wings and a tail that a later
# release of the game gave him, from a picture of it, at its own size (118x111 pixels) in 15 colors
#
# "." is transparent, and 1-f are the colors of PALETTE

PIXELS = [
    ".......................fffffffddddddd.................................................................................",
    ".............................fffffdddddd..............................................................................",
    "..................................fffffddbb...........................................................................",
    ".....................................ffffddbbb........................................................................",
    "......................................fdbffdddbb......................................................................",
    ".......................................fdfdbdfdbbb....................................................................",
    ".......................................fdfbdbdffb9b...................................................................",
    "........................................fdbffffffb9b.....d............................................................",
    "..................ffddddbbbbbbbbbdd.....fddf9ffdffb9b...fd..................d....d....................................",
    "............ffddddbbbb9998855522589bddd.ffdf8ffdfffd9b.f9d........dd.........db.d.....................................",
    ".........ddddddffffffffffffffddbb98899bddfff5dfffffdb9f9d........d.....d......db......................................",
    "......dddfffb99bddb98589bbbddfffffdbbdf258fd59ffddffdbf8f.f......dbb....d..d..dc......................................",
    "....ddfff...ffffffff9852299885899dfffff5bb8f95dfdbddfdd9f..f......ddcb..fbb.b.f6c.....................................",
    "..ddfff.............ffff8225bdd92258bdff8dd9f98ffdfddfdbf..fbb......f8bdfb6cdff4c.....................................",
    ".dff....................fb529b5259bddb99fbddfffdfffdbddfbf..ffb.....fb6effc6eff64c....................................",
    "ff....................bbdff5259995dd928bf558f558dffbbdff9f...fb...dddfb4ceecbdfc14c...................................",
    "...................fdddddddffb99bb5228b9f5bbf58b9bfdddffdbf.ffbebdebcebc144c6bfb616.bd...d.......c..........f.........",
    ".................fffffffffbfffffffbdddfffb8ddd59bffffffdfdfdde9641446bebc6646cbdc64ebb..b....f.cf.c.......ff..........",
    "..........................ffddbfdd889f9ddfb9dff89df288ffffbb8669bbbb9644ebbcc4cebb6bc6ddbe....fafc.c.....fbd..........",
    "...........................fb29d859bdf589ffffdfffbf5bb9fdbffffeb689dffcc4edfb64bcecbdbbdc6....f7cacc....fbd...........",
    "..........................f52dd229bdfdf5ff59bddf2df89bdbdffffdb6edb9defff6cbdb1c6ceccebfec6..fcaf7cac..dbd.........fff",
    "........................ff25d9259dffdffbdd9589fd5bdf9dffdfffdb8debffe6644fffdb16c6eccebbfec8fcacf7c7c.fb8d.......fdff.",
    ".......................fb85d959dff88ff9bbdfdffddb8bdfddff9fdbffbbeec6ccc6116cc616cbfeaffdfbcfccfcac3afb8d......fddf...",
    "......................f85bb55bffb8ddff59ff9b9bf5ddfff559ddbfffdeee66c641bc64411144ebffaaffeafffafc77fd88d.....fddf....",
    ".....................f8bb859ffb988bf95ffdf58bffd559bf5889beeebc666ce6bc61ccebccbcc6fbfcc7cffa7fc7f7fdc6e.....fbbf.....",
    "....................f9d889ff958d95f95ddd9dffdfdbffdddddeebc66146be66cefe6466cb6cedba7effa7afccafc3fcd86e.f..fb8d......",
    "...................fdd89ff95599d58ffd9d89dffbf8bddbbdde6441446cc6eec46ebeebc46c4cbdfc7cc7cfafcacf3afb66e.f.fc8d.......",
    "..................fdb9bfdb889b525fdd8d58bffd859fdffdc66bbeffeb86fdbbeebffbc16ceb66bdfa37cfafa73a7c3fc46bf8fb68d.......",
    ".................fdb9bfd985bb8bddddbf58bffbddbffdddfffddffddb86efdbdfbfdc646bbdbbcdfa7acfca7fca3ac7fc48ec6ec6e........",
    "................fdb9bdb9bb888ffd9bdf85bfdf8b9d98ddfbbdfffdbb8dffdfffbddfdfffdfdbbefc7acffaccafca7cacf4cf6cb68d........",
    "...............db99fd9ffffffffdf8bf95bfbdf59dffff9dfffd5c6cddfb9bdddfdddfffafaffcaaffcaacfffefffa7cfc6bc4ec49.........",
    "..............db9bfbff....ffddffbfb5bddbd59fffdf9df8bffc4ceff2589bffdbbdccfc7cacfffac7ccffbdfbbffcffc9d84e84c..d......",
    ".............dbbdfff.....fddfffdfb59dd9d89dfb9dfdf8bfeb16bfffd9bdfdb9889feca733acc7c7cff8bf8bff9dfacfbe61e66b.dd......",
    "............dbdff.......fddf..dbf95db9bdddff9dfbffffe61ebf8bbdb9bfb825225beffac7aac73afff8bf599f8bfccfe61b69ee6d......",
    "...........dbff........ffdf..d9fd5d9d8d9bfdfffd8feee4bb6efd1159dfd925115bdfcafacfcaa3f9df89fdddff59fcfd84c8bc4e.......",
    "..........bbf..........ddf...d8fb5db89bbdfbdfdffc644eb66efdbb99dfb8551229bdfcfcfccca3fd9dfffdddffb29fffc46eb16d.......",
    ".........dff..........fdf...d59d8dbd5bbdf9dfd9df6ece116bffffb9dffd9825589ddffcfc77c7fdffd985258baf818dff86eb1e........",
    "........df............ff....d8db8db89bddf8fdb9f6efe466bfbbdff5ddfdb95589bdffc737cfaf.fdbfffbdddfcaf8158bf89e4e........",
    ".......df............ff.....8bd8db89b9bfb8fd9bf6fe6ceef1258bbd9bdfdb989ddffa7cfffcf.fddb9df589fbc7fb55b98f8f6e........",
    "......df.............f.....d9db8d9bdb9bf5bfb8f6ffbbfffdd89bddfffdf9989bffaafff.fcfdfddbbdf28bfafafcfb5bbb5fe69d.......",
    "......f..............f.....dbf8ddb9bdbfd5fd98f8fbdfffdbfd28bbdfdfb8558dfccf....fc.fbbddfffffffc7c3afdd5bfb59d8f.......",
    ".........................66bfb8dffdbddfb8fb89fbfbfbfdbbdffdfffe9f82522b.cf......f..fdbbff..faafc7cedfb28fff25df.......",
    ".......................66cebf9df..fddbf8bfb5bffffd9fb6edffdfdc6fb58225b.f........f.fb99bf...fccfacddfd28df7e5bf.......",
    ".................bb9866cc.dfd8f....fdfb8dfb5df.fd9fc4edb9bdd96bf898559d.f...........fb89bf...fffcfb98fdb9dff8f98d.....",
    "................b...bcc...dfbf.....fdf98ffb5df.fdbf4cb12589bddfb9b99bd...f...........ff89db8e46cffb95bfb95dfbfffbbd...",
    "..............bb..........fdbf....ffdf89ffd8f.66ffe6bbf8bdfbd82258ddf..................fb589beefb.fb29feb259d8f.fffff.",
    ".............b............fbf....fdfdf8bf.f8f6edffbcbffb59e1bf95118f.........9.........f9d9b85c.d.fd5dc3cdbb85b.......",
    ".........................ffbf....fdfff8f.6f9fd..fe6cfbdfbfc6cbf8821d........5f44........ff6fff4c...f8ec7efd9982d......",
    ".........................fdf.....ddffb8f6ef9f...fc6fb9bde66c6bf82521d......b9fee6........fc...f6c..f9dccf.ffb95b......",
    ".........................fdf....fdf.f99fd.fbf..db48f85be6cc66bdf52582d....bbdffffb.......fb....f6..fb8dd....fb89......",
    ".........................fdf....fd..f9bf..fd...f1bbf1bd66c64cbffd98588d..dd8b855.fd.......fbd...fb..f8f....dbf98d.....",
    "........................fdf.....df.6f9df..fd..f1bffdbb9bec46cdfdffdb989ddb8ffbe41..........ff...fb..f9fbd.....f9d.....",
    "........................fdf.bb..d.48f9f....f..44ffdbfffdec1cbffbdfffff9bb8b2dffe64...............d..f99f.....dbf......",
    "........................fd....b9668dfbf.bc6f.46fbb5fddfbfb4cddf9bd...fb9bdfb1e..ec6..................ffbd.............",
    ".......................fdf......ccd.fbfb..c44cbfb28fbbd9fd6cdbd9bb....fff9df64...dc...................................",
    ".......................fdf..........fbf....cc9.f5dfdbf9ddbc6f8b8d.......f9d.f6....d...................................",
    ".......................fd...........fbf........fdfb9ff8ddbbcf8b8d.......fb..fb....d...................................",
    ".......................fd...........fdf.6669..fd9ffffe6fb9dfff95f.......f4...d........................................",
    "......................fdf...........fdf9ccc888f9ff9ddc4f98dddfd2f.......fc...f........................................",
    "......................fd..........88fddb...bbdfde8dd946e95dffbfd.........ff...........................................",
    "......................df........99bb.fd......ff96cd9b4cbd9ffdd9d...................f..................................",
    "......................df.......9bb...fd....66446cdb8e4cdfdbdd89d...........ffff....fd.................................",
    "......................f....b..bb.....fd..86bbbbedb5ec6cf8ddbfd59f...........fdbff..ffdd....fdd........................",
    "......................f.....bb........f.9b....ff559e4cef5db8fb929f...fffffffffdbbff.fb9dd..fb9dd......................",
    "......................f...............f.b....fdf29e4cdfdf5d8f8b92f.....fffddbbdfd9bffdb99ffffd99ff..f.................",
    ".......................................b.....dbdfff6efdbdf55ff852df.ffdbbbdffffffffdffffb99bdffd9bf.ff................",
    "............................................db98bddcffd8dbdfddfdf9bdfffffffffddb99dff99bfffdfbb9fdffb9f...............",
    "...........................................db989ffbf9fd8b8ffbdd8df8bdfbbbfdffffffdbdfbddbffffbdd9fddbd9f..f...........",
    "..........................................db85bf.dfd9ff8b5ddf9bd5df5dffddfbbddfddffffffffd9bdfffd9ddddd8ffd...........",
    ".........................................fb85df..df98ff52fdddf5b92bfbdfffdddffffdb99999bdfbdd99bfdfffdbd8fbd..........",
    "........................................fb88d....d98bdbffbddbdf851bdfdfffffffdbb998558259bffdbddbf988ffb8fbd..........",
    ".......................................fb89d....fb59dd9d8bdd9bdfdffd8d9bdfddbbbbbb9885228bdffdbddf9dd9bffd9df.........",
    "......................................fb8bd.....f59bfd5d89bd8b98fbddb5b9bdfffffddbbb9985959ffffbdfbbdddbdfd8ff...f....",
    ".....................................fb8bd.....f98bffb2f98bb5892df9bd92dd8bdbb9ffdb9999985bfbbdfddfdbddbddfdbf..df....",
    "....................................f99d.......f89f.f95fd598d129ddf58952db85d852dffffbdb59f.ffddfffff9bdf988fdff5f....",
    "...................................f9bd.......f98f..f59fd252fd2db9ffdddbfffddffffbbbdfffbdf...ffdfbddf9df9dd8ffb8ff...",
    "..................................f9d........fb8f...f5bfbf29ffdbb8dfdff9fb98899bdfd988bfdf......fffffdfbdbdfd9f8dfbd..",
    ".................................fbd........fb8d...db8df9dfbfbf9b5dfbbfd9fdb9852589d922fbf....dbddb8cfdfddbdddf9df8d..",
    "................................fdf.........f9d....f8bfd8dfdd9f8b2dbf98bb5fdb9855258dffdfddddb85899b4bffdf88ddfbfd5f..",
    "......ffdbbd....................f..........fbd....f8bffb8dbfb5d591d9bfb8995d988895129db95fb98888b44fb6cefd9d9dfff59f..",
    "....ff59b85ddb.............................fb.....f9ffd59d9fb2d281d8bffb582fdb9989825bfdb5d89bddffb6f6f4ffbdf9dfd8bf..",
    "...f59dddffd98dd..........................fbd....f9fdf95bf9d92df82bb5fdffffd9852189899dffddfdfff..f8dbf6ffdfffdf5ddf.f",
    "..fb8d8ff..fddb9d.........................fd.....ffddf59dffff9fff99b2fbfbbffdb9525b92bfdb99852bf..fb.dfcdfdf5ff885dfff",
    "..f9dbf.....ffdb8d...........ffdd.........fd...ffddfff5bfffddff8fd891f9f9fd9ddb989bb8dffdddb9bf....d.f.fddfd95d9d8ff5f",
    ".fdbd9f.......ffd9dd.......ffddffdd.......d..ffdffbbf59dfffd9bf5fbd21f8ffd9bb9889d98bdfddbbffff....f...fdfddb8dbf9f58f",
    ".f5d5b..........ffb9dd...fdbdf....dd......d.fbbbdfffd5bfdffb9dfbf95d2f9ffbbddb99b9bdfffdb988bfdffff...fdf98fd9ddffb8f.",
    ".f9d8d............ffddb9db9f........d......fffdffddf98fdbdf9bfffdf5fdffb9858bddbbdffffdffffdfffb99bddfff9dbffdffdf9bf.",
    ".fdfdf..............fffffff...................ffddbf8bfbffb8d..fddff.fb8555228bdffffdddbfdb98dfdb5259ddfdbdfffb82fbdf.",
    ".f5fbf......................................fddb9bfd8fffff98f..fddf..f9885895229dfbfbbdd8ffdb5dfdfffdfffddffdb8b5fbf..",
    ".f8d95f...................................fdb989bff9bfddfd89f..dbdf...fdb9989b829dfdfb8db5ffdb5dfd9db525db85f9bb8bdf..",
    ".fb9b8d....................................ffffffff9fddffd5b...dbd.....fffdb99b958dfffd8995dfdb5fdb8b98db98dfbb8fdf...",
    ".fd9ff9d...................................fdbdfddfbfffdfd5d...fbd......fdffffbbb989bffd885db9859fd85bdfffdffd9fddf...",
    "..fbddffd...............................fddbbdffdbffdfdf.f8f...db.......fbd...fd989588dffffffdffd9fb52fb985fd9fdb85f..",
    "..fd588f9d............................ffdb9bdfbbf9bdffdf.f9....fb.......fbd....f9589595bffddffbdb98f82fdb985fddb9bf...",
    "...f5bbdf5d.d...........................fbdffdb9fffdffd..f9....fd.......fdb...fbbdb989b95ffbddf9bb5fffffdffffb9bff....",
    "..ffd8bddf8f8d....d.................dddfffffbf9dffbdf.d..fb....fd........f9..d9bdd52955b82ff9bdf852fd9dffdbb8fff......",
    "....ffd58bffbfd...db..............db99bdddfbdfffdd9bf....fd.....d........f9..ff9fff2b82fb5f.f55dfffffb85ddd982bf......",
    "......ddb9bdff9dd.f5b...f..........ff89bdfbdd9ffdf9bd.....f.....d........fb..b4f..f5bd2fd99f.fffb8dfb9885f985ff.......",
    ".....d89dd589df58dfd8b..f9bd...f89bddffdbf9d9fdbf.d9d.....f.....f.........db.e4f..f8bd98fb4bf.fdfd.fff955ffdbb........",
    "....dfffffddbbdfffffd9bd.f98bddfdb9bdff9df8bfdbbf.f9......................fb.f6....f1fc4efb6f.fdbd..fbddd..ffdd.......",
    "..........ff859d599dffffdffb9bfdbdddf9d8dfffdd9df..d.......................d..e6...f4.db1ef6b..d9....fbb.....ffff.....",
    ".........fbdff89b58bd59bbdffff858bdf8bd8bdfbdf8d...f.......................d..fd...dc..db4ff6..f9.....fbd.............",
    "........fbd...fffffdf922589bddfd99bf58bfffd9df8f..................................fb....e6f.f..fb......fb.............",
    "......ddd......fd58bffd989bdf89dddfffdffdfd9f.d.........................................dcf.f...f.......fd............",
    "..............d9dfffffdddddd59bbdfdddbfddffb..f..........................................d......f........f............",
    "............ddbdf...fb9dff.fffffffbd9ffdf..f.............................................d............................",
    ".........ffddff....dbdff.....fbdfd98fd.df.............................................................................",
    ".................ffff........bdf.b8fd..f..............................................................................",
    "............................bdf.fbb...f...............................................................................",
    "..........................ddff..fd....................................................................................",
    "........................ffff...fd.....................................................................................",
]

# (red, green, blue), 0 to 31 each
PALETTE = [
    (29, 28, 24),        # 1
    (24, 22, 21),        # 2
    (30, 18, 14),        # 3
    (25, 23,  9),        # 4
    (20, 18, 17),        # 5
    (21, 18, 11),        # 6
    (25, 12, 11),        # 7
    (15, 15, 13),        # 8
    (12, 12, 10),        # 9
    (19,  8,  7),        # a
    ( 9,  9,  7),        # b
    (12,  8,  4),        # c
    ( 6,  5,  4),        # d
    ( 6,  5,  3),        # e
    ( 1,  0,  0),        # f
]

TRANSPARENT = "."

def pixels():
    # rows of palette indices, 0 is transparent
    return [[0 if pixel == TRANSPARENT else int(pixel, 16) for pixel in row] for row in PIXELS]

def palette():
    # the 16 colors of a monster's palette (the first is not seen)
    return [(0, 0, 0)] + PALETTE
