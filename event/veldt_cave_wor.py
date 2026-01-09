from event.event import *
from data.map_exit_extra import exit_data, special_airship_locations
from data.rooms import exit_world

class VeldtCaveWOR(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.DOOR_RANDOMIZE = (args.door_randomize_veldt_cave
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Veldt Cave WOR"

    def character_gate(self):
        return self.characters.SHADOW

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.shadow_npc_id = 0x12
        self.shadow_npc = self.maps.get_npc(0x161, self.shadow_npc_id)

        self.relm_npc_id = 0x13
        self.relm_npc = self.maps.get_npc(0x161, self.relm_npc_id)

        self.dr_exit_type = 'dog'  # 'behemoth'

        self.airship_thamasa = [0x001, 251, 230]
        if self.MAP_SHUFFLE:
            # modify airship warp position
            thamasa_id = 1261
            if thamasa_id in self.maps.door_map.keys():
                if self.maps.door_map[thamasa_id] in special_airship_locations.keys():
                    self.airship_thamasa = special_airship_locations[self.maps.door_map[thamasa_id]]
                else:
                    self.airship_thamasa = self.maps.get_connection_location(thamasa_id)
                # conn_south = self.maps.door_map[thamasa_id]  # connecting exit south
                # conn_pair = exit_data[conn_south][0]  # original connecting exit
                # self.airship_thamasa = [exit_world[conn_pair]] + self.maps.exits.exit_original_data[conn_pair][1:3]   # [dest_map, dest_x, dest_y]
                #print('Updated Veldt Cave airship teleport: ', self.airship_thamasa)

        self.dialog_mod()

        if self.args.character_gating:
            self.add_gating_condition()

        self.srbehemoth_battle_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

        #if self.MAP_SHUFFLE:
        #    self.delete_exit_event_tiles()

    def dialog_mod(self):
        space = Reserve(0xb79cd, 0xb79d5, "veldt cave wor you're coming with us", field.NOP())
        space = Reserve(0xb7a43, 0xb7a45, "veldt cave wor look at those wounds", field.NOP())

    def add_gating_condition(self):
        interceptor_beginning_id = 0x11
        interceptor_end_id = 0x15

        space = Reserve(0xb7d08, 0xb7d57, "veldt cave wor relm/shadow in bed in thamasa after veldt cave", field.NOP())

        entrance_event = space.next_address
        space.copy_from(0xb7982, 0xb7989) # shadow/relm animate laying down
        space.write(
            field.ReturnIfEventBitSet(event_bit.character_recruited(self.character_gate())),
            field.HideEntity(interceptor_beginning_id),
            field.HideEntity(interceptor_end_id),
            field.Return(),
        )

        interceptor_beginning_event = space.next_address
        space.copy_from(0xb79a5, 0xb79b0) # bark, pause, call blink 3 times, set event bit
        space.write(
            field.Return(),
        )

        sr_behemoth_event = space.next_address
        space.copy_from(0xb7a1e, 0xb7a2f) # pause, animate surprised, hold screen, move camera down/up
        space.write(
            field.Return(),
        )

        space = Reserve(0xb7982, 0xb7989, "veldt cave wor entrance event shadow/relm animate laying down", field.NOP())
        space.write(
            field.Call(entrance_event),
        )

        space = Reserve(0xb79a5, 0xb79b0, "veldt cave interceptor beginning event gate check", field.NOP())
        space.write(
            field.ReturnIfAny([event_bit.FOUND_INTERCEPTOR_VELDT_CAVE_WOR, True, event_bit.character_recruited(self.character_gate()), False]),
            field.Call(interceptor_beginning_event),
        )

        space = Reserve(0xb7a1e, 0xb7a2f, "veldt cave wor sr behemoth event gate check", field.NOP())
        space.write(
            field.ReturnIfAny([event_bit.DEFEATED_SR_BEHEMOTH, True, event_bit.character_recruited(self.character_gate()), False]),
            field.Call(sr_behemoth_event),
        )

    def srbehemoth_battle_mod(self):
        boss_pack_id = self.get_boss("SrBehemoth")

        space = Reserve(0xb7a73, 0xb7a98, "veldt cave wor invoke battle srbehemoth", field.NOP())
        space.write(
            # stop music before battle to prevent it playing after winning and before moving to thamasa
            field.StartSong(0), # silence
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.InvokeBattle(boss_pack_id),
            field.ClearEventBit(npc_bit.BEHEMOTH_VELDT_CAVE),
            field.SetEventBit(event_bit.DEFEATED_SR_BEHEMOTH),
        )

    def move_to_thamasa(self, reward_instructions):
        space = Reserve(0xb7aa1, 0xb7be2, "veldt cave wor move party to strago's room in thamasa", field.NOP())
        if self.DOOR_RANDOMIZE:
            # In door rando, we want to reward the player before the transition, and use a switchyard tile for the
            # transition so the airship is moved.
            from event.switchyard import AddSwitchyardEvent, GoToSwitchyard
            event_id = 2075
            switchyard_src = [
                field.FadeInSong(0x08, 0x30),
                field.LoadMap(self.airship_thamasa[0], direction.DOWN, default_music=False, x=self.airship_thamasa[1],
                              y=self.airship_thamasa[2], fade_in=False, airship=True),
                vehicle.SetPosition(self.airship_thamasa[1], self.airship_thamasa[2]),
                vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
                vehicle.LoadMap(0x15d, direction.DOWN, default_music=True, x=61, y=13, update_parent_map=True),
                # Always show interceptor in door rando
                #field.ClearEventBit(npc_bit.INTERCEPTOR_STRAGO_ROOM),
                field.FadeInScreen(),
                field.Return(),
            ]
            AddSwitchyardEvent(event_id=event_id, maps=self.maps, src=switchyard_src)

            space.write([
                reward_instructions,
                field.FinishCheck()
            ])
            self.gotoswitchyard_addr = space.next_address

            # Update event_exit_info[2075] with this information
            from data.event_exit_info import event_exit_info
            event_exit_info[2075][0:3] = [self.gotoswitchyard_addr, 7, 1]
            
            space.write([
                GoToSwitchyard(event_id, map='field'),
                field.Return()
            ])

        else:
            src = [
                field.FadeInSong(0x08, 0x30),
                field.LoadMap(self.airship_thamasa[0], direction.DOWN, default_music=False, x=self.airship_thamasa[1],
                              y=self.airship_thamasa[2], fade_in=False, airship=True),
                vehicle.SetPosition(self.airship_thamasa[1], self.airship_thamasa[2]),
                vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
                vehicle.LoadMap(0x15d, direction.DOWN, default_music=True, x=61, y=13, update_parent_map=True)
            ]
            if self.MAP_SHUFFLE:
                # Explicitly set the parent map.  Otherwise the placement is weird...
                src += [field.SetParentMap(map_id=self.airship_thamasa[0], x=self.airship_thamasa[1],
                                           y=self.airship_thamasa[2]-1, direction=direction.DOWN)]
            src += [
                # make interceptor only appear until you leave the screen
                field.ClearEventBit(npc_bit.INTERCEPTOR_STRAGO_ROOM),

                reward_instructions,

                field.FinishCheck(),
                field.Return(),
            ]
            space.write(src)
            # print([a.__str__() for a in src])

    def character_mod(self, character):
        self.shadow_npc.sprite = character
        self.shadow_npc.palette = self.characters.get_palette(character)
        self.relm_npc.sprite = character
        self.relm_npc.palette = self.characters.get_palette(character)

        if self.DOOR_RANDOMIZE:
            char_instructions = [
                field.RecruitAndSelectParty(character),
            ]
        else:
            char_instructions = [
                field.RecruitAndSelectParty(character),
                field.FadeInScreen(),
            ]
        self.move_to_thamasa(char_instructions)

    def esper_item_mod(self, esper_item_instructions):
        if self.DOOR_RANDOMIZE:
            sr_behemoth_npc = 0x14

            if self.dr_exit_type == 'behemoth':
                reward_instructions = [
                    field.EntityAct(sr_behemoth_npc, True,
                                    field_entity.SetPosition(58, 24),
                                    field_entity.Turn(direction.UP)),
                    field.EntityAct(field_entity.PARTY0, True,
                                    field_entity.AnimateStandingFront()),
                    field.HideEntity(self.shadow_npc_id),
                    field.FadeInScreen(),
                    esper_item_instructions,
                ]
            elif self.dr_exit_type == 'dog':
                reward_instructions = [
                    field.EntityAct(field_entity.PARTY0, True,
                                    field_entity.AnimateStandingFront()),
                    field.HideEntity(sr_behemoth_npc),
                    field.HideEntity(self.shadow_npc_id),
                    field.FadeInScreen(),
                    esper_item_instructions,
                ]
        else:
            reward_instructions = [
                field.FadeInScreen(),
                esper_item_instructions,
            ]
        self.move_to_thamasa(reward_instructions)

    def esper_mod(self, esper):
        self.shadow_npc.sprite = 91
        self.shadow_npc.palette = 2
        self.shadow_npc.split_sprite = 1
        self.shadow_npc.direction = direction.UP

        self.relm_npc.sprite = 91
        self.relm_npc.palette = 2
        self.relm_npc.split_sprite = 1
        self.relm_npc.direction = direction.UP

        self.esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        random_sprite = self.characters.get_random_esper_item_sprite()

        self.shadow_npc.sprite = random_sprite
        self.shadow_npc.palette = self.characters.get_palette(self.shadow_npc.sprite)

        self.relm_npc.sprite = random_sprite
        self.relm_npc.palette = self.characters.get_palette(self.relm_npc.sprite)

        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def door_rando_mod(self):
        # Add event tile to delete dog, if not yet seen: [0x161, 39, 45]
        interceptor_npc = 0x11
        src = [
            field.ReturnIfEventBitSet(event_bit.FOUND_INTERCEPTOR_VELDT_CAVE_WOR),
            field.DeleteEntity(interceptor_npc),
            field.HideEntity(interceptor_npc),
            field.Return()
        ]
        space = Write(Bank.CB, src, "Delete Interceptor coming from north")
        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 39
        new_event.y = 45
        new_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(0x161, new_event)

        # Add "create dog" to dog event script, just in case:
        # replace CB/79A5: B2    Call subroutine $CB6ABF
        src = [
            field.CreateEntity(interceptor_npc),
            field.ShowEntity(interceptor_npc),
            field.Call(0xb6abf),
            field.Return()
        ]
        show_interceptor = Write(Bank.CB, src, "force show Interceptor")
        space = Reserve(0xb79a5, 0xb79a8, "force create interceptor npc", field.NOP())
        space.write([field.Call(show_interceptor.start_address)])

        # Add a mechanism to redo the event transition after the boss is defeated
        # Modify entrance event: if Sr. Behemoth defeated, show Sr. Behemoth knocked out
        norm_entr_event_addr = 0xb7982
        if self.dr_exit_type == 'behemoth':
            sr_behemoth_npc = 0x14
            src = [
                field.BranchIfEventBitClear(event_bit.DEFEATED_SR_BEHEMOTH, "normal_entrance_event"),
                field.DeleteEntity(self.shadow_npc_id),
                field.HideEntity(self.shadow_npc_id),
                field.CreateEntity(sr_behemoth_npc),
                field.ShowEntity(sr_behemoth_npc),
                field.EntityAct(sr_behemoth_npc, False,
                                field_entity.Turn(direction.UP),
                                field_entity.SetPosition(x=58, y=24)),
                "normal_entrance_event",
                field.Branch(norm_entr_event_addr)
            ]
            space = Write(Bank.CB, src, "Cave on the Veldt updated entrance event")
            self.maps.set_entrance_event(0x161, space.start_address - EVENT_CODE_START)

            # Modify Sr. Behemoth NPC event
            sr_behemoth = self.maps.get_npc(0x161, sr_behemoth_npc)
            src = [
                field.ReturnIfEventBitClear(event_bit.DEFEATED_SR_BEHEMOTH),
                field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
                field.HoldScreen(),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.AnimateKneelingRight(),
                                field_entity.Pause(10)),
                field.EntityAct(sr_behemoth_npc, True,
                                field_entity.AnimateStandingFront()),
                field.PauseUnits(1),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.SetSpeed(field_entity.Speed.FAST),
                                field_entity.AnimateSurprised(),
                                field_entity.DisableWalkingAnimation(),
                                field_entity.AnimateHighJump(),
                                field_entity.Move(direction.UP, 10),
                                field_entity.EnableWalkingAnimation()),
                field.FreeScreen(),
                field.Branch(self.gotoswitchyard_addr)
            ]
            space = Write(Bank.CB, src, "Senior Behemoth exit event")
            sr_behemoth.event_address = space.start_address - EVENT_CODE_START
        elif self.dr_exit_type == 'dog':
            dog_npc_id = 0x15
            behemoth_npc_id = 0x14
            src = [
                field.BranchIfEventBitClear(event_bit.DEFEATED_SR_BEHEMOTH, "normal_entrance_event"),
                field.DeleteEntity(self.shadow_npc_id),
                field.HideEntity(self.shadow_npc_id),
                field.DeleteEntity(behemoth_npc_id),
                field.HideEntity(behemoth_npc_id),
                field.CreateEntity(dog_npc_id),
                field.ShowEntity(dog_npc_id),
                field.EntityAct(dog_npc_id, False,
                                field_entity.SetPosition(x=55, y=25)),
                "normal_entrance_event",
                field.Branch(norm_entr_event_addr)
            ]
            space = Write(Bank.CB, src, "Cave on the Veldt updated entrance event")
            self.maps.set_entrance_event(0x161, space.start_address - EVENT_CODE_START)

            # Modify dog NPC event
            dog_npc = self.maps.get_npc(0x161, dog_npc_id)
            src = [
                field.ReturnIfEventBitClear(event_bit.DEFEATED_SR_BEHEMOTH),
                field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
                field.Call(0xb6abf), # bark; pause 30 units
                field.Pause(.25),
                field.PlaySoundEffect(0x51),  # xfer
                field.MosaicScreen(3),
                field.PauseUnits(60),
                field.FadeOutScreen(4),
                field.Branch(self.gotoswitchyard_addr)
            ]
            space = Write(Bank.CB, src, "Veldt Cave Interceptor exit event")
            dog_npc.event_address = space.start_address - EVENT_CODE_START

    # def delete_exit_event_tiles(self):
    #     # Delete extra exit event tiles on WOR Thamasa map, so that long exit events work correctly
    #     ### Actually handled by maps.door_rando_cleanup()
    #     pass
    #     #map_id = 0x158
    #     #event_x_y = [[a, 48] for a in range(20, 26)] + [[0, b] for b in range(28, 32)]
    #     #for xy in event_x_y:
    #     #    self.maps.delete_short_event(map_id, xy[0], xy[1])
