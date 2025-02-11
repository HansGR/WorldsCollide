#rooms - series of doors.  [ [2-way doors], [1-way exits], [1-way entrances], require_world?]

### ROOMS THAT NEED FIXING:
# 68, 71: LONG EXITS in FIGARO CASTLE DESERT OUTSIDE - the same long exit is used for entrance & south exit. Split them.
# 105: SOUTH FIGARO CAVE ENTRANCE - add door into cave (currently uses event tile)
# 106, 108, 110: South Figaro outside.  North long exit is shared on left/right sides,
#                Split them since technically different rooms in WOB
# 233, 237, 238: Mobliz Relic Shop & Injured Lad.  Have a door in but handled by event tiles.
#                Mobliz Relic & Injured Lad inside exit are only event tiles (no exit)
# 314, 317, 319: Opera House: doors from lobby --> balcony are apparently event tiles.
# Phantom Train (???)
# Doma Dream Train (???)
# Chocobo stables on World Map: all of them use parent map functionality.  Maybe just don't rando them.

room_data = {
    ## Test rooms for connection algorithm:
    #'A' : [ [1], [2001], [3003], [], {'a': [2]}, 0],
    #'B' : [ [], [2002], [3001], ['a'], {}, 0],
    #'C' : [ [3, 4], [2003], [3002, 3004], [], {}, 0],
    #'D' : [ [5], [], [], [], {}, 0],
    #'E' : [ [6], [2004], [], [], {}, 0],
    #'test_room_1': [ [1801], [], [], ['b'], {}, 0],  # 2036 --> 3024 (MTek Pipe Exit)
    #'test_room_2': [ [1802], [], [], [], {'a': [1800]}, 0],  # 2024 --> 3035

    # 'root-code' rooms are terminal entrance rooms for randomizing individual sections.
    # They are also used in Dungeon Crawl mode.
    'root-u' : [ [], [2010], [3009], 1], # Root map for -door-randomize-umaro
    'root-unb' : [ [1138], [], [], 0], # Root map for -door-randomize-upper-narshe-wob
    'root-unr' : [ [1146], [], [], 1], # Root map for -door-randomize-upper-narshe-wor
    'root-ob' : [ [593], [], [], 1], # Root map for -door-randomize-owzer's basement
    'root-mf' : [ [1229], [], [3028], 0],     # Magitek Factory root entrance in Vector
    #'root-zb': [ [37, 38, 39], [], [], 0],  # Zozo WoB entrance (for Terra check)
    #'root-zr': [ [70, 71, 72], [], [], 1],  # Zozo WoR entrance (for Mt Zozo check)
    'root-lr' : [ [], [2034], [3039], 0],  # Root map for -door-randomize-lete
    'root-st' : [ [ ], [2044], [3053], 0], # Root map for -door-randomize-serpent-trench
    'root-bh' : [ [ ], [2054], [3055], 0],  # Root map for -door-randomize-burning-house
    'root-dt' : [ [1241], [], [3058], 1],  # Root map for -door-randomize-darills-tomb
    'root-cd' : [ [], [2069], [3074], 1], # Root room for Cyan's Dream
    'root-pt' : [ [468], [], [3068], 0],  # Root map for Phantom Train

    # Map Shuffle rooms:  World Maps
    #'shuffle-wob' : [ [6, 1556], [], [], 0],  # Root map for WOB map shuffle testing
    'shuffle-wob' : [ [4, 5, 1501, 1502, 1504, 1505, 1506, 6, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 23, 24, 26, 27, 28, 31, 33, 35, 37, 40, 42, 44, 1556], [], [], 0],  # Root map for WOB map shuffle (does not include connector to Sealed Gate Cave or chocobo stables)
    #'shuffle-wor' : [ [1558, 51], [], [], 1],  # Root map for WOR map shuffle testing  1554 = Phoenix Cave
    'shuffle-wor' : [ [48, 49, 51, 52, 53, 56, 57, 58, 59, 61, 62, 63, 65, 67, 68, 69, 70, 73, 75, 76, 78, 79, 1552, 1554], [], [], 1],  # Root map for WOR map shuffle (does not include Figaro Castle, KT, Phoenix Cave or chocobo stables).  Note: extra Nikeah doors are 54, 55.

    # Root map for dungeon crawl mode.  Includes lete river terminus, zone eater entry/exit, phantom train fast exit, daryl's tomb fast exit
    #'dc-world' : [ [4, 5, 1501, 1502, 1504, 1505, 1506, 6, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 23, 24, 26, 27, 28,  #
    #                31, 33, 35, 37, 40, 42, 44, 1556,
    #                48, 49, 51, 52, 53, 56, 57, 58, 59, 61, 62, 63, 65, 67, 69, 70, 73, 75, 76, 78, 79, 1552, 1554],  # 68,
    #               [2040], [3039, 3041, 3058, 3068], 0],

    # World Map Rooms: which exits on the world map you can walk to from which other ones.
    'wob-narshe' : [ [4, 5, 1502], [], [3039], 0],
    'wob-figaro' : [ [1506, 6, 10, 11], [], [], 0],
    'wob-sabil' : [ [12, 13], [], [], 0],
    'wob-nikeah' : [ [16, 14, 1501], [], [], 0],
    'wob-doma' : [ [1559, 18, 20], [], [], 0],
    'wob-baren' : [ [21, 15], [], [3068], 0],
    'wob-veldt' : [ [23, 26], [], [3076], 0],
    'wob-thamasa' : [ [1504, 44], [], [], 0],
    'wob-kohlingen' : [ [24, 27, 28, 37, 40], [], [], 0],
    'wob-empire' : [ [1505, 31, 33, 35, 42], [], [], 0],
    'wob-airship': [ [1556], [], [], 0],

    'wor-island' : [ [48], [], [], 1],
    'wor-kefkastower' : [ [49, 51, 52, 65], [], [], 1],
    'wor-fanatics' : [ [69], [], [], 1],
    'wor-figaro' : [ [57, 58], [], [], 1],
    'wor-dragonsneck' : [ [53, 56, 59], [], [3058], 1],
    'wor-jidoor' : [ [62, 63, 70, 73], [], [], 1],
    'wor-narshe' : [ [67, 79], [], [], 1],
    'wor-doma' : [ [76], [], [], 1],
    'wor-dinosaur' : [ [68], [], [], 1],
    'wor-veldt' : [ [61], [], [], 1],
    'wor-thamasa' : [ [75], [], [], 1],
    'wor-ebots' : [ [78], [], [], 1],
    'wor-triangle' : [ [], [2040], [3041], 1],
    'wor-airship' : [ [1554], [], [], 1],

    # Map Shuffle rooms:  connectors
    'ms-wob-4': [[1135], [], [], 0],        # Narshe WOB
    'ms-wob-5': [[1161], [], [], 0],        # Cave to South Figaro N
    'ms-wob-1501': [[1184], [], [], 0],     # Imperial Camp
    'ms-wob-1502': [[1156], [], [], 0],     # Figaro Castle
    'ms-wob-1504': [[1255], [], [], 0],     # Thamasa
    'ms-wob-1505': [[1228], [], [], 0],     # Vector
    'ms-wob-1506': [[269], [], [], 0],      # Cave to South Figaro S
    'ms-wob-6': [[1167, 1168], [], [], 0],        # South Figaro
    'ms-wob-10': [[360, 1174], [], [], 0],  # Sabin's House
    'ms-wob-11': [[1175], [], [], 0],       # Mt Kolts S
    'ms-wob-12': [[1178], [], [], 0],       # Mt Kolts N
    'ms-wob-13': [[1181], [], [], 0],       # Returner's Hideout
    'ms-wob-14': [[1183], [], [], 0],       # Gau's Dad's House
    'ms-wob-15': [[1196], [], [], 0],       # Baren Falls
    'ms-wob-16': [[1199, 1200], [], [], 0],       # Nikeah
    'ms-wob-18': [[1240], [], [], 0],       # Doma
    'ms-wob-20': [[1188], [], [], 0],       # Phantom Forest N
    'ms-wob-21': [[465], [], [], 0],        # Phantom Forest S
    'ms-wob-23': [[523], [], [], 0],        # Crescent Mtn
    'ms-wob-24': [[1209, 1210], [], [], 0],       # Kohlingen
    'ms-wob-26': [[1190], [], [], 0],       # Mobliz
    'ms-wob-27': [[1205], [], [], 0],       # Coliseum guy's house
    'ms-wob-28': [[1213], [], [], 0],       # Jidoor
    'ms-wob-31': [[1238, 1239], [], [], 0],       # Maranda
    'ms-wob-33': [[1244], [], [], 0],       # Tzen
    'ms-wob-35': [[1245], [], [], 0],       # Albrook
    'ms-wob-37': [[1224], [], [], 0],       # Zozo
    'ms-wob-40': [[658], [], [], 0],        # Opera House
    'ms-wob-42': [[1059], [], [], 0],       # Imperial Base
    'ms-wob-44': [[1047], [], [], 0],       # Esper Mtn
    'ms-wob-1556': [[1557], [], [], 0],     # Floating Continent

    'ms-wor-48': [[1267], [], [], 1],       # Cid's House
    'ms-wor-49': [[1249], [], [], 1],       # Albrook
    'ms-wor-51': [[1243], [], [], 1],       # Tzen
    'ms-wor-52': [[1192], [], [], 1],       # Mobliz
    'ms-wor-53': [[1242], [], [], 1],       # Daryl's Tomb
    'ms-wor-56': [[1280], [], [], 1],       # Coliseum
    'ms-wor-57': [[262], [], [], ['ac1'], {'ac1': [1558]}, 1],        # Cave to Figaro Castle, incl. key & entry to ancient castle
    'ms-wor-58': [[1162, 1163], [], [], 1],       # South Figaro
    'ms-wor-59': [[1211, 1212], [], [], 1],       # Kohlingen
    'ms-wor-61': [[978], [], [], 1],        # Cave in the Veldt
    'ms-wor-62': [[4658], [], [], 1],       # Opera House
    'ms-wor-63': [[5238, 5239], [], [], 1],       # Maranda
    'ms-wor-65': [[5199, 5200], [], [], 1],       # Nikeah
    'ms-wor-67': [[1143], [], [], 1],       # Narshe
    'ms-wor-68': [[1187], [], [], 1],       # Gau's Dad's House
    'ms-wor-69': [[1262], [], [], 1],       # Fanatics Tower
    'ms-wor-70': [[5224], [], [], 1],       # Zozo
    'ms-wor-73': [[5213], [], [], 1],       # Jidoor
    'ms-wor-75': [[1261], [], [], 1],       # Thamasa
    'ms-wor-76': [[5240], [], [], 1],       # Doma
    'ms-wor-78': [[1546], [], [], 1],       # Ebot's Rock
    'ms-wor-79': [[1186, 457], [], [], 1],  # Duncan's House
    'ms-wor-1552': [[1553], [], [], 1],     # Zone Eater
    'ms-wor-1554': [[1555], [], [], 1],     # Phoenix Cave
    'ms-wor-1558': [[1082], [], [], 1],     # Ancient Castle

    # Dungeon Crawl Rooms - mostly rooms that bridge towns, use ms- series if a dead end.
    'dc-4': [[1135, 1138], [], [], 0],          # Narshe WOB
    'dc-1501': [[1184, 1560], [], [], 0],       # Imperial Camp + west exit
    'dc-1504': [[1255, 1254], [2054], [3055], 0],     # Thamasa WOB + burning house
    'dc-1505': [[1228, 1229], [], [3028], 0],   # Vector + MTek
    'dc-13': [[1181], [2034], [], 0],           # Returner's Hideout + Lete
    'dc-15': [[1196], [2076], [], 0],           # Baren Falls + one-way exit to Veldt
    'dc-16': [[1199, 1200], [], [3053], 0],     # Nikeah + SerpentTrench dest.
    'dc-20-21': [[1188, 465, 468], [], [], 0],  # Phantom Forest N, S, to train
    'dc-23': [[523], [2044], [], 0],            # Crescent Mtn + SerpentTrench
    'dc-57': [[262], [], [], ['ac1'], {'ac1': [1558]}, 1],  # Cave to Figaro Castle, incl. key & entry to ancient castle, may want to change this.
    'dc-67': [[1143, 1146], [], [], 1],         # Narshe WOR
    'dc-73': [[5213, 593], [], [], 1],          # Jidoor WOR + Owzers
    'dc-75': [[1261, 1260], [], [3075], 1],     # Thamasa WOR + Veldt Cave dest.
    'dc-76': [[5240], [2069], [3074], 1],       # Doma WOR

    # Ruination mode
    #'ruin_hub': [ [], [393, 394, 395], [3097, 3098, 3099], 1],  # Narshe school, 3 doors as oneways
    'ruin_hub': [ [393, 394, 395], [ ], [3039, 3097, 3098, 3099], 1],  # Narshe school, 3 doors, incl. logical returns from KT and from Lete River
    #'ruin_hub_testing': [ [394], [], [3098], 1],  # Narshe school, 2 doors
    'ruin_kt1': [ [], [2097], [3077], 1],       # KT Left
    'ruin_kt2': [ [], [2098], [3078], 1],       # KT Mid
    'ruin_kt3': [ [], [2099], [3079], 1],       # KT Right
    #'ruin_hub_2': [ [], [2077, 2078, 2079], [3097, 3098, 3099], 1],  # Narshe school, 3 doors
    'ruin_kt_entry_1':  [ [1079], [2077], [ ], 1],  # The Sealed Gate
    'ruin_kt_entry_2':  [ [1057], [2078], [ ], 1],  # Esper Mountain Terminus
    'ruin_kt_entry_3':  [ [1564], [2079], [ ], 1],  # Daryl's Tomb staircase + Falcon
    'ruin-mtek3': [[ ], [2128], [3028], 0],   # MTek 3 destination with reward, logically forced to Vector
    'ruin-vector': [[1228, 1229], [], [3128], 0],   # Vector with Mtek3 destination
    'ruin-st-exit': [ [], [2153], [3053], 1],   # Serpent trench entry to nikeah with reward, logically forced to Nikeah WOR
    'ruin-nikeah': [[5199, 5200], [], [3153], 1],  # WOR Nikeah + Serpent Trench exit
    'ruin-daryl': [ [789], [], [], ['dtboss'], {'dtboss': [1563]}, 1], #Darill's Tomb Dullahan Room
    'ruin-201' : [ [469], [2065], [3068], 0],   #Phantom Train Station + custom return from train
    'ruin-thamasa': [[1261, 1260], [], [3055, 3075], [], {'STRAGO': [2054]}, 1],     # Thamasa WOR + Veldt Cave dest + burning house
    'ruin-figarocastle': [[1558], [], [], ['fc1'], {'fc1': [1156, 1157, 1158, 1159]}, 1],  # Cave entrance to Figaro Castle, incl. key locking other entrances
    'ruin-returners': [ [399], [2034], [ ], 0],  # Returners Hideout & Lete River Jumpoff
    'ruin-baren-reward': [ [ ], [2176], [3076], 0],  # End for Baren Falls with reward, logically forced to Veldt Shore
    'ruin-baren': [ [1561], [], [3176], 0],  # End for Baren Falls: door exit to (somewhere)
    'ruin-whelk': [ [178, 179], [ ], [ ], [], {"TERRA": [1155]}, 0],  #Narshe Northern Mines Main Hallway WoB.  Reskin map tileset?
    'ruin-narshe': [[1143, 1146, 140, 143], [], [], 1],         # Narshe WOR, incl. secret passage & entrance to south caves
    'ruin-zozo': [ [4600, 4601, 4602, 4604, 5224], [ ], [ ], ['zr1'], {"TERRA": 608}, 1], #Zozo 1F Outside WOR + Terra-locked 608


    0 : [ [i for i in range(45)] + [i for i in range(1501, 1507)], [ ], [3039], 0],  # World of Balance
    1 : [ [i for i in range(45,80)] + [i for i in range(1507, 1510)], [ ], [3058], 1],  # World of Ruin

    2 : [ [81], [ ], [ ], 0], #Blackjack Outside
    3 : [ [82, 83], [ ], [ ], 0], #Blackjack Gambling Room
    4 : [ [84, 85, 87], [ ], [ ], 0], #Blackjack Party Room
    5 : [ [86], [ ], [ ], 0], #Blackjack Shop Room
    6 : [ [88, 89], [ ], [ ], 0], #Blackjack Engine Room
    7 : [ [90], [ ], [ ], 0], #Blackjack Parlor Room
    8 : [ [91], [ ], [ ], 1], #Falcon Outside
    9 : [ [92, 93, 95], [ ], [ ], 1], #Falcon Main Room
    10 : [ [94], [ ], [ ], 1], #Falcon Small Room
    11 : [ [96], [ ], [ ], 1], #Falcon Engine Room
    12 : [ [1129], [ ], [ ], 0], #Chocobo Stable Exterior WoB
    13 : [ [1131], [ ], [ ], 0], #Chocobo Stable Interior
    '13R' : [ [5131], [ ], [ ], 1], #Chocobo Stable Interior
    14 : [ [1132], [ ], [ ], 1], #Chocobo Stable Exterior WoR

    16 : [ [97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 108, 112, 1135, 1136], [ ], [ ], 0], #Narshe Outside WoB
    17 : [ [107, 111], [ ], [ ], 0], #Narshe Outside Behind Arvis to Mines WoB
    18 : [ [109, 110], [ ], [ ], 0], #Narshe South Caves Secret Passage Outside WoB
    19 : [ [113, 114], [ ], [ ], 0], #Narshe Northern Mines 2nd/3rd Floor Outside WoB
    20 : [ [115, 1139], [ ], [ ], 0], #Narshe Northern Mines 3rd Floor Outside WoB
    21 : [ [1137, 1138], [ ], [ ], 0], #Narshe Northern Mines 1st Floor Outside WoB
    22 : [ [1140, 1141], [ ], [ ], 0], #Snow Battlefield WoB
    23 : [ [1142], [ ], [ ], 0], #Narshe Peak WoB

    # NARSHE SHARED MAPS
    24 : [ [116, 117], [ ], [ ], 0], #Narshe Weapon Shop
    25 : [ [118], [ ], [ ], 0], #Narshe Weapon Shop Back Room
    26 : [ [119, 120], [ ], [ ], 0], #Narshe Armor Shop
    27 : [ [121], [ ], [ ], 0], #Narshe Item Shop
    28 : [ [122], [ ], [ ], 0], #Narshe Relic Shop
    29 : [ [123], [ ], [ ], 0], #Narshe Inn
    30 : [ [124, 125], [ ], [ ], 0], #Narshe Arvis House
    31 : [ [126], [ ], [ ], 0], #Narshe Elder House
    32 : [ [127], [ ], [ ], 0], #Narshe Cursed Shld House
    33 : [ [128], [ ], [ ], 0], #Narshe Treasure Room
    '24R': [[4116, 4117], [], [], 1],  # Narshe Weapon Shop
    '25R': [[4118], [], [], 1],  # Narshe Weapon Shop Back Room
    '26R': [[4119, 4120], [], [], 1],  # Narshe Armor Shop
    '27R': [[4121], [], [], 1],  # Narshe Item Shop
    '28R': [[4122], [], [], 1],  # Narshe Relic Shop
    '29R': [[4123], [], [], 1],  # Narshe Inn
    '30R': [[4124, 4125], [], [], 1],  # Narshe Arvis House
    '31R': [[4126], [], [], 1],  # Narshe Elder House
    '32R': [[4127], [], [], 1],  # Narshe Cursed Shld House
    '33R': [[4128], [], [], 1],  # Narshe Treasure Room

    34 : [ [129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 140, 144, 1143, 1144], [ ], [ ], 1], #Narshe Outside WoR
    35 : [ [139, 143], [ ], [ ], 1], #Narshe Outside Behind Arvis to Mines WoR
    36 : [ [141, 142], [ ], [ ], 1], #Narshe South Caves Secret Passage Outside WoR
    37 : [ [145, 146], [ ], [ ], 1], #Narshe Northern Mines 2nd/3rd Floor Outside WoR
    '37a' : [ [145, 146], [ ], [3009], 1], #Narshe Northern Mines 2nd/3rd Floor Outside WoR incl. exit from Umaro's cave
    38 : [ [147, 1147], [ ], [ ], 1], #Narshe Northern Mines 3rd Floor Outside WoR
    39 : [ [1145, 1146], [ ], [ ], 1], #Narshe Northern Mines 1st Floor Outside WoR
    40 : [ [1148, 1149], [ ], [ ], 1], #Snow Battlefield WoR
    41 : [ [1150], [ ], [ ], 1], #Narshe Peak WoR
    '41a' : [ [1150], [2010], [], 1], # Narshe Peak WoR incl. entrance to Umaro's cave
    42 : [ [148, 149], [ ], [ ], 1], #Narshe Northern Mines 1F Side/East Room WoR
    43 : [ [150, 151], [ ], [ ], 1], #Narshe Northern Mines 2F Inside WoR
    44 : [ [152, 153], [ ], [ ], 1], #Narshe Northern Mines 3F Inside WoR
    45 : [ [154, 155], [ ], [ ], 1], #Narshe South Caves Secret Passage 1F WoR
    46 : [ [156, 157, 1151], [ ], [ ], 1], #Narshe Northern Mines Main Hallway WoR
    47 : [ [158], [ ], [ ], 1], #Narshe Northern Mines Tritoch Room WoR
    48 : [ [159, 160], [ ], [ ], 1], #Narshe Moogle Defense Cave WoR
    49 : [ [161, 162, 163, 164], [ ], [ ], 1], #Narshe South Caves WoR
    50 : [ [165, 166], [ ], [ ], 1], #Narshe Checkpoint Room WoR
    51 : [ [167, 168], [ ], [ ], 1], #Narshe South Caves Secret Passage 3F WoR

    53 : [ [169, 170], [ ], [ ], 0], #Narshe Northern Mines Side Room 1F WoB
    54 : [ [171, 172], [ ], [ ], 0], #Narshe Northern Mines Side Room 2F WoB
    55 : [ [173, 174], [ ], [ ], 0], #Narshe Northern Mines Inside 3F WoB
    56 : [ [175, 176], [ ], [ ], 0], #Narshe South Caves Secret Passage 1F WoB

    59 : [ [178, 179, 1155], [ ], [ ], 0], #Narshe Northern Mines Main Hallway WoB
    60 : [ [180], [ ], [ ], 0], #Narshe Northern Mines Tritoch Room WoB
    61 : [ [181, 182], [ ], [ ], 1], #Narshe Moogle Cave WoR
    62 : [ [183, 184], [ ], [ ], 0], #Narshe South Caves Secret Passage 3F WoB
    63 : [ [185, 186], [ ], [ ], 0], #Narshe Checkpoint Room WoB
    64 : [ [187, 188, 189, 190], [ ], [ ], 0], #Narshe South Caves WoB
    65 : [ [191, 192], [ ], [ ], 0], #Narshe Moogle Defense WoB
    66 : [ [193, 194], [ ], [ ], 0], #Narshe Moogle Cave WoB

    67 : [ [195, 196], [ ], [ ], 1], #Cave to South Figaro Siegfried Tunnel

    # FIGARO CASTLE MAIN
    68 : [ [197, 1156], [ ], [ ], 0], #Figaro Castle Entrance
    69 : [ [198, 199, 201, 204], [ ], [ ], 0], #Figaro Castle Outside Courtyard
    70 : [ [200], [ ], [ ], 0], #Figaro Castle Center Tower Outside
    71 : [ [202, 205, 207, 208, 1156, 1157, 1158, 1159], [ ], [ ], 0], #Figaro Castle Desert Outside
    72 : [ [203], [ ], [ ], 0], #Figaro Castle West Tower Outside
    73 : [ [206], [ ], [ ], 0], #Figaro Castle East Tower Outside
    74 : [ [209, 210], [ ], [ ], 0], #Figaro Castle King's Bedroom
    75 : [ [1160], [ ], [ ], 0], #Figaro Castle Throne Room
    76 : [ [211, 212, 213, 214], [ ], [ ], 0], #Figaro Castle Foyer
    77 : [ [215, 216, 217, 218, 219, 220], [ ], [ ], 0], #Figaro Castle Main Hallway
    78 : [ [221, 222, 223], [ ], [ ], 0], #Figaro Castle Behind Throne Room
    79 : [ [224, 225], [ ], [ ], 0], #Figaro Castle East Bedroom
    80 : [ [226, 227], [ ], [ ], 0], #Figaro Castle Inn
    81 : [ [228], [ ], [ ], 0], #Figaro Castle West Shop
    82 : [ [229], [ ], [ ], 0], #Figaro Castle East Shop
    83 : [ [230, 231], [ ], [ ], 0], #Figaro Castle Below Inn
    84 : [ [232, 233], [ ], [ ], 0], #Figaro Castle Below Library
    85 : [ [234, 235], [ ], [ ], 0], #Figaro Castle Library
    86 : [ [236, 238], [ ], [ ], 0], #Figaro Castle Switch Room
    87 : [ [237], [ ], [ ], 0], #Figaro Castle Prison
    '68R': [[4197, 5156], [], [], 1],  # Figaro Castle Entrance
    '69R': [[4198, 4199, 4201, 4204], [], [], 1],  # Figaro Castle Outside Courtyard
    '70R': [[4200], [], [], 1],  # Figaro Castle Center Tower Outside
    '71R': [[4202, 4205, 4207, 4208, 5156, 5157, 5158, 5159], [], [], 1],  # Figaro Castle Desert Outside
    '72R': [[4203], [], [], 1],  # Figaro Castle West Tower Outside
    '73R': [[4206], [], [], 1],  # Figaro Castle East Tower Outside
    '74R': [[4209, 4210], [], [], 1],  # Figaro Castle King's Bedroom
    '75R': [[5160], [], [], 1],  # Figaro Castle Throne Room
    '76R': [[4211, 4212, 4213, 4214], [], [], 1],  # Figaro Castle Foyer
    '77R': [[4215, 4216, 4217, 4218, 4219, 4220], [], [], 1],  # Figaro Castle Main Hallway
    '78R': [[4221, 4222, 4223], [], [], 1],  # Figaro Castle Behind Throne Room
    '79R': [[4224, 4225], [], [], 1],  # Figaro Castle East Bedroom
    '80R': [[4226, 4227], [], [], 1],  # Figaro Castle Inn
    '81R' : [ [4228], [ ], [ ], 1], #Figaro Castle West Shop
    '82R' : [ [4229], [ ], [ ], 1], #Figaro Castle East Shop
    '83R': [[4230, 4231], [], [], 1],  # Figaro Castle Below Inn
    '84R': [[4232, 4233], [], [], 1],  # Figaro Castle Below Library
    '85R': [[4234, 4235], [], [], 1],  # Figaro Castle Library
    '86R': [[4236, 4238], [], [], 1],  # Figaro Castle Switch Room
    '87R': [[4237, 1558], [], [], 1],  # Figaro Castle Prison

    # FIGARO CASTLE ENGINE ROOM
    88 : [ [239, 240], [ ], [ ], 1], #Figaro Castle B1 Hallway East
    89 : [ [241, 242], [ ], [ ], 1], #Figaro Castle B1 Hallway West
    90 : [ [243, 244], [ ], [ ], 1], #Figaro Castle B2 Hallway
    91 : [ [245, 247], [ ], [ ], 1], #Figaro Castle B2 East Hallway
    92 : [ [246, 248], [ ], [ ], 1], #Figaro Castle B2 West Hallway
    93 : [ [249, 250, 251], [ ], [ ], 1], #Figaro Castle B2 4 Chest Room
    94 : [ [252, 253], [ ], [ ], 1], #Figaro Castle Engine Room
    95 : [ [254], [ ], [ ], 1], #Figaro Castle Treasure Room Behind Engine Room
    96 : [ [255], [ ], [ ], 1], #Figaro Castle B1 Single Chest Room

    # CAVE TO SOUTH FIGARO
    'root-sfcb' : [ [5, 1506], [], [], 0],  # Root map for -door-randomize-south-figaro-cave-wob (to_world_map)
    'root-sfcb-mapsafe' : [ [1513, 268], [], [], 0],  # Root map for -door-randomize-south-figaro-cave-wob (to entry)
    97 : [ [256, 257], [ ], [ ], 1], #Cave to South Figaro Small Hallway WoR
    98 : [ [258, 259, 260], [ ], [ ], 1], #Cave to South Figaro Big Room WoR
    99 : [ [261, 262], [ ], [ ], 1], #Cave to South Figaro South Entrance WoR

    100 : [ [263, 264], [ ], [ ], 0], #Cave to South Figaro Small Hallway WoB
    101 : [ [265, 266, 267], [ ], [ ], 0], #Cave to South Figaro Big Room WoB
    102 : [ [268, 269], [ ], [ ], 0], #Cave to South Figaro South Entrance WoB
    103 : [ [270], [ ], [ ], 0], #Cave to South Figaro Single Chest Room WoB
    104 : [ [271, 272], [ ], [ ], 0], #Cave to South Figaro Turtle Room WoB
    105 : [ [1161, 1513], [ ], [ ], 0], #Cave to South Figaro Outside WoB

    # SOUTH FIGARO
    106 : [ [283, 286, 287, 288, 289, 290, 291, 292, 293, 294, 1162, 1163, 1164, 1165, 1166], [ ], [ ], 1], #South Figaro Outside WoR
    107 : [ [284, 285], [ ], [ ], 1], #South Figaro Rich Man's House Side Outside WoR
    108 : [ [295, 299, 300, 301, 302, 303, 304, 305, 306, 1167, 1169, 1170, 1171], [ ], [ ], 0], #South Figaro Outside WoB
    109 : [ [296, 297], [ ], [ ], 0], #South Figaro Rich Man's House Side Outside WoB
    110 : [ [298, 1168, 1169], [ ], [ ], 0], #South Figaro East Side

    112: [[307, 308], [], [], 0],  # South Figaro Relics
    113: [[309, 310], [], [], 0],  # South Figaro Inn
    114: [[311, 312], [], [], 0],  # South Figaro Armory
    115: [[313, 314, 316], [], [], 0],  # South Figaro Pub
    116: [[315], [], [], 0],  # South Figaro Pub Basement
    117: [[1172], [], [], 0],  # South Figaro Chocobo Stable
    118: [[317, 318, 319], [], [], 0],  # South Figaro Rich Man's House 1F
    119: [[320, 321, 324], [], [], 0],  # South Figaro Rich Man's House 2F Hallway
    120: [[322, 325], [], [], 0],  # South Figaro Rich Man's Master Bedroom
    121: [[323], [], [], 0],  # South Figaro Rich Man's House Kids' Room
    122: [[326, 327], [], [], 0],  # South Figaro Rich Man's House Bedroom Secret Stairwell
    123: [[328, 329, 331, 332, 333], [], [], 0],  # South Figaro Rich Man's House B1
    124: [[330], [], [], 0],  # South Figaro Celes Cell
    125: [[334, 335], [], [], 0],  # South Figaro Clock Room
    126: [[336], [], [], 0],  # South Figaro Duncan's House Basement
    127: [[337], [], [], 0],  # South Figaro Item Shop
    128: [[338], [], [], 0],  # South Figaro Rich Man's House Secret Back Door Room
    129: [[346], [], [], 0],  # South Figaro Cider House Secret Room
    130: [[339, 344], [], [], 0],  # South Figaro Cider House Upstairs
    131: [[340, 343, 348], [], [], 0],  # South Figaro Cider House Downstairs
    132: [[341, 342], [], [], 0],  # South Figaro Behind Duncan's House
    133: [[345, 347], [], [], 0],  # South Figaro Duncan's House Upstairs
    134: [[349, 350, 351], [], [], 0],  # South Figaro Escape Tunnel
    135: [[352], [], [], 0],  # South Figaro Rich Man's House Save Point Room
    136: [[353], [], [], 0],  # South Figaro B2 3 Chest Room
    137: [[354], [], [], 0],  # South Figaro B2 2 Chest Room
    '112R' : [ [4307, 4308], [ ], [ ], 1], #South Figaro Relics
    '113R' : [ [4309, 4310], [ ], [ ], 1], #South Figaro Inn
    '114R' : [ [4311, 4312], [ ], [ ], 1], #South Figaro Armory
    '115R' : [ [4313, 4314, 4316], [ ], [ ], 1], #South Figaro Pub
    '116R' : [ [4315], [ ], [ ], 1], #South Figaro Pub Basement
    '117R' : [ [5172], [ ], [ ], 1], #South Figaro Chocobo Stable
    '118R' : [ [4317, 4318, 4319], [ ], [ ], 1], #South Figaro Rich Man's House 1F
    '119R' : [ [4320, 4321, 4324], [ ], [ ], 1], #South Figaro Rich Man's House 2F Hallway
    '120R' : [ [4322, 4325], [ ], [ ], 1], #South Figaro Rich Man's Master Bedroom
    '121R' : [ [4323], [ ], [ ], 1], #South Figaro Rich Man's House Kids' Room
    '122R' : [ [4326, 4327], [ ], [ ], 1], #South Figaro Rich Man's House Bedroom Secret Stairwell
    '123R' : [ [4328, 4329, 4331, 4332, 4333], [ ], [ ], 1], #South Figaro Rich Man's House B1
    '124R' : [ [4330], [ ], [ ], 1], #South Figaro Celes Cell
    '125R' : [ [4334, 4335], [ ], [ ], 1], #South Figaro Clock Room
    '126R' : [ [4336], [ ], [ ], 1], #South Figaro Duncan's House Basement
    '127R' : [ [4337], [ ], [ ], 1], #South Figaro Item Shop
    '128R' : [ [4338], [ ], [ ], 1], #South Figaro Rich Man's House Secret Back Door Room
    '129R' : [ [4346], [ ], [ ], 1], #South Figaro Cider House Secret Room
    '130R' : [ [4339, 4344], [ ], [ ], 1], #South Figaro Cider House Upstairs
    '131R' : [ [4340, 4343, 4348], [ ], [ ], 1], #South Figaro Cider House Downstairs
    '132R' : [ [4341, 4342], [ ], [ ], 1], #South Figaro Behind Duncan's House
    '133R' : [ [4345, 4347], [ ], [ ], 1], #South Figaro Duncan's House Upstairs
    '134R' : [ [4349, 4350, 4351], [ ], [ ], 1], #South Figaro Escape Tunnel
    '135R' : [ [4352], [ ], [ ], 1], #South Figaro Rich Man's House Save Point Room
    '136R' : [ [4353], [ ], [ ], 1], #South Figaro B2 3 Chest Room
    '137R' : [ [4354], [ ], [ ], 1], #South Figaro B2 2 Chest Room

    138 : [ [355], [ ], [ ], 1], #Cave to South Figaro Single Chest Room WoR
    139 : [ [356], [ ], [ ], 1], #Cave to South Figaro Turtle Room WoR
    140 : [ [357], [ ], [ ], 1], #Cave to South Figaro Turtle Door WoR

    141 : [ [1173], [ ], [ ], 0], #South Figaro Docks
    '141R' : [ [5173], [ ], [ ], 1], #South Figaro Docks

    142 : [ [358, 359], [ ], [ ], 1], #Cave to South Figaro Behind Turtle

    # SABINS HOUSE
    143 : [ [360, 361, 1174], [ ], [ ], 0], #Sabin's House Outside
    144 : [ [362], [ ], [ ], 0], #Sabin's House Inside

    # MT KOLTS
    'root-mk' : [ [11, 12], [], [], 0],  # Root room for Mt Kolts
    'root-mk-mapsafe' : [ [363, 1177], [], [], 0],  # Root room for Mt Kolts (mapsafe)
    145 : [ [363, 1175], [ ], [ ], 0], #Mt. Kolts South Entrance
    146 : [ [364, 365, 366], [ ], [ ], 0], #Mt. Kolts 1F Outside
    147 : [ [367], [ ], [ ], 0], #Mt Kolts Outside Chest 1 Room
    148 : [ [368, 1176], [ ], [ ], 0], #Mt Kolts Outside Cliff West
    149 : [ [369], [ ], [ ], 0], #Mt Kolts Outside Chest 2 Room
    150 : [ [370, 371], [ ], [ ], 0], #Mt. Kolts Outside Bridge
    151 : [ [372, 373], [ ], [ ], 0], #Mt. Kolts Vargas Spiral
    152 : [ [374, 375], [ ], [ ], 0], #Mt. Kolts First Inside Room
    153 : [ [376, 377, 378, 385], [ ], [ ], 0], #Mt. Kolts 4-Way Split Room
    154 : [ [379, 380], [ ], [ ], 0], #Mt. Kolts 2F Inside Room
    155 : [ [381, 382], [ ], [ ], 0], #Mt. Kolts Inside Bridges Room
    156 : [ [383, 384], [ ], [ ], 0], #Mt. Kolts After Vargas Room
    157 : [ [386], [ ], [ ], 0], #Mt Kolts Inside Chest Room
    158 : [ [1177, 1178], [ ], [ ], 0], #Mt. Kolts North Exit
    159 : [ [387, 388, 389, 1179], [ ], [ ], 0], #Mt. Kolts Back Side
    160 : [ [390, 391], [ ], [ ], 0], #Mt. Kolts Save Point Room

    # NARSHE SCHOOL
    161 : [ [392, 393, 394, 395], [ ], [ ], 0], #Narshe School Main Room
    162 : [ [396], [ ], [ ], 0], #Narshe School Left Room
    163 : [ [397], [ ], [ ], 0], #Narshe School Middle Room
    164 : [ [398], [ ], [ ], 0], #Narshe School Right Room
    '161R' : [ [4392, 4393, 4394, 4395], [ ], [ ], 1], #Narshe School Main Room
    '162R' : [ [4396], [ ], [ ], 1], #Narshe School Left Room
    '163R' : [ [4397], [ ], [ ], 1], #Narshe School Middle Room
    '164R' : [ [4398], [ ], [ ], 1], #Narshe School Right Room

    # RETURNERS HIDEOUT
    165 : [ [1180, 1181], [ ], [ ], 0], #Returners Hideout Outside
    166 : [ [399, 400, 401, 402, 403], [ ], [ ], 0], #Returners Hideout Main Room
    167 : [ [404], [ ], [ ], 0], #Returners Hideout Back Room
    168 : [ [405, 406], [ ], [ ], 0], #Returners Hideout Banon's Room
    169 : [ [407], [ ], [ ], 0], #Returner's Hideout Bedroom
    170 : [ [408], [ ], [ ], 0], #Returner's Hideout Inn
    171 : [ [409, 410], [ ], [ ], 0], #Returner's Hideout Secret Passage
    172 : [ [1182], [2034], [ ], 0], #Lete River Jumpoff

    # LETE RIVER
    'LeteRiver1':  [ [ ], [2035], [3034], 0], # Lete River section 1
    'LeteCave1' :  [ [ ], [2036], [3035], 0], # Lete River cave 1
    'LeteRiver2':  [ [ ], [2037], [3036], 0],  # Lete River section 2
    'LeteCave2' :  [ [ ], [2038], [3037], 0],  # Lete River cave 2
    'LeteRiver3':  [ [ ], [2039], [3038], 0],  # Lete River section 3 + boss

    # GAU'S DAD'S HOUSE
    173 : [ [411, 1183], [ ], [ ], 0], #Crazy Old Man's House Outside WoB
    174 : [ [412], [ ], [ ], 0], #Crazy Old Man's House Inside
    '174R' : [ [4412], [ ], [ ], 1], #Crazy Old Man's House Inside

    # IMPERIAL CAMP
    175: [ [1184], [], [], 0],  # Imperial camp WoB, map 0x075

    # DOMA CASTLE
    176: [[417, 432], [], [], 0],  # Doma 3F Inside
    177: [[418, 419, 422, 424, 425, 428, 430, 431, 433], [], [], 0],  # Doma Main Room
    178: [[420], [], [], 0],  # Doma 2F Treasure Room
    179: [[421], [], [], 0],  # Doma Right Side Bedroom
    180: [[423], [], [], 0],  # Doma Throne Room
    181: [[426], [], [], 0],  # Doma Left Side Bedroom
    182: [[427, 429], [], [], 0],  # Doma Inner Room
    183: [[434], [], [], 0],  # Doma Cyan's Room
    '176R': [[4417, 4432], [], [], 1],  # Doma 3F Inside
    '177R': [[4418, 4419, 4422, 4424, 4425, 4428, 4430, 4431, 4433], [], [], 1],  # Doma Main Room
    '178R': [[4420], [], [], 1],  # Doma 2F Treasure Room
    '179R': [[4421], [], [], 1],  # Doma Right Side Bedroom
    '180R': [[4423], [], [], 1],  # Doma Throne Room
    '181R': [[4426], [], [], 1],  # Doma Left Side Bedroom
    '182R': [[4427, 4429], [], [], 1],  # Doma Inner Room
    '183R': [[4434], [], [], 1],  # Doma Cyan's Room

    # DUNCAN'S HOUSE
    194 : [ [458, 457, 1186], [ ], [ ], 1], #Duncan's House Outside
    195 : [ [459], [ ], [ ], 1], #Duncan's House

    196 : [ [460, 1187], [ ], [ ], 1], #Crazy Old Man's House WoR

    # PHANTOM FOREST & TRAIN
    197 : [ [1188, 461], [], [6466], 0],  # Phantom Forest North Room.  Exit 466 also puts you in here!
    198 : [ [462, 463], [], [], 0], # Phantom Forest Healing Pool
    199 : [ [464, 465], [466], [], 0], # Phantom Forest Fork Room.  466 is a normal door behaving as a one-way (!) and 465 goes to world map BUT has an event tile exit....
    200 : [ [467, 468], [], [], 0],  # Phantom Forest Path to Phantom Train (0x087)

    201 : [ [469], [2065], [ ], 0], #Phantom Train Station
    202 : [ [470, 471, 472, 473, 1528, 1529, 1530, 1531, 1532], [ ], [ ], [], {'pt2': [2068]}, 0], #Phantom Train Outside Front Section
    '203a': [[1515, 1516], [], [3065], 0],  # Phantom Train Inside 1st Car
    '203b': [[1523, 1524], [], [3066], 0],  # Phantom Train Inside 2nd Car
    '203c': [[1514], [], [], 0],  # Phantom Train Inside 3rd Car
    204 : [ [474, 475, 476, 1518], [] , [ ], 0], # Phantom Train Outside Car 1 - Caboose
    '204b': [ [1519, 1520], [], [], 0],  # Phantom Train Outside Car 1 - Car 2
    '204c': [ [1521, 1522], [2066, 2067], [], 0],  # Phantom Train Outside Car 2 - Car 3
    205 : [ [1525], [], [3067], 0],  # Phantom Train Outside after jump
    '205b' : [ [1526], [], [], 0],  # Phantom Train Outside after jump & disconnect
    206 : [ [1533, 1534, 1535, 1536], [], [], 0],  # Phantom Train Car 6 Inside (map 0x097)
    '206a' : [ [1537], [], [], 0],  # Phantom Train Car 6 Inside Right Cabin Siegfried Event
    '206b' : [ [1538], [], [], 0],  # Phantom Train Car 6 Inside Left Cabin
    207 : [ [1539, 1540, 1541, 1542], [], [], 0],  # Phantom Train Car 7 Inside (map 0x097 + event_bit 0x17E)
    '207a': [[1543], [], [], 0],  # Phantom Train Car 7 Inside Right Cabin
    '207b': [[1544], [], [], 0],  # Phantom Train Car 7 Inside Left Cabin MIAB room

    212 : [ [1545], [], [], ['pt2'], {}, 0], # Phantom Train Locomotive Interior
    213 : [ [488], [ ], [ ], 0], #Phantom Train Caboose Inner Room

    '215a' : [ [489, 490], [ ], [ ], 0], #Phantom Train Dining Room Left
    '215b' : [ [491, 492], [ ], [ ], 0], #Phantom Train Dining Room Right
    216 : [ [1527], [ ], [ ], ['pt1'], {'pt1': [493, 494]}, 0], #Phantom Train Car 4 with Switch



    220 : [ [496, 497, 498, 499, 500, 501], [ ], [ ], 0], #Phantom Train Caboose
    221 : [ [502], [ ], [ ], 0], #Phantom Train Final Save Point Room


    # MOBLIZ & BAREN FALLS
    225 : [ [503], [ ], [ ], 1], #Mobliz Kids' Hideaway
    226 : [ [504, 505], [ ], [ ], 0], #Baren Falls Inside
    227 : [ [1189], [ ], [ ], 0], #Baren Falls Cliff
    228 : [ [506, 507, 508, 509, 510, 511, 512, 1190, 1191], [ ], [ ], 0], #Mobliz Outside WoB
    229 : [ [1192, 1193, 514, 515, 513], [ ], [ ], 1], #Mobliz Outside WoR

    231 : [ [516], [ ], [ ], 0], #Mobliz Inn
    232 : [ [517, 518], [ ], [ ], 0], #Mobliz Arsenal
    233 : [ [ ], [ ], [ ], 0], # Mobliz Relic Shop
    234 : [ [519], [ ], [ ], 0], #Mobliz Mail Room Upstairs
    '234R' : [ [4519], [ ], [ ], 1], #Mobliz Mail Room Upstairs
    235 : [ [520], [ ], [ ], 0], #Mobliz Item Shop
    236 : [ [521], [ ], [ ], 0], #Mobliz Mail Room Basement WoB
    '236R' : [ [4521, 522], [ ], [ ], 1], #Mobliz Mail Room Basement WoR
    237 : [ [ ], [ ], [ ], 0],  # Mobliz Injured Lad House WoB
    '237R' : [ [ ], [ ], [ ], 1],  # Mobliz Injured Lad House WoR
    238 : [ [ ], [ ], [ ], 1],   # Mobliz Injured Lad Hidden Basement

    239 : [ [1196, 1197], [ ], [ ], 0], #Baren Falls Outside

    ### SERPENT TRENCH & NIKEAH SEQUENCE
    240 : [ [523, 524], [ ], [ ], 0], #Crescent Mountain
    241 : [ [1198], [2044], [ ], 0], #Serpent Trench Cliff

    # SERPENT TRENCH
    '241a' : [ [], [2045, 2046], [3044], 0], # Serpent Trench #1
    246 : [  [], [2047], [3045], 0],  # Serpent Trench Cave 1
    '241b' : [ [], [2048, 2049], [3046, 3047], 0], # Serpent Trench #2
    '247a' : [ [529], [ ], [3048], 0], #Serpent Trench Cave 2 Part A
    '247b' : [ [530], [2050], [ ], 0], #Serpent Trench Cave 2 Part B
    '247c' : [ [ ], [2051], [3050], 0], #Serpent Trench Cave 2 Part C
    '241c' : [ [ ], [2052], [3049, 3051], 0], # Serpent Trench #3
    '241d' : [ [ ], [2053], [3052], 0], # Passthru room for handling ST#3 --> Nikeah transition

    # NIKEAH DOCKS
    259: [[1208], [], [3053], 0],  # Nikeah Docks
    '259R': [[5208], [], [], 1],  # Nikeah Docks

    # NIKEAH
    242 : [ [525, 526, 1199, 1200, 1201, 1202], [ ], [ ], 0], #Nikeah Outside WoB
    243 : [ [527], [ ], [ ], 0], #Nikeah Inn
    244 : [ [528], [ ], [ ], 0], #Nikeah Pub
    245 : [ [1203], [ ], [ ], 0], #Nikeah Chocobo Stable
    '242R' : [ [4525, 4526, 5199, 5200, 5201, 5202], [ ], [ ], 1], #Nikeah Outside WoR
    '243R' : [ [4527], [ ], [ ], 1], #Nikeah Inn
    '244R' : [ [4528], [ ], [ ], 1], #Nikeah Pub
    '245R' : [ [5203], [ ], [ ], 1], #Nikeah Chocobo Stable

    # MOUNT ZOZO
    'root-mz': [[618], [], [], 1],  # Mt Zozo connection (Rusty Door)
    'root-mz_mapsafe': [[30618], [], [], 1],  # Mt Zozo connection (Rusty Door)
    'branch-mz': [[537], [], [], 1],  # Zozo branch to Mount Zozo (for use with Zozo-WoR)
    'branch-mz_mapsafe': [[30537], [], [], 1],  # Zozo branch to Mount Zozo (for use with Zozo-WoR)
    250 : [ [531, 532, 533], [ ], [ ],  1], #Mt Zozo Outside Bridge
    251 : [ [534], [ ], [ ], 1], #Mt Zozo Outside Single Chest Room
    252 : [ [535, 536], [ ], [ ], 1], #Mt Zozo Outside Cliff to Cyan's Cave
    253 : [ [537, 538, 539], [ ], [ ], 1], #Mt Zozo Inside First Room
    '253-mapsafe' : [ [538, 539], [ ], [ ], 1], #Mt Zozo Inside First Room
    254 : [ [540, 541], [ ], [ ], 1], #Mt Zozo Inside Dragon Room
    255 : [ [542, 543], [ ], [ ], 1], #Mt Zozo Cyan's Cave
    256 : [ [1204], [ ], [ ], 1], #Mt Zozo Cyan's Cliff

    #COLISEUM GUY'S HOUSE
    257 : [ [544, 1205, 1206, 1207], [ ], [ ], 0], #Coliseum Guy's House Outside
    258 : [ [545], [ ], [ ], 0], #Coliseum Guy's House Inside

    # KOHLINGEN
    260 : [ [546, 547, 548, 549, 550, 551, 1209, 1210], [ ], [ ], 0], #Kohlingen Outside WoB
    261 : [ [552, 553, 554, 555, 556, 557, 1211, 1212], [ ], [ ], 1], #Kohlingen Outside WoR
    262 : [ [558], [ ], [ ], 0], #Kohlingen Inn Inside
    263 : [ [559, 560], [ ], [ ], 0], #Kohlingen General Store Inside
    264 : [ [561, 563], [ ], [ ], 0], #Kohlingen Chemist's House Upstairs
    265 : [ [562], [ ], [ ], 0], #Kohlingen Chemist's House Downstairs
    266 : [ [564], [ ], [ ], 0], #Kohlingen Chemist's House Back Room
    '262R' : [ [4558], [ ], [ ], 1], #Kohlingen Inn Inside
    '263R' : [ [4559, 4560], [ ], [ ], 1], #Kohlingen General Store Inside
    '264R' : [ [4561, 4563], [ ], [ ], 1], #Kohlingen Chemist's House Upstairs
    '265R' : [ [4562], [ ], [ ], 1], #Kohlingen Chemist's House Downstairs
    '266R' : [ [4564], [ ], [ ], 1], #Kohlingen Chemist's House Back Room

    267 : [ [565], [ ], [ ], 0], #Maranda Lola's House Inside
    '267R' : [ [4565], [ ], [ ], 1], #Maranda Lola's House Inside

    268 : [ [566], [ ], [ ], 0], #Kohlingen Rachel's House Inside
    '268R' : [[4566], [], [], 1],  # Kohlingen Rachel's House Inside

    # JIDOOR
    269 : [ [567, 568, 569, 570, 571, 572, 573, 1213, 1214, 1215, 1216], [ ], [ ], 0], #Jidoor Outside
    270 : [ [574], [ ], [ ], 0], #Jidoor Auction House
    271 : [ [575], [ ], [ ], 0], #Jidoor Item Shop
    272 : [ [576], [ ], [ ], 0], #Jidoor Relic
    273 : [ [577], [ ], [ ], 0], #Jidoor Armor
    274 : [ [578], [ ], [ ], 0], #Jidoor Weapon
    275 : [ [1217], [ ], [ ], 0], #Jidoor Chocobo Stable
    276 : [ [579], [ ], [ ], 0], #Jidoor Inn
    '269R': [[4567, 4568, 4569, 4570, 4571, 4572, 4573, 5213, 5214, 5215, 5216], [], [], 1],  # Jidoor Outside
    '270R': [[4574], [], [], 1],  # Jidoor Auction House
    '271R': [[4575], [], [], 1],  # Jidoor Item Shop
    '272R': [[4576], [], [], 1],  # Jidoor Relic
    '273R': [[4577], [], [], 1],  # Jidoor Armor
    '274R': [[4578], [], [], 1],  # Jidoor Weapon
    '275R': [[5217], [], [], 1],  # Jidoor Chocobo Stable
    '276R': [[4579], [], [], 1],  # Jidoor Inn

    277 : [ [580, 581], [ ], [ ], 1], #Owzer's Behind Painting Room
    278 : [ [582, 583, 585], [ ], [3017], 1], #Owzer's Basement 1st Room
    279 : [ [584], [ ], [ ], 1], #Owzer's Basement Single Chest Room
    280 : [ [586, 587], [2017], [ ], 1], #Owzer's Basement Switching Door Room.  Removed 2nd trap exit (2018)
    281 : [ [588], [2019], [3021], 1], #Owzer's Basement Behind Switching Door Room
    282 : [ [589], [2021], [3020], 1], #Owzer's Basement Save Point Room
    283 : [ [ ], [2020], [3019], 1],  # Owzer's Basement Floating Chest room
    284 : [ [591], [ ], [ ], 1], #Owzer's Basement Chadarnook's Room
    285 : [ [592], [ ], [ ], 0], #Owzer's House
    '285r' : [ [4592, 593], [ ], [ ], 1], #Owzer's House

    # ESPER WORLD
    286 : [ [1218, 1219, 1220, 1221, 1222, 1223], [ ], [ ], 0], #Esper World Outside
    287 : [ [594], [ ], [ ], 0], #Esper World Gate
    288 : [ [595], [ ], [ ], 0], #Esper World Northwest House
    289 : [ [596], [ ], [ ], 0], #Esper World Far East House
    290 : [ [597], [ ], [ ], 0], #Esper World South Right House
    291 : [ [598], [ ], [ ], 0], #Esper World East House
    292 : [ [599], [ ], [ ], 0], #Esper World South Left House

    # ZOZO
    'root-zb': [[600, 601, 602, 604, 608], [], [], 0],  # Zozo 1F Outside WOB
    'root-zr': [[4600, 4601, 4602, 4604], [], [], ['zr1'], {}, 1],  # Zozo 1F Outside WOR
    293 : [ [600, 601, 602, 604, 608, 1224], [ ], [ ], 0], #Zozo 1F Outside WOB
    '293r' : [ [4600, 4601, 4602, 4604, 5224], [ ], [ ], ['zr1'], {}, 1], #Zozo 1F Outside WOB
    294 : [ [603], [ ], [ ], 0], #Zozo 2F Clock Room Balcony Outside
    '294r' : [ [4603], [ ], [ ], 1], #Zozo 2F Clock Room Balcony Outside
    295 : [ [605], [ ], [ ], 0], #Zozo 2F Cafe Balcony Outside
    '295r' : [ [4605], [ ], [ ], 1], #Zozo 2F Cafe Balcony Outside
    296 : [ [606, 607], [ ], [ ], 0], #Zozo Cafe Upstairs Outside WOB (618 --> Mt Zozo not accessible)
    '296r' : [ [4606, 4607], [ ], [ ], [], {'zr1': [618]}, 1], #Zozo Cafe Upstairs Outside WOR
    '296r-mapsafe' : [ [4606, 4607], [ ], [ ], [], {}, 1], #Zozo Cafe Upstairs Outside WOR
    297 : [ [609, 610], [ ], [3032], 0], #Zozo Relic 1st Section Outside (incl. hook entry event)
    298 : [ [611, 612, 616], [2032], [ ], 0], #Zozo Relic 2nd Section Outside (incl. hook exit)
    299 : [ [613, 617], [ ], [ ], ['clock5'], {}, 0], #Zozo Relic 3rd Section Outside
    300 : [ [614, 615, 619], [ ], [ ], 0], #Zozo Relic 4th Section Outside
    301 : [ [620, 621, 622], [ ], [ ], ['clock1'], {}, 0], #Zozo Cafe WoB
    '301r' : [ [4620, 4621, 4622], [ ], [ ], ['clock1'], {}, 1], #Zozo Cafe WoR
    302 : [ [623, 624], [ ], [ ], 0], #Zozo Relic 1st Room Inside
    # 303 : [ [625, 626], [ ], [ ], None], #Zozo Relic 2nd Room Inside - Walking guys create a one-way gate
    '303a' : [ [625], [2033], [ ], ['clock3'], {},  0], #Zozo Relic 2nd Room Inside - entrance
    '303b' : [ [626], [ ], [3033], ['clock3'], {},  0], #Zozo Relic 2nd Room Inside - exit
    304 : [ [627, 628], [ ], [ ], ['clock4'], {},  0], #Zozo West Tower Inside
    305 : [ [629], [ ], [ ], 0], #Zozo Armor
    '305r' : [ [4629], [ ], [ ], 1], #Zozo Armor
    306 : [ [630], [ ], [ ], ['clock2'], {}, 0], #Zozo Weapon WoB
    '306r' : [ [4630], [ ], [ ], ['clock2'], {}, 1], #Zozo Weapon WoR
    '307_clock' : [ [631], [], [3062], [ ], {('clock1', 'clock2', 'clock3', 'clock4', 'clock5'): [2061]}, 0], #Zozo Clock Puzzle Room West WoB INCLUDING clock logic.
    '308_clock' : [ [632], [2062], [], [ ], {'forced':[3061]}, 0], #Zozo Clock Puzzle Room East WoB INCLUDING clock logic
    307 : [ [631], [], [3062], [ ], {}, 0], #Zozo Clock Puzzle Room West WoB, assuming one-way passage  (delete 2061)
    308 : [ [632], [2062], [], [ ], {}, 0], #Zozo Clock Puzzle Room East WoB, assuming one-way passage (delete 3061)
    '307r_clock': [[4631], [], [3064], [], {('clock1', 'clock2', 'clock3', 'clock4', 'clock5'): [2063]}, 1],  # Zozo Clock Puzzle Room West WoR INCLUDING clock logic
    '308r_clock': [[4632], [2064], [], [], {'forced': [3063]}, 1],  # Zozo Clock Puzzle Room East WoR INCLUDING clock logic
    '307r': [[4631], [], [3064], [], {}, 1],  # Zozo Clock Puzzle Room West WoR, assuming one-way passage (delete 2063)
    '308r': [[4632], [2064], [], [], {}, 1],  # Zozo Clock Puzzle Room East WoR, assuming one-way passage (delete 3063)
    #'307a' : [ [631, 632],  [ ], [ ], 0],  #Zozo Clock Puzzle Room (complete)
    #'307r' : [ [4631, 4632],  [ ], [ ], 1],  #Zozo Clock Puzzle Room (complete)
    309 : [ [633], [ ], [ ], 0], #Zozo Cafe Chest Room
    '309r' : [ [4633], [ ], [ ], 1], #Zozo Cafe Chest Room
    310 : [ [634], [ ], [ ], 0], #Zozo Tower 6F Chest Room
    311 : [ [635, 636], [ ], [ ], 0], #Zozo Tower Stairwell Room
    312 : [ [637], [ ], [ ], 0], #Zozo Tower 12F Chest Room
    # Exits 638, 639, 640, 641 appear to be redundant with 634, 635, 636, 637
    313 : [ [1225], [ ], [ ], 0], #Zozo Tower Ramuh's Room

    # OPERA HOUSE - How is this handled?
    314 : [ [642, 643, 644, 645], [ ], [ ], None], #Opera House Balcony WoR and WoB Disruption
    315 : [ [646, 647], [ ], [ ], None], #Opera House Catwalk Stairwell
    316 : [ [648], [ ], [ ], None], #Opera House Switch Room
    317 : [ [649, 650], [ ], [ ], None], #Opera House Balcony WoB
    318 : [ [657], [ ], [ ], None], #Opera House Catwalks
    319 : [ [658, 659], [ ], [ ], 0], #Opera House Lobby WoB
    '319r' : [ [4658, 4659], [ ], [ ], 1], #Opera House Lobby WoR
    320 : [ [662], [ ], [ ], None], #Opera House Dressing Room

    # VECTOR
    321 : [ [1226], [ ], [ ], 0], #Vector After Train Ride
    322 : [ [1228, 1229], [ ], [ ], 0], #Vector Outside
    323 : [ [670], [ ], [ ], 0], #Imperial Castle Entrance

    325 : [ [671, 672, 673], [ ], [ ], 0], #Imperial Castle Roof





    331 : [ [674, 676, 678, 679, 680, 682, 684, 1230], [ ], [ ], 0], #Imperial Castle Main Room
    332 : [ [675], [ ], [ ], 0], #Imperial Castle 2 Chest Room
    333 : [ [677], [ ], [ ], 0], #Imperial Castle Jail Cell
    334 : [ [681, 688], [ ], [ ], 0], #Imperial Castle 2F Bedroom Hallway
    335 : [ [683, 693], [ ], [ ], 0], #Imperial Castle Left Side Roof Stairwell
    336 : [ [685, 694], [ ], [ ], 0], #Imperial Castle Right Side Roof Stairwell

    338 : [ [689, 690], [ ], [ ], 0], #Imperial Castle Bedroom
    339 : [ [691], [ ], [ ], 0], #Imperial Castle Bedroom Bathroom
    340 : [ [692], [ ], [ ], 0], #Imperial Castle Toilet
    341 : [ [1231], [ ], [ ], 0], #Imperial Castle Top Room
    342 : [ [1233], [ ], [ ], 0], #Imperial Castle Banquet Room
    343 : [ [695, 696], [ ], [ ], 0], #Imperial Castle Barracks Room

    # MAGITEK FACTORY
    345 : [ [702], [2023], [ ], 0], #Magitek Factory Upper Room Platform From Lower Room
    346 : [ [703], [2022], [3023], 0], #Magitek Factory Upper Room
    347 : [ [704], [2024, 2025], [3022, 3024, 3026], 0], #Magitek Factory Lower Room

    349 : [ [705, 706], [2026], [3025], 0], #Magitek Factory Garbage Room

    351 : [ [709, 710], [ ], [ ], 0], #Magitek Factory Stairwell
    352 : [ [711], [ ], [ ], 0], #Magitek Factory Save Point Room
    353 : [ [712, 713], [ ], [ ], 0], #Magitek Factory Tube Hallway
    354 : [ [714, 715], [ ], [ ], 0], #Magitek Factory Number 024 Room
    355 : [ [716], [2027], [ ], 0], #Magitek Factory Esper Tube Room
    '355a' : [ [], [2028], [3027], 0],  # Magitek Factory Minecart Room

    'root-ze' : [ [], [2040], [3041], 1], # ZoneEater Engulf
    'root-ze-as-doors': [ [1552, 1553], [], [], 1], # ZoneEater Engulf as doors
    356 : [ [717], [2041], [3040], 1], #Zone Eater Entry Room
    357 : [ [718, 719, 721], [2042], [ ], 1], #Zone Eater Bridge Guards Room
    358 : [ [ ], [2043], [3042], 1], #Zone Eater Pit entry
    '358b' : [ [720], [ ], [3043], 1], #Zone Eater Pit exit
    359 : [ [725, 726], [ ], [ ], 1], #Zone Eater Save Point Room
    '359b': [ [1510, 1511], [ ], [ ], 1], # Zone Eater digestive tract
    361 : [ [722, 723], [ ], [ ], 1], #Zone Eater Short Tunnel
    362 : [ [727, 728], [ ], [ ], 1], #Zone Eater Bridge Switch Room
    363 : [ [724], [ ], [ ], 1], #Zone Eater Gogo Room

    364 : [ [729, 730, 731], [2001, 2002], [3010], 1], #Umaro Cave 1st Room
    365 : [ [732, 733], [ ], [3001, 3002, 3003, 3056, 3057], 1], #Umaro Cave Bridge Room
    366 : [ [734], [2003, 2004], [ ], 1], #Umaro Cave Switch Room
    # 367 : [ [735, 736, 737, 738], [2005, 2006, 2007, 2008], [ ], None], #Umaro Cave 2nd Room
    '367a' : [ [735], [2007], [ ], 1], #Umaro Cave 2nd Room - west
    '367b' : [ [736, 738], [2006, 2008], [ ], 1], #Umaro Cave 2nd Room - middle
    '367c' : [ [737], [2005], [ ], 1], #Umaro Cave 2nd Room - east
    'share_east': [ [], [2056], [3005, 3006], 1], # Umaro Cave west shared pit logical room
    'share_west': [ [], [2057], [3007, 3008], 1], # Umaro Cave west shared pit logical room
    368 : [ [ ], [2009], [3004], 1], # Umaro Cave Umaro's Den

    369 : [ [739, 740, 741, 742, 1238, 1239], [ ], [ ], 0], #Maranda Outside
    '369R' : [ [4739, 4740, 4741, 4742, 5238, 5239], [ ], [ ], 1], #Maranda Outside

    370 : [ [743], [ ], [ ], 0], #Doma 3F Outside
    371 : [ [744, 1240], [ ], [ ], 0], #Doma 1F Outside
    372 : [ [745, 746], [ ], [ ], 0], #Doma 2F Outside
    '370R' : [ [4743], [ ], [ ], 1], #Doma 3F Outside
    '371R' : [ [4744, 5240], [ ], [ ], 1], #Doma 1F Outside
    '372R' : [ [4745, 4746], [ ], [ ], 1], #Doma 2F Outside

    # MARANDA
    374 : [ [750], [ ], [ ], 0], #Maranda Inn
    375 : [ [751], [ ], [ ], 0], #Maranda Weapon Shop
    376 : [ [752], [ ], [ ], 0], #Maranda Armor Shop
    '374R': [[4750], [], [], 1],  # Maranda Inn
    '375R': [[4751], [], [], 1],  # Maranda Weapon Shop
    '376R': [[4752], [], [], 1],  # Maranda Armor Shop

    # DARILL's TOMB
    377 : [ [1241, 1242], [ ], [ ], 1], #Darill's Tomb Outside
    378 : [ [771, 772], [ ], [ ], 1], #Darill's Tomb Entry Room
    379 : [ [773, 774, 776, 778, 780, 783], [ ], [ ], 1], #Darill's Tomb Main Upstairs Room
    380 : [ [775], [ ], [ ], 1], #Darill's Tomb Left Side Tombstone Room
    381 : [ [777, 786], [ ], [ ], 1], #Darill's Tomb Right Side Tombstone Room
    382 : [ [779, 785], [ ], [ ], 1], #Darill's Tomb B2 Left Side Bottom Room
    383 : [ [782], [ ], [ ], [ ], {'dt1': [1512]}, 1], #Darill's Tomb B2 Turtle Hallway.  781 is a shared exit.
    '383a' : [ [782], [ ], [ ], [ ], {'dt1': [1512, 781]}, 1], #Darill's Tomb B2 Turtle Hallway.  781 is a shared exit.
    384 : [ [784], [ ], [ ], 1], #Darill's Tomb B2 Right Side Bottom Room
    #385 : [ [787], [ ], [ ], [ ], {}, 1], #Darill's Tomb Right Side Secret Room Duplicate?
    386 : [ [788], [ ], [ ], 1], #Darill's Tomb B2 Graveyard
    387 : [ [789], [2058], [ ], 1], #Darill's Tomb Dullahan Room
    388 : [ [790, 791], [ ], [ ], 1], #Darills' Tomb B3
    389 : [ [792], [ ], [ ], ['dt2'], {}, 1], #Darills' Tomb B3 Switch Puzzle Room
    390 : [ [793, 794], [2059], [], ['dt3'], {'forced': [3060]}, 1], #Darills' Tomb B2 Switch Puzzle Room Left Side
    391 : [ [], [], [3059], [], {'dt2': [795], 'dt3': [2060]}, 1], # Darills' Tomb B2 Switch Puzzle Room Right Side
    392 : [ [796], [], [], ['dt1'], {}, 1], # Darills' Tomb Right Side Secret Room
    393 : [ [797, 798], [ ], [ ], 1], #Darill's Tomb MIAB Hallway


    395 : [ [803, 804, 805, 806, 807, 808, 1243], [], [], 1],  # Tzen Outside WoR 0x131
    396 : [ [809, 810, 811, 812, 813, 1244], [], [], 0],  # Tzen Outside WoB 0x132
    #397 : [ [], [], [], 1],  # Tzen Item WoR  0x133
    #398 : [ [], [], [], 1],  # Tzen Inn WoR  0x134
    #399 : [ [], [], [], 1],  # Tzen Weapon Shop WoR  0x135
    #400 : [ [], [], [], 1],  # Tzen Armor Shop WoR  0x136
    401 : [ [814, 815], [ ], [ ], 1], #Tzen Collapsing House Downstairs  0x137










    # CYAN DREAM STOOGES MAZE:  0x13d
    421 : [ [], [843, 844], [6845, 6846], 1], # Doma Dream 3 Stooges Maze Northwest Section  0x13d
    422 : [ [], [845], [6844], 1], # Doma Dream 3 Stooges Maze West Section
    423 : [ [], [846], [6847], ['cd1'], {}, 1], # Doma Dream 3 Stooges Maze North Section
    424 : [ [], [847, 848, 849], [6854, 3069], 1], # Doma Dream 3 Stooges Maze Middle Section
    425 : [ [850], [852], [6849, 6843], 1], # Doma Dream 3 Stooges Maze Northeast Section
    426 : [ [851], [], [], 1], # Doma Dream 3 Stooges Maze Southeast Section
    427 : [ [], [853], [6852], ['cd2'], {}, 1], # Doma Dream 3 Stooges Maze East Section
    428 : [ [855], [854], [6848, 6853], 1], # Doma Dream 3 Stooges Maze South Section
    429 : [ [856], [], [], [], {('cd1', 'cd2'): [2070]}, 1], # Doma Dream 3 Stooges Room

    # CYAN DREAM TRAIN: 0x08f exterior; 0x090 car 2; 0x141 car 3; 0x142 car 1
    208 : [ [477, 483], [2071], [ ], 1],  # Doma Dream Train Outside 3rd Section (front)  0x08f
    209 : [ [478, 479, 480, 481], [ ], [ ], 1],  # Doma Dream Train Outside 2nd Section (mid) 0x08f
    210 : [ [482], [ ], [3070], 1],  # Doma Dream Train Outside 1st Section (rear)        0x08f
    211 : [ [484, 485, 486, 487], [ ], [ ], 1],  # Doma Dream Train 2nd Car ("Lump of metal") 0x090
    '221R' : [ [4502], [ ], [ ], 1],  # Doma Dream Train Final Save Point Room
    435 : [ [867], [ ], [ ], ['cd3'], {'cd3': [865, 866]}, 1],  # Doma Dream Train Switch Puzzle Room  0x141
    436 : [ [868, 869, 870, 871], [ ], [ ], 1],  # Doma Dream Train 1st Car   0x142
    '212R' : [ [], [2072], [3071], 1], # Doma Dream Train Locomotive Interior

    # CYAN DREAM CAVES: 0x13f exterior, 0x140 interior
    430: [ [858], [859], [6862], 1],  # Doma Dream Caves Outside Loop     0x13f
    431: [ [860, 861], [2073], [], 1],  # Doma Dream Caves Outside Final Room    0x13f
    432: [ [], [862], [3072], 1],  # Doma Dream Caves Starting Room  0x140
    433: [ [863, 864], [], [6859], 1],  # Doma Dream Caves Inside Loop   0x140

    # CYAN DREAM DOMA: 0x7d exterior, 0x7e interior
    184 : [ [435], [ ], [ ], 1],  # Doma Dream 3F Outside
    185 : [ [436], [ ], [ ], 1],  # Doma Dream 1F Outside
    186 : [ [437, 438], [ ], [ ], 1],  # Doma Dream 2F Outside
    187 : [ [439, 453], [ ], [ ], 1],  # Doma Dream 3F Inside
    188 : [ [440, 441, 445, 449, 451, 452, 454], [ ], [ ], 1],  # Doma Dream Main Room
    '188B' : [ [443], [], [3073], 1], # Doma Dream Right Bedroom with savepoint
    189 : [ [442], [ ], [ ], 1],  # Doma Dream Treasure Room
    190 : [ [447], [ ], [ ], 1],  # Doma Dream Left Bedroom
    191 : [ [444, 446, 448, 450], [ ], [ ], 1],  # Doma Dream Inner Room
    192 : [ [455], [ ], [ ], 1],  # Doma Dream Cyan's Room
    193 : [ [456], [2074], [ ], 1],  # Doma Dream Throne Room

    # ALBROOK:
    437: [ [872, 873, 874, 875, 876, 877, 1245, 1246, 1247, 1248], [], [], 0],   # Albrook WoB, outside (0x143)
    438: [ [878, 879, 880, 881, 882, 883, 1249, 1250, 1251, 1252], [], [], 1],   # Albrook WoR, outside (0x144)
    439: [ [1548], [], [], 0],   # Albrook Inn WoB (0x145)
    '439R': [ [5548], [], [], 1],   # Albrook Inn WoR (shared map 0x145)
    440: [ [1549], [], [], 0],   # Albrook Weapon Shop WoB (0x146)
    '440R': [ [5549], [], [], 1],   # Albrook Weapon Shop WoR (shared map 0x146)
    441: [ [1550], [], [], 0],   # Albrook Armor Shop WoB (0x147)
    '441R': [ [5550], [], [], 1],   # Albrook Armor Shop WoR (shared map 0x147)
    442: [ [1551], [], [], 0],   # Albrook Item Shop WoB (0x148)
    '442R': [ [5551], [], [], 1],   # Albrook Item Shop WoR (shared map 0x148)



    # THAMASA - does WC only use this one Thamasa map (0x154)?
    447 : [ [922, 923, 924, 925, 926, 927, 928, 1253, 1254, 1255], [ ], [ ], 0], #Thamasa After Kefka Outside WoB
    450 : [ [950, 951], [ ], [ ], 0], #Thamasa Arsenal
    451 : [ [952], [2054], [3055], 0], #Thamasa Inn
    452 : [ [953], [ ], [ ], 0], #Thamasa Item Shop
    453 : [ [954], [ ], [ ], 0], #Thamasa Elder's House
    454 : [ [955, 956], [ ], [ ], 0], #Strago's House First Floor
    455 : [ [957], [ ], [ ], 0], #Strago's House Second Floor
    456 : [ [958], [ ], [ ], 0], #Thamasa Relic

    449 : [ [943, 944, 945, 946, 947, 948, 949, 1261, 1259, 1260], [], [], 1],  # Thamasa WoR outside (0x158)
    #'447R': [[4922, 4923, 4924, 4925, 4926, 4927, 4928], [], [], 1],  # Thamasa After Kefka Outside WoR
    '450R': [[4950, 4951], [], [], 1],  # Thamasa Arsenal
    '451R': [[4952], [], [], 1],  # Thamasa Inn
    '452R': [[4953], [], [], 1],  # Thamasa Item Shop
    '453R': [[4954], [], [], 1],  # Thamasa Elder's House
    '454R': [[4955, 4956], [], [], 1],  # Strago's House First Floor
    '455R': [[4957], [], [], 1],  # Strago's House Second Floor
    '456R': [[4958], [], [], 1],  # Thamasa Relic

    # Burning House - event in, event out
    457 : [ [959], [ ], [3054], 0], #Burning House Entry Room
    458 : [ [960, 961, 962], [ ], [ ], 0], #Burning House Second Room
    459 : [ [963, 964], [ ], [ ], 0], #Burning House Third Room
    460 : [ [965, 966, 968], [ ], [ ], 0], #Burning House Fourth Room
    461 : [ [967, 970, 972], [ ], [ ], 0], #Burning House Fifth Room
    462 : [ [969], [ ], [ ], 0], #Burning House 1st Chest Room
    463 : [ [971], [ ], [ ], 0], #Burning House 2nd Chest Room
    464 : [ [973, 974], [ ], [ ], 0], #Burning House Sixth Room
    465 : [ [975], [2055], [ ], 0], #Burning House Final Room

    # CAVE ON THE VELDT
    'root-vc' : [ [61], [], [3075], 1], # Root room for Cave on the Veldt
    'root-vc-mapsafe' : [ [979, 985], [], [3075], 1], # Root room for Cave on the Veldt
    467 : [ [978, 979, 985], [ ], [ ], 1], #Veldt Cave First Room
    468 : [ [980], [ ], [ ], 1], #Veldt Cave Second Room Dead End
    469 : [ [981, 986], [ ], [ ], 1], #Veldt Cave Bandit Room / Second Room
    470 : [ [982, 983], [ ], [ ], 1], #Veldt Cave Third Room
    471 : [ [984, 987], [ ], [ ], 1], #Veldt Cave Bandit Room / Second Room Lower Floor
    472 : [ [988], [ ], [ ], ['vc1'], {'vc1': [989]}, 1], #Veldt Cave Fourth Room Left Side
    #473 : [ [], [ ], [ ], 1], #Veldt Cave Fourth Room Right Side
    474 : [ [990, 992], [ ], [ ], 1], #Veldt Cave Fifth Room
    475 : [ [991], [2075], [ ], 1], #Veldt Cave Final Room

    # FANATIC'S TOWER
    476 : [ [1010, 1011, 1012], [ ], [ ], 1], #Fanatic's Tower 2nd Floor Outside
    477 : [ [1013, 1014, 1015], [ ], [ ], 1], #Fanatic's Tower 3rd Floor Outside
    478 : [ [1016, 1017, 1018], [ ], [ ], 1], #Fanatic's Tower 4th Floor Outside
    479 : [ [1262, 1019], [ ], [ ], 1], #Fanatic's Tower Bottom
    480 : [ [1020, 1021, 1022, 1023], [ ], [ ], 1], #Fanatic's Tower 1st Floor Outside
    481 : [ [1024, 1025], [ ], [ ], 1], #Fanatic's Tower Top
    482 : [ [1026], [ ], [ ], 1], #Fanatic's Tower 1st Floor Treasure Room
    483 : [ [1027], [ ], [ ], 1], #Fanatic's Tower Top Room
    484 : [ [1028], [ ], [ ], 1], #Fanatic's Tower 2nd Floor Treasure Room
    485 : [ [1029], [ ], [ ], 1], #Fanatic's Tower 3rd Floor Treasure Room
    486 : [ [1030], [ ], [ ], 1], #Fanatic's Tower 4th Floor Treasure Room
    487 : [ [1031], [ ], [ ], 1], #Fanatic's Tower 1st Floor Secret Room

    # ESPER MOUNTAIN
    'root-em' : [ [44], [], [], 0], # Root map for -door-randomize-esper-mountain
    'root-em_mapsafe' : [ [1046, 1048, 1049], [], [], 0], # Root map for -door-randomize-esper-mountain
    'root-em_mapsafe_each' : [ [30044], [], [], 0], # Root map for -door-randomize-esper-mountain & map shuffle.  would need to have map shuffle use 31047 instead of 1047...
    488 : [ [1032, 1033], [ ], [ ], 0], #Esper Mountain 3 Statues Room
    489 : [ [1034, 1035, 1036], [ ], [ ], 0], #Esper Mountain Outside Bridge Room
    490 : [ [1037], [ ], [ ], 0], #Esper Mountain Outside East Treasure Room
    491 : [ [1038, 1039, 1040, 1041], [ ], [ ], 0], #Esper Mountain Outside Path to Final Room
    492 : [ [1042, 1043], [ ], [ ], 0], #Esper Mountain Outside Statue Path
    493 : [ [1044], [ ], [ ], 0], #Esper Mountain Outside West Treasure Room
    494 : [ [1045], [ ], [ ], 0], #Esper Mountain Outside Northwest Treasure Room
    495 : [ [1046, 1047, 1048, 1049], [ ], [ ], 0], #Esper Mountain Inside First Room
    496 : [ [1050, 1051], [ ], [3011, 3012, 3013], 0], #Esper Mountain Inside Second Room South Section (with bridge jump entrances)
    497 : [ [1052], [2014, 2015, 2016], [ ], 0], #Esper Mountain Falling Pit Room
    498 : [ [1053, 1054], [2011], [3015], 0], #Esper Mountain Inside Second Room West Section
    499 : [ [1055], [2013], [3016], 0], #Esper Mountain Inside Second Room East Section
    500 : [ [1056], [2012], [3014], 0], #Esper Mountain Inside Second Room North Section
    501 : [ [1057], [ ], [ ], 0], #Esper Mountain Inside Second Room Dead End

    # IMPERIAL BASE & CAVE TO THE SEALED GATE
    502 : [ [1059, 1060, 1058, 1263], [ ], [ ], 0], #Imperial Base
    'root-sg': [[1058, 1263], [], [], 0],  # Root entrance = imperial base
    503 : [ [1061, 1062], [ ], [ ], 0], #Imperial Base House
    504 : [ [1063], [ ], [ ], 0], #Imperial Base House Basement
    '504a' : [ [41, 43], [], [], 0],  # WOB Imperial Base / Cave to Sealed Gate connector
    505 : [ [1064, 1065], [ ], [3031], 0], #Cave to Sealed Gate Entry Room
    506 : [ [1066, 1067], [ ], [ ], 0], #Cave to Sealed Gate B1
    507 : [ [1069, 1264], [2031], [ ], 0], #Cave to Sealed Gate Last Room
    508 : [ [1070], [ ], [3030], 0], #Cave to Sealed Gate Main Room Last Section
    509 : [ [1071, 1072], [2029], [ ], 0], #Cave to Sealed Gate Main Room First Section
    510 : [ [1073], [2030], [3029], 0], #Cave to Sealed Gate Main Room Middle Section
    511 : [ [1074], [ ], [ ], 0], #Cave to Sealed Gate 4 Chest Room
    512 : [ [1075, 1076, 1077], [ ], [ ], 0], #Cave to Sealed Gate Lava Switch Room  # 1076 inaccessible?
    513 : [ [1078], [ ], [ ], 0], #Cave to Sealed Gate Save Point Room
    514 : [ [1079], [ ], [ ], 0], #Sealed Gate

    # CID'S HOUSE
    515 : [ [1080, 1265, 1266, 1267, 1268, 1269, 1270], [ ], [ ], 1], #Solitary Island House Outside
    516 : [ [1081], [ ], [ ], 1], #Solitary Island House Inside
    517 : [ [1271], [ ], [ ], 1], #Solitary Island Beach

    # ANCIENT CAVE & CASTLE
    'root-ac': [ [1558], [], [], 1],  # Ancient Cave connection from Figaro Castle Basement
    520 : [ [1082, 1083, 1085, 1087], [ ], [ ], 1], #Ancient Cave First Room
    521 : [ [1084, 1086, 1088, 1274], [ ], [ ], 1], #Ancient Cave Second Room
    522 : [ [1089, 1275], [ ], [ ], 1], #Ancient Cave Third Room
    523 : [ [1090, 1091], [ ], [ ], 1], #Ancient Cave Save Point Room
    524 : [ [1092, 1093], [ ], [ ], 1], #Ancient Castle West Side South Room
    525 : [ [1094], [ ], [ ], 1], #Ancient Castle East Side Single Chest Room
    526 : [ [1095], [ ], [ ], 1], #Ancient Castle West Side North Room
    527 : [ [1096], [ ], [ ], 1], #Ancient Castle East Side 2 Chest Room
    528 : [ [1098, 1099, 1100, 1278], [ ], [ ], ['ac2'], {}, 1], #Ancient Castle Throne Room
    529 : [ [1276, 1277], [ ], [ ], 1], #Ancient Castle Entry Room
    530 : [ [1101, 1102, 1103, 1104, 1279], [ ], [ ], 1], #Ancient Castle Outside
    531 : [ [1105], [ ], [ ], [], {'ac2': [1106]}, 1], #Ancient Castle Eastern Basement
    532 : [ [1107], [ ], [ ], 1], #Ancient Castle Dragon Room

    # COLISEUM
    533 : [ [1125, 1126, 1280], [ ], [ ], 1], #Coliseum Main Room
    534 : [ [1127], [ ], [ ], 1], #Coliseum Left Room

    # EBOT'S ROCK
    535 : [ [1546], [], [], 1],  # Ebot's Rock entrance, 0x195

    # PHOENIX CAVE
    'root-pc' : [ [1554], [], [], 1],  # Phoenix cave entry as door
    'branch-pc' : [ [1555], [], [], 1],   # Phoenix cave outside (with exit as door) treated as dead end
    536 : [ [1555, 857], [], [], 1],   # Phoenix cave outside (with exit as door)
    537 : [ [828], [], [], 1],   # Phoenix cave interior entrance


    # FLOATING CONTINENT
    'root-fc-as-doors': [[1556], [], [], 0],  # Floating Continent entry as door
    'branch-fc': [[1557], [], [], 0],  # Floating Continent outside at entry
}

