from event.event import *
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class Nikeah(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle
        
    def name(self):
        return "Nikeah"

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.BOARDED_CRIMSON_ROBBERS_BOAT_NIKEAH),
        )

    def mod(self):
        self.airship_loc = [0x01, 147, 77]
        if self.MAP_SHUFFLE:
            # modify airship warp position
            nikeah_id = 5199
            if nikeah_id in self.maps.door_map.keys():
                self.airship_loc = self.maps.get_connection_location(nikeah_id)
                # conn_id = self.maps.door_map[nikeah_id]  # connecting exit south
                # conn_pair = exit_data[conn_id][0]  # original connecting exit
                # self.airship_loc = [exit_world[conn_pair]] + \
                #                    self.maps.exits.exit_original_data[conn_pair][1:3]  # [dest_map, dest_x, dest_y]
                # print('Updated Nikeah boat airship teleport: ', self.airship_loc)

        self.free_event_bit()
        self.airship_follow_boat_mod()

    def free_event_bit(self):
        # do not set event bit 0x2b0 so it can be used for other things
        space = Reserve(0xaed91, 0xaed92, "nikeah set event bit 0x2b0", field.NOP())

    def airship_follow_boat_mod(self):
        src = [
            vehicle.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.LoadMap(self.airship_loc[0], direction.DOWN, default_music = False,
                            x = self.airship_loc[1], y = self.airship_loc[2], fade_in = False, airship = True),
            vehicle.SetPosition(self.airship_loc[1], self.airship_loc[2]),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.FadeLoadMap(0xbb, direction.DOWN, default_music = True,
                                x = 24, y = 11, fade_in = True, entrance_event = True),
            field.SetParentMap(self.airship_loc[0], direction.DOWN, x = self.airship_loc[1], y = self.airship_loc[2]-1),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "nikeah boat from south figaro move airship")
        move_airship = space.start_address

        space = Reserve(0xa932a, 0xa9336, "nikeah boat from south figaro load map", field.NOP())
        space.write(
            vehicle.Branch(move_airship),
        )
