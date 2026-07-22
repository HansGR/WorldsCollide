"""Room definitions for door randomization.

room_data maps each room id to its elements:
    [ [2-way doors], [1-way exits (traps)], [1-way entrances (pits)], world ]
or, for rooms with key/lock behavior,
    [ [doors], [traps], [pits], [keys], {lock: [elements]}, world ]
The trailing field is the room's world (0 = WoB, 1 = WoR).

Room ids are human-readable names built from the 3-letter AREA_CODES
registry below (numbers are exits; formatted strings are rooms):

  Rooms      CODE + world? + NN + subletter? + (-variant)?
             world  b = WoB, r = WoR, x = no world; only present for
                    areas that exist in both worlds
             NN     ordinal within the area and world; WoB/WoR twins of
                    the same place share it (ALBb01 / ALBr01); logical
                    and mode-specific rooms occupy a band starting at 50
             sub    physical sub-room split (UPNr01a)
             -variant  mode variant of the base room (-ruin, -dc,
                    -mapsafe, -branch, -share, -test), keeping its
                    parent room's ordinal (ZOZr01-ruin)
  Roots      CODE + world? + -root(-suffix)?  (no ordinal: roots are
             connection points for the world model, not rooms)
  Lanes      Kefka's Tower and Cyan's Dream are each three lanes with
             one code per lane, in game order: KTA/KTB/KTC (left, mid,
             right party) and CDA/CDB/CDC (train, caves, Doma castle).
             CD lanes use the ordinary room grammar (CDA01); KT rooms
             keep their structured tails (KTA1, KTA5a, KTA-final).
  Map shuffle  MAP + world + - + target area code (+digit when one area
             has several stubs): MAPb-GFH. Stubs connect the world map
             into their whole area.
  World map  'wob' / 'wor' and the named world-map segments
             ('wob-narshe', 'wor-triangle', ...); these belong to no area.

``# was:`` comments record each room's pre-name id (largely vanilla map
numbering), the numbering used by claude_reference data and older notes.
tools/compile_atlas.py --check validates the ids against this grammar.
"""

