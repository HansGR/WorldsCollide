from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard

ENTRY_EVENT_CODE_ADDR = 0xc2bf0  # unused block in Rachel animation


class PhoenixCave(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle
        self.DOOR_RANDOMIZE = self.doors_touched(rooms=('branch-pc',)) or args.ruination_mode

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

        if self.args.ruination_mode:
            self.ruination_tile_mod()

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

        if self.args.ruination_mode:
            # In Ruination mode, we don't reform the party on exit.  Do it here.
            reward_scr = [field.RecruitAndSelectParty(character)]
        else:
            reward_scr = [field.RecruitCharacter(character)]
        self.reward_mod(reward_scr)
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
        1. Check conditions: THREE_PARTIES_CREATED is clear AND current party has >= 2 characters
        2. If conditions met: ask player, split into 2 parties with RemapPartiesToFreeSlots(2)
        3. If not: free movement
        """
        return [
            # Condition 1: three parties not already created
            field.BranchIfEventBitSet(event_bit.THREE_PARTIES_CREATED, "NO_SPLIT"),

            # Condition 2: current party has >= 2 characters
            field.BranchIfPartySize(1, "NO_SPLIT"),

            # Both conditions met — ask the player
            field.DialogBranch(self.split_party_dialog, "SPLIT_PARTY", "NO_SPLIT"),

            # Conditions not met or player declined
            "NO_SPLIT",
            field.FreeMovement(),
            field.Return(),

            # Player chose to split
            "SPLIT_PARTY",
            field.SetupBranchRecruit(0x2f),  # Setup for 2 parties
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES),

            # Place the two parties on the map. (Parties should always be Party1 and Party2 after SetupBranchRecruit.)
            field.HoldScreen(),

            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=8, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),

            field.SetPartyMap(2, pc_map_id),
            field.SetParty(2),

            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetPosition(x=6, y=7),
                            field_entity.AnimateKneeling()),
            field.ShowEntity(field_entity.PARTY0),
            field.UpdatePartyLeader(),

            # Finalize the party split
            field.FinalizeBranchRecruit(),

            # Complete animation
            field.FadeInScreen(),
            field.WaitForFade(),
            field.FreeScreen(),
            field.SetEventBit(event_bit.ENABLE_Y_PARTY_SWITCHING),
            field.FreeMovement(),
            field.Return(),
        ]

    def ruination_tile_mod(self):
        # Modify the tile events to activate if touched by party 3 (default: party 1/2 only).

        # (1a) Remove party check on spikes 1
        space = Reserve(0xc27b3, 0xc27d6, "Phoenix cave Spikes #1 edit", field.NOP())  # CC/27B3 -- CC/27D6
        spikes_src = [
            field.ReturnIfAny([0x2a4, True, 0x1b5, True]),
            field.Call(0xc27d7),  # Do spikes event
            field.SetEventBit(0x1b5),
            field.Return(),
        ]
        space.write(spikes_src)

        # (1b) Remove party check on spikes 2
        space = Reserve(0xc28e7, 0xc290a, "Phoenix cave Spikes #2 edit", field.NOP())  # CC/28E7 -- CC/290A
        spikes_src = [
            field.ReturnIfAny([0x2a9, True, 0x1b5, True]),
            field.Call(0xc27d7),  # Do spikes event
            field.SetEventBit(0x1b5),
            field.Return(),
        ]
        space.write(spikes_src)

        # (1c) Remove party check on spikes 3
        space = Reserve(0xc2963, 0xc2986, "Phoenix cave Spikes #3 edit", field.NOP())  # CC/2963 -- CC/2986
        spikes_src = [
            field.ReturnIfAny([0x2d1, True, 0x1b5, True]),
            field.Call(0xc27d7),  # Do spikes event
            field.SetEventBit(0x1b5),
            field.Return(),
        ]
        space.write(spikes_src)

        # (1d) Remove party check on spikes 4
        space = Reserve(0xc286a, 0xc2889, "Phoenix cave Spikes #3 edit", field.NOP())  # CC/286A--CC/2889
        spikes_src = [
            field.ReturnIfAny([0x1b5, True]),
            field.Call(0xc27d7),  # Do spikes event
            field.SetEventBit(0x1b5),
            field.Return(),
        ]
        space.write(spikes_src)

        # (2a) Remove overly cautious party-requirement check on door button #2 (would only mess up if someone walked a third party in here, simplifies logic)
        # We will repurpose $2A3 as "Party3 is standing on switch 1 in Phoenix Cave".
        space = Reserve(0xc274d, 0xc275e, "Phoenix cave Door Button #2 edit", field.NOP())  # CC/274D-CC2770
        door2_src = [
            field.ReturnIfAny([0x2a7, True]),   # CC/2760: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A7) [$1ED4, bit 7] is set), branch to $CA5EB3 (simply returns)
            field.SetEventBit(0x2a7),           # CC/2768: D4    Set event bit $1E80($2A7) [$1ED4, bit 7]
            field.PlaySoundEffect(187),         # CC/276A: F4    Play sound effect 187
            field.Call(0xc252b),                # CC/276C: B2    Call subroutine $CC252B
            field.Return(),                     # CC/2770: FE    Return
        ]
        space.write(door2_src)

        space = Reserve(0xc2771, 0xc2782, "Phoenix cave Door Button #2 release edit", field.NOP())  # CC/2771-CC/2794
        door2_release_src = [
            field.ReturnIfAny([0x2a7, False]),  # CC/2784: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A7) [$1ED4, bit 7] is clear), branch to $CA5EB3 (simply returns)
            field.PlaySoundEffect(187),         # CC/278C: F4    Play sound effect 187
            field.Call(0xc2533),                # CC/278E: B2    Call subroutine $CC2533
            field.ClearEventBit(0x2a7),         # CC/2792: D5    Clear event bit $1E80($2A7) [$1ED4, bit 7]
            field.Return()                      # CC/2794: FE    Return
        ]
        space.write(door2_release_src)

        # (2b) Remove overly cautious party-requirement check on rock switch #1 (would only mess up if someone walked a third party in here, simplifies logic)
        # Can repurpose $2D2 if needed.
        space = Reserve(0xc2987, 0xc2998, "Phoenix cave Rock Button #1 edit", field.NOP())  # CC/2987-CC/29AA
        rock1_src = [
            field.ReturnIfAny([0x2d3, True]),   # CC/299A: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2D3) [$1EDA, bit 3] is set), branch to $CA5EB3 (simply returns)
            field.SetEventBit(0x2d3),           # CC/29A2: D4    Set event bit $1E80($2D3) [$1EDA, bit 3]
            field.PlaySoundEffect(187),         # CC/29A4: F4    Play sound effect 187
            field.Call(0xc2670),                # CC/29A6: B2    Call subroutine $CC2670
            field.Return(),
        ]
        space.write(rock1_src)

        space = Reserve(0xc29ab, 0xc29ce, "Phoenix cave Rock Button #1 release edit", field.NOP())  # CC/29AB-CC/29CE
        rock1_release_src = [
            field.ReturnIfAny([0x2d3, False]),
            field.PlaySoundEffect(187),
            field.Call(0xc268e),
            field.ClearEventBit(0x2d3),
            field.Return()
        ]
        space.write(rock1_release_src)

        # (3) Modify entry logic to actually check all three parties, egad.
        # (3a) Modify button
        # We need 18 bytes for the new info.  Can fit this into the unused slot from Door button #2.
        space = Reserve(0xc275f, 0xc2770, "Phoenix cave Door Party3 edit", field.NOP())  # CC/274D-CC2770
        party3_entry_src = [
            field.LoadActiveParty(),  # CC/2717: E4    Set CaseWord bit corresponding to the number of the currently active party
            field.ReturnIfAny([0x1a3, False, 0x2a3, True]),  # CC/2718: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A6) [$1ED4, bit 6] is set), branch to $CA5EB3 (simply returns)
            field.SetEventBit(0x2a3),   # CC/2720: D4    Set event bit $1E80($2A6) [$1ED4, bit 6]
            field.PlaySoundEffect(187), # CC/2722: F4    Play sound effect 187
            field.Call(0xc251b),        # CC/2724: B2    Call subroutine $CC251B
            field.Return()              # CC/2728: FE    Return
        ]
        space.write(party3_entry_src)
        party3_addr = space.start_address

        # Update Party2 to branch here if not satisfied
        space = Reserve(0xc2718, 0xc271f, "Phoenix Cave Door Party2 branch edit", field.NOP())
        space.write([field.BranchIfAny([0x1a2, False, 0x2a6, True], party3_addr)])

        # (3b) Modify release
        # We need 18 bytes for the new info.  Can fit this into the unused slot from Door button #2 release.
        space = Reserve(0xc2783, 0xc2794, "Phoenix cave Door Party3 release edit", field.NOP())
        party3_release_src = [
            field.LoadActiveParty(),        # CC/2783: E4    Set CaseWord bit corresponding to the number of the currently active party
            field.ReturnIfAny([0x1a3, False, 0x2a3, False]),  # CC/2784: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A7) [$1ED4, bit 7] is clear), branch to $CA5EB3 (simply returns)
            field.PlaySoundEffect(187),
            field.Call(0xc2523),
            field.ClearEventBit(0x2a3),
            field.Return()
        ]
        space.write(party3_release_src)
        party3_clear_addr = space.start_address

        # Update Party2 to branch here if not satisfied
        space = Reserve(0xC273c, 0xc2743, "Phoenix Cave Door Party2 release branch edit", field.NOP())  # CC/273C: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A6) [$1ED4, bit 6] is clear), branch to $CA5EB3 (simply returns)
        space.write([field.BranchIfAny([0x1a2, False, 0x2a6, False], party3_clear_addr)])  # CC/2718: C1    If ($1E80($1A2) [$1EB4, bit 2] is clear) or ($1E80($2A6) [$1ED4, bit 6] is set), branch to $CA5EB3 (simply returns)

        # Update entry event effect of 0x2a3 to match 0x2a6.  Block of code:
        # CC/2458: C0    If ($1E80($2A2) [$1ED4, bit 2] is set), branch to $CC246E
        # CC/245E: C0    If ($1E80($2A6) [$1ED4, bit 6] is set), branch to $CC246E
        # CC/2464: B2    Call subroutine $CC2523
        # CC/2468: C0    If ($1E80($22F) [$1EC5, bit 7] is clear), branch to $CC2472
        # CC/246E: B2    Call subroutine $CC251B
        # CC/2472: C0    If ($1E80($2A3) [$1ED4, bit 3] is set), branch to $CC2488
        # CC/2478: C0    If ($1E80($2A7) [$1ED4, bit 7] is set), branch to $CC2488
        # CC/247E: B2    Call subroutine $CC2533
        # We will keep the same size, just rearrange some calls.
        space = Reserve(0xc2458, 0xc2477, "Phoenix Cave Patch entry event drawings", field.NOP())
        entry_patch_src = [
            field.BranchIfAny([0x2a2, True, 0x2a6, True, 0x2a3, True], "SHOW_DOOR"),
            field.Call(0xc2523),
            field.Branch("SKIP_DOOR"),
            "SHOW_DOOR",
            field.Call(0xc251b),
            "SKIP_DOOR",
        ]
        space.write(entry_patch_src)


        # (4) Modify Rock switch #2
        # Let's just make this one a permanent.  No reason to complicate things this late in the maze.
        space = Reserve(0xc29cf, 0xc29e2, "Phoenix Cave Rock Switch 2 edit", field.NOP())
        rock2_src = [
            # CC/29CF: E4    Set CaseWord bit corresponding to the number of the currently active party
            field.ReturnIfEventBitSet(0x2d4),   # CC/29D0: C1    If ($1E80($1A1) [$1EB4, bit 1] is clear) or ($1E80($2D4) [$1EDA, bit 4] is set), branch to $CC29E3
            field.SetEventBit(0x2d4),           # CC/29D8: D4    Set event bit $1E80($2D4) [$1EDA, bit 4]
                                                # CC/29DA: D4    Set event bit $1E80($2AA) [$1ED5, bit 2]
            field.PlaySoundEffect(187),         # CC/29DC: F4    Play sound effect 187
            field.Call(0xc26ac),                # CC/29DE: B2    Call subroutine $CC26AC
            field.Return() # CC/29E2: FE    Return
        ]
        space.write(rock2_src)

        # (4b) delete 'reset' event tiles
        # 55 (12,22; 0xc29f7)
        # 56 (12,24; 0xc29f7)
        # 57 (11,23; 0xc29f7)
        undo_tile_xy = [[12,22], [12,24], [11,23]]
        map_id = 0x13b
        for t in undo_tile_xy:
            self.maps.delete_event(map_id, t[0], t[1])

        # (5) Modify final buttons:  Use multipurpose clear-if-party-steps bits $2C5, $2C9, $2CD.
        # Should execute if any 2 of 2c5, 2c9, 2cd are set.
        move_block_addr = 0xc2b28  # Last of the four implementations.  Won't touch this one.
        space = Reserve(0xc2aac, 0xc2b27, "Phoenix Cave reimplement two-button ending", field.NOP())
        final_check_src = [
            field.ReturnIfEventBitSet(0x2d6),
            field.LoadActiveParty(),
            field.BranchIfEventBitClear(0x1a1, "PARTY2"),
            field.ReturnIfEventBitSet(event_bit.multipurpose_party1_step(1)),
            field.PlaySoundEffect(187),
            field.SetEventBit(event_bit.multipurpose_party1_step(1)),  # 0x2c5
            field.BranchIfAny([event_bit.multipurpose_party2_step(1), True, event_bit.multipurpose_party3_step(1), True], "SUCCESS"),
            field.Return(),
            "PARTY2",
            field.BranchIfEventBitClear(0x1a2, "PARTY3"),
            field.ReturnIfEventBitSet(event_bit.multipurpose_party2_step(1)),
            field.PlaySoundEffect(187),  # click
            field.SetEventBit(event_bit.multipurpose_party2_step(1)),  # 0x2c9
            field.BranchIfAny([event_bit.multipurpose_party1_step(1), True, event_bit.multipurpose_party3_step(1), True], "SUCCESS"),
            field.Return(),
            "PARTY3",
            # Must be party 3. Fallthru.
            field.ReturnIfEventBitSet(event_bit.multipurpose_party3_step(1)),
            field.PlaySoundEffect(187),  # click
            field.SetEventBit(event_bit.multipurpose_party3_step(1)),  # 0x2c9
            field.ReturnIfAll([event_bit.multipurpose_party1_step(1), False, event_bit.multipurpose_party2_step(1), False]),
            "SUCCESS",
            field.Call(move_block_addr),
            field.Return()
        ]
        space.write(final_check_src)

        # Make Button 2 also call the same code.  0xc2af0
        # 62 (12,32; 0xc2af0)
        button_2_event = self.maps.get_event(map_id, 12, 32)
        button_2_event.event_address = space.start_address - EVENT_CODE_START


    @staticmethod
    def entrance_door_patch():
        # self-contained code to be called in door rando after entering Phoenix Cave
        # to be used in event_exit_info.entrance_door_patch()
        return [field.Branch(ENTRY_EVENT_CODE_ADDR)]