# Lists of exits that must be connected
forced_connections = {
    2005 : [3005],   # Umaro's Cave logical handler for pit trapdoor accessible from 2 rooms
    2006 : [3006],   # Umaro's Cave logical handler for pit trapdoor accessible from 2 rooms
    2007 : [3007],   # Umaro's Cave logical handler for pit trapdoor accessible from 2 rooms
    2008 : [3008],   # Umaro's Cave logical handler for pit trapdoor accessible from 2 rooms

    2011 : [3011],   # Esper Mountain Inside 2nd Room: North-to-South bridge jump West
    2012 : [3012],   #      North-to-South bridge jump Mid
    2013 : [3013],   #      North-to-South bridge jump East

    2023 : [3023],   # Magitek factory elevator in Room 1
    #2028 : [3028],   # Magitek minecart ride to Mtek 3 exit

    2029 : [3029],   # Cave to the Sealed Gate, grand staircase
    2030 : [3030],   # Cave to the Sealed Gate, switch bridges
    1079 : [1264],   # Cave to the Sealed Gate, actual Sealed Gate (must be connected to enable shortcut exit)

    2032 : [3032],   # Zozo hook exit from building
    2033 : [3033],   # Zozo walking guys room
    2061 : [3061],   # Zozo WOB clock room W --> E
    2062 : [3062],   # Zozo WOB clock room E --> W
    2063 : [3063],   # Zozo WOR clock room W --> E
    2064 : [3064],   # Zozo WOR clock room E --> W

    2039: [3039],    # Lete river exit to world map

    2043: [3043],    # Zone Eater Pit to handle switch exit

    2046: [3046],    # Serpent Trench #1 continue to #2
    2049: [3049],    # Serpent Trench #2 continue to #3
    2053: [3053],    # Nikeah entry

    2055: [3055],    # Burning House defeating boss --> Thamasa Inn.  This *could* be randomized.

    2059: [3059],    # Daryl's Tomb, Turtle #2 left to right
    2060: [3060],    # Daryl's Tomb, Turtle #2 right to left

    2067: [3067],    # Phantom train roof jump event

    2076: [3076],   # Baren Falls --> Veldt (for now)
    2176: [3176],   # Baren Falls --> Veldt, trickery (reward logic)

    2097: [3097],   # KT left, trickery
    2098: [3098],   # KT mid, trickery
    2099: [3099],   # KT right, trickery
    2128: [3128],   # MTek 3 ending back to vector, trickery.
}

