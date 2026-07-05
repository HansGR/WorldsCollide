"""Hand-curated semantic layer of the door-rando atlas (Stage A).

Everything here is a fact coordinates cannot express. Each entry names
its reason; tools/compile_atlas.py fails the build if an entry becomes
redundant (derivation now agrees) or contradicts the ROM data.
"""

# reason tags
#   sibling   shared/split-exit sibling tiles; curated tile is canonical
#   interior  shared interior serves WoB and WoR; curated (WoR) door is the canonical return
#   world     world-return door (dest_map 511 is dynamic parent map); curated return tile
#   stable    chocobo stables share one interior; all stable tiles return via 1132
#   variant   event-variant twin door occupies the same tile; curated standard door
#   falldown  one-way falldown pairing; no spatially adjacent return exit
#   hans      ambiguous coordinates; resolved by HansGR 2026-07
#   logical-wor partner is the logical WoR copy (base + 4000) of a shared-map door
#   event-door partner is an event-tile door (1500+), not in the vanilla exit table

# {exit id: (vanilla partner, reason tag)}  - overrides coordinate derivation
PARTNER_OVERRIDES = {
    10: (360, 'sibling'),  # Sabin's House WoB
    45: (1132, 'stable'),  # Mobliz Chocobo Stable WoR
    46: (1132, 'stable'),  # Tzen Chocobo Stable WoR
    47: (1132, 'stable'),  # Kohlingen Chocobo Stable WoR
    48: (1267, 'stable'),  # Solitary Island Cid's House
    62: (4658, 'logical-wor'),  # Opera House WoR
    63: (5238, 'logical-wor'),  # Maranda Left Tile WoR
    64: (5238, 'logical-wor'),  # Maranda Right Tile WoR
    65: (5199, 'logical-wor'),  # Nikeah Left Tile WoR
    66: (5200, 'logical-wor'),  # Nikeah Right Tile WoR
    70: (5224, 'logical-wor'),  # Zozo Top Left Tile WoR
    71: (5224, 'logical-wor'),  # Zozo Bottom Left Tile WoR
    72: (5224, 'logical-wor'),  # Zozo Right Tile WoR
    73: (5213, 'logical-wor'),  # Jidoor Left Tile WoR
    74: (5213, 'logical-wor'),  # Jidoor Right Tile WoR
    76: (5240, 'logical-wor'),  # Doma Left Tile WoR
    77: (5240, 'logical-wor'),  # Doma Right Tile WoR
    78: (1546, 'event-door'),  # Ebot's Rock
    144: (4392, 'logical-wor'),  # Narshe School Outside WoR
    269: (1506, 'event-door'),  # Cave to South Figaro to World Map WoB
    272: (1513, 'event-door'),  # Cave to South Figaro Turtle Room to Outside WoB
    375: (365, 'sibling'),  # Mt. Kolts First Room Inside to 1F Outside
    418: (744, 'variant'),  # Doma Interior to Front Outside
    470: (490, 'sibling'),  # Phantom Train Outside Dining Room West  Door
    471: (492, 'sibling'),  # Phantom Train Outside Dining Room East Door
    477: (866, 'sibling'),  # Doma Dream Train Outside Puzzle Room West
    481: (869, 'sibling'),  # Doma Dream Train Outside First Room West
    483: (4502, 'logical-wor'),  # Doma Dream Train Outside Save Point Room
    513: (519, 'hans'),  # Mobliz Mail House Outside WoR
    540: (532, 'sibling'),  # Mt Zozo Inside to Bridge Room West
    558: (555, 'interior'),  # Kohlingen Inn Inside
    559: (553, 'interior'),  # Kohlingen General Store West Inside
    560: (554, 'interior'),  # Kohlingen General Store East Inside
    563: (556, 'interior'),  # Kohlingen Chemist's House Front Door Inside
    564: (557, 'interior'),  # Kohlingen Chemist's House Back Door Inside
    566: (552, 'interior'),  # Kohlingen Rachel's House Inside
    722: (1511, 'event-door'),  # Zone Eater Hallway to Falling Ceiling Room
    726: (1510, 'event-door'),  # Zone Eater Save Point Room West
    793: (1512, 'sibling'),  # Darill's Tomb B2 Water Room Left Top Door
    864: (861, 'sibling'),  # Doma Dream Caves Loop Room South
    885: (1110, 'falldown'),  # Kefka's Tower Falldown Room Left Door
    1046: (1035, 'sibling'),  # Esper Mountain Inside First Room North Door to Outside Loop
    1056: (1039, 'sibling'),  # Esper Mountain Inside Second Room North Door
    1057: (1041, 'sibling'),  # Esper Mountain Inside Final Room Dead End
    1082: (1558, 'event-door'),  # Ancient Cave North to Figaro Castle
    1143: (67, 'world'),  # Narshe To World Map WoR
    1156: (1502, 'event-door'),  # Figaro Castle Outside South to World Map
    1157: (1502, 'event-door'),  # Figaro Castle Outside East to World Map
    1158: (1502, 'event-door'),  # Figaro Castle Outside North to World Map
    1159: (1502, 'event-door'),  # Figaro Castle Outside West to World Map
    1162: (58, 'world'),  # South Figaro West to World Map WoR
    1163: (58, 'world'),  # South Figaro East to World Map WoR
    1164: (58, 'world'),  # South Figaro North to World Map WoR
    1167: (6, 'sibling'),  # South Figaro West to World Map WoB
    1184: (1501, 'event-door'),  # Imperial Camp
    1187: (68, 'world'),  # Crazy Old Man's House to World Map WoR
    1192: (52, 'world'),  # Mobliz East to World Map WoR
    1194: (1561, 'event-door'),  # Veldt Shore South to World Map
    1195: (1561, 'event-door'),  # Veldt Shore East to World Map
    1200: (16, 'sibling'),  # Nikeah East to World Map
    1213: (28, 'sibling'),  # Jidoor South to World Map
    1214: (28, 'sibling'),  # Jidoor West to World Map
    1215: (28, 'sibling'),  # Jidoor East to World Map
    1224: (37, 'sibling'),  # Zozo East to World Map
    1228: (1505, 'event-door'),  # Vector South to World Map
    1238: (31, 'sibling'),  # Maranda South to World Map
    1243: (51, 'world'),  # Tzen South to World Map WoR
    1249: (49, 'world'),  # Albrook West to World Map WoR
    1250: (49, 'world'),  # Albrook North to World Map WoR
    1251: (49, 'world'),  # Albrook Further North to World Map WoR
    1253: (1504, 'event-door'),  # Thamasa After Kefka North to World Map WoB
    1254: (1504, 'event-door'),  # Thamasa After Kefka West to World Map WoB
    1255: (1504, 'event-door'),  # Thamasa After Kefka South to World Map WoB
    1259: (75, 'world'),  # Thamasa North to World Map WoR
    1260: (75, 'world'),  # Thamasa West to World Map WoR
    1261: (75, 'world'),  # Thamasa South to World Map WoR
    1266: (48, 'world'),  # Cid's House East to World Map
    1267: (48, 'world'),  # Cid's House West to World Map
    1268: (48, 'world'),  # Cid's House Northwest to World Map
    1269: (48, 'world'),  # Cid's House North to World Map
    1270: (48, 'world'),  # Cid's House Northeast to World Map
    1272: (1509, 'event-door'),  # Solitary Island Cliff
}

