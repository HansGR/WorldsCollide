from event.event import *

class UmaroCave(Event):
    def name(self):
        return "Umaro's Cave"

    def character_gate(self):
        return self.characters.UMARO

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        space = Reserve(0xcd6f5, 0xcd6f7, "umaro cave what's with this carving", field.NOP())

        # umaro in cave who stomps down the stairs
        self.umaro_cave_npc_id = 0x11
        self.umaro_cave_npc = self.maps.get_npc(0x11b, self.umaro_cave_npc_id)

        # umaro visible in wob northern narshe
        self.umaro_wob_npc_id = 0x11
        self.umaro_wob_npc = self.maps.get_npc(0x015, self.umaro_wob_npc_id)

        if self.args.character_gating:
            self.add_gating_condition()

        self.umaro_battle_mod()

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
        # one script and one npc record for every kind, with the carving
        # wording, glint and magicite animation selected at runtime so
        # each kind shows exactly what its non-race build bakes; the
        # reward is granted after the battle either way.  the scene
        # animates the umaro npcs by npc id, so after the entrance
        # repaint the whole vanilla scene works for any character
        from obfuscation import rewards
        slot = rewards.register_check(self.reward)

        # both npc records keep vanilla umaro's sprite - constant
        # whatever the check holds, so nothing to read out of the rom,
        # and exactly what non-race esper/item builds show (the yeti
        # attacks you regardless of the reward).  a character reward
        # repaints them at map load
        self.race_repaint_npc_entrance(0x11b, self.umaro_cave_npc_id, slot)
        self.race_repaint_npc_entrance(0x015, self.umaro_wob_npc_id, slot)

        # each kind keeps its non-race carving: the vanilla magicite
        # wording, glint and rising-magicite animation for an esper, the
        # item wording for an item, the neutral wording for a character.
        # the spare wordings ride in dialogs whose own commands every
        # build removes (1524, "what's with this carving") or leaves
        # unused in race (1526, the baked receive text)
        item_carving_dialog = 1524
        character_carving_dialog = 1526
        self.dialogs.set_text(item_carving_dialog, "Remove the item from the eye of the carving?<line><choice> Yes<line><choice> No<end>")
        self.dialogs.set_text(character_carving_dialog, "Touch the eye of the carving?<line><choice> Yes<line><choice> No<end>")

        src = [
            field.BranchIfRewardKindNot(slot, "esper", "NOT_ESPER"),
            Read(0xcd6f8, 0xcd6fd),         # chime, the magicite glints
            field.Branch(0xcd6fe),          # the vanilla magicite wording + choice
            "NOT_ESPER",
            field.BranchIfRewardKindNot(slot, "item", "NOT_ITEM"),
            field.Dialog(item_carving_dialog),
            field.Branch(0xcd701),          # the yes/no branch
            "NOT_ITEM",
            field.Dialog(character_carving_dialog),
            field.Branch(0xcd701),
        ]
        space = Write(Bank.CC, src, "umaro cave race carving")
        carving = space.start_address
        space = Reserve(0xcd6f8, 0xcd6fd, "narshe wor umaro carving magicite flash", field.NOP())
        space.write(
            field.Branch(carving),
        )

        # the yes path: an esper replays the rising-magicite animation
        # (entity 0x12, a static record identical in every build), and
        # esper/item show the receive dialog before the battle exactly
        # as their non-race builds do - the grant itself stays after the
        # battle, as it always was
        src = [
            field.BranchIfRewardKind(slot, "character", "YES_DONE"),
            field.BranchIfRewardKindNot(slot, "esper", "SKIP_ANIMATION"),
            Read(0xcd709, 0xcd72e),         # the magicite rises from the eye
            "SKIP_ANIMATION",
            Read(0xcd72f, 0xcd730),         # got-it sound
            field.receive_reward_dialog(slot),
            Read(0xcd734, 0xcd736),         # pause, rumble
            "YES_DONE",
            field.Branch(0xcd737),          # the cave shakes, umaro attacks
        ]
        space = Write(Bank.CC, src, "umaro cave race carving yes path")
        yes_path = space.start_address
        space = Reserve(0xcd709, 0xcd736, "narshe wor get esper from bone carving", field.NOP())
        space.write(
            field.Branch(yes_path),
        )

        # umaro's wob appearance plays only for a character reward
        src = [
            field.BranchIfRewardKindNot(slot, "character", "HIDE_WOB"),
            Read(0xc3871, 0xc388d),
            field.Branch(0xc388e),
            "HIDE_WOB",
            field.HideEntity(self.umaro_wob_npc_id),
            field.Branch(0xc388e),
        ]
        space = Write(Bank.CC, src, "umaro cave race wob appearance")
        wob_appearance = space.start_address
        space = Reserve(0xc3871, 0xc388d, "narshe wob umaro appearance", field.NOP())
        space.write(
            field.Branch(wob_appearance),
        )

        # after the battle: esper/item receive and finish here; a
        # character continues into the vanilla umaro scene
        src = [
            field.BranchIfRewardKindNot(slot, "character", "ESPER_ITEM"),
            Read(0xcd77e, 0xcd78e),         # umaro gets back up
            field.Branch(0xcd791),          # the vanilla umaro scene

            "ESPER_ITEM",
            field.HideEntity(self.umaro_cave_npc_id),
            field.SetEventBit(event_bit.RECRUITED_UMARO_WOR),
            field.ClearEventBit(npc_bit.UMARO_NARSHE_WOR),
            # granted silently: the receive dialog already showed at the
            # carving, as in non-race esper/item builds
            field.AddCheckReward(slot),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "umaro cave race post battle")
        post_battle = space.start_address
        space = Reserve(0xcd77e, 0xcd790, "narshe wor umaro post battle", field.NOP())
        space.write(
            field.Branch(post_battle),
        )

        # the character path through the vanilla scene (only reached for
        # a character reward): drop the mog requirements and naming, then
        # recruit from the slot
        space = Reserve(0xcd794, 0xcd799, "narshe wor recruit umaro do not require mog", field.NOP())
        space = Reserve(0xcd79a, 0xcd7a8, "narshe wor add umaro to party", field.NOP())
        space = Reserve(0xcd7b2, 0xcd7b6, "narshe wor umaro do not change party for mog", field.NOP())
        space = Reserve(0xcd7d8, 0xcd7db, "narshe wor i'm your boss, kupo!", field.NOP())
        space = Reserve(0xcd7f5, 0xcd843, "narshe wor name umaro", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xcd870, 0xcd884, "narshe wor add umaro", field.NOP())
        space.write(
            field.AddCheckReward(slot),
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xcd88d, 0xcd894, "narshe wor umaro finish check", field.NOP())
        space.write(
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        )

    def add_gating_condition(self):
        CLIFF_MOVE_BACK = 0xc37f8

        # use dialog on black screen before naming umaro
        cliff_no_jump_dialog_id = 1529
        self.dialogs.set_text(cliff_no_jump_dialog_id, "There's an opening in the cliff.<end>")

        src = [
            field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), "NO_JUMP_OPTION"),

            Read(0xc37ed, 0xc37f7), # cliff jump yes/no dialog

            "NO_JUMP_OPTION",
            field.Dialog(cliff_no_jump_dialog_id),
            field.Branch(CLIFF_MOVE_BACK),
        ]
        space = Write(Bank.CC, src, "umaro cave cliff gating condition")
        cliff_jump_gate = space.start_address

        space = Reserve(0xc37ed, 0xc37f7, "umaro cave cliff gating condition branch", field.NOP())
        space.write(
            field.Branch(cliff_jump_gate),
        )

    def umaro_battle_mod(self):
        boss_pack_id = self.get_boss("Umaro")

        space = Reserve(0xcd777, 0xcd77d, "umaro's cave invoke battle umaro", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def character_mod(self, character):
        self.umaro_cave_npc.sprite = character
        self.umaro_cave_npc.palette = self.characters.get_palette(character)

        self.umaro_wob_npc.sprite = character
        self.umaro_wob_npc.palette = self.characters.get_palette(character)
        # TODO hide umaro in wob? (his npc bit is shared...)
        #      change the entrance event to somewhere with more space where can check for umaro recruited?

        # change dialog since no magicite in eye now
        self.dialogs.set_text(dialog_id.UMARO_CAVE_CARVING, "Touch the eye of the carving?<line><choice> Yes<line><choice> No<end>")

        space = Reserve(0xcd6f8, 0xcd6fd, "narshe wor umaro carving magicite flash", field.NOP())
        space = Reserve(0xcd709, 0xcd736, "narshe wor get esper from bone carving", field.NOP())
        space = Reserve(0xcd78f, 0xcd790, "narshe wor give party terrato", field.NOP())

        # do not require mog in party to recruit character
        space = Reserve(0xcd794, 0xcd799, "narshe wor recruit umaro do not require mog", field.NOP())
        space = Reserve(0xcd79a, 0xcd7a8, "narshe wor add umaro to party", field.NOP())
        space = Reserve(0xcd7b2, 0xcd7b6, "narshe wor umaro do not change party for mog", field.NOP())
        space = Reserve(0xcd7d8, 0xcd7db, "narshe wor i'm your boss, kupo!", field.NOP())
        space = Reserve(0xcd7f5, 0xcd843, "narshe wor name umaro", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xcd870, 0xcd884, "narshe wor add umaro", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
            field.Branch(space.end_address + 1), # skip nops
        )
        space = Reserve(0xcd88d, 0xcd894, "narshe wor umaro finish check", field.NOP())
        space.write(
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        )

    def esper_item_mod(self, add_instructions, dialog_instructions):
        # remove umaro from wob
        space = Reserve(0xc3871, 0xc388d, "narshe wob umaro appearance", field.NOP())
        space.write(
            field.HideEntity(self.umaro_wob_npc_id),
        )

        space = Reserve(0xcd731, 0xcd733, "narshe wor receive esper dialog bone carving", field.NOP())
        space.write(
            dialog_instructions,
        )

        space = Reserve(0xcd77e, 0xcd788, "narshe wor hide umaro npc", field.NOP())
        space.write(
            field.HideEntity(self.umaro_cave_npc_id),
            field.SetEventBit(event_bit.RECRUITED_UMARO_WOR),
            field.ClearEventBit(npc_bit.UMARO_NARSHE_WOR),
        )

        space = Reserve(0xcd78d, 0xcd790, "narshe wor umaro get esper", field.NOP())
        space.write(
            add_instructions,
        )

        space = Reserve(0xcd792, 0xcd895, "narshe wor talk to umaro npc event", field.NOP())
        space.write(
            field.FinishCheck(),
            field.Return(),
        )

    def esper_mod(self, esper):
        self.esper_item_mod(
            field.AddEsper(esper, sound_effect = False),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        )

    def item_mod(self, item):
        # change dialog from magicite to item
        self.dialogs.set_text(dialog_id.UMARO_CAVE_CARVING, "Remove the item from the eye of the carving?<line><choice> Yes<line><choice> No<end>")

        space = Reserve(0xcd6f8, 0xcd6fd, "umaro cave esper sound effect and blue screen flash", field.NOP())
        space = Reserve(0xcd709, 0xcd72e, "umaro cave animate receiving esper", field.NOP())

        self.esper_item_mod(
            field.AddItem(item, sound_effect = False),
            field.Dialog(self.items.get_receive_dialog(item))
        )
