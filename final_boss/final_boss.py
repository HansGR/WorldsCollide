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

class FinalBoss:
    # final kefka as he is, and what the other final bosses are made from: each is called where the
    # seed is built to change his enemy, his script, the names of his attacks and the battle itself
    NAME = "Kefka"
    ENEMY = "Kefka (Final)"

    LEVELS = 0              # levels above what final kefka's would be in the battle (battle/load_enemy_level.py)

    def __init__(self):
        from data.bosses import name_enemy
        self.enemy_id = name_enemy[self.ENEMY]

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
