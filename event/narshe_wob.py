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

        # (1a) Delete event tile that handles WOB vs WOR exit (always go to same place)
        self.maps.delete_event(school_map_id, school_door.x, school_door.y)

        # (2) Make the bucket provide a limited number of heals
        NARSHE_DIALOG_IDS = [i for i in range(1462, 1471)]  # 1461 used by Figaro Castle inn
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
        from constants.entities import CHARACTER_COUNT

        # Build a safe version of REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES that
        # preserves party assignments for away characters (character_available cleared).
        remove_available_src = []
        for char in range(CHARACTER_COUNT):
            remove_available_src += [
                field.BranchIfEventBitClear(event_bit.character_available(char), f"SKIP_{char}"),
                field.RemoveCharacterFromParties(char),
                f"SKIP_{char}",
            ]
        remove_available_src += [field.Return()]
        space = Write(Bank.CA, remove_available_src, "Remove available characters from parties (preserve away)")
        remove_available_addr = space.start_address

        # Position subroutines: position PARTY0 at each location.
        # These do NOT include SetParty/SetPartyMap - the caller handles those
        # dynamically based on which party slots are free.
        src_pos_center = [
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
        space = Write(Bank.CA, src_pos_center, "Position party at center (reform school)")
        pos_center_addr = space.start_address

        src_pos_upper_right = [
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
        space = Write(Bank.CA, src_pos_upper_right, "Position party at upper-right (reform school)")
        pos_upper_right_addr = space.start_address

        src_pos_lower_right = [
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
        space = Write(Bank.CA, src_pos_lower_right, "Position party at lower-right (reform school)")
        pos_lower_right_addr = space.start_address

        reform_src = [
            "START_OVER",
            field.DialogBranch(reform_id, dest1="REFORM", dest2=0xc359d, dest3=0xc351e, dest4=field.RETURN),

            # === Determine max new parties (3 - away_count) capped by CHARACTERS_AVAILABLE ===
            "REFORM",
            # Check away parties to determine free slot count
            field.BranchIfEventBitSet(event_bit.PARTY_1_AWAY, "CHECK_P1_AWAY"),
            field.BranchIfEventBitSet(event_bit.PARTY_2_AWAY, "CHECK_P2_AWAY_NO_P1"),
            field.BranchIfEventBitSet(event_bit.PARTY_3_AWAY, "MAX_2_NEW"),
            field.Branch("MAX_3_NEW"),

            "CHECK_P1_AWAY",  # P1 is away
            field.BranchIfEventBitSet(event_bit.PARTY_2_AWAY, "MAX_1_NEW"),  # P1+P2 away
            field.BranchIfEventBitSet(event_bit.PARTY_3_AWAY, "MAX_1_NEW"),  # P1+P3 away
            field.Branch("MAX_2_NEW"),  # only P1 away

            "CHECK_P2_AWAY_NO_P1",  # P2 away, P1 not
            field.BranchIfEventBitSet(event_bit.PARTY_3_AWAY, "MAX_1_NEW"),  # P2+P3 away
            # fallthrough: only P2 away

            "MAX_2_NEW",  # exactly 1 away -> at most 2 new parties
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 2, "1_PARTY"),
            field.DialogBranch(reform_id_2, dest1="1_PARTY", dest2="2_PARTIES", dest3=field.RETURN),

            "MAX_1_NEW",  # 2 parties away -> force 1 new party
            field.Branch("1_PARTY"),

            "MAX_3_NEW",  # 0 away -> up to 3 new parties (original logic)
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 2, "1_PARTY"),
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 3, "MAX_3_NOT_ENOUGH_FOR_3"),
            field.DialogBranch(reform_id_3, dest1="1_PARTY", dest2="2_PARTIES", dest3="3_PARTIES", dest4=field.RETURN),
            "MAX_3_NOT_ENOUGH_FOR_3",
            field.DialogBranch(reform_id_2, dest1="1_PARTY", dest2="2_PARTIES", dest3=field.RETURN),

            # === 1 PARTY: select 1 party, remap to first free slot ===
            "1_PARTY",
            field.Call(remove_available_addr),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_PARTY),
            field.RemapPartiesToFreeSlots(0),
            # Determine first free slot for SetPartyMap/SetParty
            field.BranchIfEventBitClear(event_bit.PARTY_1_AWAY, "1P_SLOT1"),
            field.BranchIfEventBitClear(event_bit.PARTY_2_AWAY, "1P_SLOT2"),
            # P1 and P2 both away -> use slot 3
            field.SetPartyMap(3, school_map_id),
            field.SetParty(3),
            field.Branch("1P_PLACE"),
            "1P_SLOT2",
            field.SetPartyMap(2, school_map_id),
            field.SetParty(2),
            field.Branch("1P_PLACE"),
            "1P_SLOT1",
            field.SetPartyMap(1, school_map_id),
            field.SetParty(1),
            # fallthrough
            "1P_PLACE",
            field.Call(pos_center_addr),
            field.FadeInScreen(),
            field.WaitForFade(),
            # Skip clear y-party switching if parties are away
            field.BranchIfAny([event_bit.PARTY_1_AWAY, True, event_bit.PARTY_2_AWAY, True, event_bit.PARTY_3_AWAY, True], "FREE_AND_RETURN"),
            field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            "FREE_AND_RETURN",
            field.FreeMovement(),
            field.Return(),

            # === 2 PARTIES: select 2 parties, remap to free slots ===
            "2_PARTIES",
            field.Call(remove_available_addr),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),
            field.RemapPartiesToFreeSlots(0),
            # Branch based on which party is away for correct slot assignment
            field.BranchIfEventBitSet(event_bit.PARTY_1_AWAY, "2P_P1_AWAY"),
            field.BranchIfEventBitSet(event_bit.PARTY_2_AWAY, "2P_P2_AWAY"),
            # P3 away or none -> free slots 1, 2
            field.SetPartyMap(1, school_map_id),
            field.SetPartyMap(2, school_map_id),
            field.SetParty(2),
            field.Call(pos_upper_right_addr),
            field.SetParty(1),
            field.Call(pos_center_addr),
            field.Branch("2P_FINISH"),

            "2P_P1_AWAY",  # P1 away -> free slots 2, 3
            field.SetPartyMap(2, school_map_id),
            field.SetPartyMap(3, school_map_id),
            field.SetParty(3),
            field.Call(pos_upper_right_addr),
            field.SetParty(2),
            field.Call(pos_center_addr),
            field.Branch("2P_FINISH"),

            "2P_P2_AWAY",  # P2 away -> free slots 1, 3
            field.SetPartyMap(1, school_map_id),
            field.SetPartyMap(3, school_map_id),
            field.SetParty(3),
            field.Call(pos_upper_right_addr),
            field.SetParty(1),
            field.Call(pos_center_addr),
            # fallthrough

            "2P_FINISH",
            field.FadeInScreen(),
            field.WaitForFade(),
            field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            field.FreeMovement(),
            field.Return(),

            # === 3 PARTIES (only reachable when 0 away - no remap needed) ===
            "3_PARTIES",
            field.Call(remove_available_addr),
            field.Call(REFRESH_CHARACTERS_AND_SELECT_THREE_PARTIES),
            field.SetPartyMap(1, school_map_id),
            field.SetPartyMap(2, school_map_id),
            field.SetPartyMap(3, school_map_id),
            field.SetParty(3),
            field.Call(pos_lower_right_addr),
            field.SetParty(2),
            field.Call(pos_upper_right_addr),
            field.SetParty(1),
            field.Call(pos_center_addr),
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

        # (3b) NPC clue scripts: each branch NPC cycles through up to 3 clues
        # about which areas are on their branch.
        # AreasUsed is set by events.py ruination_mod() before event.mod() runs.
        areas_used = getattr(self.args, 'ruination_areas_used', {})

        # Map internal area names to player-friendly display names
        # Done: replace the names with clue dialogs customized to each area
        AREA_DISPLAY_NAMES = {
            'Doma': 'Doma Castle',
            'UmarosCave': "Umaro's Cave",
            'EsperMountain': 'Esper Mountain',
            'PhantomTrain': 'Phantom Train',
            'SealedGate': 'Sealed Gate',
            'SouthFigaroCave': 'South Figaro Cave',
            'ReturnersHideout': "Returner's Hideout",
            'AncientCastle': 'Ancient Castle',
            'Jidoor': "Owzer's Mansion",
            'VeldtCave': 'Veldt Cave',
            'CrescentMtn': 'Crescent Mountain',
            'BarenFalls': 'Baren Falls',
            'Vector': 'Magitek Factory',
            'DarylsTomb': "Daryl's Tomb",
            'ZoneEater': 'Zone Eater',
            'MtKolts': 'Mt. Kolts',
            'Narshe': 'Narshe Mines',
            'Zozo': 'Zozo',
            'ZozoTower': 'Zozo Tower',
            'MtZozo': 'Mt. Zozo',
            'BurningHouse': 'Burning House',
            'SouthFigaro': 'South Figaro',
            'GauFatherHouse': "Gau's Father's House",
            'Thamasa': 'Thamasa',
            'Kohlingen': 'Kohlingen',
            'Cid': "Cid's Island",
            'Mobliz': 'Mobliz',
            'Maranda': 'Maranda',
            'FanaticsTower': "Fanatic's Tower",
            'OperaHouse': 'Opera House',
            'EbotsRock': "Ebot's Rock",
            'Coliseum': 'Coliseum',
            'Tzen': 'Tzen',
            'Albrook': 'Albrook',
            'Veldt': 'Veldt',
            'Nikeah': 'Nikeah',
            'PhoenixCave': 'Phoenix Cave',
            'FloatingContinent': 'Floating Continent',
            'ImperialCamp': 'Imperial Camp',
            'FigaroCastle': 'Figaro Castle',
            'ImperialCastle': 'Imperial Castle',
        }

        AREA_CLUES = {
            'Doma': "After the end of the world,<line>I awoke all alone in Doma Castle.<page>When I would try to sleep there, demons would come for me… Oh! I don't want to remember that!<end>",
            'UmarosCave': "The air from this door sometimes smells… terrible!<end>",
            'EsperMountain': "Travelers describe a cave with ancient magical power.<end>",
            'PhantomTrain': "Sometimes late at night, I hear the sound of a train…<end>",
            'SealedGate': "I smell sulphur and the air is warm.<end>",
            'SouthFigaroCave': "Sometimes there's a rumbling sound, like tunneling through rock.<end>",
            'ReturnersHideout': "A Returner came floating up the river on a raft!<end>",
            'AncientCastle': "This cave seems to go deeper than the others.<end>",
            'Jidoor': "A rich man came through here, trying to buy 'pre-crisis art'.  Honestly!<end>",
            'VeldtCave': "A hunter came through, talking about dragons.<end>",
            'CrescentMtn': "Part of this path is under water.  I hope you can swim!<end>",
            'BarenFalls': "Do you hear the sound of rushing water?<end>",
            'Vector': "An imperial soldier scouted us. Are we in danger?<end>",
            'DarylsTomb': "The whole world is a tomb now.<end>",
            'ZoneEater': "The rock ahead seems unstable. Watch out for cave-ins!<end>",
            'MtKolts': "In this world, people can be more dangerous than monsters.<end>",
            'Narshe': "Beyond here, the wind blows endlessly.<end>",
            'Zozo': "We helped a man and he tried to rob us. Be careful!<end>",
            'ZozoTower': "Ramuh came to me in a dream. The espers may help you in your journey.<end>",
            'MtZozo': "Even in this ruined world, there is beauty.<end>",
            'BurningHouse': "Some fires from the end of the world never went out.<end>",
            'SouthFigaro': "We know some people survived. A visitor came from South Figaro!<end>",
            'GauFatherHouse': "A few loners still live out there.<end>",
            'Thamasa': "I found Thamasa in my explorations. They don't like outsiders, though.<end>",
            'Kohlingen': "I've heard Kohlingen survived.<end>",
            'Cid': "The red ocean stretches on endlessly…<end>",
            'Mobliz': "The world is littered with broken towns from the light of judgement.<end>",
            'Maranda': "I saw some pigeons flying down this path.<end>",
            'FanaticsTower': "Some “Cult of Kefka” members have built a tower on this road.<end>",
            'OperaHouse': "Do you hear... music?<end>",
            'EbotsRock': "These caves can be disorienting. Keep your bearings!<end>",
            'Coliseum': "A strange swordsman came through here looking for prizes and glory.<end>",
            'Tzen': "Tzen still stands, for now.<end>",
            'Albrook': "Albrook has survived war, occupation, now the end of the world.<end>",
            'Veldt': "On my travels I've seen monsters from all over the world.<end>",
            'Nikeah': "Nikeah's still sending out ships. Don't know if they've found anything.<end>",
            'PhoenixCave': "I hear a legendary treasure is hidden on this path.<end>",
            'FloatingContinent': "Memories of the crisis live on in the waking world.<end>",
            'ImperialCamp': "Everyone is struggling to survive, even the imperial army.<end>",
            'FigaroCastle': "Figaro Castle disappeared the day the world became…<line>unzipped…<end>",  # "Figaro Castle had an accident under the desert.<line>Don't know what happened to its people…<end>",
            'ImperialCastle': 'Good luck!<end>',
        }

        # Build per-branch area lists (up to 3 areas per branch for clues)
        branch_clue_areas = [[], [], []]
        for area_name, branch_id in areas_used.items():
            if branch_id in (0, 1, 2) and area_name in AREA_CLUES:    # AREA_DISPLAY_NAMES
                branch_clue_areas[branch_id].append(AREA_CLUES[area_name])   # AREA_DISPLAY_NAMES
        import random

        for bca in branch_clue_areas:
            # Shuffle them just in case
            random.shuffle(bca)

        # Use dialog IDs 602-625 (0x25A-0x271) for clue messages
        # 3 clue dialogs per branch × 3 branches = 9 dialogs
        # Branch 0: 602, 603, 604  |  Branch 1: 605, 606, 607  |  Branch 2: 608, 609, 610
        clue_dialog_ids = [[602, 603, 604], [605, 606, 607], [608, 609, 610]]

        for branch_id in range(3):
            areas = branch_clue_areas[branch_id]
            for clue_idx in range(3):
                dialog_id = clue_dialog_ids[branch_id][clue_idx]
                if clue_idx < len(areas):
                    clue = areas[clue_idx]
                    #self.dialogs.set_text(dialog_id, f"I've heard that {clue} lies down this path.<end>")  # replace generic hint with actual clues
                    self.dialogs.set_text(dialog_id, clue)
                else:
                    self.dialogs.set_text(dialog_id,
                        "That's all I know about this path.<end>")

        # multipurpose_map bits (cleared on map load, so cycle resets each visit):
        # Branch 0: bits 1, 2   Branch 1: bits 3, 4   Branch 2: bits 5, 6
        branch_cycle_bits = [
            (event_bit.multipurpose_map(1), event_bit.multipurpose_map(2)),
            (event_bit.multipurpose_map(3), event_bit.multipurpose_map(4)),
            (event_bit.multipurpose_map(5), event_bit.multipurpose_map(6)),
        ]

        # Event bit 0x1B0 = player facing UP when talking to NPC
        # Event bit 0x1B3 = player facing LEFT when talking to NPC
        FACING_UP = 0x1B0
        FACING_LEFT = 0x1B3

        def build_cycle_src(branch_id):
            """Build event script that cycles through 3 clue dialogs."""
            bit_a, bit_b = branch_cycle_bits[branch_id]
            d1, d2, d3 = clue_dialog_ids[branch_id]
            pfx = f"B{branch_id}_"
            return [
                # State check: (bit_a, bit_b) = (0,0) → clue 1, (1,0) → clue 2, (x,1) → clue 3
                field.BranchIfEventBitSet(bit_a, pfx + "STATE1"),
                field.BranchIfEventBitSet(bit_b, pfx + "STATE2"),
                # State 0: show clue 1, advance to state 1
                field.Dialog(d1),
                field.SetEventBit(bit_a),
                field.Return(),
                # State 1: show clue 2, advance to state 2
                pfx + "STATE1",
                field.BranchIfEventBitSet(bit_b, pfx + "STATE2"),
                field.Dialog(d2),
                field.ClearEventBit(bit_a),
                field.SetEventBit(bit_b),
                field.Return(),
                # State 2: show clue 3, reset to state 0
                pfx + "STATE2",
                field.Dialog(d3),
                field.ClearEventBit(bit_a),
                field.ClearEventBit(bit_b),
                field.Return(),
            ]

        # Reserve ROM space for all 3 NPC clue scripts in the school tutorial range.
        # CC/33E1-CC/350B (0xc33e1-0xc350b) = 299 bytes, replaces vanilla tutorial dialogs.
        space = Reserve(0xc33e1, 0xc350b, "NPC clue scripts for branches 0-2", field.NOP())

        # Branch 0 NPC (left_npc_id = 0x13): simple cycle through clues
        left_src = build_cycle_src(0)
        left_space = space.next_address
        space.write(left_src)

        left_npc = self.maps.get_npc(school_map_id, left_npc_id)
        left_npc.event_address = left_space - EVENT_CODE_START

        # Branch 1 NPC (mid_npc_id = 0x15): simple cycle through clues
        mid_src = build_cycle_src(1)
        mid_space = space.next_address
        space.write(mid_src)

        mid_npc = self.maps.get_npc(school_map_id, mid_npc_id)
        mid_npc.event_address = mid_space - EVENT_CODE_START

        # Branch 2 NPC (right_npc_id = 0x11): facing UP → supply line, facing LEFT → cycle clues
        right_cycle_src = build_cycle_src(2)
        right_src = [
            # Check facing direction: UP → supply line, LEFT → clue cycle
            field.BranchIfEventBitSet(FACING_UP, "SUPPLY_LINE"),
            field.BranchIfEventBitClear(FACING_LEFT, "SUPPLY_LINE"),
        ] + right_cycle_src + [
            "SUPPLY_LINE",
            field.Dialog(601),
            field.Return(),
        ]
        right_space = space.next_address
        space.write(right_src)

        right_npc = self.maps.get_npc(school_map_id, right_npc_id)
        right_npc.event_address = right_space - EVENT_CODE_START

        # (4) Modify room aesthetics
        # Change the music to "esper world" (song = 33)
        school_properties = self.maps.properties[school_map_id]
        school_properties.song = 33

        # Try palette animation for torch flicker effect
        # Value 0x7 is used by torch/fire maps (maps 136, 156, 373)
        # This may or may not work depending on palette color compatibility
        school_properties.paletteanimationindex = 0x7

        # Make it darker via entrance event with dark tint
        # Also restore away-party character availability when a party returns
        # Set all characters' talk-event pointers so party interaction works
        # after loading a saved game (field RAM pointers aren't preserved in saves).
        from event.ruination import set_party_interaction_pointers_src
        entrance_src = [
            field.TintBackground(field.Tint.NIGHT),
            field.RestoreActivePartyAvailable(),  # idempotent: no-op if party isn't away
        ]
        entrance_src += set_party_interaction_pointers_src()
        entrance_src += [field.Return()]
        space = Write(Bank.CA, entrance_src, "Narshe school ruination entrance event")
        self.maps.set_entrance_event(school_map_id, space.start_address - EVENT_CODE_START)

        # (4b) Add event tiles on the three classroom doors to mark away parties
        # When a party steps on these tiles, MarkActivePartyAway fires before the map exit
        from data.map_event import MapEvent

        away_src = [
            field.MarkActivePartyAway(),  # idempotent: sets PARTY_N_AWAY, clears character_available
            field.Return(),
        ]
        space = Write(Bank.CA, away_src, "Mark party away on branch door exit")
        away_event_addr = space.start_address - EVENT_CODE_START

        # Door coordinates from exits 393, 394, 395
        branch_door_coords = [(93, 45), (99, 45), (108, 45), (108, 53)]
        for x, y in branch_door_coords:
            new_event = MapEvent()
            new_event.x = x
            new_event.y = y
            new_event.event_address = away_event_addr
            self.maps.add_event(school_map_id, new_event)

        # (5) Reskin the whelk room (map 59, WoB mines) to use WoR mines palette
        # The ruin-whelk room uses map 59 (Narshe Northern Mines Main Hallway WoB) which has
        # a different palette than the WoR mines rooms the player encounters elsewhere.
        # Copy the palette from map 36 (Narshe Northern Mines 2F Inside WoR).
        whelk_map_id = 43
        whelk_properties = self.maps.properties[whelk_map_id]
        whelk_properties.paletteindex = 0x15  # ???
        whelk_properties.song = 79  # Dark World


