from event.event import *
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from data.rooms import room_data, ruination_dont_force, shared_exits
from data.walks import *
from data.characters import Characters
import random
from log.verbose import vprint


class RuinationMappingError(Exception):
    """Raised when ruination map generation fails in an unrecoverable way.

    This exception indicates a bug or edge case that needs investigation.
    The message contains diagnostic information for troubleshooting.
    """
    pass


# Stuck reason constants - indicate WHY a branch cannot make progress
class StuckReason:
    """Reasons why a branch may be stuck and what connector types can fix it."""
    NONE = 'none'                    # Not stuck
    NO_EXITS = 'no_exits'            # No exits available at all
    NO_SAFE_EXITS = 'no_safe_exits'  # All exits filtered (would strand pits)
    NEED_PIDO = 'need_pido'          # Need pit-in, door-out room to receive trap
    NEED_PITS = 'need_pits'          # Have traps but no pits to receive them
    NEED_DOORS = 'need_doors'        # Have doors but no door entrances available
    NO_HUB = 'no_hub'                # No hub rooms available


def _room_has_pido_potential(room):
    """Check if a room can act as a PIDO (pit-in, door-out) connector.

    A PIDO room has at least one pit (to receive a trap connection) AND
    at least one door (to connect back upstream).
    """
    return len(room.pits) > 0 and len(room.doors) > 0


def _room_has_hub_potential(room):
    """Check if a room has hub potential (3+ doors+traps)."""
    return (len(room.doors) + len(room.traps)) >= 3


def _analyze_area_connectors(area_name, rooms_collection=None):
    """Analyze an area's rooms for connector potential.

    Args:
        area_name: Name of the area to analyze
        rooms_collection: Optional Rooms collection. If None, uses room_data directly.

    Returns dict with:
        - has_pido: True if area has any PIDO rooms
        - has_hub: True if area has any hub rooms
        - pido_count: Number of PIDO rooms
        - hub_count: Number of hub rooms
    """
    if area_name not in RUIN_ROOM_SETS:
        return {'has_pido': False, 'has_hub': False, 'pido_count': 0, 'hub_count': 0}

    room_ids = RUIN_ROOM_SETS[area_name]
    pido_count = 0
    hub_count = 0

    for room_id in room_ids:
        # Get room data - either from collection or directly from room_data
        if rooms_collection is not None:
            room = rooms_collection.get_room(room_id)
            if room is None:
                continue
            doors = room.doors
            traps = room.traps
            pits = room.pits
        else:
            # Use room_data directly
            if room_id not in room_data:
                continue
            data = room_data[room_id]
            doors = data[0] if len(data) > 0 else []
            traps = data[1] if len(data) > 1 else []
            pits = data[2] if len(data) > 2 else []

        # Check PIDO potential (pit-in, door-out)
        if len(pits) > 0 and len(doors) > 0:
            pido_count += 1
        # Check hub potential (3+ doors+traps)
        if (len(doors) + len(traps)) >= 3:
            hub_count += 1

    return {
        'has_pido': pido_count > 0,
        'has_hub': hub_count > 0,
        'pido_count': pido_count,
        'hub_count': hub_count
    }


