from event.event import *
from event.event_reward import CHARACTER_ESPER_ONLY_REWARDS, RewardType, choose_reward, weighted_reward_choice
from data.rooms import room_data
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

class ruination_map():
    # Class to organize data for mapping out ruination mode branches
    RewardsAvailable = [0, 0]   # [# possible characters, # possible espers]
    PARTY = []
    Requested = [3, 0]
    branches = [None, None, None]
    branch_checks = [ [], [], []]   # checks available on each branch, stored locally
    AreasUsed = set()   # use a set to avoid duplicates
    keychain = set()   # global keychain


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
        for character in self.PARTY:
            self.AreasUsed.update(CHARACTER_AREAS[character])
        #print(self.AreasUsed)

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
            self.branches[i] = branch

        # Distribute areas to the branches
        self.distribute_areas(self.AreasUsed)
        print(self.RewardsAvailable)

        # Apply keys to branches
        for branch in self.branches:
            for k in self.keychain:
                branch.apply_key(k)

        #print(branch.original_room_ids)

    def distribute_areas(self, areas, method = 'random'):
        # Distribute new areas among the branches
        branch_areas = [ [], [], []]

        if method is 'random':
            for area in areas:
                this_index = random.randint(0, 2)
                branch_areas[this_index].append(area)
        elif method is 'distribute':
            seed = random.randint(0, 2)
            use_index = [(i + seed) % 3 for i in range(len(self.AreasUsed))]
            random.shuffle(use_index)
            for area in self.AreasUsed:
                this_index = use_index.pop()
                branch_areas[this_index].append(area)
        elif method is 'shortest':
            for area in areas:
                shortest_index = [len(b.net.original_room_ids) for b in self.branches]
                use_index = shortest_index.index(min(shortest_index))
                branch_areas[use_index].append(area)
        elif method is 'least_checks':
            for area in areas:
                shortest_index = [len(b) for b in self.branch_checks]
                use_index = shortest_index.index(min(shortest_index))
                branch_areas[use_index].append(area)

        # Expand to list of rooms to add to each branch
        branch_rooms = [[], [], []]
        for i, areas in enumerate(branch_areas):
            for area in areas:
                branch_rooms[i].extend(RUIN_ROOM_SETS[area])

        # Collect which checks are available, including how many can be characters and how many espers
        for room in ROOM_REWARD:
            which_branch = next((i for i, branch in enumerate(branch_rooms) if room in branch), -1)
            if which_branch >= 0:
                for reward_id in ROOM_REWARD[room].keys():
                    self.branch_checks[i].append(reward_id)
                    reward = ROOM_REWARD[room][reward_id]
                    # print(reward_id, i, this_type.possible_types)
                    if reward.possible_types & RewardType.CHARACTER:
                        self.RewardsAvailable[0] += 1
                    if reward.possible_types & RewardType.ESPER:
                        self.RewardsAvailable[1] += 1

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

        while (RewardsObtained[0] < self.Requested[0] or RewardsObtained[1] < self.Requested[1]):
            # Pick a branch with an active reward
            branch_id = random.choice([b for b in range(3) if len(self.branch_checks[b]) > 0])
            branch = self.branches[branch_id]

            # Force any forced connections before starting
            branch.ForceConnections(forced_connections)

            # Apply any keys we have found in other branches
            for k in self.keychain.difference(branch.keychain):
                branch.apply_key(k)

            found_reward = False
            while not found_reward:
                # Attach hubs & trapdoors until none are left (create all branches)

                # Choose an exit from the active room.
                # Only allow trap doors if there is at least one entrance to the active room
                active_room = branch.rooms.get_room(branch.active)
                all_entrances = [active_room.doors()] + [active_room.pits()]
                print('Active room: ', branch.active, '.  All entrances: ', all_entrances)
                allow_traps = len(all_entrances) >= 1

                # Look at unconnected hubs.
                new_hub_door_conns = branch.get_available_hub_connections(type=0, exclude=branch.active)
                new_hub_pit_conns = branch.get_available_hub_connections(type=1, exclude=branch.active)

                # Select which exits are permissable based on what is available.
                # WE HAVE TO BE CAREFUL to not fully map a branch before we run out of checks.
                # Imagine if a branch had only Serpent Trench on it.  hub --> crescent --> ST has no way back.
                # (a) do this in a nested way, as before?
                # (b) catch the errors in one pass?  Active room + upstream must always have entrances.
                all_exits = []
                available_connections = [[], []]
                if len(new_hub_door_conns) > 0:
                    all_exits += [active_room.doors]
                    available_connections[0] += new_hub_door_conns
                if len(new_hub_pit_conns) > 0 and allow_traps:
                    all_exits += [active_room.traps]
                    available_connections[1] += new_hub_pit_conns

                # Handle failure modes: no exits available
                if len(all_exits) == 0:
                    # I think the main way we get here is if there are no more hub rooms, and a check is in a dead end.
                    check_door_cons = branch.get_all_check_connections(type=0)
                    check_pit_cons = branch.get_all_check_connections(type=1)
                    if len(check_door_cons) > 0:
                        all_exits += [active_room.doors]
                        available_connections[0] += check_door_cons
                    elif len(check_pit_cons) > 0 and allow_traps:
                        all_exits += [active_room.traps]
                        available_connections[1] += check_pit_cons
                    else:
                        print('No legal exits!')
                        break  # hopefully another branch is valid & can add some units to this one.

                # If any exits are forced, apply them
                forced_exits = [e for e in all_exits if e in forced_connections.keys()]
                if len(forced_exits) > 0:
                    this_exit = forced_exits.pop()
                    this_conn = forced_connections[this_exit]
                    print('Found forced exit!', this_exit, '-->', this_conn)
                else:
                    this_exit = random.choice(all_exits)
                    this_type = active_room.element_type(this_exit)
                    print('All allowed exits:', all_exits, '.  Choose: ', this_exit, '(type ', this_type, ')')
                    this_conn = random.choice(available_connections[this_type])
                    print('Available connections:', available_connections[this_type], '. Choose: ', this_conn)

                # Check if a reward was found
                conn_room = branch.rooms.get_room_from_element(this_conn)
                if conn_room.id in ROOM_REWARD.keys():
                    # Stop if a reward was found
                    found_reward = True
                    rewards = [ROOM_REWARD[k] for k in ROOM_REWARD[conn_room.id].keys()]

                # Actually connect them.
                branch.connect(this_exit, this_conn)

            ### Process reward & restart loop
            # Identify reward & decide on reward type
            for slot in rewards:
                #reward_types = [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]
                if self.RewardsAvailable[0] == 1 and (slot.possible_types & RewardType.CHARACTER):
                    # This must be a character.
                    slot.id, slot.type = choose_reward(RewardType.CHARACTER, characters, espers, items)
                else:
                    # Just choose from among available types
                    slot.id, slot.type = choose_reward(slot.possible_types, characters, espers, items)

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

        # After satisfying conditions, fully connect map
        for branch in self.branches:
            terminus_id = branch.terminus
            terminus_entrances = set(room_data[terminus_id][0] + room_data[terminus_id][2])

            active_room = branch.rooms.get_room(branch.active)
            print('Closing branch...\n\t', branch.active, active_room.doors, active_room.traps)
            while (len(active_room.doors) + len(active_room.traps)) > 0:
                # Connect trapdoors, if any
                if len(active_room.traps) > 0:
                    this_exit = random.choice(active_room.traps)
                    all_pits = [p for p in branch.pits]
                    if len(all_pits) > 0:
                        if len(terminus_entrances.intersection(all_pits)) > 0:
                            # Attach Terminus, if available
                            this_conn = terminus_entrances.intersection(all_pits).pop()
                        else:
                            this_conn = random.choice(all_pits)
                    else:
                        # This shouldn't happen!
                        raise Exception
                else:
                    this_exit = random.choice(active_room.doors)
                    all_doors = [d for d in branch.doors if d is not this_exit]
                    if len(terminus_entrances.intersection(all_doors)) > 0:
                        # Attach Terminus, if available
                        this_conn = terminus_entrances.intersection(all_doors).pop()
                    else:
                        this_conn = random.choice(all_doors)

                # Connect them
                branch.connect(this_exit, this_conn)

                active_room = branch.rooms.get_room(branch.active)
                print('\t', branch.active, active_room.doors, active_room.traps)

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

