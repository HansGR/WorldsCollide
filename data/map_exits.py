from data.map_exit import ShortMapExit, LongMapExit
from data.map_exit_extra import exit_data as exit_data_orig
from data.map_exit_extra import exit_data_patch

from data.map_event import MapEvent
from data.rooms import room_data, force_update_parent_map

from instruction import field

from memory.space import Allocate, Bank, Write

class MapExits():
    SHORT_EXIT_COUNT = 0x469
    LONG_EXIT_COUNT = 0x98

    SHORT_DATA_START_ADDR = 0x1fbf02
    LONG_DATA_START_ADDR = 0x2df882

    def __init__(self, rom):
        self.rom = rom
        self.short_exits = []
        self.long_exits = []
        self.exit_original_data = {}
        self.exit_type = {}

        self.read()

        # f = open('exit_original_info.txt','w')
        # f.write('# exit_ID: [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]\n')
        # for li in self.exit_original_data.keys():
        #     write_string = str(li)
        #     write_string += ': '+str(self.exit_original_data[li])
        #     write_string += '. '+str(self.exit_raw_data[li])+'\n'
        #     f.write(write_string)
        # f.close()

    def read(self):
        global_counter = 0
        for exit_index in range(self.SHORT_EXIT_COUNT):
            exit_data_start = self.SHORT_DATA_START_ADDR + exit_index * ShortMapExit.DATA_SIZE
            exit_data = self.rom.get_bytes(exit_data_start, ShortMapExit.DATA_SIZE)

            new_exit = ShortMapExit()
            new_exit.from_data(exit_data)
            # added for exit rando mod
            new_exit.index = global_counter
            global_counter = global_counter + 1
            # added for exit rando mod
            self.short_exits.append(new_exit)
            self.exit_type[new_exit.index] = 'short'

            # Archive original data for randomizing
            self.exit_original_data[new_exit.index] = [new_exit.dest_x, new_exit.dest_y, new_exit.dest_map,
                                                              new_exit.refreshparentmap, new_exit.enterlowZlevel,
                                                              new_exit.displaylocationname, new_exit.facing,
                                                              new_exit.unknown]

        for exit_index in range(self.LONG_EXIT_COUNT):
            exit_data_start = self.LONG_DATA_START_ADDR + exit_index * LongMapExit.DATA_SIZE
            exit_data = self.rom.get_bytes(exit_data_start, LongMapExit.DATA_SIZE)

            new_exit = LongMapExit()
            new_exit.from_data(exit_data)
            # added for exit rando mod
            new_exit.index = global_counter
            global_counter = global_counter + 1
            # added for exit rando mod
            self.long_exits.append(new_exit)
            self.exit_type[new_exit.index] = 'long'

            # Archive original data for randomizing
            self.exit_original_data[new_exit.index] = [new_exit.dest_x, new_exit.dest_y, new_exit.dest_map,
                                                       new_exit.refreshparentmap, new_exit.enterlowZlevel,
                                                       new_exit.displaylocationname, new_exit.facing,
                                                       new_exit.unknown]

        # For door mapping to work, all exits must be explicit (i.e. patch out "return to parent map").
        for e in exit_data_patch.keys():
            self.exit_original_data[e] = exit_data_patch[e](self.exit_original_data[e])

    def write(self):
        for exit_index, exit in enumerate(self.short_exits):
            exit_data = exit.to_data()
            exit_data_start = self.SHORT_DATA_START_ADDR + exit_index * ShortMapExit.DATA_SIZE
            self.rom.set_bytes(exit_data_start, exit_data)

        for exit_index, exit in enumerate(self.long_exits):
            exit_data = exit.to_data()
            exit_data_start = self.LONG_DATA_START_ADDR + exit_index * LongMapExit.DATA_SIZE
            self.rom.set_bytes(exit_data_start, exit_data)

    def mod(self, door_mapping, maps):
        ### exit rando (2-way doors only)
        # For all doors in map, we want to find the exit and change where it leads to
        for m in door_mapping:
            # Figure out whether exits are short or long
            exitA = self.get_exit_from_ID(m[0])
            exitB = self.get_exit_from_ID(m[1])

            # print(m[0], ' --> ', m[1], ':')
            # print('\tBefore: exitA')
            # exitA.print()
            # print('\tBefore: exitB')
            # exitB.print()

            # Attach exits:
            # Copy original properties of exitB_pair to exitA & vice versa.
            exitA_pairID = exit_data_orig[m[0]][0]
            exitB_pairID = exit_data_orig[m[1]][0]
            self.copy_exit_info(exitA, exitB_pairID)
            self.copy_exit_info(exitB, exitA_pairID)

            # print('\texitB pair:', exitB_pairID, ': ', self.exit_original_data[exitB_pairID])
            # print('\texitA pair:', exitA_pairID, ': ', self.exit_original_data[exitA_pairID], '\n')
            # print('\tAfter: exitA')
            # exitA.print()
            # print('\tAfter: exitB')
            # exitB.print()

            # Write an event on the exit to handle required conditions
            forced_world = [room_data[maps.doors.door_rooms[d]][3] for d in m]
            forced_pmap = [maps.doors.door_rooms[d] in force_update_parent_map.keys() for d in m]
            write_exit_event = [(forced_world[i] != forced_world[i-1]) or
                                forced_pmap[i]
                                for i in range(2)]
            if write_exit_event[0]:
                # Write an event on top of door m[1] to set the correct world
                this_exit = self.get_exit_from_ID(m[1])
                map_id = maps.exit_maps[m[1]]

                try:
                    existing_event = maps.get_event(map_id, this_exit.x, this_exit.y)
                    # An event already exists.  It will need to be modified.
                    # We have to be careful here: if it has a world door-switch event, we will need to do something else
                    # Read in existing event code
                    src = [maps.rom.get_byte(existing_event.event_Address)]
                    while src[-1] != 0xfe:
                        src.append(maps.rom.get_byte(existing_event.event_Address + len(src)))
                    # delete existing event
                    maps.delete_event(map_id, this_exit.x, this_exit.y)

                except IndexError:
                    # event does not exist.  Make a new one.
                    src = [field.Return()]

                # If it's a new event that is just forcing the world, just directly call the "force world" event:
                e_length = len(src)
                if e_length == 1 and not forced_pmap[0]:
                    if forced_world[0] == 0:
                        this_address = maps.GO_WOB_EVENT_ADDR - maps.events.BASE_OFFSET
                    elif forced_world[0] == 1:
                        this_address = maps.GO_WOR_EVENT_ADDR - maps.events.BASE_OFFSET

                else:
                    # Prepend call to force world bit event, if required
                    if forced_world[0] != forced_world[1]:
                        if forced_world[0] == 0:
                            src = [field.Call(maps.GO_WOB_EVENT_ADDR)] + src
                        elif forced_world[0] == 1:
                            src = [field.Call(maps.GO_WOR_EVENT_ADDR)] + src

                    # Prepend call to force parent map
                    if forced_pmap[0]:
                        pmap_data = force_update_parent_map[maps.doors.door_rooms[m[0]]]
                        src = [field.SetParentMap(pmap_data[0], 2, pmap_data[1], pmap_data[2])] + src

                    # Write data to a new event & add it
                    space = Write(Bank.CC, src, "Door Event " + str(m[1]))
                    this_address = space.start_address - maps.events.BASE_OFFSET

                if self.exit_type[m[1]] == 'short':
                    # Write the event on the tile
                    new_event = MapEvent()
                    new_event.x = this_exit.x
                    new_event.y = this_exit.y
                    new_event.event_address = this_address
                    maps.add_event(map_id, new_event)
                elif self.exit_type[m[1]] == 'long':
                    # Write the event on every tile in the exit
                    for i in range(this_exit.size+1):
                        new_event = MapEvent()
                        new_event.x = this_exit.x + i*(this_exit.direction == 0) # horizontal exit
                        new_event.y = this_exit.y + i*(this_exit.direction > 0)  # vertical exit
                        new_event.event_address = this_address
                        maps.add_event(map_id, new_event)

            if write_exit_event[1]:
                # Write an event on top of door m[0] to set the correct world
                this_exit = self.get_exit_from_ID(m[0])
                map_id = maps.exit_maps[m[0]]

                try:
                    existing_event = maps.get_event(map_id, this_exit.x, this_exit.y)
                    # An event already exists.  It will need to be modified.
                    # We have to be careful here: if it has a world door-switch event, we will need to do something else
                    # Read in existing event code
                    src = [maps.rom.get_byte(existing_event.event_Address)]
                    while src[-1] != 0xfe:
                        src.append(maps.rom.get_byte(existing_event.event_Address + len(src)))
                    # delete existing event
                    maps.delete_event(map_id, this_exit.x, this_exit.y)

                except IndexError:
                    # event does not exist.  Make a new one.
                    src = [field.Return()]

                # If it's a new event that is just forcing the world, just directly call the "force world" event:
                e_length = len(src)
                if e_length == 1 and not forced_pmap[1]:
                    if forced_world[0] != forced_world[1]:
                        if forced_world[1] == 0:
                            this_address = maps.GO_WOB_EVENT_ADDR - maps.events.BASE_OFFSET
                        elif forced_world[1] == 1:
                            this_address = maps.GO_WOR_EVENT_ADDR - maps.events.BASE_OFFSET

                else:
                    # Prepend call to force world bit event, if required
                    if forced_world[1] == 0:
                        src = [field.Call(maps.GO_WOB_EVENT_ADDR)] + src
                    elif forced_world[1] == 1:
                        src = [field.Call(maps.GO_WOR_EVENT_ADDR)] + src

                    # Prepend call to force parent map
                    if forced_pmap[1]:
                        pmap_data = force_update_parent_map[maps.doors.door_rooms[m[1]]]
                        src = [field.SetParentMap(pmap_data[0], 2, pmap_data[1], pmap_data[2])] + src

                    # Write data to a new event & add it
                    space = Write(Bank.CC, src, "Door Event " + str(m[0]))
                    this_address = space.start_address

                if self.exit_type[m[0]] == 'short':
                    # Write the event on the tile
                    new_event = MapEvent()
                    new_event.x = this_exit.x
                    new_event.y = this_exit.y
                    new_event.event_address = this_address
                    maps.add_event(map_id, new_event)
                elif self.exit_type[m[0]] == 'long':
                    # Write the event on every tile in the exit
                    for i in range(this_exit.size+1):
                        new_event = MapEvent()
                        new_event.x = this_exit.x + i*(this_exit.direction == 0) # horizontal exit
                        new_event.y = this_exit.y + i*(this_exit.direction > 0)  # vertical exit
                        new_event.event_address = this_address
                        maps.add_event(map_id, new_event)

        ### One-way doors are connected in map_events.mod()

        ### NOTES:
        # There are two ways to think about connecting world-map exits:
        #   (a) make all exits that would go to the world map instead go to some randomly selected exit
        #       --> Note this is also needed for some multi-short-exit "doors", see e.g. Esper Mountain
        #   (b) allowing any exit to connect to any other exit.
        #       This makes e.g. Cid's House a "hub" (5 doors) instead of a "hallway" (2 doors)
        # To make these two modes work:
        #   (a) needs a way to define that [list of exits] should all be connected to the same place,
        #       (plus a special treatment for SF WoB east side, probably just making it its own room).
        #       --> This is now implemented using rooms.shared_events[doorID] = [list of doorIDs with shared connection]
        #   (b) needs additional patching to make some long exits behave in a sensible way, since in vanilla they would
        #       put you at the vanilla entrance, which is a different long exit.

    def get_exit_from_ID(self, exitID):
        if self.exit_type[exitID] == 'short':
            exit = self.short_exits[exitID]  # Exit = short exit
        else:
            exit = self.long_exits[exitID - self.SHORT_EXIT_COUNT]  # Exit = long exit
        return exit

    def copy_exit_info(self, mod_exit, pair_ID):
        # Copy information to mod_exit from another exit with exitID = pair_ID.
        # Original door data is stored in self.exit_original_data[exitID] as:
        #   [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]
        pair_info = self.exit_original_data[pair_ID]
        mod_exit.dest_x = pair_info[0]
        mod_exit.dest_y = pair_info[1]
        mod_exit.dest_map = pair_info[2]
        # mod_exit.refreshparentmap = pair_info[3]  # do not want to copy refresh parent map!  Messes up warp stones.
        mod_exit.enterlowZlevel = pair_info[4]
        mod_exit.displaylocationname = pair_info[5]
        mod_exit.facing = pair_info[6]
        mod_exit.unknown = pair_info[7]
        return

    def print_short_exit_range(self, start, count):
        for offset in range(count):
            self.short_exits[start + offset].print()

    def print_long_exit_range(self, start, count):
        for offset in range(count):
            self.long_exits[start + offset].print()

    def delete_short_exit(self, search_start, x, y):
        for exit in self.short_exits[search_start:]:
            if exit.x == x and exit.y == y:
                self.short_exits.remove(exit)
                self.SHORT_EXIT_COUNT -= 1
                return

    def print(self):
        for short_exit in self.short_exits:
            short_exit.print()

        for long_exit in self.long_exits:
            long_exit.print()
