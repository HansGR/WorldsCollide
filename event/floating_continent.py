from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard
ENTRY_EVENT_CODE_ADDR = 0xa48e3

# TODO game can freeze, is this something i did or a bug in emulator/game?
#      go through and when you get to the hole that brings you to three possible holes (including the one you came from)
#      go thruogh left hole, hit both switches and go back through the hole you came from
#      can ignore the right hole since it leads nowhere and now go back through the north hole
#      now run around and take the path you just created back to the hole you came from to reach the two switches
#      going in that hole will freeze

class FloatingContinent(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle or args.door_randomize_dungeon_crawl

    def name(self):
        return "Floating Continent"

    def character_gate(self):
        return self.characters.SHADOW

    def init_rewards(self):
        self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)
        self.reward2 = self.add_reward(RewardType.ESPER | RewardType.ITEM)
        self.reward3 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)

    def mod(self):
        self.entry_id = 1556
        self.exit_id = 1557

        self.shadow_leaves_mod()
        self.airship_battle_mod()
        if not self.args.fixed_encounters_original:
            self.airship_fixed_battles_mod()
        self.ultros_chupon_battle_mod()
        self.air_force_battle_mod()

        self.ground_shadow_npc_id = 0x1b
        self.ground_shadow_npc = self.maps.get_npc(0x18a, self.ground_shadow_npc_id)

        self.ground_reward_position_mod()
        if self.reward1.type == RewardType.CHARACTER:
            self.ground_character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.ground_esper_mod(self.reward1.id)
        self.finish_ground_check()

        self.save_point_hole_mod()
        self.airship_return_mod()
        self.atma_battle_mod()

        if self.reward2.type == RewardType.ESPER:
            self.atma_esper_mod(self.reward2.id)
        elif self.reward2.type == RewardType.ITEM:
            self.atma_item_mod(self.reward2.id)

        self.statues_scene_mod()
        self.timer_mod()
        self.nerapa_battle_mod()

        if self.reward3.type == RewardType.CHARACTER:
            self.escape_character_mod(self.reward3.id)
        elif self.reward3.type == RewardType.ESPER:
            self.escape_esper_mod(self.reward3.id)

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)
        self.log_reward(self.reward3)

        if self.MAP_SHUFFLE:
            self.map_shuffle_mod()

    def shadow_leaves_mod(self):
        # remove shadow from party at floating continent (if return to airship or after atma)
        # use this space to add some new functions we need
        space = Reserve(0xad9fc, 0xada2f, "floating continent shadow leaves party", field.NOP())

        # copy some instructions to here so can make room for deleting lights where code originally was
        self.enter_floating_continent_function = space.next_address
        space.copy_from(0xa5a42, 0xa5a4a) # copy loading the map, showing party and holding screen
        space.write(
            field.Return(),
        )

        # also do the same thing for when returning from save point hole
        self.return_from_save_map_function = space.next_address
        space.copy_from(0xad951, 0xad95c) # copy loading the map and positioning the party
        space.write(
            field.Return(),
        )

        # delete the lights around the statues after the map is loaded
        # otherwise airship won't show up when 4 people in party and char (or esper?) still on ground
        # i create the lights again when the statue scene starts
        self.delete_lights_function = space.next_address
        space.write(
            field.DeleteEntity(0x1d),
            field.DeleteEntity(0x1e),
            field.DeleteEntity(0x1f),
            field.DeleteEntity(0x20),
            field.DeleteEntity(0x21),
            field.Return(),
        )

    def airship_battle_mod(self):
        space = Reserve(0xa582a, 0xa5839, "floating continent do not enforce 3 characters in party", field.NOP())
        space = Reserve(0xa592f, 0xa5931, "floating continent skip IAF dialog", field.NOP())

        # skip 3 out of the 6 battles before ultros/chupon battle
        space = Reserve(0xa5978, 0xa597d, "floating continent skip to chupon appearing in sky", field.NOP())
        space.write(
            field.Branch(0xa59bb),
        )

        # small pause to prevent chupon from clipping air force sprite in sky
        space = Reserve(0xa59bb, 0xa59be, "floating continent skip something approaches dialog", field.NOP())
        space.write(
            field.Pause(2.0),
        )

        space = Reserve(0xa5a42, 0xa5a4a, "floating continent enter after defeating air force", field.NOP())
        space.write(
            field.Call(self.enter_floating_continent_function),
            field.Call(self.delete_lights_function), # delete lights so airship shows up
        )

        space = Reserve(0xa5a68, 0xa5a6a, "floating continent skip kefka, gestahl, statues ahead dialog", field.NOP())
        if self.MAP_SHUFFLE:
            space.write(field.SetEventBit(event_bit.DEFEATED_AIR_FORCE))

    def airship_fixed_battles_mod(self):
        # change iaf battles to front attacks, even if the original pack id happens to be the new random one
        # because other random formations in the pack may not work with pincer attacks
        
        # adding an unused pack id (416) to increase variety of encounters
        battle_background = 48 # airship, right

        pack_start_addresses = [
            (382, 0xa5932), #sky armor / spit fire
            (416, 0xa59fc), #unused
            (382, 0xa5a0d)] #sky armor / spit fire
        for pack_start_address in pack_start_addresses:
            pack_id = pack_start_address[0]
            start_address = pack_start_address[1]
            space = Reserve(start_address, start_address + 2, "floating continent iaf invoke fixed battle")
            space.write(
                field.InvokeBattleType(pack_id, field.BattleType.FRONT, battle_background, check_game_over = False),
            )

    def ultros_chupon_battle_mod(self):
        boss_pack_id = self.get_boss("Ultros/Chupon")

        battle_type = field.BattleType.FRONT
        battle_background = 48 # airship, right
        if boss_pack_id == self.enemies.packs.get_id("Cranes"):
            battle_type = field.BattleType.PINCER
            battle_background = 37 # airship, center

        space = Reserve(0xa5a1e, 0xa5a24, "floating continent invoke battle ultros/chupon", field.NOP())
        space.write(
            field.InvokeBattleType(boss_pack_id, battle_type, battle_background),
        )

    def air_force_battle_mod(self):
        if self.args.flashes_remove_most or self.args.flashes_remove_worst:
            # Slow the scrolling background by modifying the ADC command.
            space = Reserve(0x2b1b1, 0x2b1b3, "falling through clouds background movement")
            space.write(
                asm.ADC(0x0001, asm.IMM16) #default: 0x0006
            )

        boss_pack_id = self.get_boss("Air Force")
        battle_background = 7 # sky, falling

        space = Reserve(0xa5a3b, 0xa5a41, "floating continent invoke battle air force", field.NOP())
        self.air_force_battle_src = [field.InvokeBattle(boss_pack_id, battle_background)]
        space.write(
            self.air_force_battle_src
        )
        self.air_force_battle_addr = space.start_address


    def ground_reward_position_mod(self):
        self.ground_shadow_npc.x = 11
        self.ground_shadow_npc.y = 13

        space = Reserve(0xad9a7, 0xad9aa, "floating continent move party above shadow", field.NOP())

    def ground_character_mod(self, character):
        self.ground_shadow_npc.sprite = character
        self.ground_shadow_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xad9b5, 0xad9b7, "floating continent down with the empire dialog", field.NOP())

        space = Reserve(0xad9c0, 0xad9ed, "floating continent add character on ground", field.NOP())
        space.write(
            field.RecruitCharacter(character),

            # i do not know why, but i need to delete the first npcs specifically before the select party screen
            # it prevents a softlock when already recruited 12+ characters
            # seems like after 11 characters they start to overwrite the npcs so i need to delete those first to make room
            field.DeleteEntity(0x10),
            field.DeleteEntity(0x11),
            field.DeleteEntity(0x12),
            field.Call(field.REFRESH_CHARACTERS_AND_SELECT_PARTY),

            # loading the map here instead of just fading in the screen prevents a graphics bug with
            # the save point when the player has already acquired around 8+ characters
            # it also reloads the npcs that were deleted before the select party screen was shown
            field.LoadMap(0x18a, direction.RIGHT, default_music = False, x = 10, y = 13, fade_in = False, entrance_event = True),
            field.DeleteEntity(0x1b),
            field.FadeInScreen(),
        )

    def ground_esper_mod(self, esper):
        self.ground_shadow_npc.sprite = 91
        self.ground_shadow_npc.palette = 2
        self.ground_shadow_npc.split_sprite = 1
        self.ground_shadow_npc.direction = direction.UP

        space = Reserve(0xad9b1, 0xad9ed, "floating continent add esper on ground", field.NOP())
        space.write(
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.DeleteEntity(self.ground_shadow_npc_id),
            field.Branch(space.end_address + 1),
        )

    def finish_ground_check(self):
        src = [
            Read(0xad9ee, 0xad9f2), # clear ground npc bit, set shadow recruited bit, update party leader
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "floating continent ground finish check")
        finish_check = space.start_address

        space = Reserve(0xad9ee, 0xad9f2, "floating continent set bits, update leader after shadow", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def save_point_hole_mod(self):
        space = Reserve(0xad951, 0xad95c, "floating continent return from save point hole", field.NOP())
        space.write(
            field.Call(self.return_from_save_map_function),
            field.Call(self.delete_lights_function), # delete lights so airship shows up
        )

    def airship_return_mod(self):
        self.dialogs.set_text(2135, "Do you wish to return?<line><choice> (No)<line><choice> (Yes)<end>")

        space = Reserve(0xa5a8b, 0xa5a8f, "floating continent do not remove shadow if return to airship", field.NOP())

        # do not set the shadow npc even bit again (otherwise when you return character/esper would be there again)
        space = Reserve(0xa5ab5, 0xa5abc, "floating continent do not put shadow npc back on map", field.NOP())

    def atma_battle_mod(self):
        boss_pack_id = self.get_boss("AtmaWeapon")

        space = Reserve(0xada30, 0xada36, "floating continent invoke battle atmaweapon", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def atma_esper_item_mod(self, esper_item_instructions):
        src = [
            esper_item_instructions,
            field.SetEventBit(event_bit.DEFEATED_ATMAWEAPON),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "floating continent atma weapon finish check")
        finish_check = space.start_address

        space = Reserve(0xada3f, 0xada46, "floating continent do not remove shadow after fighting atma", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def atma_esper_mod(self, esper):
        self.atma_esper_item_mod([
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def atma_item_mod(self, item):
        self.atma_esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def statues_scene_mod(self):
        kefka_npc_id = 0x11
        kefka_npc = self.maps.get_npc(0x18a, kefka_npc_id)
        kefka_npc.x = 60
        kefka_npc.y = 7

        gestahl_npc_id = 0x1c
        gestahl_npc = self.maps.get_npc(0x18a, gestahl_npc_id)
        gestahl_npc.x = 57
        gestahl_npc.y = 7

        space = Reserve(0xadd22, 0xaddb3, "floating continent statues move camera", field.NOP())
        space.write(
            # first create the lights i deleted
            field.CreateEntity(0x1d),
            field.CreateEntity(0x1e),
            field.CreateEntity(0x1f),
            field.CreateEntity(0x20),
            field.CreateEntity(0x21),
            field.ShowEntity(0x1d),
            field.ShowEntity(0x1e),
            field.ShowEntity(0x1f),
            field.ShowEntity(0x20),
            field.ShowEntity(0x21),
            field.RefreshEntities(),

            field.HoldScreen(),
            field.EntityAct(field_entity.CAMERA, True,
                field_entity.SetSpeed(field_entity.Speed.SLOW),
                field_entity.Move(direction.UP, 5),
            ),
        )

        space = Reserve(0xaddf0, 0xade0c, "floating continent statues party approach kefka", field.NOP())
        space.write(
            field.EntityAct(field_entity.CAMERA, False,
                field_entity.Move(direction.DOWN, 3),
            ),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.Move(direction.UP, 2),
            ),
            field.EntityAct(kefka_npc_id, True,
                field_entity.Turn(direction.DOWN),
            ),
            field.EntityAct(gestahl_npc_id, True,
                field_entity.Turn(direction.DOWN),
            ),
        )

        space = Reserve(0xade0f, 0xade11, "floating continent statues gestahl has goose bumps dialog", field.NOP())

        space = Reserve(0xade24, 0xade24, "floating continent statues kefka raise hand")
        space.write(kefka_npc_id)

        # for some reason the animation gestahl uses does not look right with kefka, change it
        space = Reserve(0xade26, 0xade26, "floating continent statues kefka raise hand animation")
        space.write(field_entity.AnimateFrontHandsUp())

        space = Reserve(0xade28, 0xade2b, "floating continent statues don't move camera down before shooting light", field.NOP())

        space = Reserve(0xade52, 0xade52, "floating continent statues kefka turn down during light")
        space.write(kefka_npc_id)

        begin_escape = 0xae3d6
        src = [
            field.EntityAct(0x21, False,
                field_entity.SetPosition(60, 4),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.LEFT, 1),
            ),
            field.EntityAct(0x1f, False,
                field_entity.SetPosition(60, 4),
                field_entity.Move(direction.DOWN, 8),
                field_entity.Move(direction.DOWN, 8),
            ),
            field.EntityAct(field_entity.CAMERA, False,
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.Move(direction.DOWN, 3),
                field_entity.SetSpeed(field_entity.Speed.SLOW),
            ),
            field.ShakeScreen(1, True, True, True, True, True),
            field.Pause(0.25),
            field.EntityAct(gestahl_npc_id, False,
                field_entity.AnimateKnockedOut2(),
            ),
            field.EntityAct(field_entity.PARTY0, False,
                field_entity.AnimateAttacked(),
                field_entity.DisableWalkingAnimation(),
                field_entity.AnimateKnockedOut(),
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
                field_entity.MoveDiagonal(direction.DOWN, 1, direction.RIGHT, 1),
            ),
            field.Call(0xad033),
            field.WaitForEntityAct(0x21),
            field.WaitForEntityAct(0x1f),

            field.Branch(begin_escape)
        ]
        space = Write(Bank.CA, src, "floating continent statues shoot light at gestahl and party")
        light_shot = space.start_address

        space = Reserve(0xade5e, 0xade63, "floating continent statues light shot branch", field.NOP())
        space.write(
            field.Branch(light_shot),
        )

    def timer_mod(self):
        if self.args.event_timers_random:
            import random

            # randomize timer between 5 and 8 minutes
            seconds = random.randint(300, 480)

            space = Reserve(0xae3f6, 0xae3f7, "floating continent timer 0")
            space.write(
                (seconds * 60).to_bytes(2, "little"),
            )

            timer_display = f"{seconds // 60}:{seconds % 60:>02}"
            self.log_change(f"Timer 6:00", timer_display)

            # floating continent escape has a second timer which expires 5 seconds before game over timer
            seconds -= 5
            space = Reserve(0xae3fc, 0xae3fd, "floating continent timer 2")
            space.write(
                (seconds * 60).to_bytes(2, "little"),
            )
        elif self.args.event_timers_none:
            space = Reserve(0xae3f5, 0xae400, "floating continent timers", field.NOP())

    def nerapa_battle_mod(self):
        boss_pack_id = self.get_boss("Nerapa")

        space = Reserve(0xada48, 0xada4e, "floating continent invoke battle nerapa", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def escape_mod(self, npc_id, airship_instructions):
        space = Reserve(0xae3ec, 0xae3f0, "floating continent get outta here dialog", field.NOP())

        space = Reserve(0xa57c0, 0xa57c0, "floating continent update character created at escape")
        space.write(npc_id)
        space = Reserve(0xa57c2, 0xa57c2, "floating continent update character placed on map at escape")
        space.write(npc_id)
        space = Reserve(0xa57cc, 0xa57cc, "floating continent update character shows at escape")
        space.write(npc_id)
        space = Reserve(0xa57cd, 0xa57cd, "floating continent update character animates in at escape")
        space.write(npc_id)
        space = Reserve(0xa57e1, 0xa57e3, "floating continent skip shadow arrives at airship dialog", field.NOP())
        if not (self.MAP_SHUFFLE and self.reward3.type == RewardType.CHARACTER):
            # For map shuffle character reward, use this space to branch to exit animation (see below)
            space = Reserve(0xa57ea, 0xa57ea, "floating continent update character who follows party to escape")
            space.write(npc_id)

        space = Reserve(0xa48cc, 0xa48cf, "floating continent do not clear shadow bits if don't wait at airship", field.NOP())

        src = [
            field.SetEventBit(event_bit.FINISHED_FLOATING_CONTINENT),
            field.StopScreenShake(),
            field.FreeScreen(),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
        ]
        if self.MAP_SHUFFLE:
            src += [
                airship_instructions,  # airship instructions include load map.  FinishCheck is in there.
                field.Return(),
            ]
            # We need to stop the screen from fading down before the reward is given.
            space = Reserve(0xa48d8, 0xa48d9, 'keep screen up for reward map shuffle', field.NOP())
        else:
            src += [
                airship_instructions,
                field.FinishCheck(),
                field.Return(),
            ]
        space = Write(Bank.CA, src, "floating continent return to airship")
        airship_return = space.start_address

        return_addr = [0xa48dd, 0xa48e2]
        if self.MAP_SHUFFLE and self.reward3.type == RewardType.CHARACTER:
            # The objective check must be before we leave the screen. This is fine for espers & items, but...
            # For characters, do it after the 2nd character lands
            # CA/57E6: B2    Call subroutine $CA5806  character jumps off FC after shadow arrives
            # ... shadow jumps off (we'll delete 0x03 after character select & skip this)
            # CA/5801: B2    Call subroutine $CA48D6
            return_addr = [0xa57e6, 0xa57eb]
        space = Reserve(return_addr[0], return_addr[1], "floating continent return to airship", field.NOP())
        space.write(
            field.Branch(airship_return),
        )

    def escape_character_mod(self, character):
        space = Reserve(0xa579d, 0xa57b2, "floating continent wait dialogs", field.NOP())
        if self.MAP_SHUFFLE:
            # CA/57E6: B2    Call subroutine $CA5806  character jumps off FC after shadow arrives
            # ... shadow jumps off (we'll delete npc after character select & skip this)
            # CA/5801: B2    Call subroutine $CA48D6
            escape_src = [
                field.RecruitAndSelectParty(character),
                field.DeleteEntity(character),
                field.HideEntity(character),
                field.RefreshEntities(),    # Maybe this prevents the 'recruit an npc' later?
                field.FadeInScreen(),
                field.FinishCheck(),   # Must be done here: might return to the world map!
                field.Call(0xa5806),   # complete jumping animation
                #field.Call(0xa48d6),  Replicate up to map load
                #Read(0xa48d6, 0xa48dc), # clear event bit, fade screen, wait for fade & animation.
                field.ClearEventBit(event_bit.CONTINUE_MUSIC_DURING_BATTLE),
                field.FadeOutScreen(speed=0x08),
                field.WaitForFade(),
                field.WaitForEntityAct(field_entity.PARTY0),
                field.FreeScreen(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        else:
            escape_src = [
                field.LoadMap(0x06, direction.DOWN, default_music = True, x = 16, y = 6, fade_in = False),
                field.RecruitAndSelectParty(character),
                field.FadeInScreen(),
            ]
        self.escape_mod(character, escape_src)

    def escape_esper_mod(self, esper):
        # use guest character to give esper reward
        guest_char_id = 0x0f
        guest_char = self.maps.get_npc(0x189, guest_char_id)

        random_sprite = self.characters.get_random_esper_item_sprite()
        random_sprite_palette = self.characters.get_palette(random_sprite)

        space = Reserve(0xa579d, 0xa57b2, "floating continent wait dialogs", field.NOP())
        space.write(
            field.SetSprite(guest_char_id, random_sprite),
            field.SetPalette(guest_char_id, random_sprite_palette),
            field.RefreshEntities(),
        )

        escape_src = [
            field.DeleteEntity(guest_char_id),
            field.RefreshEntities(),
        ]
        if self.MAP_SHUFFLE:
            escape_src = [
                field.AddEsper(esper),
                field.FinishCheck(),
                field.Dialog(self.espers.get_receive_esper_dialog(esper)),
                field.FadeOutScreen(),
                field.WaitForFade(),
            ] + GoToSwitchyard(self.exit_id, map='field')
        else:
            escape_src += [
                field.LoadMap(0x06, direction.DOWN, default_music = True, x = 16, y = 6, fade_in = True, entrance_event = True),
                field.AddEsper(esper),
                field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            ]
        self.escape_mod(guest_char_id, escape_src)

    def map_shuffle_mod(self):
        # Modify entrance event to split between Boss #1 and Boss #2
        src_after_boss1 = [
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.SetSpriteLayer(2),
                            field_entity.AnimateSurprised(),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL),
                            field_entity.AnimateHighJump(),
                            field_entity.Move(direction=direction.DOWN, distance=2),
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpriteLayer(0)
                            ),
            field.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.SetEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.Call(field.HEAL_PARTY_HP_MP_STATUS),
        ] + GoToSwitchyard(self.entry_id, map='field')
        space = Write(Bank.CA, src_after_boss1, "Map Shuffle Split after FC boss 1")
        self.boss_1_split_addr = space.start_address

        space = Reserve(0xa5a27, 0xa5a35, "Animation fall off airship after ultros/chupon", field.NOP())
        space.write(field.Branch(self.boss_1_split_addr))

        # Write switchyard tile.  The event needs to be a straight LoadMap call.
        # We will write one on the assumption that it is overwritten correctly.
        # src = [field.Branch(ENTRY_EVENT_CODE_ADDR)]
        src = [
            field.LoadMap(0x18a, x=4, y=12, direction=direction.DOWN,
                          default_music=True, fade_in=True, entrance_event=True),  # Failsafe
            field.Return()
        ]
        AddSwitchyardEvent(self.entry_id, self.maps, src=src)

        # Write the Floating Continent entry code:
        # Get the connecting exit
        self.parent_map = [0x000, 117, 162]
        if self.exit_id in self.maps.door_map.keys():
            if self.maps.door_map[1557] != 1556:  # Hack, don't update if connection is vanilla
                self.parent_map = self.maps.get_connection_location(self.exit_id)
        # Force update the parent map here
        #src_addl = [field.SetParentMap(self.parent_map[0], direction.DOWN, self.parent_map[1], self.parent_map[2] - 1)]
        src_addl = []
        if self.parent_map[0] == 1:
            # Update world
            src_addl += [field.ClearEventBit(event_bit.IN_WOR)]

        self.need_shadow_dialog = 0x0873
        self.dialogs.set_text(self.need_shadow_dialog, "Gotta wait for SHADOW...<end>")

        self.go_to_FC_dialog = 0x0851  # use "Kefka, Gestahl, and the Statues..."
        self.dialogs.set_text(self.go_to_FC_dialog,
                              "Land on the Floating Continent?<line><choice> Yes<line><choice> No<end>")

        self.enter_fc_address = self.air_force_battle_addr + 29
        # 0xa5a42 is modified earlier to:
        # field.Call(self.enter_floating_continent_function),
        # field.Call(self.delete_lights_function), # delete lights so airship shows up
        # We need to replicate this & the character animation to avoid fading up the screen again.
        # 0xa5a42 + 4 (Call takes 4 bits)
        self.something_curious_dialog = 0x0850

        # First, don't allow repeating the FC.  Show the "On That Day..." event instead & return to map.
        src = [
            field.BranchIfEventBitClear(event_bit.FINISHED_FLOATING_CONTINENT, "FC_OK"),   # No repeat FC
            field.LoadMap(0x003, x=8, y=16, direction=direction.DOWN, default_music=True, fade_in=False, entrance_event=True),
            field.FadeOutSong(0x1d),
            field.Dialog(0x0877, wait_for_input=False, inside_text_box=False, top_of_screen=False),  # On that day...
            field.Pause(seconds=2),
            field.FadeInScreen(speed=0x08),
            field.Pause(seconds=4),
            field.FadeOutScreen(speed=0x10),
            field.WaitForFade(),
            field.FadeSongVolume(fade_time=0x1d, volume=0xC0), # [0xf3, 0x1d],    # fade in previous song
        ] + GoToSwitchyard(self.exit_id, map='field') + [
            "FC_OK",
            field.LoadMap(0x18a, x=4, y=8, direction=direction.DOWN,
                          default_music=True, fade_in=False, entrance_event=True),  # Read(0xa041c, 0xa0421)
        ]
        src += src_addl  # add parent map update, world bit update if necessary.
        # Write the entrance animation & logic
        src += [
            field.HideEntity(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetPosition(x=0, y=0)),
            field.FadeInScreen(),
            field.WaitForFade(),
        ]
        if self.args.character_gating:
            src += [
                field.BranchIfEventBitSet(event_bit.character_recruited(self.events["Floating Continent"].character_gate()),
                                            "HAVE_SHADOW"),
                field.Dialog(self.need_shadow_dialog, wait_for_input=True),
                field.Branch("LEAVE_FC"),
                "HAVE_SHADOW",
            ]
        src += [
            field.DialogBranch(self.go_to_FC_dialog, "GO_TO_FC", "LEAVE_FC"),
            "GO_TO_FC",
            # If already defeated Boss #2, just go to FC
            field.BranchIfEventBitSet(event_bit.DEFEATED_AIR_FORCE, "SKIP_FC_BOSS2"),  # custom event bit
            field.Dialog(self.something_curious_dialog, wait_for_input=True),
            field.Branch(self.air_force_battle_addr),
            "SKIP_FC_BOSS2",
            field.HoldScreen(),
            field.Call(self.delete_lights_function),  # Need to rewrite this to avoid blinking
            field.ShowEntity(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetPosition(x=4, y=0),
                            field_entity.AnimateFrontHandsUp(),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.Move(direction=direction.DOWN, distance=4),
                            field_entity.AnimateKneeling()
                            ),
            field.Branch(self.enter_fc_address),
            "LEAVE_FC",
            field.HoldScreen(),
            field.ShowEntity(field_entity.PARTY0),
            field.PlaySoundEffect(186),  # falling
            field.EntityAct(field_entity.PARTY0, False,
                            field_entity.SetSpeed(field_entity.Speed.FAST),
                            field_entity.DisableWalkingAnimation(),
                            field_entity.AnimateFrontHandsUp(),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpeed(field_entity.Speed.FASTEST),
                            field_entity.Move(direction=direction.DOWN, distance=8),
                            field_entity.SetSpeed(field_entity.Speed.NORMAL)
                            ),
            field.EntityAct(field_entity.CAMERA, False,
                           field_entity.SetSpeed(field_entity.Speed.NORMAL),
                           field_entity.Move(direction=direction.DOWN, distance=4),
                           ),
            field.WaitForEntityAct(field_entity.CAMERA),
            field.WaitForEntityAct(field_entity.PARTY0),
            field.HideEntity(field_entity.PARTY0),
            field.FreeScreen(),
        ] + GoToSwitchyard(self.exit_id, map='field')
        # We need a fixed location to put this.  Bit length ~ 60 bits?
        # look at 0xa48e3 (end of escape sequence)
        space = Reserve(ENTRY_EVENT_CODE_ADDR, ENTRY_EVENT_CODE_ADDR + 153, "Floating Continent entry code modified")
        space.write(src)
        #print('FC entrance event length: ', space.end_address - space.start_address)

        # Write switchyard to handle return
        # (2b) Add the switchyard tile that handles exit to the Falcon
        # Note we will have to receive the reward before returning!  in escape_mod().
        src = [
            field.LoadMap(0x006, direction.DOWN, default_music = True, x = 16, y = 6, fade_in=True, entrance_event=True),
            field.Return()
        ]
        AddSwitchyardEvent(self.exit_id, self.maps, src=src)

        # (2c) Need to set DEFEATED_AIR_FORCE after first entry.
        # handled in airship_battle_mod().

        # (3) Update post-IAF entry: use switchyard.
        # CA/5986: B2    Call subroutine $CA5ABE (jump off airship animation)
        # CA/598A: B2    Call subroutine $CA5A42 (land on FC, right after boss #2: 0xa5a3b).
        iaf_skip_src = [
            field.FreeScreen(),
            field.SetEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
        ] + GoToSwitchyard(self.entry_id, map='field')
        space_iaf_skip = Write(Bank.CA, iaf_skip_src, 'IAF skip mod')
        space = Reserve(0xa598a, 0xa598d, "Call load FC after boss 2 mod")
        space.write(field.Call(space_iaf_skip.start_address))

        # (4) Update airship return before atma wpn
        # CA/5A96: 6B    Load map $0006 (Blackjack, upper deck (general use / "The world is groaning in pain")) instantly, (upper bits $0400), place party at (16, 6), facing up
        # This includes the animation.
        if self.maps.door_map[self.exit_id] == self.entry_id:
            # Keep the animation if returning to the airship
            pass
        else:
            # Use the switchyard exit
            space = Reserve(0xa5a96, 0xa5a9c, "return to airship mid FC edit")
            space.write(GoToSwitchyard(self.exit_id, map='field'))

        # (5) Modify warp behavior
        # We will add a new event bit to track special warp to Blackjack
        src_warp = [
            field.ClearEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.ClearEventBit(event_bit.IN_WOR),
            field.LoadMap(map_id=0x006, x=16, y=6, direction=direction.LEFT,
                          default_music=True, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CC, src_warp, "New FC warp code")
        fc_warp_addr = space.start_address
        self.warps.add_warp(event_bit.FLOATING_CONTINENT_WARP_OPTION, fc_warp_addr)


    @staticmethod
    def entrance_door_patch():
        # self-contained code to be called in door rando after entering Floating Continent (1557)
        # to be used in event_exit_info.entrance_door_patch()
        return [field.Branch(ENTRY_EVENT_CODE_ADDR)]

    @staticmethod
    def return_door_patch():
        # self-contained code to be called in door rando upon returning to airship (1556)
        # to be used in event_exit_info.entrance_door_patch()
        src = [
            field.LoadMap(0x006, x=16, y=6, direction=direction.DOWN, default_music=True, fade_in=False, entrance_event=True),
            field.ClearEventBit(event_bit.FLOATING_CONTINENT_WARP_OPTION),
            field.ShowEntity(field_entity.PARTY0),
            field.HoldScreen(),
            field.Branch(0xa5a9d),  # complete animation
        ]
        return src