"""Pure ruination planning data (ROM-free).

Split out of event/ruination.py (Stage D) so the v2 planner can import the
area/reward tables without touching the ROM-coupled event machinery, mirroring
the data/ruin_areas.py split for RUIN_ROOM_SETS.

These tables are shared MUTABLE objects: event/ruination.py's
_reset_ruination_tables() restores them in place between map-generation
attempts, and events.ruination_mod binds ROOM_REWARD values to live Reward
slot objects before the legacy generator runs. Consumers that need pristine
data must read them before Events runs, or snapshot at import time as
event/ruination.py does.
"""

from event.event_reward import RewardType

CHARACTER_LOCKED_REWARDS = {
    # Only rewards that literally cannot be obtained without the character, AND in areas that are accessible without them
    'TERRA': ['Whelk', 'Zozo'],  # 'LeteRiver3', 'Mobliz WOR'
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
    'ruin-whelk': {"Whelk": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Whelk in Narshe Mines.  Move to WOR?
    'LeteRiver3': {"Lete River": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Lete River boss
    313: {"Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Zozo WoB Ramuh reward
    #514: {"Sealed Gate": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Sealed Gate, not used in Ruination
    'ms-wor-52': {"Mobliz WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Mobliz WoR.  Actually '237R' if interiors randomized.

    # LOCKE
    'ruin-narshe': {"Narshe WOR": [RewardType.ESPER, RewardType.ITEM]},   # Narshe WOR weapon shop.  Actually '25R' if interiors are randomized.
    104: {"South Figaro Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # TunnelArmr spot
    'ms-wor-1554': {"Phoenix Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phoenix Cave (interior 1st room).  For outside platform: 'branch-pc'.  Need to modify exit: warp to esper world?

    # EDGAR
    'ruin-figarocastle': {"Figaro Castle WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],
                          "Figaro Castle WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Figaro Castle Throne Room + Engine Room checks
    532: {"Ancient Castle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Ancient Castle (dragon room).  AC starts at 520 or 'root-ac'.

    # SABIN
    'dc-1501': {"Imperial Camp": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Imperial Camp
    'ruin-baren-reward': {"Baren Falls": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Baren Falls, after boss but before shore
    220: {"Phantom Train": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phantom Train Caboose... boss is room 202
    151: {"Mt. Kolts": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Kolts
    'ms-wor-51': {"Collapsing House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM], # Tzen WoR Collapsing house
                  "Tzen": [RewardType.ESPER, RewardType.ITEM]},   # Tzen thief (WOR).  WoB is 'ms-wob-33'},
    
    # CELES
    'ms-wor-58': {"South Figaro": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # South Figaro Basement  World of Ruin;  WOB is 'ms-wob-6'.
    'ms-wob-40': {"Opera House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Opera Disturbance WOB
    'ruin-mtek1': {"Magitek Factory_1": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 1
    'ruin-mtek2': {"Magitek Factory_2": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 2
    'ruin-mtek3': {"Magitek Factory_3": [RewardType.CHARACTER, RewardType.ESPER]},  # Magitek Factory 3, needs logical separation from Vector.  2nd boss where?
    
    # CYAN
    #'ms-wob-18': {"Doma WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Doma Siege (non-ruination)
    371: {"Doma WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Doma Siege (ruination)
    429: {"Doma WOR_3": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 3: stooges
    'ruin-wrexsoul': {"Doma WOR_1": [RewardType.CHARACTER, RewardType.ESPER]},  # Doma Dream 1: Wrexsoul
    'ruin-doma': {"Doma WOR_2": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 2: throne (gated by Wrexsoul, though it's not a character so this doesn't affect gating)
    256: {"Mt. Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Zozo
    
    # SHADOW
    'ms-wob-14': {"Gau Father House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Gau's Dad's House
    'ms-wob-1556': {"Floating Continent_1": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],   # Floating Continent 1
                    "Floating Continent_2": [RewardType.ESPER, RewardType.ITEM],   # Floating Continent 2
                    "Floating Continent_3": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Floating Continent 3
    'ruin-cotv': {"Veldt Cave WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Cave on the Veldt
    
    # GAU
    'wor-veldt': {"Veldt": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Veldt (WOR theme)
    'ruin-st-exit': {"Serpent Trench": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Serpent Trench, seeds logical separation from Nikeah.
    
    # SETZER
    'ms-wor-59': {"Kohlingen": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Kohlingen Inn (force WOR)
    'ruin-daryl': {"Daryl's Tomb": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Daryl's Tomb
    # 1: {"Doom Gaze": [RewardType.ESPER, RewardType.ITEM]},   # Doom Gaze, used elsewhere in -ruin
    
    # STRAGO
    'ruin-bh': {"Burning House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Burning House (room 465, end of BurningHouse dungeon)
    'ms-wor-69': {"Fanatic's Tower": [RewardType.CHARACTER, RewardType.ESPER]},   # Fanatics Tower
    'ms-wor-78': {"Ebot's Rock": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Ebot's Rock
    
    # RELM
    488: {"Esper Mountain": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Esper Mountain
    284: {"Owzer Mansion": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Owzer's Basement
    
    # MOG
    'ruin-narshepeak': {"Tritoch": [RewardType.ESPER, RewardType.ITEM]},
    'ruin-lonewolf': {"Lone Wolf": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Lone Wolf reward gated by lw1 key from ruin-narshe
    65: {"Narshe Moogle Defense": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Moogle Defense WOR (need to update how this starts); 65 in WOB

    # UMARO
    368: {"Umaro's Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Umaro's Den
    
    # GOGO
    363: {"Zone Eater": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Zone Eater
    
    # UNGATED
    22: {"Narshe Battle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Kefka @ Narshe
    #'41a': {"Tritoch": [RewardType.ESPER, RewardType.ITEM]},   # Tritoch
    #'ms-wor-51': {"Tzen": [RewardType.ESPER, RewardType.ITEM]},   # Tzen thief (WOR).  WoB is 'ms-wob-33'
    'dc-73': {"Auction House_1": [RewardType.ESPER, RewardType.ITEM],
              "Auction House_2": [RewardType.ESPER, RewardType.ITEM]},   # Jidoor WoR.  WOB is 'ms-wob-28'

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
# near the hub or each other. May overlap with TOWN_ROOMS (e.g. 'ms-wor-58' is both a
# warp point and the South Figaro town entry).
WARP_ROOMS = {
    40,                # Snowfield WOR (Snow Battlefield WoR)
    'ms-wor-58',       # SF_prison_cell -> South Figaro WOR (also a town)
    160,               # Mt. Kolts Save Point Room
    'ruin-returners',  # Returners Hideout entry / save point
    216,               # Phantom Train Car 4 with Switch (Final Save Point Room = 221, if we switch)
    282,               # Owzer's Basement Save Point Room
    352,               # Magitek Factory Save Point Room
    359,               # Zone Eater Save Point Room
    393,               # Darill's Tomb MIAB Hallway
    424,               # Doma Dream 3 Stooges Maze Middle Section
    436,               # Doma Dream Train 1st Car (map 0x142)
    474,               # Veldt Cave Fifth Room
    497,               # Esper Mountain Falling Pit Room
    523,               # Ancient Cave Save Point Room
}

# Rooms that contain a town entry. One representative room per town area in
# AREA_TYPES['TOWNS']. For multi-room areas, picks the world-map-adjacent entry.
TOWN_ROOMS = {
    'ms-wor-59',     # Kohlingen
    'dc-73',         # Jidoor (WOR world map entry; also covers Owzer's mansion exterior)
    'ms-wor-63',     # Maranda
    'ms-wor-51',     # Tzen
    'ms-wor-49',     # Albrook
    'ruin-thamasa',  # Thamasa
    'ruin-nikeah',   # Nikeah
    'ruin-vector',   # Vector (world-map entry room)
    'ms-wor-58',     # South Figaro (also a warp point)
    'ruin-returners',  # Returners Hideout (also a warp point)
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

RUIN_TERMINI = ['ruin_terminus_1', 'ruin_terminus_2', 'ruin_terminus_3']  # list of terminal rooms for branches
