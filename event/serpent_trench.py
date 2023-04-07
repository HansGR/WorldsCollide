from event.event import *

class SerpentTrench(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_serpent_trench
                          or args.door_randomize_all
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)

    def name(self):
        return "Serpent Trench"

    def character_gate(self):
        return self.characters.GAU

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
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

        self.log_reward(self.reward)

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
            field.LoadMap(0x00, direction.DOWN, default_music = False,
                          x = 84, y = 113, fade_in = False, airship = True),
            vehicle.SetPosition(84, 113),
            vehicle.ClearEventBit(event_bit.TEMP_SONG_OVERRIDE),
            vehicle.FadeLoadMap(0x5b, direction.LEFT, default_music = True,
                                x = 12, y = 11, fade_in = True, entrance_event = True),
            field.Return(),
        ]
        space = Write(Bank.CA, src, "serpent trench move airship to south figaro")
        self.move_airship_to_south_figaro = space.start_address

        src = [
            field.SetEventBit(event_bit.TEMP_SONG_OVERRIDE),
            field.LoadMap(0x00, direction.DOWN, default_music = False,
                          x = 116, y = 61, fade_in = False, airship = True),
            vehicle.SetPosition(116, 61),
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

    def door_rando_mod(self):
        ### Maybe write a class to handle switchyard map tile writing functions?  This repeats a lot of code. ###

        # Modifications for door rando
        from data.map_event import MapEvent
        from data.event_exit_info import event_exit_info

        switchyard_map = 0x005

        # (1a) Change the entry event to load the switchyard location
        enterID = 2041  # ID of cliff jump event
        switchyard_x = enterID % 128
        switchyard_y = enterID // 128

        space = Reserve(0xbc873, 0xbc879, 'Serpent Trench Cliff Jump entry modification')
        space.write([
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ])
        # (1b) Add the switchyard event tile that handles entry to Zone Eater
        src = [
            field.Branch(0xa8ae3),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Serpent Trench Entry Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

        # (2a) Change the Cave #1 Entry event to load the switchyard location
        cave1_id = 2045
        switchyard_x = cave1_id % 128
        switchyard_y = cave1_id // 128

        space = Reserve(0xa8c3a, 0xa8c40, 'Serpent Trench #1 to cave modification')
        space.write([
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ])
        # (2b) Add the switchyard event tile that handles entry to ST Cave #1
        src = [
            field.LoadMap(0x0af, direction=direction.UP, default_music=True,
                          x=44, y=16, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave entry Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

        # (3a) Edit the event tile in Cave #1 to go to a new script that goes to the switchyard
        cave1_exit_id = 2047
        switchyard_x = cave1_exit_id % 128
        switchyard_y = cave1_exit_id // 128
        src = [
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave exit Switchyard")

        location = event_exit_info[cave1_exit_id][5]
        cave1_exit_event = self.maps.get_event(location[0], location[1], location[2])
        cave1_exit_event.event_address = space.start_address - EVENT_CODE_START

        # (3b) Add the switchyard event tile that handles exit from ST Cave #1
        src = [
            field.Branch(0xa8c41),
            world.End()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave exit Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

        # (4a) Change the Cave #1 Entry event to load the switchyard location
        cave2_id = 2048
        switchyard_x = cave2_id % 128
        switchyard_y = cave2_id // 128

        space = Reserve(0xa8c8d, 0xa8c93, 'Serpent Trench #2 to cave modification')
        space.write([
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ])
        # (4b) Add the switchyard event tile that handles entry to ST Cave #2
        src = [
            field.LoadMap(0x0af, direction=direction.UP, default_music=True,
                          x=25, y=16, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave entry Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

        # (5a) Edit the event tile in Cave #2c to go to a new script that goes to the switchyard
        cave2_exit_id = 2051
        switchyard_x = cave2_exit_id % 128
        switchyard_y = cave2_exit_id // 128
        src = [
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave exit Switchyard")

        location = event_exit_info[cave2_exit_id][5]
        cave2_exit_event = self.maps.get_event(location[0], location[1], location[2])
        cave2_exit_event.event_address = space.start_address - EVENT_CODE_START

        # (5b) Add the switchyard event tile that handles exit from ST Cave #1
        src = [
            field.Branch(0xa8c94),
            world.End()
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave exit Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

        # (6a) Change the Nikeah Entry event to load the switchyard location
        st_exit_id = 2052
        switchyard_x = st_exit_id % 128
        switchyard_y = st_exit_id // 128

        space = Reserve(0xa8be6, 0xa8bec, 'Serpent Trench #3 to Nikeah modification')
        space.write([
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ])
        # (6b) Add the switchyard event tile that handles entry to Nikeah entrance animation
        from instruction.field.entity import Hide
        src = [
            field.LoadMap(0x000, direction=direction.UP, default_music=True,
                          x=128, y=73, fade_in=True, entrance_event=True),
            Hide(),
            world.Branch(0xa8bed)
        ]
        space = Write(Bank.CA, src, "Serpent Trench #1 cave entry Switchyard")

        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)

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