ESPER_GATE_MAPID = 0x0da
NARSHE_SCHOOL_DOOR_IDS = [393, 394, 395]

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
    429: {"Doma WOR_2": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 1: stooges
    'ruin-wrexsoul': {"Doma WOR_1": [RewardType.CHARACTER, RewardType.ESPER]},  # Doma Dream 2: Wrexsoul
    'ruin-doma': {"Doma WOR_3": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 3: throne (gated by Wrexsoul, though it's not a character so this doesn't affect gating)
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

# List of rooms associated with each named area
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


_EXIT_TO_ROOM_OWNER = None
def _exit_to_room_owner(exit_id):
    # Lazily build and cache a map from an exit id to the room_data room that owns
    # it. Used to locate the partner room of a forced connection. Traps and pits
    # are unique to one room; doors may map to either side (irrelevant here, since
    # forced_connections only reference traps/pits).
    global _EXIT_TO_ROOM_OWNER
    if _EXIT_TO_ROOM_OWNER is None:
        owner = {}
        for rid, data in room_data.items():
            for group in data[:3]:
                if isinstance(group, (list, tuple, set)):
                    for e in group:
                        owner.setdefault(e, rid)
        _EXIT_TO_ROOM_OWNER = owner
    return _EXIT_TO_ROOM_OWNER.get(exit_id)


def _room_data_locks(rid):
    """Return a room_data entry's lock dict normalized to {tuple_of_keys: [items]}.

    room_data rooms are either the short 4-element form (no keys/locks) or the
    full 6-element form `[doors, traps, pits, start_keys, locks, world]`. Lock
    keys may be written as a bare string or a list/tuple; normalize to a tuple.
    """
    data = room_data.get(rid)
    if not data or len(data) < 6 or not isinstance(data[4], dict):
        return {}
    out = {}
    for k, items in data[4].items():
        ktuple = (k,) if isinstance(k, str) else tuple(k)
        out[ktuple] = items
    return out


def _room_data_start_keys(rid):
    """Return the unconditional starting keys a room_data entry grants."""
    data = room_data.get(rid)
    if not data or len(data) < 6:
        return []
    return [k for k in data[3] if isinstance(k, str)]


class RuinationBranch(Network):
    def __init__(self, rooms):
        super().__init__(rooms)
        self.dead_ends = []
        self.check_rooms = []
        # Track ALL rooms ever added, including those later merged into compound rooms.
        # This prevents re-adding a room that was already merged (and removed from net.nodes).
        self.all_rooms_added = set(rooms)
        # Track why this branch got stuck (if it did) - used for smart area distribution
        self.last_stuck_reason = StuckReason.NONE
        # Map compound room id -> list of original check_room ids merged into it.
        # Populated by compress_loop when ROOM_REWARD rooms are absorbed by a forced
        # connection (e.g., 4418<->744 fusing 371 and 'ruin-doma' into '371_ruin-doma').
        self._compound_check_rooms = {}
        # Cooldown counters that gate when warp/town rooms may be mapped onto this
        # branch. Decremented each time an unconnected room is mapped; reset to the
        # initial value (set on ruination_map) when the corresponding room type is
        # mapped. While > 0, the corresponding room type is excluded as a target.
        self.warp_cooldown = ruination_map.WARP_COOLDOWN_INITIAL
        self.town_cooldown = ruination_map.TOWN_COOLDOWN_INITIAL
        self.classify_rooms(rooms)

    def update_cooldowns(self, mapped_room_id):
        """Update warp/town cooldowns after an unconnected room is mapped onto the branch.

        Decrements both cooldowns (clamped at zero); if the newly-mapped room is a
        warp or town room, its corresponding cooldown is then reset to the initial
        value. Should be called once per unconnected room added to the branch.
        """
        if self.warp_cooldown > 0:
            self.warp_cooldown -= 1
        if self.town_cooldown > 0:
            self.town_cooldown -= 1
        if mapped_room_id in WARP_ROOMS:
            self.warp_cooldown = ruination_map.WARP_COOLDOWN_INITIAL
        if mapped_room_id in TOWN_ROOMS:
            self.town_cooldown = ruination_map.TOWN_COOLDOWN_INITIAL

    def compress_loop(self, loop_ids):
        # Capture which loop members were check_rooms BEFORE the base class drops them
        # from net/rooms. After the merge we need to re-point check_rooms (and the reward
        # tracking) at the new compound id, otherwise check_for_rewards never matches the
        # compound and the rewards are stranded.
        merged_check_rooms = [r for r in loop_ids if r in self.check_rooms]
        new_room = super().compress_loop(loop_ids)
        if new_room is not False and merged_check_rooms:
            for r in merged_check_rooms:
                self.check_rooms.remove(r)
            if new_room.id not in self.check_rooms:
                self.check_rooms.append(new_room.id)
            # Resolve each merged id to its original ROOM_REWARD components. If a member
            # was already a compound from a prior merge, inherit its components.
            components = []
            for r in merged_check_rooms:
                if r in self._compound_check_rooms:
                    components.extend(self._compound_check_rooms.pop(r))
                else:
                    components.append(r)
            existing = self._compound_check_rooms.get(new_room.id, [])
            for c in components:
                if c not in existing:
                    existing.append(c)
            self._compound_check_rooms[new_room.id] = existing
            if self.verbose:
                vprint(f'\tcompress_loop merged check_rooms {merged_check_rooms} '
                       f'-> compound {new_room.id} (components={existing})')
        return new_room

    def add_room(self, room_id):
        self.all_rooms_added.add(room_id)
        super().add_room(room_id)
        self.classify_rooms([room_id])
        #if self.verbose:
        #    print('added room:', room_id)
        # We need a custom handler for return from Lete River!
        if room_id == 'LeteRiver3':
            # add pit 3039 to ruin_hub
            hub_room_id = [n for n in self.net.nodes if 'ruin_hub' in str(n)][0]
            hub_room = self.rooms.get_room(hub_room_id)
            hub_room.add_pits([3039])
            if self.verbose:
                vprint('CUSTOM add pit 3039 to', hub_room_id, '!', hub_room.count, hub_room.pits)
            self.rooms.reindex_room(hub_room_id)

        # A room pulled from reserve during finalization (rescue/converter rooms)
        # may carry forced connections (hard-coded bridge jumps etc.); honor them
        # so the forced exit doesn't stay protected-but-unconnected (which would
        # keep its vanilla destination and leak into the unrandomized map).
        reserve_areas = getattr(self, '_active_reserve_areas', None)
        if reserve_areas is not None and not getattr(self, '_pulling_forced', False):
            self._honor_forced_connections(reserve_areas)

    def _honor_forced_connections(self, reserve_areas):
        # Apply forced connections for every *accessible* (live) forced exit in the
        # branch right now. A forced exit is live only when it sits in a placed
        # room's exit lists: a locked forced trap (e.g. Baren Falls behind Sabin,
        # Lone Wolf behind the lw1 key) becomes live exactly when its key is applied,
        # so this honors it precisely when the player can reach it and ignores it
        # while still locked. Two ways a forced exit becomes live after the initial
        # ForceConnections: a reserve room is added (rescue/converter), or a key
        # unlocks a trap mid-finalization. Partner rooms that are absent are pulled
        # from reserve when still available; ForceConnections then wires every live
        # pair whose partner is present (and is idempotent, since a connected forced
        # exit is removed from its room).
        if getattr(self, '_pulling_forced', False):
            return
        self._pulling_forced = True
        try:
            while True:
                pulled = False
                for node_id in list(self.net.nodes):
                    room = self.rooms.get_room(node_id)
                    if room is None:
                        continue
                    for d in list(room.traps) + list(room.doors):
                        if d not in forced_connections:
                            continue
                        for df in forced_connections[d]:
                            if self.rooms.get_room_from_element(df) is not None:
                                continue  # partner already present; will be wired
                            owner = _exit_to_room_owner(df)
                            if owner is None or owner in self.net.nodes:
                                continue
                            # Pull the partner only while it is still available in the
                            # shared reserve; otherwise it was consumed by another
                            # branch and adding it here would duplicate it.
                            for _area_name, area_rooms in reserve_areas:
                                if owner in area_rooms:
                                    area_rooms.remove(owner)
                                    self.add_room(owner)
                                    pulled = True
                                    break
                if not pulled:
                    break
            self.ForceConnections(forced_connections)
        finally:
            self._pulling_forced = False

    def classify_rooms(self, rooms):
        for room in rooms:
            if room in RUIN_TERMINI:
                self.terminus = room
                #print('...updated terminus: ', room)

            if self.is_dead_end(room):
                self.dead_ends.append(room)
                #print('...added dead end: ', room)

            if room in ROOM_REWARD.keys():
                self.check_rooms.append(room)
                #print('...added check room: ', room)

    def has_a_hub(self):
        # Check if this branch has a true hub (3+ doors+traps)
        possible_hubs = [node for node in self.net.nodes if (node not in self.dead_ends)]
        for node_id in possible_hubs:
            node = self.rooms.get_room(node_id)
            if len(node.doors) + len(node.traps) >= 3:
                return True
        return False

    def get_available_hubs(self, exclude=None):
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)
            #if self.verbose:
            #    print('Excluding...', exclude)
        # Exclude dead_ends and terminus (terminus is reserved for finalize_map step 4)
        available_hubs = [r for r in self.net.nodes
                         if (r not in self.dead_ends and r not in exclude and r != self.terminus)]
        #if self.verbose:
        #    print('Found available hubs:', available_hubs)
        return available_hubs

    def get_available_hub_connections(self, element_type=0, excluded=None, dito_ok=True):
        #if self.verbose:
        #    print('Excluding...', excluded)
        hub_ids = self.get_available_hubs(exclude=excluded)
        hub_conns = set()
        for hub_id in hub_ids:
            hub = self.rooms.get_room(hub_id)
            if element_type == 0:
                # Don't include pit-in, door-out doors (these are effectively dead ends for this purpose)
                if len(hub.doors) <= 1 and len(hub.traps) == 0:
                    pass
                    #if self.verbose:
                    #    print('skipping', hub_id, '(dead end or pit-in-door-out)')
                # Only include door-in, trap-out doors if allowed.
                elif (len(hub.doors) == 1 and len(hub.traps) >= 1 and len(hub.pits) == 0) and not dito_ok:
                    pass
                    #if self.verbose:
                    #    print('skipping', hub_id, '(door-in-trap-out, excluded)')
                else:
                    hub_conns.update([d for d in hub.doors if d not in self.protected])
            elif element_type == 1:
                hub_conns.update([p for p in hub.pits if p not in self.protected])
        return hub_conns

    def get_all_check_connections(self, element_type=0):
        conns = set()
        if self.verbose:
            vprint('Looking for check rooms...', self.check_rooms)
        for room_id in self.check_rooms:
            room = self.rooms.get_room(room_id)
            if element_type == 0:
                conns.update([d for d in room.doors if d not in self.protected])
            elif element_type == 1:
                conns.update([p for p in room.pits if p not in self.protected])
        return conns

    def get_all_unconnected_entrances(self, element_type, currently_used):
        """Get all available entrances from rooms not currently in the connected path.

        This is more permissive than get_available_hub_connections - it includes
        dead-end rooms and doesn't filter based on room topology.
        """
        entrances = set()
        for room_id in self.net.nodes:
            if room_id in currently_used:
                continue
            # Don't connect into the terminus - it's reserved for finalize_map step 4
            if room_id == self.terminus:
                continue
            room = self.rooms.get_room(room_id)
            if element_type == 0:
                # For doors, add all doors from unconnected rooms
                entrances.update([d for d in room.doors if d not in self.protected])
            elif element_type == 1:
                # For pits, add all pits from unconnected rooms
                entrances.update([p for p in room.pits if p not in self.protected])
        return entrances

    def count_available_elements(self, currently_used):
        """Count available exits and entrances not in the current path."""
        available_traps = 0
        available_doors_out = 0
        available_pits = 0
        available_doors_in = 0

        for room_id in self.net.nodes:
            if room_id in currently_used:
                continue
            room = self.rooms.get_room(room_id)
            available_traps += len([t for t in room.traps if t not in self.protected])
            available_pits += len([p for p in room.pits if p not in self.protected])
            available_doors_out += len([d for d in room.doors if d not in self.protected])
            available_doors_in += len([d for d in room.doors if d not in self.protected])

        return {
            'traps': available_traps,
            'pits': available_pits,
            'doors': available_doors_out  # doors can be both in and out
        }

    def validate_finalize_state(self, step_name, hub=None, remaining_doors=None,
                                  dead_ends=None, all_traps=None, all_pits=None):
        """Validate state during finalize_map and provide detailed diagnostics.

        This helps diagnose issues where door/trap/pit counts don't balance properly.
        """
        issues = []

        if hub is not None:
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub_obj = self.rooms.get_room(hub_id)

            # Count all elements in the hub network
            hub_doors = [d for d in hub_obj.doors if d not in self.protected]
            hub_traps = [t for t in hub_obj.traps if t not in self.protected]
            hub_pits = [p for p in hub_obj.pits if p not in self.protected]

            upstream = self.get_upstream_nodes(hub_id)
            downstream = self.get_downstream_nodes(hub_id)

            total_doors = len(hub_doors)
            total_traps = len(hub_traps)
            total_pits = len(hub_pits)

            for node in upstream:
                room = self.rooms.get_room(node)
                total_doors += len([d for d in room.doors if d not in self.protected])
                total_traps += len([t for t in room.traps if t not in self.protected])
                total_pits += len([p for p in room.pits if p not in self.protected])

            for node in downstream:
                room = self.rooms.get_room(node)
                total_doors += len([d for d in room.doors if d not in self.protected])
                total_traps += len([t for t in room.traps if t not in self.protected])
                total_pits += len([p for p in room.pits if p not in self.protected])

            if self.verbose:
                vprint(f'  [{step_name}] Hub network totals: doors={total_doors}, traps={total_traps}, pits={total_pits}')
                vprint(f'  [{step_name}] Hub {hub_id}: doors={hub_doors}, traps={hub_traps}, pits={hub_pits}')
                vprint(f'  [{step_name}] Upstream nodes: {list(upstream)}')
                vprint(f'  [{step_name}] Downstream nodes: {list(downstream)}')

        if remaining_doors is not None and dead_ends is not None:
            door_count = len(remaining_doors)
            dead_end_count = len(dead_ends)
            excess = door_count - dead_end_count

            if self.verbose:
                vprint(f'  [{step_name}] remaining_doors={door_count}, dead_ends={dead_end_count}, excess={excess}')

            if excess > 0 and excess % 2 == 1:
                issues.append(f'Odd excess doors ({excess}): will have orphan door after pairing')

        if all_traps is not None and all_pits is not None:
            trap_count = len(all_traps)
            pit_count = len(all_pits)

            if self.verbose:
                vprint(f'  [{step_name}] all_traps={trap_count}, all_pits={pit_count}')

            if trap_count > pit_count:
                issues.append(f'More traps ({trap_count}) than pits ({pit_count})')

        if issues and self.verbose:
            vprint(f'  [{step_name}] POTENTIAL ISSUES: {issues}')

        return issues

    def collect_network_traps_and_pits(self, include_doors=False, exclude_upstream_doors=False):
        """Collect all unconnected traps and pits from the entire connected network.

        Returns tuple: (all_traps, all_pits) or (all_traps, all_pits, all_doors) if include_doors=True.
        Each is a list of unconnected elements from hub + upstream + downstream nodes.

        Args:
            include_doors: If True, also return unconnected doors.
            exclude_upstream_doors: If True (and include_doors=True), exclude doors from upstream
                nodes. This is useful during finalization, where upstream rooms are inaccessible
                (only connected TO the hub via one-way pits) and their doors don't need connecting.
        """
        hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
        hub = self.rooms.get_room(hub_id)

        all_pits = [p for p in hub.pits if p not in self.protected]
        all_traps = [t for t in hub.traps if t not in self.protected]
        all_doors = [d for d in hub.doors if d not in self.protected] if include_doors else []

        upstream = self.get_upstream_nodes(hub_id)
        for node in upstream:
            room = self.rooms.get_room(node)
            all_pits.extend([p for p in room.pits if p not in self.protected])
            all_traps.extend([t for t in room.traps if t not in self.protected])
            # Upstream doors are inaccessible at finalization time, so optionally exclude them
            if include_doors and not exclude_upstream_doors:
                all_doors.extend([d for d in room.doors if d not in self.protected])

        downstream = self.get_downstream_nodes(hub_id)
        for node in downstream:
            room = self.rooms.get_room(node)
            all_pits.extend([p for p in room.pits if p not in self.protected])
            all_traps.extend([t for t in room.traps if t not in self.protected])
            if include_doors:
                all_doors.extend([d for d in room.doors if d not in self.protected])

        if include_doors:
            return all_traps, all_pits, all_doors
        return all_traps, all_pits

    def get_downstream_levels(self, hub_id):
        """Compute the 'level' (depth) of each downstream room from the hub.

        Returns a dict mapping room_id -> level, where level 0 is the hub itself.
        Level 1 rooms are directly connected from hub via trap->pit.
        Level 2 rooms are connected from level 1 rooms via trap->pit, etc.

        Also returns connection info: what trap/pit pairs connect each level.

        Uses get_downstream_paths for efficient traversal.
        """
        levels = {hub_id: 0}
        connections = {}  # (from_room, to_room) -> (trap, pit)

        # Build a map of trap->pit connections from self.map[1]
        trap_to_pit = {}
        pit_to_trap = {}
        for trap, pit in self.map[1]:
            trap_to_pit[trap] = pit
            pit_to_trap[pit] = trap

        # Use get_downstream_paths to get all paths from the hub
        paths = self.get_downstream_paths(hub_id)

        for path in paths:
            if not path:
                continue
            # Each path is a list of room_ids going downstream from hub
            for i, room_id in enumerate(path):
                if room_id not in levels:
                    levels[room_id] = i + 1  # Level 1 for first room in path, etc.

                # Find the connection that got us here
                if i == 0:
                    prev_room = hub_id
                else:
                    prev_room = path[i - 1]

                # Look for the trap->pit connection between prev_room and this room
                if (prev_room, room_id) not in connections:
                    # Find which trap/pit connected these rooms
                    prev_room_obj = self.rooms.get_room(prev_room)
                    curr_room_obj = self.rooms.get_room(room_id)
                    if prev_room_obj and curr_room_obj:
                        # Check all trap->pit connections to find the one linking these rooms
                        for trap, pit in self.map[1]:
                            trap_room = self.rooms.get_room_from_element(trap)
                            pit_room = self.rooms.get_room_from_element(pit)
                            # Handle compound rooms - check if IDs match or are substrings
                            trap_matches = (trap_room and trap_room.id == prev_room) or \
                                          (str(prev_room) in str(trap_room.id) if trap_room else False) or \
                                          (str(trap_room.id) if trap_room else '') in str(prev_room)
                            pit_matches = (pit_room and pit_room.id == room_id) or \
                                         (str(room_id) in str(pit_room.id) if pit_room else False) or \
                                         (str(pit_room.id) if pit_room else '') in str(room_id)
                            if trap_matches and pit_matches:
                                connections[(prev_room, room_id)] = (trap, pit)
                                break

        return levels, connections

    def get_local_upstream(self, room_id, hub_upstream):
        """Get rooms that are upstream of a specific room but NOT upstream of the hub.

        This identifies 'local upstream' created by forced connections in downstream rooms.
        These are rooms reachable by going backwards from a downstream room that aren't
        part of the hub's own upstream topology.

        Returns a list of (room_id, connection_info) tuples.
        """
        local_upstream = []
        room_upstream = self.get_upstream_nodes(room_id)

        for up_room in room_upstream:
            if up_room not in hub_upstream and 'ruin_hub_' not in str(up_room):
                # This is local upstream - find how it connects
                connection_info = None
                # Check for trap->pit connections (this room's pit connects to up_room's trap)
                for trap, pit in self.map[1]:
                    pit_room = self.rooms.get_room_from_element(pit)
                    trap_room = self.rooms.get_room_from_element(trap)
                    if pit_room and trap_room:
                        if (str(room_id) in str(pit_room.id) or pit_room.id == room_id) and \
                           (str(up_room) in str(trap_room.id) or trap_room.id == up_room):
                            connection_info = ('trap->pit', trap, pit)
                            break
                # Check for door connections
                if connection_info is None:
                    for door1, door2 in self.map[0]:
                        d1_room = self.rooms.get_room_from_element(door1)
                        d2_room = self.rooms.get_room_from_element(door2)
                        if d1_room and d2_room:
                            if (str(room_id) in str(d1_room.id) or d1_room.id == room_id) and \
                               (str(up_room) in str(d2_room.id) or d2_room.id == up_room):
                                connection_info = ('door', door1, door2)
                                break
                            elif (str(room_id) in str(d2_room.id) or d2_room.id == room_id) and \
                                 (str(up_room) in str(d1_room.id) or d1_room.id == up_room):
                                connection_info = ('door', door2, door1)
                                break

                local_upstream.append((up_room, connection_info))

        return local_upstream

    # ===== LOCATION-AWARE BRANCH MAPPING HELPERS =====
    # These methods support the new topology-aware extend_branch_path algorithm

    def get_hub_id(self):
        """Find the hub room ID for this branch."""
        hub_candidates = [n for n in self.net.nodes if 'ruin_hub_' in str(n)]
        if hub_candidates:
            return hub_candidates[0]
        return None

    def classify_topology(self):
        """Classify all connected rooms into Hub, Upstream, and Downstream regions.

        Returns:
            dict with keys:
                - 'hub_id': The hub room ID
                - 'hub_and_upstream': Set of room IDs in hub + upstream (reachable from hub)
                - 'downstream_by_level': Dict mapping level (1, 2, ...) to list of room IDs
                - 'room_levels': Dict mapping room_id to its level (0 = hub, -1 = upstream, 1+ = downstream)
        """
        hub_id = self.get_hub_id()
        if hub_id is None:
            return None

        # Get upstream (rooms with paths leading TO the hub)
        upstream = set(self.get_upstream_nodes(hub_id))

        # Get downstream levels
        levels, _ = self.get_downstream_levels(hub_id)

        # Classify all rooms
        room_levels = {}
        room_levels[hub_id] = 0
        for u in upstream:
            room_levels[u] = -1  # Upstream is level -1

        downstream_by_level = {}
        for room_id, level in levels.items():
            if level > 0:
                room_levels[room_id] = level
                if level not in downstream_by_level:
                    downstream_by_level[level] = []
                downstream_by_level[level].append(room_id)

        return {
            'hub_id': hub_id,
            'hub_and_upstream': {hub_id} | upstream,
            'downstream_by_level': downstream_by_level,
            'room_levels': room_levels,
            'upstream': upstream
        }

    def get_room_level(self, room_id, topology=None):
        """Get the level of a room in the topology.

        Returns:
            0 for hub, -1 for upstream, 1+ for downstream, None if not connected.
        """
        if topology is None:
            topology = self.classify_topology()
        if topology is None:
            return None
        return topology['room_levels'].get(room_id)

    def count_exits_in_region(self, room_ids):
        """Count total unprotected doors and traps in a set of rooms.

        Returns (door_count, trap_count).
        """
        door_count = 0
        trap_count = 0
        for room_id in room_ids:
            room = self.rooms.get_room(room_id)
            if room:
                door_count += len([d for d in room.doors if d not in self.protected])
                trap_count += len([t for t in room.traps if t not in self.protected])
        return door_count, trap_count

    def count_entrances_in_region(self, room_ids):
        """Count total unprotected doors and pits in a set of rooms.

        Returns (door_count, pit_count).
        """
        door_count = 0
        pit_count = 0
        for room_id in room_ids:
            room = self.rooms.get_room(room_id)
            if room:
                door_count += len([d for d in room.doors if d not in self.protected])
                pit_count += len([p for p in room.pits if p not in self.protected])
        return door_count, pit_count

    def classify_unconnected_room(self, room_id):
        """Classify an unconnected room by its connector type.

        Returns one of:
            'PITO': pit-in, trap-out (has pits and traps, can extend downstream)
            'PIDO': pit-in, door-out (has pits and doors, can reconnect to upstream)
            'DITO': door-in, trap-out (has doors and traps, can convert door path to trap)
            'DIDO': door-in, door-out (has only doors, forms door loops)
            'DEAD_END': only one door, no other exits
            'HUB': has 3+ doors+traps, can become a hub
            'OTHER': doesn't fit neat categories
        """
        room = self.rooms.get_room(room_id)
        if room is None:
            return 'OTHER'

        doors = len([d for d in room.doors if d not in self.protected])
        traps = len([t for t in room.traps if t not in self.protected])
        pits = len([p for p in room.pits if p not in self.protected])

        # Check for hub potential first
        if doors + traps >= 3:
            return 'HUB'

        # Dead end check
        if doors == 1 and traps == 0 and pits == 0:
            return 'DEAD_END'

        # Connector type classification
        has_pit_in = pits > 0
        has_door_in = doors > 0
        has_trap_out = traps > 0
        has_door_out = doors > 0  # doors can be both in and out

        if has_pit_in and has_trap_out:
            return 'PITO'
        elif has_pit_in and has_door_out and not has_trap_out:
            return 'PIDO'
        elif has_door_in and has_trap_out and not has_pit_in:
            return 'DITO'
        elif has_door_in and has_door_out:
            return 'DIDO'

        return 'OTHER'

    def is_true_dead_end(self, room_id):
        """Check if a room is a 'true dead end' that should be deferred to finalize_map.

        A true dead end has:
        - Only 1 door (no traps, no pits)
        - No keys
        - No locks
        - No checks (rewards)

        These rooms can be safely connected later in finalize_map, so we shouldn't
        waste exits connecting them during extend_branch_path.
        """
        room = self.rooms.get_room(room_id)
        if room is None:
            return False

        # Check room type first - must be DEAD_END (only 1 door, no traps, no pits)
        room_type = self.classify_unconnected_room(room_id)
        if room_type != 'DEAD_END':
            return False

        # Check for downstream rooms (from forced connections in the graph).
        # A room that leads to other rooms via forced connections is not truly
        # a dead end, even if it has only one local door (e.g., dc-15 in Baren
        # Falls has a forced trap leading to ruin-baren which has 2 door exits).
        if len(list(self.net.successors(room_id))) > 0:
            return False

        # Check for keys
        if len(room.keys) > 0:
            return False

        # Check for locks
        if len(room.locks) > 0:
            return False

        # Check for checks (rewards)
        if room_id in self.check_rooms:
            return False

        return True

    def would_strand_pits(self, exit_id, room):
        """Check if using this exit would strand pits (leave them unreachable).

        Returns True if using this exit would leave the room with pits but no exits.

        NOTE: This method is kept for debugging but is no longer used in extend_branch_path.
        The "would strand" check was too restrictive because it only evaluated the source
        room, not the destination. The correct approach (now implemented) is to check each
        potential CONNECTION to see if the destination provides a valid continuation path.
        """
        doors = [d for d in room.doors if d not in self.protected]
        traps = [t for t in room.traps if t not in self.protected]
        pits = [p for p in room.pits if p not in self.protected]

        # Count exits after using this one
        if exit_id in doors:
            remaining_exits = len(doors) - 1 + len(traps)
        elif exit_id in traps:
            remaining_exits = len(doors) + len(traps) - 1
        else:
            # remaining_exits = len(doors) + len(traps)
            # error, all exits are either doors or traps.
            raise Exception

        # Would strand if: remaining exits = 0 AND pits > 0
        return remaining_exits == 0 and len(pits) > 0

    def find_escape_route_exits(self, room_id, topology):
        """Find exits that could escape from a downstream room back to hub/upstream.

        For a room at downstream level N, looks for:
        - Doors that could connect to hub/upstream doors
        - Traps that could connect to pits in rooms upstream of this room

        Returns dict with 'doors' and 'traps' lists of exit IDs that could provide escape.
        """
        hub_and_upstream = topology['hub_and_upstream']
        room_level = topology['room_levels'].get(room_id, 0)

        room = self.rooms.get_room(room_id)
        if room is None:
            return {'doors': [], 'traps': []}

        doors = [d for d in room.doors if d not in self.protected]
        traps = [t for t in room.traps if t not in self.protected]

        # Any door can potentially connect back (doors are bidirectional)
        escape_doors = doors

        # Traps can only escape if there are upstream pits to connect to
        escape_traps = []
        # Check hub and upstream for pits
        for up_id in hub_and_upstream:
            up_room = self.rooms.get_room(up_id)
            if up_room and len([p for p in up_room.pits if p not in self.protected]) > 0:
                escape_traps = traps  # All traps could potentially escape
                break

        return {'doors': escape_doors, 'traps': escape_traps}

    def get_valid_pit_targets(self, trap_exit, exit_room_id, topology):
        """Get valid pit targets for a trap exit, respecting topology rules.

        Rules applied:
        0. Never connect to last entrance to hub/upstream
        1. Can connect to PITO room (kicks the can down the road)
        2a. Can connect to PIDO room if branch has exits after
        3. Can connect to upstream pit ONLY IF loop compression leaves exits
        GLOBAL: Never make a connection that leaves the branch with zero exits
        ONLY-TRAP-PIT: If branch has exactly 1 trap, 1 pit, and 0 doors,
                       don't connect them (must find unconnected room instead)

        Returns list of valid pit IDs.
        """
        valid_pits = []
        hub_and_upstream = topology['hub_and_upstream']
        room_levels = topology['room_levels']
        room_level = room_levels.get(exit_room_id, 0)
        exit_room = self.rooms.get_room(exit_room_id)

        # NOTE: We intentionally do NOT pre-filter exits based on whether the source room
        # would be "stranded" (left with no exits). Instead, we check each potential
        # CONNECTION to see if the destination provides a valid continuation path.
        # A trap exit from a room with no other exits is still valid if the destination
        # room has its own exits (e.g., connecting to a PITO room that has traps).

        # === GLOBAL PROTECTION: Count total exits in connected branch ===
        # Using this trap consumes 1 exit. We must ensure the branch still has exits after.
        connected_rooms = set(room_levels.keys())
        current_doors, current_traps = self.count_exits_in_region(connected_rooms)
        current_total_exits = current_doors + current_traps
        # After using this trap: current_total_exits - 1
        # For the connection to be valid, we need: (current_total_exits - 1) + dest_room_exits > 0
        # For loops (destination in connected branch): dest_room_exits = 0
        # For new rooms: dest_room_exits = destination room's doors + traps

        # Count doors available in hub/upstream (for rule 2a)
        hub_upstream_doors, _ = self.count_exits_in_region(hub_and_upstream)

        # NEW FILTER: Check if this is the only trap and only pit scenario
        # If the branch has exactly 1 trap (exit) and only pits in hub/upstream,
        # AND no doors, connecting them would strand the branch with no exits and no entrances.
        # If there are doors, they provide both exits and entrances, so it's OK to connect.
        _, total_hub_upstream_pits = self.count_entrances_in_region(hub_and_upstream)
        is_only_trap_and_pits = (current_traps == 1 and total_hub_upstream_pits >= 1 and current_doors == 0)

        # Get upstream pits of the exit room (for rule 3)
        local_upstream = self.get_upstream_nodes(exit_room_id)
        local_upstream_pits = set()
        for up_id in local_upstream:
            up_room = self.rooms.get_room(up_id)
            if up_room:
                local_upstream_pits.update([p for p in up_room.pits if p not in self.protected])

        # Include hub/upstream pits
        hub_upstream_pits = set()
        for h_id in hub_and_upstream:
            h_room = self.rooms.get_room(h_id)
            if h_room:
                hub_upstream_pits.update([p for p in h_room.pits if p not in self.protected])

        # === RULE 3: Connecting to upstream pits ===
        # Can connect to local upstream (not hub's upstream) IF loop compression leaves exits
        for pit_id in local_upstream_pits:
            if pit_id in self.protected:
                continue
            pit_room = self.rooms.get_room_from_element(pit_id)
            if pit_room is None:
                continue

            # NEW FILTER: Skip if this is the only trap connecting to an upstream pit
            if is_only_trap_and_pits:
                continue  # Must find an unconnected room that adds entrances/exits

            # If pit is in hub/upstream, check rule 0 (not last entrance)
            if pit_room.id in hub_and_upstream:
                hub_doors, hub_pits = self.count_entrances_in_region(hub_and_upstream)
                total_entrances = hub_doors + hub_pits
                if total_entrances <= 1:
                    continue  # Rule 0: don't use last entrance to hub/upstream

            # GLOBAL PROTECTION: Loop connections don't add new exits to the branch.
            # After using this trap, we lose 1 exit and gain 0 new exits.
            # Only allow if the branch would still have exits.
            if current_total_exits <= 1:
                continue  # This is the last exit; can't connect to an already-connected room

            # Check if loop compression would leave exits
            # After connecting trap->pit, the rooms from exit_room up to pit_room compress
            # Need to check if the compressed room has exits
            #
            # Example: Level 2 has trap 2005, Level A has pit 3003
            # If Level A -> Level 2 already exists (via 2007->3007),
            # then connecting 2005->3003 creates loop: Level 2 -> Level A -> Level 2
            # All rooms in the loop (Level 2, Level A) compress into one room.
            # We need exits > 0 after compression.

            # Collect all rooms that would be in the loop
            # Start with exit_room, then add all rooms on paths to pit_room (including pit_room)
            loop_rooms = {exit_room_id}
            paths = self.get_upstream_paths(exit_room_id)
            found_pit_room = False
            for path in paths:
                for node in path:
                    loop_rooms.add(node)
                    # Check if this node IS the pit_room or CONTAINS the pit_room (compound room)
                    if node == pit_room.id or str(pit_room.id) in str(node):
                        found_pit_room = True
                        break
                if found_pit_room:
                    break

            # Always include the pit_room itself (it must be in the loop)
            loop_rooms.add(pit_room.id)

            # Count exits in all loop rooms (excluding the trap we're using)
            loop_doors = 0
            loop_traps = 0
            for r_id in loop_rooms:
                r = self.rooms.get_room(r_id)
                if r:
                    loop_doors += len([d for d in r.doors if d not in self.protected])
                    loop_traps += len([t for t in r.traps if t not in self.protected])

            # Subtract the trap we're using
            loop_traps -= 1

            if loop_doors + loop_traps > 0:
                valid_pits.append(pit_id)

        # === Check unconnected rooms ===
        currently_connected = set(topology['room_levels'].keys())

        for room_id in self.net.nodes:
            if room_id in currently_connected:
                continue
            if room_id == self.terminus:
                continue  # Reserve terminus for finalize_map

            room = self.rooms.get_room(room_id)
            if room is None:
                continue

            room_type = self.classify_unconnected_room(room_id)
            room_pits = [p for p in room.pits if p not in self.protected]
            room_traps = [t for t in room.traps if t not in self.protected]
            room_doors = [d for d in room.doors if d not in self.protected]

            if len(room_pits) == 0:
                continue  # No pits to receive the trap

            # === RULE 1: PITO rooms (can kick the can down the road) ===
            if room_type == 'PITO' or (len(room_pits) > 0 and len(room_traps) > 0):
                # This room can receive the trap and continue downstream with its own trap
                valid_pits.extend(room_pits)
                continue

            # === RULE 2a: PIDO rooms ===
            # A PIDO room (pit-in, door-out) can receive a trap if the branch still has exits after.
            # After connecting: we lose 1 trap exit, but gain the new room's exits.
            # New doors can then connect to other rooms (including DITO rooms whose traps
            # can loop back to upstream pits), so we don't require hub to already have doors.
            if room_type == 'PIDO' or (len(room_pits) > 0 and len(room_doors) > 0 and len(room_traps) == 0):
                exits_after_connection = (current_total_exits - 1) + len(room_doors)
                if exits_after_connection > 0:
                    valid_pits.extend(room_pits)
                continue

            # === RULE: HUB rooms ===
            if room_type == 'HUB':
                # Hub rooms have enough exits to handle downstream
                valid_pits.extend(room_pits)
                continue

        # === Connect to hub/upstream pits (forms loop, compresses to hub) ===
        # GLOBAL PROTECTION: Loop connections don't add new exits to the branch.
        # Only allow if the branch would still have exits after using this trap.
        # Also skip entirely if this is the only trap connecting to the only pit.
        if current_total_exits > 1 and not is_only_trap_and_pits:
            for pit_id in hub_upstream_pits:
                if pit_id in self.protected:
                    continue
                # Rule 0 check: not the last entrance (must have entrances remaining)
                hub_doors, hub_pits = self.count_entrances_in_region(hub_and_upstream)
                total_entrances = hub_doors + hub_pits
                if total_entrances <= 1:
                    continue
                if pit_id not in valid_pits:
                    valid_pits.append(pit_id)

        return valid_pits

    def get_valid_door_targets(self, door_exit, exit_room_id, topology, available_doors=None, available_traps=None):
        """Get valid door targets for a door exit, respecting topology rules.

        Rules applied:
        0. Never connect to last door in hub/upstream (until finalize)
        2b. If unconnected pit in hub/upstream, can connect to DITO room
        GLOBAL: Never make a connection that leaves the branch with zero exits

        Args:
            door_exit: The door ID being used for exit
            exit_room_id: The room containing the exit door
            topology: Branch topology dict
            available_doors: Count of available doors at current level (optional, for stricter check)
            available_traps: Count of available traps at current level (optional, for stricter check)

        Returns list of valid door IDs.
        """
        valid_doors = []
        hub_and_upstream = topology['hub_and_upstream']
        room_levels = topology['room_levels']

        # === GLOBAL PROTECTION: Count total exits in connected branch ===
        # Using this door consumes 1 exit. We must ensure the branch still has exits after.
        connected_rooms = set(room_levels.keys())
        current_doors, current_traps = self.count_exits_in_region(connected_rooms)
        current_total_exits = current_doors + current_traps

        # Count pits available in hub/upstream (for rule 2b)
        _, hub_upstream_pits = self.count_entrances_in_region(hub_and_upstream)

        # === Check unconnected rooms ===
        currently_connected = set(topology['room_levels'].keys())

        for room_id in self.net.nodes:
            if room_id in currently_connected:
                continue
            if room_id == self.terminus:
                continue  # Reserve terminus for finalize_map

            room = self.rooms.get_room(room_id)
            if room is None:
                continue

            room_type = self.classify_unconnected_room(room_id)
            room_doors = [d for d in room.doors if d not in self.protected]
            room_traps = [t for t in room.traps if t not in self.protected]
            room_pits = [p for p in room.pits if p not in self.protected]

            if len(room_doors) == 0:
                continue  # No doors to connect to

            # === RULE 2b: DITO rooms (if hub/upstream has pits) ===
            if room_type == 'DITO' or (len(room_doors) > 0 and len(room_traps) > 0 and len(room_pits) == 0):
                if hub_upstream_pits > 0:
                    # Hub/upstream has pits to receive the new trap path
                    valid_doors.extend(room_doors)
                continue

            # Door-only rooms (DIDO, HUB, connectors) can always be connected
            if room_type in ['DIDO', 'HUB'] or (len(room_doors) >= 2):
                valid_doors.extend(room_doors)
                continue

            # Dead-end rooms with single door - skip true dead ends, defer to finalize_map
            if room_type == 'DEAD_END':
                # Skip true dead ends (no keys, no locks, no checks) - connect them in finalize_map
                if self.is_true_dead_end(room_id):
                    continue
                # GLOBAL PROTECTION: Dead-end rooms add no new exits.
                # Using our door (-1) and connecting to a room with 0 other exits = -1 total.
                # Only allow if we have other exits remaining.
                #
                # When available_doors/available_traps are provided, use stricter check:
                # - Need at least 2 doors at current level (one for dead-end, one remaining), OR
                # - Need 1 door + trap AND hub/upstream has pit (loop can be closed)
                if available_doors is not None and available_traps is not None:
                    # Stricter current-level check
                    has_enough_exits = (
                        available_doors >= 2 or
                        (available_doors >= 1 and available_traps >= 1 and hub_upstream_pits > 0)
                    )
                    if has_enough_exits:
                        valid_doors.extend(room_doors)
                elif current_total_exits > 1:
                    # Fallback to original check if available counts not provided
                    valid_doors.extend(room_doors)

        # === Connect to upstream/hub doors (forms loop) ===
        # Loop connections consume TWO exits: the source door AND the target door.
        # CRITICAL: Only count exits from rooms that will be usable after the connection:
        #   - Source-side: active path exits (available_doors + available_traps)
        #   - Target-side: exits in the target room h_id (absorbed into hub after connection)
        # Exits in OTHER upstream rooms are NOT usable by extend_branch_path, so don't count them.
        if current_total_exits > 2:  # Quick pre-filter (necessary condition)
            for h_id in hub_and_upstream:
                h_room = self.rooms.get_room(h_id)
                if h_room:
                    h_doors = [d for d in h_room.doors if d not in self.protected]
                    # Rule 0: check not last entrance (must have entrances remaining)
                    hub_doors, hub_pits = self.count_entrances_in_region(hub_and_upstream)
                    total_entrances = hub_doors + hub_pits
                    if total_entrances > 1:  # Leave at least one entrance
                        # Count exits from target room (will be absorbed after connection)
                        h_exits_doors, h_exits_traps = self.count_exits_in_region({h_id})
                        h_total_exits = h_exits_doors + h_exits_traps

                        for d in h_doors:
                            if d == door_exit:  # Don't connect to self
                                continue
                            # Per-target check: after consuming door_exit and d,
                            # are there still usable exits?
                            if available_doors is not None and available_traps is not None:
                                if h_id == exit_room_id:
                                    # Source and target in same room - exits overlap
                                    remaining = (available_doors + available_traps) - 2
                                else:
                                    # Different rooms - independent exit pools
                                    remaining = (available_doors + available_traps - 1) + (h_total_exits - 1)
                                if remaining <= 0:
                                    continue  # Would leave no usable exits
                            elif current_total_exits <= 2:
                                continue  # Fallback: not enough exits
                            valid_doors.append(d)

        return valid_doors

    def get_valid_pit_targets_v2(self, trap_exit, exit_room_id, topology):
        """V2: Get valid pit targets by directly assessing each connection's result.

        Instead of classifying room types and applying categorical rules, this method
        directly evaluates whether each potential connection maintains branch invariants:
        - Downstream of active room must have >= 1 exit after connection
        - Hub+upstream must have >= 1 entrance after connection (for loop connections)

        Rules:
        A1. Unconnected target: target room (+ its downstream forced rooms) must have
            exits (doors+traps) > 0. If exits are only in downstream rooms, hub+upstream
            must also have an entrance. (The consumed pit is not an exit.)
        B1. Connected target: (target + target's downstream) must have at least one
            exit that is not the selected exit (trap_exit).
        C.  Hub/upstream target (loop): additionally, (exit room + exit room's upstream)
            must have at least one entrance that is not the target pit.

        Returns list of valid pit IDs.
        """
        valid_pits = []
        hub_and_upstream = topology['hub_and_upstream']
        room_levels = topology['room_levels']
        currently_connected = set(room_levels.keys())

        # Pre-compute upstream rooms for rule C (lazy, only if needed)
        _upstream_room_cache = None

        def get_exit_upstream_rooms():
            nonlocal _upstream_room_cache
            if _upstream_room_cache is None:
                paths = self.get_upstream_paths(exit_room_id)
                _upstream_room_cache = set()
                for path in paths:
                    _upstream_room_cache.update(path)
            return _upstream_room_cache

        # Pre-compute hub+upstream entrance count for rule A1 hub entrance check.
        # Used both for the existing hub check (exit from hub/upstream) and for the
        # downstream-only exit check (where hub must retain an entrance regardless).
        exit_is_hub_upstream = exit_room_id in hub_and_upstream
        hub_upstream_doors, hub_upstream_pits = self.count_entrances_in_region(hub_and_upstream)
        hub_upstream_entrances = hub_upstream_doors + hub_upstream_pits

        for room_id in self.net.nodes:
            if room_id == self.terminus:
                continue

            room = self.rooms.get_room(room_id)
            if room is None:
                continue

            room_pits = [p for p in room.pits if p not in self.protected]
            if not room_pits:
                continue

            is_connected = room_id in currently_connected

            if not is_connected:
                # === A1: Unconnected room ===
                # Cooldown gating: warp/town rooms can only be mapped when the
                # corresponding cooldown has run down to zero.
                if room_id in WARP_ROOMS and self.warp_cooldown > 0:
                    continue
                if room_id in TOWN_ROOMS and self.town_cooldown > 0:
                    continue
                # Connection consumes trap_exit from exit room and a pit from target room.
                # Pit is not an exit, so target room exits are unaffected.
                # Legal if target room has at least one exit (door or trap).
                target_exits = (
                    len([d for d in room.doors if d not in self.protected])
                    + len([t for t in room.traps if t not in self.protected])
                )
                if target_exits > 0:
                    # Check that at least one exit was originally free (not unlocked
                    # by apply_key). If all exits were key-unlocked, the player could
                    # enter via pit before obtaining the keys and be trapped.
                    originally_free_exits = (
                        len([d for d in room.doors if d not in self.protected
                             and d not in self.initially_locked_exits])
                        + len([t for t in room.traps if t not in self.protected
                               and t not in self.initially_locked_exits])
                    )
                    if originally_free_exits == 0:
                        continue  # All exits were key-unlocked; player could be trapped

                    # A1-hub check: If exit is from hub/upstream, hub must retain
                    # at least 1 entrance (door or pit) so downstream nodes can
                    # reconnect during finalize_map. Trap consumption doesn't
                    # affect entrances, so we check the pre-computed count.
                    if exit_is_hub_upstream and hub_upstream_entrances == 0:
                        continue
                    valid_pits.extend(room_pits)
                elif target_exits == 0:
                    # No local exits, but downstream rooms (from forced connections)
                    # may have exits (same pattern as A2 downstream check for doors).
                    downstream_paths = self.get_downstream_paths(room_id)
                    downstream_rooms = set()
                    for path in downstream_paths:
                        downstream_rooms.update(path)
                    if downstream_rooms:
                        downstream_exits = 0
                        downstream_free_exits = 0
                        for rid in downstream_rooms - {room_id}:
                            r = self.rooms.get_room(rid)
                            if r:
                                downstream_exits += (
                                    len([d for d in r.doors if d not in self.protected])
                                    + len([t for t in r.traps if t not in self.protected]))
                                downstream_free_exits += (
                                    len([d for d in r.doors if d not in self.protected
                                         and d not in self.initially_locked_exits])
                                    + len([t for t in r.traps if t not in self.protected
                                           and t not in self.initially_locked_exits]))
                        if downstream_exits > 0 and downstream_free_exits > 0:
                            # Exits are only downstream (through forced connections),
                            # so hub+upstream must retain an entrance for looping back.
                            if hub_upstream_entrances > 0:
                                valid_pits.extend(room_pits)
            else:
                # === B1: Connected room ===
                # (target room + target's downstream) must have at least one exit
                # that is not the selected exit (trap_exit).
                downstream_paths = self.get_downstream_paths(room_id)
                downstream_rooms = set()
                for path in downstream_paths:
                    downstream_rooms.update(path)
                check_region = {room_id} | downstream_rooms

                # Count exits in region, excluding trap_exit
                exits_count = 0
                for rid in check_region:
                    r = self.rooms.get_room(rid)
                    if r:
                        exits_count += len([d for d in r.doors
                                            if d not in self.protected and d != trap_exit])
                        exits_count += len([t for t in r.traps
                                            if t not in self.protected and t != trap_exit])

                if exits_count <= 0:
                    continue

                # === C: If target is in hub/upstream, also check entrance preservation ===
                if room_id in hub_and_upstream:
                    upstream_rooms = get_exit_upstream_rooms()
                    entrance_region = {exit_room_id} | upstream_rooms

                    for pit_id in room_pits:
                        # Count entrances in region, excluding this specific target pit
                        entrance_count = 0
                        for rid in entrance_region:
                            r = self.rooms.get_room(rid)
                            if r:
                                entrance_count += len([d for d in r.doors
                                                       if d not in self.protected and d != pit_id])
                                entrance_count += len([p for p in r.pits
                                                       if p not in self.protected and p != pit_id])
                        if entrance_count > 0:
                            valid_pits.append(pit_id)
                else:
                    # Connected, not hub/upstream - B1 passed, all pits valid
                    valid_pits.extend(room_pits)

        return valid_pits

    def get_valid_door_targets_v2(self, door_exit, exit_room_id, topology, available_doors=None, available_traps=None):
        """V2: Get valid door targets by directly assessing each connection's result.

        Instead of classifying room types and applying categorical rules, this method
        directly evaluates whether each potential connection maintains branch invariants:
        - Downstream of active room must have >= 1 exit after connection
        - Hub+upstream must have >= 1 entrance after connection (for loop connections)

        Rules:
        A2. Unconnected target: (exit room + target room + target's downstream forced
            rooms) must have exits > 0 after both door_exit and target_door are consumed.
            If exits are only in downstream rooms, hub+upstream must also have an entrance.
        B2. Connected target: (exit room + target + target's downstream) must have
            at least one exit after both door_exit and target_door are consumed.
        C.  Hub/upstream target (loop): additionally, (exit room + exit room's upstream)
            must have at least one entrance that is not the target door.

        Note: available_doors and available_traps are accepted for signature compatibility
        with v1 but are not used by v2 (the method computes what it needs directly).

        Returns list of valid door IDs.
        """
        valid_doors = []
        hub_and_upstream = topology['hub_and_upstream']
        room_levels = topology['room_levels']
        currently_connected = set(room_levels.keys())

        # Pre-compute upstream rooms for rule C (lazy, only if needed)
        _upstream_room_cache = None

        def get_exit_upstream_rooms():
            nonlocal _upstream_room_cache
            if _upstream_room_cache is None:
                paths = self.get_upstream_paths(exit_room_id)
                _upstream_room_cache = set()
                for path in paths:
                    _upstream_room_cache.update(path)
            return _upstream_room_cache

        # Pre-compute hub+upstream entrance count (lazy, for downstream-only exit check)
        _hub_entrance_cache = None

        def get_hub_upstream_entrance_count():
            nonlocal _hub_entrance_cache
            if _hub_entrance_cache is None:
                hub_d, hub_p = self.count_entrances_in_region(hub_and_upstream)
                _hub_entrance_cache = hub_d + hub_p
                # door_exit is not yet protected but will be consumed by the connection;
                # subtract it from hub entrances if exit_room is in hub+upstream
                if exit_room_id in hub_and_upstream:
                    _hub_entrance_cache -= 1
            return _hub_entrance_cache

        for room_id in self.net.nodes:
            if room_id == self.terminus:
                continue

            room = self.rooms.get_room(room_id)
            if room is None:
                continue

            room_doors = [d for d in room.doors
                          if d not in self.protected and d not in self.initially_locked_exits]
            if not room_doors:
                continue

            is_connected = room_id in currently_connected

            if not is_connected:
                # === A2: Unconnected room ===
                # Cooldown gating: warp/town rooms can only be mapped when the
                # corresponding cooldown has run down to zero.
                if room_id in WARP_ROOMS and self.warp_cooldown > 0:
                    continue
                if room_id in TOWN_ROOMS and self.town_cooldown > 0:
                    continue
                # Connection consumes door_exit from exit room and target_door from target room.
                # Both are doors (exits), so we check remaining exits after removing both.
                # Also checks downstream rooms (from forced connections) for exits.

                # Skip true dead ends (deferred to finalize_map)
                if self.is_true_dead_end(room_id):
                    continue

                # Check for downstream rooms (from forced connections in the graph)
                downstream_paths = self.get_downstream_paths(room_id)
                downstream_rooms = set()
                for path in downstream_paths:
                    downstream_rooms.update(path)

                for target_door in room_doors:
                    if target_door == door_exit:
                        continue

                    exclude = {door_exit, target_door}
                    exits_count = 0
                    entrances_count = 0
                    # Use a set to avoid double-counting if exit_room_id == room_id
                    for rid in {exit_room_id, room_id}:
                        r = self.rooms.get_room(rid)
                        if r:
                            remaining_doors = len([d for d in r.doors
                                                   if d not in self.protected and d not in exclude])
                            remaining_traps = len([t for t in r.traps
                                                   if t not in self.protected])
                            remaining_pits = len([p for p in r.pits
                                                  if p not in self.protected])
                            exits_count += remaining_doors + remaining_traps
                            entrances_count += remaining_doors + remaining_pits

                    if exits_count > 0 and (entrances_count > 0 or exit_room_id not in hub_and_upstream):
                        valid_doors.append(target_door)
                    elif exits_count == 0 and downstream_rooms:
                        # No local exits, but downstream rooms (from forced connections)
                        # may have exits (e.g., Baren Falls: dc-15 -> ruin-baren-reward
                        # -> ruin-baren which has 2 doors).
                        downstream_exits = 0
                        for rid in downstream_rooms - {exit_room_id, room_id}:
                            r = self.rooms.get_room(rid)
                            if r:
                                downstream_exits += len([d for d in r.doors
                                                         if d not in self.protected
                                                         and d not in exclude])
                                downstream_exits += len([t for t in r.traps
                                                         if t not in self.protected
                                                         and t not in exclude])
                        if downstream_exits > 0:
                            # Exits are only downstream (through forced one-way connections),
                            # so this acts like a trap exit: hub+upstream must retain at
                            # least one entrance for the branch to loop back.
                            if get_hub_upstream_entrance_count() > 0:
                                valid_doors.append(target_door)
            else:
                # === B2: Connected room ===
                # (exit room + target room + target's downstream) must have at least one
                # exit after both door_exit and target_door are consumed.
                downstream_paths = self.get_downstream_paths(room_id)
                downstream_rooms = set()
                for path in downstream_paths:
                    downstream_rooms.update(path)
                check_region = {exit_room_id, room_id} | downstream_rooms

                for target_door in room_doors:
                    if target_door == door_exit:
                        continue

                    # Count exits in region, excluding both consumed doors
                    exclude = {door_exit, target_door}
                    exits_count = 0
                    for rid in check_region:
                        r = self.rooms.get_room(rid)
                        if r:
                            exits_count += len([d for d in r.doors
                                                if d not in self.protected and d not in exclude])
                            exits_count += len([t for t in r.traps
                                                if t not in self.protected and t not in exclude])

                    if exits_count <= 0:
                        continue

                    # === C: If target is in hub/upstream, check entrance preservation ===
                    if room_id in hub_and_upstream:
                        upstream_rooms = get_exit_upstream_rooms()
                        entrance_region = {exit_room_id} | upstream_rooms

                        # Count entrances in region, excluding the target door
                        entrance_count = 0
                        for rid in entrance_region:
                            r = self.rooms.get_room(rid)
                            if r:
                                entrance_count += len([d for d in r.doors
                                                       if d not in self.protected and d != target_door])
                                entrance_count += len([p for p in r.pits
                                                       if p not in self.protected and p != target_door])
                        if entrance_count > 0:
                            valid_doors.append(target_door)
                    else:
                        # Connected, not hub/upstream - B2 passed
                        valid_doors.append(target_door)

        return valid_doors

    def visualize_branch_topology(self):
        """Generate a text-based visualization of the branch's topology.

        The branch has three regions:
        - HUB: The central room (level 0), connected to Narshe school
        - UPSTREAM: Rooms connected TO the hub via pits in the hub (forced connections only)
        - DOWNSTREAM: Rooms the player reaches BY FALLING from hub via traps

        Returns a formatted string.
        """
        lines = []
        lines.append("")
        lines.append("=" * 70)
        lines.append("BRANCH TOPOLOGY")
        lines.append("=" * 70)

        # Find the hub
        hub_candidates = [n for n in self.net.nodes if 'ruin_hub_' in str(n)]
        if not hub_candidates:
            lines.append("ERROR: No hub found in branch!")
            return "\n".join(lines)

        hub_id = hub_candidates[0]
        hub = self.rooms.get_room(hub_id)

        # Get upstream and downstream
        upstream = self.get_upstream_nodes(hub_id)
        downstream = self.get_downstream_nodes(hub_id)

        # Get downstream levels
        levels, level_connections = self.get_downstream_levels(hub_id)

        # Helper to format room counts
        def room_counts(room_id):
            room = self.rooms.get_room(room_id)
            if room is None:
                return "?"
            d = len([x for x in room.doors if x not in self.protected])
            t = len([x for x in room.traps if x not in self.protected])
            p = len([x for x in room.pits if x not in self.protected])
            return f"{d}D/{t}T/{p}P"

        def short_name(room_id, max_len=35):
            s = str(room_id)
            return s[:max_len] + "..." if len(s) > max_len else s

        # ===== LEGEND =====
        lines.append("")
        lines.append("Format: room_name (doors/traps/pits free)")
        lines.append("  * = check room (has reward),  ! = terminus")

        # ===== HUB (Level 0) =====
        lines.append("")
        lines.append("-" * 70)
        lines.append("LEVEL 0: HUB (player starts here, can always return)")
        lines.append("-" * 70)
        hub_marker = ""
        if hub_id in self.check_rooms:
            hub_marker += "*"
        if hub_id == self.terminus:
            hub_marker += "!"
        lines.append(f"  {short_name(hub_id)} ({room_counts(hub_id)}){hub_marker}")

        # ===== UPSTREAM =====
        lines.append("")
        lines.append("-" * 70)
        lines.append("UPSTREAM: Rooms with paths BACK to hub (via forced pit->trap)")
        lines.append("-" * 70)
        if upstream:
            for room_id in upstream:
                marker = ""
                if room_id in self.check_rooms:
                    marker += "*"
                if room_id == self.terminus:
                    marker += "!"
                lines.append(f"  {short_name(room_id)} ({room_counts(room_id)}){marker}")
        else:
            lines.append("  (none)")

        # ===== DOWNSTREAM (by level) =====
        lines.append("")
        lines.append("-" * 70)
        lines.append("DOWNSTREAM: Rooms reached by FALLING through traps (one-way until reconnected)")
        lines.append("-" * 70)
        if downstream:
            max_level = max(levels.get(r, 0) for r in downstream) if downstream else 0
            for level in range(1, max_level + 1):
                level_rooms = [r for r in downstream if levels.get(r, 0) == level]
                if not level_rooms:
                    continue
                lines.append(f"  LEVEL {level} (fell {level}x from hub):")
                for room_id in level_rooms:
                    # Find how we got here
                    entry_info = ""
                    for (from_room, to_room), (trap, pit) in level_connections.items():
                        if to_room == room_id:
                            from_name = short_name(from_room, 20)
                            entry_info = f" <- fell from {from_name}"
                            break

                    # Check for local upstream (escape routes not through hub)
                    local_up = self.get_local_upstream(room_id, set(upstream))
                    escape_info = ""
                    if local_up:
                        escape_info = f" [+{len(local_up)} escape route(s)]"

                    marker = ""
                    if room_id in self.check_rooms:
                        marker += "*"
                    if room_id == self.terminus:
                        marker += "!"

                    lines.append(f"    {short_name(room_id)} ({room_counts(room_id)}){marker}{entry_info}{escape_info}")
        else:
            lines.append("  (none)")

        # ===== UNCONNECTED ROOMS =====
        all_connected = set([hub_id]) | set(upstream) | set(downstream)
        unconnected = [n for n in self.net.nodes if n not in all_connected]

        if unconnected:
            lines.append("")
            lines.append("-" * 70)
            lines.append("UNCONNECTED: Rooms in network but not yet in topology")
            lines.append("-" * 70)

            # CRITICAL: First show terminus and check rooms separately
            unconnected_terminus = [r for r in unconnected if r == self.terminus]
            unconnected_checks = [r for r in unconnected if r in self.check_rooms and r != self.terminus]

            if unconnected_terminus:
                lines.append("  !! TERMINUS (must be connected!) !!:")
                for room_id in unconnected_terminus:
                    lines.append(f"    {short_name(room_id)} ({room_counts(room_id)})")

            if unconnected_checks:
                lines.append("  ** CHECK ROOMS (have rewards, should be connected) **:")
                for room_id in unconnected_checks:
                    lines.append(f"    {short_name(room_id)} ({room_counts(room_id)})")

            # Classify the rest
            other = [r for r in unconnected if r not in unconnected_terminus and r not in unconnected_checks]
            if other:
                dead_ends = []
                connectors = []
                trap_rooms = []
                pit_rooms = []
                hub_potential = []

                for room_id in other:
                    room = self.rooms.get_room(room_id)
                    if room is None:
                        continue
                    doors = len([d for d in room.doors if d not in self.protected])
                    traps = len([t for t in room.traps if t not in self.protected])
                    pits = len([p for p in room.pits if p not in self.protected])

                    if doors + traps >= 3:
                        hub_potential.append(room_id)
                    elif traps > 0:
                        trap_rooms.append(room_id)
                    elif pits > 0 and doors > 0:
                        pit_rooms.append(room_id)
                    elif doors == 1:
                        dead_ends.append(room_id)
                    elif doors >= 2:
                        connectors.append(room_id)

                def format_room_list(rooms, max_show=6):
                    if not rooms:
                        return ""
                    ids = [short_name(r, 20) for r in rooms[:max_show]]
                    result = ", ".join(ids)
                    if len(rooms) > max_show:
                        result += f", ... (+{len(rooms) - max_show})"
                    return result

                lines.append("  Other rooms:")
                if hub_potential:
                    lines.append(f"    Hub potential (3+ exits): {format_room_list(hub_potential)}")
                if trap_rooms:
                    lines.append(f"    Has traps: {format_room_list(trap_rooms)}")
                if pit_rooms:
                    lines.append(f"    Has pits+doors: {format_room_list(pit_rooms)}")
                if connectors:
                    lines.append(f"    Connectors (2+ doors): {format_room_list(connectors)}")
                if dead_ends:
                    lines.append(f"    Dead ends (1 door): {format_room_list(dead_ends)}")

        # ===== SUMMARY =====
        lines.append("")
        lines.append("-" * 70)
        lines.append("SUMMARY")
        lines.append("-" * 70)

        # Count totals
        total_doors = 0
        total_traps = 0
        total_pits = 0
        for room_id in self.net.nodes:
            room = self.rooms.get_room(room_id)
            if room:
                total_doors += len([d for d in room.doors if d not in self.protected])
                total_traps += len([t for t in room.traps if t not in self.protected])
                total_pits += len([p for p in room.pits if p not in self.protected])

        connected_count = 1 + len(upstream) + len(downstream)
        lines.append(f"  Rooms: {len(self.net.nodes)} total, {connected_count} in topology, {len(unconnected)} unconnected")
        lines.append(f"  Free exits: {total_doors} doors, {total_traps} traps, {total_pits} pits")
        lines.append(f"  Connections: {len(self.map[0])} door-pairs, {len(self.map[1])} trap->pit")

        # Warnings
        warnings = []
        if total_traps > total_pits:
            warnings.append(f"traps ({total_traps}) > pits ({total_pits})")
        if total_doors % 2 == 1:
            warnings.append(f"odd doors ({total_doors})")
        if unconnected:
            unconnected_terminus = [r for r in unconnected if r == self.terminus]
            unconnected_checks = [r for r in unconnected if r in self.check_rooms]
            if unconnected_terminus:
                warnings.append("TERMINUS not connected!")
            if unconnected_checks:
                warnings.append(f"{len(unconnected_checks)} check room(s) not connected!")

        if warnings:
            lines.append("  WARNINGS:")
            for w in warnings:
                lines.append(f"    - {w}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _inject_door_if_needed_for_terminus(self, reserve_areas=None):
        """Inject a door into the network when needed to connect the terminus.

        This handles the edge case where finalize_map starts with:
        - The terminus hasn't been merged into the hub yet
        - The hub/downstream network has traps but NO unprotected doors

        Without doors, step (4) cannot connect the terminus. This method fixes
        the situation by finding a room with (pit, door, other_exit) and
        connecting a trap to its pit, which adds the room's door to the network.

        Args:
            reserve_areas: Optional list of (area_name, room_list) tuples from
                          RuinationMapping.get_reserve_area_rooms() to search
                          if no suitable room exists in the branch's network.
        """
        # Check if terminus still exists (hasn't been merged)
        terminus = self.rooms.get_room(self.terminus)
        if terminus is None:
            return  # Terminus already merged, no fix needed

        # Get current hub and topology
        hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
        hub = self.rooms.get_room(hub_id)
        upstream = self.get_upstream_nodes(hub_id)
        downstream = self.get_downstream_nodes(hub_id)

        # Collect all unprotected doors from hub + upstream + downstream
        all_doors = [d for d in hub.doors if d not in self.protected]
        for node in upstream:
            room = self.rooms.get_room(node)
            all_doors.extend([d for d in room.doors if d not in self.protected])
        for node in downstream:
            room = self.rooms.get_room(node)
            all_doors.extend([d for d in room.doors if d not in self.protected])

        # Collect all unprotected traps from hub + downstream (not upstream - traps go down)
        all_traps = [t for t in hub.traps if t not in self.protected]
        for node in downstream:
            room = self.rooms.get_room(node)
            all_traps.extend([t for t in room.traps if t not in self.protected])

        # If we have doors or no traps, no fix needed
        if len(all_doors) > 0 or len(all_traps) == 0:
            return

        if self.verbose:
            vprint('\t=== NO DOORS FOR TERMINUS FIX ===')
            vprint(f'\tTerminus {self.terminus} not merged, but network has no doors')
            vprint(f'\tAvailable traps: {all_traps}')
            vprint(f'\tSearching for room with pit, door, and another exit...')

        # Find a suitable room: has pit (to receive trap), door (to add to network),
        # and at least one other exit (door or trap) so connecting doesn't dead-end
        connected_rooms = {hub_id} | set(upstream) | set(downstream)
        unconnected_rooms = [n for n in self.net.nodes if n not in connected_rooms]

        suitable_room = None

        # First search in unconnected rooms already in the network
        for room_id in unconnected_rooms:
            room = self.rooms.get_room(room_id)
            if room is None:
                continue
            unprotected_pits = [p for p in room.pits if p not in self.protected]
            unprotected_doors = [d for d in room.doors if d not in self.protected]
            unprotected_traps = [t for t in room.traps if t not in self.protected]

            # Need: at least 1 pit, at least 1 door, at least 1 other exit (door or trap)
            total_exits = len(unprotected_doors) + len(unprotected_traps)
            if len(unprotected_pits) >= 1 and len(unprotected_doors) >= 1 and total_exits >= 2:
                suitable_room = room_id
                if self.verbose:
                    vprint(f'\tFound suitable room in network: {room_id}')
                    vprint(f'\t  pits={unprotected_pits}, doors={unprotected_doors}, traps={unprotected_traps}')
                break

        # If no suitable room in network, check reserve areas
        if suitable_room is None and reserve_areas is not None:
            if self.verbose:
                vprint('\tNo suitable room in network, checking reserve areas...')

            for area_name, area_rooms in reserve_areas:
                for room_id in area_rooms:
                    if room_id in room_data:
                        data = room_data[room_id]
                        doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                        traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                        pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []

                        # Need: at least 1 pit, at least 1 door, at least 1 other exit
                        total_exits = len(doors) + len(traps)
                        if len(pits) >= 1 and len(doors) >= 1 and total_exits >= 2:
                            # Add this room to the network
                            self.add_room(room_id)
                            area_rooms.remove(room_id)
                            suitable_room = room_id
                            if self.verbose:
                                vprint(f'\tAdded suitable room from area {area_name}: {room_id}')
                                vprint(f'\t  pits={pits}, doors={doors}, traps={traps}')
                            break
                if suitable_room is not None:
                    break

        if suitable_room is None:
            # This is a serious issue - log diagnostic info
            viz = self.visualize_branch_topology()
            raise RuntimeError(
                f"_inject_door_if_needed_for_terminus: Cannot find suitable room to inject door. "
                f"Terminus={self.terminus}, unconnected_rooms={unconnected_rooms}, "
                f"all_traps={all_traps}. Branch needs a room with at least 1 pit and 1 door.\n"
                f"{viz}"
            )

        # Connect the most downstream trap to this room's pit
        # Find the deepest trap in the downstream tree
        selected_trap = None
        if len(downstream) > 0:
            downstream_paths = self.get_downstream_paths(hub_id)
            if downstream_paths:
                max_depth = max(len(p) for p in downstream_paths)
                # Search from deepest to shallowest for a room with traps
                for depth in range(max_depth, 0, -1):
                    candidates = []
                    for path in downstream_paths:
                        if len(path) >= depth:
                            room_id = path[depth - 1]
                            room = self.rooms.get_room(room_id)
                            if room:
                                room_traps = [t for t in room.traps if t not in self.protected]
                                if room_traps:
                                    candidates.extend(room_traps)
                    if candidates:
                        selected_trap = random.choice(candidates)
                        break

        # Fallback to any available trap
        if selected_trap is None:
            selected_trap = random.choice(all_traps)

        # Connect to the suitable room's pit
        suitable_room_obj = self.rooms.get_room(suitable_room)
        suitable_pits = [p for p in suitable_room_obj.pits if p not in self.protected]
        selected_pit = random.choice(suitable_pits)

        if self.verbose:
            vprint(f'\tConnecting trap {selected_trap} --> pit {selected_pit} (room {suitable_room})')

        self.connect(selected_trap, selected_pit)

        # Verify we now have doors
        if self.verbose:
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            new_doors = [d for d in hub.doors if d not in self.protected]
            downstream = self.get_downstream_nodes(hub_id)
            for node in downstream:
                room = self.rooms.get_room(node)
                new_doors.extend([d for d in room.doors if d not in self.protected])
            vprint(f'\tAfter fix: network now has {len(new_doors)} doors')

    def _classify_branch_warp_rooms(self, hub_id):
        """Partition the branch's warp rooms into connected vs. unconnected.

        A node counts as a warp room if it is itself a member of WARP_ROOMS, or
        if it is a compound (compress_loop) id that contains a WARP_ROOMS member.
        Compound membership is tested by bracketing the node id with underscores
        and looking for "_<warp_id>_" -- the safe convention used elsewhere in
        the codebase, since some room ids themselves contain underscores
        (e.g. 'share_east', 'ruin_hub_*'). "Connected" means the node belongs to
        the hub's reachable set (hub + upstream + downstream); orphan nodes added
        via rescue paths but never wired up are reported as unconnected.

        Returns:
            (connected_warps, unconnected_warps): two lists of node ids.
        """
        connected_set = (
            {hub_id}
            | set(self.get_upstream_nodes(hub_id))
            | set(self.get_downstream_nodes(hub_id))
        )
        connected_warps = []
        unconnected_warps = []
        for node_id in self.net.nodes:
            if node_id in WARP_ROOMS:
                is_warp = True
            elif isinstance(node_id, str):
                bracketed = f'_{node_id}_'
                is_warp = any(f'_{w}_' in bracketed for w in WARP_ROOMS)
            else:
                is_warp = False
            if not is_warp:
                continue
            if node_id in connected_set:
                connected_warps.append(node_id)
            else:
                unconnected_warps.append(node_id)
        return connected_warps, unconnected_warps

    def _connect_orphan_warp_room(self, unconnected_warps, hub_id):
        """Attempt to integrate an orphan warp room into the branch.

        Only considers "hallway" warp rooms with at least 2 unprotected exits
        (doors + traps; pits are entrances, not exits). Connecting such a warp
        consumes one exit on each side and leaves the warp room with at least
        one outgoing exit, so the branch's overall exit count is unchanged
        (or grows). Dead-end warp rooms are deferred to finalize_map step 6,
        where they are connected against `remaining_doors` so they cannot
        create an inescapable dead end.

        Tries each eligible warp (in random order) against the hub and any
        downstream node. A door<->door pairing is preferred; falls back to
        hub/downstream-trap to warp-pit. Returns True if a connection was made.
        """
        random.shuffle(unconnected_warps)
        downstream = self.get_downstream_nodes(hub_id)
        targets = [(hub_id, self.rooms.get_room(hub_id))]
        for node in downstream:
            targets.append((node, self.rooms.get_room(node)))

        for warp_id in unconnected_warps:
            warp_room = self.rooms.get_room(warp_id)
            if warp_room is None:
                continue
            warp_doors = [d for d in warp_room.doors if d not in self.protected]
            warp_pits = [p for p in warp_room.pits if p not in self.protected]
            if not warp_doors and not warp_pits:
                continue
            # Hallway filter: skip dead-end warps (count [1,0,0], no locks).
            # Connecting them here could leave a downstream node with no
            # outbound exit; defer to finalize_map step 6 instead.
            if self.is_dead_end(warp_id):
                if self.verbose:
                    vprint(f'\twarp rescue: deferring dead-end warp {warp_id} to step 6')
                continue

            shuffled_targets = list(targets)
            random.shuffle(shuffled_targets)
            for target_id, target in shuffled_targets:
                if target is None or target_id == warp_id:
                    continue
                target_doors = [d for d in target.doors if d not in self.protected]
                target_traps = [t for t in target.traps if t not in self.protected]

                if warp_doors and target_doors:
                    this_exit = random.choice(target_doors)
                    this_conn = random.choice(warp_doors)
                    if self.verbose:
                        vprint(f'\twarp rescue: connecting {target_id} door {this_exit} '
                               f'--> {warp_id} door {this_conn}')
                    self.connect(this_exit, this_conn)
                    self._cleanup_dead_end_after_warp_connect(warp_id)
                    return True
                if warp_pits and target_traps:
                    this_exit = random.choice(target_traps)
                    this_conn = random.choice(warp_pits)
                    if self.verbose:
                        vprint(f'\twarp rescue: connecting {target_id} trap {this_exit} '
                               f'--> {warp_id} pit {this_conn}')
                    self.connect(this_exit, this_conn)
                    self._cleanup_dead_end_after_warp_connect(warp_id)
                    return True
        return False

    def _cleanup_dead_end_after_warp_connect(self, warp_id):
        """Remove warp_id from self.dead_ends if it can no longer serve as one.

        A warp room classified as a dead end has its only door consumed by a
        door<->door rescue, leaving a 0-door survivor still in self.dead_ends.
        Step 6 would then pop it and crash on `room.doors.pop()`. The pre-step5
        cleanup only removes entries that left net.nodes (e.g. via compress_loop
        merging), so we must handle the in-place case here.
        """
        if warp_id not in self.dead_ends:
            return
        warp_room_after = self.rooms.get_room(warp_id)
        if warp_room_after is None:
            # Merged into a compound during connect; pre-step5 cleanup will catch it.
            return
        if not [d for d in warp_room_after.doors if d not in self.protected]:
            self.dead_ends.remove(warp_id)
            if self.verbose:
                vprint(f'\twarp rescue: removed {warp_id} from dead_ends (no doors left)')

    def finalize_map(self, reserve_areas=None):
        if self.verbose:
            vprint('Closing branch...')
            try:
                viz = self.visualize_branch_topology()
                vprint(viz)
            except:
                vprint('Could not visualise branch!')

        self.ForceConnections(forced_connections)

        if self.verbose:
            vprint(f'\tProtected elements after ForceConnections: {sorted(self.protected)}')

        # Rooms pulled from reserve below (rescue/converter/hub rooms) must honor
        # their forced connections; expose the reserve pool to add_room so it can
        # pull in forced-cluster partners. Cleared again at branch close below.
        self._active_reserve_areas = reserve_areas

        # PRE-CHECK: Handle "no doors but terminus unconnected" edge case
        # This happens when the branch has only traps/pits with no remaining doors.
        # In this scenario, we need to inject a door into the network by connecting
        # a trap to a room that has: at least 1 pit, at least 1 door, and 1 other exit.
        self._inject_door_if_needed_for_terminus(reserve_areas)

        # Wrap steps 1-6 in a loop. If keys unlock new traps/doors during finalization,
        # we restart from step 1 to ensure proper topology-aware handling.
        max_finalize_iterations = 10  # Safety limit to prevent infinite loops
        finalize_iteration = 0

        while finalize_iteration < max_finalize_iterations:
            finalize_iteration += 1
            if finalize_iteration > 1 and self.verbose:
                vprint(f'\n=== Finalize iteration {finalize_iteration} (new elements were unlocked) ===\n')

            # Honor any forced connection that became accessible since the last
            # pass (a key applied during the previous iteration may have unlocked a
            # forced trap, e.g. the Lone Wolf or Baren Falls reward routes).
            if reserve_areas is not None:
                self._honor_forced_connections(reserve_areas)

            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            if self.verbose:
                vprint('\thub:', hub_id, hub.count)

            # WARP-ROOM RESCUE: If the branch ended up with no connected warp room
            # but at least one warp room sits in the network as an orphan (e.g. an
            # add_room from a rescue path that never got wired up), connect one
            # before the regular finalization steps run. Restart the loop so steps
            # 1-6 see a topology that already includes the warp room.
            #
            # Skip the rescue on very small branches (hub + terminus only): there is
            # no need for intermediate warp point rooms when the terminus connects
            # directly to the hub. Only attempt the rescue once the branch has grown
            # past a few connected rooms.
            connected_rooms = (
                {hub_id}
                | set(self.get_upstream_nodes(hub_id))
                | set(self.get_downstream_nodes(hub_id))
            )
            connected_warps, unconnected_warps = self._classify_branch_warp_rooms(hub_id)
            if self.verbose:
                vprint(f'\twarp rooms: connected={connected_warps}, '
                       f'unconnected={unconnected_warps}')
            if (len(connected_rooms) > 3
                    and len(connected_warps) < 2 and len(unconnected_warps) > 0):
                if self._connect_orphan_warp_room(unconnected_warps, hub_id):
                    if self.verbose:
                        vprint('\twarp rescue made a connection; restarting finalize loop')
                    continue
                elif self.verbose:
                    vprint('\twarp rescue could not connect any orphan; proceeding')

            # (1) Count trapdoors/pits connected to hub.  If trapdoors > pits, connect traps to rooms with (# pits > # traps).
            # Filter out protected elements to avoid using forced connection destinations
            all_pits = [p for p in hub.pits if p not in self.protected]
            all_traps = [t for t in hub.traps if t not in self.protected]

            # Show what was filtered
            filtered_pits = [p for p in hub.pits if p in self.protected]
            filtered_traps = [t for t in hub.traps if t in self.protected]
            if self.verbose and (filtered_pits or filtered_traps):
                vprint(f'\t(hub) Filtered out protected - pits: {filtered_pits}, traps: {filtered_traps}')

            upstream = self.get_upstream_nodes(hub_id)
            for node in upstream:
                room = self.rooms.get_room(node)
                all_pits.extend([p for p in room.pits if p not in self.protected])
                all_traps.extend([t for t in room.traps if t not in self.protected])

            downstream = self.get_downstream_nodes(hub_id)
            for node in downstream:
                room = self.rooms.get_room(node)
                all_pits.extend([p for p in room.pits if p not in self.protected])
                all_traps.extend([t for t in room.traps if t not in self.protected])

            if self.verbose:
                vprint('\tpits:', all_pits)
                vprint('\ttraps:', all_traps)

            while len(all_traps) > len(all_pits):
                # Find unconnected rooms with more pits than traps
                if self.verbose:
                    vprint('(1) assessing nodes for (more pits than traps):')
                winner = ''
                diff = 0
                for n in self.net.nodes:
                    if n not in upstream and n not in downstream and n != hub_id:
                        r = self.rooms.get_room(n)
                        if self.verbose:
                            vprint('\t',n, r.count, r.doors, r.traps, r.pits, r.keys, r.locks)
                        # Skip rooms with no originally-free exits (all exits were key-unlocked)
                        orig_free_exits = (
                            len([d for d in r.doors if d not in self.protected
                                 and d not in self.initially_locked_exits])
                            + len([t for t in r.traps if t not in self.protected
                                   and t not in self.initially_locked_exits])
                        )
                        if orig_free_exits == 0:
                            continue
                        # Use only unprotected pits and traps for comparison
                        unprotected_pits = [p for p in r.pits if p not in self.protected]
                        unprotected_traps = [t for t in r.traps if t not in self.protected]
                        if (len(unprotected_pits) - len(unprotected_traps)) > diff:
                            diff = len(unprotected_pits) - len(unprotected_traps)
                            winner = n

                # Fallback: search reserve areas for a room with more pits than traps
                if winner == '' and reserve_areas is not None:
                    if self.verbose:
                        vprint('(1) no suitable node in network, checking reserve areas...')
                    best_diff = 0
                    best_rid = None
                    best_area_rooms = None
                    for area_name, area_rooms in reserve_areas:
                        for rid in area_rooms:
                            if rid in self.net.nodes:
                                continue
                            if rid in room_data:
                                data = room_data[rid]
                                r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                                r_traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                                rd = len(r_pits) - len(r_traps)
                                if rd > best_diff:
                                    best_diff = rd
                                    best_rid = rid
                                    best_area = area_name
                                    best_area_rooms = area_rooms
                    if best_rid is not None:
                        self.add_room(best_rid)
                        best_area_rooms.remove(best_rid)
                        winner = best_rid
                        if self.verbose:
                            vprint(f'(1) added room from reserve area {best_area}: {best_rid}')

                # connect a hub trapdoor to this node
                this_exit = random.choice(all_traps)
                room = self.rooms.get_room(winner)
                unprotected_room_pits = [p for p in room.pits if p not in self.protected]
                this_entr = random.choice(unprotected_room_pits)
                if self.verbose:
                    protected_in_room = [p for p in room.pits if p in self.protected]
                    vprint(f'(1) selected {winner}: traps={room.traps}, pits={room.pits}')
                    if protected_in_room:
                        vprint(f'    (filtered protected pits: {protected_in_room})')
                    vprint(f'(1) connecting {this_exit} --> {this_entr}')

                self.connect(this_exit, this_entr)

                # Recollect data on pits/traps (filtering protected elements)
                hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
                hub = self.rooms.get_room(hub_id)
                all_pits = [p for p in hub.pits if p not in self.protected]
                all_traps = [t for t in hub.traps if t not in self.protected]

                upstream = self.get_upstream_nodes(hub_id)
                for node in upstream:
                    room = self.rooms.get_room(node)
                    all_pits.extend([p for p in room.pits if p not in self.protected])
                    all_traps.extend([t for t in room.traps if t not in self.protected])

                downstream = self.get_downstream_nodes(hub_id)
                for node in downstream:
                    room = self.rooms.get_room(node)
                    all_pits.extend([p for p in room.pits if p not in self.protected])
                    all_traps.extend([t for t in room.traps if t not in self.protected])

            # (2) Connect any nodes downstream from the hub room to upstream or to the hub room
            # There's a possible error mode where:  U (1 pit) --> Hub --> A (1 trap),  Hub --> B (1 trap, 1 pit).
            # The only correct solution is A --> B --> U.  If we connect A --> U, we fail.
            # So start by connecting downstream nodes with the most entrances
            delta = []
            for node in downstream:
                room = self.rooms.get_room(node)
                entrance_count = len(room.doors) + len(room.pits)
                exit_count = len(room.doors) + len(room.traps)
                delta.append((entrance_count - exit_count, node))
            if self.verbose:
                vprint('(2) delta values:', delta)
            # Fix A: Sort so trap-bearing rooms are processed BEFORE door-only rooms.
            # Since pop() takes from the end, trap-bearing rooms must sort last.
            # Secondary sort by delta value within each group.
            def _trap_priority(item):
                r = self.rooms.get_room(item[1])
                has_traps = 1 if len([t for t in r.traps if t not in self.protected]) > 0 else 0
                return (has_traps, item[0])
            delta.sort(key=_trap_priority)
            restart_finalization = False
            while len(delta) > 0:
                value = delta.pop()
                node = value[1]
                room = self.rooms.get_room(node)
                if self.verbose:
                    vprint('(2) selected', node, '(delta = ', value[0], '): ', room.count, room.doors, room.traps, room.pits)

                # Skip rooms with no exits (only pit entrances) - they can't connect upstream
                # Their pits will be connected when traps are processed in step (3)
                if len(room.doors) == 0 and len(room.traps) == 0:
                    if self.verbose:
                        vprint('(2) skipping - room has no exits (pit-only)')
                    continue

                upstream_doors = [d for d in hub.doors if d not in self.protected]
                upstream_pits = [p for p in hub.pits if p not in self.protected]
                for node in upstream:
                    uproom = self.rooms.get_room(node)
                    upstream_pits.extend([p for p in uproom.pits if p not in self.protected])
                    upstream_doors.extend([d for d in uproom.doors if d not in self.protected])

                this_conn = None
                unprotected_room_traps = [t for t in room.traps if t not in self.protected]
                unprotected_room_doors = [d for d in room.doors if d not in self.protected]
                if len(unprotected_room_traps) > 0:
                    this_exit = random.choice(unprotected_room_traps)
                    if len(upstream_pits) > 0:
                        # Before connecting trap to hub/upstream pit, check if the
                        # terminus still needs connecting. If so, verify that after
                        # consuming this trap, the accessible network (hub + downstream,
                        # NOT upstream — upstream is one-way inaccessible) still has
                        # at least 1 exit for the terminus connection.
                        terminus_room = self.rooms.get_room(self.terminus)
                        if terminus_room is not None:
                            accessible_exits = 0
                            accessible_exits += len([d for d in hub.doors if d not in self.protected])
                            accessible_exits += len([t for t in hub.traps if t not in self.protected])
                            for ds_node in downstream:
                                ds_room = self.rooms.get_room(ds_node)
                                if ds_room:
                                    accessible_exits += len([d for d in ds_room.doors if d not in self.protected])
                                    accessible_exits += len([t for t in ds_room.traps if t not in self.protected])
                            # Subtract 1 for the trap being consumed
                            accessible_exits -= 1

                            if accessible_exits <= 0:
                                # Connecting to any hub/upstream pit would leave no
                                # accessible exits for terminus. Find a converter room
                                # (1+ pit, 1+ door, 1+ other exit) so the trap connects
                                # to its pit, and its door can serve the terminus.
                                if self.verbose:
                                    vprint(f'(2) Terminus unconnected, trap connection would leave 0 accessible exits.')
                                    vprint(f'    Searching for converter room (1+ pit, 1+ door, 1+ other exit)...')

                                connected_set = {hub_id} | set(upstream) | set(downstream)
                                # Search unconnected rooms in network
                                for node_id in self.net.nodes:
                                    if node_id in connected_set or node_id == self.terminus or node_id in self.dead_ends:
                                        continue
                                    n_room = self.rooms.get_room(node_id)
                                    if n_room is None:
                                        continue
                                    n_pits = [p for p in n_room.pits if p not in self.protected]
                                    n_doors = [d for d in n_room.doors if d not in self.protected]
                                    n_traps = [t for t in n_room.traps if t not in self.protected]
                                    if len(n_pits) >= 1 and len(n_doors) >= 1 and (len(n_doors) + len(n_traps)) >= 2:
                                        this_conn = random.choice(n_pits)
                                        if self.verbose:
                                            vprint(f'    Found converter room {node_id} in network')
                                        break

                                # Fallback: search reserve areas
                                if this_conn is None and reserve_areas is not None:
                                    for area_name, area_rooms in reserve_areas:
                                        for rid in list(area_rooms):
                                            if rid in self.net.nodes:
                                                continue
                                            if rid in room_data:
                                                data = room_data[rid]
                                                r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                                r_traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                                                r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                                                if len(r_pits) >= 1 and len(r_doors) >= 1 and (len(r_doors) + len(r_traps)) >= 2:
                                                    self.add_room(rid)
                                                    area_rooms.remove(rid)
                                                    added_room = self.rooms.get_room(rid)
                                                    added_pits = [p for p in added_room.pits if p not in self.protected]
                                                    this_conn = random.choice(added_pits)
                                                    if self.verbose:
                                                        vprint(f'    Added converter room {rid} from {area_name}')
                                                    break
                                        if this_conn is not None:
                                            break
                            else:
                                this_conn = random.choice(upstream_pits)
                        else:
                            # Terminus already merged, no exit preservation needed
                            this_conn = random.choice(upstream_pits)

                if this_conn is None and len(unprotected_room_doors) > 0:
                    # Fix B: Before using a door-to-door connection, verify we aren't
                    # consuming the last 2 doors in the branch. A door-to-door connection
                    # uses 2 doors total (1 from downstream + 1 from upstream). If <= 2
                    # doors remain, connect to a hub room (3+ doors) from reserve instead.
                    _, _, all_branch_doors = self.collect_network_traps_and_pits(include_doors=True)
                    total_branch_doors = len(all_branch_doors)
                    if total_branch_doors <= 2 and reserve_areas is not None:
                        if self.verbose:
                            vprint(f'(2) Fix B: only {total_branch_doors} doors remain in branch, '
                                  f'searching for hub room (3+ doors) in reserve...')
                        hub_room_found = False
                        for area_name, area_rooms in reserve_areas:
                            for rid in list(area_rooms):
                                if rid in self.net.nodes:
                                    continue
                                if rid in room_data:
                                    data = room_data[rid]
                                    r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                    if len(r_doors) >= 3:
                                        self.add_room(rid)
                                        area_rooms.remove(rid)
                                        hub_room = self.rooms.get_room(rid)
                                        unprotected_hub_doors = [d for d in hub_room.doors if d not in self.protected]
                                        this_conn = random.choice(unprotected_hub_doors)
                                        this_exit = random.choice(unprotected_room_doors)
                                        if self.verbose:
                                            vprint(f'(2) Fix B: added hub room {rid} from {area_name} '
                                                  f'({len(r_doors)} doors), connecting {this_exit} --> {this_conn}')
                                        self.connect(this_exit, this_conn)
                                        hub_room_found = True
                                        restart_finalization = True
                                        break
                            if hub_room_found:
                                break
                        if restart_finalization:
                            break
                    if this_conn is None:
                        this_exit = random.choice(unprotected_room_doors)
                        if len(upstream_doors) > 0:
                            this_conn = random.choice(upstream_doors)

                if this_conn is None:
                    # A thing can happen here where the downstream has only a door-out, but the upstream has only pit-in (or vice versa).
                    # In such a case, we can look at unused rooms, find a converter, attach it, and try again.
                    available_nodes = [n for n in self.net.nodes if n not in self.dead_ends and n != hub_id]
                    if self.verbose:
                        vprint(f'\t(2) converter search: room_traps={unprotected_room_traps}, room_doors={unprotected_room_doors}')
                        vprint(f'\t    upstream_doors={upstream_doors}, upstream_pits={upstream_pits}')
                        vprint(f'\t    available_nodes in network: {len(available_nodes)}')
                        if reserve_areas is not None:
                            ra_summary = [(a, len(r)) for a, r in reserve_areas if len(r) > 0]
                            vprint(f'\t    reserve_areas: {ra_summary}')
                        else:
                            vprint(f'\t    reserve_areas: None')
                    if len(unprotected_room_traps) > 0 and len(upstream_pits) == 0 and len(upstream_doors) > 0:
                        # Need a pit-in, door-out converter
                        pido = []
                        if self.verbose:
                            vprint('\t\tlooking for available pido nodes:')
                        for node_id in available_nodes:
                            node = self.rooms.get_room(node_id)
                            unprotected_node_pits = [p for p in node.pits if p not in self.protected]
                            unprotected_node_traps = [t for t in node.traps if t not in self.protected]
                            unprotected_node_doors = [d for d in node.doors if d not in self.protected]
                            if len(unprotected_node_pits) > 0 and len(unprotected_node_doors) > 0 and len(unprotected_node_pits) > len(unprotected_node_traps):
                                pido.append(node_id)
                                if self.verbose:
                                    vprint('\t\t\t', node_id, ': ', node.count)

                        if len(pido) > 0:
                            pido_room_id = random.choice(pido)
                            pido_room = self.rooms.get_room(pido_room_id)
                            # Select an unprotected pit from the converter room as the connection target
                            unprotected_pido_pits = [p for p in pido_room.pits if p not in self.protected]
                            this_conn = random.choice(unprotected_pido_pits)

                        # Fallback: search reserve areas for a pido room
                        if len(pido) == 0 and reserve_areas is not None:
                            if self.verbose:
                                vprint('\t\tno pido in network, checking reserve areas...')
                            for area_name, area_rooms in reserve_areas:
                                for rid in area_rooms:
                                    if rid in self.net.nodes:
                                        continue
                                    if rid in room_data:
                                        data = room_data[rid]
                                        r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                        r_traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                                        r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                                        if len(r_pits) > 0 and len(r_doors) > 0 and len(r_pits) > len(r_traps):
                                            self.add_room(rid)
                                            area_rooms.remove(rid)
                                            pido_room = self.rooms.get_room(rid)
                                            unprotected_pido_pits = [p for p in pido_room.pits if p not in self.protected]
                                            this_conn = random.choice(unprotected_pido_pits)
                                            if self.verbose:
                                                vprint(f'\t\tadded pido room from reserve area {area_name}: {rid}')
                                            break
                                if this_conn is not None:
                                    break

                    elif len(unprotected_room_doors) > 0 and len(upstream_doors) == 0 and len(upstream_pits) > 0:
                        # Need a door-in, trap-out converter
                        dito = []
                        if self.verbose:
                            vprint('\t\tlooking for available dito nodes:')
                        for node_id in available_nodes:
                            node = self.rooms.get_room(node_id)
                            unprotected_node_traps = [t for t in node.traps if t not in self.protected]
                            unprotected_node_pits = [p for p in node.pits if p not in self.protected]
                            unprotected_node_doors = [d for d in node.doors if d not in self.protected]
                            if len(unprotected_node_traps) > 0 and len(unprotected_node_doors) > 0 and len(unprotected_node_traps) > len(unprotected_node_pits):
                                dito.append(node_id)
                                if self.verbose:
                                    vprint('\t\t\t', node_id, ': ', node.count)

                        if len(dito) > 0:
                            dito_room_id = random.choice(dito)
                            dito_room = self.rooms.get_room(dito_room_id)
                            # Select an unprotected door from the converter room as the connection target
                            unprotected_dito_doors = [d for d in dito_room.doors if d not in self.protected]
                            this_conn = random.choice(unprotected_dito_doors)

                        # Fallback: search reserve areas for a dito room
                        if len(dito) == 0 and reserve_areas is not None:
                            if self.verbose:
                                vprint('\t\tno dito in network, checking reserve areas...')
                            for area_name, area_rooms in reserve_areas:
                                for rid in area_rooms:
                                    if rid in self.net.nodes:
                                        continue
                                    if rid in room_data:
                                        data = room_data[rid]
                                        r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                        r_traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                                        r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                                        if len(r_traps) > 0 and len(r_doors) > 0 and len(r_traps) > len(r_pits):
                                            self.add_room(rid)
                                            area_rooms.remove(rid)
                                            dito_room = self.rooms.get_room(rid)
                                            unprotected_dito_doors = [d for d in dito_room.doors if d not in self.protected]
                                            this_conn = random.choice(unprotected_dito_doors)
                                            if self.verbose:
                                                vprint(f'\t\tadded dito room from reserve area {area_name}: {rid}')
                                            break
                                if this_conn is not None:
                                    break

                    elif len(unprotected_room_doors) > 0 and len(upstream_doors) == 0 and len(upstream_pits) == 0:
                        # Upstream has nothing at all - need to add any room with a door
                        if self.verbose:
                            vprint('\t\tupstream has no doors or pits, looking for a room with a door...')
                        # Search network first
                        for node_id in available_nodes:
                            node = self.rooms.get_room(node_id)
                            unprotected_node_doors = [d for d in node.doors if d not in self.protected]
                            if len(unprotected_node_doors) > 0:
                                this_conn = random.choice(unprotected_node_doors)
                                if self.verbose:
                                    vprint(f'\t\tfound door {this_conn} in network node {node_id}')
                                break

                        # Fallback: search reserve areas for any room with a door
                        if this_conn is None and reserve_areas is not None:
                            if self.verbose:
                                vprint('\t\tno door-bearing room in network, checking reserve areas...')
                            for area_name, area_rooms in reserve_areas:
                                for rid in area_rooms:
                                    if rid in self.net.nodes:
                                        continue
                                    if rid in room_data:
                                        data = room_data[rid]
                                        r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                        if len(r_doors) > 0:
                                            self.add_room(rid)
                                            area_rooms.remove(rid)
                                            added_room = self.rooms.get_room(rid)
                                            unprotected_added_doors = [d for d in added_room.doors if d not in self.protected]
                                            this_conn = random.choice(unprotected_added_doors)
                                            if self.verbose:
                                                vprint(f'\t\tadded room with door from reserve area {area_name}: {rid}')
                                            break
                                if this_conn is not None:
                                    break

                if this_conn is None:
                    viz = self.visualize_branch_topology()
                    raise RuntimeError(
                        f"finalize_map step 2: Inescapable downstream node. "
                        f"room_doors={unprotected_room_doors}, room_traps={unprotected_room_traps}, "
                        f"upstream_doors={upstream_doors}, upstream_pits={upstream_pits}, "
                        f"reserve_areas={'None' if reserve_areas is None else [(a, len(r)) for a, r in reserve_areas]}\n"
                        f"{viz}"
                    )

                if self.verbose:
                    vprint('(2) connecting', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)

                # Update hub, upstream, downstream, delta
                hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
                hub = self.rooms.get_room(hub_id)
                upstream = self.get_upstream_nodes(hub_id)
                downstream = self.get_downstream_nodes(hub_id)
                delta = []
                for node in downstream:
                    room = self.rooms.get_room(node)
                    entrance_count = len(room.doors) + len(room.pits)
                    exit_count = len(room.doors) + len(room.traps)
                    delta.append((entrance_count - exit_count, node))
                if self.verbose:
                    vprint('(2) delta values:', delta)
                delta.sort(key=_trap_priority)

            # If Fix B triggered a restart, skip remaining steps and go back to step 1
            if restart_finalization:
                if self.verbose:
                    vprint('(2) Fix B: restarting finalization after adding hub room')
                continue

            # Post-step-2 check: all downstream nodes should be merged into hub
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            remaining_downstream = self.get_downstream_nodes(hub_id)
            if len(remaining_downstream) > 0:
                viz = self.visualize_branch_topology()
                raise RuntimeError(
                    f"finalize_map step 2 post-check: {len(remaining_downstream)} downstream node(s) "
                    f"remain after step 2: {remaining_downstream}. "
                    f"All downstream paths should be looped back into the hub.\n"
                    f"{viz}"
                )

            # Post-step-2 door check: verify at least one door remains for terminus connection.
            # If no doors remain but traps and pits exist, we can rescue by adding a room
            # from reserve_areas that has at least (1 trap, 1 pit, 1 door). Step (3) will
            # then connect the trap, and the room's door becomes available for the terminus.
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            post_step2_doors = [d for d in hub.doors if d not in self.protected]
            terminus = self.rooms.get_room(self.terminus)
            if len(post_step2_doors) == 0 and terminus is not None:
                remaining_traps_check, remaining_pits_check = self.collect_network_traps_and_pits()
                if (len(remaining_traps_check) > 0 or len(remaining_pits_check) > 0) and reserve_areas is not None:
                    print(f'WARNING: No doors remain after step (2) but terminus {self.terminus} '
                          f'still needs connecting. Searching rescue room '
                          f'(needs 1+ pit, 1+ door, 1+ other exit)...')

                    # First, check if an unconnected room in the network already qualifies.
                    # This handles rescue rooms added in a previous iteration that were never
                    # connected (they're invisible to steps 1-3 which only see hub+upstream+downstream).
                    rescue_found = False
                    connected_set = {hub_id} | set(self.get_upstream_nodes(hub_id)) | set(self.get_downstream_nodes(hub_id))
                    hub_traps = [t for t in hub.traps if t not in self.protected]
                    if len(hub_traps) > 0:
                        for node_id in self.net.nodes:
                            if node_id in connected_set or node_id == self.terminus:
                                continue
                            n_room = self.rooms.get_room(node_id)
                            if n_room is None:
                                continue
                            n_pits = [p for p in n_room.pits if p not in self.protected]
                            n_doors = [d for d in n_room.doors if d not in self.protected]
                            n_traps = [t for t in n_room.traps if t not in self.protected]
                            if len(n_pits) >= 1 and len(n_doors) >= 1 and (len(n_doors) + len(n_traps)) >= 2:
                                this_trap = random.choice(hub_traps)
                                this_pit = random.choice(n_pits)
                                self.connect(this_trap, this_pit)
                                print(f'WARNING: Connected hub trap {this_trap} to existing unconnected '
                                      f'room {node_id} pit {this_pit}. Restarting finalization.')
                                rescue_found = True
                                break

                    # Fallback: search reserve areas for a new rescue room, add and connect it.
                    if not rescue_found:
                        hub_traps = [t for t in hub.traps if t not in self.protected]  # refresh
                        for area_name, area_rooms in reserve_areas:
                            for rid in list(area_rooms):
                                if rid in self.net.nodes:
                                    continue
                                if rid in room_data:
                                    data = room_data[rid]
                                    r_doors = [d for d in data[0] if d not in self.protected] if len(data) > 0 else []
                                    r_traps = [t for t in data[1] if t not in self.protected] if len(data) > 1 else []
                                    r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                                    if len(r_pits) >= 1 and len(r_doors) >= 1 and (len(r_doors) + len(r_traps)) >= 2:
                                        self.add_room(rid)
                                        area_rooms.remove(rid)
                                        added_room = self.rooms.get_room(rid)
                                        added_pits = [p for p in added_room.pits if p not in self.protected]
                                        if len(hub_traps) > 0:
                                            this_trap = random.choice(hub_traps)
                                            this_pit = random.choice(added_pits)
                                            self.connect(this_trap, this_pit)
                                            print(f'WARNING: Added rescue room {rid} from {area_name} '
                                                  f'(doors={len(r_doors)}, traps={len(r_traps)}, pits={len(r_pits)}) '
                                                  f'and connected trap {this_trap} to pit {this_pit}. '
                                                  f'Restarting finalization.')
                                        else:
                                            print(f'WARNING: Added rescue room {rid} from {area_name} '
                                                  f'(doors={len(r_doors)}, traps={len(r_traps)}, pits={len(r_pits)}). '
                                                  f'Restarting finalization.')
                                        rescue_found = True
                                        break
                            if rescue_found:
                                break
                    if rescue_found:
                        continue  # Restart finalization from step 1

            # (3) Connect any remaining trapdoors/pits
            # Collect traps and pits from the ENTIRE network (hub + upstream + downstream).
            # This is important because keys applied during connect() can unlock traps in any room,
            # not just the hub. All unlocked traps must be connected to avoid "escape" routes.
            # By this step, all downstream branches should be collapsed into the hub.
            remaining_traps, remaining_pits = self.collect_network_traps_and_pits()
            while len(remaining_traps) > 0 and len(remaining_pits) > 0:
                random.shuffle(remaining_pits)
                if self.verbose:
                    vprint('(3) remaining traps:', remaining_traps, '; pits: ', remaining_pits)
                this_exit = remaining_traps.pop()
                this_conn = remaining_pits.pop()
                if self.verbose:
                    vprint('(3) connecting:', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)
                # Re-collect from entire network - keys applied during connect() may unlock new traps
                remaining_traps, remaining_pits = self.collect_network_traps_and_pits()

            # If we still have traps but no pits, try reserve areas for rooms with pits.
            # Adding a room creates a new downstream node that must be handled by steps 1-2,
            # so restart finalization from step 1 after adding.
            if len(remaining_traps) > 0 and reserve_areas is not None:
                if self.verbose:
                    vprint(f'(3) {len(remaining_traps)} traps remaining with no pits, checking reserve areas...')
                rescue_found = False
                for area_name, area_rooms in reserve_areas:
                    for rid in list(area_rooms):
                        if rid in self.net.nodes:
                            continue
                        if rid in room_data:
                            data = room_data[rid]
                            r_pits = [p for p in data[2] if p not in self.protected] if len(data) > 2 else []
                            if len(r_pits) > 0:
                                self.add_room(rid)
                                area_rooms.remove(rid)
                                if self.verbose:
                                    vprint(f'(3) added room with pits from reserve area {area_name}: {rid}. '
                                          f'Restarting finalization.')
                                rescue_found = True
                                break
                    if rescue_found:
                        break
                if rescue_found:
                    continue  # Restart finalization from step 1

            # If we still have traps but no pits, this is an unrecoverable state
            if len(remaining_traps) > 0:
                viz = self.visualize_branch_topology()
                raise RuntimeError(
                    f"finalize_map step 3: {len(remaining_traps)} traps remaining with no pits to connect. "
                    f"remaining_traps={remaining_traps}. This indicates insufficient pit entrances in the branch.\n"
                    f"{viz}"
                )

            # (4) The terminus is currently always a dead end room.  Connect it.
            # However, the terminus may have been merged into the hub through loop compression.
            # If so, we skip this step since the terminus is already connected.
            # Re-fetch hub in case it changed during steps 1-3
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            remaining_doors = [d for d in hub.doors if d not in self.protected]
            random.shuffle(remaining_doors)
            if self.verbose:
                vprint('(4) remaining doors:', remaining_doors)
            terminus = self.rooms.get_room(self.terminus)
            if terminus is not None and len(remaining_doors) > 0:
                # Terminus is still a separate room and we have doors to connect it
                this_exit = remaining_doors.pop()
                if self.terminus in self.dead_ends:
                    self.dead_ends.remove(self.terminus)
                unprotected_terminus_doors = [d for d in terminus.doors if d not in self.protected]
                this_conn = unprotected_terminus_doors.pop() if unprotected_terminus_doors else terminus.doors.pop()
                if self.verbose:
                    vprint('(4) connecting terminus:', this_exit , '-->', this_conn)
                self.connect(this_exit, this_conn)
            elif terminus is not None and len(remaining_doors) == 0:
                # Terminus exists but no hub doors available - add terminus to dead ends for step 6
                if self.terminus not in self.dead_ends:
                    self.dead_ends.append(self.terminus)
                if self.verbose:
                    vprint('(4) no hub doors to connect terminus, deferring to step 6')
            elif self.verbose:
                vprint('(4) terminus already merged into hub, skipping')

            # (5) Count doors in hub.  Connect doors within hub until # doors <= # dead ends
            # Clean up dead ends first - use list() to avoid modifying during iteration
            for de in list(self.dead_ends):
                if de not in self.net.nodes:
                    self.dead_ends.remove(de)

            # Validate state before step 5
            self.validate_finalize_state('pre-step5', hub=True,
                                         remaining_doors=remaining_doors, dead_ends=self.dead_ends)

            # We need at least 2 doors to connect a pair. If we have an odd excess
            # (doors - dead_ends is odd), we'll end up with 1 orphan door.
            while len(remaining_doors) > len(self.dead_ends) and len(remaining_doors) >= 2:
                if self.verbose:
                    vprint('(5) doors in hub:', len(remaining_doors), '.  dead ends:', len(self.dead_ends))
                this_exit = remaining_doors.pop()
                this_conn = remaining_doors.pop()
                if self.verbose:
                    vprint('(5) connecting doors in hub:', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)

            # (5b) Handle orphan door situation: we have more doors than dead ends but can't pair them
            if len(remaining_doors) > len(self.dead_ends):
                orphan_count = len(remaining_doors) - len(self.dead_ends)
                if self.verbose:
                    vprint(f'(5b) orphan door situation: {orphan_count} excess door(s), searching for available rooms')

                # Find rooms not yet in the network that can absorb the orphan doors
                hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
                available_rooms = [n for n in self.net.nodes
                                 if n not in self.get_upstream_nodes(hub_id)
                                 and n not in self.get_downstream_nodes(hub_id)
                                 and n != hub_id]

                for orphan_idx in range(orphan_count):
                    if len(remaining_doors) <= len(self.dead_ends):
                        break

                    orphan_door = remaining_doors[-1]  # Peek at next orphan

                    # Look for a room with an unprotected door we can connect to
                    found_connection = False
                    for room_id in available_rooms:
                        room = self.rooms.get_room(room_id)
                        if room is None:
                            continue
                        unprotected_room_doors = [d for d in room.doors if d not in self.protected]
                        if len(unprotected_room_doors) > 0:
                            this_exit = remaining_doors.pop()
                            this_conn = random.choice(unprotected_room_doors)
                            if self.verbose:
                                vprint(f'(5b) connecting orphan door {this_exit} --> room {room_id} door {this_conn}')
                            self.connect(this_exit, this_conn)
                            # Add this room to dead_ends if it now has only one connection
                            if room_id not in self.dead_ends and len(room.doors) == 1:
                                self.dead_ends.append(room_id)
                            found_connection = True
                            break

                    if not found_connection:
                        # No available room found - this is a problem state
                        print(f'WARNING: Could not resolve orphan door {orphan_door}. '
                              f'remaining_doors={remaining_doors}, dead_ends={self.dead_ends}')
                        # Try adding it back as a dead end connection point
                        # by finding any room with a door
                        for node in self.net.nodes:
                            room = self.rooms.get_room(node)
                            if room and len(room.doors) > 0:
                                unprotected = [d for d in room.doors if d not in self.protected]
                                if unprotected:
                                    this_exit = remaining_doors.pop()
                                    this_conn = random.choice(unprotected)
                                    if self.verbose:
                                        vprint(f'(5b) fallback: connecting orphan {this_exit} --> {this_conn} in {node}')
                                    self.connect(this_exit, this_conn)
                                    found_connection = True
                                    break

                        if not found_connection:
                            viz = self.visualize_branch_topology()
                            raise RuntimeError(
                                f'finalize_map step 5b: Cannot resolve orphan door. '
                                f'remaining_doors={remaining_doors}, dead_ends={self.dead_ends}, '
                                f'available_rooms={available_rooms}\n'
                                f'{viz}'
                            )

            # Validate state before step 6
            self.validate_finalize_state('pre-step6', hub=True,
                                         remaining_doors=remaining_doors, dead_ends=self.dead_ends)

            # (6) Connect dead ends to all remaining doors.
            # SAFETY: Connect key-bearing dead ends FIRST so that if they unlock new traps,
            # we still have keyless dead ends available. The LAST connection must be keyless.
            #
            # (6.0) Re-check warp room balance. Hallway warps were already handled
            # by _connect_orphan_warp_room; only dead-end orphans (per
            # is_dead_end: exactly 1 door, 0 traps, 0 pits, 0 locks) are eligible
            # to be wired up here. Each such warp's single door is connected to
            # one remaining_door, just like a normal step-6 dead-end connection.
            # This restores the >=2 connected-warp invariant without risking
            # inescapable downstream nodes earlier in finalization.
            # Step 4's terminus connect (and any prior step) may have merged the
            # hub into a new compound node, so re-fetch hub_id before passing it
            # into the digraph-aware classifier.
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            connected_warps, unconnected_warps = self._classify_branch_warp_rooms(hub_id)
            while (len(connected_warps) < 2
                   and len(remaining_doors) > 0
                   and any(self.is_dead_end(w) for w in unconnected_warps)):
                dead_end_warps = [w for w in unconnected_warps if self.is_dead_end(w)]
                warp_id = random.choice(dead_end_warps)
                warp_room = self.rooms.get_room(warp_id)
                this_exit = remaining_doors.pop()
                this_conn = warp_room.doors.pop()
                if self.verbose:
                    vprint(f'(6) connecting dead-end orphan warp room: '
                           f'{this_exit} --> {warp_id} door {this_conn}')
                self.connect(this_exit, this_conn)
                # Avoid double-counting if the warp was tracked as a dead end.
                if warp_id in self.dead_ends:
                    self.dead_ends.remove(warp_id)
                # connect() may have merged the warp into the hub; refresh.
                hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
                connected_warps, unconnected_warps = self._classify_branch_warp_rooms(hub_id)

            # Skip entirely if no doors to connect
            if len(remaining_doors) == 0:
                if self.verbose:
                    vprint('(6) No remaining doors to connect, skipping step 6')
            else:
                # Pre-check: we need enough dead ends for remaining doors
                if len(remaining_doors) > len(self.dead_ends):
                    viz = self.visualize_branch_topology()
                    raise RuntimeError(
                        f'finalize_map step 6: More remaining doors ({len(remaining_doors)}) than '
                        f'dead ends ({len(self.dead_ends)}). remaining_doors={remaining_doors}, '
                        f'dead_ends={self.dead_ends}. This indicates an imbalance from earlier steps.\n'
                        f'{viz}'
                    )

                # Capture initial state to detect TRULY NEW elements (not just remaining ones)
                # After steps 1-5, traps should be 0. Doors we know about are in remaining_doors.
                initial_traps, _, initial_doors = self.collect_network_traps_and_pits(
                    include_doors=True, exclude_upstream_doors=True)
                known_doors = set(remaining_doors) | set(initial_doors)

                # Select exactly the number of dead ends we need
                random.shuffle(self.dead_ends)
                needed_count = len(remaining_doors)
                selected_dead_ends = [self.dead_ends.pop() for _ in range(needed_count)]

                # Partition into key-bearing and keyless dead ends
                dead_ends_with_keys = []
                dead_ends_without_keys = []
                for de_id in selected_dead_ends:
                    de_room = self.rooms.get_room(de_id)
                    if de_room and len(de_room.keys) > 0:
                        dead_ends_with_keys.append(de_id)
                    else:
                        dead_ends_without_keys.append(de_id)

                if self.verbose:
                    vprint('(6) remaining dead ends:', selected_dead_ends)
                    vprint(f'(6) partitioned: {len(dead_ends_with_keys)} with keys, {len(dead_ends_without_keys)} without keys')

                # CRITICAL: The last dead end connected must NOT have a key.
                # If all selected dead ends have keys, we need to find a keyless one from remaining pool.
                if len(dead_ends_without_keys) == 0 and len(dead_ends_with_keys) > 0 and len(self.dead_ends) > 0:
                    # Try to swap a key-bearing dead end for a keyless one from the remaining pool
                    for i, candidate_id in enumerate(self.dead_ends):
                        candidate_room = self.rooms.get_room(candidate_id)
                        if candidate_room and len(candidate_room.keys) == 0:
                            # Found a keyless candidate - swap it in
                            swapped_out = dead_ends_with_keys.pop()
                            self.dead_ends.append(swapped_out)
                            self.dead_ends.pop(i)
                            dead_ends_without_keys.append(candidate_id)
                            if self.verbose:
                                vprint(f'(6) swapped key-bearing {swapped_out} for keyless {candidate_id}')
                            break

                if len(dead_ends_without_keys) == 0 and len(dead_ends_with_keys) > 0:
                    # All dead ends have keys - this is risky but we must proceed
                    if self.verbose:
                        vprint('(6) WARNING: All available dead ends have keys!')

                # Order: key-bearing first, keyless last (ensures last connection is safe)
                ordered_dead_ends = dead_ends_with_keys + dead_ends_without_keys
                random.shuffle(remaining_doors)

                for this_exit in remaining_doors:
                    room_id = ordered_dead_ends.pop(0)
                    room = self.rooms.get_room(room_id)

                    # Ebot's Rock is only a true dead end when it does NOT reward a
                    # character: a character reward gains a forced exit to Thamasa
                    # (injected in process_rewards), making it non-terminal so it is
                    # connected via that trap in earlier finalize steps, never here.
                    # Reaching step 6 as a dead end therefore means its reward was
                    # never mapped and will be backfilled (events.py). Pin the slot to
                    # esper/item so the backfill can't assign a character, which would
                    # teleport the player into an unconnected, leaking Thamasa.
                    if 'ms-wor-78' in str(room_id):
                        er_reward = ROOM_REWARD.get('ms-wor-78', {}).get("Ebot's Rock")
                        if er_reward is not None and er_reward.id is None:
                            er_reward.possible_types &= (RewardType.ESPER | RewardType.ITEM)
                            if self.verbose:
                                vprint("\t(6) Ebot's Rock connected as a dead end -> "
                                       "restricting its reward to esper/item (no character backfill)")

                    unprotected_room_doors = [d for d in room.doors if d not in self.protected]
                    this_conn = unprotected_room_doors.pop() if unprotected_room_doors else room.doors.pop()
                    if self.verbose:
                        has_keys = room and len(room.keys) > 0
                        vprint(f'(6) connecting dead ends: {this_exit} --> {this_conn} (has_keys={has_keys})')
                    self.connect(this_exit, this_conn)

                    # Check if this connection unlocked TRULY NEW elements via key application.
                    # Only break if we see traps (should be 0) or doors we didn't know about.
                    check_traps, _, check_doors = self.collect_network_traps_and_pits(
                        include_doors=True, exclude_upstream_doors=True)
                    new_traps = check_traps  # Any trap is new (should be 0 after step 3)
                    new_doors = [d for d in check_doors if d not in known_doors]
                    if len(new_traps) > 0 or len(new_doors) > 0:
                        if self.verbose:
                            vprint(f'(6) Key unlocked new elements! Breaking early to preserve entrances.')
                            vprint(f'    New traps: {new_traps}, New doors: {new_doors}')
                        # Return unused dead ends to the pool
                        self.dead_ends.extend(ordered_dead_ends)
                        break

            # Check if any new elements were unlocked during this iteration.
            # If so, restart from step 1 to handle them with proper topology-aware logic.
            # Exclude upstream doors since upstream rooms are inaccessible at this point -
            # they're only connected TO the hub via one-way pits and their doors don't matter.
            new_traps, new_pits, new_doors = self.collect_network_traps_and_pits(
                include_doors=True, exclude_upstream_doors=True)
            if len(new_traps) == 0 and len(new_doors) == 0:
                break  # Done - no new elements to process

            if self.verbose:
                vprint(f'\nNew elements unlocked: {len(new_traps)} traps, {len(new_doors)} doors')
                if new_traps:
                    vprint(f'    traps: {new_traps}')
                if new_doors:
                    vprint(f'    doors: {new_doors}')
                vprint('Restarting finalization from step 1...\n')

        if finalize_iteration >= max_finalize_iterations:
            # Collect remaining element info for diagnostics
            remaining_traps, remaining_pits, remaining_doors = self.collect_network_traps_and_pits(include_doors=True)
            viz = self.visualize_branch_topology()
            raise RuntimeError(
                f"finalize_map hit max iterations ({max_finalize_iterations}). "
                f"Remaining elements after {finalize_iteration} iterations: "
                f"{len(remaining_doors)} doors, {len(remaining_traps)} traps, {len(remaining_pits)} pits. "
                f"This suggests keys are continuously unlocking new elements in a loop.\n"
                f"{viz}"
            )

        # Final pass: a key applied in the last iteration can unlock a forced trap
        # without triggering another loop (protected exits don't count as newly
        # unlocked elements), so honor any forced connection that is now accessible.
        if reserve_areas is not None:
            self._honor_forced_connections(reserve_areas)

        self._active_reserve_areas = None

        if self.verbose:
            vprint('... closing branch complete!')

    def extend_branch_path(self):
        """Extend the branch by connecting an exit to an entrance.

        LOCATION-AWARE BRANCH MAPPING ALGORITHM

        The branch has three regions:
        - HUB (level 0): The central room connected to Narshe school
        - UPSTREAM (level -1): Rooms connected TO the hub via pits in the hub (forced connections)
        - DOWNSTREAM (levels 1, 2, ...): Rooms reached by falling through traps from hub

        CORE RULE: It is NEVER permissible to make a connection that leaves no exits
                   downstream of the new active room.

        RULES:
        0. Never connect to the last entrance to hub/upstream (until finalize_map)
        1. Can connect downstream trap to unconnected pit-in, trap-out (PITO) room
        2a. Can connect downstream trap to PIDO room if branch has exits after connection
        (the PIDO room's doors count as new exits)
        2b. If unconnected pit in hub/upstream, can connect downstream door to DITO room
        3. Only connect downstream trap to pit in its local upstream (not hub's upstream)
           IF the resulting compressed loop has another exit
        """
        # === STEP 0: Analyze branch topology ===
        topology = self.classify_topology()
        if topology is None:
            # No hub yet - fall back to simple behavior
            if self.verbose:
                vprint('\tNo hub found, using simple extension')
            return self._extend_branch_path_simple()

        hub_id = topology['hub_id']
        hub_and_upstream = topology['hub_and_upstream']
        room_levels = topology['room_levels']

        # Get current active room info
        active_room = self.rooms.get_room(self.active)
        active_level = room_levels.get(self.active, 0)
        upstream = self.get_upstream_nodes(self.active)
        downstream = self.get_downstream_nodes(self.active)
        currently_connected = set(room_levels.keys())

        if self.verbose:
            vprint(f'\t=== LOCATION-AWARE EXTENSION ===')
            vprint(f'\tActive room: {self.active} (level {active_level})')
            vprint(f'\tHub+Upstream: {hub_and_upstream}')
            vprint(f'\tUpstream: {upstream}, Downstream: {downstream}')

        # === STEP 1: Check for forced exits ===
        all_connected_rooms = [self.active] + list(downstream)
        all_exits = []
        for room_id in all_connected_rooms:
            room = self.rooms.get_room(room_id)
            if room:
                all_exits.extend(list(room.doors) + list(room.traps))

        forced_exits = [e for e in all_exits if e in forced_connections.keys()]
        if len(forced_exits) > 0:
            this_exit = forced_exits[0]
            this_conn = forced_connections[this_exit][0]
            if self.verbose:
                vprint(f'\tForced exit: {this_exit} --> {this_conn}')
            return this_exit, this_conn

        # === STEP 2: Collect exits from the active path ===
        # Prioritize exits from the most downstream rooms (deepest in the tree)
        # When the active node is downstream, exclude initially-locked exits: the player
        # may not have obtained the keys yet, so following a locked exit could collapse
        # it into the hub and connect other exits to dead ends, trapping the player.
        available_exits = {'doors': [], 'traps': []}
        is_downstream = active_level > 0

        if len(downstream) == 0:
            available_exits['doors'] = [d for d in active_room.doors
                                        if d not in self.protected
                                        and (not is_downstream or d not in self.initially_locked_exits)]
            available_exits['traps'] = [t for t in active_room.traps
                                        if t not in self.protected
                                        and (not is_downstream or t not in self.initially_locked_exits)]
            exit_room_id = self.active
        else:
            # Get the most downstream nodes
            downstream_paths = self.get_downstream_paths(self.active)
            if downstream_paths:
                max_depth = max(len(p) for p in downstream_paths)
                deepest_rooms = set(p[-1] for p in downstream_paths if len(p) == max_depth)
            else:
                deepest_rooms = {self.active}

            for room_id in deepest_rooms:
                room = self.rooms.get_room(room_id)
                if room:
                    available_exits['doors'].extend(
                        [d for d in room.doors if d not in self.protected
                         and (not is_downstream or d not in self.initially_locked_exits)])
                    available_exits['traps'].extend(
                        [t for t in room.traps if t not in self.protected
                         and (not is_downstream or t not in self.initially_locked_exits)])
            exit_room_id = list(deepest_rooms)[0] if deepest_rooms else self.active

        if self.verbose:
            vprint(f'\tAvailable exits: {len(available_exits["doors"])} doors, {len(available_exits["traps"])} traps')

        # === STEP 3: Determine exit order based on location ===
        # ## Original logic:
        # # In hub/upstream: prefer doors (maintain connectivity)
        # # In downstream: prefer traps (extend the tree), but only if valid targets exist
        # if active_level <= 0:
        #     # We're in hub or upstream - prefer doors to maintain 2-way connectivity
        #     exit_type_order = ['doors', 'traps']
        # else:
        #     # We're downstream - prefer traps to extend, but check targets first
        #     exit_type_order = ['traps', 'doors']
        # ## New logic HGR 260202_1824: Always prefer traps
        exit_type_order = ['traps', 'doors']

        # Check if we have matching targets before committing to an order
        # This prevents trying traps when there are no pits available
        trap_targets_exist = False
        door_targets_exist = False

        # Quick check for available targets
        for room_id in self.net.nodes:
            if room_id in currently_connected or room_id == self.terminus:
                continue
            room = self.rooms.get_room(room_id)
            if room:
                if len([p for p in room.pits if p not in self.protected]) > 0:
                    trap_targets_exist = True
                if len([d for d in room.doors if d not in self.protected]) > 0:
                    door_targets_exist = True
                if trap_targets_exist and door_targets_exist:
                    break

        # Also check upstream for targets (loop formation)
        for up_id in hub_and_upstream:
            up_room = self.rooms.get_room(up_id)
            if up_room:
                if len([p for p in up_room.pits if p not in self.protected]) > 0:
                    trap_targets_exist = True
                if len([d for d in up_room.doors if d not in self.protected]) > 0:
                    door_targets_exist = True

        if self.verbose:
            vprint(f'\tTarget availability: pits={trap_targets_exist}, doors={door_targets_exist}')

        # Adjust order based on actual availability
        if exit_type_order[0] == 'traps' and not trap_targets_exist and door_targets_exist:
            exit_type_order = ['doors', 'traps']
        elif exit_type_order[0] == 'doors' and not door_targets_exist and trap_targets_exist:
            exit_type_order = ['traps', 'doors']

        # === STEP 4: Try each exit type ===
        # For each exit, check validity by evaluating the CONNECTION, not just the source room.
        # An exit is valid if the destination has exits (either its own, or via loop formation).
        for exit_type in exit_type_order:
            exits = available_exits[exit_type]
            if len(exits) == 0:
                continue

            # Collect all exits with their rooms
            all_exits = []
            for exit_id in exits:
                exit_room = self.rooms.get_room_from_element(exit_id)
                if exit_room is None:
                    continue
                all_exits.append((exit_id, exit_room.id))

            if self.verbose:
                vprint(f'\t{exit_type}: {len(all_exits)} exits to evaluate')

            # Shuffle and try each exit
            random.shuffle(all_exits)
            for exit_id, exit_room_id in all_exits:
                # Find valid targets - this method checks if each potential destination
                # would leave the branch with exits (handles unconnected rooms, loops, etc.)
                if exit_type == 'traps':
                    valid_targets = self.get_valid_pit_targets_v2(exit_id, exit_room_id, topology)
                else:
                    valid_targets = self.get_valid_door_targets_v2(
                        exit_id, exit_room_id, topology,
                        available_doors=len(available_exits['doors']),
                        available_traps=len(available_exits['traps'])
                    )

                if self.verbose:
                    vprint(f'\t\tExit {exit_id}: {len(valid_targets)} valid targets')
                    if False:
                        vprint(valid_targets)


                if len(valid_targets) > 0:
                    this_conn = random.choice(valid_targets)
                    if self.verbose:
                        conn_room = self.rooms.get_room_from_element(this_conn)
                        conn_room_id = conn_room.id if conn_room else 'unknown'
                        vprint(f'\t\tSelected: {exit_id} --> {this_conn} (room {conn_room_id})')
                    self.last_stuck_reason = StuckReason.NONE
                    return exit_id, this_conn

        # === STEP 5: All strategies exhausted ===
        self._diagnose_stuck_reason(available_exits, topology)

        if self.verbose:
            vprint(f'\tBranch extension failed. Reason: {self.last_stuck_reason}')

        return None, None

    def _extend_branch_path_simple(self):
        """Simple extension when no topology analysis is possible (no hub yet)."""
        active_room = self.rooms.get_room(self.active)
        if active_room is None:
            self.last_stuck_reason = StuckReason.NO_EXITS
            return None, None

        def _cooldown_blocks(room_id):
            # Filter unconnected warp/town rooms while their cooldown is active.
            if room_id in WARP_ROOMS and self.warp_cooldown > 0:
                return True
            if room_id in TOWN_ROOMS and self.town_cooldown > 0:
                return True
            return False

        # Try doors first
        doors = [d for d in active_room.doors if d not in self.protected]
        if len(doors) > 0:
            exit_id = random.choice(doors)
            # Find a door to connect to
            for room_id in self.net.nodes:
                if room_id == self.active:
                    continue
                if _cooldown_blocks(room_id):
                    continue
                room = self.rooms.get_room(room_id)
                if room:
                    room_doors = [d for d in room.doors if d not in self.protected and d != exit_id]
                    if len(room_doors) > 0:
                        return exit_id, random.choice(room_doors)

        # Try traps
        traps = [t for t in active_room.traps if t not in self.protected]
        if len(traps) > 0:
            exit_id = random.choice(traps)
            # Find a pit to connect to
            for room_id in self.net.nodes:
                if room_id == self.active:
                    continue
                if _cooldown_blocks(room_id):
                    continue
                room = self.rooms.get_room(room_id)
                if room:
                    room_pits = [p for p in room.pits if p not in self.protected]
                    if len(room_pits) > 0:
                        return exit_id, random.choice(room_pits)

        self.last_stuck_reason = StuckReason.NO_EXITS
        return None, None

    def _diagnose_stuck_reason(self, available_exits, topology):
        """Diagnose why branch extension failed and set last_stuck_reason."""
        have_traps = len(available_exits['traps']) > 0
        have_doors = len(available_exits['doors']) > 0

        if not have_traps and not have_doors:
            self.last_stuck_reason = StuckReason.NO_EXITS
            return

        # Check what targets are available
        currently_connected = set(topology['room_levels'].keys())
        hub_and_upstream = topology['hub_and_upstream']

        available_pits = False
        available_pido = False
        available_doors = False

        for room_id in self.net.nodes:
            if room_id in currently_connected or room_id == self.terminus:
                continue
            room = self.rooms.get_room(room_id)
            if room is None:
                continue

            pits = len([p for p in room.pits if p not in self.protected])
            doors = len([d for d in room.doors if d not in self.protected])
            traps = len([t for t in room.traps if t not in self.protected])

            if pits > 0:
                available_pits = True
                if doors > 0:
                    available_pido = True
            if doors > 0:
                available_doors = True

        # Check upstream for entrances
        hub_upstream_doors, hub_upstream_pits = self.count_entrances_in_region(hub_and_upstream)

        if have_traps and not available_pits and hub_upstream_pits == 0:
            self.last_stuck_reason = StuckReason.NEED_PITS
        elif have_traps and not available_pido:
            self.last_stuck_reason = StuckReason.NEED_PIDO
        elif have_doors and not available_doors and hub_upstream_doors == 0:
            self.last_stuck_reason = StuckReason.NEED_DOORS
        else:
            self.last_stuck_reason = StuckReason.NO_SAFE_EXITS

    def extend_branch_path_old(self):
        # Extend this branch by (1) adding a node or (2) closing a loop, without terminating the branch.
        active_room = self.rooms.get_room(self.active)
        all_entrances = list(active_room.doors) + list(active_room.pits)
        upstream = self.get_upstream_nodes(self.active)
        downstream = self.get_downstream_nodes(self.active)
        if self.verbose:
            vprint('\tActive room: ', self.active, '.\n\tUpstream nodes: ', upstream,
                  '\n\tDownstream nodes: ', downstream,
                  '\n\tAll entrances: ', all_entrances)
        hub_is_upstream = len([n for n in upstream if 'ruin_hub_' in str(n)]) > 0
        if hub_is_upstream and self.verbose:
            vprint('\tHub is upstream!')
        for node in upstream:
            room = self.rooms.get_room(node)
            all_entrances += list(room.doors) + list(room.pits)

        allow_traps = len(all_entrances) >= 1
        dito_ok = len(
            all_entrances) >= 2  # a door-in, trap-out room effectively replaces a door (entrance) with a trap (not entrance), so an extra entrance is required
        if self.verbose and not allow_traps:
            vprint('\ttraps not allowed!')
        elif self.verbose:
            vprint('\ttraps allowed!')

        # Look at unconnected hubs.
        currently_used = [self.active] + list(downstream) + list(upstream)
        if self.verbose:
            vprint('\tCurrently used rooms:', currently_used)
        new_hub_door_conns = self.get_available_hub_connections(element_type=0, excluded=currently_used,
                                                                  dito_ok=dito_ok)
        new_hub_pit_conns = self.get_available_hub_connections(element_type=1, excluded=currently_used)
        # If hub is upstream, possibly allow connecting back to the hub (closing the loop)
        if hub_is_upstream:
            # Requirements: total exits after connection > 0
            uppaths = self.get_upstream_paths(self.active)
            for path in uppaths:
                if self.verbose:
                    vprint('\tchecking upstream path:', path)
                path_door_count = 0
                path_trap_count = 0
                tracker = [False, False]
                for node_id in path:
                    node = self.rooms.get_room(node_id)
                    path_door_count += len(node.doors)
                    path_trap_count += len(node.traps)
                    if (path_door_count + path_trap_count) > 1:
                        # We've met the condition for trapdoor connections.  Add pits.
                        new_hub_pit_conns.update(node.pits)
                        if self.verbose and tracker[0] is False:
                            vprint('\t\tTrapdoor condition met at', node_id)
                            tracker[0] = True
                        if self.verbose:
                            vprint('\t\tAdding', node_id, node.pits)
                    if (path_door_count + path_trap_count) > 2:
                        # We've met the condition for door connections.  Add doors.
                        new_hub_door_conns.update(node.doors)
                        if self.verbose and tracker[1] is False:
                            vprint('\t\tDoor condition met at', node_id)
                            tracker[1] = True
                        if self.verbose:
                            vprint('\t\tAdding', node_id, node.doors)

        if self.verbose:
            vprint('\tCollected available hub connections:')
            vprint('\t\tdoors:', new_hub_door_conns)
            vprint('\t\tpits:', new_hub_pit_conns)

        # Select which exits are permissable based on what is available.
        # WE HAVE TO BE CAREFUL to not fully map a branch before we run out of checks.
        # Imagine if a branch had only Serpent Trench on it.  hub --> crescent --> ST --> nikeah has no way back
        #   (This case would have to do hub --> nikeah --> crescent --> ST --> nikeah)
        # (a) do this in a nested way, as before?
        # (b) catch the errors in one pass?  Active room + upstream must always have entrances.
        all_exits = []
        available_connections = [[], []]
        if len(new_hub_door_conns) > 0:
            all_exits += list(active_room.doors)
            for node_id in downstream:
                node = self.rooms.get_room(node_id)
                all_exits += list(node.doors)
            available_connections[0] += new_hub_door_conns
        if len(new_hub_pit_conns) > 0 and allow_traps:
            all_exits += list(active_room.traps)
            for node_id in downstream:
                node = self.rooms.get_room(node_id)
                all_exits += list(node.traps)
            available_connections[1] += new_hub_pit_conns
        if self.verbose:
            vprint('\tCollected available active room exits:', len(all_exits))
            vprint('\t\t', all_exits)

        # Handle failure modes: no exits available
        legal_exits = True
        if len(all_exits) == 0:
            # I think the main way we get here is if there are no more hub rooms, and a check is in a dead end.
            check_door_cons = self.get_all_check_connections(element_type=0)
            check_pit_cons = self.get_all_check_connections(element_type=1)
            if len(check_door_cons) > 0:
                all_exits += list(active_room.doors)
                available_connections[0] += check_door_cons
                if self.verbose:
                    vprint('\tInstead using rooms with checks (doors):', len(all_exits))
                    vprint('\t\t', all_exits)
            elif len(check_pit_cons) > 0 and allow_traps:
                all_exits += list(active_room.traps)
                available_connections[1] += check_pit_cons
                if self.verbose:
                    vprint('\tInstead using rooms with checks (traps):', len(all_exits))
                    vprint('\t\t', all_exits)
            else:
                if self.verbose:
                    vprint('No legal exits found on branch!')
                legal_exits = False

        # If any exits are forced, apply them
        if legal_exits:
            forced_exits = [e for e in all_exits if e in forced_connections.keys()]
            if len(forced_exits) > 0:
                this_exit = forced_exits.pop()
                this_conn = forced_connections[this_exit][0]
                if self.verbose:
                    vprint('Found forced exit!', this_exit, '-->', this_conn)
            else:
                this_exit = random.choice(all_exits)
                this_type = active_room.element_type(this_exit)
                if self.verbose:
                    vprint('All allowed exits:', all_exits, '.  Choose: ', this_exit, '(type ', this_type, ')')
                # Reconstruct available connections for this exit?

                if this_exit in available_connections[this_type]:
                    available_connections[this_type].remove(this_exit)
                this_conn = random.choice(available_connections[this_type])
                if self.verbose:
                    vprint('Available connections:', available_connections[this_type], '. Choose: ', this_conn)

        else:
            this_exit = None
            this_conn = None

        return this_exit, this_conn

    def check_for_rewards(self, this_conn):
        # Look at the room(s) being connected & return any rewards found
        conn_room = self.rooms.get_room_from_element(this_conn)
        downstream = self.get_downstream_nodes(conn_room.id)
        if self.verbose:
            vprint('Looking for reward in room', conn_room.id, '...')
        if conn_room.id in self.check_rooms:
            reward_room = conn_room.id
        elif len([n for n in downstream if n in self.check_rooms]) > 0:
            # Reward room can be downstream if there's forced connections in/out
            reward_room = [n for n in downstream if n in self.check_rooms][0]
        else:
            reward_room = None

        if reward_room is not None:
            # If this is a compound room produced by compress_loop (e.g. forced 4418<->744
            # fusing 371 and 'ruin-doma'), gather rewards from every original check_room
            # that was merged into it. ROOM_REWARD stays keyed on original ids.
            source_rooms = self._compound_check_rooms.get(reward_room, [reward_room])
            rewards = []
            for src in source_rooms:
                rewards.extend([(k, ROOM_REWARD[src][k]) for k in ROOM_REWARD[src].keys()])
            if self.verbose:
                vprint('Found a reward! ', [(r[0], r[1].possible_types) for r in rewards], 'in room',
                      reward_room)

            # Remove check room from the list
            self.check_rooms.remove(reward_room)
            self._compound_check_rooms.pop(reward_room, None)

            return rewards

        else:
            return None


class ruination_map():
    # Class to organize data for mapping out ruination mode branches

    # Initial values for the per-branch cooldown counters that prevent warp points
    # and towns from clustering near the hub or each other. While the counter is
    # > 0, rooms of the corresponding type cannot be mapped onto the branch; each
    # unconnected room mapped decrements both counters, and mapping a warp/town
    # room resets the corresponding counter back to the initial value. Tune here.
    WARP_COOLDOWN_INITIAL = 5
    TOWN_COOLDOWN_INITIAL = 4

    def __init__(self, args, starting_party, verbose=False, characters=None):
        # Verbose flag controls debug output throughout map generation
        self.verbose = verbose

        # Instance attributes - each instance gets fresh state
        self.RewardsAvailable = [0, 0]   # [# possible characters, # possible espers]
        self.PARTY = list(starting_party)  # use character names in all caps
        self.Requested = [3, 0]
        self.branches = [None, None, None]  # Populated in branch creation loop below
        self.branch_checks = [[], [], []]   # checks available on each branch, stored locally
        self.AreasUsed = dict()   # use a dict to track 'AreaName': branch_id
        self.keychain = set(starting_party)   # global keychain, initialized with party
        if args.open_world:
            self.keychain.update(ALL_CHARACTERS)  # open world: all characters immediately accessible
            CHARACTER_LOCKED_REWARDS.clear()      # open world: no character-locked checks
            REWARDS_LOCKED_BY_CHARACTER.clear()
        self.accessible_shops = []  # list of shop IDs that are accessible (for dried meat assignment)
        self.characters_data = characters  # Characters object for querying commands (e.g. Blitz)

        # Spoiler log tracking: ordered list of reward acquisitions
        # Each entry: {'order': int, 'name': str, 'branch': int, 'type': RewardType, 'reward_id': int, 'reward_room': room_id}
        self.reward_log = []

        self.args = args

        # Apply Dream Maze configuration based on -rdm flag
        self._configure_dream_maze(args)

        # Randomize Kefka's Tower lanes if -rkt is set (independent of the
        # branch graph: produces internal KT door/trap connections injected at
        # the end of generate_map_with_characters).
        self.kt_lane_map = None
        if getattr(args, 'ruin_kefka_tower', False):
            self.kt_lane_map = self._randomize_kefka_tower()

        # Read character/esper requirements from args (extracted from flagstring in args/objectives.py)
        # These are stored as [min, max] ranges; pick a random value in the range
        char_min, char_max = args.ruin_characters_required
        esper_min, esper_max = args.ruin_espers_required
        # Enforce minimum of 3 characters for ruination mode
        char_min = max(char_min, 3)
        char_max = max(char_max, 3)
        self.Requested[0] = random.randint(char_min, char_max)
        self.Requested[1] = random.randint(esper_min, esper_max)
        if self.verbose:
            vprint('Requested: ', self.Requested[0], 'characters, ', self.Requested[1], 'espers')

        # PRE-PLANNING PHASE: Determine which characters will be obtained and reserve areas
        self.planned_characters, self.reserve_characters, self.dead_checks_allowed = \
            self.pre_plan_character_acquisition()

        if self.verbose:
            vprint('Pre-plan: Will obtain characters:', self.planned_characters)
            vprint('Pre-plan: Reserve characters (for extra areas):', self.reserve_characters)
            vprint('Pre-plan: Dead checks allowed:', self.dead_checks_allowed)

        # Check if any planned or starting party character has Blitz; if so, 50% chance to include Duncan's House
        self.include_duncan_house = False
        self.duncan_house_character = None
        if self.characters_data is not None:
            blitz_char_ids = self.characters_data.get_characters_with_command("Blitz")
            blitz_char_names = [self.characters_data.DEFAULT_NAME[cid] for cid in blitz_char_ids]
            # Check starting party first, then planned characters
            party_blitz = [c for c in self.PARTY if c in blitz_char_names]
            planned_blitz = [c for c in self.planned_characters if c in blitz_char_names]
            all_blitz = party_blitz + planned_blitz
            if all_blitz and random.random() < 0.5:
                self.duncan_house_character = all_blitz[0]
                self.include_duncan_house = True
            if self.verbose:
                vprint(f'Blitz characters: {blitz_char_names}')
                vprint(f'Duncan\'s House: {"included" if self.include_duncan_house else "not included"}'
                      + (f' (character: {self.duncan_house_character})' if self.include_duncan_house else ''))

        # Assemble initial areas from starting party + planned characters
        initial_areas = set()
        for character in self.PARTY:
            initial_areas.update(CHARACTER_AREAS.get(character, []))
        # If Duncan's House is included and the Blitz character is in the starting party, add it now
        if self.include_duncan_house and self.duncan_house_character in self.PARTY:
            initial_areas.add('DuncanHouse')
        if self.verbose:
            vprint('Areas used: ', initial_areas)

        # Create branches with starting areas
        hub_id = 'ruin_hub'
        hub = room_data[hub_id]
        termini = [t for t in RUIN_TERMINI]
        random.shuffle(termini)
        for i, door_id in enumerate(hub[0]):
            # Create a new hub room
            hub_room_id = 'ruin_hub_' + str(i)
            hub_room = [[door_id], [], [], 1]  # data structure for hub room
            room_data[hub_room_id] = hub_room
            starting_rooms = [hub_room_id]
            # Also include a ruin terminus
            terminus = termini.pop()
            starting_rooms.append(terminus)

            # Create branch
            branch = RuinationBranch(starting_rooms)
            branch.active = hub_room_id  # start in the hub room
            branch.verbose = self.verbose
            self.branches[i] = branch

        # Distribute areas to the branches
        self.distribute_areas(initial_areas)
        if self.verbose:
            vprint('Rewards available: ', self.RewardsAvailable)

        # Apply keys to branches
        for branch in self.branches:
            for k in self.keychain:
                branch.apply_key(k)

        #print(branch.original_room_ids)

    def _configure_dream_maze(self, args):
        """Configure Dream Maze handling based on -maze flag.

        Default (no flag): Doma and DreamMaze are forced to the same branch.
        'sep': DreamMaze is separated from Doma and gated by ALL instead of CYAN.
        'iso': DreamMaze is replaced by a single composite room (ruin-stooge-maze),
               but the nine maze rooms are internally randomized.
        """
        dream_maze_mode = getattr(args, 'ruin_dream_maze', None)
        self.isolated_maze_map = None  # Will hold internal maze connections for iso mode

        if dream_maze_mode == 'sep':
            # Separate: move DreamMaze from CYAN to ALL gating
            if 'DreamMaze' in CHARACTER_AREAS['CYAN']:
                CHARACTER_AREAS['CYAN'].remove('DreamMaze')
            if 'DreamMaze' not in CHARACTER_AREAS['ALL']:
                CHARACTER_AREAS['ALL'].append('DreamMaze')
            # No forced_same_branch entry, so they can be on different branches

        elif dream_maze_mode == 'iso':
            # Isolate: replace the nine maze rooms with a single composite room
            RUIN_ROOM_SETS['DreamMaze'] = ['ruin-stooge-maze']
            # discard (not remove): map generation may be retried, which
            # re-instantiates ruination_map and re-runs this configuration. A
            # bare remove() would KeyError on the second pass.
            WARP_ROOMS.discard(424)
            WARP_ROOMS.add('ruin-stooge-maze')
            # Update ROOM_REWARD: move 429's reward to ruin-stooge-maze
            if 429 in ROOM_REWARD:
                ROOM_REWARD['ruin-stooge-maze'] = ROOM_REWARD.pop(429)
            # Still forced to same branch as Doma (CYAN gated)
            forced_same_branch['Doma'] = forced_same_branch.get('Doma', set()) | {'DreamMaze'}
            forced_same_branch['DreamMaze'] = {'Doma'}
            # Randomize internal maze connections
            self.isolated_maze_map = self._randomize_isolated_maze()

        else:
            # Default: force Doma and DreamMaze to same branch (preserves current behavior)
            forced_same_branch['Doma'] = forced_same_branch.get('Doma', set()) | {'DreamMaze'}
            forced_same_branch['DreamMaze'] = {'Doma'}

    def _randomize_isolated_maze(self):
        """Randomize the internal connections of the Stooges Maze (rooms 421-429).

        Rather than walking out a single connection (which could leave the maze
        unsolvable), this generates random door / trap matchings and *verifies*
        the maze is completable, retrying up to 20000 times.  A layout is valid
        when, treating doors as two-way and traps as one-way (trap -> pit) edges
        between rooms:
          - EVERY room can reach the ending room (429), so a one-way trap can
            never strand the party (this subsumes "entry -> 429" and
            "stooge room -> 429"), and
          - both stooge/key rooms (423 'cd1', 427 'cd2') are reachable from 429.
        Together: wherever the party ends up they can reach the hub, and from the
        hub they can round-trip to collect both stooge keys and return to unlock
        the boss door (429's locked exit 2070, gated by cd1+cd2).  No softlock is
        possible.  Returns [[door pairs], [trap->pit pairs]].
        """
        maze_rooms = [421, 422, 423, 424, 425, 426, 427, 428, 429]
        STOOGE_ROOMS = [423, 427]   # rooms holding the stooge keys cd1 / cd2
        END_ROOM = 429              # boss room (locked exit 2070 needs cd1+cd2)

        # Entry pits exclude the two stooge rooms (6847/423, 6852/427) and the
        # west room (6844/422) so the party never starts inside a key room.
        entry_pits = [6845, 6846, 6854, 3069, 6849, 6843, 6848, 6853]

        # Which room owns each door / trap / pit (room_data positions 0/1/2).
        door_room, trap_room, pit_room = {}, {}, {}
        for r in maze_rooms:
            for d in room_data[r][0]: door_room[d] = r
            for t in room_data[r][1]: trap_room[t] = r
            for p in room_data[r][2]: pit_room[p] = r
        doors, traps, pits = list(door_room), list(trap_room), list(pit_room)

        def reachable(door_pairs, trap_pits, start):
            adj = {r: set() for r in maze_rooms}
            for d1, d2 in door_pairs:                  # doors: two-way
                adj[door_room[d1]].add(door_room[d2])
                adj[door_room[d2]].add(door_room[d1])
            for t, p in trap_pits:                     # traps: one-way (trap -> pit)
                adj[trap_room[t]].add(pit_room[p])
            seen, stack = {start}, [start]
            while stack:
                for n in adj[stack.pop()]:
                    if n not in seen:
                        seen.add(n); stack.append(n)
            return seen

        def solvable(door_pairs, trap_pits):
            # Every room must reach the ending, so a one-way trap can never
            # strand the party (subsumes entry -> 429 and each stooge -> 429).
            if any(END_ROOM not in reachable(door_pairs, trap_pits, r) for r in maze_rooms):
                return False
            # From the hub, both stooge keys must be collectable.
            from_end = reachable(door_pairs, trap_pits, END_ROOM)
            return all(s in from_end for s in STOOGE_ROOMS)

        entry_pit = start_room_id = door_pairs = trap_pits = None
        found = False
        for _ in range(20000):
            entry_pit = random.choice(entry_pits)
            start_room_id = pit_room[entry_pit]
            # random two-way door pairing (every door is in a distinct room)
            ds = doors[:]; random.shuffle(ds)
            door_pairs = [[ds[i], ds[i + 1]] for i in range(0, len(ds), 2)]
            # random trap -> pit matching over the pits other than the entry pit
            avail = [p for p in pits if p != entry_pit]; random.shuffle(avail)
            trap_pits = [[traps[i], avail[i]] for i in range(len(traps))]
            if any(trap_room[t] == pit_room[p] for t, p in trap_pits):
                continue  # don't drop a trap back into its own room
            if solvable(door_pairs, trap_pits):
                found = True
                break
        if not found:
            vprint('WARNING: dream maze verification failed after 20000 tries; using last layout')

        # The composite room is entered through the chosen pit; its exit trap
        # (2070) is wired up by the branch mapper.
        room_data['ruin-stooge-maze'][2] = [entry_pit]

        if self.verbose:
            vprint(f'Dreamscape maze: entry pit {entry_pit} -> start room {start_room_id} '
                   f'({len(door_pairs)} doors, {len(trap_pits)} traps)')
            for d1, d2 in door_pairs:
                vprint(f'\tdoor: {d1} <-> {d2}  (room {door_room[d1]} <-> {door_room[d2]})')
            for t, p in trap_pits:
                vprint(f'\ttrap: {t} -> {p}  (room {trap_room[t]} -> {pit_room[p]})')

        return [door_pairs, trap_pits]

    # Kefka's Tower structural constants (the KT* rooms in data/rooms.py).
    KT_ENTRIES = ['KTa1', 'KTb1', 'KTc1']
    KT_FINALS = ['KTa-final', 'KTb-final', 'KTc-final']
    KT_BOSSES = ['KTb4', 'KTb10', 'KTc7', 'KTc12']
    KT_HALLWAYS = ['KTa2', 'KTa4', 'KTa6', 'KTa7',  # KT rooms that include only 2 doors (no chests, bosses, etc.)
                   'KTb9', 'KTb11',                 # 11 of 35 rooms are just filler from a map perspective.
                   'KTc2', 'KTc4', 'KTc9', 'KTc11', 'KTc13']  # We could remove some before mapping.
    # Rooms joined by a key-gated forced crossing must share a lane; the
    # crossing is a one-way edge a -> b, gated by the named switch key.
    KT_GATED = [('KTa5a', 'KTa5b', 'KT1'), ('KTa8a', 'KTa8b', 'KT2')]
    # The forced crossings as data/rooms.forced_connections entries (locked
    # traps living in room_data locks). Fed to ForceConnections during the
    # walk, then stripped from the output (they are vanilla map features, not
    # writable ROM exits).
    KT_FORCED = {2182: [2183], 2184: [2185]}
    KT_PLATFORM_IDS = {2182, 2183, 2184, 2185}
    # Room that holds each switch key (key enters the global keychain when the
    # room is first reached by any party).
    KT_KEY_ROOM = {'KTb8': 'KT1', 'KTc10': 'KT2'}
    # Budget: number of fresh partitions to try before falling back to vanilla.
    KT_MAX_SPLITS = 400

    def _randomize_kefka_tower(self):
        """Randomize the three lanes of Kefka's Tower (the KT* rooms).

        Kefka's Tower has three lanes (originally Left/Middle/Right). Each lane
        starts with a party dropping into an entry room (KTa1/KTb1/KTc1) and
        ends in one of the three sections of the 4-ton switch room
        (KT*-final). The lanes interact: the Middle and Right lanes each hold a
        switch (keys KT1 / KT2) that unlocks a key-gated forced crossing (a
        switch platform / broken stairs) somewhere in another lane.

        KT's door graph is deliberately sparse, so a lane cannot be connected by doors alone --
        connectivity also relies on the one-way conveyor/pipe connections and the two
        gated platforms. Random matching therefore almost never connects every room.
        Instead, we use the same constructive network walk the ruination
        branches use (data.walks.Network.connect_network), once per lane.

          1. Pre-condition by partitioning every KT room into three
             groups that satisfy cheap, necessary constraints:
               - each lane gets exactly one entry and one ending,
               - rooms joined by a forced crossing share a lane,
               - no lane has more than two of the four bosses,
               - each lane has equal numbers of one-way exits and entrances,
                 and an even door count.
          2. For each lane, unlock the platforms (so the walk treats them as
             open), force their crossings, attach dead ends, and walk out a
             fully-connected, traversable layout.
          3. Verify the assembled three-lane map against softlocks by modelling
             the true dynamics: three parties (one per lane) moving
             asynchronously over a shared, monotonic keychain (see verify()).
             Require EVERY room reachable (no orphans; all four bosses and both
             switches reached) AND that from EVERY situation the player can get
             into, the three parties can still all be herded to their endings
             (no party can ride a one-way into a pocket whose only exit is a
             gated crossing whose key it can no longer collect).
          4. Re-partition (fresh split + walk) until a layout verifies or the
             budget is exhausted.

        Returns [[door pairs], [trap->pit pairs]] (with the platform ids
        stripped), or None on failure (callers fall back to the vanilla KT
        layout).
        """
        import log.verbose as _verbose_mod

        KT = [r for r in room_data if isinstance(r, str) and r.startswith('KT')]
        ENTRIES, FINALS, BOSSES, HALLWAYS = self.KT_ENTRIES, self.KT_FINALS, self.KT_BOSSES, self.KT_HALLWAYS
        GATED, KEY_ROOM = self.KT_GATED, self.KT_KEY_ROOM
        PLATFORM_IDS = self.KT_PLATFORM_IDS

        remove_hallways = 0  # number of hallways to remove
        if remove_hallways in range(1, len(HALLWAYS)+1):
            rh = random.sample(HALLWAYS, remove_hallways)
            for r in rh:
                KT.remove(r)

        # Per-room free connection elements (the gated-crossing traps live in
        # room_data locks, not in these slots).
        doors_of = {r: list(room_data[r][0]) for r in KT}
        traps_of = {r: list(room_data[r][1]) for r in KT}
        pits_of = {r: list(room_data[r][2]) for r in KT}
        room_of = {}
        for r in KT:
            for e in doors_of[r] + traps_of[r] + pits_of[r]:
                room_of[e] = r

        def split_lanes():
            """One random partition of all KT rooms into three lanes, or None."""
            lanes = [{ENTRIES[i]} for i in range(3)]
            fperm = FINALS[:]
            random.shuffle(fperm)
            for i in range(3):
                lanes[i].add(fperm[i])
            placed = set(ENTRIES) | set(FINALS)
            glued = {r for a, b, _ in GATED for r in (a, b)}
            units = [[a, b] for a, b, _ in GATED]
            units += [[r] for r in KT if r not in placed and r not in glued]

            random.shuffle(units)
            for u in units:
                random.choice(lanes).update(u)
            for lane in lanes:
                if sum(len(traps_of[r]) for r in lane) != sum(len(pits_of[r]) for r in lane):
                    return None
                if sum(len(doors_of[r]) for r in lane) % 2 != 0:
                    return None
                if sum(1 for r in lane if r in BOSSES) > 2:
                    return None
            return lanes

        def connect_lane(lane):
            """Walk out a connected layout for one lane. Returns (door_pairs,
            trap_pits) with platform ids stripped, or None if the walk fails."""
            net = Network(list(lane))
            net.should_stop = None
            # Unlock both platforms so the walk can rely on the gated crossings
            # for connectivity; key timing is checked separately in verify().
            net.apply_key('KT1')
            net.apply_key('KT2')
            net.ForceConnections(self.KT_FORCED)  # inits .protected; forces any in-lane platform
            net.attach_dead_ends()
            nodes = list(net.net.nodes)
            if not nodes:
                return None
            # Start from the room with the most remaining exits (a poor seed can
            # make the walk dead-end immediately).
            net.active = max(nodes, key=lambda n: len(net.rooms.get_room(n).doors)
                             + len(net.rooms.get_room(n).traps))
            try:
                result = net.connect_network()
            except Exception:
                return None
            dp = [m for m in result.map[0]
                  if m[0] not in PLATFORM_IDS and m[1] not in PLATFORM_IDS]
            tp = [m for m in result.map[1]
                  if m[0] not in PLATFORM_IDS and m[1] not in PLATFORM_IDS]
            return dp, tp

        def verify(door_pairs, trap_pits, lane_of):
            """Reject any layout a player could softlock.

            The three lanes are physically disjoint; their only coupling is the
            **global, monotonic keychain** (pressing the switch in `KTb8`/`KTc10`
            sets `KT1`/`KT2`, which opens a gated crossing that may be in a
            different lane). The player drives all three parties asynchronously
            and switches between them freely, so the honest model is a joint
            state-space over `(roomA, roomB, roomC, keychain)`:

              - a move steps ONE party along a door (two-way), a trap (one-way),
                or a gated crossing (one-way, only if its key is already held);
              - a party standing on a switch room may add that key to the shared
                keychain (permanent — the keychain never shrinks).

            A layout is accepted iff (1) every room is occupied by its lane's
            party in some reachable state (no orphans — all bosses/switches
            reachable) AND (2) from EVERY reachable state the players can still
            herd all three parties onto their lane endings (no situation is a
            dead end). This catches the case the old "assume both keys held"
            check missed: a party riding a one-way into a pocket whose only exit
            is a gated crossing whose key it can no longer collect.
            """
            KEY_BIT = {'KT1': 1, 'KT2': 2}
            # room -> list of (dest_room, required_key_bit_or_None)
            adj = {r: [] for r in KT}
            for d1, d2 in door_pairs:
                adj[room_of[d1]].append((room_of[d2], None))
                adj[room_of[d2]].append((room_of[d1], None))
            for t, p in trap_pits:
                adj[room_of[t]].append((room_of[p], None))
            for a, b, k in GATED:
                adj[a].append((b, KEY_BIT[k]))
            # room -> keychain bit it grants while a party stands on it
            grant = {room: KEY_BIT[key] for room, key in KEY_ROOM.items()}

            # Lane i is seeded with ENTRIES[i]; its ending is the in-lane final.
            entry = tuple(ENTRIES)
            ending = [None, None, None]
            for f in FINALS:
                ending[lane_of[f]] = f
            ending = tuple(ending)

            def successors(state):
                a, b, c, K = state
                pos = (a, b, c)
                for j in range(3):
                    r = pos[j]
                    for dest, need in adj[r]:
                        if need is None or (K & need):
                            nxt = list(pos)
                            nxt[j] = dest
                            yield (nxt[0], nxt[1], nxt[2], K)
                    g = grant.get(r)
                    if g and not (K & g):
                        yield (a, b, c, K | g)

            # (1) Forward reachable joint states from the three entries.
            start = (entry[0], entry[1], entry[2], 0)
            forward = {start}
            stack = [start]
            while stack:
                s = stack.pop()
                for ns in successors(s):
                    if ns not in forward:
                        forward.add(ns)
                        stack.append(ns)

            # No orphans: every room must be standable by its party somewhere.
            visited = set()
            for a, b, c, _K in forward:
                visited.add(a); visited.add(b); visited.add(c)
            if visited != set(KT):
                return False

            # (2) No softlock: every forward state must be able to reach a goal
            # state (all three parties on their endings). Reverse-BFS the goal
            # set over the forward edges and require it covers `forward`.
            rev = {}
            for s in forward:
                for ns in successors(s):
                    if ns in forward:
                        rev.setdefault(ns, []).append(s)
            goal = [s for s in forward
                    if (s[0], s[1], s[2]) == ending]
            if not goal:
                return False
            can_finish = set(goal)
            stack = list(goal)
            while stack:
                s = stack.pop()
                for pre in rev.get(s, ()):
                    if pre not in can_finish:
                        can_finish.add(pre)
                        stack.append(pre)
            return forward <= can_finish


        # The network walk is internally chatty; silence vprint during the
        # search (it would emit hundreds of pages and is far slower) and
        # restore it before logging the chosen layout.
        saved_verbose = (_verbose_mod._to_stdout, _verbose_mod._to_file)
        _verbose_mod._to_stdout = False
        _verbose_mod._to_file = False
        result = None
        lanes = None
        try:
            for _ in range(self.KT_MAX_SPLITS):
                split = None
                guard = 0
                while split is None and guard < 5000:
                    split = split_lanes()
                    guard += 1
                if split is None:
                    continue
                lane_of = {r: i for i, lane in enumerate(split) for r in lane}
                door_pairs, trap_pits = [], []
                ok = True
                for lane in split:
                    res = connect_lane(lane)
                    if res is None:
                        ok = False
                        break
                    door_pairs += res[0]
                    trap_pits += res[1]
                if ok and verify(door_pairs, trap_pits, lane_of):
                    result = [door_pairs, trap_pits]
                    lanes = split
                    break
        finally:
            _verbose_mod._to_stdout, _verbose_mod._to_file = saved_verbose

        if result is None:
            vprint("WARNING: Kefka's Tower randomization failed after "
                   f'{self.KT_MAX_SPLITS} partitions; using vanilla KT layout')
            return None

        if self.verbose:
            door_pairs, trap_pits = result
            vprint("Kefka's Tower randomized into three lanes:")
            for i, lane in enumerate(lanes):
                bosses = [r for r in lane if r in BOSSES]
                vprint(f'\tlane {i} ({len(lane)} rooms, bosses {bosses}): '
                       f'{sorted(lane)}')
            for d1, d2 in door_pairs:
                vprint(f'\tdoor: {d1} <-> {d2}  '
                       f'(room {room_of[d1]} <-> {room_of[d2]})')
            for t, p in trap_pits:
                vprint(f'\ttrap: {t} -> {p}  '
                       f'(room {room_of[t]} -> {room_of[p]})')
        return result

    def pre_plan_character_acquisition(self):
        """Pre-plan which characters will be obtained to ensure sufficient areas.

        This method:
        1. Identifies starting party (already in self.PARTY)
        2. Randomly chooses additional characters up to the requested number
        3. Checks that there are enough reward slots for required espers
        4. Adds more characters if needed to get enough esper slots
        5. Returns: (planned_characters, reserve_characters, dead_checks_allowed)
        """
        # Characters that can be obtained (not in starting party)
        obtainable = [c for c in ALL_CHARACTERS if c not in self.PARTY]
        random.shuffle(obtainable)

        # How many more characters do we need beyond starting party?
        characters_needed = max(0, self.Requested[0] - len(self.PARTY))

        # Pick random characters to obtain
        planned_characters = obtainable[:characters_needed]
        remaining_characters = obtainable[characters_needed:]

        # Calculate areas that will be used
        planned_areas = set()
        for char in self.PARTY:
            planned_areas.update(CHARACTER_AREAS.get(char, []))
        for char in planned_characters:
            planned_areas.update(CHARACTER_AREAS.get(char, []))
        # Always include 'ALL' areas
        planned_areas.update(CHARACTER_AREAS.get('ALL', []))

        # Count reward slots in planned areas
        total_character_slots = 0
        total_esper_slots = 0
        total_checks = 0

        for room_id, rewards in ROOM_REWARD.items():
            # Check if this room is in any planned area
            room_in_planned = False
            for area_name in planned_areas:
                if area_name in RUIN_ROOM_SETS and room_id in RUIN_ROOM_SETS[area_name]:
                    room_in_planned = True
                    break

            if room_in_planned:
                for reward_name, reward_data in rewards.items():
                    total_checks += 1
                    if reward_data.possible_types & RewardType.CHARACTER:
                        total_character_slots += 1
                    if reward_data.possible_types & RewardType.ESPER:
                        total_esper_slots += 1

        if self.verbose:
            vprint(f'Pre-plan: Planned areas have {total_checks} checks, '
                  f'{total_character_slots} character slots, {total_esper_slots} esper slots')

        # Check if we have enough esper slots after accounting for character slots
        # We need espers + planned characters, since character slots can't be used for espers
        while total_esper_slots < self.Requested[1] + len(planned_characters) and len(remaining_characters) > 0:
            # Add another character to get more areas/esper slots
            new_char = remaining_characters.pop(0)
            planned_characters.append(new_char)
            new_areas = CHARACTER_AREAS.get(new_char, [])

            if self.verbose:
                vprint(f'Pre-plan: Adding {new_char} to get more esper slots (areas: {new_areas})')

            # Count new slots from this character's areas
            for area_name in new_areas:
                if area_name not in planned_areas and area_name in RUIN_ROOM_SETS:
                    planned_areas.add(area_name)
                    for room_id in RUIN_ROOM_SETS[area_name]:
                        if room_id in ROOM_REWARD:
                            for reward_name, reward_data in ROOM_REWARD[room_id].items():
                                total_checks += 1
                                if reward_data.possible_types & RewardType.CHARACTER:
                                    total_character_slots += 1
                                if reward_data.possible_types & RewardType.ESPER:
                                    total_esper_slots += 1

        # Calculate dead checks allowed
        # Dead checks = total checks - characters needed - espers needed
        dead_checks_allowed = total_checks - len(planned_characters) - self.Requested[1]

        # Reserve characters are those not planned to be obtained
        reserve_characters = remaining_characters

        return planned_characters, reserve_characters, max(0, dead_checks_allowed)

    def get_reserve_area_rooms(self):
        """Get rooms from reserve character areas for use when branches get stuck.

        Returns a list of (area_name, room_list) tuples, prioritizing areas with
        more rooms and hub potential (multiple doors/traps).

        Always includes EXTRA areas (like ImperialCastle) so they can appear in seeds.
        """
        reserve_areas = []

        # Helper to calculate hub potential for an area
        def calc_hub_potential(rooms):
            hub_potential = 0
            for room_id in rooms:
                if room_id in room_data:
                    data = room_data[room_id]
                    doors = len(data[0]) if len(data) > 0 else 0
                    traps = len(data[1]) if len(data) > 1 else 0
                    if doors + traps >= 2:
                        hub_potential += 1
            return hub_potential

        # Add areas from reserve characters
        for char in self.reserve_characters:
            for area_name in CHARACTER_AREAS.get(char, []):
                if area_name not in self.AreasUsed and area_name in RUIN_ROOM_SETS:
                    rooms = list(RUIN_ROOM_SETS[area_name])
                    hub_potential = calc_hub_potential(rooms)
                    reserve_areas.append((area_name, rooms, hub_potential, len(rooms)))

        # Always include EXTRA areas (like ImperialCastle) if not already used
        for area_name in CHARACTER_AREAS.get('EXTRA', []):
            if area_name not in self.AreasUsed and area_name in RUIN_ROOM_SETS:
                # Check if already added from reserve characters
                if not any(a[0] == area_name for a in reserve_areas):
                    rooms = list(RUIN_ROOM_SETS[area_name])
                    hub_potential = calc_hub_potential(rooms)
                    reserve_areas.append((area_name, rooms, hub_potential, len(rooms)))

        # Sort by hub potential (descending), then by room count (descending)
        reserve_areas.sort(key=lambda x: (x[2], x[3]), reverse=True)

        return [(a[0], a[1]) for a in reserve_areas]

    def distribute_areas(self, areas, method='random'):
        """Distribute areas among branches.

        Args:
            areas: List of area names to distribute
            method: Distribution method ('random', 'distribute', 'shortest', 'least_checks')
        """
        # Distribute new areas among the branches
        branch_areas = [ set(), set(), set()]

        def _check_forced_same_branch(a):
            # Helper function to assess if an area has a forced destination
            if a in forced_same_branch.keys():
                partners = forced_same_branch[a]
                for partner in partners:
                    if partner in self.AreasUsed.keys():
                        branch_index = self.AreasUsed[partner]
                        if self.verbose:
                            vprint('Forced same branch:', a, partner, branch_index)
                        return branch_index
                return False
            return False

        # Make sure we don't double-add areas
        areas = [a for a in areas if a not in self.AreasUsed.keys()]

        # PRIORITY DISTRIBUTION: If any branches are stuck, try to send them areas
        # that have the right connector types to unstick them
        if hasattr(self, 'stuck_branches') and len(self.stuck_branches) > 0:
            # Analyze each area's connector potential
            area_analysis = {}
            for area in areas:
                area_analysis[area] = _analyze_area_connectors(area)

            # For each stuck branch, try to find and assign a helpful area
            remaining_areas = list(areas)
            for branch_id, stuck_reason in list(self.stuck_branches.items()):
                if stuck_reason == StuckReason.NEED_PIDO:
                    # Find an area with PIDO rooms
                    for area in remaining_areas:
                        forced_idx = _check_forced_same_branch(area)
                        if forced_idx is not False and forced_idx != branch_id:
                            continue  # Can't assign to this branch
                        if area_analysis[area]['has_pido']:
                            if self.verbose:
                                vprint(f'\tPriority: Assigning {area} to stuck branch {branch_id} (has PIDO rooms)')
                            branch_areas[branch_id].add(area)
                            self.AreasUsed[area] = branch_id
                            remaining_areas.remove(area)
                            break
                elif stuck_reason == StuckReason.NO_HUB:
                    # Find an area with hub rooms
                    for area in remaining_areas:
                        forced_idx = _check_forced_same_branch(area)
                        if forced_idx is not False and forced_idx != branch_id:
                            continue  # Can't assign to this branch
                        if area_analysis[area]['has_hub']:
                            if self.verbose:
                                vprint(f'\tPriority: Assigning {area} to stuck branch {branch_id} (has hub rooms)')
                            branch_areas[branch_id].add(area)
                            self.AreasUsed[area] = branch_id
                            remaining_areas.remove(area)
                            break

            # Update areas list to only include remaining unassigned areas
            areas = remaining_areas

        # Town spreading: route every STANDALONE_TOWNS member queued for
        # distribution to whichever branch currently has the fewest mapped
        # TOWNS (random tiebreak), recomputing the count after each placement
        # so they actually spread when multiple come in together. Anything
        # caught by forced_same_branch falls through to the normal dispatch.
        balanced_towns = [a for a in areas if a in STANDALONE_TOWNS]
        if balanced_towns:
            town_set = set(AREA_TYPES['TOWNS'])
            random.shuffle(balanced_towns)
            placed = []
            for town in balanced_towns:
                if _check_forced_same_branch(town) is not False:
                    continue
                town_counts = [
                    sum(1 for a, bid in self.AreasUsed.items()
                        if bid == i and a in town_set)
                    for i in range(3)
                ]
                min_count = min(town_counts)
                candidates = [i for i, c in enumerate(town_counts) if c == min_count]
                this_index = random.choice(candidates)
                if self.verbose:
                    vprint(f'\tTown spread: {town} -> branch {this_index} '
                           f'(town counts: {town_counts})')
                branch_areas[this_index].add(town)
                self.AreasUsed[town] = this_index
                placed.append(town)
            if placed:
                areas = [a for a in areas if a not in placed]

        if method == 'random':
            for area in areas:
                this_index = _check_forced_same_branch(area)
                if this_index is False:
                    this_index = random.randint(0, 2)
                branch_areas[this_index].add(area)
                self.AreasUsed[area] = this_index
        elif method == 'distribute':
            seed = random.randint(0, 2)
            use_index = [(i + seed) % 3 for i in range(len(areas))]
            random.shuffle(use_index)
            for area in areas:
                this_index = _check_forced_same_branch(area)
                if this_index is False:
                    this_index = use_index.pop()
                branch_areas[this_index].add(area)
                self.AreasUsed[area] = this_index
        elif method == 'shortest':
            num_rooms = [len(b.original_room_ids) for b in self.branches]
            random.shuffle(areas)
            for area in areas:
                this_index = _check_forced_same_branch(area)
                if this_index is False:
                    if self.verbose:
                        vprint('\t\t# rooms on each branch: ', num_rooms)
                    this_index = num_rooms.index(min(num_rooms))
                branch_areas[this_index].add(area)
                self.AreasUsed[area] = this_index
                area_room_num = len(RUIN_ROOM_SETS[area])
                num_rooms[this_index] += area_room_num
        elif method == 'least_checks':
            for area in areas:
                this_index = _check_forced_same_branch(area)
                if this_index is False:
                    shortest_index = [len(b) for b in self.branch_checks]
                    this_index = shortest_index.index(min(shortest_index))
                branch_areas[this_index].add(area)
                self.AreasUsed[area] = this_index


        if self.verbose:
            vprint('Distributed areas:')
            for i, b in enumerate(branch_areas):
                vprint('\t', i, ': ', b)

        # Expand to list of rooms to add to each branch
        branch_rooms = [set(), set(), set()]
        for i, areas in enumerate(branch_areas):
            for area in areas:
                branch_rooms[i].update(RUIN_ROOM_SETS[area])
                # Track accessible shops from areas with shops
                if area in AREA_SHOPS:
                    for shop_id in AREA_SHOPS[area]:
                        if shop_id not in self.accessible_shops:
                            self.accessible_shops.append(shop_id)

        # Collect which checks are available, including how many can be characters and how many espers
        for room in ROOM_REWARD:
            which_branch = next((i for i, branch in enumerate(branch_rooms) if room in branch), -1)
            if which_branch >= 0:
                for reward_id in ROOM_REWARD[room].keys():
                    process_me = self._is_reward_accessible(reward_id)
                    if process_me:
                        self.branch_checks[which_branch].append(reward_id)
                        reward = ROOM_REWARD[room][reward_id]
                        # print(reward_id, i, this_type.possible_types)
                        if reward.possible_types & RewardType.CHARACTER:
                            self.RewardsAvailable[0] += 1
                        if reward.possible_types & RewardType.ESPER:
                            self.RewardsAvailable[1] += 1

        if self.verbose:
            vprint('Checks available:')
            for i, b in enumerate(self.branch_checks):
                vprint('\t', i, ': ', b)

        # Add rooms to the branches (skip rooms that already exist in ANY branch)
        # Use all_rooms_added to include rooms that may have been merged into compound rooms
        all_existing_rooms = set()
        for branch in self.branches:
            all_existing_rooms.update(branch.all_rooms_added)

        for i, branch in enumerate(self.branches):
            for room in branch_rooms[i]:
                if room not in all_existing_rooms:
                    branch.add_room(room)
                    all_existing_rooms.add(room)

        # If any stuck branch received new areas that could help unstick it, give it another chance
        # This is critical for cases where a branch got stuck early but later received
        # new areas when a character was obtained
        if hasattr(self, 'stuck_branches'):
            for i, branch in enumerate(self.branches):
                if i in self.stuck_branches and len(branch_rooms[i]) > 0:
                    stuck_reason = self.stuck_branches[i]
                    should_unstick = False

                    # Check if new areas can help based on stuck reason
                    if stuck_reason == StuckReason.NEED_PIDO:
                        # Branch needs a PIDO room - check if any new room has pits AND doors
                        for room_id in branch_rooms[i]:
                            room = branch.rooms.get_room(room_id)
                            if room and _room_has_pido_potential(room):
                                if self.verbose:
                                    vprint(f'\tFound PIDO room {room_id} for stuck branch {i}')
                                should_unstick = True
                                break
                    elif stuck_reason == StuckReason.NO_HUB:
                        # Branch needs a hub room - check if any new room is a hub
                        for room_id in branch_rooms[i]:
                            room = branch.rooms.get_room(room_id)
                            if room and _room_has_hub_potential(room):
                                if self.verbose:
                                    vprint(f'\tFound hub room {room_id} for stuck branch {i}')
                                should_unstick = True
                                break
                    else:
                        # For other reasons, check if branch now has a hub (general unsticking)
                        if branch.has_a_hub():
                            should_unstick = True

                    if should_unstick:
                        if self.verbose:
                            vprint(f'\tUnsticking branch {i} - received helpful areas (was stuck: {stuck_reason})')
                        self.stuck_branches.pop(i, None)

    def apply_key(self, key):
        # Apply a key in all branches
        self.keychain.add(key)
        for branch in self.branches:
            branch.apply_key(key)

        # If this is a character key that unlocks rewards, add those rewards to branch_checks
        if key in CHARACTER_LOCKED_REWARDS:
            unlocked_rewards = CHARACTER_LOCKED_REWARDS[key]
            for reward_name in unlocked_rewards:
                # Find which room has this reward
                for room_id, rewards in ROOM_REWARD.items():
                    if reward_name in rewards:
                        # Find which branch has this room
                        for branch_id, branch in enumerate(self.branches):
                            if room_id in branch.net.nodes or room_id in branch.original_room_ids:
                                if reward_name not in self.branch_checks[branch_id] and self._is_reward_accessible(reward_name):
                                    self.branch_checks[branch_id].append(reward_name)
                                    # Also update RewardsAvailable
                                    reward_slot = ROOM_REWARD[room_id][reward_name]
                                    if reward_slot.possible_types & RewardType.CHARACTER:
                                        self.RewardsAvailable[0] += 1
                                    if reward_slot.possible_types & RewardType.ESPER:
                                        self.RewardsAvailable[1] += 1
                                    if self.verbose:
                                        vprint(f'\tUnlocked reward {reward_name} added to branch {branch_id} checks')
                                break

        # If this key is a character that owns areas, check for area-locked rewards now accessible
        if key in ALL_CHARACTERS:
            for room_id, rewards in ROOM_REWARD.items():
                for reward_name in rewards.keys():
                    if reward_name in REWARD_OWNERS and key in REWARD_OWNERS[reward_name]:
                        if self._is_reward_accessible(reward_name):
                            for branch_id, branch in enumerate(self.branches):
                                if room_id in branch.all_rooms_added:
                                    if reward_name not in self.branch_checks[branch_id]:
                                        self.branch_checks[branch_id].append(reward_name)
                                        reward_slot = ROOM_REWARD[room_id][reward_name]
                                        if reward_slot.possible_types & RewardType.CHARACTER:
                                            self.RewardsAvailable[0] += 1
                                        if reward_slot.possible_types & RewardType.ESPER:
                                            self.RewardsAvailable[1] += 1
                                        if self.verbose:
                                            vprint(f'\tArea-unlocked reward {reward_name} added to branch {branch_id} checks')
                                    break

    def _is_reward_accessible(self, reward_name):
        """Check if a reward is currently accessible (not locked).

        A reward is inaccessible if:
        1. It has an in-game character lock and the locking character is not in keychain, OR
        2. It is in a character-owned area and none of the area owners are in keychain.
        """
        if reward_name in REWARDS_LOCKED_BY_CHARACTER:
            if REWARDS_LOCKED_BY_CHARACTER[reward_name] not in self.keychain:
                return False
        if reward_name in REWARD_OWNERS:
            if not any(c in self.keychain for c in REWARD_OWNERS[reward_name]):
                return False
        return True

    def get_non_veldt_gated_shops(self, characters):
        """Identify shops that are NOT gated behind the Veldt reward.

        This is necessary to ensure dried meat is available BEFORE Gau is obtained,
        since dried meat is required to recruit Gau on the Veldt.

        Uses characters.character_path to determine which characters depend on
        the Veldt character. Shops in areas unlocked by those characters are
        considered Veldt-gated and excluded from dried meat assignment.

        Args:
            characters: Characters object with character_path populated

        Returns:
            List of shop IDs that are NOT Veldt-gated
        """
        # Quick check: if Gau is not in the game at all, no need for special Veldt handling
        # Note: must check both PARTY (starting characters) and planned_characters (to be obtained)
        all_game_characters = set(self.PARTY) | set(self.planned_characters)
        if 'GAU' not in all_game_characters:
            if self.verbose:
                vprint('Gau not in game characters, all accessible shops valid for dried meat')
            return self.accessible_shops[:]

        # Find which character was assigned to the Veldt reward
        veldt_reward_room = 'wor-veldt'
        veldt_char_id = None

        if veldt_reward_room in ROOM_REWARD:
            veldt_rewards = ROOM_REWARD[veldt_reward_room]
            for reward_name, reward_slot in veldt_rewards.items():
                if reward_slot.type == RewardType.CHARACTER:
                    veldt_char_id = reward_slot.id
                    veldt_char_name = characters.DEFAULT_NAME[veldt_char_id]
                    if self.verbose:
                        vprint(f'Veldt character: {veldt_char_name} (ID: {veldt_char_id})')
                    break

        # If no character at Veldt (or Veldt not in map), all accessible shops are valid
        if veldt_char_id is None:
            if self.verbose:
                vprint('No character at Veldt, all accessible shops valid for dried meat')
            return self.accessible_shops[:]

        # Find all characters that depend on the Veldt character
        veldt_gated_chars = set()
        for char_id in range(len(characters.DEFAULT_NAME)):
            # Check if veldt_char_id is in this character's dependency path
            if veldt_char_id in characters.character_paths[char_id]:
                veldt_gated_chars.add(char_id)
                if self.verbose:
                    vprint(f'  {characters.DEFAULT_NAME[char_id]} is gated by Veldt character')

        # Collect areas unlocked by Veldt-gated characters
        veldt_gated_areas = set()
        for char_id in veldt_gated_chars:
            char_name = characters.DEFAULT_NAME[char_id]
            if char_name in CHARACTER_AREAS:
                veldt_gated_areas.update(CHARACTER_AREAS[char_name])

        if self.verbose and veldt_gated_areas:
            vprint(f'Veldt-gated areas: {veldt_gated_areas}')

        # Collect shop IDs in Veldt-gated areas
        veldt_gated_shops = set()
        for area in veldt_gated_areas:
            if area in AREA_SHOPS:
                veldt_gated_shops.update(AREA_SHOPS[area])

        # Return non-Veldt-gated shops
        non_veldt_shops = [shop_id for shop_id in self.accessible_shops
                          if shop_id not in veldt_gated_shops]

        if self.verbose:
            vprint(f'Accessible shops: {len(self.accessible_shops)}')
            vprint(f'Veldt-gated shops: {list(veldt_gated_shops)}')
            vprint(f'Non-Veldt-gated shops: {len(non_veldt_shops)} - {non_veldt_shops}')

        # Warn if no non-Veldt-gated shops exist when Gau is in the game
        if not non_veldt_shops and 'GAU' in all_game_characters:
            print('WARNING: No non-Veldt-gated shops available for dried meat!')
            print('  This may make Gau unrecrutable. Consider adjusting map generation.')
            print(f'  Falling back to all {len(self.accessible_shops)} accessible shops.')
            return self.accessible_shops[:]

        return non_veldt_shops

    def _collect_mapping_diagnostics(self, reason, stuck_branches=None, branch_is_viable=None, branch_id=None):
        """Collect detailed diagnostic information when mapping fails.

        Returns a formatted string with all relevant state for troubleshooting.
        """
        lines = [
            f"\n{'='*60}",
            f"RUINATION MAPPING FAILURE: {reason}",
            f"{'='*60}",
            "",
            "=== Rewards State ===",
            f"  Requested: {self.Requested[0]} characters, {self.Requested[1]} espers",
            f"  Obtained:  {self.RewardsObtained[0]} characters, {self.RewardsObtained[1]} espers",
            f"  Available: {self.RewardsAvailable[0]} character slots, {self.RewardsAvailable[1]} esper slots",
            f"  Planned characters: {self.planned_characters}",
            f"  Reserve characters: {self.reserve_characters}",
            f"  Dead checks allowed: {self.dead_checks_allowed}",
            "",
            "=== Branch State ===",
        ]

        if stuck_branches is not None:
            lines.append(f"  Stuck branches: {dict(stuck_branches) if isinstance(stuck_branches, dict) else stuck_branches}")
        if branch_is_viable is not None:
            lines.append(f"  Branch viability: {branch_is_viable}")
        if branch_id is not None:
            lines.append(f"  Current branch_id: {branch_id}")

        lines.append("")

        for i, branch in enumerate(self.branches):
            lines.append(f"  Branch {i}:")
            lines.append(f"    Active room: {branch.active}")
            lines.append(f"    Terminus: {branch.terminus}")
            lines.append(f"    Has hub: {branch.has_a_hub()}")
            lines.append(f"    Last stuck reason: {branch.last_stuck_reason}")
            lines.append(f"    Check rooms: {branch.check_rooms}")
            lines.append(f"    Dead ends: {branch.dead_ends}")
            lines.append(f"    Nodes in network: {len(branch.net.nodes)}")
            lines.append(f"    Rooms added (incl. merged): {len(branch.all_rooms_added)}")
            lines.append(f"    Branch checks: {self.branch_checks[i]}")
            lines.append(f"    Keychain: {branch.keychain}")

            # Count available elements
            total_doors = sum(len(branch.rooms.get_room(n).doors) for n in branch.net.nodes if branch.rooms.get_room(n))
            total_traps = sum(len(branch.rooms.get_room(n).traps) for n in branch.net.nodes if branch.rooms.get_room(n))
            total_pits = sum(len(branch.rooms.get_room(n).pits) for n in branch.net.nodes if branch.rooms.get_room(n))
            lines.append(f"    Unconnected elements: {total_doors} doors, {total_traps} traps, {total_pits} pits")
            lines.append("")

        # Add detailed topology visualization for each branch
        lines.append("")
        lines.append("=== Branch Topology Visualizations ===")
        for i, branch in enumerate(self.branches):
            lines.append(f"\n--- Branch {i} Topology ---")
            try:
                lines.append(branch.visualize_branch_topology())
            except Exception as e:
                lines.append(f"  (Error generating visualization: {e})")
            lines.append("")

        lines.append("=== Areas State ===")
        lines.append(f"  Areas used: {dict(self.AreasUsed)}")
        lines.append(f"  Global keychain: {self.keychain}")
        lines.append(f"  Locked rewards waiting: {dict(self.LockedRewards)}")
        lines.append("")

        # Show available reserve areas
        reserve_areas = self.get_reserve_area_rooms()
        lines.append(f"  Reserve areas available: {len(reserve_areas)}")
        for area_name, rooms in reserve_areas[:5]:  # Show first 5
            lines.append(f"    {area_name}: {len(rooms)} rooms")

        lines.append("")
        lines.append("=== Troubleshooting Hints ===")
        if stuck_branches and len(stuck_branches) == 3:
            lines.append("  - All 3 branches stuck: likely insufficient hub rooms in initial area distribution")
        if self.RewardsAvailable[0] == 0 and self.RewardsObtained[0] < len(self.planned_characters):
            lines.append("  - No character slots remaining but characters still needed")
        if not reserve_areas:
            lines.append("  - No reserve areas: all character areas already used")

        lines.append(f"{'='*60}")

        return "\n".join(lines)

    def generate_map_with_characters(self, characters, espers, items):
        """Generate the ruination mode dungeon map and assign character/esper/item rewards.

        Note: reward_slots (from events.py) are updated automatically through shared object references.
        ROOM_REWARD dictionary is populated with Reward objects from event.rewards in events.py (lines 228-237).
        When process_rewards() updates these Reward objects (slot.id, slot.type), the changes propagate
        to reward_slots because they reference the same objects.
        """
        # Build out branches, always starting with the least connected
        self.RewardsObtained = [0, 0]
        # Track rewards found on each branch, used to weight branch selection
        # toward less-extended branches (avoids one stub branch when others get long).
        self.branch_rewards_found = [0, 0, 0]
        self.LockedRewards = dict()
        # Track stuck branches and WHY they're stuck (branch_id -> StuckReason)
        # This allows distribute_areas to prioritize sending areas with the right connectors
        self.stuck_branches = dict()
        max_retries_per_branch = 3  # Retry before declaring stuck

        # Calculate which characters to exclude from selection (non-planned characters)
        planned_char_ids = [characters.DEFAULT_NAME.index(name) for name in self.planned_characters]
        non_planned_chars = [char_id for char_id in characters.available_characters
                            if char_id not in planned_char_ids]

        # Edit forced connections for ruination
        #for fc in ruination_extra_force:
        for fc in ruination_dont_force:
            if fc in forced_connections.keys():
                forced_connections.pop(fc)

        if self.verbose:
            vprint('Generating map with characters...')

        ### This approach fails if a branch has only dead ends on it.  For example: a branch could initially get just
        # 'Gau Father House', 'Floating Continent', both of which are dead ends.
        # In such a case, may need to throw in an optional hub room to get started... or just start on a different branch & assume it'll get sorted.

        while (self.RewardsObtained[0] < len(self.planned_characters) or self.RewardsObtained[1] < self.Requested[1]):
            # Pick a branch with an active reward, excluding stuck branches
            #branch_in_hub = ['ruin_hub_' in str(b.active) for b in self.branches]
            #if branch_in_hub.count(False) > 0:
            #    # One of the branches is not in the hub. Keep working on that one.
            #    branch_id = branch_in_hub.index(False)
            # Pick a branch that is not all dead ends.  Requires at least one true hub room
            branch_is_viable = [b.has_a_hub() for b in self.branches]
            if self.verbose:
                vprint('Branch viability:', branch_is_viable, 'Stuck:', self.stuck_branches)
            viable_branches = [b for b in range(3) if len(self.branch_checks[b]) > 0 and branch_is_viable[b] and b not in self.stuck_branches]
            if len(viable_branches) > 0:
                # Weight toward branches with fewer rewards found, so one stub branch
                # doesn't get left behind while the others grow long. Weight is always
                # >= 1, so any viable branch can still be chosen.
                total_rewards_found = sum(self.branch_rewards_found)
                branch_weights = [1 + total_rewards_found - self.branch_rewards_found[b] for b in viable_branches]
                if self.verbose:
                    vprint('Branch selection weights:', dict(zip(viable_branches, branch_weights)))
                branch_id = random.choices(viable_branches, weights=branch_weights, k=1)[0]
                branch = self.branches[branch_id]
            else:
                # All branches with checks are stuck or non-viable - try to unstick one
                checkable_branches = [b for b in range(3) if len(self.branch_checks[b]) > 0]
                if len(checkable_branches) == 0:
                    # Collect diagnostic information
                    diag = self._collect_mapping_diagnostics(
                        "No branches have remaining checks",
                        stuck_branches=self.stuck_branches,
                        branch_is_viable=branch_is_viable
                    )
                    raise RuinationMappingError(diag)

                # Try adding rooms from reserve character areas to 'loosen up' the branch
                branch_id = checkable_branches[0]  # Pick first branch with checks
                branch = self.branches[branch_id]

                # Get reserve areas sorted by hub potential
                reserve_areas = self.get_reserve_area_rooms()

                if len(reserve_areas) > 0:
                    # Use the best reserve area (most hub potential)
                    new_area, new_rooms = reserve_areas[0]
                    if self.verbose:
                        vprint(f'Adding reserve area {new_area} ({len(new_rooms)} rooms) to unstick branch {branch_id}')

                    # Mark area as used
                    self.AreasUsed[new_area] = branch_id

                    # Remove from reserve characters' areas
                    for char in list(self.reserve_characters):
                        if new_area in CHARACTER_AREAS.get(char, []):
                            # Remove this area from consideration
                            break

                    # Add rooms to the branch (skip any that already exist in any branch)
                    # Use all_rooms_added to include rooms that may have been merged into compound rooms
                    existing_rooms = set()
                    for b in self.branches:
                        existing_rooms.update(b.all_rooms_added)
                    for room in new_rooms:
                        if room in existing_rooms:
                            if self.verbose:
                                vprint(f'\tSkipping room {room} - already exists')
                            continue
                        branch.add_room(room)

                    # Check if this area has any reward rooms (only add accessible ones)
                    for room in new_rooms:
                        if room in ROOM_REWARD:
                            for reward_id in ROOM_REWARD[room].keys():
                                if reward_id not in self.branch_checks[branch_id]:
                                    if self._is_reward_accessible(reward_id):
                                        self.branch_checks[branch_id].append(reward_id)
                                        reward = ROOM_REWARD[room][reward_id]
                                        if reward.possible_types & RewardType.CHARACTER:
                                            self.RewardsAvailable[0] += 1
                                        if reward.possible_types & RewardType.ESPER:
                                            self.RewardsAvailable[1] += 1
                                        if self.verbose:
                                            vprint(f'\tAdded new check: {reward_id}')
                                    else:
                                        if self.verbose:
                                            vprint(f'\tReward {reward_id} is area-locked, skipping')

                    self.stuck_branches.pop(branch_id, None)  # Give it another chance

                    # CRITICAL: Reset the active room to the hub so we can try a different path
                    # Without this, the branch stays at the stuck position and immediately gets stuck again
                    hub_id = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)][0]
                    branch.active = hub_id
                    if self.verbose:
                        vprint(f'\tReset branch {branch_id} active room to hub: {hub_id}')

                elif len(CHARACTER_AREAS.get('EXTRA', [])) > 0:
                    # Fallback to EXTRA areas if no reserve areas left
                    new_area = CHARACTER_AREAS['EXTRA'].pop()
                    if self.verbose:
                        vprint('Adding extra area', new_area, 'to unstick branch', branch_id)
                    # Skip rooms that already exist (use all_rooms_added to catch merged rooms)
                    existing_rooms = set()
                    for b in self.branches:
                        existing_rooms.update(b.all_rooms_added)
                    for room in RUIN_ROOM_SETS[new_area]:
                        if room in existing_rooms:
                            if self.verbose:
                                vprint(f'\tSkipping room {room} - already exists')
                            continue
                        branch.add_room(room)
                    self.stuck_branches.pop(branch_id, None)

                    # CRITICAL: Reset the active room to the hub so we can try a different path
                    hub_id = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)][0]
                    branch.active = hub_id
                    if self.verbose:
                        vprint(f'\tReset branch {branch_id} active room to hub: {hub_id}')

                else:
                    # Collect diagnostic information
                    diag = self._collect_mapping_diagnostics(
                        "No reserve areas available to unstick branches",
                        stuck_branches=self.stuck_branches,
                        branch_is_viable=branch_is_viable,
                        branch_id=branch_id
                    )
                    raise RuinationMappingError(diag)

            # Update lists of dead ends
            for de in list(branch.dead_ends):  # Use list() to avoid modifying during iteration
                if de not in branch.net.nodes:
                    branch.dead_ends.remove(de)
                    if self.verbose:
                        vprint('\ttrimmed dead end ', de)

            if self.verbose:
                vprint('Working on branch', branch_id, '(', self.branch_checks[branch_id], ')')
                vprint('status: terminus', branch.terminus)
                vprint('status: check rooms', branch.check_rooms)
                vprint('status: dead ends', branch.dead_ends)

            # Force any forced connections before starting
            if self.verbose:
                vprint('Forcing connections...')
            branch.ForceConnections(forced_connections)

            # Forcing connections can update the name of the active branch
            if branch.active not in branch.net.nodes:
                new_active = [n_id for n_id in branch.net.nodes if branch.active in str(n_id)]
                if self.verbose:
                    vprint('updating active room id: ', branch.active, '-->', new_active[0])
                branch.active = new_active[0]

            # Apply any keys we have found in other branches
            for k in self.keychain.difference(branch.keychain):
                branch.apply_key(k)

            found_reward = False
            rewards = []
            accessible_rewards = []
            retries = 0
            while not found_reward:
                # Attach hubs & trapdoors until none are left (create all branches)

                # Choose an exit from the active room.
                this_exit, this_conn = branch.extend_branch_path()

                if this_exit is None:
                    retries += 1
                    if retries >= max_retries_per_branch:
                        if self.verbose:
                            vprint(f'Branch {branch_id} is stuck after {retries} retries. Reason: {branch.last_stuck_reason}')
                        self.stuck_branches[branch_id] = branch.last_stuck_reason
                        break
                    else:
                        if self.verbose:
                            vprint(f'Branch {branch_id} failed to extend, retry {retries}/{max_retries_per_branch}')
                        continue  # Try again with different random choices

                # Check if a reward was found
                rewards = branch.check_for_rewards(this_conn)

                if rewards is not None:
                    # Check to see if the reward is locked; if so, bank it
                    accessible_rewards = []
                    for r in rewards:
                        reward_name = r[0]
                        # Check in-game character lock
                        if reward_name in REWARDS_LOCKED_BY_CHARACTER:
                            locker = REWARDS_LOCKED_BY_CHARACTER[reward_name]
                            if locker not in self.keychain:
                                if locker not in self.LockedRewards:
                                    self.LockedRewards[locker] = []
                                self.LockedRewards[locker].append(
                                    (branch_id, [r]))
                                if self.verbose:
                                    vprint('\t\treward is locked by', locker, '(in-game). Saving for later.')
                                continue
                        # Check area-level character lock
                        if reward_name in REWARD_OWNERS:
                            area_owners = REWARD_OWNERS[reward_name]
                            if not any(c in self.keychain for c in area_owners):
                                # Bank under one of the unrecruited area owners
                                locker = sorted(area_owners - self.keychain)[0]
                                if locker not in self.LockedRewards:
                                    self.LockedRewards[locker] = []
                                self.LockedRewards[locker].append(
                                    (branch_id, [r]))
                                if self.verbose:
                                    vprint(f'\t\treward is area-locked by {area_owners}. Banking under {locker}.')
                                continue
                        # Not locked - reward is accessible
                        accessible_rewards.append(r)
                        found_reward = True

                # Identify the target room and whether it was unconnected before
                # this connection. Mapping a previously-unconnected room is what
                # ticks the warp/town cooldown counters for this branch.
                target_room_obj = branch.rooms.get_room_from_element(this_conn)
                target_room_id = target_room_obj.id if target_room_obj is not None else None
                target_was_connected = (
                    target_room_id is not None
                    and target_room_id in branch.net.nodes
                    and (branch.net.in_degree(target_room_id) + branch.net.out_degree(target_room_id)) > 0
                )

                # Actually connect them.  This also moves the active room to the new room.
                if self.verbose:
                    vprint('Making connection: ', this_exit, '-->', this_conn)
                branch.connect(this_exit, this_conn)

                # If a previously-unconnected room just got mapped onto the branch,
                # tick the cooldown counters (and reset if it's a warp/town room).
                if target_room_id is not None and not target_was_connected:
                    branch.update_cooldowns(target_room_id)
                    if self.verbose:
                        vprint(f'\tCooldowns: warp={branch.warp_cooldown}, town={branch.town_cooldown}'
                               f' (mapped {target_room_id})')

            ### Process reward & restart loop - only if we actually found a reward
            if found_reward and accessible_rewards:
                self.process_rewards(accessible_rewards, characters, espers, items, branch_id=branch_id, exclude_chars=non_planned_chars)
                self.branch_rewards_found[branch_id] += len(accessible_rewards)
            elif branch_id in self.stuck_branches:
                if self.verbose:
                    vprint(f'Skipping reward processing for stuck branch {branch_id}')

            # If not in the hub room, return to the hub room?

        # Validate that we actually obtained enough rewards before finalizing
        if self.RewardsObtained[0] < len(self.planned_characters):
            diag = self._collect_mapping_diagnostics(
                f"Exited main loop with insufficient characters: obtained {self.RewardsObtained[0]}, needed {len(self.planned_characters)}",
                stuck_branches=self.stuck_branches,
                branch_is_viable=[b.has_a_hub() for b in self.branches]
            )
            raise RuinationMappingError(diag)

        if self.RewardsObtained[1] < self.Requested[1]:
            diag = self._collect_mapping_diagnostics(
                f"Exited main loop with insufficient espers: obtained {self.RewardsObtained[1]}, needed {self.Requested[1]}",
                stuck_branches=self.stuck_branches,
                branch_is_viable=[b.has_a_hub() for b in self.branches]
            )
            raise RuinationMappingError(diag)

        # Add CHARACTER_AREAS['ALL'] areas (dead ends like Coliseum, Albrook)
        # with a chance per branch, in random order
        ADD_ALL_PERCENT = 1
        all_areas = list(CHARACTER_AREAS.get('ALL', []))
        random.shuffle(all_areas)
        branch_order = list(range(3))
        random.shuffle(branch_order)
        for i, area_name in enumerate(all_areas):
            if area_name in self.AreasUsed or area_name not in RUIN_ROOM_SETS:
                continue
            target_branch_id = branch_order[i % 3]
            if random.random() < ADD_ALL_PERCENT:
                branch = self.branches[target_branch_id]
                all_existing_rooms = set()
                for b in self.branches:
                    all_existing_rooms.update(b.all_rooms_added)
                for room in RUIN_ROOM_SETS[area_name]:
                    if room not in all_existing_rooms:
                        branch.add_room(room)
                self.AreasUsed[area_name] = target_branch_id
                if area_name in AREA_SHOPS:
                    for shop_id in AREA_SHOPS[area_name]:
                        if shop_id not in self.accessible_shops:
                            self.accessible_shops.append(shop_id)
                if self.verbose:
                    vprint(f'Added ALL area {area_name} to branch {target_branch_id}')

        # After satisfying conditions, fully connect map
        reserve_areas = self.get_reserve_area_rooms()
        for branch_id, branch in enumerate(self.branches):
            try:
                branch.finalize_map(reserve_areas)
            except Exception as e:
                diag = self._collect_mapping_diagnostics(
                    f"finalize_map failed on branch {branch_id}: {str(e)}",
                    branch_id=branch_id
                )
                raise RuinationMappingError(diag) from e

        # Post-finalization validation: ensure hub room has no unconnected exits
        # (It's OK if other rooms are unconnected - they just won't be accessible)
        for branch_id, branch in enumerate(self.branches):
            # Find the hub room for this branch
            hub_id = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = branch.rooms.get_room(hub_id)

            # Check hub's unconnected exits (doors and traps only - pits are entrances)
            unconnected_doors = [d for d in hub.doors if d not in branch.protected]
            unconnected_traps = [t for t in hub.traps if t not in branch.protected]

            if unconnected_doors or unconnected_traps:
                diag = self._collect_mapping_diagnostics(
                    f"Branch {branch_id} hub room has unconnected exits after finalize_map: "
                    f"{len(unconnected_doors)} doors, {len(unconnected_traps)} traps. "
                    f"doors={unconnected_doors}, traps={unconnected_traps}",
                    branch_id=branch_id
                )
                raise RuinationMappingError(diag)

            # Verify terminus was merged into hub (required for Kefka's Tower access)
            # By the end of finalize_map, all connected rooms should be merged into
            # the hub compound room via loop compression. If terminus is not in the
            # hub ID string, something went wrong with the finalization.
            terminus_id = branch.terminus
            terminus_merged = terminus_id in str(hub_id)

            if not terminus_merged:
                diag = self._collect_mapping_diagnostics(
                    f"Branch {branch_id} terminus '{terminus_id}' was not merged into hub '{hub_id}'. "
                    f"This indicates a bug in finalize_map - terminus should always be merged.",
                    branch_id=branch_id
                )
                raise RuinationMappingError(diag)

        # Wrap up: create & export a total map
        map = [[], []]
        for branch in self.branches:
            map[0].extend([m for m in branch.map[0]])
            map[1].extend([m for m in branch.map[1]])

        # Append shared doors to the map
        for m in map[0]:
            if m[0] in shared_exits.keys():
                for se in shared_exits[m[0]]:
                    # Send shared exits to the same destination
                    map[0].append([se, m[1]])
            if m[1] in shared_exits.keys():
                for se in shared_exits[m[1]]:
                    # Send shared exits to the same destination
                    map[0].append([m[0], se])

        # Add isolated maze internal connections (if -maze iso)
        if self.isolated_maze_map is not None:
            map[0].extend(self.isolated_maze_map[0])
            map[1].extend(self.isolated_maze_map[1])

        # Add randomized Kefka's Tower lane connections (if -rkt)
        if self.kt_lane_map is not None:
            map[0].extend(self.kt_lane_map[0])
            map[1].extend(self.kt_lane_map[1])

        # Add mapping for connections to KT
        traps_to_kt = [2077, 2078, 2079]
        pits_into_kt = [t + 1000 for t in traps_to_kt]
        random.shuffle(traps_to_kt)
        for i in range(3):
            map[1].append([traps_to_kt[i], pits_into_kt[i]])

        # Reject any layout with a character-gated softlock: a region that can
        # be entered with only the starting party but cannot be left without a
        # character recruited elsewhere on the map. Caught by the retry loop in
        # events.py, which regenerates the map.
        self._verify_no_character_gated_softlock(map)

        # Debug: print shortest route if requested (after all finalization)
        if self.args.debug_route_destination:
            self.debug_print_shortest_route(self.args.debug_route_destination)

        return map

    def _character_blocked_exits(self, branch):
        """Exit IDs in `branch` that need a non-starting-party character to traverse.

        Models the worst case where the player holds only the starting party:
        any exit whose in-game lock is keyed (directly, or transitively via a
        character-locked key such as 'lw1'/'zr1') on a character not yet
        recruited is unusable. The branch mapper unlocks these the moment the
        gating character is *planned* and then freely routes through them, but
        in play a region can be entered (via two-way doors or one-way pits)
        long before its gating character is obtained on some other branch. Such
        exits must therefore not be the sole escape from any region the player
        can otherwise reach (see _verify_no_character_gated_softlock).
        """
        party = set(self.PARTY)
        placed = [r for r in branch.all_rooms_added if r in room_data]

        # Party-only keychain: starting party plus every key obtainable without
        # recruiting anyone (unconditional grants and non-character-gated locks).
        keychain = set(party)
        for rid in placed:
            keychain.update(_room_data_start_keys(rid))
        changed = True
        while changed:
            changed = False
            for rid in placed:
                for ktuple, items in _room_data_locks(rid).items():
                    if set(ktuple) <= keychain:
                        for item in items:
                            if isinstance(item, str) and item not in keychain:
                                keychain.add(item)
                                changed = True

        # Any locked exit whose lock the party-only keychain cannot satisfy is
        # character-blocked (exits are ints; keys are strings).
        blocked = set()
        for rid in placed:
            for ktuple, items in _room_data_locks(rid).items():
                if set(ktuple) <= keychain:
                    continue
                for item in items:
                    if isinstance(item, int):
                        blocked.add(item)
        return blocked

    def _branch_exit_owner_map(self, branch):
        """Static map from exit id -> owning room, scoped to a branch's placed rooms.

        Built from room_data (not the live Room objects): once an exit is
        connected during finalization it is removed from its Room and unindexed,
        and branch.net is left edgeless, so the only durable record of the
        topology is branch.map (the connection pairs) resolved through the
        original room_data definitions. Locked exits (the character-gated ones
        we care about) live in the locks dict, so index those too. Scoping to
        branch.all_rooms_added keeps exits that several room_data entries share
        (e.g. WoB/WoR variants) unambiguous, since only one variant is placed.
        """
        owner = {}
        for rid in branch.all_rooms_added:
            data = room_data.get(rid)
            if not data:
                continue
            groups = [data[0], data[1], data[2]]  # doors, traps, pits
            for items in _room_data_locks(rid).values():
                groups.append(items)
            for group in groups:
                if isinstance(group, (list, tuple, set)):
                    for e in group:
                        if isinstance(e, int):
                            owner.setdefault(e, rid)
        return owner

    def _verify_no_character_gated_softlock(self, full_map):
        """Reject maps with a character-gated softlock.

        For each branch, build two room-connectivity graphs from branch.map's
        connection pairs (two-way doors plus one-way trap->pit edges), mapping
        each exit to its room via _branch_exit_owner_map. The *full* graph
        includes every exit; the *free* graph omits exits gated by a character
        not in the starting party (_character_blocked_exits) -- i.e. exactly the
        edges the player can traverse holding only the starting party.

        A room is a character-gated softlock when it can be entered with the
        starting party (reachable from the hub in the free graph) and could be
        left if the gating character were held (can reach the hub in the full
        graph) but cannot be left without it (cannot reach the hub in the free
        graph). Comparing against the full graph excludes pre-existing one-way
        dead ends and event-warp exits (which are escapes the graph never
        models) so only genuine character gates trigger a reroll.

        Raises RuinationMappingError, which the retry loop in events.py catches.
        """
        door_pairs = full_map[0]
        trap_pairs = full_map[1]
        for branch_id, branch in enumerate(self.branches):
            if branch is None:
                continue
            placed = set(branch.all_rooms_added)
            hub_candidates = [r for r in placed if 'ruin_hub_' in str(r)]
            if not hub_candidates:
                continue
            hub_id = hub_candidates[0]

            owner = self._branch_exit_owner_map(branch)
            blocked = self._character_blocked_exits(branch)

            full_g = nx.DiGraph()
            free_g = nx.DiGraph()
            full_g.add_nodes_from(placed)
            free_g.add_nodes_from(placed)

            for d1, d2 in door_pairs:  # two-way doors
                a = owner.get(d1)
                b = owner.get(d2)
                if a is None or b is None:
                    continue
                full_g.add_edge(a, b)
                full_g.add_edge(b, a)
                if d1 not in blocked and d2 not in blocked:
                    free_g.add_edge(a, b)
                    free_g.add_edge(b, a)

            for d1, d2 in trap_pairs:  # one-way trap -> pit
                a = owner.get(d1)
                b = owner.get(d2)
                if a is None or b is None:
                    continue
                full_g.add_edge(a, b)
                if d1 not in blocked and d2 not in blocked:
                    free_g.add_edge(a, b)

            reachable_free = nx.descendants(free_g, hub_id) | {hub_id}
            can_return_free = nx.ancestors(free_g, hub_id) | {hub_id}
            can_return_full = nx.ancestors(full_g, hub_id) | {hub_id}

            stranded = {r for r in reachable_free
                        if r in can_return_full and r not in can_return_free}
            if stranded:
                diag = self._collect_mapping_diagnostics(
                    f"Character-gated softlock on branch {branch_id}: room(s) "
                    f"{sorted(str(s) for s in stranded)} are reachable from the "
                    f"hub with only the starting party but cannot return without "
                    f"a recruited character (gated exits: {sorted(blocked)})",
                    branch_id=branch_id)
                raise RuinationMappingError(diag)

    def compute_actual_areas_used(self):
        """Determine which branch each area's rooms actually reached after finalization.

        self.AreasUsed tracks which branch an area was *distributed* to. That's
        not enough for the Narshe school clues because:
          (a) Distribution only adds rooms that aren't already present in some
              other branch (forced_same_branch, shared rooms, the
              CHARACTER_AREAS['ALL'] pass), so AreasUsed can tag a branch that
              holds none of the area's rooms.
          (b) Even rooms that were added may not be reachable: finalize_map
              only guarantees the hub has no dangling exits, and explicitly
              allows non-hub rooms to remain unconnected (see validation at
              the end of generate_map_with_characters).

        By the end of finalize_map, every connected room has been merged into
        the hub's compound node via loop compression (its constituent IDs are
        joined by '_'). A room R is therefore reachable iff '_R_' is a
        substring of the bracketed hub ID — the underscore boundaries avoid
        false positives from numeric ID prefixes (e.g. 78 vs 278, 501 vs 1501)
        and work for IDs that already contain underscores (share_east,
        ruin_hub_0).

        Returns dict mapping area_name -> branch_id, including only areas with
        at least one reachable room. For areas split across branches, picks
        the branch holding the most reachable rooms.
        """
        connected_per_branch = []
        for branch in self.branches:
            if branch is None:
                connected_per_branch.append(set())
                continue
            hub_ids = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)]
            if not hub_ids:
                connected_per_branch.append(set())
                continue
            hub_bracketed = f"_{hub_ids[0]}_"
            connected = {
                r for r in branch.all_rooms_added
                if f"_{r}_" in hub_bracketed
            }
            connected_per_branch.append(connected)

        result = {}
        for area_name, room_ids in RUIN_ROOM_SETS.items():
            branch_counts = [0, 0, 0]
            for i, connected in enumerate(connected_per_branch):
                for room_id in room_ids:
                    if room_id in connected:
                        branch_counts[i] += 1
            max_count = max(branch_counts)
            if max_count > 0:
                result[area_name] = branch_counts.index(max_count)
        return result

    def _choose_reward_with_exclusion(self, possible_types, characters, espers, items, exclude_chars):
        """Choose a reward from possible types, excluding specified characters.

        Similar to choose_reward() from event_reward.py, but with character exclusion support.
        """
        import random

        all_types = [flag for flag in RewardType]
        random.shuffle(all_types)

        item_possible = False
        for reward_type in all_types:
            if reward_type & possible_types:
                if reward_type == RewardType.CHARACTER and characters.get_available_count():
                    # Check if any characters are available after exclusion
                    available_after_exclusion = [c for c in characters.available_characters if c not in exclude_chars]
                    if available_after_exclusion:
                        return (characters.get_random_available(exclude=exclude_chars), reward_type)
                elif reward_type == RewardType.ESPER and espers.available():
                    return (espers.get_random_esper(), reward_type)
                elif reward_type == RewardType.ITEM:
                    item_possible = True

        # No characters or espers available, must use item
        assert(item_possible)
        return (items.get_good_random(), RewardType.ITEM)

    def _add_conditional_areas(self, new_areas, new_char):
        """Append any CONDITIONAL_AREAS whose predicate is currently satisfied.

        Returns the (possibly extended) `new_areas` list. Areas already mapped
        or already queued in `new_areas` are skipped so that verbose logging
        and future predicate inspection stay accurate; distribute_areas would
        otherwise silently drop duplicates.
        """
        for area_name, condition in CONDITIONAL_AREAS.items():
            if area_name in self.AreasUsed or area_name in new_areas:
                continue
            if condition(self, new_char):
                new_areas.append(area_name)
                if self.verbose:
                    vprint(f'\tAdding conditional area {area_name} to {new_char}\'s areas')
        return new_areas

    def process_rewards(self, rewards, characters, espers, items, branch_id, exclude_chars=None):
        # Identify reward & decide on reward type
        if exclude_chars is None:
            exclude_chars = []

        for reward in rewards:
            # reward_types = [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]
            reward_name = reward[0]  # reward_name = slot.event.name()
            slot = reward[1]
            if self.verbose:
                vprint('Processing reward: ', reward_name)

            remaining_chars_needed = len(self.planned_characters) - self.RewardsObtained[0]
            if remaining_chars_needed >= 1 and self.RewardsAvailable[0] == 1 and (slot.possible_types & RewardType.CHARACTER):
                # This is the last character-capable slot — must be a character.
                if self.verbose:
                    vprint('\tmust be a character')
                # Use characters.get_random_available with exclude parameter
                slot.id = characters.get_random_available(exclude=exclude_chars)
                slot.type = RewardType.CHARACTER
                if self.verbose:
                    vprint('\tgot ', characters.get_name(slot.id), '!')
            else:
                # Just choose from among available types
                if self.verbose:
                    vprint('\tchoosing from...', slot.possible_types)
                slot.id, slot.type = self._choose_reward_with_exclusion(slot.possible_types, characters, espers, items, exclude_chars)
                if self.verbose:
                    if slot.type is RewardType.CHARACTER:
                        vprint('\tgot', characters.get_name(slot.id), '!')
                    elif slot.type is RewardType.ESPER:
                        vprint('\tgot', espers.get_name(slot.id), '!')
                    elif slot.type is RewardType.ITEM:
                        vprint('\tgot', items.get_name(slot.id), '!')

            # Update RewardsObtained
            if slot.type is RewardType.CHARACTER:
                self.RewardsObtained[0] += 1

                # Set character path using the event's character_gate method
                # This returns the character ID that gates this reward (or None for starting areas)
                characters.set_character_path(slot.id, slot.event.character_gate())
                unlocker_name = characters.DEFAULT_NAME[slot.event.character_gate()]
                if self.verbose and slot.event.character_gate() is not None:
                    new_char_name = characters.DEFAULT_NAME[slot.id]
                    vprint(f'\tSet character path: {new_char_name} depends on {unlocker_name}')
                if slot.event.character_gate() is not None and unlocker_name not in self.keychain:
                    # Error:
                    event_name = slot.event.name()
                    new_char_name = characters.DEFAULT_NAME[slot.id]
                    diag = f'\tMAPPING ERROR: got {new_char_name} at {event_name} reward before {unlocker_name} was recruited!'
                    raise RuinationMappingError(diag)


                # If a character, add new areas to the map
                new_char = characters.DEFAULT_NAME[slot.id]
                self.apply_key(new_char)  # apply new key to all branches
                new_areas = list(CHARACTER_AREAS[new_char])
                new_areas = self._add_conditional_areas(new_areas, new_char)
                self.distribute_areas(new_areas, method='shortest')

                # Ebot's Rock diverts the party to Thamasa only when its reward is a
                # character (esper/item rewards leave via door 1546). Model that forced
                # one-way exit by injecting trap 2085 onto the live Ebot's Rock room;
                # forced_connections[2085] = [3085] (pit 3085 in ruin-thamasa) is wired by
                # finalize_map's ForceConnections, so Thamasa becomes a proper downstream
                # node and its exits get connected instead of leaking to the world map.
                # Kept out of static room_data so it stays conditional on the character
                # reward. Both 2085 and 3085 are already in `protected` from distribution
                # time (ForceConnections protects every forced pair regardless of presence),
                # so injecting here can't be consumed early by branch extension.
                if reward_name in ROOM_REWARD.get('ms-wor-78', {}):
                    er_branch = self.branches[branch_id]
                    er_room = er_branch.rooms.get_room('ms-wor-78')
                    if er_room is None:
                        # ms-wor-78 may have been merged into a compound room by
                        # compress_loop; find the live node that contains it.
                        for _node in er_branch.net.nodes:
                            if 'ms-wor-78' in str(_node):
                                er_room = er_branch.rooms.get_room(_node)
                                break
                    if er_room is not None and 2085 not in er_room.traps:
                        er_room.add_traps([2085])
                        er_branch.rooms.reindex_room(er_room.id)
                        if self.verbose:
                            vprint("\tEbot's Rock character reward: injected forced exit "
                                   "(trap 2085 --> Thamasa pit 3085)")

            elif slot.type is RewardType.ESPER:
                self.RewardsObtained[1] += 1

            # Update RewardsAvailable
            if slot.possible_types & RewardType.CHARACTER:
                self.RewardsAvailable[0] -= 1
            if slot.possible_types & RewardType.ESPER:
                self.RewardsAvailable[1] -= 1

            if self.verbose:
                vprint('\tUpdated Rewards Obtained: ', self.RewardsObtained[0], 'Characters, ', self.RewardsObtained[1], 'Espers')
                vprint('\tUpdated Rewards Available: ', self.RewardsAvailable[0], 'Characters, ',
                      self.RewardsAvailable[1],
                      'Espers')

            # Track this reward for spoiler log
            # Find which room this reward is in
            reward_room = None
            for room_id, room_rewards in ROOM_REWARD.items():
                if reward_name in room_rewards:
                    reward_room = room_id
                    break
            self.reward_log.append({
                'order': len(self.reward_log) + 1,
                'name': reward_name,
                'branch': branch_id,
                'type': slot.type,
                'reward_id': slot.id,
                'reward_room': reward_room,
            })

            # Update branch_checks
            self.branch_checks[branch_id].remove(reward_name)
            if self.verbose:
                vprint('\tUpdated branch checks available:')
                for i, bc in enumerate(self.branch_checks):
                    vprint('\t', i, ': ', bc)

            # If a new character unlocks a reward we already found, apply it.
            if slot.type is RewardType.CHARACTER:
                this_char = characters.DEFAULT_NAME[slot.id]
                if this_char in self.LockedRewards:
                    value = self.LockedRewards.pop(this_char)
                    for v in value:
                        unlocked_rewards = v[1]
                        for new_reward in unlocked_rewards:
                            if self.verbose:
                                vprint('\tUnlocked an available reward!', new_reward[0], 'on branch', v[0])
                            # Skip if apply_key already added this reward via
                            # CHARACTER_LOCKED_REWARDS/REWARD_OWNERS — otherwise
                            # branch_checks and RewardsAvailable double-count.
                            if new_reward[0] in self.branch_checks[v[0]]:
                                continue
                            self.branch_checks[v[0]].append(new_reward[0])
                            if new_reward[1].possible_types & RewardType.CHARACTER:
                                self.RewardsAvailable[0] += 1
                            if new_reward[1].possible_types & RewardType.ESPER:
                                self.RewardsAvailable[1] += 1
                        # Then process them all
                        self.process_rewards(unlocked_rewards, characters, espers, items, v[0], exclude_chars)

                # Also scan all remaining LockedRewards for area-locked rewards now
                # accessible (handles shared-area cases like Thamasa owned by SHADOW+STRAGO)
                for other_char in list(self.LockedRewards.keys()):
                    still_locked = []
                    to_unlock = []
                    for entry in self.LockedRewards[other_char]:
                        entry_branch_id, entry_rewards = entry
                        all_accessible = all(self._is_reward_accessible(r[0]) for r in entry_rewards)
                        if all_accessible:
                            to_unlock.append(entry)
                        else:
                            still_locked.append(entry)

                    if to_unlock:
                        if still_locked:
                            self.LockedRewards[other_char] = still_locked
                        else:
                            del self.LockedRewards[other_char]
                        for entry in to_unlock:
                            entry_branch_id, entry_rewards = entry
                            for r in entry_rewards:
                                if r[0] in self.branch_checks[entry_branch_id]:
                                    # apply_key already accounted for this one
                                    continue
                                self.branch_checks[entry_branch_id].append(r[0])
                                if r[1].possible_types & RewardType.CHARACTER:
                                    self.RewardsAvailable[0] += 1
                                if r[1].possible_types & RewardType.ESPER:
                                    self.RewardsAvailable[1] += 1
                            if self.verbose:
                                vprint(f'\tArea-unlock scan: processing {[r[0] for r in entry_rewards]} on branch {entry_branch_id}')
                            self.process_rewards(entry_rewards, characters, espers, items, entry_branch_id, exclude_chars)

    def generate_spoiler_log(self, characters, espers, items):
        """Generate a ruination-specific spoiler log for the -sl flag.

        Outputs:
        - Characters: order obtained, branch, check name, shortest path from hub
        - Other rewards: branch, order obtained
        - Branch terminus rooms: shortest path from hub
        """
        import networkx as nx
        from data.walks import Network
        from data.map_exit_extra import exit_data
        from data.event_exit_info import event_exit_info

        def get_door_name(door_id):
            if door_id in exit_data:
                return exit_data[door_id][1]
            elif door_id in event_exit_info:
                return event_exit_info[door_id][4]
            else:
                return f"Door {door_id}"

        # Rebuild fresh networks for pathfinding (same approach as debug_print_shortest_route)
        rebuilt = {}
        for branch_id, branch in enumerate(self.branches):
            walks = Network(list(branch.all_rooms_added))
            for d1, d2 in branch.map[0]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id)
                    walks.net.add_edge(r2.id, r1.id)
            for d1, d2 in branch.map[1]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id)
            rebuilt[branch_id] = walks

        def find_hub(walks):
            for node_id in walks.net.nodes:
                if 'ruin_hub_' in str(node_id):
                    return node_id
            return None

        def format_path(walks, door_map, hub_id, target_node):
            """Return a list of strings describing the path from hub to target."""
            if target_node == hub_id:
                return ["  (in hub)"]
            try:
                path = nx.shortest_path(walks.net, source=hub_id, target=target_node)
            except nx.NetworkXNoPath:
                return ["  (no path found)"]

            lines = [f"  Path: {len(path)} rooms"]
            for i in range(len(path) - 1):
                current_room = path[i]
                next_room = path[i + 1]
                connection = find_connecting_info(walks, door_map, current_room, next_room)
                lines.append(f"    {current_room}: {connection}")
            lines.append(f"    {path[-1]}: (destination)")
            return lines

        def find_connecting_info(walks, door_map, room1, room2):
            for d1, d2 in door_map[0]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if not r1 or not r2:
                    continue
                if r1.id == room1 and r2.id == room2:
                    has_reverse = walks.net.has_edge(room2, room1)
                    arrow = "<-->" if has_reverse else "-->"
                    return f"{d1} ({get_door_name(d1)}) {arrow} {d2} ({get_door_name(d2)})"
                if r1.id == room2 and r2.id == room1:
                    has_reverse = walks.net.has_edge(room2, room1)
                    arrow = "<-->" if has_reverse else "-->"
                    return f"{d2} ({get_door_name(d2)}) {arrow} {d1} ({get_door_name(d1)})"
            for d1, d2 in door_map[1]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if not r1 or not r2:
                    continue
                if r1.id == room1 and r2.id == room2:
                    return f"TRAP {d1} ({get_door_name(d1)}) --> PIT {d2} ({get_door_name(d2)})"
            return "(connection not found)"

        def find_room_on_branches(room_id):
            for branch_id, walks in rebuilt.items():
                if room_id in walks.net.nodes:
                    return branch_id, walks, room_id
            return None, None, None

        def get_reward_name(entry, characters, espers, items):
            if entry['type'] == RewardType.CHARACTER:
                return characters.get_name(entry['reward_id'])
            elif entry['type'] == RewardType.ESPER:
                return espers.get_name(entry['reward_id'])
            elif entry['type'] == RewardType.ITEM:
                return items.get_name(entry['reward_id'])
            return f"ID {entry['reward_id']}"

        def get_type_label(reward_type):
            if reward_type == RewardType.CHARACTER:
                return "Char"
            elif reward_type == RewardType.ESPER:
                return "Esper"
            elif reward_type == RewardType.ITEM:
                return "Item"
            return "?"

        # Capture rewards assigned after map generation (e.g., by safety code in events.py)
        # ROOM_REWARD entries are shared Reward objects updated by both ruination map gen
        # and the post-ruination reward distribution in events.py
        logged_names = {e['name'] for e in self.reward_log}
        for room_id, rewards in ROOM_REWARD.items():
            for reward_name, slot in rewards.items():
                if reward_name not in logged_names and slot.id is not None and slot.type is not None:
                    # Determine which branch this room is on (if any)
                    branch_id = -1
                    for bid, walks in rebuilt.items():
                        if room_id in walks.net.nodes:
                            branch_id = bid
                            break
                    self.reward_log.append({
                        'order': len(self.reward_log) + 1,
                        'name': reward_name,
                        'branch': branch_id,
                        'type': slot.type,
                        'reward_id': slot.id,
                        'reward_room': room_id,
                    })

        # Build the log output
        log_lines = []

        # Starting party
        log_lines.append(f"Starting Party: {', '.join(self.PARTY)}")
        log_lines.append("")

        # Physical reachability: a path of doors exists from the hub to the
        # reward room. Necessary, but NOT sufficient — see the character-gating
        # fixpoint below.
        def is_physically_reachable(entry):
            if entry['branch'] == -1:
                return False
            reward_room = entry.get('reward_room')
            if reward_room is None:
                return False
            bid, walks, target = find_room_on_branches(reward_room)
            if walks is None:
                return False
            hub_id = find_hub(walks)
            if hub_id is None:
                return False
            if target == hub_id:
                return True
            try:
                nx.shortest_path(walks.net, source=hub_id, target=target)
                return True
            except nx.NetworkXNoPath:
                return False

        # Character-gating reachability.
        #
        # Physical connectivity is necessary but not sufficient: most reward
        # rooms sit in a character-owned area (REWARD_OWNERS) and/or are locked
        # in-game behind a specific character (REWARDS_LOCKED_BY_CHARACTER). A
        # reward is only truly obtainable if every gating character is itself
        # obtainable. Because character rewards are themselves keys, this is a
        # fixpoint: seed the keychain with the starting party, then repeatedly
        # admit any physically-reachable reward whose gates are all satisfied,
        # feeding newly-obtained characters back into the keychain, until no
        # further reward can be admitted.
        #
        # This is what drops circularly-gated characters from the log. The
        # generator can leave such characters on the map (e.g. Cyan placed at
        # Whelk which is Terra's area, Terra at Mt. Kolts which is Sabin's area,
        # Sabin at Doma WOB which is Cyan's area): each is physically present
        # and individually "reachable", but the cycle means none of their
        # gating characters ever enters the keychain, so none can actually be
        # obtained. Without this filter they were printed as findable rewards.
        def gates_satisfied(entry, keychain):
            name = entry['name']
            locker = REWARDS_LOCKED_BY_CHARACTER.get(name)
            if locker is not None and locker not in keychain:
                return False
            owners = REWARD_OWNERS.get(name)
            if owners is not None and not any(o in keychain for o in owners):
                return False
            return True

        reachable_keychain = set(self.PARTY)
        if self.args.open_world:
            # Open world: every character is immediately accessible, so the
            # gating dicts don't apply (the generator clears the lock dict and
            # admits all characters up front).
            reachable_keychain.update(ALL_CHARACTERS)

        candidate_entries = [e for e in self.reward_log if is_physically_reachable(e)]
        accessible_entries = set()  # ids of entries determined accessible
        changed = True
        while changed:
            changed = False
            for e in candidate_entries:
                if id(e) in accessible_entries:
                    continue
                if gates_satisfied(e, reachable_keychain):
                    accessible_entries.add(id(e))
                    changed = True
                    if e['type'] == RewardType.CHARACTER:
                        reachable_keychain.add(characters.DEFAULT_NAME[e['reward_id']])

        def is_accessible(entry):
            return id(entry) in accessible_entries

        # Separate character rewards from other rewards, filtering out inaccessible ones
        char_rewards = [e for e in self.reward_log if e['type'] == RewardType.CHARACTER and is_accessible(e)]
        other_rewards = [e for e in self.reward_log if e['type'] != RewardType.CHARACTER and is_accessible(e)]

        # Number characters starting from the starting party size + 1
        starting_count = len(self.PARTY)

        # --- Character Rewards ---
        log_lines.append("Character Rewards:")
        log_lines.append(f"  {'#':<4} {'Character':<14} {'Branch':<8} {'Check':<28}")

        char_number = starting_count + 1
        for entry in char_rewards:
            char_name = characters.get_name(entry['reward_id'])
            check_name = entry['name']
            branch = entry['branch']

            log_lines.append(f"  {char_number:<4} {char_name:<14} {branch:<8} {check_name:<28}")

            # Find path to reward room
            reward_room = entry['reward_room']
            if reward_room is not None:
                bid, walks, target = find_room_on_branches(reward_room)
                if walks is not None:
                    hub_id = find_hub(walks)
                    if hub_id is not None:
                        door_map = self.branches[bid].map
                        path_lines = format_path(walks, door_map, hub_id, target)
                        log_lines.extend(path_lines)

            char_number += 1

        log_lines.append("")

        # --- Other Rewards ---
        log_lines.append("Other Rewards:")
        log_lines.append(f"  {'#':<4} {'Type':<8} {'Reward':<20} {'Branch':<8} {'Check':<28}")
        for entry in other_rewards:
            reward_name = get_reward_name(entry, characters, espers, items)
            type_label = get_type_label(entry['type'])
            log_lines.append(f"  {entry['order']:<4} {type_label:<8} {reward_name:<20} {entry['branch']:<8} {entry['name']:<28}")

        log_lines.append("")

        # --- Terminus Routes ---
        log_lines.append("Branch Terminus Routes:")
        for branch_id, branch in enumerate(self.branches):
            terminus = branch.terminus
            walks = rebuilt[branch_id]
            hub_id = find_hub(walks)
            if hub_id is None:
                log_lines.append(f"  Branch {branch_id}: hub not found")
                continue

            log_lines.append(f"  Branch {branch_id} terminus: {terminus}")

            # The terminus may have been merged into a compound room; search for it
            target_node = None
            if terminus in walks.net.nodes:
                target_node = terminus
            else:
                for node_id in walks.net.nodes:
                    if terminus in str(node_id):
                        target_node = node_id
                        break

            if target_node is not None:
                door_map = self.branches[branch_id].map
                path_lines = format_path(walks, door_map, hub_id, target_node)
                log_lines.extend(path_lines)
            else:
                log_lines.append("    (terminus not found in network)")

        return log_lines

    def generate_map_image(self, image_path, characters=None, espers=None, items=None):
        """Generate a graphical map of the ruination room network as a PNG image.

        Draws all three branches with:
        - Color-coded nodes by area (from RUIN_ROOM_SETS)
        - Solid lines for two-way door connections
        - Dashed arrows for one-way trap/pit connections
        - Star markers for reward rooms, diamond for terminus, hexagon for hub
        - A legend showing area colors and symbols
        """
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import matplotlib.lines as mlines
        import networkx as nx
        from data.walks import Network
        from data.map_exit_extra import exit_data
        from data.event_exit_info import event_exit_info

        # Build reverse lookup: room_id -> area name
        room_to_area = {}
        for area_name, room_ids in RUIN_ROOM_SETS.items():
            for rid in room_ids:
                room_to_area[rid] = area_name

        # Area color palette - distinct colors for major areas
        area_colors = {
            'Narshe': '#4A90D9',
            'Doma': '#D94A4A',
            'DreamMaze': '#E06666',
            'UmarosCave': '#7B68EE',
            'EsperMountain': '#2ECC71',
            'PhantomTrain': '#8B4513',
            'SealedGate': '#FF6347',
            'SouthFigaroCave': '#DAA520',
            'ReturnersHideout': '#3CB371',
            'AncientCastle': '#CD853F',
            'Jidoor': '#DDA0DD',
            'VeldtCave': '#556B2F',
            'CrescentMtn': '#4682B4',
            'BarenFalls': '#00CED1',
            'Vector': '#DC143C',
            'DarylsTomb': '#9370DB',
            'ZoneEater': '#FF8C00',
            'MtKolts': '#6B8E23',
            'Zozo': '#B8860B',
            'ZozoTower': '#BDB76B',
            'MtZozo': '#808000',
            'BurningHouse': '#FF4500',
            'SouthFigaro': '#F4A460',
            'GauFatherHouse': '#8FBC8F',
            'Thamasa': '#E9967A',
            'Kohlingen': '#87CEEB',
            'Cid': '#ADD8E6',
            'Mobliz': '#98FB98',
            'Maranda': '#FFB6C1',
            'FanaticsTower': '#BA55D3',
            'OperaHouse': '#FF69B4',
            'EbotsRock': '#A0522D',
            'Coliseum': '#C0C0C0',
            'Tzen': '#FFDEAD',
            'Albrook': '#B0E0E6',
            'Veldt': '#9ACD32',
            'Nikeah': '#5F9EA0',
            'PhoenixCave': '#FF7F50',
            'FloatingContinent': '#6495ED',
            'ImperialCamp': '#DB7093',
            'FigaroCastle': '#F0E68C',
            'ImperialCastle': '#778899',
        }
        default_color = '#AAAAAA'

        def get_node_color(node_id):
            if 'ruin_hub_' in str(node_id):
                return '#FFD700'  # Gold for hub
            area = room_to_area.get(node_id)
            if area:
                return area_colors.get(area, default_color)
            # For compound rooms, check if any component matches
            node_str = str(node_id)
            for rid, area in room_to_area.items():
                if str(rid) in node_str:
                    return area_colors.get(area, default_color)
            return default_color

        def get_node_area(node_id):
            if 'ruin_hub_' in str(node_id):
                return 'Hub'
            area = room_to_area.get(node_id)
            if area:
                return area
            node_str = str(node_id)
            for rid, a in room_to_area.items():
                if str(rid) in node_str:
                    return a
            return 'Unknown'

        def is_reward_room(node_id):
            return node_id in ROOM_REWARD

        def is_hub(node_id):
            return 'ruin_hub_' in str(node_id)

        def is_terminus(node_id):
            return node_id in RUIN_TERMINI or 'terminus' in str(node_id)

        def get_reward_label(node_id):
            if node_id in ROOM_REWARD:
                names = list(ROOM_REWARD[node_id].keys())
                return '\n'.join(names)
            return ''

        def get_node_label(node_id):
            if is_hub(node_id):
                return 'HUB'
            if is_terminus(node_id):
                return 'TERMINUS'
            reward = get_reward_label(node_id)
            if reward:
                return reward
            # Use area name as fallback label
            area = get_node_area(node_id)
            if area != 'Unknown':
                return area
            return str(node_id)[:15]

        def get_door_name(door_id):
            if door_id in exit_data:
                return exit_data[door_id][1]
            elif door_id in event_exit_info:
                return event_exit_info[door_id][4]
            return f"Door {door_id}"

        # Rebuild networks (same as spoiler log)
        rebuilt = {}
        for branch_id, branch in enumerate(self.branches):
            walks = Network(list(branch.all_rooms_added))
            for d1, d2 in branch.map[0]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id, edge_type='door')
                    walks.net.add_edge(r2.id, r1.id, edge_type='door')
            for d1, d2 in branch.map[1]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id, edge_type='trap')
            rebuilt[branch_id] = walks

        branch_names = ['Branch 0 (Left)', 'Branch 1 (Center)', 'Branch 2 (Right)']

        # Create figure with 3 subplots (one per branch) + legend
        fig, axes = plt.subplots(1, 3, figsize=(30, 18))
        fig.suptitle('Ruination Mode - Room Network Map', fontsize=20, fontweight='bold', y=0.98)

        for branch_id in range(3):
            ax = axes[branch_id]
            walks = rebuilt[branch_id]
            branch = self.branches[branch_id]
            G = walks.net

            # Remove disconnected nodes (no edges)
            connected_nodes = set()
            for u, v in G.edges():
                connected_nodes.add(u)
                connected_nodes.add(v)
            disconnected = [n for n in G.nodes if n not in connected_nodes]
            G.remove_nodes_from(disconnected)

            if len(G.nodes) == 0:
                ax.set_title(f'{branch_names[branch_id]}\n(empty)', fontsize=14)
                ax.axis('off')
                continue

            # Compute layout - use kamada_kawai for cleaner graphs, fall back to spring
            try:
                pos = nx.kamada_kawai_layout(G)
            except Exception:
                pos = nx.spring_layout(G, k=2.0, iterations=100, seed=42)

            # Classify nodes
            hub_nodes = [n for n in G.nodes if is_hub(n)]
            terminus_nodes = [n for n in G.nodes if is_terminus(n)]
            reward_nodes = [n for n in G.nodes if is_reward_room(n) and n not in hub_nodes and n not in terminus_nodes]
            regular_nodes = [n for n in G.nodes if n not in hub_nodes and n not in terminus_nodes and n not in reward_nodes]

            # Sub-classify regular nodes by warp/town membership. A room can be in
            # both sets (e.g. 'ms-wor-58' is both), so combine: triangle for warp,
            # 50% larger size for town.
            regular_warp_town = [n for n in regular_nodes if n in WARP_ROOMS and n in TOWN_ROOMS]
            regular_warp_only = [n for n in regular_nodes if n in WARP_ROOMS and n not in TOWN_ROOMS]
            regular_town_only = [n for n in regular_nodes if n in TOWN_ROOMS and n not in WARP_ROOMS]
            regular_plain = [n for n in regular_nodes if n not in WARP_ROOMS and n not in TOWN_ROOMS]

            # Classify edges
            door_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('edge_type') == 'door']
            trap_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('edge_type') == 'trap']

            # For door edges, deduplicate bidirectional pairs for drawing
            door_edge_pairs = set()
            door_edges_deduped = []
            for u, v in door_edges:
                pair = tuple(sorted([str(u), str(v)]))
                if pair not in door_edge_pairs:
                    door_edge_pairs.add(pair)
                    door_edges_deduped.append((u, v))

            # Draw edges - doors as solid lines
            if door_edges_deduped:
                nx.draw_networkx_edges(G, pos, edgelist=door_edges_deduped, ax=ax,
                                       edge_color='#555555', width=1.5, style='solid',
                                       arrows=False, alpha=0.7)

            # Draw edges - traps as dashed arrows
            if trap_edges:
                nx.draw_networkx_edges(G, pos, edgelist=trap_edges, ax=ax,
                                       edge_color='#CC0000', width=2.0, style='dashed',
                                       arrows=True, arrowstyle='->', arrowsize=20,
                                       alpha=0.8, connectionstyle='arc3,rad=0.1')

            # Draw nodes by category. Regular nodes split by warp/town:
            #   plain    -> circle, size 300
            #   town     -> circle, size 600
            #   warp     -> upward triangle, size 300
            #   warp+town-> upward triangle, size 600
            if regular_plain:
                nx.draw_networkx_nodes(G, pos, nodelist=regular_plain, ax=ax,
                                       node_color=[get_node_color(n) for n in regular_plain],
                                       node_size=300, node_shape='o',
                                       edgecolors='black', linewidths=1.0)
            if regular_town_only:
                nx.draw_networkx_nodes(G, pos, nodelist=regular_town_only, ax=ax,
                                       node_color=[get_node_color(n) for n in regular_town_only],
                                       node_size=600, node_shape='o',
                                       edgecolors='black', linewidths=1.0)
            if regular_warp_only:
                nx.draw_networkx_nodes(G, pos, nodelist=regular_warp_only, ax=ax,
                                       node_color=[get_node_color(n) for n in regular_warp_only],
                                       node_size=300, node_shape='^',
                                       edgecolors='black', linewidths=1.0)
            if regular_warp_town:
                nx.draw_networkx_nodes(G, pos, nodelist=regular_warp_town, ax=ax,
                                       node_color=[get_node_color(n) for n in regular_warp_town],
                                       node_size=600, node_shape='^',
                                       edgecolors='black', linewidths=1.0)

            node_colors_reward = [get_node_color(n) for n in reward_nodes]
            if reward_nodes:
                nx.draw_networkx_nodes(G, pos, nodelist=reward_nodes, ax=ax,
                                       node_color=node_colors_reward, node_size=600,
                                       node_shape='*', edgecolors='black', linewidths=1.5)

            if hub_nodes:
                nx.draw_networkx_nodes(G, pos, nodelist=hub_nodes, ax=ax,
                                       node_color='#FFD700', node_size=800,
                                       node_shape='H', edgecolors='black', linewidths=2.0)

            if terminus_nodes:
                nx.draw_networkx_nodes(G, pos, nodelist=terminus_nodes, ax=ax,
                                       node_color='#FF1493', node_size=700,
                                       node_shape='D', edgecolors='black', linewidths=2.0)

            # Labels - multi-line format centered below each node:
            #   Regular: AREA / room#    Reward: AREA / room# / reward_name
            # Build reward room -> actual reward name lookup from reward_log
            reward_name_lookup = {}
            if characters and espers and items:
                for entry in self.reward_log:
                    room = entry.get('reward_room')
                    if room is not None:
                        if entry['type'] == RewardType.CHARACTER:
                            name = characters.get_name(entry['reward_id'])
                        elif entry['type'] == RewardType.ESPER:
                            name = espers.get_name(entry['reward_id'])
                        elif entry['type'] == RewardType.ITEM:
                            name = items.get_name(entry['reward_id'])
                        else:
                            name = None
                        if name:
                            reward_name_lookup.setdefault(room, []).append(name)

            all_y = [p[1] for p in pos.values()]
            y_range = max(all_y) - min(all_y) if len(all_y) > 1 else 1.0
            label_offset = y_range * 0.025

            for n in G.nodes:
                x, y = pos[n]
                area = get_node_area(n)
                room_id = str(n)

                if is_hub(n):
                    line1 = 'HUB'
                elif is_terminus(n):
                    line1 = 'TERMINUS'
                elif is_reward_room(n):
                    reward_names = list(ROOM_REWARD[n].keys())
                    line1 = reward_names[0] if len(reward_names) == 1 else '/'.join(reward_names[:2])
                else:
                    line1 = area if area != 'Unknown' else ''

                lines = [line1, room_id] if line1 else [room_id]

                # Add actual reward name(s) as 3rd line for reward rooms
                if is_reward_room(n) and n in reward_name_lookup:
                    lines.append(', '.join(reward_name_lookup[n]))

                label = '\n'.join(lines)
                ax.text(x, y - label_offset, label, fontsize=7, fontweight='bold',
                        ha='center', va='top', multialignment='center')

            # Title with room count
            n_rooms = len(G.nodes)
            n_rewards = len(reward_nodes)
            n_doors = len(door_edges_deduped)
            n_traps = len(trap_edges)
            ax.set_title(f'{branch_names[branch_id]}\n{n_rooms} rooms, {n_rewards} rewards, '
                         f'{n_doors} doors, {n_traps} traps',
                         fontsize=13, fontweight='bold')
            ax.axis('off')

        # Build legend
        # Area color patches
        areas_used = set()
        for branch_id in range(3):
            for n in rebuilt[branch_id].net.nodes:
                areas_used.add(get_node_area(n))

        legend_handles = []
        # Symbol legend
        legend_handles.append(mlines.Line2D([], [], color='#FFD700', marker='H', linestyle='None',
                              markersize=12, markeredgecolor='black', label='Hub'))
        legend_handles.append(mlines.Line2D([], [], color='#FF1493', marker='D', linestyle='None',
                              markersize=10, markeredgecolor='black', label='Terminus'))
        legend_handles.append(mlines.Line2D([], [], color='white', marker='*', linestyle='None',
                              markersize=14, markeredgecolor='black', label='Reward'))
        legend_handles.append(mlines.Line2D([], [], color='white', marker='^', linestyle='None',
                              markersize=10, markeredgecolor='black', label='Warp point'))
        legend_handles.append(mlines.Line2D([], [], color='white', marker='o', linestyle='None',
                              markersize=14, markeredgecolor='black', label='Town'))
        legend_handles.append(mlines.Line2D([], [], color='#555555', linestyle='solid',
                              linewidth=2, label='Door (two-way)'))
        legend_handles.append(mlines.Line2D([], [], color='#CC0000', linestyle='dashed',
                              linewidth=2, label='Trap/Pit (one-way)'))
        legend_handles.append(mlines.Line2D([], [], linestyle='None', label=''))  # spacer

        # Area color legend - sort alphabetically, only include used areas
        for area_name in sorted(areas_used):
            if area_name in ('Hub', 'Unknown'):
                continue
            color = area_colors.get(area_name, default_color)
            legend_handles.append(mpatches.Patch(facecolor=color, edgecolor='black',
                                  label=area_name))

        fig.legend(handles=legend_handles, loc='lower center', ncol=6,
                   fontsize=9, frameon=True, fancybox=True, shadow=True,
                   bbox_to_anchor=(0.5, 0.0))

        plt.tight_layout(rect=[0, 0.08, 1, 0.96])
        plt.savefig(image_path, dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        return image_path

    def debug_print_shortest_route(self, destination_rooms):
        """Find and print the shortest route from hub to each destination room in ruination mode.

        The branch networks are collapsed into single hub compounds by the mapping
        algorithm (loop merging). To find actual paths between rooms, we rebuild
        fresh networks from the original rooms and the door/trap connections
        recorded in branch.map, mirroring the approach used in data/doors.py.

        Supports room IDs (int or string) and area names from RUIN_ROOM_SETS.

        Args:
            destination_rooms: List of target room IDs or area names (strings from argparse)
        """
        import networkx as nx
        from data.walks import Network
        from data.map_exit_extra import exit_data
        from data.event_exit_info import event_exit_info

        def get_door_name(door_id):
            """Get human-readable name for a door/exit ID."""
            if door_id in exit_data:
                return exit_data[door_id][1]
            elif door_id in event_exit_info:
                return event_exit_info[door_id][4]
            else:
                return f"Door {door_id}"

        # Rebuild fresh networks for each branch from original rooms + connections.
        # This gives us individual room nodes (not collapsed compounds) for pathfinding.
        rebuilt = {}
        for branch_id, branch in enumerate(self.branches):
            walks = Network(list(branch.all_rooms_added))

            # Add edges from two-way door pairs
            for d1, d2 in branch.map[0]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id)
                    walks.net.add_edge(r2.id, r1.id)

            # Add edges from one-way pairs
            for d1, d2 in branch.map[1]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if r1 and r2:
                    walks.net.add_edge(r1.id, r2.id)

            rebuilt[branch_id] = walks

        def find_room_on_branches(room_id):
            """Find which branch contains a room."""
            for branch_id, walks in rebuilt.items():
                if room_id in walks.net.nodes:
                    return branch_id, walks, room_id
            return None, None, None

        def find_hub(walks):
            """Find the hub node ID in a rebuilt network."""
            for node_id in walks.net.nodes:
                if 'ruin_hub_' in str(node_id):
                    return node_id
            return None

        def find_connecting_info(walks, door_map, room1, room2):
            """Find the exit IDs connecting two rooms using the door mapping."""
            # Check door pairs (two-way)
            for d1, d2 in door_map[0]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if not r1 or not r2:
                    continue
                if r1.id == room1 and r2.id == room2:
                    has_reverse = walks.net.has_edge(room2, room1)
                    arrow = "<-->" if has_reverse else "-->"
                    return f"{d1} ({get_door_name(d1)}) {arrow} {d2} ({get_door_name(d2)})"
                if r1.id == room2 and r2.id == room1:
                    has_reverse = walks.net.has_edge(room2, room1)
                    arrow = "<-->" if has_reverse else "-->"
                    return f"{d2} ({get_door_name(d2)}) {arrow} {d1} ({get_door_name(d1)})"

            # Check trap pairs (one-way)
            for d1, d2 in door_map[1]:
                r1 = walks.rooms.get_room_from_element(d1)
                r2 = walks.rooms.get_room_from_element(d2)
                if not r1 or not r2:
                    continue
                if r1.id == room1 and r2.id == room2:
                    return f"TRAP {d1} ({get_door_name(d1)}) --> PIT {d2} ({get_door_name(d2)})"

            return "(connection not found in map)"

        def print_route(destination_label, branch_id, walks, door_map, hub_id, target_node):
            """Print the route from hub to target node."""
            if target_node == hub_id:
                print(f"\n{'='*80}")
                print(f"DEBUG ROUTE: '{destination_label}' is in the hub on Branch {branch_id}")
                print(f"  Hub: {hub_id}")
                print(f"{'='*80}\n")
                return

            try:
                path = nx.shortest_path(walks.net, source=hub_id, target=target_node)
            except nx.NetworkXNoPath:
                print(f"\n{'='*80}")
                print(f"DEBUG ROUTE: No path from hub to '{destination_label}' on Branch {branch_id}")
                print(f"  Hub: {hub_id}")
                print(f"  Target node: {target_node}")
                print(f"{'='*80}\n")
                return

            print(f"\n{'='*80}")
            print(f"DEBUG ROUTE: Hub --> '{destination_label}' (Branch {branch_id})")
            print(f"{'='*80}")
            print(f"  Path length: {len(path)} rooms\n")

            for i in range(len(path) - 1):
                current_room = path[i]
                next_room = path[i + 1]
                connection = find_connecting_info(walks, door_map, current_room, next_room)
                print(f"  {current_room}: {connection}")

            print(f"  {path[-1]}: (destination)")
            print(f"{'='*80}\n")

        # Process each destination
        for dest_str in destination_rooms:
            # Try to convert to int (room IDs can be integers)
            try:
                dest = int(dest_str)
            except (ValueError, TypeError):
                dest = dest_str

            # Check if it's an area name in RUIN_ROOM_SETS
            if dest in RUIN_ROOM_SETS:
                area_name = dest
                if area_name in self.AreasUsed:
                    branch_id = self.AreasUsed[area_name]
                    walks = rebuilt[branch_id]
                    door_map = self.branches[branch_id].map
                    hub_id = find_hub(walks)

                    if hub_id is None:
                        print(f"DEBUG ERROR: Hub not found on branch {branch_id}")
                        continue

                    # Find the closest room of this area from the hub
                    area_rooms = RUIN_ROOM_SETS[area_name]
                    best_path_len = float('inf')
                    best_room_id = None

                    for room_id in area_rooms:
                        if room_id in walks.net.nodes and room_id != hub_id:
                            try:
                                path = nx.shortest_path(walks.net, source=hub_id, target=room_id)
                                if len(path) < best_path_len:
                                    best_path_len = len(path)
                                    best_room_id = room_id
                            except nx.NetworkXNoPath:
                                continue

                    if best_room_id is not None:
                        print_route(f"{area_name} (room {best_room_id})", branch_id, walks, door_map, hub_id, best_room_id)
                    elif any(r == hub_id for r in area_rooms):
                        print(f"\n{'='*80}")
                        print(f"DEBUG ROUTE: Area '{area_name}' is in the hub on Branch {branch_id}")
                        print(f"  Hub: {hub_id}")
                        print(f"{'='*80}\n")
                    else:
                        print(f"DEBUG ERROR: No reachable rooms from area '{area_name}' found on branch {branch_id}")
                else:
                    print(f"DEBUG ERROR: Area '{area_name}' was not placed on any branch.")
                    print(f"  Areas used: {dict(sorted(self.AreasUsed.items(), key=lambda x: x[1]))}")
                continue

            # It's a room ID - find it on branches
            branch_id, walks, target_node = find_room_on_branches(dest)
            if walks is None:
                print(f"DEBUG ERROR: Room '{dest}' not found on any branch.")
                print(f"  Hint: use area names like {list(RUIN_ROOM_SETS.keys())[:5]}... or room IDs from RUIN_ROOM_SETS")
                continue

            door_map = self.branches[branch_id].map
            hub_id = find_hub(walks)
            if hub_id is None:
                print(f"DEBUG ERROR: Hub not found on branch {branch_id}")
                continue

            print_route(str(dest), branch_id, walks, door_map, hub_id, target_node)


