import graphics.czar_dragon as czar_dragon_sprite
import graphics.czar_fire as czar_fire

from final_boss.final_boss import FinalBoss, ABILITY_DATA_START

class CzarDragon(FinalBoss):
    # czardragon, a boss the game has an enemy for and never uses: here with the looks a later
    # release gave him (graphics/czar_dragon.py). his magic is the highest of each of the eight
    # elements, and his blows are fewer than final kefka's. final kefka's stats, with more speed
    # and magic defense and less defense
    #
    #   Goner       Megiddo: it also sets one status, chosen for each one it hits
    #   Revenger    Terror: drains the whole party, and he gets what they lose
    NAME = "CzarDragon"
    SPEED, DEFENSE, MAGIC_DEFENSE = 1.2, 0.9, 1.2   # of final kefka's

    CZAR_DRAGON = 311                       # the unused enemy (a dragon, with graphics as his are)
    SCALE = (1, 1)                          # his sprite is 118x111 pixels: as it is
    LOWER = 16                              # pixels: clear of the boxes at the top
    FIRE_MOVE = (1, -1)                     # the fire: 16 pixels left and 16 up from the laughing head's place

    ABILITY_NAMES = {
        "Goner"     : "Megiddo",
        "Revenger"  : "Terror",
    }
    GONER_TEXT = "Mwa ha ha... Prepare yourselves!<wait 60 frames><end>"

    # the highest attack of each element that an enemy can use on the party
    FIRE, ICE, BOLT, POISON = "Fire 3", "Ice 3", "Bolt 3", "Bio"
    WIND, PEARL, EARTH, WATER = "Aero", "Pearl", "Quake", "El Nino"
    # he takes half the damage of fire, ice and bolt (the magic a party has most of), absorbs wind
    # (merton, fire and wind, hits both sides: it heals him) and takes the damage of the others:
    # of poison too, where final kefka takes none. he flies, for good: quake, which hits both
    # sides, misses him
    HALF_ELEMENTS = 0x01 | 0x02 | 0x04
    WIND_ELEMENT, POISON_ELEMENT = 0x10, 0x08
    MERTON, N_CROSS, GIGA_VOLT = "Merton", "N. Cross", "Giga Volt"      # at 53% hp and below

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

    TERROR_SOURCE, TERROR_POWER = "Drain", 100

    def enemies_mod(self, enemies):
        czar = self.enemy(enemies)
        czar.name = self.NAME
        czar.speed = min(round(czar.speed * self.SPEED), 2 ** 8 - 1)
        czar.defense = min(round(czar.defense * self.DEFENSE), 2 ** 8 - 1)
        czar.magic_defense = min(round(czar.magic_defense * self.MAGIC_DEFENSE), 2 ** 8 - 1)
        czar.immune_elements &= ~self.POISON_ELEMENT
        # float that is not taken away: on a monster that is "dance" among its statuses. (not the
        # float of its data's last status byte as well: that one is also kept in a byte of the
        # battle's where it means something else, and with it he dies as any monster does, without
        # the final death)
        czar.status_effects.dance = 1
        czar.absorb_elements |= self.WIND_ELEMENT

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
                       ai_instr.RandomAttack(name_id[self.MERTON], name_id[self.N_CROSS], revenger))
        script.replace(ai_instr.RandomAttack(special, nothing, nothing),
                       ai_instr.RandomAttack(name_id[self.GIGA_VOLT], poison, nothing))
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
        self.goner_text_mod(data, self.GONER_TEXT, room = True)

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
        self.half_damage_mod(self.HALF_ELEMENTS)
        self.giant_sprite_mod(self.CZAR_DRAGON, pixels = czar_dragon_sprite.pixels(),
                              palette = czar_dragon_sprite.palette(), scale = self.SCALE, lower = self.LOWER)

        # he charges up before megiddo as final kefka does before goner. for the laughing head, his
        # eye flashes and fire comes out of his nostrils: a picture of them is shown over his head,
        # and taken away
        self.goner_sprite_mod(czar_fire.pixels(), czar_fire.palette(), self.FIRE_MOVE)
