#rooms - series of doors.  [ [2-way doors], [1-way exits], [1-way entrances], require_world?]

room_data = {
    # 'root-code' rooms are terminal entrance rooms for randomizing individual sections.
    # They are also used in Dungeon Crawl mode.
    'root-u' : [ [], [2010], [3009], None], # Root map for -door-randomize-umaro
    'root-unb' : [ [1138], [], [], 0], # Root map for -door-randomize-upper-narshe-wob
    'root-unr' : [ [1146], [], [], 1], # Root map for -door-randomize-upper-narshe-wor
    'root-em' : [ [44], [], [], 0], # Root map for -door-randomize-esper-mountain
    'root-ob' : [ [593], [], [], 1], # Root map for -door-randomize-owzer's basement
    'root-mf' : [ [1229], [ ], [3028], 0],     # Magitek Factory root entrance in Vector

    2 : [ [81], [ ], [ ], None], #Blackjack Outside
    3 : [ [82, 83], [ ], [ ], None], #Blackjack Gambling Room
    4 : [ [84, 85, 87], [ ], [ ], None], #Blackjack Party Room
    5 : [ [86], [ ], [ ], None], #Blackjack Shop Room
    6 : [ [88, 89], [ ], [ ], None], #Blackjack Engine Room
    7 : [ [90], [ ], [ ], None], #Blackjack Parlor Room
    8 : [ [91], [ ], [ ], None], #Falcon Outside
    9 : [ [92, 93, 95], [ ], [ ], None], #Falcon Main Room
    10 : [ [94], [ ], [ ], None], #Falcon Small Room
    11 : [ [96], [ ], [ ], None], #Falcon Engine Room
    12 : [ [1129], [ ], [ ], None], #Chocobo Stable Exterior WoB
    13 : [ [1131], [ ], [ ], None], #Chocobo Stable Interior
    14 : [ [1132], [ ], [ ], None], #Chocobo Stable Exterior WoR

    16 : [ [97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 108, 112, 1135, 1136], [ ], [ ], None], #Narshe Outside WoB
    17 : [ [107, 111], [ ], [ ], None], #Narshe Outside Behind Arvis to Mines WoB
    18 : [ [109, 110], [ ], [ ], None], #Narshe South Caves Secret Passage Outside WoB
    19 : [ [113, 114], [ ], [ ], None], #Narshe Northern Mines 2nd/3rd Floor Outside WoB
    20 : [ [115, 1139], [ ], [ ], None], #Narshe Northern Mines 3rd Floor Outside WoB
    21 : [ [1137, 1138], [ ], [ ], None], #Narshe Northern Mines 1st Floor Outside WoB
    22 : [ [1140, 1141], [ ], [ ], None], #Snow Battlefield WoB
    23 : [ [1142], [ ], [ ], None], #Narshe Peak WoB
    24 : [ [116, 117], [ ], [ ], None], #Narshe Weapon Shop
    25 : [ [118], [ ], [ ], None], #Narshe Weapon Shop Back Room
    26 : [ [119, 120], [ ], [ ], None], #Narshe Armor Shop
    27 : [ [121], [ ], [ ], None], #Narshe Item Shop
    28 : [ [122], [ ], [ ], None], #Narshe Relic Shop
    29 : [ [123], [ ], [ ], None], #Narshe Inn
    30 : [ [124, 125], [ ], [ ], None], #Narshe Arvis House
    31 : [ [126], [ ], [ ], None], #Narshe Elder House
    32 : [ [127], [ ], [ ], None], #Narshe Cursed Shld House
    33 : [ [128], [ ], [ ], None], #Narshe Treasure Room
    34 : [ [129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 140, 144, 1143, 1144], [ ], [ ], None], #Narshe Outside WoR
    35 : [ [139, 143], [ ], [ ], None], #Narshe Outside Behind Arvis to Mines WoR
    36 : [ [141, 142], [ ], [ ], None], #Narshe South Caves Secret Passage Outside WoR
    37 : [ [145, 146], [ ], [ ], None], #Narshe Northern Mines 2nd/3rd Floor Outside WoR
    '37a' : [ [145, 146], [ ], [3009], None], #Narshe Northern Mines 2nd/3rd Floor Outside WoR incl. exit from Umaro's cave
    38 : [ [147, 1147], [ ], [ ], None], #Narshe Northern Mines 3rd Floor Outside WoR
    39 : [ [1145, 1146], [ ], [ ], None], #Narshe Northern Mines 1st Floor Outside WoR
    40 : [ [1148, 1149], [ ], [ ], None], #Snow Battlefield WoR
    41 : [ [1150], [ ], [ ], None], #Narshe Peak WoR
    '41a' : [ [1150], [2010], [], None], # Narshe Peak WoR incl. entrance to Umaro's cave
    42 : [ [148, 149], [ ], [ ], None], #Narshe Northern Mines 1F Side/East Room WoR
    43 : [ [150, 151], [ ], [ ], None], #Narshe Northern Mines 2F Inside WoR
    44 : [ [152, 153], [ ], [ ], None], #Narshe Northern Mines 3F Inside WoR
    45 : [ [154, 155], [ ], [ ], None], #Narshe South Caves Secret Passage 1F WoR
    46 : [ [156, 157, 1151], [ ], [ ], None], #Narshe Northern Mines Main Hallway WoR
    47 : [ [158], [ ], [ ], None], #Narshe Northern Mines Tritoch Room WoR
    48 : [ [159, 160], [ ], [ ], None], #Narshe 3-Party Cave WoR
    49 : [ [161, 162, 163, 164], [ ], [ ], None], #Narshe South Caves WoR
    50 : [ [165, 166], [ ], [ ], None], #Narshe Checkpoint Room WoR
    51 : [ [167, 168], [ ], [ ], None], #Narshe South Caves Secret Passage 3F WoR

    53 : [ [169, 170], [ ], [ ], None], #Narshe Northern Mines Side Room 1F WoB
    54 : [ [171, 172], [ ], [ ], None], #Narshe Northern Mines Side Room 2F WoB
    55 : [ [173, 174], [ ], [ ], None], #Narshe Northern Mines Inside 3F WoB
    56 : [ [175, 176], [ ], [ ], None], #Narshe South Caves Secret Passage 1F WoB


    59 : [ [178, 179, 1155], [ ], [ ], None], #Narshe Northern Mines Main Hallway WoB
    60 : [ [180], [ ], [ ], None], #Narshe Northern Mines Tritoch Room WoB
    61 : [ [181, 182], [ ], [ ], None], #Narshe Moogle Cave WoR
    62 : [ [183, 184], [ ], [ ], None], #Narshe South Caves Secret Passage 3F WoB
    63 : [ [185, 186], [ ], [ ], None], #Narshe Checkpoint Room WoB
    64 : [ [187, 188, 189, 190], [ ], [ ], None], #Narshe South Caves WoB
    65 : [ [191, 192], [ ], [ ], None], #Narshe 3-Party Cave WoB
    66 : [ [193, 194], [ ], [ ], None], #Narshe Moogle Cave WoB
    67 : [ [195], [ ], [ ], None], #Cave to South Figaro Siegfried Tunnel
    68 : [ [197], [ ], [ ], None], #Figaro Castle Entrance
    69 : [ [198, 199, 201, 204], [ ], [ ], None], #Figaro Castle Outside Courtyard
    70 : [ [200], [ ], [ ], None], #Figaro Castle Center Tower Outside
    71 : [ [202, 205, 207, 208], [ ], [ ], None], #Figaro Castle Desert Outside
    72 : [ [203], [ ], [ ], None], #Figaro Castle West Tower Outside
    73 : [ [206], [ ], [ ], None], #Figaro Castle East Tower Outside
    74 : [ [209, 210], [ ], [ ], None], #Figaro Castle King's Bedroom
    75 : [ [1160], [ ], [ ], None], #Figaro Castle Throne Room
    76 : [ [211, 212, 213, 214], [ ], [ ], None], #Figaro Castle Foyer
    77 : [ [215, 216, 217, 218, 219, 220], [ ], [ ], None], #Figaro Castle Main Hallway
    78 : [ [221, 222, 223], [ ], [ ], None], #Figaro Castle Behind Throne Room
    79 : [ [224, 225], [ ], [ ], None], #Figaro Castle East Bedroom
    80 : [ [226, 227], [ ], [ ], None], #Figaro Castle Inn
    81 : [ [228], [ ], [ ], None], #Figaro Castle West Shop
    82 : [ [229], [ ], [ ], None], #Figaro Castle East Shop
    83 : [ [230, 231], [ ], [ ], None], #Figaro Castle Below Inn
    84 : [ [232, 233], [ ], [ ], None], #Figaro Castle Below Library
    85 : [ [234, 235], [ ], [ ], None], #Figaro Castle Library
    86 : [ [236, 238], [ ], [ ], None], #Figaro Castle Switch Room
    87 : [ [237], [ ], [ ], None], #Figaro Castle Prison
    88 : [ [239, 240], [ ], [ ], None], #Figaro Castle B1 Hallway East
    89 : [ [241, 242], [ ], [ ], None], #Figaro Castle B1 Hallway West
    90 : [ [243, 244], [ ], [ ], None], #Figaro Castle B2 Hallway
    91 : [ [245, 247], [ ], [ ], None], #Figaro Castle B2 East Hallway
    92 : [ [246, 248], [ ], [ ], None], #Figaro Castle B2 West Hallway
    93 : [ [249, 250, 251], [ ], [ ], None], #Figaro Castle B2 4 Chest Room
    94 : [ [252, 253], [ ], [ ], None], #Figaro Castle Engine Room
    95 : [ [254], [ ], [ ], None], #Figaro Castle Treasure Room Behind Engine Room
    96 : [ [255], [ ], [ ], None], #Figaro Castle B1 Single Chest Room
    97 : [ [256, 257], [ ], [ ], None], #Cave to South Figaro Small Hallway WoR
    98 : [ [258, 259, 260], [ ], [ ], None], #Cave to South Figaro Big Room WoR
    99 : [ [261, 262], [ ], [ ], None], #Cave to South Figaro South Entrance WoR
    100 : [ [263, 264], [ ], [ ], None], #Cave to South Figaro Small Hallway WoB
    101 : [ [265, 266, 267], [ ], [ ], None], #Cave to South Figaro Big Room WoB
    102 : [ [268], [ ], [ ], None], #Cave to South Figaro South Entrance WoB
    103 : [ [270], [ ], [ ], None], #Cave to South Figaro Single Chest Room WoB
    104 : [ [271], [ ], [ ], None], #Cave to South Figaro Turtle Room WoB
    105 : [ [1161], [ ], [ ], None], #Cave to South Figaro Outside WoB
    106 : [ [283, 286, 287, 288, 289, 290, 291, 292, 293, 294, 1165, 1166], [ ], [ ], None], #South Figaro Outside WoR
    107 : [ [284, 285], [ ], [ ], None], #South Figaro Rich Man's House Side Outside WoR
    108 : [ [295, 299, 300, 301, 302, 303, 304, 305, 306, 1170, 1171], [ ], [ ], None], #South Figaro Outside WoB
    109 : [ [296, 297], [ ], [ ], None], #South Figaro Rich Man's House Side Outside WoB
    110 : [ [298], [ ], [ ], None], #South Figaro East Side

    112 : [ [307, 308], [ ], [ ], None], #South Figaro Relics
    113 : [ [309, 310], [ ], [ ], None], #South Figaro Inn
    114 : [ [311, 312], [ ], [ ], None], #South Figaro Armory
    115 : [ [313, 314, 316], [ ], [ ], None], #South Figaro Pub
    116 : [ [315], [ ], [ ], None], #South Figaro Pub Basement
    117 : [ [1172], [ ], [ ], None], #South Figaro Chocobo Stable
    118 : [ [317, 318, 319], [ ], [ ], None], #South Figaro Rich Man's House 1F
    119 : [ [320, 321, 324], [ ], [ ], None], #South Figaro Rich Man's House 2F Hallway
    120 : [ [322, 325], [ ], [ ], None], #South Figaro Rich Man's Master Bedroom
    121 : [ [323], [ ], [ ], None], #South Figaro Rich Man's House Kids' Room
    122 : [ [326, 327], [ ], [ ], None], #South Figaro Rich Man's House Bedroom Secret Stairwell
    123 : [ [328, 329, 331, 332, 333], [ ], [ ], None], #South Figaro Rich Man's House B1
    124 : [ [330], [ ], [ ], None], #South Figaro Celes Cell
    125 : [ [334, 335], [ ], [ ], None], #South Figaro Clock Room
    126 : [ [336], [ ], [ ], None], #South Figaro Duncan's House Basement
    127 : [ [337], [ ], [ ], None], #South Figaro Item Shop
    128 : [ [338], [ ], [ ], None], #South Figaro Rich Man's House Secret Back Door Room
    129 : [ [346], [ ], [ ], None], #South Figaro Cider House Secret Room
    130 : [ [339, 344], [ ], [ ], None], #South Figaro Cider House Upstairs
    131 : [ [340, 343, 348], [ ], [ ], None], #South Figaro Cider House Downstairs
    132 : [ [341, 342], [ ], [ ], None], #South Figaro Behind Duncan's House
    133 : [ [345, 347], [ ], [ ], None], #South Figaro Duncan's House Upstairs
    134 : [ [349, 350, 351], [ ], [ ], None], #South Figaro Escape Tunnel
    135 : [ [352], [ ], [ ], None], #South Figaro Rich Man's House Save Point Room
    136 : [ [353], [ ], [ ], None], #South Figaro B2 3 Chest Room
    137 : [ [354], [ ], [ ], None], #South Figaro B2 2 Chest Room
    138 : [ [355], [ ], [ ], None], #Cave to South Figaro Single Chest Room WoR
    139 : [ [356], [ ], [ ], None], #Cave to South Figaro Turtle Room WoR
    140 : [ [357], [ ], [ ], None], #Cave to South Figaro Turtle Door WoR
    141 : [ [1173], [ ], [ ], None], #South Figaro Docks
    142 : [ [358, 359], [ ], [ ], None], #Cave to South Figaro Behind Turtle
    143 : [ [361], [ ], [ ], None], #Sabin's House Outside
    144 : [ [362], [ ], [ ], None], #Sabin's House Inside
    145 : [ [363, 1175], [ ], [ ], None], #Mt. Kolts South Entrance
    146 : [ [364, 365, 366], [ ], [ ], None], #Mt. Kolts 1F Outside
    147 : [ [367], [ ], [ ], None], #Mt Kolts Outside Chest 1 Room
    148 : [ [368, 1176], [ ], [ ], None], #Mt Kolts Outside Cliff West
    149 : [ [369], [ ], [ ], None], #Mt Kolts Outside Chest 2 Room
    150 : [ [370, 371], [ ], [ ], None], #Mt. Kolts Outside Bridge
    151 : [ [372, 373], [ ], [ ], None], #Mt. Kolts Vargas Spiral
    152 : [ [374, 375], [ ], [ ], None], #Mt. Kolts First Inside Room
    153 : [ [376, 377, 378, 385], [ ], [ ], None], #Mt. Kolts 4-Way Split Room
    154 : [ [379, 380], [ ], [ ], None], #Mt. Kolts 2F Inside Room
    155 : [ [381, 382], [ ], [ ], None], #Mt. Kolts Inside Bridges Room
    156 : [ [383, 384], [ ], [ ], None], #Mt. Kolts After Vargas Room
    157 : [ [386], [ ], [ ], None], #Mt Kolts Inside Chest Room
    158 : [ [1177, 1178], [ ], [ ], None], #Mt. Kolts North Exit
    159 : [ [387, 388, 389, 1179], [ ], [ ], None], #Mt. Kolts Back Side
    160 : [ [390, 391], [ ], [ ], None], #Mt. Kolts Save Point Room
    161 : [ [392, 393, 394, 395], [ ], [ ], None], #Narshe School Main Room
    162 : [ [396], [ ], [ ], None], #Narshe School Left Room
    163 : [ [397], [ ], [ ], None], #Narshe School Middle Room
    164 : [ [398], [ ], [ ], None], #Narshe School Right Room
    165 : [ [1180, 1181], [ ], [ ], None], #Returners Hideout Outside
    166 : [ [399, 400, 401, 402, 403], [ ], [ ], None], #Returners Hideout Main Room
    167 : [ [404], [ ], [ ], None], #Returners Hideout Back Room
    168 : [ [405, 406], [ ], [ ], None], #Returners Hideout Banon's Room
    169 : [ [407], [ ], [ ], None], #Returner's Hideout Bedroom
    170 : [ [408], [ ], [ ], None], #Returner's Hideout Inn
    171 : [ [409, 410], [ ], [ ], None], #Returner's Hideout Secret Passage
    172 : [ [1182], [ ], [ ], None], #Lete River Jumpoff
    173 : [ [411], [ ], [ ], None], #Crazy Old Man's House Outside WoB
    174 : [ [412], [ ], [ ], None], #Crazy Old Man's House Inside

    176 : [ [417, 432], [ ], [ ], None], #Doma 3F Inside
    177 : [ [418, 419, 422, 424, 425, 428, 430, 431, 433], [ ], [ ], None], #Doma Main Room
    178 : [ [420], [ ], [ ], None], #Doma 2F Treasure Room
    179 : [ [421], [ ], [ ], None], #Doma Right Side Bedroom
    180 : [ [423], [ ], [ ], None], #Doma Throne Room
    181 : [ [426], [ ], [ ], None], #Doma Left Side Bedroom
    182 : [ [427, 429], [ ], [ ], None], #Doma Inner Room
    183 : [ [434], [ ], [ ], None], #Doma Cyan's Room
    184 : [ [435], [ ], [ ], None], #Doma Dream 3F Outside
    185 : [ [436], [ ], [ ], None], #Doma Dream 1F Outside
    186 : [ [437, 438], [ ], [ ], None], #Doma Dream 2F Outside
    187 : [ [439, 453], [ ], [ ], None], #Doma Dream 3F Inside
    188 : [ [440, 441, 443, 444, 445, 446, 449, 451, 452, 454], [ ], [ ], None], #Doma Dream Main Room
    189 : [ [442], [ ], [ ], None], #Doma Dream Treasure Room
    190 : [ [447], [ ], [ ], None], #Doma Dream Side Bedroom
    191 : [ [448, 450], [ ], [ ], None], #Doma Dream Inner Room
    192 : [ [455], [ ], [ ], None], #Doma Dream Cyan's Room
    193 : [ [456], [ ], [ ], None], #Doma Dream Throne Room
    194 : [ [458], [ ], [ ], None], #Duncan's House Outside
    195 : [ [459], [ ], [ ], None], #Duncan's House
    196 : [ [460], [ ], [ ], None], #Crazy Old Man's House WoR




    201 : [ [469], [ ], [ ], None], #Phantom Train Station
    202 : [ [470, 471, 472, 473], [ ], [ ], None], #Phantom Train Outside 4th Section

    204 : [ [474, 475, 476], [ ], [ ], None], #Phantom Train Outside 1st Section



    208 : [ [477, 483], [ ], [ ], None], #Doma Dream Train Outside 3rd Section
    209 : [ [478, 479, 480, 481], [ ], [ ], None], #Doma Dream Train Outside 2nd Section
    210 : [ [482], [ ], [ ], None], #Doma Dream Train Outside 1st Section
    211 : [ [484, 485, 486, 487], [ ], [ ], None], #Doma Dream Train 2nd Car

    213 : [ [488], [ ], [ ], None], #Phantom Train Caboose Inner Room

    215 : [ [489, 490, 491, 492], [ ], [ ], None], #Phantom Train Dining Room
    216 : [ [493, 494], [ ], [ ], None], #Phantom Train Seating Car with Switch Left Side



    220 : [ [496, 497, 498, 499, 500, 501], [ ], [ ], None], #Phantom Train Caboose
    221 : [ [502], [ ], [ ], None], #Phantom Train Final Save Point Room



    225 : [ [503], [ ], [ ], None], #Mobliz Kids' Hideaway
    226 : [ [504, 505], [ ], [ ], None], #Baren Falls Inside
    227 : [ [1189], [ ], [ ], None], #Baren Falls Cliff
    228 : [ [506, 507, 508, 512, 1190, 1191], [ ], [ ], None], #Mobliz Outside WoB
    229 : [ [1192, 1193], [ ], [ ], None], #Mobliz Outside WoR

    231 : [ [516], [ ], [ ], None], #Mobliz Inn
    232 : [ [517, 518], [ ], [ ], None], #Mobliz Arsenal

    234 : [ [519], [ ], [ ], None], #Mobliz Mail Room Upstairs
    235 : [ [520], [ ], [ ], None], #Mobliz Item Shop
    236 : [ [521], [ ], [ ], None], #Mobliz Mail Room Basement WoB


    239 : [ [1196, 1197], [ ], [ ], None], #Baren Falls Outside
    240 : [ [523, 524], [ ], [ ], None], #Crescent Mountain
    241 : [ [1198], [ ], [ ], None], #Serpent Trench Cliff
    242 : [ [525, 526, 1199, 1200, 1201, 1202], [ ], [ ], None], #Nikeah Outside WoB
    243 : [ [527], [ ], [ ], None], #Nikeah Inn
    244 : [ [528], [ ], [ ], None], #Nikeah Pub
    245 : [ [1203], [ ], [ ], None], #Nikeah Chocobo Stable
    246 : [ [529], [ ], [ ], None], #Serpent Trench Cave 2nd Part 1st Room
    247 : [ [530], [ ], [ ], None], #Serpent Trench Cave 2nd Part 2nd Room


    250 : [ [531, 532, 533], [ ], [ ], None], #Mt Zozo Outside Bridge
    251 : [ [534], [ ], [ ], None], #Mt Zozo Outside Single Chest Room
    252 : [ [535, 536], [ ], [ ], None], #Mt Zozo Outside Cliff to Cyan's Cave
    253 : [ [537, 538, 539], [ ], [ ], None], #Mt Zozo Inside First Room
    254 : [ [540, 541], [ ], [ ], None], #Mt Zozo Inside Dragon Room
    255 : [ [542, 543], [ ], [ ], None], #Mt Zozo Cyan's Cave
    256 : [ [1204], [ ], [ ], None], #Mt Zozo Cyan's Cliff
    257 : [ [544, 1205, 1206, 1207], [ ], [ ], None], #Coliseum Guy's House Outside
    258 : [ [545], [ ], [ ], None], #Coliseum Guy's House Inside
    259 : [ [1208], [ ], [ ], None], #Nikeah Docks
    260 : [ [546, 547, 548, 549, 550, 551, 1209, 1210], [ ], [ ], None], #Kohlingen Outside WoB
    261 : [ [552, 553, 554, 555, 556, 557, 1211, 1212], [ ], [ ], None], #Kohlingen Outside WoR
    262 : [ [558], [ ], [ ], None], #Kohlingen Inn Inside
    263 : [ [559, 560], [ ], [ ], None], #Kohlingen General Store Inside
    264 : [ [561, 563], [ ], [ ], None], #Kohlingen Chemist's House Upstairs
    265 : [ [562], [ ], [ ], None], #Kohlingen Chemist's House Downstairs
    266 : [ [564], [ ], [ ], None], #Kohlingen Chemist's House Back Room
    267 : [ [565], [ ], [ ], None], #Maranda Lola's House Inside
    268 : [ [566], [ ], [ ], None], #Kohlingen Rachel's House Inside
    269 : [ [567, 568, 569, 570, 571, 572, 573, 1213, 1214, 1215, 1216], [ ], [ ], None], #Jidoor Outside
    270 : [ [574], [ ], [ ], None], #Jidoor Auction House
    271 : [ [575], [ ], [ ], None], #Jidoor Item Shop
    272 : [ [576], [ ], [ ], None], #Jidoor Relic
    273 : [ [577], [ ], [ ], None], #Jidoor Armor
    274 : [ [578], [ ], [ ], None], #Jidoor Weapon
    275 : [ [1217], [ ], [ ], None], #Jidoor Chocobo Stable
    276 : [ [579], [ ], [ ], None], #Jidoor Inn

    277 : [ [580, 581], [ ], [ ], 1], #Owzer's Behind Painting Room
    278 : [ [582, 583, 585], [ ], [3017], 1], #Owzer's Basement 1st Room
    279 : [ [584], [ ], [ ], 1], #Owzer's Basement Single Chest Room
    280 : [ [586, 587], [2017, 2018], [ ], 1], #Owzer's Basement Switching Door Room
    281 : [ [588], [2019], [3021], 1], #Owzer's Basement Behind Switching Door Room
    282 : [ [589], [2021], [3020], 1], #Owzer's Basement Save Point Room
    283 : [ [ ], [2020], [3019], 1],  # Owzer's Basement Floating Chest room
    284 : [ [591], [ ], [ ], 1], #Owzer's Basement Chadarnook's Room
    285 : [ [592, 593], [ ], [ ], None], #Owzer's House

    286 : [ [1218, 1219, 1220, 1221, 1222, 1223], [ ], [ ], None], #Esper World Outside
    287 : [ [594], [ ], [ ], None], #Esper World Gate
    288 : [ [595], [ ], [ ], None], #Esper World Northwest House
    289 : [ [596], [ ], [ ], None], #Esper World Far East House
    290 : [ [597], [ ], [ ], None], #Esper World South Right House
    291 : [ [598], [ ], [ ], None], #Esper World East House
    292 : [ [599], [ ], [ ], None], #Esper World South Left House

    # ZOZO
    'root-zb' : [ [37, 38, 39], [], [], 0],  # Zozo WoB entrance (for Terra check)
    'root-zr' : [ [70, 71, 72], [], [], 1],  # Zozo WoR entrance (for Mt Zozo check)
    293 : [ [600, 601, 602, 604, 608, 1224], [ ], [ ], None], #Zozo 1F Outside
    'zozo-b' : [ [600, 601, 602, 604, 608, 1224], [ ], [ ], 0], #Zozo 1F Outside WOB
    # Convention: if same door is used in WoB and WoR, then logical id_WOR = (4000 + id_WOB)
    # Then, when writing door tiles, we can use id >= 4000 to write an exit event, and id <= 2000 to write the exit.
    'zozo-r' : [ [4600, 4601, 4602, 4604, 5224], [ ], [ ], 1], #Zozo 1F Outside WOR:
    294 : [ [603], [ ], [ ], None], #Zozo 2F Clock Room Balcony Outside
    295 : [ [605], [ ], [ ], None], #Zozo 2F Cafe Balcony Outside
    296 : [ [606, 607], [ ], [ ], None], #Zozo Cafe Upstairs Outside WOB (618 --> Mt Zozo not accessible)
    '296r' : [ [606, 607, 618], [ ], [ ], None], #Zozo Cafe Upstairs Outside WOR
    297 : [ [609, 610], [ ], [3032], None], #Zozo Relic 1st Section Outside (incl. hook entry event)
    298 : [ [611, 612, 616], [2032], [ ], None], #Zozo Relic 2nd Section Outside (incl. hook exit)
    299 : [ [613, 617], [ ], [ ], None], #Zozo Relic 3rd Section Outside
    300 : [ [614, 615, 619], [ ], [ ], None], #Zozo Relic 4th Section Outside
    301 : [ [620, 621, 622], [ ], [ ], None], #Zozo Cafe
    302 : [ [623, 624], [ ], [ ], None], #Zozo Relic 1st Room Inside
    # 303 : [ [625, 626], [ ], [ ], None], #Zozo Relic 2nd Room Inside - Walking guys create a one-way gate
    '303a' : [ [625], [2033], [ ], None], #Zozo Relic 2nd Room Inside - entrance
    '303b' : [ [626], [ ], [3033], None], #Zozo Relic 2nd Room Inside - exit
    304 : [ [627, 628], [ ], [ ], None], #Zozo West Tower Inside
    305 : [ [629], [ ], [ ], None], #Zozo Armor
    306 : [ [630], [ ], [ ], None], #Zozo Weapon
    #307 : [ [631], [ ], [ ], None], #Zozo Clock Puzzle Room West
    #308 : [ [632], [ ], [ ], None], #Zozo Clock Puzzle Room East
    '307a' : [ [631, 632],  [ ], [ ], None],  #Zozo Clock Puzzle Room (complete)
    309 : [ [633], [ ], [ ], None], #Zozo Cafe Chest Room
    310 : [ [634], [ ], [ ], None], #Zozo Tower 6F Chest Room
    311 : [ [635, 636], [ ], [ ], None], #Zozo Tower Stairwell Room
    312 : [ [637], [ ], [ ], None], #Zozo Tower 12F Chest Room
    # Exits 638, 639, 640, 641 appear to be redundant with 634, 635, 636, 637
    313 : [ [1225], [ ], [ ], None], #Zozo Tower Ramuh's Room

    # OPERA HOUSE
    314 : [ [642, 643], [ ], [ ], None], #Opera House Balcony WoR and WoB Disruption
    315 : [ [646, 647], [ ], [ ], None], #Opera House Catwalk Stairwell
    316 : [ [648], [ ], [ ], None], #Opera House Switch Room
    317 : [ [649, 650], [ ], [ ], None], #Opera House Balcony WoB
    318 : [ [657], [ ], [ ], None], #Opera House Catwalks
    319 : [ [658, 659], [ ], [ ], None], #Opera House Lobby
    320 : [ [662], [ ], [ ], None], #Opera House Dressing Room
    321 : [ [1226], [ ], [ ], None], #Vector After Train Ride
    322 : [ [1229], [ ], [ ], None], #Vector Outside
    323 : [ [670], [ ], [ ], None], #Imperial Castle Entrance

    325 : [ [671, 672, 673], [ ], [ ], None], #Imperial Castle Roof





    331 : [ [674, 676, 678, 679, 680, 682, 684, 1230], [ ], [ ], None], #Imperial Castle Main Room
    332 : [ [675], [ ], [ ], None], #Imperial Castle 2 Chest Room
    333 : [ [677], [ ], [ ], None], #Imperial Castle Jail Cell
    334 : [ [681, 688], [ ], [ ], None], #Imperial Castle 2F Bedroom Hallway
    335 : [ [683, 693], [ ], [ ], None], #Imperial Castle Left Side Roof Stairwell
    336 : [ [685, 694], [ ], [ ], None], #Imperial Castle Right Side Roof Stairwell

    338 : [ [689, 690], [ ], [ ], None], #Imperial Castle Bedroom
    339 : [ [691], [ ], [ ], None], #Imperial Castle Bedroom Bathroom
    340 : [ [692], [ ], [ ], None], #Imperial Castle Toilet
    341 : [ [1231], [ ], [ ], None], #Imperial Castle Top Room
    342 : [ [1233], [ ], [ ], None], #Imperial Castle Banquet Room
    343 : [ [695, 696], [ ], [ ], None], #Imperial Castle Barracks Room

    345 : [ [702], [2023], [ ], None], #Magitek Factory Upper Room Platform From Lower Room
    346 : [ [703], [2022], [3023], None], #Magitek Factory Upper Room
    347 : [ [704], [2024, 2025], [3022, 3024, 3026], None], #Magitek Factory Lower Room

    349 : [ [705, 706], [2026], [3025], None], #Magitek Factory Garbage Room

    351 : [ [709, 710], [ ], [ ], None], #Magitek Factory Stairwell
    352 : [ [711], [ ], [ ], None], #Magitek Factory Save Point Room
    353 : [ [712, 713], [ ], [ ], None], #Magitek Factory Tube Hallway
    354 : [ [714, 715], [ ], [ ], None], #Magitek Factory Number 024 Room
    355 : [ [716], [2027], [ ], None], #Magitek Factory Esper Tube Room
    '355a' : [ [], [2028], [3027], None],  # Magitek Factory Minecart Room

    356 : [ [717], [ ], [ ], None], #Zone Eater Entry Room
    357 : [ [718, 719, 721], [ ], [ ], None], #Zone Eater Bridge Guards Room
    358 : [ [720], [ ], [ ], None], #Zone Eater Pit
    359 : [ [723], [ ], [ ], None], #Zone Eater Short Tunnel
    360 : [ [724], [ ], [ ], None], #Zone Eater Gogo Room
    361 : [ [725], [ ], [ ], None], #Zone Eater Save Point Room
    362 : [ [727, 728], [ ], [ ], None], #Zone Eater Bridge Switch Room

    364 : [ [729, 730, 731], [2001, 2002], [3010], None], #Umaro Cave 1st Room
    365 : [ [732, 733], [ ], [3001, 3002, 3003, 3005, 3007], None], #Umaro Cave Bridge Room
    366 : [ [734], [2003, 2004], [ ], None], #Umaro Cave Switch Room
    # 367 : [ [735, 736, 737, 738], [2005, 2006, 2007, 2008], [ ], None], #Umaro Cave 2nd Room
    '367a' : [ [735], [2007], [ ], None], #Umaro Cave 2nd Room - west
    '367b' : [ [736, 738], [2006, 2008], [ ], None], #Umaro Cave 2nd Room - middle
    '367c' : [ [737], [2005], [ ], None], #Umaro Cave 2nd Room - east
    368 : [ [ ], [2009], [3004], None], # Umaro Cave Umaro's Den

    369 : [ [739, 740, 741, 742], [ ], [ ], None], #Maranda Outside
    370 : [ [743], [ ], [ ], None], #Doma 3F Outside
    371 : [ [744, 1240], [ ], [ ], None], #Doma 1F Outside
    372 : [ [745, 746], [ ], [ ], None], #Doma 2F Outside

    374 : [ [750], [ ], [ ], None], #Maranda Inn
    375 : [ [751], [ ], [ ], None], #Maranda Weapon Shop
    376 : [ [752], [ ], [ ], None], #Maranda Armor Shop
    377 : [ [1241], [ ], [ ], None], #Darill's Tomb Outside
    378 : [ [771, 772], [ ], [ ], None], #Darill's Tomb Entry Room
    379 : [ [773, 774, 776, 778, 780, 783], [ ], [ ], None], #Darill's Tomb Main Upstairs Room
    380 : [ [775], [ ], [ ], None], #Darill's Tomb Left Side Tombstone Room
    381 : [ [777, 786], [ ], [ ], None], #Darill's Tomb Right Side Tombstone Room
    382 : [ [779, 785], [ ], [ ], None], #Darill's Tomb B2 Left Side Bottom Room
    383 : [ [781, 782], [ ], [ ], None], #Darill's Tomb B2 Turtle Hallway
    384 : [ [784], [ ], [ ], None], #Darill's Tomb B2 Right Side Bottom Room
    385 : [ [787], [ ], [ ], None], #Darill's Tomb Right Side Secret Room
    386 : [ [788], [ ], [ ], None], #Darill's Tomb B2 Graveyard
    387 : [ [789], [ ], [ ], None], #Darill's Tomb Dullahan Room
    388 : [ [790, 791], [ ], [ ], None], #Darills' Tomb B3
    389 : [ [792], [ ], [ ], None], #Darills' Tomb B3 Water Level Switch Room
    390 : [ [793, 794], [ ], [ ], None], #Darills' Tomb B2 Water Level Switch Room Left Side


    393 : [ [797, 798], [ ], [ ], None], #Darill's Tomb MIAB Hallway







    401 : [ [814, 815], [ ], [ ], None], #Tzen Collapsing House Downstairs
































    434 : [ [865, 866], [ ], [ ], None], #Doma Dream Train Switch Puzzle Room Left Section
    435 : [ [867], [ ], [ ], None], #Doma Dream Train Switch Puzzle Room
    436 : [ [868, 869, 870, 871], [ ], [ ], None], #Doma Dream Train 1st Car










    447 : [ [922, 923, 924, 925, 926, 927, 928], [ ], [ ], None], #Thamasa After Kefka Outside WoB


    450 : [ [950, 951], [ ], [ ], None], #Thamasa Arsenal
    451 : [ [952], [ ], [ ], None], #Thamasa Inn
    452 : [ [953], [ ], [ ], None], #Thamasa Item Shop
    453 : [ [954], [ ], [ ], None], #Thamasa Elder's House
    454 : [ [955, 956], [ ], [ ], None], #Strago's House First Floor
    455 : [ [957], [ ], [ ], None], #Strago's House Second Floor
    456 : [ [958], [ ], [ ], None], #Thamasa Relic
    457 : [ [959], [ ], [ ], None], #Burning House Entry Room
    458 : [ [960, 961, 962], [ ], [ ], None], #Burning House Second Room
    459 : [ [963, 964], [ ], [ ], None], #Burning House Third Room
    460 : [ [965, 966, 968], [ ], [ ], None], #Burning House Fourth Room
    461 : [ [967, 970, 972], [ ], [ ], None], #Burning House Fifth Room
    462 : [ [969], [ ], [ ], None], #Burning House 1st Chest Room
    463 : [ [971], [ ], [ ], None], #Burning House 2nd Chest Room
    464 : [ [973, 974], [ ], [ ], None], #Burning House Sixth Room
    465 : [ [975], [ ], [ ], None], #Burning House Final Room

    467 : [ [979, 985], [ ], [ ], None], #Veldt Cave First Room
    468 : [ [980], [ ], [ ], None], #Veldt Cave Second Room Dead End
    469 : [ [981, 986], [ ], [ ], None], #Veldt Cave Bandit Room / Second Room
    470 : [ [982, 983], [ ], [ ], None], #Veldt Cave Third Room
    471 : [ [984, 987], [ ], [ ], None], #Veldt Cave Bandit Room / Second Room Lower Floor
    472 : [ [988], [ ], [ ], None], #Veldt Cave Fourth Room Left Side
    473 : [ [989], [ ], [ ], None], #Veldt Cave Fourth Room Right Side
    474 : [ [990, 992], [ ], [ ], None], #Veldt Cave Fifth Room
    475 : [ [991], [ ], [ ], None], #Veldt Cave Final Room
    476 : [ [1010, 1011, 1012], [ ], [ ], None], #Fanatic's Tower 2nd Floor Outside
    477 : [ [1013, 1014, 1015], [ ], [ ], None], #Fanatic's Tower 3rd Floor Outside
    478 : [ [1016, 1017, 1018], [ ], [ ], None], #Fanatic's Tower 4th Floor Outside
    479 : [ [1019], [ ], [ ], None], #Fanatic's Tower Bottom
    480 : [ [1020, 1021, 1022, 1023], [ ], [ ], None], #Fanatic's Tower 1st Floor Outside
    481 : [ [1024, 1025], [ ], [ ], None], #Fanatic's Tower Top
    482 : [ [1026], [ ], [ ], None], #Fanatic's Tower 1st Floor Treasure Room
    483 : [ [1027], [ ], [ ], None], #Fanatic's Tower Top Room
    484 : [ [1028], [ ], [ ], None], #Fanatic's Tower 2nd Floor Treasure Room
    485 : [ [1029], [ ], [ ], None], #Fanatic's Tower 3rd Floor Treasure Room
    486 : [ [1030], [ ], [ ], None], #Fanatic's Tower 4th Floor Treasure Room
    487 : [ [1031], [ ], [ ], None], #Fanatic's Tower 1st Floor Secret Room

    488 : [ [1032, 1033], [ ], [ ], None], #Esper Mountain 3 Statues Room
    489 : [ [1034, 1035, 1036], [ ], [ ], None], #Esper Mountain Outside Bridge Room
    490 : [ [1037], [ ], [ ], None], #Esper Mountain Outside East Treasure Room
    491 : [ [1038, 1039, 1040, 1041], [ ], [ ], None], #Esper Mountain Outside Path to Final Room
    492 : [ [1042, 1043], [ ], [ ], None], #Esper Mountain Outside Statue Path
    493 : [ [1044], [ ], [ ], None], #Esper Mountain Outside West Treasure Room
    494 : [ [1045], [ ], [ ], None], #Esper Mountain Outside Northwest Treasure Room
    495 : [ [1046, 1047, 1048, 1049], [ ], [ ], None], #Esper Mountain Inside First Room
    496 : [ [1050, 1051], [ ], [3011, 3012, 3013], None], #Esper Mountain Inside Second Room South Section (with bridge jump entrances)
    497 : [ [1052], [2014, 2015, 2016], [ ], None], #Esper Mountain Falling Pit Room
    498 : [ [1053, 1054], [2011], [3015], None], #Esper Mountain Inside Second Room West Section
    499 : [ [1055], [2013], [3016], None], #Esper Mountain Inside Second Room East Section
    500 : [ [1056], [2012], [3014], None], #Esper Mountain Inside Second Room North Section
    501 : [ [1057], [ ], [ ], None], #Esper Mountain Inside Second Room Dead End

    502 : [ [1059, 1060, 1058, 1263], [ ], [ ], None], #Imperial Base
    'root_sg': [[1058, 1263], [], [], 0],  # Root entrance = imperial base
    503 : [ [1061, 1062], [ ], [ ], None], #Imperial Base House
    504 : [ [1063], [ ], [ ], None], #Imperial Base House Basement
    '504a' : [ [41, 43], [], [], 0],  # WOB Imperial Base / Cave to Sealed Gate connector
    505 : [ [1064, 1065], [ ], [3031], None], #Cave to Sealed Gate Entry Room
    506 : [ [1066, 1067], [ ], [ ], None], #Cave to Sealed Gate B1
    507 : [ [1069, 1264], [2031], [ ], None], #Cave to Sealed Gate Last Room
    508 : [ [1070], [ ], [3030], None], #Cave to Sealed Gate Main Room Last Section
    509 : [ [1071, 1072], [2029], [ ], None], #Cave to Sealed Gate Main Room First Section
    510 : [ [1073], [2030], [3029], None], #Cave to Sealed Gate Main Room Middle Section
    511 : [ [1074], [ ], [ ], None], #Cave to Sealed Gate 4 Chest Room
    512 : [ [1075, 1076, 1077], [ ], [ ], None], #Cave to Sealed Gate Lava Switch Room  # 1076 inaccessible?
    513 : [ [1078], [ ], [ ], None], #Cave to Sealed Gate Save Point Room
    514 : [ [1079], [ ], [ ], None], #Sealed Gate

    515 : [ [1080, 1265, 1266, 1267, 1268, 1269, 1270], [ ], [ ], None], #Solitary Island House Outside
    516 : [ [1081], [ ], [ ], None], #Solitary Island House Inside
    517 : [ [1271], [ ], [ ], None], #Solitary Island Beach


    520 : [ [1083, 1085, 1087], [ ], [ ], None], #Ancient Cave First Room
    521 : [ [1084, 1086, 1088, 1274], [ ], [ ], None], #Ancient Cave Second Room
    522 : [ [1089, 1275], [ ], [ ], None], #Ancient Cave Third Room
    523 : [ [1090, 1091], [ ], [ ], None], #Ancient Cave Save Point Room
    524 : [ [1092, 1093], [ ], [ ], None], #Ancient Castle West Side South Room
    525 : [ [1094], [ ], [ ], None], #Ancient Castle East Side Single Chest Room
    526 : [ [1095], [ ], [ ], None], #Ancient Castle West Side North Room
    527 : [ [1096], [ ], [ ], None], #Ancient Castle East Side 2 Chest Room
    528 : [ [1098, 1099, 1100, 1278], [ ], [ ], None], #Ancient Castle Throne Room
    529 : [ [1276, 1277], [ ], [ ], None], #Ancient Castle Entry Room
    530 : [ [1101, 1102, 1103, 1104, 1279], [ ], [ ], None], #Ancient Castle Outside
    531 : [ [1105, 1106], [ ], [ ], None], #Ancient Castle Eastern Basement
    532 : [ [1107], [ ], [ ], None], #Ancient Castle Dragon Room
    533 : [ [1125, 1126, 1280], [ ], [ ], None], #Coliseum Main Room
    534 : [ [1127], [ ], [ ], None], #Coliseum Left Room

}