def ruination_start_game_mod(dialogs, party):
    # Write the event that starts the game in ruination mode

    # Dialog IDs $0590/$0591 sit in the vanilla Maduin/Madonna esper-world
    # conversation block, which never plays in ruination mode. See ARCHIVE.md
    # "Ruination Mode — Dialog ID Reservations" for the complete map.
    ruination_start_1 = 0x0590
    if party >= 2:
        dialogs.set_text(ruination_start_1, "After Kefka broke the world, we woke up here.<wait 60 frames><end>")
    else:
        dialogs.set_text(ruination_start_1, "After Kefka broke the world, I woke up here.<wait 60 frames><end>")
    ruination_start_2 = 0x0591
    dialogs.set_text(ruination_start_2, "This new world is dark and full of monsters.<wait 30 frames> Let's find our friends and bring hope to the darkness.<end>")

    src = [
        field.LoadMap(ESPER_GATE_MAPID, direction.DOWN, default_music=False,
                        x=55, y=33, entrance_event=True),
    ]

    # Only create/position/show entities for party slots that have actual characters.
    # Operating on empty party slots can alias to wrong characters due to stale data.
    if party >= 2:
        src += [field.CreateEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.CreateEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.CreateEntity(field_entity.PARTY3)]

    src += [
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetPosition(54, 31),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpriteLayer(2),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),
    ]
    if party >= 2:
        src += [
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.SetPosition(56, 32),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]
    if party >= 3:
        src += [
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.SetPosition(53, 33),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]
    if party >= 4:
        src += [
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.SetPosition(55, 35),
                            field_entity.AnimateKnockedOut(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            ),
        ]

    src += [field.ShowEntity(field_entity.PARTY0)]
    if party >= 2:
        src += [field.ShowEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.ShowEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.ShowEntity(field_entity.PARTY3)]

    src += [
        field.RefreshEntities(),
        field.Dialog(ruination_start_1, wait_for_input=False, inside_text_box=False, top_of_screen=False),
        field.HoldScreen(),
        field.FadeInScreen(speed=8),
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.Pause(60),
                        field_entity.AnimateKneeling(),
                        field_entity.Pause(20),
                        field_entity.AnimateStandingHeadDown(),
                        field_entity.Pause(10),
                        # Shaking head (see e.g. CA/FCC6)
                        field_entity.AnimateTiltHeadLeft(),
                        field_entity.Pause(8),
                        field_entity.AnimateTiltHeadRight(),
                        field_entity.Pause(15),
                        #field_entity.AnimateTiltHeadLeft(),
                        #field_entity.Pause(8),
                        #field_entity.AnimateTiltHeadRight(),
                        #field_entity.Pause(8),
                        ),
        field.Dialog(ruination_start_2, wait_for_input=False, inside_text_box=False, top_of_screen=False),
    ]
    # Animate party assembling, based on number of characters
    if party == 1:
        # Just animate main character
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(2),
                            field_entity.AnimateCloseEyes(),
                            field_entity.Pause(2),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(2),
                            field_entity.AnimateCloseEyes(),
                            field_entity.Pause(2),
                            field_entity.AnimateStandingFront(),
                            ),
        ]
    elif party == 2:
        # Animate character 1 picking up character 2
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.AnimateAttackRight(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, True,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),

        ]
    elif party == 3:
        # Animate character 1 waking up character 2, picking up character 3
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.Pause(1),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(16),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.Pause(16),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            ),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.DisableEntityCollision(field_entity.PARTY2),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY2, True,
                            field_entity.AnimateFaceRightHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Hide(),
                            ),

        ]
    elif party == 4:
        # Animate character 1 waking up character 2, picking up character 3;  character 4 wakes themselves up.
        src += [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.AnimateKneelingRight(),
                            ),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(8),
                            field_entity.Turn(direction.LEFT),
                            field_entity.AnimateHandsUp(),
                            field_entity.Pause(1),
                            field_entity.AnimateAttack(),
                            field_entity.Pause(16),
                            field_entity.Move(direction.DOWN, 1),
                            field_entity.Turn(direction.LEFT)
                            ),
            field.EntityAct(field_entity.PARTY2, False,
                            field_entity.Pause(16),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadLeft(),
                            field_entity.Pause(1),
                            field_entity.AnimateTiltHeadRight(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            ),
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.Pause(20),
                            field_entity.AnimateSurprised(),
                            field_entity.Pause(1),
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(2),
                            field_entity.AnimateFrontRightHandUp(),
                            field_entity.Pause(4),
                            field_entity.AnimateFrontRightHandWaving(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.UP, 1),
                            ),
            field.WaitForEntityAct(field_entity.PARTY2),
            field.DisableEntityCollision(field_entity.PARTY0),
            field.DisableEntityCollision(field_entity.PARTY1),
            field.DisableEntityCollision(field_entity.PARTY2),
            field.DisableEntityCollision(field_entity.PARTY3),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(4),
                            field_entity.AnimateStandingFront(),
                            field_entity.Pause(4),
                            field_entity.Move(direction.DOWN, 1),
                            ),
            field.EntityAct(field_entity.PARTY1, False,
                            field_entity.AnimateFaceLeftHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.LEFT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY2, False,
                            field_entity.AnimateFaceRightHeadDown(),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.Pause(4),
                            field_entity.Move(direction.RIGHT, 1),
                            field_entity.Hide(),
                            ),
            field.EntityAct(field_entity.PARTY3, True,
                            field_entity.Turn(direction.UP),
                            field_entity.Pause(8),
                            field_entity.Move(direction.UP, 1),
                            field_entity.Hide(),
                            ),
            field.EnableEntityCollision(field_entity.PARTY0),

        ]

    # Only hide party entities that were actually created
    if party >= 2:
        src += [field.HideEntity(field_entity.PARTY1)]
    if party >= 3:
        src += [field.HideEntity(field_entity.PARTY2)]
    if party >= 4:
        src += [field.HideEntity(field_entity.PARTY3)]

    src += [
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetSpriteLayer(0),
                        ),

        field.RefreshEntities(),
        field.FreeScreen(),
        field.Return(),
    ]
    space = Write(Bank.CC, src, "start game ruination")
    return space.start_address


