from event.event import *

class EsperWorld(Event):
    def name(self):
        return "Esper World"

    def init_event_bits(self, space):
        # Set NPC bits to avoid showing NPCs
        pass

    def mod(self):
        self.map_outside = 0x0d9   # Esper world hub
        self.map_gate_cave = 0x0da   # Esper gate
        self.map_interiors = 0x0db   # interior houses & rooms

        self.cleanup_entrance_events()

    def cleanup_entrance_events(self):
        # Turn off the entrance events for these rooms
        RETURN_ADDR = 0x5eb3
        self.maps.maps[self.map_outside]["entrance_event_address"] = RETURN_ADDR
        self.maps.maps[self.map_gate_cave]["entrance_event_address"] = RETURN_ADDR
        self.maps.maps[self.map_interiors]["entrance_event_address"] = RETURN_ADDR

        # Delete event tile in gate cave: 0xaa78f -- 0xaa7f4
        self.maps.delete_event(self.map_gate_cave, 56, 49)
        #print('Cleaned up Esper World')