# Lists of exits that must be connected
forced_connections = {
    2011 : [3011],   # Esper Mountain Inside 2nd Room: North-to-South bridge jump West
    2012 : [3012],   #      North-to-South bridge jump Mid
    2013 : [3013],   #      North-to-South bridge jump East

    2023 : [3023],   # Magitek factory elevator in Room 1

    2029 : [3029],   # Cave to the Sealed Gate, grand staircase
    2030 : [3030],   # Cave to the Sealed Gate, switch bridges
    1079 : [1264],   # Cave to the Sealed Gate, actual Sealed Gate (must be connected to enable shortcut exit)

    2032 : [3032]   # Zozo hook exit from building
}

# Add forced connections for virtual doors (-dra)
#if 'root' in room_data.keys():
#    for i in range(8000, 8000+len(room_data['root'][0])):
#        forced_connections[i] = [i+1000]

# List of one-ways that must have the same destination
shared_oneways = {
    2005: [2006],  # Umaro's cave room 2: east trapdoor (shared exit)
    2006: [2005],  # Umaro's cave room 2: east trapdoor (shared exit)
    2007: [2008],  # Umaro's cave room 2: west trapdoor (shared exit)
    2008: [2007],  # Umaro's cave room 2: west trapdoor (shared exit)

    2017: [2018],   # Owzer's Mansion switching doors (same destination)
    2018: [2017],    # Owzer's Mansion switching doors (same destination)

}

# Lists of doors that have a shared destination. key_doorID : [doorIDs that share destination]
shared_exits = {
    1034 : [1035],  # Esper Mountain outside bridge, left door
    1038 : [1039],  # Esper Mountain Outside Path to Final Room East Door
    1040 : [1041],  # Esper Mountain Outside Path to Final Room West Door

    1229 : [1226],  # Post-minecart Vector long exit to MTek.  Same destination as normal Vector exit to MTek.

    1059 : [1060],  # Imperial camp, left entrance

    1075 : [1076],  # Cave to the Sealed Gate, lava switch room: exit 1076 inaccessible (for door exit error?)

    38 : [37, 39]   # Zozo WoB entrance
}

# List of doors that CANNOT be connected to each other.  Only rare instances.
invalid_connections = {
    702 : [703],  # Magitek factory room 1: entrance & platform door
    703 : [702],

}

# List of rooms that should have a forced update to Parent Map variable when entering.
# force_update_parent_map[roomID] = [x, y, mapID]
force_update_parent_map = {
    '285a' : [1, 34, 157]  # Entering WoR Jidoor from Owzer's Basement
}
