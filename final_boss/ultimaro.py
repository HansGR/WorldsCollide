from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.monster_sprite as monster_sprite
import graphics.green_cherry as green_cherry

from final_boss.final_boss import FinalBoss

class Ultimaro(FinalBoss):
    # umaro, giant. he is 5 levels above final kefka and a fifth faster, absorbs ice as umaro does and
    # has ice where kefka had fire and bolt. he jumps as umaro does, landing 2 to 4 times as with a
    # dragon horn, and eats a green cherry before u'ghaaaa (goner)
    #
    #   Havoc Wing  Yeti Punch, with the looks of umaro's tackle
    #   HyperDrive  Yeti Blast
    #   Goner       U'ghaaaa
    #   Revenger    Enrager: the bserk spell on the whole party
    NAME = "Ultimaro"
    LEVELS = 5
    SPEED = 1.2

    UMARO = "Umaro"
    SHADOW_COLOR, SHADOW_ROWS = 1, 8        # umaro stands on a shadow, a patch of his outline color

    ABILITY_NAMES = {
        "HyperDrive"    : "Yeti Blast",
        "Goner"         : "U'ghaaaa",
        "Revenger"      : "Enrager",
    }
    GONER_TEXT = "Yeti used a Green Cherry!<wait 60 frames><end>"

    def enemies_mod(self, enemies):
        ultimaro = self.enemy(enemies)
        umaro = enemies.enemies[enemies.get_enemy(self.UMARO)]

        ultimaro.name = self.NAME
        ultimaro.special_name = "Yeti Punch"        # was Havoc Wing
        ultimaro.speed = min(round(ultimaro.speed * self.SPEED), 2 ** 8 - 1)
        ultimaro.absorb_elements |= umaro.absorb_elements       # ice

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id
        from data.enemy_script_custom_commands import JUMP

        # a script can choose JUMP as it does its attacks
        scripts.enemy_script_custom_commands.jump_attack_mod()

        special, train, revenger, nothing = (name_id[name] for name in ["Special", "Train", "Revenger", "Nothing"])
        script = scripts.get_script(self.ENEMY)

        # above 53% hp, every other turn
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special),
                       ai_instr.RandomAttack(name_id["Storm"], train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(name_id["Surge"], nothing, special))

        # at 53% hp and below, the turns after goner
        script.replace(ai_instr.RandomAttack(special, train, revenger),      # (revenger is enrager)
                       ai_instr.RandomAttack(special, name_id["Ice 3"], revenger))
        script.replace(ai_instr.RandomAttack(train, special, revenger),
                       ai_instr.RandomAttack(train, special, JUMP))
        script.replace(ai_instr.RandomAttack(special, special, nothing),
                       ai_instr.RandomAttack(special, JUMP, nothing))

    def data_mod(self, data):
        self.rename_abilities(data, self.ABILITY_NAMES)
        self.enrager_mod(data)

        goner_dialog = 140      # "the end comes...beyond chaos."
        data.dialogs.set_single_line_battle_text(goner_dialog, self.GONER_TEXT)

    def enrager_mod(self, data):
        # revenger, which only final kefka has, is enrager: the bserk spell (as it is in this seed)
        # cast on the whole party, with revenger's animation. unlike bserk it can not be reflected or
        # absorbed by runic, and it misses more: bserk's hit rate is 150, which always hits a magic
        # block below 44 (the chance is hit rate * (256 - 2 * magic block) / 256). with 75, 3 in 4
        # without magic block and half at 40
        from data.spell_names import name_id
        from data.ability_data import AbilityData
        ABILITY_DATA_START = 0x046ac0
        NOT_REFLECTABLE, RUNIC = 0x02, 0x08     # flags2
        HIT_RATE = 75

        revenger = ABILITY_DATA_START + name_id["Revenger"] * AbilityData.DATA_SIZE
        revenger_targets = data.rom.get_bytes(revenger, 1)[0]       # all of the other side

        enrager = data.spells.spells[name_id["Bserk"]]
        enrager = AbilityData(name_id["Revenger"], enrager.ability_data())
        enrager.targets = revenger_targets
        enrager.flags2 = (enrager.flags2 | NOT_REFLECTABLE) & ~RUNIC
        enrager.accuracy = HIT_RATE
        data.rom.set_bytes(revenger, enrager.ability_data())

    def battle_mod(self):
        from data.bosses import name_enemy
        umaro = name_enemy[self.UMARO]

        self.giant_sprite_mod(umaro, self.SHADOW_COLOR, self.SHADOW_ROWS)
        self.special_attack_mod(umaro)
        self.jump_mod()
        self.jump_animation_mod()
        self.green_cherry_mod()

    def special_attack_mod(self, umaro):
        # ultimaro's special attack (yeti punch: final kefka's havoc wing, and still that
        # attack in every other way) looks and sounds like umaro's (tackle)
        SPECIAL_ATTACK_GRAPHICS = 0xf37c0       # a byte for each enemy

        space = Reserve(SPECIAL_ATTACK_GRAPHICS + self.enemy_id, SPECIAL_ATTACK_GRAPHICS + self.enemy_id, "final kefka special attack graphic")
        space.write(
            Read(SPECIAL_ATTACK_GRAPHICS + umaro, SPECIAL_ATTACK_GRAPHICS + umaro),
        )

    def jump_mod(self):
        # when ultimaro jumps (scripts_mod) he lands 2 to 4 times, as
        # with a dragon horn: where the jump command looks for the jumper's dragon horn ("jump
        # continuously", bit 7 of its relic effects), he has one
        # x = the jumper (8 and up are the enemies). 8 bit a, x and y
        JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END = 0x21820, 0x21822

        relic_effects = 0x3c44
        enemy_ids = 0x33a8
        first_enemy = 8

        src = [
            Read(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END),
            asm.BMI("RETURN"),                      # branch if the jumper has a dragon horn

            asm.CPX(first_enemy, asm.IMM8),
            asm.BLT("NO_DRAGON_HORN"),
            asm.A16(),
            asm.LDA(enemy_ids, asm.ABS_X),
            asm.CMP(self.enemy_id, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BNE("NO_DRAGON_HORN"),
            asm.LDA(0x80, asm.IMM8),
            asm.RTS(),

            "NO_DRAGON_HORN",
            asm.LDA(relic_effects, asm.ABS_X),

            "RETURN",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "ultimaro jumps as with a dragon horn")
        jumper_relic_effects = space.start_address

        space = Reserve(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END, "jump: load jumper's relic effects", asm.NOP())
        space.write(
            asm.JSR(jumper_relic_effects, asm.ABS),
        )

    def jump_animation_mod(self):
        # a jumper with more landings to come (only the dragon horn does that) bounces: down onto
        # the target and straight back up, and it returns to its place only after the last landing.
        # the game's own animation hops back after every landing
        #
        # the damage of a landing shows when its animation has ended, and outside of an animation
        # monsters are drawn over the characters and the damage. so the jumper goes up at the speed
        # it took off with and nothing is left to wait for after that: the damage shows as soon as
        # it is gone
        #
        # the landing of a monster's jump is animation script 0x84 (D1/EAD8 has the scripts'
        # pointers, they are in bank D0). it is copied here with the bounce added after the fall
        LANDING_SCRIPT = 0x84
        SCRIPT_POINTERS = 0x11ead8
        LANDING_START, LANDING_END = 0x10682d, 0x106855
        FALL_END = 0x10684e                 # the fall's last byte; what follows is the hop back and the end

        landing = Read(LANDING_START, LANDING_END)
        fall = landing[:FALL_END - LANDING_START + 1]
        hop_back = landing[FALL_END - LANDING_START + 1:]

        DOWN_8_PIXELS, UP_8_PIXELS, DOWN_32_PIXELS = 0x27, 0xc7, 0x3f
        assert fall[-6:] == [0x89, 0x13, 0x86, DOWN_8_PIXELS, 0x0f, 0x8a]   # 20 times: move, wait a frame
        assert hop_back == [0xd1, 0x00, 0x0f, 0xe3, 0x08, 0x03, 0xff]

        src = [
            fall,
            0x80, 0x7d, len(hop_back),      # skip the hop back if another landing is coming
            hop_back,

            0x89, 0x13,                     # 20 times, the way it came:
                0x86, UP_8_PIXELS,
                0x0f,                       # wait a frame
            0x8a,
            0xe1, 0x80,                     # hide the monster
            [0x86, DOWN_32_PIXELS] * 5,     # the script is back where the fall ended
            0xd1, 0x00,                     # (as before the hop back)
            0xe3, 0xff, 0x00,               # the hop back, all of it at once: the monster is in its place
            0xff,
        ]
        src = [value for values in src for value in (values if isinstance(values, list) else [values])]
        space = Write(Bank.D0, src, "ultimaro: monster jump landing animation")
        landing_script = space.start_address

        pointer = SCRIPT_POINTERS + LANDING_SCRIPT * 2
        space = Reserve(pointer, pointer + 1, "monster jump landing animation script pointer")
        space.write(
            (landing_script & 0xffff).to_bytes(2, "little"),
        )

    def green_cherry_mod(self):
        # before goner (u'ghaaaa, after "Yeti used a Green Cherry!") final kefka's laughing head
        # appears in front of him and fades away: battle animation 399. it becomes the green cherry
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
        # nothing else, and neither is that part of the layout
        ATTACK_ANIMATIONS, ATTACK_ANIMATION_SIZE = 0x107fb2, 14
        LAYER_ANIMATIONS, LAYER_ANIMATION_SIZE = 0x14d000, 6
        FRAME_POINTERS, FRAMES = 0x14df3c, 0x110000
        TILE_LAYOUTS, TILE_LAYOUT_STEP = 0x120000, 0x40
        GRAPHICS = 0x130000
        PALETTES, PALETTE_SIZE = 0x126000, 16

        LAUGHING_HEAD = 399
        BG1_LAYER = 1
        EMPTY_TILE = 0x0015
        LAYOUT_ROW_TILES = 16               # 8x8 tiles in a row of a tile layout
        FLIPPED = 0x40
        HEAD_FRAME = [0x73, 0x11 | FLIPPED, 0x83, 0x10 | FLIPPED, 0x74, 0x19 | FLIPPED, 0x84, 0x18 | FLIPPED]
        CHERRY_PALETTE = 0xfe               # after the game's palettes, where nothing is

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
        TILES = green_cherry.SIZE // monster_sprite.TILE_PIXELS
        first_row, first_column = 2 * (0x10 // 8), 2 * (0x10 % 8)
        layout_rows = [tile_layout + ((first_row + row) * LAYOUT_ROW_TILES + first_column) * 2 for row in range(TILES)]
        own_tiles = [word(layout_row + column * 2) for layout_row in layout_rows for column in range(TILES)]
        own_tiles = [tile for tile in own_tiles if tile != EMPTY_TILE]

        # the frame flips its tiles, and an animation is flipped again when a monster is the
        # attacker: the cherry is seen as it is stored
        pixels = green_cherry.pixels()
        for row, layout_row in enumerate(layout_rows):
            layout = []
            for column in range(TILES):
                tile = [pixels[row * monster_sprite.TILE_PIXELS + y][column * monster_sprite.TILE_PIXELS:][:monster_sprite.TILE_PIXELS]
                        for y in range(monster_sprite.TILE_PIXELS)]
                if not any(map(any, tile)):
                    layout += EMPTY_TILE.to_bytes(2, "little")
                    continue

                own_tile = own_tiles.pop(0)     # (the cherry has no more tiles than the head had)
                layout += own_tile.to_bytes(2, "little")

                tile_address = GRAPHICS + own_tile * monster_sprite.TILE_SIZE_3BPP
                space = Reserve(tile_address, tile_address + monster_sprite.TILE_SIZE_3BPP - 1, "green cherry graphics")
                space.write(monster_sprite.tile_data(tile, three_bpp = True))

            space = Reserve(layout_row, layout_row + len(layout) - 1, "green cherry tile layout")
            space.write(layout)

        palette_address = PALETTES + CHERRY_PALETTE * PALETTE_SIZE
        space = Reserve(palette_address, palette_address + PALETTE_SIZE - 1, "green cherry palette")
        space.write([color.to_bytes(2, "little") for color in green_cherry.palette()])

        BG1_PALETTE = attack_animation + 6 + BG1_LAYER
        space = Reserve(BG1_PALETTE, BG1_PALETTE, "laughing head palette")
        space.write(CHERRY_PALETTE)
