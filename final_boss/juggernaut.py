from memory.space import Reserve, Read

from final_boss.final_boss import FinalBoss

SPECIAL_ATTACK_GRAPHICS = 0xf37c0           # the blow an enemy's special attack is shown with, a byte for each enemy

class Juggernaut(FinalBoss):
    # tunnelarmr, giant: armor that blows do little to, and that answers magic. final kefka's stats
    # with much more defense and less magic defense, weak to bolt and water as tunnelarmr is
    #
    #   Havoc Wing  Drill, with the looks of tunnelarmr's
    NAME = "Juggernaut"
    DEFENSE, MAGIC_DEFENSE = 1.8, 0.75      # of final kefka's

    TUNNEL_ARMOR = "TunnelArmr"
    SPECIAL_NAME = "Drill"
    SHADOW_COLOR, SHADOW_ROWS = 1, 12
    SCALE = (4, 3)                          # his sprite is 95x59 pixels without its shadow: 127 wide is the most that fits
    LOWER = 24                              # pixels: clear of the boxes at the top

    BOLT, WATER = 0x04, 0x80                # elements

    # the armors' attacks, where final kefka has fire 3, ice 3 and bolt 3
    LASERS = ["Atomic Ray", "Shrapnel", "Diffuser"]

    # hit by magic: one of these, at any hp
    MAGIC, X_MAGIC, LORE, SUMMON = 0x02, 0x17, 0x0c, 0x19       # commands
    MAGIC_ANSWERS = ["Diffuser", "Atomic Ray", "Tek Laser"]
    HIT_BY_COMMAND, NOT_CHARGING = 0x01, 0x15                   # script conditions

    def enemies_mod(self, enemies):
        self.tunnel_armor = enemies.get_enemy(self.TUNNEL_ARMOR)
        juggernaut = self.enemy(enemies)
        juggernaut.name = self.NAME
        juggernaut.special_name = self.SPECIAL_NAME
        juggernaut.defense = min(round(juggernaut.defense * self.DEFENSE), 2 ** 8 - 1)
        juggernaut.magic_defense = min(round(juggernaut.magic_defense * self.MAGIC_DEFENSE), 2 ** 8 - 1)
        juggernaut.weak_elements |= self.BOLT | self.WATER

    def scripts_mod(self, scripts):
        # (his battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id

        special, train, nothing = (name_id[name] for name in ["Special", "Train", "Nothing"])
        script = scripts.get_script(self.ENEMY)

        # above 53% hp, every other turn
        fire, ice, bolt = (name_id[name] for name in self.LASERS)
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special), ai_instr.RandomAttack(fire, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Ice 3"], train, special), ai_instr.RandomAttack(ice, train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special), ai_instr.RandomAttack(bolt, nothing, special))

        # hit by a spell (magic, x-magic, a lore or an esper): he answers, before what else he does
        # when he is hit and after what he does when he dies. not while he charges up, as kefka's
        instructions = script.instructions
        counters = instructions.index(ai_instr.EndIf(), instructions.index(ai_instr.EndMainLoop()))
        answers = [name_id[name] for name in self.MAGIC_ANSWERS]
        answer = []
        for commands in ((self.MAGIC, self.X_MAGIC), (self.LORE, self.SUMMON)):
            answer += [
                ai_instr.If(self.HIT_BY_COMMAND, *commands),
                ai_instr.If(self.NOT_CHARGING, 0x00, 0x00),
                ai_instr.RandomAttack(*answers),
                ai_instr.EndIf(),
            ]
        script.insert(counters + 1, answer)

    def battle_mod(self):
        self.giant_sprite_mod(self.tunnel_armor, self.SHADOW_COLOR, self.SHADOW_ROWS,
                              scale = self.SCALE, lower = self.LOWER)

        # his special attack is shown as tunnelarmr's is
        graphic = Read(SPECIAL_ATTACK_GRAPHICS + self.tunnel_armor, SPECIAL_ATTACK_GRAPHICS + self.tunnel_armor)
        space = Reserve(SPECIAL_ATTACK_GRAPHICS + self.enemy_id, SPECIAL_ATTACK_GRAPHICS + self.enemy_id, "final kefka special attack graphic")
        space.write(graphic)
