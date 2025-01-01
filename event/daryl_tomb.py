from event.event import *
from event.switchyard import *
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class DarylTomb(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_daryls_tomb
                          or args.door_randomize_all
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle
        self.MAP_CROSSWORLD = args.map_shuffle_crossworld

    def name(self):
        return "Daryl's Tomb"

    def character_gate(self):
        return self.characters.SETZER

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.exit_loc = [0x01, 25, 53]
        if self.MAP_SHUFFLE:
            # modify exit position
            south_id = 1242
            if south_id in self.maps.door_map.keys():
                conn_south = self.maps.door_map[south_id]  # connecting exit south
                conn_pair = exit_data[conn_south][0]  # original connecting exit
                self.exit_loc = [exit_world[conn_pair]] + \
                                self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]
                #print('Updated Daryl Cave quick exit: ', self.exit_loc)

        self.entrance_mod()
        self.staircase_mod()
        self.dullahan_battle_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)
        self.finish_check_mod()

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

        self.log_reward(self.reward)

    def entrance_mod(self):
        if self.args.character_gating:
            space = Reserve(0xa3f91, 0xa3f97, "daryl tomb require setzer in party", field.NOP())
            space.write(
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            )
        else:
            space = Reserve(0xa3f91, 0xa3f97, "daryl tomb require setzer in party", field.NOP())

        space = Reserve(0xa3f9c, 0xa3fa0, "daryl tomb make setzer party leader", field.NOP())
        space = Reserve(0xa3fb9, 0xa3fbc, "daryl tomb she was your friend?", field.NOP())

        space = Reserve(0xa3fbd, 0xa3fbd, "daryl tomb setzer opening entrance animation", field.NOP())
        space.write(field_entity.PARTY0)

        space = Reserve(0xa3fd0, 0xa3fd0, "daryl tomb setzer animation after entrance open", field.NOP())
        space.write(field_entity.PARTY0)

        space = Reserve(0xa3fda, 0xa3fdc, "daryl tomb could be anything lurking", field.NOP())

    def staircase_mod(self):
        src = [
            # reset turtle's positions before leaving in case player re-enters later
            field.ClearEventBit(event_bit.DARYL_TOMB_TURTLE1_MOVED),
            field.ClearEventBit(event_bit.DARYL_TOMB_TURTLE2_MOVED),
        ]

        if self.DOOR_RANDOMIZE:
            # Send the player to the switchyard to handle random connections
            event_id = 2058  # ID of Daryl's Tomb quick exit
            src += GoToSwitchyard(event_id)

            # (2b) Add the switchyard event tile that handles exit to the world map
            switchyard_src = SummonAirship(self.exit_loc[0], self.exit_loc[1], self.exit_loc[2])
            AddSwitchyardEvent(event_id, self.maps, src=switchyard_src)

        else:
            if self.MAP_CROSSWORLD:
                # Need to set/clear world bit before returning to world map
                if self.exit_loc[0] == 0x0:
                    src += [field.ClearEventBit(event_bit.IN_WOR)]
                else:
                    src += [field.SetEventBit(event_bit.IN_WOR)]

            # for convenience change staircase door to take player back out to wor
            src += [
                field.LoadMap(self.exit_loc[0], direction.DOWN, default_music = True, x = self.exit_loc[1],
                              y = self.exit_loc[2]),
                world.End(),
                field.Return()
            ]
        # Need to reserve 12 bytes for vanilla command.
        space = Reserve(0xa435d, 0xa436a, "daryl tomb staircase and getting falcon scenes", field.NOP())
        space.write(src)

    def dullahan_battle_mod(self):
        boss_pack_id = self.get_boss("Dullahan")

        space = Reserve(0xa4321, 0xa4327, "daryl tomb invoke battle dullahan", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def daryl_sleeps_here_mod(self, new_name):
        num_spaces = 15 - len(new_name) # try to center dialog

        daryl_sleeps_here_dialog_id = 2461 # previously 2464
        self.dialogs.set_text(daryl_sleeps_here_dialog_id, f"<line><{' ' * num_spaces}>{new_name} SLEEPS HERE<end>")

        space = Reserve(0xa42f9, 0xa42fb, "daryl tomb daryl sleeps here dialog", field.NOP())
        space.write(
            field.Dialog(daryl_sleeps_here_dialog_id, inside_text_box = False),
        )

    def character_mod(self, character):
        self.daryl_sleeps_here_mod(self.characters.get_name(character))

        space = Reserve(0xa4328, 0xa4333, "daryl tomb open staircase entrance", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
            field.FadeInScreen(),
        )

    def esper_item_mod(self):
        space = Reserve(0xa4329, 0xa4333, "daryl tomb open staircase entrance", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Turn(direction.UP),
            ),
        )
        return space

    def esper_mod(self, esper):
        self.daryl_sleeps_here_mod(self.espers.get_name(esper).upper())

        space = self.esper_item_mod()
        space.write(
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        )

    def item_mod(self, item):
        self.daryl_sleeps_here_mod(self.items.get_name(item).upper())

        space = self.esper_item_mod()
        space.write(
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        )

    def finish_check_mod(self):
        src = [
            field.SetEventBit(event_bit.DEFEATED_DULLAHAN),
            field.FinishCheck(),
            field.PlaySoundEffect(187),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "daryl tomb finish check")
        finish_check = space.start_address

        OPEN_BACK_EXIT = 0xaf1ed
        space = Reserve(0xa4334, 0xa433d, "daryl tomb open back exit", field.NOP())
        space.write(
            field.Call(finish_check),
            field.ShakeScreen(intensity = 2, permanent = False,
                              layer1 = True, layer2 = True, layer3 = True, sprite_layer = True),
            field.Call(OPEN_BACK_EXIT),
        )

    def door_rando_mod(self):
        # (1) Change map for Daryl's Tomb turtle #2 right door.
        # Change the tiles at map_id = 0x12C, Layer 1 (79, 2) with the following 2x1: $0A, $04 
        src = [
            field.SetMapTiles(1, 79, 2, 1, 2, [0x0a, 0x04]),
            field.SetMapTiles(2, 79, 1, 1, 1, [0x21]),
            field.BranchIfEventBitClear(event_bit.DARYL_TOMB_DOOR_SWITCH, 0xaf20f),
            # CA/F205: C0    If ($1E80($2B8) [$1ED7, bit 0] is clear), branch to $CAF20F
            field.Branch(0xaf20b)
        ]
        space = Write(Bank.CA, src, 'Daryls Tomb DR map modification')
        dr_map_address = space.start_address
        # Call this script in the entrance event:
        space = Reserve(0xaf205, 0xaf20a, "Daryls Tomb entrance event DR modification", field.NOP())
        space.write(field.Branch(dr_map_address))

        # 795: lambda info: set_y(info[9]-1, info),  # [797, "Darill's Tomb B2 Water Room Right Door"], move up 1 tile
        turtle2_exit = self.maps.get_exit(795)
        turtle2_exit.y -= 1  # move to [79, 2]
        # 797: lambda info: set_dest_y(info[2]-2, info),  #  [795, "Darill's Tomb B2 MIAB Hallway to Water Room"],
        miab_s_exit = self.maps.get_exit(797)
        miab_s_exit.dest_y -= 2  # Move to [79, 3] to match

        # (2) Make turtle #1 not activate if water is low
        src = [
            field.BranchIfEventBitSet(event_bit.DARYL_TOMB_WATER1_HIGH, 0xa4259),
            field.Return()
        ]
        space = Write(Bank.CA, src, 'Modified daryls tomb turtle #1 event')

        turtle_event = self.maps.get_event(0x12b, 56, 20)
        turtle_event.event_address = space.start_address - EVENT_CODE_START

        # (3) Make turtle #2 not activate if water is low
        src = [
            field.BranchIfEventBitSet(event_bit.DARYL_TOMB_WATER2_HIGH, 0xa42c0),
            field.Return()
        ]
        space = Write(Bank.CA, src, 'Modified daryls tomb turtle #2 event R')
        turtle2_event = self.maps.get_event(0x12c, 79, 6)
        turtle2_event.event_address = space.start_address - EVENT_CODE_START
