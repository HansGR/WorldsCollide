from event.event import *

class VectorCastle(Event):
    def name(self):
        return "Vector Castle"

    def init_event_bits(self, space):
        # Set NPC bits to avoid showing NPCs
        pass

    def mod(self):
        self.map_interiors = 0x0fa   # Interior rooms
        self.map_gate_cave = 0x0da   # Esper gate

        self.cleanup_entrance_events()

    def cleanup_entrance_events(self):
        # Turn off the entrance events for these rooms
        RETURN_ADDR = 0x5eb3
        self.maps.maps[self.map_interiors]["entrance_event_address"] = RETURN_ADDR

        # Delete event tiles in imperial castle
        self.maps.delete_event(self.map_interiors, 23, 12)
        #print('Cleaned up Imperial Castle')
