from data.map_exit import ShortMapExit, LongMapExit
from data.map_exit_extra import exit_data_patch, add_new_exits, event_door_connection_data

from data.map_event import MapEvent
from data.rooms import room_data

from instruction import field

from memory.space import Allocate, Bank, Write

class MapExits():
    SHORT_EXIT_COUNT = 0x469
    LONG_EXIT_COUNT = 0x98

    SHORT_DATA_START_ADDR = 0x1fbf02
    SHORT_DATA_END_ADDR   = 0x1FD9FF
    LONG_DATA_START_ADDR  = 0x2df882
    LONG_DATA_END_ADDR    = 0x2DFDFF

    def __init__(self, rom, DOOR_RANDO = [False, False]):
        self.rom = rom
        self.DOOR_RANDOMIZE = DOOR_RANDO[0]
        self.MAP_SHUFFLE = DOOR_RANDO[1]
        self.short_exits = []
        self.long_exits = []
        self.exit_original_data = {}
        self.exit_type = {}

        self.read()

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
            self.exit_original_data[new_exit.index] = [new_exit.dest_map, new_exit.dest_x, new_exit.dest_y,
                                                       new_exit.refreshparentmap, new_exit.enterlowZlevel,
                                                       new_exit.displaylocationname, new_exit.facing, new_exit.unknown,
                                                       new_exit.x, new_exit.y, new_exit.size, new_exit.direction]

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
            self.exit_original_data[new_exit.index] = [new_exit.dest_map, new_exit.dest_x, new_exit.dest_y,
                                                       new_exit.refreshparentmap, new_exit.enterlowZlevel,
                                                       new_exit.displaylocationname, new_exit.facing, new_exit.unknown,
                                                       new_exit.x, new_exit.y, new_exit.size, new_exit.direction]



    def write(self):
        for exit_index, exit in enumerate(self.short_exits):
            exit_data = exit.to_data()
            exit_data_start = self.SHORT_DATA_START_ADDR + exit_index * ShortMapExit.DATA_SIZE
            # Assert that the address being written doesn't go beyond the expected end point
            assert(exit_data_start < self.SHORT_DATA_END_ADDR)
            self.rom.set_bytes(exit_data_start, exit_data)

        for exit_index, exit in enumerate(self.long_exits):
            exit_data = exit.to_data()
            exit_data_start = self.LONG_DATA_START_ADDR + exit_index * LongMapExit.DATA_SIZE
            # Assert that the address being written doesn't go beyond the expected end point
            assert(exit_data_start < self.LONG_DATA_END_ADDR)
            self.rom.set_bytes(exit_data_start, exit_data)

    def mod(self):
        pass

    def _get_exit_from_ID(self, exitID):
        if self.exit_type[exitID] == 'short':
            #exit = self.short_exits[exitID]  # Exit = short exit
            exit = self.get_short_exit_by_id(0, self.SHORT_EXIT_COUNT, exitID)  # Exit = short exit
        else:
            #exit = self.long_exits[exitID - self.SHORT_EXIT_COUNT]  # Exit = long exit
            exit = self.get_long_exit_by_id(0, self.LONG_EXIT_COUNT, exitID)  # Exit = long exit
        return exit

    def copy_exit_info(self, mod_exit, pair_ID, type='dest'):
        # Copy information to mod_exit from another exit with exitID = pair_ID.
        # Original door data is stored in self.exit_original_data[exitID] as:
        #   [dest_map, dest_x, dest_y, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]
        pair_info = self.exit_original_data[pair_ID]
        mod_exit.dest_map = pair_info[0]
        mod_exit.dest_x = pair_info[1]
        mod_exit.dest_y = pair_info[2]
        # mod_exit.refreshparentmap = pair_info[3]  # do not want to copy refresh parent map!  Messes up warp stones.
        mod_exit.enterlowZlevel = pair_info[4]
        mod_exit.displaylocationname = pair_info[5]
        mod_exit.facing = pair_info[6]
        mod_exit.unknown = pair_info[7]

        if type == 'all':
            # Include exit location info
            mod_exit.x = pair_info[8]
            mod_exit.y = pair_info[9]
            mod_exit.size = pair_info[10]
            mod_exit.direction = pair_info[11]
        return

    def print_short_exit_range(self, start, count):
        for offset in range(count):
            self.short_exits[start + offset].print()

    def print_long_exit_range(self, start, count):
        for offset in range(count):
            self.long_exits[start + offset].print()

    def get_short_exit(self, search_start, search_end, x, y):
        for exit in self.short_exits[search_start:search_end + 1]:
            if exit.x == x and exit.y == y:
                return exit
        raise IndexError(f"get_short_exit: could not find short exit at {x} {y}")

    def get_short_exit_by_id(self, search_start, search_end, id):
        for exit in self.short_exits[search_start:search_end + 1]:
            if exit.index == id:
                return exit
        raise IndexError(f"get_short_exit: could not find short exit with index {id}")

    def get_long_exit(self, search_start, search_end, x, y):
        for exit in self.long_exits[search_start:search_end + 1]:
            if exit.x == x and exit.y == y:
                return exit
        raise IndexError(f"get_long_exit: could not find long exit at {x} {y}")

    def get_long_exit_by_id(self, search_start, search_end, id):
        for exit in self.long_exits[search_start:search_end + 1]:
            if exit.index == id:
                return exit
        raise IndexError(f"get_long_exit: could not find long exit with index {id}")

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

    def patch_exits(self, exit_list, verbose=False):
        # For DOOR_RANDOMIZE and MAP_SHUFFLE
        # Make all exits explicit (i.e. patch out "return to parent map") for door randomization
        # "Parent map" is set when entering a non-world-map from a world map.
        # - Warp stones send you back to the last parent map location.
        # - Some exits (but only exits to world map?) send you back to the last parent map location.
        for e in exit_list:
            if e in exit_data_patch.keys():
                #print('Patching:', e)
                if e in self.exit_original_data.keys():
                    #if self.DOOR_RANDOMIZE:  # apply patches if doing full door rando
                    # Update the "original data"
                    self.exit_original_data[e] = exit_data_patch[e](self.exit_original_data[e])
                    # Copy the "original data" to the exit itself
                    this_exit = self._get_exit_from_ID(e)
                    self.copy_exit_info(this_exit, e, type='all')
                    if verbose:
                        print('Patching: ', e, ':', self.exit_original_data[e])
                else:
                    if 6000 > e >= 4000:
                        # This is a logical exit.  Create an entry for it from its WOB pair.
                        #if self.DOOR_RANDOMIZE:  # apply patches if doing full door rando
                        self.exit_original_data[e] = exit_data_patch[e](self.exit_original_data[e-4000])
                        #else:
                        #self.exit_original_data[e] = self.exit_original_data[e - 4000]
                        if verbose:
                            print('Patching used logical:', e, self.exit_original_data[e])

            if e in event_door_connection_data.keys():
                # This is an event exit behaving as an exit, or a logical exit that cannot be copied from its vanilla
                # partner. Create an entry for it.
                self.exit_original_data[e] = event_door_connection_data[e]
                if verbose:
                    print('Patching event door:', e, self.exit_original_data[e])

            if e in add_new_exits.keys():
                pass

            #if e + 4000 in exit_data_patch.keys():
            #    # This door has a logical exit.  Create an entry for it from its WOB pair.
            #    self.exit_original_data[e+4000] = exit_data_patch[e+4000](self.exit_original_data[e])
            #    #print('Patching implied logical: ', e+4000, ':', self.exit_original_data[e+4000])
