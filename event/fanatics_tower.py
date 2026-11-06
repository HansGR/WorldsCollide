from event.event import *

class FanaticsTower(Event):
    def name(self):
        return "Fanatic's Tower"

    def character_gate(self):
        return self.characters.STRAGO

    def init_rewards(self):
        self.reward1 = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)
        self.reward2 = self.add_reward(RewardType.ITEM)

    def mod(self):
        self.strago_npc_id = 0x13
        self.strago_npc = self.maps.get_npc(0x16a, self.strago_npc_id)

        self.battle_commands_mod()
        self.relm_event_mod()
        self.tower_top_mod()
        self.magimaster_battle_mod()

        if self.reward1.type == RewardType.CHARACTER:
            self.character_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ESPER:
            self.esper_mod(self.reward1.id)
        elif self.reward1.type == RewardType.ITEM:
            self.item_mod(self.reward1.id)

        self.finish_magimaster_check_mod()
        self.finish_strago_check_mod()

        self.log_reward(self.reward1)
        self.log_reward(self.reward2)

    def battle_commands_mod(self):
        # vanilla rewrites each character's battle menu when it is built (C2/5340, shared with
        # magitek armor): Fight becomes Magic, Magic itself is blanked, everything but Item/Mimic
        # is blanked (and Gau's Rage counts as Fight). with randomized commands that hands Magic
        # to characters who have no Magic command, and blanks the Magic of those who do.
        # instead, keep every menu as it is and gray out every command but Magic/X Magic/Item/
        # Mimic, the way Mute grays Magic: a character without Magic cannot cast in the tower.
        # (a menu with nothing usable is only possible with the probability command modes, which
        # install battle/command_menu_guard.py so the cursor does not hang)
        # bank C2 is nearly full, so only small stubs go there; the checks live in F0
        from constants.commands import name_id
        from memory.space import START_ADDRESS_SNES
        fanatics_tower = 0x3ebb     # bit 0 is set for battles in the tower
        tower_commands = [name_id["Magic"], name_id["X Magic"], name_id["Item"], name_id["Mimic"]]

        # C2/534E: not in magitek armor; vanilla goes on to the tower conversion if $3ebb bit 0
        space = Reserve(0x2534e, 0x25353, "fanatics tower: do not rewrite battle menu commands", asm.NOP())
        space.add_label("MENU_DONE", 0x2539d)
        space.write(
            asm.BRA("MENU_DONE"),
        )

        # carry set if a (a command) cannot be used here: in the tower and not a tower command
        src = [
            asm.PHA(),
            asm.LDA(fanatics_tower, asm.ABS),
            asm.LSR(),
            asm.PLA(),
            asm.BCC("RETURN"),                  # not in the tower (carry clear)
        ]
        for command in tower_commands:
            src += [
                asm.CMP(command, asm.IMM8),
                asm.BEQ("ALLOWED"),
            ]
        src += [
            asm.SEC(),
            asm.RTL(),
            "ALLOWED",
            asm.CLC(),
            "RETURN",
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "fanatics tower: is command unusable")
        unusable = space.start_address_snes

        # C2/527D grays a menu slot when its carry ends up set (ROR into bit 7 of the slot's
        # second byte): C2/52C6 LDX #$0007 starts the per-command checks (Mute grays Magic, ...)
        src = [
            asm.JSL(unusable),
            asm.BCS("GRAY"),
            asm.LDX(0x0007, asm.IMM16),         # vanilla (x is 16 bit here)
            asm.RTS(),

            "GRAY",
            asm.PLA(),                          # drop the return address (a is 8 bit)
            asm.PLA(),
            asm.SEC(),                          # gray
            asm.JMP(0x52db, asm.ABS),
        ]
        space = Write(Bank.C2, src, "fanatics tower: gray out commands other than magic/item")
        gray_check = space.start_address

        space = Reserve(0x252c6, 0x252c8, "fanatics tower: gray out commands other than magic/item")
        space.write(
            asm.JSR(gray_check, asm.ABS),
        )

        # C2/0420 picks a command for an uncontrollable character (muddle, charm, berserk) from its
        # four menu commands (copied to $f6/$f8/$fa/$fc) plus Fight ($fe); it ignores the gray bit,
        # so drop the commands that cannot be used in the tower from those copies (vanilla: Magic,
        # Item or Fight). x and y are 8 bit; x is the character
        src = [
            asm.LDA(0x05, asm.IMM8),            # vanilla: number of candidate commands
            asm.STA(0xf5, asm.DIR),
            asm.PHX(),
            asm.LDX(0x06, asm.IMM8),
            "LOOP",
            asm.LDA(0xf6, asm.DIR_X),
            asm.JSL(unusable),
            asm.BCC("NEXT"),
            asm.LDA(0xff, asm.IMM8),            # no command: the chooser skips (and uncounts) it
            asm.STA(0xf6, asm.DIR_X),
            "NEXT",
            asm.DEX(),
            asm.DEX(),
            asm.BPL("LOOP"),
            asm.PLX(),
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "fanatics tower: uncontrollable characters use magic/item")
        chooser_filter = space.start_address_snes

        space = Reserve(0x20440, 0x20443, "fanatics tower: uncontrollable characters use magic/item")
        space.write(
            asm.JSL(chooser_filter),
        )

    def relm_event_mod(self):
        # normally there are 4 event tiles surrounding player when they enter map and if player steps on one
        # with relm in party and strago not already recruited the relm/strago event is triggered
        # need to move the event tiles to the bottom of the stairs so player can not go around them and miss
        # recruiting the character after defeating magi master
        # create left/right event tiles which move the player to the original north event tile and
        # call the original event code (skipping the old checks for strago recruited/relm in party)
        space = Reserve(0xc522e, 0xc5282, "fanatics tower relm/strago event tiles", field.NOP())

        relm_strago_event = 0xc5283
        left_tile_event = space.next_address
        space.write(
            field.ReturnIfEventBitClear(event_bit.DEFEATED_MAGIMASTER),
            field.ReturnIfEventBitSet(event_bit.RECRUITED_STRAGO_FANATICS_TOWER),
        )
        if self.args.character_gating:
            space.write(
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            )
        space.write(
            field.Call(field.DISABLE_COLLISIONS_FOR_PARTY_MEMBERS),

            # move to where event normally happens and call normal event code
            field.EntityAct(0x31, True,
                field_entity.Move(direction.DOWN, 3),
                field_entity.Move(direction.RIGHT, 1),
                field_entity.Turn(direction.UP),
            ),
            field.Call(relm_strago_event),
            field.Return(),
        )

        right_tile_event = space.next_address
        space.write(
            field.ReturnIfEventBitClear(event_bit.DEFEATED_MAGIMASTER),
            field.ReturnIfEventBitSet(event_bit.RECRUITED_STRAGO_FANATICS_TOWER),
        )
        if self.args.character_gating:
            space.write(
                field.ReturnIfEventBitClear(event_bit.character_recruited(self.character_gate())),
            )
        space.write(
            field.Call(field.DISABLE_COLLISIONS_FOR_PARTY_MEMBERS),

            # move to where event normally happens and call normal event code
            field.EntityAct(0x31, True,
                field_entity.Move(direction.DOWN, 3),
                field_entity.Turn(direction.UP),
            ),
            field.Call(relm_strago_event),
            field.Return(),
        )

        self.maps.delete_event(0x16a, 8, 12) # relm/strago event tile (north)
        self.maps.delete_event(0x16a, 7, 13) # relm/strago event tile (west)
        self.maps.delete_event(0x16a, 9, 13) # relm/strago event tile (east)
        self.maps.delete_event(0x16a, 8, 14) # relm/strago event tile (south)

        from data.map_event import MapEvent

        # add event tile to bottom left of stairs
        new_event = MapEvent()
        new_event.x = 7
        new_event.y = 9
        new_event.event_address = left_tile_event - EVENT_CODE_START
        self.maps.add_event(0x16a, new_event)

        # add event tile to bottom right of stairs
        new_event = MapEvent()
        new_event.x = 8
        new_event.y = 9
        new_event.event_address = right_tile_event - EVENT_CODE_START
        self.maps.add_event(0x16a, new_event)

        space = Reserve(0xc528b, 0xc528f, "fanatics tower don't change party for relm", field.NOP())
        space = Reserve(0xc52aa, 0xc52cc, "fanatics tower relm runs up stairs you old fool", field.NOP())
        space = Reserve(0xc5303, 0xc5307, "fanatics tower relm looks up after strago jumps", field.NOP())
        space = Reserve(0xc5316, 0xc5326, "fanatics tower relm and strago face each other", field.NOP())
        space = Reserve(0xc5329, 0xc5350, "fanatics tower various relm animations", field.NOP())
        space = Reserve(0xc5356, 0xc5389, "fanatics tower more relm animations and foul mouthed", field.NOP())
        space = Reserve(0xc5392, 0xc5395, "fanatics tower turn relm left", field.NOP())
        space = Reserve(0xc53a2, 0xc53a5, "fanatics tower turn relm down", field.NOP())
        space = Reserve(0xc53ca, 0xc53df, "fanatics tower all right, make room for me", field.NOP())

        space = Reserve(0xc53fd, 0xc53fd, "fanatics tower party leader head nod", field.NOP())
        space.write(field_entity.PARTY0)

        space = Reserve(0xc5407, 0xc5408, "fanatics tower stop relm song before screen fade", field.NOP())

    def tower_top_mod(self):
        space = Reserve(0xc5548, 0xc554a, "fanatics tower master kefka's treasure", field.NOP())
        space = Reserve(0xc554d, 0xc554e, "fanatics tower long pause before magic master appears", field.NOP())

        self.item = self.reward2.id
        self.maps.set_chest_item(0x16e, 7, 7, self.item)

    def magimaster_battle_mod(self):
        boss_pack_id = self.get_boss("MagiMaster")

        space = Reserve(0xc5578, 0xc557e, "fanatic's tower invoke battle magimaster", field.NOP())
        space.write(
            field.InvokeBattle(boss_pack_id),
        )

    def character_music_mod(self, character):
        from music.song_utils import get_character_theme

        space = Reserve(0xc5327, 0xc5328, "Play Song Relm")
        space.write([
            field.StartSong(get_character_theme(character)),
        ])

    def character_mod(self, character):
        self.character_music_mod(character)
        self.strago_npc.sprite = character
        self.strago_npc.palette = self.characters.get_palette(character)

        space = Reserve(0xc540d, 0xc542a, "fanatics tower add character", field.NOP())
        space.write(
            field.RecruitAndSelectParty(character),
        )

    def esper_item_mod(self, esper_item_instructions):
        self.strago_npc.sprite = self.characters.get_random_esper_item_sprite()
        self.strago_npc.palette = self.characters.get_palette(self.strago_npc.sprite)

        space = Reserve(0xc5409, 0xc542a, "fanatics tower esper/item reward", field.NOP())
        space.write(
            esper_item_instructions,
            field.FadeOutScreen(4),
            field.WaitForFade(),
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

    def finish_magimaster_check_mod(self):
        src = [
            Read(0xc5583, 0xc5588), # load map
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "fanatic's tower magimaster finish check")
        finish_check = space.start_address

        space = Reserve(0xc5583, 0xc5588, "fanatic's tower load map after magimaster", field.NOP())
        space.write(
            field.Call(finish_check),
        )

    def finish_strago_check_mod(self):
        src = [
            Read(0xc5438, 0xc543d), # load map
            field.FinishCheck(),
            field.Return(),
        ]
        space = Write(Bank.CC, src, "fanatics tower strago finish check")
        finish_check = space.start_address

        space = Reserve(0xc5438, 0xc543d, "fanatics tower load map after strago", field.NOP())
        space.write(
            field.Call(finish_check),
        )
