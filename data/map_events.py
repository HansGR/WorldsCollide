from data.map_event import MapEvent
from data.event_exit_info import event_exit_info, exit_event_patch, entrance_event_patch, event_address_patch
from event.event import *
import time

class MapEvents():
    EVENT_COUNT = 1164
    DATA_START_ADDR = 0x040342
    BASE_OFFSET = 0xA0000

    def __init__(self, rom):
        self.rom = rom
        self.read()

    def read(self):
        self.events = []
        self.event_address_index = {}
        counter = 0
        for event_index in range(self.EVENT_COUNT):
            event_data_start = self.DATA_START_ADDR + event_index * MapEvent.DATA_SIZE
            event_data = self.rom.get_bytes(event_data_start, MapEvent.DATA_SIZE)

            new_event = MapEvent()
            new_event.from_data(event_data)
            self.events.append(new_event)
            self.event_address_index[new_event.event_address] = counter
            counter += 1

    def write(self):
        for event_index, event in enumerate(self.events):
            event_data = event.to_data()
            event_data_start = self.DATA_START_ADDR + event_index * MapEvent.DATA_SIZE
            self.rom.set_bytes(event_data_start, event_data)

    def mod(self, doors, maps):
        # Perform Event modification for one-way entrances
        # For the connection "Event1" --> "Event2":
        for m in doors.map[1]:
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
                this_exit = maps.exits.get_exit_from_ID(m[0])
                exit_location = [this_exit.x, this_exit.y, maps.exit_maps[m[0]]]

                src = [0x6a]

            if m[1] >= 3000:
                # Right now the convention is that vanilla one-way entrance ID = (vanilla one-way exit ID + 1000)
                entr_info = event_exit_info[m[1] - 1000]
                entr_address = entr_info[0]
                entr_length = entr_info[1]
                entr_split = entr_info[2]
                entr_state = entr_info[3]

                src_end = self.rom.get_bytes(entr_address + entr_split, entr_length - entr_split) # Second half of event

            else:
                # Handle the small number of one-way entrances from doors
                entr_address = None
                entr_state = [False, False, False]
                entr_location = maps.exits.exit_original_data[m[1] - 1000]  # [dest_x, dest_y, dest_map, refreshparentmap, enterlowZlevel, displaylocationname, facing, unknown]

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
                    # Add a "clear $1EB9 bit 4" (song override) before transition
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
                # Update the MapEvent.event_address = Address(Event1a)
                this_event_ID = self.event_address_index[exit_address - self.BASE_OFFSET]
                if m[0] == 2017:  # HACK for shared event in Owzer's Mansion switch doors
                    this_event_ID -= 1
                self.events[this_event_ID].event_address = new_event_address - self.BASE_OFFSET
                #print('Updated event ', this_event_ID, ': ', hex(exit_address - self.BASE_OFFSET), '-->', hex(new_event_address - self.BASE_OFFSET), '\n\n')
            else:
                # Create a new MapEvent for this event
                new_event = MapEvent()
                new_event.x = exit_location[0]
                new_event.y = exit_location[1]
                new_event.event_address = new_event_address - self.BASE_OFFSET
                maps.add_event(exit_location[2], new_event)


            # (Event2 will be updated when the initiating door for Event2 is mapped)

            # free previous event data space
            do_free = False
            if do_free:
                Free(exit_address, exit_address + exit_length - 1)

            if do_free:
                print('\n\tFreed addresses: ', hex(exit_address), hex(exit_address + exit_length - 1))



    def get_event(self, search_start, search_end, x, y):
        for event in self.events[search_start:search_end + 1]:
            if event.x == x and event.y == y:
                return event
        raise IndexError(f"get_event: could not find event at {x} {y}")

    def add_event(self, index, new_event):
        self.events.insert(index, new_event)
        self.EVENT_COUNT += 1

    def delete_event(self, search_start, search_end, x, y):
        for event in self.events[search_start:search_end + 1]:
            if event.x == x and event.y == y:
                self.events.remove(event)
                self.EVENT_COUNT -= 1
                return
        raise IndexError("delete_event: could not find event at {x} {y}")

    def print_range(self, start, count):
        for offset in range(count):
            self.events[start + offset].print()

    def print(self):
        for event in self.events:
            event.print()
