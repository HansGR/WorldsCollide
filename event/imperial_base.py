from event.event import *
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class ImperialBase(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_sealed_gate
                          or args.door_randomize_all
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Imperial Base"

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.ESPERS_CRASHED_AIRSHIP), # allow entrance without terra in party
            field.ClearEventBit(npc_bit.TREASURE_ROOM_DOOR_IMPERIAL_BASE),
        )

    def mod(self):
        self.exit_location = [0x0, 164, 194]
        if self.MAP_SHUFFLE:
            # modify exit position from "no terra" event
            exit_id = 1059
            if exit_id in self.maps.door_map.keys():
                conn = self.maps.door_map[exit_id]  # connecting exit
                conn_pair = exit_data[conn][0]  # original connecting exit
                self.exit_location = [exit_world[conn_pair]] + \
                                     self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]

        self.entrance_event_mod()

    def entrance_event_mod(self):
        SOLDIERS_BATTLE_ON_TOUCH = 0xb25b9

        space = Reserve(0xb25d6, 0xb25f8, "imperial base entrance event conditions", field.NOP())
        if self.args.character_gating:
            space.write(
                #field.BranchIfEventBitSet(event_bit.character_recruited(self.events["Sealed Gate"].character_gate()), SOLDIERS_BATTLE_ON_TOUCH),
                field.ReturnIfEventBitSet(event_bit.character_recruited(self.events["Sealed Gate"].character_gate())),
            )
            if self.DOOR_RANDOMIZE:
                from event.switchyard import SummonAirship
                space = Write(Bank.CB, SummonAirship(self.exit_location[0], self.exit_location[1],
                                                     self.exit_location[2]), "summon airship to imperial base")
                airship_addr = space.start_address
                space = Reserve(0xb25fd, 0xb2605, "imperial base thrown out summon airship", field.NOP())
                space.write(
                    field.Branch(airship_addr)
                )
            if self.MAP_SHUFFLE:
                # CB/25FF: 6B    Load map $0000 (World of Balance) instantly, (upper bits $3000), place party at (164, 194), facing left, flags $00
                space = Reserve(0xb25ff, 0xb2604, 'Edit Imperial Base return to world map')
                space.write(
                    field.LoadMap(map_id=self.exit_location[0], x=self.exit_location[1], y=self.exit_location[2],
                                  direction=direction.LEFT, default_music=True, fade_in=True)
                )
                # CB/2605: FF        End map script

        else:
            space.write(
                #field.Branch(SOLDIERS_BATTLE_ON_TOUCH),
                field.Return(),
            )