# Add forced connections for virtual doors (-dra)
#if 'root' in room_data.keys():
#    for i in range(8000, 8000+len(room_data['root'][0])):
#        forced_connections[i] = [i+1000]

# List of one-ways that must have the same destination
shared_oneways = {
    # These are better handled with a logical room:  'share_east' = [ [], ['2005L'], [3005, 3006], 1] and
    # and forced connections:  2005: [3005], 2006: [3006]
    #2005: [2006],  # Umaro's cave room 2: east trapdoor (shared exit)
    #2006: [2005],  # Umaro's cave room 2: east trapdoor (shared exit)
    # These are better handled with a logical room:  'share_west' = [ [], ['2007L'], [3007, 3008], 1]
    # and forced connections:  2007: [3007], 2008: [3008]
    #2007: [2008],  # Umaro's cave room 2: west trapdoor (shared exit)
    #2008: [2007],  # Umaro's cave room 2: west trapdoor (shared exit)

    # With JMP, just modify one of them (they call the same code).
    #2017: [2018],   # Owzer's Mansion switching doors (same destination)
    #2018: [2017],    # Owzer's Mansion switching doors (same destination)

}

# Lists of doors that have a shared destination. key_doorID : [doorIDs that share destination]
shared_exits = {
    6: [7, 8, 9],  # South Figaro WoB entrance
    16: [17],      # Nikeah WoB entrance
    18: [19],      # Doma WoB entrance
    21: [22],      # Phantom Forest, south entrance
    24: [25],      # Kohlingen WoB entrance
    28: [29, 30],  # Jidoor WoB entrance
    31: [32],      # Maranda WoB entrance
    33: [34],      # Tzen WoB entrance
    35: [36],      # Albrook WoB entrance
    37: [38, 39],  # Zozo WoB entrance

    49: [50],      # Albrook WoR entrance
    #54: [55],      # Nikeah WoR entrance, pair 1 (not used)
    59: [60],      # Kohlingen WoR entrance
    63: [64],      # Maranda WoR entrance
    65: [66],      # Nikeah WoR entrance, pair 2
    #65: [66, 54, 55],      # Nikeah WoR entrance, both pairs
    70: [71, 72],  # Zozo WoR entrance
    73: [74],      # Jidoor WoR entrance
    76: [77],      # Doma WoR entrance

    1034: [1035],  # Esper Mountain outside bridge, left door
    1038: [1039],  # Esper Mountain Outside Path to Final Room East Door
    1040: [1041],  # Esper Mountain Outside Path to Final Room West Door

    1229: [1226],  # Post-minecart Vector long exit to MTek.  Same destination as normal Vector exit to MTek.

    1059: [1060],  # Imperial camp, left entrance

    1075: [1076],  # Cave to the Sealed Gate, lava switch room: exit 1076 inaccessible (for door exit error?)

    531: [532],    # Mt. Zozo, entrance to dragon room

    1156: [1157, 1158, 1159],     # Figaro Castle exits to world map
    1157: [1158, 1159],     # Figaro Castle exits to world map

    1255: [1254, 1253],   # "Thamasa After Kefka WoB exits to world map"
    1261: [1259, 1260],   # "Thamasa WoR exits to world map"

    960: [961],  # Double door in Burning House Room 2

    1512: [781],  # Daryl's Tomb: Turtle exit event, same as south door.

    496: [498],  # Phantom Train Caboose, left exit
    497: [499],  # Phantom Train Caboose, right exit
    493: [494],  # Phantom Train Car 4, left exit
    1525: [1526], # Phantom Train Car 4 outside --> car 4.

    489: [490],  # Phantom Train dining car left side
    491: [492],  # Phantom Train dining car right side

    484: [485],  # Dream train lump-of-metal room left side
    486: [487],  # Dream train lump-of-metal room right side
    865: [866],  # Doma Dream Train Switch Puzzle Room Left Section  0x141
    868: [869],  # Doma Dream Train 1st Car Left door   0x142
    870: [871],  # Doma Dream Train 1st Car Right door   0x142
    860: [861],  # Doma Dream Caves final room door (not used?)

    360: [1174], # Sabin's house, north & south exits
    457: [1186], # Duncan's house, north & south exits
    364: [365],  # Mt Kolts 1F outside left
    387: [388],  # Mt Koltz back side middle door

    1162: [1163, 1164],  # South Figaro WoR to world map
    1167: [1168, 1169],  # South Figaro WoB to world map

    1238: [1239],        # Maranda WoB to world map
    5238: [5239],        # Maranda WoR to world map

    1245: [1246, 1247],   # Albrook WoB to world map
    1249: [1250, 1251],   # Albrook WoR to world map

    1199: [1200],    # Nikeah WoB to world map
    5199: [5200],    # Nikeah WoR to world map

    1267: [1266, 1268, 1269, 1270],   # Cid's house outside to world map

    1209: [1210],    # Kohlingen WoB to world map
    1211: [1212],    # Kohlingen WoR to world map

    1205: [1206, 1207],  # Coliseum guy's house to world map

    1190: [1191],   # Mobliz WoB to world map
    1192: [1193],   # Mobliz WoR to world map

    1213: [1214, 1215],     # Jidoor WoB
    5213: [5214, 5215],     # Jidoor WoR

    1194: [1195],   # Veldt shore, goes to world map.

    #1092: [1093],   # Ancient Castle, exits from KatanaSoul room?
    #1101: [1102],   # Ancient Castle, entrances to KatanaSoul room?

}

