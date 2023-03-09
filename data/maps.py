from data.map_property import MapProperty

import data.npcs as npcs
from data.npc import NPC

from data.chests import Chests

import data.doors as doors

import data.map_events as events
from data.map_event import MapEvent, LongMapEvent

import data.map_exits as exits
from data.map_exit import ShortMapExit, LongMapExit
#from data.connections import Connections
from data.transitions import Transitions

import data.world_map_event_modifications as world_map_event_modifications
from data.world_map import WorldMap

from memory.space import Allocate, Bank, Free, Write, Reserve

from instruction import field
from instruction.event import EVENT_CODE_START
import instruction.field.entity as field_entity

from data.event_exit_info import event_exit_info, exit_event_patch, entrance_event_patch, event_address_patch, \
    multi_events
from data.map_exit_extra import exit_data, exit_data_patch, has_event_entrance
from data.rooms import room_data, exit_world, force_update_parent_map, shared_exits

from data.parse import delete_nops

import data.event_bit as event_bit

class Maps():
    MAP_COUNT = 416

    EVENT_PTR_START = 0x40000
    LONG_EVENT_PTR_START = events.LongMapEvents.POINTER_START_ADDR_LONG
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
        self.long_events = events.LongMapEvents(rom)
        self.exits = exits.MapExits(rom, args.door_randomize)
        #self.connections = Connections(self.exits)
        self.world_map_event_modifications = world_map_event_modifications.WorldMapEventModifications(rom)
        self.world_map = WorldMap(rom, args)
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

        # Record the vanilla world of each door
        self.exit_world = exit_world

        # Perform cleanup actions if door randomization is happening
        if args.door_randomize is True:
            self.door_rando_cleanup()

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

            # LONG EVENTS INITIALIZATION:
            # Vanilla code has no long events.  Set initial offset to the vanilla value for each map.
            self.maps[map_index]["long_events_ptr"] = self.maps[0]["events_ptr"]
            #long_events_ptr_address = self.LONG_EVENT_PTR_START + map_index * self.rom.SHORT_PTR_SIZE
            #long_events_ptr = self.rom.get_bytes(long_events_ptr_address, self.rom.SHORT_PTR_SIZE)
            #self.maps[map_index]["long_events_ptr"] = long_events_ptr[0] | (long_events_ptr[1] << 8)

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

        # Add non-standard "exits"
        for e in exit_data.keys():
            if e not in self.exit_maps.keys():
                if (e-4000) in self.exit_maps.keys():
                    # Logical exit
                    self.exit_maps[e] = self.exit_maps[e-4000]
                    self.exit_x_y[e] = self.exit_x_y[e-4000]
                elif e in event_exit_info.keys():
                    # Event tile as exit.
                    self.exit_maps[e] = event_exit_info[e][5][0]
                    self.exit_x_y[e] = event_exit_info[e][5][1:]

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
        #self.event_map_x_y = {}
        #counter = 0
        #for m in range(len(self.maps)-1):
        #    num_events = self.get_event_count(m)
        #    for i in range(num_events):
        #        #self.event_maps[i + counter] = m
        #        this_e = self.events.events[i + counter]
        #        self.event_map_x_y[i + counter] = [m, this_e.x, this_e.y]
        #    counter += num_events

        # f = open('event_map&address_info.txt','w')
        # f.write('# Event_ID: map_ID, (x, y), event_address')
        # for i in self.event_map_x_y.keys():
        #     f.write(str(i) + ' : ' + str(hex(self.event_map_x_y[i][0])) + ', (' + str(self.event_map_x_y[i][1]) + ', ' +
        #             str(self.event_map_x_y[i][2]) + '), ' + str(hex(self.events.events[i].event_address)) + '\n')
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

        # f = open('original_map_event_tally.txt', 'w')
        # f.write('# map_ID: # events in map, then event data in map\n')
        # for m in range(len(self.maps) - 1):
        #     num_events = self.get_event_count(m)
        #     this_ptr = self.maps[m]["events_ptr"]
        #     write_string = str(m) + ':\t' + str(num_events) + '(' + str(hex(this_ptr)) + ')'
        #     write_string += '.\n'
        #     f.write(write_string)
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

    ### LONG EVENTS ###
    def get_long_event_count(self, map_id):
        return (self.maps[map_id + 1]["long_events_ptr"] - self.maps[map_id]["long_events_ptr"]) // LongMapEvent.DATA_SIZE

    def print_long_events(self, map_id):
        first_event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE

        self.long_events.print_range(first_event_id, self.get_event_count(map_id))

    def get_long_event(self, map_id, x, y):
        first_event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE
        last_event_id = first_event_id + self.get_event_count(map_id)
        return self.long_events.get_event(first_event_id, last_event_id, x, y)

    def add_long_event(self, map_id, new_event):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["long_events_ptr"] += LongMapEvent.DATA_SIZE

        event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE
        self.long_events.add_event(event_id, new_event)

    def delete_long_event(self, map_id, x, y):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["long_events_ptr"] -= LongMapEvent.DATA_SIZE

        first_event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE
        last_event_id = first_event_id + self.get_event_count(map_id)
        self.long_events.delete_event(first_event_id, last_event_id, x, y)
    ### LONG EVENTS ###

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
        self.world_map.mod()
        self.doors.mod()
        ### HACK FOR TESTING
        #newmap = [
        #    [[81, 736]],  # Airship <--> Umaro Cave 2nd room mid door,
        #    [[2005, 3015], # Umaro Cave 2nd Room west trapdoor --> Esper mtn north pit
        #     [2015, 3005]], # Esper mtn north pit --> Umaro cave
        #]
        #self.doorRandoOverride(newmap)
        ###
        if self.doors.verbose:
            print('Door connections:')
            for m in self.doors.map[0]:
                print('\t' + str(m[0]) + "<-->" + str(m[1]) )
            print('One-way connections:')
            for m in self.doors.map[1]:
                print('\t', m[0], " -> ", m[1])
        self.events.mod()  # self.events.mod(self.doors, self)
        self.long_events.mod()  # LONG EVENTS

        ### FOR TESTING ONLY ###
        # self.testLongEvents()
        ### FOR TESTING ONLY ###

        self.exits.mod()  # self.exits.mod(self.doors.map[0], self)

        self._fix_imperial_camp_boxes()

        # Make all maps warpable for -door-randomize-all
        if self.args.debug or self.args.door_randomize_all:
            for map_index, cur_map in enumerate(self.maps):
                self.properties[map_index].warpable = 1

        # Add doors to the spoiler log
        if len(self.doors.map) > 0:
            self.doors.print()

    def doorRandoOverride(self, newmap):
        from data.map_exit_extra import exit_data as ed
        for r in room_data.keys():
            for d in room_data[r][0]:
                self.doors.door_rooms[d] = r
                if d > 4000:
                    self.doors.door_descr[d] = ed[d-4000][1] + "LOGICAL WOR"
                else:
                    self.doors.door_descr[d] = ed[d][1]
        for d in room_data[r][1]:
            self.doors.door_descr[d] = event_exit_info[d][4]
            self.doors.door_descr[d+1000] = event_exit_info[d][4] + "DEST"
        self.doors.map = newmap

    def testLongEvents(self):
        ### FOR TESTING: MAKE SOME LONG EVENTS TO VERIFY THE CODE WORKS CORRECTLY
        print('Long event count: ' + str(self.long_events.EVENT_COUNT))

        # LONG EVENT #1: play the lore sound effect on some horizontal tiles on the Blackjack
        src = [
            field.BranchIfEventBitSet(0x1b5, "SetBit"),
            field.PlaySoundEffect(0x0),  # Lore sound effect
            field.SetEventBit(0x1b5),
            "SetBit",
            field.Return(),
        ]
        space = Write(Bank.CC, src, 'Test long event')
        new_le = LongMapEvent()
        new_le.x = 14
        new_le.y = 7
        new_le.size = 2
        new_le.direction = 0  # 0 = horizontal; 128 = vertical
        new_le.event_address = space.start_address - EVENT_CODE_START
        self.add_long_event(0x006, new_le)  # add to map 0x006 (Blackjack, Deck)
        print('Added long event #1:')
        new_le.print()

        # LONG EVENT #2: play the Bolt3 sound effect on some vertical tiles on the Blackjack
        src = [
            field.BranchIfEventBitSet(0x1b5, "SetBit"),
            field.PlaySoundEffect(0x015),  # Bolt3 sound effect
            field.SetEventBit(0x1b5),
            "SetBit",
            field.Return(),
        ]
        space = Write(Bank.CC, src, 'Test long event')
        new_le = LongMapEvent()
        new_le.x = 17
        new_le.y = 6
        new_le.size = 2
        new_le.direction = 128  # 0 = horizontal; 128 = vertical
        new_le.event_address = space.start_address - EVENT_CODE_START
        self.add_long_event(0x006, new_le)  # add to map 0x006 (Blackjack, Deck)
        print('Added long event #2:')
        new_le.print()

        print('Long event count: ' + str(self.long_events.EVENT_COUNT))

    def write_post_diagnostic_info(self):
        # Write edited event info to a text file in human-readable format
        f = open('event_map&address_info_post.txt','w')
        f.write('# Event_ID: map_ID, (x, y), event_address')
        counter = 0
        for m in range(len(self.maps) - 1):
            num_events = self.get_event_count(m)
            for i in range(num_events):
                this_e = self.events.events[i + counter]
                f.write(str(counter+i) + ': ' + str(hex(m)) + " (" + str(this_e.x) + ", " + str(this_e.y) + ").  "
                        + str(hex(this_e.event_address)) + '\n')
            counter += num_events
        f.write('\n\n')
        for i in range(len(self.events.events)):
            this_e = self.events.events[i]
            f.write(str(counter + i) + ': ' + "(" + str(this_e.x) + ", " + str(this_e.y) + ").  "
                    + str(hex(this_e.event_address)) + '\n')
        f.close()

    def write(self):
        #self.write_post_diagnostic_info()

        # Patch the door randomizer exits & events before writing:
        # Connect one-way event exits using the Transitions class
        self.transitions = Transitions(self.doors.map[1], self.rom, self.exits.exit_original_data)
        for t in self.transitions.transitions:
            print(t.exit.id, t.entr.id)
        self.transitions.write(maps=self)
        #self.connect_events()
        #self.connections = Connections(self.doors.map[0], self.doors.door_rooms)
        self.connect_exits()

        # Move Event Trigger pointer & data location in ROM
        self.move_event_trigger_data()

        self.npcs.write()
        self.chests.write()
        self.events.write()
        self.long_events.write()
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

            # LONG EVENTS
            long_events_ptr_start = self.LONG_EVENT_PTR_START + cur_map["id"] * self.rom.SHORT_PTR_SIZE
            long_events_ptr_bytes = [0x00] * self.rom.SHORT_PTR_SIZE
            long_events_ptr_bytes[0] = cur_map["long_events_ptr"] & 0xff
            long_events_ptr_bytes[1] = (cur_map["long_events_ptr"] & 0xff00) >> 8
            self.rom.set_bytes(long_events_ptr_start, long_events_ptr_bytes)

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

    # def connect_events(self):
    #     # Perform Event modification for one-way entrances
    #     # For the connection "Event1" --> "Event2":
    #     for m in self.doors.map[1]:
    #         if m[0] >= 2000:
    #             # Collect exit event information for patching
    #             exit_info = event_exit_info[m[0]]
    #             exit_address = exit_info[0]
    #             exit_length = exit_info[1]
    #             exit_split = exit_info[2]
    #             exit_state = exit_info[3]
    #             exit_descr = exit_info[4]
    #             exit_location = exit_info[5]
    #
    #             src = self.rom.get_bytes(exit_address, exit_split)  # First half of event
    #
    #         else:
    #             # Handle the small number of one-way exits coded as doors
    #             exit_address = None
    #             exit_state = [False, False, False]
    #             this_exit = self.get_exit(m[0])
    #             exit_location = [self.exit_maps[m[0]], this_exit.x, this_exit.y]
    #
    #             src = [0x6a]
    #
    #         if m[1] >= 3000:
    #             # Right now the convention is that vanilla one-way entrance ID = (vanilla one-way exit ID + 1000)
    #             entr_info = event_exit_info[m[1] - 1000]
    #             entr_address = entr_info[0]
    #             entr_length = entr_info[1]
    #             entr_split = entr_info[2]
    #             entr_state = entr_info[3]
    #             entr_descr = entr_info[4]
    #             entr_location = entr_info[5]
    #
    #             src_end = self.rom.get_bytes(entr_address + entr_split,
    #                                          entr_length - entr_split)  # Second half of event
    #
    #         else:
    #             # Handle the small number of one-way entrances from doors
    #             entr_address = None
    #             entr_state = [False, False, False]
    #             entr_location = self.exits.exit_original_data[m[1] - 1000]
    #             # [dest_map, dest_x, dest_y, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]
    #
    #             # Load the map with facing & destination music; x coord; y coord; fade screen in & run entrance event, return
    #             src_end = [entr_location[0], entr_location[6] << 4, entr_location[1], entr_location[2], 0x80, 0xfe]
    #
    #         # Ignore forced vanilla / logical event patches
    #         if exit_address != entr_address:
    #
    #             # Check for other event patches & implement if found
    #             if m[0] in exit_event_patch.keys():
    #                 [src, src_end] = exit_event_patch[m[0]](src, src_end)
    #             if m[1] in entrance_event_patch.keys():
    #                 [src, src_end] = entrance_event_patch[m[1]](src, src_end)
    #
    #             # Perform common event patches
    #             if exit_state != entr_state:
    #                 ex_patch = []
    #                 en_patch = []
    #                 if exit_state[0] and not entr_state[0]:
    #                     # Character is hidden during the transition and not unhidden later.
    #                     # Add a "Show object 31" line ("0x41 0x31", two bytes)
    #                     en_patch += [0x41, 0x31]  # [field.ShowEntity(field_entity.PARTY0)]  #
    #                 if exit_state[1] and not entr_state[1]:
    #                     # Song override bit is on in the exit but not cleared in the entrance.
    #                     # Add a "clear $1E80($1CC)" (song override) before transition
    #                     ex_patch += [0xd3, 0xcc]  # [field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE)]  #
    #                 if exit_state[2] and not entr_state[2]:
    #                     # Hold screen bit is set (command 0x38) in the exit but not freed (command 0x39) in the entrance
    #                     # Add a "0x39 Free Screen" before transition
    #                     ex_patch += [0x39]  # [field.FreeScreen()]  #
    #
    #                 # Add patched lines before map transition
    #                 src = src[:-1] + ex_patch + src[-1:]
    #                 # Add patched lines after map transition
    #                 src_end = src_end[:5] + en_patch + src_end[5:]
    #
    #             # Combine events
    #             src.extend(src_end)
    #
    #             # Delete NOPs, if requested, to save space
    #             # Note there is the possibility for conflict with event_address_patch - be careful!
    #             if True:
    #                 src = delete_nops(src)
    #
    #             # Allocate space
    #             space = Allocate(Bank.CC, len(src), "Exit Event Randomize: " + str(m[0]) + " --> " + str(m[1]))
    #             new_event_address = space.start_address
    #
    #             # Check for event address patches & implement if found
    #             if m[0] in event_address_patch.keys():
    #                 src = event_address_patch[m[0]](src, new_event_address)
    #
    #             space.write(src)
    #
    #             print('Writing: ', m[0], ' --> ', m[1],
    #                   ':\n\toriginal memory addresses: ', hex(exit_address), ', ', hex(entr_address),
    #                   '\n\tbitstring: ', [hex(s)[2:] for s in src])
    #             print('\n\tnew memory address: ', hex(new_event_address))
    #
    #             if exit_address is not None:
    #                 if exit_location[1] == 'NPC':
    #                         # This is an NPC event.  (see e.g. Cid/Minecart entrance).  NPC ID is stored in location[2]
    #                         npc = self.get_npc(exit_location[0], exit_location[2] + 0x10)
    #                         npc.set_event_address(new_event_address)
    #
    #                 #if exit_address == 0xc8022:
    #                     # One-time hack for Cid/Minecart NPC entrance event.  If there are more, make a case for it.
    #                     #cid = self.get_npc(0x110, 0 + 0x10)
    #                     # print('Cid index = ', self.get_npc_index(0x110, 0 + 0x10))
    #                     #cid.set_event_address(new_event_address)
    #                     # cid.print()
    #
    #                 else:
    #                     # Update the MapEvent.event_address = Address(Event1a)
    #                     #this_event_id = self.events.event_address_index[exit_address - EVENT_CODE_START]
    #                     #if m[0] == 2017:  # HACK for shared event in Owzer's Mansion switch doors
    #                     #    this_event_id -= 1
    #                     #e_mxy = self.event_map_x_y[this_event_id]
    #                     e_mxy = event_exit_info[m[0]][5]
    #                     this_event = self.get_event(e_mxy[0], e_mxy[1], e_mxy[2])  # get event using [map_id, x, y] data
    #                     this_event.event_address = new_event_address - EVENT_CODE_START
    #
    #                     if m[0] in multi_events.keys():
    #                         # Other tiles must also be updated to point to the event at the appropriate offset
    #                         for le in multi_events[m[0]]:
    #                             le_addr = event_exit_info[le][0]
    #                             #le_id = self.events.event_address_index[le_addr - EVENT_CODE_START]
    #                             #le_mxy = self.event_map_x_y[le_id]
    #                             le_mxy = event_exit_info[le][5]
    #                             le_event = self.get_event(le_mxy[0], le_mxy[1], le_mxy[2]) # get event using [map_id, x, y] data
    #                             le_event.event_address = new_event_address + (le_addr - exit_address) - EVENT_CODE_START
    #
    #             else:
    #                 # Create a new MapEvent for this event
    #                 new_event = MapEvent()
    #                 new_event.x = exit_location[1]
    #                 new_event.y = exit_location[2]
    #                 new_event.event_address = new_event_address - EVENT_CODE_START
    #                 self.add_event(exit_location[0], new_event)
    #
    #             # (Event2 will be updated when the initiating door for Event2 is mapped)
    #
    #             # free previous event data space
    #             do_free = False
    #             if do_free:
    #                 Free(exit_address, exit_address + exit_length - 1)
    #
    #             if do_free:
    #                 print('\n\tFreed addresses: ', hex(exit_address), hex(exit_address + exit_length - 1))

    def connect_exits(self):
        # For all doors in doors.map[0], we want to find the exit and change where it leads to
        # Create sorted map, so they are connected in order:
        map = {}
        for m in self.doors.map[0]:
            if m[0] not in map.keys():
                map[m[0]] = m[1]
            if m[1] not in map.keys():
                map[m[1]] = m[0]

        temp = [m for m in map.keys() if m+4000 in exit_data.keys() and m+4000 not in map.keys()]
        for m in temp:
            # Add logical WoR exits to the map (with vanilla connections)
            map[m + 4000] = exit_data[m + 4000][0]
            map[map[m + 4000]] = m + 4000

            # Look up the rooms of these exits
            this_room = [r for r in room_data.keys() if (m+4000) in room_data[r][0]]
            self.doors.door_rooms[m + 4000] = this_room[0]
            that_room = [r for r in room_data.keys() if map[m+4000] in room_data[r][0]]
            self.doors.door_rooms[map[m+4000]] = that_room[0]

        # Need to add modified world map exits if they weren't randomized (to print exit events)
        for m in exit_data_patch.keys():
            if m not in map.keys():
                map[m] = exit_data[m][0]

                # Look up the rooms of these exits
                this_room = [r for r in room_data.keys() if m in room_data[r][0]]
                self.doors.door_rooms[m] = this_room[0]
                that_room = [r for r in room_data.keys() if map[m] in room_data[r][0]]
                self.doors.door_rooms[map[m]] = that_room[0]

        all_exits = list(map.keys())
        all_exits.sort()

        for m in all_exits:
            # Only connect real doors (virtual doors should never connect to real doors)
            if m < 2000:
                # Get exits associated with doors m and m_conn
                exitA = self.get_exit(m)

                # Attach exits:
                # Copy original properties of exitB_pair to exitA & vice versa.
                exitB_pairID = exit_data[map[m]][0] # Original connecting exit to B...
                if exitB_pairID not in self.exits.exit_original_data.keys():
                    # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                    exitB_pairID = exitB_pairID - 4000
                self.exits.copy_exit_info(exitA, exitB_pairID)  # ... copied to exit A

                if self.doors.verbose:
                    print('Connecting: ' + str(m) + ' to ' + str(map[m]))

                # THERE IS THE POTENTIAL FOR CONFLICTS between has_event_entrance() and create_exit_event()
                # Ultimately, we should probably handle this in there as well:
                #   one function that creates events and handles all cases would be ideal.
                if m in has_event_entrance.keys():
                    # move the event entrance to the partner tile
                    info = has_event_entrance[m]
                    this_event = self.get_event(info[0], info[1], info[2])

                    # Create an event tile that activates the event to this entrance on its connection
                    conn_exit = self.get_exit(map[m])
                    new_event = MapEvent()
                    new_event.x = conn_exit.x
                    new_event.y = conn_exit.y
                    new_event.event_address = this_event.event_address

                    self.add_event(self.exit_maps[map[m]], new_event) # add the new event
                    self.delete_event(info[0], info[1], info[2])  # delete the original event
                    if self.doors.verbose:
                        print('Moving event ', str(hex(info[0])) + ' (' + str(info[1]) + ',' + str(info[2]) + ') to',
                              str(hex(self.exit_maps[map[m]])) + ' (' + str(conn_exit.x) + ',' + str(conn_exit.y))

                # Write events on the exits to handle required conditions:
                # Write an event on top of exit m[1] to set the correct properties (world, parent map) for exit m[0]
                self.create_exit_event(m, map[m])

            elif m >= 4000:
                # This is a shared (WOB, WOR) exit (m - 4000, m).
                # The WOB exit & exit event (if necessary) are handled by the previous door code.
                self.shared_map_exit_event(m, map[m])

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
        SOUND_EFFECT = None # [None, 0x00 = Lore, 0x15 = Bolt3]

        # Write an event on top of exit d to set the correct properties (world, parent map) for exit d_ref
        # Collect information about the properties for the exit
        this_exit = self.get_exit(d)
        map_id = self.exit_maps[d]
        this_world = self.exit_world[d]  # room_data[self.doors.door_rooms[d]][3]

        # Collect information about the properties of the connecting exit
        that_world = self.exit_world[d_ref]
        #forced_world = room_data[self.doors.door_rooms[d_ref]][3]
        #forced_pmap = self.doors.door_rooms[d_ref] in force_update_parent_map.keys()

        # Check to make sure an exit event is required:
        # (1) the connection is in the other world
        ### (XXX) the connection requires a parent map update
        # (2) the connection requires special code (in entrance_event_patch[d_ref])
        # (3) the door requires special code (in exit_event_patch[d])
        require_event_flags = [
            (this_world != that_world), # ((forced_world is not None) and (forced_world != this_world)),
            #forced_pmap,
            d_ref in entrance_event_patch.keys(),
            d in exit_event_patch.keys()
        ]
        if require_event_flags.count(True) > 0:
            # Look for an existing event on this exit tile
            try:
                if self.doors.verbose:
                    print('looking for event at: ', hex(map_id), this_exit.x, this_exit.y)
                existing_event = self.get_event(map_id, this_exit.x, this_exit.y)
                # An event already exists.  It will need to be modified.
                # We have to be careful here: if it has a world door-switch event, we will need to do something else

                # Read in existing event code
                start_address = existing_event.event_address + EVENT_CODE_START
                src = [self.rom.get_byte(start_address)]
                while src[-1] != 0xfe:
                    src.append(self.rom.get_byte(start_address + len(src)))

                if self.doors.verbose:
                    print('Found an existing event: ', str(hex(map_id)), ' (', str(this_exit.x), ', ', str(this_exit.y),
                          '): ')
                    print('\t(', str(existing_event.x), ', ', str(existing_event.y), '):  ',
                          str(hex(existing_event.event_address)))

                # delete existing event
                self.delete_event(map_id, this_exit.x, this_exit.y)

            except IndexError:
                # event does not exist.  Make a new one.
                src = [field.Return()]

            this_address = 0x05eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

            if SOUND_EFFECT is not None:
                # Note this kills the direct "force world" event.
                src = [field.PlaySoundEffect(SOUND_EFFECT)] + src

            # If it's a new event that is just forcing the world, just directly call the "force world" event:
            e_length = len(src)
            if e_length == 1 and not require_event_flags[1:].count(True) > 0:
                if that_world == 0:
                    this_address = self.GO_WOB_EVENT_ADDR - EVENT_CODE_START
                elif that_world == 1:
                    this_address = self.GO_WOR_EVENT_ADDR - EVENT_CODE_START

                if self.doors.verbose:
                    print('Writing exit event:', d, '(pair =',d_ref,') @ ', hex(this_address))
                    print('\tReason: ', require_event_flags)

            else:
                #  (4) <code required when leaving room>
                #  (3) <code required when entering connection>
                #  (1,2) <required world-bit setting when entering WOB connection>
                #  (0) Return();  # Connection is handled by the door.

                # (1) Prepend call to force world bit event, if required
                if require_event_flags[0]:
                    if that_world == 0:
                        src = [field.ClearEventBit(event_bit.IN_WOR)] + src
                    elif that_world == 1:
                        src = [field.SetEventBit(event_bit.IN_WOR)] + src

                ## (2) Prepend call to force parent map, if required
                #if require_event_flags[1]:
                #    pmap_data = force_update_parent_map[self.doors.door_rooms[d_ref]]
                #    src = [field.SetParentMap(pmap_data[0], 2, pmap_data[1], pmap_data[2])] + src

                # (3) Prepend any data required by the connection
                if require_event_flags[1]:
                    src = entrance_event_patch[d_ref] + src

                # (4) Prepend any data required by the door
                if require_event_flags[2]:
                    src = exit_event_patch[d] + src

                # Write data to a new event & add it
                space = Write(Bank.CC, src, "Door Event " + str(d))
                this_address = space.start_address - EVENT_CODE_START

                if self.doors.verbose:
                    print('Writing exit event:', d, '(pair =',d_ref,') @ ', hex(this_address))
                    print('\tReason: ', require_event_flags)
                    print([str(s) for s in src])

            # Write the new event on the exit
            if self.exits.exit_type[d] == 'short':
                # Write the event on the short exit tile
                new_event = MapEvent()
                new_event.x = this_exit.x
                new_event.y = this_exit.y
                new_event.event_address = this_address
                self.add_event(map_id, new_event)
            elif self.exits.exit_type[d] == 'long':
                # Write the long event on the long exit tile
                new_event = LongMapEvent()
                new_event.x = this_exit.x
                new_event.y = this_exit.y
                new_event.direction = this_exit.direction
                new_event.size = this_exit.size
                new_event.event_address = this_address
                self.add_long_event(map_id, new_event)
                # Write the event on every tile in the long exit
                # for i in range(this_exit.size + 1):
                #    new_event = MapEvent()
                #    new_event.x = this_exit.x + i * (this_exit.direction == 0)  # horizontal exit
                #    new_event.y = this_exit.y + i * (this_exit.direction > 0)  # vertical exit
                #    new_event.event_address = this_address
                #    self.add_event(map_id, new_event)

    def shared_map_exit_event(self, d, d_ref):
        SOUND_EFFECT = None  # [None, 0x00 = Lore, 0x15 = Bolt3]
        # THIS IS A SHARED ROOM (i.e. the exit d is one of a (WOB, WOR) pair: (d-4000, d).
        # SINCE THE WOB CONNECTION IS ALWAYS DONE FIRST, WHEN THE WOR CONNECTION IS WRITTEN WE CAN DO:
        #   if IS_WOR:
        #       <code required when leaving WOR room>
        #       <code required when entering WOR connection>
        #       <required world-bit setting when entering WOR connection>
        #       <Load Map call for WOR connection>
        #   else:
        #       BranchTo(existing_event_code)
        # IN FF6 EVENT CODE, THIS IS:
        #   src = [field.BranchIfEventBitSet(IN_WOR, <address for WOR stuff>),
        #          field.Branch(<address for WOB stuff>),
        #          field.Return()]
        # So we should:
        #   (1) Find the address for WOB script
        #   (2) Write a script for the WOR branch
        #   (3) Write a script that chooses between them based on IN_WOR
        #   (4) make an event tile for the final script in (3)

        # Collect information about the properties for the exit
        this_exit = self.get_exit(d-4000)
        map_id = self.exit_maps[d-4000]
        this_world = self.exit_world[d] # note: virtual exits should always be WoR

        # Collect information about the properties of the connecting exit
        that_world = self.exit_world[d_ref]
        #forced_pmap = self.doors.door_rooms[d_ref] in force_update_parent_map.keys()

        # (1) the connection requires a specific world that is not this world
        ### (XXX) the connection requires a parent map update
        # (2) the connection requires special code (in entrance_event_patch[d_ref])
        # (3) the door requires special code (in exit_event_patch[d])
        require_event_flags = [
            ( (this_world != that_world)),
            # forced_pmap,
            d_ref in entrance_event_patch.keys(),
            d in exit_event_patch.keys()
        ]

        #if self.doors.verbose:
        #    print('Writing shared event at ' + str(d) + ' (ref = ' + str(d_ref) + ')')
        # Look for an existing event on this exit tile
        try:
            existing_event = self.get_event(map_id, this_exit.x, this_exit.y)
            # An event already exists.

            # Add Call to existing event code
            src = [field.Call(existing_event.event_address + EVENT_CODE_START), field.Return()]

            # delete existing event
            self.delete_event(map_id, this_exit.x, this_exit.y)

        except IndexError:
            # event does not exist.  Make a new one.
            src = [field.Return()]

        this_address = 0xa5eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

        # Send the player to the location that the connection's vanilla partner sends you to
        # [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown, ...]
        d_ref_partner = exit_data[d_ref][0]
        if d_ref_partner in self.exits.exit_original_data.keys():
            conn_data = self.exits.exit_original_data[d_ref_partner]
        else:
            # Probably a logical exit without tweaks.  Can use vanilla connection info.
            conn_data = self.exits.exit_original_data[d_ref_partner - 4000]

        #if d_ref in self.exit_maps.keys():
        #    conn_map = self.exit_maps[d_ref]
        #else:
        #    # Probably a logical exit without tweaks.  Can use vanilla connection info.
        #    conn_map = self.exit_maps[d_ref - 4000]

        wor_src = [field.FadeLoadMap(conn_data[0], conn_data[6], True, conn_data[1], conn_data[2], fade_in=True, entrance_event=True)]
        if conn_data[0] in [0, 1, 2]:
            # Include End command when loading world maps
            wor_src += [field.End()]
        wor_src += [field.Return()]

        if SOUND_EFFECT is not None:
            wor_src = [field.PlaySoundEffect(SOUND_EFFECT)] + wor_src

        # (1) Prepend call to force world bit event, if required
        if require_event_flags[0]:
            if that_world == 0:
                wor_src = [field.ClearEventBit(event_bit.IN_WOR)] + wor_src
            elif that_world == 1:
                wor_src = [field.SetEventBit(event_bit.IN_WOR)] + wor_src

        # (2) Prepend call to force parent map, if required
        #if require_event_flags[1]:
        #    pmap_data = force_update_parent_map[self.doors.door_rooms[d_ref]]
        #    wor_src = [field.SetParentMap(pmap_data[0], 2, pmap_data[1], pmap_data[2])] + wor_src

        # (2) Prepend any data required by the connection
        if require_event_flags[1]:
            wor_src = entrance_event_patch[d_ref] + wor_src

        # (3) Prepend any data required by the door
        if require_event_flags[2]:
            wor_src = exit_event_patch[d] + wor_src

        # Write data to a new event & add it
        if len(wor_src) > 0:
            space = Write(Bank.CC, wor_src, "WOR door Event " + str(d))
            this_address = space.start_address
            if self.doors.verbose:
                print('Writing WOR door event:', d, ' @ ', hex(this_address))
                print('\t',[str(s) for s in wor_src])

        src = [field.BranchIfEventBitSet(event_bit.IN_WOR, this_address)] + src

        # Write data to a new event & add it
        space = Write(Bank.CC, src, "Event tile for shared WOB/WOR door " + str(d))
        tile_address = space.start_address - EVENT_CODE_START

        if self.doors.verbose:
            print('Writing exit event:', d, '(pair =', d_ref, ') @ ', hex(tile_address))
            print('\tReason: ', require_event_flags)
            print([str(s) for s in src])

        # Write the new event on the exit
        if self.exits.exit_type[d-4000] == 'short':
            # Write the event on the short exit tile
            new_event = MapEvent()
            new_event.x = this_exit.x
            new_event.y = this_exit.y
            new_event.event_address = tile_address
            self.add_event(map_id, new_event)
        elif self.exits.exit_type[d-4000] == 'long':
            # Write the event on the long exit tile
            new_long_event = LongMapEvent()
            new_long_event.x = this_exit.x
            new_long_event.y = this_exit.y
            new_long_event.size = this_exit.size
            new_long_event.direction = this_exit.direction
            new_long_event.event_address = tile_address
            self.add_long_event(map_id, new_long_event)
            # Write the event on every tile in the long exit
            #for i in range(this_exit.size + 1):
            #    new_event = MapEvent()
            #    new_event.x = this_exit.x + i * (this_exit.direction == 0)  # horizontal exit
            #    new_event.y = this_exit.y + i * (this_exit.direction > 0)  # vertical exit
            #    new_event.event_address = tile_address
            #    self.add_event(map_id, new_event)

    def move_event_trigger_data(self):
        # Rewrite the ROM bits that look for event trigger data
        new_bank = 0xf1

        # Patch Field Program
        # C0 / BCAE: BF0200C4       LDA $C40002, X
        self.rom.set_byte(0x0bcb1, new_bank)
        # C0 / BCB4: BF0000C4       LDA $C40000, X
        self.rom.set_byte(0x0bcb7, new_bank)
        # C0 / BCBD: BF0000C4       LDA $C40000, X
        self.rom.set_byte(0x0bcc0, new_bank)
        # C0 / BCD3: BF0200C4       LDA $C40002, X
        self.rom.set_byte(0x0bcd6, new_bank)
        # C0 / BCED: BF0400C4       LDA $C40004, X
        self.rom.set_byte(0x0bcf0, new_bank)

        # Patch World Program
        # EE / 2176: BF0000C4   LDA $C40000, X
        self.rom.set_byte(0x2e2179, new_bank)
        # EE / 217C: BF0200C4   LDA $C40002, X
        self.rom.set_byte(0x2e217f, new_bank)
        # EE / 218B: BF0000C4   LDA $C40000, X
        self.rom.set_byte(0x2e218e, new_bank)
        # EE / 2193: BF0100C4   LDA $C40001, X
        self.rom.set_byte(0x2e2196, new_bank)
        # EE / 219B: BF0200C4   LDA $C40002, X
        self.rom.set_byte(0x2e219e, new_bank)
        # EE / 21A4: BF0300C4   LDA $C40003, X
        self.rom.set_byte(0x2e21a7, new_bank)
        # EE / 21AC: BF0400C4   LDA $C40004, X
        self.rom.set_byte(0x2e21af, new_bank)

        # Repoint event pointers & event tile data to the expanded ROM
        new_ref = (new_bank << 16) - 0xC00000
        self.events.DATA_START_ADDR = new_ref + (self.events.DATA_START_ADDR - self.EVENT_PTR_START)
        self.EVENT_PTR_START = new_ref

        space = Reserve(new_ref, new_ref + 0xffff, "Door Rando map event pointers")
        space = Reserve(0x040000, 0x041A0F, "Original map event pointer data", field.NOP())

        if self.doors.verbose:
            print('Moved Event Trigger data to ' + str(hex(new_bank)) + ': ' + str(hex(self.EVENT_PTR_START)) + ', ' + str(hex(self.events.DATA_START_ADDR)))
            for e in range(14):
                print('\t' + str(e) + ' (' + str(self.events.events[e].x) + ', ' + str(self.events.events[e].y) + '): ' + str(hex(self.events.events[e].event_address)))


    def door_rando_cleanup(self):
        # Perform cleanup actions, if we are doing door rando

        ### THAMASA WOR (0x158): replace manual long-event tiles with a real long_event
        # To be honest, we probably don't need these events at all.  They just check bits 0x196, 0x19E, 0x19F to see if Relm/Shadow story can progress.
        # Let's just delete them and free space (CB/7D69 - CB/7D82)
        THA_WR = 0x158

        # South Exit tiles
        #e = self.get_event(THA_WR, 20, 48)
        #le = LongMapEvent()
        #le.x = e.x
        #le.y = e.y
        #le.event_address = e.event_address
        #le.direction = 0
        #le.size = 5
        for x in range(20, 26):
            self.delete_event(THA_WR, x, 48)
        #self.add_long_event(THA_WR, le)

        # West Exit tiles
        #e = self.get_event(THA_WR, 0, 28)
        #le = LongMapEvent()
        #le.x = e.x
        #le.y = e.y
        #le.event_address = e.event_address
        #le.direction = 128  # Vertical
        #le.size = 3
        for y in range(28, 32):
            self.delete_event(THA_WR, 0, y)
        #self.add_long_event(THA_WR, le)
        Free(0x17d69, 0x17d82)