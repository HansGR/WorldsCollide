from event.event import *

class ZoneEater(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_zone_eater
                          or args.door_randomize_all
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
    def name(self):
        return "Zone Eater"

    def character_gate(self):
        return self.characters.GOGO

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.gogo_npc_id = 0x10
        self.gogo_npc = self.maps.get_npc(0x116, self.gogo_npc_id)

        if self.args.character_gating:
            self.add_gating_condition()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        if self.DOOR_RANDOMIZE:
            self.door_rando_mod()

        self.log_reward(self.reward)

    def add_gating_condition(self):
        chest_bridge_npc_id = 0x11
        chest_bridge_npc = self.maps.get_npc(0x114, chest_bridge_npc_id)

        import copy
        from data.npc import NPC
        gate_npc = copy.deepcopy(chest_bridge_npc) # copy bottom left npc to drop towards end of bottom level
        gate_npc.x = 30
        gate_npc.y = 28
        gate_npc.direction = direction.RIGHT
        gate_npc.movement = NPC.NO_MOVE # instead of completely random, restrict it to bridge in entrance event

        gate_npc_id = self.maps.append_npc(0x114, gate_npc)

        # use extra space after recruiting gogo
        enable_npc_touch_events = 0xb8200
        space = Reserve(enable_npc_touch_events, 0xb824b, "zone eater enable npc touch events", field.NOP())
        space.copy_from(0xb7dc2, 0xb7dc7) # enable touch events for original npcs
        space.write(
            field.BranchIfEventBitSet(event_bit.character_recruited(self.character_gate()), "HIDE_GATE_NPC"),
            field.EnableTouchEvent(gate_npc_id),
            field.Return(),

            "HIDE_GATE_NPC",
            field.HideEntity(gate_npc_id),
            field.Return(),
        )

        space = Reserve(0xb7dc2, 0xb7dc7, "zone eater entrance event", field.NOP())
        space.write(
            field.Call(enable_npc_touch_events),
        )

    def character_mod(self, character):
        self.gogo_npc.sprite = character
        self.gogo_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xb81ce, 0xb81ff, "zone eater recruit gogo", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),

            field.DeleteEntity(self.gogo_npc_id),
            field.ClearEventBit(npc_bit.GOGO_ZONE_EATER),
            field.SetEventBit(event_bit.RECRUITED_GOGO_WOR),
            field.FadeInScreen(),
            field.FinishCheck(),
            field.Return(),
        )

    def esper_item_mod(self, esper_item_instructions):
        space = Reserve(0xb81ce, 0xb81ff, "zone eater recruit gogo", field.NOP())
        space.write(
            esper_item_instructions,

            field.DeleteEntity(self.gogo_npc_id),
            field.ClearEventBit(npc_bit.GOGO_ZONE_EATER),
            field.SetEventBit(event_bit.RECRUITED_GOGO_WOR),
            field.FinishCheck(),
            field.Return(),
        )

    def esper_mod(self, esper):
        self.gogo_npc.sprite = 91
        self.gogo_npc.palette = 2
        self.gogo_npc.split_sprite = 1
        self.gogo_npc.direction = direction.UP

        self.esper_item_mod([
            field.DisableEntityCollision(self.gogo_npc_id),
            field.EntityAct(self.gogo_npc_id, True,
                field_entity.SetSpeed(field_entity.Speed.NORMAL),
                field_entity.Move(direction.DOWN, 1),
                field_entity.Hide(),
            ),

            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
        ])

    def item_mod(self, item):
        self.gogo_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.gogo_npc.palette = self.characters.get_palette(self.gogo_npc.sprite)

        self.esper_item_mod([
            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
        ])

    def door_rando_mod(self):
        # Modifications for door rando
        engulfID = 2040  # ID of engulf event

        # (1) Change the entry event to load the switchyard location
        switchyard_map = 0x005
        switchyard_x = engulfID % 128
        switchyard_y = engulfID // 128

        space = Reserve(0xa008f, 0xa0095, 'Zone Eater Entry modification')
        space.write([
            world.LoadMap(switchyard_map, direction=direction.UP, default_music=False,
                          x=switchyard_x, y=switchyard_y,
                          fade_in=False, entrance_event=False),
            field.Return()
        ])
        # (2) Add the switchyard event tile that handles entry to Zone Eater
        src = [
            field.LoadMap(0x114, direction=direction.DOWN, default_music=True,
                          x=10, y=12, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CA, src, "Zone Eater Entry Switchyard")

        from data.map_event import MapEvent
        switchyard_event = MapEvent()
        switchyard_event.x = switchyard_x
        switchyard_event.y = switchyard_y
        switchyard_event.event_address = space.start_address - EVENT_CODE_START
        self.maps.add_event(switchyard_map, switchyard_event)