logical_links = [
    [30537, 30618],  # Mt Zozo connection
    [30044, 31047],  # Esper Mtn connection
    #[31558, 31082],  # Ancient Castle connection
]

map_shuffle_protected_doors = {
    'EsperMountain_mapsafe': 1047
}

# In the new Dungeon Crawl mode, some shared exits are split to reduce the number of dead ends.
dungeon_crawl_split_exits = {
    #1156: [1157, 1158, 1159],     # Figaro Castle south vs other exits to world map

    1255: [1254],   # "Thamasa After Kefka WoB exits to world map".  1253 is north, inaccessible
    1261: [1260],   # "Thamasa WoR exits to world map".  1259 is north, inaccessible

    360: [1174],    # Sabin's house, north & south exits
    457: [1186],    # Duncan's house, north & south exits

    1162: [1163],   # South Figaro WoR to world map.  1164 is north, accessible but very rarely used.
    1167: [1168],   # South Figaro WoB to world map.  1169 is north, accessible but very rarely used.

    1238: [1239],    # Maranda WoB to world map
    5238: [5239],    # Maranda WoR to world map

    1199: [1200],    # Nikeah WoB to world map
    5199: [5200],    # Nikeah WoR to world map

    1209: [1210],    # Kohlingen WoB to world map
    1211: [1212],    # Kohlingen WoR to world map

}

