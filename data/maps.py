from data.map_property import MapProperty

import data.npcs as npcs
from data.npc import NPC

from data.chests import Chests

import data.doors as doors

import data.map_events as events
from data.map_event import MapEvent

import data.map_exits as exits
from data.map_exit import ShortMapExit, LongMapExit

import data.world_map_event_modifications as world_map_event_modifications

from memory.space import Allocate, Bank, Free, Write

from instruction import field
from instruction.event import EVENT_CODE_START

from data.event_exit_info import event_exit_info, exit_event_patch, entrance_event_patch, event_address_patch, long_events
from data.map_exit_extra import exit_data as exit_data_orig
from data.rooms import room_data, force_update_parent_map

from data.parse import delete_nops

class Maps():
    MAP_COUNT = 416

    EVENT_PTR_START = 0x40000
    ENTRANCE_EVENTS_START_ADDR = 0x11fa00

    SHORT_EXIT_PTR_START = 0x1fbb00
    LONG_EXIT_PTR_START = 0x2df480

    NPCS_PTR_START = 0x41a10

    GO_WOB_EVENT_ADDR = None
    GO_WOR_EVENT_ADDR = None

    def __init__(self, rom, args, items):
        self.rom = rom
        self.args = args

        self.npcs = npcs.NPCs(rom)
        self.chests = Chests(self.rom, self.args, items)
        self.events = events.MapEvents(rom)
        self.exits = exits.MapExits(rom)
        self.world_map_event_modifications = world_map_event_modifications.WorldMapEventModifications(rom)
        self.read()

        self.doors = doors.Doors(args)

        # Create an event code to set the world bit
        src_WOR = [0xd0, 0xa4, 0xfe]  # Set world bit = WoR, return
        space = Allocate(Bank.CC, len(src_WOR), "Go To WoR")
        space.write(src_WOR)
        self.GO_WOR_EVENT_ADDR = space.start_address

        src_WOB = [0xd1, 0xa4, 0xfe]  # Set world bit = WoB, return
        space = Allocate(Bank.CC, len(src_WOB), "Go To WoB")
        space.write(src_WOB)
        self.GO_WOB_EVENT_ADDR = space.start_address

    def read(self):
        self.maps = []
        self.properties = []

        for map_index in range(self.MAP_COUNT):
            self.maps.append({"id" : map_index})

            map_property = MapProperty(self.rom, map_index)
            self.properties.append(map_property)
            self.maps[map_index]["name_index"] = map_property.name_index

            entrance_event_start = self.ENTRANCE_EVENTS_START_ADDR + map_index * self.rom.LONG_PTR_SIZE
            entrance_event = self.rom.get_bytes(entrance_event_start, self.rom.LONG_PTR_SIZE)
            self.maps[map_index]["entrance_event_address"] = entrance_event[0] | (entrance_event[1] << 8) | (entrance_event[2] << 16)

            events_ptr_address = self.EVENT_PTR_START + map_index * self.rom.SHORT_PTR_SIZE
            events_ptr = self.rom.get_bytes(events_ptr_address, self.rom.SHORT_PTR_SIZE)
            self.maps[map_index]["events_ptr"] = events_ptr[0] | (events_ptr[1] << 8)

            short_exit_ptr_address = self.SHORT_EXIT_PTR_START + map_index * self.rom.SHORT_PTR_SIZE
            short_exit_ptr = self.rom.get_bytes(short_exit_ptr_address, self.rom.SHORT_PTR_SIZE)
            self.maps[map_index]["short_exits_ptr"] = short_exit_ptr[0] | (short_exit_ptr[1] << 8)

            long_exit_ptr_address = self.LONG_EXIT_PTR_START + map_index * self.rom.SHORT_PTR_SIZE
            long_exit_ptr = self.rom.get_bytes(long_exit_ptr_address, self.rom.SHORT_PTR_SIZE)
            self.maps[map_index]["long_exits_ptr"] = long_exit_ptr[0] | (long_exit_ptr[1] << 8)

            npcs_ptr_address = self.NPCS_PTR_START + map_index * self.rom.SHORT_PTR_SIZE
            npcs_ptr = self.rom.get_bytes(npcs_ptr_address, self.rom.SHORT_PTR_SIZE)
            self.maps[map_index]["npcs_ptr"] = npcs_ptr[0] | (npcs_ptr[1] << 8)

            #####grab map warp-ability flag
            self.maps[map_index]["warpable"] = map_property.warpable
            #####grab map warp-ability flag

        ### Populate the dictionary for parent map given door ID
        self.exit_maps = {}
        self.exit_x_y = {}
        counter = 0
        for m in range(len(self.maps)-1):
            num_short = self.get_short_exit_count(m)
            for i in range(num_short):
                self.exit_maps[i+counter] = m
                se = self.exits.short_exits[i+counter]
                self.exit_x_y[i+counter] = [se.x, se.y]
            counter += num_short
        num_short_exits = counter
        for m in range(len(self.maps)-1):
            num_long = self.get_long_exit_count(m)
            for i in range(num_long):
                self.exit_maps[i + counter] = m
                le = self.exits.long_exits[i + counter - num_short_exits]
                self.exit_x_y[i + counter] = [le.x, le.y]
            counter += num_long

        # f = open('exit_original_info.txt', 'w')
        # f.write(
        #     '# exit_ID: [x, y, parent_map, dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]\n')
        # for li in self.exits.exit_original_data.keys():
        #     this_exit = self.get_exit(li)
        #     write_string = str(li)
        #     write_string += ': ' + str(this_exit.x) + ', ' + str(this_exit.y) + ' [' + str(hex(self.exit_maps[li])) + '], '
        #     write_string += str(self.exits.exit_original_data[li])
        #     write_string += '.\n'
        #     f.write(write_string)
        # f.close()

        ### Do we also need this for event exits?
        #self.event_maps = {}
        self.event_map_x_y = {}
        counter = 0
        for m in range(len(self.maps)-1):
            num_events = self.get_event_count(m)
            for i in range(num_events):
                #self.event_maps[i + counter] = m
                this_e = self.events.events[i + counter]
                self.event_map_x_y[i + counter] = [m, this_e.x, this_e.y]
            counter += num_events

        # f = open('event_map&address_info.txt','w')
        # f.write('# Event_ID: map_ID, (x, y), event_address')
        # for i in self.event_maps.keys():
        #     f.write(str(i) + ' : ' + str(self.event_maps[i]) + ', (' + str(self.events.events[i].x) + ', ' +
        #             str(self.events.events[i].y) + '), ' + str(hex(self.events.events[i].event_address)) + '\n')
        # f.close()

        self.npc_maps = {}
        counter = 0
        for m in range(len(self.maps) - 1):
            num_npcs = self.get_npc_count(m)
            for i in range(num_npcs):
                self.npc_maps[i + counter] = m
            counter += num_npcs

        # f = open('npc_info.txt', 'w')
        # f.write('# NPC_id: map_ID, (x,y), event_address')
        # for n in self.npc_maps.keys():
        #     npc = self.npcs.get_npc(n)
        #     f.write(str(n) + ': ' + str(hex(self.npc_maps[n])) + ' (' + str(npc.x) + ', ' + str(npc.y) + '): '
        #           + str(hex(npc.event_address)) + '\n')
        # f.close()


    def set_entrance_event(self, map_id, event_address):
        self.maps[map_id]["entrance_event_address"] = event_address

    def get_entrance_event(self, map_id):
        return self.maps[map_id]["entrance_event_address"]

    def get_npc_index(self, map_id, npc_id):
        first_npc_index = (self.maps[map_id]["npcs_ptr"] - self.maps[0]["npcs_ptr"]) // NPC.DATA_SIZE
        return first_npc_index + (npc_id - 0x10)

    def get_npc(self, map_id, npc_id):
        return self.npcs.get_npc(self.get_npc_index(map_id, npc_id))

    def append_npc(self, map_id, new_npc):
        prev_npc_count = self.get_npc_count(map_id)
        new_npc_id = 0x10 + prev_npc_count

        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["npcs_ptr"] += NPC.DATA_SIZE

        npc_index = (self.maps[map_id]["npcs_ptr"] - self.maps[0]["npcs_ptr"]) // NPC.DATA_SIZE
        npc_index += prev_npc_count # add new npc to the end of current map's npcs
        self.npcs.add_npc(npc_index, new_npc)

        return new_npc_id # return id of the new npc

    def remove_npc(self, map_id, npc_id):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["npcs_ptr"] -= NPC.DATA_SIZE

        self.npcs.remove_npc(self.get_npc_index(map_id, npc_id))

    def get_npc_count(self, map_id):
        return (self.maps[map_id + 1]["npcs_ptr"] - self.maps[map_id]["npcs_ptr"]) // NPC.DATA_SIZE

    def get_chest_count(self, map_id):
        return self.chests.chest_count(map_id)

    def set_chest_item(self, map_id, x, y, item_id):
        self.chests.set_item(map_id, x, y, item_id)

    def get_event_count(self, map_id):
        return (self.maps[map_id + 1]["events_ptr"] - self.maps[map_id]["events_ptr"]) // MapEvent.DATA_SIZE

    def print_events(self, map_id):
        first_event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE

        self.events.print_range(first_event_id, self.get_event_count(map_id))

    def get_event(self, map_id, x, y):
        first_event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        last_event_id = first_event_id + self.get_event_count(map_id)
        return self.events.get_event(first_event_id, last_event_id, x, y)

    def add_event(self, map_id, new_event):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["events_ptr"] += MapEvent.DATA_SIZE

        event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        self.events.add_event(event_id, new_event)

    def delete_event(self, map_id, x, y):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["events_ptr"] -= MapEvent.DATA_SIZE

        first_event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        last_event_id = first_event_id + self.get_event_count(map_id)
        self.events.delete_event(first_event_id, last_event_id, x, y)

    def get_exit(self, exit_id):
        map_id = self.exit_maps[exit_id]  # Get [map_id, x, y] for exits
        xy = self.exit_x_y[exit_id]
        if self.exits.exit_type[exit_id] == 'short':
            first_exit_id = (self.maps[map_id]["short_exits_ptr"] - self.maps[0]["short_exits_ptr"]) // ShortMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_short_exit_count(map_id)
            return self.exits.get_short_exit(first_exit_id, last_exit_id, xy[0], xy[1])
        elif self.exits.exit_type[exit_id] == 'long':
            first_exit_id = (self.maps[map_id]["long_exits_ptr"] - self.maps[0]["long_exits_ptr"]) // LongMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_long_exit_count(map_id)
            return self.exits.get_long_exit(first_exit_id, last_exit_id, xy[0], xy[1])
        else:
            raise Exception('Unknown exit type')

    def get_short_exit_count(self, map_id):
        return (self.maps[map_id + 1]["short_exits_ptr"] - self.maps[map_id]["short_exits_ptr"]) // ShortMapExit.DATA_SIZE

    def print_short_exits(self, map_id):
        first_exit_id = (self.maps[map_id]["short_exits_ptr"] - self.maps[0]["short_exits_ptr"]) // ShortMapExit.DATA_SIZE
        self.exits.print_short_exit_range(first_exit_id, self.get_short_exit_count(map_id))

    def delete_short_exit(self, map_id, x, y):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["short_exits_ptr"] -= ShortMapExit.DATA_SIZE

        map_first_short_exit = (self.maps[map_id]["short_exits_ptr"] - self.maps[0]["short_exits_ptr"]) // ShortMapExit.DATA_SIZE
        self.exits.delete_short_exit(map_first_short_exit, x, y)

    def get_long_exit_count(self, map_id):
        return (self.maps[map_id + 1]["long_exits_ptr"] - self.maps[map_id]["long_exits_ptr"]) // LongMapExit.DATA_SIZE

    def print_long_exits(self, map_id):
        first_exit_id = (self.maps[map_id]["long_exits_ptr"] - self.maps[0]["long_exits_ptr"]) // LongMapExit.DATA_SIZE
        self.exits.print_long_exit_range(first_exit_id, self.get_long_exit_count(map_id))

    def _fix_imperial_camp_boxes(self):
        # near the northern tent normally accessed by jumping over a wall
        # there is a box which can be walked into but not out of which causes the game to lock
        # fix the three boxes to no longer be walkable

        from utils.compression import compress, decompress
        layer1_tilemap = 0x1c
        tilemap_ptrs_start = 0x19cd90
        tilemap_ptr_addr = tilemap_ptrs_start + layer1_tilemap * self.rom.LONG_PTR_SIZE
        tilemap_addr_bytes = self.rom.get_bytes(tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        tilemap_addr = int.from_bytes(tilemap_addr_bytes, byteorder = "little")

        next_tilemap_ptr_addr = tilemap_ptr_addr + self.rom.LONG_PTR_SIZE
        next_tilemap_addr_bytes = self.rom.get_bytes(next_tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        next_tilemap_addr = int.from_bytes(next_tilemap_addr_bytes, byteorder = "little")

        tilemaps_start = 0x19d1b0
        tilemap_len = next_tilemap_addr - tilemap_addr
        tilemap = self.rom.get_bytes(tilemaps_start + tilemap_addr, tilemap_len)
        decompressed = decompress(tilemap)

        map_width = 64
        impassable_box_tile = 62 # box tile that cannot be entered
        coordinates = [(19, 13), (15, 14), (18, 14)] # coordinates of boxes to change
        for coordinate in coordinates:
            decompressed[coordinate[0] + coordinate[1] * map_width] = impassable_box_tile

        compressed = compress(decompressed)
        self.rom.set_bytes(tilemaps_start + tilemap_addr, compressed)

    def mod(self, characters):
        self.npcs.mod(characters)
        self.chests.mod()
        self.doors.mod()
        ### HACK FOR TESTING
        # from data.map_exit_extra import exit_data as ed
        # for r in room_data.keys():
        #     for d in room_data[r][0]:
        #         self.doors.door_rooms[d] = r
        #         self.doors.door_descr[d] = ed[d][1]
        #     for d in room_data[r][1]:
        #         self.doors.door_descr[d] = event_exit_info[d][4]
        #         self.doors.door_descr[d+1000] = event_exit_info[d][4] + "DEST"
        #
        # self.doors.map = [[[81, 582],    # Airship <--> Owzer Basement stairs,
        #                    [587, 1032]],   # switch true door <--> esper mtn boss room
        #                   [[2017, 3010], # switch Door left --> umaro's cave
        #                    [2018, 3014], # switch door right --> esper mtn
        #                    ] ]
        ###
        self.events.mod()  # self.events.mod(self.doors, self)
        self.exits.mod()  # self.exits.mod(self.doors.map[0], self)

        self._fix_imperial_camp_boxes()

        # Make all maps warpable for -door-randomize-all
        if self.args.debug or self.args.door_randomize_all:
            for map_index, cur_map in enumerate(self.maps):
                self.properties[map_index].warpable = 1

        # Add doors to the spoiler log
        if len(self.doors.map) > 0:
            self.doors.print()

    def write(self):
        # Patch the door randomizer exits & events before writing:
        self.connect_events()
        self.connect_exits()

        self.npcs.write()
        self.chests.write()
        self.events.write()
        self.exits.write()
        self.world_map_event_modifications.write()

        for map_index, cur_map in enumerate(self.maps):
            self.properties[map_index].write()

            entrance_event_start = self.ENTRANCE_EVENTS_START_ADDR + cur_map["id"] * self.rom.LONG_PTR_SIZE
            entrance_event_bytes = [0x00] * self.rom.LONG_PTR_SIZE
            entrance_event_bytes[0] = cur_map["entrance_event_address"] & 0xff
            entrance_event_bytes[1] = (cur_map["entrance_event_address"] & 0xff00) >> 8
            entrance_event_bytes[2] = (cur_map["entrance_event_address"] & 0xff0000) >> 16
            self.rom.set_bytes(entrance_event_start, entrance_event_bytes)

            events_ptr_start = self.EVENT_PTR_START + cur_map["id"] * self.rom.SHORT_PTR_SIZE
            events_ptr_bytes = [0x00] * self.rom.SHORT_PTR_SIZE
            events_ptr_bytes[0] = cur_map["events_ptr"] & 0xff
            events_ptr_bytes[1] = (cur_map["events_ptr"] & 0xff00) >> 8
            self.rom.set_bytes(events_ptr_start, events_ptr_bytes)

            short_exits_ptr_start = self.SHORT_EXIT_PTR_START + cur_map["id"] * self.rom.SHORT_PTR_SIZE
            short_exits_bytes = [0x00] * self.rom.SHORT_PTR_SIZE
            short_exits_bytes[0] = cur_map["short_exits_ptr"] & 0xff
            short_exits_bytes[1] = (cur_map["short_exits_ptr"] & 0xff00) >> 8
            self.rom.set_bytes(short_exits_ptr_start, short_exits_bytes)

            long_exits_ptr_start = self.LONG_EXIT_PTR_START + cur_map["id"] * self.rom.SHORT_PTR_SIZE
            long_exits_bytes = [0x00] * self.rom.SHORT_PTR_SIZE
            long_exits_bytes[0] = cur_map["long_exits_ptr"] & 0xff
            long_exits_bytes[1] = (cur_map["long_exits_ptr"] & 0xff00) >> 8
            self.rom.set_bytes(long_exits_ptr_start, long_exits_bytes)

            npcs_ptr_address = self.NPCS_PTR_START + cur_map["id"] * self.rom.SHORT_PTR_SIZE
            npcs_ptr = [0x00] * self.rom.SHORT_PTR_SIZE
            npcs_ptr[0] = cur_map["npcs_ptr"] & 0xff
            npcs_ptr[1] = (cur_map["npcs_ptr"] & 0xff00) >> 8
            self.rom.set_bytes(npcs_ptr_address, npcs_ptr)

    def connect_events(self):
        # Perform Event modification for one-way entrances
        # For the connection "Event1" --> "Event2":
        for m in self.doors.map[1]:
            if m[0] >= 2000:
                # Collect exit event information for patching
                exit_info = event_exit_info[m[0]]
                exit_address = exit_info[0]
                exit_length = exit_info[1]
                exit_split = exit_info[2]
                exit_state = exit_info[3]

                src = self.rom.get_bytes(exit_address, exit_split)  # First half of event

            else:
                # Handle the small number of one-way exits coded as doors
                exit_address = None
                exit_state = [False, False, False]
                this_exit = self.get_exit(m[0])
                exit_location = [this_exit.x, this_exit.y, self.exit_maps[m[0]]]

                src = [0x6a]

            if m[1] >= 3000:
                # Right now the convention is that vanilla one-way entrance ID = (vanilla one-way exit ID + 1000)
                entr_info = event_exit_info[m[1] - 1000]
                entr_address = entr_info[0]
                entr_length = entr_info[1]
                entr_split = entr_info[2]
                entr_state = entr_info[3]

                src_end = self.rom.get_bytes(entr_address + entr_split,
                                             entr_length - entr_split)  # Second half of event

            else:
                # Handle the small number of one-way entrances from doors
                entr_address = None
                entr_state = [False, False, False]
                entr_location = self.exits.exit_original_data[m[1] - 1000]
                # [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]

                # Load the map with facing & destination music; x coord; y coord; fade screen in & run entrance event, return
                src_end = [entr_location[2], entr_location[6] << 4, entr_location[0], entr_location[1], 0x80, 0xfe]

            # Perform common event patches
            if exit_state != entr_state:
                ex_patch = []
                en_patch = []
                if exit_state[0] and not entr_state[0]:
                    # Character is hidden during the transition and not unhidden later.
                    # Add a "Show object 31" line ("0x41 0x31", two bytes)
                    en_patch += [0x41, 0x31]
                if exit_state[1] and not entr_state[1]:
                    # Song override bit is on in the exit but not cleared in the entrance.
                    # Add a "clear $1E80($1CC)" (song override) before transition
                    ex_patch += [0xd3, 0xcc]
                if exit_state[2] and not entr_state[2]:
                    # Hold screen bit is set (command 0x38) in the exit but not freed (command 0x39) in the entrance
                    # Add a "0x39 Free Screen" before transition
                    ex_patch += [0x39]
                # Add patched lines before map transition
                src = src[:-1] + ex_patch + src[-1:]
                # Add patched lines after map transition
                src_end = src_end[:5] + en_patch + src_end[5:]

            # Check for other event patches & implement if found
            if m[0] in exit_event_patch.keys():
                [src, src_end] = exit_event_patch[m[0]](src, src_end)
            if m[1] in entrance_event_patch.keys():
                [src, src_end] = entrance_event_patch[m[1]](src, src_end)

            # Combine events
            src.extend(src_end)

            # Delete NOPs, if requested, to save space
            # Note there is the possibility for conflict with event_address_patch - be careful!
            if True:
                src = delete_nops(src)

            # Allocate space
            space = Allocate(Bank.CC, len(src), "Exit Event Randomize: " + str(m[0]) + " --> " + str(m[1]))
            new_event_address = space.start_address

            # Check for event address patches & implement if found
            if m[0] in event_address_patch.keys():
                src = event_address_patch[m[0]](src, new_event_address)

            space.write(src)

            print('Writing: ', m[0], ' --> ', m[1],
                  ':\n\toriginal memory addresses: ', hex(exit_address), ', ', hex(entr_address),
                  '\n\tbitstring: ', [hex(s)[2:] for s in src])
            print('\n\tnew memory address: ', hex(new_event_address))

            if exit_address is not None:
                if exit_address == 0xc8022:
                    # One-time hack for Cid/Minecart NPC entrance event.  If there are more, make a case for it.
                    cid = self.get_npc(0x110, 0 + 0x10)
                    # print('Cid index = ', self.get_npc_index(0x110, 0 + 0x10))
                    cid.set_event_address(new_event_address)
                    # cid.print()

                else:
                    # Update the MapEvent.event_address = Address(Event1a)
                    this_event_id = self.events.event_address_index[exit_address - EVENT_CODE_START]
                    if m[0] == 2017:  # HACK for shared event in Owzer's Mansion switch doors
                        this_event_id -= 1
                    e_mxy = self.event_map_x_y[this_event_id]
                    this_event = self.get_event(e_mxy[0], e_mxy[1], e_mxy[2])  # get event using [map_id, x, y] data
                    this_event.event_address = new_event_address - EVENT_CODE_START

                    if m[0] in long_events.keys():
                        # Other tiles must also be updated to point to the event at the appropriate offset
                        for le in long_events[m[0]]:
                            le_addr = event_exit_info[le][0]
                            le_id = self.events.event_address_index[le_addr - EVENT_CODE_START]
                            le_mxy = self.event_map_x_y[le_id]
                            le_event = self.get_event(le_mxy[0], le_mxy[1], le_mxy[2]) # get event using [map_id, x, y] data
                            le_event.event_address = new_event_address + (le_addr - exit_address) - EVENT_CODE_START

            else:
                # Create a new MapEvent for this event
                new_event = MapEvent()
                new_event.x = exit_location[0]
                new_event.y = exit_location[1]
                new_event.event_address = new_event_address - EVENT_CODE_START
                self.add_event(exit_location[2], new_event)

            # (Event2 will be updated when the initiating door for Event2 is mapped)

            # free previous event data space
            do_free = False
            if do_free:
                Free(exit_address, exit_address + exit_length - 1)

            if do_free:
                print('\n\tFreed addresses: ', hex(exit_address), hex(exit_address + exit_length - 1))

    def connect_exits(self):
        # For all doors in doors.map[0], we want to find the exit and change where it leads to
        for m in self.doors.map[0]:
            # Only connect real doors (virtual doors should never connect to real doors)
            if m[0] < 2000 and m[1] < 2000:
                # Get exits associated with doors m[0] and m[1]
                exitA = self.get_exit(m[0])
                exitB = self.get_exit(m[1])

                # Attach exits:
                # Copy original properties of exitB_pair to exitA & vice versa.
                exitB_pairID = exit_data_orig[m[1]][0] # Original connecting exit to B...
                self.exits.copy_exit_info(exitA, exitB_pairID)  # ... copied to exit A
                exitA_pairID = exit_data_orig[m[0]][0]  # Original connecting exit to A...
                self.exits.copy_exit_info(exitB, exitA_pairID)  # ... copied to exit B

                # Write events on the exits to handle required conditions:
                # Write an event on top of exit m[1] to set the correct properties (world, parent map) for exit m[0]
                self.create_exit_event(m[1], m[0])
                # Write an event on top of exit m[0] to set the correct properties (world, parent map) for exit m[1]
                self.create_exit_event(m[0], m[1])

            elif (m[0] < 2000) != (m[1] < 2000):
                print('ERROR!  something weird happened.', m)

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

    def create_exit_event(self, d, d_ref):
        # Write an event on top of exit d to set the correct properties (world, parent map) for exit d_ref

        # Collect information about the properties for the exit
        this_exit = self.get_exit(d)
        map_id = self.exit_maps[d]
        this_world = room_data[self.doors.door_rooms[d]][3]

        # Collect information about the properties of the connecting exit
        forced_world = room_data[self.doors.door_rooms[d_ref]][3]
        forced_pmap = self.doors.door_rooms[d_ref] in force_update_parent_map.keys()

        # Check to make sure an exit event is required:
        # (1) the connection requires a specific world that is not this world
        # (2) the connection requires a parent map update
        # (3) the connection requires special code (in entrance_event_patch[d_ref])
        # (4) the door requires special code (in exit_event_patch[d])
        require_event_flags = [
            ((forced_world is not None) and (forced_world != this_world)),
            forced_pmap,
            d_ref in entrance_event_patch.keys(),
            d in exit_event_patch.keys()
        ]
        if require_event_flags.count(True) > 0:
            # Look for an existing event on this exit tile
            try:
                existing_event = self.get_event(map_id, this_exit.x, this_exit.y)
                # An event already exists.  It will need to be modified.
                # We have to be careful here: if it has a world door-switch event, we will need to do something else

                # Read in existing event code
                src = [self.rom.get_byte(existing_event.event_address)]
                while src[-1] != 0xfe:
                    src.append(self.rom.get_byte(existing_event.event_address + len(src)))

                # delete existing event
                self.delete_event(map_id, this_exit.x, this_exit.y)

            except IndexError:
                # event does not exist.  Make a new one.
                src = [field.Return()]

            this_address = 0x05eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

            # If it's a new event that is just forcing the world, just directly call the "force world" event:
            e_length = len(src)
            if e_length == 1 and not require_event_flags[1:].count(True) > 0:
                if forced_world == 0:
                    this_address = self.GO_WOB_EVENT_ADDR - EVENT_CODE_START
                elif forced_world == 1:
                    this_address = self.GO_WOR_EVENT_ADDR - EVENT_CODE_START

            else:
                # (1) Prepend call to force world bit event, if required
                if require_event_flags[0]:
                    if forced_world == 0:
                        src = [field.Call(self.GO_WOB_EVENT_ADDR)] + src
                    elif forced_world == 1:
                        src = [field.Call(self.GO_WOR_EVENT_ADDR)] + src

                # (2) Prepend call to force parent map, if required
                if require_event_flags[1]:
                    pmap_data = force_update_parent_map[self.doors.door_rooms[d_ref]]
                    src = [field.SetParentMap(pmap_data[0], 2, pmap_data[1], pmap_data[2])] + src

                # (3) Prepend any data required by the connection
                if require_event_flags[2]:
                    src = entrance_event_patch[d_ref] + src

                # (4) Prepend any data required by the door
                if require_event_flags[3]:
                    src = exit_event_patch[d] + src

                # Write data to a new event & add it
                space = Write(Bank.CC, src, "Door Event " + str(d))
                this_address = space.start_address - EVENT_CODE_START

            # Write the new event on the exit
            if self.exits.exit_type[d] == 'short':
                # Write the event on the short exit tile
                new_event = MapEvent()
                new_event.x = this_exit.x
                new_event.y = this_exit.y
                new_event.event_address = this_address
                self.add_event(map_id, new_event)
            elif self.exits.exit_type[d] == 'long':
                # Write the event on every tile in the long exit
                for i in range(this_exit.size + 1):
                    new_event = MapEvent()
                    new_event.x = this_exit.x + i * (this_exit.direction == 0)  # horizontal exit
                    new_event.y = this_exit.y + i * (this_exit.direction > 0)  # vertical exit
                    new_event.event_address = this_address
                    self.add_event(map_id, new_event)

            #print('Connecting ' + str(d) + '(map = ' + str(map_id) + ' [' + str(this_exit.x) + ',' + str(this_exit.y) +
            #      '], world = ' + str(this_world) + ') --> ' + str(d_ref) + ' (force world = ' + str(forced_world) +
            #      ', force parent map = ' + str(forced_pmap) + '): event script @ ' + str(hex(this_address)))
