from memory.space import Bank, Reserve, Write, Read
import instruction.asm as asm
import graphics.monster_sprite as monster_sprite
import graphics.green_cherry as green_cherry

from final_boss.final_boss import FinalBoss

class Ultimaro(FinalBoss):
    # umaro, giant. he is 5 levels above final kefka and a fifth faster, absorbs ice as umaro does and
    # has ice where kefka had fire and bolt. he jumps as umaro does, landing 2 to 4 times as with a
    # dragon horn, and eats a green cherry before u'ghaaaa (goner)
    #
    #   Havoc Wing  Yeti Punch, with the looks of umaro's tackle
    #   HyperDrive  Yeti Blast
    #   Goner       U'ghaaaa
    #   Revenger    Enrager: the bserk spell on the whole party
    NAME = "Ultimaro"
    LEVELS = 5
    SPEED = 1.2

    UMARO = "Umaro"
    SHADOW_COLOR, SHADOW_ROWS = 1, 8        # umaro stands on a shadow, a patch of his outline color

    ABILITY_NAMES = {
        "HyperDrive"    : "Yeti Blast",
        "Goner"         : "U'ghaaaa",
        "Revenger"      : "Enrager",
    }
    GONER_TEXT = "Yeti used a Green Cherry!<wait 60 frames><end>"
    ENRAGER_HIT_RATE = 75       # half of bserk's

    def enemies_mod(self, enemies):
        ultimaro = self.enemy(enemies)
        umaro = enemies.enemies[enemies.get_enemy(self.UMARO)]

        ultimaro.name = self.NAME
        ultimaro.special_name = "Yeti Punch"        # was Havoc Wing
        ultimaro.speed = min(round(ultimaro.speed * self.SPEED), 2 ** 8 - 1)
        ultimaro.absorb_elements |= umaro.absorb_elements       # ice

    def scripts_mod(self, scripts):
        # (his battle program is written out in final_boss/README.md: keep it up to date with this)
        import data.enemy_script_commands as ai_instr
        from data.spell_names import name_id
        from data.enemy_script_custom_commands import JUMP

        # a script can choose JUMP as it does its attacks
        scripts.enemy_script_custom_commands.jump_attack_mod()

        special, train, revenger, nothing = (name_id[name] for name in ["Special", "Train", "Revenger", "Nothing"])
        script = scripts.get_script(self.ENEMY)

        # above 53% hp, every other turn
        script.replace(ai_instr.RandomAttack(name_id["Fire 3"], train, special),
                       ai_instr.RandomAttack(name_id["Storm"], train, special))
        script.replace(ai_instr.RandomAttack(name_id["Bolt 3"], nothing, special),
                       ai_instr.RandomAttack(name_id["Surge"], nothing, special))

        # at 53% hp and below, the turns after goner
        script.replace(ai_instr.RandomAttack(special, train, revenger),      # (revenger is enrager)
                       ai_instr.RandomAttack(special, name_id["Ice 3"], revenger))
        script.replace(ai_instr.RandomAttack(train, special, revenger),
                       ai_instr.RandomAttack(train, special, JUMP))
        script.replace(ai_instr.RandomAttack(special, special, nothing),
                       ai_instr.RandomAttack(special, JUMP, nothing))

    def data_mod(self, data):
        self.rename_abilities(data, self.ABILITY_NAMES)
        self.party_status_attack_mod(data, "Bserk", self.ENRAGER_HIT_RATE)

        self.goner_text_mod(data, self.GONER_TEXT)

    def battle_mod(self):
        from data.bosses import name_enemy
        umaro = name_enemy[self.UMARO]

        self.giant_sprite_mod(umaro, self.SHADOW_COLOR, self.SHADOW_ROWS)
        self.special_attack_mod(umaro)
        self.jump_mod()
        self.jump_animation_mod()
        self.goner_sprite_mod(green_cherry.pixels(), green_cherry.palette())     # he eats a green cherry

    def special_attack_mod(self, umaro):
        # ultimaro's special attack (yeti punch: final kefka's havoc wing, and still that
        # attack in every other way) looks and sounds like umaro's (tackle)
        SPECIAL_ATTACK_GRAPHICS = 0xf37c0       # a byte for each enemy

        space = Reserve(SPECIAL_ATTACK_GRAPHICS + self.enemy_id, SPECIAL_ATTACK_GRAPHICS + self.enemy_id, "final kefka special attack graphic")
        space.write(
            Read(SPECIAL_ATTACK_GRAPHICS + umaro, SPECIAL_ATTACK_GRAPHICS + umaro),
        )
