from data.map_exit_extra import exit_data, reset_exit_data  # for door descriptions
from data.event_exit_data import event_exit_info, \
    reset_event_exit_addresses  # for one-way exit descriptions (ROM-free)
from log.verbose import vprint, is_enabled as _verbose_enabled


class Doors():
    @property
    def verbose(self):
        """Delegates to the centralized verbose logging flag."""
        return _verbose_enabled()

    def __init__(self, args):
        # Per-build scratch reset. Realization treats exactly two shared
        # tables as scratch: exit_data (the dungeon-crawl destination
        # override edits partner entries) and the event_exit_info runtime
        # address column (filled from the built ROM). Restore both so a
        # second build in the same process (tests, tools, a reroll
        # server) starts clean. Everything else the modes adjust travels
        # on the DoorPlan as a per-plan view, never by table mutation.
        reset_exit_data()
        reset_event_exit_addresses()

        self.args = args
        self.map = []
        # The DoorPlan artifact: constructed in mod() (one planning site,
        # Data phase); Events receives it and binds the ruination view.
        # It carries the mode-adjusted table views (plan.shared_exits,
        # plan.forcing) that realization and the spoiler read.
        self.plan = None

    def debug_print_shortest_route(self, door_map, destination_room):
        """Print the shortest route from any world-map room (or ruination
        hub) to destination_room over the final map (-debug_dest). Pure BFS
        with the connecting elements as edge payloads."""
        from data.rooms import room_data
        from doors.atlas import exit_description as get_door_name

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

        # Ruination's live hubs are the synthetic per-branch rooms
        # ('ruin_hub_0/1/2'), not the 'HUB50-ruin' template they are cut from.
        starts = [r for r in rooms_on_map if isinstance(r, str) and
                  (r.startswith('wob-') or r.startswith('wor-') or
                   r.startswith('ruin_hub'))]
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
        """Plan the door map (doors/plan) -- one planning site for every
        mode including ruination. Planning consumes the seeded
        global RNG stream in one contiguous window here; the resulting
        DoorPlan is owned by the Data phase (self.plan) and received by
        Events."""
        from doors.plan.modes import plan_for_args
        import random as _random
        self.plan = plan_for_args(self.args, _random, characters=characters)
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
            from data.event_exit_data import event_exit_info
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
            for d in self.plan.forcing.keys():
                lcolumn.append(str(d) + ' --> ' + str(self.plan.forcing[d]))
            if len(self.map) > 0:
                lcolumn.append('Map:')
                for m in self.map[0]:
                    lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(door_descr[m[0]]) + ' --> ' + str(
                        door_descr[m[1]]) + ')')
                for m in self.map[1]:
                    lcolumn.append(str(m[0]) + ' --> ' + str(m[1]) + '(' + str(door_descr[m[0]]) + ' --> ' + str(
                        door_descr[m[1]]) + ')')

            section("Door Rando: ", lcolumn, [])
