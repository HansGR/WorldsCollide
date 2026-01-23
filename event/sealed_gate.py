from event.event import *

SET_PARTY_LAYER2 = 0xb3980
SET_PARTY_LAYER0 = 0xb3995

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
            pass
            #self.kefka_npc.y = 30
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
        map_id = 0x187

        # Set Kefka to not be shown at the beginning
        self.kefka_npc.event_bit = npc_bit.event_bit(npc_bit.ALWAYS_OFF)
        self.kefka_npc.event_byte = npc_bit.event_byte(npc_bit.ALWAYS_OFF)

        # Move event tile up one square, to allow party to retreat
        event_in = self.maps.get_event(map_id, 8, 21)
        event_in.y -= 1

        # Get boss pack for the battle
        boss_pack_id = self.get_boss("Ultros/Chupon")

        # Write complete new sealed gate event using Python field functions
        # This replaces the complex original event with surgical patches
        src = [
            # Check if event already completed - if so, return immediately
            field.ReturnIfEventBitSet(event_bit.SEALED_GATE_OPENED),

            # Play wind song and set party to layer 2 (above background)
            field.StartSongAtVolume(0x39, 0x78),
            field.Call(self.lightning_strike),
            field.Call(SET_PARTY_LAYER2),

            # Create the gate guardian NPCs (espers behind gate)
            field.CreateEntity(0x16),
            field.CreateEntity(0x17),
            field.CreateEntity(0x18),
            field.RefreshEntities(),

            # Party walks up toward the gate
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.UP, 4)),

            # Hold screen and pause before panning up
            field.HoldScreen(),
            field.Pause(1.0),

            # Camera pans up to show the gate
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.UP, 7)),

            # Pause to let player see the gate
            field.Pause(1.5),

            # Increase song volume and lightning strike
            field.FadeSongVolume(100, 0x96),
            field.Call(0xb38ac),  # lightning strike variant (right side)

            # Pause to build tension
            field.Pause(2.0),

            # Camera pans back down
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.DOWN, 4)),

            # Lightning strike and pause
            field.Call(self.lightning_strike),
            field.Pause(1.5),

            # Increase song volume more
            field.FadeSongVolume(50, 0xc8),
            field.Pause(1.5),

            # Free screen briefly for party movement
            field.FreeScreen(),

            # Party approaches the gate
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.UP, 5)),

            # Increase to full volume and lightning
            field.Pause(0.5),
            field.FadeSongVolume(100, 0xff),
            field.Call(self.lightning_strike),
            field.Pause(0.5),

            # Show the esper NPCs
            field.ShowEntity(0x16),
            field.ShowEntity(0x17),
            field.ShowEntity(0x18),

            # Set NPCs to layer 2
            field.EntityAct(0x16, True,
                            field_entity.SetSpriteLayer(2)),
            field.EntityAct(0x17, True,
                            field_entity.SetSpriteLayer(2)),
            field.EntityAct(0x18, True,
                            field_entity.SetSpriteLayer(2)),

            # Pause and hold screen
            field.Pause(0.75),
            field.HoldScreen(),
            field.Pause(1.0),

            # Mute song, play dramatic sound
            field.FadeSongVolume(0, 0x00),
            field.PlaySoundEffect(205),
            field.Pause(2.0),

            # Camera quickly moves down
            field.PauseUnits(15),
            field.EntityAct(field_entity.CAMERA, False,
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.Move(direction.DOWN, 7)),

            # Play battle music
            field.StartSongAtVolume(0x1f, 0xff),  # Metamorphosis
            field.WaitForEntityAct(field_entity.CAMERA),
            field.Pause(0.5),

            # Party turns down to face threat
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Turn(direction.DOWN)),

            field.Pause(0.75),

            # Fade out and invoke battle
            field.FadeOutScreen(),
            field.WaitForFade(),

            # Boss battle
            field.InvokeBattleType(boss_pack_id, field.BattleType.BACK),

            # After battle - set event bit to prevent repeat
            field.SetEventBit(event_bit.SEALED_GATE_OPENED),

            # Hide the esper NPCs
            field.HideEntity(0x16),
            field.HideEntity(0x17),
            field.HideEntity(0x18),
            field.RefreshEntities(),

            # Play wind song and fade in
            field.StartSongAtVolume(0x39, 0x96),
            field.FadeInScreen(),

            # Party turns up toward the gate
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.Turn(direction.UP)),

            field.Pause(0.5),

            # Play gate opening sound
            field.FadeSoundEffect(0, 0x64),
            field.PlaySoundEffect(165),
            field.Pause(2.0),

            # Gate opens - move the gate NPCs (door pieces) apart
            field.EntityAct(0x10, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.LEFT, 1)),
            field.EntityAct(0x12, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.LEFT, 1)),
            field.EntityAct(0x13, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.LEFT, 1)),
            field.EntityAct(0x11, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.RIGHT, 1)),
            field.EntityAct(0x14, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.RIGHT, 1)),
            field.EntityAct(0x15, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOWEST),
                            field_entity.Move(direction.RIGHT, 1)),

            # Wait for gate animation
            field.Pause(1.5),

            # Fade out sound effect
            field.FadeSoundEffect(40, 0x00),

            # Camera moves down a bit
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.DOWN, 2)),

            # Set party back to layer 0 and free screen
            field.Call(SET_PARTY_LAYER0),
            field.FreeScreen(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "sealed gate ruination event")
        new_event_addr = space.start_address

        # Patch the original event start to branch to our new event
        # Original event starts at 0xb39ca with a check for event bit 0x079
        space = Reserve(0xb39ca, 0xb39d7, "sealed gate branch to new event", field.NOP())
        space.write(
            field.Branch(new_event_addr),
        )

        # Add exit tile at sealed gate to KT
        from event.switchyard import GoToSwitchyard
        kt_enter_id = 2077

        dialog_entry_id = 0x0666
        self.dialogs.set_text(dialog_entry_id, "Enter Kefka's Tower? There's no going back.<line><choice> Let's go<line><choice> Not just yet<end>")
        no_return_text = 1293   # same as airship.py

        src = [
            field.HoldScreen(),
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.UP, 2)),
            field.BranchIfEventBitSet(event_bit.ENABLE_Y_PARTY_SWITCHING, "ALLOW_ENTRY"),
            field.Dialog(no_return_text),
            "DO_NOT_ENTER",
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.Move(direction.DOWN, 2)),
            field.FreeScreen(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.DOWN, 2)),
            field.Return(),
            "ALLOW_ENTRY",
            field.DialogBranch(dialog_entry_id, dest1="ENTER_KT", dest2="DO_NOT_ENTER"),
            "ENTER_KT",
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetSpeed(field_entity.Speed.SLOW),
                            field_entity.Move(direction.UP, 3)),
            field.EntityAct(field_entity.CAMERA, True,
                            field_entity.Move(direction.UP, 2)),
            field.Call(0xb38ac),  # lightning strike
            field.HideEntity(field_entity.PARTY0),
            field.Pause(1),
            field.FadeOutScreen(),
            field.FreeScreen(),
        ] + GoToSwitchyard(kt_enter_id)
        space = Write(Bank.CB, src, "Sealed Gate access to Kefka's Tower")

        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 8
        new_event.y = 9
        new_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(map_id, new_event)

        # Set Sealed Gate map song to "wind" 0x39
        sealed_gate_properties = self.maps.properties[map_id]
        sealed_gate_properties.song = 0x39

        # Edit entrance event to show sealed gate as "open" if event already happened: CB/39BE
        patch_addr = [0xb39c3, 0xb39c8]
        src = [
            Read(patch_addr[0], patch_addr[1]),
            field.ReturnIfEventBitClear(event_bit.SEALED_GATE_OPENED),
            field.EntityAct(0x10, False,
                            field_entity.SetPosition(6, 5)),
            field.EntityAct(0x12, False,
                            field_entity.SetPosition(6, 7)),
            field.EntityAct(0x13, False,
                            field_entity.SetPosition(7, 7)),
            field.EntityAct(0x11, False,
                            field_entity.SetPosition(9, 5)),
            field.EntityAct(0x14, False,
                            field_entity.SetPosition(10, 7)),
            field.EntityAct(0x15, False,
                            field_entity.SetPosition(9, 7)),
            field.Return()
        ]
        space = Write(Bank.CB, src, 'Sealed Gate entrance event check if gate open')
        open_gate_addr = space.start_address

        space = Reserve(patch_addr[0], patch_addr[1], "Edit Sealed Gate entrance event", field.NOP())
        space.write(field.Call(open_gate_addr))

