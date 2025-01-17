from event.event import *

class DomaWOR(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.DOOR_RANDOMIZE = (args.door_randomize_cyans_dream
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)

    def name(self):
        return "Doma WOR"

    def character_gate(self):
        return self.characters.CYAN

    def init_rewards(self):
        self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)
        self.reward2 = self.add_reward(RewardType.ESPER | RewardType.ITEM)
        self.reward3 = self.add_reward(RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.cyan_phantom_train_npc_id = 0x10
        self.cyan_phantom_train_npc = self.maps.get_npc(0x08f, self.cyan_phantom_train_npc_id)
        self.cyan_mines_npc_id = 0x11
        self.cyan_mines_npc = self.maps.get_npc(0x140, self.cyan_mines_npc_id)
        self.cyan_outside_mines_npc_id = 0x10
        self.cyan_outside_mines_npc = self.maps.get_npc(0x13f, self.cyan_outside_mines_npc_id)
        self.cyan_fishing_npc_id = 0x11
        self.cyan_fishing_npc = self.maps.get_npc(0x07d, self.cyan_fishing_npc_id)
        self.cyan_training_npc_id = 0x13
        self.cyan_training_npc = self.maps.get_npc(0x07d, self.cyan_training_npc_id)
        self.cyan_bedroom_npc_id = 0x14
        self.cyan_bedroom_npc = self.maps.get_npc(0x07e, self.cyan_bedroom_npc_id)
        self.cyan_throne_room_npc_id = 0x17
        self.cyan_throne_room_npc = self.maps.get_npc(0x07e, self.cyan_throne_room_npc_id)

        self.sleep_mod()
        self.stooges_mod()
        self.stooges_battle_mod()

        if self.reward3.type == RewardType.ESPER:
            self.stooges_esper_mod(self.reward3.id)
        elif self.reward3.type == RewardType.ITEM:
            self.stooges_item_mod(self.reward3.id)

        self.mines_mod()
        self.doma_mod()
        self.wrexsoul_battle_mod()

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

        if self.reward1.type == RewardType.CHARACTER:
            self.cyan_character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.cyan_esper_mod(self.reward1.id)
        self.finish_dream_awaken_mod()

        if self.reward2.type == RewardType.ESPER:
            self.throne_esper_mod(self.reward2.id)
        elif self.reward2.type == RewardType.ITEM:
            self.throne_item_mod(self.reward2.id)

        self.log_reward(self.reward3)
        self.log_reward(self.reward1)
        self.log_reward(self.reward2)

    def sleep_mod(self):
        NORMAL_SLEEP_ADDR = 0xb8294

        space = Reserve(0xb82b1, 0xb82c6, "doma wor check if event already done, in wor, have cyan and 4 party members", field.NOP())
        space.write(
            field.BranchIfEventBitClear(event_bit.IN_WOR, NORMAL_SLEEP_ADDR),
        )
        if not self.DOOR_RANDOMIZE:
            # Make the dream repeatable
            space.write(
                field.BranchIfEventBitSet(event_bit.FINISHED_DOMA_WOR, NORMAL_SLEEP_ADDR),
            )
        if self.args.character_gating:
            space.write(
                field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), NORMAL_SLEEP_ADDR),
            )

        space = Reserve(0xb82d2, 0xb82d6, "doma wor make cyan party leader", field.NOP())

        space = Reserve(0xb82dd, 0xb82dd, "doma wor put cyan (party leader) in bottom left bed")
        space.write(field_entity.PARTY0)

        stooges_introduction_scene_end = 0xb8466
        space = Reserve(0xb82f5, 0xb8300, "doma wor larry, curly, moe introduce themselves scene", field.NOP())
        space.write(
            field.Branch(stooges_introduction_scene_end + 1),
        )
        Free(space.end_address + 1, stooges_introduction_scene_end)

        space = Reserve(0xb8469, 0xb8470, "doma wor party leaps into cyan dream", field.NOP())

        space = Reserve(0xb847b, 0xb8482, "doma wor remove first 2 characters in party", field.NOP())
        space.write(
            field.Call(field.ENABLE_COLLISIONS_FOR_PARTY_MEMBERS),
            field.Call(field.HIDE_PARTY_MEMBERS_EXCEPT_LEADER),
        )

    def stooges_mod(self):
        space = Reserve(0xb8b9d, 0xb8ba0, "doma wor back off", field.NOP())

        space = Reserve(0xb8baa, 0xb8bb7, "doma wor fight stooges if 2 party members and found 2 stooges", field.NOP())
        space.write(
            field.ReturnIfAll([event_bit.FOUND_DREAM_STOOGE1, True, event_bit.FOUND_DREAM_STOOGE2, True]),
        )

        space = Reserve(0xb8c1f, 0xb8c21, "doma wor we're the 3 stooges", field.NOP())
        space = Reserve(0xb8c39, 0xb8c3b, "doma wor let's rumble", field.NOP())

    def stooges_battle_mod(self):
        boss_pack_id = self.get_boss("Stooges")

        space = Reserve(0xb8c3c, 0xb8c42, "doma wor invoke battle stooges", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def stooges_esper_item_mod(self, esper_item_instructions):
        src = [
            Read(0xb8c4f, 0xb8c55), # hide stooges and fade in screen
            esper_item_instructions,
            field.SetEventBit(event_bit.DEFEATED_STOOGES),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "doma wor stooges receive reward")
        receive_reward = space.start_address

        space = Reserve(0xb8c4f, 0xb8c55, "doma wor clear event bits, hide stooges, fade in screen", field.NOP())
        space.write(
            field.Call(receive_reward),
        )

    def stooges_esper_mod(self, esper):
        self.stooges_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def stooges_item_mod(self, item):
        self.stooges_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def mines_mod(self):
        # change the code to give all 4 (instead of just 3) party members magitek armor status in battle
        # NOTE: magitek armor uses a palette slot normally reserved for a party member, so
        #       a party of 4 with magitek was never intended and has a graphical bug
        space = Reserve(0xb93da, 0xb93e5, "toggle magitek on for party", field.NOP())
        space.write(
            field.Call(field.TOGGLE_PARTY_MAGITEK),
        )
        space = Reserve(0xb9503, 0xb950e, "toggle magitek off for party", field.NOP())
        space.write(
            field.Call(field.TOGGLE_PARTY_MAGITEK),
        )

    def doma_mod(self):
        space = Reserve(0xb9542, 0xb95de, "doma wor elayne and owain ask party to save cyan", field.NOP())
        space = Reserve(0xb95ed, 0xb95ef, "doma wor please... help cyan...", field.NOP())
        space = Reserve(0xb97de, 0xb97e0, "doma wor you must be wrexsoul", field.NOP())
        space = Reserve(0xb97e7, 0xb97e9, "doma wor you're too late", field.NOP())
        space = Reserve(0xb97fd, 0xb9801, "doma wor create cyan and add to party after wrexsoul", field.NOP())
        space = Reserve(0xb9806, 0xb9812, "doma wor change party members after wrexsoul", field.NOP())

        space = Reserve(0xb9833, 0xb9950, "doma wor elayne and owain scene after wrexsoul", field.NOP())
        space.write(
            field.EntityAct(field_entity.PARTY0, False,
                field_entity.Turn(direction.UP),
            ),
            field.Branch(space.end_address + 1), # skip nops
        )

        if(self.args.flashes_remove_most or self.args.flashes_remove_worst):
            space = Reserve(0xb9952, 0xb9953, "doma wor sword appears flash 1", field.FlashScreen(field.Flash.NONE))
            space = Reserve(0xb9975, 0xb9976, "doma wor sword appears flashes", field.FlashScreen(field.Flash.NONE))
            space = Reserve(0xb99a9, 0xb99aa, "doma wor sword appears flash 3", field.FlashScreen(field.Flash.NONE))

        space = Reserve(0xb997d, 0xb9984, "doma wor cyan kneeling", field.NOP())
        space = Reserve(0xb99df, 0xb99e0, "doma wor pause before loading room slept in", field.NOP())
        if self.DOOR_RANDOMIZE:
            # move the "Set Event Bit COMPLETED_DOMA_WOR (0x0DA)" to before the load map @ CB/99E1
            space.write([field.SetEventBit(event_bit.FINISHED_DOMA_WOR)])
            space = Reserve(0xb99e7, 0xb99e8, "doma wor moved set event bit for completed", field.NOP())

        space = Reserve(0xb99f6, 0xb99fa, "doma wor animate party knocked out", field.NOP())

        space = Reserve(0xb99fe, 0xb9a23, "doma wor change party members after elayne and owain scene", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xb9a27, 0xb9a44, "doma wor cyan walks down and soul cleared", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xb9a51, 0xb9a6c, "doma wor party gathers up", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

    def wrexsoul_battle_mod(self):
        boss_pack_id = self.get_boss("Wrexsoul")

        space = Reserve(0xb97ea, 0xb97ec, "doma wor invoke battle wrexsoul", field.NOP())
        space.write(
            # game over call is preceded by song change so don't overwrite it here
            # (in case they actually did that for a reason)
            field.InvokeBattle(boss_pack_id, check_game_over = False),
        )

    def cyan_character_mod(self, character):
        self.cyan_phantom_train_npc.sprite = character
        self.cyan_phantom_train_npc.palette = self.characters.get_palette(character)
        self.cyan_mines_npc.sprite = character
        self.cyan_mines_npc.palette = self.characters.get_palette(character)
        self.cyan_outside_mines_npc.sprite = character
        self.cyan_outside_mines_npc.palette = self.characters.get_palette(character)
        self.cyan_fishing_npc.sprite = character
        self.cyan_fishing_npc.palette = self.characters.get_palette(character)
        self.cyan_training_npc.sprite = character
        self.cyan_training_npc.palette = self.characters.get_palette(character)
        self.cyan_bedroom_npc.sprite = character
        self.cyan_bedroom_npc.palette = self.characters.get_palette(character)
        self.cyan_throne_room_npc.sprite = character
        self.cyan_throne_room_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xb9818, 0xb982f, "doma wor split up party after wrexsoul battle", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
            field.HideEntity(character),
            field.UpdatePartyLeader(),
        )

        space = Reserve(0xb99b4, 0xb99d4, "doma wor cyan touches sword", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

    def random_cyan_npc_mod(self):
        sprite = self.characters.get_random_esper_item_sprite()
        palette = self.characters.get_palette(sprite)

        self.cyan_phantom_train_npc.sprite = sprite
        self.cyan_phantom_train_npc.palette = palette
        self.cyan_mines_npc.sprite = sprite
        self.cyan_mines_npc.palette = palette
        self.cyan_outside_mines_npc.sprite = sprite
        self.cyan_outside_mines_npc.palette = palette
        self.cyan_fishing_npc.sprite = sprite
        self.cyan_fishing_npc.palette = palette
        self.cyan_training_npc.sprite = sprite
        self.cyan_training_npc.palette = palette
        self.cyan_bedroom_npc.sprite = sprite
        self.cyan_bedroom_npc.palette = palette
        self.cyan_throne_room_npc.sprite = sprite
        self.cyan_throne_room_npc.palette = palette

    def cyan_esper_mod(self, esper):
        self.random_cyan_npc_mod()

        space = Reserve(0xb9818, 0xb982f, "doma wor split up party after wrexsoul battle", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xb99b4, 0xb99d4, "doma wor cyan touches sword", field.NOP())
        space.write(
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.Branch(space.end_address + 1), # skip nops
        )

    def finish_dream_awaken_mod(self):
        if(self.args.flashes_remove_most or self.args.flashes_remove_worst):
            space = Reserve(0xb9a47, 0xb9a48, "doma wor peak swordmanship flash", field.FlashScreen(field.Flash.NONE))

        src = [
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "doma wor finish dream")
        finish_dream_awaken = space.start_address

        space = Reserve(0xb9a49, 0xb9a4c, "doma wor peak swordsmanship dialog", field.NOP())
        space.write(
            field.Call(finish_dream_awaken),
        )

        space = Reserve(0xb9a6f, 0xb9a6f, "doma wor learn all swdtechs", field.NOP())

    def throne_esper_item_mod(self, reward_instructions):
        src = [
            reward_instructions,
            field.SetEventBit(event_bit.GOT_ALEXANDR),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "doma wor throne receive reward")
        receive_reward = space.start_address

        space = Reserve(0xb9a7a, 0xb9a7d, "doma wor throne call receive reward", field.NOP())
        space.write(
            field.Call(receive_reward),
        )

        space = Reserve(0xb9a89, 0xb9a8b, "doma wor receive alexandr dialog", field.NOP())

    def throne_esper_mod(self, esper):
        self.throne_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def throne_item_mod(self, item):
        # the magicite is represented by 2 npcs for some reason
        magicite_throne_room_npc_id = 0x17
        magicite_throne_room_npc = self.maps.get_npc(0x7b, magicite_throne_room_npc_id)
        magicite_throne_room_npc.sprite = 106
        magicite_throne_room_npc.palette = 6
        magicite_throne_room_npc.split_sprite = 1
        magicite_throne_room_npc.direction = direction.DOWN

        magicite_throne_room_npc_id = 0x18
        magicite_throne_room_npc = self.maps.get_npc(0x7b, magicite_throne_room_npc_id)
        magicite_throne_room_npc.sprite = 106
        magicite_throne_room_npc.palette = 6
        magicite_throne_room_npc.split_sprite = 1
        magicite_throne_room_npc.direction = direction.DOWN

        self.throne_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def door_rando_mod(self):
        # Delete vanilla shared map exit event tile in phantom train car
        self.maps.delete_event(0x99, 8, 12)

        # (2) Need to add NPCs to block exits while the animation is playing.
        from data.npc import CreateInvisibleBlockNPCs

        # (2a) TRAIN GHOST CHASE
        # Block door entry with invisible NPCs while a ghost chases Cyan
        map_id = 0x08f
        door_locations = [[65, 8], [75, 8], [82, 8], [91, 8]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.cyan_phantom_train_npc)

        patch_in = [0xb9347, 0xb934a]  # create object 0x10, create object 0x11
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 1")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 1", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb93a6, 0xb93a9]  # clear event bit, set event bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 1")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 1", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Randomize Train Chest code?
        # - Actually randomize code shown/read in Cars 2/3
        # - Lock exit to Car 3 with a key in Car 2.


        # (2b) MAGITEK MINE CHASE
        # Block door entry with invisible NPCs while soldiers chase Cyan
        map_id = 0x140
        door_locations = [[6, 22]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.cyan_phantom_train_npc)

        patch_in = [0xb9433, 0xb9436]  # call subroutine $CB6A4C (colorize)
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 2")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 2", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb949c, 0xb949f]  # disable passthru 0x13, 0x14
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 2")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 2", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Only play the cave chase animation one time:
        # use custom event_bit.SAW_DREAM_CAVE_CHASE = 0x163  # DR custom
        src = [
            field.BranchIfEventBitSet(event_bit.SAW_DREAM_CAVE_CHASE, "SKIP_CHASE_SCENE"),
            field.SetEventBit(event_bit.SAW_DREAM_CAVE_CHASE),
            # CB/93F8: F4    Play sound effect 152
            # CB/93FA: 31    Begin action queue for character $31 (Party Character 0), 4 bytes long (Wait until complete)
            # CB/93FC: CF        Turn vehicle/entity left
            # CB/93FD: E0        Pause for 4 * 6 (24) frames
            # CB/93FF: FF        End queue
            field.PlaySoundEffect(0x98),  # Magitek walk sound effect
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Turn(direction.LEFT),
                            field_entity.Pause(6)),
            field.Branch(0xb9402),
            "SKIP_CHASE_SCENE",
            field.FreeScreen(),
            field.Return()
        ]
        show_dream_chase = Write(Bank.CB, src, "Show dream chase once")
        space = Reserve(0xb93f8, 0xb93ff, "Cyan Dream play chase scene only once", field.NOP())
        space.write([field.Branch(show_dream_chase.start_address)])


        # (3): BRIDGE ESCAPE
        # Block door entry with invisible NPC while Cyan walks across bridge
        map_id = 0x13f
        door_locations = [[25, 24], [25, 25]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.cyan_phantom_train_npc)

        patch_in = [0xb94bb, 0xb94be]  # call subroutine $CB6A4C (colorize)
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 3")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 3", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb94e2, 0xb94e5]  # set event bit, disable passthru 0x10
        src = [
            Read(patch_out[0], patch_out[1]),
            field.SetEventBit(event_bit.SAW_DREAM_BRIDGE_ESCAPE)   # see below
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 3")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 3", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Only play the bridge escape animation one time:
        # use custom event_bit.SAW_DREAM_BRIDGE_ESCAPE = 0x164  # DR custom
        src = [
            field.DeleteEntity(0x10),
            field.HideEntity(0x10),
            field.DeleteEntity(0x11),
            field.HideEntity(0x11),
            field.RefreshEntities(),
            field.Return()
        ]
        hide_npc_script = Write(Bank.CB, src, "Delete NPCs in bridge room")
        space = Reserve(0xb94b2, 0xb94b7, "Check for dream bridge escape", field.NOP())
        space.write([field.BranchIfEventBitSet(event_bit.SAW_DREAM_BRIDGE_ESCAPE, hide_npc_script.start_address)])
        #space = Reserve(0xb94e2, 0xb94e3, "Set dream bridge escape bit", field.NOP())
        #space.write([field.SetEventBit(event_bit.SAW_DREAM_BRIDGE_ESCAPE)])

        # (4): SCENES IN DOMA CASTLE
        # Block door entry with invisible NPC while Cyan walks across bridge
        map_id = 0x07E
        door_locations = [[28, 37]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.cyan_phantom_train_npc)

        patch_in = [0xb96ca, 0xb96cd]  # set event bit, create 0x14
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 4")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 4", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb979c, 0xb979f]  # disable passthru 0x10,  set event bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 4")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 4", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Block door entry with invisible NPC while Cyan does stuff outside
        map_id = 0x07D
        door_locations = [[28, 31]]
        npc_id = CreateInvisibleBlockNPCs(self.maps, map_id, door_locations, self.cyan_phantom_train_npc)

        patch_in = [0xb964a, 0xb964d]  # set event bit, create 0x12
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 5")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 5", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb96be, 0xb96c1]  #  clear bit, set bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 5")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 5", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Same NPC for event 6 on the other side
        patch_in = [0xb95f9, 0xb95fc]  # set event bit, create 0x10
        src = [
            Read(patch_in[0], patch_in[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.CreateEntity(npc_id[i]),
                field.ShowEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_create = Write(Bank.CB, src, "create NPCs dream 6")
        space = Reserve(patch_in[0], patch_in[1], "patch create NPCs dream 6", field.NOP())
        space.write(field.Call(space_create.start_address))

        patch_out = [0xb963e, 0xb9641]  # set bit, clear bit
        src = [
            Read(patch_out[0], patch_out[1]),
        ]
        for i in range(len(npc_id)):
            src += [
                field.DeleteEntity(npc_id[i]),
                field.HideEntity(npc_id[i]),
            ]
        src += [field.Return()]
        space_delete = Write(Bank.CB, src, "delete NPCs dream 6")
        space = Reserve(patch_out[0], patch_out[1], "patch delete npcs dream 6", field.NOP())
        space.write(field.Call(space_delete.start_address))

        # Make the 2f exit to balcony (id = 441) accessible in Doma Dream
        balcony_exit = self.maps.get_exit(441)
        balcony_exit.x -= 1  # move to [17, 39]
        balcony_entrance = self.maps.get_exit(437)
        balcony_entrance.dest_x -= 1  # Move to [17, 38] to match

        # Place an event tile on [0x07e, 25, 17] that deletes Wrexsoul & Cyan NPCs if boss is defeated
        boss_npc_id = 0x18
        cyan_npc_id = 0x17
        magicite_npc_id = 0x24
        src = [
            field.ReturnIfEventBitClear(event_bit.FINISHED_DOMA_WOR),
            field.ReturnIfEventBitSet(0x1b5),
            field.DeleteEntity(boss_npc_id),
            field.HideEntity(boss_npc_id),
            field.DeleteEntity(cyan_npc_id),
            field.HideEntity(cyan_npc_id),
            field.DeleteEntity(magicite_npc_id),
            field.HideEntity(magicite_npc_id),
            field.SetEventBit(0x1b5),
            field.Return()
        ]
        space = Write(Bank.CB, src, "Cyan Dream Delete NPCs if Boss Cleared")
        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 25
        new_event.y = 17
        new_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(0x07e, new_event)

        # Skip Wrexsoul battle, if already fought
        src = [
            field.BranchIfEventBitClear(event_bit.FINISHED_DOMA_WOR, 0xb97D6), # branch to Wrexsoul battle
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.UP, 6),
                            field_entity.Pause(4),
                            field_entity.Turn(direction.RIGHT),
                            field_entity.Pause(2),
                            field_entity.Turn(direction.DOWN),
                            field_entity.Pause(6),
                            field_entity.AnimateCloseEyes(),
                            field_entity.Pause(6),
                            field_entity.AnimateStandingHeadDown(),
                            field_entity.Pause(8),
            ),
            field.Branch(0xb99D4),  # branch back to fade screen, load map etc.
        ]
        space = Write(Bank.CB, src, "Skip Wrexsoul fight if already done")
        # Update event tile
        boss_event = self.maps.get_event(0x07E, 25, 11)
        boss_event.event_address = space.start_address - EVENT_CODE_START

