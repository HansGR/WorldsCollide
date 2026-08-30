from event.event import *

class LoneWolf(Event):
    def name(self):
        return "Lone Wolf"

    def character_gate(self):
        return self.characters.MOG

    def init_rewards(self):
        if self.args.no_free_characters_espers:
            self.reward1 = self.add_reward(RewardType.ITEM)
        else:
            self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)
        
        self.reward2 = self.add_reward(RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
        )

    def mod(self):
        self.mog_npc_id = 0x1c
        self.mog_npc = self.maps.get_npc(0x017, self.mog_npc_id)

        self.lone_wolf_npc_id = 0x1b
        self.lone_wolf_npc = self.maps.get_npc(0x017, self.lone_wolf_npc_id)

        self.mog_moogle_room_npc_id = 0x10
        self.mog_moogle_room_npc = self.maps.get_npc(0x02c, self.mog_moogle_room_npc_id)

        # invisible npc blocking bridge until player chooses either mog or lone wolf
        self.invisible_bridge_block_npc_id = 0x1d

        self.dialog_mod()
        self.chase_mod()

        if self.args.race:
            self.race_reward_mod()
        elif self.reward1.type == RewardType.CHARACTER:
            self.character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            self.item_mod(self.reward1.id)
        self.alternative_item_mod()
        self.finish_check_mod()

        self.moogle_room_entrance_event_mod()
        self.moogle_room_reward_mod()

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)

    def dialog_mod(self):
        space = Reserve(0xcd3ef, 0xcd3f1, "lone wolf G'whoa! I've been made!", field.NOP())
        space = Reserve(0xcd407, 0xcd409, "I am lone wolf, the pickpocket!", field.NOP())
        space = Reserve(0xcd437, 0xcd439, "lone wolf outside treasure room G'heh!", field.NOP())
        space = Reserve(0xcd4a1, 0xcd4a3, "lone wolf Persistent, aren't you!", field.NOP())
        space = Reserve(0xcd54c, 0xcd54e, "lone wolf mog stands dialog Kupo!!", field.NOP())
        space = Reserve(0xcd560, 0xcd562, "lone wolf G'heh! Got a wild one, here", field.NOP())
        space = Reserve(0xcd5a0, 0xcd5a2, "lone wolf kupo before mog falls", field.NOP())
        space = Reserve(0xcd608, 0xcd60a, "lone wolf Thankupo!", field.NOP())

    def chase_mod(self):
        if self.args.character_gating:
            space = Reserve(0xcd3d4, 0xcd3db, "lone wolf saw maduin die and not started lone wolf requirements")
            space.write(
                field.ReturnIfAny([event_bit.character_recruited(self.character_gate()), False, event_bit.CHASING_LONE_WOLF1, True]),
            )

        space = Reserve(0xcd3f3, 0xcd3f4, "lone wolf pauses before beginning to exit", field.NOP())
        space.write(field.Pause(0.5)) # shorten from 1.5 seconds
        space = Reserve(0xcd402, 0xcd402, "lone wolf pauses before turning right")
        space.write(field.Pause(0.5)) # shorten from 2 seconds

    def character_music_mod(self, character):
        from music.song_utils import get_character_theme
        src = [
            field.StartSong(get_character_theme(character)),
        ]
        space = Reserve(0xcd606, 0xcd607, "Play Song Mog")
        space.write(src)

    def character_mod(self, character):
        self.character_music_mod(character)
        self.mog_npc.sprite = character
        self.mog_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xcd5e5, 0xcd5f3, "lone wolf create char and make available", field.NOP())
        space.write(
            field.CreateEntity(character),
            field.RecruitCharacter(character),
        )

        # move lone wolf falling up to make room for adding character
        # skip copying lone wolf take this dialog at [0xcd693,0xcd695]
        space = Reserve(0xcd61b, 0xcd67b, "lone wolf mog dialog and naming", field.NOP())
        space.copy_from(0xcd67c, 0xcd692)
        space.copy_from(0xcd696, 0xcd6bf)
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xcd67c, 0xcd6dc, "lone wolf add char", field.NOP())
        space.write(
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.HideEntity(self.mog_npc_id),
            field.HideEntity(self.invisible_bridge_block_npc_id),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.RECRUITED_MOG_WOB),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.Branch(space.end_address + 1), # skip nops
        )

    def race_reward_mod(self):
        # one script and one npc record for every kind of reward1.  the
        # cliff npc gets the decoy sprite, repainted at map load for a
        # character.  both kinds play the vanilla lone-wolf-falls scene:
        # a character branch replays it from a relocated copy and then
        # recruits; the esper/item branch takes it in place and shows the
        # receive dialog at the vanilla dialog site.  *Race-only
        # cosmetic*: the scene keeps vanilla's song (the StartSong site
        # is two bytes, too tight for the slot-driven theme command)
        from obfuscation import rewards
        slot = rewards.register_check(self.reward1)
        self.race_slot = slot

        self.mog_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.mog_npc.palette = self.characters.get_palette(self.mog_npc.sprite)
        self.race_repaint_npc_entrance(0x017, self.mog_npc_id, slot)

        src = [
            field.BranchIfRewardKindNot(slot, "character", "ESPER_ITEM"),
            Read(0xcd5df, 0xcd5e4),
            field.CreateRewardEntity(slot),
            field.AddCheckReward(slot),
            field.Branch(0xcd5f4),
            "ESPER_ITEM",
            field.Branch(0xcd5f4),
        ]
        space = Write(Bank.CC, src, "lone wolf race create/recruit")
        create_script = space.start_address

        space = Reserve(0xcd5df, 0xcd5f3, "lone wolf assign character properties", field.NOP())
        space.write(
            field.Branch(create_script),
        )

        src = [
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.HideEntity(self.mog_npc_id),
            field.HideEntity(self.invisible_bridge_block_npc_id),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.RECRUITED_MOG_WOB),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.Branch(0xcd6dd),
        ]
        space = Write(Bank.CC, src, "lone wolf race character finish")
        character_finish = space.start_address

        src = [
            field.BranchIfRewardKindNot(slot, "character", "ESPER_ITEM"),
            # replay the falls scene (skipping the "take this" dialog),
            # then finish the recruit
            Read(0xcd67c, 0xcd692),
            Read(0xcd696, 0xcd6bf),
            field.Branch(character_finish),
            "ESPER_ITEM",
            field.AddCheckReward(slot),
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.Branch(0xcd67c),      # the falls scene, in place
        ]
        space = Write(Bank.CC, src, "lone wolf race reward")
        reward_script = space.start_address

        space = Reserve(0xcd61b, 0xcd67b, "lone wolf reward", field.NOP())
        space.write(
            field.Branch(reward_script),
        )

        space = Reserve(0xcd693, 0xcd695, "char chosen dialog before lone wolf falls", field.NOP())

        space = Reserve(0xcd6bf, 0xcd6c3, "lone wolf add esper/item dialog", field.NOP())
        space.write(
            field.PlaySoundEffect(141),
            field.receive_reward_dialog(slot),
        )

    def esper_item_mod(self, add_esper_item, sound_dialog_esper_item):
        space = Reserve(0xcd5df, 0xcd5f3, "lone wolf assign character properties", field.NOP())
        space = Reserve(0xcd693, 0xcd695, "char chosen dialog before lone wolf falls", field.NOP())

        space = Reserve(0xcd61b, 0xcd67b, "lone wolf add esper/item", field.NOP())
        space.write(
            add_esper_item,
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xcd6bf, 0xcd6c3, "lone wolf add esper/item dialog", field.NOP())
        space.write(
            sound_dialog_esper_item,
        )

    def esper_mod(self, esper):
        self.mog_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.mog_npc.palette = self.characters.get_palette(self.mog_npc.sprite)

        self.esper_item_mod([
            field.AddEsper(esper, sound_effect = False),
        ],
        [
            field.PlaySoundEffect(141),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.mog_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.mog_npc.palette = self.characters.get_palette(self.mog_npc.sprite)

        self.esper_item_mod([
            field.AddItem(item, sound_effect = False),
        ],
        [
            field.PlaySoundEffect(141),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def alternative_item_mod(self):
        # item lone wolf will give as a reward for not picking self.reward1
        item_name = self.items.dialog_name(self.reward2.id)

        # the taunt runs before any grant, so the dialog itself has to
        # decode the name; "Got X!" follows the grant, which already
        # leaves the id in $0583 (race builds; plain text otherwise)
        space = Reserve(0xcd582, 0xcd584, "lone wolf taunt dialog")
        space.write(
            field.reward_dialog("item", self.reward2.id, 1765,
                                inside_text_box = False, top_of_screen = False),
        )
        self.dialogs.set_text(1765, "<line><     >Grrrr…<line><     >You'll never get this<line><     >“" + item_name + "”!<end>")
        self.dialogs.set_text(dialog_id.LONE_WOLF_GOT_ITEM, "<line><      >Got “" + item_name + "”!<end>")

        if self.args.race:
            # the vanilla script grants this reward with $80 <item id>;
            # replace the whole 2-byte command with the opaque one so the
            # id is not sitting in the script (and so the grant leaves the
            # decoded id in $0583 for the "Got X!" dialog)
            from obfuscation import rewards
            import instruction.field.custom as custom
            space = Reserve(0xcd59e, 0xcd59f, "lone wolf item received (opaque)")
            space.write(
                custom.add_check_reward_opcode(),
                rewards.register("item", self.reward2.id),
            )
        else:
            space = Reserve(0xcd59f, 0xcd59f, "lone wolf item received", field.NOP())
            space.write(
                self.reward2.id,
            )

        space = Reserve(0xcd5be, 0xcd5c0, "item chosen dialog before lone wolf falls", field.NOP())
        space.write(
            field.SetEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
        )

        # add pause after lone wolf jumps to wait for falling sound effect
        src = [
            field.HideEntity(self.lone_wolf_npc_id),
            field.RefreshEntities(),
            field.HideEntity(self.invisible_bridge_block_npc_id),
            field.RefreshEntities(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf hide lone wolf and remove bridge block")
        hide_npcs = space.start_address

        space = Reserve(0xcd5d1, 0xcd5d6, "lone wolf hide npcs after fall", field.NOP())
        space.write(
            field.Call(hide_npcs),
            field.Pause(1.5),
        )

    def finish_check_mod(self):
        src = [
            field.ClearEventBit(npc_bit.LONE_WOLF_MOG_NARSHE_CLIFF),
            field.ClearEventBit(npc_bit.LONE_WOLF_NARSHE_CLIFF_BRIDGE),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf finish check")
        finish_check = space.start_address

        space = Reserve(0xcd6dd, 0xcd6e0, "lone wolf finish saving mog", field.NOP())
        space.write(
            field.Call(finish_check),
        )

        space = Reserve(0xcd5d7, 0xcd5da, "lone wolf finish saving gold hairpin", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def moogle_room_character_mod(self, character):
        src = [
            field.RecruitAndSelectParty(character),

            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf moogle room npc character reward")
        return space.start_address

    def moogle_room_esper_item_mod(self, esper_item_instructions):
        src = [
            esper_item_instructions,

            field.FadeOutScreen(),
            field.WaitForFade(),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf moogle room npc esper/item reward")
        return space.start_address

    def moogle_room_esper_mod(self, esper):
        return self.moogle_room_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def moogle_room_item_mod(self, item):
        return self.moogle_room_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def race_moogle_room_reward_mod(self):
        # one script and one npc look for every kind of reward1 in the
        # moogle room too - the follow-up npc that hands over whichever
        # reward was not taken on the cliff.  the per-kind build-time
        # arms below were the one script that still differed by kind,
        # and the extra slots their esper/item grants registered made
        # slot numbering seed-dependent (caught in playtest).  the
        # entrance repaint chains onto the swap handler installed by
        # moogle_room_entrance_event_mod, so the repaint runs first and
        # the lone-wolf swap can still override it
        slot = self.race_slot
        self.race_repaint_npc_entrance(0x02c, self.mog_moogle_room_npc_id, slot)

        src = [
            field.BranchIfRewardKindNot(slot, "character", "ESPER_ITEM"),
            field.AddCheckReward(slot),
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),

            "ESPER_ITEM",
            field.AddCheckReward(slot),
            field.PlaySoundEffect(141),
            field.receive_reward_dialog(slot),
            field.FadeOutScreen(),
            field.WaitForFade(),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf moogle room race reward")
        return space.start_address

    def moogle_room_reward_mod(self):
        receive_reward = field.RETURN
        if self.args.race:
            receive_reward = self.race_moogle_room_reward_mod()
        elif self.reward1.type == RewardType.CHARACTER:
            receive_reward = self.moogle_room_character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            receive_reward = self.moogle_room_esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            receive_reward = self.moogle_room_item_mod(self.reward1.id)

        src = [
            field.BranchIfEventBitSet(event_bit.RECRUITED_MOG_WOB, "LONE_WOLF_FELL"),
            field.EntityAct(self.mog_moogle_room_npc_id, True,
                field_entity.AnimateSurprised(),
                field_entity.Pause(8),
                field_entity.AnimateStandingFront(),
            ),
            field.Call(receive_reward),
            field.Return(),

            "LONE_WOLF_FELL",
            field.DisableEntityCollision(self.mog_moogle_room_npc_id),
            field.EntityAct(self.mog_moogle_room_npc_id, True,
                field_entity.AnimateLowJump(),
                field_entity.Pause(8),
                field_entity.SetSpeed(field_entity.Speed.FASTEST),
                field_entity.Move(direction.DOWN, 8),
            ),
            field.AddItem(self.reward2.id),
            field.Dialog(dialog_id.LONE_WOLF_GOT_ITEM),
            field.HideEntity(self.mog_moogle_room_npc_id),
            field.ClearEventBit(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.SetEventBit(event_bit.GOT_BOTH_REWARDS_LONE_WOLF),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf npc event second reward not chosen")
        npc_event = space.start_address

        space = Reserve(0xc396c, 0xc3970, "lone wolf npc not saved second reward", field.NOP())
        space.write(
            field.Call(npc_event),
            field.Return(),
        )

    def moogle_room_entrance_event_mod(self):
        # initialize mog npc to match the npc that was on the cliff with lone wolf
        self.mog_moogle_room_npc.sprite = self.mog_npc.sprite
        self.mog_moogle_room_npc.palette = self.mog_npc.palette

        # if mog npc is here (i.e. finished lone wolf event and haven't received the second reward yet)
        # and if did not choose to save lone wolf on cliff
        # change mog npc to lone wolf
        src = [
            field.ReturnIfEventBitClear(npc_bit.MOG_MOOGLE_ROOM_WOR),
            field.ReturnIfEventBitClear(event_bit.RECRUITED_MOG_WOB),
            field.SetSprite(self.mog_moogle_room_npc_id, self.lone_wolf_npc.sprite),
            field.SetPalette(self.mog_moogle_room_npc_id, self.lone_wolf_npc.palette),
            field.RefreshEntities(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "lone wolf new moogle room entrance event")

        self.maps.set_entrance_event(0x02c, space.start_address - EVENT_CODE_START)