# --- Party Interaction Scripts (talking to inactive party leaders) ---

# Dialog IDs for character airship quotes (vanilla WoR airship dialog).
# Order matches character IDs 0-13: Terra, Locke, Cyan, Shadow, Edgar, Sabin,
# Celes, Strago, Relm, Setzer, Mog, Gau, Gogo, Umaro.
CHARACTER_AIRSHIP_DIALOG_IDS = [
    0x0B94, 0x0B95, 0x0B96, 0x0B97,  # Terra, Locke, Cyan, Shadow
    0x0B98, 0x0B99, 0x0B9A, 0x0B9B,  # Edgar, Sabin, Celes, Strago
    0x0B9C, 0x0B9D, 0x068B, 0x068D,  # Relm, Setzer, Mog, Gau
    0x068F, 0x0690,                    # Gogo, Umaro
]

# Per-character dialog choices for party interaction. One is randomly selected
# on each compile and written over the vanilla airship quote dialog slot.
# Sourced from memorable vanilla FF6 dialog lines for each character.
from constants.entities import (
    TERRA, LOCKE, CYAN, SHADOW, EDGAR, SABIN, CELES, STRAGO, RELM, SETZER,
    MOG, GAU, GOGO, UMARO,
)
CHARACTER_DIALOG_CHOICES = {
    TERRA: [
        # introspective, searching for meaning/love, determined
        "General Leo...<line>I believe I understand what you were trying to say.<end>",  # edited
        "I know what love is...!<end>",
        #"I'll do it!<end>",
        "People only seem to want power.<line>Do they really want to be like me?<end>",
        #"I'm hardly...normal...<end>",
        #"I can do it...<line>But why do I feel so wretched?<end>",
        "I'm all right.<line>I'm sure peace is within our grasp!<end>",
        "We must fight for those who aren't even born yet!<end>",  # Now I must go to war.<line>
        #"I want to know what love is...<line>now!<end>",
        "I can fight!<end>",
        #"Come with me!<end>",
        #"Everyone's calling me.<end>",
    ],
    LOCKE: [
        # treasure hunter, protective, devoted
        "I PREFER the term treasure hunting!<end>",
        #"That's TREASURE HUNTER!<end>",
        "I'll protect you!<end>",
        "Trust me! You'll be fine!<end>",
        "As long as there're people who need to be protected, I'll fight!<end>",
        "I have learned to celebrate life... and the living.<end>",  # <line>
        "Let's go!<line>We have work to do!!<end>",
        #"We haven't a second to lose!<end>",
        #"I promised I'd protect her.<line>I WILL NOT back out on my word.<end>",
    ],
    CYAN: [
        # honorable samurai, formal speech
        #"What an amazing device!<end>",
        "Thou musn't give up the fight!<end>",
        #"I am <CYAN>,<line>retainer to the King of Doma.<line>I am your worst nightmare...<end>",
        "My family lives on inside of me.<end>",
        "I will avenge the people of Doma!!<end>",
        "I shall go with you!<end>",
    ],
    SHADOW: [
        # mysterious loner, terse
        "...<end>",
        "The Reaper is always just a step behind me...<end>",
        #"Leave 'em alone.<end>",
        "We meet again...<end>",
        "I know what friendship is...<line>and family...<end>",
        #"Go! There are people counting on you!<end>",
        "I can't help you.<line>You must look within for answers.<end>",
    ],
    EDGAR: [
        # charming king, flirtatious, witty
        "If something happens to me, all the world's women will grieve!<end>",  # <line>
        "It is my dream to build a kingdom in which I can guarantee freedom, and dignity.<end>", # <line>
        #"First of all, your beauty<line>has captivated me!<end>",
        #"Guess my technique's getting a bit rusty...<end>",
        #"He'd slit his mama's throat for a nickel!<end>",
        "It's time to break into Kefka's domain!<end>",
        "I finally think we're gonna pull this off!<end>",
        #"Bravo, Figaro!!!<end>",
        "You can't keep track of 'em all!<end>",
    ],
    SABIN: [
        # strong, earnest, bear-like
        "Think a 'bear' like me could help you in your fight?<end>",
        "Riiiiiight!<end>",
        "Let me have at it!<end>",
        #"Then let's just bust through!<end>",
        "Master Duncan's techniques mustn't fail me.<end>",
        "You think the end of the world was gonna do me in?<end>", # <line>
        "Now I know why I have these stupid muscles!<end>",
        "I have come to experience anew the love of my brother!<end>", # <line>
        "Can't wage war on an empty stomach!<end>",
        "...smash Kefka, and deliver peace unto the world! All right, count me in!<end>",
    ],
    CELES: [
        # former general, strong-willed, emotional depth
        "I'm a soldier, not some love-starved twit!<end>",
        "I'm free...<line>The Empire can't control me!<end>",
        "I've met someone who can accept me<line>for what I am.<end>",
        "I'm glad I made it this far... I feel I have a lot to live for...<end>", # <line>
        #"I think you've been hustled,<line>Mr. Gambler.<end>",
        "I'm a GENERAL, not some opera floozy!<end>",
        "Come on, everybody!<line>We have to work together!<end>",
        #"He's alive...<line><LOCKE>'s still alive!!!<end>",
        "I'll make you proud of me, Granddad...<end>",
    ],
    STRAGO: [
        # old sage, grandfather figure
        #"I have a special little Granddaughter!<end>",
        "Hey everyone! Let me see the light in your eyes! The old man, here, hasn't given up yet!<end>", # <line> #<line>
        "I wanted to show my enemy the true meaning of the word, 'hero'!<end>",  # <line>
        "Fool! I may be old,<line>but I'm not powerless!<end>",
        #"I owe you for saving <RELM>.<line>I'll help you find your Espers.<end>",
        "In all my travels,<line>and in all my years...<end>",
    ],
    RELM: [
        # sassy young painter
        "Let's do it!<line>Let's go get that madman!<end>",
        #"And I have a brave Grandpa who'll<line>stand by me through it all.<end>",
        "Who is this puffed up aerobics instructor, anyway?<end>", #<line>
        "Did you think I was gonna check out<line>before you, old man?!<end>",
        "Hey! Did you see me? I was awesome!<end>",
        "I'm coming along, too.<end>",
        "What a fuddy duddy...<end>",
        "Aaack! I'm gonna paint your portrait!<end>",
    ],
    SETZER: [
        # gambler, risk-taker, romantic
        "My life is a chip in your pile.<line>Ante up!<end>",
        "My friend's airship...<line>and her love!<end>",
        "Something good will come of it all!<end>",
        "Nothing to lose but my life...<end>",
        "When things fall, they fall!<line>It's all a matter of fate...<end>",
        #"There's nothing like flying!<end>",
        "I'm starting to feel lucky!!<end>",
        "Sometimes in life you just have to<line>FEEL your way through a situation!<end>",
    ],
    MOG: [
        # cute moogle
        "Kupoppo!!<end>",
        "I'm your boss, kupo!<line>You're gonna join us, kupo!!!<end>",
        "Kupo!<end>",
        #"I have my friends here!<end>",
    ],
    GAU: [
        # wild boy, broken speech, heartfelt
        "You my friends!<line>Me uwaooo all of you!<end>",
        "<GAU>...<line><GAU> do his best!<end>",
        "<GAU> hit hard!!!<end>",
        #"<GAU> become stronger on the Veldt.<end>",
        "Fffatherrr...alive...<line>H...a...p...p...y...<end>",
        "<GAU> find short cut!<end>",
        "Awoooo...!<end>",
    ],
    GOGO: [
        # mysterious mimic
        "This should be fun.<line>When do we leave?<end>",
        "You seek to save the world? Then I guess that means I shall save the world as well.<end>",
        "Lead on! I will copy your every move.<end>",
        #"I have been idle for too many years... Perhaps I ought to mimic you.<end>",
        "...<end>",
    ],
    UMARO: [
        # barely speaks
        "Uhhhh...<end>",
        "Oooh...<end>",
        "Ughaaa!<end>",
    ],
}