AREA_CODES = {
    'AIR': 'Airship',
    'ALB': 'Albrook',
    'ANC': 'AncientCastle',
    'BAR': 'BarenFalls',
    'BUR': 'BurningHouse',
    'CDA': 'CyansDreamTrain',
    'CDB': 'CyansDreamCaves',
    'CDC': 'CyansDreamDoma',
    'CHO': 'ChocoboStables',
    'CID': 'Cid',
    'COL': 'Coliseum',
    'COV': 'CaveOnTheVeldt',
    'CRE': 'CrescentMtn',
    'DAR': 'DarylsTomb',
    'DOM': 'Doma',
    'DRM': 'DreamMaze',
    'DUN': 'DuncanHouse',
    'EBO': 'EbotsRock',
    'ESM': 'EsperMountain',
    'ESW': 'EsperWorld',
    'FAN': 'FanaticsTower',
    'FIG': 'FigaroCastle',
    'FLO': 'FloatingContinent',
    'GFH': 'GauFatherHouse',
    'HUB': 'RuinHub',
    'IMP': 'ImperialCamp',
    'JID': 'Jidoor',
    'KOH': 'Kohlingen',
    'KTA': 'KefkasTowerLeft',
    'KTB': 'KefkasTowerMid',
    'KTC': 'KefkasTowerRight',
    'LET': 'Lete',
    'MAP': 'MapShuffle',
    'MAR': 'Maranda',
    'MOB': 'Mobliz',
    'MTF': 'MagitekFactory',
    'MTK': 'MtKolts',
    'MTZ': 'MtZozo',
    'NAR': 'Narshe',
    'NIK': 'Nikeah',
    'OPE': 'OperaHouse',
    'OWZ': 'OwzerBasement',
    'PHF': 'PhantomForest',
    'PHO': 'PhoenixCave',
    'PHT': 'PhantomTrain',
    'RET': 'ReturnersHideout',
    'SAB': 'SabinsHouse',
    'SEA': 'SealedGate',
    'SER': 'SerpentTrench',
    'SFC': 'SouthFigaroCave',
    'SFI': 'SouthFigaro',
    'THA': 'Thamasa',
    'TZE': 'Tzen',
    'UMA': 'Umaro',
    'UPN': 'UpperNarshe',
    'VEC': 'Vector',
    'VIC': 'VectorImperialCastle',
    'ZON': 'ZoneEater',
    'ZOZ': 'Zozo',
}

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
    'UMA-root' : [ [], [2010], [3009], 1], # was: root-u; Root map for -door-randomize-umaro
    'UPNb-root' : [ [1138], [], [], 0], # was: root-unb; Root map for -door-randomize-upper-narshe-wob
    'UPNr-root' : [ [1146], [], [], 1], # was: root-unr; Root map for -door-randomize-upper-narshe-wor
    'OWZr-root' : [ [593], [], [], 1], # was: root-ob; Root map for -door-randomize-owzer's basement
    'MTF-root' : [ [1229], [], [3028], 0],     # was: root-mf; Magitek Factory root entrance in Vector
    #'ZOZb-root': [ [37, 38, 39], [], [], 0],  # Zozo WoB entrance (for Terra check)
    #'ZOZr-root': [ [70, 71, 72], [], [], 1],  # Zozo WoR entrance (for Mt Zozo check)
    'LET-root' : [ [], [2034], [3039], 0],  # was: root-lr; Root map for -door-randomize-lete
    'SER-root' : [ [ ], [2044], [3053], 0], # was: root-st; Root map for -door-randomize-serpent-trench
    'BUR-root' : [ [ ], [2054], [3055], 0],  # was: root-bh; Root map for -door-randomize-burning-house
    'DAR-root' : [ [1241], [], [3058], 1],  # was: root-dt; Root map for -door-randomize-darills-tomb
    'CDA-root' : [ [], [2069], [3074], 1], # was: root-cd; Root room for Cyan's Dream
    'PHT-root' : [ [468], [], [3068], 0],  # was: root-pt; Root map for Phantom Train

    # Map Shuffle rooms:  World Maps
    #'MAPb-root' : [ [6, 1556], [], [], 0],  # Root map for WOB map shuffle testing
    'MAPb-root' : [ [4, 5, 1501, 1502, 1504, 1505, 1506, 6, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 23, 24, 26, 27, 28, 31, 33, 35, 37, 40, 42, 44, 1556], [], [], 0],  # was: shuffle-wob; Root map for WOB map shuffle (does not include connector to Sealed Gate Cave or chocobo stables)
    #'MAPr-root' : [ [1558, 51], [], [], 1],  # Root map for WOR map shuffle testing  1554 = Phoenix Cave
    'MAPr-root' : [ [48, 49, 51, 52, 53, 56, 57, 58, 59, 61, 62, 63, 65, 67, 68, 69, 70, 73, 75, 76, 78, 79, 1552, 1554], [], [], 1],  # was: shuffle-wor; Root map for WOR map shuffle (does not include Figaro Castle, KT, Phoenix Cave or chocobo stables).  Note: extra Nikeah doors are 54, 55.

    # Root map for dungeon crawl mode.  Includes lete river terminus, zone eater entry/exit, phantom train fast exit, daryl's tomb fast exit
    #'dc-world' : [ [4, 5, 1501, 1502, 1504, 1505, 1506, 6, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 23, 24, 26, 27, 28,  #
    #                31, 33, 35, 37, 40, 42, 44, 1556,
    #                48, 49, 51, 52, 53, 56, 57, 58, 59, 61, 62, 63, 65, 67, 69, 70, 73, 75, 76, 78, 79, 1552, 1554],  # 68,
    #               [2040], [3039, 3041, 3058, 3068], 0],

    # World Map Rooms: which exits on the world map you can walk to from which other ones.
    'wob-narshe' : [ [4, 5, 1502], [], [3039], 0],  # was: wob-narshe
    'wob-figaro' : [ [1506, 6, 10, 11], [], [], 0],  # was: wob-figaro
    'wob-sabil' : [ [12, 13], [], [], 0],  # was: wob-sabil
    'wob-nikeah' : [ [16, 14, 1501], [], [], 0],  # was: wob-nikeah
    'wob-doma' : [ [1559, 18, 20], [], [], 0],  # was: wob-doma
    'wob-baren' : [ [21, 15], [], [3068], 0],  # was: wob-baren
    'wob-veldt' : [ [23, 26], [], [3076], 0],  # was: wob-veldt
    'wob-thamasa' : [ [1504, 44], [], [], 0],  # was: wob-thamasa
    'wob-kohlingen' : [ [24, 27, 28, 37, 40], [], [], 0],  # was: wob-kohlingen
    'wob-empire' : [ [1505, 31, 33, 35, 42], [], [], 0],  # was: wob-empire
    'wob-airship': [ [1556], [], [], 0],  # was: wob-airship

    'wor-island' : [ [48], [], [], 1],  # was: wor-island
    'wor-kefkastower' : [ [49, 51, 52, 65], [], [], 1],  # was: wor-kefkastower
    'wor-fanatics' : [ [69], [], [], 1],  # was: wor-fanatics
    'wor-figaro' : [ [57, 58], [], [], 1],  # was: wor-figaro
    'wor-dragonsneck' : [ [53, 56, 59], [], [3058], 1],  # was: wor-dragonsneck
    'wor-jidoor' : [ [62, 63, 70, 73], [], [], 1],  # was: wor-jidoor
    'wor-narshe' : [ [67, 79], [], [], 1],  # was: wor-narshe
    'wor-doma' : [ [76], [], [], 1],  # was: wor-doma
    'wor-dinosaur' : [ [68], [], [], 1],  # was: wor-dinosaur
    'wor-veldt' : [ [61], [], [], 1],  # was: wor-veldt
    'wor-thamasa' : [ [75], [], [], 1],  # was: wor-thamasa
    'wor-ebots' : [ [78], [], [], 1],  # was: wor-ebots
    'wor-triangle' : [ [], [2040], [3041], 1],  # was: wor-triangle
    'wor-airship' : [ [1554], [], [], 1],  # was: wor-airship

    # Map Shuffle rooms:  connectors
    'MAPb-NAR': [[1135], [], [], 0],        # was: ms-wob-4; Narshe WOB
    'MAPb-SFC2': [[1161], [], [], 0],        # was: ms-wob-5; Cave to South Figaro N
    'MAPb-IMP': [[1184], [], [], 0],     # was: ms-wob-1501; Imperial Camp
    'MAPb-FIG': [[1156], [], [], 0],     # was: ms-wob-1502; Figaro Castle
    'MAPb-THA': [[1255], [], [], 0],     # was: ms-wob-1504; Thamasa
    'MAPb-VEC': [[1228], [], [], 0],     # was: ms-wob-1505; Vector
    'MAPb-SFC': [[269], [], [], 0],      # was: ms-wob-1506; Cave to South Figaro S
    'MAPb-SFI': [[1167, 1168], [], [], 0],        # was: ms-wob-6; South Figaro
    'MAPb-SAB': [[360, 1174], [], [], 0],  # was: ms-wob-10; Sabin's House
    'MAPb-MTK': [[1175], [], [], 0],       # was: ms-wob-11; Mt Kolts S
    'MAPb-MTK2': [[1178], [], [], 0],       # was: ms-wob-12; Mt Kolts N
    'MAPb-RET': [[1181], [], [], 0],       # was: ms-wob-13; Returner's Hideout
    'MAPb-GFH': [[1183], [], [], 0],       # was: ms-wob-14; Gau's Dad's House
    'MAPb-BAR': [[1196], [], [], 0],       # was: ms-wob-15; Baren Falls
    'MAPb-NIK': [[1199, 1200], [], [], 0],       # was: ms-wob-16; Nikeah
    'MAPb-DOM': [[1240], [], [], 0],       # was: ms-wob-18; Doma
    'MAPb-PHF': [[1188], [], [], 0],       # was: ms-wob-20; Phantom Forest N
    'MAPb-PHF2': [[465], [], [], 0],        # was: ms-wob-21; Phantom Forest S
    'MAPb-CRE': [[523], [], [], 0],        # was: ms-wob-23; Crescent Mtn
    'MAPb-KOH': [[1209, 1210], [], [], 0],       # was: ms-wob-24; Kohlingen
    'MAPb-MOB': [[1190], [], [], 0],       # was: ms-wob-26; Mobliz
    'MAPb-COL': [[1205], [], [], 0],       # was: ms-wob-27; Coliseum guy's house
    'MAPb-JID': [[1213], [], [], 0],       # was: ms-wob-28; Jidoor
    'MAPb-MAR': [[1238, 1239], [], [], 0],       # was: ms-wob-31; Maranda
    'MAPb-TZE': [[1244], [], [], 0],       # was: ms-wob-33; Tzen
    'MAPb-ALB': [[1245, 1246], [], [], 0],       # was: ms-wob-35; Albrook
    'MAPb-ZOZ': [[1224], [], [], 0],       # was: ms-wob-37; Zozo
    'MAPb-OPE': [[658], [], [], 0],        # was: ms-wob-40; Opera House
    'MAPb-SEA': [[1059], [], [], 0],       # was: ms-wob-42; Imperial Base
    'MAPb-ESM': [[1047], [], [], 0],       # was: ms-wob-44; Esper Mtn
    'MAPb-FLO': [[1557], [], [], 0],     # was: ms-wob-1556; Floating Continent

    'MAPr-CID': [[1267], [], [], 1],       # was: ms-wor-48; Cid's House
    'MAPr-ALB': [[1249, 1250], [], [], 1],       # was: ms-wor-49; Albrook
    'MAPr-TZE': [[1243], [], [], 1],       # was: ms-wor-51; Tzen
    'MAPr-MOB': [[1192], [], [], 1],       # was: ms-wor-52; Mobliz
    'MAPr-DAR': [[1242], [], [], 1],       # was: ms-wor-53; Daryl's Tomb
    'MAPr-COL': [[1280], [], [], 1],       # was: ms-wor-56; Coliseum
    'MAPr-SFC': [[262], [], [], ['ac1'], {'ac1': [1558]}, 1],        # was: ms-wor-57; Cave to Figaro Castle, incl. key & entry to ancient castle
    'MAPr-SFI': [[1162, 1163], [], [], 1],       # was: ms-wor-58; South Figaro
    'MAPr-KOH': [[1211, 1212], [], [], 1],       # was: ms-wor-59; Kohlingen
    'MAPr-COV': [[978], [], [], 1],        # was: ms-wor-61; Cave in the Veldt
    'MAPr-OPE': [[4658], [], [], 1],       # was: ms-wor-62; Opera House
    'MAPr-MAR': [[5238, 5239], [], [], 1],       # was: ms-wor-63; Maranda
    'MAPr-NIK': [[5199, 5200], [], [], 1],       # was: ms-wor-65; Nikeah
    'MAPr-NAR': [[1143], [], [], 1],       # was: ms-wor-67; Narshe
    'MAPr-GFH': [[1187], [], [], 1],       # was: ms-wor-68; Gau's Dad's House
    'MAPr-FAN': [[1262], [], [], 1],       # was: ms-wor-69; Fanatics Tower
    'MAPr-ZOZ': [[5224], [], [], 1],       # was: ms-wor-70; Zozo
    'MAPr-JID': [[5213], [], [], 1],       # was: ms-wor-73; Jidoor
    'MAPr-THA': [[1261], [], [], 1],       # was: ms-wor-75; Thamasa
    'MAPr-DOM': [[5240], [], [], 1],       # was: ms-wor-76; Doma
    'MAPr-EBO': [[1546], [], [], 1],       # was: ms-wor-78; Ebot's Rock
    'MAPr-DUN': [[1186, 457], [], [], 1],  # was: ms-wor-79; Duncan's House
    'MAPr-ZON': [[1553], [], [], 1],     # was: ms-wor-1552; Zone Eater
    'MAPr-PHO': [[1555], [], [], 1],     # was: ms-wor-1554; Phoenix Cave
    'MAPr-ANC': [[1082], [], [], 1],     # was: ms-wor-1558; Ancient Castle

    # Dungeon Crawl Rooms - mostly rooms that bridge towns, use ms- series if a dead end.
    'NARb01-dc': [[1135, 1138], [], [], 0],          # was: dc-4; Narshe WOB
    'IMP01-dc': [[1184, 1560], [], [], 0],       # was: dc-1501; Imperial Camp + west exit
    'THAb01-dc': [[1255, 1254], [2054], [3055], 0],     # was: dc-1504; Thamasa WOB + burning house
    'VEC01-dc': [[1228, 1229], [], [3028], 0],   # was: dc-1505; Vector + MTek
    'RET01-dc': [[1181], [2034], [], 0],           # was: dc-13; Returner's Hideout + Lete
    'BAR03-dc': [[1196], [2076], [], 0],           # was: dc-15; Baren Falls + one-way exit to Veldt
    'NIKb01-dc': [[1199, 1200], [], [3053], 0],     # was: dc-16; Nikeah + SerpentTrench dest.
    'PHF01-dc': [[1188, 465, 468], [], [], 0],  # was: dc-20-21; Phantom Forest N, S, to train
    'CRE01-dc': [[523], [2044], [], 0],            # was: dc-23; Crescent Mtn + SerpentTrench
    'SFCr04-dc': [[262], [], [], ['ac1'], {'ac1': [1558]}, 1],  # was: dc-57; Cave to Figaro Castle, incl. key & entry to ancient castle, may want to change this.
    'NARr01-dc': [[1143, 1146], [], [], 1],         # was: dc-67; Narshe WOR
    'JIDr01-dc': [[5213, 593], [], [], 1],          # was: dc-73; Jidoor WOR + Owzers
    'THAr01-dc': [[1261, 1260], [], [3075], 1],     # was: dc-75; Thamasa WOR + Veldt Cave dest.
    'DOMr10-dc': [[5240], [2069], [3074], 1],       # was: dc-76; Doma WOR
    'DOMr02-ruin': [[4418], [2069], [3074], 1],    # was: ruin-doma; Doma WOR interior (ruination split: indoor stays WoR)

    # Ruination mode
    #'HUB50-ruin': [ [], [393, 394, 395], [3097, 3098, 3099], 1],  # Narshe school, 3 doors as oneways
    'HUB50-ruin': [ [393, 394, 395], [ ], [3039, 3097, 3098, 3099], 1],  # was: ruin_hub; Narshe school, 3 doors, incl. logical returns from KT and from Lete River

    'HUB51-test': [ [393, 394, 395], [], [3097, 3098, 3099], 1],  # was: ruin_hub_testing; Narshe school, 2 doors
    'NIKr51-test': [ [523, 5199, 5200], [], [], 1],   # was: ruin_testing; Room with 2 doors to test out checks in -ruin.
    # e.g. moogle defense [[191, 192]],  # WOR Zozo [5224, 4600],  # Nikeah Serpent Trench []

    'KTA-ruin': [ [], [2097], [3077], 1],       # was: ruin_kt1; KT Left
    'KTB-ruin': [ [], [2098], [3078], 1],       # was: ruin_kt2; KT Mid
    'KTC-ruin': [ [], [2099], [3079], 1],       # was: ruin_kt3; KT Right
    #'ruin_hub_2': [ [], [2077, 2078, 2079], [3097, 3098, 3099], 1],  # Narshe school, 3 doors
    'KTA0-ruin':  [ [1079], [2077], [ ], 1],  # was: ruin_kt_entry_1; The Sealed Gate
    'KTB0-ruin':  [ [1057], [2078], [ ], 1],  # was: ruin_kt_entry_2; Esper Mountain Terminus
    'KTC0-ruin':  [ [1564], [2079], [ ], 1],  # was: ruin_kt_entry_3; Daryl's Tomb staircase + Falcon
    'HUB52-ruin':  [ [1079], [], [ ], 1],  # was: ruin_terminus_1; The Sealed Gate (KT connection will be patched separately)
    'HUB53-ruin':  [ [1057], [], [ ], 1],  # was: ruin_terminus_2; Esper Mountain Terminus (KT connection will be patched separately)
    'HUB54-ruin':  [ [1564], [], [ ], 1],  # was: ruin_terminus_3; Daryl's Tomb staircase + Falcon (KT connection will be patched separately)
    'MTF50-ruin': [[ ], [2128], [3028], 0],   # was: ruin-mtek3; MTek 3 destination with reward, logically forced to Vector
    'VEC01-ruin': [[1228, 1229], [], [3128], 0],   # was: ruin-vector; Vector with Mtek3 destination
    'CRE01-ruin': [[523], [ ], [], [ ], {'GAU': [2044]},  0],            # was: ruin-st-entr; Crescent Mtn + SerpentTrench. Not sure we want to keep GAU lock on this...
    'NIKr52-ruin': [ [], [2153], [3053], 1],   # was: ruin-st-exit; Serpent trench entry to nikeah with reward, logically forced to Nikeah WOR
    'NIKr01-ruin': [[5199, 5200], [], [3153], 1],  # was: ruin-nikeah; WOR Nikeah + Serpent Trench exit
    'DAR10-ruin': [ [789], [], [], ['dtboss'], {('dtboss', 'SETZER'): [1563]}, 1], # was: ruin-daryl; Darill's Tomb Dullahan Room
    'PHT01-ruin' : [ [469], [2065], [3068], 0],   # was: ruin-201; Phantom Train Station + custom return from train
    'PHT02-ruin' : [ [470, 471, 472, 473, 1528, 1529, 1530, 1531, 1532], [ ], [ ], [], {('pt2','SABIN'): [2068]}, 0], # was: ruin-202; Phantom Train Outside Front Section with character gating
    'PHF01-ruin' : [ [1188, 465, 468], [], [], 0],   # was: ruin-phantomforest; Phantom Forest, all rooms + spring (internally randomized)
    'THAr01-ruin': [[1261, 1260], [], [3055, 3075, 3085], [], {'STRAGO': [2054]}, 1],     # was: ruin-thamasa; Thamasa WOR + Veldt Cave dest + burning house + Ebot's Rock character reward dest (pit 3085)
    'FIGr04-ruin': [[5156, 5157, 5158, 5159], [], [], ['fcer'], {('EDGAR', 'fcer'): [1558]}, 1],  # was: ruin-figarocastle; Figaro Castle world map entrances (Ancient Castle entrance 1558 locked by engine room, which is locked by Edgar)
    'RET02-ruin': [ [399], [2034], [ ], 0],  # was: ruin-returners; Returners Hideout & Lete River Jumpoff
    'BAR01-ruin': [[504], [], [], [], {"SABIN": [2076]}, 0],           # was: ruin-baren-falls; Baren Falls + one-way exit to Veldt.  Skip outside entry room (1196)
    'BAR50-ruin': [ [ ], [2176], [3076], 0],  # was: ruin-baren-reward; End for Baren Falls with reward, logically forced to Veldt Shore
    'BAR51-ruin': [ [1194, 1195], [], [3176], 0],  # was: ruin-baren; End for Baren Falls: door exit to (somewhere)
    'UPNb08-ruin': [ [178, 179], [ ], [ ], [], {"TERRA": [1155]}, 0],  # was: ruin-whelk; Narshe Northern Mines Main Hallway WoB.  Reskin map tileset?
    'NARr01-ruin': [[1143, 1146, 140, 143, 144], [], [], [], {"MOG": ['lw1']}, 1],         # was: ruin-narshe; Narshe WOR, incl. secret passage & entrance to south caves & school.  Key 'lw1' (locked by Mog) unlocks Lone Wolf reward.
    'UPNr04-ruin' : [ [1150], [2010], [3181], [], {'lw1': [2180]}, 1], # was: ruin-narshepeak; Narshe Peak WoR incl. entrance to Umaro's cave.  Lone Wolf reward (2180) locked by lw1 key from ruin-narshe.  3181 is return from ruin-lonewolf.  clone of 'UPNr04a'
    'NARr50-ruin': [[], [2181], [3180], 1],           # was: ruin-lonewolf; Lone Wolf reward room, logical only.  Forced connection from Narshe Peak (41a), return via 2181.
    'ZOZr01-ruin': [ [4600, 4601, 4602, 4604, 5224], [ ], [ ], [], {"TERRA": [4608], "CYAN": ['zr1']}, 1], # was: ruin-zozo; Zozo 1F Outside WOR + Terra-locked 608


    'wob' : [ [i for i in range(45)] + [i for i in range(1501, 1507)], [ ], [3039], 0],  # was: 0; World of Balance
    'wor' : [ [i for i in range(45,80)] + [i for i in range(1507, 1510)], [ ], [3058], 1],  # was: 1; World of Ruin

    'AIRb01' : [ [81], [ ], [ ], 0], # was: 2; Blackjack Outside
    'AIRb02' : [ [82, 83], [ ], [ ], 0], # was: 3; Blackjack Gambling Room
    'AIRb03' : [ [84, 85, 87], [ ], [ ], 0], # was: 4; Blackjack Party Room
    'AIRb04' : [ [86], [ ], [ ], 0], # was: 5; Blackjack Shop Room
    'AIRb05' : [ [88, 89], [ ], [ ], 0], # was: 6; Blackjack Engine Room
    'AIRb06' : [ [90], [ ], [ ], 0], # was: 7; Blackjack Parlor Room
    'AIRr01' : [ [91], [ ], [ ], 1], # was: 8; Falcon Outside
    'AIRr02' : [ [92, 93, 95], [ ], [ ], 1], # was: 9; Falcon Main Room
    'AIRr03' : [ [94], [ ], [ ], 1], # was: 10; Falcon Small Room
    'AIRr04' : [ [96], [ ], [ ], 1], # was: 11; Falcon Engine Room
    'CHOb01' : [ [1129], [ ], [ ], 0], # was: 12; Chocobo Stable Exterior WoB
    'CHOb02' : [ [1131], [ ], [ ], 0], # was: 13; Chocobo Stable Interior
    'CHOr02' : [ [5131], [ ], [ ], 1], # was: 13R; Chocobo Stable Interior
    'CHOr01' : [ [1132], [ ], [ ], 1], # was: 14; Chocobo Stable Exterior WoR

    'NARb01' : [ [97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 108, 112, 1135, 1136], [ ], [ ], 0], # was: 16; Narshe Outside WoB
    'NARb02' : [ [107, 111], [ ], [ ], 0], # was: 17; Narshe Outside Behind Arvis to Mines WoB
    'NARb03' : [ [109, 110], [ ], [ ], 0], # was: 18; Narshe South Caves Secret Passage Outside WoB
    'UPNb01' : [ [113, 114], [ ], [ ], 0], # was: 19; Narshe Northern Mines 2nd/3rd Floor Outside WoB
    'UPNb02' : [ [115, 1139], [ ], [ ], 0], # was: 20; Narshe Northern Mines 3rd Floor Outside WoB
    'NARb04' : [ [1137, 1138], [ ], [ ], 0], # was: 21; Narshe Northern Mines 1st Floor Outside WoB
    'UPNb03' : [ [1140, 1141], [ ], [ ], 0], # was: 22; Snow Battlefield WoB
    'UPNb04' : [ [1142], [ ], [ ], 0], # was: 23; Narshe Peak WoB

    # NARSHE SHARED MAPS
    'NARb05' : [ [116, 117], [ ], [ ], 0], # was: 24; Narshe Weapon Shop
    'NARb06' : [ [118], [ ], [ ], 0], # was: 25; Narshe Weapon Shop Back Room
    'NARb07' : [ [119, 120], [ ], [ ], 0], # was: 26; Narshe Armor Shop
    'NARb08' : [ [121], [ ], [ ], 0], # was: 27; Narshe Item Shop
    'NARb09' : [ [122], [ ], [ ], 0], # was: 28; Narshe Relic Shop
    'NARb10' : [ [123], [ ], [ ], 0], # was: 29; Narshe Inn
    'NARb11' : [ [124, 125], [ ], [ ], 0], # was: 30; Narshe Arvis House
    'NARb12' : [ [126], [ ], [ ], 0], # was: 31; Narshe Elder House
    'NARb13' : [ [127], [ ], [ ], 0], # was: 32; Narshe Cursed Shld House
    'NARb14' : [ [128], [ ], [ ], 0], # was: 33; Narshe Treasure Room
    'NARr05': [[4116, 4117], [], [], 1],  # was: 24R; Narshe Weapon Shop
    'NARr06': [[4118], [], [], 1],  # was: 25R; Narshe Weapon Shop Back Room
    'NARr07': [[4119, 4120], [], [], 1],  # was: 26R; Narshe Armor Shop
    'NARr08': [[4121], [], [], 1],  # was: 27R; Narshe Item Shop
    'NARr09': [[4122], [], [], 1],  # was: 28R; Narshe Relic Shop
    'NARr10': [[4123], [], [], 1],  # was: 29R; Narshe Inn
    'NARr11': [[4124, 4125], [], [], 1],  # was: 30R; Narshe Arvis House
    'NARr12': [[4126], [], [], 1],  # was: 31R; Narshe Elder House
    'NARr13': [[4127], [], [], 1],  # was: 32R; Narshe Cursed Shld House
    'NARr14': [[4128], [], [], 1],  # was: 33R; Narshe Treasure Room

    'NARr01' : [ [129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 140, 144, 1143, 1144], [ ], [ ], 1], # was: 34; Narshe Outside WoR
    'NARr02' : [ [139, 143], [ ], [ ], 1], # was: 35; Narshe Outside Behind Arvis to Mines WoR
    'NARr03' : [ [141, 142], [ ], [ ], 1], # was: 36; Narshe South Caves Secret Passage Outside WoR
    'UPNr01' : [ [145, 146], [ ], [ ], 1], # was: 37; Narshe Northern Mines 2nd/3rd Floor Outside WoR
    'UPNr01a' : [ [145, 146], [ ], [3009], 1], # was: 37a; Narshe Northern Mines 2nd/3rd Floor Outside WoR incl. exit from Umaro's cave
    'UPNr02' : [ [147, 1147], [ ], [ ], 1], # was: 38; Narshe Northern Mines 3rd Floor Outside WoR
    'NARr04' : [ [1145, 1146], [ ], [ ], 1], # was: 39; Narshe Northern Mines 1st Floor Outside WoR
    'UPNr03' : [ [1148, 1149], [ ], [ ], 1], # was: 40; Snow Battlefield WoR
    'UPNr04' : [ [1150], [ ], [ ], 1], # was: 41; Narshe Peak WoR
    'UPNr04a' : [ [1150], [2010], [], 1], # was: 41a; Narshe Peak WoR incl. entrance to Umaro's cave
    'UPNr05' : [ [148, 149], [ ], [ ], 1], # was: 42; Narshe Northern Mines 1F Side/East Room WoR
    'UPNr06' : [ [150, 151], [ ], [ ], 1], # was: 43; Narshe Northern Mines 2F Inside WoR
    'UPNr07' : [ [152, 153], [ ], [ ], 1], # was: 44; Narshe Northern Mines 3F Inside WoR
    'NARr15' : [ [154, 155], [ ], [ ], 1], # was: 45; Narshe South Caves Secret Passage 1F WoR
    'UPNr08' : [ [156, 157, 1151], [ ], [ ], 1], # was: 46; Narshe Northern Mines Main Hallway WoR
    'UPNr09' : [ [158], [ ], [ ], 1], # was: 47; Narshe Northern Mines Tritoch Room WoR
    'NARr19' : [ [159, 160], [ ], [ ], 1], # was: 48; Narshe Moogle Defense Cave WoR
    'NARr18' : [ [161, 162, 164], [ ], [6182], 1], # was: 49; Narshe South Caves WoR.  Door 163 is inaccessible.
    'NARr17' : [ [165, 166], [ ], [ ], 1], # was: 50; Narshe Checkpoint Room WoR
    'NARr16' : [ [167, 168], [ ], [ ], 1], # was: 51; Narshe South Caves Secret Passage 3F WoR

    'UPNb05' : [ [169, 170], [ ], [ ], 0], # was: 53; Narshe Northern Mines Side Room 1F WoB
    'UPNb06' : [ [171, 172], [ ], [ ], 0], # was: 54; Narshe Northern Mines Side Room 2F WoB
    'UPNb07' : [ [173, 174], [ ], [ ], 0], # was: 55; Narshe Northern Mines Inside 3F WoB
    'NARb15' : [ [175, 176], [ ], [ ], 0], # was: 56; Narshe South Caves Secret Passage 1F WoB

    'UPNb08' : [ [178, 179, 1155], [ ], [ ], 0], # was: 59; Narshe Northern Mines Main Hallway WoB
    'UPNb09' : [ [180], [ ], [ ], 0], # was: 60; Narshe Northern Mines Tritoch Room WoB
    'NARr20' : [ [181], [182], [ ], 1], # was: 61; Narshe Moogle Cave WoR.  # 182 acts as a trap door --> rm 49
    'NARb16' : [ [183, 184], [ ], [ ], 0], # was: 62; Narshe South Caves Secret Passage 3F WoB
    'NARb17' : [ [185, 186], [ ], [ ], 0], # was: 63; Narshe Checkpoint Room WoB
    'NARb18' : [ [187, 188, 190], [ ], [6194], 0], # was: 64; Narshe South Caves WoB.  Door 189 is inaccessible.
    'NARb19' : [ [191, 192], [ ], [ ], 0], # was: 65; Narshe Moogle Defense WoB
    'NARb20' : [ [193], [194], [ ], 0], # was: 66; Narshe Moogle Cave WoB

    'SFCr01' : [ [195, 196], [ ], [ ], 1], # was: 67; Cave to South Figaro Siegfried Tunnel

    # FIGARO CASTLE MAIN
    'FIGb01' : [ [197, 1156], [ ], [ ], 0], # was: 68; Figaro Castle Entrance
    'FIGb02' : [ [198, 199, 201, 204], [ ], [ ], 0], # was: 69; Figaro Castle Outside Courtyard
    'FIGb03' : [ [200], [ ], [ ], 0], # was: 70; Figaro Castle Center Tower Outside
    'FIGb04' : [ [202, 205, 207, 208, 1156, 1157, 1158, 1159], [ ], [ ], 0], # was: 71; Figaro Castle Desert Outside
    'FIGb05' : [ [203], [ ], [ ], 0], # was: 72; Figaro Castle West Tower Outside
    'FIGb06' : [ [206], [ ], [ ], 0], # was: 73; Figaro Castle East Tower Outside
    'FIGb07' : [ [209, 210], [ ], [ ], 0], # was: 74; Figaro Castle King's Bedroom
    'FIGb08' : [ [1160], [ ], [ ], 0], # was: 75; Figaro Castle Throne Room
    'FIGb09' : [ [211, 212, 213, 214], [ ], [ ], 0], # was: 76; Figaro Castle Foyer
    'FIGb10' : [ [215, 216, 217, 218, 219, 220], [ ], [ ], 0], # was: 77; Figaro Castle Main Hallway
    'FIGb11' : [ [221, 222, 223], [ ], [ ], 0], # was: 78; Figaro Castle Behind Throne Room
    'FIGb12' : [ [224, 225], [ ], [ ], 0], # was: 79; Figaro Castle East Bedroom
    'FIGb13' : [ [226, 227], [ ], [ ], 0], # was: 80; Figaro Castle Inn
    'FIGb14' : [ [228], [ ], [ ], 0], # was: 81; Figaro Castle West Shop
    'FIGb15' : [ [229], [ ], [ ], 0], # was: 82; Figaro Castle East Shop
    'FIGb16' : [ [230, 231], [ ], [ ], 0], # was: 83; Figaro Castle Below Inn
    'FIGb17' : [ [232, 233], [ ], [ ], 0], # was: 84; Figaro Castle Below Library
    'FIGb18' : [ [234, 235], [ ], [ ], 0], # was: 85; Figaro Castle Library
    'FIGb19' : [ [236, 238], [ ], [ ], 0], # was: 86; Figaro Castle Switch Room
    'FIGb20' : [ [237], [ ], [ ], 0], # was: 87; Figaro Castle Prison
    'FIGr01': [[4197, 5156], [], [], 1],  # was: 68R; Figaro Castle Entrance
    'FIGr02': [[4198, 4199, 4201, 4204], [], [], 1],  # was: 69R; Figaro Castle Outside Courtyard
    'FIGr03': [[4200], [], [], 1],  # was: 70R; Figaro Castle Center Tower Outside
    'FIGr04': [[4202, 4205, 4207, 4208, 5156, 5157, 5158, 5159], [], [], 1],  # was: 71R; Figaro Castle Desert Outside
    'FIGr05': [[4203], [], [], 1],  # was: 72R; Figaro Castle West Tower Outside
    'FIGr06': [[4206], [], [], 1],  # was: 73R; Figaro Castle East Tower Outside
    'FIGr07': [[4209, 4210], [], [], 1],  # was: 74R; Figaro Castle King's Bedroom
    'FIGr08': [[5160], [], [], 1],  # was: 75R; Figaro Castle Throne Room
    'FIGr09': [[4211, 4212, 4213, 4214], [], [], 1],  # was: 76R; Figaro Castle Foyer
    'FIGr10': [[4215, 4216, 4217, 4218, 4219, 4220], [], [], 1],  # was: 77R; Figaro Castle Main Hallway
    'FIGr11': [[4221, 4222, 4223], [], [], 1],  # was: 78R; Figaro Castle Behind Throne Room
    'FIGr12': [[4224, 4225], [], [], 1],  # was: 79R; Figaro Castle East Bedroom
    'FIGr13': [[4226, 4227], [], [], 1],  # was: 80R; Figaro Castle Inn
    'FIGr14' : [ [4228], [ ], [ ], 1], # was: 81R; Figaro Castle West Shop
    'FIGr15' : [ [4229], [ ], [ ], 1], # was: 82R; Figaro Castle East Shop
    'FIGr16': [[4230, 4231], [], [], 1],  # was: 83R; Figaro Castle Below Inn
    'FIGr17': [[4232, 4233], [], [], 1],  # was: 84R; Figaro Castle Below Library
    'FIGr18': [[4234, 4235], [], [], 1],  # was: 85R; Figaro Castle Library
    'FIGr19': [[4236, 4238], [], [], 1],  # was: 86R; Figaro Castle Switch Room
    'FIGr20': [[4237, 1558], [], [], 1],  # was: 87R; Figaro Castle Prison

    # FIGARO CASTLE ENGINE ROOM
    'FIGr21' : [ [239, 240], [ ], [ ], 1], # was: 88; Figaro Castle B1 Hallway East
    'FIGr22' : [ [241, 242], [ ], [ ], 1], # was: 89; Figaro Castle B1 Hallway West
    'FIGr23' : [ [243, 244], [ ], [ ], 1], # was: 90; Figaro Castle B2 Hallway
    'FIGr24' : [ [245, 247], [ ], [ ], 1], # was: 91; Figaro Castle B2 East Hallway
    'FIGr25' : [ [246, 248], [ ], [ ], 1], # was: 92; Figaro Castle B2 West Hallway
    'FIGr26' : [ [249, 250, 251], [ ], [ ], 1], # was: 93; Figaro Castle B2 4 Chest Room
    'FIGr27' : [ [252, 253], [ ], [ ], 1], # was: 94; Figaro Castle Engine Room (arguably has key to unlock Ancient Castle entrance?  If figaro castle was ever randomized internally, would need to add:  ['fc-engine'], {'fc-engine': [1558]})
    'FIGr28' : [ [254], [ ], [ ], 1], # was: 95; Figaro Castle Treasure Room Behind Engine Room
    'FIGr29' : [ [255], [ ], [ ], 1], # was: 96; Figaro Castle B1 Single Chest Room

    # CAVE TO SOUTH FIGARO
    'SFCb-root' : [ [5, 1506], [], [], 0],  # was: root-sfcb; Root map for -door-randomize-south-figaro-cave-wob (to_world_map)
    'SFCb-root-mapsafe' : [ [1513, 268], [], [], 0],  # was: root-sfcb-mapsafe; Root map for -door-randomize-south-figaro-cave-wob (to entry)
    'SFCr02' : [ [256, 257], [ ], [ ], 1], # was: 97; Cave to South Figaro Small Hallway WoR
    'SFCr03' : [ [258, 259, 260], [ ], [ ], 1], # was: 98; Cave to South Figaro Big Room WoR
    'SFCr04' : [ [261, 262], [ ], [ ], 1], # was: 99; Cave to South Figaro South Entrance WoR

    'SFCb05' : [ [263, 264], [ ], [ ], 0], # was: 100; Cave to South Figaro Small Hallway WoB
    'SFCb06' : [ [265, 266, 267], [ ], [ ], 0], # was: 101; Cave to South Figaro Big Room WoB
    'SFCb07' : [ [268, 269], [ ], [ ], 0], # was: 102; Cave to South Figaro South Entrance WoB
    'SFCb08' : [ [270], [ ], [ ], 0], # was: 103; Cave to South Figaro Single Chest Room WoB
    'SFCb09' : [ [271, 272], [ ], [ ], 0], # was: 104; Cave to South Figaro Turtle Room WoB
    'SFCb10' : [ [1161, 1513], [ ], [ ], 0], # was: 105; Cave to South Figaro Outside WoB

    # SOUTH FIGARO
    'SFIr01' : [ [283, 286, 287, 288, 289, 290, 291, 292, 293, 294, 1162, 1163, 1164, 1165, 1166], [ ], [ ], 1], # was: 106; South Figaro Outside WoR
    'SFIr02' : [ [284, 285], [ ], [ ], 1], # was: 107; South Figaro Rich Man's House Side Outside WoR
    'SFIb01' : [ [295, 299, 300, 301, 302, 303, 304, 305, 306, 1167, 1169, 1170, 1171], [ ], [ ], 0], # was: 108; South Figaro Outside WoB
    'SFIb02' : [ [296, 297], [ ], [ ], 0], # was: 109; South Figaro Rich Man's House Side Outside WoB
    'SFIb03' : [ [298, 1168, 1169], [ ], [ ], 0], # was: 110; South Figaro East Side

    'SFIb04': [[307, 308], [], [], 0],  # was: 112; South Figaro Relics
    'SFIb05': [[309, 310], [], [], 0],  # was: 113; South Figaro Inn
    'SFIb06': [[311, 312], [], [], 0],  # was: 114; South Figaro Armory
    'SFIb07': [[313, 314, 316], [], [], 0],  # was: 115; South Figaro Pub
    'SFIb08': [[315], [], [], 0],  # was: 116; South Figaro Pub Basement
    'SFIb09': [[1172], [], [], 0],  # was: 117; South Figaro Chocobo Stable
    'SFIb10': [[317, 318, 319], [], [], 0],  # was: 118; South Figaro Rich Man's House 1F
    'SFIb11': [[320, 321, 324], [], [], 0],  # was: 119; South Figaro Rich Man's House 2F Hallway
    'SFIb12': [[322, 325], [], [], 0],  # was: 120; South Figaro Rich Man's Master Bedroom
    'SFIb13': [[323], [], [], 0],  # was: 121; South Figaro Rich Man's House Kids' Room
    'SFIb14': [[326, 327], [], [], 0],  # was: 122; South Figaro Rich Man's House Bedroom Secret Stairwell
    'SFIb15': [[328, 329, 331, 332, 333], [], [], 0],  # was: 123; South Figaro Rich Man's House B1
    'SFIb16': [[330], [], [], 0],  # was: 124; South Figaro Celes Cell
    'SFIb17': [[334, 335], [], [], 0],  # was: 125; South Figaro Clock Room
    'SFIb18': [[336], [], [], 0],  # was: 126; South Figaro Duncan's House Basement
    'SFIb19': [[337], [], [], 0],  # was: 127; South Figaro Item Shop
    'SFIb20': [[338], [], [], 0],  # was: 128; South Figaro Rich Man's House Secret Back Door Room
    'SFIb21': [[346], [], [], 0],  # was: 129; South Figaro Cider House Secret Room
    'SFIb22': [[339, 344], [], [], 0],  # was: 130; South Figaro Cider House Upstairs
    'SFIb23': [[340, 343, 348], [], [], 0],  # was: 131; South Figaro Cider House Downstairs
    'SFIb24': [[341, 342], [], [], 0],  # was: 132; South Figaro Behind Duncan's House
    'SFIb25': [[345, 347], [], [], 0],  # was: 133; South Figaro Duncan's House Upstairs
    'SFIb26': [[349, 350, 351], [], [], 0],  # was: 134; South Figaro Escape Tunnel
    'SFIb27': [[352], [], [], 0],  # was: 135; South Figaro Rich Man's House Save Point Room
    'SFIb28': [[353], [], [], 0],  # was: 136; South Figaro B2 3 Chest Room
    'SFIb29': [[354], [], [], 0],  # was: 137; South Figaro B2 2 Chest Room
    'SFIr04' : [ [4307, 4308], [ ], [ ], 1], # was: 112R; South Figaro Relics
    'SFIr05' : [ [4309, 4310], [ ], [ ], 1], # was: 113R; South Figaro Inn
    'SFIr06' : [ [4311, 4312], [ ], [ ], 1], # was: 114R; South Figaro Armory
    'SFIr07' : [ [4313, 4314, 4316], [ ], [ ], 1], # was: 115R; South Figaro Pub
    'SFIr08' : [ [4315], [ ], [ ], 1], # was: 116R; South Figaro Pub Basement
    'SFIr09' : [ [5172], [ ], [ ], 1], # was: 117R; South Figaro Chocobo Stable
    'SFIr10' : [ [4317, 4318, 4319], [ ], [ ], 1], # was: 118R; South Figaro Rich Man's House 1F
    'SFIr11' : [ [4320, 4321, 4324], [ ], [ ], 1], # was: 119R; South Figaro Rich Man's House 2F Hallway
    'SFIr12' : [ [4322, 4325], [ ], [ ], 1], # was: 120R; South Figaro Rich Man's Master Bedroom
    'SFIr13' : [ [4323], [ ], [ ], 1], # was: 121R; South Figaro Rich Man's House Kids' Room
    'SFIr14' : [ [4326, 4327], [ ], [ ], 1], # was: 122R; South Figaro Rich Man's House Bedroom Secret Stairwell
    'SFIr15' : [ [4328, 4329, 4331, 4332, 4333], [ ], [ ], 1], # was: 123R; South Figaro Rich Man's House B1
    'SFIr16' : [ [4330], [ ], [ ], 1], # was: 124R; South Figaro Celes Cell
    'SFIr17' : [ [4334, 4335], [ ], [ ], 1], # was: 125R; South Figaro Clock Room
    'SFIr18' : [ [4336], [ ], [ ], 1], # was: 126R; South Figaro Duncan's House Basement
    'SFIr19' : [ [4337], [ ], [ ], 1], # was: 127R; South Figaro Item Shop
    'SFIr20' : [ [4338], [ ], [ ], 1], # was: 128R; South Figaro Rich Man's House Secret Back Door Room
    'SFIr21' : [ [4346], [ ], [ ], 1], # was: 129R; South Figaro Cider House Secret Room
    'SFIr22' : [ [4339, 4344], [ ], [ ], 1], # was: 130R; South Figaro Cider House Upstairs
    'SFIr23' : [ [4340, 4343, 4348], [ ], [ ], 1], # was: 131R; South Figaro Cider House Downstairs
    'SFIr24' : [ [4341, 4342], [ ], [ ], 1], # was: 132R; South Figaro Behind Duncan's House
    'SFIr25' : [ [4345, 4347], [ ], [ ], 1], # was: 133R; South Figaro Duncan's House Upstairs
    'SFIr26' : [ [4349, 4350, 4351], [ ], [ ], 1], # was: 134R; South Figaro Escape Tunnel
    'SFIr27' : [ [4352], [ ], [ ], 1], # was: 135R; South Figaro Rich Man's House Save Point Room
    'SFIr28' : [ [4353], [ ], [ ], 1], # was: 136R; South Figaro B2 3 Chest Room
    'SFIr29' : [ [4354], [ ], [ ], 1], # was: 137R; South Figaro B2 2 Chest Room

    'SFCr11' : [ [355], [ ], [ ], 1], # was: 138; Cave to South Figaro Single Chest Room WoR
    'SFCr12' : [ [356], [ ], [ ], 1], # was: 139; Cave to South Figaro Turtle Room WoR
    'SFCr13' : [ [357], [ ], [ ], 1], # was: 140; Cave to South Figaro Turtle Door WoR

    'SFIb30' : [ [1173], [ ], [ ], 0], # was: 141; South Figaro Docks
    'SFIr30' : [ [5173], [ ], [ ], 1], # was: 141R; South Figaro Docks

    'SFCr14' : [ [358, 359], [ ], [ ], 1], # was: 142; Cave to South Figaro Behind Turtle

    # SABINS HOUSE
    'SAB01' : [ [360, 361, 1174], [ ], [ ], 0], # was: 143; Sabin's House Outside
    'SAB02' : [ [362], [ ], [ ], 0], # was: 144; Sabin's House Inside

    # MT KOLTS
    'MTK-root' : [ [11, 12], [], [], 0],  # was: root-mk; Root room for Mt Kolts
    'MTK-root-mapsafe' : [ [363, 1177], [], [], 0],  # was: root-mk-mapsafe; Root room for Mt Kolts (mapsafe)
    'MTK01' : [ [363, 1175], [ ], [ ], 0], # was: 145; Mt. Kolts South Entrance
    'MTK02' : [ [364, 365, 366], [ ], [ ], 0], # was: 146; Mt. Kolts 1F Outside
    'MTK03' : [ [367], [ ], [ ], 0], # was: 147; Mt Kolts Outside Chest 1 Room
    'MTK04' : [ [368, 1176], [ ], [ ], 0], # was: 148; Mt Kolts Outside Cliff West
    'MTK05' : [ [369], [ ], [ ], 0], # was: 149; Mt Kolts Outside Chest 2 Room
    'MTK06' : [ [370, 371], [ ], [ ], 0], # was: 150; Mt. Kolts Outside Bridge
    'MTK07' : [ [372, 373], [ ], [ ], 0], # was: 151; Mt. Kolts Vargas Spiral
    'MTK08' : [ [374, 375], [ ], [ ], 0], # was: 152; Mt. Kolts First Inside Room
    'MTK09' : [ [376, 377, 378, 385], [ ], [ ], 0], # was: 153; Mt. Kolts 4-Way Split Room
    'MTK10' : [ [379, 380], [ ], [ ], 0], # was: 154; Mt. Kolts 2F Inside Room
    'MTK11' : [ [381, 382], [ ], [ ], 0], # was: 155; Mt. Kolts Inside Bridges Room
    'MTK12' : [ [383, 384], [ ], [ ], 0], # was: 156; Mt. Kolts After Vargas Room
    'MTK13' : [ [386], [ ], [ ], 0], # was: 157; Mt Kolts Inside Chest Room
    'MTK14' : [ [1177, 1178], [ ], [ ], 0], # was: 158; Mt. Kolts North Exit
    'MTK15' : [ [387, 388, 389, 1179], [ ], [ ], 0], # was: 159; Mt. Kolts Back Side
    'MTK16' : [ [390, 391], [ ], [ ], 0], # was: 160; Mt. Kolts Save Point Room

    # NARSHE SCHOOL
    'NARb21' : [ [392, 393, 394, 395], [ ], [ ], 0], # was: 161; Narshe School Main Room
    'NARb22' : [ [396], [ ], [ ], 0], # was: 162; Narshe School Left Room
    'NARb23' : [ [397], [ ], [ ], 0], # was: 163; Narshe School Middle Room
    'NARb24' : [ [398], [ ], [ ], 0], # was: 164; Narshe School Right Room
    'NARr21' : [ [4392, 4393, 4394, 4395], [ ], [ ], 1], # was: 161R; Narshe School Main Room
    'NARr22' : [ [4396], [ ], [ ], 1], # was: 162R; Narshe School Left Room
    'NARr23' : [ [4397], [ ], [ ], 1], # was: 163R; Narshe School Middle Room
    'NARr24' : [ [4398], [ ], [ ], 1], # was: 164R; Narshe School Right Room

    # RETURNERS HIDEOUT
    'RET01' : [ [1180, 1181], [ ], [ ], 0], # was: 165; Returners Hideout Outside
    'RET02' : [ [399, 400, 401, 402, 403], [ ], [ ], 0], # was: 166; Returners Hideout Main Room
    'RET03' : [ [404], [ ], [ ], 0], # was: 167; Returners Hideout Back Room
    'RET04' : [ [405, 406], [ ], [ ], 0], # was: 168; Returners Hideout Banon's Room
    'RET05' : [ [407], [ ], [ ], 0], # was: 169; Returner's Hideout Bedroom
    'RET06' : [ [408], [ ], [ ], 0], # was: 170; Returner's Hideout Inn
    'RET07' : [ [409, 410], [ ], [ ], 0], # was: 171; Returner's Hideout Secret Passage
    'RET08' : [ [1182], [2034], [ ], 0], # was: 172; Lete River Jumpoff

    # LETE RIVER
    'LET01':  [ [ ], [2035], [3034], 0], # was: LeteRiver1; Lete River section 1
    'LET02' :  [ [ ], [2036], [3035], 0], # was: LeteCave1; Lete River cave 1
    'LET03':  [ [ ], [2037], [3036], 0],  # was: LeteRiver2; Lete River section 2
    'LET04' :  [ [ ], [2038], [3037], 0],  # was: LeteCave2; Lete River cave 2
    'LET05':  [ [ ], [2039], [3038], 0],  # was: LeteRiver3; Lete River section 3 + boss

    # GAU'S DAD'S HOUSE
    'GFHb01' : [ [411, 1183], [ ], [ ], 0], # was: 173; Crazy Old Man's House Outside WoB
    'GFHb02' : [ [412], [ ], [ ], 0], # was: 174; Crazy Old Man's House Inside
    'GFHr02' : [ [4412], [ ], [ ], 1], # was: 174R; Crazy Old Man's House Inside

    # IMPERIAL CAMP
    'IMP01': [ [1184], [], [], 0],  # was: 175; Imperial camp WoB, map 0x075

    # DOMA CASTLE
    'DOMb01': [[417, 432], [], [], 0],  # was: 176; Doma 3F Inside
    'DOMb02': [[418, 419, 422, 424, 425, 428, 430, 431, 433], [], [], 0],  # was: 177; Doma Main Room
    'DOMb03': [[420], [], [], 0],  # was: 178; Doma 2F Treasure Room
    'DOMb04': [[421], [], [], 0],  # was: 179; Doma Right Side Bedroom
    'DOMb05': [[423], [], [], 0],  # was: 180; Doma Throne Room
    'DOMb06': [[426], [], [], 0],  # was: 181; Doma Left Side Bedroom
    'DOMb07': [[427, 429], [], [], 0],  # was: 182; Doma Inner Room
    'DOMb08': [[434], [], [], 0],  # was: 183; Doma Cyan's Room
    'DOMr01': [[4417, 4432], [], [], 1],  # was: 176R; Doma 3F Inside
    'DOMr02': [[4418, 4419, 4422, 4424, 4425, 4428, 4430, 4431, 4433], [], [], 1],  # was: 177R; Doma Main Room
    'DOMr03': [[4420], [], [], 1],  # was: 178R; Doma 2F Treasure Room
    'DOMr04': [[4421], [], [], 1],  # was: 179R; Doma Right Side Bedroom
    'DOMr05': [[4423], [], [], 1],  # was: 180R; Doma Throne Room
    'DOMr06': [[4426], [], [], 1],  # was: 181R; Doma Left Side Bedroom
    'DOMr07': [[4427, 4429], [], [], 1],  # was: 182R; Doma Inner Room
    'DOMr08': [[4434], [], [], 1],  # was: 183R; Doma Cyan's Room

    # DUNCAN'S HOUSE
    'DUN01' : [ [458, 457, 1186], [ ], [ ], 1], # was: 194; Duncan's House Outside
    'DUN02' : [ [459], [ ], [ ], 1], # was: 195; Duncan's House
    'DUN01-ruin': [[457, 1186], [], [], 1],  # was: ruin-duncan; Duncan's House Outside (door 458 to interior stays vanilla)

    'GFHr01' : [ [460, 1187], [ ], [ ], 1], # was: 196; Crazy Old Man's House WoR

    # PHANTOM FOREST & TRAIN
    'PHF01' : [ [1188, 461], [], [6466], 0],  # was: 197; Phantom Forest North Room.  Exit 466 also puts you in here!
    'PHF02' : [ [462, 463], [], [], 0], # was: 198; Phantom Forest Healing Pool
    'PHF03' : [ [464, 465], [466], [], 0], # was: 199; Phantom Forest Fork Room.  466 is a normal door behaving as a one-way (!) and 465 goes to world map BUT has an event tile exit....
    'PHF04' : [ [467, 468], [], [], 0],  # was: 200; Phantom Forest Path to Phantom Train (0x087)

    'PHT01' : [ [469], [2065], [ ], 0], # was: 201; Phantom Train Station
    'PHT02' : [ [470, 471, 472, 473, 1528, 1529, 1530, 1531, 1532], [ ], [ ], [], {'pt2': [2068]}, 0], # was: 202; Phantom Train Outside Front Section
    'PHT03a': [[1515, 1516], [], [3065], 0],  # was: 203a; Phantom Train Inside 1st Car
    'PHT03b': [[1523, 1524], [], [3066], 0],  # was: 203b; Phantom Train Inside 2nd Car
    'PHT03c': [[1514], [], [], 0],  # was: 203c; Phantom Train Inside 3rd Car
    'PHT04' : [ [474, 475, 476, 1518], [] , [ ], 0], # was: 204; Phantom Train Outside Car 1 - Caboose
    'PHT04b': [ [1519, 1520], [], [], 0],  # was: 204b; Phantom Train Outside Car 1 - Car 2
    'PHT04c': [ [1521, 1522], [2066, 2067], [], 0],  # was: 204c; Phantom Train Outside Car 2 - Car 3
    'PHT05' : [ [1525], [], [3067], 0],  # was: 205; Phantom Train Outside after jump
    'PHT05b' : [ [1526], [], [], 0],  # was: 205b; Phantom Train Outside after jump & disconnect
    'PHT06' : [ [1533, 1534, 1535, 1536], [], [], 0],  # was: 206; Phantom Train Car 6 Inside (map 0x097)
    'PHT06a' : [ [1537], [], [], 0],  # was: 206a; Phantom Train Car 6 Inside Right Cabin Siegfried Event
    'PHT06b' : [ [1538], [], [], 0],  # was: 206b; Phantom Train Car 6 Inside Left Cabin
    'PHT07' : [ [1539, 1540, 1541, 1542], [], [], 0],  # was: 207; Phantom Train Car 7 Inside (map 0x097 + event_bit 0x17E)
    'PHT07a': [[1543], [], [], 0],  # was: 207a; Phantom Train Car 7 Inside Right Cabin
    'PHT07b': [[1544], [], [], 0],  # was: 207b; Phantom Train Car 7 Inside Left Cabin MIAB room

    'PHT08' : [ [1545], [], [], ['pt2'], {}, 0], # was: 212; Phantom Train Locomotive Interior
    'PHT09' : [ [488], [ ], [ ], 0], # was: 213; Phantom Train Caboose Inner Room

    'PHT10a' : [ [489, 490], [ ], [ ], 0], # was: 215a; Phantom Train Dining Room Left
    'PHT10b' : [ [491, 492], [ ], [ ], 0], # was: 215b; Phantom Train Dining Room Right
    'PHT11' : [ [1527], [ ], [ ], ['pt1'], {'pt1': [493, 494]}, 0], # was: 216; Phantom Train Car 4 with Switch



    'PHT12' : [ [496, 497, 498, 499, 500, 501], [ ], [ ], 0], # was: 220; Phantom Train Caboose
    'PHT13' : [ [502], [ ], [ ], 0], # was: 221; Phantom Train Final Save Point Room


    # MOBLIZ & BAREN FALLS
    'MOBr09' : [ [503], [ ], [ ], 1], # was: 225; Mobliz Kids' Hideaway
    'BAR01' : [ [504, 505], [ ], [ ], 0], # was: 226; Baren Falls Inside
    'BAR02' : [ [1189], [ ], [ ], 0], # was: 227; Baren Falls Cliff
    'MOBb01' : [ [506, 507, 508, 509, 510, 511, 512, 1190, 1191], [ ], [ ], 0], # was: 228; Mobliz Outside WoB
    'MOBr01' : [ [1192, 1193, 514, 515, 513], [ ], [ ], 1], # was: 229; Mobliz Outside WoR

    'MOBb02' : [ [516], [ ], [ ], 0], # was: 231; Mobliz Inn
    'MOBb03' : [ [517, 518], [ ], [ ], 0], # was: 232; Mobliz Arsenal
    'MOBb04' : [ [ ], [ ], [ ], 0], # was: 233; Mobliz Relic Shop
    'MOBb05' : [ [519], [ ], [ ], 0], # was: 234; Mobliz Mail Room Upstairs
    'MOBr05' : [ [4519], [ ], [ ], 1], # was: 234R; Mobliz Mail Room Upstairs
    'MOBb06' : [ [520], [ ], [ ], 0], # was: 235; Mobliz Item Shop
    'MOBb07' : [ [521], [ ], [ ], 0], # was: 236; Mobliz Mail Room Basement WoB
    'MOBr07' : [ [4521, 522], [ ], [ ], 1], # was: 236R; Mobliz Mail Room Basement WoR
    'MOBb08' : [ [ ], [ ], [ ], 0],  # was: 237; Mobliz Injured Lad House WoB
    'MOBr08' : [ [ ], [ ], [ ], 1],  # was: 237R; Mobliz Injured Lad House WoR
    'MOBr10' : [ [ ], [ ], [ ], 1],   # was: 238; Mobliz Injured Lad Hidden Basement

    'BAR03' : [ [1196, 1197], [ ], [ ], 0], # was: 239; Baren Falls Outside

    ### SERPENT TRENCH & NIKEAH SEQUENCE
    'CRE01' : [ [523, 524], [ ], [ ], 0], # was: 240; Crescent Mountain
    'SER01' : [ [1198], [2044], [ ], 0], # was: 241; Serpent Trench Cliff

    # SERPENT TRENCH
    'SER01a' : [ [], [2045, 2046], [3044], 0], # was: 241a; Serpent Trench #1
    'SER02' : [  [], [2047], [3045], 0],  # was: 246; Serpent Trench Cave 1
    'SER01b' : [ [], [2048, 2049], [3046, 3047], 0], # was: 241b; Serpent Trench #2
    'SER03a' : [ [529], [ ], [3048], 0], # was: 247a; Serpent Trench Cave 2 Part A
    'SER03b' : [ [530], [2050], [ ], 0], # was: 247b; Serpent Trench Cave 2 Part B
    'SER03c' : [ [ ], [2051], [3050], 0], # was: 247c; Serpent Trench Cave 2 Part C
    'SER01c' : [ [ ], [2052], [3049, 3051], 0], # was: 241c; Serpent Trench #3
    'NIKb50' : [ [ ], [2053], [3052], 0], # was: 241d; Passthru room for handling ST#3 --> Nikeah transition

    # NIKEAH DOCKS
    'NIKb05': [[1208], [], [3053], 0],  # was: 259; Nikeah Docks
    'NIKr05': [[5208], [], [], 1],  # was: 259R; Nikeah Docks

    # NIKEAH
    'NIKb01' : [ [525, 526, 1199, 1200, 1201, 1202], [ ], [ ], 0], # was: 242; Nikeah Outside WoB
    'NIKb02' : [ [527], [ ], [ ], 0], # was: 243; Nikeah Inn
    'NIKb03' : [ [528], [ ], [ ], 0], # was: 244; Nikeah Pub
    'NIKb04' : [ [1203], [ ], [ ], 0], # was: 245; Nikeah Chocobo Stable
    'NIKr01' : [ [4525, 4526, 5199, 5200, 5201, 5202], [ ], [ ], 1], # was: 242R; Nikeah Outside WoR
    'NIKr02' : [ [4527], [ ], [ ], 1], # was: 243R; Nikeah Inn
    'NIKr03' : [ [4528], [ ], [ ], 1], # was: 244R; Nikeah Pub
    'NIKr04' : [ [5203], [ ], [ ], 1], # was: 245R; Nikeah Chocobo Stable

    # MOUNT ZOZO
    'MTZ-root': [[618], [], [], 1],  # was: root-mz; Mt Zozo connection (Rusty Door)
    'MTZ-root-mapsafe': [[30618], [], [], 1],  # was: root-mz_mapsafe; Mt Zozo connection (Rusty Door)
    'ZOZr53-branch': [[537], [], [], 1],  # was: branch-mz; Zozo branch to Mount Zozo (for use with Zozo-WoR)
    'ZOZr54-branch-mapsafe': [[30537], [], [], 1],  # was: branch-mz_mapsafe; Zozo branch to Mount Zozo (for use with Zozo-WoR)
    'MTZ01' : [ [531, 532, 533], [ ], [ ],  1], # was: 250; Mt Zozo Outside Bridge
    'MTZ02' : [ [534], [ ], [ ], 1], # was: 251; Mt Zozo Outside Single Chest Room
    'MTZ03' : [ [535, 536], [ ], [ ], 1], # was: 252; Mt Zozo Outside Cliff to Cyan's Cave
    'MTZ04' : [ [537, 538, 539], [ ], [ ], 1], # was: 253; Mt Zozo Inside First Room
    'MTZ04-mapsafe' : [ [538, 539], [ ], [ ], 1], # was: 253-mapsafe; Mt Zozo Inside First Room
    'MTZ05' : [ [540, 541], [ ], [ ], 1], # was: 254; Mt Zozo Inside Dragon Room
    'MTZ06' : [ [542, 543], [ ], [ ], 1], # was: 255; Mt Zozo Cyan's Cave
    'MTZ07' : [ [1204], [ ], [ ], 1], # was: 256; Mt Zozo Cyan's Cliff

    #COLISEUM GUY'S HOUSE
    'COLb01' : [ [544, 1205, 1206, 1207], [ ], [ ], 0], # was: 257; Coliseum Guy's House Outside
    'COLb02' : [ [545], [ ], [ ], 0], # was: 258; Coliseum Guy's House Inside

    # KOHLINGEN
    'KOHb01' : [ [546, 547, 548, 549, 550, 551, 1209, 1210], [ ], [ ], 0], # was: 260; Kohlingen Outside WoB
    'KOHr01' : [ [552, 553, 554, 555, 556, 557, 1211, 1212], [ ], [ ], 1], # was: 261; Kohlingen Outside WoR
    'KOHb02' : [ [558], [ ], [ ], 0], # was: 262; Kohlingen Inn Inside
    'KOHb03' : [ [559, 560], [ ], [ ], 0], # was: 263; Kohlingen General Store Inside
    'KOHb04' : [ [561, 563], [ ], [ ], 0], # was: 264; Kohlingen Chemist's House Upstairs
    'KOHb05' : [ [562], [ ], [ ], 0], # was: 265; Kohlingen Chemist's House Downstairs
    'KOHb06' : [ [564], [ ], [ ], 0], # was: 266; Kohlingen Chemist's House Back Room
    'KOHr02' : [ [4558], [ ], [ ], 1], # was: 262R; Kohlingen Inn Inside
    'KOHr03' : [ [4559, 4560], [ ], [ ], 1], # was: 263R; Kohlingen General Store Inside
    'KOHr04' : [ [4561, 4563], [ ], [ ], 1], # was: 264R; Kohlingen Chemist's House Upstairs
    'KOHr05' : [ [4562], [ ], [ ], 1], # was: 265R; Kohlingen Chemist's House Downstairs
    'KOHr06' : [ [4564], [ ], [ ], 1], # was: 266R; Kohlingen Chemist's House Back Room

    'MARb02' : [ [565], [ ], [ ], 0], # was: 267; Maranda Lola's House Inside
    'MARr02' : [ [4565], [ ], [ ], 1], # was: 267R; Maranda Lola's House Inside

    'KOHb07' : [ [566], [ ], [ ], 0], # was: 268; Kohlingen Rachel's House Inside
    'KOHr07' : [[4566], [], [], 1],  # was: 268R; Kohlingen Rachel's House Inside

    # JIDOOR
    'JIDb01' : [ [567, 568, 569, 570, 571, 572, 573, 1213, 1214, 1215, 1216], [ ], [ ], 0], # was: 269; Jidoor Outside
    'JIDb02' : [ [574], [ ], [ ], 0], # was: 270; Jidoor Auction House
    'JIDb03' : [ [575], [ ], [ ], 0], # was: 271; Jidoor Item Shop
    'JIDb04' : [ [576], [ ], [ ], 0], # was: 272; Jidoor Relic
    'JIDb05' : [ [577], [ ], [ ], 0], # was: 273; Jidoor Armor
    'JIDb06' : [ [578], [ ], [ ], 0], # was: 274; Jidoor Weapon
    'JIDb07' : [ [1217], [ ], [ ], 0], # was: 275; Jidoor Chocobo Stable
    'JIDb08' : [ [579], [ ], [ ], 0], # was: 276; Jidoor Inn
    'JIDr01': [[4567, 4568, 4569, 4570, 4571, 4572, 4573, 5213, 5214, 5215, 5216], [], [], 1],  # was: 269R; Jidoor Outside
    'JIDr02': [[4574], [], [], 1],  # was: 270R; Jidoor Auction House
    'JIDr03': [[4575], [], [], 1],  # was: 271R; Jidoor Item Shop
    'JIDr04': [[4576], [], [], 1],  # was: 272R; Jidoor Relic
    'JIDr05': [[4577], [], [], 1],  # was: 273R; Jidoor Armor
    'JIDr06': [[4578], [], [], 1],  # was: 274R; Jidoor Weapon
    'JIDr07': [[5217], [], [], 1],  # was: 275R; Jidoor Chocobo Stable
    'JIDr08': [[4579], [], [], 1],  # was: 276R; Jidoor Inn

    'OWZr01' : [ [580, 581], [ ], [ ], 1], # was: 277; Owzer's Behind Painting Room
    'OWZr02' : [ [582, 583, 585], [ ], [3017], 1], # was: 278; Owzer's Basement 1st Room
    'OWZr03' : [ [584], [ ], [ ], 1], # was: 279; Owzer's Basement Single Chest Room
    'OWZr04' : [ [586, 587], [2017], [ ], 1], # was: 280; Owzer's Basement Switching Door Room.  Removed 2nd trap exit (2018)
    'OWZr05' : [ [588], [2019], [3021], 1], # was: 281; Owzer's Basement Behind Switching Door Room
    'OWZr06' : [ [589], [2021], [3020], 1], # was: 282; Owzer's Basement Save Point Room
    'OWZr07' : [ [ ], [2020], [3019], 1],  # was: 283; Owzer's Basement Floating Chest room
    'OWZr08' : [ [591], [ ], [ ], 1], # was: 284; Owzer's Basement Chadarnook's Room
    'OWZb09' : [ [592], [ ], [ ], 0], # was: 285; Owzer's House
    'OWZr09' : [ [4592, 593], [ ], [ ], 1], # was: 285r; Owzer's House

    # ESPER WORLD
    'ESW01' : [ [1218, 1219, 1220, 1221, 1222, 1223], [ ], [ ], 0], # was: 286; Esper World Outside
    'ESW02' : [ [594], [ ], [ ], 0], # was: 287; Esper World Gate
    'ESW03' : [ [595], [ ], [ ], 0], # was: 288; Esper World Northwest House
    'ESW04' : [ [596], [ ], [ ], 0], # was: 289; Esper World Far East House
    'ESW05' : [ [597], [ ], [ ], 0], # was: 290; Esper World South Right House
    'ESW06' : [ [598], [ ], [ ], 0], # was: 291; Esper World East House
    'ESW07' : [ [599], [ ], [ ], 0], # was: 292; Esper World South Left House

    # ZOZO
    'ZOZb-root': [[600, 601, 602, 604, 608], [], [], 0],  # was: root-zb; Zozo 1F Outside WOB
    'ZOZr-root': [[4600, 4601, 4602, 4604], [], [], ['zr1'], {}, 1],  # was: root-zr; Zozo 1F Outside WOR
    'ZOZb01' : [ [600, 601, 602, 604, 608, 1224], [ ], [ ], 0], # was: 293; Zozo 1F Outside WOB
    'ZOZr01' : [ [4600, 4601, 4602, 4604, 5224], [ ], [ ], ['zr1'], {}, 1], # was: 293r; Zozo 1F Outside WOB
    'ZOZb02' : [ [603], [ ], [ ], 0], # was: 294; Zozo 2F Clock Room Balcony Outside
    'ZOZr02' : [ [4603], [ ], [ ], 1], # was: 294r; Zozo 2F Clock Room Balcony Outside
    'ZOZb03' : [ [605], [ ], [ ], 0], # was: 295; Zozo 2F Cafe Balcony Outside
    'ZOZr03' : [ [4605], [ ], [ ], 1], # was: 295r; Zozo 2F Cafe Balcony Outside
    'ZOZb04' : [ [606, 607], [ ], [ ], 0], # was: 296; Zozo Cafe Upstairs Outside WOB (618 --> Mt Zozo not accessible)
    'ZOZr04' : [ [4606, 4607], [ ], [ ], [], {'zr1': [618]}, 1], # was: 296r; Zozo Cafe Upstairs Outside WOR
    'ZOZr50-mapsafe' : [ [4606, 4607], [ ], [ ], [], {}, 1], # was: 296r-mapsafe; Zozo Cafe Upstairs Outside WOR
    'ZOZb05' : [ [609, 610], [ ], [3032], 0], # was: 297; Zozo Relic 1st Section Outside (incl. hook entry event)
    'ZOZb06' : [ [611, 612, 616], [2032], [ ], 0], # was: 298; Zozo Relic 2nd Section Outside (incl. hook exit)
    'ZOZb07' : [ [613, 617], [ ], [ ], ['clock5'], {}, 0], # was: 299; Zozo Relic 3rd Section Outside
    'ZOZb08' : [ [614, 615, 619], [ ], [ ], 0], # was: 300; Zozo Relic 4th Section Outside
    'ZOZb09' : [ [620, 621, 622], [ ], [ ], ['clock1'], {}, 0], # was: 301; Zozo Cafe WoB
    'ZOZr09' : [ [4620, 4621, 4622], [ ], [ ], ['clock1'], {}, 1], # was: 301r; Zozo Cafe WoR
    'ZOZb10' : [ [623, 624], [ ], [ ], 0], # was: 302; Zozo Relic 1st Room Inside
    'ZOZr10' : [ [4623, 4624], [ ], [ ], 1], # was: 302r; Zozo Relic 1st Room Inside WoR (data only, for ruination mode connection)
    # 303 : [ [625, 626], [ ], [ ], None], #Zozo Relic 2nd Room Inside - Walking guys create a one-way gate
    'ZOZb11a' : [ [625], [2033], [ ], ['clock3'], {},  0], # was: 303a; Zozo Relic 2nd Room Inside - entrance
    'ZOZb11b' : [ [626], [ ], [3033], ['clock3'], {},  0], # was: 303b; Zozo Relic 2nd Room Inside - exit
    'ZOZb12' : [ [627, 628], [ ], [ ], ['clock4'], {},  0], # was: 304; Zozo West Tower Inside
    'ZOZb13' : [ [629], [ ], [ ], 0], # was: 305; Zozo Armor
    'ZOZr13' : [ [4629], [ ], [ ], 1], # was: 305r; Zozo Armor
    'ZOZb14' : [ [630], [ ], [ ], ['clock2'], {}, 0], # was: 306; Zozo Weapon WoB
    'ZOZr14' : [ [4630], [ ], [ ], ['clock2'], {}, 1], # was: 306r; Zozo Weapon WoR
    'ZOZb15-clock' : [ [631], [], [3062], [ ], {('clock1', 'clock2', 'clock3', 'clock4', 'clock5'): [2061]}, 0], # was: 307_clock; Zozo Clock Puzzle Room West WoB INCLUDING clock logic.
    'ZOZb16-clock' : [ [632], [2062], [3061], [ ], {}, 0], # was: 308_clock; Zozo Clock Puzzle Room East WoB INCLUDING clock logic
    'ZOZb15' : [ [631], [], [3062], [ ], {}, 0], # was: 307; Zozo Clock Puzzle Room West WoB, assuming one-way passage  (delete 2061)
    'ZOZb16' : [ [632], [2062], [], [ ], {}, 0], # was: 308; Zozo Clock Puzzle Room East WoB, assuming one-way passage (delete 3061)
    'ZOZr51': [[4631], [], [3064], [], {('clock1', 'clock2', 'clock3', 'clock4', 'clock5'): [2063]}, 1],  # was: 307r_clock; Zozo Clock Puzzle Room West WoR INCLUDING clock logic
    'ZOZr52': [[4632], [2064], [3063], [], {}, 1],  # was: 308r_clock; Zozo Clock Puzzle Room East WoR INCLUDING clock logic
    'ZOZr15': [[4631], [], [3064], [], {}, 1],  # was: 307r; Zozo Clock Puzzle Room West WoR, assuming one-way passage (delete 2063)
    'ZOZr16': [[4632], [2064], [], [], {}, 1],  # was: 308r; Zozo Clock Puzzle Room East WoR, assuming one-way passage (delete 3063)
    #'307a' : [ [631, 632],  [ ], [ ], 0],  #Zozo Clock Puzzle Room (complete)
    #'ZOZr15' : [ [4631, 4632],  [ ], [ ], 1],  #Zozo Clock Puzzle Room (complete)
    'ZOZb17' : [ [633], [ ], [ ], 0], # was: 309; Zozo Cafe Chest Room
    'ZOZr17' : [ [4633], [ ], [ ], 1], # was: 309r; Zozo Cafe Chest Room
    'ZOZb18' : [ [634], [ ], [ ], 0], # was: 310; Zozo Tower 6F Chest Room
    'ZOZb19' : [ [635, 636], [ ], [ ], 0], # was: 311; Zozo Tower Stairwell Room
    'ZOZb20' : [ [637], [ ], [ ], 0], # was: 312; Zozo Tower 12F Chest Room
    # Exits 638, 639, 640, 641 are redundant with 634, 635, 636, 637 (same tiles) and are
    # unused; Maps.door_rando_cleanup() relocates them to (0,0) so they can't shadow them.
    'ZOZb21' : [ [1225], [ ], [ ], 0], # was: 313; Zozo Tower Ramuh's Room

    # OPERA HOUSE - How is this handled?
    'OPEx01' : [ [642, 643, 644, 645], [ ], [ ], None], # was: 314; Opera House Balcony WoR and WoB Disruption
    'OPEx02' : [ [646, 647], [ ], [ ], None], # was: 315; Opera House Catwalk Stairwell
    'OPEx03' : [ [648], [ ], [ ], None], # was: 316; Opera House Switch Room
    'OPEx04' : [ [649, 650], [ ], [ ], None], # was: 317; Opera House Balcony WoB
    'OPEx05' : [ [657], [ ], [ ], None], # was: 318; Opera House Catwalks
    'OPEb06' : [ [658, 659], [ ], [ ], 0], # was: 319; Opera House Lobby WoB
    'OPEr06' : [ [4658, 4659], [ ], [ ], 1], # was: 319r; Opera House Lobby WoR
    'OPEx07' : [ [662], [ ], [ ], None], # was: 320; Opera House Dressing Room

    # VECTOR
    'VEC01-mtek3' : [ [1226], [ ], [ ], 0], # was: 321; Vector After Train Ride
    'VEC01' : [ [1228, 1229], [ ], [ ], 0], # was: 322; Vector Outside
    'VIC01' : [ [670], [ ], [ ], 0], # was: 323; Imperial Castle Entrance

    'VIC02' : [ [671, 672, 673], [ ], [ ], 0], # was: 325; Imperial Castle Roof





    'VIC03' : [ [674, 676, 678, 679, 680, 682, 684, 1230], [ ], [ ], 0], # was: 331; Imperial Castle Main Room
    'VIC04' : [ [675], [ ], [ ], 0], # was: 332; Imperial Castle 2 Chest Room
    'VIC05' : [ [677], [ ], [ ], 0], # was: 333; Imperial Castle Jail Cell
    'VIC06' : [ [681, 688], [ ], [ ], 0], # was: 334; Imperial Castle 2F Bedroom Hallway
    'VIC07' : [ [683, 693], [ ], [ ], 0], # was: 335; Imperial Castle Left Side Roof Stairwell
    'VIC08' : [ [685, 694], [ ], [ ], 0], # was: 336; Imperial Castle Right Side Roof Stairwell

    'VIC09' : [ [689, 690], [ ], [ ], 0], # was: 338; Imperial Castle Bedroom
    'VIC10' : [ [691], [ ], [ ], 0], # was: 339; Imperial Castle Bedroom Bathroom
    'VIC11' : [ [692], [ ], [ ], 0], # was: 340; Imperial Castle Toilet
    'VIC12' : [ [1231], [ ], [ ], 0], # was: 341; Imperial Castle Top Room
    'VIC13' : [ [1233], [ ], [ ], 0], # was: 342; Imperial Castle Banquet Room
    'VIC14' : [ [695, 696], [ ], [ ], 0], # was: 343; Imperial Castle Barracks Room

    # MAGITEK FACTORY
    'MTF01' : [ [702], [2023], [ ], 0], # was: 345; Magitek Factory Upper Room Platform From Lower Room
    'MTF02' : [ [703], [2022], [3023], 0], # was: 346; Magitek Factory Upper Room
    'MTF03' : [ [704], [2024, 2025], [3022, 3024, 3026], 0], # was: 347; Magitek Factory Lower Room

    'MTF04' : [ [705, 706], [2026], [3025], 0], # was: 349; Magitek Factory Garbage Room
    'MTF04-ruin' : [ [705], [2026], [3025], ['mtboss1'], {('mtboss1','CELES'): [706]}, 0], # was: ruin-mtek1; Magitek Factory Garbage Room
    'MTF05' : [ [709, 710], [ ], [ ], 0], # was: 351; Magitek Factory Stairwell
    'MTF06' : [ [711], [ ], [ ], 0], # was: 352; Magitek Factory Save Point Room
    'MTF07' : [ [712, 713], [ ], [ ], 0], # was: 353; Magitek Factory Tube Hallway
    'MTF08' : [ [714, 715], [ ], [ ], 0], # was: 354; Magitek Factory Number 024 Room
    'MTF08-ruin' : [ [714], [ ], [ ], ['mtboss2'], {('mtboss2','CELES'): [715]}, 0], # was: ruin-mtek2; Magitek Factory Number 024 Room.  Try to force doors in a particular order.
    'MTF09' : [ [716], [2027], [ ], 0], # was: 355; Magitek Factory Esper Tube Room
    'MTF10' : [ [], [2028], [3027], 0],  # was: 355a; Magitek Factory Minecart Room

    'ZON-root' : [ [], [2040], [3041], 1], # was: root-ze; ZoneEater Engulf
    'ZON-root-doors': [ [1552, 1553], [], [], 1], # was: root-ze-as-doors; ZoneEater Engulf as doors
    'ZON01' : [ [717], [2041], [3040], 1], # was: 356; Zone Eater Entry Room
    'ZON02' : [ [718, 719, 721], [2042], [ ], 1], # was: 357; Zone Eater Bridge Guards Room
    'ZON03' : [ [ ], [2043], [3042], 1], # was: 358; Zone Eater Pit entry
    'ZON03b' : [ [720], [ ], [3043], 1], # was: 358b; Zone Eater Pit exit
    'ZON04' : [ [725, 726], [ ], [ ], 1], # was: 359; Zone Eater Save Point Room
    'ZON04b': [ [1510, 1511], [ ], [ ], 1], # was: 359b; Zone Eater digestive tract
    'ZON05' : [ [722, 723], [ ], [ ], 1], # was: 361; Zone Eater Short Tunnel
    'ZON06' : [ [727, 728], [ ], [ ], 1], # was: 362; Zone Eater Bridge Switch Room
    'ZON07' : [ [724], [ ], [ ], 1], # was: 363; Zone Eater Gogo Room

    'UMA01' : [ [729, 730, 731], [2001, 2002], [3010], 1], # was: 364; Umaro Cave 1st Room
    'UMA02' : [ [732, 733], [ ], [3001, 3002, 3003, 3056, 3057], 1], # was: 365; Umaro Cave Bridge Room
    'UMA03' : [ [734], [2003, 2004], [ ], 1], # was: 366; Umaro Cave Switch Room
    # 367 : [ [735, 736, 737, 738], [2005, 2006, 2007, 2008], [ ], None], #Umaro Cave 2nd Room
    'UMA04a' : [ [735], [2007], [ ], 1], # was: 367a; Umaro Cave 2nd Room - west
    'UMA04b' : [ [736, 738], [2006, 2008], [ ], 1], # was: 367b; Umaro Cave 2nd Room - middle
    'UMA04c' : [ [737], [2005], [ ], 1], # was: 367c; Umaro Cave 2nd Room - east
    'UMA51-share': [ [], [2056], [3005, 3006], 1], # was: share_east; Umaro Cave west shared pit logical room
    'UMA52-share': [ [], [2057], [3007, 3008], 1], # was: share_west; Umaro Cave west shared pit logical room
    'UMA05' : [ [ ], [2009], [3004], 1], # was: 368; Umaro Cave Umaro's Den

    'MARb01' : [ [739, 740, 741, 742, 1238, 1239], [ ], [ ], 0], # was: 369; Maranda Outside
    'MARr01' : [ [4739, 4740, 4741, 4742, 5238, 5239], [ ], [ ], 1], # was: 369R; Maranda Outside

    'DOMb09' : [ [743], [ ], [ ], 0], # was: 370; Doma 3F Outside
    'DOMb10' : [ [744, 1240], [ ], [ ], 0], # was: 371; Doma 1F Outside
    'DOMb11' : [ [745, 746], [ ], [ ], 0], # was: 372; Doma 2F Outside
    'DOMr09' : [ [4743], [ ], [ ], 1], # was: 370R; Doma 3F Outside
    'DOMr10' : [ [4744, 5240], [ ], [ ], 1], # was: 371R; Doma 1F Outside
    'DOMr11' : [ [4745, 4746], [ ], [ ], 1], # was: 372R; Doma 2F Outside

    # MARANDA
    'MARb03' : [ [750], [ ], [ ], 0], # was: 374; Maranda Inn
    'MARb04' : [ [751], [ ], [ ], 0], # was: 375; Maranda Weapon Shop
    'MARb05' : [ [752], [ ], [ ], 0], # was: 376; Maranda Armor Shop
    'MARr03': [[4750], [], [], 1],  # was: 374R; Maranda Inn
    'MARr04': [[4751], [], [], 1],  # was: 375R; Maranda Weapon Shop
    'MARr05': [[4752], [], [], 1],  # was: 376R; Maranda Armor Shop

    # DARILL's TOMB
    'DAR01' : [ [1241, 1242], [ ], [ ], 1], # was: 377; Darill's Tomb Outside
    'DAR02' : [ [771, 772], [ ], [ ], 1], # was: 378; Darill's Tomb Entry Room
    'DAR03' : [ [773, 774, 776, 778, 780, 783], [ ], [ ], 1], # was: 379; Darill's Tomb Main Upstairs Room
    'DAR04' : [ [775], [ ], [ ], 1], # was: 380; Darill's Tomb Left Side Tombstone Room
    'DAR05' : [ [777, 786], [ ], [ ], 1], # was: 381; Darill's Tomb Right Side Tombstone Room
    'DAR06' : [ [779, 785], [ ], [ ], 1], # was: 382; Darill's Tomb B2 Left Side Bottom Room
    'DAR07' : [ [782], [ ], [ ], [ ], {'dt1': [1512]}, 1], # was: 383; Darill's Tomb B2 Turtle Hallway.  781 is a shared exit.
    'DAR07a' : [ [782], [ ], [ ], [ ], {'dt1': [1512, 781]}, 1], # was: 383a; Darill's Tomb B2 Turtle Hallway.  781 is a shared exit.
    'DAR08' : [ [784], [ ], [ ], 1], # was: 384; Darill's Tomb B2 Right Side Bottom Room
    #385 : [ [787], [ ], [ ], [ ], {}, 1], #Darill's Tomb Right Side Secret Room Duplicate?
    'DAR09' : [ [788], [ ], [ ], 1], # was: 386; Darill's Tomb B2 Graveyard
    'DAR10' : [ [789], [2058], [ ], 1], # was: 387; Darill's Tomb Dullahan Room
    'DAR11' : [ [790, 791], [ ], [ ], 1], # was: 388; Darills' Tomb B3
    'DAR12' : [ [792], [ ], [ ], ['dt2'], {}, 1], # was: 389; Darills' Tomb B3 Switch Puzzle Room
    'DAR13' : [ [793, 794], [2059], [3060], ['dt3'], {}, 1], # was: 390; Darills' Tomb B2 Switch Puzzle Room Left Side
    'DAR14' : [ [], [], [3059], [], {'dt2': [795], 'dt3': [2060]}, 1], # was: 391; Darills' Tomb B2 Switch Puzzle Room Right Side
    'DAR15' : [ [796], [], [], ['dt1'], {}, 1], # was: 392; Darills' Tomb Right Side Secret Room
    'DAR16' : [ [797, 798], [ ], [ ], 1], # was: 393; Darill's Tomb MIAB Hallway


    'TZEr01' : [ [803, 804, 805, 806, 807, 808, 1243], [], [], 1],  # was: 395; Tzen Outside WoR 0x131
    'TZEb01' : [ [809, 810, 811, 812, 813, 1244], [], [], 0],  # was: 396; Tzen Outside WoB 0x132
    #397 : [ [], [], [], 1],  # Tzen Item WoR  0x133
    #398 : [ [], [], [], 1],  # Tzen Inn WoR  0x134
    #399 : [ [], [], [], 1],  # Tzen Weapon Shop WoR  0x135
    #400 : [ [], [], [], 1],  # Tzen Armor Shop WoR  0x136
    'TZEr03' : [ [814, 815], [ ], [ ], 1], # was: 401; Tzen Collapsing House Downstairs  0x137










    # CYAN DREAM STOOGES MAZE:  0x13d
    'DRM01' : [ [], [843, 844], [6845, 6846], 1], # was: 421; Doma Dream 3 Stooges Maze Northwest Section  0x13d
    'DRM02' : [ [], [845], [6844], 1], # was: 422; Doma Dream 3 Stooges Maze West Section
    'DRM03' : [ [], [846], [6847], ['cd1'], {}, 1], # was: 423; Doma Dream 3 Stooges Maze North Section
    'DRM04' : [ [], [847, 848, 849], [6854, 3069], 1], # was: 424; Doma Dream 3 Stooges Maze Middle Section
    'DRM05' : [ [850], [852], [6849, 6843], 1], # was: 425; Doma Dream 3 Stooges Maze Northeast Section
    'DRM06' : [ [851], [], [], 1], # was: 426; Doma Dream 3 Stooges Maze Southeast Section
    'DRM07' : [ [], [853], [6852], ['cd2'], {}, 1], # was: 427; Doma Dream 3 Stooges Maze East Section
    'DRM08' : [ [855], [854], [6848, 6853], 1], # was: 428; Doma Dream 3 Stooges Maze South Section
    'DRM09' : [ [856], [], [], [], {('cd1', 'cd2'): [2070]}, 1], # was: 429; Doma Dream 3 Stooges Room

    # Composite room for isolated Dream Maze (-maze iso): one pit entrance from 421, unlocked trap exit from 429
    'DRM50-ruin' : [ [], [2070], [3069], 1], # was: ruin-stooge-maze; Dream Maze (isolated)

    # CYAN DREAM TRAIN: 0x08f exterior; 0x090 car 2; 0x141 car 3; 0x142 car 1
    'CDA01' : [ [477, 483], [2071], [ ], 1],  # was: 208; Doma Dream Train Outside 3rd Section (front)  0x08f
    'CDA02' : [ [478, 479, 480, 481], [ ], [ ], 1],  # was: 209; Doma Dream Train Outside 2nd Section (mid) 0x08f
    'CDA03' : [ [482], [ ], [3070], 1],  # was: 210; Doma Dream Train Outside 1st Section (rear)        0x08f
    'CDA04' : [ [484, 485, 486, 487], [ ], [ ], 1],  # was: 211; Doma Dream Train 2nd Car ("Lump of metal") 0x090
    'CDA06' : [ [4502], [ ], [ ], 1],  # was: 221R; Doma Dream Train Final Save Point Room
    'CDA07' : [ [867], [ ], [ ], ['cd3'], {'cd3': [865, 866]}, 1],  # was: 435; Doma Dream Train Switch Puzzle Room  0x141
    'CDA08' : [ [868, 869, 870, 871], [ ], [ ], 1],  # was: 436; Doma Dream Train 1st Car   0x142
    'CDA05' : [ [], [2072], [3071], 1], # was: 212R; Doma Dream Train Locomotive Interior

    # CYAN DREAM CAVES: 0x13f exterior, 0x140 interior
    'CDB01': [ [858], [859], [6862], 1],  # was: 430; Doma Dream Caves Outside Loop     0x13f
    'CDB02': [ [860, 861], [2073], [], 1],  # was: 431; Doma Dream Caves Outside Final Room    0x13f
    'CDB03': [ [], [862], [3072], 1],  # was: 432; Doma Dream Caves Starting Room  0x140
    'CDB04': [ [863, 864], [], [6859], 1],  # was: 433; Doma Dream Caves Inside Loop   0x140

    # CYAN DREAM DOMA: 0x7d exterior, 0x7e interior
    'CDC01' : [ [435], [ ], [ ], 1],  # was: 184; Doma Dream 3F Outside
    'CDC02' : [ [436], [ ], [ ], 1],  # was: 185; Doma Dream 1F Outside
    'CDC03' : [ [437, 438], [ ], [ ], 1],  # was: 186; Doma Dream 2F Outside
    'CDC04' : [ [439, 453], [ ], [ ], 1],  # was: 187; Doma Dream 3F Inside
    'CDC05' : [ [440, 441, 445, 449, 451, 452, 454], [ ], [ ], 1],  # was: 188; Doma Dream Main Room
    'CDC06' : [ [443], [], [3073], 1], # was: 188B; Doma Dream Right Bedroom with savepoint
    'CDC07' : [ [442], [ ], [ ], 1],  # was: 189; Doma Dream Treasure Room
    'CDC08' : [ [447], [ ], [ ], 1],  # was: 190; Doma Dream Left Bedroom
    'CDC09' : [ [444, 446, 448, 450], [ ], [ ], 1],  # was: 191; Doma Dream Inner Room
    'CDC10' : [ [455], [ ], [ ], 1],  # was: 192; Doma Dream Cyan's Room
    'CDC11' : [ [456], [2074], [ ], 1],  # was: 193; Doma Dream Throne Room
    'CDC11-ruin' : [ [456], [ ], [ ], [], {'CYAN': [2074]}, 1],  # was: ruin-wrexsoul; Doma Dream Throne Room with Cyan gate on Wrexsoul exit

    # ALBROOK:
    'ALBb01': [ [872, 873, 874, 875, 876, 877, 1245, 1246, 1247, 1248], [], [], 0],   # was: 437; Albrook WoB, outside (0x143)
    'ALBr01': [ [878, 879, 880, 881, 882, 883, 1249, 1250, 1251, 1252], [], [], 1],   # was: 438; Albrook WoR, outside (0x144)
    'ALBb02': [ [1548], [], [], 0],   # was: 439; Albrook Inn WoB (0x145)
    'ALBr02': [ [5548], [], [], 1],   # was: 439R; Albrook Inn WoR (shared map 0x145)
    'ALBb03': [ [1549], [], [], 0],   # was: 440; Albrook Weapon Shop WoB (0x146)
    'ALBr03': [ [5549], [], [], 1],   # was: 440R; Albrook Weapon Shop WoR (shared map 0x146)
    'ALBb04': [ [1550], [], [], 0],   # was: 441; Albrook Armor Shop WoB (0x147)
    'ALBr04': [ [5550], [], [], 1],   # was: 441R; Albrook Armor Shop WoR (shared map 0x147)
    'ALBb05': [ [1551], [], [], 0],   # was: 442; Albrook Item Shop WoB (0x148)
    'ALBr05': [ [5551], [], [], 1],   # was: 442R; Albrook Item Shop WoR (shared map 0x148)



    # THAMASA - does WC only use this one Thamasa map (0x154)?
    'THAb01' : [ [922, 923, 924, 925, 926, 927, 928, 1253, 1254, 1255], [ ], [ ], 0], # was: 447; Thamasa After Kefka Outside WoB
    'THAb02' : [ [950, 951], [ ], [ ], 0], # was: 450; Thamasa Arsenal
    'THAb03' : [ [952], [2054], [3055], 0], # was: 451; Thamasa Inn
    'THAb04' : [ [953], [ ], [ ], 0], # was: 452; Thamasa Item Shop
    'THAb05' : [ [954], [ ], [ ], 0], # was: 453; Thamasa Elder's House
    'THAb06' : [ [955, 956], [ ], [ ], 0], # was: 454; Strago's House First Floor
    'THAb07' : [ [957], [ ], [ ], 0], # was: 455; Strago's House Second Floor
    'THAb08' : [ [958], [ ], [ ], 0], # was: 456; Thamasa Relic

    'THAr01' : [ [943, 944, 945, 946, 947, 948, 949, 1261, 1259, 1260], [], [], 1],  # was: 449; Thamasa WoR outside (0x158)
    #'447R': [[4922, 4923, 4924, 4925, 4926, 4927, 4928], [], [], 1],  # Thamasa After Kefka Outside WoR
    'THAr02': [[4950, 4951], [], [], 1],  # was: 450R; Thamasa Arsenal
    'THAr03': [[4952], [], [], 1],  # was: 451R; Thamasa Inn
    'THAr04': [[4953], [], [], 1],  # was: 452R; Thamasa Item Shop
    'THAr05': [[4954], [], [], 1],  # was: 453R; Thamasa Elder's House
    'THAr06': [[4955, 4956], [], [], 1],  # was: 454R; Strago's House First Floor
    'THAr07': [[4957], [], [], 1],  # was: 455R; Strago's House Second Floor
    'THAr08': [[4958], [], [], 1],  # was: 456R; Thamasa Relic

    # Burning House - event in, event out
    'BUR01' : [ [959], [ ], [3054], 0], # was: 457; Burning House Entry Room
    'BUR02' : [ [960, 961, 962], [ ], [ ], 0], # was: 458; Burning House Second Room
    'BUR03' : [ [963, 964], [ ], [ ], 0], # was: 459; Burning House Third Room
    'BUR04' : [ [965, 966, 968], [ ], [ ], 0], # was: 460; Burning House Fourth Room
    'BUR05' : [ [967, 970, 972], [ ], [ ], 0], # was: 461; Burning House Fifth Room
    'BUR06' : [ [969], [ ], [ ], 0], # was: 462; Burning House 1st Chest Room
    'BUR07' : [ [971], [ ], [ ], 0], # was: 463; Burning House 2nd Chest Room
    'BUR08' : [ [973, 974], [ ], [ ], 0], # was: 464; Burning House Sixth Room
    'BUR09-ruin' : [ [975], [ ], [ ], [ ], {'STRAGO': [2055]}, 0], # was: ruin-bh; Burning House Final Room
    'BUR09' : [ [975], [2055], [ ], 0], # was: 465; Burning House Final Room

    # CAVE ON THE VELDT
    'COV-root' : [ [61], [], [3075], 1], # was: root-vc; Root room for Cave on the Veldt
    'COV-root-mapsafe' : [ [979, 985], [], [3075], 1], # was: root-vc-mapsafe; Root room for Cave on the Veldt
    'COV01' : [ [978, 979, 985], [ ], [ ], 1], # was: 467; Veldt Cave First Room
    'COV02' : [ [980], [ ], [ ], 1], # was: 468; Veldt Cave Second Room Dead End
    'COV03' : [ [981, 986], [ ], [ ], 1], # was: 469; Veldt Cave Bandit Room / Second Room
    'COV04' : [ [982, 983], [ ], [ ], 1], # was: 470; Veldt Cave Third Room
    'COV05' : [ [984, 987], [ ], [ ], 1], # was: 471; Veldt Cave Bandit Room / Second Room Lower Floor
    'COV06' : [ [988], [ ], [ ], ['vc1'], {'vc1': [989]}, 1], # was: 472; Veldt Cave Fourth Room Left Side
    #473 : [ [], [ ], [ ], 1], #Veldt Cave Fourth Room Right Side
    'COV07' : [ [990, 992], [ ], [ ], 1], # was: 474; Veldt Cave Fifth Room
    'COV08-ruin' : [ [991], [ ], [ ], [ ], {'SHADOW': [2075]}, 1], # was: ruin-cotv; Veldt Cave Final Room
    'COV08' : [ [991], [2075], [ ], 1], # was: 475; Veldt Cave Final Room

    # FANATIC'S TOWER
    'FAN01' : [ [1010, 1011, 1012], [ ], [ ], 1], # was: 476; Fanatic's Tower 2nd Floor Outside
    'FAN02' : [ [1013, 1014, 1015], [ ], [ ], 1], # was: 477; Fanatic's Tower 3rd Floor Outside
    'FAN03' : [ [1016, 1017, 1018], [ ], [ ], 1], # was: 478; Fanatic's Tower 4th Floor Outside
    'FAN04' : [ [1262, 1019], [ ], [ ], 1], # was: 479; Fanatic's Tower Bottom
    'FAN05' : [ [1020, 1021, 1022, 1023], [ ], [ ], 1], # was: 480; Fanatic's Tower 1st Floor Outside
    'FAN06' : [ [1024, 1025], [ ], [ ], 1], # was: 481; Fanatic's Tower Top
    'FAN07' : [ [1026], [ ], [ ], 1], # was: 482; Fanatic's Tower 1st Floor Treasure Room
    'FAN08' : [ [1027], [ ], [ ], 1], # was: 483; Fanatic's Tower Top Room
    'FAN09' : [ [1028], [ ], [ ], 1], # was: 484; Fanatic's Tower 2nd Floor Treasure Room
    'FAN10' : [ [1029], [ ], [ ], 1], # was: 485; Fanatic's Tower 3rd Floor Treasure Room
    'FAN11' : [ [1030], [ ], [ ], 1], # was: 486; Fanatic's Tower 4th Floor Treasure Room
    'FAN12' : [ [1031], [ ], [ ], 1], # was: 487; Fanatic's Tower 1st Floor Secret Room

    # ESPER MOUNTAIN
    'ESM-root' : [ [44], [], [], 0], # was: root-em; Root map for -door-randomize-esper-mountain
    'ESM-root-mapsafe' : [ [1046, 1048, 1049], [], [], 0], # was: root-em_mapsafe; Root map for -door-randomize-esper-mountain
    'ESM-root-mapsafe-each' : [ [30044], [], [], 0], # was: root-em_mapsafe_each; Root map for -door-randomize-esper-mountain & map shuffle.  would need to have map shuffle use 31047 instead of 1047...
    'ESM01' : [ [1032, 1033], [ ], [ ], 0], # was: 488; Esper Mountain 3 Statues Room
    'ESM02' : [ [1034, 1035, 1036], [ ], [ ], 0], # was: 489; Esper Mountain Outside Bridge Room
    'ESM03' : [ [1037], [ ], [ ], 0], # was: 490; Esper Mountain Outside East Treasure Room
    'ESM04' : [ [1038, 1039, 1040, 1041], [ ], [ ], 0], # was: 491; Esper Mountain Outside Path to Final Room
    'ESM05' : [ [1042, 1043], [ ], [ ], 0], # was: 492; Esper Mountain Outside Statue Path
    'ESM06' : [ [1044], [ ], [ ], 0], # was: 493; Esper Mountain Outside West Treasure Room
    'ESM07' : [ [1045], [ ], [ ], 0], # was: 494; Esper Mountain Outside Northwest Treasure Room
    'ESM08' : [ [1046, 1047, 1048, 1049], [ ], [ ], 0], # was: 495; Esper Mountain Inside First Room
    'ESM09' : [ [1050, 1051], [ ], [3011, 3012, 3013], 0], # was: 496; Esper Mountain Inside Second Room South Section (with bridge jump entrances)
    'ESM10' : [ [1052], [2014, 2015, 2016], [ ], 0], # was: 497; Esper Mountain Falling Pit Room
    'ESM11' : [ [1053, 1054], [2011], [3015], 0], # was: 498; Esper Mountain Inside Second Room West Section
    'ESM12' : [ [1055], [2013], [3016], 0], # was: 499; Esper Mountain Inside Second Room East Section
    'ESM13' : [ [1056], [2012], [3014], 0], # was: 500; Esper Mountain Inside Second Room North Section
    'ESM14' : [ [1057], [ ], [ ], 0], # was: 501; Esper Mountain Inside Second Room Dead End

    # IMPERIAL BASE & CAVE TO THE SEALED GATE
    'SEA01' : [ [1059, 1060, 1058, 1263], [ ], [ ], 0], # was: 502; Imperial Base
    'SEA-root': [[1058, 1263], [], [], 0],  # was: root-sg; Root entrance = imperial base
    'SEA02' : [ [1061, 1062], [ ], [ ], 0], # was: 503; Imperial Base House
    'SEA03' : [ [1063], [ ], [ ], 0], # was: 504; Imperial Base House Basement
    'SEA03a' : [ [41, 43], [], [], 0],  # was: 504a; WOB Imperial Base / Cave to Sealed Gate connector
    'SEA04' : [ [1064, 1065], [ ], [3031], 0], # was: 505; Cave to Sealed Gate Entry Room
    'SEA05' : [ [1066, 1067], [ ], [ ], 0], # was: 506; Cave to Sealed Gate B1
    'SEA06' : [ [1069, 1264], [2031], [ ], 0], # was: 507; Cave to Sealed Gate Last Room
    'SEA07' : [ [1070], [ ], [3030], 0], # was: 508; Cave to Sealed Gate Main Room Last Section
    'SEA08' : [ [1071, 1072], [2029], [ ], 0], # was: 509; Cave to Sealed Gate Main Room First Section
    'SEA09' : [ [1073], [2030], [3029], 0], # was: 510; Cave to Sealed Gate Main Room Middle Section
    'SEA10' : [ [1074], [ ], [ ], 0], # was: 511; Cave to Sealed Gate 4 Chest Room
    'SEA11' : [ [1075, 1076, 1077], [ ], [ ], 0], # was: 512; Cave to Sealed Gate Lava Switch Room  # 1076 inaccessible?
    'SEA12' : [ [1078], [ ], [ ], 0], # was: 513; Cave to Sealed Gate Save Point Room
    'SEA13' : [ [1079], [ ], [ ], 0], # was: 514; Sealed Gate

    # CID'S HOUSE
    'CID01' : [ [1080, 1265, 1266, 1267, 1268, 1269, 1270], [ ], [ ], 1], # was: 515; Solitary Island House Outside
    'CID02' : [ [1081], [ ], [ ], 1], # was: 516; Solitary Island House Inside
    'CID03' : [ [1271], [ ], [ ], 1], # was: 517; Solitary Island Beach

    # ANCIENT CAVE & CASTLE
    'ANC-root': [ [1558], [], [], 1],  # was: root-ac; Ancient Cave connection from Figaro Castle Basement
    'ANC01' : [ [1082, 1083, 1085, 1087], [ ], [ ], 1], # was: 520; Ancient Cave First Room
    'ANC02' : [ [1084, 1086, 1088, 1274], [ ], [ ], 1], # was: 521; Ancient Cave Second Room
    'ANC03' : [ [1089, 1275], [ ], [ ], 1], # was: 522; Ancient Cave Third Room
    'ANC04' : [ [1090, 1091], [ ], [ ], 1], # was: 523; Ancient Cave Save Point Room
    'ANC05' : [ [1092, 1093], [ ], [ ], 1], # was: 524; Ancient Castle West Side South Room
    'ANC06' : [ [1094], [ ], [ ], 1], # was: 525; Ancient Castle East Side Single Chest Room
    'ANC07' : [ [1095], [ ], [ ], 1], # was: 526; Ancient Castle West Side North Room
    'ANC08' : [ [1096], [ ], [ ], 1], # was: 527; Ancient Castle East Side 2 Chest Room
    'ANC09' : [ [1098, 1099, 1100, 1278], [ ], [ ], ['ac2'], {}, 1], # was: 528; Ancient Castle Throne Room
    'ANC10' : [ [1276, 1277], [ ], [ ], 1], # was: 529; Ancient Castle Entry Room
    'ANC11' : [ [1101, 1102, 1103, 1104, 1279], [ ], [ ], 1], # was: 530; Ancient Castle Outside
    'ANC12' : [ [1105], [ ], [ ], [], {'ac2': [1106]}, 1], # was: 531; Ancient Castle Eastern Basement
    'ANC13' : [ [1107], [ ], [ ], 1], # was: 532; Ancient Castle Dragon Room

    # COLISEUM
    'COLr03' : [ [1125, 1126, 1280], [ ], [ ], 1], # was: 533; Coliseum Main Room
    'COLr04' : [ [1127], [ ], [ ], 1], # was: 534; Coliseum Left Room

    # EBOT'S ROCK
    'EBO01' : [ [1546], [], [], 1],  # was: 535; Ebot's Rock entrance, 0x195

    # PHOENIX CAVE
    'PHO-root' : [ [1554], [], [], 1],  # was: root-pc; Phoenix cave entry as door
    'PHO52-branch' : [ [1555], [], [], 1],   # was: branch-pc; Phoenix cave outside (with exit as door) treated as dead end
    'PHO01' : [ [1555, 857], [], [], 1],   # was: 536; Phoenix cave outside (with exit as door)
    'PHO02' : [ [828], [], [], 1],   # was: 537; Phoenix cave interior entrance


    # FLOATING CONTINENT
    'FLO-root': [[1556], [], [], 0],  # was: root-fc-as-doors; Floating Continent entry as door
    'FIGb50-branch': [[1557], [], [], 0],  # was: branch-fc; Floating Continent outside at entry

    # KEFKA'S TOWER: We are breaking naming scheme here because from a map numbering perspective these should go earlier
    # need to figure out how to handle connection to ruination code
    # KT outside: map_id = 0x14F
    # LEFT LANE
    'KTA1': [ [887], [], [], [], {}, 1],  # was: KTa1; 0x14E, Kefka's Tower, left side, entry room (How to integrate with ruination mode entry?)
    'KTA2': [ [799, 800], [], [], [], {}, 1],  # was: KTa2; 0x12F,  KT left side, conveyor belts room
    'KTA3': [ [801, 802], [], [], [], {}, 1],  # was: KTa3; 0x130,  KT left side, third room (horseshoe with chest)
    'KTA4': [ [888, 889], [], [], [], {}, 1],  # was: KTa4; 0x14E, KT left side, fourth room (outside connector)
    'KTA5a': [ [760], [], [], [], {'KT1': [1565]}, 1],  # was: KTa5a; 0x124, KT left side, fifth room entry (switch platform left)
    'KTA5b': [ [761], [], [], [], {'KT1': [1566]}, 1],  # was: KTa5b; 0x124, KT left side, fifth room exit
    'KTA6': [ [976, 977], [], [], [], {}, 1],  # was: KTa6; 0x160, KT left side, sixth room (broken tubes)
    'KTA7': [ [769, 768], [], [], [], {}, 1],  # was: KTa7; 0x127, KT left side, seventh room (after-tubes connector)
    'KTA8a': [ [890], [], [], [], {'KT2': [1567]}, 1],  # was: KTa8a; 0x14E, KT left side, eighth room (outside before broken stairs)
    'KTA8b': [ [894], [], [], [], {'KT2': [1568]}, 1],  # was: KTa8b; 0x14E, KT left side, eighth room (outside after broken stairs)
    'KTA-final': [ [904], [], [], [], {}, 1],  # was: KTa-final; 0x151, KT left side, ninth room (4-ton switch room middle)

    # MIDDLE LANE
    'KTB1': [  [895], [], [], [], {}, 1],  # was: KTb1; 0x14E, Kefka's Tower, middle, entry room
    'KTB2': [  [913, 914, 915], [], [], [], {}, 1],  # was: KTb2; 0x152, Kefka's Tower, middle, second room (fork)
    'KTB3': [  [916], [], [7108], [], {}, 1],  # was: KTb3; 0x152, Kefka's Tower, middle, third room (treasure & pipe return.  7108 = pit landing of door-as-trap 1108 from KTb6; actual door 917 is never used.)
    'KTB4': [  [886], [2080], [], [], {}, 1],  # was: KTb4; 0x14B, Kefka's Tower, middle, fourth room (toilet atma)
    'KTB5': [  [885], [], [3080], [], {}, 1],  # was: KTb5; 0x149, Kefka's Tower, middle, fifth room (drop + stairs. 884 is a door from which you fall, inaccessible)
    'KTB6': [  [1110, 1109], [1108], [], [], {}, 1],  # was: KTb6; 0x199, Kefka's Tower, middle, sixth room (two pipes out; 'fall' event is on destination map for 1108)
    'KTB7': [  [896, 893, 891], [], [], [], {}, 1],  # was: KTb7; 0x14E, Kefka's Tower, middle, 7th room (outside, conveyors, fork)
    'KTB8': [  [759], [], [], ['KT1'], {}, 1],  # was: KTb8; 0x124, Kefka's Tower, middle, 8th room (switch platform right side with button)
    'KTB9': [  [766, 767], [], [], [], {}, 1],  # was: KTb9; 0x126, Kefka's Tower, middle, 9th room (hallway to gold drgn)
    'KTB10': [  [902, 903], [], [], [], {}, 1],  # was: KTb10; 0x14F, Kefka's Tower, middle, 10th room (gold drgn room)
    'KTB11': [  [994, 993], [], [], [], {}, 1],  # was: KTb11; 0x162, Kefka's Tower, middle, 11th room (post-drgn connector)
    'KTB-final': [  [911], [], [], [], {}, 1],  # was: KTb-final; 0x151, Kefka's Tower, middle, 12th room (4-ton switch room left)

    # RIGHT LANE
    'KTC1': [  [898, 899], [], [], [], {}, 1],  # was: KTc1; 0x14E, Kefka's Tower, right, entry room
    'KTC2': [  [918, 919], [], [], [], {}, 1],  # was: KTc2; 0x153, Kefka's Tower, right, second room (hallway to inferno balcony)
    'KTC3': [  [770], [], [], [], {}, 1],  # was: KTc3; 0x128, Kefka's Tower, right, third room (inferno balcony)
    'KTC4': [  [920, 921], [], [], [], {}, 1],  # was: KTc4; 0x153, Kefka's Tower, right, fourth room (connector to conveyor basement)
    'KTC5': [  [1120], [2081], [3084], [], {}, 1],  # was: KTc5; 0x19A, Kefka's Tower, right, fifth room (Aegis basement)
    'KTC6': [  [], [2082], [3081], [], {}, 1],  # was: KTc6; 0x19A, Kefka's Tower, right, sixth room (conveyor belt ride)
    'KTC7': [  [1111], [2083], [3082], [], {}, 1],  # was: KTc7; 0x19A, Kefka's Tower, right, seventh room (Inferno room)
    'KTC8': [  [], [2084], [3083], [], {}, 1],  # was: KTc8; 0x19A, Kefka's Tower, right, eighth room (conveyor belt return ride)
    'KTC9': [  [763, 762], [], [], [], {}, 1],  # was: KTc9; 0x125, Kefka's Tower, right, ninth room (post-Inferno hallway)
    'KTC10': [  [897, 892], [], [], ['KT2'], {}, 1],  # was: KTc10; 0x14e, Kefka's Tower, right, tenth room (outside with red switch box)
    'KTC11': [  [764, 765], [], [], [], {}, 1],  # was: KTc11; 0x125, Kefka's Tower, right, eleventh room (hallway to skull drgn)
    'KTC12': [  [998, 999], [], [], [], {}, 1],  # was: KTc12; 0x162, Kefka's Tower, right, twelfth room (skull drgn room)
    'KTC13': [  [996, 995], [], [], [], {}, 1],  # was: KTc13; 0x162, Kefka's Tower, right, thirteenth room (connector post-skull drgn)
    'KTC-final': [  [912], [], [], [], {}, 1],  # was: KTc-final; 0x151, Kefka's Tower, middle, last room (4-ton switch room right)

}

