from event.event import *
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from data.rooms import room_data, ruination_dont_force, shared_exits
from data.walks import *
import random


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

# Inn cost multiplier for ruination mode
# Change this value to adjust how much inn costs are multiplied
INN_COST_MULTIPLIER = 2

CHARACTER_LOCKED_REWARDS = {
    # Only rewards that literally cannot be obtained without the character, and in areas that are accessible without them
    'TERRA': ['Whelk', 'Zozo'],  # Narshe, Zozo
    'LOCKE': ["Narshe WOR"],        # Narshe weapon shop
    'CELES': ["South Figaro"],   # South Figaro cell
    'SETZER': ["Kohlingen"],   # Kohlingen inn
    'STRAGO': ["Burning House"],  # Thamasa inn
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
    229: {"Mobliz WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Mobliz WoR.  Actually '237R' if interiors randomized.

    # LOCKE
    34: {"Narshe WOR": [RewardType.ESPER, RewardType.ITEM]},   # Narshe WOR weapon shop.  Actually '25R' if interiors are randomized.
    104: {"South Figaro Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # TunnelArmr spot
    537: {"Phoenix Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phoenix Cave (interior 1st room).  For outside platform: 'branch-pc'.  Need to modify exit: warp to esper world?

    # EDGAR
    'ruin-figarocastle': {"Figaro Castle WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],
                          "Figaro Castle WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Figaro Castle Throne Room + Engine Room checks
    532: {"Ancient Castle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Ancient Castle (dragon room).  AC starts at 520 or 'root-ac'.

    # SABIN
    'dc-1501': {"Imperial Camp": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Imperial Camp
    'ruin-baren-reward': {"Baren Falls": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Baren Falls, after boss but before shore
    220: {"Phantom Train": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Phantom Train Caboose... boss is room 202
    151: {"Mt. Kolts": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Kolts
    395: {"Collapsing House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Tzen WoR Collapsing house
    
    # CELES
    'ms-wor-58': {"South Figaro": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # South Figaro Basement  World of Ruin;  WOB is 'ms-wob-6'.
    'ms-wob-40': {"Opera House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Opera Disturbance WOB
    349: {"Magitek Factory_1": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 1
    354: {"Magitek Factory_2": [RewardType.ESPER, RewardType.ITEM]},  # Magitek Factory 2
    'ruin-mtek3': {"Magitek Factory_3": [RewardType.CHARACTER, RewardType.ESPER]},  # Magitek Factory 3, needs logical separation from Vector.  2nd boss where?
    
    # CYAN
    'ms-wob-18': {"Doma WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Doma Siege
    429: {"Doma WOR_2": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 1: stooges
    193: {"Doma WOR_1": [RewardType.CHARACTER, RewardType.ESPER]},  # Doma Dream 2: Wrexsoul
    'dc-76': {"Doma WOR_3": [RewardType.ESPER, RewardType.ITEM]},  # Doma Dream 3: throne (gated by Wrexsoul, though it's not a character so this doesn't affect gating)
    256: {"Mt. Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Mt Zozo
    
    # SHADOW
    'ms-wob-14': {"Gau Father House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Gau's Dad's House
    'ms-wob-1556': {"Floating Continent_1": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM],   # Floating Continent 1
                    "Floating Continent_2": [RewardType.ESPER, RewardType.ITEM],   # Floating Continent 2
                    "Floating Continent_3": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Floating Continent 3
    475: {"Veldt Cave WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Cave on the Veldt
    
    # GAU
    'wor-veldt': {"Veldt": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Veldt (WOR theme)
    'ruin-st-exit': {"Serpent Trench": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Serpent Trench, seeds logical separation from Nikeah.
    
    # SETZER
    'ms-wor-59': {"Kohlingen": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Kohlingen Inn (force WOR)
    'ruin-daryl': {"Daryl's Tomb": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Daryl's Tomb
    # 1: {"Doom Gaze": [RewardType.ESPER, RewardType.ITEM]},   # Doom Gaze, used elsewhere in -ruin
    
    # STRAGO
    'dc-75': {"Burning House": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},  # Burning House
    'ms-wor-69': {"Fanatic's Tower": [RewardType.CHARACTER, RewardType.ESPER]},   # Fanatics Tower
    'ms-wor-78': {"Ebot's Rock": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Ebot's Rock
    
    # RELM
    488: {"Esper Mountain": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Esper Mountain
    284: {"Owzer Mansion": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Owzer's Basement
    
    # MOG
    23: {"Lone Wolf": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Lone Wolf.  Move to WOR?
    65: {"Narshe Moogle Defense": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Moogle Defense WOR (need to update how this starts); 65 in WOB

    # UMARO
    368: {"Umaro's Cave": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Umaro's Den
    
    # GOGO
    363: {"Zone Eater": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Zone Eater
    
    # UNGATED
    22: {"Narshe Battle": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Kefka @ Narshe
    '41a': {"Tritoch": [RewardType.ESPER, RewardType.ITEM]},   # Tritoch
    'ms-wor-51': {"Tzen": [RewardType.ESPER, RewardType.ITEM]},   # Tzen thief (WOR).  WoB is 'ms-wob-33'
    'dc-73': {"Auction House_1": [RewardType.ESPER, RewardType.ITEM],
              "Auction House_2": [RewardType.ESPER, RewardType.ITEM]},   # Jidoor WoR.  WOB is 'ms-wob-28'

}

# HOW to deal with cross-branch transport?
#(1) don't allow it.  Force certain areas to be in the same branch:
forced_same_branch = {
    'Zozo': {'ZozoTower', 'MtZozo'},
    'Thamasa': {'VeldtCave', 'EbotsRock'},
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
    'CYAN': ['Doma', 'Zozo', 'MtZozo', 'Maranda'],
    'SHADOW': ['GauFatherHouse', 'FloatingContinent', 'VeldtCave', 'Thamasa'],
    'GAU': ['Veldt', 'CrescentMtn', 'Nikeah'],
    'SETZER': ['Kohlingen', 'DarylsTomb'],
    'STRAGO': ['Thamasa', 'FanaticsTower', 'EbotsRock'],
    'RELM': ['Jidoor', 'EsperMountain'],
    'MOG': ['Narshe'],
    'GOGO': ['ZoneEater'],
    'UMARO': ['UmarosCave'],
    'ALL': ['Coliseum', 'Albrook'],
    'EXTRA': ['ImperialCastle']
}

# All playable characters that can be obtained as rewards
ALL_CHARACTERS = ['TERRA', 'LOCKE', 'EDGAR', 'SABIN', 'CELES', 'CYAN', 'SHADOW',
                  'GAU', 'SETZER', 'STRAGO', 'RELM', 'MOG', 'GOGO', 'UMARO']

AREA_TYPES = {
    'TOWNS': ['Kohlingen', 'Jidoor', 'Maranda', 'Tzen', 'Albrook', 'Thamasa', 'Nikeah', 'Vector', 'SouthFigaro'],  # 'Mobliz', 'Narshe', # WOB only
}

# List of rooms associated with each named area
RUIN_ROOM_SETS = {
    'Doma': [421, 422, 423, 424, 425, 426, 427, 428, 429, 208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
                  432, 433, 184, 185, 186, 187, 188, '188B', 189, 190, 191, 192, 193, 'dc-76'],
    'UmarosCave': [364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368],  # root is in Narshe
    'EsperMountain': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500],  # 501 excluded: shares exit 1057 with ruin_terminus_2
    'PhantomTrain': ['ruin-201', 202, '203a', '203b', '203c', 204, '204b', '204c', 205, 206, '206a', '206b', 207, '207a',
                     '207b', 212, 213, '215a', '215b', 216, 220, 221], # 'ruin-phantomforest' if you want to include the forest + healing spring
    'SealedGate': [502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513],  # no worldmap connector '504a'; no sealed gate itself 514
    'SouthFigaroCave': [100, 101, 102, 103, 104, 105],
    'ReturnersHideout': ['ruin-returners', 'LeteRiver1', 'LeteCave1', 'LeteRiver2', 'LeteCave2', 'LeteRiver3'],  # Need to add raft return to Esper World
    'AncientCastle': [520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532],
    'Jidoor': ['dc-73', 277, 278, 279, 280, 281, 282, 283, 284],   # Including Owzer's Mansion
    'VeldtCave': [467, 468, 469, 470, 471, 472, 474, 475, 'ruin-thamasa'],  # It's OK to double rooms, we will check to make sure they don't actually map twice.
    'CrescentMtn': ['dc-23', '241a', 246, '241b', '247a', '247b', '247c', '241c', '241d', 'ruin-st-exit', 'ruin-nikeah'],
    'BarenFalls': ['dc-15', 'ruin-baren-reward', 'ruin-baren'],
    'Vector': [345, 346, 347, 349, 351, 352, 353, 354, 355, '355a', 'ruin-mtek3', 'ruin-vector'],
    'DarylsTomb': [377, 378, 379, 380, 381, 382, 383, 384, 386, 'ruin-daryl', 388, 389, 390, 391, 392, 393],
    'ZoneEater': [356, 357, 358, '358b', 359, '359b', 361, 362, 363],
    'MtKolts': [145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160],
    'Narshe': ['ruin-narshe', 36, '37a', 38, 40, 41, 42, 43, 44, 45, 'ruin-whelk', 47, 65, 49, 50, 51],   # Narshe WOR + northern caves (swap out WOB Whelk 46 --> 59) + snow battlefield + Tritoch + Umaro exit + moogle mines (swap out 48 --> 65 for moogle defense)
    'Zozo': ['ruin-zozo', '294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r'],
    'ZozoTower': [297, 298, 299, 300, 302, '303a', '303b', 304, 310, 311, 312, 313],
    'MtZozo': [250, 251, 252, 253, 254, 255, 256],

    'SouthFigaro': ['ms-wor-58'],
    'GauFatherHouse': ['ms-wob-14'],  # use WOB for shadow check & vendor.  Change tileset, perhaps?
    'Thamasa': ['ruin-thamasa'],  # including STRAGO-locked burning house
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

    'ImperialCastle': [331],  # Extra hub room if needed
}

# Maps ruination area names to shop IDs from data/shop_map_names.py
# Used to track which shops are accessible in ruination mode for dried meat assignment
AREA_SHOPS = {
    'Kohlingen': [67, 68, 69],         # WOR shops (items/weapons/armor)
    'Nikeah': [58, 59, 60, 61],        # WOR shops
    'Thamasa': [74, 75, 76, 77],       # WOR shops
    'SouthFigaro': [62, 63, 64, 65],   # WOR shops
    'Albrook': [50, 51, 52, 53],       # WOR shops
    'Tzen': [54, 55, 56, 57],          # WOR shops
    'Jidoor': [78, 79, 80, 81],        # WOR shops (includes Owzer's mansion)
    'Maranda': [82, 83],               # WOR shops
    'FigaroCastle': [67, 86],          # WOR shops (left/right)
    'ReturnersHideout': [38],          # Item shop
    'PhantomTrain': [87],              # Vendor
    'GauFatherHouse': [41],            # Vendor (WOB map used in ruination)
}

RUIN_TERMINI = ['ruin_terminus_1', 'ruin_terminus_2', 'ruin_terminus_3']  # list of terminal rooms for branches


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
        self.classify_rooms(rooms)

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
                print('CUSTOM add pit 3039 to', hub_room_id, '!', hub_room.count, hub_room.pits)
            self.rooms.reindex_room(hub_room_id)

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
            print('Looking for check rooms...', self.check_rooms)
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
                print(f'  [{step_name}] Hub network totals: doors={total_doors}, traps={total_traps}, pits={total_pits}')
                print(f'  [{step_name}] Hub {hub_id}: doors={hub_doors}, traps={hub_traps}, pits={hub_pits}')
                print(f'  [{step_name}] Upstream nodes: {list(upstream)}')
                print(f'  [{step_name}] Downstream nodes: {list(downstream)}')

        if remaining_doors is not None and dead_ends is not None:
            door_count = len(remaining_doors)
            dead_end_count = len(dead_ends)
            excess = door_count - dead_end_count

            if self.verbose:
                print(f'  [{step_name}] remaining_doors={door_count}, dead_ends={dead_end_count}, excess={excess}')

            if excess > 0 and excess % 2 == 1:
                issues.append(f'Odd excess doors ({excess}): will have orphan door after pairing')

        if all_traps is not None and all_pits is not None:
            trap_count = len(all_traps)
            pit_count = len(all_pits)

            if self.verbose:
                print(f'  [{step_name}] all_traps={trap_count}, all_pits={pit_count}')

            if trap_count > pit_count:
                issues.append(f'More traps ({trap_count}) than pits ({pit_count})')

        if issues and self.verbose:
            print(f'  [{step_name}] POTENTIAL ISSUES: {issues}')

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
        2a. If unconnected door in hub/upstream, can connect to PIDO room
        3. Can connect to upstream pit ONLY IF loop compression leaves exits
        GLOBAL: Never make a connection that leaves the branch with zero exits

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

            # === RULE 2a: PIDO rooms (if hub/upstream has doors) ===
            if room_type == 'PIDO' or (len(room_pits) > 0 and len(room_doors) > 0 and len(room_traps) == 0):
                if hub_upstream_doors > 0:
                    # Hub/upstream has doors, so this PIDO room can connect back
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
        if current_total_exits > 1:
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
        # GLOBAL PROTECTION: Loop connections don't add new exits to the branch.
        # They consume TWO exits: the source door AND the target door in hub/upstream.
        # Only allow if the branch would still have exits after using both doors.
        if current_total_exits > 2:
            for h_id in hub_and_upstream:
                h_room = self.rooms.get_room(h_id)
                if h_room:
                    h_doors = [d for d in h_room.doors if d not in self.protected]
                    # Rule 0: check not last entrance (must have entrances remaining)
                    hub_doors, hub_pits = self.count_entrances_in_region(hub_and_upstream)
                    total_entrances = hub_doors + hub_pits
                    if total_entrances > 1:  # Leave at least one entrance
                        for d in h_doors:
                            if d != door_exit:  # Don't connect to self
                                valid_doors.append(d)

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
            print('\t=== NO DOORS FOR TERMINUS FIX ===')
            print(f'\tTerminus {self.terminus} not merged, but network has no doors')
            print(f'\tAvailable traps: {all_traps}')
            print(f'\tSearching for room with pit, door, and another exit...')

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
                    print(f'\tFound suitable room in network: {room_id}')
                    print(f'\t  pits={unprotected_pits}, doors={unprotected_doors}, traps={unprotected_traps}')
                break

        # If no suitable room in network, check reserve areas
        if suitable_room is None and reserve_areas is not None:
            if self.verbose:
                print('\tNo suitable room in network, checking reserve areas...')

            for area_name, area_rooms in reserve_areas:
                for room_id in area_rooms:
                    if room_id in room_data:
                        data = room_data[room_id]
                        doors = list(data[0]) if len(data) > 0 else []
                        traps = list(data[1]) if len(data) > 1 else []
                        pits = list(data[2]) if len(data) > 2 else []

                        # Need: at least 1 pit, at least 1 door, at least 1 other exit
                        total_exits = len(doors) + len(traps)
                        if len(pits) >= 1 and len(doors) >= 1 and total_exits >= 2:
                            # Add this room to the network
                            self.add_room(room_id)
                            suitable_room = room_id
                            if self.verbose:
                                print(f'\tAdded suitable room from area {area_name}: {room_id}')
                                print(f'\t  pits={pits}, doors={doors}, traps={traps}')
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
            print(f'\tConnecting trap {selected_trap} --> pit {selected_pit} (room {suitable_room})')

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
            print(f'\tAfter fix: network now has {len(new_doors)} doors')

    def finalize_map(self, reserve_areas=None):
        if self.verbose:
            print('Closing branch...')

        self.ForceConnections(forced_connections)

        if self.verbose:
            print(f'\tProtected elements after ForceConnections: {sorted(self.protected)}')

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
                print(f'\n=== Finalize iteration {finalize_iteration} (new elements were unlocked) ===\n')

            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            if self.verbose:
                print('\thub:', hub_id, hub.count)

            # (1) Count trapdoors/pits connected to hub.  If trapdoors > pits, connect traps to rooms with (# pits > # traps).
            # Filter out protected elements to avoid using forced connection destinations
            all_pits = [p for p in hub.pits if p not in self.protected]
            all_traps = [t for t in hub.traps if t not in self.protected]

            # Show what was filtered
            filtered_pits = [p for p in hub.pits if p in self.protected]
            filtered_traps = [t for t in hub.traps if t in self.protected]
            if self.verbose and (filtered_pits or filtered_traps):
                print(f'\t(hub) Filtered out protected - pits: {filtered_pits}, traps: {filtered_traps}')

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
                print('\tpits:', all_pits)
                print('\ttraps:', all_traps)

            while len(all_traps) > len(all_pits):
                # Find unconnected rooms with more pits than traps
                if self.verbose:
                    print('(1) assessing nodes for (more pits than traps):')
                winner = ''
                diff = 0
                for n in self.net.nodes:
                    if n not in upstream and n not in downstream and n != hub_id:
                        r = self.rooms.get_room(n)
                        if self.verbose:
                            print('\t',n, r.count, r.doors, r.traps, r.pits, r.keys, r.locks)
                        # Use only unprotected pits and traps for comparison
                        unprotected_pits = [p for p in r.pits if p not in self.protected]
                        unprotected_traps = [t for t in r.traps if t not in self.protected]
                        if (len(unprotected_pits) - len(unprotected_traps)) > diff:
                            diff = len(unprotected_pits) - len(unprotected_traps)
                            winner = n

                # connect a hub trapdoor to this node
                this_exit = random.choice(all_traps)
                room = self.rooms.get_room(winner)
                unprotected_room_pits = [p for p in room.pits if p not in self.protected]
                this_entr = random.choice(unprotected_room_pits)
                if self.verbose:
                    protected_in_room = [p for p in room.pits if p in self.protected]
                    print(f'(1) selected {winner}: traps={room.traps}, pits={room.pits}')
                    if protected_in_room:
                        print(f'    (filtered protected pits: {protected_in_room})')
                    print(f'(1) connecting {this_exit} --> {this_entr}')

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
                print('(2) delta values:', delta)
            delta.sort(key=lambda x: x[0])
            while len(delta) > 0:
                value = delta.pop()
                node = value[1]
                room = self.rooms.get_room(node)
                if self.verbose:
                    print('(2) selected', node, '(delta = ', value[0], '): ', room.count, room.doors, room.traps, room.pits)

                # Skip rooms with no exits (only pit entrances) - they can't connect upstream
                # Their pits will be connected when traps are processed in step (3)
                if len(room.doors) == 0 and len(room.traps) == 0:
                    if self.verbose:
                        print('(2) skipping - room has no exits (pit-only)')
                    continue

                upstream_doors = [d for d in hub.doors if d not in self.protected]
                upstream_pits = [p for p in hub.pits if p not in self.protected]
                for node in upstream:
                    uproom = self.rooms.get_room(node)
                    upstream_pits.extend([p for p in uproom.pits if p not in self.protected])

                this_conn = None
                unprotected_room_traps = [t for t in room.traps if t not in self.protected]
                unprotected_room_doors = [d for d in room.doors if d not in self.protected]
                if len(unprotected_room_traps) > 0:
                    this_exit = random.choice(unprotected_room_traps)
                    if len(upstream_pits) > 0:
                        this_conn = random.choice(upstream_pits)

                if this_conn is None and len(unprotected_room_doors) > 0:
                    this_exit = random.choice(unprotected_room_doors)
                    if len(upstream_doors) > 0:
                        this_conn = random.choice(upstream_doors)

                if this_conn is None:
                    # A thing can happen here where the downstream has only a door-out, but the upstream has only pit-in (or vice versa).
                    # In such a case, we can look at unused rooms, find a converter, attach it, and try again.
                    available_nodes = [n for n in self.net.nodes if n not in self.dead_ends and n != hub_id]
                    if len(unprotected_room_traps) > 0 and len(upstream_pits) == 0 and len(upstream_doors) > 0:
                        # Need a pit-in, door-out converter
                        pido = []
                        if self.verbose:
                            print('\t\tlooking for available pido nodes:')
                        for node_id in available_nodes:
                            node = self.rooms.get_room(node_id)
                            unprotected_node_pits = [p for p in node.pits if p not in self.protected]
                            unprotected_node_traps = [t for t in node.traps if t not in self.protected]
                            unprotected_node_doors = [d for d in node.doors if d not in self.protected]
                            if len(unprotected_node_pits) > 0 and len(unprotected_node_doors) > 0 and len(unprotected_node_pits) > len(unprotected_node_traps):
                                pido.append(node_id)
                                if self.verbose:
                                    print('\t\t\t', node_id, ': ', node.count)

                        if len(pido) > 0:
                            pido_room_id = random.choice(pido)
                            pido_room = self.rooms.get_room(pido_room_id)
                            # Select an unprotected pit from the converter room as the connection target
                            unprotected_pido_pits = [p for p in pido_room.pits if p not in self.protected]
                            this_conn = random.choice(unprotected_pido_pits)

                    elif len(unprotected_room_doors) > 0 and len(upstream_doors) == 0 and len(upstream_pits) > 0:
                        # Need a door-in, trap-out converter
                        dito = []
                        if self.verbose:
                            print('\t\tlooking for available dito nodes:')
                        for node_id in available_nodes:
                            node = self.rooms.get_room(node_id)
                            unprotected_node_traps = [t for t in node.traps if t not in self.protected]
                            unprotected_node_pits = [p for p in node.pits if p not in self.protected]
                            unprotected_node_doors = [d for d in node.doors if d not in self.protected]
                            if len(unprotected_node_traps) > 0 and len(unprotected_node_doors) > 0 and len(unprotected_node_traps) > len(unprotected_node_pits):
                                dito.append(node_id)
                                if self.verbose:
                                    print('\t\t\t', node_id, ': ', node.count)

                        if len(dito) > 0:
                            dito_room_id = random.choice(dito)
                            dito_room = self.rooms.get_room(dito_room_id)
                            # Select an unprotected door from the converter room as the connection target
                            unprotected_dito_doors = [d for d in dito_room.doors if d not in self.protected]
                            this_conn = random.choice(unprotected_dito_doors)

                if this_conn is None:
                    # There is no solution.
                    print('Found an inescapable downstream node!')
                    raise Exception

                if self.verbose:
                    print('(2) connecting', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)

                # Update hub, upstream, downstream, delta
                hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
                upstream = self.get_upstream_nodes(hub_id)
                downstream = self.get_downstream_nodes(hub_id)
                delta = []
                for node in downstream:
                    room = self.rooms.get_room(node)
                    entrance_count = len(room.doors) + len(room.pits)
                    exit_count = len(room.doors) + len(room.traps)
                    delta.append((entrance_count - exit_count, node))
                if self.verbose:
                    print('(2) delta values:', delta)
                delta.sort(key=lambda x: x[0])

            # (3) Connect any remaining trapdoors/pits
            # Collect traps and pits from the ENTIRE network (hub + upstream + downstream).
            # This is important because keys applied during connect() can unlock traps in any room,
            # not just the hub. All unlocked traps must be connected to avoid "escape" routes.
            remaining_traps, remaining_pits = self.collect_network_traps_and_pits()
            while len(remaining_traps) > 0 and len(remaining_pits) > 0:
                random.shuffle(remaining_pits)
                if self.verbose:
                    print('(3) remaining traps:', remaining_traps, '; pits: ', remaining_pits)
                this_exit = remaining_traps.pop()
                this_conn = remaining_pits.pop()
                if self.verbose:
                    print('(3) connecting:', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)
                # Re-collect from entire network - keys applied during connect() may unlock new traps
                remaining_traps, remaining_pits = self.collect_network_traps_and_pits()

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
                print('(4) remaining doors:', remaining_doors)
            terminus = self.rooms.get_room(self.terminus)
            if terminus is not None and len(remaining_doors) > 0:
                # Terminus is still a separate room and we have doors to connect it
                this_exit = remaining_doors.pop()
                if self.terminus in self.dead_ends:
                    self.dead_ends.remove(self.terminus)
                unprotected_terminus_doors = [d for d in terminus.doors if d not in self.protected]
                this_conn = unprotected_terminus_doors.pop() if unprotected_terminus_doors else terminus.doors.pop()
                if self.verbose:
                    print('(4) connecting terminus:', this_exit , '-->', this_conn)
                self.connect(this_exit, this_conn)
            elif terminus is not None and len(remaining_doors) == 0:
                # Terminus exists but no hub doors available - add terminus to dead ends for step 6
                if self.terminus not in self.dead_ends:
                    self.dead_ends.append(self.terminus)
                if self.verbose:
                    print('(4) no hub doors to connect terminus, deferring to step 6')
            elif self.verbose:
                print('(4) terminus already merged into hub, skipping')

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
                    print('(5) doors in hub:', len(remaining_doors), '.  dead ends:', len(self.dead_ends))
                this_exit = remaining_doors.pop()
                this_conn = remaining_doors.pop()
                if self.verbose:
                    print('(5) connecting doors in hub:', this_exit, '-->', this_conn)
                self.connect(this_exit, this_conn)

            # (5b) Handle orphan door situation: we have more doors than dead ends but can't pair them
            if len(remaining_doors) > len(self.dead_ends):
                orphan_count = len(remaining_doors) - len(self.dead_ends)
                if self.verbose:
                    print(f'(5b) orphan door situation: {orphan_count} excess door(s), searching for available rooms')

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
                                print(f'(5b) connecting orphan door {this_exit} --> room {room_id} door {this_conn}')
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
                                        print(f'(5b) fallback: connecting orphan {this_exit} --> {this_conn} in {node}')
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
            # Pre-check: we need enough dead ends for remaining doors
            if len(remaining_doors) > len(self.dead_ends):
                viz = self.visualize_branch_topology()
                raise RuntimeError(
                    f'finalize_map step 6: More remaining doors ({len(remaining_doors)}) than '
                    f'dead ends ({len(self.dead_ends)}). remaining_doors={remaining_doors}, '
                    f'dead_ends={self.dead_ends}. This indicates an imbalance from earlier steps.\n'
                    f'{viz}'
                )

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
                print('(6) remaining dead ends:', selected_dead_ends)
                print(f'(6) partitioned: {len(dead_ends_with_keys)} with keys, {len(dead_ends_without_keys)} without keys')

            # CRITICAL: The last dead end connected must NOT have a key.
            # If all selected dead ends have keys, we need to find a keyless one from remaining pool.
            if len(dead_ends_without_keys) == 0 and len(self.dead_ends) > 0:
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
                            print(f'(6) swapped key-bearing {swapped_out} for keyless {candidate_id}')
                        break

            if len(dead_ends_without_keys) == 0:
                # All dead ends have keys - this is risky but we must proceed
                if self.verbose:
                    print('(6) WARNING: All available dead ends have keys!')

            # Order: key-bearing first, keyless last (ensures last connection is safe)
            ordered_dead_ends = dead_ends_with_keys + dead_ends_without_keys
            random.shuffle(remaining_doors)

            for this_exit in remaining_doors:
                room_id = ordered_dead_ends.pop(0)
                room = self.rooms.get_room(room_id)
                unprotected_room_doors = [d for d in room.doors if d not in self.protected]
                this_conn = unprotected_room_doors.pop() if unprotected_room_doors else room.doors.pop()
                if self.verbose:
                    has_keys = room and len(room.keys) > 0
                    print(f'(6) connecting dead ends: {this_exit} --> {this_conn} (has_keys={has_keys})')
                self.connect(this_exit, this_conn)

                # Check if this connection unlocked new elements via key application.
                # If so, break IMMEDIATELY to preserve remaining entrances for the new elements.
                check_traps, _, check_doors = self.collect_network_traps_and_pits(
                    include_doors=True, exclude_upstream_doors=True)
                if len(check_traps) > 0 or len(check_doors) > 0:
                    if self.verbose:
                        print(f'(6) Key unlocked new elements! Breaking early to preserve entrances.')
                        print(f'    New traps: {check_traps}, New doors: {check_doors}')
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
                print(f'\nNew elements unlocked: {len(new_traps)} traps, {len(new_doors)} doors')
                if new_traps:
                    print(f'    traps: {new_traps}')
                if new_doors:
                    print(f'    doors: {new_doors}')
                print('Restarting finalization from step 1...\n')

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

        if self.verbose:
            print('... closing branch complete!')

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
        2a. If unconnected door in hub/upstream, can connect downstream trap to PIDO room
        2b. If unconnected pit in hub/upstream, can connect downstream door to DITO room
        3. Only connect downstream trap to pit in its local upstream (not hub's upstream)
           IF the resulting compressed loop has another exit
        """
        # === STEP 0: Analyze branch topology ===
        topology = self.classify_topology()
        if topology is None:
            # No hub yet - fall back to simple behavior
            if self.verbose:
                print('\tNo hub found, using simple extension')
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
            print(f'\t=== LOCATION-AWARE EXTENSION ===')
            print(f'\tActive room: {self.active} (level {active_level})')
            print(f'\tHub+Upstream: {hub_and_upstream}')
            print(f'\tUpstream: {upstream}, Downstream: {downstream}')

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
                print(f'\tForced exit: {this_exit} --> {this_conn}')
            return this_exit, this_conn

        # === STEP 2: Collect exits from the active path ===
        # Prioritize exits from the most downstream rooms (deepest in the tree)
        available_exits = {'doors': [], 'traps': []}

        if len(downstream) == 0:
            available_exits['doors'] = [d for d in active_room.doors if d not in self.protected]
            available_exits['traps'] = [t for t in active_room.traps if t not in self.protected]
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
                    available_exits['doors'].extend([d for d in room.doors if d not in self.protected])
                    available_exits['traps'].extend([t for t in room.traps if t not in self.protected])
            exit_room_id = list(deepest_rooms)[0] if deepest_rooms else self.active

        if self.verbose:
            print(f'\tAvailable exits: {len(available_exits["doors"])} doors, {len(available_exits["traps"])} traps')

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
            print(f'\tTarget availability: pits={trap_targets_exist}, doors={door_targets_exist}')

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
                print(f'\t{exit_type}: {len(all_exits)} exits to evaluate')

            # Shuffle and try each exit
            random.shuffle(all_exits)
            for exit_id, exit_room_id in all_exits:
                # Find valid targets - this method checks if each potential destination
                # would leave the branch with exits (handles unconnected rooms, loops, etc.)
                if exit_type == 'traps':
                    valid_targets = self.get_valid_pit_targets(exit_id, exit_room_id, topology)
                else:
                    valid_targets = self.get_valid_door_targets(
                        exit_id, exit_room_id, topology,
                        available_doors=len(available_exits['doors']),
                        available_traps=len(available_exits['traps'])
                    )

                if self.verbose:
                    print(f'\t\tExit {exit_id}: {len(valid_targets)} valid targets')

                if len(valid_targets) > 0:
                    this_conn = random.choice(valid_targets)
                    if self.verbose:
                        conn_room = self.rooms.get_room_from_element(this_conn)
                        conn_room_id = conn_room.id if conn_room else 'unknown'
                        print(f'\t\tSelected: {exit_id} --> {this_conn} (room {conn_room_id})')
                    self.last_stuck_reason = StuckReason.NONE
                    return exit_id, this_conn

        # === STEP 5: All strategies exhausted ===
        self._diagnose_stuck_reason(available_exits, topology)

        if self.verbose:
            print(f'\tBranch extension failed. Reason: {self.last_stuck_reason}')

        return None, None

    def _extend_branch_path_simple(self):
        """Simple extension when no topology analysis is possible (no hub yet)."""
        active_room = self.rooms.get_room(self.active)
        if active_room is None:
            self.last_stuck_reason = StuckReason.NO_EXITS
            return None, None

        # Try doors first
        doors = [d for d in active_room.doors if d not in self.protected]
        if len(doors) > 0:
            exit_id = random.choice(doors)
            # Find a door to connect to
            for room_id in self.net.nodes:
                if room_id == self.active:
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
            print('\tActive room: ', self.active, '.\n\tUpstream nodes: ', upstream,
                  '\n\tDownstream nodes: ', downstream,
                  '\n\tAll entrances: ', all_entrances)
        hub_is_upstream = len([n for n in upstream if 'ruin_hub_' in str(n)]) > 0
        if hub_is_upstream and self.verbose:
            print('\tHub is upstream!')
        for node in upstream:
            room = self.rooms.get_room(node)
            all_entrances += list(room.doors) + list(room.pits)

        allow_traps = len(all_entrances) >= 1
        dito_ok = len(
            all_entrances) >= 2  # a door-in, trap-out room effectively replaces a door (entrance) with a trap (not entrance), so an extra entrance is required
        if self.verbose and not allow_traps:
            print('\ttraps not allowed!')
        elif self.verbose:
            print('\ttraps allowed!')

        # Look at unconnected hubs.
        currently_used = [self.active] + list(downstream) + list(upstream)
        if self.verbose:
            print('\tCurrently used rooms:', currently_used)
        new_hub_door_conns = self.get_available_hub_connections(element_type=0, excluded=currently_used,
                                                                  dito_ok=dito_ok)
        new_hub_pit_conns = self.get_available_hub_connections(element_type=1, excluded=currently_used)
        # If hub is upstream, possibly allow connecting back to the hub (closing the loop)
        if hub_is_upstream:
            # Requirements: total exits after connection > 0
            uppaths = self.get_upstream_paths(self.active)
            for path in uppaths:
                if self.verbose:
                    print('\tchecking upstream path:', path)
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
                            print('\t\tTrapdoor condition met at', node_id)
                            tracker[0] = True
                        if self.verbose:
                            print('\t\tAdding', node_id, node.pits)
                    if (path_door_count + path_trap_count) > 2:
                        # We've met the condition for door connections.  Add doors.
                        new_hub_door_conns.update(node.doors)
                        if self.verbose and tracker[1] is False:
                            print('\t\tDoor condition met at', node_id)
                            tracker[1] = True
                        if self.verbose:
                            print('\t\tAdding', node_id, node.doors)

        if self.verbose:
            print('\tCollected available hub connections:')
            print('\t\tdoors:', new_hub_door_conns)
            print('\t\tpits:', new_hub_pit_conns)

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
            print('\tCollected available active room exits:', len(all_exits))
            print('\t\t', all_exits)

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
                    print('\tInstead using rooms with checks (doors):', len(all_exits))
                    print('\t\t', all_exits)
            elif len(check_pit_cons) > 0 and allow_traps:
                all_exits += list(active_room.traps)
                available_connections[1] += check_pit_cons
                if self.verbose:
                    print('\tInstead using rooms with checks (traps):', len(all_exits))
                    print('\t\t', all_exits)
            else:
                if self.verbose:
                    print('No legal exits found on branch!')
                legal_exits = False

        # If any exits are forced, apply them
        if legal_exits:
            forced_exits = [e for e in all_exits if e in forced_connections.keys()]
            if len(forced_exits) > 0:
                this_exit = forced_exits.pop()
                this_conn = forced_connections[this_exit][0]
                if self.verbose:
                    print('Found forced exit!', this_exit, '-->', this_conn)
            else:
                this_exit = random.choice(all_exits)
                this_type = active_room.element_type(this_exit)
                if self.verbose:
                    print('All allowed exits:', all_exits, '.  Choose: ', this_exit, '(type ', this_type, ')')
                # Reconstruct available connections for this exit?

                if this_exit in available_connections[this_type]:
                    available_connections[this_type].remove(this_exit)
                this_conn = random.choice(available_connections[this_type])
                if self.verbose:
                    print('Available connections:', available_connections[this_type], '. Choose: ', this_conn)

        else:
            this_exit = None
            this_conn = None

        return this_exit, this_conn

    def check_for_rewards(self, this_conn):
        # Look at the room(s) being connected & return any rewards found
        conn_room = self.rooms.get_room_from_element(this_conn)
        downstream = self.get_downstream_nodes(conn_room.id)
        if self.verbose:
            print('Looking for reward in room', conn_room.id, '...')
        if conn_room.id in self.check_rooms:
            reward_room = conn_room.id
        elif len([n for n in downstream if n in self.check_rooms]) > 0:
            # Reward room can be downstream if there's forced connections in/out
            reward_room = [n for n in downstream if n in self.check_rooms][0]
        else:
            reward_room = None

        if reward_room is not None:
            rewards = [(k, ROOM_REWARD[reward_room][k]) for k in ROOM_REWARD[reward_room].keys()]
            if self.verbose:
                print('Found a reward! ', [(r[0], r[1].possible_types) for r in rewards], 'in room',
                      reward_room)

            # Remove check room from the list
            self.check_rooms.remove(reward_room)

            return rewards

        else:
            return None


class ruination_map():
    # Class to organize data for mapping out ruination mode branches

    def __init__(self, args, starting_party, verbose=False):
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
        self.accessible_shops = []  # list of shop IDs that are accessible (for dried meat assignment)

        self.args = args

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
            print('Requested: ', self.Requested[0], 'characters, ', self.Requested[1], 'espers')

        # PRE-PLANNING PHASE: Determine which characters will be obtained and reserve areas
        self.planned_characters, self.reserve_characters, self.dead_checks_allowed = \
            self.pre_plan_character_acquisition()

        if self.verbose:
            print('Pre-plan: Will obtain characters:', self.planned_characters)
            print('Pre-plan: Reserve characters (for extra areas):', self.reserve_characters)
            print('Pre-plan: Dead checks allowed:', self.dead_checks_allowed)

        # Assemble initial areas from starting party + planned characters
        initial_areas = set()
        for character in self.PARTY:
            initial_areas.update(CHARACTER_AREAS.get(character, []))
        if self.verbose:
            print('Areas used: ', initial_areas)

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
            print('Rewards available: ', self.RewardsAvailable)

        # Apply keys to branches
        for branch in self.branches:
            for k in self.keychain:
                branch.apply_key(k)

        #print(branch.original_room_ids)

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
            print(f'Pre-plan: Planned areas have {total_checks} checks, '
                  f'{total_character_slots} character slots, {total_esper_slots} esper slots')

        # Check if we have enough esper slots after accounting for character slots
        # We need espers + planned characters, since character slots can't be used for espers
        while total_esper_slots < self.Requested[1] + len(planned_characters) and len(remaining_characters) > 0:
            # Add another character to get more areas/esper slots
            new_char = remaining_characters.pop(0)
            planned_characters.append(new_char)
            new_areas = CHARACTER_AREAS.get(new_char, [])

            if self.verbose:
                print(f'Pre-plan: Adding {new_char} to get more esper slots (areas: {new_areas})')

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
                    rooms = RUIN_ROOM_SETS[area_name]
                    hub_potential = calc_hub_potential(rooms)
                    reserve_areas.append((area_name, rooms, hub_potential, len(rooms)))

        # Always include EXTRA areas (like ImperialCastle) if not already used
        for area_name in CHARACTER_AREAS.get('EXTRA', []):
            if area_name not in self.AreasUsed and area_name in RUIN_ROOM_SETS:
                # Check if already added from reserve characters
                if not any(a[0] == area_name for a in reserve_areas):
                    rooms = RUIN_ROOM_SETS[area_name]
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
                            print('Forced same branch:', a, partner, branch_index)
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
                                print(f'\tPriority: Assigning {area} to stuck branch {branch_id} (has PIDO rooms)')
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
                                print(f'\tPriority: Assigning {area} to stuck branch {branch_id} (has hub rooms)')
                            branch_areas[branch_id].add(area)
                            self.AreasUsed[area] = branch_id
                            remaining_areas.remove(area)
                            break

            # Update areas list to only include remaining unassigned areas
            areas = remaining_areas

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
                        print('\t\t# rooms on each branch: ', num_rooms)
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
            print('Distributed areas:')
            for i, b in enumerate(branch_areas):
                print('\t', i, ': ', b)

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
                    process_me = True
                    # Check if this reward is locked by a character, and if we have that character.
                    if reward_id in REWARDS_LOCKED_BY_CHARACTER.keys():
                        lock_char = REWARDS_LOCKED_BY_CHARACTER[reward_id]
                        if lock_char not in self.keychain:
                            process_me = False
                    if process_me:
                        self.branch_checks[which_branch].append(reward_id)
                        reward = ROOM_REWARD[room][reward_id]
                        # print(reward_id, i, this_type.possible_types)
                        if reward.possible_types & RewardType.CHARACTER:
                            self.RewardsAvailable[0] += 1
                        if reward.possible_types & RewardType.ESPER:
                            self.RewardsAvailable[1] += 1

        if self.verbose:
            print('Checks available:')
            for i, b in enumerate(self.branch_checks):
                print('\t', i, ': ', b)

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
                                    print(f'\tFound PIDO room {room_id} for stuck branch {i}')
                                should_unstick = True
                                break
                    elif stuck_reason == StuckReason.NO_HUB:
                        # Branch needs a hub room - check if any new room is a hub
                        for room_id in branch_rooms[i]:
                            room = branch.rooms.get_room(room_id)
                            if room and _room_has_hub_potential(room):
                                if self.verbose:
                                    print(f'\tFound hub room {room_id} for stuck branch {i}')
                                should_unstick = True
                                break
                    else:
                        # For other reasons, check if branch now has a hub (general unsticking)
                        if branch.has_a_hub():
                            should_unstick = True

                    if should_unstick:
                        if self.verbose:
                            print(f'\tUnsticking branch {i} - received helpful areas (was stuck: {stuck_reason})')
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
                                if reward_name not in self.branch_checks[branch_id]:
                                    self.branch_checks[branch_id].append(reward_name)
                                    # Also update RewardsAvailable
                                    reward_slot = ROOM_REWARD[room_id][reward_name]
                                    if reward_slot.possible_types & RewardType.CHARACTER:
                                        self.RewardsAvailable[0] += 1
                                    if reward_slot.possible_types & RewardType.ESPER:
                                        self.RewardsAvailable[1] += 1
                                    if self.verbose:
                                        print(f'\tUnlocked reward {reward_name} added to branch {branch_id} checks')
                                break

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
        # Quick check: if Gau is not in planned characters, no need for special Veldt handling
        if 'GAU' not in self.planned_characters:
            if self.verbose:
                print('Gau not in planned characters, all accessible shops valid for dried meat')
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
                        print(f'Veldt character: {veldt_char_name} (ID: {veldt_char_id})')
                    break

        # If no character at Veldt (or Veldt not in map), all accessible shops are valid
        if veldt_char_id is None:
            if self.verbose:
                print('No character at Veldt, all accessible shops valid for dried meat')
            return self.accessible_shops[:]

        # Find all characters that depend on the Veldt character
        veldt_gated_chars = set()
        for char_id in range(len(characters.DEFAULT_NAME)):
            # Check if veldt_char_id is in this character's dependency path
            if veldt_char_id in characters.character_paths[char_id]:
                veldt_gated_chars.add(char_id)
                if self.verbose:
                    print(f'  {characters.DEFAULT_NAME[char_id]} is gated by Veldt character')

        # Collect areas unlocked by Veldt-gated characters
        veldt_gated_areas = set()
        for char_id in veldt_gated_chars:
            char_name = characters.DEFAULT_NAME[char_id]
            if char_name in CHARACTER_AREAS:
                veldt_gated_areas.update(CHARACTER_AREAS[char_name])

        if self.verbose and veldt_gated_areas:
            print(f'Veldt-gated areas: {veldt_gated_areas}')

        # Collect shop IDs in Veldt-gated areas
        veldt_gated_shops = set()
        for area in veldt_gated_areas:
            if area in AREA_SHOPS:
                veldt_gated_shops.update(AREA_SHOPS[area])

        # Return non-Veldt-gated shops
        non_veldt_shops = [shop_id for shop_id in self.accessible_shops
                          if shop_id not in veldt_gated_shops]

        if self.verbose:
            print(f'Accessible shops: {len(self.accessible_shops)}')
            print(f'Veldt-gated shops: {list(veldt_gated_shops)}')
            print(f'Non-Veldt-gated shops: {len(non_veldt_shops)} - {non_veldt_shops}')

        # Warn if no non-Veldt-gated shops exist when Gau is in the game
        if not non_veldt_shops and 'GAU' in self.planned_characters:
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
            print('Generating map with characters...')

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
                print('Branch viability:', branch_is_viable, 'Stuck:', self.stuck_branches)
            viable_branches = [b for b in range(3) if len(self.branch_checks[b]) > 0 and branch_is_viable[b] and b not in self.stuck_branches]
            if len(viable_branches) > 0:
                branch_id = random.choice(viable_branches)
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
                        print(f'Adding reserve area {new_area} ({len(new_rooms)} rooms) to unstick branch {branch_id}')

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
                                print(f'\tSkipping room {room} - already exists')
                            continue
                        branch.add_room(room)

                    # Check if this area has any reward rooms
                    for room in new_rooms:
                        if room in ROOM_REWARD:
                            for reward_id in ROOM_REWARD[room].keys():
                                if reward_id not in self.branch_checks[branch_id]:
                                    self.branch_checks[branch_id].append(reward_id)
                                    if self.verbose:
                                        print(f'\tAdded new check: {reward_id}')

                    self.stuck_branches.pop(branch_id, None)  # Give it another chance

                    # CRITICAL: Reset the active room to the hub so we can try a different path
                    # Without this, the branch stays at the stuck position and immediately gets stuck again
                    hub_id = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)][0]
                    branch.active = hub_id
                    if self.verbose:
                        print(f'\tReset branch {branch_id} active room to hub: {hub_id}')

                elif len(CHARACTER_AREAS.get('EXTRA', [])) > 0:
                    # Fallback to EXTRA areas if no reserve areas left
                    new_area = CHARACTER_AREAS['EXTRA'].pop()
                    if self.verbose:
                        print('Adding extra area', new_area, 'to unstick branch', branch_id)
                    # Skip rooms that already exist (use all_rooms_added to catch merged rooms)
                    existing_rooms = set()
                    for b in self.branches:
                        existing_rooms.update(b.all_rooms_added)
                    for room in RUIN_ROOM_SETS[new_area]:
                        if room in existing_rooms:
                            if self.verbose:
                                print(f'\tSkipping room {room} - already exists')
                            continue
                        branch.add_room(room)
                    self.stuck_branches.pop(branch_id, None)

                    # CRITICAL: Reset the active room to the hub so we can try a different path
                    hub_id = [n for n in branch.net.nodes if 'ruin_hub_' in str(n)][0]
                    branch.active = hub_id
                    if self.verbose:
                        print(f'\tReset branch {branch_id} active room to hub: {hub_id}')

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
                        print('\ttrimmed dead end ', de)

            if self.verbose:
                print('Working on branch', branch_id, '(', self.branch_checks[branch_id], ')')
                print('status: terminus', branch.terminus)
                print('status: check rooms', branch.check_rooms)
                print('status: dead ends', branch.dead_ends)

            # Force any forced connections before starting
            if self.verbose:
                print('Forcing connections...')
            branch.ForceConnections(forced_connections)

            # Forcing connections can update the name of the active branch
            if branch.active not in branch.net.nodes:
                new_active = [n_id for n_id in branch.net.nodes if branch.active in str(n_id)]
                if self.verbose:
                    print('updating active room id: ', branch.active, '-->', new_active[0])
                branch.active = new_active[0]

            # Apply any keys we have found in other branches
            for k in self.keychain.difference(branch.keychain):
                branch.apply_key(k)

            found_reward = False
            rewards = []
            retries = 0
            while not found_reward:
                # Attach hubs & trapdoors until none are left (create all branches)

                # Choose an exit from the active room.
                this_exit, this_conn = branch.extend_branch_path()

                if this_exit is None:
                    retries += 1
                    if retries >= max_retries_per_branch:
                        if self.verbose:
                            print(f'Branch {branch_id} is stuck after {retries} retries. Reason: {branch.last_stuck_reason}')
                        self.stuck_branches[branch_id] = branch.last_stuck_reason
                        break
                    else:
                        if self.verbose:
                            print(f'Branch {branch_id} failed to extend, retry {retries}/{max_retries_per_branch}')
                        continue  # Try again with different random choices

                # Check if a reward was found
                rewards = branch.check_for_rewards(this_conn)

                if rewards is not None:
                    # Check to see if the reward is locked; if so, bank it
                    for r in rewards:
                        if r[0] in REWARDS_LOCKED_BY_CHARACTER.keys():
                            locker = REWARDS_LOCKED_BY_CHARACTER[r[0]]
                            if locker not in self.keychain:
                                # Bank this reward for later & keep going
                                if locker not in self.LockedRewards.keys():
                                    self.LockedRewards[locker] = []
                                self.LockedRewards[locker].append(
                                    (branch_id, [r]))  # (branch_id, [check_name, check_data])
                                if self.verbose:
                                    print('\t\treward is locked by', locker, '. Saving for later.')
                            else:
                                # We have the locking character, so reward is accessed.
                                found_reward = True
                        else:
                            # There is no potential character lock, so reward is accessed.
                            found_reward = True

                # Actually connect them.  This also moves the active room to the new room.
                if self.verbose:
                    print('Making connection: ', this_exit, '-->', this_conn)
                branch.connect(this_exit, this_conn)

            ### Process reward & restart loop - only if we actually found a reward
            if found_reward and rewards:
                self.process_rewards(rewards, characters, espers, items, branch_id=branch_id, exclude_chars=non_planned_chars)
            elif branch_id in self.stuck_branches:
                if self.verbose:
                    print(f'Skipping reward processing for stuck branch {branch_id}')

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

        # Add mapping for connections to KT
        traps_to_kt = [2077, 2078, 2079]
        pits_into_kt = [t + 1000 for t in traps_to_kt]
        random.shuffle(traps_to_kt)
        for i in range(3):
            map[1].append([traps_to_kt[i], pits_into_kt[i]])

        return map

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

    def process_rewards(self, rewards, characters, espers, items, branch_id, exclude_chars=None):
        # Identify reward & decide on reward type
        if exclude_chars is None:
            exclude_chars = []

        for reward in rewards:
            # reward_types = [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]
            reward_name = reward[0]  # reward_name = slot.event.name()
            slot = reward[1]
            if self.verbose:
                print('Processing reward: ', reward_name)

            remaining_chars_needed = len(self.planned_characters) - self.RewardsObtained[0]
            if remaining_chars_needed >= 1 and self.RewardsAvailable[0] == 1 and (slot.possible_types & RewardType.CHARACTER):
                # This must be a character.
                if self.verbose:
                    print('\tmust be a character')
                # Use characters.get_random_available with exclude parameter
                slot.id = characters.get_random_available(exclude=exclude_chars)
                slot.type = RewardType.CHARACTER
                if self.verbose:
                    print('\tgot ', characters.get_name(slot.id), '!')
            else:
                # Just choose from among available types
                if self.verbose:
                    print('\tchoosing from...', slot.possible_types)
                slot.id, slot.type = self._choose_reward_with_exclusion(slot.possible_types, characters, espers, items, exclude_chars)
                if self.verbose:
                    if slot.type is RewardType.CHARACTER:
                        print('\tgot', characters.get_name(slot.id), '!')
                    elif slot.type is RewardType.ESPER:
                        print('\tgot', espers.get_name(slot.id), '!')
                    elif slot.type is RewardType.ITEM:
                        print('\tgot', items.get_name(slot.id), '!')

            # Update RewardsObtained
            if slot.type is RewardType.CHARACTER:
                self.RewardsObtained[0] += 1

                # Set character path using the event's character_gate method
                # This returns the character ID that gates this reward (or None for starting areas)
                characters.set_character_path(slot.id, slot.event.character_gate())
                if self.verbose and slot.event.character_gate() is not None:
                    unlocker_name = characters.DEFAULT_NAME[slot.event.character_gate()]
                    new_char_name = characters.DEFAULT_NAME[slot.id]
                    print(f'\tSet character path: {new_char_name} depends on {unlocker_name}')

                # If a character, add new areas to the map
                new_char = characters.DEFAULT_NAME[slot.id]
                self.apply_key(new_char)  # apply new key to all branches
                new_areas = CHARACTER_AREAS[new_char]
                self.distribute_areas(new_areas, method='shortest')

            elif slot.type is RewardType.ESPER:
                self.RewardsObtained[1] += 1

            # Update RewardsAvailable
            if slot.possible_types & RewardType.CHARACTER:
                self.RewardsAvailable[0] -= 1
            if slot.possible_types & RewardType.ESPER:
                self.RewardsAvailable[1] -= 1

            if self.verbose:
                print('\tUpdated Rewards Obtained: ', self.RewardsObtained[0], 'Characters, ', self.RewardsObtained[1], 'Espers')
                print('\tUpdated Rewards Available: ', self.RewardsAvailable[0], 'Characters, ',
                      self.RewardsAvailable[1],
                      'Espers')

            # Update branch_checks
            self.branch_checks[branch_id].remove(reward_name)
            if self.verbose:
                print('\tUpdated branch checks available:')
                for i, bc in enumerate(self.branch_checks):
                    print('\t', i, ': ', bc)

            # If a new character unlocks a reward we already found, apply it.
            if slot.type is RewardType.CHARACTER:
                this_char = characters.DEFAULT_NAME[slot.id]
                if this_char in self.LockedRewards.keys():
                    # self.LockedRewards[locker].append((branch_id, [r]))   # (branch_id, [check_name, check_data])
                    value = self.LockedRewards.pop(this_char)
                    for v in value:
                        unlocked_rewards = v[1]
                        for new_reward in unlocked_rewards:
                            if self.verbose:
                                print('\tUnlocked an available reward!', new_reward[0], 'on branch', v[0])
                            # Add to branch_checks so it can be properly removed during processing
                            self.branch_checks[v[0]].append(new_reward[0])
                            # First add this to rewards available (since it was never done)
                            if new_reward[1].possible_types & RewardType.CHARACTER:
                                self.RewardsAvailable[0] -= 1
                            if new_reward[1].possible_types & RewardType.ESPER:
                                self.RewardsAvailable[1] -= 1
                        # Then process them all
                        self.process_rewards(unlocked_rewards, characters, espers, items, v[0], exclude_chars)


def ruination_start_game_mod(dialogs, party):
    # Write the event that starts the game in ruination mode

    # For dialog, let's use the Maduin/Madonna conversation: $05A4 -- $05AA
    ruination_start_1 = 0x0590
    dialogs.set_text(ruination_start_1, "After Kefka broke the world, we woke up here.<wait 60 frames><end>")
    ruination_start_2 = 0x0591
    dialogs.set_text(ruination_start_2, "This new world is dark and full of monsters.<wait 30 frames> Let's find our friends and bring hope to the darkness.<end>")

    src = [
        field.LoadMap(ESPER_GATE_MAPID, direction.DOWN, default_music=False,
                        x=55, y=33, entrance_event=True),

        field.CreateEntity(field_entity.PARTY1),
        field.CreateEntity(field_entity.PARTY2),
        field.CreateEntity(field_entity.PARTY3),

        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetPosition(54, 31),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpriteLayer(2),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),
        field.EntityAct(field_entity.PARTY1, True,
                        field_entity.SetPosition(56, 32),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),
        field.EntityAct(field_entity.PARTY2, True,
                        field_entity.SetPosition(53, 33),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),
        field.EntityAct(field_entity.PARTY3, True,
                        field_entity.SetPosition(55, 35),
                        field_entity.AnimateKnockedOut(),
                        field_entity.SetSpeed(field_entity.Speed.NORMAL),
                        ),

        field.ShowEntity(field_entity.PARTY0),
        field.ShowEntity(field_entity.PARTY1),
        field.ShowEntity(field_entity.PARTY2),
        field.ShowEntity(field_entity.PARTY3),

        field.RefreshEntities(),
        field.Dialog(ruination_start_1, wait_for_input=False, inside_text_box=False, top_of_screen=False),
        field.HoldScreen(),
        field.FadeInScreen(speed=8),
        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.Pause(60),
                        field_entity.AnimateKneeling(),
                        field_entity.Pause(30),
                        field_entity.AnimateStandingHeadDown(),
                        field_entity.Pause(15),
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

    src += [
        field.HideEntity(field_entity.PARTY1),
        field.HideEntity(field_entity.PARTY2),
        field.HideEntity(field_entity.PARTY3),

        field.EntityAct(field_entity.PARTY0, True,
                        field_entity.SetSpriteLayer(0),
                        ),

        field.RefreshEntities(),
        field.FreeScreen(),
        field.Return(),
    ]
    space = Write(Bank.CC, src, "start game ruination")
    return space.start_address

def modify_inn_costs(maps, rom, dialogs, args):
    """
    Modifies all inn costs in the game by multiplying them by INN_COST_MULTIPLIER.
    Also updates the associated dialog text to reflect the new prices.
    Additionally converts free inns (Returners Hideout, Figaro Castle) to paid inns.

    Each inn event has a "Take GP" instruction (opcode 0x85) followed by a 2-byte
    little-endian amount. This function finds all these locations and multiplies
    the GP amount by the multiplier constant.

    Args:
        maps: The Maps object to modify NPCs and event tiles
        rom: The ROM object to modify
        dialogs: The Dialogs object to update dialog text
        args: Command line arguments
    """
    from memory.space import Write, Bank
    from instruction.event import EVENT_CODE_START
    import data.event_bit as event_bit

    # List of all inn GP cost addresses in the ROM
    # Format: (address, original_cost, dialog_id, dialog_template, description)
    # dialog_id is None for entries that share a dialog with another entry
    # dialog_template uses {price} as placeholder for the GP amount
    # Note: Chocobo stables are handled separately by disable_chocobo_stables()
    # Note: Thamasa inn is handled separately by modify_thamasa_inn_ruination()
    inn_costs = [
        (0xa78a0, 80, 0x0B89, "{price} GP per night.<line>Stay the night?<line><choice> Yes<line><choice> No<end>", "South Figaro inn"),
        (0xa8ef1, 150, 0x0B8A, "{price} GP per night!<line>Sound good?<line><choice> Yes<line><choice> No<end>", "Nikeah inn WoB"),
        (0xb449c, 250, 0x0112, "{price} GP per night.<line>Lights out?<line><choice> Yes<line><choice> No<end>", "Jidoor inn"),
        (0xc5caf, 350, 0x062A, "{price} GP per night!<line>Rest a while?<line><choice> Yes<line><choice> No<end>", "Tzen inn"),
        (0xc62b2, 300, 0x0649, "{price} GP if you wanna stay.<line>How 'bout it?<line><choice> Yes<line><choice> No<end>", "Albrook inn WOR"),
        (0xc6593, 200, 0x060D, "{price} GP per night!<line>Need a rest?<line><choice> Sure<line><choice> Nope<end>", "Maranda inn"),
        (0xc665f, 100, 0x064B, "You look tired!<line>{price} GP for a snooze.<line><choice> Yes<line><choice> No<end>", "Mobliz inn"),
        (0xc69d6, 200, None, None, "Kohlingen inn"),  # Shares dialog 0x060D with Maranda
        (0xcd2b3, 200, None, None, "Narshe inn"),  # Shares dialog 0x060D with Maranda
    ]

    # Track which dialogs we've already updated to avoid double-updating shared dialogs
    updated_dialogs = set()

    for address, original_cost, dialog_id, dialog_template, description in inn_costs:
        # Calculate new cost
        new_cost = min(original_cost * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

        # Write the new cost as 2-byte little-endian
        rom.set_bytes(address, new_cost.to_bytes(2, 'little'))

        # Update dialog text if this entry has its own dialog ID
        if dialog_id is not None and dialog_id not in updated_dialogs:
            new_text = dialog_template.format(price=new_cost)
            dialogs.set_text(dialog_id, new_text)
            updated_dialogs.add(dialog_id)

            if args.debug:
                print(f"Updated dialog {dialog_id:#x} for {description}: {original_cost} GP -> {new_cost} GP")

        if args.debug:
            print(f"Modified {description}: {original_cost} GP -> {new_cost} GP")

    # =========================================================================
    # FREE INNS - Convert to paid inns
    # =========================================================================
    # These locations originally provided free healing. We add GP charges
    # affected by INN_COST_MULTIPLIER.

    # Free inn base prices (before multiplier)
    RETURNERS_HIDEOUT_INN_PRICE = 100
    FIGARO_CASTLE_INN_PRICE = 150

    # -------------------------------------------------------------------------
    # RETURNERS HIDEOUT INN (Map 111, NPC ID 16)
    # -------------------------------------------------------------------------
    # Original event at 0xCAF64E displays "Take a nap? Yes/No"
    # If yes: movement animation, call $CACD3C (sleep), load inn map, call $CACF96 (wake)
    # New: Display price, take GP, then jump to original movement code at 0xCAF659
    RETURNERS_DIALOG_ID = 0x111
    RETURNERS_ORIGINAL_YES_CODE = 0xCAF659

    returners_price = min(RETURNERS_HIDEOUT_INN_PRICE * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

    dialogs.set_text(RETURNERS_DIALOG_ID,
        f"{returners_price} GP per night!<line>Take a nap?<line><choice> Yes<line><choice> No<end>")

    returners_src = [
        field.DialogBranch(RETURNERS_DIALOG_ID, "RETURNERS_YES", "RETURNERS_NO"),
        field.Return(),

        "RETURNERS_YES",
        field.RemoveGP(returners_price),
        field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, "RETURNERS_NO_MONEY"),
        field.Branch(RETURNERS_ORIGINAL_YES_CODE),

        "RETURNERS_NO_MONEY",
        field.ClearEventBit(event_bit.NOT_ENOUGH_GP),
        "RETURNERS_NO",
        field.Return(),
    ]

    space = Write(Bank.CC, returners_src, "Returners Hideout inn with price")
    returners_npc = maps.get_npc(111, 0x10)
    returners_npc.event_address = space.start_address - EVENT_CODE_START

    if args.debug:
        print(f"Returners Hideout inn: {RETURNERS_HIDEOUT_INN_PRICE} GP -> {returners_price} GP")

    # -------------------------------------------------------------------------
    # FIGARO CASTLE REST (Map 59, event tile at (47, 52))
    # -------------------------------------------------------------------------
    # Original event at 0xCA71BF checks conditions then displays "Need a rest? Yes/No"
    # If yes: movement, check more conditions, call $CACD31 (sleep)
    # New: Same condition checks, display price, take GP, jump to original code
    # Note: We use dialog ID 1461 (0x5B5) instead of the original 0xB80 because
    # 0xB80 is also used by a Doma Castle event.
    FIGARO_DIALOG_ID = 1461
    FIGARO_ORIGINAL_YES_CODE = 0xCA71D9
    FIGARO_USED_ONCE_BIT = 0x1B5
    FIGARO_BANON_BIT = 0x1B0

    figaro_price = min(FIGARO_CASTLE_INN_PRICE * INN_COST_MULTIPLIER, field.RemoveGP.MAX)

    dialogs.set_text(FIGARO_DIALOG_ID,
        f"{figaro_price} GP per night!<line>Need a rest?<line><choice>(Yes)<line><choice>(No)<end>")

    figaro_src = [
        field.BranchIfEventBitSet(FIGARO_USED_ONCE_BIT, "FIGARO_RETURN"),
        field.BranchIfEventBitClear(FIGARO_BANON_BIT, "FIGARO_RETURN"),
        field.SetEventBit(FIGARO_USED_ONCE_BIT),
        field.DialogBranch(FIGARO_DIALOG_ID, "FIGARO_YES", "FIGARO_RETURN"),

        "FIGARO_YES",
        field.RemoveGP(figaro_price),
        field.BranchIfEventBitSet(event_bit.NOT_ENOUGH_GP, "FIGARO_NO_MONEY"),
        field.Branch(FIGARO_ORIGINAL_YES_CODE),

        "FIGARO_NO_MONEY",
        field.ClearEventBit(event_bit.NOT_ENOUGH_GP),
        "FIGARO_RETURN",
        field.Return(),
    ]

    space = Write(Bank.CC, figaro_src, "Figaro Castle rest with price")
    figaro_event = maps.get_event(59, 47, 52)
    if figaro_event is not None:
        figaro_event.event_address = space.start_address - EVENT_CODE_START
        if args.debug:
            print(f"Figaro Castle rest: {FIGARO_CASTLE_INN_PRICE} GP -> {figaro_price} GP")
    elif args.debug:
        print(f"Warning: Could not find Figaro Castle rest event at (47, 52)")


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


def fix_ferry_connections(rom, dialogs, ruin_map, args):
    """
    Fixes the ferry connection between South Figaro and Nikeah for ruination mode.

    If both South Figaro and Nikeah are mapped, preserves the original ferry behavior.
    If not both are mapped, changes the ferryman dialogs to indicate the ferry
    is not running and removes the choice from the NPC events.

    Args:
        rom: The ROM object to modify
        dialogs: The Dialogs object to update dialog text
        ruin_map: The ruination_map object containing AreasUsed
        args: Command line arguments (for debug flag)
    """
    # Check if both South Figaro and Nikeah are mapped
    south_figaro_mapped = 'SouthFigaro' in ruin_map.AreasUsed
    nikeah_mapped = 'Nikeah' in ruin_map.AreasUsed

    if south_figaro_mapped and nikeah_mapped:
        if args.debug:
            print("Ferry: Both South Figaro and Nikeah are mapped - preserving ferry connection")
        return

    # Ferry connection data:
    # - Dialog 810 (0x32A) = "South Figaro-bound ferry..." - used by Nikeah ferryman
    # - Dialog 812 (0x32C) = "Nikeah-bound ferry..." - used by South Figaro ferryman
    # - South Figaro dock ferryman: event at ROM 0x0A77D7, uses dialog 812 (0x32C)
    # - Nikeah dock ferryman: event at ROM 0x0A8CBB, uses dialog 810 (0x32A)

    disabled_message = "Some of us went out to map the sea, but no one returned.<end>"

    # Update both ferry dialogs
    dialogs.set_text(810, disabled_message)  # South Figaro-bound ferry dialog
    dialogs.set_text(812, disabled_message)  # Nikeah-bound ferry dialog

    # Patch South Figaro ferryman event to just display dialog and return
    # Event at 0x0A77D7 - uses dialog 812 (0x32C)
    south_figaro_event_addr = 0x0a77d7
    south_figaro_dialog_id = 812  # 0x32C
    event_bytes = bytes([0x4B, south_figaro_dialog_id & 0xFF, south_figaro_dialog_id >> 8, 0xFE])
    rom.set_bytes(south_figaro_event_addr, event_bytes)

    # Patch Nikeah ferryman event to just display dialog and return
    # Event at 0x0A8CBB - uses dialog 810 (0x32A)
    nikeah_event_addr = 0x0a8cbb
    nikeah_dialog_id = 810  # 0x32A
    event_bytes = bytes([0x4B, nikeah_dialog_id & 0xFF, nikeah_dialog_id >> 8, 0xFE])
    rom.set_bytes(nikeah_event_addr, event_bytes)

    if args.debug:
        print(f"Ferry: South Figaro mapped={south_figaro_mapped}, Nikeah mapped={nikeah_mapped}")
        print(f"Ferry: Disabled ferry connections - updated dialogs 810 and 812")
        print(f"Ferry: Patched South Figaro ferryman at {south_figaro_event_addr:#x}")
        print(f"Ferry: Patched Nikeah ferryman at {nikeah_event_addr:#x}")


# Battle pack for nighttime ambush at free beds
# This should be a difficult encounter - can be adjusted as needed
FREE_BED_AMBUSH_PACK = 416  # Placeholder pack - adjust to desired encounter
FREE_BED_DIALOG_ID = 443  # "Take a nap?" at Gau's Dad's House

# Vanilla free bed heal subroutine address (used by multiple bed event tiles)
VANILLA_BED_HEAL_ADDRESS = 0xcd17

# Address of the ruination bed heal routine (set by modify_free_bed_heals)
RUINATION_BED_HEAL_ADDRESS = None

# Existing free bed heal event tile locations
# Most point to the vanilla subroutine at 0xcd17
# Gau's Father's House has its own inline code but we treat it the same way
# Format: (map_id, x, y, description)
FREE_BED_LOCATIONS = [
    (24, 45, 51, "Narshe Weapon Shop"),
    (94, 73, 31, "Sabin's House"),
    (94, 81, 29, "Sabin's House"),
    (94, 84, 29, "Sabin's House"),
    (116, 113, 9, "Gau's Father's House"),
    (162, 29, 12, "Mobliz Relic Shop"),
]


def modify_free_bed_heals(maps, dialogs, args):
    """
    Modifies existing free bed heal events for ruination mode.

    Changes the bed heals to:
    - Have a 3/8 (37.5%) chance of triggering a back attack before healing
    - Heal only HP and status effects (NOT MP)
    - Use the standard bed animation (fade, Nighty Night song, unfade)

    Args:
        maps: The Maps object to modify event tiles
        dialogs: The Dialogs object to modify dialog for these events
        args: Command line arguments (for debug flag)
    """
    from instruction.field.custom import BranchChance

    # NIGHTY_NIGHT song ID
    NIGHTY_NIGHT = 56 | 0x80  # High bit set for temporary song

    # Status effects to remove (same as vanilla heal but we skip MP)
    # Remove: Death, Petrify, Imp, Vanish, Poison, Zombie, Darkness
    HEAL_STATUS = (field.Status.DEATH | field.Status.PETRIFY | field.Status.IMP |
                   field.Status.VANISH | field.Status.POISON | field.Status.ZOMBIE |
                   field.Status.DARKNESS)

    free_bed_dialog = "Sleep for the night?<line><choice> (Yes)<line><choice> (No)<end>"
    dialogs.set_text(FREE_BED_DIALOG_ID, free_bed_dialog)

    ambushed_dialog_id = 448  # Repurpose unused Dry Goods Merchant dialog
    ambushed_dialog = "           Ambushed!"
    dialogs.set_text(ambushed_dialog_id, ambushed_dialog)

    # Create the new bed heal event code
    # 5/8 chance to skip attack (so 3/8 chance of attack)
    src = [
        # Include a trigger so this can only be done once per map load
        field.ReturnIfEventBitSet(event_bit.multipurpose_map(0)),
        field.SetEventBit(event_bit.multipurpose_map(0)),

        # Ask if player wants to sleep for the night
        field.DialogBranch(FREE_BED_DIALOG_ID, dest1="CONTINUE", dest2="RETURN"),
        "CONTINUE",

        # Fade out current song
        field.FadeOutSong(48),
        field.PauseUnits(60),
        field.FadeOutScreen(8),
        field.WaitForFade(),

        # 3/8 chance of monster attack (branch with 5/8 = 62.5% probability to skip)
        BranchChance(0.625, "HEAL"),

        # Monster attack! (back attack)
        field.Dialog(ambushed_dialog_id),
        *field.InvokeBattleType(FREE_BED_AMBUSH_PACK, field.BattleType.BACK),

        "HEAL",
        # Play Nighty Night song
        field.StartSong(NIGHTY_NIGHT),

        # Heal HP and status for all party members (NOT MP)
        # Remove status effects
        field.RemoveStatusEffects(field_entity.PARTY0, HEAL_STATUS),
        field.RemoveStatusEffects(field_entity.PARTY1, HEAL_STATUS),
        field.RemoveStatusEffects(field_entity.PARTY2, HEAL_STATUS),
        field.RemoveStatusEffects(field_entity.PARTY3, HEAL_STATUS),
        # Restore HP to max
        field.RestoreHp(field_entity.PARTY0, 0x7f),
        field.RestoreHp(field_entity.PARTY1, 0x7f),
        field.RestoreHp(field_entity.PARTY2, 0x7f),
        field.RestoreHp(field_entity.PARTY3, 0x7f),
        # Note: No MP restoration!

        # Stop temporary song and restore previous
        field.WaitForSong(),
        field.FadeInPreviousSong(32),
        field.FadeInScreen(8),

        "RETURN",
        field.Return(),
    ]

    space = Write(Bank.CC, src, "ruination free bed heal event")
    new_bed_heal_address = space.start_address

    # Export the address for use by other modules (e.g., doma_wor.py)
    global RUINATION_BED_HEAL_ADDRESS
    RUINATION_BED_HEAL_ADDRESS = new_bed_heal_address

    if args.debug:
        print(f"Created modified bed heal event at {new_bed_heal_address:#x}")

    # Update existing bed event tiles to point to the new subroutine
    for map_id, x, y, description in FREE_BED_LOCATIONS:
        event = maps.get_event(map_id, x, y)
        if event is not None:
            event.event_address = new_bed_heal_address - EVENT_CODE_START
            if args.debug:
                print(f"Updated bed heal at {description} (map {map_id}, {x}, {y})")
        else:
            if args.debug:
                print(f"Warning: No event found at {description} (map {map_id}, {x}, {y})")


# Recovery Spring Effect Types
class SpringEffect:
    FULL_RECOVERY = 0    # HP + MP + Status
    RECOVER_HP = 1       # HP only
    RECOVER_MP = 2       # MP only
    RECOVER_STATUS = 3   # Status only
    POISON = 4           # Add poison to random party members
    IMP = 5              # Add imp to random party members
    ZOMBIE = 6           # Add zombie to random party members
    STONE = 7            # Add petrify to random party members
    REDUCE_TO_1_HP = 8   # Reduce all party members to 1 HP

# Recovery spring locations grouped by area
# Each area will have the same effect for all its tiles
SPRING_LOCATIONS = {
    'phantom_forest': [
        (133, 9, 10),   # Phantom Forest Healing Pool
        (133, 8, 10),
        (133, 7, 10),
        (133, 6, 10),
        (133, 5, 9),
    ],
    'cave_south_figaro': [
        (70, 47, 29),   # Cave to South Figaro (WoB)
        (73, 47, 29),   # Cave to South Figaro (WoB variant)
    ],
}

# Flash colors for each effect type
SPRING_FLASH_COLORS = {
    SpringEffect.FULL_RECOVERY: field.Flash.BLUE,
    SpringEffect.RECOVER_HP: field.Flash.BLUE,
    SpringEffect.RECOVER_MP: field.Flash.BLUE,
    SpringEffect.RECOVER_STATUS: field.Flash.BLUE,
    SpringEffect.POISON: field.Flash.GREEN,
    SpringEffect.IMP: field.Flash.GREEN,
    SpringEffect.ZOMBIE: field.Flash.RED | field.Flash.BLUE,  # Purple
    SpringEffect.STONE: field.Flash.WHITE,  # Grey-ish
    SpringEffect.REDUCE_TO_1_HP: field.Flash.RED,
}

# Dialog IDs for spring messages (using range 1480-1495)
SPRING_DIALOG_BASE = 1480


def modify_recovery_springs(maps, rom, dialogs, args):
    """
    Modifies recovery spring events for ruination mode.

    Each spring location gets a randomly assigned effect at compile time.
    Effects can be beneficial (healing) or harmful (status ailments).
    Player is asked before drinking from the pool.

    Args:
        maps: The Maps object to modify event tiles
        rom: The ROM object
        dialogs: The Dialogs object for setting dialog text
        args: Command line arguments (for debug flag)
    """
    import random as rng

    # Status effects for healing
    HEAL_STATUS = (field.Status.DEATH | field.Status.PETRIFY | field.Status.IMP |
                   field.Status.VANISH | field.Status.POISON | field.Status.ZOMBIE |
                   field.Status.DARKNESS)

    PARTY = [field_entity.PARTY0, field_entity.PARTY1, field_entity.PARTY2, field_entity.PARTY3]

    # All possible effects
    ALL_EFFECTS = [
        SpringEffect.FULL_RECOVERY,
        SpringEffect.RECOVER_HP,
        SpringEffect.RECOVER_MP,
        SpringEffect.RECOVER_STATUS,
        SpringEffect.POISON,
        SpringEffect.IMP,
        SpringEffect.ZOMBIE,
        SpringEffect.STONE,
        SpringEffect.REDUCE_TO_1_HP,
    ]

    # Result messages for each effect
    EFFECT_MESSAGES = {
        SpringEffect.FULL_RECOVERY: "HP, MP, and status restored!<end>",
        SpringEffect.RECOVER_HP: "HP restored!<end>",
        SpringEffect.RECOVER_MP: "MP restored!<end>",
        SpringEffect.RECOVER_STATUS: "Status ailments cured!<end>",
        SpringEffect.POISON: "The water was poisoned!<end>",
        SpringEffect.IMP: "The water turned you into Imps!<end>",
        SpringEffect.ZOMBIE: "The water was cursed!<end>",
        SpringEffect.STONE: "The water is petrifying!<end>",
        SpringEffect.REDUCE_TO_1_HP: "The water drained your strength!<end>",
    }

    dialog_id = SPRING_DIALOG_BASE

    # Set up the "Drink from the pool?" dialog
    drink_dialog_id = dialog_id
    dialogs.set_text(drink_dialog_id, "Drink from the pool?<line><choice> Yes<line><choice> No<end>")
    dialog_id += 1

    # Process each spring location area
    for area_name, locations in SPRING_LOCATIONS.items():
        # Randomly choose an effect for this area
        effect = rng.choice(ALL_EFFECTS)

        # Set up result message dialog
        result_dialog_id = dialog_id
        dialogs.set_text(result_dialog_id, EFFECT_MESSAGES[effect])
        dialog_id += 1

        # Get flash color for this effect
        flash_color = SPRING_FLASH_COLORS[effect]

        # Build the effect instructions
        effect_instructions = []

        if effect == SpringEffect.FULL_RECOVERY:
            for p in PARTY:
                effect_instructions.append(field.RemoveStatusEffects(p, HEAL_STATUS))
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x7f))
            for p in PARTY:
                effect_instructions.append(field.RestoreMp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_HP:
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_MP:
            for p in PARTY:
                effect_instructions.append(field.RestoreMp(p, 0x7f))

        elif effect == SpringEffect.RECOVER_STATUS:
            for p in PARTY:
                effect_instructions.append(field.RemoveStatusEffects(p, HEAL_STATUS))

        elif effect in [SpringEffect.POISON, SpringEffect.IMP, SpringEffect.ZOMBIE, SpringEffect.STONE]:
            # Determine which status to apply
            status_map = {
                SpringEffect.POISON: field.Status.POISON,
                SpringEffect.IMP: field.Status.IMP,
                SpringEffect.ZOMBIE: field.Status.ZOMBIE,
                SpringEffect.STONE: field.Status.PETRIFY,
            }
            status = status_map[effect]

            # Always affect party leader
            effect_instructions.append(field.AddStatusEffects(field_entity.PARTY0, status))
            # 50% chance to affect each other party member (at runtime)
            effect_instructions.extend([
                field.BranchRandomly("SKIP_P1"),
                field.AddStatusEffects(field_entity.PARTY1, status),
                "SKIP_P1",
                field.BranchRandomly("SKIP_P2"),
                field.AddStatusEffects(field_entity.PARTY2, status),
                "SKIP_P2",
                field.BranchRandomly("SKIP_P3"),
                field.AddStatusEffects(field_entity.PARTY3, status),
                "SKIP_P3",
            ])

        elif effect == SpringEffect.REDUCE_TO_1_HP:
            # Subtract 2^14 HP (16384), which reduces to 1 HP minimum
            for p in PARTY:
                effect_instructions.append(field.RestoreHp(p, 0x80 | 0x0e))

        # Build the full event code
        src = [
            # Require pressing the "A" button to activate
            field.BranchIfEventBitClear(event_bit=event_bit.PRESSING_A, destination="RETURN"),

            # Ask player if they want to drink
            field.DialogBranch(drink_dialog_id, "DRINK", "RETURN"),

            "DRINK",
            # Flash screen with appropriate color
            field.FlashScreen(flash_color),
            field.PlaySoundEffect(233),  # Spring sound
            field.PauseUnits(30),

            # Apply the effect
            *effect_instructions,

            # Show result message
            field.Dialog(result_dialog_id),

            # Enable movement and return
            field.FreeMovement(),
            field.Return(),

            "RETURN",
            field.Return(),
        ]

        space = Write(Bank.CC, src, f"ruination spring event {area_name}")
        spring_event_address = space.start_address

        if args.debug:
            effect_name = [k for k, v in vars(SpringEffect).items() if v == effect and not k.startswith('_')][0]
            print(f"Spring {area_name}: effect={effect_name}, address={spring_event_address:#x}")

        # Update all event tiles for this area to use the new event
        for map_id, x, y in locations:
            event = maps.get_event(map_id, x, y)
            if event is not None:
                event.event_address = spring_event_address - EVENT_CODE_START
                if args.debug:
                    print(f"  Updated spring tile at map {map_id} ({x}, {y})")
            else:
                if args.debug:
                    print(f"  Warning: No event at map {map_id} ({x}, {y})")