# Repurpose vanilla "Change party members?" dialog (0x0528 = 1320) for the choice menu.
PARTY_INTERACT_CHOICE_DIALOG = 1320

# Maps character ID -> ROM address of that character's party interaction event script.
# Populated by create_party_interaction_scripts(); read by RecruitAndSelectParty and
# NarsheWob/Start to emit ChangeNPCEventAddress instructions.
PARTY_INTERACTION_SCRIPT_ADDRS = {}

# ROM address of the shared "set all party interaction NPC pointers" subroutine.
# Populated by create_party_interaction_scripts() (runs before the event mod loop).
# Callers import this lazily (inside a method) and invoke it via field.Call, or
# assign it as a map's entrance_event_address (after subtracting EVENT_CODE_START).
SET_PARTY_INTERACTION_POINTERS = None


def create_party_interaction_scripts(dialogs):
    """Create per-character event scripts for party interaction in ruination mode.

    When the player talks to an inactive party's leader, the script:
      1. Shows the leader's airship quote dialog
      2. Offers a 3-option choice: Join forces / Swap members / Do nothing
      3. Runs the appropriate party formation sequence

    Also creates a shared finishing subroutine used by all 14 scripts.

    Args:
        dialogs: The Dialogs object for setting dialog text.
    """
    from instruction.field.functions import (
        REFRESH_CHARACTERS_AND_SELECT_PARTY,
        REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES,
    )
    from constants.entities import CHARACTER_COUNT

    # Set the choice dialog text.
    dialogs.set_text(PARTY_INTERACT_CHOICE_DIALOG,
                     "<choice> Join forces<line>"
                     "<choice> Swap members<line>"
                     "<choice> Do nothing<end>")

    # Shared finishing subroutine: called (via Branch) after SelectParties returns.
    finish_src = [
        field.FinalizeBranchRecruit(),
        field.RefreshEntities(),
        field.UpdatePartyLeader(),
        field.FadeInScreen(),
        field.WaitForFade(),
        field.FreeMovement(),
        field.Return(),
    ]
    space = Write(Bank.CA, finish_src, "party interact finish subroutine")
    finish_addr = space.start_address

    # Randomly select and write a dialog line for each character.
    for char_id in range(CHARACTER_COUNT):
        choices = CHARACTER_DIALOG_CHOICES.get(char_id)
        if choices:
            dialog_id = CHARACTER_AIRSHIP_DIALOG_IDS[char_id]
            char_name = Characters.DEFAULT_NAME[char_id]
            dialogs.set_text(dialog_id, f"<{char_name}>: {random.choice(choices)}")

    # Create one event script per character.
    for char_id in range(CHARACTER_COUNT):
        char_dialog = CHARACTER_AIRSHIP_DIALOG_IDS[char_id]
        join_arg = char_id | 0x10   # 0b0001cccc: include party, merge into 1
        swap_arg = char_id | 0x30   # 0b0011cccc: include party, 2-party swap

        src = [
            field.Dialog(char_dialog),
            field.DialogBranch(PARTY_INTERACT_CHOICE_DIALOG,
                               dest1="JOIN", dest2="SWAP", dest3=field.RETURN),

            "JOIN",
            field.SetupBranchRecruit(join_arg),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.Branch(finish_addr),

            "SWAP",
            field.SetupBranchRecruit(swap_arg),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),
            field.Branch(finish_addr),
        ]
        space = Write(Bank.CA, src, f"party interact script char {char_id}")
        PARTY_INTERACTION_SCRIPT_ADDRS[char_id] = space.start_address

    # Free the vanilla airship event scripts that we replaced.
    # CA/3F13-CA/3F82 (112 bytes, 8 per character).
    Free(0xa3f13, 0xa3f82)

    # Write the shared subroutine that repoints every recruited character's
    # NPC talk event to its party-interaction script. Runs after the per-character
    # scripts above so PARTY_INTERACTION_SCRIPT_ADDRS is fully populated. Must
    # happen before the event.mod() loop so callers (NarsheWob, EsperWorld)
    # can read SET_PARTY_INTERACTION_POINTERS.
    _write_set_party_interaction_pointers_subroutine()


