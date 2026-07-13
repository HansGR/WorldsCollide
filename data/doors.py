from data.rooms import forced_connections, map_shuffle_protected_doors, \
    dungeon_crawl_split_exits, reset_room_tables, room_data, shared_exits
from data.map_exit_extra import exit_data, reset_exit_data  # for door descriptions
from data.event_exit_data import event_exit_info  # for one-way exit descriptions (ROM-free)
from log.verbose import vprint, is_enabled as _verbose_enabled

# ROOM_SETS lives in data/room_sets.py (ROM-free; Stage A 3b split)
from data.room_sets import ROOM_SETS


def apply_mode_table_adjustments(args):
    """Deliver the correct initial state of the room/exit tables for the
    active mode, before planning connects them (applied once per build;
    reset_room_tables()/reset_exit_data() make it idempotent across
    retries and tests). Three adjustments, each with its own reason:

    1. -ruin: drop the forced connection from the penultimate Sealed Gate
       Cave room to the Sealed Gate (forced_connections[1079]). Ruination
       uses the Sealed Gate differently from every other mode -- as a
       branch terminus -- and it must not be pinned to the same spot.
    2. -ruin and -drdc: split some town exits (dungeon_crawl_split_exits
       out of shared_exits) so those towns can have two different exits,
       making them walk-through rooms instead of dead ends.
    3. Door randomization (-dra/-drx/-dre) combined with map shuffle:
       Zone Eater entry/exit is handled as doors (1552/1553) by pure map
       shuffle for simplicity, but as traps (2040/2041) by the door-rando
       modes. When both are active, traps win: the door ids are removed
       from the shuffle rooms. Phoenix Cave's doors (1554/1555) leave the
       door pools for the same both-modes-active reason, and the
       map_shuffle_protected_doors get their 30000+ stand-ins swapped
       into the shuffle rooms.
    """
    if args.ruination_mode or args.door_randomize_dungeon_crawl:
        for se in dungeon_crawl_split_exits.keys():
            for exit in dungeon_crawl_split_exits[se]:
                shared_exits[se].remove(exit)

    if args.ruination_mode:
        forced_connections.pop(1079)

    if args.door_randomize_dungeon_crawl:
        args.map_shuffle = False    # -drdc overrides -maps/-mapx

    if (args.door_randomize_all or args.door_randomize_crossworld
            or args.door_randomize_each) and args.map_shuffle:
        from doors.plan.modes import door_rando_pool_keys
        protect_doors = {}
        for key in door_rando_pool_keys(args):
            if key in map_shuffle_protected_doors:
                d = map_shuffle_protected_doors[key]
                protect_doors[d] = d + 30000
        ignore_maps = [1552, 1553]  # zone eater: traps win over doors
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

        ignore_doors = [1554, 1555]  # phoenix cave leaves the door pools
        for a in room_data.keys():
            if a not in shuffle_rooms:
                for dk in [d for d in room_data[a][0]]:
                    if dk in ignore_doors:
                        vprint('removing ', dk, ' from ', a)
                        room_data[a][0].remove(dk)


class Doors():
    force_vanilla = False  # for debugging purposes

    @property
    def verbose(self):
        """Delegates to the centralized verbose logging flag."""
        return _verbose_enabled()

    def __init__(self, args):
        # Restore the shared data tables to their pristine import-time
        # state (constructing Doors twice in one process -- tests, tools --
        # must start clean), then apply the per-mode adjustments.
        reset_room_tables()
        reset_exit_data()

        self.args = args
        self.door_rooms = {}   # populated and read by realization (data/maps.py)
        self.door_descr = {}   # read by realization for spoiler descriptions
        # Intentional alias (not a copy): the -ruin pop in
        # apply_mode_table_adjustments must be visible to the spoiler print.
        self.forcing = forced_connections
        self.map = []
        # The DoorPlan artifact: constructed in mod() (one planning site,
        # Data phase); Events receives it and binds the ruination view.
        self.plan = None

        apply_mode_table_adjustments(args)

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
