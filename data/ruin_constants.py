"""Pure ruination planning data (ROM-free).

The area/reward tables the ruination planner reads, importable without
the ROM-coupled event machinery (the room-set half lives in
data/ruin_areas.py). Nothing mutates these tables: RuinConfig takes
per-plan copies, and ROOM_REWARD values stay abstract RewardType lists
(the live Reward slots are resolved by name in event/ruination_bind.py),
so they can be read at any time.
"""

from event.event_reward import RewardType

CHARACTER_LOCKED_REWARDS = {
    # Only rewards that literally cannot be obtained without the character, AND in areas that are accessible without them
    'TERRA': ['Whelk', 'Zozo'],  # 'LET05', 'Mobliz WOR'
    'LOCKE': ["Narshe WOR"],     # 'Phoenix Cave', 'South Figaro Cave'
    #'EDGAR': ['Figaro Castle WOR', 'Figaro Castle WOB'],
    'CELES': ["South Figaro"],   # South Figaro cell
    'SETZER': ["Kohlingen"],   # Kohlingen inn
    'STRAGO': ["Burning House"],  # Thamasa inn.  Technically, BH is not tied to the inn anymore.
    'MOG':  ["Lone Wolf", "Narshe Moogle Defense"], # Narshe
}
REWARDS_LOCKED_BY_CHARACTER = dict()
for clr in CHARACTER_LOCKED_REWARDS.keys():
    for reward in CHARACTER_LOCKED_REWARDS[clr]:
        REWARDS_LOCKED_BY_CHARACTER[reward] = clr

