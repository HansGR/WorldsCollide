"""Mode room-set (pool) definitions (ROM-free).

Split out of data/doors.py (rewrite Stage A milestone 3b) so the atlas
compiler and other ROM-free tooling can validate pool membership.
data/doors.py imports it back; behavior is unchanged.
"""

# Comment convention in the sets below: room ids trailing a `#` comment
# (e.g. "# South Figaro Cave WOB  102, 105,") are rooms deliberately
# EXCLUDED from that set — usually dead ends, rooms replaced by a
# root-/mapsafe variant, or rooms whose doors must stay vanilla.
ROOM_SETS = {
    'Umaro': [364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368, 'root-u'],
    'UpperNarshe_WoB': [19, 20, 22, 23, 53, 54, 55, 59, 60, 'root-unb'],
    'UpperNarshe_WoR': [37, 38, 40, 41, 42, 43, 44, 46, 47, 'root-unr'],
    'EsperMountain': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 'root-em'],
    # 495 IS included here (unlike the 'WoB' meta-set below): the -dre mapsafe
    # root ('root-em_mapsafe_each') protects the world-map entrance as door
    # 30044, paired with 495's entrance 1047 via map_shuffle_protected_doors.
    'EsperMountain_mapsafe': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 'root-em_mapsafe_each'],
    'OwzerBasement' : [277, 278, 279, 280, 281, 282, 283, 284, 'root-ob'],
    'MagitekFactory' : [345, 346, 347, 349, 351, 352, 353, 354, 355, '355a', 'root-mf'],
    'SealedGate' : [503, 504, '504a', 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 'root-sg'],
    'Zozo' : [294, 295, 296, 297, 298, 299, 300, 301, 302, '303a', '303b', 304, 305, 306, 307, 308, 309, 310, 311, 312,
              313, 'root-zb'],
    'Zozo-WOR' : ['294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r', 'root-zr', 'branch-mz'],
    #'Zozo-WOR_mapsafe' : ['294r', '295r', '296r-mapsafe', '301r', '305r', '306r', '307r', '308r', '309r', 'root-zr'],  # only used in -dre
    'Zozo-WOR_mapsafe' : ['294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r', 'root-zr', 'branch-mz_mapsafe'],  # only used in -dre
    'MtZozo' : [250, 251, 252, 253, 254, 255, 256, 'root-mz'],
    #'MtZozo_mapsafe' : [250, 251, 252, '253-mapsafe', 254, 255, 256],  # only used in -dre
    'MtZozo_mapsafe' : [250, 251, 252, 253, 254, 255, 256, 'root-mz_mapsafe'],  # only used in -dre
    'Lete' : ['LeteRiver1', 'LeteCave1', 'LeteRiver2', 'LeteCave2', 'LeteRiver3', 'root-lr'],
    'ZoneEater': [356, 357, 358, '358b', 359, '359b', 361, 362, 363, 'root-ze'],
    'SerpentTrench': ['241a', 246, '241b', '247a', '247b', '247c', '241c', '241d', 'root-st'],
    'BurningHouse': [457, 458, 459, 460, 461, 462, 463, 464, 465, 'root-bh'],
    'DarylsTomb': [378, 379, 380, 381, 382, 383, 384, 386, 387, 388, 389, 390, 391, 392, 393, 'root-dt'],
    #'DarylsTombMinimal': [379, 380, 383, 384, 386, 387, 389, 390, 391, 392, 'root-dt'],  # for testing
    'SouthFigaroCaveWOB': [100, 101, 102, 103, 104, 105, 'root-sfcb'],
    'SouthFigaroCaveWOB_mapsafe': [100, 101, 103, 104, 'root-sfcb-mapsafe'],  #  102, 105,
    'PhantomTrain': [201, 202, '203a', '203b', '203c', 204, '204b', '204c', 205, 206, '206a', '206b', 207, '207a',
                     '207b', 212, 213, '215a', '215b', 216, 220, 221, 'root-pt'],
    'CyansDream': [421, 422, 423, 424, 425, 426, 427, 428, 429, 208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
                  432, 433, 184, 185, 186, 187, 188, '188B', 189, 190, 191, 192, 193, 'root-cd'],
    'MtKolts': [145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 'root-mk'],
    'MtKolts_mapsafe': [146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 159, 160, 'root-mk-mapsafe'],  # 145, 158,
    #'MtKoltsMinimal': [151, 'root-mk'],
    'VeldtCave': [467, 468, 469, 470, 471, 472, 474, 475, 'root-vc'],
    'VeldtCave_mapsafe': [468, 469, 470, 471, 472, 474, 475, 'root-vc-mapsafe'],  # 467
    #'VeldtCaveMinimal': [470, 475, 'root-vc'],

    # Meta rooms:
    'WoB': [
        19, 20, 22, 23, 53, 54, 55, 59, 60, 'root-unb',  # Upper Narshe WoB
        # Esper Mountain: 495 excluded — 'root-em_mapsafe' stands in for it,
        # carrying 495's interior doors (1046/1048/1049) while its world-map
        # entrance 1047 stays vanilla so map shuffle can manage it.
        488, 489, 490, 491, 492, 493, 494, 496, 497, 498, 499, 500, 501, 'root-em_mapsafe',
        345, 346, 347, 349, 351, 352, 353, 354, 355, '355a', 'root-mf',  # Magitek Factory
        503, 504, '504a', 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 'root-sg',  # Cave to the Sealed Gate
        294, 295, 296, 297, 298, 299, 300, 301, 302, '303a', '303b', 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 'root-zb', # Zozo-WoB
        'LeteRiver1', 'LeteCave1', 'LeteRiver2', 'LeteCave2', 'LeteRiver3', 'root-lr',  # Lete River
        '241a', 246, '241b', '247a', '247b', '247c', '241c', '241d', 'root-st',  # Serpent Trench
        457, 458, 459, 460, 461, 462, 463, 464, 465, 'root-bh', # Burning House
        100, 101, 103, 104, 'root-sfcb-mapsafe',  # South Figaro Cave WOB  102, 105,
        201, 202, '203a', '203b', '203c', 204, '204b', '204c', 205, 206, '206a', '206b', 207, '207a',
        '207b', 212, 213, '215a', '215b', 216, 220, 221, 'root-pt',  # Phantom Train
        146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 159, 160, 'root-mk-mapsafe', # Mt. Kolts  145, 158,
        ],
    'WoR': [
        364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368,  # Umaro's cave
        '37a', 38, 40, '41a', 42, 43, 44, 46, 47, 'root-unr',  # Upper Narshe WoR
        277, 278, 279, 280, 281, 282, 283, 284, 'root-ob',  # Owzer's Basement
        '294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r', 'root-zr', # Zozo-WoR
        250, 251, 252, 253, 254, 255, 256,  # Mt. Zozo
        356, 357, 358, '358b', 359, '359b', 361, 362, 363, 'root-ze',  # Zone Eater
        378, 379, 380, 381, 382, 383, 384, 386, 387, 388, 389, 390, 391, 392, 393, 'root-dt',  # Daryl's Tomb
        421, 422, 423, 424, 425, 426, 427, 428, 429, 208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
        432, 433, 184, 185, 186, 187, 188, '188B', 189, 190, 191, 192, 193, 'root-cd',  # Cyan's Dream
        468, 469, 470, 471, 472, 474, 475, 'root-vc-mapsafe', # Veldt Cave WOR   467,
        'branch-pc', 'root-pc'  # Phoenix cave entry
             ],
    'MapShuffleWOB':  ['shuffle-wob',
                       'ms-wob-4', 'ms-wob-5', 'ms-wob-1501', 'ms-wob-1502', 'ms-wob-1504', 'ms-wob-1505',
                       'ms-wob-1506', 'ms-wob-6', 'ms-wob-10', 'ms-wob-11', 'ms-wob-12', 'ms-wob-13', 'ms-wob-14',
                       'ms-wob-15', 'ms-wob-16', 'ms-wob-18', 'ms-wob-20', 'ms-wob-21', 'ms-wob-23', 'ms-wob-24',
                       'ms-wob-26', 'ms-wob-27', 'ms-wob-28', 'ms-wob-31', 'ms-wob-33', 'ms-wob-35', 'ms-wob-37',
                       'ms-wob-40', 'ms-wob-42', 'ms-wob-44', 'ms-wob-1556'],
    'MapShuffleWOR':  ['shuffle-wor',
                       'ms-wor-48', 'ms-wor-49', 'ms-wor-51', 'ms-wor-52', 'ms-wor-53', 'ms-wor-56', 'ms-wor-57',
                       'ms-wor-58', 'ms-wor-59', 'ms-wor-61', 'ms-wor-62', 'ms-wor-63', 'ms-wor-65', 'ms-wor-67',
                       'ms-wor-68', 'ms-wor-69', 'ms-wor-70', 'ms-wor-73', 'ms-wor-75', 'ms-wor-76', 'ms-wor-78',
                       'ms-wor-79', 'ms-wor-1552', 'ms-wor-1554', 'ms-wor-1558'],

    'DungeonCrawl': [
        #'dc-world',  # WOB & WOR
        'wob-narshe', 'wob-figaro', 'wob-sabil', 'wob-nikeah', 'wob-doma', 'wob-baren', 'wob-veldt', 'wob-thamasa',
        'wob-kohlingen', 'wob-empire', 'wob-airship',
        'dc-4', 105, 'dc-1501', 'ms-wob-1502', 'dc-1504', 'dc-1505', 102, 'ms-wob-6', 'ms-wob-10', 145, 158, 'dc-13',
        'ms-wob-14', 'dc-15', 'dc-16', 'ms-wob-18', 'dc-20-21', 'dc-23', 'ms-wob-24', 'ms-wob-26', 'ms-wob-27',
        'ms-wob-28', 'ms-wob-31', 'ms-wob-33', 'ms-wob-35', 293, 'ms-wob-40', 502, 495, 'branch-fc', # WOB connectors
        19, 20, 22, 23, 53, 54, 55, 59, 60,  # Upper Narshe WoB
        488, 489, 490, 491, 492, 493, 494, 496, 497, 498, 499, 500,  # Esper Mountain  removed dead ends: 501,
        345, 346, 347, 349, 351, 352, 353, 354, 355, '355a',  # Magitek Factory
        503, 504, '504a', 505, 506, 507, 508, 509, 510, 511, 512, 513, 514,  # Cave to the Sealed Gate
        296, 297, 298, 299, 300, 301, 302, '303a', '303b', 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, # Zozo-WoB  # removed dead ends: 294, 295,
        'LeteRiver1', 'LeteCave1', 'LeteRiver2', 'LeteCave2', 'LeteRiver3',  # Lete River
        '241a', 246, '241b', '247a', '247b', '247c', '241c', '241d',  # Serpent Trench
        457, 458, 459, 460, 461, 462, 463, 464, 465, # Burning House
        100, 101, 103, 104,  # South Figaro Cave WOB  102, 105,
        201, 202, '203a', '203b', '203c', 204, '204b', '204c', 205, 206, '206a', '206b', 207, '207a',
        '207b', 212, 213, '215a', '215b', 216, 220, 221,  # Phantom Train
        146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 159, 160, # Mt. Kolts  145, 158,
        286, 331, #  Esper world  #  Vector castle;
        'wor-island', 'wor-kefkastower', 'wor-fanatics', 'wor-figaro', 'wor-dragonsneck', 'wor-jidoor', 'wor-narshe',
        'wor-doma', 'wor-dinosaur', 'wor-veldt', 'wor-thamasa', 'wor-ebots', 'wor-triangle', 'wor-airship',
        'ms-wor-48', 'ms-wor-49', 'ms-wor-51', 'ms-wor-52', 377, 'ms-wor-56', 'dc-57', 'ms-wor-58', 'ms-wor-59', 467,
        'ms-wor-62', 'ms-wor-63', 'ms-wor-65', 'dc-67', 'ms-wor-69', '293r', 'dc-73', 'dc-75', 'dc-76',  # 'ms-wor-68',
        'ms-wor-78', 'ms-wor-79', 'branch-pc', 'ms-wor-1558',  # WOR connectors
        364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368,  # Umaro's cave
        '37a', 38, 40, '41a', 42, 43, 44, 46,   # Upper Narshe WoR  # removed dead ends: 47,
        277, 278, 279, 280, 281, 282, 283, 284,  # Owzer's Basement
        '296r', '301r', '305r', '306r', '307r', '308r', '309r', # Zozo-WoR  # removed dead ends: '294r', '295r',
        250, 251, 252, 253, 254, 255, 256,  # Mt. Zozo
        356, 357, 358, '358b', 359, '359b', 361, 362, 363,  # Zone Eater
        378, 379, 380, 381, 382, 383, 384, 386, 387, 388, 389, 390, 391, 392, 393,  # Daryl's Tomb
        421, 422, 423, 424, 425, 426, 427, 428, 429, 208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
        432, 433, 186, 187, 188, '188B', 189, 190, 191, 192, 193,  # Cyan's Dream  # removed dead ends: 184, 185,
        469, 470, 471, 472, 474, 475 # Veldt Cave WOR  # removed dead end: 468,
        ],

    #'test': ['test_room_1', 'test_room_2']  # for testing only

}

# Derived meta-pools
ROOM_SETS['All'] = [r for r in ROOM_SETS['WoB']] + [r for r in ROOM_SETS['WoR']]
ROOM_SETS['MapShuffleXW'] = [r for r in ROOM_SETS['MapShuffleWOB']] + [r for r in ROOM_SETS['MapShuffleWOR']]

ROOM_SETS['Ruination'] = ['ruin_hub_testing', 'ruin_testing',
                          'ruin_kt1', 'ruin_kt2', 'ruin_kt3',
                          'ruin_kt_entry_1', 'ruin_kt_entry_2', 'ruin_kt_entry_3']

