from final_boss.final_boss import FinalBoss, HELPERS, HELPER_ENEMY

class Grampaluma(FinalBoss):
    # dadaluma, giant, who calls in two chromefists as dadaluma does his iron fists: iron fists in
    # chrome, with 14000 hp, who throw a dirk every turn. (a prototype: his stats, attacks and the
    # rest of his script are final kefka's)
    NAME = "Grampaluma"

    DADALUMA = "Dadaluma"
    HELPER = "Iron Fist"
    HELPER_NAME = "ChromeFist"
    HELPER_HP = 14000
    HELPER_LEVEL = 40
    THROW, DIRK = 0x01, 0x00

    # dadaluma is 88x56 pixels. the monsters of the formation share 16x16 tiles of graphics: he has
    # the top 16x10 (125x80 pixels: 1.43 times his size), and the iron fists 6x6 each under him
    TILES = (16, 10)
    HELPER_TILES = (6, 6)

    # on the screen, (x, y) in steps of 8 pixels: he is clear of the boxes at the top
    POSITION = (0, 7)
    HELPER_POSITIONS = [(15, 5), (15, 12)]

    CALL_TIME = 30                          # he calls them when they are gone and his timer is above this
    CALL_ANIMATION = 3

    def enemies_mod(self, enemies):
        self.enemy(enemies).name = self.NAME
        self.iron_fist_id = enemies.get_enemy(self.HELPER)
        helper = self.helper_enemy_mod(enemies, self.iron_fist_id, self.HELPER_NAME)
        helper.hp = self.HELPER_HP
        helper.level = self.HELPER_LEVEL
        self.helpers_mod(enemies, HELPER_ENEMY, self.HELPER_POSITIONS, self.POSITION)

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr

        # the chromefists throw a dirk every turn
        scripts.scripts[HELPER_ENEMY].instructions = [
            ai_instr.RandomItem(self.THROW, self.DIRK, self.DIRK),
            ai_instr.EndMainLoop(),
            ai_instr.EndScript(),
        ]

        script = scripts.get_script(self.ENEMY)
        intro_end = script.instructions.index(ai_instr.EndIf())
        script.insert(intro_end + 1, [
            ai_instr.If(0x0b, self.CALL_TIME, 0x00),    # if his timer is above this
            ai_instr.Misc(0x00, 0x00),                  # reset his timer
            ai_instr.If(0x12, HELPERS, 0x00),           # if the helpers are dead or not in the battle
            ai_instr.ChangeEnemies(self.CALL_ANIMATION, 0x00, HELPERS),     # bring them in
            ai_instr.EndIf(),
        ])

    @staticmethod
    def chrome(palette):
        # a palette in chrome: its colors (but the first, which is not seen) by their brightness,
        # from near black to white and brighter in between, as greys with a little blue
        DARKEST, BRIGHTEST, GAMMA = 2, 31, 0.6
        TINT = (0.93, 0.97, 1.0)

        def brightness(color):
            red, green, blue = color
            return 0.30 * red + 0.59 * green + 0.11 * blue
        low = min(brightness(color) for color in palette[1:])
        high = max(brightness(color) for color in palette[1:])

        colors = []
        for color in palette:
            level = min(max((brightness(color) - low) / (high - low), 0), 1) ** GAMMA
            grey = DARKEST + (BRIGHTEST - DARKEST) * level
            colors.append(tuple(min(max(round(grey * tint), 0), 31) for tint in TINT))
        return colors

    def battle_mod(self):
        from data.bosses import name_enemy

        width, height = self.TILES
        dadaluma = name_enemy[self.DADALUMA]
        sprite, _ = self.enemy_sprite(dadaluma)
        self.giant_sprite_mod(dadaluma, scale = (height * 8, len(sprite)))
        iron_fist = self.iron_fist_id
        self.helper_palette_mod(iron_fist, self.chrome(self.monster_palette(iron_fist)))
        self.helpers_layout_mod(self.TILES, self.HELPER_TILES, len(self.HELPER_POSITIONS))
