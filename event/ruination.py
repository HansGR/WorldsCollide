from event.event import *
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from data.rooms import room_data, ruination_dont_force
from data.walks import *
import random

ESPER_GATE_MAPID = 0x0da
NARSHE_SCHOOL_DOOR_IDS = [393, 394, 395]

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
    48: {"Narshe Moogle Defense": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},   # Moogle Defense WOR (need to update how this starts); 65 in WOB

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
}
AREA_TYPES = {
    'TOWNS': ['Kohlingen', 'Jidoor', 'Maranda', 'Tzen', 'Albrook', 'Thamasa', 'Nikeah', 'Vector', 'SouthFigaro'],  # 'Mobliz', 'Narshe', # WOB only
}

# List of rooms associated with each named area
RUIN_ROOM_SETS = {
    'Doma': [421, 422, 423, 424, 425, 426, 427, 428, 429, 208, 209, 210, 211, '221R', 435, 436, '212R', 430, 431,
                  432, 433, 184, 185, 186, 187, 188, '188B', 189, 190, 191, 192, 193, 'dc-76'],
    'UmarosCave': [364, 365, 366, '367a', '367b', '367c', 'share_east', 'share_west', 368],  # root is in Narshe
    'EsperMountain': [488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501],
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
        if self.verbose:
            print('added room:', room_id)
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

    def get_available_hubs(self, exclude=None):
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)
            if self.verbose:
                print('Excluding...', exclude)
        available_hubs = [r for r in self.net.nodes if (r not in self.dead_ends and r not in exclude)]
        if self.verbose:
            print('Found available hubs:', available_hubs)
        return available_hubs

    def get_available_hub_connections(self, element_type=0, excluded=None, dito_ok=True):
        if self.verbose:
            print('Excluding...', excluded)
        hub_ids = self.get_available_hubs(exclude=excluded)
        hub_conns = set()
        for hub_id in hub_ids:
            hub = self.rooms.get_room(hub_id)
            if element_type == 0:
                # Don't include pit-in, door-out doors (these are effectively dead ends for this purpose)
                if len(hub.doors) <= 1 and len(hub.traps) == 0:
                    if self.verbose:
                        print('skipping', hub_id, '(dead end or pit-in-door-out)')
                # Only include door-in, trap-out doors if allowed.
                elif (len(hub.doors) == 1 and len(hub.traps) >= 1 and len(hub.pits) == 0) and not dito_ok:
                    if self.verbose:
                        print('skipping', hub_id, '(door-in-trap-out, excluded)')
                else:
                    hub_conns.update(hub.doors)
            elif element_type == 1:
                hub_conns.update(hub.pits)
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

    def finalize_map(self):
        print('Closing branch...')

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
            winner = ''
            diff = 0
            for n in self.net.nodes:
                if n not in upstream and n not in downstream and n != hub_id:
                    r = self.rooms.get_room(n)
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
        delta.sort()
        while len(delta) > 0:
            value = delta.pop()
            node = value[1]
            room = self.rooms.get_room(node)
            if self.verbose:
                print('(2) selected', node, '(delta = ', value[0], '): ', room.count, room.doors, room.traps, room.pits)

            hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
            hub = self.rooms.get_room(hub_id)
            upstream = self.get_upstream_nodes(hub_id)

            ### A thing can happen here where the downstream has only a door-out, but the upstream has only pit-in (or vice versa).
            # In such a case, we can look at unused rooms, find a converter, and go through it.
            if len(room.traps) > 0:
                this_exit = random.choice(list(room.traps))
                upstream_pits = [p for p in hub.pits]
                for node in upstream:
                    uproom = self.rooms.get_room(node)
                    upstream_pits.extend([p for p in uproom.pits])
                this_conn = random.choice(upstream_pits)
            elif len(room.doors) > 0:
                this_exit = random.choice(list(room.doors))
                upstream_doors = [d for d in hub.doors]
                for node in upstream:
                    uproom = self.rooms.get_room(node)
                    upstream_doors.extend([d for d in uproom.doors])
                this_conn = random.choice(upstream_doors)
            else:
                # Failure.
                print('Found an inescapable downstream node!')
                raise Exception

            if self.verbose:
                print('(2) connecting', this_exit, '-->', this_conn)
            self.connect(this_exit, this_conn)

        # (3) Connect any remaining trapdoors/pits
        # At this point, only the hub room should be remaining.
        hub_id = [n for n in self.net.nodes if 'ruin_hub_' in str(n)][0]
        hub = self.rooms.get_room(hub_id)
        remaining_pits = [p for p in hub.pits]
        random.shuffle(remaining_pits)
        if self.verbose:
            print('(3) remaining traps:', hub.traps, '; pits: ', remaining_pits)
        for this_exit in hub.traps:
            this_conn = remaining_pits.pop()
            if self.verbose:
                print('(3) connecting:', this_exit, '-->', this_conn)
            self.connect(this_exit, this_conn)

        # (4) The terminus is currently always a dead end room.  Connect it.
        remaining_doors = [d for d in hub.doors]
        random.shuffle(remaining_doors)
        if self.verbose:
            print('(4) remaining doors:', remaining_doors)
        this_exit = remaining_doors.pop()
        terminus = self.rooms.get_room(self.terminus)
        if self.terminus in self.dead_ends:
            self.dead_ends.remove(self.terminus)
        this_conn = terminus.doors.pop()
        if self.verbose:
            print('(4) connecting terminus:', this_exit , '-->', this_conn)
        self.connect(this_exit, this_conn)

        # (5) Count doors in hub.  Connect doors within hub until # doors < # dead ends
        # Clean up dead ends first
        for de in self.dead_ends:
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