def _write_set_party_interaction_pointers_subroutine():
    """Write the 'set all party interaction NPC pointers' subroutine to Bank.CA once.

    For each of the 14 characters, emits:
        if character_recruited(c): ChangeNPCEventAddress(c, PARTY_INTERACTION_SCRIPT_ADDRS[c])
    followed by a Return so the subroutine can be invoked via field.Call or used
    as a map entrance_event. Stores the full SNES address in the module-level
    SET_PARTY_INTERACTION_POINTERS.
    """
    from constants.entities import CHARACTER_COUNT
    global SET_PARTY_INTERACTION_POINTERS

    src = []
    for char_id in range(CHARACTER_COUNT):
        addr = PARTY_INTERACTION_SCRIPT_ADDRS[char_id]
        src += [
            field.BranchIfEventBitClear(event_bit.character_recruited(char_id), f"SKIP_{char_id}"),
            field.ChangeNPCEventAddress(char_id, addr),
            f"SKIP_{char_id}",
        ]
    src.append(field.Return())
    space = Write(Bank.CA, src, "set party interaction pointers subroutine")
    SET_PARTY_INTERACTION_POINTERS = space.start_address


# ROM addresses of the shared y-party-switch save/disable and restore subroutines.
# Populated by create_y_party_switch_subroutines() (runs before the event mod loop).
# Callers import these lazily (inside a method) and invoke them via field.Call, or
# assign one as a map event's event_address (after subtracting EVENT_CODE_START).
DISABLE_Y_PARTY_SWITCH = None
RESTORE_Y_PARTY_SWITCH = None