ruination_dont_force = [
    1079,    # Cave to the Sealed Gate, now movable.  Quick exit always open?

]

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
    2153: [3153],    # ST reward --> nikeah, trickery

    2055: [3055],    # Burning House defeating boss --> Thamasa Inn.  This *could* be randomized.
    2085: [3085],    # Ebot's Rock character reward --> Thamasa.  Trap injected onto ms-wor-78 only when its reward is a character (see ruination.process_rewards).

    2059: [3059],    # Daryl's Tomb, Turtle #2 left to right
    2060: [3060],    # Daryl's Tomb, Turtle #2 right to left

    2067: [3067],    # Phantom train roof jump event

    2076: [3076],   # Baren Falls --> Veldt (for now)
    2176: [3176],   # Baren Falls --> Veldt, trickery (reward logic)

    2097: [3097],   # KT left, trickery
    2098: [3098],   # KT mid, trickery
    2099: [3099],   # KT right, trickery
    2128: [3128],   # MTek 3 ending back to vector, trickery.

    2180: [3180],   # Narshe Peak (ruin-narshepeak) --> Lone Wolf reward room (ruin-lonewolf), logical only.
    2181: [3181],   # Lone Wolf reward room (ruin-lonewolf) --> Narshe Peak (ruin-narshepeak), return.

    4418: [744],    # Doma WOR Main Room --> Doma WoB Outside (ruination: splits indoor WoR from outdoor WoB for siege).  If Doma interior were ever randomized, this would cause problems.

    1565: [1566],   # Kefka's Tower switch platform room
    1567: [1568],   # Kefka's Tower, broken stairs
}

