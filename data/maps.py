from data.map_property import MapProperty

import data.npcs as npcs
from data.npc import NPC

from data.chests import Chests
import data.direction as direction
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

from instruction import field, world
from instruction.event import EVENT_CODE_START
import instruction.field.entity as field_entity

from data.event_exit_info import event_exit_info, exit_event_patch, entrance_event_patch, event_address_patch, \
    multi_events, entrance_door_patch, exit_door_patch, require_event_bit

from data.map_exit_extra import exit_data, exit_data_patch, has_event_entrance, event_door_connection_data
from data.rooms import room_data, exit_world, shared_exits

from data.parse import delete_nops, branch_parser, get_branch_code

import data.event_bit as event_bit

from event.switchyard import *

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
        self.exits = exits.MapExits(rom, [args.door_randomize, args.map_shuffle])
        #self.connections = Connections(self.exits)
        self.world_map_event_modifications = world_map_event_modifications.WorldMapEventModifications(rom)
        self.world_map = WorldMap(rom, args)
        self.read()

        self.doors = doors.Doors(args)

        # Create an event code to set the world bit
        src_WOR = [field.SetEventBit(event_bit.IN_WOR), field.Return()]  # [0xd0, 0xa4, 0xfe]
        space = Write(Bank.CC, src_WOR, "Go To WoR")
        self.GO_WOR_EVENT_ADDR = space.start_address

        src_WOB = [field.ClearEventBit(event_bit.IN_WOR), field.Return()]  # [0xd1, 0xa4, 0xfe]
        space = Write(Bank.CC, src_WOB, "Go To WoB")
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

            # LONG EVENTS INITIALIZATION: Vanilla code has no long events.
            # Set initial offset to the vanilla value for each map.
            self.maps[map_index]["long_events_ptr"] = self.maps[0]["events_ptr"]

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

        ### Populate the dictionary for map_id given door ID
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

        # Append map_id information to exit_original_data
        for e in self.exits.exit_original_data.keys():
            if e in self.exit_maps.keys():
                self.exits.exit_original_data[e].append(self.exit_maps[e])


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
        #print('added event: ', map_id, new_event.x, new_event.y, event_id, '. # events in this map: ', self.get_event_count(map_id))

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
        #xy = self.exit_x_y[exit_id]
        if self.exits.exit_type[exit_id] == 'short':
            first_exit_id = (self.maps[map_id]["short_exits_ptr"] - self.maps[0]["short_exits_ptr"]) // ShortMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_short_exit_count(map_id)
            return self.exits.get_short_exit_by_id(first_exit_id, last_exit_id, exit_id)
        elif self.exits.exit_type[exit_id] == 'long':
            first_exit_id = (self.maps[map_id]["long_exits_ptr"] - self.maps[0]["long_exits_ptr"]) // LongMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_long_exit_count(map_id)
            return self.exits.get_long_exit_by_id(first_exit_id, last_exit_id, exit_id)
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

    def _fix_Cid_timer_glitch(self):
        from memory.space import Bank, Write
        import instruction.field as field
        from event.event import EVENT_CODE_START
        # If you start Cid's timer and then leave, the timer can affect event tile, NPC and objective triggering
        # Write some LongMapEvents to turn off the Cid timer when exiting to the world map.
        HORIZ = 0
        VERT = 128

        # LONG EVENT #1: play the lore sound effect on some horizontal tiles on the Blackjack
        src = [
            field.BranchIfEventBitSet(0x1b5, "SetBit"),
            field.ResetTimer(0),
            field.SetEventBit(0x1b5),
            "SetBit",
            field.Return(),
        ]
        space = Write(Bank.CC, src, 'Reset Cid event timer')

        map_id = 0x18c  # Cid's Island, Outside

        new_event_data = [(16, 1, 14, VERT), (15, 1, 14, VERT),  # (x, y, length, direction)
                          (0, 1, 14, VERT), (1, 1, 14, VERT),    # Include 2 layers to make sure it doesn't get skipped
                          (0, 1, 3, HORIZ), (0, 2, 3, HORIZ),
                          (7, 0, 2, HORIZ), (7, 1, 2, HORIZ),
                          (12, 1, 3, HORIZ), (12, 2, 3, HORIZ)]
        for i in range(len(new_event_data)):
            new_le = LongMapEvent()
            new_le.x = new_event_data[i][0]
            new_le.y = new_event_data[i][1]
            new_le.size = new_event_data[i][2]
            new_le.direction = new_event_data[i][3]
            new_le.event_address = space.start_address - EVENT_CODE_START
            self.add_long_event(map_id, new_le)

    def _disable_saves(self):
        # Ironmog mode -- disable saves
        space = Reserve(0x32ead, 0x32eae, asm.NOP())
        space.add_label("DISABLE SAVE", 0x32ebf)
        space.write(
            asm.BRA("DISABLE SAVE") # replace the vanilla BPL $2EBF to always branch)
        )

    def mod(self, characters):
        self.npcs.mod(characters)
        self.chests.mod()
        self.world_map.mod()
        self.doors.mod()
        if self.doors.verbose:
            print('Door connections:')
            for m in self.doors.map[0]:
                print('\t' + str(m[0]) + "<-->" + str(m[1]) + '\t(' + exit_data[m[0]][1] + '<-->' + exit_data[m[1]][1] + ')')
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
        self._fix_Cid_timer_glitch()
        if self.args.no_saves:
            self._disable_saves()

        # Make all maps warpable for -door-randomize-all
        if self.args.debug or self.args.door_randomize:
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
        if self.args.door_randomize or self.args.map_shuffle:
            #used_exits = list(set([m[0] for m in self.doors.map[0]] + [m[1] for m in self.doors.map[0]]))
            #print(used_exits)
            #self.exits.patch_exits(used_exits)
            # Create sorted map, so they are connected in order:
            map = {}
            for m in self.doors.map[0]:
                if m[0] not in map.keys():
                    map[m[0]] = m[1]
                if m[1] not in map.keys():
                    map[m[1]] = m[0]

            temp = [m for m in map.keys() if m + 4000 in exit_data.keys() and m + 4000 not in map.keys()]
            for m in temp:
                # Add logical WoR exits to the map (with vanilla connections)
                map[m + 4000] = exit_data[m + 4000][0]
                map[map[m + 4000]] = m + 4000

                # Look up the rooms of these exits
                this_room = [r for r in room_data.keys() if (m + 4000) in room_data[r][0]]
                self.doors.door_rooms[m + 4000] = this_room[0]
                that_room = [r for r in room_data.keys() if map[m + 4000] in room_data[r][0]]
                self.doors.door_rooms[map[m + 4000]] = that_room[0]

            # Patch exits if necessary
            used_exits = [m for m in map.keys()]
            #print(used_exits)
            self.exits.patch_exits(used_exits)

            used_events = [m[0] for m in self.doors.map[1]] \
                          + [m[0] for m in self.doors.map[0] if 2000 > m[0] >= 1500] \
                          + [m[1] for m in self.doors.map[0] if 2000 > m[1] >= 1500]

            for e in event_exit_info.keys():
                if (e in used_events or e in used_exits) and event_exit_info[e][0] is None:
                    # Update the event addresses
                    mapid = event_exit_info[e][5][0]
                    ex = event_exit_info[e][5][1]
                    ey = event_exit_info[e][5][2]
                    ev = self.get_event(mapid, ex, ey)
                    event_exit_info[e][0] = ev.event_address + EVENT_CODE_START
                    if self.doors.verbose:
                        print('Updated event exit info: ', e, hex(event_exit_info[e][0]))

            # Connect one-way event exits using the Transitions class
            self.transitions = Transitions(self.doors.map[1], self.rom, self.exits.exit_original_data, event_exit_info)
            self.transitions.write(maps=self)

            # Connect two-way doors
            self.connect_exits(map)

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


    def connect_exits(self, map):
        # For all doors in doors.map[0], we want to find the exit and change where it leads to
        # # Create sorted map, so they are connected in order:
        # map = {}
        # for m in self.doors.map[0]:
        #     if m[0] not in map.keys():
        #         map[m[0]] = m[1]
        #     if m[1] not in map.keys():
        #         map[m[1]] = m[0]
        #
        # temp = [m for m in map.keys() if m+4000 in exit_data.keys() and m+4000 not in map.keys()]
        # for m in temp:
        #     # Add logical WoR exits to the map (with vanilla connections)
        #     map[m + 4000] = exit_data[m + 4000][0]
        #     map[map[m + 4000]] = m + 4000
        #
        #     # Look up the rooms of these exits
        #     this_room = [r for r in room_data.keys() if (m+4000) in room_data[r][0]]
        #     self.doors.door_rooms[m + 4000] = this_room[0]
        #     that_room = [r for r in room_data.keys() if map[m+4000] in room_data[r][0]]
        #     self.doors.door_rooms[map[m+4000]] = that_room[0]
        #
        #     # Patch exits if necessary
        #     if m + 4000 in exit_data_patch.keys():
        #         self.exits.patch_exits([m+4000])

        # Need to add modified world map exits if they weren't randomized (to print exit events)
        if self.args.door_randomize:
            # Only do this if door_randomize, not map_shuffle
            for m in exit_data_patch.keys():
                if m not in map.keys():
                    map[m] = exit_data[m][0]
                    # Look up the rooms of these exits
                    #this_room = [r for r in room_data.keys() if m in room_data[r][0]]
                    #if len(this_room)> 0:
                    #    self.doors.door_rooms[m] = this_room[0]
                    #that_room = [r for r in room_data.keys() if map[m] in room_data[r][0]]
                    #if len(that_room)> 0:
                    #    self.doors.door_rooms[map[m]] = that_room[0]

        # Build dictionary of maps with entrance events that will need to be called
        self.exit_event_addr_to_call = {}
        # Must be referenced in:
        # (A) self.create_exit_event(m, map[m])     # for normal doors, m < 1500
        # (B) dt = Transitions(new_map, ...)        # for event tiles acting as doors, 1500 <= m < 4000
        # (C) self.shared_map_exit_event(m, map[m]) # for logical WOR exits
        for m in has_event_entrance.keys():
            if m in map.keys():
                # Record the event script address to call
                info = has_event_entrance[m]
                this_event = self.get_event(info[0], info[1], info[2])
                self.exit_event_addr_to_call[map[m]] = this_event.event_address + EVENT_CODE_START
                # Delete the event tile
                self.delete_event(info[0], info[1], info[2])  # delete the original event

        # Generate a final list of all exits that need to be connected
        all_exits = list(map.keys())
        all_exits.sort()  # apply the doors in order.
        #if self.doors.verbose:
            #print(all_exits)

        # Connect real doors:  m < 1500
        door_exits = [m for m in all_exits if m < 1500]
        for m in door_exits:
            if self.doors.verbose:
                print('Connecting: ' + str(m) + ' to ' + str(map[m]))
                #  + ": " + str(exit_data[m][1]) + ' to ' + str(exit_data[map[m]][1])

            # Get exits associated with doors m and m_conn
            exitA = self.get_exit(m)

            # Attach exits:
            # Copy original properties of exitB_pair to exitA & vice versa.
            exitB_pairID = exit_data[map[m]][0] # Original connecting exit to B...
            if exitB_pairID not in self.exits.exit_original_data.keys():
                if 1500 <= exitB_pairID < 4000:
                    # Event exit behaving as a door.
                    pass
                elif exitB_pairID >= 4000:
                    # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                    exitB_pairID = exitB_pairID - 4000

            self.exits.copy_exit_info(exitA, exitB_pairID)  # ... copied to exit A

            # Write events on the exits to handle required conditions:
            self.create_exit_event(m, map[m])



        # Connect event tiles that are acting as doors: 1500 <= m < 4000.  Treat them as transitions.
        transition_map = []
        transition_exits = [m for m in all_exits if 1500 <= m < 4000]
        for m in transition_exits:
            # We want to accumulate them first, then write them all together to avoid conflicts.
            if self.doors.verbose:
                print('Connecting: ' + str(m) + ' to ' + str(map[m]))
            transition_map.append([m, map[m]])
        dt = Transitions(transition_map, self.rom, self.exits.exit_original_data, event_exit_info,
                         self.exit_event_addr_to_call)
        dt.write(maps=self)

        # Connect logical WOR exits: 4000 <= m,  m_WOB = (m - 4000).
        wor_exits = [m for m in all_exits if m >= 4000]
        for m in wor_exits:
            # The WOB exit & exit event (if necessary) are handled by the previous door code.
            self.shared_map_exit_event(m, map[m])

    def create_exit_event(self, d, d_ref):
        # Write an event on top of exit d to set the correct properties (world, parent map) for exit d_ref.
        # Logical WOR exits (id >= 4000) are handled by maps.shared_map_exit_event(d, d_ref).
        SOUND_EFFECT = None  # [None, 0x00 = Lore, 0x15 = Bolt3]

        # Collect information about the properties for the exit
        this_exit = self.get_exit(d)
        map_id = self.exit_maps[d]
        this_world = self.exit_world[d]

        # Collect information about the properties of the connecting exit
        that_world = self.exit_world[d_ref]
        that_map = self.exit_maps[d_ref]

        # Check to make sure an exit event is required:
        # (1) the connection is in the other world
        # (2) the connection requires special code (in entrance_door_patch) or event bits (in require_event_bit)
        # (3) the door requires special code (in exit_door_patch[d])
        # (4) the connection has an event script that should be run upon entry (in has_event_entrance)
        # (5) the connection is a world map.  Move the airship to the player's location on the worldmap.
        # (6) the door is an event tile behaving as a door
        require_event_flags = [
            (this_world != that_world),
            d_ref in entrance_door_patch.keys() or d_ref in require_event_bit.keys(),
            d in exit_door_patch.keys(),
            d in self.exit_event_addr_to_call.keys(),
            that_map in [0x000, 0x001, SWITCHYARD_MAP]
        ]
        if self.args.map_shuffle and not self.args.door_randomize:
            # Don't summon the airship by default
            require_event_flags[4] = False

        if require_event_flags.count(True) > 0:
            # Need to use different commands for world maps vs field maps.
            # Look for an existing event on this exit tile
            try:
                if self.doors.verbose:
                    print('looking for event at: ', hex(map_id), this_exit.x, this_exit.y)
                existing_event = self.get_event(map_id, this_exit.x, this_exit.y)
                # An event already exists.  It will need to be modified.

                # Read in existing event code
                start_address = existing_event.event_address + EVENT_CODE_START
                src = [self.rom.get_byte(start_address)]
                while src[-1] != 0xfe:
                    src.append(self.rom.get_byte(start_address + len(src)))

                if self.doors.verbose:
                    print('WARNING: found an existing event: ', str(hex(map_id)), ' (', str(this_exit.x), ', ', str(this_exit.y),
                          '): ')
                    print('\t(', str(existing_event.x), ', ', str(existing_event.y), '):  ',
                          str(hex(existing_event.event_address)))

                # delete existing event
                self.delete_event(map_id, this_exit.x, this_exit.y)
                #existing_event_length = len(src) - 1

            except IndexError:
                # event does not exist.  Make a new one.
                src = [field.Return()]
                #existing_event_length = False

            this_address = 0x05eb3  # Default address to fail gracefully: event at $CA/5EB3 is just 0xfe (return)

            # If it's a new event that is just forcing the world, just directly call the "force world" event:
            e_length = len(src)
            if e_length == 1 and not require_event_flags[1:].count(True) > 0 and map_id > 2:
                if that_world == 0:
                    this_address = self.GO_WOB_EVENT_ADDR - EVENT_CODE_START
                elif that_world == 1:
                    this_address = self.GO_WOR_EVENT_ADDR - EVENT_CODE_START

                if self.doors.verbose:
                    print('Writing exit event:', d, '(pair =',d_ref,') @ ', hex(this_address))
                    print('\tReason: ', require_event_flags)

            else:
                #  (5) <code required when leaving room>
                #  (4) <code required when entering connection>
                #  (3) <required world-bit setting when entering WOB connection>
                #  (2) <call any required entrance script>
                #  (1) If going to the world map, summon the airship as well.
                #  (0) Return();  # Connection is handled by the door.

                # (1) If going to world map, also summon the airship
                if require_event_flags[4]:
                    # Note, in this case we don't need the terminal field.Return(), but it doesn't hurt and makes this
                    # more robust to errors.
                    # Get [x,y] location of the destination for the exit.
                    d_ref_pairID = exit_data[d_ref][0]  # Original connecting exit to d_ref..
                    if d_ref_pairID in self.exits.exit_original_data.keys():
                        conn_data = self.exits.exit_original_data[d_ref_pairID]  # [dest_map, dest_x, dest_y, ...]
                    elif d_ref_pairID >= 4000:  # Do we actually need this?
                        # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
                        conn_data = self.exits.exit_original_data[d_ref_pairID - 4000]
                    src = SummonAirship(conn_data[0], conn_data[1], conn_data[2]) + src

                # (2) Add call to entrance script, if any
                if require_event_flags[3]:
                    # This could be more elegant.
                    if map_id > 2:
                        # This is a normal door, just call the expected script
                        src = [field.Call(self.exit_event_addr_to_call[d])] + src
                    else:
                        # This is a worldmap door, and will be replaced by an event tile going to the switchyard.
                        # Parse the requested branching condition
                        load_address = self.exit_event_addr_to_call[d]
                        srcdata = self.rom.get_bytes(load_address, 6)
                        [comm_type, is_set, ebit, branch_addr] = branch_parser(srcdata)

                        if branch_addr == 0x5eb3:
                            # This is a "Return if event bit CONDITION" call.  Swap the condition and branch to the next line.
                            branch_addr = load_address + 6
                            is_set = not is_set

                        # Prepend the required branch condition to the switchyard script
                        src = get_branch_code(ebit, is_set, branch_addr, SWITCHYARD_MAP) + src

                # (3) Prepend call to force world bit event, if required
                if require_event_flags[0]:
                    if that_world == 0:
                        src = [field.ClearEventBit(event_bit.IN_WOR)] + src
                    elif that_world == 1:
                        src = [field.SetEventBit(event_bit.IN_WOR)] + src

                # (4) Prepend any data required by the connection
                if require_event_flags[1]:
                    if d_ref in entrance_door_patch.keys():
                        # These need to be inserted AFTER loading the map.
                        # Generate map load code for this door; the door itself will not be used.
                        load_map_src = self._get_load_map_code(d_ref)
                        if entrance_door_patch[d_ref] is list:
                            edp = entrance_door_patch[d_ref]
                        else:
                            # patch requires knowledge of arguments
                            edp = entrance_door_patch[d_ref](self.args)
                        src = src[:-1] + load_map_src + edp + src[-1:]

                    if d_ref in require_event_bit.keys():
                        entr_bits = require_event_bit[d_ref]
                        for k in entr_bits:
                            if entr_bits[k]:
                                src = [field.SetEventBit(k)] + src
                            else:
                                src = [field.ClearEventBit(k)] + src

                # (5) Prepend any data required by the door
                if require_event_flags[2]:
                    src = exit_door_patch[d] + src

                if map_id <= 2:
                    # This event is on the world map, where the event -> exit passthru trick doesn't work
                    # Solution: send the player to a dummy map, directly onto an event tile that does the necessary
                    # modifications and then sends them on to the destination.  A switchyard, if you will.
                    #dummy_map = 0x005   # mog's black map, 128 x 128
                    #dummy_x = d % 128   # unique ID in [x,y]
                    #dummy_y = d // 128
                    #[dummy_x, dummy_y] = switchyard_xy(d)

                    # (a) add a LoadMap command for the destination; write it to a dummy event
                    src_dummy = src[:-1] + [
                        field.LoadMap(this_exit.dest_map, direction=this_exit.facing, default_music=True,
                                      x=this_exit.dest_x, y=this_exit.dest_y, fade_in=True, entrance_event=True)
                        ] + src[-1:]
                    AddSwitchyardEvent(d, self, src=src_dummy)
                    #space = Write(Bank.CC, src_dummy, "Door Dummy Event " + str(d))
                    #dummy_address = space.start_address - EVENT_CODE_START
                    # (b) make a new event tile on the dummy map
                    #dummy_event = MapEvent()
                    #dummy_event.x = dummy_x
                    #dummy_event.y = dummy_y
                    #dummy_event.event_address = dummy_address
                    #self.add_event(dummy_map, dummy_event)

                    # (c) make a new src that loads the dummy map and places the character on the dummy tile.
                    if map_id > 0x002:
                        maptype = 'field'
                    else:
                        maptype = 'world'
                    src = GoToSwitchyard(d, map=maptype)
                    #src = [world.LoadMap(dummy_map, direction=direction.UP, default_music=False,
                    #                     x=dummy_x, y=dummy_y,
                    #                     fade_in=False, entrance_event=False), field.Return()]

                # Write data to a new event & add it
                space = Write(Bank.CC, src, "Door Event " + str(d))
                this_address = space.start_address - EVENT_CODE_START

                if self.doors.verbose:
                    print('Writing exit event:', d, '(pair =',d_ref,') @ ', hex(this_address))
                    print('\tReason: ', require_event_flags)
                    print([str(s) for s in src])

            if SOUND_EFFECT is not None:
                # Note this kills the direct "force world" event.
                src = [field.PlaySoundEffect(SOUND_EFFECT)] + src

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

            if map_id <= 2:
                # This event is on the world map, where the event -> exit passthru trick doesn't work.
                # (a) eventually, just delete the exit. but for now:
                # (b) move the exit it is replacing to somewhere else ('dummy' it)
                this_exit.x = d
                this_exit.y = 0
                # DO WE NEED to move the exit, though?  Does it matter?
                # I forget - on the world map, does the exit take effect before the event?  Is that why we did this?

    def shared_map_exit_event(self, d, d_ref):
        SOUND_EFFECT = None  # [None, 0x00 = Lore, 0x15 = Bolt3]
        # THIS IS A SHARED ROOM (i.e. the exit d is one of a (WOB, WOR) pair: (d-4000, d).
        # SINCE THE WOB CONNECTION IS ALWAYS DONE FIRST, WHEN THE WOR CONNECTION IS WRITTEN WE CAN DO:
        #   if IS_WOR:
        #       <code required when leaving WOR room>
        #       <code required when entering WOR connection>
        #       <required world-bit setting when entering WOR connection>
        #       <Call (or Branch to?) entrance_script code, if any>
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
        that_map = self.exit_maps[d_ref]

        # (1) the connection requires a specific world that is not this world
        # (2) the connection requires special code (in entrance_door_patch) or event bits (in require_event_bit)
        # (3) the door requires special code (in exit_door_patch[d])
        # (4) the door needs to run an entrance event script (in exit_event_addr_to_call[d])
        # (5) the connection is a world map: also summon the airship.
        require_event_flags = [
            ( (this_world != that_world)),
            d_ref in entrance_door_patch.keys() or d_ref in require_event_bit.keys(),
            d in exit_door_patch.keys(),
            d in self.exit_event_addr_to_call.keys(),
            that_map in [0x0, 0x1]
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
            # This is a logical exit without tweaks.  Can use vanilla connection info.
            conn_data = self.exits.exit_original_data[d_ref_partner - 4000]

        if require_event_flags[4]:
            wor_src = SummonAirship(conn_data[0], conn_data[1], conn_data[2])
        else:
            wor_src = [field.FadeLoadMap(conn_data[0], conn_data[6], True, conn_data[1], conn_data[2], fade_in=True, entrance_event=True)]
            if conn_data[0] in [0, 1, 2]:
                # Include End command when loading world maps
                wor_src += [field.End()]
            else:
                wor_src += [field.Return()]

        if SOUND_EFFECT is not None:
            wor_src = [field.PlaySoundEffect(SOUND_EFFECT)] + wor_src

        # (0) Prepend a call to entrance event script, if any
        # NOTES: This is trying to replicate the event-tile passthru to a door.
        # It's probably not going to work - it will complete the event script, and then ALWAYS load the map.
        # What we need is to replicate the event script code by doing *here*:
        #   [field.BranchIfEventBitCONDITION(eventbit, branchaddr)]
        # for whatever the appropriate branch condition is.
        # So for example, the entry script to Cyan's Cliff is:
        #   CC/3FA7: C0    If ($1E80($0D2) [$1E9A, bit 2] is set), branch to $CA5EB3 (simply returns)
        #   ... <continue script until hitting an 0xfe>
        # ... And the one for Doma Siege is:
        #   ['b0', '40', '80', 'c2', '9a', '1',   # world.BranchIfEventBitSet(0x40, 0x19ac2)
        #    'd3', '78', '0', '21', '2a', '40',   # world.LoadMap(0x78, x=0x21, y = 0x2a, ...)
        #    'fe']                                # field.Return()
        # In these cases (also in Transitions version), we want to:
        #   (1) In the case of Cyan's Cliff:
        #       wor_src = [field.BranchIfEventBitClear(0x0d2, 0xc3fa7 + 6] + wor_src
        #   (2) In the case of Doma Siege:
        #       wor_src = [field.BranchIfEventBitSet(0x40, doma_siege_addr)] + wor_src
        # Right now, we're just copying the address from the tile.  our options are:
        #   (A) Parse the data in the event script; make the right choice based on it
        #   (B) Track what needs to happen for each exit as metadata, in has_entrance_event
        # Let's try A for now.
        if require_event_flags[3]:
            # Parse the requested branching condition
            load_address = self.exit_event_addr_to_call[d]
            srcdata = self.rom.get_bytes(load_address, 6)
            [comm_type, is_set, ebit, branch_addr] = branch_parser(srcdata)

            if branch_addr == 0x5eb3:
                # This is a "Return if event bit CONDITION" call.  Swap the condition and branch to the next line.
                branch_addr = load_address + 6
                is_set = not is_set

            # Prepend the required branch condition
            wor_src = get_branch_code(ebit, is_set, branch_addr, map_id) + wor_src

        # (1) Prepend call to force world bit event, if required
        if require_event_flags[0]:
            if that_world == 0:
                wor_src = [field.ClearEventBit(event_bit.IN_WOR)] + wor_src
            elif that_world == 1:
                wor_src = [field.SetEventBit(event_bit.IN_WOR)] + wor_src

        # (2) Prepend any data required by the connection
        if require_event_flags[1]:
            if d_ref in entrance_door_patch.keys():
                # These need to be inserted AFTER loading the map.
                # Generate map load code for this door; the door itself will not be used.
                load_map_src = self._get_load_map_code(d_ref)
                wor_src = wor_src[:-1] + load_map_src + entrance_door_patch[d_ref] + wor_src[-1:]

            if d_ref in require_event_bit.keys():
                entr_bits = require_event_bit[d_ref]
                for k in entr_bits:
                    if entr_bits[k]:
                        wor_src = [field.SetEventBit(k)] + wor_src
                    else:
                        wor_src = [field.ClearEventBit(k)] + wor_src

        # (3) Prepend any data required by the door
        if require_event_flags[2]:
            wor_src = exit_door_patch[d] + wor_src

        # Write WOR data to a new event script
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

    def _get_load_map_code(self, entr_id):
        # Generate load map code for a given door
        partner_id = exit_data[entr_id][0]  # vanilla partner of door
        partner_data = self.exits.exit_original_data[partner_id]  # connection data for vanilla partner
        map_id = partner_data[0]  # destination map
        x = partner_data[1]       # destination x
        y = partner_data[2]       # destination y
        direction = partner_data[6]   # facing after transit
        src = [field.LoadMap(map_id=map_id, direction=direction, x=x, y=y,
                             default_music=True, fade_in=True, entrance_event=True)]
        return src

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
            #for e in range(14):
            #    print('\t' + str(e) + ' (' + str(self.events.events[e].x) + ', ' + str(self.events.events[e].y) + '): ' + str(hex(self.events.events[e].event_address)))

    def door_rando_cleanup(self):
        # Perform cleanup actions, if we are doing door rando

        ### THAMASA WOR (0x158): replace manual long-event tiles with a real long_event
        # We don't need these events: they just check bits 0x196, 0x19E, 0x19F to see if Relm/Shadow story can progress.
        # Let's just delete them and free space (CB/7D69 - CB/7D82)
        THA_WR = 0x158

        # South Exit tiles
        for x in range(20, 26):
            self.delete_event(THA_WR, x, 48)

        # West Exit tiles
        for y in range(28, 32):
            self.delete_event(THA_WR, 0, y)

        # Note: This line caused SwdTech to break the game - because I forgot the EVENT_CODE_START offset!
        Free(0x17d69 + EVENT_CODE_START, 0x17d82 + EVENT_CODE_START)