def create_y_party_switch_subroutines():
    """Write the shared y-party-switch save/disable and restore subroutines once.

    Several ruination-mode events (doma wob, fanatics tower, floating continent,
    narshe moogle defense) make dynamic map edits that break if the player presses
    "y" to switch parties mid-event. Each disables y-party switching when its scene
    begins and restores it at the end, remembering whether it was on in the
    SAVED_Y_PARTY_SWITCHING event bit. The scenes never overlap, so one pair of
    subroutines (and one save bit) serves all of them.

    Stores the SNES addresses in the module-level DISABLE_Y_PARTY_SWITCH /
    RESTORE_Y_PARTY_SWITCH. Each ends in Return so it can be invoked via field.Call
    or used as a map event's event_address (after subtracting EVENT_CODE_START).
    """
    global DISABLE_Y_PARTY_SWITCH, RESTORE_Y_PARTY_SWITCH

    # Save ENABLE_Y_PARTY_SWITCHING to SAVED_Y_PARTY_SWITCHING, then clear it.
    src = [
        field.BranchIfEventBitSet(event_bit.ENABLE_Y_PARTY_SWITCHING, "Y_WAS_ON"),
        field.ClearEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        field.Branch("DONE"),
        "Y_WAS_ON",
        field.SetEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        "DONE",
        field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        field.Return(),
    ]
    space = Write(Bank.CB, src, "save and disable y-party switching")
    DISABLE_Y_PARTY_SWITCH = space.start_address

    # Restore ENABLE_Y_PARTY_SWITCHING from SAVED_Y_PARTY_SWITCHING.
    src = [
        field.BranchIfEventBitSet(event_bit.SAVED_Y_PARTY_SWITCHING, "Y_WAS_ON"),
        field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        field.Branch("DONE"),
        "Y_WAS_ON",
        field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
        "DONE",
        field.ClearEventBit(event_bit.SAVED_Y_PARTY_SWITCHING),
        field.Return(),
    ]
    space = Write(Bank.CB, src, "restore y-party switching")
    RESTORE_Y_PARTY_SWITCH = space.start_address


