from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.monster_sprite as monster_sprite

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
