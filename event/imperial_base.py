from event.event import *
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class ImperialBase(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_sealed_gate
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle
        self.MAP_CROSSWORLD = args.map_shuffle_crossworld

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
            # modify exit position from "no terra" and "chucked out!" events
            exit_id = 1059
            if exit_id in self.maps.door_map.keys():
                self.exit_location = self.maps.get_connection_location(exit_id)
                # conn = self.maps.door_map[exit_id]  # connecting exit
                # conn_pair = exit_data[conn][0]  # original connecting exit
                # self.exit_location = [exit_world[conn_pair]] + \
                #                      self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]

        self.entrance_event_mod()

    def entrance_event_mod(self):
        SOLDIERS_BATTLE_ON_TOUCH = 0xb25b9
        SOLDIER_BATTLE_EVENT = 0xb2583

        space = Reserve(0xb25d6, 0xb25f8, "imperial base entrance event conditions", field.NOP())
        if self.args.character_gating:
            space.write(
                #field.BranchIfEventBitSet(event_bit.character_recruited(self.events["Sealed Gate"].character_gate()), SOLDIERS_BATTLE_ON_TOUCH),
                field.ReturnIfEventBitSet(event_bit.character_recruited(self.events["Sealed Gate"].character_gate())),
            )
            if self.DOOR_RANDOMIZE:
                from event.switchyard import SummonAirship
                space = Write(Bank.CB, SummonAirship(self.exit_location[0], self.exit_location[1],
                                                     self.exit_location[2], fadeout=True), "summon airship to imperial base")
                airship_addr = space.start_address
                space = Reserve(0xb25fd, 0xb2605, "imperial base thrown out summon airship", field.NOP())
                space.write(
                    field.Branch(airship_addr)
                )
            elif self.MAP_SHUFFLE:
                # CB/25FD: 97    Fade screen to black
                # CB/25FE: 5C    Pause execution until fade in or fade out is complete
                # CB/25FF: 6B    Load map $0000 (World of Balance) instantly, (upper bits $3000), place party at (164, 194), facing left, flags $00
                space = Reserve(0xb25fd, 0xb2604, 'Edit Imperial Base return to world map')
                src = [
                    field.FadeLoadMap(map_id=self.exit_location[0], x=self.exit_location[1], y=self.exit_location[2],
                                  direction=direction.DOWN, default_music=True, fade_in=True)
                ]
                if self.MAP_CROSSWORLD and self.exit_location[0] == 0x1:
                    # Prepend set world bit
                    src = [field.SetEventBit(event_bit.IN_WOR)] + src
                space.write(src)
                # CB/2605: FF        End map script

        else:
            space.write(
                #field.Branch(SOLDIERS_BATTLE_ON_TOUCH),
                field.Return(),
            )

        # Modify where touching the soldiers sends you
        if self.MAP_SHUFFLE:
            # There are three apparent "chucked out!" routines.  Not sure which is used, let's patch all of them
            src = [
                field.FadeLoadMap(map_id=self.exit_location[0], x=self.exit_location[1], y=self.exit_location[2],
                                  direction=direction.LEFT, default_music=True, fade_in=True),
                world.End()
            ]
            if self.MAP_CROSSWORLD and self.exit_location[0] == 0x1:
                # Prepend set world bit
                src = [field.SetEventBit(event_bit.IN_WOR)] + src

            space = Write(Bank.CB, src, 'Imperial base updated chucked out destination')
            chucked_address = space.start_address

            # Call 'chucked out' address at each location
            src = [field.Branch(chucked_address)]

            # CB/2587: 6A    Load map $0000 (World of Balance) after fade out, (upper bits $3000), place party at (164, 194), facing left, flags $00
            space = Reserve(0xb2587, 0xb258c, 'Chucked Out destination #1', field.NOP())
            space.write(src)

            # CB/2592: 6A    Load map $0000 (World of Balance) after fade out, (upper bits $3000), place party at (164, 194), facing left, flags $00
            space = Reserve(0xb2592, 0xb2597, 'Chucked Out destination #2', field.NOP())
            space.write(src)

            # CB/25B2: 6A    Load map $0000 (World of Balance) after fade out, (upper bits $3000), place party at (164, 194), facing left, flags $00
            space = Reserve(0xb25b2, 0xb25b7, 'Chucked Out destination #1', field.NOP())
            space.write(src)
