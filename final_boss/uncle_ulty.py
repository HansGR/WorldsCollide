from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.shrimp as shrimp

from final_boss.final_boss import FinalBoss, ABILITY_DATA_START, PALETTES, PALETTE_SIZE

ATTACK_ANIMATIONS, ATTACK_ANIMATION_SIZE = 0x107fb2, 14     # layers' animations (3 words), their palettes (3 bytes), ...
PALETTE_COLORS = PALETTE_SIZE // 2

class UncleUlty(FinalBoss):
    # ultros (the one with all his tentacles), giant. he is 5 levels above final kefka and a fifth
    # faster, absorbs water, and has water where kefka had bolt
    #
    #   Havoc Wing  Tentacle, with the looks and sound of the tentacle attack
    #   HyperDrive  Ink Blast: black, and blinds
    #   Goner       Gumbo: he shows a shrimp before it, and it blinds
    #   Revenger    Imp Sonata: the imp spell on the whole party
    NAME = "Uncle Ulty"
    LEVELS = 5
    SPEED = 1.2

    ULTROS = "Ultros 2"                     # 1 is the head in the river, the others have the tentacles
    SHADOW_COLOR, SHADOW_ROWS = 1, range(64)
    LOWER = 32                              # pixels: his sprite is 94 high, and clear of the boxes at the top

    ABILITY_NAMES = {
        "HyperDrive"    : "Ink Blast",
        "Goner"         : "Gumbo",
        "Revenger"      : "Imp Sonata",
    }
    GONER_TEXT = "Gwee-hee-hee...<wait 60 frames><end>"
    GONER_TEXT_2 = "It's my special recipe!<wait 60 frames><end>"   # (a line holds some 32 letters)
    SECOND_TEXT = 0x12                      # a line of vargas which goner_text_mod empties
    IMP_SONATA_HIT_RATE = 125

    WATER = 0x80                            # element
    DARK = 0x01                             # status (first byte): blind
    MUDDLE_BYTE, MUDDLE = 1, 0x20           # status (second byte)
    GUMBO_MUDDLE_HIT_RATE = 65

    def enemies_mod(self, enemies):
        ulty = self.enemy(enemies)
        ulty.name = self.NAME
        ulty.special_name = "Tentacle"              # was Havoc Wing
        ulty.speed = min(round(ulty.speed * self.SPEED), 2 ** 8 - 1)
        ulty.absorb_elements |= self.WATER
        self.lower_mod(enemies, self.LOWER)

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id

        special, train, revenger, nothing = (name_id[name] for name in ["Special", "Train", "Revenger", "Nothing"])
        clean_sweep = name_id["CleanSweep"]
        script = scripts.get_script(self.ENEMY)

        # he says two lines before goner
        goner_text = ai_instr.Message(140)
        said = [index for index, instruction in enumerate(script.instructions) if instruction == goner_text]
        assert len(said) == 2
        for index in reversed(said):
            script.insert(index + 1, ai_instr.Message(self.SECOND_TEXT))

        # above 53% hp, every other turn (fire 3 and ice 3 stay)
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(clean_sweep, nothing, special))

        # at 53% hp and below, the turns after goner
        script.replace(ai_instr.RandomAttack(special, train, revenger),      # (revenger is imp sonata)
                       ai_instr.RandomAttack(special, clean_sweep, revenger))

    def data_mod(self, data):
        from data.spell_names import name_id
        from data.ability_data import AbilityData

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.party_status_attack_mod(data, "Imp", self.IMP_SONATA_HIT_RATE)

        # ink blast and the gumbo blind whoever they do not kill
        STATUS1 = 10
        for attack in ("HyperDrive", "Goner"):
            status = ABILITY_DATA_START + name_id[attack] * AbilityData.DATA_SIZE + STATUS1
            data.rom.set_bytes(status, [data.rom.get_bytes(status, 1)[0] | self.DARK])

        # and the gumbo may muddle them, as his lv.3 muddle did
        self.status_chance_mod(data, name_id["Goner"], self.MUDDLE_BYTE, self.MUDDLE, self.GUMBO_MUDDLE_HIT_RATE)

        self.goner_text_mod(data, self.GONER_TEXT, room = True)
        data.dialogs.set_single_line_battle_text(self.SECOND_TEXT, self.GONER_TEXT_2)

    def battle_mod(self):
        from data.bosses import name_enemy
        from data.spell_names import name_id

        self.giant_sprite_mod(name_enemy[self.ULTROS], self.SHADOW_COLOR, self.SHADOW_ROWS)
        self.special_attack_animation_mod(name_id["Tentacle"])
        self.goner_sprite_mod(shrimp.pixels(), shrimp.palette())
        self.ink_blast_mod(name_id["HyperDrive"])
        self.gumbo_mod(name_id["Goner"])

    def _palette(self, palette):
        address = PALETTES + palette * PALETTE_SIZE
        data = Read(address, address + PALETTE_SIZE - 1)
        return [data[index * 2] | (data[index * 2 + 1] << 8) for index in range(PALETTE_COLORS)]

    def ink_blast_mod(self, hyperdrive):
        # hyperdrive, which only final kefka has, in ink: the palettes of its animation's layers, with
        # every color as dark as it was bright and a little blue
        def ink(color):
            red, green, blue = color & 0x1f, (color >> 5) & 0x1f, (color >> 10) & 0x1f
            brightness = (red + green + blue) / 3
            return round(brightness * 0.30) | (round(brightness * 0.28) << 5) | (round(brightness * 0.42) << 10)

        animation = ATTACK_ANIMATIONS + hyperdrive * ATTACK_ANIMATION_SIZE
        LAYERS, LAYER_PALETTES = 3, 6
        for layer in range(LAYERS):
            layer_animation = Read(animation + layer * 2, animation + layer * 2 + 1)
            if layer_animation == [0xff, 0xff]:
                continue
            palette = Read(animation + LAYER_PALETTES + layer, animation + LAYER_PALETTES + layer)[0]
            ink_palette = self.add_palette([ink(color) for color in self._palette(palette)])

            space = Reserve(animation + LAYER_PALETTES + layer, animation + LAYER_PALETTES + layer, "ink blast palette")
            space.write(ink_palette)


    def gumbo_mod(self, goner):
        # goner, which only final kefka has, in blue and black for red: the palette of its streaks,
        # and what its animation script does to the colors of the background and of the monster
        #
        # the script's color commands (b6: the background, b9 and bc: the monsters) take a byte:
        # which of red (0x80), green (0x40) and blue (0x20), more (0x10) or less, and how much
        SCRIPT_POINTERS, SCRIPTS = 0x11ead8, 0x100000
        BG1_LAYER, LAYER_PALETTES = 1, 6
        SCRIPT_SIZE = 258

        animation = ATTACK_ANIMATIONS + goner * ATTACK_ANIMATION_SIZE
        layer_animation = Read(animation + BG1_LAYER * 2, animation + BG1_LAYER * 2 + 1)
        layer_animation = layer_animation[0] | (layer_animation[1] << 8)

        # the streaks: red and blue change places
        palette = Read(animation + LAYER_PALETTES + BG1_LAYER, animation + LAYER_PALETTES + BG1_LAYER)[0]
        def blue(color):
            return (color >> 10) & 0x1f | (color & 0x03e0) | ((color & 0x1f) << 10)
        space = Reserve(animation + LAYER_PALETTES + BG1_LAYER, animation + LAYER_PALETTES + BG1_LAYER, "gumbo palette")
        space.write(self.add_palette([blue(color) for color in self._palette(palette)]))

        pointer = Read(SCRIPT_POINTERS + layer_animation * 2, SCRIPT_POINTERS + layer_animation * 2 + 1)
        script_address = SCRIPTS + (pointer[0] | (pointer[1] << 8))
        script = bytes(Read(script_address, script_address + SCRIPT_SIZE - 1))
        for red, blue in (
            ("b6 61", "b6 c1"),             # the background turns red: blue
            ("b6 31", "b6 c1"),             # then to purple: stays blue
            ("b6 81", "b6 21"),             # then to blue: black
            ("b6 91 b6 21", "b6 31 b6 c1"), # and back to red: blue
            ("b9 60", "b9 c0"),             # the monster turns red: blue
            ("bc 61", "bc c1"),
            ("b6 8f bc 8f", "b6 2f bc 2f"), # both go dark
        ):
            red, blue = bytes.fromhex(red), bytes.fromhex(blue)
            assert script.count(red) == 1
            script = script.replace(red, blue)
        space = Reserve(script_address, script_address + SCRIPT_SIZE - 1, "gumbo animation script")
        space.write(list(script))
