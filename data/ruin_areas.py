"""Ruination area -> room-set table (ROM-free): the rooms each
plannable area contributes. RuinConfig takes per-plan copies;
tools/compile_atlas.py --check validates pool membership.
"""

RUIN_ROOM_SETS = {
    'Doma': ['CDA01', 'CDA02', 'CDA03', 'CDA04', 'CDA06', 'CDA07', 'CDA08', 'CDA05', 'CDB01', 'CDB02',
                  'CDB03', 'CDB04', 'CDC01', 'CDC02', 'CDC03', 'CDC04', 'CDC05', 'CDC06', 'CDC07', 'CDC08', 'CDC09', 'CDC10', 'CDC11-ruin', 'DOMr02-ruin', 'DOMb10'],
    'DreamMaze': ['DRM01', 'DRM02', 'DRM03', 'DRM04', 'DRM05', 'DRM06', 'DRM07', 'DRM08', 'DRM09'],
    'UmarosCave': ['UMA01', 'UMA02', 'UMA03', 'UMA04a', 'UMA04b', 'UMA04c', 'UMA51-share', 'UMA52-share', 'UMA05'],  # root is in Narshe
    'EsperMountain': ['ESM01', 'ESM02', 'ESM03', 'ESM04', 'ESM05', 'ESM06', 'ESM07', 'ESM08', 'ESM09', 'ESM10', 'ESM11', 'ESM12', 'ESM13'],  # 501 excluded: shares exit 1057 with ruin_terminus_2
    'PhantomTrain': ['PHT01-ruin', 'PHT02-ruin', 'PHT03a', 'PHT03b', 'PHT03c', 'PHT04', 'PHT04b', 'PHT04c', 'PHT05', 'PHT06', 'PHT06a', 'PHT06b', 'PHT07', 'PHT07a',
                     'PHT07b', 'PHT08', 'PHT09', 'PHT10a', 'PHT10b', 'PHT11', 'PHT12', 'PHT13'], # 'PHF01-ruin' if you want to include the forest + healing spring
    'SealedGate': ['SEA01', 'SEA02', 'SEA03', 'SEA04', 'SEA05', 'SEA06', 'SEA07', 'SEA08', 'SEA09', 'SEA10', 'SEA11', 'SEA12'],  # no worldmap connector 'SEA03a'; no sealed gate itself 514
    'SouthFigaroCave': ['SFCb05', 'SFCb06', 'SFCb07', 'SFCb08', 'SFCb09'],  # Removed outside hallway (105)
    'ReturnersHideout': ['RET02-ruin', 'LET01', 'LET02', 'LET03', 'LET04', 'LET05'],  # Need to add raft return to Esper World
    'AncientCastle': ['ANC01', 'ANC02', 'ANC03', 'ANC04', 'ANC05', 'ANC06', 'ANC07', 'ANC08', 'ANC09', 'ANC10', 'ANC11', 'ANC12', 'ANC13'],
    'Jidoor': ['JIDr01-dc', 'OWZr01', 'OWZr02', 'OWZr03', 'OWZr04', 'OWZr05', 'OWZr06', 'OWZr07', 'OWZr08'],   # Including Owzer's Mansion
    'VeldtCave': ['COV01', 'COV02', 'COV03', 'COV04', 'COV05', 'COV06', 'COV07', 'COV08-ruin', 'THAr01-ruin'],  # It's OK to double rooms, we will check to make sure they don't actually map twice. 475
    'CrescentMtn': ['CRE01-ruin', 'SER01a', 'SER02', 'SER01b', 'SER03a', 'SER03b', 'SER03c', 'SER01c', 'NIKb50', 'NIKr52-ruin', 'NIKr01-ruin'],   # 'CRE01-dc'.  Gau lock on Serpent Trench Cliff.
    'BarenFalls': ['BAR01-ruin', 'BAR50-ruin', 'BAR51-ruin'],  # 'BAR03-dc'
    'Vector': ['MTF01', 'MTF02', 'MTF03', 'MTF04-ruin', 'MTF05', 'MTF06', 'MTF07', 'MTF08-ruin', 'MTF09', 'MTF10', 'MTF50-ruin', 'VEC01-ruin'],  # 349
    'DarylsTomb': ['DAR01', 'DAR02', 'DAR03', 'DAR04', 'DAR05', 'DAR06', 'DAR07', 'DAR08', 'DAR09', 'DAR10-ruin', 'DAR11', 'DAR12', 'DAR13', 'DAR14', 'DAR15', 'DAR16'],
            # Hallways: 377, 378.
    'ZoneEater': ['ZON01', 'ZON02', 'ZON03', 'ZON03b', 'ZON04', 'ZON04b', 'ZON05', 'ZON06', 'ZON07'],
    'MtKolts': ['MTK02', 'MTK03', 'MTK04', 'MTK05', 'MTK06', 'MTK07', 'MTK08', 'MTK09', 'MTK11', 'MTK12', 'MTK13', 'MTK15', 'MTK16'],
            # Hallways: 145, 146 (anim), 148, 150 (anim), 152, 154, 155, 158.  Removed: 145, 154, 158.
    'Narshe': ['NARr01-ruin', 'UPNr01a', 'UPNr02', 'UPNr03', 'UPNr04-ruin', 'NARr50-ruin', 'UPNr05', 'UPNr06', 'UPNr07', 'NARr15', 'UPNb08-ruin', 'UPNr09', 'NARb19', 'NARr18', 'NARr17', 'NARr20'],   # Narshe WOR + northern caves (swap out WOB Whelk 46 --> 59) + snow battlefield + Tritoch + Umaro exit + moogle mines (swap out 48 --> 65 for moogle defense) + Lone Wolf reward room
            # Hallways: 36, 38, 42, 43, 44, 45, 50, 51.  Removed: 36, 51
    'Zozo': ['ZOZr01-ruin', 'ZOZr02', 'ZOZr03', 'ZOZr04', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17'],
    'ZozoTower': ['ZOZb05', 'ZOZb06', 'ZOZb07', 'ZOZb08', 'ZOZb10', 'ZOZb11a', 'ZOZb11b', 'ZOZb12', 'ZOZb18', 'ZOZb19', 'ZOZb20', 'ZOZb21'],
    'MtZozo': ['MTZ01', 'MTZ02', 'MTZ03', 'MTZ04', 'MTZ05', 'MTZ06', 'MTZ07'],
    'BurningHouse': ['BUR01', 'BUR02', 'BUR03', 'BUR04', 'BUR05', 'BUR06', 'BUR07', 'BUR08', 'BUR09-ruin'],  # Burning House interior; 465

    'SouthFigaro': ['MAPr-SFI'],
    'GauFatherHouse': ['MAPb-GFH'],  # use WOB for shadow check & vendor.  Change tileset, perhaps?
    'Thamasa': ['THAr01-ruin'],  # Thamasa town (burning house entrance gated by STRAGO)
    'Kohlingen': ['MAPr-KOH'],
    'Cid': ['MAPr-CID'],
    'Mobliz': ['MAPr-MOB'],
    'Maranda': ['MAPr-MAR'],
    'FanaticsTower': ['MAPr-FAN'],
    'OperaHouse': ['MAPb-OPE'],   # WOB for the opera scene.  Have code switch it to WOR after opera scene is complete.  Edit end of opera scene.
    'EbotsRock': ['MAPr-EBO'],
    'Coliseum': ['MAPr-COL'],
    'Tzen': ['MAPr-TZE'],   # WOR only (collapsing house)
    'Albrook': ['MAPr-ALB'],
    'Veldt': ['wor-veldt'],
    'Nikeah': ['NIKr01-ruin'],  # including Serpent Trench exit (post reward)
    'PhoenixCave': ['MAPr-PHO'],  # Need to make red exit point go to Esper World, probably.
    'FloatingContinent': ['MAPb-FLO'],
    'ImperialCamp': ['IMP01-dc'],
    'FigaroCastle': ['FIGr04-ruin'],  # Figaro Castle world map entrances

    'DuncanHouse': ['DUN01-ruin'],  # Duncan's House (Bum Rush); conditionally added when a Blitz character is planned

    'ImperialCastle': ['VIC03'],  # Extra hub room if needed
}