class RuinationBranch(Network):
    def __init__(self, rooms):
        super().__init__(rooms)
        self.dead_ends = []
        self.check_rooms = []
        self.classify_rooms(rooms)

    def add_room(self, room_id):
        super().add_room(room_id)
        self.classify_rooms([room_id])
        # We need a custom handler for return from Lete River!
        if room_id is 'LeteRiver3':
            # add pit 3039 to ruin_hub
            hub_room_id = [n for n in self.net.nodes if 'ruin_hub' in n][0]
            hub_room = self.rooms.get_room(hub_room_id)
            hub_room.add_pits([3039])

    def classify_rooms(self, rooms):
        for room in rooms:
            if room in RUIN_TERMINI:
                self.terminus = room

            if self.is_dead_end(room):
                self.dead_ends.append(room)

            if room in ROOM_REWARD.keys():
                self.check_rooms.append(room)

    def get_available_hubs(self, exclude=None):
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)
        return [r for r in self.net.nodes if r not in self.dead_ends and r not in exclude]

    def get_available_hub_connections(self, conn_type=0):
        hub_ids = self.get_available_hubs()
        hub_conns = []
        for hub_id in hub_ids:
            hub = self.rooms.get_room(hub_id)
            if conn_type == 0:
                hub_conns.extend(hub.doors)
            elif conn_type == 1:
                hub_conns.extend(hub.pits)
        return hub_conns

    def get_all_check_connections(self, conn_type=0):
        conns = []
        for room_id in self.check_rooms:
            room = self.rooms.get_room(room_id)
            if conn_type == 0:
                conns.extend(room.doors)
            elif conn_type == 1:
                conns.extend(room.pits)
        return conns

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


