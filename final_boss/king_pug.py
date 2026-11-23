import graphics.lantern_glow as lantern_glow
import graphics.king_pug as king_pug_sprite

from final_boss.final_boss import FinalBoss, DAMAGED

class KingPug(FinalBoss):
    # pug (the green one), giant and crowned: big, slow, and he hits hard. final kefka's script with
    # the spell for his weakness as master pug casts it, stop, a lullaby (sleep on the whole party)
    # and life mine: step mine by the target's experience. damaged by an attack with an element, he answers
    # with wallchange
    NAME = "King Pug"
    SPEED, VIGOR = 0.8, 1.2                 # of final kefka's
    HP = 2 ** 16 - 1                        # the most an enemy can have

    PUG = "Pug"

    # his sprite (graphics/king_pug.py: pug's at 1.5x with a crown drawn at that size, 48x49 pixels)
    # at 2x: 96x98. where he is in his mold, in pixels: lower, to be clear of the boxes at the top,
    # and such that the glass of his lantern (the middle of it is at 86, 78 of his sprite at 2x) is
    # under the glow's (which is 4 pixels below the middle of its picture)
    SCALE = (2, 1)
    LOWER, RIGHT = 28, 11
    GLOW_MOVE = (2, 1)                      # the glow: 32 pixels left and 16 down from the laughing head's place

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

        # damaged by an attack with an element: wallchange, on himself (before what else he does
        # when he is hit, after what he does when he dies)
        instructions = script.instructions
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        script.insert(counters + 1, [
            ai_instr.If(DAMAGED, 0x00, 0x00),           # the hit damaged him (tested for every hit)
            ai_instr.If(0x04, self.ANY_ELEMENT, 0x00),  # and it had an element
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
        # in pug's palette, with two of its colors for the gold of his crown
        palette = self.monster_palette(self.pug)
        for index, color in king_pug_sprite.GOLD.items():
            palette[index] = color
        self.giant_sprite_mod(self.pug, pixels = king_pug_sprite.pixels(), palette = palette,
                              scale = self.SCALE, lower = self.LOWER, right = self.RIGHT)

        self.damaged_condition_mod()
        self.grudge_ray_mod()

        # his lantern lights up and shines before grudge ray: the glow is shown over it, and taken away
        self.goner_sprite_mod(lantern_glow.pixels(), lantern_glow.palette(), self.GLOW_MOVE)

    def grudge_ray_mod(self):
        # grudge ray is goner in green and gold for red: gold streaks, and the background and the
        # monster turn green, then gold, then green again
        from data.spell_names import name_id
        def gold(color):
            red, green, blue = color & 0x1f, (color >> 5) & 0x1f, (color >> 10) & 0x1f
            return red | (max(green, round(red * 0.8)) << 5) | (blue << 10)
        self.goner_colors_mod(name_id["Goner"], gold, (
            ("b6 61", "b6 a1"),             # the background turns red: green (less red and blue)
            ("b6 31", "b6 91"),             # then to purple: gold (more red)
            ("b6 81", "b6 81"),             # then to blue: green again (less red)
            ("b6 91 b6 21", "b6 a1 b6 a1"), # and back to red: stays green
            ("b9 60", "b9 a0"),             # the monster turns red: green
            ("bc 61", "bc a1"),
            ("b6 8f bc 8f", "b6 4f bc 4f"), # both go dark (less green)
        ))
