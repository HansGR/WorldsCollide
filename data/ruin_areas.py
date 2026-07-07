"""Ruination area -> room-set table (ROM-free).

Split out of event/ruination.py (rewrite Stage A milestone 3b) so the
atlas compiler and other ROM-free tooling can validate pool membership.
event/ruination.py imports it back; behavior is unchanged.
"""

RUIN_ROOM_SETS = {
    'Doma': [208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
                  432, 433, 184, 185, 186, 187, 188, '188B', 189, 190, 191, 192, 'ruin-wrexsoul', 'ruin-doma', 371],
    'DreamMaze': [421, 422, 423, 424, 425, 426, 427, 428, 429],
    'UmarosCave': [364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368],  # root is in Narshe
    'EsperMountain': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500],  # 501 excluded: shares exit 1057 with ruin_terminus_2
    'PhantomTrain': ['ruin-201', 'ruin-202', '203a', '203b', '203c', 204, '204b', '204c', 205, 206, '206a', '206b', 207, '207a',
                     '207b', 212, 213, '215a', '215b', 216, 220, 221], # 'ruin-phantomforest' if you want to include the forest + healing spring
    'SealedGate': [502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513],  # no worldmap connector '504a'; no sealed gate itself 514
    'SouthFigaroCave': [100, 101, 102, 103, 104],  # Removed outside hallway (105)
    'ReturnersHideout': ['ruin-returners', 'LeteRiver1', 'LeteCave1', 'LeteRiver2', 'LeteCave2', 'LeteRiver3'],  # Need to add raft return to Esper World
    'AncientCastle': [520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532],
    'Jidoor': ['dc-73', 277, 278, 279, 280, 281, 282, 283, 284],   # Including Owzer's Mansion
    'VeldtCave': [467, 468, 469, 470, 471, 472, 474, 'ruin-cotv', 'ruin-thamasa'],  # It's OK to double rooms, we will check to make sure they don't actually map twice. 475
    'CrescentMtn': ['ruin-st-entr', '241a', 246, '241b', '247a', '247b', '247c', '241c', '241d', 'ruin-st-exit', 'ruin-nikeah'],   # 'dc-23'.  Gau lock on Serpent Trench Cliff.
    'BarenFalls': ['ruin-baren-falls', 'ruin-baren-reward', 'ruin-baren'],  # 'dc-15'
    'Vector': [345, 346, 347, 'ruin-mtek1', 351, 352, 353, 'ruin-mtek2', 355, '355a', 'ruin-mtek3', 'ruin-vector'],  # 349
    'DarylsTomb': [377, 378, 379, 380, 381, 382, 383, 384, 386, 'ruin-daryl', 388, 389, 390, 391, 392, 393],
            # Hallways: 377, 378.
    'ZoneEater': [356, 357, 358, '358b', 359, '359b', 361, 362, 363],
    'MtKolts': [146, 147, 148, 149, 150, 151, 152, 153, 155, 156, 157, 159, 160],
            # Hallways: 145, 146 (anim), 148, 150 (anim), 152, 154, 155, 158.  Removed: 145, 154, 158.
    'Narshe': ['ruin-narshe', '37a', 38, 40, 'ruin-narshepeak', 'ruin-lonewolf', 42, 43, 44, 45, 'ruin-whelk', 47, 65, 49, 50, 61],   # Narshe WOR + northern caves (swap out WOB Whelk 46 --> 59) + snow battlefield + Tritoch + Umaro exit + moogle mines (swap out 48 --> 65 for moogle defense) + Lone Wolf reward room
            # Hallways: 36, 38, 42, 43, 44, 45, 50, 51.  Removed: 36, 51
    'Zozo': ['ruin-zozo', '294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r'],
    'ZozoTower': [297, 298, 299, 300, 302, '303a', '303b', 304, 310, 311, 312, 313],
    'MtZozo': [250, 251, 252, 253, 254, 255, 256],
    'BurningHouse': [457, 458, 459, 460, 461, 462, 463, 464, 'ruin-bh'],  # Burning House interior; 465

    'SouthFigaro': ['ms-wor-58'],
    'GauFatherHouse': ['ms-wob-14'],  # use WOB for shadow check & vendor.  Change tileset, perhaps?
    'Thamasa': ['ruin-thamasa'],  # Thamasa town (burning house entrance gated by STRAGO)
    'Kohlingen': ['ms-wor-59'],
    'Cid': ['ms-wor-48'],
    'Mobliz': ['ms-wor-52'],
    'Maranda': ['ms-wor-63'],
    'FanaticsTower': ['ms-wor-69'],
    'OperaHouse': ['ms-wob-40'],   # WOB for the opera scene.  Have code switch it to WOR after opera scene is complete.  Edit end of opera scene.
    'EbotsRock': ['ms-wor-78'],
    'Coliseum': ['ms-wor-56'],
    'Tzen': ['ms-wor-51'],   # WOR only (collapsing house)
    'Albrook': ['ms-wor-49'],
    'Veldt': ['wor-veldt'],
    'Nikeah': ['ruin-nikeah'],  # including Serpent Trench exit (post reward)
    'PhoenixCave': ['ms-wor-1554'],  # Need to make red exit point go to Esper World, probably.
    'FloatingContinent': ['ms-wob-1556'],
    'ImperialCamp': ['dc-1501'],
    'FigaroCastle': ['ruin-figarocastle'],  # Figaro Castle world map entrances

    'DuncanHouse': ['ruin-duncan'],  # Duncan's House (Bum Rush); conditionally added when a Blitz character is planned

    'ImperialCastle': [331],  # Extra hub room if needed
}
