from event.event import *
import random

class Start(Event):
    def name(self):
        return "Start"

    def init_rewards(self):
        party = [None] * len(self.args.start_chars)

        # assign explicit character rewards first to prevent randomly choosing them first
        # e.g. random, random, random, terra choosing terra first, second or third and making her unavailable fourth
        for index, start_char in enumerate(self.args.start_chars):
            if start_char != "random" and start_char != "randomngu":
                party[index] = self.characters.get_by_name(start_char).id
                self.characters.set_unavailable(party[index])

        gogo_umaro = [self.characters.GOGO, self.characters.UMARO]
        for index, start_char in enumerate(self.args.start_chars):
            if start_char == "random":
                party[index] = self.characters.get_random_available()
            elif start_char == "randomngu":
                party[index] = self.characters.get_random_available(exclude = gogo_umaro)

        # assign chosen character rewards
        for character_id in party:
            if character_id is not None:
                reward = self.add_reward(RewardType.CHARACTER)
                reward.id = character_id
                reward.type = RewardType.CHARACTER

    def init_event_bits(self, space):
        self.event_bit_init = space.start_address
        initialize_event_bits = [
            field.SetEventBit(event_bit.NAMED_SABIN),
            field.SetEventBit(event_bit.NAMED_SHADOW),

            field.SetEventBit(event_bit.MET_BANON),
            field.SetEventBit(event_bit.GOT_GENJI_GLOVES_OR_GAUNTLET),

            field.SetEventBit(event_bit.FINISHED_LOCKE_SCENARIO),
            field.SetEventBit(event_bit.FINISHED_TERRA_SCENARIO),
            field.SetEventBit(event_bit.FINISHED_SABIN_SCENARIO),
            field.SetEventBit(event_bit.FINISHED_GESTAHL_DINNER),

            field.SetEventBit(event_bit.SAW_SHADOW_DREAM1),
            field.SetEventBit(event_bit.SAW_SHADOW_DREAM2),
            field.SetEventBit(event_bit.SAW_SHADOW_DREAM3),
            field.SetEventBit(event_bit.SAW_SHADOW_DREAM4),

            field.SetEventBit(event_bit.CONTINENT_IS_FLOATING),

            field.SetEventBit(event_bit.DISABLE_SAVE_POINT_TUTORIAL),
            field.SetEventBit(event_bit.DISABLE_CHOCOBO_TUTORIAL),

            field.SetEventWord(event_word.CHARACTERS_AVAILABLE, 0),
            field.SetEventWord(event_word.ESPERS_FOUND, 0),

            field.SetBattleEventBit(battle_bit.MAGIC_POINTS_AFTER_BATTLE),
        ]

        # Handle event bits specific to door randomizer
        if self.args.door_randomize_all or self.args.door_randomize_each or self.args.door_randomize_dungeon_crawl \
                or self.args.door_randomize_phantom_train or self.args.door_randomize_cyans_dream:
            # Deconflict Siegfried event bit:  shared with Lump Of Metal event bit 0x187 in vanilla.
            # CB/B7F8: C2    If ($1E80($1B0) [$1EB6, bit 0] is clear) or ($1E80($187) [$1EB0, bit 7] is set) or ($1E80($188) [$1EB1, bit 0] is set), branch to $CA5EB3 (simply returns)
            spc = Reserve(0xbb7f8, 0xbb801, "Siegfried event tile bit check", field.NOP())
            spc.write([field.ReturnIfAny([0x1B0, False, event_bit.FOUGHT_SIEGFRIED, True])])
            # CB/B8FC: D2    Set event bit $1E80($187) [$1EB0, bit 7]
            spc = Reserve(0xbb8fc, 0xbb8fd, "Fought Siegfried", field.NOP())
            spc.write([field.SetEventBit(event_bit.FOUGHT_SIEGFRIED)])

            # Deconflict "Lump of metal" bit from "Phantom Train" bit.  Originally 0x180
            # CB/91D9: C0    If ($1E80($180) [$1EB0, bit 0] is set), branch to $CB91E8
            spc = Reserve(0xb91d9, 0xb91de, "Lump of metal bit check", field.NOP())
            spc.write([field.BranchIfEventBitSet(event_bit.LUMP_OF_METAL_CHEST, 0xb91e8)])
            # CB/922D: D2    Set event bit $1E80($180) [$1EB0, bit 0]
            spc = Reserve(0xb922d, 0xb922e, "Lump of metal bit set", field.NOP())
            spc.write([field.SetEventBit(event_bit.LUMP_OF_METAL_CHEST)])

            # initialize new event bits
            initialize_event_bits += [
                field.ClearEventBit(event_bit.SET_PHANTOM_TRAIN_SWITCHES),
                field.ClearEventBit(event_bit.FOUGHT_SIEGFRIED),
                field.ClearEventBit(event_bit.LUMP_OF_METAL_CHEST)
            ]

        space.write(initialize_event_bits)


    def mod(self):
        self.intro_loop_mod()
        self.init_characters_mod()
        self.start_party_mod()
        self.start_esper_mod()
        self.start_gold_mod()
        self.start_items_mod()
        self.start_game_mod()

        # Warp stone modification
        if self.args.debug or self.args.door_randomize_dungeon_crawl:
            # Dungeon Crawl mode doesn't have a well-defined parent map.
            # Warp stones will always go to the airship over WOB Narshe.
            src = [
                field.Call(0xa0159),
                # 0x6b, 0xff, 0x25, 0x00, 0x00, 0x00, 0xff, 0xfe,  <- original warp to parent map
                field.LoadMap(0x00, direction.UP, default_music=False,
                              x=84, y=34, fade_in=True, airship=True),
                vehicle.SetPosition(84, 34),
                vehicle.ClearEventBit(event_bit.IN_WOR),  # we're going back to WoB
                field.End(),  # end of script
                field.Return(),  # return
            ]
            space = Write(Bank.CA, src, "new warp")
            warp_to_narshe = space.start_address

            space = Reserve(0xa0144, 0xa014e, "edited warp section dungeon crawl", field.NOP())
            space.write(
                field.Call(warp_to_narshe),
                field.End(),
            )

            # For safety, knock out the check for the phoenix cave warp bit.
            # CA/0138: C0    If ($1E80($2BF) [$1ED7, bit 7] is set), branch to $CA0154
            space = Reserve(0xa0138, 0xa013d, "skip phoenix cave custom warp bit check", field.NOP())

        elif self.args.map_shuffle:
            # In Map Shuffle, parent map is well-defined, but sometimes the parent world is different.
            # Update the world bit and return to parent map.
            src = [
                field.Call(0xa0159),
                field.UpdateWorldReturnToParentMap(),
                world.End(),  # end of script
            ]
            space = Write(Bank.CA, src, "warp update IN_WOR")
            warp_update = space.start_address

            space = Reserve(0xa0144, 0xa014e, "edited warp to respect world bit", field.NOP())
            space.write(
                field.Call(warp_update),
                world.End(),
            )

        # where the game begins after intro/pregame
        space = Reserve(0xc9a4f, 0xc9ad4, "setup and start game", field.NOP())
        space.write(
            field.Call(self.event_bit_init),
            field.Call(self.character_init),
            field.Call(self.start_party),
            field.Call(self.start_esper),
            field.Call(self.start_gold),
            field.Call(self.start_items),
            field.Call(self.start_game),

            field.CheckObjectives(),
            field.Return(),
        )

        for reward in self.rewards:
            self.log_reward(reward)

    def intro_loop_mod(self):
        space = Reserve(0xa5e34, 0xa5e7d, "create/initialize ??????/biggs/wedge", field.NOP())
        space.write(
            field.Branch(space.end_address + 1), # skip nops
        )

        space = Reserve(0xa5e8e, 0xa5e91, "call text intro, terra/wedge/vicks on cliff", field.NOP())
        space = Reserve(0xa5e92, 0xa5e92, "call magitek walking intro credits scene", field.NOP())

    def init_characters_mod(self):
        # this has to be done in a very specific way
        # MUST set properties before creating character
        # MUST create all characters in separate loop before deleting them all in a different loop
        #      (cannot create, initialize, refresh then delete all in same loop) (why?)
        # MUST delete all characters or some npcs won't show up (e.g. in narshe)
        # MUST refresh objects between chars created and deleted
        # to test these things: start new game with terra, immediately check for npc in narshe outside tutorial
        #                       start new game with terra, immediately go to doma and sleep (why do other inns work?)
        space = Allocate(Bank.CC, 207, "start character initialization", field.NOP())
        for character in range(self.characters.CHARACTER_COUNT):
            palette = self.characters.get_palette(character)
            space.write(
                field.SetProperties(character, character),
                field.CreateEntity(character),
                field.SetName(character, character),
                field.SetSprite(character, character),
                field.SetPalette(character, palette),
            )
        space.write(
            field.AddStatusEffects(self.characters.SHADOW, field.Status.DOG_BLOCK),
            field.RefreshEntities(),
            field.Call(field.DELETE_ALL_CHARACTERS),
            field.RefreshEntities(),

            field.Return(),
        )
        self.character_init = space.start_address

    def start_party_mod(self):
        src = []
        for reward in self.rewards:
            if reward.type == RewardType.CHARACTER:
                character = reward.id
                src += [
                    field.CreateEntity(character),
                    field.RecruitCharacter(character),
                    field.AddCharacterToParty(character, 1),
                ]

        src += [
            field.SetParty(1),
            field.RefreshEntities(),
            field.UpdatePartyLeader(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "start party")
        self.start_party = space.start_address

    def start_esper_mod(self):
        src = []

        for esper_id in self.espers.starting_espers:
            src += [
                field.AddEsper(esper_id, sound_effect = False)
            ]

        src += [
            field.Return()
        ]

        space = Write(Bank.CC, src, "start espers")
        self.start_esper = space.start_address

    def start_gold_mod(self):
        gold = self.args.gold
        if self.args.debug:
            gold += 300000

        src = []
        max_value = 2 ** 16 - 1 # AddGP has 2 byte argument
        while gold > max_value:
            src += [
                field.AddGP(max_value),
            ]
            gold -= max_value
        if gold > 0:
            src += [
                field.AddGP(gold),
            ]
        src += [
            field.Return(),
        ]
        space = Write(Bank.CC, src, "start gold")
        self.start_gold = space.start_address

    def start_items_mod(self):
        src = []
        for mc in range(self.args.start_moogle_charms):
            src += [
                field.AddItem("Moogle Charm", sound_effect = False),
            ]
        for mc in range(self.args.start_sprint_shoes):
            src += [
                field.AddItem("Sprint Shoes", sound_effect = False),
            ]
        for ws in range(self.args.start_warp_stones):
            src += [
                field.AddItem("Warp Stone", sound_effect = False),
            ]
        for fd in range(self.args.start_fenix_downs):
            src += [
                field.AddItem("Fenix Down", sound_effect = False),
            ]

        tools = ["NoiseBlaster", "Bio Blaster", "Flash", "Chain Saw",
                 "Debilitator", "Drill", "Air Anchor", "AutoCrossbow"]
        start_tools = random.sample(tools, self.args.start_tools)
        for tool in start_tools:
            src += [
                field.AddItem(tool, sound_effect = False),
            ]

        from constants.items import id_name
        from data.shop_item_tiers import tiers
        from data.item import Item
        junk = []
        junk += tiers[Item.WEAPON][0]
        junk += tiers[Item.SHIELD][0]
        junk += tiers[Item.HELMET][0]
        junk += tiers[Item.ARMOR][0]
        junk += tiers[Item.RELIC][0]

        start_junk = random.sample(junk, self.args.start_junk)

        for junk_id in start_junk:
            src += [
                field.AddItem(id_name[junk_id], sound_effect = False)
            ]

        if self.args.debug:
            src += [
                field.AddItem("Dried Meat", sound_effect = False),
                field.AddItem("Dried Meat", sound_effect = False),
                field.AddItem("Dried Meat", sound_effect = False),
                field.AddItem("Warp Stone", sound_effect = False),
                field.AddItem("Warp Stone", sound_effect = False),
                field.AddItem("Warp Stone", sound_effect = False),
            ]
            for fd in range(99):
                src += [
                    field.AddItem("Warp Stone", sound_effect=False),
                ]

        src += [
            field.Return(),
        ]
        space = Write(Bank.CC, src, "start items")
        self.start_items = space.start_address

    def start_game_mod(self):
        src = [
            # place airship on wob, right outside narshe, start on airship deck
            field.LoadMap(0x00, direction.DOWN, default_music = False,
                          x = 84, y = 34, fade_in = True, airship = True),
            vehicle.SetPosition(84, 34),
            vehicle.LoadMap(0x06, direction.DOWN, default_music = True,
                            x = 16, y = 6, entrance_event = True),

            field.EntityAct(field_entity.PARTY0, True,
                field_entity.CenterScreen(),
            ),
            field.ShowEntity(field_entity.PARTY0),
            field.RefreshEntities(),
            field.FreeScreen(),
            field.FadeInScreen(speed = 4),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "start game")
        self.start_game = space.start_address
