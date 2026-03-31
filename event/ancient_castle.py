from event.event import *

class AncientCastle(Event):
    def __init__(self, events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps):
        super().__init__(events, rom, args, dialogs, characters, items, maps, enemies, espers, shops, warps)
        self.MAP_SHUFFLE = args.map_shuffle_separate or args.map_shuffle_crossworld

    def name(self):
        return "Ancient Castle"

    def character_gate(self):
        if self.MAP_SHUFFLE:
            # AC may be ungated in map shuffle.  We handle Edgar logic later.
            return None
        else:
            return self.characters.EDGAR

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM)

    def init_event_bits(self, space):
        space.write(
            field.ClearEventBit(npc_bit.ODIN_STATUE_ANCIENT_CASTLE),
            field.SetEventBit(event_bit.GOT_ODIN),
            field.SetEventBit(event_bit.FOUND_ANCIENT_CASTLE),
            field.SetEventBit(npc_bit.BOOKCASE_ANCIENT_CASTLE),
            field.SetEventBit(npc_bit.DRAGON_ANCIENT_CASTLE),
        )

    def mod(self):
        self.dialog_mod()

        if self.reward.type == RewardType.CHARACTER:
            self.character_mod(self.reward.id)
        elif self.reward.type == RewardType.ESPER:
            self.esper_mod(self.reward.id)
        elif self.reward.type == RewardType.ITEM:
            self.item_mod(self.reward.id)
        self.finish_check_mod()

        if self.MAP_SHUFFLE:
            self.map_shuffle_mod()

        if self.args.ruination_mode:
            self.ruination_mod()

        if self.args.ruination_mode and self.args.character_gating:
            self.add_ruin_character_gate()

        self.log_reward(self.reward)

    def dialog_mod(self):
        space = Reserve(0xc1f5c, 0xc1f5f, "ancient castle even the queen was turned to stone", field.NOP())
        space = Reserve(0xc1f73, 0xc1f75, "ancient castle a tear comes from the stone", field.NOP())

    def character_mod(self, character):
        statue_npc_id = 0x11
        statue_npc = self.maps.get_npc(0x198, statue_npc_id)
        statue_npc.sprite = character

        space = Reserve(0xc1f72, 0xc1f72, "ancient castle pause after tear", field.NOP())

        # NOTE: statue/character turned gray at 0xc19fd
        #       for command 0x61 some colors are # 00 = black, 01 = red, 02 = green, 03 = yellow, 04 = blue, 05 = purple,
        #                                        # 06 = teal, 07 = gray, 08 = teal, 09 = blue/purple, 0a = darker yellow
        src = [
            field.SetPalette(statue_npc_id, self.characters.get_palette(character)),
            field.EntityAct(statue_npc_id, True,
                field_entity.AnimateKneeling(),
                field_entity.Pause(20),
                field_entity.AnimateStandingHeadDown(),
                field_entity.Pause(16),
                field_entity.AnimateStandingFront(),
                field_entity.Pause(8),

                # blink eyes
                field_entity.AnimateCloseEyes(),
                field_entity.Pause(1),
                field_entity.Turn(direction.DOWN),
                field_entity.Pause(1),
                field_entity.AnimateCloseEyes(),
                field_entity.Pause(1),
                field_entity.Turn(direction.DOWN),
                field_entity.Pause(1),
            ),

            field.FadeOutScreen(4),
            field.WaitForFade(),

            field.ClearEventBit(npc_bit.MARIA_STATUE_ANCIENT_CASTLE),
            field.HideEntity(statue_npc_id),
            field.DeleteEntity(statue_npc_id),

            field.RecruitAndSelectParty(character),

            field.FadeInScreen(),
            field.WaitForFade(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "ancient castle statue to character")
        recruit_character = space.start_address

        space = Reserve(0xc1f76, 0xc1f84, "ancient castle display receive raiden dialog and take odin", field.NOP())
        space.write(
            field.Call(recruit_character),
            field.Branch(space.end_address + 1),
        )

    def esper_mod(self, esper):
        space = Reserve(0xc1f7e, 0xc1f84, "ancient castle display receive raiden dialog and take odin", field.NOP())
        space.write(
            field.Dialog(self.espers.get_receive_esper_dialog(esper)),
            field.AddEsper(esper, sound_effect = False),
        )

    def item_mod(self, item):
        space = Reserve(0xc1f76, 0xc1f84, "ancient castle display receive raiden dialog and take odin", field.NOP())
        space.write(
            field.Dialog(self.items.get_receive_dialog(item)),
            field.AddItem(item, sound_effect = False),
            field.Branch(space.end_address + 1), # skip nops
        )

    def finish_check_mod(self):
        src = [
            field.SetEventBit(event_bit.GOT_RAIDEN),
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "ancient castle finish check")
        finish_check = space.start_address

        space = Reserve(0xc1f85, 0xc1f88, "ancient castle give raiden and set event bit", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def map_shuffle_mod(self):
        # Add a specified warp handler case: return to FC prison WOR
        src_warp = [
            field.SetEventBit(event_bit.IN_WOR),
            field.ClearEventBit(event_bit.ANCIENT_CASTLE_WARP_OPTION),
            field.LoadMap(map_id=0x03d, x=35, y=36, direction=direction.DOWN,
                          default_music=True, fade_in=True, entrance_event=True),
            field.Return()
        ]
        space = Write(Bank.CA, src_warp, 'Ancient Castle warp handler code')
        self.warps.add_warp(event_bit.ANCIENT_CASTLE_WARP_OPTION, space.start_address)

    def ruination_mod(self):
        # In ruination mode, the entrance_door_patch for exit 1558 is disabled (maps.py),
        # so GOT_FALCON is never set before the exit event runs. Without it, the
        # BranchIfEventBitSet(GOT_FALCON) at 0xa5f25 falls through to load Cave to South
        # Figaro instead of Ancient Castle, causing a softlock.
        #
        # Fix: overwrite the 2-byte event-bit field (0xa5f26-0xa5f27) to encode
        # BranchIfEventBitClear(ALWAYS_CLEAR) instead. Both Set and Clear use opcode 0xc0;
        # the distinction is bit 15 of the event-bit argument. ALWAYS_CLEAR (0x176) without
        # the 0x8000 flag = always-branch, so the exit unconditionally loads Ancient Castle.
        space = Reserve(0xa5f26, 0xa5f27, "ruination: always branch to Ancient Castle from prison exit")
        space.write(event_bit.ALWAYS_CLEAR.to_bytes(2, "little"))

    def add_ruin_character_gate(self):
        # Add a local character gate for ruination mode (in place of unused GOT_ODIN check)
        # Statue will just be unresponsive without EDGAR.
        space = Reserve(0xc1f49, 0xc1f50, "Ancient Castle local character gate condition", field.NOP())
        space.write([
            field.ReturnIfAny([event_bit.character_recruited(self.character_gate()), False,
                               event_bit.GOT_RAIDEN, True])
        ])

    @staticmethod
    def entrance_door_patch():
        # self-contained code to be called in door rando BEFORE entering 1558 (figaro castle basement) from AC connection
        # This is necessary in case tentacles have not been defeated when you go there (and also if you go when FC is buried)

        # to be used in event_exit_info.entrance_door_patch()
        src = [
            field.SetEventBit(event_bit.IN_WOR),
            field.ClearEventBit(npc_bit.LONE_WOLF_FIGARO_CASTLE),
            field.ClearEventBit(npc_bit.PRISONERS_FIGARO_CASTLE),
            field.SetEventBit(event_bit.GOT_FALCON),
            field.ClearEventBit(event_bit.ANCIENT_CASTLE_WARP_OPTION),

            # Set required bits for FC underground
            field.SetEventBit(npc_bit.BLOCK_INSIDE_DOORS_FIGARO_CASTLE),
            field.SetEventBit(event_bit.PRISON_DOOR_OPEN_FIGARO_CASTLE),

            # Set required flags for Engine Room Event...
            field.BranchIfEventBitSet(event_bit.DEFEATED_TENTACLES_FIGARO, "DEFEATED_TENTACLES"),
            field.SetEventBit(npc_bit.DEAD_SOLDIERS_FIGARO_CASTLE),
            field.ClearEventBit(npc_bit.PRISON_GUARD_FIGARO_CASTLE),

            # ... or set Figaro Castle under the desert, heading toward South Figaro
            "DEFEATED_TENTACLES",
            field.BranchIfEventBitClear(event_bit.DEFEATED_TENTACLES_FIGARO, "ENDING"),
            field.ClearEventBit(event_bit.FIGARO_CASTLE_IN_SF_DESERT_WOR),
            field.ClearEventBit(event_bit.FIGARO_CASTLE_IN_KOHL_DESERT_WOR),
            field.SetEventBit(event_bit.FIGARO_CASTLE_AT_ANCIENT_CASTLE_WOR),  # 0x26f
            field.ClearEventBit(event_bit.FIGARO_CASTLE_HEADING_TOWARD_KOHLINGEN), # Head toward SF upon exit
            "ENDING",
        ]

        return src
