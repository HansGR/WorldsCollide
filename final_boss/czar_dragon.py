import graphics.czar_dragon as czar_dragon_sprite

from final_boss.final_boss import FinalBoss, ABILITY_DATA_START

class CzarDragon(FinalBoss):
    # czardragon, a boss the game has an enemy for and never uses: here with the looks a later
    # release gave him (graphics/czar_dragon.py). his magic is the highest of each of the eight
    # elements, and his blows are fewer than final kefka's. final kefka's stats, with more magic
    # defense and less defense
    #
    #   Goner       Megiddo: it also sets one status, chosen for each one it hits
    #   Revenger    Terror: drains the whole party, and he gets what they lose
    NAME = "CzarDragon"
    DEFENSE, MAGIC_DEFENSE = 0.9, 1.2       # of final kefka's

    CZAR_DRAGON = 311                       # the unused enemy (a dragon, with graphics as his are)
    SCALE = (1, 1)                          # his sprite is 118x111 pixels: as it is
    LOWER = 16                              # pixels: clear of the boxes at the top

    ABILITY_NAMES = {
        "Goner"     : "Megiddo",
        "Revenger"  : "Terror",
    }
    GONER_TEXT = "GRRROOOAAAR!!<wait 60 frames><end>"

    # the highest attack of each element that an enemy can use on the party
    FIRE, ICE, BOLT, POISON = "Fire 3", "Ice 3", "Bolt 3", "Bio"
    WIND, PEARL, EARTH, WATER = "Aero", "Pearl", "Quake", "El Nino"
    EARTH_ELEMENT = 0x40                    # quake hits both sides: he takes no damage from earth

    # megiddo: one of these for each one it hits (status byte 0 to 2, status), unless protected
    MEGIDDO_STATUSES = [
        (0, 0x01),      # dark
        (0, 0x04),      # poison
        (0, 0x20),      # imp
        (1, 0x08),      # mute
        (1, 0x20),      # muddle
        (1, 0x80),      # sleep
        (2, 0x04),      # slow
        (2, 0x10),      # stop
    ]

    TERROR_SOURCE, TERROR_POWER = "Drain", 60

    def enemies_mod(self, enemies):
        czar = self.enemy(enemies)
        czar.name = self.NAME
        czar.defense = min(round(czar.defense * self.DEFENSE), 2 ** 8 - 1)
        czar.magic_defense = min(round(czar.magic_defense * self.MAGIC_DEFENSE), 2 ** 8 - 1)
        czar.immune_elements |= self.EARTH_ELEMENT

    def scripts_mod(self, scripts):
        # (his battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id

        battle, special, train, revenger, nothing = (
            name_id[name] for name in ["Battle", "Special", "Train", "Revenger", "Nothing"])
        fire, ice, bolt, poison, wind, pearl, earth, water = (name_id[name] for name in [
            self.FIRE, self.ICE, self.BOLT, self.POISON, self.WIND, self.PEARL, self.EARTH, self.WATER])
        script = scripts.get_script(self.ENEMY)
        instructions = script.instructions

        # above 53% hp, after fallen one: the six turns in their order
        blow = ai_instr.RandomAttack(battle, nothing, special)
        blows = [index for index, instruction in enumerate(instructions) if instruction == blow]
        assert len(blows) == 3
        instructions[blows[0]] = ai_instr.RandomAttack(fire, ice, bolt)
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special),
                       ai_instr.RandomAttack(battle, nothing, special))
        instructions[blows[1]] = ai_instr.RandomAttack(poison, wind, earth)
        script.replace(ai_instr.RandomAttack(name_id["Ice 3"], train, special),
                       ai_instr.RandomAttack(battle, train, nothing))
        instructions[blows[2]] = ai_instr.RandomAttack(pearl, water, train)
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(battle, nothing, special))

        # at 53% hp and below, the turns after goner (megiddo; revenger is terror)
        script.replace(ai_instr.RandomAttack(special, train, revenger),
                       ai_instr.RandomAttack(fire, ice, revenger))
        script.replace(ai_instr.RandomAttack(special, nothing, nothing),
                       ai_instr.RandomAttack(bolt, poison, nothing))
        script.replace(ai_instr.RandomAttack(train, special, revenger),
                       ai_instr.RandomAttack(wind, earth, revenger))
        script.replace(ai_instr.RandomAttack(special, special, nothing),
                       ai_instr.RandomAttack(pearl, water, special))

    def data_mod(self, data):
        from data.spell_names import name_id
        from data.ability_data import AbilityData
        NOT_REFLECTABLE, RUNIC = 0x02, 0x08     # flags2
        NOT_DODGED = 0x20                       # flags3

        self.rename_abilities(data, self.ABILITY_NAMES)
        self.goner_text_mod(data, self.GONER_TEXT)

        self.random_status_mod(data, name_id["Goner"], self.MEGIDDO_STATUSES)

        # terror: revenger becomes the drain spell on the whole party, with revenger's animation.
        # it can not be reflected, absorbed by runic or dodged
        revenger = ABILITY_DATA_START + name_id["Revenger"] * AbilityData.DATA_SIZE
        revenger_targets = data.rom.get_bytes(revenger, 1)[0]       # all of the other side

        terror = AbilityData(name_id["Revenger"], data.spells.spells[name_id[self.TERROR_SOURCE]].ability_data())
        terror.targets = revenger_targets
        terror.flags2 = (terror.flags2 | NOT_REFLECTABLE) & ~RUNIC
        terror.flags3 |= NOT_DODGED
        terror.power = self.TERROR_POWER
        data.rom.set_bytes(revenger, terror.ability_data())

    def battle_mod(self):
        self.giant_sprite_mod(self.CZAR_DRAGON, pixels = czar_dragon_sprite.pixels(),
                              palette = czar_dragon_sprite.palette(), scale = self.SCALE, lower = self.LOWER)

        # he charges up before megiddo as final kefka does before goner, without the laughing head:
        # it is a picture of nothing
        HEAD_PIXELS, PALETTE_COLORS = 32, 8
        self.goner_sprite_mod([[0] * HEAD_PIXELS for _ in range(HEAD_PIXELS)], [0] * PALETTE_COLORS)
