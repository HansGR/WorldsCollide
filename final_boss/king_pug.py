import graphics.lantern_glow as lantern_glow
import graphics.crown as crown

from final_boss.final_boss import FinalBoss

class KingPug(FinalBoss):
    # pug (the green one), giant and crowned: big, slow, and he hits hard. final kefka's script with
    # the spell for his weakness as master pug casts it, stop, a lullaby (sleep on the whole party)
    # and life mine: step mine by the target's experience. hit with an element, he answers with
    # wallchange
    NAME = "King Pug"
    SPEED, VIGOR = 0.8, 1.2                 # of final kefka's
    HP = 2 ** 16 - 1                        # the most an enemy can have

    PUG = "Pug"
    SCALE = (3, 1)                          # pug is 32x32 pixels: 96x96
    # where he is in his mold, in pixels: lower, to be clear of the boxes at the top, and such that
    # the glass of his lantern (the middle of it is at 85.5, 75 of his sprite) is under the glow
    LOWER, RIGHT = 27, 12
    GLOW_MOVE = (2, 1)                      # the glow: 32 pixels left and 16 down from the laughing head's place

    # his crown (graphics/crown.py). in pug's palette 13 is a dark green and 14 a khaki, 8 or 9 pixels
    # each of his sprite: those are 7 and 8 in it, and the two are the crown's gold
    RECOLOR = {13 : 7, 14 : 8}
    CROWN_PALETTE = {13 : (20, 13, 2), 14 : (31, 25, 5)}       # (r, g, b), 0 to 31: gold in shade, gold
    CROWN_COLORS = {"o" : 1, "g" : 14, "h" : 15, "d" : 13, "r" : 3}     # outline, gold, lit, shade, jewel
    CROWN_PLACE = (49, -6)                  # its left and top by his sprite's: on his head (it is 26x15)

    SPECIAL_NAME = "Cleaver"                # was havoc wing
    ABILITY_NAMES = {
        "Goner"         : "Grudge Ray",
        "Revenger"      : "Lullaby",
    }
    GONER_TEXT = "......<wait 60 frames><end>"
    LULLABY_HIT_RATE = 90                   # the sleep spell's is 111
    LIFE_MINE = "Confusion"                 # an attack no script, sketch, control or rage uses
    LIFE_MINE_DIVISOR = 64
    LIFE_MINE_EFFECT = 0x46                 # a special effect nothing has (grudge ray's stop is 0x45)
    STOP_BYTE, STOP = 2, 0x10               # the third status byte
    GRUDGE_RAY_STOP_HIT_RATE = 65           # gumbo's muddle has that

    # master pug's spells for his weakness: fire, ice, bolt, poison, wind, pearl, earth, water
    WEAKNESS_SPELLS = ["Ice 3", "Fire 3", "W Wind", "Pearl", "Bolt 3", "Bio", "CleanSweep", "Quake"]
    NO_WEAKNESS_ATTACK = "Battle"           # before his first wallchange

    WATER, ANY_ELEMENT = 0x80, 0xff         # elements
    SELF, ALL_CHARACTERS = 0x36, 0x43       # targets
    POWER_BYTE = 6                          # in an attack's data

    def crown_mod(self, pixels):
        # the crown on his head: over his sprite as it is in the mold
        left, top = self.RIGHT + self.CROWN_PLACE[0], self.LOWER + self.CROWN_PLACE[1]
        for y, row in enumerate(crown.pixels(self.CROWN_COLORS)):
            for x, color in enumerate(row):
                if color is not None:
                    assert top + y >= 0
                    pixels[top + y][left + x] = color

    def enemies_mod(self, enemies):
        self.pug = enemies.get_enemy(self.PUG)
        king_pug = self.enemy(enemies)
        king_pug.name = self.NAME
        king_pug.special_name = self.SPECIAL_NAME
        king_pug.speed = round(king_pug.speed * self.SPEED)
        king_pug.vigor = min(round(king_pug.vigor * self.VIGOR), 2 ** 8 - 1)
        king_pug.hp = self.HP
        king_pug.absorb_elements |= self.WATER          # as the pugs do

    def scripts_mod(self, scripts):
        # (his battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id
        from data.enemy_script_custom_commands import WEAKNESS

        scripts.enemy_script_custom_commands.command_attacks_mod(
            {}, [name_id[spell] for spell in self.WEAKNESS_SPELLS], name_id[self.NO_WEAKNESS_ATTACK])

        special, train, revenger, nothing = (name_id[name] for name in ["Special", "Train", "Revenger", "Nothing"])
        life_mine = name_id[self.LIFE_MINE]
        script = scripts.get_script(self.ENEMY)

        # above 53% hp, after fallen one
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special),
                       ai_instr.RandomAttack(WEAKNESS, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Ice 3"], train, special),
                       ai_instr.RandomAttack(life_mine, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(name_id["Stop"], nothing, special))

        # at 53% hp and below, the turns after goner (grudge; revenger is the lullaby)
        script.replace(ai_instr.RandomAttack(special, train, revenger),
                       ai_instr.RandomAttack(special, life_mine, revenger))

        # hit below 49% hp: life mine for hyperdrive (master pug answers with step mine)
        script.replace(ai_instr.RandomAttack(nothing, name_id["Battle"], name_id["HyperDrive"]),
                       ai_instr.RandomAttack(nothing, name_id["Battle"], life_mine))

        # hit by an attack with an element: wallchange, on himself (before what else he does when
        # he is hit, after what he does when he dies)
        instructions = script.instructions
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        script.insert(counters + 1, [
            ai_instr.If(0x04, self.ANY_ELEMENT, 0x00),
            ai_instr.SetTarget(self.SELF),
            ai_instr.Spell(name_id["WallChange"]),
            ai_instr.EndIf(),
        ])

    def data_mod(self, data):
        from data.spell_names import name_id

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.goner_text_mod(data, self.GONER_TEXT)

        # the lullaby: sleep on the whole party
        self.party_status_attack_mod(data, "Sleep", self.LULLABY_HIT_RATE)

        # life mine: step mine, by the target's experience
        life_mine = self.new_attack_mod(data, name_id[self.LIFE_MINE], name_id["Step Mine"], "Life Mine")
        data.rom.set_bytes(life_mine + self.POWER_BYTE, [self.LIFE_MINE_DIVISOR])
        self.experience_damage_mod(data, name_id[self.LIFE_MINE], self.LIFE_MINE_EFFECT)

        # grudge ray may stop each one it hits, as uncle ulty's gumbo may muddle
        self.status_chance_mod(data, name_id["Goner"], self.STOP_BYTE, self.STOP, self.GRUDGE_RAY_STOP_HIT_RATE)

    def battle_mod(self):
        # his sprite at 3x with its edges smoothed, in pug's palette with two of its colors (which
        # are given to their nearest others in the sprite) for the gold of his crown
        palette = self.monster_palette(self.pug)
        for index, color in self.CROWN_PALETTE.items():
            palette[index] = color
        self.giant_sprite_mod(self.pug, scale = self.SCALE, lower = self.LOWER, right = self.RIGHT,
                              smooth = True, recolor = self.RECOLOR, palette = palette, draw = self.crown_mod)

        # his lantern lights up and shines before grudge ray: the glow is shown over it, and taken away
        self.goner_sprite_mod(lantern_glow.pixels(), lantern_glow.palette(), self.GLOW_MOVE)
