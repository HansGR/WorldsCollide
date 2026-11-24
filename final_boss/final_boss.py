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

HELPERS_MOLD = 13                   # the mold of a final boss with helpers (the game has 0 to 12)
CHANCE = 0x0a                       # a script condition (chance_condition_mod)
DAMAGED = 0x0a                      # or this one (damaged_condition_mod)
HELPER_ENEMY = 382                  # an enemy no formation has: the helpers' own
HELPERS = 0x06                      # his helpers: the second and third enemies of his formation

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

    FIX_VANISH_DOOM = False # a final boss who can be made clear needs the fix whether the seed has it or not (bug_fixes/vanish_doom.py)
    LEVELS = 0              # levels above what final kefka's would be in the battle (battle/load_enemy_level.py)

    def __init__(self):
        from data.bosses import name_enemy
        self.enemy_id = name_enemy[self.ENEMY]
        self.free_palettes = list(FREE_PALETTES)
        self.free_monster_palettes = [766, 764, 762, 760]   # 4bpp monster palettes (two each): the game's end at 602

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

    def carried_jump_mod(self, position = (16, 16)):
        # for a final boss who is carried off by palidor (the esper has its caster's side jump: his,
        # with mirrorcast). palidor's animation leaves a monster where it carried it, off the
        # screen, and the landing brings a jumper back to where it started from: so when he lands
        # (where the jump command looks for the jumper's dragon horn, as jump_mod: one or the
        # other) he is first put back in his place, where the final formation has him
        # x = the jumper (8 and up are the enemies). 8 bit a, x and y
        JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END = 0x21820, 0x21822

        enemy_ids = 0x33a8
        first_enemy = 8
        monster_x, monster_y = 0x80c3, 0x80cf       # a word for each monster

        src = [
            asm.CPX(first_enemy, asm.IMM8),
            asm.BLT("JUMPER"),
            asm.A16(),
            asm.LDA(enemy_ids, asm.ABS_X),
            asm.CMP(self.enemy_id, asm.IMM16),
            asm.BNE("NOT_HIM"),
            asm.LDA(position[0], asm.IMM16),
            asm.STA(monster_x - first_enemy, asm.ABS_X),
            asm.LDA(position[1], asm.IMM16),
            asm.STA(monster_y - first_enemy, asm.ABS_X),
            "NOT_HIM",
            asm.A8(),
            "JUMPER",
            asm.RTL(),
        ]
        in_place = Write(Bank.F0, src, "final boss: back in his place to land")
        space = Write(Bank.C2, [
            asm.JSL(in_place.start_address_snes),
            Read(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END),
            asm.RTS(),
        ], "final boss: back in his place to land call")

        hook = Reserve(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END, "jump: load jumper's relic effects", asm.NOP())
        hook.write(
            asm.JSR(space.start_address, asm.ABS),
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

    def experience_damage_mod(self, data, attack, free_effect = 0x45):
        # (free_effect: a special effect that does nothing for each target, or for each strike: 0x45,
        # 0x46 and 0x47 are, and no attack that is used has them)
        # an attack does damage by its target (this is its special effect, in the place of any it had): the character's
        # experience divided by the attack's power, whatever the defenses, as step mine's is the
        # steps divided by its power (a level 45 character has 234808 experience, a level 60 one
        # 561528). against a monster it is as it was
        # called once for each target hit: y = the target. 8 bit a, x and y
        from data.ability_data import AbilityData
        EFFECT = 9                              # in the attack's data
        TARGET_EFFECTS = 0x23dcd                # what to call for each target, by special effect
        STRIKE_EFFECTS = 0x242e1
        NOTHING, NOTHING_FOR_STRIKE = 0x388c, 0x3e8a
        DIVIDE = 0x4792                         # a (16 bit) / x: a = the quotient, x = the remainder
        FIRST_ENEMY = 8

        damage_modifiers, damage, power = 0x3414, 0x11b0, 0x11a6
        character_data, experience = 0x3010, 0x1611     # the target's offset to its character's data
        high, low = 0xee, 0xf0

        effect = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE + EFFECT
        pointer = TARGET_EFFECTS + free_effect * 2
        assert Read(pointer, pointer + 1) == list(NOTHING.to_bytes(2, "little")), "the effect is in use"
        pointer_for_strike = STRIKE_EFFECTS + free_effect * 2
        assert Read(pointer_for_strike, pointer_for_strike + 1) == list(NOTHING_FOR_STRIKE.to_bytes(2, "little"))
        data.rom.set_bytes(effect, [free_effect])

        src = [
            asm.CPY(FIRST_ENEMY, asm.IMM8),
            asm.BGE("RETURN"),
            asm.STZ(damage_modifiers, asm.ABS),     # ignore damage modifiers
            asm.AXY16(),
            asm.LDX(character_data, asm.ABS_Y),
            asm.LDA(experience + 1, asm.ABS_X),     # its high 2 bytes
            asm.STA(high, asm.DIR),
            asm.A8(),
            asm.LDA(experience, asm.ABS_X),
            asm.STA(low, asm.DIR),
            asm.XY8(),

            # as step mine: 65535 if it is more than 2 bytes
            asm.A16(),
            asm.TDC(),
            asm.DEC(),
            asm.STA(damage, asm.ABS),
            asm.LDA(high, asm.DIR),
            asm.LDX(power, asm.ABS),
            asm.JSR(DIVIDE, asm.ABS),
            asm.A8(),
            asm.XBA(),
            asm.BNE("RETURN"),
            asm.TXA(),
            asm.XBA(),
            asm.STA(damage + 1, asm.ABS),
            asm.LDA(low, asm.DIR),
            asm.LDX(power, asm.ABS),
            asm.JSR(DIVIDE, asm.ABS),
            asm.STA(damage, asm.ABS),

            "RETURN",
            asm.AXY8(),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: damage by experience")
        Reserve(pointer, pointer + 1, "final boss: damage by experience pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

    def party_statuses_mod(self, data, attack, statuses_byte, statuses):
        # an attack (which has no special effect) also sets these statuses on every enemy in the
        # battle, each time it is used, whether it hits or not: statuses_byte is 0 to 3 (0x08 of byte
        # 2 is haste). enemies protected from them do not get them
        # once for each strike. 8 bit a, x and y
        from data.ability_data import AbilityData
        EFFECT = 9                              # in the attack's data
        NO_EFFECT = 0xff
        STRIKE_EFFECTS = 0x242e1                # what to call for each strike, by special effect
        TARGET_EFFECTS = 0x23dcd
        FREE_EFFECT = 0x45                      # does nothing for each strike, or for each target
        NOTHING, NOTHING_FOR_TARGET = 0x3e8a, 0x388c
        FIRST_ENEMY, ENTITIES_END = 8, 0x14

        enemy_bit, present_enemies = 0x3019, 0x3a75
        status_to_set = (0x3dd4, 0x3dd5, 0x3de8, 0x3de9)[statuses_byte]

        effect = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE + EFFECT
        assert data.rom.get_bytes(effect, 1)[0] == NO_EFFECT, "the attack has a special effect"
        pointer = STRIKE_EFFECTS + FREE_EFFECT * 2
        assert Read(pointer, pointer + 1) == list(NOTHING.to_bytes(2, "little")), "the effect is in use"
        pointer_for_target = TARGET_EFFECTS + FREE_EFFECT * 2
        assert Read(pointer_for_target, pointer_for_target + 1) == list(NOTHING_FOR_TARGET.to_bytes(2, "little"))
        data.rom.set_bytes(effect, [FREE_EFFECT])

        src = [
            asm.LDX(FIRST_ENEMY, asm.IMM8),
            "ENEMY",
            asm.LDA(enemy_bit, asm.ABS_X),
            asm.BIT(present_enemies, asm.ABS),
            asm.BEQ("NEXT"),
            asm.LDA(status_to_set, asm.ABS_X),
            asm.ORA(statuses, asm.IMM8),
            asm.STA(status_to_set, asm.ABS_X),
            "NEXT",
            asm.INX(),
            asm.INX(),
            asm.CPX(ENTITIES_END, asm.IMM8),
            asm.BLT("ENEMY"),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: statuses for the enemies")
        Reserve(pointer, pointer + 1, "final boss: statuses for the enemies pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

    def new_attack_mod(self, data, attack, source, name, animation_source = None):
        # an attack which nothing uses (no script, sketch, control, rage or lore) becomes a new one: another's data (returned,
        # to change), with this name, and the looks of animation_source (or of the source)
        from data.ability_data import AbilityData
        from data.spell_names import id_name
        ANIMATIONS, ANIMATION_SIZE = 0x107fb2, 14

        source_address = ABILITY_DATA_START + source * AbilityData.DATA_SIZE
        address = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE
        data.rom.set_bytes(address, data.rom.get_bytes(source_address, AbilityData.DATA_SIZE))
        self.rename_abilities(data, {id_name[attack] : name})

        if animation_source is None:
            animation_source = source
        animation = ANIMATIONS + animation_source * ANIMATION_SIZE
        data.rom.set_bytes(ANIMATIONS + attack * ANIMATION_SIZE, data.rom.get_bytes(animation, ANIMATION_SIZE))
        return address

    def damaged_condition_mod(self):
        # a script condition the game does not have: ai_instr.If(DAMAGED, 0, 0) is true when the
        # monster has lost more hp than it had the last time it was tested, for the script's answers
        # to being hit: put first in a block, where it is tested for every hit. (the game's "if
        # damaged", 0x05, is true for every hit once anyone has ever damaged the monster.)
        # in the place of condition 0x0a, which the game does not use (as chance_condition_mod is:
        # a final boss has one or the other). the hp he had lost at the last test are kept in the
        # battle's script variables 2 and 3, which final kefka's script does not use.
        # y = the monster. 8 bit a, x and y
        CONDITIONS = 0x21d55                # pointers
        UNUSED_CONDITION = 0x1d2c           # rts
        hp, max_hp, last_lost = 0x3bf4, 0x3c1c, 0x3eb2

        pointer = CONDITIONS + DAMAGED * 2
        assert Read(pointer, pointer + 1) == list(UNUSED_CONDITION.to_bytes(2, "little"))
        src = [
            asm.A16(),
            asm.LDA(max_hp, asm.ABS_Y),
            asm.SEC(),
            asm.SBC(hp, asm.ABS_Y),         # the hp he has lost
            asm.CMP(last_lost, asm.ABS),
            asm.STA(last_lost, asm.ABS),    # (keeps the flags of the comparison)
            asm.A8(),
            asm.BEQ("FALSE"),
            asm.BGE("TRUE"),
            "FALSE",
            asm.CLC(),
            asm.RTS(),
            "TRUE",
            asm.SEC(),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: damaged script condition")
        Reserve(pointer, pointer + 1, "damaged script condition pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

    def chance_condition_mod(self):
        # a script condition the game does not have: ai_instr.If(CHANCE, n, 0) is true n times in 256.
        # (conditions are tested as the script is read, before what it has queued is done)
        # in the place of condition 0x0a, which the game does not use. 8 bit a
        CONDITIONS = 0x21d55                # pointers
        UNUSED_CONDITION = 0x1d2c           # rts
        RANDOM = 0x4b5a                     # a = 0 to 255
        argument = 0x3a2e

        pointer = CONDITIONS + CHANCE * 2
        assert Read(pointer, pointer + 1) == list(UNUSED_CONDITION.to_bytes(2, "little"))
        src = [
            asm.JSR(RANDOM, asm.ABS),
            asm.CMP(argument, asm.ABS),
            asm.BLT("TRUE"),
            asm.CLC(),
            asm.RTS(),
            "TRUE",
            asm.SEC(),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: chance script condition")
        Reserve(pointer, pointer + 1, "chance script condition pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

    def helper_enemy_mod(self, enemies, source, name):
        # the helpers are an enemy of their own, made from this one (which stays as it is) in the
        # place of an enemy no formation has. as the final boss, they are protected from all statuses,
        # but for death
        import copy

        helper = enemies.enemies[HELPER_ENEMY]
        assert not helper.name
        for attribute, value in vars(enemies.enemies[source]).items():
            if attribute != "id":
                setattr(helper, attribute, copy.deepcopy(value))
        helper.name = name
        helper.status_immunities = copy.deepcopy(self.enemy(enemies).status_immunities)
        helper.status_immunities.death = 0
        return helper

    def add_monster_palette(self, palette):
        # a monster palette of these 16 colors (r, g, b), 0 to 31 each, and its number
        MONSTER_PALETTES, MONSTER_PALETTE_SIZE = 0x127820, 16   # 8 colors each: a 4bpp monster has two
        assert len(palette) == MONSTER_PALETTE_SIZE

        number = self.free_monster_palettes.pop(0)
        address = MONSTER_PALETTES + number * MONSTER_PALETTE_SIZE
        assert not any(Read(address, address + 2 * MONSTER_PALETTE_SIZE - 1))
        space = Reserve(address, address + 2 * MONSTER_PALETTE_SIZE - 1, "final boss: monster palette")
        space.write([(red | (green << 5) | (blue << 10)).to_bytes(2, "little") for red, green, blue in palette])
        return number

    def helper_palette_mod(self, source, palette):
        # the helpers look like this enemy with this palette: its 16 colors (r, g, b), 0 to 31 each
        spec = Read(self._spec_address(source), self._spec_address(source) + GRAPHICS_SPEC_SIZE - 1)
        assert not spec[1] & 0x80, "3bpp graphics"

        number = self.add_monster_palette(palette)
        spec[2] = (spec[2] & 0xfc) | (number >> 8)
        spec[3] = number & 0xff
        address = self._spec_address(HELPER_ENEMY)
        Reserve(address, address + GRAPHICS_SPEC_SIZE - 1, "final boss: helpers graphics spec").write(spec)

    def monster_palette(self, enemy):
        # the 16 colors (r, g, b) of a monster with 4bpp graphics
        MONSTER_PALETTES, MONSTER_PALETTE_SIZE = 0x127820, 16
        spec = Read(self._spec_address(enemy), self._spec_address(enemy) + GRAPHICS_SPEC_SIZE - 1)
        address = MONSTER_PALETTES + (((spec[2] & 0x03) << 8) | spec[3]) * MONSTER_PALETTE_SIZE
        data = Read(address, address + 2 * MONSTER_PALETTE_SIZE - 1)
        colors = [data[index] | (data[index + 1] << 8) for index in range(0, len(data), 2)]
        return [(color & 0x1f, (color >> 5) & 0x1f, (color >> 10) & 0x1f) for color in colors]

    def helpers_mod(self, enemies, helper, positions, boss_position):
        # the final boss has helpers: enemies of this kind which are in his formation but not in the
        # battle until his script brings them in (ai_instr.ChangeEnemies(animation, 0, HELPERS)).
        # positions are theirs on the screen and boss_position his, (x, y) in steps of 8 pixels.
        # helpers_layout_mod (battle_mod) makes the room for their graphics
        FINAL_FORMATION = 0x202             # the last tier of the final battle, he is its first enemy
        MOLD_SHIFT = 4

        formation = enemies.formations.formations[FINAL_FORMATION]
        assert formation.enemy_ids[0] == self.enemy_id
        formation.mold = (HELPERS_MOLD << MOLD_SHIFT) | (formation.mold & 0x0f)
        formation.enemy_x_positions[0], formation.enemy_y_positions[0] = boss_position
        for slot, (x, y) in enumerate(positions, start = 1):
            formation.enemy_ids[slot] = helper
            formation.enemy_x_positions[slot], formation.enemy_y_positions[slot] = x, y

    def helpers_layout_mod(self, boss_tiles, helper_tiles, helpers = 2):
        # (after giant_sprite_mod: the boss has no sprites where his sprite is empty)
        # a formation's monsters share 16x16 tiles of graphics (128x128 pixels), which its mold divides
        # between them: each has a rectangle of the 16x16 (where it is, (row * 16 + column) * 0x20,
        # and its width and height in tiles). the final formation's mold gives its one monster all
        # of it. this adds a mold: the final boss has the top (width, height) and the helpers are in
        # a row under him, (width, height) each
        #
        # the molds' pointers have no room for one more, so they are moved. the same for the lists of
        # the 32x32 pixel sprites each monster of a mold is drawn with when it is one (16 of them
        # cover the 16x16 tiles): the final boss and his helpers do not divide the tiles in steps of
        # 32 pixels, so as sprites they would show some of each other
        MOLDS, MOLD_COUNT = 0x2d01a, 13                 # pointers (bank c2), for each mold
        MOLDS_USERS = [0x120d1, 0x1254a]                # lda $c2d01a,x
        SPRITES, SPRITES_SIZE = 0x2c4a4, 12             # 6 pointers (bank c2) for each mold
        SPRITES_USERS = [(0x13e98, 0), (0x13e9e, 1)]    # lda $c2c4a4,x and lda $c2c4a5,x
        MONSTERS = 6
        TILES, TILE_SIZE, SPRITE_TILES = 16, 0x20, 4
        assert HELPERS_MOLD == MOLD_COUNT

        boss_width, boss_height = boss_tiles
        helper_width, helper_height = helper_tiles
        assert boss_width <= TILES and boss_height + helper_height <= TILES and helpers * helper_width <= TILES

        rectangles = [(0, 0, boss_width, boss_height)]
        rectangles += [(boss_height, index * helper_width, helper_width, helper_height) for index in range(helpers)]
        rectangles += [(0, 0, 0, 0)] * (MONSTERS - len(rectangles))

        mold = []
        for row, column, width, height in rectangles:
            mold += list(((row * TILES + column) * TILE_SIZE).to_bytes(2, "little")) + [width, height]

        # bank c2 has little room: the molds and their pointers all go to another bank, and the code
        # which reads them is told the bank
        MOLDS_DATA_START, MOLDS_DATA_END = 0x2d034, 0x2d0f3
        MOLDS_BANK_USERS = [0x120c6, 0x12540]           # lda #$c2
        SPRITES_DATA_START, SPRITES_DATA_END = 0x2c540, 0x2c688
        SPRITES_BANK_USERS = [0x13ea3]                  # lda #$c2

        def moved(pointers, old_start, new_start):
            # pointers (words) into a block of data, for the block where it is now
            words = [int.from_bytes(pointers[index : index + 2], "little") for index in range(0, len(pointers), 2)]
            words = [word - (old_start & 0xffff) + (new_start & 0xffff) for word in words]
            return [byte for word in words for byte in word.to_bytes(2, "little")]

        def set_bank(users, space):
            for user in users:
                assert Read(user, user + 1) == [0xa9, 0xc2]
                Reserve(user + 1, user + 1, "bank").write([space.start_address_snes >> 16])

        molds = Read(MOLDS_DATA_START, MOLDS_DATA_END)
        molds_space = Write(Bank.F0, molds + mold, "final boss: molds")
        set_bank(MOLDS_BANK_USERS, molds_space)

        pointers = moved(Read(MOLDS, MOLDS + MOLD_COUNT * 2 - 1), MOLDS_DATA_START, molds_space.start_address)
        pointers += list(((molds_space.start_address + len(molds)) & 0xffff).to_bytes(2, "little"))
        pointers_space = Write(Bank.F0, pointers, "final boss: mold pointers")
        for user in MOLDS_USERS:
            assert Read(user, user + 3) == [0xbf] + list((MOLDS + 0xc00000).to_bytes(3, "little"))
            Reserve(user + 1, user + 3, "mold pointers address").write(
                list(pointers_space.start_address_snes.to_bytes(3, "little")))

        # each monster's sprites: where its first is (x, y in pixels), then which sprites, the lists
        # one after the other. a sprite is x, y, its first tile (row * 16 + column) and 1. the first
        # tile of a monster's first sprite is also where its tiles start when it is drawn on the
        # background. in the final battle the monsters are sprites: 32x32 pixels, which do not divide
        # these rectangles, so what is left at the right and bottom of each is 16x16 sprites
        # (_small_sprites_mod). the game's 16 sprites are moved, with these after them
        PIECES, PIECE_COUNT, PIECE_SIZE = 0x2b9e7, 16, 4
        PIECES_USERS = [0x13ec7, 0x13ed1, 0x13edb, 0x13ee2]     # lda $c2b9e7,x and the 3 bytes after it
        MONSTER_SPRITES = 16
        SMALL_TILES = 2

        pieces = Read(PIECES, PIECES + PIECE_COUNT * PIECE_SIZE - 1)
        lists, small = [], []
        for row, column, width, height in rectangles:
            assert width % SMALL_TILES == 0 and height % SMALL_TILES == 0
            large_width, large_height = width - width % SPRITE_TILES, height - height % SPRITE_TILES
            sprites, sizes = [], []
            for sprite_row in range(0, height, SMALL_TILES):
                for sprite_column in range(0, width, SMALL_TILES):
                    large = sprite_row < large_height and sprite_column < large_width
                    if large and (sprite_row % SPRITE_TILES or sprite_column % SPRITE_TILES):
                        continue
                    size = SPRITE_TILES if large else SMALL_TILES
                    if (row, column) == (0, 0) and sprites and not self._any_pixels(sprite_row, sprite_column, size):
                        continue                # the boss: nothing of him is here
                    tile = (row + sprite_row) * TILES + column + sprite_column
                    sprites.append(len(pieces) // PIECE_SIZE)
                    sizes.append(0 if large else 1)
                    pieces += [sprite_column * 8, sprite_row * 8, tile, 0x01]
            assert len(sprites) <= MONSTER_SPRITES
            lists += [0, 0] + sprites + [0xff]
            small += sizes + [0] * (MONSTER_SPRITES - len(sizes))
        assert len(pieces) // PIECE_SIZE <= 0x80
        all_lists = Read(SPRITES_DATA_START, SPRITES_DATA_END)
        lists_space = Write(Bank.F0, all_lists + lists, "final boss: mold sprite lists")
        set_bank(SPRITES_BANK_USERS, lists_space)
        sprite_pointers = list(((lists_space.start_address + len(all_lists)) & 0xffff).to_bytes(2, "little")) * MONSTERS
        self._small_sprites_mod(small)
        self._helpers_death_mod(boss_height)

        pieces_space = Write(Bank.F0, pieces, "final boss: monster sprites")
        for offset, user in enumerate(PIECES_USERS):
            assert Read(user - 1, user + 2) == [0xbf] + list((PIECES + offset + 0xc00000).to_bytes(3, "little"))
            Reserve(user, user + 2, "monster sprites address").write(
                list((pieces_space.start_address_snes + offset).to_bytes(3, "little")))

        table = moved(Read(SPRITES, SPRITES + MOLD_COUNT * SPRITES_SIZE - 1), SPRITES_DATA_START, lists_space.start_address)
        table += sprite_pointers
        table_space = Write(Bank.F0, table, "final boss: mold sprites")
        for user, offset in SPRITES_USERS:
            assert Read(user - 1, user + 2) == [0xbf] + list((SPRITES + offset + 0xc00000).to_bytes(3, "little"))
            Reserve(user, user + 2, "mold sprites address").write(
                list((table_space.start_address_snes + offset).to_bytes(3, "little")))

    def _helpers_death_mod(self, boss_height):
        # when the final boss dies he crumbles as he sinks. the animation (C2/A96B) crumbles the
        # formation's 16x16 tiles of graphics, which the monsters' sprites show, a row of tiles at a
        # time from the last row up, each row 4 steps after the one under it; what crumbles off is
        # sand on a background layer, which falls. it is made for final kefka, whose picture fills
        # the 16x16 tiles and who is at (16, 16):
        #
        # - the sand's layer is put at (16, 16). a boss anywhere else has his sand somewhere else
        #   (above him, when he is lower). with the helpers' mold it is put where the boss is
        # - the rows crumble from the 16th up. with the helpers' mold the last rows are the helpers'
        #   and the boss is in the first ones: he would sink whole while the rows under his
        #   crumbled. the helpers' rows do not wait, and the count starts at the boss's last row
        #
        # where the animation sets each row's wait (0 for the last row, 4 for the one above it...),
        # after it has placed the layer. 8 bit a, 16 bit x and y, data bank $7e
        WAITS_START, WAITS_END = 0x2aa23, 0x2aa33       # tdc, tax, the loop
        TILES, STEP = 16, 4

        mold = 0x2000
        waits, progress = 0xecbc, 0xeccc
        boss_x, boss_y = 0x80c3, 0x80cf
        layer_x, layer_y = (0x64b4, 0x7b16), (0x64b6, 0x7b18)   # the layer's scroll, and a copy of it

        assert Read(WAITS_START, WAITS_START + 4) == [0x7b, 0xaa, 0x9d, waits & 0xff, waits >> 8]
        src = [
            asm.PHY(),
            asm.LDY(0x0000, asm.IMM16),
            asm.LDA(mold, asm.ABS),
            asm.CMP(HELPERS_MOLD, asm.IMM8),
            asm.BNE("START"),
            asm.LDY(TILES - boss_height, asm.IMM16),    # the rows under the boss
        ]
        for coordinate, layer in ((boss_x, layer_x), (boss_y, layer_y)):
            src += [
                asm.A16(),
                asm.LDA(coordinate, asm.ABS),
                asm.AND(0x00ff, asm.IMM16),
                asm.EOR(0xffff, asm.IMM16),
                asm.INC(),
                asm.STA(layer[0], asm.ABS),
                asm.STA(layer[1], asm.ABS),
                asm.A8(),
            ]
        src += [
            "START",
            asm.TDC(),
            asm.TAX(),
            "ROW",
            asm.STA(waits, asm.ABS_X),
            asm.STZ(progress, asm.ABS_X),
            asm.CPY(0x0000, asm.IMM16),
            asm.BEQ("WAIT"),
            asm.DEY(),
            asm.BRA("NEXT"),
            "WAIT",
            asm.CLC(),
            asm.ADC(STEP, asm.IMM8),
            "NEXT",
            asm.INX(),
            asm.CPX(TILES, asm.IMM16),
            asm.BNE("ROW"),
            asm.PLY(),
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "final boss: death with helpers")
        Reserve(WAITS_START, WAITS_END, "final boss death: rows' waits", asm.NOP()).write(
            asm.JSL(space.start_address_snes),
        )

    def _any_pixels(self, row, column, size):
        # whether the giant sprite has anything in the size x size tiles from this row and column
        pixels = self.giant_sprite_pixels
        return any(any(pixels_row[column * 8 : (column + size) * 8]) for pixels_row in pixels[row * 8 : (row + size) * 8])

    def _small_sprites_mod(self, small):
        # where a monster's sprite is given its size bit (and the high bit of its x), in the two
        # branches of the code which writes the monsters' sprites: with the helpers' mold, the
        # sprites flagged in small (16 flags for each monster of the formation) are 16x16
        # 8 bit a, 16 bit x (the sprite * 4) and y, data bank $7e
        NO_HIGH_X_START, NO_HIGH_X_END = 0x139ac, 0x139bf
        HIGH_X_START, HIGH_X_END = 0x139c0, 0x139d0
        CONTINUE = 0x39d1

        mold, monster, monster_sprites, sprites_left = 0x2000, 0x88d2, 0x88b9, 0x2c
        high_table, large_bits, large_high_x_bits = 0xa17f, 0xa37f, 0xa57f
        high_oam, temp = 0x0500, 0x44

        small_space = Write(Bank.F0, small, "final boss: small sprites")
        src = [
            asm.PHA(),                              # whether x is 256 or more
            asm.LDA(mold, asm.ABS),
            asm.CMP(HELPERS_MOLD, asm.IMM8),
            asm.BNE("LARGE"),
            asm.PHX(),
            asm.TDC(),
            asm.LDA(monster, asm.ABS),
            asm.ASL(), asm.ASL(), asm.ASL(), asm.ASL(),
            asm.STA(temp, asm.DIR),
            asm.LDA(monster, asm.ABS),
            asm.TAX(),
            asm.LDA(monster_sprites, asm.ABS_X),
            asm.SEC(),
            asm.SBC(sprites_left, asm.DIR),
            asm.CLC(),
            asm.ADC(temp, asm.DIR),
            asm.TAX(),                              # monster * 16 + which of its sprites
            asm.LDA(small_space.start_address_snes, asm.LNG_X),
            asm.PLX(),
            asm.CMP(0x00, asm.IMM8),
            asm.BEQ("LARGE"),

            asm.PLA(),
            asm.BEQ("SMALL_NO_HIGH_X"),
            asm.LDA(large_high_x_bits, asm.ABS_X),
            asm.EOR(large_bits, asm.ABS_X),
            asm.BRA("SET"),
            "SMALL_NO_HIGH_X",
            asm.LDA(0x00, asm.IMM8),
            asm.BRA("SET"),

            "LARGE",
            asm.PLA(),
            asm.BEQ("LARGE_NO_HIGH_X"),
            asm.LDA(large_high_x_bits, asm.ABS_X),
            asm.BRA("SET"),
            "LARGE_NO_HIGH_X",
            asm.LDA(large_bits, asm.ABS_X),

            "SET",
            asm.STY(temp, asm.DIR),
            asm.PHA(),
            asm.LDA(high_table, asm.ABS_X),
            asm.TAY(),
            asm.PLA(),
            asm.ORA(high_oam, asm.ABS_Y),
            asm.STA(high_oam, asm.ABS_Y),
            asm.LDY(temp, asm.DIR),
            asm.RTL(),
        ]
        space = Write(Bank.F0, src, "final boss: monster sprite size")
        set_size = space.start_address_snes

        space = Reserve(NO_HIGH_X_START, NO_HIGH_X_END, "monster sprite size, x below 256", asm.NOP())
        space.write(
            asm.LDA(0x00, asm.IMM8),
            asm.JSL(set_size),
            asm.JMP(CONTINUE, asm.ABS),
        )
        space = Reserve(HIGH_X_START, HIGH_X_END, "monster sprite size, x from 256", asm.NOP())
        space.write(
            asm.LDA(0x01, asm.IMM8),
            asm.JSL(set_size),
        )

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

    def golem_mod(self, golem_hp):
        # golem's wall for a final boss who calls it (with mirrorcast). the game's wall is the
        # party's whoever calls it: it has the hp of its caster, and it takes the blows of fight
        # on a character. called by a monster it is his: it has this many hp, and while it has
        # any a physical attack does him no damage and takes its damage from the wall
        #
        # the wall's hp are kept in the battle's script variables 2 and 3, which the scripts of the
        # final battle do not use
        GOLEM_START, GOLEM_END = 0x23f65, 0x23f6d       # y = the target. 8 bit a, x and y; returns with 16 bit a
        PHYSICAL_START, PHYSICAL_END = 0x20c2d, 0x20c30  # y = the target. 8 bit a, x and y
        FIRST_ENEMY = 8
        hp, party_golem_hp, his_golem_hp = 0x3bf4, 0x3a36, 0x3eb2
        attack_flags, damage, enemy_ids = 0x11a2, 0xf0, 0x33a8

        assert Read(GOLEM_START, GOLEM_END) == [0xc2, 0x20, 0xb9, 0xf4, 0x3b, 0x8d, 0x36, 0x3a, 0x60]
        golem = Write(Bank.F0, [
            asm.CPY(FIRST_ENEMY, asm.IMM8),
            asm.A16(),                              # (does not change the carry)
            asm.BGE("HIS"),
            asm.LDA(hp, asm.ABS_Y),
            asm.STA(party_golem_hp, asm.ABS),
            asm.RTL(),
            "HIS",
            asm.LDA(golem_hp, asm.IMM16),
            asm.STA(his_golem_hp, asm.ABS),
            asm.RTL(),
        ], "final boss: golem")
        space = Reserve(GOLEM_START, GOLEM_END, "golem", asm.NOP())
        space.write(
            asm.JSL(golem.start_address_snes),
            asm.RTS(),
        )

        # where the damage of an attack to a target is known, and a physical attack is told apart
        # (the carry on return)
        assert Read(PHYSICAL_START, PHYSICAL_END) == [0xad, 0xa2, 0x11, 0x4a]
        physical = Write(Bank.F0, [
            asm.LDA(attack_flags, asm.ABS),
            asm.LSR(),
            asm.BCC("RETURN"),                      # not physical
            asm.CPY(FIRST_ENEMY, asm.IMM8),
            asm.BLT("PHYSICAL"),
            asm.A16(),
            asm.LDA(enemy_ids, asm.ABS_Y),
            asm.CMP(self.enemy_id, asm.IMM16),
            asm.BNE("NO_WALL"),
            asm.LDA(his_golem_hp, asm.ABS),
            asm.BEQ("NO_WALL"),
            asm.SEC(),
            asm.SBC(damage, asm.DIR),
            asm.BGE("WALL"),
            asm.LDA(0x0000, asm.IMM16),
            "WALL",
            asm.STA(his_golem_hp, asm.ABS),
            asm.STZ(damage, asm.DIR),
            "NO_WALL",
            asm.A8(),
            "PHYSICAL",
            asm.SEC(),
            "RETURN",
            asm.RTL(),
        ], "final boss: golem takes the damage of physical attacks")
        space = Reserve(PHYSICAL_START, PHYSICAL_END, "physical attack damage")
        space.write(
            asm.JSL(physical.start_address_snes),
        )

    def mp_damage_mod(self, data, attack, free_effect = 0x47):
        # an attack (which has no special effect) also takes from its targets' mp what it takes from
        # their hp: where hp damage is dealt, the same is taken from mp for this attack, which is
        # known by a special effect that does nothing (free_effect: 0x45 to 0x47)
        # y = the target. 16 bit a
        from data.ability_data import AbilityData
        EFFECT = 9                              # in the attack's data
        NO_EFFECT = 0xff
        DEAL_HP_DAMAGE_START, DEAL_HP_DAMAGE_END = 0x21323, 0x21325
        HEALED_MINUS_DAMAGE = 0x13a7            # a = healing - damage (zero flag: none, carry: healing)
        attack_effect, mp, damage = 0x11a9, 0x3c08, 0xee    # (the effect * 2)

        effect = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE + EFFECT
        assert data.rom.get_bytes(effect, 1)[0] == NO_EFFECT, "the attack has a special effect"
        data.rom.set_bytes(effect, [free_effect])

        # (bank c2 has little room: all but the call of the game's own function is in bank f0)
        src = [
            asm.PHP(),
            asm.BEQ("RETURN"),
            asm.BGE("RETURN"),
            asm.PHA(),
            asm.EOR(0xffff, asm.IMM16),
            asm.INC(),
            asm.STA(damage, asm.DIR),
            asm.LDA(attack_effect, asm.ABS),
            asm.AND(0x00ff, asm.IMM16),
            asm.CMP(free_effect * 2, asm.IMM16),
            asm.BNE("NOT_THIS_ATTACK"),
            asm.LDA(mp, asm.ABS_Y),
            asm.SEC(),
            asm.SBC(damage, asm.DIR),
            asm.BGE("SET_MP"),
            asm.LDA(0x0000, asm.IMM16),
            "SET_MP",
            asm.STA(mp, asm.ABS_Y),
            "NOT_THIS_ATTACK",
            asm.PLA(),
            "RETURN",
            asm.PLP(),
            asm.RTL(),
        ]
        mp_damage = Write(Bank.F0, src, "final boss: mp damage with hp damage")
        space = Write(Bank.C2, [
            asm.JSR(HEALED_MINUS_DAMAGE, asm.ABS),
            asm.JSL(mp_damage.start_address_snes),
            asm.RTS(),
        ], "final boss: mp damage with hp damage call")

        hook = Reserve(DEAL_HP_DAMAGE_START, DEAL_HP_DAMAGE_END, "final boss: deal hp damage")
        hook.write(
            asm.JSR(space.start_address, asm.ABS),
        )

    def half_damage_mod(self, elements):
        # he takes half the damage of these elements. an enemy's data has the elements it is weak
        # to, absorbs and takes no damage from, and none for half: that is a character's, from
        # equipment (the high byte of $3be0). where a monster's weak elements are loaded, his get
        # these as well
        # 8 bit a, 16 bit x (the monster * 32) and y (the monster in the battle)
        LOAD_WEAK_START, LOAD_WEAK_END = 0x22dc9, 0x22dd2
        ENEMY_DATA_SIZE = 32
        weak_data, weak, half = 0xcf0019, 0x3be0, 0x3be1

        src = [
            asm.LDA(weak_data, asm.LNG_X),
            asm.ORA(weak, asm.ABS_Y),
            asm.STA(weak, asm.ABS_Y),
            asm.CPX(self.enemy_id * ENEMY_DATA_SIZE, asm.IMM16),
            asm.BNE("RETURN"),
            asm.LDA(elements, asm.IMM8),
            asm.ORA(half, asm.ABS_Y),
            asm.STA(half, asm.ABS_Y),
            "RETURN",
            asm.RTL(),
        ]
        load = Write(Bank.F0, src, "final boss: half damage elements")

        space = Reserve(LOAD_WEAK_START, LOAD_WEAK_END, "final boss: load weak elements", asm.NOP())
        space.write(
            asm.JSL(load.start_address_snes),
        )

    def random_status_mod(self, data, attack, statuses):
        # an attack with no special effect also sets one status on each target it hits: one of
        # these 8 (status byte 0 to 2, status), chosen for each target, and none if the target is
        # protected from the one chosen
        # called once for each target hit: y = the target. 8 bit a, x and y
        from data.ability_data import AbilityData
        EFFECT = 9                              # in the attack's data
        NO_EFFECT = 0xff
        TARGET_EFFECTS = 0x23dcd                # what to call for each target, by special effect
        FREE_EFFECT = 0x45                      # does nothing for each target, or for each strike
        NOTHING = 0x388c
        RANDOM = 0x4b65                         # 0 to a - 1
        vulnerable = 0x331c                     # statuses the target is not protected from (4 bytes)
        status_to_set = (0x3dd4, 0x3dd5, 0x3de8)

        assert len(statuses) == 8 and all(status_byte < len(status_to_set) for status_byte, _ in statuses)
        effect = ABILITY_DATA_START + attack * AbilityData.DATA_SIZE + EFFECT
        assert data.rom.get_bytes(effect, 1)[0] == NO_EFFECT, "the attack has a special effect"
        pointer = TARGET_EFFECTS + FREE_EFFECT * 2
        assert Read(pointer, pointer + 1) == list(NOTHING.to_bytes(2, "little")), "the effect is in use"
        data.rom.set_bytes(effect, [FREE_EFFECT])

        # (bank c2 has little room: the choice is made there, and the rest is in f0)
        table = Write(Bank.F0, [value for status in statuses for value in status], "final boss: random statuses")
        src = [
            asm.ASL(),
            asm.TAX(),
            asm.LDA(table.start_address_snes, asm.LNG_X),       # the status byte
            asm.BEQ("BYTE_0"),
            asm.DEC(),
            asm.BEQ("BYTE_1"),
        ]
        for status_byte in (2, 1, 0):
            src += [
                f"BYTE_{status_byte}",
                asm.LDA(table.start_address_snes + 1, asm.LNG_X),
                asm.AND(vulnerable + status_byte, asm.ABS_Y),
                asm.ORA(status_to_set[status_byte], asm.ABS_Y),
                asm.STA(status_to_set[status_byte], asm.ABS_Y),
                asm.RTL(),
            ]
        set_status = Write(Bank.F0, src, "final boss: random status")

        src = [
            asm.LDA(len(statuses), asm.IMM8),
            asm.JSR(RANDOM, asm.ABS),
            asm.JSL(set_status.start_address_snes),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "final boss: random status choice")
        Reserve(pointer, pointer + 1, "final boss: random status pointer").write(
            list((space.start_address & 0xffff).to_bytes(2, "little")))

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

    def attack_special_animation_mod(self, attack, enemy):
        # the other way around: an attack of his looks and sounds like the special attack of this
        # enemy (the blow a monster's special is shown with, a byte for each enemy), and is otherwise
        # what it was: when the battle queues the attack's animation, it queues that of a special
        # x = the attacker (8 and up are the enemies). 8 bit a, x and y
        QUEUE_ANIMATION_START, QUEUE_ANIMATION_END = 0x23414, 0x23416
        QUEUE_ANIMATION = 0x35ad
        SPECIAL_ATTACK_GRAPHICS = 0xf37c0       # a byte for each enemy
        FIGHT_COMMAND, SPECIAL_ATTACK = 0x00, 0xef
        SPECIAL_FLAG = 0x01

        command, command_attack, graphic, flags = 0xb5, 0xb6, 0xb7, 0xa0
        enemy_ids = 0x33a8
        first_enemy = 8

        src = [
            asm.LDA(command_attack, asm.DIR),
            asm.CMP(attack, asm.IMM8),
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
            asm.LDA(graphic, asm.DIR),
            asm.PHA(),
            asm.LDA(flags, asm.DIR),
            asm.PHA(),
            asm.ORA(SPECIAL_FLAG, asm.IMM8),
            asm.STA(flags, asm.DIR),
            asm.LDA(FIGHT_COMMAND, asm.IMM8),
            asm.STA(command, asm.DIR),
            asm.LDA(SPECIAL_ATTACK, asm.IMM8),
            asm.STA(command_attack, asm.DIR),
            asm.LDA(Read(SPECIAL_ATTACK_GRAPHICS + enemy, SPECIAL_ATTACK_GRAPHICS + enemy)[0], asm.IMM8),
            asm.STA(graphic, asm.DIR),
            asm.JSR(QUEUE_ANIMATION, asm.ABS),
            asm.PLA(),
            asm.STA(flags, asm.DIR),
            asm.PLA(),
            asm.STA(graphic, asm.DIR),
            asm.PLA(),
            asm.STA(command_attack, asm.DIR),
            asm.PLA(),
            asm.STA(command, asm.DIR),
            asm.RTS(),

            "AS_IT_IS",
            asm.JMP(QUEUE_ANIMATION, asm.ABS),
        ]
        space = Write(Bank.C2, src, "final boss: attack with a special attack's animation")
        queue_animation = space.start_address

        space = Reserve(QUEUE_ANIMATION_START, QUEUE_ANIMATION_END, "queue attack animation", asm.NOP())
        space.write(
            asm.JSR(queue_animation, asm.ABS),
        )

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

    def goner_colors_mod(self, goner, streak_color, script_changes):
        # goner, which only final kefka has, in other colors than red: the palette of its streaks
        # (streak_color: a 15 bit color for each of its 8), and what its animation script does to
        # the colors of the background and of the monster (script_changes: (bytes, bytes in their
        # place) in hex, each found once in the script)
        #
        # the script's color commands (b6: the background, b9 and bc: the monsters) take a byte:
        # which of red (0x80), green (0x40) and blue (0x20), more (0x10) or less, and how much.
        # goner's: b6 61 (the background turns red), b6 31 (then purple), b6 81 (then blue),
        # b6 91 b6 21 (and red again), b9 60 and bc 61 (the monster turns red), b6 8f bc 8f (both
        # go dark)
        ATTACK_ANIMATIONS, ATTACK_ANIMATION_SIZE = 0x107fb2, 14
        SCRIPT_POINTERS, SCRIPTS = 0x11ead8, 0x100000
        BG1_LAYER, LAYER_PALETTES = 1, 6
        SCRIPT_SIZE = 258
        PALETTE_COLORS = PALETTE_SIZE // 2

        animation = ATTACK_ANIMATIONS + goner * ATTACK_ANIMATION_SIZE
        layer_animation = Read(animation + BG1_LAYER * 2, animation + BG1_LAYER * 2 + 1)
        layer_animation = layer_animation[0] | (layer_animation[1] << 8)

        palette = Read(animation + LAYER_PALETTES + BG1_LAYER, animation + LAYER_PALETTES + BG1_LAYER)[0]
        address = PALETTES + palette * PALETTE_SIZE
        data = Read(address, address + PALETTE_SIZE - 1)
        colors = [data[index * 2] | (data[index * 2 + 1] << 8) for index in range(PALETTE_COLORS)]
        space = Reserve(animation + LAYER_PALETTES + BG1_LAYER, animation + LAYER_PALETTES + BG1_LAYER, "goner palette")
        space.write(self.add_palette([streak_color(color) for color in colors]))

        pointer = Read(SCRIPT_POINTERS + layer_animation * 2, SCRIPT_POINTERS + layer_animation * 2 + 1)
        script_address = SCRIPTS + (pointer[0] | (pointer[1] << 8))
        script = bytes(Read(script_address, script_address + SCRIPT_SIZE - 1))
        for old, new in script_changes:
            old, new = bytes.fromhex(old), bytes.fromhex(new)
            assert script.count(old) == 1 and len(old) == len(new)
            script = script.replace(old, new)
        space = Reserve(script_address, script_address + SCRIPT_SIZE - 1, "goner animation script")
        space.write(list(script))

    def goner_sprite_mod(self, pixels, palette, move = (0, 0)):
        # (move: where the picture is, in steps of 16 pixels to the left and down from the head's place)
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

        if move != (0, 0):
            # the frame's tiles: where each goes (x, y: a nibble each), and which. the animation
            # is flipped for a monster, so more x is further left on the screen
            moved = list(HEAD_FRAME)
            for index in range(0, len(moved), 2):
                x, y = (moved[index] >> 4) + move[0], (moved[index] & 0x0f) + move[1]
                assert 0 <= x < 16 and 0 <= y < 16
                moved[index] = (x << 4) | y
            Reserve(FRAMES + frame_start, FRAMES + frame_end - 1, "final boss: goner sprite frame").write(moved)

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

    def enemy_sprite(self, enemy):
        # the pixels of a monster with 4bpp graphics (without the empty rest of its mold), and its
        # graphics spec
        spec = Read(self._spec_address(enemy), self._spec_address(enemy) + GRAPHICS_SPEC_SIZE - 1)
        pointer = spec[0] | (spec[1] << 8)
        assert not pointer & 0x8000, "3bpp graphics"

        large = spec[2] & 0x80
        tiles = monster_sprite.LARGE_MOLD_TILES if large else monster_sprite.SMALL_MOLD_TILES
        mold_address = (LARGE_MOLDS if large else SMALL_MOLDS) + spec[4] * monster_sprite.mold_size(tiles)
        mold = Read(mold_address, mold_address + monster_sprite.mold_size(tiles) - 1)

        graphics_address = GRAPHICS + pointer * 8
        graphics_size = monster_sprite.mold_tile_count(mold) * monster_sprite.TILE_SIZE_4BPP
        graphics = Read(graphics_address, graphics_address + graphics_size - 1)

        return monster_sprite.bounds(monster_sprite.sprite_pixels(mold, tiles, graphics)), spec

    def giant_sprite_mod(self, enemy, shadow_color = None, shadow_rows = 0, lower = 0, scale = None, palette = None, right = 0,
                         smooth = False, recolor = None, draw = None, pixels = None):
        # (pixels: a sprite drawn for him, rows of the enemy's palette indices, in the place of the enemy's)
        # (smooth: at 3x, with scale3x. recolor: {palette index : another} of the enemy's sprite.
        # draw: called with the sprite in its mold, 128 rows of 128 palette indices, to change it)
        # (right: pixels to the right in the mold, for a sprite that is not as wide)
        # (palette: 16 colors (r, g, b) in the place of the enemy's own)
        # the final boss looks like this enemy, giant and in its palette: at twice its size if that
        # fits the 128x128 pixels of a large mold (it does for a monster with a small mold), or else
        # as large as fits, or at this scale (factor, divisor). a shadow under its feet (its color,
        # and how many of the sprite's last rows it is in) is removed: the final boss is in the air
        #
        # the sprite is given to final kefka in kefka's own mold (no other monster uses it). it does not
        # fit where kefka's was and nothing is free in reach of the 15 bit pointer, so it is written
        # wherever there is room and kefka's pointer is a value no monster has, which the graphics
        # loader is taught to send there
        size = monster_sprite.LARGE_MOLD_TILES * monster_sprite.TILE_PIXELS
        own_pixels = pixels
        pixels, enemy_spec = self.enemy_sprite(enemy)
        if own_pixels is not None:
            pixels = monster_sprite.bounds(own_pixels)
        if shadow_rows:
            pixels = monster_sprite.without_shadow(pixels, shadow_color, shadow_rows)
        if scale is None:
            longest = max(len(pixels), len(pixels[0]))
            scale = (GIANT_SPRITE_SCALE, 1) if longest * GIANT_SPRITE_SCALE <= size else (size, longest)
        #
        # a sprite that is not as high as the mold can be this many pixels lower in it, to be clear of
        # the boxes at the top of the screen (it is at the top of the mold otherwise, as all monsters'
        # are). the battle takes a monster's height to be its mold's rows before the first empty one,
        # and hangs on a mold with an empty first row: the rows above the sprite get an empty tile
        if recolor:
            pixels = [[recolor.get(pixel, pixel) for pixel in row] for row in pixels]
        if smooth:
            assert tuple(scale) == (3, 1)
            pixels = monster_sprite.canvas(monster_sprite.scale3x(pixels), size)
        else:
            pixels = monster_sprite.canvas(monster_sprite.scale(pixels, *scale), size)
        if lower:
            assert not any(any(row) for row in pixels[-lower:]), "the sprite is too high to be lower"
            pixels = [[0] * len(pixels[0]) for _ in range(lower)] + pixels[:-lower]
        if right:
            assert not any(any(row[-right:]) for row in pixels), "the sprite is too wide to be further right"
            pixels = [[0] * right + row[:-right] for row in pixels]
        if draw:
            draw(pixels)
        self.giant_sprite_pixels = pixels
        mold, graphics = monster_sprite.sprite_data(pixels, no_empty_rows = True)
        assert len(mold) == monster_sprite.mold_size(monster_sprite.LARGE_MOLD_TILES)

        space = Write(Bank.F0, graphics, "final boss graphics")
        self._graphics_loader_mod(space.start_address_snes)

        palette_spec = [enemy_spec[2], enemy_spec[3]]
        if palette is not None:
            number = self.add_monster_palette(palette)
            palette_spec = [(enemy_spec[2] & 0xfc) | (number >> 8), number & 0xff]

        kefka_spec_address = self._spec_address(self.enemy_id)
        kefka_mold = Read(kefka_spec_address + 4, kefka_spec_address + 4)[0]

        space = Reserve(kefka_spec_address, kefka_spec_address + GRAPHICS_SPEC_SIZE - 1, "final kefka graphics spec")
        space.write(
            GIANT_SPRITE_POINTER & 0xff, GIANT_SPRITE_POINTER >> 8,
            0x80 | (palette_spec[0] & 0x7f),    # large mold, the enemy's palette
            palette_spec[1],
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
