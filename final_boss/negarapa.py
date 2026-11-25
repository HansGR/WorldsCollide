import graphics.skull as skull

from memory.space import Reserve, Read

from final_boss.final_boss import FinalBoss, ABILITY_DATA_START

class Negarapa(FinalBoss):
    # nerapa, giant: death on a clock. she starts as nerapa does, with condemned on each of the
    # party, and her attacks are those that kill outright or take a part of the hp there is, with
    # nerapa's fire. final kefka's stats; she absorbs fire as nerapa does, and is weak to ice and pearl
    #
    #   Havoc Wing  Demon Whip, with the sound of a flail and a red line
    #   Goner       Last Rites: it also sets condemned
    NAME = "Negarapa"
    NERAPA = "Nerapa"
    SPECIAL_NAME = "Demon Whip"
    SCALE = (7, 4)                          # her sprite is 64 pixels high: twice that fills the mold, and her head would be behind the boxes at the top
    LOWER = 16                              # pixels: clear of the boxes at the top

    FIRE, ICE, PEARL = 0x01, 0x02, 0x20     # elements

    ABILITY_NAMES = {
        "Goner"     : "Last Rites",
    }
    CONDEMNED = "Condemned"
    CHARACTERS = [0x48, 0x49, 0x4a, 0x4b]   # targets: each of the party (condemned is for one)
    ATTACKER = 0x47                         # target: who hit her last
    NOT_CHARGING, HIT = 0x15, 0x05          # script conditions
    COUNTERS = ["Demi", "Shimsham", "Nothing"]

    # demon whip: the blow a monster's special attack is shown with is one of a table (8 bytes
    # each: byte 3 the picture of the hit, byte 4 its palette, byte 6 its sound). one that no
    # monster uses becomes hers: a line across its target (0) in red (0x35), and the sound of the
    # flail (0x5b)
    SPECIAL_ATTACK_GRAPHICS, SPECIAL_GRAPHICS_DATA, SPECIAL_GRAPHIC_SIZE = 0xf37c0, 0x2ce6e8, 8
    ENEMIES = 384
    WHIP_GRAPHIC = 29
    WHIP = [0x41, 0x41, 0x00, 0x00, 0x35, 0x00, 0x5b, 0x00]

    STATUS_2_BYTE, CONDEMNED_STATUS = 11, 0x01      # in an attack's data

    def enemies_mod(self, enemies):
        self.nerapa = enemies.get_enemy(self.NERAPA)
        negarapa = self.enemy(enemies)
        negarapa.name = self.NAME
        negarapa.special_name = self.SPECIAL_NAME
        negarapa.absorb_elements |= self.FIRE
        negarapa.weak_elements |= self.ICE | self.PEARL

    def scripts_mod(self, scripts):
        # (her battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id

        battle, special, train, revenger, nothing = (
            name_id[name] for name in ["Battle", "Special", "Train", "Revenger", "Nothing"])
        fire, s_cross, demi, quartr, doom, x_zone, roulette, merton, flare = (name_id[name] for name in [
            "Fire 3", "S. Cross", "Demi", "Quartr", "Doom", "X-Zone", "Roulette", "Merton", "Flare"])
        condemned = name_id[self.CONDEMNED]
        script = scripts.get_script(self.ENEMY)
        instructions = script.instructions

        def condemn():
            return [instruction for character in self.CHARACTERS
                    for instruction in (ai_instr.SetTarget(character), ai_instr.Spell(condemned))]

        # her first turn (where the battle's first turn is known, once): condemned on each of the party
        first_turn = instructions.index(ai_instr.EndIf())
        script.insert(first_turn, condemn() + [ai_instr.EndTurn()])

        # above 53% hp: four turns in the place of fallen one and final kefka's six
        instructions = script.instructions
        fallen_one = instructions.index(ai_instr.Spell(name_id["Fallen One"]))
        end = instructions.index(ai_instr.EndMainLoop())
        assert isinstance(instructions[fallen_one - 1], ai_instr.SetTarget)
        instructions[fallen_one - 1:end] = [
            ai_instr.RandomAttack(fire, s_cross, special),
            ai_instr.EndTurn(),
            ai_instr.RandomAttack(battle, demi, nothing),
            ai_instr.EndTurn(),
            ai_instr.RandomAttack(fire, doom, special),
            ai_instr.EndTurn(),
            ai_instr.RandomAttack(battle, roulette, nothing),
        ]

        # at 53% hp and below, the turns after goner (last rites)
        script.replace(ai_instr.RandomAttack(special, train, revenger),
                       ai_instr.RandomAttack(quartr, fire, x_zone))
        script.replace(ai_instr.RandomAttack(special, nothing, nothing),
                       ai_instr.RandomAttack(special, doom, nothing))
        script.replace(ai_instr.RandomAttack(train, special, revenger),
                       ai_instr.RandomAttack(merton, quartr, battle))
        script.replace(ai_instr.RandomAttack(special, special, nothing),
                       ai_instr.RandomAttack(flare, nothing, nothing))

        # hit, at any hp (not while she charges up): one of her counters on who hit her, in the
        # place of final kefka's below 17% and below 49% hp. after what she does when she dies
        instructions = script.instructions
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop())) + 1
        instructions[counters:len(instructions) - 1] = [
            ai_instr.If(self.NOT_CHARGING, 0x00, 0x00),
            ai_instr.If(self.HIT, 0x00, 0x00),
            ai_instr.SetTarget(self.ATTACKER),
            ai_instr.RandomAttack(*(name_id[name] for name in self.COUNTERS)),
        ]

    def data_mod(self, data):
        from data.spell_names import name_id
        from data.ability_data import AbilityData

        self.rename_abilities(data, self.ABILITY_NAMES)

        # last rites: goner also sets condemned on those it hits
        status = ABILITY_DATA_START + name_id["Goner"] * AbilityData.DATA_SIZE + self.STATUS_2_BYTE
        data.rom.set_bytes(status, [data.rom.get_bytes(status, 1)[0] | self.CONDEMNED_STATUS])

    def battle_mod(self):
        self.giant_sprite_mod(self.nerapa, scale = self.SCALE, lower = self.LOWER)

        # demon whip
        used = Read(self.SPECIAL_ATTACK_GRAPHICS, self.SPECIAL_ATTACK_GRAPHICS + self.ENEMIES - 1)
        assert self.WHIP_GRAPHIC not in used, "a monster's special attack is shown with it"
        graphic = self.SPECIAL_GRAPHICS_DATA + self.WHIP_GRAPHIC * self.SPECIAL_GRAPHIC_SIZE
        Reserve(graphic, graphic + self.SPECIAL_GRAPHIC_SIZE - 1, "demon whip graphic").write(self.WHIP)
        special = self.SPECIAL_ATTACK_GRAPHICS + self.enemy_id
        Reserve(special, special, "final kefka special attack graphic").write(self.WHIP_GRAPHIC)

        # she charges up before last rites as final kefka does before goner, and a skull is shown
        # where his laughing head was
        self.goner_sprite_mod(skull.pixels(), skull.palette())
