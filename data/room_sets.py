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
    'Umaro': ['UMA01', 'UMA02', 'UMA03', 'UMA04a', 'UMA04b', 'UMA04c', 'UMA51-share', 'UMA52-share', 'UMA05', 'UMA-root'],
    'UpperNarshe_WoB': ['UPNb01', 'UPNb02', 'UPNb03', 'UPNb04', 'UPNb05', 'UPNb06', 'UPNb07', 'UPNb08', 'UPNb09', 'UPNb-root'],
    'UpperNarshe_WoR': ['UPNr01', 'UPNr02', 'UPNr03', 'UPNr04', 'UPNr05', 'UPNr06', 'UPNr07', 'UPNr08', 'UPNr09', 'UPNr-root'],
    'EsperMountain': ['ESM01', 'ESM02', 'ESM03', 'ESM04', 'ESM05', 'ESM06', 'ESM07', 'ESM08', 'ESM09', 'ESM10', 'ESM11', 'ESM12', 'ESM13', 'ESM14', 'ESM-root'],
    # 495 IS included here (unlike the 'WoB' meta-set below): the -dre mapsafe
    # root ('ESM-root-mapsafe-each') protects the world-map entrance as door
    # 30044, paired with 495's entrance 1047 via map_shuffle_protected_doors.
    'EsperMountain_mapsafe': ['ESM01', 'ESM02', 'ESM03', 'ESM04', 'ESM05', 'ESM06', 'ESM07', 'ESM08', 'ESM09', 'ESM10', 'ESM11', 'ESM12', 'ESM13', 'ESM14', 'ESM-root-mapsafe-each'],
    'OwzerBasement' : ['OWZr01', 'OWZr02', 'OWZr03', 'OWZr04', 'OWZr05', 'OWZr06', 'OWZr07', 'OWZr08', 'OWZr-root'],
    'MagitekFactory' : ['MTF01', 'MTF02', 'MTF03', 'MTF04', 'MTF05', 'MTF06', 'MTF07', 'MTF08', 'MTF09', 'MTF10', 'MTF-root'],
    'SealedGate' : ['SEA02', 'SEA03', 'SEA03a', 'SEA04', 'SEA05', 'SEA06', 'SEA07', 'SEA08', 'SEA09', 'SEA10', 'SEA11', 'SEA12', 'SEA13', 'SEA-root'],
    'Zozo' : ['ZOZb02', 'ZOZb03', 'ZOZb04', 'ZOZb05', 'ZOZb06', 'ZOZb07', 'ZOZb08', 'ZOZb09', 'ZOZb10', 'ZOZb11a', 'ZOZb11b', 'ZOZb12', 'ZOZb13', 'ZOZb14', 'ZOZb15', 'ZOZb16', 'ZOZb17', 'ZOZb18', 'ZOZb19', 'ZOZb20',
              'ZOZb21', 'ZOZb-root'],
    'Zozo-WOR' : ['ZOZr02', 'ZOZr03', 'ZOZr04', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17', 'ZOZr-root', 'ZOZr53-branch'],
    #'Zozo-WOR_mapsafe' : ['ZOZr02', 'ZOZr03', 'ZOZr50-mapsafe', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17', 'ZOZr-root'],  # only used in -dre
    'Zozo-WOR_mapsafe' : ['ZOZr02', 'ZOZr03', 'ZOZr04', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17', 'ZOZr-root', 'ZOZr54-branch-mapsafe'],  # only used in -dre
    'MtZozo' : ['MTZ01', 'MTZ02', 'MTZ03', 'MTZ04', 'MTZ05', 'MTZ06', 'MTZ07', 'MTZ-root'],
    #'MtZozo_mapsafe' : [250, 251, 252, 'MTZ04-mapsafe', 254, 255, 256],  # only used in -dre
    'MtZozo_mapsafe' : ['MTZ01', 'MTZ02', 'MTZ03', 'MTZ04', 'MTZ05', 'MTZ06', 'MTZ07', 'MTZ-root-mapsafe'],  # only used in -dre
    'Lete' : ['LET01', 'LET02', 'LET03', 'LET04', 'LET05', 'LET-root'],
    'ZoneEater': ['ZON01', 'ZON02', 'ZON03', 'ZON03b', 'ZON04', 'ZON04b', 'ZON05', 'ZON06', 'ZON07', 'ZON-root'],
    'SerpentTrench': ['SER01a', 'SER02', 'SER01b', 'SER03a', 'SER03b', 'SER03c', 'SER01c', 'NIKb50', 'SER-root'],
    'BurningHouse': ['BUR01', 'BUR02', 'BUR03', 'BUR04', 'BUR05', 'BUR06', 'BUR07', 'BUR08', 'BUR09', 'BUR-root'],
    'DarylsTomb': ['DAR02', 'DAR03', 'DAR04', 'DAR05', 'DAR06', 'DAR07', 'DAR08', 'DAR09', 'DAR10', 'DAR11', 'DAR12', 'DAR13', 'DAR14', 'DAR15', 'DAR16', 'DAR-root'],
    #'DarylsTombMinimal': [379, 380, 383, 384, 386, 387, 389, 390, 391, 392, 'DAR-root'],  # for testing
    'SouthFigaroCaveWOB': ['SFCb05', 'SFCb06', 'SFCb07', 'SFCb08', 'SFCb09', 'SFCb10', 'SFCb-root'],
    'SouthFigaroCaveWOB_mapsafe': ['SFCb05', 'SFCb06', 'SFCb08', 'SFCb09', 'SFCb-root-mapsafe'],  #  102, 105,
    'PhantomTrain': ['PHT01', 'PHT02', 'PHT03a', 'PHT03b', 'PHT03c', 'PHT04', 'PHT04b', 'PHT04c', 'PHT05', 'PHT06', 'PHT06a', 'PHT06b', 'PHT07', 'PHT07a',
                     'PHT07b', 'PHT08', 'PHT09', 'PHT10a', 'PHT10b', 'PHT11', 'PHT12', 'PHT13', 'PHT-root'],
    'CyansDream': ['DRM01', 'DRM02', 'DRM03', 'DRM04', 'DRM05', 'DRM06', 'DRM07', 'DRM08', 'DRM09', 'CDA01', 'CDA02', 'CDA03', 'CDA04', 'CDA06', 'CDA07', 'CDA08', 'CDA05', 'CDB01', 'CDB02',
                  'CDB03', 'CDB04', 'CDC01', 'CDC02', 'CDC03', 'CDC04', 'CDC05', 'CDC06', 'CDC07', 'CDC08', 'CDC09', 'CDC10', 'CDC11', 'CDA-root'],
    'MtKolts': ['MTK01', 'MTK02', 'MTK03', 'MTK04', 'MTK05', 'MTK06', 'MTK07', 'MTK08', 'MTK09', 'MTK10', 'MTK11', 'MTK12', 'MTK13', 'MTK14', 'MTK15', 'MTK16', 'MTK-root'],
    'MtKolts_mapsafe': ['MTK02', 'MTK03', 'MTK04', 'MTK05', 'MTK06', 'MTK07', 'MTK08', 'MTK09', 'MTK10', 'MTK11', 'MTK12', 'MTK13', 'MTK15', 'MTK16', 'MTK-root-mapsafe'],  # 145, 158,
    #'MtKoltsMinimal': [151, 'MTK-root'],
    'VeldtCave': ['COV01', 'COV02', 'COV03', 'COV04', 'COV05', 'COV06', 'COV07', 'COV08', 'COV-root'],
    'VeldtCave_mapsafe': ['COV02', 'COV03', 'COV04', 'COV05', 'COV06', 'COV07', 'COV08', 'COV-root-mapsafe'],  # 467
    #'VeldtCaveMinimal': [470, 475, 'COV-root'],

    # Meta rooms:
    'WoB': [
        'UPNb01', 'UPNb02', 'UPNb03', 'UPNb04', 'UPNb05', 'UPNb06', 'UPNb07', 'UPNb08', 'UPNb09', 'UPNb-root',  # Upper Narshe WoB
        # Esper Mountain: 495 excluded — 'ESM-root-mapsafe' stands in for it,
        # carrying 495's interior doors (1046/1048/1049) while its world-map
        # entrance 1047 stays vanilla so map shuffle can manage it.
        'ESM01', 'ESM02', 'ESM03', 'ESM04', 'ESM05', 'ESM06', 'ESM07', 'ESM09', 'ESM10', 'ESM11', 'ESM12', 'ESM13', 'ESM14', 'ESM-root-mapsafe',
        'MTF01', 'MTF02', 'MTF03', 'MTF04', 'MTF05', 'MTF06', 'MTF07', 'MTF08', 'MTF09', 'MTF10', 'MTF-root',  # Magitek Factory
        'SEA02', 'SEA03', 'SEA03a', 'SEA04', 'SEA05', 'SEA06', 'SEA07', 'SEA08', 'SEA09', 'SEA10', 'SEA11', 'SEA12', 'SEA13', 'SEA-root',  # Cave to the Sealed Gate
        'ZOZb02', 'ZOZb03', 'ZOZb04', 'ZOZb05', 'ZOZb06', 'ZOZb07', 'ZOZb08', 'ZOZb09', 'ZOZb10', 'ZOZb11a', 'ZOZb11b', 'ZOZb12', 'ZOZb13', 'ZOZb14', 'ZOZb15', 'ZOZb16', 'ZOZb17', 'ZOZb18', 'ZOZb19', 'ZOZb20', 'ZOZb21', 'ZOZb-root', # Zozo-WoB
        'LET01', 'LET02', 'LET03', 'LET04', 'LET05', 'LET-root',  # Lete River
        'SER01a', 'SER02', 'SER01b', 'SER03a', 'SER03b', 'SER03c', 'SER01c', 'NIKb50', 'SER-root',  # Serpent Trench
        'BUR01', 'BUR02', 'BUR03', 'BUR04', 'BUR05', 'BUR06', 'BUR07', 'BUR08', 'BUR09', 'BUR-root', # Burning House
        'SFCb05', 'SFCb06', 'SFCb08', 'SFCb09', 'SFCb-root-mapsafe',  # South Figaro Cave WOB  102, 105,
        'PHT01', 'PHT02', 'PHT03a', 'PHT03b', 'PHT03c', 'PHT04', 'PHT04b', 'PHT04c', 'PHT05', 'PHT06', 'PHT06a', 'PHT06b', 'PHT07', 'PHT07a',
        'PHT07b', 'PHT08', 'PHT09', 'PHT10a', 'PHT10b', 'PHT11', 'PHT12', 'PHT13', 'PHT-root',  # Phantom Train
        'MTK02', 'MTK03', 'MTK04', 'MTK05', 'MTK06', 'MTK07', 'MTK08', 'MTK09', 'MTK10', 'MTK11', 'MTK12', 'MTK13', 'MTK15', 'MTK16', 'MTK-root-mapsafe', # Mt. Kolts  145, 158,
        ],
    'WoR': [
        'UMA01', 'UMA02', 'UMA03', 'UMA04a', 'UMA04b', 'UMA04c', 'UMA51-share', 'UMA52-share', 'UMA05',  # Umaro's cave
        'UPNr01a', 'UPNr02', 'UPNr03', 'UPNr04a', 'UPNr05', 'UPNr06', 'UPNr07', 'UPNr08', 'UPNr09', 'UPNr-root',  # Upper Narshe WoR
        'OWZr01', 'OWZr02', 'OWZr03', 'OWZr04', 'OWZr05', 'OWZr06', 'OWZr07', 'OWZr08', 'OWZr-root',  # Owzer's Basement
        'ZOZr02', 'ZOZr03', 'ZOZr04', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17', 'ZOZr-root', # Zozo-WoR
        'MTZ01', 'MTZ02', 'MTZ03', 'MTZ04', 'MTZ05', 'MTZ06', 'MTZ07',  # Mt. Zozo
        'ZON01', 'ZON02', 'ZON03', 'ZON03b', 'ZON04', 'ZON04b', 'ZON05', 'ZON06', 'ZON07', 'ZON-root',  # Zone Eater
        'DAR02', 'DAR03', 'DAR04', 'DAR05', 'DAR06', 'DAR07', 'DAR08', 'DAR09', 'DAR10', 'DAR11', 'DAR12', 'DAR13', 'DAR14', 'DAR15', 'DAR16', 'DAR-root',  # Daryl's Tomb
        'DRM01', 'DRM02', 'DRM03', 'DRM04', 'DRM05', 'DRM06', 'DRM07', 'DRM08', 'DRM09', 'CDA01', 'CDA02', 'CDA03', 'CDA04', 'CDA06', 'CDA07', 'CDA08', 'CDA05', 'CDB01', 'CDB02',
        'CDB03', 'CDB04', 'CDC01', 'CDC02', 'CDC03', 'CDC04', 'CDC05', 'CDC06', 'CDC07', 'CDC08', 'CDC09', 'CDC10', 'CDC11', 'CDA-root',  # Cyan's Dream
        'COV02', 'COV03', 'COV04', 'COV05', 'COV06', 'COV07', 'COV08', 'COV-root-mapsafe', # Veldt Cave WOR   467,
        'PHO52-branch', 'PHO-root'  # Phoenix cave entry
             ],
    'MapShuffleWOB':  ['MAPb-root',
                       'MAPb-NAR', 'MAPb-SFC2', 'MAPb-IMP', 'MAPb-FIG', 'MAPb-THA', 'MAPb-VEC',
                       'MAPb-SFC', 'MAPb-SFI', 'MAPb-SAB', 'MAPb-MTK', 'MAPb-MTK2', 'MAPb-RET', 'MAPb-GFH',
                       'MAPb-BAR', 'MAPb-NIK', 'MAPb-DOM', 'MAPb-PHF', 'MAPb-PHF2', 'MAPb-CRE', 'MAPb-KOH',
                       'MAPb-MOB', 'MAPb-COL', 'MAPb-JID', 'MAPb-MAR', 'MAPb-TZE', 'MAPb-ALB', 'MAPb-ZOZ',
                       'MAPb-OPE', 'MAPb-SEA', 'MAPb-ESM', 'MAPb-FLO'],
    'MapShuffleWOR':  ['MAPr-root',
                       'MAPr-CID', 'MAPr-ALB', 'MAPr-TZE', 'MAPr-MOB', 'MAPr-DAR', 'MAPr-COL', 'MAPr-SFC',
                       'MAPr-SFI', 'MAPr-KOH', 'MAPr-COV', 'MAPr-OPE', 'MAPr-MAR', 'MAPr-NIK', 'MAPr-NAR',
                       'MAPr-GFH', 'MAPr-FAN', 'MAPr-ZOZ', 'MAPr-JID', 'MAPr-THA', 'MAPr-DOM', 'MAPr-EBO',
                       'MAPr-DUN', 'MAPr-ZON', 'MAPr-PHO', 'MAPr-ANC'],

    'DungeonCrawl': [
        #'dc-world',  # WOB & WOR
        'wob-narshe', 'wob-figaro', 'wob-sabil', 'wob-nikeah', 'wob-doma', 'wob-baren', 'wob-veldt', 'wob-thamasa',
        'wob-kohlingen', 'wob-empire', 'wob-airship',
        'NARb01-dc', 'SFCb10', 'IMP01-dc', 'MAPb-FIG', 'THAb01-dc', 'VEC01-dc', 'SFCb07', 'MAPb-SFI', 'MAPb-SAB', 'MTK01', 'MTK14', 'RET01-dc',
        'MAPb-GFH', 'BAR03-dc', 'NIKb01-dc', 'MAPb-DOM', 'PHF01-dc', 'CRE01-dc', 'MAPb-KOH', 'MAPb-MOB', 'MAPb-COL',
        'MAPb-JID', 'MAPb-MAR', 'MAPb-TZE', 'MAPb-ALB', 'ZOZb01', 'MAPb-OPE', 'SEA01', 'ESM08', 'FIGb50-branch', # WOB connectors
        'UPNb01', 'UPNb02', 'UPNb03', 'UPNb04', 'UPNb05', 'UPNb06', 'UPNb07', 'UPNb08', 'UPNb09',  # Upper Narshe WoB
        'ESM01', 'ESM02', 'ESM03', 'ESM04', 'ESM05', 'ESM06', 'ESM07', 'ESM09', 'ESM10', 'ESM11', 'ESM12', 'ESM13',  # Esper Mountain  removed dead ends: 501,
        'MTF01', 'MTF02', 'MTF03', 'MTF04', 'MTF05', 'MTF06', 'MTF07', 'MTF08', 'MTF09', 'MTF10',  # Magitek Factory
        'SEA02', 'SEA03', 'SEA03a', 'SEA04', 'SEA05', 'SEA06', 'SEA07', 'SEA08', 'SEA09', 'SEA10', 'SEA11', 'SEA12', 'SEA13',  # Cave to the Sealed Gate
        'ZOZb04', 'ZOZb05', 'ZOZb06', 'ZOZb07', 'ZOZb08', 'ZOZb09', 'ZOZb10', 'ZOZb11a', 'ZOZb11b', 'ZOZb12', 'ZOZb13', 'ZOZb14', 'ZOZb15', 'ZOZb16', 'ZOZb17', 'ZOZb18', 'ZOZb19', 'ZOZb20', 'ZOZb21', # Zozo-WoB  # removed dead ends: 294, 295,
        'LET01', 'LET02', 'LET03', 'LET04', 'LET05',  # Lete River
        'SER01a', 'SER02', 'SER01b', 'SER03a', 'SER03b', 'SER03c', 'SER01c', 'NIKb50',  # Serpent Trench
        'BUR01', 'BUR02', 'BUR03', 'BUR04', 'BUR05', 'BUR06', 'BUR07', 'BUR08', 'BUR09', # Burning House
        'SFCb05', 'SFCb06', 'SFCb08', 'SFCb09',  # South Figaro Cave WOB  102, 105,
        'PHT01', 'PHT02', 'PHT03a', 'PHT03b', 'PHT03c', 'PHT04', 'PHT04b', 'PHT04c', 'PHT05', 'PHT06', 'PHT06a', 'PHT06b', 'PHT07', 'PHT07a',
        'PHT07b', 'PHT08', 'PHT09', 'PHT10a', 'PHT10b', 'PHT11', 'PHT12', 'PHT13',  # Phantom Train
        'MTK02', 'MTK03', 'MTK04', 'MTK05', 'MTK06', 'MTK07', 'MTK08', 'MTK09', 'MTK10', 'MTK11', 'MTK12', 'MTK13', 'MTK15', 'MTK16', # Mt. Kolts  145, 158,
        'ESW01', 'VIC03', #  Esper world  #  Vector castle;
        'wor-island', 'wor-kefkastower', 'wor-fanatics', 'wor-figaro', 'wor-dragonsneck', 'wor-jidoor', 'wor-narshe',
        'wor-doma', 'wor-dinosaur', 'wor-veldt', 'wor-thamasa', 'wor-ebots', 'wor-triangle', 'wor-airship',
        'MAPr-CID', 'MAPr-ALB', 'MAPr-TZE', 'MAPr-MOB', 'DAR01', 'MAPr-COL', 'SFCr04-dc', 'MAPr-SFI', 'MAPr-KOH', 'COV01',
        'MAPr-OPE', 'MAPr-MAR', 'MAPr-NIK', 'NARr01-dc', 'MAPr-FAN', 'ZOZr01', 'JIDr01-dc', 'THAr01-dc', 'DOMr10-dc',  # 'MAPr-GFH',
        'MAPr-EBO', 'MAPr-DUN', 'PHO52-branch', 'MAPr-ANC',  # WOR connectors
        'UMA01', 'UMA02', 'UMA03', 'UMA04a', 'UMA04b', 'UMA04c', 'UMA51-share', 'UMA52-share', 'UMA05',  # Umaro's cave
        'UPNr01a', 'UPNr02', 'UPNr03', 'UPNr04a', 'UPNr05', 'UPNr06', 'UPNr07', 'UPNr08',   # Upper Narshe WoR  # removed dead ends: 47,
        'OWZr01', 'OWZr02', 'OWZr03', 'OWZr04', 'OWZr05', 'OWZr06', 'OWZr07', 'OWZr08',  # Owzer's Basement
        'ZOZr04', 'ZOZr09', 'ZOZr13', 'ZOZr14', 'ZOZr15', 'ZOZr16', 'ZOZr17', # Zozo-WoR  # removed dead ends: 'ZOZr02', 'ZOZr03',
        'MTZ01', 'MTZ02', 'MTZ03', 'MTZ04', 'MTZ05', 'MTZ06', 'MTZ07',  # Mt. Zozo
        'ZON01', 'ZON02', 'ZON03', 'ZON03b', 'ZON04', 'ZON04b', 'ZON05', 'ZON06', 'ZON07',  # Zone Eater
        'DAR02', 'DAR03', 'DAR04', 'DAR05', 'DAR06', 'DAR07', 'DAR08', 'DAR09', 'DAR10', 'DAR11', 'DAR12', 'DAR13', 'DAR14', 'DAR15', 'DAR16',  # Daryl's Tomb
        'DRM01', 'DRM02', 'DRM03', 'DRM04', 'DRM05', 'DRM06', 'DRM07', 'DRM08', 'DRM09', 'CDA01', 'CDA02', 'CDA03', 'CDA04', 'CDA06', 'CDA07', 'CDA08', 'CDA05', 'CDB01', 'CDB02',
        'CDB03', 'CDB04', 'CDC03', 'CDC04', 'CDC05', 'CDC06', 'CDC07', 'CDC08', 'CDC09', 'CDC10', 'CDC11',  # Cyan's Dream  # removed dead ends: 184, 185,
        'COV03', 'COV04', 'COV05', 'COV06', 'COV07', 'COV08' # Veldt Cave WOR  # removed dead end: 468,
        ],

    #'test': ['test_room_1', 'test_room_2']  # for testing only

}

# Derived meta-pools
ROOM_SETS['All'] = [r for r in ROOM_SETS['WoB']] + [r for r in ROOM_SETS['WoR']]
ROOM_SETS['MapShuffleXW'] = [r for r in ROOM_SETS['MapShuffleWOB']] + [r for r in ROOM_SETS['MapShuffleWOR']]

ROOM_SETS['Ruination'] = ['HUB51-test', 'NIKr51-test',
                          'KTA-ruin', 'KTB-ruin', 'KTC-ruin',
                          'KTA0-ruin', 'KTB0-ruin', 'KTC0-ruin']

