from event.event import *

class SealedGate(Event):
    def name(self):
        return "Sealed Gate"

    def character_gate(self):
        return self.characters.TERRA

    def init_rewards(self):
        if self.args.no_free_characters_espers:
            self.reward = self.add_reward(RewardType.ITEM)
        else:
            self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(npc_bit.GUARD_BLOCKING_SEALED_GATE_IMPERIAL_BASE),
            field.SetEventBit(npc_bit.KEFKA_SEALED_GATE),
        )

    def mod(self):
        # arbitrarily using kefka npc for char/esper/item
        self.kefka_npc_id = 0x16
        self.kefka_npc = self.maps.get_npc(0x187, self.kefka_npc_id)
        if self.args.ruination_mode:
            self.kefka_npc.y = 30
        else:
            self.kefka_npc.x = 8
            self.kefka_npc.y = 10

        self.world_map_mod()
        self.exit_shortcut_mod()
        self.ninja_mod()

        self.lightning_strike = 0xb3890

        if self.args.ruination_mode:
            # We will use this as an entry point to KT.  Don't set up the reward.
            self.ruination_mod()
        else:
            if self.reward.type == RewardType.CHARACTER:
                self.character_mod(self.reward.id)
            elif self.reward.type == RewardType.ESPER:
                self.esper_mod(self.reward.id)
            elif self.reward.type == RewardType.ITEM:
                self.item_mod(self.reward.id)

            self.log_reward(self.reward)

    def world_map_mod(self):
        import instruction.asm as asm

        # calls to remove from minimap
        space = Reserve(0x2e85dc, 0x2e85de, "sealed gate call remove from minimap", asm.NOP())
        space = Reserve(0x2e886f, 0x2e8871, "sealed gate call remove from minimap", asm.NOP())
        space = Reserve(0x2e8b35, 0x2e8b37, "sealed gate call remove from minimap", asm.NOP())

        # remove from minimap function, leave a rts statement just in case there is another call somewhere
        # otherwise, this is now free space
        space = Reserve(0x2e9af1, 0x2e9b13, "sealed gate remove from minimap function", asm.NOP())
        space.write(0x60)    # rts

        # sealed gate is removed from world map depending on the floating continent event bit
        # change the event bit that is checked to always clear so sealed gate is always available
        self.maps.world_map_event_modifications.set_sealed_gate_event_bit(event_bit.ALWAYS_CLEAR)
        # because these modified map chunks are never used that more ee bank free space available

    def gate_scene_mod(self, char_esper_item_instructions):
        SET_PARTY_LAYER2 = 0xb3980
        SET_PARTY_LAYER0 = 0xb3995

        src = [
            field.Call(SET_PARTY_LAYER2),

            # add small scene showing gate and having npc walk toward player
            field.HoldScreen(),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Move(direction.UP, 5),
            ),
            field.EntityAct(field_entity.CAMERA, False,
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Move(direction.UP, 4),
            ),
            field.Call(self.lightning_strike),
            field.WaitForEntityAct(field_entity.CAMERA),
            field.Pause(2.0),
            field.Call(self.lightning_strike),
            field.Pause(2.0),
            field.EntityAct(self.kefka_npc_id, False,
                field_entity.SetSpriteLayer(2),
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Turn(direction.DOWN),
                field_entity.Move(direction.DOWN, 3),
            ),
            field.Pause(1.0),
            field.WaitForEntityAct(self.kefka_npc_id),
            field.Pause(0.5),

            field.ClearEventBit(npc_bit.KEFKA_SEALED_GATE),
            field.SetEventBit(npc_bit.BLOCK_SEALED_GATE),
            # event bit 0x79 also affects vector, don't bother setting it

            char_esper_item_instructions,

            # must set party layering after possible new char may have joined
            field.Call(SET_PARTY_LAYER0),

            field.FreeScreen(),
            field.LoadMap(0x180, direction.DOWN, default_music = True,
                          x = 10, y = 28, fade_in = True, entrance_event = True),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "sealed gate end/reward")
        end_event = space.start_address

        space = Reserve(0xb39d8, 0xb39dd, "sealed gate end/reward branch", field.NOP())
        space.write(
            field.Branch(end_event),
        )

        src = [
            Read(0xb39be, 0xb39c8), # copy original entrance event code

            field.CreateEntity(self.kefka_npc_id),
            field.ShowEntity(self.kefka_npc_id),
            field.RefreshEntities(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "sealed gate entrance event")
        entrance_event = space.start_address

        space = Reserve(0xb39be, 0xb39c8, "sealed gate call entrance event", field.NOP())
        space.write(
            field.Call(entrance_event),
            field.Return(),
        )

    def character_mod(self, character):
        self.kefka_npc.sprite = character
        self.kefka_npc.palette = self.characters.get_palette(character)

        self.gate_scene_mod([
            field.FadeOutScreen(),
            field.WaitForFade(),
            field.RecruitAndSelectParty(character),
        ])

    def esper_item_mod(self, esper_item_instructions):
        self.kefka_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.kefka_npc.palette = self.characters.get_palette(self.kefka_npc.sprite)

        self.gate_scene_mod([
            esper_item_instructions,
            field.FadeOutScreen(4),
            field.Call(self.lightning_strike),
            field.WaitForFade(),
        ])

    def esper_mod(self, esper):
        self.esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def exit_shortcut_mod(self):
        # change event bit which triggers shortcut exit since 0x79 is not set above
        space = Reserve(0xb2eb1, 0xb2eb6, "sealed gate exit shortcut event bit condition", field.NOP())
        space.write(
            field.ReturnIfEventBitClear(npc_bit.BLOCK_SEALED_GATE),
        )

    def ninja_mod(self):
        src = [
            field.SetEventBit(event_bit.DEFEATED_NINJA_CAVE_TO_SEALED_GATE),
            field.CheckObjectives(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "sealed gate ninja set event bit, check objectives")
        check_objectives = space.start_address

        space = Reserve(0xb30bb, 0xb30be, "sealed gate ninja i thought i had the monopoly", field.NOP())
        space.write(
            field.Call(check_objectives),
        )

    def ruination_mod(self):
        SET_PARTY_LAYER2 = 0xb3980
        SET_PARTY_LAYER0 = 0xb3995

        map_id = 0x187

        # Sealed Gate event edits:
        # Move event tile up one square, to allow party to retreat
        event_in = self.maps.get_event(map_id, 8, 21)
        event_in.y -= 1
        space = Reserve(0xb39e6, 0xb39e6, "sealed gate event moved up 1 tile", field_entity.Move(direction.UP, 4))

        # Skip reform party & enable party to move thru things
        space = Reserve(0xb39e8, 0xb39f8, "sealed gate skip split party", field.NOP())
        # Skip party split animation
        space = Reserve(0xb39fa, 0xb3a12, "sealed gate edits 2", field.NOP())
        # Skip dialog "This is the sealed gate..."
        space = Reserve(0xb3a23, 0xb3a25, "sealed gate edits 3", field.NOP())
        # Skip party-dependent dialog options
        space = Reserve(0xb3a32, 0xb3a35, "sealed gate edits 3a", field.NOP())
        # Change terra movement to party movement
        space = Reserve(0xb3a3d, 0xb3a3d, "sealed gate change animation 1", field.NOP())
        space.write(field_entity.PARTY0)
        # Skip split party move & dialog "Terra..."
        space = Reserve(0xb3a42, 0xb3a56, "sealed gate edits 4", field.NOP())
        # Change terra movement to party movement
        space = Reserve(0xb3a63, 0xb3a63, "sealed gate change animation 2", field.NOP())
        space.write(field_entity.PARTY0)
        # Skip split party animation
        space = Reserve(0xb3a94, 0xb3a9f, "sealed gate edits 5", field.NOP())
        # Change terra movement to party movement
        space = Reserve(0xb3aa0, 0xb3aa0, "sealed gate change animation 3", field.NOP())
        space.write(field_entity.PARTY0)
        # Skip dialog "Terra!  ... the gate... quickly!"
        space = Reserve(0xb3aa4, 0xb3aac, "sealed gate edits 5", field.NOP())
        # Change terra movement to party movement
        space = Reserve(0xb3ab1, 0xb3ab1, "sealed gate change animation 4", field.NOP())
        space.write(field_entity.PARTY0)
        # Skip replace a party member with Kefka
        space = Reserve(0xb3aba, 0xb3adb, "sealed gate edits 6", field.NOP())
        # Modify invoked battle
        space = Reserve(0xb3adc, 0xb3ae2, "sealed gate battle mod", field.NOP())

        boss_pack_id = self.get_boss("Kefka (Narshe)")
        space.write(field.InvokeBattleType(boss_pack_id, field.BattleType.BACK))

        # Skip unreplace a party member with Kefka
        space = Reserve(0xb3ae3, 0xb3ae5, "sealed gate edits 7", field.NOP())
        space.write(field.SetEventBit(0x079))  # stop Sealed Gate event from repeating

        # Skip replace character positions after battle
        space = Reserve(0xb3aea, 0xb3afd, "sealed gate edits 8", field.NOP())
        space.write([
            field.HideEntity(0x17),
            field.HideEntity(0x18),
            #field.HideEntity(0x16),
            field.RefreshEntities(),
        ])
        # Skip move characters after battle
        space = Reserve(0xb3b06, 0xb3b11, "sealed gate edits 9", field.NOP())
        # Change terra movement to party movement
        space = Reserve(0xb3b12, 0xb3b12, "sealed gate change animation 5", field.NOP())
        space.write(field_entity.PARTY0)
        # Skip "Espers... please heed my call...""
        space = Reserve(0xb3b16, 0xb3b1d, "sealed gate edits 10", field.NOP())
        # Skip character animations
        space = Reserve(0xb3b4d, 0xb3b5a, "sealed gate edits 11", field.NOP())
        # End before second battle
        space = Reserve(0xb3b66, 0xb3b76, "sealed gate edits 11", field.NOP())
        space.write([
            field.StopScreenShake(),
            field.FreeScreen(),
            field.Return()
        ])

        # Add to entrance event:  doors open if already did fight
        # Change timing of screen shake to correspond with doors
        # Move event tile back down; show "this is the sealed gate" text.  Add dialog option to open it?
        # Recenter screen after doors open.
        # Add exit tile at sealed gate to KT

        # src = [
        #     Read(0xb39be, 0xb39c8),  # copy original entrance event code
        #
        #     field.CreateEntity(self.kefka_npc_id),
        #     field.ShowEntity(self.kefka_npc_id),
        #     field.RefreshEntities(),
        #     field.Return(),
        # ]
        # space = Write(Bank.CB, src, "sealed gate entrance event")
        # entrance_event = space.start_address
        #
        # space = Reserve(0xb39be, 0xb39c8, "sealed gate call entrance event", field.NOP())
        # space.write(
        #     field.Call(entrance_event),
        #     field.Return(),
        # )