# Keys to apply immediately, based on flags.
# '-flag': [True/False, [list of keys to apply]]
# random_clock flag was removed.  it's always random now.
keys_applied_immediately = {
    #'random_clock': [False, ['clock1', 'clock2', 'clock3', 'clock4', 'clock5']]
}

# List of doors that CANNOT be connected to each other.  Only rare instances.
# Superceded by walk method
# invalid_connections = {
#     702 : [703],  # Magitek factory room 1: entrance & platform door
#     703 : [702],
# }

# List of rooms that should have a forced update to Parent Map variable when entering.
# force_update_parent_map[roomID] = [x, y, mapID]
# force_update_parent_map = {
#     '285a' : [1, 34, 157]  # Entering WoR Jidoor from Owzer's Basement
# }

def get_locked_items(locks):
    locked = []
    for v in locks.values():
        for vv in v:
            if type(vv) is dict:
                locked.extend(get_locked_items(vv))
            else:
                locked.append(vv)
    return locked

# Create dictionary lookup for which world each exit is in
exit_world = {}
exit_room = {}
for r in room_data.keys():
    locked = []
    if len(room_data[r]) > 4:
        #contains locked elements.
        locked = [item for item in get_locked_items(room_data[r][4]) if type(item) is int]

    # Read in door world
    these_doors = [d for d in room_data[r][0]] + [d for d in locked if d < 2000]
    for d in these_doors:
        exit_world[d] = room_data[r][-1]
        exit_room[d] = r
        #if d in shared_oneways.keys():
        #    for ds in shared_oneways[d]:
        #        exit_world[ds] = room_data[r][-1]
        #        exit_room[d]

    # Read in one-way world
    these_traps = [t for t in room_data[r][1]] + [t for t in locked if 2000 <= t < 3000]
    for t in these_traps:
        exit_world[t] = room_data[r][-1]
        exit_room[t] = r

    # Read in one-way exits
    these_pits = [p for p in room_data[r][2]] + [p for p in locked if 3000 <= p < 4000 or 6000 < p]
    for p in these_pits:
        exit_world[p] = room_data[r][-1]
        exit_room[p] = r

# Generate a list of doors that act as trapdoors
doors_as_traps = []
doors_as_traps_2 = []
for r in room_data.keys():
    traps = [t for t in room_data[r][1]]
    for t in traps:
        if isinstance(t, int):
            if t < 2000:
                doors_as_traps.append(t)
    pits = [p for p in room_data[r][2]]
    for p in pits:
        if isinstance(p, int):
            if p >= 6000:
                doors_as_traps_2.append(p-6000)
test = [d for d in doors_as_traps if d not in doors_as_traps_2] +  [d for d in doors_as_traps_2 if d not in doors_as_traps]
if len(test) > 0:
    print('BROKEN DOOR/TRAP pairs:', test)
