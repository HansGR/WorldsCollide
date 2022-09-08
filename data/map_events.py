from data.map_event import MapEvent
from data.event_exit_info import event_exit_info, exit_event_patch
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

    def mod(self, doors):
        # Perform Event modification for one-way entrances
        # For the connection "Event1" --> "Event2":
        for m in doors.map[1]:
            if m[0] in event_exit_info.keys():
                # Reserve the code regions for (Event1) and (Event2)
                exit_info = event_exit_info[m[0]]
                exit_address = exit_info[0]
                exit_length = exit_info[1]
                exit_split = exit_info[2]

                # Right now the convention is that vanilla one-way entrance ID = (vanilla one-way exit ID + 1000)
                entr_info = event_exit_info[m[1] - 1000]
                entr_address = entr_info[0]
                entr_length = entr_info[1]
                entr_split = entr_info[2]

                # Write a new Event1a = Event1[0:split1] + Event2[split2:]
                src = self.rom.get_bytes(exit_address, exit_split)  # First half of event
                src_end = self.rom.get_bytes(entr_address + entr_split, entr_length - entr_split)
                if exit_info[3] and not entr_info[3]:
                    # Character is hidden during the transition and not unhidden later.
                    # Add a "Show object 31" line after map transition ("0x41 0x31", two bytes) after the 6A or 6B
                    src.extend(src_end[:6] + [0x41, 0x31] + src_end[6:])
                else:
                    src.extend(src_end)

                space = Allocate(Bank.CC, len(src), "Umaro trapdoor replaced memory")
                new_event_address = space.start_address

                # Check for event patches & implement if found
                if m[0] in exit_event_patch.keys():
                    src = exit_event_patch[m[0]](src, new_event_address)

                space.write(src)

                # Update the MapEvent.event_address = Address(Event1a)
                self.events[self.event_address_index[exit_address - self.BASE_OFFSET]].event_address = new_event_address - self.BASE_OFFSET
                # (Event2 will be updated when the initiating door for Event2 is mapped)

                # free previous event data space
                #Free(exit_address, exit_address + exit_length - 1)

                print('Writing: ', m[0], ' --> ', m[1],
                      ':\n\toriginal memory addresses: ', hex(exit_address), ', ', hex(entr_address),
                      '\n\tbitstring: ', [hex(s)[2:] for s in src])
                print('\n\tnew memory address: ', hex(new_event_address))

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
