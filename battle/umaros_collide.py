from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.monster_sprite as monster_sprite
import graphics.green_cherry as green_cherry

# UMAROS COLLIDE: the last tier of the final battle is a giant umaro
#
# monster graphics specs (D2/7000, 5 bytes each): pointer to the graphics (bits 0-14: offset / 8 from
# E9/7000, bit 15: 3bpp), large mold flag (bit 7) and palette, mold
#
# umaro's sprite is drawn at twice its size and given to final kefka, in kefka's own mold (no other
# monster uses it). the bigger sprite does not fit where kefka's was and nothing is free in reach of the
# 15 bit pointer, so it is written wherever there is room and kefka's pointer is a value no monster has,
# which the graphics loader is taught to send there

GRAPHICS_SPECS = 0x127000
GRAPHICS_SPEC_SIZE = 5
GRAPHICS = 0x297000
SMALL_MOLDS = 0x12a824
LARGE_MOLDS = 0x12ac24

GIANT_UMARO_POINTER = 0x7fff
SCALE = 2

class _UmarosCollide:
    def __init__(self):
        from data.bosses import name_enemy
        self.giant_umaro_mod(name_enemy["Umaro"], name_enemy["Kefka (Final)"])
        self.jump_mod(name_enemy["Kefka (Final)"])
        self.jump_animation_mod()
        self.special_attack_mod(name_enemy["Umaro"], name_enemy["Kefka (Final)"])
        self.green_cherry_mod()

    def spec_address(self, enemy):
        return GRAPHICS_SPECS + enemy * GRAPHICS_SPEC_SIZE

    def small_sprite(self, enemy):
        # the pixels of a monster with a small mold and 4bpp graphics, and its graphics spec
        spec = Read(self.spec_address(enemy), self.spec_address(enemy) + GRAPHICS_SPEC_SIZE - 1)
        pointer = spec[0] | (spec[1] << 8)
        assert not pointer & 0x8000 and not spec[2] & 0x80

        tiles = monster_sprite.SMALL_MOLD_TILES
        mold_address = SMALL_MOLDS + spec[4] * monster_sprite.mold_size(tiles)
        mold = Read(mold_address, mold_address + monster_sprite.mold_size(tiles) - 1)

        graphics_address = GRAPHICS + pointer * 8
        graphics_size = monster_sprite.mold_tile_count(mold) * monster_sprite.TILE_SIZE_4BPP
        graphics = Read(graphics_address, graphics_address + graphics_size - 1)

        return monster_sprite.sprite_pixels(mold, tiles, graphics), spec

    def giant_umaro_mod(self, umaro, kefka):
        pixels, umaro_spec = self.small_sprite(umaro)

        # umaro stands on a shadow, which has no place in the sky of the final battle
        SHADOW_COLOR, SHADOW_ROWS = 1, 8
        pixels = monster_sprite.without_shadow(pixels, SHADOW_COLOR, SHADOW_ROWS)

        mold, graphics = monster_sprite.sprite_data(monster_sprite.scale(pixels, SCALE))
        assert len(mold) == monster_sprite.mold_size(monster_sprite.LARGE_MOLD_TILES)

        space = Write(Bank.F0, graphics, "umaros collide: giant umaro graphics")
        self.graphics_loader_mod(space.start_address_snes)

        kefka_spec_address = self.spec_address(kefka)
        kefka_mold = Read(kefka_spec_address + 4, kefka_spec_address + 4)[0]

        space = Reserve(kefka_spec_address, kefka_spec_address + GRAPHICS_SPEC_SIZE - 1, "final kefka graphics spec")
        space.write(
            GIANT_UMARO_POINTER & 0xff, GIANT_UMARO_POINTER >> 8,
            0x80 | (umaro_spec[2] & 0x7f),      # large mold, umaro's palette
            umaro_spec[3],
            kefka_mold,
        )

        mold_address = LARGE_MOLDS + kefka_mold * len(mold)
        space = Reserve(mold_address, mold_address + len(mold) - 1, "final kefka mold")
        space.write(mold)

    def special_attack_mod(self, umaro, kefka):
        # the giant umaro's special attack (yeti punch: final kefka's havoc wing, and still that
        # attack in every other way) looks and sounds like umaro's (tackle)
        SPECIAL_ATTACK_GRAPHICS = 0xf37c0       # a byte for each enemy

        space = Reserve(SPECIAL_ATTACK_GRAPHICS + kefka, SPECIAL_ATTACK_GRAPHICS + kefka, "final kefka special attack graphic")
        space.write(
            Read(SPECIAL_ATTACK_GRAPHICS + umaro, SPECIAL_ATTACK_GRAPHICS + umaro),
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

    def jump_mod(self, kefka):
        # when the giant umaro jumps (data/enemy_scripts.py ultimaro_mod) he lands 2 to 4 times, as
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
            asm.CMP(kefka, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BNE("NO_DRAGON_HORN"),
            asm.LDA(0x80, asm.IMM8),
            asm.RTS(),

            "NO_DRAGON_HORN",
            asm.LDA(relic_effects, asm.ABS_X),

            "RETURN",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "umaros collide: giant umaro jumps as with a dragon horn")
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
        space = Write(Bank.D0, src, "umaros collide: monster jump landing animation")
        landing_script = space.start_address

        pointer = SCRIPT_POINTERS + LANDING_SCRIPT * 2
        space = Reserve(pointer, pointer + 1, "monster jump landing animation script pointer")
        space.write(
            (landing_script & 0xffff).to_bytes(2, "little"),
        )

    def graphics_loader_mod(self, giant_umaro_graphics):
        # where the loader adds the start of the monster graphics to the offset in $64-$66
        # (8 bit a, data bank $7e), $81a8 is the monster's graphics pointer
        ADD_GRAPHICS_START, ADD_GRAPHICS_END = 0x1210b, 0x1211d

        graphics_pointer = 0x81a8
        address = 0x64

        src = [
            asm.A16(),
            asm.LDA(graphics_pointer, asm.ABS),
            asm.CMP(GIANT_UMARO_POINTER, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BEQ("GIANT_UMARO"),
            Read(ADD_GRAPHICS_START, ADD_GRAPHICS_END),
            asm.RTL(),

            "GIANT_UMARO",
            asm.LDA(giant_umaro_graphics & 0xff, asm.IMM8),
            asm.STA(address, asm.DIR),
            asm.LDA((giant_umaro_graphics >> 8) & 0xff, asm.IMM8),
            asm.STA(address + 1, asm.DIR),
            asm.LDA(giant_umaro_graphics >> 16, asm.IMM8),
            asm.STA(address + 2, asm.DIR),
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "umaros collide: monster graphics address")
        graphics_address = space.start_address_snes

        space = Reserve(ADD_GRAPHICS_START, ADD_GRAPHICS_END, "monster graphics address", asm.NOP())
        space.write(
            asm.JSL(graphics_address),
        )

umaros_collide = _UmarosCollide()
