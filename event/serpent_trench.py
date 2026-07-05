from event.event import *
from data.map_exit_extra import exit_data, special_airship_locations
from data.rooms import exit_world

class SerpentTrench(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.DOOR_RANDOMIZE = (args.door_randomize_serpent_trench
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each
                          or args.ruination_mode)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Serpent Trench"

    def character_gate(self):
        return self.characters.GAU

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    # --- Ruination mode: probabilistic Serpent Trench fixed battles ---
    # On the first run through any Serpent Trench segment, its battles always
    # fire and the segment's tracking bit is set. On subsequent runs the
    # battles fire only with this probability (skipped otherwise).
    RUINATION_REPEAT_BATTLE_PROBABILITY = 0.25

    # One tracking ("done") bit per segment, in the unused NPC bit range.
    # 0x3a1-0x3ac are used by the Burning House fireballs; we use the next
    # five bits here.
    RUINATION_SEGMENT_DONE_BITS = [0x3ad, 0x3ae, 0x3af, 0x3b0, 0x3b1]

    # Per-battle metadata for ruination_battles_mod.
    # (battle_addr, segment_index, is_last_in_segment, return_addr)
    #   battle_addr        - SNES/ROM addr of the vanilla `CF pack bg` battle
    #                        invocation in the vehicle script
    #   segment_index      - 0..4, indexing RUINATION_SEGMENT_DONE_BITS
    #   is_last_in_segment - True if this battle should set the done bit;
    #                        False for non-final battles in multi-battle
    #                        segments (so the segment's later battles still
    #                        see the bit clear within the same run)
    #   return_addr        - addr to resume the vehicle script after the
    #                        custom block runs (== battle_addr + 7, i.e.
    #                        past the 6 overwritten bytes plus the orphaned
    #                        arg byte of the partially-clobbered instruction)
    RUINATION_BATTLES = [
        (0xa8b22, 0, True,  0xa8b29),   # Battle 1  - segment 1
        (0xa8b62, 1, False, 0xa8b69),   # Battle 2  - segment 2
        (0xa8b77, 1, True,  0xa8b7e),   # Battle 3  - segment 2
        (0xa8c25, 2, True,  0xa8c2c),   # Battle A1 - segment 3
        (0xa8bb7, 3, False, 0xa8bbe),   # Battle 4  - segment 4
        (0xa8bd0, 3, True,  0xa8bd7),   # Battle 5  - segment 4
        (0xa8c6c, 4, True,  0xa8c73),   # Battle B1 - segment 5
    ]

    def init_event_bits(self, space):
        if self.args.ruination_mode:
            for bit in self.RUINATION_SEGMENT_DONE_BITS:
                space.write(field.ClearEventBit(bit))

    def mod(self):
        self.airship_nikeah = [0x0, 116, 61]
        self.airship_sf = [0x0, 84, 113]
        if self.MAP_SHUFFLE:
            # modify airship position: nikeah
            nikeah_id = 1199
            if nikeah_id in self.maps.door_map.keys():
                if self.maps.door_map[nikeah_id] in special_airship_locations.keys():
                    self.airship_nikeah = special_airship_locations[self.maps.door_map[nikeah_id]]
                else:
                    self.airship_nikeah = self.maps.get_connection_location(nikeah_id)
                # conn_south = self.maps.door_map[nikeah_id]  # connecting exit south
                # conn_pair = exit_data[conn_south][0]  # original connecting exit
                # self.airship_nikeah = [exit_world[conn_pair]] + \
                #                       self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]

            # modify airship position: south figaro
            sf_id = 1167
            if sf_id in self.maps.door_map.keys():
                if self.maps.door_map[sf_id] in special_airship_locations.keys():
                    self.airship_sf = special_airship_locations[self.maps.door_map[sf_id]]
                else:
                    self.airship_sf = self.maps.get_connection_location(sf_id)
                # conn_north = self.maps.door_map[sf_id]
                # conn_pair = exit_data[conn_north][0]  # original connecting exit
                # self.airship_sf = [exit_world[conn_pair]] + \
                #                   self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]

            #print('Updated Serpent Trench airship teleports: ', self.airship_nikeah, self.airship_sf)

        self.cave_mod()
        self.find_diving_helmet_mod()
        self.add_move_airship()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

        if self.args.ruination_mode:
            self.ruination_battles_mod()

        if not self.args.fixed_encounters_original and not self.args.ruination_mode:
            # Fixed-encounter variety (upstream). Skipped in ruination mode:
            # ruination_battles_mod replaces each battle site with a 6-byte
            # redirect (Reserve battle_addr..+5) that overlaps the pack byte
            # (battle_addr+1) this would write. Safe alongside door_rando_mod,
            # whose reserves (0xa8c3a+) are clear of the pack bytes.
            self.fixed_battles_mod()

        self.log_reward(self.reward)

    def ruination_battles_mod(self):
        """
        In ruination mode the player can be forced to redo parts of the
        Serpent Trench animation. Make the seven fixed battles always fire
        on the first run through each segment, then fire only with
        probability RUINATION_REPEAT_BATTLE_PROBABILITY on later runs.

        Five segments share the seven battles:
            Segment 1: Battle 1                    @ 0xa8b22
            Segment 2: Battle 2 & 3                @ 0xa8b62, 0xa8b77
            Segment 3: Battle A1 (cave A return)   @ 0xa8c25
            Segment 4: Battle 4 & 5                @ 0xa8bb7, 0xa8bd0
            Segment 5: Battle B1 (cave B return)   @ 0xa8c6c

        Each segment has a single tracking ("done") bit. Within a single
        run through the animation, all of a segment's battles fight or all
        skip together: the segment's last battle is the only one that sets
        the done bit, so earlier battles in the same segment still see it
        clear and also fight.

        Implementation: the new vehicle-script opcode `BranchProbability`
        (instruction/vehicle.py) lets us roll the probability inline at
        each battle site. The vanilla `CF pack bg` battle invocation is
        only 3 bytes, so we still can't fit the conditional logic inline;
        each battle site is replaced with an unconditional 6-byte branch
        to a per-battle custom block in Bank CA which:
          1. if done_bit is CLEAR -> jump to FIGHT (first visit always fights)
          2. else, BranchProbability(p, FIGHT) - 25% chance to fight again
          3. otherwise skip the battle and continue
          4. on the FIGHT path, invoke the battle and (if last in segment)
             set the done bit
          5. replay the four bytes of original instructions the 6-byte
             redirect displaced
          6. branch back to the byte after those displaced bytes

        Tracking bits are cleared at game start in init_event_bits.
        """
        # Convert the float (0.0-1.0) chance into the 0-255 byte the new
        # opcode expects. BranchProbability would do this internally, but
        # doing it here means logging/diagnostics see the integer chance.
        chance_byte = int(self.RUINATION_REPEAT_BATTLE_PROBABILITY * 255)

        for battle_addr, seg_idx, is_last, return_addr in self.RUINATION_BATTLES:
            done_bit = self.RUINATION_SEGMENT_DONE_BITS[seg_idx]

            # The 6-byte branch we install at battle_addr clobbers the
            # 3-byte battle, the next whole 2-byte instruction
            # (battle_addr+3..+4), and the opcode of the instruction
            # after that (battle_addr+5). Its arg byte at battle_addr+6
            # is left in ROM but is unreachable (the branch always
            # fires). To resume the original animation we replay all
            # four of those displaced bytes (battle_addr+3..+6).
            #
            # Read them now, before the redirect overwrites the first three.
            displaced_bytes = list(self.rom.get_bytes(battle_addr + 3, return_addr - battle_addr - 3))
            # Battle bytes (CF, pack, bg) - read so we re-emit the same
            # encounter even if some other mod has changed the pack byte.
            battle_bytes = list(self.rom.get_bytes(battle_addr, 3))

            custom_src = [
                # First visit (done bit clear): always fight.
                vehicle.BranchIfEventBitClear(done_bit, "FIGHT"),
                # Repeat visit (done bit set): fight with probability p.
                vehicle.BranchProbability(chance_byte, "FIGHT"),
                # Otherwise skip the battle.
                vehicle.Branch("AFTER_BATTLE"),

                "FIGHT",
                battle_bytes,
            ]
            if is_last:
                custom_src.append(vehicle.SetEventBit(done_bit))
            custom_src += [
                "AFTER_BATTLE",
                displaced_bytes,
                vehicle.Branch(return_addr),
            ]
            cspace = Write(Bank.CA, custom_src,
                           f"serpent trench ruin battle @ {hex(battle_addr)}")
            custom_addr = cspace.start_address

            redirect = Reserve(battle_addr, battle_addr + 5,
                               f"serpent trench ruin battle redirect @ {hex(battle_addr)}")
            redirect.write(vehicle.Branch(custom_addr))

    def fixed_battles_mod(self):
        # Serpents Trench has 3 fixed encounters:
        #  275 - encountered once (first battle)
        #  276 - encountered 3 times
        #  277 - encountered 3 times
        # to increase the variety of encounters, we are adding 4 more and swapping 2 of the 276 and 2 of the 277s
        # 410 - 413 are otherwise unused fixed encounters

        replaced_encounters = [
            (410, 0xA8BB7), 
            (411, 0xA8C25),
            (412, 0xA8BD0),
            (413, 0xA8C6C),
        ]
        for pack_id_address in replaced_encounters:
            pack_id = pack_id_address[0]
            # first byte of the command is the pack_id
            invoke_encounter_pack_address = pack_id_address[1]+1
            space = Reserve(invoke_encounter_pack_address, invoke_encounter_pack_address, "serpent trench invoke fixed battle (battle byte)")
            space.write(
                # subtrack 256 since WC stores fixed encounter IDs starting at 256
                pack_id - 0x100
            )

    def cave_mod(self):
        self.maps.delete_event(0x0a7, 12, 22)
        self.maps.delete_event(0x0a7, 13, 18)
        self.maps.delete_event(0x0a7, 5, 16)
        self.maps.delete_event(0x0a7, 10, 8)

    def find_diving_helmet_mod(self):
        space = Reserve(0xbc601, 0xbc607, "serpent trench cave require gau to find diving helmet", field.NOP())
        if self.args.character_gating:
            space.write(
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            )

        space = Reserve(0xbc608, 0xbc615, "serpent trench cave find diving helmet rearrange party", field.NOP())
        space = Reserve(0xbc61c, 0xbc62b, "serpent trench cave sabin/cyan split from party", field.NOP())
        space = Reserve(0xbc662, 0xbc66a, "serpent trench cave sabin/cyan surprised animation", field.NOP())
        space = Reserve(0xbc676, 0xbc680, "serpent trench cave sabin/cyan face down is this it?", field.NOP())
        space = Reserve(0xbc687, 0xbc693, "serpent trench cave sabin/cyan move down", field.NOP())
        space = Reserve(0xbc69f, 0xbc6a1, "serpent trench cave treasure yesss", field.NOP())
        space = Reserve(0xbc6a6, 0xbc705, "serpent trench cave sabin/cyan reactions, let's go", field.NOP())
        space.write(
            field.Pause(0.5),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbc70a, 0xbc711, "serpent trench cave move cyan left", field.NOP())
        space = Reserve(0xbc716, 0xbc71d, "serpent trench cave join party", field.NOP())
        space = Reserve(0xbc71f, 0xbc72f, "serpent trench cave go outside and finish scene", field.NOP())
        space.write(
            field.SetEventBit(event_bit.FOUND_DIVING_HELMET),
            field.ClearEventBit(npc_bit.TEMP_NPC), # diving helmet npc bit shared by many npcs
            field.FreeScreen(),
            field.Return(),
        )

        # replace gau with party lead
        space = Reserve(0xbc616, 0xbc616, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc62d, 0xbc62d, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc639, 0xbc639, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc63d, 0xbc63d, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc641, 0xbc641, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc645, 0xbc645, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc649, 0xbc649, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc64d, 0xbc64d, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc652, 0xbc652, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc66b, 0xbc66b, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc681, 0xbc681, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc694, 0xbc694, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc6a2, 0xbc6a2, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc706, 0xbc706, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)
        space = Reserve(0xbc713, 0xbc713, "serpent trench cave find diving helmet gau")
        space.write(field_entity.PARTY0)

    def add_move_airship(self):
        # TODO remove load nikeah map at 0xa8bfd and replace with load wob map in airship to move it
        #      the clear bit also already happens in move airship functions ($1cc is cleared not $cc)
        #      however, it looks like vehicle's do not have a call command, they can only branch so the
        #      end of move airship functions need to call character/esper/item reward function
        src = [
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.LoadMap(self.airship_sf[0], direction.DOWN, default_music = False,
                          x = self.airship_sf[1], y = self.airship_sf[2], fade_in = False, airship = True),
            vehicle.SetPosition(self.airship_sf[1], self.airship_sf[2]),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.FadeLoadMap(0x5b, direction.LEFT, default_music = True,
                                x = 12, y = 11, fade_in = True, entrance_event = True),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "serpent trench move airship to south figaro")
        self.move_airship_to_south_figaro = space.start_address

        src = [
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.LoadMap(self.airship_nikeah[0], direction.DOWN, default_music = False,
                          x = self.airship_nikeah[1], y = self.airship_nikeah[2], fade_in = False, airship = True),
            vehicle.SetPosition(self.airship_nikeah[1], self.airship_nikeah[2]),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.FadeLoadMap(0xbb, direction.DOWN, default_music = True,
                                x = 24, y = 11, entrance_event = True),
            field.Return()
        ]
        space = Write(Bank.CA, src, "serpent trench move airship to nikeah")
        self.move_airship_to_nikeah = space.start_address

        space = Reserve(0xa8d21, 0xa8d26, "serpent trench move airship to south figaro after boat ride to south figaro", field.NOP())
        space.write(
            field.Branch(self.move_airship_to_south_figaro),
        )

        if self.MAP_SHUFFLE:
            # modify Parent Map Updates in entry to nikeah and entry to SF
            # NIKEAH:
            # CA/8C05: 6C    Set parent map to $0000 (World of Balance), parent coordinates to (117, 0), facing left
            space = Reserve(0xa8c05, 0xa8c0a, "serpent trench to nikeah parent map update")
            space.write(
                field.SetParentMap(map_id=self.airship_nikeah[0], x=self.airship_nikeah[1], y=self.airship_nikeah[2]-1,
                                   direction=direction.DOWN)
            )

            # SOUTH FIGARO:
            # CA/8D1B: 6C    Set parent map to $0000 (World of Balance), parent coordinates to (84, 0), facing down
            space = Reserve(0xa8d1b, 0xa8d20, "nikeah ship to south figaro parent map update")
            space.write(
                field.SetParentMap(map_id=self.airship_sf[0], x=self.airship_sf[1], y=self.airship_sf[2]-1,
                                   direction=direction.DOWN)
            )


    def door_rando_mod(self):
        # Modifications for door rando
        from data.event_exit_info import event_exit_info
        from event.switchyard import AddSwitchyardEvent, GoToSwitchyard

        # (1a) Change the entry event to load the switchyard location
        event_id = 2044  # ID of cliff jump event
        space = Reserve(0xbc873, 0xbc879, 'Serpent Trench Cliff Jump entry modification')
        space.write(GoToSwitchyard(event_id))
        # (1b) Add the switchyard event tile that handles entry to Serpent Trench #1
        AddSwitchyardEvent(event_id, self.maps, branch=0xa8ae3)

        # (2a) Change the Cave #1 Entry event to load the switchyard location
        event_id = 2045
        space = Reserve(0xa8c3a, 0xa8c40, 'Serpent Trench #1 to cave modification')
        space.write(GoToSwitchyard(event_id, map='world'))
        # (2b) Add the switchyard event tile that handles entry to ST Cave #1
        src = [
            field.LoadMap(0x0af, direction=direction.UP, default_music=True,
                          x=44, y=16, fade_in=True, entrance_event=True),
            field.Return()
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)

        # (3a) Edit the event tile in Cave #1 to go to a new script that goes to the switchyard
        event_id = 2047
        space = Reserve(0xa8c41, 0xa8c47, 'Serpent Trench Cave 1 exit modification')
        space.write(GoToSwitchyard(event_id), "Serpent Trench Cave 1 exit to Switchyard")
        # (3b) Add the switchyard event tile that handles exit from ST Cave #1
        src = [
            field.LoadMap(0x002, direction=direction.DOWN, default_music=True,
                          x=83, y=67, fade_in=True, entrance_event=True, airship=True),
            world.HideMinimap(),
            vehicle.MoveForward(direction.UP, 14),
            world.Branch(0xa8c49)
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)

        # (4a) Change the Cave #2 Entry event to load the switchyard location
        event_id = 2048
        space = Reserve(0xa8c8d, 0xa8c93, 'Serpent Trench #2 to cave modification')
        space.write(GoToSwitchyard(event_id, map='world'))
        # (4b) Add the switchyard event tile that handles entry to ST Cave #2
        src = [
            field.LoadMap(0x0af, direction=direction.UP, default_music=True,
                          x=25, y=16, fade_in=True, entrance_event=True),
            field.Return()
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)

        # (5a) Edit the event tile in Cave #2c to go to a new script that goes to the switchyard
        event_id = 2051
        space = Reserve(0xa8c94, 0xa8c9b, 'Serpent Trench Cave 2 exit modification')
        space.write(GoToSwitchyard(event_id), "Serpent Trench Cave 2 exit to Switchyard")
        # (5b) Add the switchyard event tile that handles exit from ST Cave #2
        src = [
            field.LoadMap(0x002, direction=direction.DOWN, default_music=True,
                          x=31, y=33, fade_in=True, entrance_event=True, airship=True),
            world.HideMinimap(),
            vehicle.MoveForward([], 4),
            world.Branch(0xa8c9c)
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)

        # (6a) Change the Nikeah Entry event to load the switchyard location
        event_id = 2052
        space = Reserve(0xa8be6, 0xa8bec, 'Serpent Trench #3 to Nikeah modification')
        space.write(GoToSwitchyard(event_id, map='world'))
        # (6b) Add the switchyard event tile that handles exit from Serpent Trench #3
        AddSwitchyardEvent(event_id, self.maps, src=GoToSwitchyard(2053))

        # (6c) Add the switchyard event tile that handles entry to Nikeah entrance animation
        event_id = 2053
        if self.args.ruination_mode:
            # In ruination mode, skip animation & set world to WOR
            src = [
                field.SetEventBit(event_bit.IN_WOR),
                field.LoadMap(0x0bb, direction=direction.UP, default_music=True,
                              x=24, y=11, fade_in=False, entrance_event=True),
                field.Branch(0xa8c03)
            ]
        else:
            from instruction.field.entity import Hide
            src = [
                field.LoadMap(0x000, direction=direction.UP, default_music=False,
                              x=128, y=73, fade_in=True, entrance_event=True),
                Hide(),
                world.Branch(0xa8bed)
            ]
        AddSwitchyardEvent(event_id, self.maps, src=src)

    def character_mod(self, character):
        # use gerad npc to show character
        gerad_npc_id = 0x15
        gerad_npc = self.maps.get_npc(0x0bb, gerad_npc_id)
        gerad_npc.sprite = character
        gerad_npc.palette = self.characters.get_palette(character)

        src = [
            field.BranchIfEventBitSet(event_bit.GOT_SERPENT_TRENCH_REWARD, "SKIP_CHARACTER_REWARD"),

            field.SetEventBit(npc_bit.GERAD_NIKEAH_BOAT),
            field.Call(self.move_airship_to_nikeah),
            field.CreateEntity(gerad_npc_id),
            field.EntityAct(gerad_npc_id, True,
                field_entity.SetPosition(24, 11),
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpriteLayer(0),
            ),

            field.HideEntity(field_entity.PARTY0),
            field.ShowEntity(gerad_npc_id),

            field.FadeInScreen(speed = 2),
            field.WaitForFade(),
            field.Pause(2),
            field.Pause(1),
            field.FadeOutScreen(speed = 2),
            field.WaitForFade(),

            field.ClearEventBit(npc_bit.GERAD_NIKEAH_BOAT),
            field.HideEntity(gerad_npc_id),
            field.DeleteEntity(gerad_npc_id),
            field.ShowEntity(field_entity.PARTY0),

            field.RecruitAndSelectParty(character),

            field.EntityAct(field_entity.PARTY0, True,
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpriteLayer(0),
            ),

            field.FadeInScreen(),
            field.WaitForFade(),

            field.SetEventBit(event_bit.GOT_SERPENT_TRENCH_REWARD),
            field.FinishCheck(),
            field.Return(),

            "SKIP_CHARACTER_REWARD",
            field.Call(self.move_airship_to_nikeah),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpriteLayer(0),
            ),
            field.FadeInScreen(speed = 2),
            field.WaitForFade(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "serpent trench recruit character")
        recruit_character = space.start_address

        space = Reserve(0xa8c03, 0xa8c04, "serpent trench pause before showing screen", field.NOP())

        space = Reserve(0xa8c0b, 0xa8c14, "serpent trench knocked out animation", field.NOP())
        space.write(
            field.Call(recruit_character),
            field.Return(),
        )

    def esper_item_mod(self, esper_item_instructions):
        src = [
            field.Call(self.move_airship_to_nikeah),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpriteLayer(0),
            ),
            field.FadeInScreen(speed = 2),
            field.WaitForFade(),
            field.ReturnIfEventBitSet(event_bit.GOT_SERPENT_TRENCH_REWARD),

            esper_item_instructions,

            field.SetEventBit(event_bit.GOT_SERPENT_TRENCH_REWARD),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "serpent trench esper/item reward")
        esper_item_reward = space.start_address

        space = Reserve(0xa8c03, 0xa8c04, "serpent trench pause before showing screen", field.NOP())

        space = Reserve(0xa8c0b, 0xa8c14, "serpent trench knocked out animation", field.NOP())
        space.write(
            field.Call(esper_item_reward),
            field.Return(),
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
