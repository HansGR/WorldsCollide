from event.event import *

NUM_HEALS = 3

class NarsheWOB(Event):
    def name(self):
        return "Narshe WOB"

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.MET_ARVIS),
            field.SetEventBit(event_bit.NARSHE_GUARDS_SAW_TERRA_ON_BRIDGE),
            field.SetEventBit(event_bit.NARSHE_SECRET_ENTRANCE_ACCESS),
            field.SetEventBit(event_bit.TERRA_AGREED_TO_OPEN_SEALED_GATE),

            field.ClearEventBit(npc_bit.BACK_DOOR_ARVIS_HOUSE),
            field.ClearEventBit(npc_bit.SOLDIER_DOORWAY_ARVIS_HOUSE),
        )

        if self.args.ruination_mode:
            space.write(
                field.SetEventWord(event_word.NARSHE_CHECKPOINT, NUM_HEALS)
            )  # [E8 02 03 0]

    def mod(self):
        self.terra_elder_scene_mod()
        self.security_checkpoint_mod()
        self.shop_mod()

        if self.args.ruination_mode:
            self.ruination_mod()

    def end_terra_scenario(self):
        # delete the end of terra's scenario event in arvis' house
        self.maps.delete_event(0x01e, 66, 35)

        # also put a return at the beginning of it just to be safe
        space = Reserve(0xcb3fa, 0xcb3ff, "banon's party reaches end in 3 scenarios", field.NOP())
        space.write(field.Return())

    def terra_elder_scene_mod(self):
        space = Reserve(0xc7083, 0xc7096, "narshe wob left trigger scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())
        space = Reserve(0xc7097, 0xc70aa, "narshe wob right trigger scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())

        # NOTE: the end of this space is where the soldiers are removed from imperial base near sealed gate
        space = Reserve(0xc70ab, 0xc72b9, "narshe wob scene where terra agrees to open sealed gate", field.NOP())
        space.write(field.Return())

    def security_checkpoint_mod(self):
        # remove explanation event and use the 0x2d8 flag bit for objective condition instead
        space = Reserve(0xcda09, 0xcda0f, "narshe wob security checkpoint explanation", field.NOP())
        space.write(field.Return())

        Free(0xcda10, 0xcda49)  # explanation event

        src = [
            Read(0xce3fa, 0xce3fd), # set first checkpoint event word to 0

            # return if checkpoint event not started (i.e. came in from the exit)
            field.ReturnIfEventBitClear(event_bit.multipurpose_map(0)),

            field.SetEventBit(event_bit.FINISHED_NARSHE_CHECKPOINT),
            field.CheckObjectives(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "narshe wob security checkpoint check objectives")
        check_objectives = space.start_address

        space = Reserve(0xce3fa, 0xce3fd, "narshe wob security checkpoint clear first event word", field.NOP())
        space.write(
            field.Call(check_objectives),
        )

    def shop_mod(self):
        # do not change shops after defeating cranes, always use ones after cranes
        space = Reserve(0xcd253, 0xcd258, "narshe wob weapon shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd25c)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd268, 0xcd26d, "narshe wob armor shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd271)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd27d, 0xcd282, "narshe wob relic shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd286)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )
        space = Reserve(0xcd292, 0xcd297, "narshe wob item shop defeated cranes branch")
        space.add_label("INVOKE_SHOP", 0xcd29b)
        space.write(
            field.Branch("INVOKE_SHOP"),
        )

    def ruination_mod(self):
        school_map_id = 0x068

        # (1) Change destination of school door to esper gate
        school_door_id = 392
        school_door = self.maps.get_exit(school_door_id)  # (0x068, 108, 53)
        school_door.dest_map = 0x0da
        school_door.dest_x = 55
        school_door.dest_y = 30

        # (2) Make the bucket provide a limited number of heals
        NARSHE_DIALOG_IDS = [i for i in range(1460, 1470)]
        # Based on Dragon number src: see e.g. CC/1F9F
        # Could use this memory space if needed  [0xc1f9f -- 0xc2047]
        # Could also use dragon dialogs:  [1498 -- 1506]
        # It turns out AtmaTek already used all the free event words (for CHARACTERS, ESPERS, CHECKS, DRAGONS, CID HEALTH, and CORAL).
        # How are 0x0 (CHECKPOINT_BANQUET) and 0x1 (NARSHE_CHECKPOINT) used?  just in vanilla code.
        # If this mode doesn't include the checkpoint, we can use 0x1.
        drink_query_ids = []
        drink_src = []
        pot_heal_address = 0xc33ae
        for i in range(NUM_HEALS):
            this_id = NARSHE_DIALOG_IDS.pop()
            drink_query_ids.append(this_id)
            this_num = NUM_HEALS - i
            num_drinks_line = "<line>(" + str(this_num) + " drink" + ["s", ""][[True, False].index(this_num != 1)] + " left)"
            self.dialogs.set_text(this_id, "Drink from the bucket?" + num_drinks_line + "<line><choice> Yes<line><choice> No<end>")
            drink_src += [
                field.BranchIfEventWordLess(event_word.NARSHE_CHECKPOINT, this_num, "LESS_"+str(this_num)),
                field.DialogBranch(this_id, "HEAL", "RETURN"),
                "LESS_" + str(this_num),
            ]

        empty_id = NARSHE_DIALOG_IDS.pop()
        self.dialogs.set_text(empty_id, "The bucket is empty.<end>")
        drink_src += [
            field.Dialog(empty_id),
            "RETURN",
            field.Return(),
            "HEAL",
            field.Call(pot_heal_address),
            field.DecrementEventWord(event_word.NARSHE_CHECKPOINT),  # = [EA 02 01 0]
            field.Return()
        ]
        space = Write(Bank.CC, drink_src, "Limited use pot heal")

        pot_npc_id = 0x12
        pot_npc = self.maps.get_npc(school_map_id, pot_npc_id)
        pot_npc.event_address = space.start_address - EVENT_CODE_START

        # (3) Update the NPC dialogs & actions
        counter_npc_id = 0x10
        right_npc_id = 0x11
        left_npc_id = 0x13
        ghost_npc_id = 0x14
        mid_npc_id = 0x15

        self.dialogs.set_text(601, "We can no longer replenish our supplies. Please use this water wisely.<end>")

        info_id = 0x0258  # NARSHE_DIALOG_IDS.pop()
        self.dialogs.set_text(info_id, "Welcome. We have little we can offer you, but will help as much as we can." +
                              "<page>Each door leads to a path through the ruins." +
                              "<page>As you travel, you'll find green warp points. If you're in danger, use them to return to the Esper world." +
                              "<page>All roads lead to Kefka's tower. But you'll need to send a team down each path to defeat him." +
                              "<page>Speak to the ghost to reform your party.<end>")
        space = Reserve(0xc33a2, 0xc33a4, "make npc dialog the same in both worlds")
        space.write(field.Dialog(info_id, top_of_screen=False))

        reform_id = NARSHE_DIALOG_IDS.pop()
        self.dialogs.set_text(reform_id, "<choice> Reform parties.<line><choice> Unequip those not in party.<line><choice> Unequip all members.<line><choice> Don't do a thing!<end>")
        reform_id_2 = NARSHE_DIALOG_IDS.pop()
        self.dialogs.set_text(reform_id_2,
                              "How many parties?<line><choice> 1<line><choice> 2<line><choice> never mind<end>")
        reform_id_3 = NARSHE_DIALOG_IDS.pop()
        self.dialogs.set_text(reform_id_3,
                              "How many parties?<line><choice> 1      <choice> 2<line><choice> 3      <choice> never mind<end>")

        from instruction.field.functions import REFRESH_CHARACTERS_AND_SELECT_PARTY, \
            REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES, REFRESH_CHARACTERS_AND_SELECT_THREE_PARTIES, \
            REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES

        src_party1 = [
            field.SetPartyMap(1, school_map_id),  # Set party 1 on this map
            field.SetParty(1),  # Make party 1 the active party
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=109, y=49),
                            field_entity.Turn(direction.RIGHT),
                            ),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.Return()
        ]
        space = Write(Bank.CA, src_party1, "Place party 1 reform school")
        place_party_1_addr = space.start_address

        src_party2 = [
            field.SetParty(2),  # Make party 2 the active party
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=110, y=48),
                            field_entity.Turn(direction.DOWN),
                            ),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.Return()
        ]
        space = Write(Bank.CA, src_party2, "Place party 2 reform school")
        place_party_2_addr = space.start_address

        src_party3 = [
            field.SetParty(3),  # Make party 3 the active party
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=110, y=50),
                            field_entity.Turn(direction.UP),
                            ),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.Return()
        ]
        space = Write(Bank.CA, src_party3, "Place party 3 reform school")
        place_party_3_addr = space.start_address

        reform_src = [
            "START_OVER",
            field.DialogBranch(reform_id, dest1 = "REFORM", dest2 = 0xc359d, dest3 = 0xc351e, dest4 = field.RETURN),
            "REFORM",
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 2, "1_PARTY"),
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 3, "NOT_3_PARTIES"),
            field.DialogBranch(reform_id_3, dest1="1_PARTY", dest2="2_PARTIES", dest3="3_PARTIES", dest4=field.RETURN),
            "NOT_3_PARTIES",
            field.DialogBranch(reform_id_2, dest1="1_PARTY", dest2="2_PARTIES", dest3=field.RETURN),
            "1_PARTY",
            field.Call(REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_PARTY),
            # Place on map & load map
            field.Call(place_party_1_addr),
            field.FadeInScreen(),
            field.WaitForFade(),
            field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),  # Disable y-party switching
            field.Return(),
            "2_PARTIES",
            field.Call(REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),
            # Place on map & load map
            field.SetPartyMap(1, school_map_id),  # Set party 1 on this map
            field.SetPartyMap(2, school_map_id),  # Set party 2 on this map
            field.Call(place_party_2_addr),
            field.Call(place_party_1_addr),
            field.FadeInScreen(),
            field.WaitForFade(),
            field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            field.FreeMovement(),
            field.Return(),
            "3_PARTIES",
            field.Call(REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_THREE_PARTIES),
            # Place on map & load map
            field.SetPartyMap(1, school_map_id),  # Set party 1 on this map
            field.SetPartyMap(2, school_map_id),  # Set party 2 on this map
            field.SetPartyMap(3, school_map_id),  # Set party 3 on this map
            field.Call(place_party_3_addr),
            field.Call(place_party_2_addr),
            field.Call(place_party_1_addr),
            field.FadeInScreen(),
            field.WaitForFade(),
            field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            field.FreeMovement(),
            field.Return(),
        ]
        space = Write(Bank.CA, reform_src, "Custom split parties npc action")

        ghost_npc = self.maps.get_npc(school_map_id, ghost_npc_id)
        ghost_npc.event_address = space.start_address - EVENT_CODE_START
        ghost_npc.event_byte = pot_npc.event_byte
        ghost_npc.event_bit = pot_npc.event_bit
        ghost_npc.movement = 0
        ghost_npc.x = 110
        ghost_npc.direction = direction.LEFT

