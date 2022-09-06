from data.map_event import MapEvent
from data.event_exit_info import event_exit_info
from event.event import *

class MapEvents():
    EVENT_COUNT = 1164
    DATA_START_ADDR = 0x040342

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
        for m in doors.map:
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
                src = self.rom.get_bytes(exit_address, exit_split)
                src.extend(self.rom.get_bytes(entr_address + entr_split, entr_length - entr_split))
                #space = Reserve(exit_address, exit_address + exit_length, "Umaro trapdoor initial memory", field.NOP())
                space = Write(Bank.CC, src, "Umaro trapdoor replaced memory")
                new_event_address = space.start_address

                # Update the MapEvent.event_address = Address(Event1a)
                self.events[self.event_address_index[exit_address]].event_address = new_event_address
                # Event2 will be updated when the initiating door for Event2 is mapped
                #   e.g. Event2a = Event2[0:split2] + Event3[split3:]; & so on.

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
