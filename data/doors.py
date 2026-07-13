from data.rooms import forced_connections, logical_links, map_shuffle_protected_doors, \
    dungeon_crawl_split_exits, reset_room_tables, room_data, shared_exits
from data.map_exit_extra import exit_data, doors_WOB_WOR, reset_exit_data  # for door descriptions, WOR/WOB equivalent doors
from data.event_exit_data import event_exit_info  # for one-way exit descriptions (ROM-free)
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
        # The v2 DoorPlan artifact (-d2): constructed in mod() and owned by
        # the Data phase; Events receives it (events.ruination_mod binds the
        # ruination view's rewards). None on the legacy path.
        self.plan = None

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
        """Print the shortest route from any world-map room (or ruination
        hub) to destination_room over the final map (-debug_dest). Pure BFS
        with the connecting elements as edge payloads (the legacy version
        walked a networkx Network)."""
        from data.rooms import room_data
        from doors.atlas import exit_description as get_door_name

        try:
            destination_room = int(destination_room)
        except (ValueError, TypeError):
            pass  # room ids can be strings

        # element -> room: exact ownership from the ruination plan's world
        # when available, otherwise a room_data scan (first owner wins).
        owner = {}
        if self.plan is not None and self.plan.ruination is not None:
            w = self.plan.ruination.planner.world
            owner = {e: w.room_ids[h] for e, h in w._owner.items()}
        else:
            for rid, spec in room_data.items():
                for e in spec[0] + spec[1] + spec[2]:
                    owner.setdefault(e, rid)

        adj = {}

        def add_edge(r1, r2, payload):
            if r1 is not None and r2 is not None:
                adj.setdefault(r1, []).append((r2, payload))

        for d1, d2 in door_map[0]:
            add_edge(owner.get(d1), owner.get(d2), ('door', d1, d2))
            add_edge(owner.get(d2), owner.get(d1), ('door', d2, d1))
        for d1, d2 in door_map[1]:
            add_edge(owner.get(d1), owner.get(d2), ('oneway', d1, d2))

        rooms_on_map = set(adj)
        for outs in adj.values():
            rooms_on_map.update(r for r, _ in outs)
        if destination_room not in rooms_on_map:
            print(f"DEBUG ERROR: Destination room '{destination_room}' not found in map.")
            return

        starts = [r for r in rooms_on_map if isinstance(r, str) and
                  (r.startswith('wob-') or r.startswith('wor-') or 'ruin_hub' in r)]
        if not starts:
            print("DEBUG: No world map rooms found in the network.")
            return

        # Multi-source BFS gives the shortest route from ANY start.
        prev = {s: None for s in starts}
        queue = list(starts)
        i = 0
        while i < len(queue) and destination_room not in prev:
            r = queue[i]
            i += 1
            for nxt, payload in adj.get(r, ()):
                if nxt not in prev:
                    prev[nxt] = (r, payload)
                    queue.append(nxt)
        if destination_room not in prev:
            print(f"DEBUG: No path found from any world map room to '{destination_room}'")
            return

        steps = []
        node = destination_room
        while prev[node] is not None:
            r0, payload = prev[node]
            steps.append((r0, payload))
            node = r0
        steps.reverse()

        print("\n" + "=" * 80)
        print(f"DEBUG: SHORTEST ROUTE FROM WORLD MAP TO '{destination_room}'")
        print("=" * 80)
        print(f"Starting from world map room: {node}")
        print(f"Path length: {len(steps) + 1} rooms\n")
        for r0, (kind, e1, e2) in steps:
            if kind == 'door':
                print(f"{r0}: {e1} ({get_door_name(e1)}) <--> {e2} ({get_door_name(e2)})")
            else:
                print(f"{r0}: EXIT {e1} ({get_door_name(e1)}) --> ENTRANCE {e2} ({get_door_name(e2)})")
        print(f"{destination_room}: (destination)")
        print("=" * 80 + "\n")

    def mod(self, characters=None):
        """Plan the door map with the v2 planner (doors/plan) -- one planning
        site for every mode including ruination (Stage E2 cutover; the
        walk-based legacy planner was deleted). Planning consumes the seeded
        global RNG stream in one contiguous window here; the resulting
        DoorPlan is owned by the Data phase (self.plan) and received by
        Events."""
        from doors.plan.modes import plan_for_args
        import random as _random
        self.plan = plan_for_args(self.args, _random, characters=characters)
        if self.args.ruination_mode:
            # Realization timing matches the historical flow: the ruination
            # map is applied to self.map (and postprocessed) in
            # events.ruination_mod, after the Start event has consumed the
            # planned party. self.map stays empty through the rest of the
            # Data phase.
            return
        self.map = self.plan.as_map()

        # Debug: print shortest route if requested
        if self.args.debug_route_destination and self.map:
            for dest in self.args.debug_route_destination:
                self.debug_print_shortest_route(self.map, dest)

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
