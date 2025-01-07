from event.event import *
from data.map_exit_extra import exit_data
from data.rooms import exit_world

class ZoneEater(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops)
        self.DOOR_RANDOMIZE = (args.door_randomize_zone_eater
                          or args.door_randomize_all
                          or args.door_randomize_dungeon_crawl
                          or args.door_randomize_each)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Zone Eater"

    def character_gate(self):
        return self.characters.GOGO

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def mod(self):
        self.gogo_npc_id = 0x10
        self.gogo_npc = self.maps.get_npc(0x116, self.gogo_npc_id)

        if self.DOOR_RANDOMIZE:
            # Use events as one-ways.  Takes priority.
            self.engulf_id = 2040  # ID of engulf event
            self.exit_id = 2041  # ID of exit zone eater event
        elif self.MAP_SHUFFLE:
            # Use events as doors
            self.engulf_id = 1552  # ID of engulf door
            self.exit_id = 1553  # ID of exit zone eater door

        if self.args.character_gating:
            self.add_gating_condition()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        if self.DOOR_RANDOMIZE or self.MAP_SHUFFLE:
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
        from event.switchyard import AddSwitchyardEvent, GoToSwitchyard, SummonAirship, switchyard_xy

        # (1a) Change the entry event to load the switchyard location
        space = Reserve(0xa008f, 0xa0095, 'Zone Eater Entry modification')
        space.write(GoToSwitchyard(self.engulf_id, map='world'))

        # (1b) Add the switchyard event tile that handles entry to Zone Eater
        src = [
            field.LoadMap(0x114, direction=direction.DOWN, default_music=True,
                          x=10, y=12, fade_in=True, entrance_event=True),
        ]
        if self.MAP_SHUFFLE:
            # Get the connecting exit
            self.parent_map = [0x001, 237, 50]
            if self.exit_id in self.maps.door_map.keys():
                self.parent_map = self.maps.get_connection_location(self.exit_id)
                # conn_id = self.maps.door_map[self.exit_id]  # connecting exit south
                # conn_pair = exit_data[conn_id][0]  # original connecting exit
                # self.parent_map = [exit_world[conn_pair]] + \
                #                      self.maps.exits.exit_original_data[conn_pair][1:3]  # [dest_map, dest_x, dest_y]
            # Force update the parent map here
            src += [field.SetParentMap(self.parent_map[0], direction.DOWN, self.parent_map[1], self.parent_map[2] + 1)]
            if self.parent_map[0] == 0:
                # Update world
                src += [field.SetEventBit(event_bit.IN_WOR)]  # Zone Eater is in WOR.  is this necessary?
        src += [field.Return()]
        AddSwitchyardEvent(self.engulf_id, self.maps, src=src)
        #print(self.exit_id, ': added event at ', switchyard_xy(self.engulf_id), ':', [a.__str__() for a in src])

        # (2a) Change the exit event to load the switchyard location
        space = Reserve(0xb7db7, 0xb7dbd, 'Zone Eater Exit modification')
        space.write(GoToSwitchyard(self.exit_id))
        # (2b) Add the switchyard event tile that handles exit to Triangle Island
        src = SummonAirship(0x001, 237, 50)
        AddSwitchyardEvent(self.exit_id, self.maps, src=src)
