from event.event import *

class OwzerMansion(Event):
    def name(self):
        return "Owzer Mansion"

    def character_gate(self):
        return self.characters.RELM

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.relm_npc_id = 0x13
        self.relm_npc = self.maps.get_npc(0x0d0, self.relm_npc_id)

        self.dialog_mod()

        if(self.args.flashes_remove_most):
            self.flash_mod()

        if self.args.character_gating:
            self.add_gating_condition()

        if not self.args.fixed_encounters_original:
            self.fixed_battles_mod()
        self.chadarnook_battle_mod()

        # remove return instruction (and direction requirements) so player does not have to go click on bookshelf
        space = Reserve(0xb4dc5, 0xb4dcd, "owzer mansion return after defeating chadarnook", field.NOP())
        space = Reserve(0xb4dea, 0xb4ded, "owzer mansion turn party left at bookshelf", field.NOP())
        space = Reserve(0xb4dee, 0xb4df4, "owzer mansion turn relm npc right", field.NOP())

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)
        self.finish_check_mod()

        self.log_reward(self.reward)

        if self.args.door_randomize_all or self.args.door_randomize_dungeon_crawl:
            # Remove warp-to-Jidoor from end of Chadarnook cutscene
            space = Reserve(0xb4e1f, 0xb4e24, "owzer mansion warp to Jidoor", field.NOP())
            src = [
                field.HideEntity(self.relm_npc_id),
                field.FadeInScreen()
            ]
            space.write(src)

            self.door_timer_mod()
            self.painting_mod()

    def flash_mod(self):
        space = Reserve(0xb4d10, 0xb4d11, "owzer mansion flash", field.NOP())

    def dialog_mod(self):
        space = Reserve(0xb4d0d, 0xb4d0f, "owzer mansion help that painting!!", field.NOP())
        space = Reserve(0xb4d12, 0xb4d17, "owzer mansion we can't attack this masterpiece", field.NOP())
        space = Reserve(0xb4d60, 0xb4d62, "owzer mansion relax! the monster croaked!", field.NOP())
        space = Reserve(0xb4d80, 0xb4d82, "owzer mansion thanks for saving the day", field.NOP())
        space = Reserve(0xb4d90, 0xb4d92, "owzer mansion what was a monster doing in that picture", field.NOP())
        space = Reserve(0xb4d9d, 0xb4d9f, "owzer mansion where is the stone", field.NOP())
        space = Reserve(0xb4dde, 0xb4de0, "owzer mansion this is magicite", field.NOP())
        space = Reserve(0xb4df5, 0xb4df7, "owzer mansion i have to go", field.NOP())

    def add_gating_condition(self):
        src = [
            Read(0xb4930, 0xb4943), # in wor, haven't fought chadarnook, facing up, press A
            field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), "STAY_AWAY"),
            Read(0xb4944, 0xb4955), # toggle light

            "STAY_AWAY",
            field.Dialog(2703, wait_for_input = True, inside_text_box = False),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "owzer mansion light switch character gate")
        light_switch = space.start_address

        space = Reserve(0xb4930, 0xb4955, "owzer mansion light toggle", field.NOP())
        space.write(
            field.Branch(light_switch),
        )

    def fixed_battles_mod(self):
        # change backgrounds to not have wall with blank painting on left for back/pincer attacks
        dahling_pack = 402
        nightshade_pack = 403
        still_life_pack = 404
        battle_background = 43 # inside building

        fixed_battles = [(dahling_pack, 0xb47db), (nightshade_pack, 0xb4821), (still_life_pack, 0xb4c5d)]

        for pack_id_address in fixed_battles:
            pack_id = pack_id_address[0]
            start_address = pack_id_address[1]
            end_address = start_address + 2

            space = Reserve(start_address, end_address, "owzer mansion invoke fixed battle")
            space.write(
                field.InvokeBattle(pack_id, battle_background, check_game_over = False),
            )

    def chadarnook_battle_mod(self):
        boss_pack_id = self.get_boss("Chadarnook")

        if boss_pack_id == self.enemies.packs.get_id("Chadarnook"):
            battle_background = 32 # owzer's house, painting

            space = Reserve(0xb4d18, 0xb4d1e, "owzer mansion invoke battle chadarnook", field.NOP())
            space.write(
                field.InvokeBattleType(boss_pack_id, field.BattleType.FRONT, battle_background),
            )
        else:
            battle_background = 43 # inside building

            space = Reserve(0xb4d18, 0xb4d1e, "owzer mansion invoke battle chadarnook", field.NOP())
            space.write(
                field.InvokeBattle(boss_pack_id, battle_background),
            )

    def character_mod(self, character):
        self.relm_npc.sprite = character
        self.relm_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xb4de1, 0xb4de7, "owzer mansion get startlet esper", field.NOP())

        space = Reserve(0xb4dfd, 0xb4e1c, "owzer mansion add relm", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
        )

    def esper_mod(self, esper):
        self.relm_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.relm_npc.palette = self.characters.get_palette(self.relm_npc.sprite)

        space = Reserve(0xb4de3, 0xb4de7, "owzer mansion get esper", field.NOP())
        space.write(
            field.AddEsper(esper, sound_effect = False),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        )

        space = Reserve(0xb4dfd, 0xb4e1c, "owzer mansion add relm", field.NOP())

    def item_mod(self, item):
        self.relm_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.relm_npc.palette = self.characters.get_palette(self.relm_npc.sprite)

        space = Reserve(0xb4de3, 0xb4de7, "owzer mansion get item", field.NOP())
        space.write(
            field.AddItem(item, sound_effect = False),
            field.Dialog(self.items.get_receive_dialog(item)),
        )

        space = Reserve(0xb4dfd, 0xb4e1c, "owzer mansion add relm", field.NOP())

    def finish_check_mod(self):
        src = [
            field.Call(field.HIDE_PARTY_MEMBERS_EXCEPT_LEADER),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "owzer mansion finish check")
        finish_check = space.start_address

        space = Reserve(0xb4e25, 0xb4e28, "owzer mansion call finish check", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def door_timer_mod(self):
        # Overwrite the check to see if Chadarnook has been killed (so this room always works)
        space = Reserve(0xb4962, 0xb4967, "owzer mansion start door timer", field.NOP())
        space.write([0x3a])  # enable player to move while commands execute

        # Write a 2nd event tile (so the door timer will start if entering the room through other door)
        from data.map_event import MapEvent
        new_event = MapEvent()
        new_event.x = 88
        new_event.y = 51
        new_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(0x0cf, new_event)

    def painting_mod(self):
        # Overwrite the check to see if Chadarnook has been killed (so you can always fight the painting)
        # Painting 1:
        space = Reserve(0xb47c2, 0xb47c7, "owzer mansion painting 1")
        space.write([
            field.BranchIfEventBitClear(event_bit.DEFEATED_PAINTING_1, 0xb47ce)
        ])