# Exits that exist in the ROM but are unused/unreachable: no partner.
UNUSED_EXITS = {
    80,  # Serpent Trench
    196,  # Cave to South Figaro Siegfried Tunnel West
    273,  # Cave to South Figaro Small Hallway West WoB - vanilla Terra/Locke/Edgar
    274,  # Cave to South Figaro Small Hallway East to Big Room WoB - vanilla Terra/Locke/Edgar
    275,  # Cave to South Figaro Big Room to Turtle Room WoB - vanilla Terra/Locke/Edgar
    276,  # Cave to South Figaro Big Room to Single Chest Room WoB - vanilla Terra/Locke/Edgar
    277,  # Cave to South Figaro Big Room to Small Hallway WoB - vanilla Terra/Locke/Edgar
    278,  # Cave to South Figaro Entrance Room to Small Hallway WoB - vanilla Terra/Locke/Edgar
    279,  # Cave to South Figaro to World Map WoB - vanilla Terra/Locke/Edgar
    280,  # Cave to South Figaro Single Chest Room WoB - vanilla Terra/Locke/Edgar
    281,  # Cave to South Figaro Turtle Room to Big Room WoB - vanilla Terra/Locke/Edgar
    282,  # Cave to South Figaro Turtle Room to Outside WoB - vanilla Terra/Locke/Edgar
    413,  # Doma Poisoning Event - 3F Outside to Inside
    414,  # Doma Poisoning Event - 1F Outside Main Door
    415,  # Doma Poisoning Event - 2F Outside to Main Room
    416,  # Doma Poisoning Event - 2F Outside to Treasure Room
    495,  # Mobliz Left House Basement
    509,  # Mobliz Mail House Outside WoB
    510,  # Mobliz Relic Outside WoB
    511,  # Mobliz Injured Lad Outside WoB
    514,  # Mobliz Relic Outside WoR
    515,  # Mobliz Injured Lad Outside WoR
    590,  # Owzer's Basement Floating Chest Room Door
    638,  # Zozo Tower 6F Single Chest Room Inside
    639,  # Zozo Tower 7F Inside
    640,  # Zozo Tower 10F Inside
    641,  # Zozo Tower 12F Single Chest Room Inside
    644,  # Opera House Balcony To Lobby Left WoR
    645,  # Opera House Balcony To Lobby Right WoR
    651,  # Opera House Balcony To Lobby Left WoB
    652,  # Opera House Balcony To Lobby Right WoB
    655,  # Opera House Balcony To Lobby Left
    656,  # Opera House Balcony To Lobby Right
    665,  # Vector Pub Outside
    666,  # Vector Armor Outside
    667,  # Vector Weapon Outside
    668,  # Vector Healer House Outside
    669,  # Vector Inn Outside
    697,  # Vector Burning Pub Outside
    698,  # Vector Burning Armor Outside
    699,  # Vector Burning Weapon Outside
    700,  # Vector Burning Healer House Outside
    701,  # Vector Burning Inn Outside
    707,  # unused connector to Kefka's Tower?
    708,  # unused connector to Kefka's Tower?
    781,  # Darill's Tomb B2 Turtle Hallway South
    787,  # Darill's Tomb B2 Right Side Secret Room
    803,  # Tzen WoR Collapsing House Outside
    804,  # Tzen Armor Outside WoR
    805,  # Tzen Weapon Outside WoR
    806,  # Tzen Inn Outside WoR
    807,  # Tzen Item Outside WoR
    808,  # Tzen Relic Outside WoR
    809,  # Tzen Armor Outside WoB
    810,  # Tzen Weapon Outside WoB
    811,  # Tzen Inn Outside WoB
    812,  # Tzen Item Outside WoB
    813,  # Tzen Relic Outside WoB
    827,  # Phoenix Cave ?
    840,  # Phoenix Cave ?
    841,  # Phoenix Cave ?
    842,  # Phoenix Cave ?
    843,  # Doma Dream 3 Stooges Maze Northwest Section North Door
    844,  # Doma Dream 3 Stooges Maze Northwest Section South Door
    845,  # Doma Dream 3 Stooges Maze West Section Door
    846,  # Doma Dream 3 Stooges Maze North Section Door
    847,  # Doma Dream 3 Stooges Maze Middle Section Left Door
    848,  # Doma Dream 3 Stooges Maze Middle Section Middle Door
    849,  # Doma Dream 3 Stooges Maze Middle Section Right Door
    852,  # Doma Dream 3 Stooges Maze Northeast Section Right Door
    853,  # Doma Dream 3 Stooges Maze East Section Door
    854,  # Doma Dream 3 Stooges Maze South Section Right Door
    859,  # Doma Dream Cliffs Outside Loop East Door
    862,  # Doma Dream Caves Starting Room to Cliffs
    872,  # Albrook Inn Outside WoB
    873,  # Albrook Weapon Outside WoB
    874,  # Albrook Armor Outside WoB
    875,  # Albrook Item Outside WoB
    876,  # Albrook Pub Outside WoB
    877,  # Albrook Relic Outside WoB
    878,  # Albrook Inn Outside WoR
    879,  # Albrook Weapon Outside WoR
    880,  # Albrook Armor Outside WoR
    881,  # Albrook Item Outside WoR
    882,  # Albrook Pub Outside WoR
    883,  # Albrook Relic Outside WoR
    884,  # Kefka's Tower Falldown Room Entry Right Door 
    905,  # Kefka's Tower 4 Ton Switch Room Middle Upstairs North
    906,  # Kefka's Tower 4 Ton Switch Room Middle Downstairs North
    929,  # Thamasa Kefka Attack Arsenal West Outside WoB
    930,  # Thamasa Kefka Attack Arsenal East Outside WoB
    931,  # Thamasa Kefka Attack Item Outside WoB
    932,  # Thamasa Kefka Attack Relic Outside WoB
    933,  # Thamasa Kefka Attack Strago's House Outside WoB
    934,  # Thamasa Kefka Attack Elder's House Outside WoB
    935,  # Thamasa Kefka Attack Inn Outside WoB
    943,  # Thamasa Arsenal West Outside WoR
    944,  # Thamasa Arsenal East Outside WoR
    945,  # Thamasa Item Outside WoR
    946,  # Thamasa Relic Outside WoR
    947,  # Thamasa Strago's House Outside WoR
    948,  # Thamasa Elder's House Outside WoR
    949,  # Thamasa Inn Outside WoR
    1068,  # Cave to Sealed Gate ?
    1097,  # Ancient Castle Dragon Room Stairs Up
    1130,  # Chocobo Stable Exterior to World Map WoB
    1133,  # Chocobo Stable Exterior to World Map WoR
    1134,  # Narshe To Northern Mines Outside Intro Sequence
    1152,  # Narshe Northern Mines Outside to Inside Intro Sequence
    1153,  # Narshe Northern Mines Outside to Town Intro Sequence
    1185,  # Doma Poisoning Event - Outside to World Map
    1227,  # Vector To Imperial Castle
    1234,  # Vector Burning To Imperial Castle
    1235,  # Vector Burning South to World Map
    1236,  # Magitek Upper Room Conveyor to Lower Room
    1237,  # Magitek Factory Lower Room Unreachable
    1248,  # Albrook South to Docks WoB
    1252,  # Albrook South to Docks WoR
    1256,  # Thamasa North to World Map WoB
    1257,  # Thamasa West to World Map WoB
    1258,  # Thamasa South to World Map WoB
    1273,  # Cid's House Beach with No Fish
}