def disable_chocobo_stables(rom, dialogs, args):
    """
    Disables the in-town chocobo stables for ruination mode.
    Changes the chocobo keeper dialogs to explain chocobos won't go outside,
    and patches the event code to just display the dialog and return (no choices).

    Args:
        rom: The ROM object to modify
        dialogs: The Dialogs object to update dialog text
        args: Command line arguments (for debug flag)
    """
    # Chocobo stable event addresses and their dialog IDs
    # Format: (event_address, dialog_id, description)
    chocobo_stables = [
        (0xa7a36, 0x0B8E, "South Figaro chocobo"),
        (0xa8fb4, 0x0B8E, "Nikeah chocobo"),  # Shares dialog with South Figaro
        (0xb44cd, 0x0113, "Jidoor chocobo"),
    ]

    disabled_message = "The chocobos won't go outside anymore.<end>"

    # Track which dialogs we've already updated
    updated_dialogs = set()

    for event_addr, dialog_id, description in chocobo_stables:
        # Update dialog text (only once per unique dialog ID)
        if dialog_id not in updated_dialogs:
            dialogs.set_text(dialog_id, disabled_message)
            updated_dialogs.add(dialog_id)

            if args.debug:
                print(f"Updated dialog {dialog_id:#x} for {description}")

        # Patch event code to: display dialog (4B), return (FE)
        # Format: 4B [dialog_id_lo] [dialog_id_hi] FE
        event_bytes = bytes([0x4B, dialog_id & 0xFF, dialog_id >> 8, 0xFE])
        rom.set_bytes(event_addr, event_bytes)

        if args.debug:
            print(f"Disabled {description} at {event_addr:#x}")


# Ferry-port descriptors used by fix_ferry_connections.
#   npc_event_addr  - the field-event slot the NPC's talk script enters at.
#   dest_map / dest_spawn / dest_dir - where the player materialises after travel.
#   wor_dock        - the airship-park tile on the WoR overworld for the boat anim.
# Albrook adds a few extra fields because we promote a generic NPC into a sailor:
#   sailor_map / sailor_npc_id - which NPC slot we promote
#   sailor_npc_bit             - the visibility bit that must be ON for the NPC
#   sailor_sprite              - sprite to assign (54 = sailor)
FERRY_PORTS = {
    'SouthFigaro': {
        'display':        'South Figaro',
        'npc_event_addr': 0xa77d7,
        'dest_map':       0x5b,  'dest_spawn': (12, 11), 'dest_dir': direction.LEFT,
        'wor_dock':       (113, 96),
    },
    'Nikeah': {
        'display':        'Nikeah',
        'npc_event_addr': 0xa8cbb,
        'dest_map':       0xbb,  'dest_spawn': (24, 11), 'dest_dir': direction.DOWN,
        'wor_dock':       (147, 77),
    },
    'Albrook': {
        'display':        'Albrook',
        'npc_event_addr': 0xbd1f3,
        'dest_map':       0x14c, 'dest_spawn': (28, 7),  'dest_dir': direction.LEFT,
        'wor_dock':       (141, 210),
        'sailor_map':     0x14c, 'sailor_npc_id': 0x22,
        'sailor_npc_bit': 0x565, 'sailor_sprite': 54,
    },
}

# Each port's NPC has a single owned dialog ID; we rewrite its text to whatever
# prompt makes sense (1-destination "X-bound ferry" or 2-destination "Where to?").
FERRY_PROMPT_DIALOG = {
    'SouthFigaro': 812,    # vanilla: "Nikeah-bound ferry..."
    'Nikeah':      810,    # vanilla: "South Figaro-bound ferry..."
    'Albrook':     1925,   # vanilla: Leo cargo-ship line ($0785)
}

# Per-port flavor dialog shown before the ferry prompt while the sea boss
# (event_bit.FINISHED_NARSHE_BATTLE) is undefeated. IDs sit in the vanilla
# Maduin/Madonna esper-world conversation block, which never plays in ruination.
# Placed in the gap between limited_heals (1467-1470) and SPRING_DIALOG_BASE
# (1480-1495) — outside WARP_DIALOG_IDS (1426-1460). See ARCHIVE.md
# "Ruination Mode — Dialog ID Reservations" for the full Maduin-block layout.
FERRY_FLAVOR_DIALOG = {
    'SouthFigaro': 0x05BF,  # 1471
    'Nikeah':      0x05C0,  # 1472
    'Albrook':     0x05C1,  # 1473
}

FERRY_FLAVOR_TOWN1_TEXT = (
    "We sent out a ship, but it was destroyed by a terrible monster!<end>"
)

# {town1} is replaced with the display name of the chosen TOWN1 port.
FERRY_FLAVOR_OTHER_TEXTS = [
    "A sailor from {town1} washed up... his ship was wrecked with all hands!<end>",
    "The waterways are guarded by a great beast! Can you help us?<end>",
]

# Vanilla "stay" return target — CA/5EB3 is just a single Return.
FERRY_STAY_RETURN_ADDR = 0xa5eb3

FERRY_DISABLED_MESSAGE = (
    "Some of us went out to map the sea, but no one returned.<end>"
)


def _ferry_disabled_patch(dialog_id):
    """4-byte field-event sequence: Display dialog, Return."""
    return bytes([0x4B, dialog_id & 0xFF, dialog_id >> 8, 0xFE])


def _ferry_build_prompt(src_port, destinations):
    """Return dialog text for the src_port sailor offering the given destinations."""
    if len(destinations) == 1:
        dst = FERRY_PORTS[destinations[0]]['display']
        return (
            f"{dst}-bound ferry."
            f"<line><choice> (Still need to shop.)"
            f"<line><choice> (Hop aboard?)<end>"
        )
    dst1 = FERRY_PORTS[destinations[0]]['display']
    dst2 = FERRY_PORTS[destinations[1]]['display']
    return (
        f"Where to?"
        f"<line><choice> (Still need to shop.)"
        f"<line><choice> ({dst1})"
        f"<line><choice> ({dst2})<end>"
    )


def _ferry_build_trip(src_port, dst_port, boss_pack_id=None):
    """Allocate a Bank.CA subroutine that runs the boat-trip animation."""
    src = FERRY_PORTS[src_port]
    dst = FERRY_PORTS[dst_port]

    # Do some math to determine route for animation.  Elbow is at (223, 200).
    elbow = [228, 205]  # [223, 200].  Change destinations to be w.r.t elbow.
    ANIMATION_XY = {
        'SouthFigaro': [-12, 0, direction.RIGHT],
        'Nikeah': [12, 0, direction.LEFT],
        'Albrook': [0, 11, direction.UP],
    }

    delta_xy_1 = [-ANIMATION_XY[src_port][a] for a in range(2)]  # first part of journey (positive is right/down)
    delta_xy_2 = [ANIMATION_XY[dst_port][a] for a in range(2)]  # second part of journey

    # Helper functions
    get_dir = lambda x: [direction.RIGHT, direction.LEFT, direction.DOWN, direction.UP][
        [x[0] > 0, x[0] < 0, x[1] > 0, x[1] < 0].index(True)]
    get_distance = lambda x: abs(x[x.index(0) - 1])

    code = [
        # Begin sea journey
        field.FadeOutSong(8),
        field.FadeOutScreen(),
        field.StartSong(0x3a),  # "Tide"
        field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
        field.LoadMap(map_id=0x001, x=ANIMATION_XY[src_port][0] + elbow[0], y=ANIMATION_XY[src_port][1] + elbow[1],
                      direction=ANIMATION_XY[src_port][2], default_music=False, entrance_event=False, airship=False,
                      fade_in=True),
        world.SetSpeed(field_entity.Speed.SLOW),
        world.BecomeShip(),
        world.HideMinimap(),
    ]

    # Go to elbow
    dist = get_distance(delta_xy_1)
    d_ix = get_dir(delta_xy_1)
    while dist > 8:
        code += [
            #vehicle.MoveForward(direction=get_dir(delta_xy_1), distance=8)  # This is the wrong code.  Need something more like field_entity.Move codes
            field_entity.Move(direction=d_ix, distance=8)
        ]
        dist -= 8
    if dist > 0:
        code += [
            field_entity.Move(direction=d_ix, distance=dist)
        ]
    # Sea Battle?  We don't have a background for it (0x0d = raft, 0x29 = airship wor).  Might add some nice danger.
    # Can we capture an unused boss & have it trigger 3/8 of the time, once?
    # We are using the "Kefka (Narshe)" boss for this, since Kefka@Narshe event is not used in Ruination.
    #   Ultros/Chupon --> Sealed Gate event
    #   DoomGaze --> Falcon event
    #   Kefka@Narshe --> Sea boss
    # So we can set event_bit.FINISHED_NARSHE_BATTLE to track it.
    #SHIP_BOSS_BATTLE_PROBABILITY = 0.375
    #skip_boss_chance = int(SHIP_BOSS_BATTLE_PROBABILITY * 255)
    #print(f'USING SEA BOSS BATTLE ID: {boss_pack_id}')
    if boss_pack_id is not None:
        code += [
            world.BranchIfEventBitSet(event_bit.FINISHED_NARSHE_BATTLE, "SKIP_BATTLE"),
            #vehicle.BranchProbability(skip_boss_chance, "SKIP_BATTLE"),
            #vehicle.InvokeBattle(pack=boss_pack_id, background=0x0d),  # Vehicle.InvokeBattle wasn't working.
            world.FadeLoadMap(map_id=0x009, direction=0, default_music=False, x=0, y=0, entrance_event=False,
                              fade_in=False),
            field.InvokeBattleType(pack=boss_pack_id, battle_type=field.BattleType.FRONT, background=0x0d),
            field.SetEventBit(event_bit.FINISHED_NARSHE_BATTLE),
            field.StartSong(0x3a),  # "Tide"
            field.LoadMap(map_id=0x001, x=elbow[0], y=elbow[1], direction=ANIMATION_XY[src_port][2],
                          default_music=False, entrance_event=False, airship=False, fade_in=True),
            world.SetSpeed(field_entity.Speed.SLOW),
            world.BecomeShip(),
            "SKIP_BATTLE",
        ]

    # Complete journey
    dist = get_distance(delta_xy_2)
    d_ix = get_dir(delta_xy_2)
    while dist > 8:
        code += [
            field_entity.Move(direction=d_ix, distance=8)
        ]
        dist -= 8
    if dist > 0:
        code += [
            field_entity.Move(direction=d_ix, distance=dist)
        ]

    code += [
        # Airship move for safety
        vehicle.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
        vehicle.LoadMap(0x01, direction.DOWN, default_music=False,
                        x=src['wor_dock'][0], y=src['wor_dock'][1],
                        fade_in=False, airship=True),
        vehicle.SetPosition(dst['wor_dock'][0], dst['wor_dock'][1]),
        vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        vehicle.FadeLoadMap(dst['dest_map'], dst['dest_dir'], default_music=True,
                            x=dst['dest_spawn'][0], y=dst['dest_spawn'][1],
                            fade_in=True, entrance_event=True),
        field.SetParentMap(0x01, direction.DOWN,
                           x=dst['wor_dock'][0], y=dst['wor_dock'][1] - 1),
        field.Return(),
    ]
    return Write(Bank.CA, code, f"ruin ferry {src_port}->{dst_port}").start_address


def _ferry_install_disabled(rom, dialogs):
    """Disable every port's NPC: each shows the disabled message and returns."""
    for port_name in FERRY_PORTS:
        dialog_id = FERRY_PROMPT_DIALOG[port_name]
        dialogs.set_text(dialog_id, FERRY_DISABLED_MESSAGE)
        rom.set_bytes(FERRY_PORTS[port_name]['npc_event_addr'],
                      _ferry_disabled_patch(dialog_id))


def _ferry_install_enabled(rom, dialogs, maps, mapped, args, boss_pack_id=None):
    """For each pair of mapped ports, build a trip subroutine and dispatch event."""
    # Promote the Albrook NPC if Albrook is on the network. Sprite is set here;
    # the visibility bit is flipped via init_event_bits in event/albrook_wob.py
    # (see Events.ruination_mod ordering — fix_ferry_connections runs before the
    # init_event_bits loop, so the bit-flip cannot live here).
    if 'Albrook' in mapped:
        port = FERRY_PORTS['Albrook']
        maps.get_npc(port['sailor_map'], port['sailor_npc_id']).sprite = port['sailor_sprite']

    # Pre-boss flavor dialog: pick one mapped port as TOWN1 (the "we sent out a
    # ship..." sailor); the other(s) get the alternative lines naming TOWN1.
    # When all three ports are mapped, the two non-TOWN1 sailors get distinct
    # alternative lines (one each, shuffled). Only mapped ports get text written.
    town1_port = random.choice(mapped)
    town1_display = FERRY_PORTS[town1_port]['display']
    other_ports = [p for p in mapped if p != town1_port]
    if len(other_ports) >= 2:
        other_texts = random.sample(FERRY_FLAVOR_OTHER_TEXTS, len(other_ports))
    else:
        other_texts = [random.choice(FERRY_FLAVOR_OTHER_TEXTS)]
    other_text_for = dict(zip(other_ports, other_texts))
    flavor_dialog = {}
    for port in mapped:
        flavor_id = FERRY_FLAVOR_DIALOG[port]
        if port == town1_port:
            text = FERRY_FLAVOR_TOWN1_TEXT
        else:
            text = other_text_for[port].format(town1=town1_display)
        dialogs.set_text(flavor_id, text)
        flavor_dialog[port] = flavor_id

    # Build all ordered trip subroutines we will need.
    trips = {}
    for src in mapped:
        for dst in mapped:
            if src == dst:
                continue
            trips[(src, dst)] = _ferry_build_trip(src, dst, boss_pack_id)

    # For each port, build a dispatch event (DialogBranch with stay + 1 or 2 boats)
    # and patch the NPC's event slot with a Branch into it.
    for src in mapped:
        destinations = [p for p in mapped if p != src]
        prompt_text = _ferry_build_prompt(src, destinations)
        dialog_id = FERRY_PROMPT_DIALOG[src]
        dialogs.set_text(dialog_id, prompt_text)

        dest1 = trips[(src, destinations[0])]
        dest2 = trips[(src, destinations[1])] if len(destinations) == 2 else None

        # DialogBranch returns (Dialog, _DialogBranch, Return). Choice 1 is the
        # "stay" option (matches vanilla "Still need to shop."), so we route it
        # to the bare-Return stub at FERRY_STAY_RETURN_ADDR.
        # Pre-boss: show flavor dialog before the prompt; skip once the sea boss
        # is defeated (event_bit.FINISHED_NARSHE_BATTLE).
        dispatch_code = [
            field.BranchIfEventBitSet(event_bit.FINISHED_NARSHE_BATTLE, "FERRY_PROMPT"),
            field.Dialog(flavor_dialog[src]),
            "FERRY_PROMPT",
            field.DialogBranch(dialog_id=dialog_id, dest1=FERRY_STAY_RETURN_ADDR,
                               dest2=dest1, dest3=dest2),
        ]
        space = Write(Bank.CA, dispatch_code, f"ruin ferry dispatch {src}")
        dispatch_addr = space.start_address

        # field.Branch is BranchIfEventBitClear(ALWAYS_CLEAR, dest) = 6 bytes.
        # The vanilla event slots all have >=12 bytes available (verified for
        # SF 0xa77d7=21B, Nikeah 0xa8cbb=31B, Albrook 0xbd1f3=18B).
        #patch = field.Branch(dispatch_addr)
        #opcode, patch_args = patch(None)
        #patch_bytes = bytes([opcode]) + bytes(patch_args)
        #rom.set_bytes(FERRY_PORTS[src]['npc_event_addr'], patch_bytes)
        space = Reserve(FERRY_PORTS[src]['npc_event_addr'], FERRY_PORTS[src]['npc_event_addr']+5, f"ruin ferry dispatch hook {src}")
        space.write(field.Branch(dispatch_addr))

    if args.debug:
        for (src, dst), addr in trips.items():
            print(f"Ferry: trip {src}->{dst} at {addr:#x}")


def fix_ferry_connections(rom, dialogs, maps, ruin_map, args, boss_pack_id=None):
    """Wire up the SF / Nikeah / Albrook ferry network for ruination mode.

    If 0 or 1 of the three ports has any reachable rooms on the map, every
    sailor shows a disabled message. If 2 or 3 are mapped, each mapped sailor
    offers travel to every other mapped port. The Albrook NPC is a generic
    sprite-16 NPC on map 0x14C that we promote to sprite 54 (sailor) and make
    visible via npc_bit 0x565 (the latter via init_event_bits in
    event/albrook_wob.py).

    Uses the rooms actually placed in each branch (not ruin_map.AreasUsed),
    because distribution can tag an area with a branch whose rooms already
    lived elsewhere — leaving the ferry enabled when a port has no reachable
    rooms on the map.
    """
    actual_areas_used = ruin_map.compute_actual_areas_used()
    mapped = [p for p in FERRY_PORTS if p in actual_areas_used]

    if args.debug:
        print(f"Ferry: mapped ports = {mapped}")

    if len(mapped) < 2:
        _ferry_install_disabled(rom, dialogs)
        if args.debug:
            print("Ferry: <2 ports mapped - all sailors disabled")
        return

    _ferry_install_enabled(rom, dialogs, maps, mapped, args, boss_pack_id)
