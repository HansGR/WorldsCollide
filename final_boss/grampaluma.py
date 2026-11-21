from final_boss.final_boss import FinalBoss, HELPERS, HELPER_ENEMY, CHANCE, ABILITY_DATA_START

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
    HELPER = "Scrapper"                     # the highest of the enemies with the iron fist's looks: his stats
    HELPER_LOOKS = "Iron Fist"
    HELPER_NAME = "ChromeFist"
    HELPER_HP = 14000
    HELPER_LEVEL, HELPER_VIGOR, HELPER_EVADE = 40, 14, 60       # the scrapper's are 34, 10 and 120

    SPECIAL_NAME = "Tiger Claw"             # was havoc wing
    ABILITY_NAMES = {
        "Goner"         : "Chi Shock",
        "Revenger"      : "Time Warp",
    }
    GONER_TEXT = "Friends! Lovely to see you.<wait 60 frames><end>"
    SWEEP = "Confusion"                     # an attack no script, sketch, control or rage uses: his sweep
    SWEEP_LOOKS = "Sonic Boom"
    TIME_WARP_HIT_RATE = 150                # slow 2's

    ONE_TARGET = 0x41                       # an attack's targets (its first byte): one, of the other side
    SEIZURE_BYTE, SEIZURE = 11, 0x40        # in an attack's data: the second status byte (sap)
    HASTE_BYTE, HASTE = 2, 0x08             # the third status byte

    # dadaluma is 88x56 pixels, and he 107x68: 1.21 times that (the most that fit the 128 pixels
    # of a formation's graphics is 1.43 times). the monsters of the formation share 16x16 tiles of
    # graphics: he has the top 14x10, and the chromefists 6x6 each under him
    HEIGHT = 68
    TILES = (14, 10)
    HELPER_TILES = (6, 6)

    # on the screen, (x, y) in steps of 8 pixels: he is clear of the boxes at the top
    POSITION = (2, 8)
    HELPER_POSITIONS = [(15, 5), (15, 12)]

    CALL_TIME = 30                          # he calls them when they are gone and his timer is above this
    CALL_ANIMATION = 3
    HEAL_HP = 25                            # percent (data/enemy_script_custom_commands.py)
    HITS = 4                                # by the fight command, before the wing edge

    # script variables: 0 and 0x24 are final kefka's. below 0x24 they are the battle's, from it each monster's own
    FLAGS, HEALED, THROWN = 0x01, 0, 1      # a variable and two of its bits
    HIT_COUNT = 0x03

    SELF, RANDOM_CHARACTER = 0x36, 0x44     # targets
    USE, THROW = 0x00, 0x01
    FIGHT = 0x00                            # command

    def enemies_mod(self, enemies):
        grampaluma = self.enemy(enemies)
        grampaluma.name = self.NAME
        grampaluma.special_name = self.SPECIAL_NAME
        # for time warp: an enemy protected from slow or haste is protected from both
        grampaluma.status_immunities.haste = 0
        grampaluma.status_immunities.slow = 0

        self.iron_fist_id = enemies.get_enemy(self.HELPER_LOOKS)
        helper = self.helper_enemy_mod(enemies, enemies.get_enemy(self.HELPER), self.HELPER_NAME)
        helper.hp = self.HELPER_HP
        helper.level = self.HELPER_LEVEL
        helper.vigor = self.HELPER_VIGOR
        helper.evasion = self.HELPER_EVADE
        helper.status_immunities.haste = 0
        helper.status_immunities.slow = 0
        self.helpers_mod(enemies, HELPER_ENEMY, self.HELPER_POSITIONS, self.POSITION)

    def scripts_mod(self, scripts):
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id
        from data.item_names import name_id as item_id

        SET, CLEAR = 0x01, 0x02             # ai_instr.Bits
        ADD = ai_instr.Arithmetic.ADD
        battle = ai_instr.Spell(name_id["Battle"])

        # a script is blocks which end with EndIf or the end of the script: each turn, from the top,
        # the first block whose conditions are all true is what the monster does, and the turn ends
        # with the block (or at an EndTurn in it, after which the block goes on the turn it is
        # reached again). a block with no condition is always true.

        # the chromefists: a dirk, or else two attacks
        scripts.scripts[HELPER_ENEMY].instructions = [
            ai_instr.If(CHANCE, 128, 0x00),
            ai_instr.SetTarget(self.RANDOM_CHARACTER),
            ai_instr.RandomItem(self.THROW, item_id["Dirk"], item_id["Dirk"]),
            ai_instr.EndIf(),
            battle,
            battle,
            ai_instr.EndMainLoop(),
            ai_instr.EndScript(),
        ]

        # what dadaluma does: blocks before final kefka's, after his entrance, tested every turn. a
        # block which ends a turn also has final kefka's script start over (with fallen one), so
        # each of these ends with a condition that is never true: what is before it is done, and the
        # turn goes on with final kefka's script where it was
        never = ai_instr.If(CHANCE, 0, 0x00)
        call = [
            ai_instr.If(0x0b, self.CALL_TIME, 0x00),    # if his timer is above this
            ai_instr.Misc(0x00, 0x00),                  # reset his timer
            ai_instr.If(0x12, HELPERS, 0x00),           # if the helpers are dead or not in the battle
            ai_instr.ChangeEnemies(self.CALL_ANIMATION, 0x00, HELPERS),     # bring them in
            never,
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
            never,
            ai_instr.EndIf(),

            ai_instr.If(0x0d, self.HIT_COUNT, self.HITS),   # if he has been hit this many times
            ai_instr.If(0x15, self.FLAGS, self.THROWN),     # and he has not done this
            ai_instr.SetTarget(self.RANDOM_CHARACTER),
            ai_instr.RandomItem(self.THROW, item_id["Wing Edge"], item_id["Wing Edge"]),
            ai_instr.Bits(SET, self.FLAGS, self.THROWN),
            never,
            ai_instr.EndIf(),
        ]

        script = scripts.get_script(self.ENEMY)
        instructions = script.instructions

        # his attacks. a script can choose JUMP and THROW (a mithril knife) as it does its attacks
        from data.enemy_script_custom_commands import JUMP, THROW
        JUMP_COMMAND, THROW_COMMAND = 0x16, 0x08
        scripts.enemy_script_custom_commands.command_attacks_mod({
            JUMP    : (JUMP_COMMAND, 0),
            THROW   : (THROW_COMMAND, item_id["MithrilKnife"]),
        })
        special, train, revenger, nothing = (name_id[name] for name in ["Special", "Train", "Revenger", "Nothing"])
        sweep, hyperdrive = name_id[self.SWEEP], name_id["HyperDrive"]

        # above 53% hp, every other turn
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special),
                       ai_instr.RandomAttack(THROW, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Ice 3"], train, special),
                       ai_instr.RandomAttack(hyperdrive, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(sweep, nothing, special))

        # at 53% hp and below, the turns after goner (chi shock; revenger is time warp)
        script.replace(ai_instr.RandomAttack(special, train, revenger),
                       ai_instr.RandomAttack(special, THROW, revenger))
        script.replace(ai_instr.RandomAttack(train, special, revenger),
                       ai_instr.RandomAttack(train, special, JUMP))
        script.replace(ai_instr.RandomAttack(special, special, nothing),
                       ai_instr.RandomAttack(special, JUMP, nothing))

        # no laughing head before chi shock
        head = ai_instr.Animate(0x0a, 0x01, 0x00)
        script.remove(head, count = 2)


        entrance_end = instructions.index(ai_instr.EndIf())
        script.insert(entrance_end + 1, call + heal_and_throw)

        # hit by fight: one more hit (and then what final kefka's script does when he is hit)
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        script.insert(counters + 1, [                   # after what he does when he dies
            ai_instr.If(0x01, self.FIGHT, self.FIGHT),
            ai_instr.Arithmetic(self.HIT_COUNT, ADD | 1),
            never,
            ai_instr.EndIf(),
        ])

    def data_mod(self, data):
        from data.spell_names import name_id
        from data.ability_data import AbilityData

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.goner_text_mod(data, self.GONER_TEXT)

        # chi shock also saps
        status = ABILITY_DATA_START + name_id["Goner"] * AbilityData.DATA_SIZE + self.SEIZURE_BYTE
        data.rom.set_bytes(status, [data.rom.get_bytes(status, 1)[0] | self.SEIZURE])

        # time warp: slow 2 on the whole party, and haste for every enemy
        self.party_status_attack_mod(data, "Slow 2", self.TIME_WARP_HIT_RATE)
        self.party_statuses_mod(data, name_id["Revenger"], self.HASTE_BYTE, self.HASTE)

        # sweep, dadaluma's special: a blow which saps (tentacle is the enemies' one attack that is a blow)
        sweep = self.new_attack_mod(data, name_id[self.SWEEP], name_id["Tentacle"], "Sweep", name_id[self.SWEEP_LOOKS])
        status = sweep + self.SEIZURE_BYTE
        data.rom.set_bytes(status, [data.rom.get_bytes(status, 1)[0] | self.SEIZURE])
        data.rom.set_bytes(sweep, [self.ONE_TARGET])

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
        self.giant_sprite_mod(dadaluma, scale = (self.HEIGHT, len(sprite)))
        self.helper_palette_mod(self.iron_fist_id, self.chrome(self.monster_palette(self.iron_fist_id)))
        self.helpers_layout_mod(self.TILES, self.HELPER_TILES, len(self.HELPER_POSITIONS))
        self.chance_condition_mod()
        self.jump_mod()
        self.jump_animation_mod()
