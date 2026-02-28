from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard

ENTRY_EVENT_CODE_ADDR = 0xc2bf0  # unused block in Rachel animation


class PhoenixCave(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle
        self.DOOR_RANDOMIZE = args.door_randomize_all or args.door_randomize_crossworld \
                              or args.door_randomize_dungeon_crawl or args.ruination_mode

    def name(self):
        return "Phoenix Cave"

    def character_gate(self):
        return self.characters.LOCKE

    def characters_required(self):
        return 2

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.locke_npc_id = 0x10
        self.locke_npc = self.maps.get_npc(0x139, self.locke_npc_id)

        if not (self.MAP_SHUFFLE or self.DOOR_RANDOMIZE):
            self.landing_mod()
        else:
            self.map_shuffle_mod()

        self.end_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)



    def landing_mod(self):
        self.need_more_characters_dialog = 2978
        self.dialogs.set_text(self.need_more_characters_dialog, "We need to find more allies.<end>")

        self.need_locke_dialog = 2981
        self.dialogs.set_text(self.need_locke_dialog, "We need to find Locke.<end>")

        src = [
            Read(0xa0405, 0xa0408),
            Read(0xa040c, 0xa0428),
        ]
        space = Write(Bank.CA, src, "phoenix cave enter")
        enter_phoenix_cave = space.start_address

        src = [
            field.LoadMap(0x01, direction.DOWN, default_music = False, x = 118, y = 156, fade_in = True, airship = True),
            vehicle.End(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "phoenix cave cancel landing")
        cancel_landing = space.start_address

        src = [
            field.Dialog(self.need_locke_dialog),
            field.Branch(cancel_landing),
        ]
        space = Write(Bank.CA, src, "phoenix cave no locke cancel")
        no_locke_cancel_landing = space.start_address

        src = [
            field.Dialog(self.need_more_characters_dialog),
            field.Branch(cancel_landing),
        ]
        space = Write(Bank.CA, src, "phoenix cave character requirements cancel")
        character_requirements_cancel_landing = space.start_address

        space = Reserve(0xa0405, 0xa0428, "phoenix cave landing checks", field.NOP())
        space.write(
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, self.characters_required(), character_requirements_cancel_landing),
            field.Branch(enter_phoenix_cave),
        )

    def end_mod(self):
        space = Reserve(0xc2b74, 0xc2b75, "phoenix cave pause before locke opens chest", field.NOP())
        space = Reserve(0xc2b82, 0xc2b84, "phoenix cave LOCKE!!", field.NOP())
        space = Reserve(0xc2b95, 0xc2b98, "phoenix cave you're all safe", field.NOP())
        space = Reserve(0xc2b9e, 0xc2ba0, "phoenix cave that looks like...", field.NOP())
        space = Reserve(0xc2ba5, 0xc2baf, "phoenix cave celes extra dialog", field.NOP())
        space = Reserve(0xc2bb6, 0xc2bbe, "phoenix cave i wasn't able to save rachel", field.NOP())

    def locke_holding_esper_mod(self):
        space = Reserve(0xc2b7f, 0xc2b81, "phoenix cave play magicite sound effect", field.NOP())
        space = Reserve(0xc2b99, 0xc2b9d, "phoenix cave show magicite", field.NOP())
        space = Reserve(0xc2ba1, 0xc2ba4, "phoenix cave hide magicite", field.NOP())

    def reward_mod(self, reward_instructions):
        src = []
        if self.args.character_gating:
            src += [
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            ]
        src += [
            Read(0xc2b3a, 0xc2b41), # create/show locke/npc
            field.Return(),
        ]
        space = Write(Bank.CC, src, "phoenix cave reward room npc check")
        npc_check = space.start_address

        space = Reserve(0xc2b3a, 0xc2b41, "phoenix cave reward room start event tile", field.NOP())
        space.write(
            field.Branch(npc_check),
        )

        src = [
            Read(0xc2b49, 0xc2b53), # event bits, magicite npc
            field.Return(),
        ]
        space = Write(Bank.CC, src, "phoenix cave begin reward")
        begin_reward = space.start_address

        space = Reserve(0xc2b49, 0xc2b53, "phoenix cave call begin reward", field.NOP())
        if self.args.character_gating:
            space.write(
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            )
        space.write(
            field.Call(begin_reward),
        )

        space = Reserve(0xc2bcb, 0xc2bef, "phoenix cave kohlingen rachel scenes", field.NOP())
        if self.MAP_SHUFFLE or self.DOOR_RANDOMIZE:
            space.write(
                reward_instructions,
                field.FinishCheck(),
                field.Call(self.exit_address),
                field.Return(),
            )
        else:
            space.write(
                reward_instructions,
                field.Call(field.RETURN_ALL_PARTIES_TO_FALCON),
                field.FinishCheck(),
                field.Return(),
            )

    def character_mod(self, character):
        self.locke_npc.sprite = character
        self.locke_npc.palette = self.characters.get_palette(character)

        self.locke_holding_esper_mod()

        self.reward_mod([
            field.RecruitCharacter(character),
        ])
        space = Reserve(0xc2b76, 0xc2b7e, "phoenix cave open phoenix chest", field.NOP())

    def esper_item_mod(self, esper_item_instructions):
        self.locke_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.locke_npc.palette = self.characters.get_palette(self.locke_npc.sprite)

        self.reward_mod([
            esper_item_instructions,
        ])

    def esper_mod(self, esper):
        self.esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.locke_holding_esper_mod()

        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def map_shuffle_mod(self):
        # (1a) Change the entry event to load the switchyard location
        self.entry_id = 1554
        src = [
            Read(0xa0405, 0xa0408),  # animate walk to railing
            field.HoldScreen(),
            field.Call(0xa0469),    # animate jumping off railing
            field.FreeScreen(),
            field.FadeOutScreen(),
            field.SetEventBit(event_bit.PHOENIX_CAVE_WARP_OPTION),
        ] + GoToSwitchyard(self.entry_id, map='field')

        space = Reserve(0xa0405, 0xa041b, 'Airship Jump to Phoenix Cave mod')
        space.write(src)
        #print('Phoenix Cave mod: added entry', [a.__str__() for a in src])

        # (1b) Add the switchyard event tile that handles entry to Phoenix Cave
        # Get the connecting exit
        self.parent_map = [0x001, 117, 162]  # [0x00b, 16, 8]  # Parent map falcon!? NO!  it breaks things!  world map: [0x001, 117, 162]
        self.exit_id = 1555
        if self.exit_id in self.maps.door_map.keys():
            if self.maps.door_map[1555] != 1554:   # Hack, don't update if connection is vanilla
                self.parent_map = self.maps.get_connection_location(self.exit_id)

        src_addl = []
        if self.parent_map[0] < 0x2:
            # The connection is on a world map.  Force update the parent map here
            src_addl += [field.SetParentMap(self.parent_map[0], direction.DOWN, self.parent_map[1], self.parent_map[2] - 1)]
        if self.parent_map[0] == 0 or self.args.door_randomize_crossworld or self.args.door_randomize_dungeon_crawl:
            # Update world.  Possibly redundant/unneeded?  Might be handled by create_exit_event()
            src_addl += [field.SetEventBit(event_bit.IN_WOR)]

        self.need_more_characters_dialog = 2978
        self.dialogs.set_text(self.need_more_characters_dialog, "We need to find more allies.<end>")

        self.split_party_dialog = 2981     # use same as need_locke_dialog, since it is unused.
        self.dialogs.set_text(self.split_party_dialog, "Split the party to proceed?<line><choice> Yes<line><choice> No<end>")

        pc_map_id = 0x13e  # Phoenix Cave exterior map

        # Common entry code: load map, animate landing
        src_entry_common = [
            field.LoadMap(pc_map_id, x=8, y=7, direction=direction.DOWN,
                              default_music=True, fade_in=False, entrance_event=True),
        ]
        src_entry_common += src_addl  # add parent map update, world bit update if necessary.
        src_entry_common += [
            field.HoldScreen(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=8, y=0),
                            ),
            field.ShowEntity(field_entity.PARTY0),
            field.FadeInScreen(),
            field.WaitForFade(),
            field.PlaySoundEffect(186),  # falling
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpeed(field_entity.Speed.FASTEST),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.AnimateFrontHandsUp(),
                            field_entity.Move(direction=direction.DOWN, distance=7),
                            field_entity.AnimateKneeling(),
                            field_entity.EnableWalkingAnimation(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL)
                            ),
            field.PlaySoundEffect(181),  # landing
            field.Pause(0.5),  # 30 units (0.5 sec)
            field.FreeScreen(),
        ]

        if self.args.ruination_mode:
            src = list(src_entry_common)
            src += self._ruination_entry_src(pc_map_id)
        else:
            src = list(src_entry_common)
            src += [
                # Handle branching & dialog
                field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, self.characters_required(), "NEED_MORE_CHARACTERS"),
                field.DialogBranch(self.split_party_dialog, "SPLIT_PARTY", "NO_SPLIT_PARTY"),
                "NEED_MORE_CHARACTERS",
                field.Dialog(self.need_more_characters_dialog),
                "NO_SPLIT_PARTY",
                field.Return(),
                "SPLIT_PARTY",
                field.Call(0xacbaf),  # Recover party in advance of party switch
                field.SelectParties(2, clear_party=True),
                field.HoldScreen(),
                field.SetPartyMap(1, pc_map_id),
                field.SetPartyMap(2, pc_map_id),
                field.SetParty(2),            # Make party 2 the active party
                field.RefreshEntities(),
                field.UpdatePartyLeader(),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.SetPosition(x=6, y=7),
                                field_entity.AnimateKneeling()
                                ),
                field.ShowEntity(field_entity.PARTY0),
                field.UpdatePartyLeader(),
                field.SetParty(1),
                field.RefreshEntities(),
                field.UpdatePartyLeader(),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.SetPosition(x=8, y=7),
                                field_entity.AnimateKneeling()
                                ),
                field.ShowEntity(field_entity.PARTY0),
                field.UpdatePartyLeader(),
                field.FadeInScreen(),
                field.WaitForFade(),
                field.FreeScreen(),
                field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
                field.FreeMovement(),
                field.Return()
            ]

        # Write entry code. Ruination mode is too large for the 122-byte reserve,
        # so write to Bank.CC and branch from the reserved address.
        if self.args.ruination_mode:
            entry_space = Write(Bank.CC, src, "Phoenix Cave ruination entry code")
            space = Reserve(ENTRY_EVENT_CODE_ADDR, ENTRY_EVENT_CODE_ADDR + 121, "Phoenix Cave entry code modified")
            space.write(field.Branch(entry_space.start_address))
        else:
            space = Reserve(ENTRY_EVENT_CODE_ADDR, ENTRY_EVENT_CODE_ADDR + 121, "Phoenix Cave entry code modified")
            space.write(src)

        # The Switchyard event needs to be a straight LoadMap call.  We will write one on the assumption that it is overwritten correctly.
        #src = [field.Branch(ENTRY_EVENT_CODE_ADDR)]
        src = [
            field.LoadMap(0x13e, x=8, y=7, direction=direction.DOWN,
                          default_music=True, fade_in=True, entrance_event=True),  # Failsafe
            field.Return()
        ]
        AddSwitchyardEvent(self.entry_id, self.maps, src=src)


        # (2a) modify the exit from phoenix cave:
        # hook exit event @ CC/20E5:
        #       CC/20E5 check to make sure facing hook & A is pressed
        # 		CC/20ED animation...
        # 		CC/2109 reform party...
        # 		CC/2143: 6B    Load map $000B (Falcon, upper deck (general use / with Daryl / buried / homing pigeon)) instantly, (upper bits $2000), place party at (16, 8), facing down
        # 		CC/215D: FE    Return

        # Redo party starts at 0xc2109, but this is also called by warp out of KT
        # WC rewrites this in airship.return_to_airship().  We follow that data here, but do everything before the LoadMap.
        if self.args.ruination_mode:
            # Ruination mode: skip party reform, just clear switch bits and exit.
            # Parties remain split — recombination handled elsewhere.
            src_exit = [
                field.ClearEventBit(0x2a2),   # Party 1 is standing on a switch in Phoenix Cave 1
                field.ClearEventBit(0x2a6),   # Party 2 is standing on a switch in Phoenix Cave 1
                field.ClearEventBit(0x2a3),   # Party 1 is standing on a switch in Phoenix Cave 2
                field.ClearEventBit(0x2a7),   # Party 2 is standing on a switch in Phoenix Cave 2
                field.RefreshEntities(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        else:
            # Add check to see if there is only one party, and don't Reform Party if so.
            src_exit = [
                field.BranchIfEventBitClear(event_bit.ENABLE_Y_PARTY_SWITCHING, "SKIP_PARTY_REFORM"),
                field.SetParty(1),
                field.Call(field.REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES),
                field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),
                field.UpdatePartyLeader(),
                field.ShowEntity(field_entity.PARTY0),
                field.RefreshEntities(),
                field.ClearEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
                "SKIP_PARTY_REFORM",
                field.ClearEventBit(0x2a2),   # Party 1 is standing on a switch in Phoenix Cave 1
                field.ClearEventBit(0x2a6),   # Party 2 is standing on a switch in Phoenix Cave 1
                field.ClearEventBit(0x2a3),   # Party 1 is standing on a switch in Phoenix Cave 2
                field.ClearEventBit(0x2a7),   # Party 2 is standing on a switch in Phoenix Cave 2
                field.RefreshEntities(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        space = Write(Bank.CC, src_exit, "Exit From Phoenix Cave")
        self.exit_address = space.start_address


        # (2b) Add the switchyard tile that handles exit to the Falcon
        # CC/2143: 6B    Load map $000B (Falcon, upper deck (general use / with Daryl / buried / homing pigeon)) instantly,
        # (upper bits $2000), place party at (16, 8), facing down
        src = [
            field.LoadMap(map_id=0x00b, x=16, y=8, direction=direction.LEFT,
                              default_music=True, fade_in=True, entrance_event=True),
            field.SetEventBit(event_bit.IN_WOR),
            field.Return()
        ]
        AddSwitchyardEvent(self.exit_id, self.maps, src=src)

        # Update hook event
        src_hook = [
            Read(0xc20ed, 0xc2108),  # animation of the exit on the hook
            field.FreeScreen(),
            field.Branch(self.exit_address),
        ]
        space = Write(Bank.CC, src_hook, "Phoenix Cave hook exit update")
        hook_event = self.maps.get_event(0x13e, 5, 6)  # hook event tile at [0x13e, 5, 6]
        hook_event.event_address = space.start_address - EVENT_CODE_START

        # Update sparkle event
        #sparkle_event = self.maps.get_event(0x139, 14, 47)
        #sparkle_event.event_address = space.start_address - EVENT_CODE_START
        space = Reserve(0xc216a, 0xc216d, "Phoenix Cave sparkle exit update")
        space.write(field.Call(self.exit_address))

        # The check complete exit event will be handled in self.reward_mod()

        # since we're only warping out of non-PC locations, we can just load the Falcon
        src_warp = [
            field.LoadMap(map_id=0x00b, x=16, y=8, direction=direction.LEFT,
                          default_music=True, fade_in=True, entrance_event=True),
            field.Return()
        ]
        warp_space = Write(Bank.CC, src_warp, "Repurposed PC warp code")

        space = Reserve(0xc1001, 0xc1004, 'Call Phoenix Cave warp mod')
        space.write(field.Call(warp_space.start_address))
        self.warps.add_warp(event_bit.PHOENIX_CAVE_WARP_OPTION, space.start_address)

    def _ruination_entry_src(self, pc_map_id):
        """Build the ruination-specific portion of the Phoenix Cave entry event.
        Appended after the common landing animation code.

        Flow:
        1. RestoreActivePartyAvailable clears AWAY bit explicitly
        2. SetupBranchRecruit(0x0F) restricts available to current party only (no recruit)
        3. Check conditions: CHARACTERS_AVAILABLE >= 2 AND at most 1 party away
        4. If conditions met: ask player, split into 2 parties with RemapPartiesToFreeSlots(2)
        5. If not: FinalizeBranchRecruit to undo, then free movement
        """
        return [
            # Setup: clear current party's AWAY bit, then restrict available to current party.
            field.RestoreActivePartyAvailable(),
            field.SetupBranchRecruit(0x0f),

            # Condition 1: current party has >= 2 characters
            # (CHARACTERS_AVAILABLE now reflects only the current party after Setup)
            field.BranchIfEventWordLess(event_word.CHARACTERS_AVAILABLE, 2, "NO_SPLIT_UNDO"),

            # Condition 2: at most 1 party away (need 2 free slots for the split).
            # RestoreActivePartyAvailable already cleared the current party's AWAY bit,
            # so these checks are purely about OTHER away parties.
            field.BranchIfEventBitClear(event_bit.PARTY_1_AWAY, "P1_OK"),
            field.BranchIfEventBitSet(event_bit.PARTY_2_AWAY, "NO_SPLIT_UNDO"),
            field.BranchIfEventBitSet(event_bit.PARTY_3_AWAY, "NO_SPLIT_UNDO"),
            "P1_OK",
            field.BranchIfEventBitClear(event_bit.PARTY_2_AWAY, "P2_OK"),
            field.BranchIfEventBitSet(event_bit.PARTY_3_AWAY, "NO_SPLIT_UNDO"),
            "P2_OK",

            # Both conditions met — ask the player
            field.DialogBranch(self.split_party_dialog, "SPLIT_PARTY", "NO_SPLIT_UNDO"),

            # Player declined or conditions not met: undo Setup and proceed with 1 party
            "NO_SPLIT_UNDO",
            # NOTE: this does NOT correctly undo the setup!  Testing with Party1, characters in Party1 remain marked
            # in "characters_available", and # characters available is not decremented.
            field.FinalizeBranchRecruit(),
            field.FreeMovement(),
            field.Return(),

            # Player chose to split
            "SPLIT_PARTY",
            #field.Call(0xacbaf),  # Recover party HP/MP before party select
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),
            field.RemapPartiesToFreeSlots(2),
            field.FinalizeBranchRecruit(),

            # Determine which 2 slots are occupied based on AWAY bits.
            # After RestoreActivePartyAvailable cleared the current party's AWAY bit, the only possible
            # away party is one OTHER party. RemapPartiesToFreeSlots(2) mapped to free slots:
            #   P1 away → free=[2,3], P2 away → free=[1,3], P3 away or none → free=[1,2]
            # NOTE: This approach does not work if a party is formed but remains in the School!  Need another approach.
            # We could claim more event_bits:  PARTY_N_FORMED, e.g. This might simplify other tasks too.
            field.HoldScreen(),
            field.BranchIfEventBitSet(event_bit.PARTY_1_AWAY, "SLOTS_2_3"),
            field.BranchIfEventBitSet(event_bit.PARTY_2_AWAY, "SLOTS_1_3"),

            # Party 3 away or no party away → slots 1, 2
            field.SetPartyMap(1, pc_map_id),
            field.SetPartyMap(2, pc_map_id),
            field.SetParty(2),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=6, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.SetParty(1),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=8, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.Branch("SPLIT_FINISH"),

            # Party 1 away → slots 2, 3
            "SLOTS_2_3",
            field.SetPartyMap(2, pc_map_id),
            field.SetPartyMap(3, pc_map_id),
            field.SetParty(3),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=6, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.SetParty(2),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=8, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.Branch("SPLIT_FINISH"),

            # Party 2 away → slots 1, 3
            "SLOTS_1_3",
            field.SetPartyMap(1, pc_map_id),
            field.SetPartyMap(3, pc_map_id),
            field.SetParty(3),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=6, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            field.SetParty(1),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=8, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),
            # fallthrough

            "SPLIT_FINISH",
            field.FadeInScreen(),
            field.WaitForFade(),
            field.FreeScreen(),
            field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            field.FreeMovement(),
            field.Return(),
        ]

    @staticmethod
    def entrance_door_patch():
        # self-contained code to be called in door rando after entering Doma WoB
        # to be used in event_exit_info.entrance_door_patch()
        return [field.Branch(ENTRY_EVENT_CODE_ADDR)]