# Ruination area data
ROOM_REWARD = {
    # TERRA
    'UPNb08-ruin': {"Whelk": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Whelk in Narshe Mines.  Move to WOR?
    'LET05': {"Lete River": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Lete River boss
    'ZOZb21': {"Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Zozo WoB Ramuh reward
    #514: {"Sealed Gate": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Sealed Gate, not used in Ruination
    'MAPr-MOB': {"Mobliz WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Mobliz WoR.  Actually 'MOBr08' if interiors randomized.

    # LOCKE
    'NARr01-ruin': {"Narshe WOR": [RewardType.ESPER, RewardType.ITEM]},   # Narshe WOR weapon shop.  Actually 'NARr06' if interiors are randomized.
    'SFCb09': {"South Figaro Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # TunnelArmr spot
    'MAPr-PHO': {"Phoenix Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phoenix Cave (interior 1st room).  For outside platform: 'PHO52-branch'.  Need to modify exit: warp to esper world?

    # EDGAR
    'FIGr04-ruin': {"Figaro Castle WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],
                          "Figaro Castle WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Figaro Castle Throne Room + Engine Room checks
    'ANC13': {"Ancient Castle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Ancient Castle (dragon room).  AC starts at 520 or 'ANC-root'.

    # SABIN
    'IMP01-dc': {"Imperial Camp": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Imperial Camp
    'BAR50-ruin': {"Baren Falls": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Baren Falls, after boss but before shore
    'PHT12': {"Phantom Train": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phantom Train Caboose... boss is room 202
    'MTK07': {"Mt. Kolts": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Kolts
    'MAPr-TZE': {"Collapsing House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM], # Tzen WoR Collapsing house
                  "Tzen": [RewardType.ESPER, RewardType.ITEM]},   # Tzen thief (WOR).  WoB is 'MAPb-TZE'},
    
    # CELES
    'MAPr-SFI': {"South Figaro": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # South Figaro Basement  World of Ruin;  WOB is 'MAPb-SFI'.
    'MAPb-OPE': {"Opera House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Opera Disturbance WOB
    'MTF04-ruin': {"Magitek Factory_1": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 1
    'MTF08-ruin': {"Magitek Factory_2": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 2
    'MTF50-ruin': {"Magitek Factory_3": [RewardType.CHARACTER, RewardType.ESPER]},  # Magitek Factory 3, needs logical separation from Vector.  2nd boss where?
    
    # CYAN
    #'MAPb-DOM': {"Doma WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Doma Siege (non-ruination)
    'DOMb10': {"Doma WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Doma Siege (ruination)
    'DRM09': {"Doma WOR_3": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 3: stooges
    'CDC11-ruin': {"Doma WOR_1": [RewardType.CHARACTER, RewardType.ESPER]},  # Doma Dream 1: Wrexsoul
    'DOMr02-ruin': {"Doma WOR_2": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 2: throne (gated by Wrexsoul, though it's not a character so this doesn't affect gating)
    'MTZ07': {"Mt. Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Zozo
    
    # SHADOW
    'MAPb-GFH': {"Gau Father House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Gau's Dad's House
    'MAPb-FLO': {"Floating Continent_1": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],   # Floating Continent 1
                    "Floating Continent_2": [RewardType.ESPER, RewardType.ITEM],   # Floating Continent 2
                    "Floating Continent_3": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Floating Continent 3
    'COV08-ruin': {"Veldt Cave WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Cave on the Veldt
    
    # GAU
    'wor-veldt': {"Veldt": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Veldt (WOR theme)
    'NIKr52-ruin': {"Serpent Trench": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Serpent Trench, seeds logical separation from Nikeah.
    
    # SETZER
    'MAPr-KOH': {"Kohlingen": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Kohlingen Inn (force WOR)
    'DAR10-ruin': {"Daryl's Tomb": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Daryl's Tomb
    # 1: {"Doom Gaze": [RewardType.ESPER, RewardType.ITEM]},   # Doom Gaze, used elsewhere in -ruin
    
    # STRAGO
    'BUR09-ruin': {"Burning House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Burning House (room 465, end of BurningHouse dungeon)
    'MAPr-FAN': {"Fanatic's Tower": [RewardType.CHARACTER, RewardType.ESPER]},   # Fanatics Tower
    'MAPr-EBO': {"Ebot's Rock": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Ebot's Rock
    
    # RELM
    'ESM01': {"Esper Mountain": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Esper Mountain
    'OWZr08': {"Owzer Mansion": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Owzer's Basement
    
    # MOG
    'UPNr04-ruin': {"Tritoch": [RewardType.ESPER, RewardType.ITEM]},
    'NARr50-ruin': {"Lone Wolf": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Lone Wolf reward gated by lw1 key from ruin-narshe
    'NARb19': {"Narshe Moogle Defense": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Moogle Defense WOR (need to update how this starts); 65 in WOB

    # UMARO
    'UMA05': {"Umaro's Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Umaro's Den
    
    # GOGO
    'ZON07': {"Zone Eater": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Zone Eater
    
    # UNGATED
    # NOTE: room 22 is deliberately in NO RUIN_ROOM_SETS area, so "Narshe
    # Battle" is never claimable during map generation - it is always a dead
    # check backfilled by events.py. Intentional (HansGR): the WoB Snowfield
    # would mirror the WoR Snowfield (warp point + dragon), and its boss is
    # transposed to the Ferry Boss. Inclusion guidelines: ARCHIVE.md
    # "Narshe Battle Exclusion + Ruination Boss Budget".
    'UPNb03': {"Narshe Battle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Kefka @ Narshe
    #'UPNr04a': {"Tritoch": [RewardType.ESPER, RewardType.ITEM]},   # Tritoch
    #'MAPr-TZE': {"Tzen": [RewardType.ESPER, RewardType.ITEM]},   # Tzen thief (WOR).  WoB is 'MAPb-TZE'
    'JIDr01-dc': {"Auction House_1": [RewardType.ESPER, RewardType.ITEM],
              "Auction House_2": [RewardType.ESPER, RewardType.ITEM]},   # Jidoor WoR.  WOB is 'MAPb-JID'

}

# HOW to deal with cross-branch transport?
#(1) don't allow it.  Force certain areas to be in the same branch:
forced_same_branch = {
    'Zozo': {'ZozoTower', 'MtZozo'},
    'Thamasa': {'VeldtCave', 'EbotsRock', 'BurningHouse'},
    'Nikeah': {'CrescentMtn'}
}
for fsb in [f for f in forced_same_branch.keys()]:
    other_values = forced_same_branch[fsb]
    all_values = set([fsb]).union(other_values)
    for value in other_values:
        others = all_values.difference({value})
        forced_same_branch[value] = others
#(2) allow it.  Just don't track e.g. VeldtCave --> Thamasa, EbotsRock --> Thamasa.


# List of named areas associated with each character
CHARACTER_AREAS = {
    'TERRA': ['Narshe', 'ReturnersHideout', 'Zozo', 'ZozoTower', 'Mobliz', 'SealedGate'],
    'LOCKE': ['Kohlingen', 'PhoenixCave', 'SouthFigaroCave', 'Narshe'],
    'EDGAR': ['FigaroCastle', 'AncientCastle', 'SouthFigaro'],
    'SABIN': ['MtKolts', 'PhantomTrain', 'BarenFalls', 'ImperialCamp', 'Tzen'],
    'CELES': ['SouthFigaro', 'OperaHouse', 'Vector', 'Cid'],  # 'Albrook'
    'CYAN': ['Doma', 'DreamMaze', 'Zozo', 'MtZozo', 'Maranda'],
    'SHADOW': ['GauFatherHouse', 'FloatingContinent', 'VeldtCave', 'Thamasa'],
    'GAU': ['Veldt', 'CrescentMtn', 'Nikeah'],
    'SETZER': ['Kohlingen', 'DarylsTomb'],
    'STRAGO': ['Thamasa', 'BurningHouse', 'FanaticsTower', 'EbotsRock'],
    'RELM': ['Jidoor', 'EsperMountain'],
    'MOG': ['Narshe'],
    'GOGO': ['ZoneEater'],
    'UMARO': ['UmarosCave'],
    'ALL': ['Coliseum'],
    'EXTRA': ['ImperialCastle']
}

# Areas that are appended to a recruited character's `new_areas` during
# process_rewards iff their predicate (called as `predicate(ruination_map, new_char)`)
# is satisfied. distribute_areas filters out areas already in `self.AreasUsed`,
# but the helper also short-circuits to keep verbose logging clean.
#
# Add an entry here for any area that should be mapped on demand based on
# global mapping state (e.g. cooldowns, recruited commands) rather than being
# tied to a specific character's CHARACTER_AREAS list.
CONDITIONAL_AREAS = {
    # Duncan's House (Bum Rush teacher) — added when the planned Blitz character
    # is recruited (and the 50% inclusion roll passed at pre-plan time).
    'DuncanHouse': lambda rm, new_char: (
        rm.include_duncan_house and new_char == rm.duncan_house_character
    ),
    # Albrook is a two-exit pass-through town. Only add it when at least two
    # of the three branches have a zeroed town cooldown, so towns don't
    # cluster and Albrook isn't placed too early or too often.
    'Albrook': lambda rm, new_char: (
        sum(1 for b in rm.branches if b.town_cooldown == 0) >= 2
    ),
}

# All playable characters that can be obtained as rewards
ALL_CHARACTERS = ['TERRA', 'LOCKE', 'EDGAR', 'SABIN', 'CELES', 'CYAN', 'SHADOW',
                  'GAU', 'SETZER', 'STRAGO', 'RELM', 'MOG', 'GOGO', 'UMARO']

AREA_TYPES = {
    'TOWNS': ['Kohlingen', 'Jidoor', 'Maranda', 'Tzen', 'Albrook', 'Thamasa', 'Nikeah', 'Vector', 'SouthFigaro'],  # 'Mobliz', 'Narshe', # WOB only
}

# Towns whose RUIN_ROOM_SETS entry is a single room and which aren't tied to
# another area via forced_same_branch — these are spread across branches by
# distribute_areas instead of using the normal dispatch, so towns don't all
# pile up on one branch. Composite towns (Jidoor + Owzer's, Vector + Magitek)
# and forced-same-branch towns (Thamasa, Nikeah) are intentionally excluded;
# they place with their larger area.
STANDALONE_TOWNS = ['SouthFigaro', 'Kohlingen', 'Maranda', 'Tzen', 'Albrook']

# Rooms that contain a warp/save point (best-effort mapping from data/warps.WARP_POINTS).
# Used by the cooldown system in RuinationBranch to keep warp points from clustering
# near the hub or each other. May overlap with TOWN_ROOMS (e.g. 'MAPr-SFI' is both a
# warp point and the South Figaro town entry).
WARP_ROOMS = {
    'UPNr03',                # Snowfield WOR (Snow Battlefield WoR)
    'MAPr-SFI',       # SF_prison_cell -> South Figaro WOR (also a town)
    'MTK16',               # Mt. Kolts Save Point Room
    'RET02-ruin',  # Returners Hideout entry / save point
    'PHT11',               # Phantom Train Car 4 with Switch (Final Save Point Room = 221, if we switch)
    'OWZr06',               # Owzer's Basement Save Point Room
    'MTF06',               # Magitek Factory Save Point Room
    'ZON04',               # Zone Eater Save Point Room
    'DAR16',               # Darill's Tomb MIAB Hallway
    'DRM04',               # Doma Dream 3 Stooges Maze Middle Section
    'CDA08',               # Doma Dream Train 1st Car (map 0x142)
    'COV07',               # Veldt Cave Fifth Room
    'ESM10',               # Esper Mountain Falling Pit Room
    'ANC04',               # Ancient Cave Save Point Room
}

# Rooms that contain a town entry. One representative room per town area in
# AREA_TYPES['TOWNS']. For multi-room areas, picks the world-map-adjacent entry.
TOWN_ROOMS = {
    'MAPr-KOH',     # Kohlingen
    'JIDr01-dc',         # Jidoor (WOR world map entry; also covers Owzer's mansion exterior)
    'MAPr-MAR',     # Maranda
    'MAPr-TZE',     # Tzen
    'MAPr-ALB',     # Albrook
    'THAr01-ruin',  # Thamasa
    'NIKr01-ruin',   # Nikeah
    'VEC01-ruin',   # Vector (world-map entry room)
    'MAPr-SFI',     # South Figaro (also a warp point)
    'RET02-ruin',  # Returners Hideout (also a warp point)
}

# Build area-level reward locking:
# For each character-owned area, map rewards to the set of characters that provide access.
# A reward is area-locked if none of its area-owning characters are in the keychain.
# Could hypothetically read this data from Event.character_gate
REWARD_OWNERS = {
    "Whelk": frozenset(['TERRA']),
    "Lete River": frozenset(['TERRA']),
    "Zozo": frozenset(['TERRA']),
    "Mobliz WOR": frozenset(['TERRA']),
    "Narshe WOR": frozenset(['LOCKE']),
    "South Figaro Cave": frozenset(['LOCKE']),
    "Phoenix Cave": frozenset(['LOCKE']),
    "Figaro Castle WOB": frozenset(['EDGAR']),
    "Figaro Castle WOR": frozenset(['EDGAR']),
    "Ancient Castle": frozenset(['EDGAR']),
    "Imperial Camp": frozenset(['SABIN']),
    "Baren Falls": frozenset(['SABIN']),
    "Phantom Train": frozenset(['SABIN']),
    "Mt. Kolts": frozenset(['SABIN']),
    "Collapsing House": frozenset(['SABIN']),
    "South Figaro": frozenset(['CELES']),
    "Opera House": frozenset(['CELES']),
    "Magitek Factory_1": frozenset(['CELES']),
    "Magitek Factory_2": frozenset(['CELES']),
    "Magitek Factory_3": frozenset(['CELES']),
    "Doma WOB": frozenset(['CYAN']),
    "Doma WOR_2": frozenset(['CYAN']),
    "Doma WOR_1": frozenset(['CYAN']),
    "Doma WOR_3": frozenset(['CYAN']),
    "Mt. Zozo": frozenset(['CYAN']),
    "Gau Father House": frozenset(['SHADOW']),
    "Floating Continent_1": frozenset(['SHADOW']),
    "Floating Continent_2": frozenset(['SHADOW']),
    "Floating Continent_3": frozenset(['SHADOW']),
    "Veldt Cave WOR": frozenset(['SHADOW']),
    "Veldt": frozenset(['GAU']),
    "Serpent Trench": frozenset(['GAU']),
    "Kohlingen": frozenset(['SETZER']),
    "Daryl's Tomb": frozenset(['SETZER']),
    "Burning House": frozenset(['STRAGO']),
    "Fanatic's Tower": frozenset(['STRAGO']),
    "Ebot's Rock": frozenset(['STRAGO']),
    "Esper Mountain": frozenset(['RELM']),
    "Owzer Mansion": frozenset(['RELM']),
    "Lone Wolf": frozenset(['MOG']),
    "Narshe Moogle Defense": frozenset(['MOG']),
    "Umaro's Cave": frozenset(['UMARO']),
    "Zone Eater": frozenset(['GOGO'])
}  # reward_name -> frozenset of character name


# Maps ruination area names to shop IDs from data/shop_map_names.py
# Used to track which shops are accessible in ruination mode for dried meat assignment
AREA_SHOPS = {
    'Vector': [27, 28],                # WOB shops (weapon/armor, no item)
    'Kohlingen': [65, 66, 67],         # WOR shops (items/weapons/armor)
    'Nikeah': [56, 57, 58, 59],        # WOR shops
    'Thamasa': [72, 73, 74, 75],       # WOR shops
    'SouthFigaro': [60, 61, 62, 63],   # WOR shops
    'Albrook': [48, 49, 50, 51],       # WOR shops
    'Tzen': [52, 53, 54, 55],          # WOR shops
    'Jidoor': [76, 77, 78, 79],        # WOR shops (includes Owzer's mansion)
    'Maranda': [80, 81],               # WOR shops
    'FigaroCastle': [64, 84],          # WOR shops (left/right)
    'ReturnersHideout': [36],          # Item shop
    'PhantomTrain': [85],              # Vendor
    'GauFatherHouse': [39],            # Vendor (WOB map used in ruination)
}

RUIN_TERMINI = ['HUB52-ruin', 'HUB53-ruin', 'HUB54-ruin']  # list of terminal rooms for branches
