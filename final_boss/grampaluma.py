from final_boss.final_boss import FinalBoss, HELPERS, HELPER_ENEMY, CHANCE

class Grampaluma(FinalBoss):
    # dadaluma, giant, with what dadaluma does in zozo added to final kefka's script (a prototype:
    # his stats and attacks are final kefka's)
    #
    #   he calls in two chromefists when his timer is above 30 and both are dead or gone, as
    #   dadaluma does his iron fists. they are not in the battle at its start
    #   once, below 25% hp: x-potion, x-potion or potion three times, and safe
    #   once, when he has been hit by fight four times: he throws a wing edge
    #
    # a chromefist is an iron fist in chrome with 14000 hp: each turn it throws a dirk or attacks
    # twice, one as likely as the other
    NAME = "Grampaluma"

    DADALUMA = "Dadaluma"
    HELPER = "Iron Fist"
    HELPER_NAME = "ChromeFist"
    HELPER_HP = 14000
    HELPER_LEVEL = 40

    # dadaluma is 88x56 pixels. the monsters of the formation share 16x16 tiles of graphics: he has
    # the top 16x10 (125x80 pixels: 1.43 times his size), and the chromefists 6x6 each under him
    TILES = (16, 10)
    HELPER_TILES = (6, 6)

    # on the screen, (x, y) in steps of 8 pixels: he is clear of the boxes at the top
    POSITION = (0, 7)
    HELPER_POSITIONS = [(15, 5), (15, 12)]

    CALL_TIME = 30                          # he calls them when they are gone and his timer is above this
    CALL_ANIMATION = 3
    HEAL_HP = 25                            # percent (data/enemy_script_custom_commands.py)
    HITS = 4                                # by the fight command, before the wing edge

    # script variables: 0 and 0x24 are final kefka's. below 0x24 they are the battle's, from it each monster's own
    FLAGS, HEALED, THROWN = 0x01, 0, 1      # a variable and two of its bits
    HIT_COUNT = 0x03
    COIN = 0x24                             # the chromefists'

    SELF, RANDOM_CHARACTER = 0x36, 0x44     # targets
    USE, THROW = 0x00, 0x01
    FIGHT = 0x00                            # command

    def enemies_mod(self, enemies):
        self.enemy(enemies).name = self.NAME
        self.iron_fist_id = enemies.get_enemy(self.HELPER)
        helper = self.helper_enemy_mod(enemies, self.iron_fist_id, self.HELPER_NAME)
        helper.hp = self.HELPER_HP
        helper.level = self.HELPER_LEVEL
        self.helpers_mod(enemies, HELPER_ENEMY, self.HELPER_POSITIONS, self.POSITION)

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id
        from data.item_names import name_id as item_id

        SET, CLEAR = 0x01, 0x02             # ai_instr.Bits
        ADD = ai_instr.Arithmetic.ADD
        battle = ai_instr.Spell(name_id["Battle"])

        # the chromefists: a dirk or two attacks, by the coin they threw the turn before (a condition
        # is tested as the script is read, and what sets a variable when the turn is taken)
        scripts.scripts[HELPER_ENEMY].instructions = [
            ai_instr.If(0x0d, self.COIN, 1),            # if the coin is 1 or more
            ai_instr.RandomItem(self.THROW, item_id["Dirk"], item_id["Dirk"]),
            ai_instr.EndIf(),
            ai_instr.If(0x0c, self.COIN, 1),            # if it is less
            battle,
            battle,
            ai_instr.EndIf(),
            ai_instr.Arithmetic(self.COIN, 0),
            ai_instr.If(CHANCE, 128, 0x00),
            ai_instr.Arithmetic(self.COIN, 1),
            ai_instr.EndMainLoop(),
            ai_instr.EndScript(),
        ]

        # what dadaluma does, before some of the turns of final kefka's script that are not in a
        # condition (his script goes around once in 7 turns or more, and there is not the room in
        # the scripts for all of it before each): the call before every other, the rest before
        # every fourth
        call = [
            ai_instr.If(0x0b, self.CALL_TIME, 0x00),    # if his timer is above this
            ai_instr.Misc(0x00, 0x00),                  # reset his timer
            ai_instr.If(0x12, HELPERS, 0x00),           # if the helpers are dead or not in the battle
            ai_instr.ChangeEnemies(self.CALL_ANIMATION, 0x00, HELPERS),     # bring them in
            ai_instr.EndIf(),
        ]
        heal_and_throw = [
            ai_instr.If(0x06, self.SELF, self.HEAL_HP), # if his hp are below this
            ai_instr.If(0x15, self.FLAGS, self.HEALED), # and he has not done this
            ai_instr.SetTarget(self.SELF),
            ai_instr.RandomItem(self.USE, item_id["X-Potion"], item_id["Potion"]),  # 2 in 3 the first
            ai_instr.RandomItem(self.USE, item_id["X-Potion"], item_id["Potion"]),
            ai_instr.RandomItem(self.USE, item_id["X-Potion"], item_id["Potion"]),
            ai_instr.Spell(name_id["Safe"]),
            ai_instr.Bits(SET, self.FLAGS, self.HEALED),
            ai_instr.EndIf(),

            ai_instr.If(0x0d, self.HIT_COUNT, self.HITS),   # if he has been hit this many times
            ai_instr.If(0x15, self.FLAGS, self.THROWN),     # and he has not done this
            ai_instr.SetTarget(self.RANDOM_CHARACTER),
            ai_instr.RandomItem(self.THROW, item_id["Wing Edge"], item_id["Wing Edge"]),
            ai_instr.Bits(SET, self.FLAGS, self.THROWN),
            ai_instr.EndIf(),
        ]

        script = scripts.get_script(self.ENEMY)
        instructions = script.instructions
        main_end = instructions.index(ai_instr.EndMainLoop())

        turns, in_condition = [], False
        for index, instruction in enumerate(instructions[:main_end]):
            if type(instruction) is ai_instr.If:
                in_condition = True
            elif type(instruction) is ai_instr.EndIf:
                in_condition = False
                if not turns:
                    turns.append(index + 1)             # after his entrance
            elif type(instruction) is ai_instr.EndTurn and not in_condition:
                turns.append(index + 1)
        for turn, index in reversed(list(enumerate(turns))):
            if turn % 4 == 0:
                script.insert(index, call + heal_and_throw)
            elif turn % 2 == 0:
                script.insert(index, list(call))

        # hit by fight: one more hit
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        script.insert(counters + 1, [                   # after what he does when he dies
            ai_instr.If(0x01, self.FIGHT, self.FIGHT),
            ai_instr.Arithmetic(self.HIT_COUNT, ADD | 1),
            ai_instr.EndIf(),
        ])

    @staticmethod
    def chrome(palette):
        # a palette in chrome: its colors by their brightness as dark greys with more contrast, a
        # little blue
        CONTRAST, MIDDLE = 1.6, 14
        TINT = (0.94, 0.98, 1.08)
        colors = []
        for red, green, blue in palette:
            brightness = 0.30 * red + 0.59 * green + 0.11 * blue
            grey = MIDDLE + (brightness - MIDDLE) * CONTRAST
            colors.append(tuple(min(max(round(grey * tint), 0), 31) for tint in TINT))
        return colors

    def battle_mod(self):
        from data.bosses import name_enemy

        width, height = self.TILES
        dadaluma = name_enemy[self.DADALUMA]
        sprite, _ = self.enemy_sprite(dadaluma)
        self.giant_sprite_mod(dadaluma, scale = (height * 8, len(sprite)))
        self.helper_palette_mod(self.iron_fist_id, self.chrome(self.monster_palette(self.iron_fist_id)))
        self.helpers_layout_mod(self.TILES, self.HELPER_TILES, len(self.HELPER_POSITIONS))
        self.chance_condition_mod()