class ruination_map():
    # Class to organize data for mapping out ruination mode branches
    RewardsAvailable = [0, 0]   # [# possible characters, # possible espers]
    PARTY = []
    Requested = [3, 0]
    branches = [RuinationBranch([]), RuinationBranch([]), RuinationBranch([])]
    branch_checks = [ [], [], []]   # checks available on each branch, stored locally
    AreasUsed = set()   # use a set to avoid duplicates
    keychain = set()   # global keychain

    verbose = True

    def __init__(self, args, starting_party):
        self.args = args
        self.PARTY.extend(starting_party)  # use character names in all caps
        self.keychain.update(self.PARTY)  # add party to the keychain

        # Interpret unlock requirements as requested # characters & espers in the map
        for o in args.objectives:
            if o.result.name == "Unlock Final Kefka":
                for c in o.conditions:
                    #print(c.name, c.args)
                    if c.name == "Characters":
                        self.Requested[0] = c.args[0]
                    if c.name == "Espers":
                        self.Requested[1] = c.args[0]
        #print(self.Requested)

        # Assemble initial areas to use & distribute among starting branches
        initial_areas = set()
        for character in self.PARTY:
            initial_areas.update(CHARACTER_AREAS[character])
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

    def distribute_areas(self, areas, method = 'random'):
        # Distribute new areas among the branches
        branch_areas = [ set(), set(), set()]

        # Make sure we don't double-add areas
        areas = [a for a in areas if a not in self.AreasUsed]

        if method == 'random':
            for area in areas:
                this_index = random.randint(0, 2)
                branch_areas[this_index].add(area)
        elif method == 'distribute':
            seed = random.randint(0, 2)
            use_index = [(i + seed) % 3 for i in range(len(areas))]
            random.shuffle(use_index)
            for area in areas:
                this_index = use_index.pop()
                branch_areas[this_index].add(area)
        elif method == 'shortest':
            num_rooms = [len(b.original_room_ids) for b in self.branches]
            random.shuffle(areas)
            for area in areas:
                if self.verbose:
                    print('\t\t# rooms on each branch: ', num_rooms)
                use_index = num_rooms.index(min(num_rooms))
                branch_areas[use_index].add(area)
                area_room_num = len(RUIN_ROOM_SETS[area])
                num_rooms[use_index] += area_room_num
        elif method == 'least_checks':
            for area in areas:
                shortest_index = [len(b) for b in self.branch_checks]
                use_index = shortest_index.index(min(shortest_index))
                branch_areas[use_index].add(area)

        # Add areas to global catalog
        self.AreasUsed.update(areas)

        if self.verbose:
            print('Distributed areas:')
            for i, b in enumerate(branch_areas):
                print('\t', i, ': ', b)

        # Expand to list of rooms to add to each branch
        branch_rooms = [set(), set(), set()]
        for i, areas in enumerate(branch_areas):
            for area in areas:
                branch_rooms[i].update(RUIN_ROOM_SETS[area])

        # Collect which checks are available, including how many can be characters and how many espers
        for room in ROOM_REWARD:
            which_branch = next((i for i, branch in enumerate(branch_rooms) if room in branch), -1)
            if which_branch >= 0:
                for reward_id in ROOM_REWARD[room].keys():
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

    def generate_map_with_characters(self, reward_slots, characters, espers, items):
        # Build out branches, always starting with the least connected
        RewardsObtained = [0, 0]

        # Edit forced connections for ruination
        #for fc in ruination_extra_force:
        for fc in ruination_dont_force:
            if fc in forced_connections.keys():
                forced_connections.pop(fc)

        if self.verbose:
            print('Generating map with characters...')

        while (RewardsObtained[0] < self.Requested[0] or RewardsObtained[1] < self.Requested[1]):
            # Pick a branch with an active reward
            #branch_in_hub = ['ruin_hub_' in str(b.active) for b in self.branches]
            #if branch_in_hub.count(False) > 0:
            #    # One of the branches is not in the hub. Keep working on that one.
            #    branch_id = branch_in_hub.index(False)
            branch_id = random.choice([b for b in range(3) if len(self.branch_checks[b]) > 0])
            branch = self.branches[branch_id]

            # Update lists of dead ends
            for de in branch.dead_ends:
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
            while not found_reward:
                # Attach hubs & trapdoors until none are left (create all branches)

                # Choose an exit from the active room.
                # Only allow trap doors if there is at least one entrance to the active room
                active_room = branch.rooms.get_room(branch.active)
                all_entrances = list(active_room.doors) + list(active_room.pits)
                upstream = branch.get_upstream_nodes(branch.active)
                if self.verbose:
                    print('\tActive room: ', branch.active, '.  Upstream nodes: ', upstream,
                          '\n\tAll entrances: ', all_entrances)
                hub_is_upstream = len([n for n in upstream if 'ruin_hub_' in str(n)]) > 0
                if hub_is_upstream:
                    print('\tHub is upstream!')
                for node in upstream:
                    room = branch.rooms.get_room(node)
                    all_entrances += list(room.doors) + list(room.pits)

                allow_traps = len(all_entrances) >= 1
                dito_ok = len(all_entrances) >= 2  # a door-in, trap-out room effectively replaces a door (entrance) with a trap (not entrance), so an extra entrance is required
                if self.verbose and not allow_traps:
                    print('\ttraps not allowed!')
                elif self.verbose:
                    print('\ttraps allowed!')

                # Look at unconnected hubs.
                new_hub_door_conns = branch.get_available_hub_connections(element_type=0, excluded=[branch.active], dito_ok=dito_ok)
                new_hub_pit_conns = branch.get_available_hub_connections(element_type=1, excluded=[branch.active])
                # If hub is upstream, possibly allow connecting back to the hub (closing the loop)
                if hub_is_upstream:
                    # Requirements: total exits after connection > 0
                    uppaths = branch.get_upstream_paths(branch.active)
                    for path in uppaths:
                        if self.verbose:
                            print('\tchecking upstream path:', path)
                        path_door_count = 0
                        path_trap_count = 0
                        tracker = [False, False]
                        for node_id in path:
                            node = branch.rooms.get_room(node_id)
                            path_door_count += len(node.doors)
                            path_trap_count += len(node.traps)
                            if (path_door_count + path_trap_count) > 1:
                                # We've met the condition for trapdoor connections.  Add pits.
                                new_hub_pit_conns.update(node.pits)
                                if self.verbose and tracker[0] is False:
                                    print('\t\tTrapdoor condition met at', node_id)
                                    tracker[0] = True
                            if (path_door_count + path_trap_count) > 2:
                                # We've met the condition for door connections.  Add doors.
                                new_hub_door_conns.update(node.doors)
                                if self.verbose and tracker[1] is False:
                                    print('\t\tDoor condition met at', node_id)
                                    tracker[1] = True

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
                downstream = branch.get_downstream_nodes(branch.active)
                if self.verbose:
                    print('\tDownstream nodes: ', downstream)
                if len(new_hub_door_conns) > 0:
                    all_exits += list(active_room.doors)
                    for node_id in downstream:
                        node = branch.rooms.get_room(node_id)
                        all_exits += list(node.doors)
                    available_connections[0] += new_hub_door_conns
                if len(new_hub_pit_conns) > 0 and allow_traps:
                    all_exits += list(active_room.traps)
                    for node_id in downstream:
                        node = branch.rooms.get_room(node_id)
                        all_exits += list(node.traps)
                    available_connections[1] += new_hub_pit_conns
                if self.verbose:
                    print('\tCollected available active room exits:', len(all_exits))
                    print('\t\t', all_exits)

                # Handle failure modes: no exits available
                if len(all_exits) == 0:
                    # I think the main way we get here is if there are no more hub rooms, and a check is in a dead end.
                    check_door_cons = branch.get_all_check_connections(element_type=0)
                    check_pit_cons = branch.get_all_check_connections(element_type=1)
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
                        break  # hopefully another branch is valid & can add some units to this one.

                # If any exits are forced, apply them
                forced_exits = [e for e in all_exits if e in forced_connections.keys()]
                if len(forced_exits) > 0:
                    this_exit = forced_exits.pop()
                    this_conn = forced_connections[this_exit]
                    if self.verbose:
                        print('Found forced exit!', this_exit, '-->', this_conn)
                else:
                    this_exit = random.choice(all_exits)
                    this_type = active_room.element_type(this_exit)
                    if self.verbose:
                        print('All allowed exits:', all_exits, '.  Choose: ', this_exit, '(type ', this_type, ')')
                    if this_exit in available_connections[this_type]:
                        available_connections[this_type].remove(this_exit)
                    this_conn = random.choice(available_connections[this_type])
                    if self.verbose:
                        print('Available connections:', available_connections[this_type], '. Choose: ', this_conn)

                # Check if a reward was found
                conn_room = branch.rooms.get_room_from_element(this_conn)
                if conn_room.id in ROOM_REWARD.keys():
                    # Stop if a reward was found
                    found_reward = True
                    rewards = [(k, ROOM_REWARD[conn_room.id][k]) for k in ROOM_REWARD[conn_room.id].keys()]
                    if self.verbose:
                        print('Found a reward! ', [(r[0], r[1].possible_types) for r in rewards])
                    # Remove check room from the list
                    branch.check_rooms.remove(conn_room.id)

                # Actually connect them.  This also moves the active room to the new room.
                if self.verbose:
                    print('Making connection: ', this_exit, '-->', this_conn)
                branch.connect(this_exit, this_conn)

            ### Process reward & restart loop
            # Identify reward & decide on reward type
            for reward in rewards:
                #reward_types = [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]
                reward_name = reward[0]  #reward_name = slot.event.name()
                slot = reward[1]
                if self.verbose:
                    print('Processing reward: ', reward_name)

                if self.RewardsAvailable[0] == 1 and (slot.possible_types & RewardType.CHARACTER):
                    # This must be a character.
                    if self.verbose:
                        print('\tmust be a character')
                    slot.id, slot.type = choose_reward(RewardType.CHARACTER, characters, espers, items)
                    if self.verbose:
                        print('\tgot ', characters.get_name(slot.id), '!')
                else:
                    # Just choose from among available types
                    if self.verbose:
                        print('\tchoosing from...', slot.possible_types)
                    slot.id, slot.type = choose_reward(slot.possible_types, characters, espers, items)
                    if self.verbose:
                        if slot.type is RewardType.CHARACTER:
                            print('\tgot', characters.get_name(slot.id), '!')
                        elif slot.type is RewardType.ESPER:
                            print('\tgot', espers.get_name(slot.id), '!')
                        elif slot.type is RewardType.ITEM:
                            print('\tgot', items.get_name(slot.id), '!')

                # Update RewardsObtained
                if slot.type is RewardType.CHARACTER:
                    RewardsObtained[0] += 1
                    # If a character, add new areas to the map
                    new_char = characters.DEFAULT_NAME[slot.id]
                    self.apply_key(new_char)   # apply new key to all branches
                    new_areas = CHARACTER_AREAS[new_char]
                    self.distribute_areas(new_areas, method='shortest')  # distribute areas among branches

                elif slot.type is RewardType.ESPER:
                    RewardsObtained[1] += 1

                # Update RewardsAvailable
                if slot.possible_types & RewardType.CHARACTER:
                    self.RewardsAvailable[0] -= 1
                if slot.possible_types & RewardType.ESPER:
                    self.RewardsAvailable[1] -= 1

                if self.verbose:
                    print('\tUpdated Rewards Obtained: ', RewardsObtained[0], 'Characters, ', RewardsObtained[1], 'Espers')
                    print('\tUpdated Rewards Available: ', self.RewardsAvailable[0], 'Characters, ', self.RewardsAvailable[1],
                          'Espers')

                # Update branch_checks
                self.branch_checks[branch_id].remove(reward_name)
                if self.verbose:
                    print('\tUpdated branch checks available:')
                    for i, bc in enumerate(self.branch_checks):
                        print('\t', i, ': ', bc)

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


