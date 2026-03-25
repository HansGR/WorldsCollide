from event.event import *
from data.map_exit_extra import exit_data, special_airship_locations
from data.rooms import exit_world

class EbotsRock(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle
        self.DOOR_RANDOMIZE = (args.door_randomize_all
                          or args.door_randomize_crossworld
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each
                          or args.ruination_mode)

    def name(self):
        return "Ebot's Rock"

    def character_gate(self):
        return self.characters.STRAGO

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.FOUND_EBOTS_ROCK),
            field.SetEventBit(event_bit.MET_EBOTS_ROCK_CHEST),
            field.SetEventBit(npc_bit.HIDON_EBOTS_ROCK),

            field.SetEventWord(event_word.CORAL_FOUND, 0),
        )

    def mod(self):
        self.exit_loc = [0x01, 249, 224]
        self.airship_thamasa = [0x001, 251, 230]
        self.EXIT_IN_WOB = False
        self.MOVE_AIRSHIP_TO_THAMASA = True

        if self.MAP_SHUFFLE:
            # modify exit position
            exit_id = 1546
            if exit_id in self.maps.door_map.keys():
                self.exit_loc = self.maps.get_connection_location(exit_id, parent_map_ok=True)
                self.EXIT_IN_WOB = (self.exit_loc[-1] == 0)

            # modify airship warp position
            thamasa_id = 1261
            if thamasa_id in self.maps.door_map.keys():
                if self.maps.door_map[thamasa_id] in special_airship_locations.keys():
                    self.airship_thamasa = special_airship_locations[self.maps.door_map[thamasa_id]]
                else:
                    self.airship_thamasa = self.maps.get_connection_location(thamasa_id)

        elif self.DOOR_RANDOMIZE:
            # Dungeon crawl / ruination: entry point may not be the world map.
            # Update exit_loc from door 1546's randomized connection.
            exit_id = 1546
            if exit_id in self.maps.door_map.keys():
                self.exit_loc = self.maps.get_connection_location(exit_id)
                self.EXIT_IN_WOB = (self.exit_loc[3] == 0)

            if self.args.ruination_mode:
                # Ruination: no airship movement needed.
                self.MOVE_AIRSHIP_TO_THAMASA = False
            else:
                # Dungeon crawl: move airship to Thamasa's world map connection
                # only if Thamasa actually connects to a world map.
                thamasa_id = 1261
                if thamasa_id in self.maps.door_map.keys():
                    thamasa_loc = self.maps.get_connection_location(thamasa_id)
                    if thamasa_loc[0] in [0x0, 0x1]:
                        if self.maps.door_map[thamasa_id] in special_airship_locations.keys():
                            self.airship_thamasa = special_airship_locations[self.maps.door_map[thamasa_id]]
                        else:
                            self.airship_thamasa = thamasa_loc[:3]
                    else:
                        self.MOVE_AIRSHIP_TO_THAMASA = False
                else:
                    self.MOVE_AIRSHIP_TO_THAMASA = False

        self.find_gungho_hurt_mod()
        self.chest_mod()
        self.hidon_mod()
        self.hidon_battle_mod()

        self.warp_to_chest_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def find_gungho_hurt_mod(self):
        space = Reserve(0xb75d5, 0xb75d5, "ebots rock relm and strago find gungho hurt in thamasa", field.NOP())
        space.write(
            field.Return(),
        )

    def chest_mod(self):
        # shorten chest dialog, remove first page "I like to eat Coral! Have any?"
        self.dialogs.set_text(2881, "Hand over some “Coral”?<line><choice>(Sure.)<line><choice>(I don't think so.)<end>")

        # shorten requirements not met dialog, remove "Munch <wait>munch <wait>munch <wait><line>"
        self.dialogs.set_text(2879, "Muurp…that was great. <wait 60 frame><line>Bring me some more!!<end>")

        space = Reserve(0xb70eb, 0xb70ed, "ebots rock Skinflint! Git outta here!", field.NOP())
        space = Reserve(0xb7137, 0xb713f, "ebots rock I'm not happy unless I have plenty to eat!", field.Return())

        if self.args.character_gating:
            space = Reserve(0xb7141, 0xb7149, "ebots rock require hidon defeated or strago to pass chest", field.NOP())
            space.add_label("CHEST_STUFFED", 0xb714f)
            space.write(
                field.BranchIfEventBitSet(event_bit.character_recruited(self.character_gate()), "CHEST_STUFFED"),
            )
        else:
            space = Reserve(0xb7141, 0xb714e, "ebots rock require hidon defeated or strago to pass chest", field.NOP())

        space = Reserve(0xb7153, 0xb717f, "ebots rock chest full, blurp, pause, party wave arms", field.NOP())
        space.copy_from(0xb70b4, 0xb70bd) # close chest

        space = Reserve(0xb7197, 0xb7197, "ebots rock pause as chest leaves", field.NOP())
        space = Reserve(0xb71a0, 0xb71a2, "ebots rock TREASURE: Eh!! What the?!", field.NOP())

    def hidon_mod(self):
        space = Reserve(0xb71c4, 0xb71ce, "ebots rock that's hidon!", field.NOP())
        space = Reserve(0xb71e8, 0xb71e9, "ebots rock hide party after hidon", field.NOP())

    def hidon_battle_mod(self):
        boss_pack_id = self.get_boss("Hidon")

        space = Reserve(0xb71d2, 0xb71d8, "ebots rock invoke battle hidon", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def character_mod(self, character):
        # gungho sitting at table listening to strago excitedly talk about defeating hidon
        gungho_table_npc_id = 0x22
        gungho_table_npc = self.maps.get_npc(0x15d, gungho_table_npc_id)
        gungho_table_npc.sprite = character
        gungho_table_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xb71ec, 0xb71f0, "ebots rock show strago after hidon defeated", field.NOP())

        space = Reserve(0xb71f5, 0xb7216, "ebots rock strago celebrating after hidon defeated", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xb721a, 0xb721b, "ebots rock disable collisions for strago", field.NOP())
        space = Reserve(0xb7221, 0xb7225, "ebots rock strago runs down", field.NOP())
        space = Reserve(0xb7233, 0xb7234, "ebots rock wait for strago character commands", field.NOP())
        space = Reserve(0xb7238, 0xb7239, "ebots rock enable collisions for strago", field.NOP())

        if self.MAP_SHUFFLE or self.DOOR_RANDOMIZE:
            # Vanilla code here moves the airship to Thamasa on the world map.
            # NOP it out and only rewrite if we actually need to move the airship.
            space = Reserve(0xb723b, 0xb7243, "ebots rock airship move", field.NOP())
            if self.MOVE_AIRSHIP_TO_THAMASA:
                space.write(
                    field.LoadMap(self.airship_thamasa[0], direction.DOWN, default_music=False, x=self.airship_thamasa[1],
                                  y=self.airship_thamasa[2], fade_in=False, airship=True),
                    vehicle.SetPosition(self.airship_thamasa[1], self.airship_thamasa[2]),
                )

        # NOTE: just finished moving airship to thamasa, use vehicle command to load map here
        space = Reserve(0xb7244, 0xb7249, "ebots rock after hidon load strago's room map", field.NOP())
        space.write(
            vehicle.LoadMap(0x15d, direction.UP, default_music = False, x = 45, y = 21, fade_in = False, update_parent_map = True),
        )

        space = Reserve(0xb724e, 0xb7315, "ebots rock after hidon bedroom scene and that evening", field.NOP())
        space.write(
            field.HideEntity(0x23), # hide strago npc to be replaced with party

            # disable collisions and draw party on top of the chairs
            field.DisableEntityCollision(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpriteLayer(2)
            )
        )
        if self.MOVE_AIRSHIP_TO_THAMASA:
            space.write(
                field.SetParentMap(map_id=self.airship_thamasa[0], x=self.airship_thamasa[1],
                                   y=self.airship_thamasa[2] - 1, direction=direction.DOWN)
            )
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )
        # change strago npc to party
        space = Reserve(0xb7316, 0xb7316, "ebots rock dinner table strago")
        space.write(field_entity.PARTY0)
        space = Reserve(0xb7328, 0xb7328, "ebots rock dinner table strago")
        space.write(field_entity.PARTY0)
        space = Reserve(0xb7333, 0xb7333, "ebots rock dinner table strago")
        space.write(field_entity.PARTY0)
        space = Reserve(0xb733e, 0xb733e, "ebots rock dinner table strago")
        space.write(field_entity.PARTY0)
        space = Reserve(0xb734a, 0xb734a, "ebots rock dinner table strago")
        space.write(field_entity.PARTY0)

        # remove dialogs
        # strago's actions repeat while dialog is showing so add pauses to have animations play a little without dialogs
        space = Reserve(0xb7325, 0xb7327, "ebots rock there i was, in a cave that seemed endless", field.NOP())
        space.write(field.Pause(0.5)),
        space = Reserve(0xb733b, 0xb733d, "ebots rock G'pow!! Thwack!! Crash!!", field.NOP())
        space.write(field.Pause(2.0)),
        space = Reserve(0xb7347, 0xb7349, "ebots rock true meaning of the word, hero", field.NOP())
        space.write(field.Pause(2.0)),
        space = Reserve(0xb734e, 0xb7351, "ebots rock and then...", field.NOP())

        space = Reserve(0xb7356, 0xb73e0, "ebots rock relm gungho night scene", field.NOP())
        space.write(
            field.EnableEntityCollision(field_entity.PARTY0),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpriteLayer(0)
            ),
            field.RecruitAndSelectParty(character),
            field.Branch(space.end_address + 1), # skip nops
        )

        src = [
            Read(0xb73f2, 0xb73f7), # load strago's house map
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CB, src, "ebots rock finish check")
        finish_check = space.start_address

        space = Reserve(0xb73f2, 0xb73f7, "ebots rock load strago's house after character reward", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def esper_item_mod(self, esper_item_instructions):
        space = Reserve(0xb71ec, 0xb7216, "ebots rock show strago celebrating", field.NOP())
        space.write(
            field.Call(0xb7410), # unfade screen, wait for unfade
            esper_item_instructions,
            field.SetEventBit(event_bit.DEFEATED_HIDON),
            field.FinishCheck(),
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xb721a, 0xb721b, "ebots rock disable collisions for strago", field.NOP())
        space = Reserve(0xb7221, 0xb7225, "ebots rock strago runs down", field.NOP())
        space = Reserve(0xb722b, 0xb722c, "ebots rock temp song override before airship", field.NOP())
        space = Reserve(0xb7233, 0xb7234, "ebots rock wait for strago runs down", field.NOP())

        space = Reserve(0xb7238, 0xb73df, "ebots rock strago/relm/gungho events after hidon", field.NOP())
        space.copy_from(0xb73e1, 0xb73f0)  # event bits after hidon
        if self.EXIT_IN_WOB:
            space.write(
                field.ClearEventBit(event_bit.IN_WOR)
            )
        space.write(field.FreeScreen())
        if self.DOOR_RANDOMIZE and (self.exit_loc[0] in [0x0, 0x1]):
            # Door rando returning to world map: summon the airship.
            from event.switchyard import SummonAirship
            space.write(
                SummonAirship(self.exit_loc[0], x=self.exit_loc[1], y=self.exit_loc[2], fadeout=True)
            )
        elif self.DOOR_RANDOMIZE:
            # Door rando returning to interior room (ruination, or dungeon crawl
            # where Ebot's Rock was reached from a non-world-map room).
            space.write(
                field.LoadMap(self.exit_loc[0], direction.DOWN, default_music=True,
                              x=self.exit_loc[1], y=self.exit_loc[2], fade_in=True, entrance_event=True),
                field.Return(),
            )
        else:
            # Vanilla or map shuffle: exit to world map.
            space.write(
                field.LoadMap(self.exit_loc[0], direction.DOWN, default_music = True, x = self.exit_loc[1],
                              y = self.exit_loc[2]),
                world.End(),
            )

        space = Reserve(0xb73f1, 0xb73f9, "ebots rock load thamasa map", field.NOP())

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

    def warp_to_chest_mod(self):
        # If the player has sufficient Coral, make teleports have only 3 locations: Boss, Save, and Exit
        CORAL_EVENT_WORD = 0x07
        NORMAL_LOGIC_ADDR = 0xb6f0e # Normal Ebot's Cave branch logic location in ROM
        GO_TO_CHEST_ADDR = 0xb6fb5 # The address in ROM of the event instruction to go to Chest
        GO_TO_SAVE_ADDR = 0xb6fa3 # The address in ROM of the event instruction to go to Save point
        GO_TO_EXIT_ADDR = 0xb6fac # the address in ROM of the event instruction to go to the exit
        NUM_CORAL_ADDR = 0xb7109 # The address of the number of coral that the chest checks
        num_coral = Read(NUM_CORAL_ADDR, NUM_CORAL_ADDR+1)[0]

        src = [
            field.BranchIfEventWordEqual(CORAL_EVENT_WORD, num_coral, NORMAL_LOGIC_ADDR), #coral count == 21, branch to regular logic
            field.BranchIfEventWordLess(CORAL_EVENT_WORD, num_coral, NORMAL_LOGIC_ADDR),  #coral count  < 21, branch to regular logic
            # else, we've > 21
            field.BranchRandomly(GO_TO_CHEST_ADDR), # 50% chance to go to chest
            field.BranchRandomly(GO_TO_SAVE_ADDR),  # 50% chance to go to save
            field.Branch(GO_TO_EXIT_ADDR),      # else, go to entrance
        ]
        space = Write(Bank.CB, src, "Coral check to branch")
        check_coral = space.start_address

        space = Reserve(0xb6f01, 0xb6f04, "Call Ebot's Cave branch logic")
        space.write(field.Call(check_coral))
