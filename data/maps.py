from data.map_property import MapProperty
from log.verbose import vprint

import data.npcs as npcs
from data.npc import NPC

from data.chests import Chests
import data.direction as direction
import data.doors as doors

import data.map_events as events
from data.map_event import MapEvent, LongMapEvent

import data.map_exits as exits
from data.map_exit import ShortMapExit, LongMapExit
# from data.connections import Connections

import data.world_map_event_modifications as world_map_event_modifications
from data.world_map import WorldMap

from memory.space import Allocate, Bank, Free, Write, Reserve

from instruction import field, world, asm
from instruction.event import EVENT_CODE_START
import instruction.field.entity as field_entity

from data.event_exit_data import event_exit_info, event_return_map
from data.event_exit_patches import exit_event_patch, entrance_event_patch, event_address_patch, \
    multi_events, entrance_door_patch, exit_door_patch, require_event_bit

from data.map_exit_extra import exit_data, exit_data_patch, exit_make_explicit, \
    event_door_connection_data, map_shuffle_airship_warp, map_shuffle_force_explicit, map_shuffle_partner_explicit, \
    dungeon_crawl_exit_destination_override
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
        # self.connections = Connections(self.exits)
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
        if args.door_randomize or args.map_shuffle:
            self.door_rando_cleanup()

    def read(self):
        self.maps = []
        self.properties = []

        for map_index in range(self.MAP_COUNT):
            self.maps.append({"id": map_index})

            map_property = MapProperty(self.rom, map_index)
            self.properties.append(map_property)
            self.maps[map_index]["name_index"] = map_property.name_index

            entrance_event_start = self.ENTRANCE_EVENTS_START_ADDR + map_index * self.rom.LONG_PTR_SIZE
            entrance_event = self.rom.get_bytes(entrance_event_start, self.rom.LONG_PTR_SIZE)
            self.maps[map_index]["entrance_event_address"] = entrance_event[0] | (entrance_event[1] << 8) | (
                        entrance_event[2] << 16)

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
        for m in range(len(self.maps) - 1):
            num_short = self.get_short_exit_count(m)
            for i in range(num_short):
                self.exit_maps[i + counter] = m
                se = self.exits.short_exits[i + counter]
                self.exit_x_y[i + counter] = [se.x, se.y]
            counter += num_short
        num_short_exits = counter
        for m in range(len(self.maps) - 1):
            num_long = self.get_long_exit_count(m)
            for i in range(num_long):
                self.exit_maps[i + counter] = m
                le = self.exits.long_exits[i + counter - num_short_exits]
                self.exit_x_y[i + counter] = [le.x, le.y]
            counter += num_long

        # Add non-standard "exits"
        for e in exit_data.keys():
            if e not in self.exit_maps.keys():
                if (e - 4000) in self.exit_maps.keys():
                    # Logical exit
                    self.exit_maps[e] = self.exit_maps[e - 4000]
                    self.exit_x_y[e] = self.exit_x_y[e - 4000]
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
        # self.event_maps = {}
        # self.event_map_x_y = {}
        # counter = 0
        # for m in range(len(self.maps)-1):
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
        npc_index += prev_npc_count  # add new npc to the end of current map's npcs
        self.npcs.add_npc(npc_index, new_npc)

        return new_npc_id  # return id of the new npc

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
        try:
            event = self.get_short_event(map_id, x, y)
        except:
            event = self.get_long_event(map_id, x, y)

        return event

    def get_short_event(self, map_id, x, y):
        first_event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        # last_event_id is an inclusive index, and get_event() searches [first_event_id : last_event_id + 1].
        # Subtract 1 so the search is bounded to this map's own events; otherwise it overreaches by one and
        # can falsely match the first event of the next populated map (see delete_short_event below).
        last_event_id = first_event_id + self.get_event_count(map_id) - 1
        return self.events.get_event(first_event_id, last_event_id, x, y)

    def add_event(self, map_id, new_event):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["events_ptr"] += MapEvent.DATA_SIZE

        event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        self.events.add_event(event_id, new_event)
        # print('added event: ', map_id, new_event.x, new_event.y, event_id, '. # events in this map: ', self.get_event_count(map_id))

    def delete_event(self, map_id, x, y):
        try:
            e = self.get_short_event(map_id, x, y)
            self.delete_short_event(map_id, x, y)

        except:
            e = self.get_long_event(map_id, x, y)
            self.delete_long_event(map_id, x, y)

    def delete_short_event(self, map_id, x, y):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["events_ptr"] -= MapEvent.DATA_SIZE

        first_event_id = (self.maps[map_id]["events_ptr"] - self.maps[0]["events_ptr"]) // MapEvent.DATA_SIZE
        last_event_id = first_event_id + self.get_event_count(map_id)
        self.events.delete_event(first_event_id, last_event_id, x, y)

    ### LONG EVENTS ###
    def get_long_event_count(self, map_id):
        return (self.maps[map_id + 1]["long_events_ptr"] - self.maps[map_id][
            "long_events_ptr"]) // LongMapEvent.DATA_SIZE

    def print_long_events(self, map_id):
        first_event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE
        self.long_events.print_range(first_event_id, self.get_long_event_count(map_id))

    def get_long_event(self, map_id, x, y):
        first_event_id = (self.maps[map_id]["long_events_ptr"] - self.maps[0]["long_events_ptr"]) // LongMapEvent.DATA_SIZE
        # last_event_id is an inclusive index, and get_event() searches [first_event_id : last_event_id + 1].
        # Subtract 1 so the search is bounded to this map's own long events; otherwise it overreaches by one
        # and can falsely match the first long event of the next populated map. That false match makes
        # create_exit_event() call delete_event(), which decrements every later map's long-event pointer but
        # then raises IndexError (swallowed by its 'except IndexError'), desyncing the long-event pointer table
        # by one entry for all subsequent maps (e.g. exit 1264's world-bit event landing on the wrong map).
        last_event_id = first_event_id + self.get_long_event_count(map_id) - 1
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
        last_event_id = first_event_id + self.get_long_event_count(map_id)
        self.long_events.delete_event(first_event_id, last_event_id, x, y)

    ### LONG EVENTS ###

    def get_exit(self, exit_id):
        map_id = self.exit_maps[exit_id]  # Get [map_id, x, y] for exits
        # xy = self.exit_x_y[exit_id]
        if self.exits.exit_type[exit_id] == 'short':
            first_exit_id = (self.maps[map_id]["short_exits_ptr"] - self.maps[0][
                "short_exits_ptr"]) // ShortMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_short_exit_count(map_id)
            return self.exits.get_short_exit_by_id(first_exit_id, last_exit_id, exit_id)
        elif self.exits.exit_type[exit_id] == 'long':
            first_exit_id = (self.maps[map_id]["long_exits_ptr"] - self.maps[0][
                "long_exits_ptr"]) // LongMapExit.DATA_SIZE
            last_exit_id = first_exit_id + self.get_long_exit_count(map_id)
            return self.exits.get_long_exit_by_id(first_exit_id, last_exit_id, exit_id)
        else:
            raise Exception('Unknown exit type')

    def get_short_exit_count(self, map_id):
        return (self.maps[map_id + 1]["short_exits_ptr"] - self.maps[map_id][
            "short_exits_ptr"]) // ShortMapExit.DATA_SIZE

    def print_short_exits(self, map_id):
        first_exit_id = (self.maps[map_id]["short_exits_ptr"] - self.maps[0][
            "short_exits_ptr"]) // ShortMapExit.DATA_SIZE
        self.exits.print_short_exit_range(first_exit_id, self.get_short_exit_count(map_id))

    def delete_short_exit(self, map_id, x, y):
        for map_index in range(map_id + 1, self.MAP_COUNT):
            self.maps[map_index]["short_exits_ptr"] -= ShortMapExit.DATA_SIZE

        map_first_short_exit = (self.maps[map_id]["short_exits_ptr"] - self.maps[0][
            "short_exits_ptr"]) // ShortMapExit.DATA_SIZE
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
        tilemap_addr = int.from_bytes(tilemap_addr_bytes, byteorder="little")

        next_tilemap_ptr_addr = tilemap_ptr_addr + self.rom.LONG_PTR_SIZE
        next_tilemap_addr_bytes = self.rom.get_bytes(next_tilemap_ptr_addr, self.rom.LONG_PTR_SIZE)
        next_tilemap_addr = int.from_bytes(next_tilemap_addr_bytes, byteorder="little")

        tilemaps_start = 0x19d1b0
        tilemap_len = next_tilemap_addr - tilemap_addr
        tilemap = self.rom.get_bytes(tilemaps_start + tilemap_addr, tilemap_len)
        decompressed = decompress(tilemap)

        map_width = 64
        impassable_box_tile = 62  # box tile that cannot be entered
        coordinates = [(19, 13), (15, 14), (18, 14)]  # coordinates of boxes to change
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
                          (0, 1, 14, VERT), (1, 1, 14, VERT),  # Include 2 layers to make sure it doesn't get skipped
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
            asm.BRA("DISABLE SAVE")  # replace the vanilla BPL $2EBF to always branch)
        )

    def _disable_map_name_popups(self):
        # Disable "show map name" popup for all exits (short and long)
        for exit in self.exits.short_exits:
            exit.displaylocationname = 0
        for exit in self.exits.long_exits:
            exit.displaylocationname = 0

    def mod(self, characters):
        self.npcs.mod(characters)
        self.chests.mod()
        self.world_map.mod()
        self.doors.mod(characters)
        if self.args.door_randomize or self.args.map_shuffle:
            # Spoiler log Door Rando section (before postprocess: the
            # dungeon-crawl override edits exit_data descriptions).
            if self.doors.map:
                self.doors.print()
            self.postprocess_door_map()
        self.events.mod()  # self.events.mod(self.doors, self)
        self.long_events.mod()  # LONG EVENTS

        ### FOR TESTING ONLY ###
        # self.testLongEvents()
        ### FOR TESTING ONLY ###

        self.exits.mod()  # self.exits.mod(self.doors.map[0], self)
        self._fix_imperial_camp_boxes()
        self._fix_Cid_timer_glitch()
        if self.args.no_saves == 'full':
            self._disable_saves()

        # Ruination mode: warp stones/spell send player to Esper World
        # Make all maps warpable EXCEPT Kefka's Tower and Phoenix Cave
        if self.args.ruination_mode:
            no_warp_maps = set([
                0x11F, 0x123, 0x124, 0x125, 0x126, 0x127, 0x128, 0x12F, 0x130,  # KT interior
                0x149, 0x14B, 0x14D, 0x14E, 0x14F,                                # KT mid
                0x150, 0x151, 0x152, 0x153,                                        # KT upper
                0x160, 0x162, 0x163, 0x164, 0x165,                                 # KT rooms
                0x199, 0x19A, 0x19B, 0x19C,                                        # KT factory/final
                #0x139, 0x13A, 0x13B, 0x13C, 0x13E,                                  # Phoenix Cave.  Actually allow warp in Phoenix cave as softlock protection if the player is dumb.
                0x167, 0x168, 0x169, 0x16A, 0x16B, 0x16C, 0x16D, 0x16E, 0x16F,  # Fanatics Tower
                0x170, 0x171, 0x172,                                              # Fanatics Tower (cont.)
                0x033,                                                              # Narshe Moogle Defense
            ])
            for map_index in range(len(self.maps)):
                if map_index in no_warp_maps:
                    self.properties[map_index].warpable = 0
                else:
                    self.properties[map_index].warpable = 1
            self._disable_map_name_popups()

        # Make all maps warpable for -door-randomize-dungeon-crawl
        elif self.args.debug or self.args.door_randomize_dungeon_crawl:
            keep_no_warp = [
                0x167, 0x168, 0x169, 0x16a, 0x16b, 0x16c, 0x16d, 0x16e, 0x16f, 0x170, 0x171, 0x172,  # Fanatics Tower
                0x139, 0x13a, 0x13b, 0x13c, 0x13e,  # phoenix cave
            ]
            for map_index, cur_map in enumerate(self.maps):
                if map_index not in keep_no_warp:  # protect Phoenix Cave, Fanatics Tower
                    self.properties[map_index].warpable = 1

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
        f = open('event_map&address_info_post.txt', 'w')
        f.write('# Event_ID: map_ID, (x, y), event_address')
        counter = 0
        for m in range(len(self.maps) - 1):
            num_events = self.get_event_count(m)
            for i in range(num_events):
                this_e = self.events.events[i + counter]
                f.write(str(counter + i) + ': ' + str(hex(m)) + " (" + str(this_e.x) + ", " + str(this_e.y) + ").  "
                        + str(hex(this_e.event_address)) + '\n')
            counter += num_events
        f.write('\n\n')
        for i in range(len(self.events.events)):
            this_e = self.events.events[i]
            f.write(str(counter + i) + ': ' + "(" + str(this_e.x) + ", " + str(this_e.y) + ").  "
                    + str(hex(this_e.event_address)) + '\n')
        f.close()

    # Door realization moved to doors/realize/ (Stage F); these thin
    # delegates keep the historical call sites (events.py, read(), write()).
    def postprocess_door_map(self):
        from doors.realize.door_map import postprocess_door_map
        return postprocess_door_map(self)

    def door_rando_cleanup(self):
        from doors.realize.exits import door_rando_cleanup
        return door_rando_cleanup(self)

    def move_event_trigger_data(self):
        from doors.realize.exits import move_event_trigger_data
        return move_event_trigger_data(self)

    def write(self):
        # self.write_post_diagnostic_info()
        # Patch the door randomizer exits & events before writing:
        if self.args.door_randomize or self.args.map_shuffle:
            from doors.realize import realize_doors
            realize_doors(self)

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

    def get_connection_location(self, exit_id, parent_map_ok=False):
        # Return the location [map_id, x, y, world] that a given exit_id should go to
        conn_id = self.door_map[exit_id]
        conn_pair = exit_data[conn_id][0]  # original connecting exit
        if conn_pair in self.exits.exit_original_data.keys():
            conn_data = self.exits.exit_original_data[conn_pair]   # [dest_map, dest_x, dest_y]
        elif conn_pair >= 4000:
            # Logical WOR exit hasn't been updated in exit_original_data.  Just use basic door ID.
            conn_data = self.exits.exit_original_data[conn_pair - 4000]

        if parent_map_ok:
            # It's OK to return a dest_map = 0x1ff.
            return conn_data[:3] + [exit_world[conn_id]]
        else:
            # Safely handle dest_map = 0x1ff
            if conn_data[0] in [0x1ff, 0x1fe]:
                # instead of return to parent map, use world map
                exit_map = exit_world[conn_pair]
            else:
                # wherever this goes is OK
                exit_map = conn_data[0]
            return [exit_map] + conn_data[1:3] + [exit_world[conn_id]] # [dest_map, dest_x, dest_y, dest_world]
