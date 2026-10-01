from event.event import *

class BarenFalls(Event):
    def name(self):
        return "Baren Falls"

    def character_gate(self):
        return self.characters.SABIN

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        # delete row of events that trigger sabin/cyan dialog and shadow leaving (if in party)
        for x in range(9, 18):
            self.maps.delete_event(0x9c, x, 12)

        if self.args.character_gating:
            self.add_gating_condition()

        if self.args.no_free_heals:
            self.remove_free_heal_mod()

        self.rizopas_battle_mod()
        self.after_battle_mod()
        self.already_complete_mod()

        if self.args.flashes_remove_most:
            self.background_scrolling_mod()

        if self.args.race:
            self.race_reward_mod()
        elif self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def race_reward_mod(self):
        # one script for every kind.  the vanilla scene animates only the
        # gau NPC (entity 0x10) and the party leader, so it carries no
        # character id at all - the leaks were the npc record (left
        # vanilla now, repainted in-scene), the theme song operand (now
        # PlayRewardTheme) and the differing per-kind patch shapes (now
        # one runtime branch)
        slot = self.race_slot(self.reward)

        gau_npc_id = 0x10

        # scene entry: fade song, pause, create npc / show / refresh,
        # start song (vanilla 0xbc0f7-0xbc100).  the character branch
        # replays it with the npc repainted between create and show and
        # the theme decoded from the slot; other kinds skip the scene as
        # the esper/item path always did
        src = [
            field.BranchIfRewardKindNot(slot, "character", "SKIP_SCENE"),
            Read(0xbc0f7, 0xbc0fb),         # fade song, pause, create npc
            field.SetRewardSprite(gau_npc_id, slot),
            field.SetRewardPalette(gau_npc_id, slot),
            Read(0xbc0fc, 0xbc0fe),         # show npc, refresh
            field.PlayRewardTheme(slot),
            field.Branch(0xbc101),          # the arrival scene
            "SKIP_SCENE",
            field.Branch(0xbc1b8),          # straight to the landing
        ]
        space = Write(Bank.CB, src, "baren falls race scene entry")
        scene_entry = space.start_address

        # the turn toward the npc runs only when the npc exists
        src = [
            field.BranchIfRewardKindNot(slot, "character", "NO_TURN"),
            Read(0xbc1c2, 0xbc1c5),         # npc turns
            "NO_TURN",
            Read(0xbc1c6, 0xbc1db),         # party leader looks around
            field.Branch(0xbc1dc),
        ]
        space = Write(Bank.CB, src, "baren falls race npc turn")
        npc_turn = space.start_address

        src = [
            field.BranchIfRewardKindNot(slot, "character", "ESPER_ITEM"),

            # the character scene (character_mod's script, slot-driven)
            Read(0xbc1dc, 0xbc1e1),         # pause, party leader nods
            field.Pause(0.5),
            field.AddCheckReward(slot),
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            Read(0xbc1ef, 0xbc1f1),         # hide npc, refresh
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.NAMED_GAU),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Branch(0xbc1f6),          # rest of the vanilla wrap-up

            # the esper/item scene (esper/item_mod's script, slot-driven)
            "ESPER_ITEM",
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.NAMED_GAU),
            field.ReceiveCheckReward(slot),
            field.FinishCheck(),
            field.Branch(0xbc1f6),
        ]
        space = Write(Bank.CB, src, "baren falls race reward")
        reward_script = space.start_address

        space = Reserve(0xbc0f7, 0xbc100, "baren falls scene entry", field.NOP())
        space.write(
            field.Branch(scene_entry),
        )
        space = Reserve(0xbc15d, 0xbc1b1, "baren falls gau naming", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xbc1c2, 0xbc1db, "baren falls npc turn", field.NOP())
        space.write(
            field.Branch(npc_turn),
        )
        space = Reserve(0xbc1dc, 0xbc1f5, "baren falls reward", field.NOP())
        space.write(
            field.Branch(reward_script),
        )

    def add_gating_condition(self):
        src = [
            field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            Read(0xbc03f, 0xbc057)   # jump? dialog
        ]
        space = Write(Bank.CB, src, "baren falls character gating")
        gate_check = space.start_address

        space = Reserve(0xbc03f, 0xbc057, "baren falls jump dialog options", field.NOP())
        space.write(
            field.Branch(gate_check),
            field.Return(),
        )

    def rizopas_battle_mod(self):
        boss_pack_id = self.get_boss("Rizopas")

        space = Reserve(0xbc0b6, 0xbc0bc, "baren falls invoke battle rizopas", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def after_battle_mod(self):
        src = [
            # move airship
            field.LoadMap(0x000, direction.DOWN, default_music = False,
                          x = 192, y = 105, fade_in = False, airship = True),
            vehicle.SetPosition(192, 105),
            vehicle.SetEventBit(event_bit.VELDT_WORLD_MUSIC),

            vehicle.LoadMap(0x09f, direction.DOWN, default_music = True, x = 15, y = 0, fade_in = False),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "baren falls move airship after rizopas battle")
        load_map = space.start_address

        space = Reserve(0xbc0bf, 0xbc0c4, "baren falls load map after rizopas battle", field.NOP())
        space.write(
            field.Call(load_map),
        )

        space = Reserve(0xbc0cb, 0xbc0cc, "baren falls pause before starting song", field.NOP())

    def already_complete_mod(self):
        # jumped after rizopas already defeated, exit to world map after battle
        src = [
            # move airship
            field.StartSong(0),
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.LoadMap(0x000, direction.DOWN, default_music = False,
                          x = 192, y = 105, fade_in = False, airship = True),
            vehicle.SetPosition(192, 105),
            vehicle.SetEventBit(event_bit.VELDT_WORLD_MUSIC),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),

            # load world map
            vehicle.LoadMap(0x000, direction.DOWN, default_music = True, x = 192, y = 105),
            world.End(),
        ]
        space = Write(Bank.CB, src, "baren falls exit function")
        exit_function = space.start_address

        space = Reserve(0xbc203, 0xbc209, "baren falls rizopas already defeated, load wob", field.NOP())
        space.write(
            field.Branch(exit_function),
        )

    def character_music_mod(self, character):
        from music.song_utils import get_character_theme

        space = Reserve(0xbc0ff, 0xbc100, "Play Song Gau")
        space.write([
            field.StartSong(get_character_theme(character)),
        ])

    def character_mod(self, character):
        self.character_music_mod(character)
        gau_npc_id = 0x10
        gau_npc = self.maps.get_npc(0x09f, gau_npc_id)
        gau_npc.sprite = character
        gau_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xbc15d, 0xbc1b1, "baren falls gau naming", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nop
        )

        space = Reserve(0xbc1e2, 0xbc1ee, "baren falls gau runs off", field.NOP())
        space.write(
            field.Pause(0.5),
            field.RecruitCharacter(character),
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.Branch(space.end_address + 1), # skip nop
        )

        src = [
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.NAMED_GAU),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "baren falls character finish check")
        finish_check = space.start_address

        space = Reserve(0xbc1f2, 0xbc1f5, "baren falls character call finish check", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def esper_item_mod(self, esper_item_instructions):
        space = Reserve(0xbc0f7, 0xbc1b7, "baren falls gau moving/naming", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nop
        )

        space = Reserve(0xbc1c2, 0xbc1c5, "skip gau turns left at baren falls", field.NOP())

        space = Reserve(0xbc1dc, 0xbc1f5, "baren falls esper item reward", field.NOP())
        space.write(
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.NAMED_GAU),
            esper_item_instructions,
            field.FinishCheck(),
            field.Branch(space.end_address + 1), # skip nop
        )

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

    def background_scrolling_mod(self):
        # Slow the scrolling background by modifying the ADC command.
        space = Reserve(0x2b1f7, 0x2b1f9, "waterfall background movement")
        space.write(
            asm.ADC(0x0001, asm.IMM16) #default: 0x0006
        )

        # Eliminate the palette swaps without reducing any cpu cycles by just writing back the value from the previous LDA
        space = Reserve(0x2b20b, 0x2b20d, "waterfall palette change")
        space.write(
            asm.STA(0xEC71, asm.ABS_X)
        )

    def remove_free_heal_mod(self):
        # Event beginning the battle has a free heal.  Remove it.
        # CB/C0B2: B2    Call subroutine $CACFBD (heals all HP/MP/Statuses except M-Tek & Dog Block)
        space = Reserve(0xbc0b2, 0xbc0b5, "Baren Falls remove free heal", field.NOP())
