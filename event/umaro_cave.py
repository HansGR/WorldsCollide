from event.event import *

class UmaroCave(Event):
    def name(self):
        return "Umaro's Cave"

    def character_gate(self):
        return self.characters.UMARO

    def init_rewards(self):
        # UMAROS COLLIDE: an item only. after kefka the carving starts the final battle instead of
        # giving its reward, which must not be something a route to kefka depends on
        self.reward = self.add_reward(RewardType.ITEM)

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

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.umaros_collide_mod()

        self.log_reward(self.reward)

    def umaros_collide_mod(self):
        # UMAROS COLLIDE: once kefka has knocked the party into the den (event/kefka_tower.py),
        # the carving starts the final battle: "touch the eye of the carving?", umaro stomps
        # in as he does before his own fight, then every available character joins the final
        # lineup in kefka's lair and the final battle begins (kefka tower's lineup and battle)
        CARVING_EVENT = 0xcd6eb                 # if the check is done return, else the carving scene
        CARVING_SCENE = 0xcd6f1
        UMARO_ENTRANCE_START, UMARO_ENTRANCE_END = 0xcd737, 0xcd776  # party startled, umaro stomps in
        KEFKA_LAIR = 0x164                      # the map the final lineup and battle start from
        SHOW_CASEWORD_CHARACTERS = 0xac9f3
        FINAL_LINEUP = 0xa0e46                  # kefka tower: final lineup, final battle, ending
        GOT_CARVING_REWARD = 0x27a

        touch_dialog = 1524 # vanilla: "what's with this carving? ..." (removed above)
        self.dialogs.set_text(touch_dialog, "Touch the eye of the carving?<line><choice> Yes<line><choice> No<end>")
        roar_dialog = 1527  # vanilla: "ooh..." umaro without mog in the party (removed in every reward mod)
        self.dialogs.set_text(roar_dialog, "UMARO: U'ghaaaa!!<end>")

        src = [
            field.BranchIfEventBitSet(event_bit.KNOCKED_INTO_UMAROS_DEN, "FINAL_BATTLE"),
            field.ReturnIfEventBitSet(GOT_CARVING_REWARD),
            field.Branch(CARVING_SCENE),

            "FINAL_BATTLE",
            field.DialogBranch(touch_dialog, dest1 = "TOUCH", dest2 = field.RETURN),

            "TOUCH",
            # the one who stomps in is umaro himself, whoever the cave's reward was
            field.SetSprite(self.umaro_cave_npc_id, self.characters.UMARO),
            field.SetPalette(self.umaro_cave_npc_id, self.characters.get_palette(self.characters.UMARO)),
            field.Pause(0.5),
            field.PlaySoundEffect(187),
            Read(UMARO_ENTRANCE_START, UMARO_ENTRANCE_END),
            field.Dialog(roar_dialog),
            field.FadeOutScreen(),
            field.WaitForFade(),
            field.HideEntity(self.umaro_cave_npc_id),

            # the final lineup lists the characters who are in a party: put every available
            # character into one (the lineup holds 12; umaro and gogo first so they are never
            # the ones left out)
            field.Call(field.REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES),
            field.Call(field.DELETE_ALL_CHARACTERS),
            field.Call(field.CREATE_AVAILABLE_CHARACTERS),
            field.RefreshEntities(),
            field.SetEventWord(event_word.SCRATCH, 0),
        ]
        characters = [self.characters.UMARO, self.characters.GOGO]
        characters += [character for character in range(self.characters.CHARACTER_COUNT) if character not in characters]
        for character in characters:
            src += [
                field.BranchIfEventBitClear(event_bit.character_available(character), f"NEXT_{character}"),
                field.BranchIfEventWordLess(event_word.SCRATCH, 4, f"PARTY_1_{character}"),
                field.BranchIfEventWordLess(event_word.SCRATCH, 8, f"PARTY_2_{character}"),
                field.BranchIfEventWordLess(event_word.SCRATCH, 12, f"PARTY_3_{character}"),
                field.Branch(f"NEXT_{character}"),

                f"PARTY_1_{character}",
                field.AddCharacterToParty(character, 1),
                field.Branch(f"PLACED_{character}"),
                f"PARTY_2_{character}",
                field.AddCharacterToParty(character, 2),
                field.Branch(f"PLACED_{character}"),
                f"PARTY_3_{character}",
                field.AddCharacterToParty(character, 3),
                f"PLACED_{character}",
                field.IncrementEventWord(event_word.SCRATCH),
                f"NEXT_{character}",
            ]
        src += [
            field.SetParty(1),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),

            # what kefka tower does before the lineup (0xa0e24-0xa0e45), with the screen held as
            # it is there (the camera moves before the battle) and faded back in
            field.SetEventBit(0x39e),                # npc bits
            field.ClearEventBit(0x3f5),
            field.LoadMap(KEFKA_LAIR, direction.DOWN, default_music = False, x = 15, y = 17),
            field.HoldScreen(),
            field.LoadAvailableCharacters(),
            field.Call(SHOW_CASEWORD_CHARACTERS),
            field.SetPartyMap(1, KEFKA_LAIR),
            field.SetPartyMap(2, KEFKA_LAIR),
            field.SetPartyMap(3, KEFKA_LAIR),
            field.RefreshEntities(),
            field.FadeInScreen(),
            field.WaitForFade(),                # (the lineup menu hangs if opened mid-fade)
            field.Branch(FINAL_LINEUP),
        ]
        space = Write(Bank.CC, src, "umaros collide: carving starts the final battle")
        carving = space.start_address

        space = Reserve(CARVING_EVENT, CARVING_SCENE - 1, "umaro cave carving event", field.NOP())
        space.write(
            field.Branch(carving),
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
