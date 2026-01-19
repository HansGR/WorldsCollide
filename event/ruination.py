from event.event import *
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from data.rooms import room_data, ruination_dont_force
from data.walks import *
import random

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
    75: {"Figaro Castle WOB": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Figaro Castle Throne Room
    'dc-57': {"Figaro Castle WOR": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Figaro Castle engine room (beginning of Cave).  Engine Room is 94; Control Room is 86.
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
                     '207b', 212, 213, '215a', '215b', 216, 220, 221],
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
    'Zozo': ['ruin-zozo', '294r', '295r', '296r', '301r', '305r', '306r', '307r', '308r', '309r', 'branch-mz_mapsafe'],
    'ZozoTower': [297, 298, 299, 300, 302, '303a', '303b', 304, 310, 311, 312, 313],
    'MtZozo': [250, 251, 252, 253, 254, 255, 256, 'root-mz_mapsafe'],

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
    'FigaroCastle': ['ruin-figarocastle'],  # Remove entrance from South Figaro Cave; just have somewhere connect into the basement & require Engine Room before unlocking Castle.

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
        self.classify_rooms(rooms)

    def add_room(self, room_id):
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
        available_hubs = [r for r in self.net.nodes if (r not in self.dead_ends and r not in exclude)]
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
                conns.update(room.doors)
            elif element_type == 1:
                conns.update(room.pits)
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

    def finalize_map(self):
        print('Closing branch...')

        self.ForceConnections(forced_connections)

        hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
        hub = self.rooms.get_room(hub_id)
        if self.verbose:
            print('\thub:', hub_id, hub.count)

        # (1) Count trapdoors/pits connected to hub.  If trapdoors > pits, connect traps to rooms with (# pits > # traps).
        all_pits = [p for p in hub.pits]
        all_traps = [t for t in hub.traps]

        upstream = self.get_upstream_nodes(hub_id)
        for node in upstream:
            room = self.rooms.get_room(node)
            all_pits.extend([p for p in room.pits])
            all_traps.extend([t for t in room.traps])

        downstream = self.get_downstream_nodes(hub_id)
        for node in downstream:
            room = self.rooms.get_room(node)
            all_pits.extend([p for p in room.pits])
            all_traps.extend([t for t in room.traps])

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
                    if (len(r.pits) - len(r.traps)) > diff:
                        diff = len(r.pits) - len(r.traps)
                        winner = n

            # connect a hub trapdoor to this node
            this_exit = random.choice(all_traps)
            room = self.rooms.get_room(winner)
            this_entr = random.choice(room.pits)
            if self.verbose:
                print('(1) selected', winner, ': ', room.traps, room.pits)
                print('(1) connecting', this_exit, '-->', this_entr)

            self.connect(this_exit, this_entr)

            # Recollect data on pits/traps
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            all_pits = [p for p in hub.pits]
            all_traps = [t for t in hub.traps]

            upstream = self.get_upstream_nodes(hub_id)
            for node in upstream:
                room = self.rooms.get_room(node)
                all_pits.extend([p for p in room.pits])
                all_traps.extend([t for t in room.traps])

            downstream = self.get_downstream_nodes(hub_id)
            for node in downstream:
                room = self.rooms.get_room(node)
                all_pits.extend([p for p in room.pits])
                all_traps.extend([t for t in room.traps])

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

            upstream_doors = [d for d in hub.doors]
            upstream_pits = [p for p in hub.pits]
            for node in upstream:
                uproom = self.rooms.get_room(node)
                upstream_pits.extend([p for p in uproom.pits])

            this_conn = None
            if len(room.traps) > 0:
                this_exit = random.choice(list(room.traps))
                if len(upstream_pits) > 0:
                    this_conn = random.choice(upstream_pits)

            if this_conn is None and len(room.doors) > 0:
                this_exit = random.choice(list(room.doors))
                if len(upstream_doors) > 0:
                    this_conn = random.choice(upstream_doors)

            if this_conn is None:
                # A thing can happen here where the downstream has only a door-out, but the upstream has only pit-in (or vice versa).
                # In such a case, we can look at unused rooms, find a converter, attach it, and try again.
                available_nodes = [n for n in self.net.nodes if n not in self.dead_ends and n != hub_id]
                if len(room.traps) > 0 and len(upstream_pits) == 0 and len(upstream_doors) > 0:
                    # Need a pit-in, door-out converter
                    pido = []
                    if self.verbose:
                        print('\t\tlooking for available pido nodes:')
                    for node_id in available_nodes:
                        node = self.rooms.get_room(node_id)
                        if len(node.pits) > 0 and len(node.doors) > 0 and len(node.pits) > len(node.traps):
                            pido.append(node_id)
                            if self.verbose:
                                print('\t\t\t', node_id, ': ', node.count)

                    if len(pido) > 0:
                        pido_room_id = random.choice(pido)
                        pido_room = self.rooms.get_room(pido_room_id)
                        # Select a pit from the converter room as the connection target
                        this_conn = random.choice(list(pido_room.pits))

                elif len(room.doors) > 0 and len(upstream_doors) == 0 and len(upstream_pits) > 0:
                    # Need a door-in, trap-out converter
                    dito = []
                    if self.verbose:
                        print('\t\tlooking for available dito nodes:')
                    for node_id in available_nodes:
                        node = self.rooms.get_room(node_id)
                        if len(node.traps) > 0 and len(node.doors) > 0 and len(node.traps) > len(node.pits):
                            dito.append(node_id)
                            if self.verbose:
                                print('\t\t\t', node_id, ': ', node.count)

                    if len(dito) > 0:
                        dito_room_id = random.choice(dito)
                        dito_room = self.rooms.get_room(dito_room_id)
                        # Select a door from the converter room as the connection target
                        this_conn = random.choice(list(dito_room.doors))

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
        # At this point, only the hub room should be remaining & possibly upstream/downstream pits.
        # Recollect data on pits/traps (including downstream pits from pit-only rooms skipped in step 2)
        while len(hub.traps) > 0:
            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            remaining_pits = [p for p in hub.pits]
            remaining_traps = [t for t in hub.traps]
            upstream = self.get_upstream_nodes(hub_id)
            for node in upstream:
                room = self.rooms.get_room(node)
                remaining_pits.extend([p for p in room.pits])
            # Also collect pits from downstream nodes (pit-only rooms skipped in step 2)
            downstream = self.get_downstream_nodes(hub_id)
            for node in downstream:
                room = self.rooms.get_room(node)
                remaining_pits.extend([p for p in room.pits])

            random.shuffle(remaining_pits)
            if self.verbose:
                print('(3) remaining traps:', hub.traps, '; pits: ', remaining_pits)
            this_exit = remaining_traps.pop()
            this_conn = remaining_pits.pop()
            if self.verbose:
                print('(3) connecting:', this_exit, '-->', this_conn)
            self.connect(this_exit, this_conn)

        # (4) The terminus is currently always a dead end room.  Connect it.
        # However, the terminus may have been merged into the hub through loop compression.
        # If so, we skip this step since the terminus is already connected.
        remaining_doors = [d for d in hub.doors]
        random.shuffle(remaining_doors)
        if self.verbose:
            print('(4) remaining doors:', remaining_doors)
        terminus = self.rooms.get_room(self.terminus)
        if terminus is not None and len(remaining_doors) > 0:
            # Terminus is still a separate room and we have doors to connect it
            this_exit = remaining_doors.pop()
            if self.terminus in self.dead_ends:
                self.dead_ends.remove(self.terminus)
            this_conn = terminus.doors.pop()
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

        # (5) Count doors in hub.  Connect doors within hub until # doors < # dead ends
        # Clean up dead ends first - use list() to avoid modifying during iteration
        for de in list(self.dead_ends):
            if de not in self.net.nodes:
                self.dead_ends.remove(de)

        while len(remaining_doors) > len(self.dead_ends):
            if self.verbose:
                print('(5) doors in hub:', len(remaining_doors), '.  dead ends:', len(self.dead_ends))
            this_exit = remaining_doors.pop()
            this_conn = remaining_doors.pop()
            if self.verbose:
                print('(5) connecting doors in hub:', this_exit, '-->', this_conn)
            self.connect(this_exit, this_conn)

        # (6) Connect dead ends to all remaining doors.
        random.shuffle(self.dead_ends)
        if self.verbose:
            print('(6) remaining dead ends:', self.dead_ends)
        for this_exit in remaining_doors:
            room_id = self.dead_ends.pop()
            room = self.rooms.get_room(room_id)
            this_conn = room.doors.pop()
            if self.verbose:
                print('(6) connecting dead ends:', this_exit, '-->', this_conn)
            self.connect(this_exit, this_conn)

        if self.verbose:
            print('... closing branch complete!')

    def extend_branch_path(self):
        """Extend the branch by connecting an exit to an entrance.

        Improved algorithm:
        1. First check what exits AND entrances are available
        2. Choose exit type based on available entrances (don't blindly prefer traps)
        3. If primary type fails, try alternate type
        4. Expand search to all unconnected rooms, not just hubs
        5. Multiple fallback strategies before giving up
        """
        # (0) Get the current active room & look at the state of the branch
        active_room = self.rooms.get_room(self.active)
        upstream = self.get_upstream_nodes(self.active)
        downstream = self.get_downstream_nodes(self.active)
        currently_used = [self.active] + list(downstream) + list(upstream)

        if self.verbose:
            print('\tActive room: ', self.active, '.\n\tUpstream nodes: ', upstream,
                  '\n\tDownstream nodes: ', downstream)

        # Collect all available exits from current path
        all_exits = list(active_room.doors) + list(active_room.traps)
        for node in downstream:
            room = self.rooms.get_room(node)
            all_exits += list(room.doors) + list(room.traps)

        # (1) Look for forced exits first
        forced_exits = [e for e in all_exits if e in forced_connections.keys()]
        if len(forced_exits) > 0:
            this_exit = forced_exits.pop()
            this_conn = forced_connections[this_exit][0]
            if self.verbose:
                print('Found forced exit!', this_exit, '-->', this_conn)
            return this_exit, this_conn

        # (2) Collect available exits from most downstream nodes
        if len(downstream) == 0:
            available_exits = [list(active_room.doors), list(active_room.traps)]
        else:
            downstream_paths = self.get_downstream_paths(self.active)
            path_lengths = [len(p) for p in downstream_paths]
            longest_paths = [p for p in downstream_paths if len(p) == max(path_lengths)]
            most_downstream_nodes = list(set([p[-1] for p in longest_paths]))
            available_exits = [[], []]
            for node in most_downstream_nodes:
                room = self.rooms.get_room(node)
                available_exits[0] += list(room.doors)
                available_exits[1] += list(room.traps)

        # (3) Count available entrances to decide exit type intelligently
        available_pits = self.get_all_unconnected_entrances(element_type=1, currently_used=currently_used)
        available_doors_in = self.get_all_unconnected_entrances(element_type=0, currently_used=currently_used)

        if self.verbose:
            print(f'\tAvailable exits: {len(available_exits[0])} doors, {len(available_exits[1])} traps')
            print(f'\tAvailable entrances: {len(available_doors_in)} doors, {len(available_pits)} pits')

        # Count total doors in the connected path (active + upstream + downstream)
        # This is used to ensure we never run out of doors
        # Also collect the set of path doors for filtering
        path_doors = set(active_room.doors)
        for node in upstream:
            room = self.rooms.get_room(node)
            path_doors.update(room.doors)
        for node in downstream:
            room = self.rooms.get_room(node)
            path_doors.update(room.doors)
        path_door_count = len(path_doors)

        if self.verbose:
            print(f'\tTotal doors in connected path: {path_door_count}')

        # (4) Choose exit type based on what entrances are available
        # Only prefer traps if there are pits available to receive them
        have_traps = len(available_exits[1]) > 0
        have_doors = len(available_exits[0]) > 0
        have_pits = len(available_pits) > 0
        have_doors_in = len(available_doors_in) > 0

        # Determine exit type order: try the type that has matching entrances first
        if have_traps and have_pits:
            exit_type_order = [1, 0]  # Try trap first, then door
        elif have_doors and have_doors_in:
            exit_type_order = [0, 1]  # Try door first, then trap
        elif have_traps:
            exit_type_order = [1, 0]
        elif have_doors:
            exit_type_order = [0, 1]
        else:
            # No exits available
            if self.verbose:
                print('\tNo exits available!')
            return None, None

        # (5) Try each exit type in order
        for this_type in exit_type_order:
            if len(available_exits[this_type]) == 0:
                continue

            # Filter out exits that would strand pits in their source room
            # (using the last exit from a room that still has pits would trap players)
            safe_exits = []
            for exit_id in available_exits[this_type]:
                exit_room = self.rooms.get_room_from_element(exit_id)
                # Count remaining exits after using this one
                remaining_exits = len(exit_room.doors) + len(exit_room.traps) - 1

                # Would strand pits? (hard filter - never allow)
                if remaining_exits == 0 and len(exit_room.pits) > 0:
                    if self.verbose:
                        print(f'\t\tFiltering exit {exit_id} - would strand pits in {exit_room.id}')
                    continue

                safe_exits.append(exit_id)

            if len(safe_exits) == 0:
                if self.verbose:
                    print(f'\t\tNo safe {["door", "trap"][this_type]} exits available')
                continue

            this_exit = random.choice(safe_exits)
            this_room = self.rooms.get_room_from_element(this_exit)
            this_room_id = this_room.id

            if self.verbose:
                type_name = 'trap' if this_type == 1 else 'door'
                print(f'\tTrying {type_name} exit: {this_exit} in room {this_room_id}')

            # (6) Collect all possible entrances for this exit type
            available_conns = set()

            # Strategy A: Hub connections (non-dead-end unconnected rooms)
            if this_type == 0:
                available_conns.update(self.get_available_hub_connections(
                    element_type=0, excluded=currently_used, dito_ok=True))
            else:
                available_conns.update(self.get_available_hub_connections(
                    element_type=1, excluded=currently_used))

            # Strategy B: Upstream path connections (with connectivity rules)
            uppaths = self.get_upstream_paths(this_room_id)
            for path in uppaths:
                local_door_count = 0
                local_trap_count = 0
                for node_id in path:
                    node = self.rooms.get_room(node_id)
                    local_door_count += len(node.doors)
                    local_trap_count += len(node.traps)
                    if this_type == 1 and (local_door_count + local_trap_count) > 1:
                        available_conns.update(node.pits)
                    elif this_type == 0 and (local_door_count + local_trap_count) > 2:
                        available_conns.update(node.doors)

            # Strategy C: All unconnected rooms (more permissive - includes dead ends)
            if len(available_conns) == 0:
                if self.verbose:
                    print('\t\tExpanding search to all unconnected rooms...')
                available_conns.update(self.get_all_unconnected_entrances(
                    element_type=this_type, currently_used=currently_used))

            # Strategy D: Check rooms specifically
            if len(available_conns) == 0:
                if self.verbose:
                    print('\t\tTrying check rooms...')
                available_conns.update(self.get_all_check_connections(element_type=this_type))

            # If we found connections, filter and use them
            if len(available_conns) > 0:
                # If this is a door exit and we have < 3 doors in the path,
                # don't allow connecting to another door in the path (would consume 2 doors at once)
                if this_type == 0 and path_door_count < 3:
                    filtered_conns = [c for c in available_conns if c not in path_doors]
                    if len(filtered_conns) > 0:
                        available_conns = set(filtered_conns)
                        if self.verbose:
                            print(f'\t\tFiltered out path doors (path has only {path_door_count} doors)')
                    elif self.verbose:
                        print(f'\t\tWarning: only path doors available, using any')

                # If this is a door exit and we're down to our last door in the path,
                # only connect to rooms with 2+ doors so we don't run out
                if this_type == 0 and path_door_count == 1:
                    filtered_conns = []
                    for conn in available_conns:
                        conn_room = self.rooms.get_room_from_element(conn)
                        if len(conn_room.doors) >= 2:
                            filtered_conns.append(conn)
                    if len(filtered_conns) > 0:
                        available_conns = set(filtered_conns)
                        if self.verbose:
                            print(f'\t\tFiltered to rooms with 2+ doors (path has only 1 door left)')
                    elif self.verbose:
                        print(f'\t\tWarning: no rooms with 2+ doors, using any available')

                this_conn = random.choice(list(available_conns))
                if self.verbose:
                    conn_room = self.rooms.get_room_from_element(this_conn)
                    print(f'\tFound {len(available_conns)} connections, selected: {this_conn} in room {conn_room.id}')
                return this_exit, this_conn
            else:
                if self.verbose:
                    type_name = 'trap' if this_type == 1 else 'door'
                    print(f'\t\tNo entrances found for {type_name}, trying alternate type...')

        # (7) All strategies exhausted
        if self.verbose:
            print('\tAll connection strategies exhausted. Branch extension failed.')
        return None, None


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
        if hub_is_upstream:
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
    verbose = True

    def __init__(self, args, starting_party):
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

        # Interpret unlock requirements as requested # characters & espers in the map
        for o in args.objectives:
            if o.result.name == "Unlock Final Kefka":
                for c in o.conditions:
                    #print(c.name, c.args)
                    if c.name == "Characters":
                        self.Requested[0] = c.args[0]
                    if c.name == "Espers":
                        self.Requested[1] = c.args[0]
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

        # Add rooms to the branches
        for i, branch in enumerate(self.branches):
            for room in branch_rooms[i]:
                branch.add_room(room)

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
        stuck_branches = set()  # Track branches that can't progress
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
                print('Branch viability:', branch_is_viable, 'Stuck:', stuck_branches)
            viable_branches = [b for b in range(3) if len(self.branch_checks[b]) > 0 and branch_is_viable[b] and b not in stuck_branches]
            if len(viable_branches) > 0:
                branch_id = random.choice(viable_branches)
                branch = self.branches[branch_id]
            else:
                # All branches with checks are stuck or non-viable - try to unstick one
                checkable_branches = [b for b in range(3) if len(self.branch_checks[b]) > 0]
                if len(checkable_branches) == 0:
                    print("ERROR: No branches have remaining checks!")
                    break

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
                    existing_rooms = set()
                    for b in self.branches:
                        existing_rooms.update(b.net.nodes)
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

                    stuck_branches.discard(branch_id)  # Give it another chance
                elif len(CHARACTER_AREAS.get('EXTRA', [])) > 0:
                    # Fallback to EXTRA areas if no reserve areas left
                    new_area = CHARACTER_AREAS['EXTRA'].pop()
                    if self.verbose:
                        print('Adding extra area', new_area, 'to unstick branch', branch_id)
                    # Skip rooms that already exist
                    existing_rooms = set()
                    for b in self.branches:
                        existing_rooms.update(b.net.nodes)
                    for room in RUIN_ROOM_SETS[new_area]:
                        if room in existing_rooms:
                            if self.verbose:
                                print(f'\tSkipping room {room} - already exists')
                            continue
                        branch.add_room(room)
                    stuck_branches.discard(branch_id)
                else:
                    print("ERROR: No reserve areas available to unstick branches!")
                    break

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
                            print(f'Branch {branch_id} is stuck after {retries} retries')
                        stuck_branches.add(branch_id)
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
            elif branch_id in stuck_branches:
                if self.verbose:
                    print(f'Skipping reward processing for stuck branch {branch_id}')

            # If not in the hub room, return to the hub room?

        # After satisfying conditions, fully connect map
        for branch in self.branches:
            branch.finalize_map()

        # Wrap up: create & export a total map
        map = [[], []]
        for branch in self.branches:
            map[0].extend([m for m in branch.map[0]])
            map[1].extend([m for m in branch.map[1]])

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

            if self.RewardsAvailable[0] == 1 and (slot.possible_types & RewardType.CHARACTER):
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
    FIGARO_DIALOG_ID = 0xB80
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


# Battle pack for nighttime ambush at free beds
# This should be a difficult encounter - can be adjusted as needed
FREE_BED_AMBUSH_PACK = 416  # Placeholder pack - adjust to desired encounter

# Vanilla free bed heal subroutine address (used by multiple bed event tiles)
VANILLA_BED_HEAL_ADDRESS = 0xcd17

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


def modify_free_bed_heals(maps, rom):
    """
    Modifies existing free bed heal events for ruination mode.

    Changes the bed heals to:
    - Have a 3/8 (37.5%) chance of triggering a back attack before healing
    - Heal only HP and status effects (NOT MP)
    - Use the standard bed animation (fade, Nighty Night song, unfade)

    Args:
        maps: The Maps object to modify event tiles
        rom: The ROM object for debug output
    """
    from instruction.field.custom import BranchChance

    # NIGHTY_NIGHT song ID
    NIGHTY_NIGHT = 56 | 0x80  # High bit set for temporary song

    # Status effects to remove (same as vanilla heal but we skip MP)
    # Remove: Death, Petrify, Imp, Vanish, Poison, Zombie, Darkness
    HEAL_STATUS = (field.Status.DEATH | field.Status.PETRIFY | field.Status.IMP |
                   field.Status.VANISH | field.Status.POISON | field.Status.ZOMBIE |
                   field.Status.DARKNESS)

    # Create the new bed heal event code
    # 5/8 chance to skip attack (so 3/8 chance of attack)
    src = [
        # Fade out current song
        field.FadeOutSong(48),
        field.PauseUnits(60),
        field.FadeOutScreen(8),
        field.WaitForFade(),

        # 3/8 chance of monster attack (branch with 5/8 = 62.5% probability to skip)
        BranchChance(0.625, "HEAL"),

        # Monster attack! (back attack)
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

        field.Return(),
    ]

    space = Write(Bank.CC, src, "ruination free bed heal event")
    new_bed_heal_address = space.start_address

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


def modify_recovery_springs(maps, rom, dialogs):
    """
    Modifies recovery spring events for ruination mode.

    Each spring location gets a randomly assigned effect at compile time.
    Effects can be beneficial (healing) or harmful (status ailments).
    Player is asked before drinking from the pool.

    Args:
        maps: The Maps object to modify event tiles
        rom: The ROM object
        dialogs: The Dialogs object for setting dialog text
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

