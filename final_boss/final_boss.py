from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.monster_sprite as monster_sprite

# monster graphics specs (D2/7000, 5 bytes each): pointer to the graphics (bits 0-14: offset / 8 from
# E9/7000, bit 15: 3bpp), large mold flag (bit 7) and palette, mold
GRAPHICS_SPECS = 0x127000
GRAPHICS_SPEC_SIZE = 5
GRAPHICS = 0x297000
SMALL_MOLDS = 0x12a824
LARGE_MOLDS = 0x12ac24

GIANT_SPRITE_POINTER = 0x7fff       # a graphics pointer no monster has
GIANT_SPRITE_SCALE = 2

ABILITY_NAMES_START, FIRST_NAMED_ABILITY, ABILITY_NAME_SIZE = 0x26f7b9, 81, 10
ABILITY_DATA_START = 0x046ac0

# battle animation palettes (D2/6000, 8 colors each). the game's end at 0xef, and what follows up
# to 0xf6 is other data: these are free
PALETTES, PALETTE_SIZE = 0x126000, 16
FREE_PALETTES = [0xfe, 0xfd, 0xfc, 0xfb, 0xfa, 0xf9, 0xf8, 0xf7]

class FinalBoss:
    # final kefka as he is, and what the other final bosses are made from: each is called where the
    # seed is built to change his enemy, his script, the names of his attacks and the battle itself
    NAME = "Kefka"
    ENEMY = "Kefka (Final)"

    LEVELS = 0              # levels above what final kefka's would be in the battle (battle/load_enemy_level.py)

    def __init__(self):
        from data.bosses import name_enemy
        self.enemy_id = name_enemy[self.ENEMY]
        self.free_palettes = list(FREE_PALETTES)

    def enemies_mod(self, enemies):
        # his stats and name (data/enemies.py, with the other enemies')
        pass

    def scripts_mod(self, scripts):
        # his battle script (data/enemy_scripts.py, before abilities are scaled)
        pass

    def data_mod(self, data):
        # anything else in the data: attack names, spells, battle text (data/data.py, as it is written)
        pass

    def battle_mod(self):
        # the battle's own code and graphics (battle/final_boss.py)
        pass

    # what follows is for the final bosses to use

    def enemy(self, enemies):
        return enemies.enemies[self.enemy_id]

    def lower_mod(self, enemies, pixels):
        # he is this much lower on the screen than final kefka (who is 16 pixels from its top), in
        # steps of 8 pixels: for a sprite that is not as high, to be clear of the boxes at the top.
        # (leaving the top of his mold empty instead hangs the battle as he appears)
        FINAL_FORMATION = 0x202             # the last tier of the final battle, he is its first enemy
        POSITION_PIXELS = 8

        formation = enemies.formations.formations[FINAL_FORMATION]
        assert formation.enemy_ids[0] == self.enemy_id
        formation.enemy_y_positions[0] += pixels // POSITION_PIXELS

    def rename_abilities(self, data, names):
        # the attacks named in the box at the top of the screen, {name : new name}. -steveify names them all
        import data.text as text
        from data.spell_names import name_id
        if data.args.steveify:
            return
        for ability, name in names.items():
            name_bytes = text.get_bytes(name, text.TEXT2)
            name_bytes += [0xff] * (ABILITY_NAME_SIZE - len(name_bytes))
            data.rom.set_bytes(ABILITY_NAMES_START + (name_id[ability] - FIRST_NAMED_ABILITY) * ABILITY_NAME_SIZE, name_bytes)

    def goner_text_mod(self, data, text, room = False):
        # what is said at the top of the screen before goner ("the end comes...beyond chaos."). the
        # battle's one line texts share a fixed space: a longer text asks for room, and the four
        # lines of vargas which the randomizer takes out of his script are emptied
        import data.enemy_script_commands as ai_instr
        GONER_TEXT = 140
        VARGAS_TEXTS = [0x12, 0x43, 0x0a, 0x42]

        data.dialogs.set_single_line_battle_text(GONER_TEXT, text)
        if room:
            for script in data.enemies.scripts.scripts:
                if script.id == self.enemy_id:
                    continue                # (the final boss may say them himself, with another text)
                for said in VARGAS_TEXTS:
                    assert ai_instr.Message(said) not in script.instructions, f"battle text {said} is in use"
            for unsaid in VARGAS_TEXTS:
                data.dialogs.set_single_line_battle_text(unsaid, "<end>")

    def add_palette(self, colors):
        # a battle animation palette of these 8 colors (15 bit), and its number
        palette = self.free_palettes.pop(0)
        address = PALETTES + palette * PALETTE_SIZE
        space = Reserve(address, address + PALETTE_SIZE - 1, "final boss: battle animation palette")
        space.write([color.to_bytes(2, "little") for color in colors])
        return palette

    def party_status_attack_mod(self, data, spell, hit_rate):
        # revenger, which only final kefka has, becomes this spell (as it is in this seed) cast on the
        # whole party, with revenger's animation. unlike the spell it can not be reflected or absorbed
        # by runic, and it has this hit rate: the chance to hit is hit rate * (256 - 2 * magic block)
        # / 256, so 150 always hits a magic block below 44, and 75 hits 3 in 4 without magic block
        from data.spell_names import name_id
        from data.ability_data import AbilityData
        NOT_REFLECTABLE, RUNIC = 0x02, 0x08     # flags2

        revenger = ABILITY_DATA_START + name_id["Revenger"] * AbilityData.DATA_SIZE
        revenger_targets = data.rom.get_bytes(revenger, 1)[0]       # all of the other side

        attack = AbilityData(name_id["Revenger"], data.spells.spells[name_id[spell]].ability_data())
        attack.targets = revenger_targets
        attack.flags2 = (attack.flags2 | NOT_REFLECTABLE) & ~RUNIC
        attack.accuracy = hit_rate
        data.rom.set_bytes(revenger, attack.ability_data())

    def status_chance_mod(self, data, attack, status_byte, status, hit_rate):
        # an attack with no special effect also sets this status (0x20 of byte 1 (0 to 3) is muddle)
        # on each target it hits, with a hit rate of its own: the chance is hit rate * (256 - 2 *
        # magic block) / 256, as it is for a spell, and none for a target protected from the status.
        # the attack's own status bytes always take with an attack that can not be dodged
        # called once for each target hit: y = the target. 8 bit a, x and y
        from data.ability_data import AbilityData
        EFFECT = 9                              # in the attack's data
        NO_EFFECT = 0xff
        TARGET_EFFECTS = 0x23dcd                # what to call for each target, by special effect
        FREE_EFFECT = 0x45                      # does nothing for each target, or for each strike
        NOTHING = 0x388c
        MULTIPLY, RANDOM = 0x4781, 0x4b65       # a * b, 0 to a - 1

        magic_block = 0x3b55                    # 255 - magic block * 2 + 1
        vulnerable = 0x331c + status_byte       # statuses the target is not protected from
        status_to_set = (0x3dd4, 0x3dd5, 0x3de8, 0x3de9)[status_byte]
        chance = 0xee

        effect = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE + EFFECT
        assert data.rom.get_bytes(effect, 1)[0] == NO_EFFECT, "the attack has a special effect"
        pointer = TARGET_EFFECTS + FREE_EFFECT * 2
        assert Read(pointer, pointer + 1) == list(NOTHING.to_bytes(2, "little")), "the effect is in use"
        data.rom.set_bytes(effect, [FREE_EFFECT])

        src = [
            asm.LDA(magic_block, asm.ABS_Y),
            asm.XBA(),
            asm.LDA(hit_rate, asm.IMM8),
            asm.JSR(MULTIPLY, asm.ABS),
            asm.XBA(),
            asm.STA(chance, asm.DIR),
            asm.LDA(100, asm.IMM8),
            asm.JSR(RANDOM, asm.ABS),
            asm.CMP(chance, asm.DIR),
            asm.BGE("RETURN"),
            asm.LDA(vulnerable, asm.ABS_Y),
            asm.AND(status, asm.IMM8),
            asm.ORA(status_to_set, asm.ABS_Y),
            asm.STA(status_to_set, asm.ABS_Y),
            "RETURN",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: status chance")
        Reserve(pointer, pointer + 1, "final boss: status chance pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

    def special_attack_animation_mod(self, attack):
        # his special attack (havoc wing) looks and sounds like this attack, one the lore command
        # animates (0x8b and up: the enemies' own), and is otherwise what it was: when the battle
        # queues the animation of his special, it queues that of the attack in its place
        # x = the attacker (8 and up are the enemies). 8 bit a, x and y
        QUEUE_ANIMATION_START, QUEUE_ANIMATION_END = 0x23414, 0x23416
        QUEUE_ANIMATION = 0x35ad
        SPECIAL_MESSAGE = 0x06
        LORE_COMMAND = 0x0c

        message = 0x3412            # what is named at the top of the screen
        command, command_attack = 0xb5, 0xb6
        enemy_ids = 0x33a8
        first_enemy = 8

        src = [
            asm.LDA(message, asm.ABS),
            asm.CMP(SPECIAL_MESSAGE, asm.IMM8),
            asm.BNE("AS_IT_IS"),
            asm.CPX(first_enemy, asm.IMM8),
            asm.BLT("AS_IT_IS"),
            asm.A16(),
            asm.LDA(enemy_ids, asm.ABS_X),
            asm.CMP(self.enemy_id, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BNE("AS_IT_IS"),

            asm.LDA(command, asm.DIR),
            asm.PHA(),
            asm.LDA(command_attack, asm.DIR),
            asm.PHA(),
            asm.LDA(LORE_COMMAND, asm.IMM8),
            asm.STA(command, asm.DIR),
            asm.LDA(attack, asm.IMM8),
            asm.STA(command_attack, asm.DIR),
            asm.JSR(QUEUE_ANIMATION, asm.ABS),
            asm.PLA(),
            asm.STA(command_attack, asm.DIR),
            asm.PLA(),
            asm.STA(command, asm.DIR),
            asm.RTS(),

            "AS_IT_IS",
            asm.JMP(QUEUE_ANIMATION, asm.ABS),
        ]
        space = Write(Bank.C2, src, "final boss: special attack animation")
        queue_animation = space.start_address

        space = Reserve(QUEUE_ANIMATION_START, QUEUE_ANIMATION_END, "queue attack animation", asm.NOP())
        space.write(
            asm.JSR(queue_animation, asm.ABS),
        )

    def goner_sprite_mod(self, pixels, palette):
        # before goner final kefka's laughing head appears in front of him and fades away: battle
        # animation 399. it becomes this picture: 32 rows of 32 palette indices (0 is transparent),
        # and its 8 colors (the first is unused). the picture is seen as it is given
        #
        # an attack animation (D0/7FB2, 14 bytes) names an animation for each of 3 layers and their
        # palettes (D2/6000, 8 colors each). a layer's animation (D4/D000, 6 bytes) has its number
        # of frames, its tile layout, its first frame and its size. a tile layout is a part of
        # D2/0000: rows of 16 8x8 tiles, 2 bytes each (the tile in the 3bpp graphics at D3/0000,
        # bit 14: flipped left to right, bit 15: upside down), starting 0x40 bytes later with each
        # layout. a frame (D4/DF3C has their pointers, they are in bank D1) lists 16x16 tiles of
        # the layout: where it goes (x, y: a nibble each) and which one (8 to a row, bit 6: flipped
        # left to right)
        #
        # the head is 4 16x16 tiles, flipped. their 14 8x8 tiles (2 are the empty tile) are used by
        # nothing else, and neither is that part of the layout. a picture with pixels in more than
        # 14 of its 16 tiles takes the rest from the free space after the last of the graphics
        ATTACK_ANIMATIONS, ATTACK_ANIMATION_SIZE = 0x107fb2, 14
        LAYER_ANIMATIONS, LAYER_ANIMATION_SIZE = 0x14d000, 6
        FRAME_POINTERS, FRAMES = 0x14df3c, 0x110000
        TILE_LAYOUTS, TILE_LAYOUT_STEP = 0x120000, 0x40
        GRAPHICS = 0x130000

        LAUGHING_HEAD = 399
        BG1_LAYER = 1
        EMPTY_TILE = 0x0015
        LAYOUT_ROW_TILES = 16               # 8x8 tiles in a row of a tile layout
        FLIPPED = 0x40
        HEAD_FRAME = [0x73, 0x11 | FLIPPED, 0x83, 0x10 | FLIPPED, 0x74, 0x19 | FLIPPED, 0x84, 0x18 | FLIPPED]

        def word(address):
            return int.from_bytes(bytes(Read(address, address + 1)), "little")

        attack_animation = ATTACK_ANIMATIONS + LAUGHING_HEAD * ATTACK_ANIMATION_SIZE
        layer_animation = LAYER_ANIMATIONS + word(attack_animation + BG1_LAYER * 2) * LAYER_ANIMATION_SIZE
        frames, tile_layout = Read(layer_animation, layer_animation + 1)
        tile_layout = TILE_LAYOUTS + ((frames & 0x40) << 2 | tile_layout) * TILE_LAYOUT_STEP

        frame = word(layer_animation + 2)
        frame_start, frame_end = word(FRAME_POINTERS + frame * 2), word(FRAME_POINTERS + frame * 2 + 2)
        assert frames & 0x3f == 1 and Read(FRAMES + frame_start, FRAMES + frame_end - 1) == HEAD_FRAME

        # the 8x8 tiles of the frame's 16x16 tiles 0x10, 0x11, 0x18 and 0x19: 4 rows of 4
        TILES = len(pixels) // monster_sprite.TILE_PIXELS
        first_row, first_column = 2 * (0x10 // 8), 2 * (0x10 % 8)
        layout_rows = [tile_layout + ((first_row + row) * LAYOUT_ROW_TILES + first_column) * 2 for row in range(TILES)]
        own_tiles = [word(layout_row + column * 2) for layout_row in layout_rows for column in range(TILES)]
        own_tiles = [tile for tile in own_tiles if tile != EMPTY_TILE]

        FREE_GRAPHICS_START, FREE_GRAPHICS_END = 0x14c998, 0x14c9ff
        first_free_tile = (FREE_GRAPHICS_START - GRAPHICS) // monster_sprite.TILE_SIZE_3BPP
        free_tiles = (FREE_GRAPHICS_END + 1 - FREE_GRAPHICS_START) // monster_sprite.TILE_SIZE_3BPP
        own_tiles += range(first_free_tile, first_free_tile + free_tiles)

        # (the frame flips its tiles, and an animation is flipped again when a monster is the
        # attacker: the picture is seen as it is stored)
        for row, layout_row in enumerate(layout_rows):
            layout = []
            for column in range(TILES):
                tile = [pixels[row * monster_sprite.TILE_PIXELS + y][column * monster_sprite.TILE_PIXELS:][:monster_sprite.TILE_PIXELS]
                        for y in range(monster_sprite.TILE_PIXELS)]
                if not any(map(any, tile)):
                    layout += EMPTY_TILE.to_bytes(2, "little")
                    continue

                own_tile = own_tiles.pop(0)
                layout += own_tile.to_bytes(2, "little")

                tile_address = GRAPHICS + own_tile * monster_sprite.TILE_SIZE_3BPP
                space = Reserve(tile_address, tile_address + monster_sprite.TILE_SIZE_3BPP - 1, "final boss: goner sprite graphics")
                space.write(monster_sprite.tile_data(tile, three_bpp = True))

            space = Reserve(layout_row, layout_row + len(layout) - 1, "final boss: goner sprite tile layout")
            space.write(layout)

        BG1_PALETTE = attack_animation + 6 + BG1_LAYER
        space = Reserve(BG1_PALETTE, BG1_PALETTE, "laughing head palette")
        space.write(self.add_palette(palette))

    def _spec_address(self, enemy):
        return GRAPHICS_SPECS + enemy * GRAPHICS_SPEC_SIZE

    def small_sprite(self, enemy):
        # the pixels of a monster with a small mold and 4bpp graphics, and its graphics spec
        spec = Read(self._spec_address(enemy), self._spec_address(enemy) + GRAPHICS_SPEC_SIZE - 1)
        pointer = spec[0] | (spec[1] << 8)
        assert not pointer & 0x8000 and not spec[2] & 0x80

        tiles = monster_sprite.SMALL_MOLD_TILES
        mold_address = SMALL_MOLDS + spec[4] * monster_sprite.mold_size(tiles)
        mold = Read(mold_address, mold_address + monster_sprite.mold_size(tiles) - 1)

        graphics_address = GRAPHICS + pointer * 8
        graphics_size = monster_sprite.mold_tile_count(mold) * monster_sprite.TILE_SIZE_4BPP
        graphics = Read(graphics_address, graphics_address + graphics_size - 1)

        return monster_sprite.sprite_pixels(mold, tiles, graphics), spec

    def giant_sprite_mod(self, enemy, shadow_color = None, shadow_rows = 0):
        # the final boss looks like this enemy (one with a small mold: up to 64x64 pixels), at twice its
        # size and in its palette. a shadow under its feet (its color, and how many of the sprite's last
        # rows it is in) is removed: the final boss is in the air
        #
        # the sprite is given to final kefka in kefka's own mold (no other monster uses it). it does not
        # fit where kefka's was and nothing is free in reach of the 15 bit pointer, so it is written
        # wherever there is room and kefka's pointer is a value no monster has, which the graphics
        # loader is taught to send there
        pixels, enemy_spec = self.small_sprite(enemy)
        if shadow_rows:
            pixels = monster_sprite.without_shadow(pixels, shadow_color, shadow_rows)
        mold, graphics = monster_sprite.sprite_data(monster_sprite.scale(pixels, GIANT_SPRITE_SCALE))
        assert len(mold) == monster_sprite.mold_size(monster_sprite.LARGE_MOLD_TILES)

        space = Write(Bank.F0, graphics, "final boss graphics")
        self._graphics_loader_mod(space.start_address_snes)

        kefka_spec_address = self._spec_address(self.enemy_id)
        kefka_mold = Read(kefka_spec_address + 4, kefka_spec_address + 4)[0]

        space = Reserve(kefka_spec_address, kefka_spec_address + GRAPHICS_SPEC_SIZE - 1, "final kefka graphics spec")
        space.write(
            GIANT_SPRITE_POINTER & 0xff, GIANT_SPRITE_POINTER >> 8,
            0x80 | (enemy_spec[2] & 0x7f),      # large mold, the enemy's palette
            enemy_spec[3],
            kefka_mold,
        )

        mold_address = LARGE_MOLDS + kefka_mold * len(mold)
        space = Reserve(mold_address, mold_address + len(mold) - 1, "final kefka mold")
        space.write(mold)

    def _graphics_loader_mod(self, giant_sprite_graphics):
        # where the loader adds the start of the monster graphics to the offset in $64-$66
        # (8 bit a, data bank $7e), $81a8 is the monster's graphics pointer
        ADD_GRAPHICS_START, ADD_GRAPHICS_END = 0x1210b, 0x1211d

        graphics_pointer = 0x81a8
        address = 0x64

        src = [
            asm.A16(),
            asm.LDA(graphics_pointer, asm.ABS),
            asm.CMP(GIANT_SPRITE_POINTER, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BEQ("GIANT_SPRITE"),
            Read(ADD_GRAPHICS_START, ADD_GRAPHICS_END),
            asm.RTL(),

            "GIANT_SPRITE",
            asm.LDA(giant_sprite_graphics & 0xff, asm.IMM8),
            asm.STA(address, asm.DIR),
            asm.LDA((giant_sprite_graphics >> 8) & 0xff, asm.IMM8),
            asm.STA(address + 1, asm.DIR),
            asm.LDA(giant_sprite_graphics >> 16, asm.IMM8),
            asm.STA(address + 2, asm.DIR),
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "final boss: monster graphics address")
        graphics_address = space.start_address_snes

        space = Reserve(ADD_GRAPHICS_START, ADD_GRAPHICS_END, "monster graphics address", asm.NOP())
        space.write(
            asm.JSL(graphics_address),
        )
