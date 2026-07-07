from data.rooms import forced_connections, logical_links, map_shuffle_protected_doors, \
    dungeon_crawl_split_exits, reset_room_tables
from data.map_exit_extra import exit_data, doors_WOB_WOR, reset_exit_data  # for door descriptions, WOR/WOB equivalent doors
from data.event_exit_data import event_exit_info  # for one-way exit descriptions (ROM-free)
from data.walks import *
from log.verbose import vprint, is_enabled as _verbose_enabled

# ROOM_SETS lives in data/room_sets.py (ROM-free; Stage A 3b split)
from data.room_sets import ROOM_SETS


class Doors():
    force_vanilla = False  # for debugging purposes

    @property
    def verbose(self):
        """Delegates to the centralized verbose logging flag."""
        return _verbose_enabled()

    def __init__(self, args):
        # Doors (and the mapping code downstream of it) treats the shared data
        # tables as scratch space: shared_exits gets split-exit entries removed,
        # forced_connections gets popped, and room_data lists get edited for
        # map shuffle / -dra root doors / ruination hub rooms. Restore all of
        # them to their pristine import-time state first so that constructing
        # Doors a second time in the same process (retries, tests) starts clean.
        reset_room_tables()
        reset_exit_data()

        # Hard overrides for testing
        self.OVERRIDE = [
            #[1558, 978],  # Connect Ancient Castle spot to Cave in the Veldt WOR
            #[1558, 10],  # Connect Ancient Castle spot to Sabin's House WOB
            #[56, 262],  # Connect Coliseum to Figaro Cave
            #[62, 1261]   # Connect Opera House to Thamasa
            #[1559, 1560]    # Imperial camp west force connection
            #[4, 1218],    # Narshe to esper world
            #[4, 1557],  # Narshe to Floating Continent
            #[10, 674]    #  Sabin's house to Vector Castle interior
            #[1563, 397]    #  Sabin's house to Vector Castle interior
        ]

        # self.rom = rom
        self.args = args

        self.door_rooms = {}
        self.door_descr = {}
        self.area_room_sets = []  # one list of room ids per randomized area (parallel to area_name)
        self.room_doors = {}
        self.room_counts = {}
        # Intentional alias (not a copy): the ruination-mode pop below must be
        # visible to the walk code, which reads the module-level table.
        # reset_room_tables() above makes the mutation safe across builds.
        self.forcing = forced_connections
        self.map = []

        self.match_WOB_WOR = False
        self.combine_areas = True  # make individually called flags get mixed together
        self.area_name = []

        # Attempted-connection budget for each walk (see Network.walk_budget).
        # Healthy walks use ~200 attempts on the biggest area (-drdc) and far
        # fewer elsewhere; 5000 is ~25x that headroom while bounding a
        # pathological start to roughly the old 10s wall-clock timeout this
        # replaces. Unlike the timeout, the budget is deterministic: the same
        # seed stops (and retries) at the same point on any machine.
        # <= 0 disables the budget entirely.
        self.walk_budget = 5000

        # Read in the doors to be randomized.
        room_sets = []
        protect_doors = {}

        if self.args.ruination_mode:
            # Ruination mode overrides all others.
            # It will probably have a custom sorting algorithm, but for now...
            ruin_override = False
            if ruin_override:
                room_sets.append(ROOM_SETS['Ruination'])
                self.area_name.append('Ruination')
            # Door mapping is now done in events.ruination_mod()

            # Split some town exits in ruination mode (same as for dungeon crawl mode):
            for se in dungeon_crawl_split_exits.keys():
                for exit in dungeon_crawl_split_exits[se]:
                    shared_exits[se].remove(exit)

            self.forcing.pop(1079)  # Final room --> Sealed gate connection.  Sealed gate is used differently in -ruin.

        elif self.args.door_randomize_crossworld: # -drx, old version of -drdc
            # Prioritize randomizing all doors.
            # Both options the same room list.  -dra uses drafting; -drdc does not.
            room_sets.append(ROOM_SETS['All'])
            self.area_name.append('All')

        elif self.args.door_randomize_dungeon_crawl:  # -drdc, updated with towns
            # for Dungeon Crawl to work, all doors on the world map should be made into dead ends.
            # This forces the dungeon to be fully connected.

            # Uses 'real' world map rooms, most of which are not dead ends.

            # Split some town exits in dungeon crawl mode:
            for se in dungeon_crawl_split_exits.keys():
                for exit in dungeon_crawl_split_exits[se]:
                    shared_exits[se].remove(exit)
                #print('Updated shared_exits[', se, '] = ', shared_exits[se])

            room_sets.append(ROOM_SETS['DungeonCrawl'])
            self.area_name.append('DungeonCrawl')

            # Redundant: -drdc overrides -maps, -mapx
            self.args.map_shuffle = False  # Do not allow -drdc with -maps or -mapx


        elif self.args.door_randomize_all:  # -dra
            room_sets.append(ROOM_SETS['WoB'])
            self.area_name.append('WoB')
            room_sets.append(ROOM_SETS['WoR'])
            self.area_name.append('WoR')

        elif self.args.door_randomize_each:  # -dre
            # Randomize all areas separately

            # Regardless of shuffle, we want to use mapsafe sets & protections for MtZozo and Zozo-WOR
            use_mapsafe = ['MtZozo', 'Zozo-WOR']
            for key in ROOM_SETS.keys():
                if key not in ['All', 'WoB', 'WoR', 'MapShuffleWOB', 'MapShuffleWOR', 'MapShuffleXW', 'DungeonCrawl', 'Ruination']:
                    if self.args.map_shuffle:
                        # Check for _mapsafe
                        if '_mapsafe' in key or key+'_mapsafe' not in ROOM_SETS.keys():
                            room_sets.append(ROOM_SETS[key])
                            self.area_name.append(key)
                            if key in map_shuffle_protected_doors.keys():
                                d = map_shuffle_protected_doors[key]
                                protect_doors[d] = d + 30000
                    else:
                        if key in [name + '_mapsafe' for name in use_mapsafe]:
                            room_sets.append(ROOM_SETS[key])
                            self.area_name.append(key)
                        elif '_mapsafe' not in key and key not in use_mapsafe:
                            room_sets.append(ROOM_SETS[key])
                            self.area_name.append(key)

            self.combine_areas = False

        else:
            # Randomize separately
            if self.args.door_randomize_umaro:  # -dru
                key = 'Umaro'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_upper_narshe:  # -drun
                key = 'UpperNarshe_WoB'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)
                self.match_WOB_WOR = True

            else:
                if self.args.door_randomize_upper_narshe_wob:  # -drunb
                    key = 'UpperNarshe_WoB'
                    room_sets.append(ROOM_SETS[key])
                    self.area_name.append(key)
                if self.args.door_randomize_upper_narshe_wor:  # -drunr
                    key = 'UpperNarshe_WoR'
                    room_sets.append(ROOM_SETS[key])
                    self.area_name.append(key)

            if self.args.door_randomize_esper_mountain:  # -drem
                key = 'EsperMountain'
                if self.args.map_shuffle:
                    key += '_mapsafe'
                    pd = map_shuffle_protected_doors[key]
                    protect_doors[pd] = pd + 30000  # protect map shuffle
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_owzer_basement:  # -drob
                key = 'OwzerBasement'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_magitek_factory:  # -drmf
                key = 'MagitekFactory'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_sealed_gate:  # -drsg
                key = 'SealedGate'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_zozo_wob:  # -drzb
                key = 'Zozo'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_zozo_wor:  # -drzr  ***
                key = 'Zozo-WOR'  # not using _mapsafe here, it's for -dre only
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_mt_zozo:  # -drmz
                key = 'MtZozo'   # not using _mapsafe here, it's for -dre only
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_lete_river:  # -drlr
                key = 'Lete'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_zone_eater:  # -drze
                key = 'ZoneEater'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_serpent_trench:  # -drst
                key = 'SerpentTrench'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_burning_house:  # -drbh
                key = 'BurningHouse'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_daryls_tomb:  # -drdt
                key = 'DarylsTomb'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_south_figaro_cave_wob:  # -drsfcb
                key = 'SouthFigaroCaveWOB'
                if self.args.map_shuffle:
                    key += '_mapsafe'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_phantom_train:  # -drpt
                key = 'PhantomTrain'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_cyans_dream:  # -drcd
                key = 'CyansDream'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_mt_kolts:  # -drmk
                key = 'MtKolts'
                if self.args.map_shuffle:
                    key += '_mapsafe'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.args.door_randomize_veldt_cave:  # -drvc
                key = 'VeldtCave'
                if self.args.map_shuffle:
                    key += '_mapsafe'
                room_sets.append(ROOM_SETS[key])
                self.area_name.append(key)

            if self.combine_areas:
                temp = []
                temp_name = ''
                for r_id in range(len(room_sets)):
                    temp.extend(room_sets[r_id])
                    temp_name += self.area_name[r_id] + '_'
                if len(temp) > 0:
                    room_sets = [temp]
                    self.area_name = [temp_name]

        # Deconflict door_randomize and map_shuffle
        if (self.args.door_randomize_all or self.args.door_randomize_crossworld or self.args.door_randomize_each) \
                and self.args.map_shuffle:
            ignore_maps = [1552, 1553]  # don't include zone-eater as doors if included as transitions
            shuffle_rooms = [r for r in ROOM_SETS['MapShuffleWOB']] + [r for r in ROOM_SETS['MapShuffleWOR']]
            for r in shuffle_rooms:
                for dk in [d for d in room_data[r][0]]:
                    if dk in ignore_maps:
                        vprint('removing ', dk, ' from ', r)
                        room_data[r][0].remove(dk)
                    if dk in protect_doors.keys():
                        vprint('protecting ', dk, ' in ', r, ' --> ', protect_doors[dk])
                        room_data[r][0].remove(dk)
                        room_data[r][0].append(protect_doors[dk])

            ignore_doors = [1554, 1555]  # don't include phoenix cave in doors if doing map shuffle
            for a in room_data.keys():
                if a not in shuffle_rooms:
                    for dk in [d for d in room_data[a][0]]:
                        if dk in ignore_doors:
                            vprint('removing ', dk, ' from ', a)
                            room_data[a][0].remove(dk)

        if self.args.map_shuffle_separate:  # -maps
            # Separately:  add rooms for WOR, WOB
            room_sets.append(ROOM_SETS['MapShuffleWOB'])
            self.area_name.append('MapShuffleWOB')
            room_sets.append(ROOM_SETS['MapShuffleWOR'])
            self.area_name.append('MapShuffleWOR')

        elif self.args.map_shuffle_crossworld:  # -mapx
            room_sets.append(ROOM_SETS['MapShuffleXW'])
            self.area_name.append('MapShuffleXW')

        # One room list per area to randomize (parallel to self.area_name).
        self.area_room_sets.extend(room_sets)

    def debug_print_shortest_route(self, door_map, destination_room):
        """Find and print the shortest route from any world map room to the destination room.

        Args:
            door_map: The mapping result [[door_pairs], [oneway_pairs]]
            destination_room: The target room ID (int or string)
        """
        import networkx as nx
        from data.rooms import room_data
        from data.walks import Network

        # Convert destination_room to appropriate type (try int first, then keep as string)
        try:
            destination_room = int(destination_room)
        except (ValueError, TypeError):
            pass  # Keep as string

        # Build a fresh Network with all rooms from room_data
        for area in self.area_room_sets:
            if destination_room in area:
                walks = Network(area)

                # Add edges from two-way door pairs
                for d1, d2 in door_map[0]:
                    r1 = walks.rooms.get_room_from_element(d1)
                    r2 = walks.rooms.get_room_from_element(d2)
                    if r1 and r2:
                        walks.net.add_edge(r1.id, r2.id)
                        walks.net.add_edge(r2.id, r1.id)  # Two-way connection

                # Add edges from one-way pairs
                for d1, d2 in door_map[1]:
                    r1 = walks.rooms.get_room_from_element(d1)
                    r2 = walks.rooms.get_room_from_element(d2)
                    if r1 and r2:
                        walks.net.add_edge(r1.id, r2.id)  # One-way connection only

                # Get all world map rooms (wob-* and wor-*)
                world_map_rooms = [room_id for room_id in walks.rooms.rooms
                                  if isinstance(room_id, str) and (room_id.startswith('wob-') or room_id.startswith('wor-'))]

                if not world_map_rooms:
                    print("DEBUG: No world map rooms found in the network.")
                    return

                # Validate destination room exists
                if destination_room not in walks.rooms.rooms:
                    print(f"DEBUG ERROR: Destination room '{destination_room}' not found in network.")
                    print(f"Available rooms: {sorted([str(r) for r in walks.rooms.rooms])}")
                    return

                # Find shortest path from any world map room to destination
                shortest_path = None
                shortest_length = float('inf')
                start_room = None

                for wm_room in world_map_rooms:
                    try:
                        path = nx.shortest_path(walks.net, source=wm_room, target=destination_room)
                        if len(path) < shortest_length:
                            shortest_path = path
                            shortest_length = len(path)
                            start_room = wm_room
                    except nx.NetworkXNoPath:
                        continue  # No path from this world map room

                if shortest_path is None:
                    print(f"DEBUG: No path found from any world map room to '{destination_room}'")
                    return

                # Format and print the route
                print("\n" + "="*80)
                print(f"DEBUG: SHORTEST ROUTE FROM WORLD MAP TO '{destination_room}'")
                print("="*80)
                print(f"Starting from world map room: {start_room}")
                print(f"Path length: {len(shortest_path)} rooms\n")

                # Get door connections for each step
                for i in range(len(shortest_path) - 1):
                    current_room = shortest_path[i]
                    next_room = shortest_path[i + 1]

                    # Find the door(s) connecting these rooms
                    connecting_doors = self._find_connecting_doors(walks, door_map, current_room, next_room)

                    if connecting_doors:
                        door_desc = connecting_doors
                    else:
                        door_desc = "(unknown connection)"

                    print(f"{current_room}: {door_desc}")

                print(f"{shortest_path[-1]}: (destination)")
                print("="*80 + "\n")

    def _find_connecting_doors(self, walks, door_map, room1, room2):
        """Find the door(s) connecting two rooms using the door mapping."""
        # Helper to get door description from exit_data or event_exit_info
        def get_door_name(door_id):
            if door_id in exit_data:
                return exit_data[door_id][1]
            elif door_id in event_exit_info:
                return event_exit_info[door_id][4]  # description is at index 4
            else:
                return f"Door {door_id}"

        # Check if there's a reverse edge (for two-way doors)
        has_reverse = walks.net.has_edge(room2, room1)

        # Search through two-way door mappings
        for d1, d2 in door_map[0]:
            r1 = walks.rooms.get_room_from_element(d1)
            r2 = walks.rooms.get_room_from_element(d2)
            if not r1 or not r2:
                continue

            if (r1.id == room1 and r2.id == room2) or (r1.id == room2 and r2.id == room1):
                arrow = "<-->" if has_reverse else "-->"
                if (r1.id == room1 and r2.id == room2):
                    return f" {d1} ({get_door_name(d1)}) {arrow} {d2} ({get_door_name(d2)})"
                else:
                    return f" {d2} ({get_door_name(d2)}) {arrow} {d1} ({get_door_name(d1)})"

        # Search through one-way exit mappings
        for d1, d2 in door_map[1]:
            r1 = walks.rooms.get_room_from_element(d1)
            r2 = walks.rooms.get_room_from_element(d2)
            if not r1 or not r2:
                continue

            if r1.id == room1 and r2.id == room2:
                return f"EXIT {d1} ({get_door_name(d1)}) --> ENTRANCE {d2} ({get_door_name(d2)})"

        return "(connection not found in map)"

    def mod(self):
        # Create list of randomized connections using walks
        full_map = [[], []]

        if self.args.door_randomize_crossworld:
            all_id = self.area_name.index('All')
            # Make a meta-World Map 'root' room that connects to all the 'root-zone' rooms.
            # This encodes that you can reach all roots from all roots.
            # This is not done for old door-randomize-dungeon-crawl (using 'All' room)
            root_rooms = [r for r in self.area_room_sets[all_id] if 'root' in str(r)]
            offset = 10000
            root_map = [[offset + i, offset + len(root_rooms) + i] for i in range(len(root_rooms))]
            root_doors = []
            for ri in range(len(root_rooms)):
                room_data[root_rooms[ri]][0].append(root_map[ri][0])
                root_doors.append(root_map[ri][1])
                self.forcing[root_map[ri][1]] = [root_map[ri][0]]
            self.area_room_sets[all_id].append('root')
            room_data['root'] = [ root_doors, [], [], [], {}, 0]
            self.room_counts['root'] = [len(r) for r in room_data['root'][:-1]]
            self.room_doors['root'] = [r for r in room_data['root'][:-1]]
        elif self.args.door_randomize_all:
            areas = ['WoB', 'WoR']
            offset_0 = 0
            store_root_doors = []
            for name in areas:
                a_id = self.area_name.index(name)
                # Make a meta-World Map 'root' room that connects to all the 'root-zone' rooms.
                # This encodes that you can reach all roots from all roots.
                # This is not done for old door-randomize-dungeon-crawl (using 'All' room)
                root_rooms = [r for r in self.area_room_sets[a_id] if 'root' in str(r)]
                offset = 10000 + offset_0
                root_map = [[offset + i, offset + len(root_rooms) + i] for i in range(len(root_rooms))]
                root_doors = []
                for ri in range(len(root_rooms)):
                    room_data[root_rooms[ri]][0].append(root_map[ri][0])
                    root_doors.append(root_map[ri][1])
                    self.forcing[root_map[ri][1]] = [root_map[ri][0]]
                rn = 'root_'+name
                self.area_room_sets[a_id].append(rn)
                room_data[rn] = [ root_doors, [], [], [], {}, 0]
                self.room_counts[rn] = [len(r) for r in room_data[rn][:-1]]
                self.room_doors[rn] = [r for r in room_data[rn][:-1]]
                # Prep for next area
                offset_0 += 2*len(root_rooms)
                store_root_doors.extend([d for d in root_doors])
            # Store root doors for cleanup phase
            root_doors = [d for d in store_root_doors]

        if self.args.map_shuffle_crossworld:
            xw_id = self.area_name.index('MapShuffleXW')
            # Force a connection between the WoB and WoR.
            # This encodes that you can reach these rooms from each other.
            offset = 20000
            xw_map = [[offset, offset + 1]]
            xw_root_doors = xw_map[0]
            room_data['shuffle-wob'][0].append(xw_map[0][0])
            room_data['shuffle-wor'][0].append(xw_map[0][1])
            self.forcing[xw_map[0][0]] = [xw_map[0][1]]

        for area_id in self.area_name:
            ai = self.area_name.index(area_id)
            area = self.area_room_sets[ai]

            vprint('Now Randomizing:' , area_id)

            if len(area) > 0:

                # Initialize the Walk Network
                walks = Network(area)
                vprint('Initial Count: ', walks.rooms.count)

                walks.ApplyImmediateKeys(self.args)
                walks.ForceConnections(self.forcing)  # Force initial connections, if any

                vprint('Count after forced connections: ', walks.rooms.count)

                walks.attach_dead_ends()  # Connect all the dead ends.

                # Select starting node
                if area_id == 'All':
                    # Start in the root room
                    string_rooms = [R for R in walks.rooms.rooms if isinstance(R, str)]
                    root_room_id = string_rooms[[sr.find('root') >= 0 for sr in string_rooms].index(True)]
                    start_room_ids = [root_room_id]
                elif area_id == 'DungeonCrawl':
                    # Try starting from the biggest remaining room?
                    room_sizes = [(r, len(walks.rooms.get_room(r).doors)) for r in walks.rooms.rooms]
                    max_size = max([r[1] for r in room_sizes])
                    start_room_ids = [r[0] for r in room_sizes if r[1] == max_size]

                elif len([r for r in walks.rooms.rooms if 'root' in str(r)]) > 0:
                    # Choose a root room to begin
                    # This might fail due to forcing.
                    start_room_ids = [r for r in walks.rooms.rooms if 'root' in str(r)]
                else:
                    # Choose a random room
                    start_room_ids = [n for n in walks.net.nodes]

                start_room_id = random.choice(start_room_ids)
                walks.active = start_room_id   # walks.rooms.rooms.index(walks.rooms.get_room(start_room_id))

                # Connect the network
                if self.walk_budget <= 0:
                    # Directly connect the network, no budget
                    fully_connected = walks.connect_network()
                else:
                    # connect_network only mutates a deepcopy of the network, so a
                    # failed or budget-exhausted attempt can be retried on the same
                    # walks object; each retry re-rolls the start room and random
                    # order. The budget list is shared by every copy the recursive
                    # search makes, so it bounds the whole attempt.
                    max_attempts = 5
                    fully_connected = None
                    last_error = None
                    for attempt in range(max_attempts):
                        walks.walk_budget = [self.walk_budget]
                        try:
                            vprint('\tstarting room... ', walks.active)
                            fully_connected = walks.connect_network()
                        except WalkBudgetExceeded as e:
                            last_error = e
                            vprint(f"Walk budget ({self.walk_budget}) exhausted")
                        except Exception as e:
                            last_error = e
                            vprint(f"Network connection failed: {e}")
                        if fully_connected is not None:
                            vprint(f'\twalk budget used: '
                                   f'{self.walk_budget - walks.walk_budget[0]}/{self.walk_budget}')
                            break
                        print(f'Door connection attempt {attempt + 1}/{max_attempts} for area '
                              f'{area_id} failed or exceeded budget; retrying')
                        walks.active = random.choice(start_room_ids)
                    walks.walk_budget = None
                    if fully_connected is None:
                        raise Exception(f'Door randomization failed for area {area_id} '
                                        f'after {max_attempts} attempts') from last_error

                fcm_doors = [m for m in fully_connected.map[0]]
                fcm_oneways = [m for m in fully_connected.map[1]]

                # Copy the results into the full map
                full_map[0].extend(fcm_doors)
                full_map[1].extend(fcm_oneways)

        # Postprocess the mapping algorithm results
        # Patch out logical link
        ll = {}
        for l in logical_links:
            ll[l[0]] = l[1]
            ll[l[1]] = l[0]
        llink = {}
        # Iterate over a snapshot: removing from the live list while iterating
        # skips the element after each removal (could silently drop a link pair).
        for m in list(full_map[0]):
            remove_flag = False
            if m[0] in ll.keys():
                llink[m[0]] = m[1]
                remove_flag = True
            if m[1] in ll.keys():
                llink[m[1]] = m[0]
                remove_flag = True
            if remove_flag:
                full_map[0].remove(m)
                vprint('Removing logical link: ', m)
        for L in logical_links:
            if L[0] in llink.keys():
                patched_m = [llink[L[0]], llink[L[1]]]
                full_map[0].append(patched_m)
                vprint('Patching logical link: ', patched_m)

        # Process OVERRIDE
        for op in self.OVERRIDE:
            target = set(op)
            containing_pairs = []
            pair_indices = []
            for i, pair in enumerate(full_map[0]):
                if op[0] in pair or op[1] in pair:
                    containing_pairs.append(set(pair))
                    pair_indices.append(i)
            if len(containing_pairs) == 2:
                other_elements = (containing_pairs[0] | containing_pairs[1]) - target
                # new_map = full_map[0].copy()
                print('OVERRIDE: ', full_map[0][pair_indices[0]], "-->", list(target), ', ', full_map[0][pair_indices[1]],
                      "-->", list(other_elements))
                full_map[0][pair_indices[0]] = list(target)
                full_map[0][pair_indices[1]] = list(other_elements)
            else:
                print('warning: did not find ', op, '. found pairs: ', containing_pairs)

        # Append shared doors to the full_map
        for m in full_map[0]:
            if m[0] in shared_exits.keys():
                for se in shared_exits[m[0]]:
                    # Send shared exits to the same destination
                    full_map[0].append([se, m[1]])
            if m[1] in shared_exits.keys():
                for se in shared_exits[m[1]]:
                    # Send shared exits to the same destination
                    full_map[0].append([m[0], se])

        # Remove root doors
        if self.args.door_randomize_all or self.args.door_randomize_crossworld:
            # Remove the (logical) root doors from the full_map
            full_map[0] = [m for m in full_map[0] if m[0] not in root_doors and m[1] not in root_doors]
        if self.args.map_shuffle_crossworld:
            full_map[0] = [m for m in full_map[0] if m[0] not in xw_root_doors and m[1] not in xw_root_doors]


        if self.match_WOB_WOR:
            # Make the WOR full_map match the WOB full_map in relevant areas
            vprint('Mapping WoR to match WoB ...')
            WOR_map = []
            for m in full_map[0]:
                if m[0] in doors_WOB_WOR.keys():
                    WOR_map.append([doors_WOB_WOR[j] for j in m])
            full_map[0].extend(WOR_map)

        if self.force_vanilla:
            # disregard everything above.  Force vanilla connections to be written.
            vprint('OVERWRITING MAP: ')
            vprint(full_map)
            vanilla_map = [tuple( sorted((m[0], exit_data[m[0]][0])) ) for m in full_map[0]] + \
                          [tuple( sorted((m[1], exit_data[m[1]][0])) ) for m in full_map[0]]
            vanilla_map = list(set(vanilla_map))
            vanilla_oneways = [ [m[0], m[0]+1000] for m in full_map[1] ]
            full_map = [vanilla_map, vanilla_oneways]
            print(full_map)

        # Assess full_map for repeats
        all_shared = []
        for s in shared_exits.keys():
            all_shared += shared_exits[s]
        doors_used = [d[0] for d in full_map[0] if d[0] not in all_shared and d[1] not in all_shared] \
                     + [d[1] for d in full_map[0] if d[0] not in all_shared and d[1] not in all_shared]
        unique_doors = set(doors_used)
        if len(unique_doors) < len(doors_used):
            repeat_doors = [d for d in unique_doors if doors_used.count(d) > 1]
            repeat_doors.sort()
            print('Warning: repeat doors:', repeat_doors)
            for m in full_map[0]:
                if m[0] in repeat_doors:
                    print('\t',m)
                elif m[1] in repeat_doors:
                    print('\t',m)

        # Debug: print shortest route if requested (after all postprocessing)
        if self.args.debug_route_destination:
            for dest in self.args.debug_route_destination:
                self.debug_print_shortest_route(full_map, dest)

        # Return full_map
        self.map = full_map

    def print(self):
        if self.args.spoiler_log:
            from log import SECTION_WIDTH, section, format_option
            lcolumn = []

            # Construct door descriptions
            from data.event_exit_info import event_exit_info
            door_descr = {}
            for mmm in self.map:
                for m in mmm:
                    for d in m:
                        if d in exit_data.keys():
                            door_descr[d] = exit_data[d][1]
                        elif d in event_exit_info.keys():
                            door_descr[d] = event_exit_info[d][4]
                        elif d-1000 in event_exit_info.keys():
                            door_descr[d] = event_exit_info[d-1000][4] + 'DESTINATION'
                        else:
                            door_descr[d] = 'UNKNOWN'

            lcolumn.append('Forced connections:')
            for d in self.forcing.keys():
                lcolumn.append(str(d) + ' --> ' + str(self.forcing[d]))
            if len(self.map) > 0:
                lcolumn.append('Map:')
                for m in self.map[0]:
                    lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(door_descr[m[0]]) + ' --> ' + str(
                        door_descr[m[1]]) + ')')
                for m in self.map[1]:
                    lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(door_descr[m[0]]) + ' --> ' + str(
                        door_descr[m[1]]) + ')')

            section("Door Rando: ", lcolumn, [])