# Pairings that are intentionally not reciprocal. Tag explains the shape:
#   extra-entrance  partner already pairs two-way with another door
#                   (multi-tile entrances, WoB/WoR shared interiors)
#   dead-return     partner's own exit record is unused/event-variant
#   chain           multi-hop event-mediated pairing
# compile_atlas fails if an entry here has become reciprocal (stale).
ASYMMETRIC_PARTNERS = {
    0: 'dead-return',  # -> 1130 -> None  (Dragon's Eye Chocobo Stable WoB)
    1: 'dead-return',  # -> 1130 -> None  (Figaro Chocobo Stable WoB)
    2: 'dead-return',  # -> 1130 -> None  (Tzen Chocobo Stable WoB)
    3: 'dead-return',  # -> 1130 -> None  (Maranda Chocobo Stable WoB)
    45: 'chain',  # -> 1132 -> 1131  (Mobliz Chocobo Stable WoR)
    46: 'chain',  # -> 1132 -> 1131  (Tzen Chocobo Stable WoR)
    47: 'chain',  # -> 1132 -> 1131  (Kohlingen Chocobo Stable WoR)
    54: 'extra-entrance',  # -> 1199 -> 16  (Nikeah Left Tile WoR)
    55: 'extra-entrance',  # -> 1199 -> 16  (Nikeah Right Tile WoR)
    129: 'extra-entrance',  # -> 123 -> 97  (Narshe Inn Outside WoR)
    130: 'extra-entrance',  # -> 128 -> 98  (Narshe Treasure Room Outside WoR)
    131: 'extra-entrance',  # -> 116 -> 99  (Narshe Weapon Outside WoR)
    132: 'extra-entrance',  # -> 122 -> 100  (Narshe Relic Outside WoR)
    133: 'extra-entrance',  # -> 126 -> 101  (Narshe Elder House Outside WoR)
    134: 'extra-entrance',  # -> 127 -> 102  (Narshe Cursed Shld House Outside WoR)
    135: 'extra-entrance',  # -> 121 -> 103  (Narshe Item Outside WoR)
    136: 'extra-entrance',  # -> 119 -> 104  (Narshe Armor Left Outside WoR)
    137: 'extra-entrance',  # -> 120 -> 105  (Narshe Armor Right Outside WoR)
    138: 'extra-entrance',  # -> 124 -> 106  (Narshe Arvis House Left Outside WoR)
    139: 'extra-entrance',  # -> 125 -> 107  (Narshe Arvis House Right Outside WoR)
    283: 'extra-entrance',  # -> 317 -> 295  (South Figaro Rich Man's House Outside WoR)
    284: 'extra-entrance',  # -> 318 -> 296  (South Figaro Rich Man's House Side Door Outside WoR)
    285: 'extra-entrance',  # -> 338 -> 297  (South Figaro Rich Man's House Secret Back Door Outside WoR)
    286: 'extra-entrance',  # -> 342 -> 298  (South Figaro Secret Door Behind Duncan's House Outside WoR)
    287: 'extra-entrance',  # -> 343 -> 299  (South Figaro Cider House Hidden Back Door Outside WoR)
    288: 'extra-entrance',  # -> 344 -> 300  (South Figaro Cider House Main Door Outside WoR)
    289: 'extra-entrance',  # -> 307 -> 301  (South Figaro Relic Outside WoR)
    290: 'extra-entrance',  # -> 316 -> 302  (South Figaro Pub Outside WoR)
    291: 'extra-entrance',  # -> 311 -> 303  (South Figaro Armory West Outside WoR)
    292: 'extra-entrance',  # -> 312 -> 304  (South Figaro Armory East Outside WoR)
    293: 'extra-entrance',  # -> 337 -> 305  (South Figaro Item Outside WoR)
    294: 'extra-entrance',  # -> 345 -> 306  (South Figaro Duncan's House Outside WoR)
    417: 'dead-return',  # -> 413 -> None  (Doma 3F Inside to 3F Outside)
    419: 'dead-return',  # -> 415 -> None  (Doma Interior to 2F Outside)
    460: 'extra-entrance',  # -> 412 -> 411  (Crazy Old Man's House Outside to Inside WoR)
    466: 'extra-entrance',  # -> 461 -> 462  (Phantom Forest Fork Room to North Room)
    467: 'extra-entrance',  # -> 465 -> 21  (Phantom Forest Room Before Train to Fork)
    513: 'extra-entrance',  # -> 519 -> 521  (Mobliz Mail House Outside WoR)
    546: 'extra-entrance',  # -> 566 -> 552  (Kohlingen Rachel's House Outside WoB)
    547: 'extra-entrance',  # -> 559 -> 553  (Kohlingen General Store West Outside WoB)
    548: 'extra-entrance',  # -> 560 -> 554  (Kohlingen General Store East Outside WoB)
    549: 'extra-entrance',  # -> 558 -> 555  (Kohlingen Inn Outside WoB)
    550: 'extra-entrance',  # -> 563 -> 556  (Kohlingen Chemist's House Front Door Outside WoB)
    551: 'extra-entrance',  # -> 564 -> 557  (Kohlingen Chemist's House Back Door Outside WoB)
    687: 'extra-entrance',  # -> 1233 -> 686  (Imperial Castle Right Door Behind Throne)
    743: 'chain',  # -> 417 -> 413  (Doma 3F Outside to Inside)
    745: 'chain',  # -> 419 -> 415  (Doma 2F Outside to Main Room)
    922: 'extra-entrance',  # -> 950 -> 936  (Thamasa After Kefka Arsenal West Outside WoB)
    923: 'extra-entrance',  # -> 951 -> 937  (Thamasa After Kefka Arsenal East Outside WoB)
    924: 'extra-entrance',  # -> 953 -> 938  (Thamasa After Kefka Item Outside WoB)
    925: 'extra-entrance',  # -> 958 -> 939  (Thamasa After Kefka Relic Outside WoB)
    926: 'extra-entrance',  # -> 955 -> 940  (Thamasa After Kefka Strago's House Outside WoB)
    927: 'extra-entrance',  # -> 954 -> 941  (Thamasa After Kefka Elder's House Outside WoB)
    928: 'extra-entrance',  # -> 952 -> 942  (Thamasa After Kefka Inn Outside WoB)
    1132: 'extra-entrance',  # -> 1131 -> 1129  (Chocobo Stable Exterior to Inside WoR)
    1165: 'extra-entrance',  # -> 1173 -> 1170  (South Figaro To Docks WoR)
    1166: 'extra-entrance',  # -> 1172 -> 1171  (South Figaro To Chocobo Stable WoR)
}
