from data.map_exit import ShortMapExit, LongMapExit


class MapExits():
    SHORT_EXIT_COUNT = 0x469
    LONG_EXIT_COUNT = 0x98

    SHORT_DATA_START_ADDR = 0x1fbf02
    LONG_DATA_START_ADDR = 0x2df882

    def __init__(self, rom):
        self.rom = rom
        self.short_exits = []
        self.long_exits = []
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

    def write(self):
        for exit_index, exit in enumerate(self.short_exits):
            exit_data = exit.to_data()
            exit_data_start = self.SHORT_DATA_START_ADDR + exit_index * ShortMapExit.DATA_SIZE
            self.rom.set_bytes(exit_data_start, exit_data)

        for exit_index, exit in enumerate(self.long_exits):
            exit_data = exit.to_data()
            exit_data_start = self.LONG_DATA_START_ADDR + exit_index * LongMapExit.DATA_SIZE
            self.rom.set_bytes(exit_data_start, exit_data)

    def mod(self, doors):
        ### exit rando (2-way doors only)
        # For all doors in map, we want to find the exit and change where it leads to
        for m in doors.map[0]:
            # Figure out whether exits are short or long
            if self.exit_type[m[0]] == 'short':
                exitA = self.short_exits[m[0]]  # Exit A = short exit
            else:
                exitA = self.long_exits[m[0] - self.SHORT_EXIT_COUNT]  # Exit A = long exit
            if self.exit_type[m[1]] == 'short':
                exitB = self.short_exits[m[1]]  # Exit B = short exit
            else:
                exitB = self.long_exits[m[1] - self.SHORT_EXIT_COUNT]  # Exit B = long exit

            # Attach exits
            exitA.dest_x = exitB.x
            exitA.dest_y = exitB.y
            exitA.facing = exitB.facing
            exitA.dest_map = doors.door_maps[exitB.index]

            exitB.dest_x = exitA.x
            exitB.dest_y = exitA.y
            exitB.facing = exitA.direction
            exitB.dest_map = doors.door_maps[exitA.index]
        ### One-way doors are connected in map_events.mod()

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
