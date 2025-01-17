# event exit information:  Event_ID:  [original address, event bit length, split point, transition state, description, location]
#   transition state = [is_chararacter_hidden, is_song_override_on, is_screen_hold_on, is_on_raft, update_parent_map]
#   location = [map_id, x, y]
#   None = not implemented
event_exit_info = {
    # UMARO'S CAVE
    2001: [0xcd8d4, 34, 24, [True, True, False, False, False], 'Umaro Cave 1st Room trapdoor top', [281, 11, 53], 'JMP'],
    2002: [0xcd8b2, 34, 24, [True, True, False, False, False], 'Umaro Cave 1st Room trapdoor left', [281, 10, 54], 'JMP'],
    2003: [0xcd93a, 45, 35, [True, True, False, False, False], 'Umaro Cave Switch Room trapdoor to 2nd Room', [281, 31, 9], 'JMP' ],
    2004: [0xcd967, 45, 35, [True, True, False, False, False], 'Umaro Cave Switch Room trapdoor to Boss Room', [281, 40, 12], 'JMP' ],
    2005: [0x00000, 0, 0, [None, None, None, None, False], 'Umaro Cave 2nd Room west trapdoor logical exit A', [282, 33 ,26], None],
    2006: [0x00000, 0, 0, [None, None, None, None, False], 'Umaro Cave 2nd Room west trapdoor logical exit B', [282, 33 ,26], None],
    2056: [0xcd918, 34, 24, [True, True, False, False, False], 'Umaro Cave 2nd Room west trapdoor', [282, 33, 26], 'JMP' ],
    2007: [0x00000, 0, 0, [None, None, None, None, False], 'Umaro Cave 2nd Room east trapdoor logical exit A', [282, 14 ,30], None],
    2008: [0x00000, 0, 0, [None, None, None, None, False], 'Umaro Cave 2nd Room east trapdoor logical exit B', [282, 14 ,30], None],
    2057: [0xcd8f6, 34, 24, [True, True, False, False, False], 'Umaro Cave 2nd Room east trapdoor', [282, 14, 30], 'JMP' ],
    2009: [0xc3839, 50, 1, [False, False, False, False, False], 'Umaro Cave Boss Room trapdoor to Narshe', [283, 57, 7], 'JMP' ],
    2010: [0xc37e7, 82, 67, [True, True, True, False, False], 'Narshe Peak WoR entrance to Umaros Cave', [35, 9, 12], 'JMP' ],

    # ESPER MOUNTAIN
    2011: [0xbee80, 15, 0, [None, None, None, None, False], 'Esper Mtn 2nd Room bridge jump west', [0x177, 36, 53], None ],
    # forced connection, no mod
    2012: [0xbee71, 15, 0, [None, None, None, None, False], 'Esper Mtn 2nd Room bridge jump middle', [0x177, 39, 54], None ],
    # forced connection, no mod
    2013: [0xbee62, 15, 0, [None, None, None,None, False], 'Esper Mtn 2nd Room bridge jump east', [0x177, 47, 53], None ],
    # forced connection, no mod
    2014: [0xbee8f, 47, 30, [False, False, True, False, False], 'Esper Mtn Pit Room South trapdoor', [0x177, 11, 51], 'JMP' ],
    2015: [0xbeebe, 46, 30, [False, False, True, False, False], 'Esper Mtn Pit Room North trapdoor', [0x177, 12, 46], 'JMP'],
    2016: [0xbeeec, 47, 30, [False, False, True, False, False], 'Esper Mtn Pit Room East trapdoor', [0x177, 17, 49], 'JMP' ],

    # OWZER'S MANSION
    2017: [0xb4b86, 47, 1, [False, False, False, False, False], 'Owzers Mansion switching door left',  [0x0CF, 90, 50], 'JMP'],
    #2018: [0xb4b86, 47, 1, [False, False, False, False], 'Owzers Mansion switching door right', [0x0CF, 92, 50], 'JMP'],
    # same destination, same event!  When handling as JMP, this is not included a 2nd time (shared_oneways).
    2019: [0xb4bb5, 53, 3, [False, False, False, False, False], 'Owzers Mansion behind switching door exit', [0x0CF, 85, 50], 'JMP'],
    # set event bit 0x24c?
    2020: [0xb4c94, 13, 1, [False, False, False, False, False], 'Owzers Mansion floating chest room exit', [0x0CF, 76, 51], 'JMP'],
    2021: [0xb4bea, 51, 1, [False, False, False, False, False], 'Owzers Mansion save point room oneway', [0x0CF, 86, 38], 'JMP'],

    # MAGITEK FACTORY
    2022: [0xc7651, 49, 29, [False, False, False, False, False], 'Magitek factory 1 conveyor to Mtek-2 top tile', [0x106, 22, 53], 'JMP'],
    # '2022a': [0xc765f, 0, 0, [None, None, None, None], 'Magitek factory 1 conveyor to Mtek-2 bottom tile', [0x106, 22, 54]],
    # same exit as above; requires address patch & tile edit if using rewrite method.
    2023: [0xc7682, 37, 0, [None, None, None, None, False], 'Magitek factory platform elevator to Mtek-1', [0x106, 10, 54], None],
    2024: [0xc7905, 50, 10, [False, False, False, False, False], 'Magitek factory 2 pipe exit loop', [0x107, 49, 48], 'JMP'],
    2025: [0xc7565, 86, 58, [True, False, False, False, False], 'Magitek factory 2 conveyor to pit left tile', [0x107, 36, 44], 'JMP'],
    #'2025a': [0xc7581, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit mid tile', [0x107, 37, 44]],
    #'2025b': [0xc7573, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit right tile', [0x107, 38, 44]],
    # same exits as above; requires address patch & tile edit if using rewrite method.
    2026: [0xc75f6, 91, 39, [False, False, False, False, False], 'Magitek factory pit hook to Mtek-2', [0x108, 6, 6], 'JMP'],
    2027: [0xc7f43, 217, 131, [False, False, False, False, False], 'Magitek factory lab Cid''s elevator', [0x112, 20, 13], 'JMP'],
    # bit $1E80($068) set by switch (0c7a60)?  Look for conflicts with event patch code.
    2028: [0xc8022, 309, 152, [False, True, False, False, False], 'Magitek factory minecart start event', [0x110, 'NPC', 0], 'JMP'],
    # NPC #0 on this map. Not an event tile.  Started by talking to Cid.  Position: # [0x110, 9, 51]

    # CAVE TO THE SEALED GATE
    2029: [0xb3176, 84, 0, [None, None, None, None, False], 'Cave to the Sealed Gate grand staircase', [0x180, 71, 15], None],
    # Grand staircase event
    2030: [0xb33c9, 32, 0, [None, None, None, None, False], 'Cave to the Sealed Gate switch bridges', [0x180, 104, 17], None],
    # Switch bridge events
    2031: [0xb2a9f, 7, 1, [False, False, False, False, False], 'Cave to the Sealed Gate shortcut exit', [0x180, 5, 43], 'JMP'],  # Shortcut exit

    # ZOZO (WORLD OF BALANCE)
    2032: [0xa963d, 22, 0, [None, None, None, None, False], 'Zozo hook descent from building', [0x0DD, 35, 41], None],
    2033: [0x00000, 0, 0, [None, None, None, None, False], 'Zozo line of walking guys (logical)', [0x0E1, 0, 0], None],
    2061: [0x00000, 0, 0, [None, None, None, None, False], 'Zozo clock room left to right WOB (logical)', [0x0E1, None, None], None], # logical no randomize
    2062: [0x00000, 0, 0, [None, None, None, None, False], 'Zozo clock room right to left WOB (logical)', [0x0E1, None, None], None], # logical, no randomize
    2063: [0x00000, 0, 0, [None, None, None, None, False], 'Zozo clock room left to right WOR (logical)', [0x0E1, None, None], None], # logical no randomize
    2064: [0x00000, 0, 0, [None, None, None, None, False], 'Zozo clock room right to left WOR (logical)', [0x0E1, None, None], None], # logical, no randomize

    # LETE RIVER
    2034: [0xb059f, 151, 146, [False, False, False, True, False], 'Lete River start', [0x071, 31, 51], 'JMP'],
    2035: [0xb0636, 193, 182, [False, False, False, True, False], 'Lete River Section 1', [0x071, None, None], 'JMP'],
    '2035a': [0xb06f7, 101, 90, [False, False, False, True, False], 'Lete River Section 1 (LEFT)', [0x071, None, None], 'JMP'],
    '2035b': [0xb075c, 112, 101, [False, False, False, True, False], 'Lete River Section 1 (RIGHT)', [0x071, None, None], 'JMP'],
    2036: [0xb051c, 64, 52, [False, False, False, True, False], 'Lete River Cave 1', [0x072, 20, 24], 'JMP'],
    2037: [0xb07cc, 157, 145, [False, False, False, True, False], 'Lete River Section 2', [0x071, None, None], 'JMP'],
    2038: [0xb055c, 67, 55, [False, False, False, True, False], 'Lete River Cave 2', [0x072, 6, 15], 'JMP'],
    2039: [0xb0869, 229, 108, [False, False, False, True, False], 'Lete River Section 3 + boss', [0x071, None, None], 'JMP'],

    # ZONE EATER
    # For Zone Eater entrance and exit, we are in world map operations, so we can't use the normal state mod codes.
    # Instead, we make ZoneEater send you to the switchyard [0x005, 2040 % 128, 2040 // 128] and place an event tile
    # there that just does the load command.  That event tile can then be modified by Transitions()
    #2040: [0xa008f, 7, 1, [False, False, False, False], 'Zone Eater Engulf', [0x001, 'JMP', 0] ],  # In battle event
    2040: [None, 7, 1, [False, False, False, False, False], 'Zone Eater Engulf', [0x005, 2040 % 128, 2040 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2041: [0xb7d9d, 33, 27, [False, False, False, False, False], 'Zone Eater Exit', [0x114, 5, 6], 'JMP'],  # Goes to Switchyard tile
    2042: [0xb8251, 35, 18, [False, False, False, False, False], 'Zone Eater leprechaun bump', [0x114, 'NPC', 0], 'JMP' ], # Shared code, 3 NPCs
    2043: [0xb8062, 0, 0, [None, None, None, None, False], 'Zone Eater pit switch exit (logical)', [0x114, 46, 17], None],

    # SERPENT TRENCH
    2044: [0xbc84d, 45, 39, [False, False, False, False, False], 'Cliff jump to Serpent Trench', [0x0A8, 8, 11], 'JMP'],
    #2044a: [0x1c84d, 7, 1, [False, False, False, False], 'Cliff jump to Serpent Trench tile 2', [0x0A8, 9, 11], 'JMP'],  # Duplicate, not needed with JMP
    2045: [None, 7, 1, [False, False, False, False, False], 'Serpent Trench #1 to cave', [0x005, 2045 % 128, 2045 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2046: [0x00000, 0, 0, [None, None, None, None, False], 'Serpent Trench #1 continue to #2', [0x002, 0, 0], None],  # logical exit
    2047: [0xa8c41, 7, 1, [False, False, False, False, False], 'Serpent Trench Cave 1 to Serpent Trench #2', [0x0af, 43, 4], 'JMP'], # Goes to switchyard.
    2048: [None, 7, 1, [False, False, False, False, False], 'Serpent Trench #2 to cave 2a', [0x005, 2048 % 128, 2048 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2049: [0x00000, 0, 0, [None, None, None, None, False], 'Serpent Trench #2 continue to #3', [0x002, 0, 0], None],  # logical exit
    2050: [0xa8cae, 13, 7, [False, False, False, False, False], 'Serpent Trench Cave 2b to Cave 2c', [0x0af, 49, 42], 'JMP'],
    2051: [0xa8c94, 7, 1, [False, False, False, False, False], 'Serpent Trench Cave 2c to Serpent Trench #3', [0x0af, 6, 36], 'JMP'], # Goes to switchyard.
    2052: [None, 7, 1, [False, False, False, False, False], 'Serpent Trench #3 to SWITCHYARD', [0x005, 2052 % 128, 2052 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2053: [None, 11, 1, [False, False, False, False, False], 'SWITCHYARD to Nikeah (forced)', [0x005, 2053 % 128, 2053 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]

    # BURNING HOUSE
    2054: [0xbdcc7, 7, 1, [False, False, False, False, False], 'Thamasa Inn to Burning House', [0x15A, 'NPC', 0], 'JMP' ], # Talk to the innkeeper.  requires JMP.
    2055: [0x00000, 0, 0, [None, None, None, None, False], 'Burning House after boss to Inn', [0x15F, None, None], None], # logical? no randomize?

    # DARYL'S TOMB
    2058: [0xa435d, 12, 5, [False, False, False, False, False], 'Darills Tomb Quick Exit to World Map', [0x12B, 100, 7], 'JMP' ],  # Goes to Switchyard tile
    2059: [0x00000, 0, 0, [None, None, None, None, False], 'Darills Tomb Turtle 2 left to right (logical)', [0x12C, None, None], None], # logical no randomize
    2060: [0x00000, 0, 0, [None, None, None, None, False], 'Darills Tomb Turtle 2 right to left (logical)', [0x12C, None, None], None], # logical, no randomize

    # PHANTOM TRAIN
    2065: [0xba8f1, 309, 149, [False, False, False, False, False], 'Phantom Train Platform to Car 1', [0x08C, 72, 10], 'JMP' ],
    2066: [0xba709, 83, 32, [False, False, False, False, False], 'Phantom Train Car 2 outside trapdoor', [0x08E, 56, 5], 'JMP'],  # Who knew about this ?!?
    2067: [0x00000, 0, 0, [False, False, False, False, False], 'Phantom Train roof jump cutscene (logical)', [0x08E, 56, 5], 'JMP'],  #
    2068: [0xbba0c, 9, 3, [False, False, False, False, False], 'Phantom Train smokestack switch & boss', [0x08D, 31, 7], 'JMP'],  # tile points to 0xbb9d4

    # CYAN'S DREAM
    2069: [0xb8484, 18, 1, [False, False, False, False, False], 'Doma sleeping into Cyans Dream', [0x07b, 4, 12], 'JMP'],  # tile points to 0xb827d
    2070: [0xb8c62, 21, 1, [False, False, False, False, False], 'Cyans Dream Three Stooges Door', [0x13d, 46, 55], 'JMP'],  # tile points to 0xb8bd1
    2071: [0xb93b8, 7, 1, [False, False, False, False, False], 'Cyans Dream Locomotive outside', [0x08f, 38, 8], 'JMP'],  # tile points to 0xb93b8
    2072: [0xb93bf, 226, 12, [False, False, False, False, False], 'Cyans Dream Locomotive interior', [0x092, 8, 13], 'JMP'],  # tile points to 0xba808
    2073: [0xb94e7, 268, 46, [False, False, False, False, False], 'Cyans Dream Caves Bridge Fall', [0x13f, 14, 25], 'JMP'],  # tile points to 0xb94e7
    2074: [0xb97d6, 676, 524, [False, True, False, False, False], 'Cyans Dream Doma Throne Room Boss', [0x07e, 25, 11], 'JMP'],  # tile points to 0xb97d6

    # CAVE ON THE VELDT
    2075: [0, 0, 0, [False, True, False, False, False], 'Cave on the Veldt Boss Fight', [0x161, 59, 18], 'JMP'],  # tile points to 0xb7a18.  Address values updated dynamically in events.veldt_cave_wor???

    # EVENT TILES that behave as if they are doors:
    #       WOB: Imperial Camp; Figaro Castle (@ Figaro & Kohlingen); Thamasa; Vector; Cave to SF south entrance
    #       WOR: Figaro Castle (@ Figaro & Kohlingen); Solitary Island Cliff
    #       Other: Opera House Lobby, Mobliz Outside, ...
    # To do this: must add index to map_exit_extra.
    # FOR TILES ON WORLD MAP:  we cannot use JMP routines (because world map opcodes are different, and there's no straight Call)
    # Instead, send to a switchyard tile.  See event.south_figaro_cave_wob.door_rando_mod() for an example.
    1501: [None, 7, 1, [None, None, None, None, True], 'Imperial Camp WoB', [0x005, 1501 % 128, 1501 // 128], 'JMP'],  # Tile loads 0xb0bb7 (Check if FINISHED_IMPERIAL_CAMP, load camp if not)  [0x000, 179, 71]
    1502: [None, 7, 1, [None, None, None, None, True], 'Figaro Castle WoB', [0x005, 1502 % 128, 1502 // 128], 'JMP'],  # Tile loads 0xa5eb5 (Check if FC is in figaro desert, branch to load map 0x037 at 0xa5ebb).  [0x000, 64, 76]
    #'1502a': [0xa5eb5, 0, 0, [None, None, None, None], 'Figaro Castle WoB 2', [0x000, 65, 76], None],
    1503: [0xa5ec2, 0, 0, [None, None, None, None, True], 'Figaro Castle WoB (kohlingen)', [0x000, 30, 48], None],
    #'1503a': [0xa5ec2, 0, 0, [None, None, None, None], 'Figaro Castle WoB (kohlingen) 2', [0x000, 31, 48], None],
    1504: [None, 7, 1, [None, None, None, None, True], 'Thamasa WoB', [0x005, 1504 % 128, 1504 // 128], 'JMP'],  # Tile loads 0xbd2ee (Check if LEO_BURIED_THAMASA, branch to load map 0x154 at 0xbd308) [0x000, 250, 128]
    1505: [None, 7, 1, [None, None, None, None, True], 'Vector entrance event tile', [0x005, 1505 % 128, 1505 // 128], 'JMP'],  # Tile loads 0xa5ecf (Check if SEALED_GATE, branch to load burning vector if so; load map at CA/5ED5 (0x0f2, 32, 61)  [0x000, 120, 187]
    #'1505a': [0xa5ecf, 14, 7, [None, None, None, None], 'Vector entrance event tile 2', [0x000, 121, 187], None],
    #1506: [0xa5ee3, 20, 14, [False, False, False, False], 'Cave to South Figaro South Entrance WoB', [0x000, 75, 102], None],
    1506: [None, 7, 1, [False, False, False, False, True], 'Cave to South Figaro South Entrance WoB', [0x005, 1506 % 128, 1506 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    1507: [None, 7, 1, [None, None, None, None, True], 'Figaro Castle WoR', [0x005, 1507 % 128, 1507 // 128], 'JMP'],  # Tile loads 0xa5f0b (Check if FC in figaro desert WOR, branch to load map at 0x037 if so. [0x001, 81, 85]
    #'1507a': [0xa5f0b, 0, 0, [None, None, None, None], 'Figaro Castle WoR 2', [0x001, 82, 85], None],
    1508: [0xa5f18, 0, 0, [None, None, None, None, True], 'Figaro Castle WoR (kohlingen)', [0x001, 53, 58], None],
    #'1508a': [0xa5f18, 0, 0, [None, None, None, None], 'Figaro Castle WoR (kohlingen) 2', [0x001, 54, 58], None],
    1509: [0xa5f39, 0, 0, [None, None, None, None, True], 'Solitary Island cliff entrance', [0x001, 73, 231], None],

    1510: [0xb80a9, 15, 9, [False, False, False, False, False], 'Zone Eater Digestive Tract east', [0x118, 54, 53], 'JMP'],
    1511: [0xb809a, 15, 9, [False, False, False, False, False], 'Zone Eater Digestive Tract west', [0x118, 26, 54], 'JMP'],
    1512: [0xa422e, 43, 35, [False, False, False, False, False], 'Daryls Tomb turtle room south exit', [0x12b, 56, 14], 'JMP'],
    1513: [0xa5ef7, 20, 14, [False, False, False, False, False], 'Cave to South Figaro North WOB', [0x047, 10, 48], 'JMP'],
    #'1513a': [0xa5ef7, 20, 14, [False, False, False, False], 'Cave to South Figaro North WOB 2', [0x047, 11, 48], 'JMP']

    1514: [0xba7e4, 7, 1, [False, False, False, False, False], 'Phantom Train Car 3 South Exit', [0x091, 26, 11], 'JMP'],  # Note: just including event addresses for map loads.  Ignoring all switchyard code.
    1515: [0xba78b, 7, 1, [False, False, False, False, False], 'Phantom Train Car 1 Left Exit', [0x091, 1, 7], 'JMP'],
    #'1515a': [0xbaac4, 143, 137, [False, False, False, False], 'Phantom Train Car 1 Left Exit 2', [0x091, 1, 8], 'JMP'],
    1516: [0xba778, 7, 1, [False, False, False, False, False], 'Phantom Train Car 1 Right Exit', [0x091, 30, 7], 'JMP'],
    #'1516a': [0xbaac4, 143, 137, [False, False, False, False], 'Phantom Train Car 1 Right Exit 2', [0x091, 30, 8], 'JMP'],
    #1517: [0xba5f9, 21, 15, [False, False, False, False], 'Phantom Train Car 1 South Door Outside', [0x08E, 72, 8], 'JMP'],  # These will need special treatment:
    1518: [0xba60e, 21, 15, [False, False, False, False, False], 'Phantom Train Car 1 Right Door Outside', [0x08E, 74, 8], 'JMP'],  # They set event bits that are used by the interior
    1519: [0xba623, 21, 15, [False, False, False, False, False], 'Phantom Train Car 1 Left Door Outside', [0x08E, 67, 8], 'JMP'],   # switchyard exit tiles to decide on destination.
    1520: [0xba6e5, 18, 11, [False, False, False, False, False], 'Phantom Train Car 2 Right Door Outside', [0x08E, 58, 8], 'JMP'],  # These event bits need to be set upon entry.
    1521: [0xba6f7, 18, 11, [False, False, False, False, False], 'Phantom Train Car 2 Left Door Outside', [0x08E, 51, 8], 'JMP'],
    1522: [0xba67d, 23, 17, [False, False, False, False, False], 'Phantom Train Car 3 South Door Outside', [0x08E, 41, 8], 'JMP'],

    1523: [0xba84b, 7, 1, [False, False, False, False, False], 'Phantom Train Car 2 Left Exit', [0x091, 1, 7], 'JMP'],
    1524: [0xba842, 7, 1, [False, False, False, False, False], 'Phantom Train Car 2 Right Exit', [0x091, 30, 7], 'JMP'],

    1525: [0xba638, 7, 1, [False, False, False, False, False], 'Phantom Train Car 4 Right Door Outside', [0x08E, 10, 8], 'JMP'],  # on map 0x08E
    1526: [0xba647, 7, 1, [False, False, False, False, False], 'Phantom Train Car 4 Right Door Outside no caboose', [0x08D, 116, 8], 'JMP'],  # on map 0x08D
    1527: [0xba7a1, 7, 1, [False, False, False, False, False], 'Phantom Train Car 4 Right Exit', [0x095, 31, 7], 'JMP'],  # 0xba792

    1528: [0xba656, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Right Door Outside', [0x08D, 82, 8], 'JMP'],
    1529: [0xba665, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Left Door Outside', [0x08D, 75, 8], 'JMP'],
    1530: [0xba676, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Right Door Outside', [0x08D, 66, 8], 'JMP'],
    1531: [0xba69e, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Left Door Outside', [0x08D, 59, 8], 'JMP'],
    1532: [0xba6a5, 24, 7, [False, False, False, False, False], 'Phantom Train Engine Door Outside', [0x08D, 38, 8], 'JMP'], # --> 0x92, 8, 12

    1533: [0xba7bf, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Right Exit', [0x097, 26, 8], 'JMP'],  # map 0x097 & 0x17E clear
    #'1533a': [0xba7bf, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 26, 9], 'JMP'],
    1534: [0xba7d2, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Left Exit', [0x097, 1, 8], 'JMP'],
    #'1534a': [0xba7d2, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 1, 9], 'JMP'],
    1535: [0xba6c3, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Right Cabin', [0x097, 19, 7], 'JMP'],  # --> 0x99, 8, 28
    1536: [0xba6d0, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Left Cabin', [0x097, 9, 7], 'JMP'],    # --> 0x99, 23, 11
    1537: [0xba81e, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Right Cabin interior exit', [0x099, 8, 29], 'JMP'],  # Not shared. --> 0x97, 19, 9. Siegfried room?
    1538: [0xba82b, 7, 1, [False, False, False, False, False], 'Phantom Train Car 6 Left Cabin interior exit', [0x099, 23, 12], 'JMP'],  # --> 0x97, 9, 9. 0x17E OFF!

    1539: [0xba7db, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Right Exit', [0x097, 26, 8], 'JMP'],  # map 0x097 & 0x17E set
    #'1539a': [0xba7bf, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 26, 9], 'JMP'],
    1540: [0xba801, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Left Exit', [0x097, 1, 8], 'JMP'],
    #'1540a': [0xba801, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Exit 2', [0x097, 1, 9], 'JMP'],
    1541: [0xba6d7, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Right Cabin', [0x097, 19, 7], 'JMP'],  # --> 0x99, 23, 11
    1542: [0xba6de, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Left Cabin', [0x097, 9, 7], 'JMP'],    # --> 0x99, 23, 28
    1543: [0xba832, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Right Cabin interior exit', [0x099, 23, 12], 'JMP'],  # --> 0x97, 19, 9.  0x17E ON, NOT CLEARED!
    1544: [0xba839, 7, 1, [False, False, False, False, False], 'Phantom Train Car 7 Left Cabin interior exit', [0x099, 23, 29], 'JMP'],  # Not shared. --> 0x97, 9, 9.  MIAB room.

    1545: [0xba80e, 7, 1, [False, False, False, False, False], 'Phantom Train Locomotive interior exit', [0x092, 8, 13], 'JMP'],  # --> 0x8d, 38, 9.  tile calls 0xba808.

    # EBOT'S ROCK (HIDON CAVE)
    1546: [0xb6e51, 7, 1, [False, False, False, False, False], 'Exit from Hidon Cave', [0x195, 7, 24], 'JMP'],  # --> 0x1, 249, 224.  tile points to 0xb6e4b

    # DOMA WOB MODIFIED EVENT ENTRANCE
    1547: [None, 7, 1, [False, False, False, False, True], 'Doma Left Tile WoB', [0x005, 1547 % 128, 1547 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    #'1547a': [None, 7, 1, [False, False, False, False], 'Doma Right Tile WoB', [0x005, 1547 % 128, 1547 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]  # don't need both, just reuse code

    # ALBROOK WoB/WoR
    1548: [0xc60d8, 7, 1, [False, False, False, False, False], 'Albrook Inn exit WoB', [0x145, 58, 57], 'JMP'],  # --> 0x143, 54, 14.  tile calls 0xc60d2 (a WOB/WOR handler)
    5548: [0xc60df, 7, 1, [False, False, False, False, False], 'Albrook Inn exit WoR', [0x145, 58, 57], 'JMP'],  # --> 0x144, 54, 14.  tile calls 0xc60d2 (a WOB/WOR handler)
    1549: [0xc60ec, 7, 1, [False, False, False, False, False], 'Albrook Wpn Shop exit WoB', [0x146, 4, 56], 'JMP'],  # --> 0x143, 23, 21.  tile calls 0xc60e6 (a WOB/WOR handler)
    5549: [0xc60f3, 7, 1, [False, False, False, False, False], 'Albrook Wpn Shop exit WoR', [0x146, 4, 56], 'JMP'],  # --> 0x144, 23, 21.  tile calls 0xc60e6 (a WOB/WOR handler)
    1550: [0xc6100, 7, 1, [False, False, False, False, False], 'Albrook Armor Shop exit WoB', [0x147, 101, 24], 'JMP'],  # --> 0x143, 39, 21.  tile calls 0xc60fa (a WOB/WOR handler)
    5550: [0xc6107, 7, 1, [False, False, False, False, False], 'Albrook Armor Shop exit WoR', [0x147, 101, 24], 'JMP'],  # --> 0x144, 39, 21.  tile calls 0xc60fa (a WOB/WOR handler)
    1551: [0xc6114, 7, 1, [False, False, False, False, False], 'Albrook Item Shop exit WoB', [0x148, 37, 55], 'JMP'],  # --> 0x143, 7, 15.  tile calls 0xc610e (a WOB/WOR handler)
    5551: [0xc611b, 7, 1, [False, False, False, False, False], 'Albrook Item Shop exit WoR', [0x148, 37, 55], 'JMP'],  # --> 0x144, 7, 15.  tile calls 0xc610e (a WOB/WOR handler)

    # ZONE EATER AS DOOR (for Map Shuffle only!)
    # NOTE: not compatible with &doors, if Zone Eater entrance/exit are being treated as one-ways!  (2040, 2041)
    1552: [None, 7, 1, [False, False, False, False, True], 'Zone Eater Engulf as door', [0x005, 1552 % 128, 1552 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    1553: [0xb7d9d, 33, 27, [False, False, False, False, False], 'Zone Eater Exit as door', [0x114, 5, 6], 'JMP'],  # Goes to Switchyard tile

    # PHOENIX CAVE AS DOOR
    1554: [None, 7, 1, [False, False, False, False, False], 'Phoenix Cave entry as door', [0x005, 1554 % 128, 1554 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    1555: [None, 7, 1, [False, False, False, False, False], 'Phoenix Cave exit as door', [0x005, 1555 % 128, 1555 // 128], 'JMP'],  # exit event from Phoenix cave. hook @ [0x13e, 5, 6] calls 0xc20e5

    # FLOATING CONTINENT AS DOOR
    1556: [None, 7, 1, [False, False, False, False, False], 'Floating Continent entry as door', [0x005, 1556 % 128, 1556 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    1557: [None, 7, 1, [False, False, False, False, False], 'Floating Continent exit as door', [0x005, 1557 % 128, 1557 // 128], 'JMP'],  # exit event from Floating Continent:

    # FIGARO CASTLE PRISON TO ANCIENT CAVE
    1558: [0xa5f25, 20, 14, [False, False, False, False, False], 'Figaro Castle Prison to Ancient Cave', [0x03d, 35, 35], 'JMP'],  # If (0x0cd), branch to load AC; otherwise load Cave to SF
}
# Notes:
#   1. is_screen_hold_on is False for Umaro's Cave trapdoor events, but they all include a hold screen / free screen
#       pair after the transition, so it technically does not need to be patched in for entrances.  It also doesn't need
#       to be patched in for exits, so the value shouldn't be "True" either.  If there were a value for which both
#       "i" and "not i" were false, I would use it here.
#   2. Currently choosing to randomize destination of mine cart event.
#       Talking to Cid always starts minecart event, but destination can take you elsewhere
#       What happens with MTek3 prize?  Is it triggered by minecart, or by entering Vector?

# For events that go to switchyard tiles, we still will need to know sometimes what map they should return to.
# Used in maps.
event_return_map = {
    1501: 0x000,  # 'Imperial Camp WoB'
    1502: 0x000,  # 'Figaro Castle WoB'
    1504: 0x000,  # 'Thamasa WoB'
    1505: 0x000,  # 'Vector WOB'
    1506: 0x000,  # 'Cave to South Figaro South Entrance WoB'
    1507: 0x001,  # 'Figaro Castle WoR'
    1546: 0x001,  # 'Exit from Hidon Cave' WoR
    1547: 0x000,  # 'Doma Left Tile WoB'
    1552: 0x001,  # 'Zone Eater Engulf as door' WoR
    1554: 0x00b,  # 'Phoenix Cave entry as door' Falcon
    1556: 0x006,  # 'Floating Continent entry as door' Blackjack
}


from instruction.event import EVENT_CODE_START
from instruction import field
import instruction.field.entity as field_entity
import data.event_bit as event_bit

def set_locomotive_switches(bytes=True):
    # Set single event bit 0x03E to check when initiating smokestack event
    # CB/B9DC: C2    If ($1E80($185) [$1EB0, bit 5] is set) or ($1E80($186) [$1EB0, bit 6] is clear) or ($1E80($184) [$1EB0, bit 4] is clear), branch to $CBB9D0
    # CB/B9D0: <smokestack doesn't work>
    from memory.space import Write, Bank
    pt_switches_bit = [
        field.BranchIfAny([0x184, False, 0x185, True, 0x186, False], "CLEAR_SWITCHES"),
        field.SetEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
        field.Return(),
        "CLEAR_SWITCHES",
        field.ClearEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
        field.Return()
    ]
    space = Write(Bank.CB, pt_switches_bit, "Set or Clear PT switches bit")

    set_switches = [field.Call(space.start_address)]

    if bytes:
        set_switches_bytes = []
        for f in set_switches:
            set_switches_bytes += [f.opcode] + f.args
        return set_switches_bytes
    else:
        return set_switches


def add_mtek_armor(bytes=False):
    src = [
        field.Call(field.ADD_PARTY_MAGITEK),
        field.SetVehicle(field_entity.PARTY0, field.Vehicle.MAGITEK_AND_RIDER)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def remove_mtek_armor(bytes=False):
    src = [
        field.Call(field.REMOVE_PARTY_MAGITEK),
        field.SetVehicle(field_entity.PARTY0, field.Vehicle.NONE)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src


def tentacles_bit_check(bytes=False):
    src = [
        field.SetEventBit(event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.LONE_WOLF_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.PRISONERS_FIGARO_CASTLE),
        field.SetEventBit(event_bit.GOT_FALCON),  # Needed to go to AC afterward
        field.ReturnIfEventBitSet(event_bit.DEFEATED_TENTACLES_FIGARO),
        field.SetEventBit(npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE),
        field.SetEventBit(npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE),
        field.ClearEventBit(npc_bit.PRISON_GUARD_FIGARO_CASTLE),
        field.Return()
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def opera_disruption_bit_check(bytes=False):
    src = [
        field.ReturnIfEventBitSet(event_bit.FINISHED_OPERA_DISRUPTION),
        field.ClearEventBit(event_bit.BEGAN_OPERA_DISRUPTION),
        field.SetEventBit(npc_bit.ULTROS_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT1_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT2_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT3_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT4_OPERA_CEILING),
        field.SetEventBit(npc_bit.RAT5_OPERA_CEILING),
        field.SetEventBit(npc_bit.CEILING_DOOR_OPERA_HOUSE),
        field.SetEventBit(npc_bit.DANCING_COUPLE1_OPERA),
        field.SetEventBit(npc_bit.DANCING_COUPLE2_OPERA),
        field.SetEventBit(npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING)
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src

def opera_dragon_bit_check(bytes=False):
    src = [
        field.ReturnIfEventBitSet(event_bit.DEFEATED_OPERA_HOUSE_DRAGON),
        field.ClearEventBit(npc_bit.IMPRESARIO_OPERA_LOBBY),
        field.SetEventBit(npc_bit.IMPRESARIO_OPERA_PANICKING),
        field.SetEventBit(npc_bit.DRAGON_OPERA_HOUSE),
        field.HideEntity(0x13)   # hide the Impressario in the lobby, since he's not supposed to be there.
    ]
    if bytes:
        src_bit = []
        for s in src:
            src_bit += [s.opcode] + s.args
        return src_bit
    else:
        return src


# from instruction.field.functions import ORIGINAL_CHECK_GAME_OVER
exit_event_patch = {
    # Jump into Umaro's Cave:  Reproduce AtmaTek's changes to the event in data/umaro_cave.add_gating_condition()
    ### Not used when using JMP method ###
    #2010: lambda src, src_end: tritoch_event_mod(src, src_end),

    # Trapdoors in Esper Mountain: remove the check to see if the boss has been defeated yet.
    # e.g. "CB/EE8F: C0    If ($1E80($097) [$1E92, bit 7] is clear), branch to $CA5EB3 (simply returns)
    # When using JMP method, this should be handled in events.esper_mountain.py
    #2014: lambda src, src_end: [src[6:], src_end],
    #2015: lambda src, src_end: [src[6:], src_end],
    #2016: lambda src, src_end: [src[6:], src_end],

    # Switching door events in Owzer's Mansion: turn off the door timer before transitioning
    # Call subroutine $CB/2CAA (resets all timers).
    # # May also be necessary to clear event bits $1FC, $1FD, $1FE: [0xd3, 0xfc, 0xd3, 0xfd, 0xd3, 0xfe], but
    # # supposedly these are cleared on map load.
    2017: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],
    2018: lambda src, src_end: [[0xb2, 0xaa, 0x2c, 0x01] + src, src_end],

    # Zone eater: fade back in music after exit animation
    2041: lambda src, src_end: [src[:-1] + [0xf3, 0x20] + src[-1:], src_end],

    # Phantom Train set correct "switches" bit if leaving locomotive
    1545: lambda src, src_end: [src[:-1] + set_locomotive_switches(bytes=True) + src[-1:], src_end],

    # Doma Cave one-way doors: remove MTek armor
    859: lambda src, src_end: [src, src_end[:5] + remove_mtek_armor(bytes=True) + src_end[5:]],
    862: lambda src, src_end: [src, src_end[:5] + remove_mtek_armor(bytes=True) + src_end[5:]],
}

from event.phantom_train import *
phantom_train_initiate = PhantomTrain.initiation_script

exit_door_patch = {
    # For use with maps.create_exit_event() and maps.shared_map_exit_event()

    # Owzer's Mansion doors
    586: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.
    587: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.

    # Cave to the sealed gate: force reset timers when leaving lava room
    1075: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.
    1077: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.

    # Phantom Train set correct "switches" bit if leaving locomotive
    1545: set_locomotive_switches(bytes=False),

    # Doma Cave doors: remove MTek armor
    858: remove_mtek_armor(),
    860: remove_mtek_armor(),
    861: remove_mtek_armor(),
    863: remove_mtek_armor(),
    864: remove_mtek_armor(),

    # Phantom Train: initiate PT event if Sabin is recruited
    465: phantom_train_initiate(),

    # Baren Falls: for some reason, it doesn't auto update the parent map
    15: [field.SetParentMap(0x0, direction.DOWN, 185, 93)],


}

entrance_event_patch = {
    # For use by transitions.mod()

    # Jump back to Narshe from Umaro's cave: force "clear $1EB9 bit 4" (song override) before transition
    # Now handled in map_events.mod() with common patches
    # 3009: lambda src, src_end: [src[:-1] + [0xd3, 0xcc] + src[-1:], src_end],

    # Jump from Narshe into Umaro's cave: Remove extra falling sound effect (src_end[5:6])
    # Can't do this with JMP method.
    #3010: lambda src, src_end: [src, src_end[:5] + src_end[7:]],

    # Jump into Esper Mountain room 2, North trapdoor: patch in "hold screen" (0x38) after map transition
    # The other trapdoors have this, maybe it's just a typo?
    2015: lambda src, src_end: [src, src_end[:5] + [0x38] + src_end[5:]],

    # Cid's Elevator Ride: remove move-party-down after elevator.
    # space = Reserve(0xc8014, 0xc801a, "magitek factory move party down after elevator", field.NOP())
    # NOTE: should now be handled in Events(), no need to repeat.
    # 3027: lambda src, src_end: [ src, src_end[:-8] + src_end[-1:]]

    # Minecart Ride: if Cranes are defeated, instead go to normal Vector
    2028: lambda src, src_end: minecart_event_mod(src, src_end),    # JMP code
    #3028: lambda src, src_end: minecart_event_mod(src, src_end),   # rewrite code

    # Lete River: Hide the Raft NPCs ($10, $11) when entering the cave rooms
    # see e.g. CB/052F -- CB/0533 (Delete object $10, Refresh Objects, Hide Object $10)
    2035: lambda src, src_end: [src, src_end[:5] + [0x3e, 0x10, 0x45, 0x42, 0x10] + src_end[5:]], # Cave 1 entry, object $10
    2037: lambda src, src_end: [src, src_end[:5] + [0x3e, 0x11, 0x45, 0x42, 0x11] + src_end[5:]], # Cave 2 entry, object $11

    # Daryl's Tomb: Move the turtles to the appropriate side.
    ### MOVED TO require_event_bit

    # Doma Cave one-way doors: add MTek armor.  Redundant if in map.
    6859: lambda src, src_end: [src, src_end[:5] + add_mtek_armor(bytes=True) + src_end[5:]],
    6862: lambda src, src_end: [src, src_end[:5] + add_mtek_armor(bytes=True) + src_end[5:]],
}

from event.doma_wob import *
doma_siege_patch = DomaWOB.entrance_door_patch

from event.mt_zozo import *
mt_zozo_cliff_check = MtZozo.entrance_door_patch()

from event.phoenix_cave import *
phoenix_cave_animation = PhoenixCave.entrance_door_patch()

from event.floating_continent import *
floating_continent_logic = FloatingContinent.entrance_door_patch()
floating_continent_return = FloatingContinent.return_door_patch()

entrance_door_patch = {
    # For use by maps.create_exit_event() and maps.shared_map_exit_event()
    # door_id: [Code that must be run upon entering a door, Before (True) or After (False) map load]
    # If you are just setting or clearing event bits, use require_event_bit instead.

    # Doma Cave doors: add MTek armor.  Redundant if in map.
    858: [add_mtek_armor(), False],
    860: [add_mtek_armor(), False],
    861: [add_mtek_armor(), False],
    863: [add_mtek_armor(), False],
    864: [add_mtek_armor(), False],

    # Doma siege entrance patch
    1240: [doma_siege_patch, True],

    # Figaro Castle WoR tentacles bit check patch (on entering SF Cave for map shuffle)
    262: [tentacles_bit_check(), False],

    # Opera House WoB completed opera bit check patch
    658: [opera_disruption_bit_check(), False],

    # Opera House WoR defeated dragon bit check patch
    4658: [opera_dragon_bit_check(), False],

    # Mt Zozo cliff entrance patch
    1204: [mt_zozo_cliff_check, True],

    # Phoenix cave animation & party split
    1555: [phoenix_cave_animation, True],

    # Floating continent choice, animation, boss call
    1557: [floating_continent_logic, True],

    # Return to Blackjack after FC connection, animation
    1556: [floating_continent_return, True],

}

# Automatically set required event bits BEFORE loading the map
require_event_bit = {
    # Lete River: hide raft NPC before entering caves
    2035: {0x4FC: False},   # Cave #1
    2037: {0x4FD: False},   # Cave #2

    # Daryl's Tomb: move turtles to the appropriate side
    1512: {event_bit.DARYL_TOMB_TURTLE1_MOVED: True},
    782: {event_bit.DARYL_TOMB_TURTLE1_MOVED: False},
    793: {event_bit.DARYL_TOMB_TURTLE2_MOVED: False},
    794: {event_bit.DARYL_TOMB_TURTLE2_MOVED: False},
    795: {event_bit.DARYL_TOMB_TURTLE2_MOVED: True},

    # Phantom Train, Outside rear section: turn off ghosts
    474: {0x509: False},
    475: {0x509: False},
    476: {0x509: False},
    1518: {0x509: False},
    1519: {0x509: False},
    1520: {0x509: False},
    1521: {0x509: False},
    1522: {0x509: False},

    # Phantom Train, Car 1
    1515: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: True, 0x507: False, 0x509: False},
    1516: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: True, 0x507: False, 0x509: False},
    # Phantom Train, Car 2
    1523: {0x17e: True, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: False, 0x507: True, 0x509: False},
    1524: {0x17e: True, event_bit.PHANTOM_TRAIN_CAR_3: False, 0x506: False, 0x507: True, 0x509: False},
    # Phantom Train, Car 3
    1514: {0x17e: False, event_bit.PHANTOM_TRAIN_CAR_3: True, 0x506: False, 0x507: False, 0x509: True},

    # Phantom Train, Car 6
    1533: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Right Exit
    1534: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Left Exit
    1535: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Right Cabin
    1536: {0x17e: False, 0x506: True, 0x507: False},  # Phantom Train Car 6 Left Cabin
    1538: {0x17e: False},  # Phantom Train Car 6 Left Cabin interior

    # Phantom Train, Car 7
    1539: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Right Exit
    1540: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Left Exit
    1541: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Right Cabin
    1542: {0x17e: True, 0x506: False, 0x507: True},  # Phantom Train Car 7 Left Cabin
    1543: {0x17e: True},  # Phantom Train Car 7 Right Cabin interior # 0x17E ON, NOT CLEARED!

    # Cyan Dream, Train (NPCs for jumping animation).  Not needed.
    #478: {0x543: True},
    #479: {0x543: True},
    #480: {0x543: True},
    #481: {0x543: True},

    # Cyan Dream, Caves exit (NPCs for bridge animation)
    860: {0x545: True},
    861: {0x545: True},

    # Cyan Dream, savepoint room (from door, show savepoint; from drop don't)
    2073: {0x548: False},
    443: {0x548: True},

    # Cyan Dream, Wrexsoul room (NPCs)
    456: {0x548: True},

    # Cave on the Veldt, Relm/shadow NPC
    988: {0x552: True},
    991: {0x552: True},

    # Owzer's Basement Chadarnook Room, Owzer & Relm NPCs
    591: {0x488: True, 0x487: True},

    # Phoenix Cave return to Falcon, unset warp bit
    1554: {event_bit.PHOENIX_CAVE_WARP_OPTION: False},

}

room_require_event_bit = {
    # Narshe WoB NPC bits
    16: {npc_bit.STORES_NARSHE: True, npc_bit.WEAPON_ELDER_NARSHE: False, npc_bit.WEAPON_ROOM_ESPER_NARSHE: False},
    21: {npc_bit.STORES_NARSHE: True, npc_bit.WEAPON_ELDER_NARSHE: False, npc_bit.WEAPON_ROOM_ESPER_NARSHE: False}, # north entrance from caves

    # Narshe WoR NPC bits
    34: {npc_bit.STORES_NARSHE: False, npc_bit.WEAPON_ELDER_NARSHE: True, npc_bit.WEAPON_ROOM_ESPER_NARSHE: True},
    39: {npc_bit.STORES_NARSHE: False, npc_bit.WEAPON_ELDER_NARSHE: True, npc_bit.WEAPON_ROOM_ESPER_NARSHE: True}, # north entrance from caves

    # Mobliz WoB NPC bits
    228: {npc_bit.MOBLIZ_CITIZENS: True, npc_bit.MOBLIZ_SOLDIERS_LETTER: True},

    # Mobliz WoR NPC bits
    229: {npc_bit.MOBLIZ_CITIZENS: False, npc_bit.MOBLIZ_SOLDIERS_LETTER: False},

    # Figaro Castle WoB NPC & event bits:
    68: {event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE: False,
         npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE: False,
         npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE: False,
         npc_bit.LONE_WOLF_FIGARO_CASTLE: True,
         npc_bit.PRISONERS_FIGARO_CASTLE: True,
         npc_bit.PRISON_GUARD_FIGARO_CASTLE: True,
         event_bit.GOT_FALCON: False},  # Required to not go to AC in WOB

    # Figaro Castle WoR NPC & event bits:
    '68R': {event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE: True,
            npc_bit.LONE_WOLF_FIGARO_CASTLE: False,
            npc_bit.PRISONERS_FIGARO_CASTLE: False,
            event_bit.GOT_FALCON: True},  # Required to go to AC
            # Other bits must be set when entering south figaro cave, but only if not TENTACLE_DEFEATED:
            #if not TENTACLE_DEFEATED:
            #   field.SetEventBit(npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE),
            #   field.SetEventBit(npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE),
            #   field.ClearEventBit(npc_bit.PRISON_GUARD_FIGARO_CASTLE),

    # Opera House WoB NPC & event bits:
    319: {npc_bit.MAN_AT_COUNTER_OPERA: False,
          npc_bit.IMPRESARIO_OPERA_PANICKING: False,
          npc_bit.IMPRESARIO_OPERA_LOBBY: False,
          npc_bit.IMPRESARIO_OPERA_SITTING: True,
          npc_bit.DRAGON_OPERA_HOUSE: False},
          # Other bits must be set/cleared depending on FINISHED_OPERA_DISRUPTION:
          #if not FINISHED_OPERA_DISRUPTION:
          #   field.ClearEventBit(event_bit.BEGAN_OPERA_DISRUPTION),
          #   field.SetEventBit(npc_bit.ULTROS_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT1_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT2_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT3_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT4_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.RAT5_OPERA_CEILING),
          #   field.SetEventBit(npc_bit.CEILING_DOOR_OPERA_HOUSE),
          #   field.SetEventBit(npc_bit.DANCING_COUPLE1_OPERA),
          #   field.SetEventBit(npc_bit.DANCING_COUPLE2_OPERA),
          #   field.SetEventBit(npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING),

    '319r': {npc_bit.MAN_AT_COUNTER_OPERA: True,
             npc_bit.IMPRESARIO_OPERA_LOBBY: True,
             npc_bit.IMPRESARIO_OPERA_SITTING: False,
             event_bit.BEGAN_OPERA_DISRUPTION: True,
             npc_bit.ULTROS_OPERA_CEILING: False,
             npc_bit.RAT1_OPERA_CEILING: False,
             npc_bit.RAT2_OPERA_CEILING: False,
             npc_bit.RAT3_OPERA_CEILING: False,
             npc_bit.RAT4_OPERA_CEILING: False,
             npc_bit.RAT5_OPERA_CEILING: False,
             npc_bit.CEILING_DOOR_OPERA_HOUSE: False,
             npc_bit.DANCING_COUPLE1_OPERA: False,
             npc_bit.DANCING_COUPLE2_OPERA: False,
             npc_bit.FIGHTING_SOLDIERS_OPERA: False,
             npc_bit.FIGHTING_SOLDIERS_OPERA_CEILING: False},
             #if not DEFEATED_OPERA_HOUSE_DRAGON:
             #    field.ClearEventBit(npc_bit.IMPRESARIO_OPERA_LOBBY),
             #    field.SetEventBit(npc_bit.IMPRESARIO_OPERA_PANICKING),
             #    field.SetEventBit(npc_bit.DRAGON_OPERA_HOUSE),

    # Thamasa inn NPC bits for Interceptor, Strago
    #447: {npc_bit.ATTACK_GHOSTS_PHANTOM_TRAIN: False},  # Do we need to deconflict this?
    # No, just change entrance event to delete these NPCS.  We don't use them.

}

# push room required event bits to door required event bits
from data.rooms import room_data
for rb in room_require_event_bit.keys():
    for db in room_data[rb][0]:
        # door entrances
        require_event_bit[db] = room_require_event_bit[rb]


def minecart_event_mod(src, src_end):
    # Special event for outro of minecart ride: return to Vector if cranes have been defeated.
    # C0    If ($1E80($06B) is set), branch to $(new event) that sends you to Vector map instead
    # C0    If ($1E80($069) is set), branch to $(new event) that sends you to MTek3 Vector map without animation
    from memory.space import Write, Bank
    from event.event import direction
    go_to_vector = (
        field.LoadMap(0xf2, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.FadeInScreen(),
        field.Return()
    )
    go_to_mtek3_vector = (
        field.LoadMap(0xf0, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
        field.FadeInScreen(),
        field.Return()
    )
    space = Write(Bank.CC, go_to_vector, "Return to Vector")
    patch1 = branch_code(space.start_address, 0)
    space = Write(Bank.CC, go_to_mtek3_vector, "Return to MTek3 Vector")
    patch2 = branch_code(space.start_address, 0)
    src = src[:-1] + [0xc0, 0x6b, 0x80] + patch1 + [0xc0, 0x69, 0x80] + patch2 + src[-1:]
    return src, src_end


# def tritoch_event_mod(src, src_end):
#     new_src = [0xc0, 0x9e, 0x2, 0xb3, 0x5e, 0x0]  # field.BranchIfEventBitClear(event_bit.GOT_TRITOCH, 0xa5eb3),
#
#     if src[6] == 0xc0:
#         # Special event for cliff jump behind Tritoch: reproduce the modified WC event for character gating
#         atma_event_addr = code_address(src[10:13]) + EVENT_CODE_START
#         # atma_src = rom.ROM.get_bytes(atma_event_addr, 0xed-0xd8)
#         new_src += [0xc0, 0xed, 0x2] + branch_code(atma_event_addr, 17) # field.BranchIfEventBitClear(0x2ed, 0xc74e9)
#
#     new_src += [0x4b, 0x3b, 0xa] + [  # display text box $a3b
#                 0xb6] + [0x0, 0x0, 0x0] + [0xf8, 0x37, 0x2] + [   # Yes --> branch to (placeholder), No --> branch to step back;
#                 0xfe] + src[23:]  # return; source code for jumping animation
#
#     return new_src, src_end


def branch_code(addr, offset):
    return [(offset + addr) % 0x100, ((offset + addr) >> 8) % 0x100, ((offset + addr - EVENT_CODE_START) >> 16) % 0x100]


def code_address(code):
    return (code[2] << 16) + (code[1] << 8) + code[0]


event_address_patch = {
    # Jump into Umaro's Cave: update branched event address.  Slightly risky search for 1st instance of 0xb6.
    ### Not used with JMP method ###
    #2010: lambda src, addr: src[:src.index(0xb6)+1] + branch_code(addr, 23) + src[src.index(0xb6)+4:],

    # Magitek factory Room 1 conveyor into room 2:
    #   At CC/7658 (+7), branch-if-clear [0xc0, ] to CC/7666 (+21)
    #   Paired event starts at CC/765F (+14).
    ### Not needed if using JMP method ###
    #2022: lambda src, addr: src[:10] + branch_code(addr, 21) + src[13:],

    # Magitek factory Room 2 conveyor into pit room:
    #   At CC/756C (+7), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   At CC/757A (+21), branch-if-clear [0xc0, ] to CC/7588 (+35)
    #   Paired events start at CC/7573 (+14) and CC/7581 (+28).
    ### Not needed if using JMP method ###
    #2025: lambda src, addr: src[:10] + branch_code(addr, 35) + src[13:24] + branch_code(addr, 35) + src[27:]

}

# We define "multi events" as multiple event tiles that are all logically the same exit and partially share
# the same code.  The event tile with the earliest address should be the key event, others will be referenced to it.
### NOTE: multi_events no longer used!  Instead, just patch the relevant event scripts to all branch to the main transition.
### e.g. events.leteriver.door_rando_mod()

multi_events = {
    #2022: ['2022a'],  # Magitek factory room 1 conveyor belt  ### Not needed if using JMP method
    #2025: ['2025a', '2025b'],  # Magitek factory room 1 conveyor belt ### Not needed if using JMP method ###

    #2035: ['2035a', '2035b'],  # Lete River section 1 branching code

    #1502: ['1502a'],  # Figaro Castle WoB entrance tiles
    #1503: ['1503c'],  # Figaro Castle WoB (kohlingen) entrance tiles
    #1505: ['1505a'],   # Vector entrance tiles WoB

    #1507: ['1507a'],  # Figaro Castle WoR entrance tiles
    #1508: ['1508a']   # Figaro Castle WoR (kohlingen) entrance tiles
}

# NOTES ON JUMP/CALL vs REWRITE:
# 1. If we use jumping/calling instead of writing, we are probably much efficient...
# --> UNLESS we can reclaim all the original event space, in which case rewriting would be much more efficient because
# --> we can reclaim all the NOP space!
# 2. Using jumping/calling removes the need for event_address_patch and the Magitek use of multi_events (2 in, 1 out)
# 3. Using jumping/calling adds a need for Lete river use of multi_events (1 in, 3 out).

# Some events need to be modified by different parts of the code before being written.  We identify them here by where
# the event script starts in the code.
# key_events = [0xc7f43,  # Cid's elevator ride
#              0xc8022   # Cid's minecart ride
#              ]

# Notes:
# 2009.  The transition out of Umaro's cave and back to Narshe should load the Narshe music, but instead just keeps
#   playing the Umaro music when randomized. I am not sure why this happens: look at the post-transition code for 2009?
#   Maybe something having to do with the door exit?
#
#   Music is going to be tricky in general: should we always load music when changing between maps with different
#   default music?  We probably want different behavior for different cases.
#       How do we figure out what the default music is for an area?
#
# 2010b. The transition to the correct location happens now, but the fade behavior is weird and the music is not loaded.
#   There's a momentary fade up on the cliff, fade down, transition, and then land animation & sound effect, no music.
#   Here's the code in the 2010 post-transition:
#       CC/3829: 6B    Load map $0119 (Umaro's Cave first room), place party at (14, 55), facing down
#       CC/382F: F4    Play sound effect 186
#       CC/3831: B2    Call subroutine $CCD9A6  <-- standard Umaro's cave trapdoor animation
#       CC/3835: 92    Pause for 30 units
#       CC/3836: F0    Play song 48 (Umaro), (high bit clear), full volume:  <-- "[0xf0, 0x30]" = [240, 48]
#       CC/3838: FE    Return
#   Fade behavior is weird because this is a 6B call instead of a 6A call; all the other transitions are 6A's
#       6A is "Fade out & load new map"; 6B is "Load new map assuming fadeout already happened."
#       They have the same parameters - so we can get around this by moving the split one byte later:
#       the original type of transition is preserved but destination is modified. IMPLEMENTED/NOT TESTED.
#   For the music, just patch in [0xf0, 0x30] just before the return bit.  IMPLEMENTED/NOT TESTED

# 2010. The Narshe Peak WoR jump into Umaro's cave event has a branch point (B6) at CC/37F0 (byte 10).  Code is:
#       B6 FE 37 02 F8 37 02 = (branch cmd) (choice 1 address bytes [x3]) (choice 2 address bytes [x3])
#   Choice address bytes are in order [low byte, mid byte, hi byte]; the address is also relative to offset $CA0000
#   so this translates as:  (Branch to) (1. CC/37FE [enter cave]) (2. CC/37F8 [return])
#   since we are copying the entire event with both branches, we need to patch these bytes with updated addresses:
#   specifically, we need to take them to e.g. 0C37FE + (New Address) - 0c37e7.  Also subtract 0A0000 (offset).