from event.event import *
from event.switchyard import AddSwitchyardEvent, GoToSwitchyard

class ImperialCamp(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle

    def name(self):
        return "Imperial Camp"

    def character_gate(self):
        return self.characters.SABIN

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.SetEventBit(event_bit.GENERAL_LEO_IMPERIAL_CAMP),
            field.SetEventBit(npc_bit.CHEST_IMPERIAL_CAMP),

            field.ClearEventBit(npc_bit.EAST_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(npc_bit.WEST_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(npc_bit.GENERAL_LEO_IMPERIAL_CAMP),
            field.ClearEventBit(npc_bit.MESSENGER_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(npc_bit.MARANDA_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(npc_bit.DOMA_GENERAL_IMPERIAL_CAMP),
        )
        if self.MAP_SHUFFLE:
            # Deactivate imperial camp by default.  It will be activated when needed.
            space.write(
                field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
                field.SetEventBit(event_bit.CHASING_KEFKA1_IMPERIAL_CAMP),
                field.SetEventBit(event_bit.CHASING_KEFKA3_IMPERIAL_CAMP),
                field.SetEventBit(event_bit.FINISHED_CHASING_KEFKA_IMPERIAL_CAMP),
            )

    def mod(self):
        self.kefka_npc_id = 0x15
        self.soldier_npc_id = 0x17

        self.entrance_events_mod()
        self.leo_and_chasing_kefka_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)

        self.log_reward(self.reward)

    def entrance_events_mod(self):
        # delete tile events near entrance that lead to doma attack
        self.maps.delete_event(0x75, 36, 3)
        self.maps.delete_event(0x75, 37, 2)
        self.maps.delete_event(0x75, 34, 2)

        # overwrite tile events near entrance that lead to doma attack
        space = Reserve(0xb0c2e, 0xb0d86, "imperial camp entrance tile events", field.NOP())
        space.write(
            field.HideEntity(self.kefka_npc_id),
            field.Return(),
        )

        # this does not get called anymore, use it for extra wob event tile space
        if self.MAP_SHUFFLE:
            # Overwrite the entrance event to go to switchyard.
            # (1a) Change the entry event to load the switchyard location
            event_id = 1501  # ID of Imperial Camp event entrance

            # For map shuffle, we will allow re-entry, so we can just write over the bit check
            sy_space = Reserve(0xb0bb7, 0xb0bea, 'Imperial Camp WOB entrance', field.NOP())

            sy_space.write(GoToSwitchyard(event_id, map='world'))
            # (1b) Add the switchyard event tile that handles entry to South Figaro Cave
            src = [
                field.LoadMap(0x075, direction=direction.DOWN, x=36, y=2, default_music=True, fade_in=True),
                field.Return()
            ]
            AddSwitchyardEvent(event_id, self.maps, src=src)

            # Modify the logic to allow exploring a deactivated imperial camp if not yet complete & gating condition not met
            gating_logic = space.next_address
            space.write(
                field.HideEntity(self.soldier_npc_id),
                #field.BranchIfEventBitSet(event_bit.FINISHED_IMPERIAL_CAMP, "IMPERIAL_CAMP_DEACTIVATED")
                field.ReturnIfEventBitSet(event_bit.FINISHED_IMPERIAL_CAMP)
            )
            if self.args.character_gating:
                space.write(
                    #field.BranchIfEventBitClear(event_bit.character_recruited(self.character_gate()), "IMPERIAL_CAMP_DEACTIVATED"),
                    field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
                )
            # Activate imperial camp if it should be active.
            space.write(
                #field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
                field.ClearEventBit(event_bit.CHASING_KEFKA1_IMPERIAL_CAMP),
                field.ClearEventBit(event_bit.CHASING_KEFKA3_IMPERIAL_CAMP),
                field.ClearEventBit(event_bit.FINISHED_CHASING_KEFKA_IMPERIAL_CAMP),
                field.ShowEntity(self.soldier_npc_id),
                field.Return()
            )

            space = Reserve(0xb0bf1, 0xb0bf4, "Call imperial camp gating logic") # replace call to unused spotlight routine at CB/0EF8 depending on event_bit 0x1b5
            space.write(field.Call(gating_logic))

            # Figure out how to neutralize imperial camp actions
            # If the following event bits are set, imperial camp is deactivated:
            # --> clear 02c (BRIDGE_BLOCKED_IMPERIAL_CAMP), and ...    (CB/1104).
            # --> set 02c or set 0x02d (CHASING_KEFKA1_IMPERIAL_CAMP), and ...   (CB/1032)  Modified in leo_and_chasing_kefka_mod()
            # --> clear 02c or set 02f (CHASING_KEFKA3_IMPERIAL_CAMP), and ...
            # --> set 155 (FINISHED_CHASING_KEFKA_IMPERIAL_CAMP)
            #space.write(
            #    'IMPERIAL_CAMP_DEACTIVATED',
            #    field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
            #    field.SetEventBit(event_bit.CHASING_KEFKA1_IMPERIAL_CAMP),
            #    field.SetEventBit(event_bit.CHASING_KEFKA3_IMPERIAL_CAMP),
            #    field.SetEventBit(event_bit.FINISHED_CHASING_KEFKA_IMPERIAL_CAMP),
            #    field.Return()
            #)
            # We will actually just deactivate it by default in the init_event_bits,
            # and only activate it if it should be active.

        else:
            # TODO what does the unknown flag here in load map do?
            space = Reserve(0xb0bbd, 0xb0bea, "imperial camp load after doma wob scene", world.End())
            if self.args.character_gating:
                space.write(
                    world.EndIfEventBitClear(event_bit.character_recruited(self.character_gate())),
                )
            space.write(
                world.FadeLoadMap(0x075, direction.DOWN, default_music = False, x = 36, y = 2,
                                  fade_in = True, entrance_event = True, unknown = True),
                field.Return(),
            )

    def leo_and_chasing_kefka_mod(self):
        # first scene with general leo
        space = Reserve(0xb0f2e, 0xb0f2e, "imperial camp first general leo scene", field.Return())

        # scene before first kefka fight where leo leaves and kefka orders river poisoned
        space = Reserve(0xb1032, 0xb10f5, "imperial camp player jumps in front of kefka", field.NOP())
        space.write(
            field.ReturnIfEventBitSet(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),

            # NOTE: add this check so can explore imperial camp after finished event
            field.ReturnIfEventBitSet(event_bit.CHASING_KEFKA1_IMPERIAL_CAMP),

            field.SetEventBit(npc_bit.KEFKA_IMPERIAL_CAMP),
            field.CreateEntity(self.kefka_npc_id),
            field.ShowEntity(self.kefka_npc_id),

            field.HoldScreen(),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.AnimateSurprised(),
                field_entity.Pause(6),
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.Move(direction.UP, 1),
                field_entity.Move(direction.RIGHT, 3),
                field_entity.AnimateKneeling(),
            ),
            field.EntityAct(self.kefka_npc_id, True,
                field_entity.Move(direction.UP, 4),
                field_entity.Move(direction.LEFT, 3),
                field_entity.Move(direction.UP, 4),
                field_entity.Move(direction.LEFT, 1),
            ),
            field.EntityAct(self.kefka_npc_id, False,
                field_entity.Move(direction.UP, 1),
            ),
            field.EntityAct(field_entity.PARTY0, True,
                field_entity.SetSpeed(field_entity.Speed.FAST),
                field_entity.Move(direction.LEFT, 3),
                field_entity.Turn(direction.DOWN),
            ),
            field.FreeScreen(),
            field.SetEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
            field.Call(0xb1126),
            field.Return(),
        )

        space = Reserve(0xb112c, 0xb112e, "imperial camp player jumps in front of kekfa dialog", field.NOP())
        space = Reserve(0xb115a, 0xb115c, "imperial camp first Wait!!! dialog", field.NOP())
        space = Reserve(0xb117c, 0xb117e, "imperial camp second Wait!!! dialog", field.NOP())
        space = Reserve(0xb1199, 0xb119b, "imperial camp what a toad dialog", field.NOP())
        space = Reserve(0xb11ba, 0xb11bc, "imperial camp next time you're a goner dialog", field.NOP())
        space = Reserve(0xb120d, 0xb120f, "imperial camp oh, gripe! dialog", field.NOP())

        # skip battles with kefka because in his battle there is actually no enemy
        # he is added to the party and acts as a character with ai
        # this does not work with 4 party members, the battle will just immediately end and kefka won't show up
        # TODO posssibly fix this by changing an existing enemy to kefka with 1 hp and invoke a battle with him instead
        space = Reserve(0xb112f, 0xb1153, "imperial camp skip kefka battle 1", field.NOP())
        space = Reserve(0xb11aa, 0xb11b9, "imperial camp skip kefka battle 2", field.NOP())

        space = Reserve(0xb1156, 0xb1156, "imperial camp make kefka run away fast")
        space.write(field_entity.SetSpeed(field_entity.Speed.FAST))

    def cyan_battles_mod(self, sprite, palette):
        cyan_npc_id = 0x12
        cyan_npc = self.maps.get_npc(0x077, cyan_npc_id)
        cyan_npc.sprite = sprite
        cyan_npc.palette = palette

        space = Reserve(0xb1225, 0xb1225, "imperial camp song playing when cyan rushes in")
        space.write(0x32)

        # kefka poisons river after battle
        space = Reserve(0xb122d, 0xb1282, "imperial camp kefka poisons river", field.NOP())
        space.write(
            field.Call(0xb1348), # jump to cyan rushing in
            field.Return(),
        )

        # change sabin to current party leader
        self.rom.set_byte(0xb1355, field_entity.PARTY0)
        self.rom.set_byte(0xb135c, field_entity.PARTY0)
        self.rom.set_byte(0xb138f, field_entity.PARTY0)

        # remove cyan and sabin's names from dialog when you get in the middle of the fight
        self.dialogs.set_text(578, "Eeoooa!<line>Be you friend or enemy?!<end>")
        self.dialogs.set_text(579, "Ouuuch!<line>…didn't MEAN to step in there…<end>")

        space = Reserve(0xb136b, 0xb136d, "imperial camp dialog after cyan rushes in", field.NOP())
        space = Reserve(0xb137e, 0xb1380, "imperial camp soldier's dialog after meeting cyan", field.NOP())
        space = Reserve(0xb1394, 0xb1396, "imperial camp sabin's dialog after seeing cyan fighting", field.NOP())
        space = Reserve(0xb1491, 0xb1493, "imperial camp sabin dialog to cyan before first battle", field.NOP())
        space = Reserve(0xb14a2, 0xb14a4, "imperial camp cyan dialog to sabin before first battle", field.NOP())
        space = Reserve(0xb14ce, 0xb14d0, "imperial camp cyan dialog after first battle", field.NOP())
        space = Reserve(0xb1532, 0xb1534, "imperial camp sabin dialog to cyan before second battle", field.NOP())
        space = Reserve(0xb1543, 0xb1545, "imperial camp cyan dialog to sabin before second battle", field.NOP())
        space = Reserve(0xb156f, 0xb1571, "imperial camp cyan dialog after second battle", field.NOP())
        space = Reserve(0xb15df, 0xb15e1, "imperial camp sabin dialog to cyan before third battle", field.NOP())
        space = Reserve(0xb15f0, 0xb15f2, "imperial camp cyan dialog to sabin before third battle", field.NOP())

    def character_mod(self, character):
        self.cyan_battles_mod(character, self.characters.get_palette(character))

        # after all battles complete
        space = Reserve(0xb1616, 0xb16a1, "imperial camp character finish", field.NOP())
        space.write(
            field.ClearEventBit(npc_bit.WESTMOST_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
            field.SetEventBit(event_bit.FINISHED_IMPERIAL_CAMP),

            field.RecruitAndSelectParty(character),
            field.LoadMap(0x75, direction.DOWN, default_music = True, x = 8, y = 21, fade_in = True, entrance_event = True),
            field.FinishCheck(),
            field.Return(),
        )

    def esper_mod(self, esper):
        random_sprite = self.characters.get_random_esper_item_sprite()
        self.cyan_battles_mod(random_sprite, self.characters.get_palette(random_sprite))

        # after all battles complete
        space = Reserve(0xb1616, 0xb16a1, "imperial camp esper finish", field.NOP())
        space.write(
            field.ClearEventBit(npc_bit.WESTMOST_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
            field.SetEventBit(event_bit.FINISHED_IMPERIAL_CAMP),

            field.LoadMap(0x75, direction.DOWN, default_music = True, x = 8, y = 21, fade_in = True, entrance_event = True),
            field.AddEsper(esper),
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.FinishCheck(),
            field.Return(),
        )

    def item_mod(self, item):
        random_sprite = self.characters.get_random_esper_item_sprite()
        self.cyan_battles_mod(random_sprite, self.characters.get_palette(random_sprite))

        # after all battles complete
        space = Reserve(0xb1616, 0xb16a1, "imperial camp item finish", field.NOP())
        space.write(
            field.ClearEventBit(npc_bit.WESTMOST_SOLDIER_IMPERIAL_CAMP),
            field.ClearEventBit(event_bit.BRIDGE_BLOCKED_IMPERIAL_CAMP),
            field.SetEventBit(event_bit.FINISHED_IMPERIAL_CAMP),

            field.LoadMap(0x75, direction.DOWN, default_music = True, x = 8, y = 21, fade_in = True, entrance_event = True),

            field.AddItem(item),
            field.Dialog(self.items.get_receive_dialog(item)),
            field.FinishCheck(),
            field.Return(),
        )
