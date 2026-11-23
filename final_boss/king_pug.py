from final_boss.final_boss import FinalBoss

class KingPug(FinalBoss):
    # pug (the green one), giant: big, slow, and he hits hard. final kefka's script with wallchange
    # for fallen one, the spell for his weakness as master pug casts it, stop, a lullaby (sleep on the
    # whole party) and life mine: step mine by the target's experience
    NAME = "King Pug"
    SPEED, VIGOR = 0.8, 1.2                 # of final kefka's
    HP = 2 ** 16 - 1                        # the most an enemy can have

    PUG = "Pug"
    SCALE = (3, 1)                          # pug is 32x32 pixels: 96x96
    LOWER = 32                              # pixels: clear of the boxes at the top

    SPECIAL_NAME = "Cleaver"                # was havoc wing
    ABILITY_NAMES = {
        "Goner"         : "Grudge",
        "Revenger"      : "Lullaby",
    }
    GONER_TEXT = "......<wait 60 frames><end>"
    LULLABY_HIT_RATE = 90                   # the sleep spell's is 111
    LIFE_MINE = "Confusion"                 # an attack no script, sketch, control or rage uses
    LIFE_MINE_DIVISOR = 64

    # master pug's spells for his weakness: fire, ice, bolt, poison, wind, pearl, earth, water
    WEAKNESS_SPELLS = ["Ice 3", "Fire 3", "W Wind", "Pearl", "Bolt 3", "Bio", "CleanSweep", "Quake"]
    NO_WEAKNESS_ATTACK = "Battle"           # before his first wallchange

    WATER = 0x80                            # element
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

        # above 53% hp: wallchange (on himself) for fallen one, then six turns
        script.replace([ai_instr.SetTarget(self.ALL_CHARACTERS), ai_instr.Spell(name_id["Fallen One"])],
                       [ai_instr.SetTarget(self.SELF), ai_instr.Spell(name_id["WallChange"])])
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

    def data_mod(self, data):
        from data.spell_names import name_id

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.goner_text_mod(data, self.GONER_TEXT)

        # the lullaby: sleep on the whole party
        self.party_status_attack_mod(data, "Sleep", self.LULLABY_HIT_RATE)

        # life mine: step mine, by the target's experience
        life_mine = self.new_attack_mod(data, name_id[self.LIFE_MINE], name_id["Step Mine"], "Life Mine")
        data.rom.set_bytes(life_mine + self.POWER_BYTE, [self.LIFE_MINE_DIVISOR])
        self.experience_damage_mod(data, name_id[self.LIFE_MINE])

    def battle_mod(self):
        self.giant_sprite_mod(self.pug, scale = self.SCALE, lower = self.LOWER)
