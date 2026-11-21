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

    def jump_mod(self):
        # when ultimaro jumps (scripts_mod) he lands 2 to 4 times, as
        # with a dragon horn: where the jump command looks for the jumper's dragon horn ("jump
        # continuously", bit 7 of its relic effects), he has one
        # x = the jumper (8 and up are the enemies). 8 bit a, x and y
        JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END = 0x21820, 0x21822

        relic_effects = 0x3c44
        enemy_ids = 0x33a8
        first_enemy = 8

        src = [
            Read(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END),
            asm.BMI("RETURN"),                      # branch if the jumper has a dragon horn

            asm.CPX(first_enemy, asm.IMM8),
            asm.BLT("NO_DRAGON_HORN"),
            asm.A16(),
            asm.LDA(enemy_ids, asm.ABS_X),
            asm.CMP(self.enemy_id, asm.IMM16),
            asm.A8(),                               # (keeps the zero flag)
            asm.BNE("NO_DRAGON_HORN"),
            asm.LDA(0x80, asm.IMM8),
            asm.RTS(),

            "NO_DRAGON_HORN",
            asm.LDA(relic_effects, asm.ABS_X),

            "RETURN",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "ultimaro jumps as with a dragon horn")
        jumper_relic_effects = space.start_address

        space = Reserve(JUMPER_RELIC_EFFECTS_START, JUMPER_RELIC_EFFECTS_END, "jump: load jumper's relic effects", asm.NOP())
        space.write(
            asm.JSR(jumper_relic_effects, asm.ABS),
        )

    def jump_animation_mod(self):
        # a jumper with more landings to come (only the dragon horn does that) bounces: down onto
        # the target and straight back up, and it returns to its place only after the last landing.
        # the game's own animation hops back after every landing
        #
        # the damage of a landing shows when its animation has ended, and outside of an animation
        # monsters are drawn over the characters and the damage. so the jumper goes up at the speed
        # it took off with and nothing is left to wait for after that: the damage shows as soon as
        # it is gone
        #
        # the landing of a monster's jump is animation script 0x84 (D1/EAD8 has the scripts'
        # pointers, they are in bank D0). it is copied here with the bounce added after the fall
        LANDING_SCRIPT = 0x84
        SCRIPT_POINTERS = 0x11ead8
        LANDING_START, LANDING_END = 0x10682d, 0x106855
        FALL_END = 0x10684e                 # the fall's last byte; what follows is the hop back and the end

        landing = Read(LANDING_START, LANDING_END)
        fall = landing[:FALL_END - LANDING_START + 1]
        hop_back = landing[FALL_END - LANDING_START + 1:]

        DOWN_8_PIXELS, UP_8_PIXELS, DOWN_32_PIXELS = 0x27, 0xc7, 0x3f
        assert fall[-6:] == [0x89, 0x13, 0x86, DOWN_8_PIXELS, 0x0f, 0x8a]   # 20 times: move, wait a frame
        assert hop_back == [0xd1, 0x00, 0x0f, 0xe3, 0x08, 0x03, 0xff]

        src = [
            fall,
            0x80, 0x7d, len(hop_back),      # skip the hop back if another landing is coming
            hop_back,

            0x89, 0x13,                     # 20 times, the way it came:
                0x86, UP_8_PIXELS,
                0x0f,                       # wait a frame
            0x8a,
            0xe1, 0x80,                     # hide the monster
            [0x86, DOWN_32_PIXELS] * 5,     # the script is back where the fall ended
            0xd1, 0x00,                     # (as before the hop back)
            0xe3, 0xff, 0x00,               # the hop back, all of it at once: the monster is in its place
            0xff,
        ]
        src = [value for values in src for value in (values if isinstance(values, list) else [values])]
        space = Write(Bank.D0, src, "ultimaro: monster jump landing animation")
        landing_script = space.start_address

        pointer = SCRIPT_POINTERS + LANDING_SCRIPT * 2
        space = Reserve(pointer, pointer + 1, "monster jump landing animation script pointer")
        space.write(
            (landing_script & 0xffff).to_bytes(2, "little"),
        )