# Add forced connections for virtual doors (-dra)
#if 'root' in room_data.keys():
#    for i in range(8000, 8000+len(room_data['root'][0])):
#        forced_connections[i] = [i+1000]

# List of one-ways that must have the same destination
shared_oneways = {
    # These are better handled with a logical room:  'UMA51-share' = [ [], ['2005L'], [3005, 3006], 1] and
    # and forced connections:  2005: [3005], 2006: [3006]
    #2005: [2006],  # Umaro's cave room 2: east trapdoor (shared exit)
    #2006: [2005],  # Umaro's cave room 2: east trapdoor (shared exit)
    # These are better handled with a logical room:  'UMA52-share' = [ [], ['2007L'], [3007, 3008], 1]
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
    5156: [5157, 5158, 5159],     # Figaro Castle exits to world map (WoR)
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
    1246: [1247],         # Albrook WoB north to world map
    1249: [1250, 1251],   # Albrook WoR to world map
    1250: [1251],         # Albrook WoR north to world map

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

    1245: [1246, 1247],    # Albrook WoB to world map
    1249: [1250, 1251],    # Albrook WoR to world map

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
    these_doors = [d for d in room_data[r][0]] + [d for d in locked if d < 2000 or 4000 <= d < 6000]
    for d in these_doors:
        exit_world[d] = room_data[r][-1]
        exit_room[d] = r
        #if d in shared_oneways.keys():
        #    for ds in shared_oneways[d]:
        #        exit_world[ds] = room_data[r][-1]
        #        exit_room[d]

    # Read in one-way world.  Note that technically some doors behave as traps, and this won't catch them if they are also locked.  This scenario may not exist yet but is logically possible.
    these_traps = [t for t in room_data[r][1]] + [t for t in locked if 2000 <= t < 3000]
    for t in these_traps:
        exit_world[t] = room_data[r][-1]
        exit_room[t] = r

    # Read in one-way exits
    these_pits = [p for p in room_data[r][2]] + [p for p in locked if 3000 <= p < 4000 or 6000 < p]
    for p in these_pits:
        exit_world[p] = room_data[r][-1]
        exit_room[p] = r

# Generate a list of doors that act as trapdoors (trap bucket, id < 2000).
# Each must have a 6000+id landing pit somewhere; tools/compile_atlas.py
# --check validates the pairing.
doors_as_traps = []
for r in room_data.keys():
    for t in room_data[r][1]:
        if isinstance(t, int) and t < 2000:
            doors_as_traps.append(t)


# ---------------------------------------------------------------------------
# Reset boundary for the shared mutable tables.
#
# The per-mode table setup (apply_mode_table_adjustments in data/doors.py,
# run by Doors.__init__) mutates the tables in this module: it splits
# dungeon-crawl/ruination town exits out of shared_exits, pops the -ruin
# forced connection, and edits shuffle-room door lists when map shuffle and
# door randomization combine. That is fine for a single build, but a second
# build in the same process (retries, tests, a reroll server) would start
# from corrupted tables. Doors.__init__ calls reset_room_tables() first so
# that every build starts from the pristine import-time state. The reset
# preserves the dict object identities (clear + update), so existing
# `from data.rooms import room_data`-style references stay valid.
#
# exit_room / exit_world / doors_as_traps are derived once above and are not
# mutated at run time, so they do not need to be re-derived here.
import copy as _copy

_ROOM_DATA_PRISTINE = _copy.deepcopy(room_data)
_FORCED_CONNECTIONS_PRISTINE = _copy.deepcopy(forced_connections)
_SHARED_EXITS_PRISTINE = _copy.deepcopy(shared_exits)


def reset_room_tables():
    """Restore room_data, forced_connections and shared_exits to their
    pristine import-time contents (fresh copies, same dict objects)."""
    room_data.clear()
    room_data.update(_copy.deepcopy(_ROOM_DATA_PRISTINE))
    forced_connections.clear()
    forced_connections.update(_copy.deepcopy(_FORCED_CONNECTIONS_PRISTINE))
    shared_exits.clear()
    shared_exits.update(_copy.deepcopy(_SHARED_EXITS_PRISTINE))
