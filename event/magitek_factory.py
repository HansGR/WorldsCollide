from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class MagitekFactory(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.DOOR_RANDOMIZE = (args.door_randomize_magitek_factory
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Magitek Factory"

    def character_gate(self):
        return self.characters.CELES

    def init_rewards(self):
        self.reward1 = self.add_reward(RewardType.ESPER | RewardType.ITEM)
        self.reward2 = self.add_reward(RewardType.ESPER | RewardType.ITEM)
        self.reward3 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.TALKED_TO_IFRIT_MAGITEK_FACTORY),
            field.SetEventBit(event_bit.TALKED_TO_SHIVA_MAGITEK_FACTORY),
            field.SetEventBit(event_bit.MET_SETZER_AFTER_MAGITEK_FACTORY),
        )

    def mod(self):
        self.setzer_npc_id = 0x18
        self.setzer_npc = self.maps.get_npc(0x0f0, self.setzer_npc_id)

        self.airship_position = [0x00, 120, 188]
        if self.MAP_SHUFFLE:
            exit_id = 1228
            if exit_id in self.maps.door_map.keys():
                self.airship_position = self.maps.get_connection_location(exit_id)
                # conn_id = self.maps.door_map[exit_id]  # connecting exit south
                # conn_pair = exit_data[conn_id][0]  # original connecting exit
                # self.airship_position = [exit_world[conn_pair]] + \
                #                    self.maps.exits.exit_original_data[conn_pair][1:3]  # [dest_map, dest_x, dest_y]

        self.vector_mod()

        if self.reward1.type == RewardType.ESPER:
            self.ifrit_shiva_esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            self.ifrit_shiva_item_mod(self.reward1.id)
        self.ifrit_shiva_battle_mod()

        if self.reward2.type == RewardType.ESPER:
            self.number024_esper_mod(self.reward2.id)
        elif self.reward2.type == RewardType.ITEM:
            self.number024_item_mod(self.reward2.id)

        self.esper_tubes_mod()

        self.minecart_mod()
        if not self.args.fixed_encounters_original:
            self.fixed_battles_mod()
        self.number128_battle_mod()

        if self.reward3.type == RewardType.CHARACTER:
            self.character_mod(self.reward3.id)
        elif self.reward3.type == RewardType.ESPER:
            self.esper_mod(self.reward3.id)

        self.crane_battle_mod()
        self.after_cranes_mod()
        self.guardian_mod()

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)
        self.log_reward(self.reward3)

        if self.DOOR_RANDOMIZE:
            self.mtek_1_mod()

        if self.MAP_SHUFFLE:
            self.map_shuffle_mod()


    def vector_mod(self):
        # npcs used to block/enter magitek factory
        sympathizer_npc_id = 0x10
        north_soldier_id = 0x11
        red_soldier_id = 0x12
        south_soldier_id = 0x13

        mtek_block_left_id = 0x20
        mtek_block_mid_id = 0x21
        mtek_block_right_id = 0x22

        # never show vector redish while burning, so hide npcs here instead
        # also do not conditionally branch to 0xc9540, always execute npc queues/movement
        space = Reserve(0xc9527, 0xc953f, "vector entrance event", field.NOP())
        space.add_label("NPC_QUEUES", 0xc9540)
        space.write(
            field.HideEntity(sympathizer_npc_id),
        )
        if self.args.character_gating:
            space.write(
                field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), "NPC_QUEUES"),
            )
        space.write(
            field.HideEntity(north_soldier_id),
            field.HideEntity(red_soldier_id),
            field.HideEntity(south_soldier_id),
        )

        if self.DOOR_RANDOMIZE:
            space.write(
                field.HideEntity(mtek_block_mid_id),
                #field.HideEntity(mtek_block_right_id),
            )

        space.write(
            field.Branch("NPC_QUEUES"),
        )

        # delete jump up onto boxes event
        self.maps.delete_event(0x0f2, 43, 38)

        # delete getting caught after passing guards events
        self.maps.delete_event(0x0f2, 56, 39)
        self.maps.delete_event(0x0f2, 57, 39)
        self.maps.delete_event(0x0f2, 58, 39)

    def ifrit_shiva_mod(self, esper_item_instructions):
        ifrit_npc_id = 0x14
        shiva_npc_id = 0x15

        # delete kefka throwing ifrit/shiva into trash tile events
        self.maps.delete_event(0x107, 40, 32)
        self.maps.delete_event(0x107, 41, 32)
        self.maps.delete_event(0x107, 42, 32)

        space = Reserve(0xc7962, 0xc7964, "magitek factory well, ramuh", field.NOP())
        space = Reserve(0xc7986, 0xc7988, "magitek factory gestahl has grabbed our friends", field.NOP())
        space = Reserve(0xc7998, 0xc799a, "magitek factory they drained our powers", field.NOP())

        space = Reserve(0xc79a4, 0xc79cf, "magitek factory ifrit/shiva magicite", field.NOP())
        src = []
        if self.args.flashes_remove_most or self.args.flashes_remove_worst:
            src.append(field.FlashScreen(field.Flash.NONE))
        else:
            src.append(field.FlashScreen(field.Flash.WHITE))

        src.append([
            field.PlaySoundEffect(80),
            field.HideEntity(ifrit_npc_id),
            field.HideEntity(shiva_npc_id),
            field.RefreshEntities(),
            field.ClearEventBit(npc_bit.IFRIT_SHIVA_MAGITEK_FACTORY),
            field.ClearEventBit(event_bit.DISABLE_HOOK_MAGITEK_FACTORY),
            field.Pause(1.5),

            esper_item_instructions,
            field.SetEventBit(event_bit.GOT_IFRIT_SHIVA),
            field.FinishCheck(),
            field.Return(),
        ])
        space.write(src)

    def ifrit_shiva_esper_mod(self, esper):
        self.ifrit_shiva_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def ifrit_shiva_item_mod(self, item):
        self.ifrit_shiva_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def ifrit_shiva_battle_mod(self):
        boss_pack_id = self.get_boss("Ifrit/Shiva")

        space = Reserve(0xc7958, 0xc795e, "magitek factory invoke battle ifrit/shiva", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def number024_mod(self, esper_item_instructions):
        boss_pack_id = self.get_boss("Number 024")

        space = Reserve(0xc79ed, 0xc79f3, "magitek factory number 024 battle", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

        # use some of the receive ifrit/shiva magicite space
        space = Reserve(0xc79d0, 0xc79ec, "magitek factory ifrit/shiva magicite", field.NOP())
        space.write(
            Read(0xc79f7, 0xc79fa), # clear npc bit, fade in, wait for fade
            esper_item_instructions,
            field.SetEventBit(event_bit.DEFEATED_NUMBER_024),
            field.FinishCheck(),
            field.Return(),
        )
        receive_reward = space.start_address

        space = Reserve(0xc79f7, 0xc79fa, "magitek factory number 024 battle", field.NOP())
        space.write(
            field.Call(receive_reward),
        )

    def number024_esper_mod(self, esper):
        self.number024_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def number024_item_mod(self, item):
        self.number024_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def esper_tubes_mod(self):
        cid_npc_id = 0x1c
        elevator_npc_id = 0x22 # elevator is also an npc

        if self.DOOR_RANDOMIZE:
            # Make switch scene repeatable: write over switch condition
            # CC/7A60: C2    If ($1E80($1B0) [$1EB6, bit 0] is clear) or ($1E80($1B4) [$1EB6, bit 4] is clear) or ($1E80($068) [$1E8D, bit 0] is set), branch to $CA5EB3 (simply returns)
            space = Reserve(0xc7a60, 0xc7a69, "magitek factory esper room switch", field.NOP())
            space.write(
                field.BranchIfAny([0x1b0, False, 0x1b4, False], 0xa5eb3)
            )

        space = Reserve(0xc7ec9, 0xc7ecb, "magitek factory cid ooh, ooh", field.NOP())
        space = Reserve(0xc7ed1, 0xc7edc, "magitek factory characters turn down after screen shake", field.NOP())

        space = Reserve(0xc7ee4, 0xc7eef, "magitek factory turn party towards cid", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Turn(direction.LEFT),
            ),
        )

        space = Reserve(0xc7ef6, 0xc7ef8, "magitek factory this is a disaster", field.NOP())
        space = Reserve(0xc7f04, 0xc7f16, "magitek factory combine party members", field.NOP())

        space = Reserve(0xc7a6c, 0xc7a84, "magitek factory tube espers and celes scene", field.NOP())
        space.add_label("CID_ENTER", 0xc7ec4)
        space.write(
            field.FadeOutSong(128),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.DOWN, 2),
            ),
            field.EntityAct(cid_npc_id, True,
                field_entity.SetPosition(18, 12),
            ),
            field.EntityAct(elevator_npc_id, True,
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Move(direction.UP, 3),
            ),

            field.Branch("CID_ENTER"), # skip scene
        )

    def minecart_mod(self):
        space = Reserve(0xc7f6c, 0xc7f71, "magitek factory load elevator ride down with cid map", field.NOP())
        space = Reserve(0xc7f80, 0xc7fc2, "magitek factory elevator ride down with cid", field.NOP())
        # if not self.DOOR_RANDOMIZE:   # Not needed with JMP technique
        #     space.write(
        #         field.Branch(space.end_address + 1), # skip nops
        #     )
        space = Reserve(0xc8014, 0xc801a, "magitek factory move party down after elevator", field.NOP())
        space = Reserve(0xc8027, 0xc802a, "magitek factory celes i've known her", field.NOP())
        space = Reserve(0xc803a, 0xc803d, "magitek factory no! it's kefka!", field.NOP())
        space = Reserve(0xc805c, 0xc805e, "magitek factory go!!", field.NOP())

        # shorten the mine cart script, how i think this works:
        # commands 00-07 are for the mine cart ride (which parts to show? e.g. straight, left, right, up, down, fork, ...)
        # commands e0 and e1 are battles with mag roader packs, e2 is battle with number 128, and ff is end script
        # commands are executed in groups of 5, 4 ride commands then a possible ride/battle/end command
        space = Reserve(0x2e2ef2, 0x2e2faf, "magitek factory mine cart commands")
        space.copy_from(0x2e2f24, 0x2e2f3c) # ride data and battle with mag roaders
        space.copy_from(0x2e2f4c, 0x2e2f5e) # ride data (using these groups of 5 because they are more interesting, fork in the road)
        space.copy_from(0x2e2f6e, 0x2e2f6e) # battle with mag roaders
        space.copy_from(0x2e2f7e, 0x2e2f91) # ride data and battle with mag roaders
        space.copy_from(0x2e2f92, 0x2e2fa5) # ride data and battle with Number 128
        space.copy_from(0x2e2fa6, 0x2e2faf) # ride data and end script

    def fixed_battles_mod(self):
        import instruction.asm as asm

        # force front attacks for fixed battles
        # luckily, value chosen for front attack is one shift away from overriding battle song bit so this fits in the original space
        front_attack = [
            asm.LDA(0x04, asm.IMM8),    # load 0b0100 into a register for front attack
            asm.STA(0x00011e3, asm.LNG),# store battle type in the same place invoke_battle_type does
            asm.ASL(),                  # set bit for overriding battle song (a = 0x08)
        ]

        space = Reserve(0x2e32b0, 0x2e32b6, "magitek factory set front attack for first fixed pack", asm.NOP())
        space.write(
            front_attack,
        )

        space = Reserve(0x2e32fe, 0x2e3304, "magitek factory set front attack for second fixed pack", asm.NOP())
        space.write(
            front_attack,
        )

    def number128_battle_mod(self):
        import instruction.asm as asm

        boss_pack_id = self.get_boss("Number 128")
        if boss_pack_id == self.enemies.packs.get_id("Phunbaba 3"):
            # TODO: if bababreath removes a character in this battle they are somehow back in the party after the mine cart ride
            #       if phunbaba3 ends up here, replace him with phunbaba4 which does not use bababreath
            boss_pack_id = self.enemies.packs.get_id("Phunbaba 4")
        boss_formation_id = self.enemies.packs.get_formations(boss_pack_id)[0]

        # load new boss formation with battle type and save some space doing it
        space = Reserve(0x2e3316, 0x2e332d, "magitek factory set number 128 formation", asm.NOP())
        space.write(
            asm.A16(),
            asm.LDA(boss_formation_id, asm.IMM16),
            asm.STA(0x0011e0, asm.LNG), # store formation at $0011e0 (low byte) and $0011e1 (high byte)
            asm.A8(),
            asm.LDA(0x04, asm.IMM8),    # load 0b0100 into a register for front attack
            asm.STA(0x0011e3, asm.LNG), # store battle type in the same place invoke_battle_type does
        )

        # don't overwrite the battle type just set with zero
        space = Reserve(0x2e3335, 0x2e3338, "magitek factory set number 128 high background byte", asm.NOP())

        # use original game over check function after mine cart ride, the custom one cannot be used here
        # refreshing objects or updating the party leader causes a hard lock at the end of the ride (never return from black screen)
        space = Reserve(0xc80ad, 0xc80b0, "magitek factory check game over after mine cart ride", field.NOP())
        space.write(
            field.Call(field.ORIGINAL_CHECK_GAME_OVER),
        )

    def character_mod(self, character):
        self.setzer_npc.sprite = character
        self.setzer_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xc819b, 0xc81c4, "magitek factory setzer dialog and party splits", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xc81da, 0xc8302, "magitek factory add char and kefka cranes scene", field.NOP())
        space.write(
            field.FadeOutScreen(),
            field.WaitForFade(),
            field.RecruitAndSelectParty(character),
            field.Branch(space.end_address + 1), # skip nops
        )

    def esper_mod(self, esper):
        self.setzer_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.setzer_npc.palette = self.characters.get_palette(self.setzer_npc.sprite)

        space = Reserve(0xc819b, 0xc8302, "magitek factory add char and kefka cranes scene", field.NOP())
        space.write(
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.FadeOutScreen(),
            field.WaitForFade(),
            field.Branch(space.end_address + 1), # skip nops
        )

    def crane_battle_mod(self):
        boss_pack_id = self.get_boss("Cranes")
        IS_CRANES = (boss_pack_id == self.enemies.packs.get_id("Cranes"))

        battle_type = field.BattleType.FRONT
        if IS_CRANES:
            battle_type = field.BattleType.PINCER

        if self.airship_position[0] == 0 and not IS_CRANES:
            battle_background = 48  # airship, right
        elif self.airship_position[0] == 0 and IS_CRANES:
            battle_background = 37  # airship, center
        elif self.airship_position[0] == 1 and not IS_CRANES:
            battle_background = 41  # airship WOR, right
        else:
            battle_background = 37  # airship WOR, center (does not exist!)

        space = Reserve(0xb40e5, 0xb40eb, "magitek factory invoke battle cranes", field.NOP())
        space.write(
            field.InvokeBattleType(boss_pack_id, battle_type, battle_background),
        )

    def after_cranes_mod(self):
        space = Reserve(0xb3ff1, 0xb40e0, "magitek factory scene before crane fight", field.NOP())
        space.write(
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.IncrementEventWord(event_word.CHECKS_COMPLETE), # objectives finished after battle
        )
        if self.airship_position[0] == 0x1:
            # Update world bit, if required
            space.write(field.SetEventBit(event_bit.IN_WOR))
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xc8303, 0xc8304, "after magitek factory do not delete vector townspeople", field.NOP())

        space = Reserve(0xc8319, 0xc831f, "after magitek factory do not call go to zozo scenes", field.Return())
        space.write(
            field.LoadMap(self.airship_position[0], direction.DOWN, default_music = True, x = self.airship_position[1],
                          y = self.airship_position[2], airship = True),
            vehicle.End(),
        )

    def guardian_mod(self):
        # guardian is made up of 9 npcs, remove them all
        for guardian_npc_id in range(0x20, 0x29):
            self.maps.remove_npc(0x0f2, 0x20)

        # delete the events that trigger guardian battle
        self.maps.delete_event(0x0f2, 30, 59)
        self.maps.delete_event(0x0f2, 31, 60)
        self.maps.delete_event(0x0f2, 32, 60)
        self.maps.delete_event(0x0f2, 33, 60)
        self.maps.delete_event(0x0f2, 34, 59)

    def mtek_1_mod(self):
        # Fix behavior of MTek room 1 if you re-enter after minecart ride
        # Remove event tile that sends you to Mtek-escape-Vector:
        self.maps.delete_event(0x106, 28, 9)

        # Modify entrance event:
        space = Reserve(0xc72dc, 0xc7315, "after MTek minecart do not change MTek1", field.NOP())

        # Modify pipe events to remove check for RODE_MINE_CART
        space = Reserve(0xc7735, 0xc773a, "after MTek minecart do not change MTek1 pipeL1", field.NOP())
        space = Reserve(0xc7753, 0xc7758, "after MTek minecart do not change MTek1 pipeL2", field.NOP())
        space = Reserve(0xc7771, 0xc7776, "after MTek minecart do not change MTek1 pipeL3", field.NOP())
        space = Reserve(0xc77b0, 0xc77b5, "after MTek minecart do not change MTek1 pipeR1", field.NOP())
        space = Reserve(0xc77ce, 0xc77d3, "after MTek minecart do not change MTek1 pipeR2", field.NOP())
        space = Reserve(0xc77ec, 0xc77f1, "after MTek minecart do not change MTek1 pipeR3", field.NOP())
        space = Reserve(0xc781b, 0xc7820, "after MTek minecart do not change MTek1 pipeR4", field.NOP())

    def map_shuffle_mod(self):
        # (1a) Change the entry event to load the switchyard location
        event_id = 1505  # ID of Vector event entrance

        # We don't use Burning Vector so we can just write over the event bit check
        space = Reserve(0xa5ecf, 0xa5edb, 'Vector WOB entrance', field.NOP())
        space.write(GoToSwitchyard(event_id, map='world'))
        # (1b) Add the switchyard event tile that handles entry to Vector
        src = [
            field.LoadMap(0x0f2, direction=direction.UP, x=32, y=61, default_music=True, fade_in=True),
            field.Return()
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)


    # def reride_minecart_mod(src):
    #     # Special event for outro of minecart ride: return to Vector if cranes have been defeated.
    #     # C0    If ($1E80($06B) is set), branch to $(new event) that sends you to Vector map instead
    #     # C0    If ($1E80($069) is set), branch to $(new event) that sends you to MTek3 Vector map without animation
    #     #from memory.space import Write, Bank
    #     #from event.event import direction
    #
    #     # Hook in at CC/80B5.  Need 4 bytes for field.Call().  LoadMap at CC/80B9.
    #     patch_magitek_minecart = (
    #         field.SetEventBit(0x6a3),   # CC/80B5
    #         field.ClearEventBit(0x6ae), # CC/80B7
    #         field.BranchIfEventBitSet(event_bit.DEFEATED_CRANES, 'GO_TO_VECTOR'),
    #         field.BranchIfEventBitSet(event_bit.RODE_MINE_CART_MAGITEK_FACTORY, 'GO_TO_MTEK3_VECTOR'),
    #         field.Return(),
    #         'GO_TO_VECTOR',
    #         field.LoadMap(0xf2, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
    #         field.FadeInScreen(),
    #         field.Return(),
    #         'GO_TO_MTEK3_VECTOR',
    #         field.LoadMap(0xf0, direction.LEFT, default_music=True, x=62, y=13, entrance_event=True),
    #         field.FadeInScreen(),
    #         field.Return()
    #     )
    #     space = Write(Bank.CC, patch_magitek_minecart, 'Patch for re-rideable minecart')
    #
    #     hook = Reserve(0xc80b5, 0xc80b8, 'Hook for Minecart Exit Patch')
    #     hook_code = (
    #         field.Call(space.start_address)
    #     )
    #     hook.write(hook_code)
