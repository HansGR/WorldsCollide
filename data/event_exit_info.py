# event exit information:  Event_ID:  [original address, event bit length, split point, transition state, description, location]
#   transition state = [is_chararacter_hidden, is_song_override_on, is_screen_hold_on, is_on_raft]
#   location = [map_id, x, y]
#   None = not implemented
event_exit_info = {
    # UMARO'S CAVE
    2001: [0xcd8d4, 34, 24, [True, True, False, False], 'Umaro Cave 1st Room trapdoor top', [281, 11, 53], 'JMP'],
    2002: [0xcd8b2, 34, 24, [True, True, False, False], 'Umaro Cave 1st Room trapdoor left', [281, 10, 54], 'JMP'],
    2003: [0xcd93a, 45, 35, [True, True, False, False], 'Umaro Cave Switch Room trapdoor to 2nd Room', [281, 31, 9], 'JMP' ],
    2004: [0xcd967, 45, 35, [True, True, False, False], 'Umaro Cave Switch Room trapdoor to Boss Room', [281, 40, 12], 'JMP' ],
    2005: [0x00000, 0, 0, [None, None, None, None], 'Umaro Cave 2nd Room west trapdoor logical exit A', [282, 33 ,26], None],
    2006: [0x00000, 0, 0, [None, None, None, None], 'Umaro Cave 2nd Room west trapdoor logical exit B', [282, 33 ,26], None],
    2056: [0xcd918, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room west trapdoor', [282, 33, 26], 'JMP' ],
    2007: [0x00000, 0, 0, [None, None, None, None], 'Umaro Cave 2nd Room east trapdoor logical exit A', [282, 14 ,30], None],
    2008: [0x00000, 0, 0, [None, None, None, None], 'Umaro Cave 2nd Room east trapdoor logical exit B', [282, 14 ,30], None],
    2057: [0xcd8f6, 34, 24, [True, True, False, False], 'Umaro Cave 2nd Room east trapdoor', [282, 14, 30], 'JMP' ],
    2009: [0xc3839, 50, 1, [False, False, False, False], 'Umaro Cave Boss Room trapdoor to Narshe', [283, 57, 7], 'JMP' ],
    2010: [0xc37e7, 82, 67, [True, True, True, False], 'Narshe Peak WoR entrance to Umaros Cave', [35, 9, 12], 'JMP' ],

    # ESPER MOUNTAIN
    2011: [0xbee80, 15, 0, [None, None, None, None], 'Esper Mtn 2nd Room bridge jump west', [0x177, 36, 53], None ],
    # forced connection, no mod
    2012: [0xbee71, 15, 0, [None, None, None, None], 'Esper Mtn 2nd Room bridge jump middle', [0x177, 39, 54], None ],
    # forced connection, no mod
    2013: [0xbee62, 15, 0, [None, None, None,None], 'Esper Mtn 2nd Room bridge jump east', [0x177, 47, 53], None ],
    # forced connection, no mod
    2014: [0xbee8f, 47, 30, [False, False, True, False], 'Esper Mtn Pit Room South trapdoor', [0x177, 11, 51], 'JMP' ],
    2015: [0xbeebe, 46, 30, [False, False, True, False], 'Esper Mtn Pit Room North trapdoor', [0x177, 12, 46], 'JMP'],
    2016: [0xbeeec, 47, 30, [False, False, True, False], 'Esper Mtn Pit Room East trapdoor', [0x177, 17, 49], 'JMP' ],

    # OWZER'S MANSION
    2017: [0xb4b86, 47, 1, [False, False, False, False], 'Owzers Mansion switching door left',  [0x0CF, 90, 50], 'JMP'],
    #2018: [0xb4b86, 47, 1, [False, False, False, False], 'Owzers Mansion switching door right', [0x0CF, 92, 50], 'JMP'],
    # same destination, same event!  When handling as JMP, this is not included a 2nd time (shared_oneways).
    2019: [0xb4bb5, 53, 3, [False, False, False, False], 'Owzers Mansion behind switching door exit', [0x0CF, 85, 50], 'JMP'],
    # set event bit 0x24c?
    2020: [0xb4c94, 13, 1, [False, False, False, False], 'Owzers Mansion floating chest room exit', [0x0CF, 76, 51], 'JMP'],
    2021: [0xb4bea, 51, 1, [False, False, False, False], 'Owzers Mansion save point room oneway', [0x0CF, 86, 38], 'JMP'],

    # MAGITEK FACTORY
    2022: [0xc7651, 49, 29, [False, False, False, False], 'Magitek factory 1 conveyor to Mtek-2 top tile', [0x106, 22, 53], 'JMP'],
    # '2022a': [0xc765f, 0, 0, [None, None, None, None], 'Magitek factory 1 conveyor to Mtek-2 bottom tile', [0x106, 22, 54]],
    # same exit as above; requires address patch & tile edit if using rewrite method.
    2023: [0xc7682, 37, 0, [None, None, None, None], 'Magitek factory platform elevator to Mtek-1', [0x106, 10, 54], None],
    2024: [0xc7905, 50, 10, [False, False, False, False], 'Magitek factory 2 pipe exit loop', [0x107, 49, 48], 'JMP'],
    2025: [0xc7565, 86, 58, [True, False, False, False], 'Magitek factory 2 conveyor to pit left tile', [0x107, 36, 44], 'JMP'],
    #'2025a': [0xc7581, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit mid tile', [0x107, 37, 44]],
    #'2025b': [0xc7573, 0, 0, [None, None, None, None], 'Magitek factory 2 conveyor to pit right tile', [0x107, 38, 44]],
    # same exits as above; requires address patch & tile edit if using rewrite method.
    2026: [0xc75f6, 91, 39, [False, False, False, False], 'Magitek factory pit hook to Mtek-2', [0x108, 6, 6], 'JMP'],
    2027: [0xc7f43, 217, 131, [False, False, False, False], 'Magitek factory lab Cid''s elevator', [0x112, 20, 13], 'JMP'],
    # bit $1E80($068) set by switch (0c7a60)?  Look for conflicts with event patch code.
    2028: [0xc8022, 309, 152, [False, True, False, False], 'Magitek factory minecart start event', [0x110, 'NPC', 0], 'JMP'],
    # NPC #0 on this map. Not an event tile.  Started by talking to Cid.  Position: # [0x110, 9, 51]

    # CAVE TO THE SEALED GATE
    2029: [0xb3176, 84, 0, [None, None, None, None], 'Cave to the Sealed Gate grand staircase', [0x180, 71, 15], None],
    # Grand staircase event
    2030: [0xb33c9, 32, 0, [None, None, None, None], 'Cave to the Sealed Gate switch bridges', [0x180, 104, 17], None],
    # Switch bridge events
    2031: [0xb2a9f, 7, 1, [False, False, False, False], 'Cave to the Sealed Gate shortcut exit', [0x180, 5, 43], 'JMP'],  # Shortcut exit

    # ZOZO (WORLD OF BALANCE)
    2032: [0xa963d, 22, 0, [None, None, None, None], 'Zozo hook descent from building', [0x0DD, 35, 41], None],
    2033: [0x00000, 0, 0, [None, None, None, None], 'Zozo line of walking guys (logical)', [0x0E1, 0, 0], None],
    2061: [0x00000, 0, 0, [None, None, None, None], 'Zozo clock room left to right WOB (logical)', [0x0E1, None, None], None], # logical no randomize
    2062: [0x00000, 0, 0, [None, None, None, None], 'Zozo clock room right to left WOB (logical)', [0x0E1, None, None], None], # logical, no randomize
    2063: [0x00000, 0, 0, [None, None, None, None], 'Zozo clock room left to right WOR (logical)', [0x0E1, None, None], None], # logical no randomize
    2064: [0x00000, 0, 0, [None, None, None, None], 'Zozo clock room right to left WOR (logical)', [0x0E1, None, None], None], # logical, no randomize

    # LETE RIVER
    2034: [0xb059f, 151, 146, [False, False, False, True], 'Lete River start', [0x071, 31, 51], 'JMP'],
    2035: [0xb0636, 193, 182, [False, False, False, True], 'Lete River Section 1', [0x071, None, None], 'JMP'],
    '2035a': [0xb06f7, 101, 90, [False, False, False, True], 'Lete River Section 1 (LEFT)', [0x071, None, None], 'JMP'],
    '2035b': [0xb07c0, 106, 95, [False, False, False, True], 'Lete River Section 1 (RIGHT)', [0x071, None, None], 'JMP'],
    2036: [0xb051c, 64, 52, [False, False, False, True], 'Lete River Cave 1', [0x072, 20, 24], 'JMP'],
    2037: [0xb07cc, 157, 145, [False, False, False, True], 'Lete River Section 2', [0x071, None, None], 'JMP'],
    2038: [0xb055c, 67, 55, [False, False, False, True], 'Lete River Cave 2', [0x072, 6, 15], 'JMP'],
    2039: [0xb0869, 229, 108, [False, False, False, True], 'Lete River Section 3 + boss', [0x071, None, None], 'JMP'],

    # ZONE EATER
    # For Zone Eater entrance and exit, we are in world map operations, so we can't use the normal state mod codes.
    # Instead, we make ZoneEater send you to the switchyard [0x005, 2040 % 128, 2040 // 128] and place an event tile
    # there that just does the load command.  That event tile can then be modified by Transitions()
    #2040: [0xa008f, 7, 1, [False, False, False, False], 'Zone Eater Engulf', [0x001, 'JMP', 0] ],  # In battle event
    2040: [None, 7, 1, [False, False, False, False], 'Zone Eater Engulf', [0x005, 2040 % 128, 2040 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2041: [0xb7d9d, 33, 27, [False, False, False, False], 'Zone Eater Exit', [0x114, 5, 6], 'JMP'],  # Goes to Switchyard tile
    2042: [0xb8251, 35, 18, [False, False, False, False], 'Zone Eater leprechaun bump', [0x114, 'NPC', 0], 'JMP' ], # Shared code, 3 NPCs
    2043: [0xb8062, 0, 0, [None, None, None, None], 'Zone Eater pit switch exit (logical)', [0x114, 46, 17], None],

    # SERPENT TRENCH
    2044: [0xbc84d, 45, 39, [False, False, False, False], 'Cliff jump to Serpent Trench', [0x0A8, 8, 11], 'JMP'],
    #2044a: [0x1c84d, 7, 1, [False, False, False, False], 'Cliff jump to Serpent Trench tile 2', [0x0A8, 9, 11], 'JMP'],  # Duplicate, not needed with JMP
    2045: [None, 7, 1, [False, False, False, False], 'Serpent Trench #1 to cave', [0x005, 2045 % 128, 2045 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2046: [0x00000, 0, 0, [None, None, None, None], 'Serpent Trench #1 continue to #2', [0x002, 0, 0], None],  # logical exit
    2047: [0xa8c41, 7, 1, [False, False, False, False], 'Serpent Trench Cave 1 to Serpent Trench #2', [0x0af, 43, 4], 'JMP'], # Goes to switchyard.
    2048: [None, 7, 1, [False, False, False, False], 'Serpent Trench #2 to cave 2a', [0x005, 2048 % 128, 2048 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2049: [0x00000, 0, 0, [None, None, None, None], 'Serpent Trench #2 continue to #3', [0x002, 0, 0], None],  # logical exit
    2050: [0xa8cae, 13, 7, [False, False, False, False], 'Serpent Trench Cave 2b to Cave 2c', [0x0af, 49, 42], 'JMP'],
    2051: [0xa8c94, 7, 1, [False, False, False, False], 'Serpent Trench Cave 2c to Serpent Trench #3', [0x0af, 6, 36], 'JMP'], # Goes to switchyard.
    2052: [None, 7, 1, [False, False, False, False], 'Serpent Trench #3 to SWITCHYARD', [0x005, 2052 % 128, 2052 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    2053: [None, 11, 1, [False, False, False, False], 'SWITCHYARD to Nikeah (forced)', [0x005, 2053 % 128, 2053 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]

    # BURNING HOUSE
    2054: [0xbdcc7, 7, 1, [False, False, False, False], 'Thamasa Inn to Burning House', [0x15A, 'NPC', 0], 'JMP' ], # Talk to the innkeeper.  requires JMP.
    2055: [0x00000, 0, 0, [None, None, None, None], 'Burning House after boss to Inn', [0x15F, None, None], None], # logical? no randomize?

    # DARYL'S TOMB
    2058: [0xa435d, 12, 5, [False, False, False, False], 'Darills Tomb Quick Exit to World Map', [0x12B, 100, 7], 'JMP' ],  # Goes to Switchyard tile
    2059: [0x00000, 0, 0, [None, None, None, None], 'Darills Tomb Turtle 2 left to right (logical)', [0x12C, None, None], None], # logical no randomize
    2060: [0x00000, 0, 0, [None, None, None, None], 'Darills Tomb Turtle 2 right to left (logical)', [0x12C, None, None], None], # logical, no randomize

    # PHANTOM TRAIN
    2065: [0xba8f1, 309, 149, [False, False, False, False], 'Phantom Train Platform to Car 1', [0x08C, 72, 10], 'JMP' ],
    2066: [0xba709, 83, 32, [False, False, False, False], 'Phantom Train Car 2 outside trapdoor', [0x08E, 56, 5], 'JMP'],  # Who knew about this ?!?
    2067: [0x00000, 0, 0, [False, False, False, False], 'Phantom Train roof jump cutscene (logical)', [0x08E, 56, 5], 'JMP'],  #
    2068: [0xbba0c, 9, 3, [False, False, False, False], 'Phantom Train smokestack switch & boss', [0x08D, 31, 7], 'JMP'],  # tile points to 0xbb9d4

    # EVENT TILES that behave as if they are doors:
    #       WOB: Imperial Camp; Figaro Castle (@ Figaro & Kohlingen); Thamasa; Vector; Cave to SF south entrance
    #       WOR: Figaro Castle (@ Figaro & Kohlingen); Solitary Island Cliff
    #       Other: Opera House Lobby, Mobliz Outside, ...
    # To do this: must add index to map_exit_extra.
    1501: [0xb0bb7, 0, 0, [None, None, None, None], 'Imperial Camp WoB', [0x000, 179, 71], None],
    1502: [0xa5eb5, 0, 0, [None, None, None, None], 'Figaro Castle WoB', [0x000, 64, 76], None],
    '1502a': [0xa5eb5, 0, 0, [None, None, None, None], 'Figaro Castle WoB 2', [0x000, 65, 76], None],
    1503: [0xa5ec2, 0, 0, [None, None, None, None], 'Figaro Castle WoB (kohlingen)', [0x000, 30, 48], None],
    '1503c': [0xa5ec2, 0, 0, [None, None, None, None], 'Figaro Castle WoB (kohlingen) 2', [0x000, 31, 48], None],
    1504: [0xbd2ee, 0, 0, [None, None, None, None], 'Thamasa WoB', [0x000, 250, 128] ],  # wtf is this event doing?
    1505: [0xa5ecf, 14, 7, [None, None, None, None], 'Vector entrance event tile', [0x000, 120, 187], None],
    '1505a': [0xa5ecf, 14, 7, [None, None, None, None], 'Vector entrance event tile 2', [0x000, 121, 187], None],
    #1506: [0xa5ee3, 20, 14, [False, False, False, False], 'Cave to South Figaro South Entrance WoB', [0x000, 75, 102], None],
    1506: [None, 7, 1, [False, False, False, False], 'Cave to South Figaro South Entrance WoB', [0x005, 1506 % 128, 1506 // 128], 'JMP'],  # Switchyard tile: [x,y] = [ID % 128, ID // 128]
    1507: [0xa5f0b, 0, 0, [None, None, None, None], 'Figaro Castle WoR', [0x001, 81, 85], None],
    '1507a': [0xa5f0b, 0, 0, [None, None, None, None], 'Figaro Castle WoR 2', [0x001, 82, 85], None],
    1508: [0xa5f18, 0, 0, [None, None, None, None], 'Figaro Castle WoR (kohlingen)', [0x001, 53, 58], None],
    '1508a': [0xa5f18, 0, 0, [None, None, None, None], 'Figaro Castle WoR (kohlingen) 2', [0x001, 54, 58], None],
    1509: [0xa5f39, 0, 0, [None, None, None, None], 'Solitary Island cliff entrance', [0x001, 73, 231], None],
    1510: [0xb80a9, 15, 9, [False, False, False, False], 'Zone Eater Digestive Tract east', [0x118, 54, 53], 'JMP'],
    1511: [0xb809a, 15, 9, [False, False, False, False], 'Zone Eater Digestive Tract west', [0x118, 26, 54], 'JMP'],
    1512: [0xa422e, 43, 35, [False, False, False, False], 'Daryls Tomb turtle room south exit', [0x12b, 56, 14], 'JMP'],
    1513: [0xa5ef7, 20, 14, [False, False, False, False], 'Cave to South Figaro North WOB', [0x047, 10, 48], 'JMP'],
    #'1513a': [0xa5ef7, 20, 14, [False, False, False, False], 'Cave to South Figaro North WOB 2', [0x047, 11, 48], 'JMP']

    1514: [0xba7e4, 7, 1, [False, False, False, False], 'Phantom Train Car 3 South Exit', [0x091, 26, 11], 'JMP'],  # Note: just including event addresses for map loads.  Ignoring all switchyard code.
    1515: [0xba78b, 7, 1, [False, False, False, False], 'Phantom Train Car 1 Left Exit', [0x091, 1, 7], 'JMP'],
    #'1515a': [0xbaac4, 143, 137, [False, False, False, False], 'Phantom Train Car 1 Left Exit 2', [0x091, 1, 8], 'JMP'],
    1516: [0xba778, 7, 1, [False, False, False, False], 'Phantom Train Car 1 Right Exit', [0x091, 30, 7], 'JMP'],
    #'1516a': [0xbaac4, 143, 137, [False, False, False, False], 'Phantom Train Car 1 Right Exit 2', [0x091, 30, 8], 'JMP'],
    #1517: [0xba5f9, 21, 15, [False, False, False, False], 'Phantom Train Car 1 South Door Outside', [0x08E, 72, 8], 'JMP'],  # These will need special treatment:
    1518: [0xba60e, 21, 15, [False, False, False, False], 'Phantom Train Car 1 Right Door Outside', [0x08E, 74, 8], 'JMP'],  # They set event bits that are used by the interior
    1519: [0xba623, 21, 15, [False, False, False, False], 'Phantom Train Car 1 Left Door Outside', [0x08E, 67, 8], 'JMP'],   # switchyard exit tiles to decide on destination.
    1520: [0xba6e5, 18, 11, [False, False, False, False], 'Phantom Train Car 2 Right Door Outside', [0x08E, 58, 8], 'JMP'],  # These event bits need to be set upon entry.
    1521: [0xba6f7, 18, 11, [False, False, False, False], 'Phantom Train Car 2 Left Door Outside', [0x08E, 51, 8], 'JMP'],
    1522: [0xba67d, 23, 17, [False, False, False, False], 'Phantom Train Car 3 South Door Outside', [0x08E, 41, 8], 'JMP'],

    1523: [0xba84b, 7, 1, [False, False, False, False], 'Phantom Train Car 2 Left Exit', [0x091, 1, 7], 'JMP'],
    1524: [0xba842, 7, 1, [False, False, False, False], 'Phantom Train Car 2 Right Exit', [0x091, 30, 7], 'JMP'],

    1525: [0xba638, 7, 1, [False, False, False, False], 'Phantom Train Car 4 Right Door Outside', [0x08E, 10, 8], 'JMP'],  # on map 0x08E
    1526: [0xba647, 7, 1, [False, False, False, False], 'Phantom Train Car 4 Right Door Outside no caboose', [0x08D, 116, 8], 'JMP'],  # on map 0x08D
    1527: [0xba7a1, 7, 1, [False, False, False, False], 'Phantom Train Car 4 Right Exit', [0x095, 31, 7], 'JMP'],  # 0xba792

    1528: [0xba656, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Door Outside', [0x08D, 82, 8], 'JMP'],
    1529: [0xba665, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Left Door Outside', [0x08D, 75, 8], 'JMP'],
    1530: [0xba676, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Door Outside', [0x08D, 66, 8], 'JMP'],
    1531: [0xba69e, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Left Door Outside', [0x08D, 59, 8], 'JMP'],
    1532: [0xba6a5, 24, 7, [False, False, False, False], 'Phantom Train Engine Door Outside', [0x08D, 38, 8], 'JMP'], # --> 0x92, 8, 12

    1533: [0xba7bf, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit', [0x097, 26, 8], 'JMP'],  # map 0x097 & 0x17E clear
    #'1533a': [0xba7bf, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 26, 9], 'JMP'],
    1534: [0xba7d2, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Left Exit', [0x097, 1, 8], 'JMP'],
    #'1534a': [0xba7d2, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 1, 9], 'JMP'],
    1535: [0xba6c3, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Cabin', [0x097, 19, 7], 'JMP'],  # --> 0x99, 8, 28
    1536: [0xba6d0, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Left Cabin', [0x097, 9, 7], 'JMP'],    # --> 0x99, 23, 11
    1537: [0xba81e, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Cabin interior exit', [0x099, 8, 29], 'JMP'],  # Not shared. --> 0x97, 19, 9. Siegfried room?
    1538: [0xba82b, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Left Cabin interior exit', [0x099, 23, 12], 'JMP'],  # --> 0x97, 9, 9. 0x17E OFF!

    1539: [0xba7db, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Exit', [0x097, 26, 8], 'JMP'],  # map 0x097 & 0x17E set
    #'1539a': [0xba7bf, 7, 1, [False, False, False, False], 'Phantom Train Car 6 Right Exit 2', [0x097, 26, 9], 'JMP'],
    1540: [0xba801, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Left Exit', [0x097, 1, 8], 'JMP'],
    #'1540a': [0xba801, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Exit 2', [0x097, 1, 9], 'JMP'],
    1541: [0xba6d7, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Cabin', [0x097, 19, 7], 'JMP'],  # --> 0x99, 23, 11
    1542: [0xba6de, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Left Cabin', [0x097, 9, 7], 'JMP'],    # --> 0x99, 23, 28
    1543: [0xba832, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Right Cabin interior exit', [0x099, 23, 12], 'JMP'],  # --> 0x97, 19, 9.  0x17E ON, NOT CLEARED!
    1544: [0xba839, 7, 1, [False, False, False, False], 'Phantom Train Car 7 Left Cabin interior exit', [0x099, 23, 29], 'JMP'],  # Not shared. --> 0x97, 9, 9.  MIAB room.

    1545: [0xba80e, 7, 1, [False, False, False, False], 'Phantom Train Locomotive interior exit', [0x092, 8, 13], 'JMP'],  # Not shared. --> 0x97, 9, 9.  MIAB room.
}
# Notes:
#   1. is_screen_hold_on is False for Umaro's Cave trapdoor events, but they all include a hold screen / free screen
#       pair after the transition, so it technically does not need to be patched in for entrances.  It also doesn't need
#       to be patched in for exits, so the value shouldn't be "True" either.  If there were a value for which both
#       "i" and "not i" were false, I would use it here.
#   2. Currently choosing to randomize destination of mine cart event.
#       Talking to Cid always starts minecart event, but destination can take you elsewhere
#       What happens with MTek3 prize?  Is it triggered by minecart, or by entering Vector?

from instruction.event import EVENT_CODE_START
from instruction import field
import data.event_bit as event_bit

def set_locomotive_switches(bytes=True):
    # Set single event bit 0x03E to check when initiating smokestack event
    # CB/B9DC: C2    If ($1E80($185) [$1EB0, bit 5] is set) or ($1E80($186) [$1EB0, bit 6] is clear) or ($1E80($184) [$1EB0, bit 4] is clear), branch to $CBB9D0
    # CB/B9D0: <smokestack doesn't work>
    from memory.space import Write, Bank
    clear_pt_switches_bit = [
        field.ClearEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
        field.Return()
    ]
    space = Write(Bank.CB, clear_pt_switches_bit, "Clear PT switches bit")

    set_switches = [
        field.BranchIfAny([0x184, False, 0x185, True, 0x186, False], space.start_address),
        field.SetEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
        field.Return()
    ]
    if bytes:
        set_switches_bytes = []
        for f in set_switches:
            set_switches_bytes += [f.opcode] + f.args
        return set_switches_bytes
    else:
        return set_switches

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

    # Phantom Train shared map bit controls
    1543: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Clear bit 0x17E
    # Phantom Train set correct "switches" bit if leaving locomotive
    1545: lambda src, src_end: [src[:-1] + set_locomotive_switches(bytes=True) + src[-1:], src_end]
}


exit_door_patch = {
    # For use with maps.create_exit_event() and maps.shared_map_exit_event()

    # Owzer's Mansion doors
    586: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.
    587: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.

    # Cave to the sealed gate: force reset timers when leaving lava room
    1075: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # North door.
    1077: [field.Call(0xb2caa)],  # [0xb2, 0xaa, 0x2c, 0x01],  # South door.

    # Phantom Train shared map bit controls
    1543: [field.ClearEventBit(0x17E)],  # Clear bit 0x17E
    # Phantom Train set correct "switches" bit if leaving locomotive
    1545: set_locomotive_switches(bytes=False)

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
    1512: lambda src, src_end: [src[:-1] + [0xd4, 0xb6] + src[-1:], src_end],   # Turtle room south exit

    # Phantom Train: set the correct room bits when entering Cars 1, 2, 3:
    1515: lambda src, src_end: [src[:-1] + [0xd3, 0x7e, 0xd3, 0x80] + src[-1:], src_end],  # Phantom Train Car 1 Left Exit
    1516: lambda src, src_end: [src[:-1] + [0xd3, 0x7e, 0xd3, 0x80] + src[-1:], src_end],  # Phantom Train Car 1 Right Exit
    1523: lambda src, src_end: [src[:-1] + [0xd2, 0x7e, 0xd3, 0x80] + src[-1:], src_end],  # Phantom Train Car 2 Left Exit
    1524: lambda src, src_end: [src[:-1] + [0xd2, 0x7e, 0xd3, 0x80] + src[-1:], src_end],  # Phantom Train Car 2 Right Exit
    1514: lambda src, src_end: [src[:-1] + [0xd3, 0x7e, 0xd2, 0x80] + src[-1:], src_end],  # Phantom Train Car 3 South Exit

    1533: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Phantom Train Car 6 Right Exit # 0x17E clear
    1534: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Phantom Train Car 6 Left Exit
    1535: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Phantom Train Car 6 Right Cabin
    1536: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Phantom Train Car 6 Left Cabin
    1538: lambda src, src_end: [src[:-1] + [0xd3, 0x7e] + src[-1:], src_end],  # Phantom Train Car 6 Left Cabin interior

    1539: lambda src, src_end: [src[:-1] + [0xd2, 0x7e] + src[-1:], src_end],  # Phantom Train Car 7 Right Exit # 0x17E set
    1540: lambda src, src_end: [src[:-1] + [0xd2, 0x7e] + src[-1:], src_end],  # Phantom Train Car 7 Left Exit
    1541: lambda src, src_end: [src[:-1] + [0xd2, 0x7e] + src[-1:], src_end],  # Phantom Train Car 7 Right Cabin
    1542: lambda src, src_end: [src[:-1] + [0xd2, 0x7e] + src[-1:], src_end],  # Phantom Train Car 7 Left Cabin
    1543: lambda src, src_end: [src[:-1] + [0xd2, 0x7e] + src[-1:], src_end],  # Phantom Train Car 7 Right Cabin interior # 0x17E ON, NOT CLEARED!

}

entrance_door_patch = {
    # For use by maps.create_exit_event() and maps.shared_map_exit_event()
    # Daryl's Tomb: Move the turtles to the appropriate side.
    1512: [field.SetEventBit(event_bit.DARYL_TOMB_TURTLE1_MOVED)],   # Turtle room south exit
    782: [field.ClearEventBit(event_bit.DARYL_TOMB_TURTLE1_MOVED)],  # Turtle room north exit.
    793: [field.ClearEventBit(event_bit.DARYL_TOMB_TURTLE2_MOVED)],  # Water puzzle room top exit.
    794: [field.ClearEventBit(event_bit.DARYL_TOMB_TURTLE2_MOVED)],  # Water puzzle room bottom exit.
    795: [field.SetEventBit(event_bit.DARYL_TOMB_TURTLE2_MOVED)],    # Water puzzle room right exit.

    # Phantom Train: set the correct room bits for Cars 1, 2, 3:
    # Bits are cleared upon leaving the cars. Explicit is safer, though.
    1515: [field.ClearEventBit(0x17E), field.ClearEventBit(event_bit.PHANTOM_TRAIN_CAR_3)], # Phantom Train Car 1 Left Exit
    1516: [field.ClearEventBit(0x17E), field.ClearEventBit(event_bit.PHANTOM_TRAIN_CAR_3)], # Phantom Train Car 1 Right Exit
    1523: [field.SetEventBit(0x17E), field.ClearEventBit(event_bit.PHANTOM_TRAIN_CAR_3)], # Phantom Train Car 2 Left Exit
    1524: [field.SetEventBit(0x17E), field.ClearEventBit(event_bit.PHANTOM_TRAIN_CAR_3)], # Phantom Train Car 2 Right Exit
    1514: [field.ClearEventBit(0x17E), field.SetEventBit(event_bit.PHANTOM_TRAIN_CAR_3)], # Phantom Train Car 3 South Exit

    1533: [field.ClearEventBit(0x17E)],  # Phantom Train Car 6 Right Exit # 0x17E clear
    1534: [field.ClearEventBit(0x17E)],  # Phantom Train Car 6 Left Exit
    1535: [field.ClearEventBit(0x17E)],  # Phantom Train Car 6 Right Cabin
    1536: [field.ClearEventBit(0x17E)],  # Phantom Train Car 6 Left Cabin
    1538: [field.ClearEventBit(0x17E)],  # Phantom Train Car 6 Left Cabin interior

    1539: [field.SetEventBit(0x17E)],   # Phantom Train Car 7 Right Exit # 0x17E set
    1540: [field.SetEventBit(0x17E)],   # Phantom Train Car 7 Left Exit
    1541: [field.SetEventBit(0x17E)],   # Phantom Train Car 7 Right Cabin
    1542: [field.SetEventBit(0x17E)],   # Phantom Train Car 7 Left Cabin
    1543: [field.SetEventBit(0x17E)],   # Phantom Train Car 7 Right Cabin interior # 0x17E ON, NOT CLEARED!
}


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
multi_events = {
    #2022: ['2022a'],  # Magitek factory room 1 conveyor belt  ### Not needed if using JMP method
    #2025: ['2025a', '2025b'],  # Magitek factory room 1 conveyor belt ### Not needed if using JMP method ###

    2035: ['2035a', '2035b'],  # Lete River section 1 branching code

    1502: ['1502a'],  # Figaro Castle WoB entrance tiles
    1503: ['1503c'],  # Figaro Castle WoB (kohlingen) entrance tiles
    1505: ['1505a'],   # Vector entrance tiles WoB

    1507: ['1507a'],  # Figaro Castle WoR entrance tiles
    1508: ['1508a']   # Figaro Castle WoR (kohlingen) entrance tiles
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