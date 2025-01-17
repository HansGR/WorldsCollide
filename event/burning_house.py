from event.event import *

# TODO: only trigger this event in wob

class BurningHouse(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.DOOR_RANDOMIZE = (args.door_randomize_burning_house
                          or args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Burning House"

    def character_gate(self):
        return self.characters.STRAGO

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.MET_STRAGO_RELM),
            field.SetEventBit(event_bit.DEFEATED_KEFKA_THAMASA),
            field.SetEventBit(event_bit.LEO_BURIED_THAMASA),
            field.SetEventBit(event_bit.FINISHED_THAMASA_KEFKA),

            field.ClearEventBit(npc_bit.FIRST_MAYOR_THAMASA),
            field.ClearEventBit(npc_bit.STRAGO_THAMASA_HOME),
            field.ClearEventBit(npc_bit.PARTY_THAMASA_AFTER_KEFKA),
            field.ClearEventBit(npc_bit.GUNGHO_OUTSIDE_THAMASA),
            field.SetEventBit(npc_bit.THAMASA_CITIZENS),
        )

    def mod(self):
        if self.args.character_gating:
            self.add_gating_condition()

        self.enter_burning_house_mod()
        self.flame_eater_mod()
        self.wake_up_mod()

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()
        if self.MAP_SHUFFLE:
            self.map_shuffle_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def add_gating_condition(self):
        # increase the price from 1500
        self.dialogs.set_text(1936, "You're strangers…<page>100000000 GP<line><choice> (Well, okay.)<line><choice> (No way!)<end>")

        space = Reserve(0xbd774, 0xbd79c, "burning house inn stranger sleep", field.NOP())
        space.write(
            field.Call(field.NOT_ENOUGH_MONEY),
            field.Return(),
        )

        space = Reserve(0xbd73f, 0xbd746, "burning house inn stranger check", field.NOP())
        space.add_label("STRANGER_PRICE", 0xbd769),
        space.write(
            field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), "STRANGER_PRICE"),
        )

    def enter_burning_house_mod(self):
        # wake up in middle of night, enter burning house, skip scene with villagers outside burning house
        space = Reserve(0xbdcc7, 0xbdccd, "load burning house map", field.NOP())
        space.write(
            field.LoadMap(0x15f, direction.UP, default_music = True, x = 4, y = 11, fade_in = True),
            field.Return(),
        )

        # event at entrance of burning house
        space = Reserve(0xbe5e4, 0xbe621, "burning house entrance event", field.NOP())
        space.write(
            field.Return(),
        )

        if self.DOOR_RANDOMIZE:
            # Make entry to burning house repeatable by removing check for DEFEATED_FLAME_EATER
            space = Reserve(0xbd7bf, 0xbd7c4, "make burning house repeatable", field.NOP())

    def flame_eater_mod(self):
        boss_pack_id = self.get_boss("FlameEater")

        space = Reserve(0xbe793, 0xbe799, "burning house invoke battle flame eater", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

        if self.DOOR_RANDOMIZE:
            # Add a Return if flame eater was defeated
            space = Reserve(0xbe767, 0xbe78d, "burning house approach flame eater dialog", field.NOP())
            space.write(
                field.ReturnIfEventBitSet(event_bit.DEFEATED_FLAME_EATER),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                                field_entity.Move(direction.UP, 1),
                                ),
            )
        else:
            # split party, "Is this the source of our blaze...?"
            space = Reserve(0xbe76c, 0xbe78d, "burning house approach flame eater dialog", field.NOP())


    def defeated_flame_eater_mod(self, space):
        space.write(
            field.SetEventBit(event_bit.DEFEATED_FLAME_EATER),
            field.SetEventBit(npc_bit.SHADOW_AFTER_FLAME_EATER),
            field.HoldScreen(),
        )

    def wake_up_mod(self):
        src = [
            field.FadeOutSong(0x60),
            field.Pause(1),
            field.StartSong(0xb8),
            field.WaitForSong(),

            field.LoadMap(0x15a, direction.DOWN, default_music = True, x = 13, y = 16, fade_in = False, entrance_event = True),
            field.Call(field.UPDATE_LEADER_AND_SHOW_ALL_PARTY_MEMBERS),
            field.Call(field.DISABLE_COLLISIONS_FOR_PARTY_MEMBERS),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.SetPosition(15, 14), # top right bed
                field_entity.Turn(direction.DOWN),
            ),
            field.EntityAct(field_entity.PARTY1, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.SetPosition(11, 14), # top left bed
                field_entity.Turn(direction.DOWN),
            ),
            field.EntityAct(field_entity.PARTY2, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.SetPosition(15, 18), # bottom right bed
                field_entity.Turn(direction.DOWN),
            ),
            field.EntityAct(field_entity.PARTY3, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.SetPosition(11, 18), # bottom left bed
                field_entity.Turn(direction.DOWN),
            ),
            field.Call(field.HEAL_PARTY_HP_MP_STATUS),
            field.FadeInScreen(8),
            field.Pause(2.00),
            field.FinishCheck(),
            field.Call(field.GATHER_AFTER_INN),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "burning house wake up")
        self.wake_up = space.start_address

    def fixed_battles_mod(self):
        # BH has 12 fixed encounters that all share the same pack ID
        # to increase the variety of encounters, we are adding 1 more and swapping 6 of the flames to it
        # 415 is an otherwise unused encounter

        replaced_encounters = [
            (415, 0xBE6FF), 
            (415, 0xBE740),
            (415, 0xBE70C),
            (415, 0xBE733),
            (415, 0xBE726),
            (415, 0xBE74D),
        ]
        for pack_id_address in replaced_encounters:
            pack_id = pack_id_address[0]
            # first byte of the command is the pack_id
            invoke_encounter_pack_address = pack_id_address[1]+1
            space = Reserve(invoke_encounter_pack_address, invoke_encounter_pack_address, "flame invoke fixed battle (battle byte)")
            space.write(
                # subtrack 256 since WC stores fixed encounter IDs starting at 256
                pack_id - 0x100
            )

    def character_mod(self, character):
        shadow_npc_id = 0x1d
        shadow_npc = self.maps.get_npc(0x15f, shadow_npc_id)
        shadow_npc.sprite = character
        shadow_npc.palette = self.characters.get_palette(character)

        # strago jumps around, party finds relm
        space = Reserve(0xbe79e, 0xbe8da, "flame eater defeated", field.NOP())
        self.defeated_flame_eater_mod(space)
        space.write(
            field.CreateEntity(character),
            field.CreateEntity(0x1d),
            field.DeleteEntity(0x1b),
            field.RefreshEntities(),
            field.ShowEntity(0x1d),
            field.HideEntity(0x1b),

            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetPosition(49, 43),
                field_entity.AnimateKnockedOut(),
            ),
            field.EntityAct(field_entity.CAMERA, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.Move(direction.UP, 7),
            ),
            field.Branch(space.end_address + 1), # skip nop
        )

        # "I'll use a smoke bomb"
        space = Reserve(0xbea2c, 0xbea2e, "burning house smoke bomb dialog", field.NOP())

        if self.DOOR_RANDOMIZE:
            dog_npc_id = 0x1c
            # If door randomized, just replace the character where they were.
            # Talking to the dog will animate the exit to Thamasa Inn.
            space = Reserve(0xbea2f, 0xbea64, "burning house wake up", field.NOP())
            src = [
                field.RecruitAndSelectParty(character),
                # Two event bits cleared after animation:
                field.ClearEventBit(0x507),  # CB/EA40: DB    Clear event bit $1E80($507) [$1F20, bit 7]
                field.ClearEventBit(0x506),  # CB/EA42: DB    Clear event bit $1E80($506) [$1F20, bit 6]
                field.Call(self.delete_flameeater_npcs),
                field.EntityAct(field_entity.PARTY0, True,
                                field_entity.AnimateStandingFront(),
                                ),
                field.EntityAct(dog_npc_id, True,
                                field_entity.SetPosition(47, 43),
                                ),
                #field.FreeMovement(),
                field.FadeInScreen(),
                field.FreeScreen(),
                field.Return()
            ]
        else:
            space = Reserve(0xbea44, 0xbea64, "burning house wake up", field.NOP())
            src = [
                field.RecruitAndSelectParty(character),
                field.Branch(self.wake_up)
            ]

        space.write(src)

    def esper_item_mod(self, instructions):
        # strago jumps around, party finds relm
        space = Reserve(0xbe79f, 0xbea3e, "burning house esper item", field.NOP())
        self.defeated_flame_eater_mod(space)
        space.write(
            instructions,
            #field.FadeOutScreen(4),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xbea44, 0xbea64, "burning house wake up", field.NOP())
        if self.DOOR_RANDOMIZE:
            # if doors are randomized, don't auto go to wakeup
            space.write(
                field.Call(self.delete_flameeater_npcs),
                #field.FadeInScreen(),
                field.FreeScreen(),
                field.Return()
            )
        else:
            space.write(
                field.FadeOutScreen(4),
                field.Branch(self.wake_up),
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

    def door_rando_mod(self):
        # Make Burning House re-exitable by talking to the dog NPC
        # Copy animation from 0xbea27 ("I'll use a smoke bomb!")
        src_escape = [
            field.Call(0xb6abf),  # "Woof!"
            field.EntityAct(field_entity.PARTY0, True,
                            field_entity.AnimateKneeling(),
                            field_entity.Pause(1),
                            field_entity.AnimateFrontRightHandUp(),
                            field_entity.Pause(5),
                            field_entity.Turn(direction.DOWN),
                            field_entity.End()
                            ),
            field.MosaicScreen(5),
            field.PlaySoundEffect(0x85),  # Smoke Bomb
            field.FadeOutScreen(5),
            field.WaitForFade(),
            field.HoldScreen(),
            field.Branch(self.wake_up),
        ]
        space = Write(Bank.CB, src_escape, 'Smoke Bomb Escape from Burning House')

        dog_npc_id = 0x1c
        dog_npc = self.maps.get_npc(0x15f, dog_npc_id)
        dog_npc.event_address = space.start_address - EVENT_CODE_START

        # Place an event tile on [0x15f, 46, 54] that deletes fireball & Relm NPCs if boss is defeated.
        boss_npc_id = 0x18
        relm_npc_id = 0x1b
        shadow_npc_id = 0x1d
        src = [
            field.ReturnIfEventBitClear(event_bit.DEFEATED_FLAME_EATER),
            field.ReturnIfEventBitSet(0x1b5),
            field.DeleteEntity(boss_npc_id),
            field.HideEntity(boss_npc_id),
            field.DeleteEntity(relm_npc_id),
            field.HideEntity(relm_npc_id),
            field.DeleteEntity(shadow_npc_id),
            field.HideEntity(shadow_npc_id),
            field.SetEventBit(0x1b5),
            field.Return()
        ]
        space = Write(Bank.CB, src, "Burning House Delete NPCs if Boss Cleared")
        self.delete_flameeater_npcs = space.start_address

        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 46
        new_event.y = 54
        new_event.event_address = self.delete_flameeater_npcs - EVENT_CODE_START
        self.maps.add_event(0x15f, new_event)

        # Delete NPCs in Thamasa Inn to avoid softlocking.
        # We don't use them, and they appear if npc_bit.ATTACK_GHOSTS_PHANTOM_TRAIN (0x507) is set
        #thamasa_inn = 0x15a
        strago_npc_id = 0x11
        interceptor_npc_id = 0x12
        src = [
            field.DeleteEntity(strago_npc_id),
            field.HideEntity(strago_npc_id),
            field.DeleteEntity(interceptor_npc_id),
            field.HideEntity(interceptor_npc_id),
            field.Call(0xbd65f),
            field.Return(),
        ]
        space = Write(Bank.CB, src, 'Thamasa Inn Entrance Event hide npcs')
        hide_addr = space.start_address

        space = Reserve(0xbd6a3, 0xbd6a6, 'Thamasa Inn Entrance Event mod')
        space.write(field.Call(hide_addr))


    def map_shuffle_mod(self):
        # Change the entrance on the worldmap to skip bit checks & just load the map
        #enter_event = self.maps.get_event(0x0, 250, 128)
        #enter_event.event_address = 0xbd308 - EVENT_CODE_START
        from event.switchyard import GoToSwitchyard, AddSwitchyardEvent

        # (1a) Change the entry event to load the switchyard location
        event_id = 1504  # ID of Thamasa WoB entrance
        space = Reserve(0xbd2ee, 0xbd30e, 'Thamasa WoB Entrance', field.NOP())
        space.write(GoToSwitchyard(event_id, map='world'))
        # (1b) Add the switchyard event tile that handles entry to South Figaro Cave
        src = [
            field.LoadMap(0x154, direction=direction.UP, x=23, y=46, default_music=True, fade_in=True),
            field.Return()
        ]
        AddSwitchyardEvent(event_id, self.maps, src=src)
