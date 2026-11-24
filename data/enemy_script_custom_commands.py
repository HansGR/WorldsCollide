from memory.space import Bank, START_ADDRESS_SNES, Reserve, Allocate, Write, Read
import instruction.asm as asm
from constants.battle_addresses import ENEMY_LEVEL

# 0xf0 custom argument values (e.g. FIRE1 = randomly choose from fire category with tier +1)
FIRE0, FIRE1, FIRE2, ICE0, ICE1, ICE2, BOLT0, BOLT1, BOLT2, EARTH0, EARTH1, EARTH2, WIND0, WIND1, WIND2, WATER0, WATER1, WATER2, POISON0, POISON1, POISON2, PEARL0, PEARL1, PEARL2, NON_ELEMENTAL0, NON_ELEMENTAL1, NON_ELEMENTAL2 = range(0x36, 0x51)
# NOTE: gap in range here to keep original skean/edge/storm argument ids
CURE0, CURE1, CURE2, TEK0, TEK1, TEK2, DAMAGE0, DAMAGE1, DAMAGE2, SPECIAL0, SPECIAL1, SPECIAL2 = range(0x55, 0x61)
# NOTE: 0x61 and 0x62 still available

# an attack value (alone or as an 0xf0 argument) which is the jump command, for scripts which call jump_attack_mod
JUMP = 0x63
# and one which throws an item, for scripts which call command_attacks_mod
THROW = 0x64
# and one which is the attack for the element the monster is weak to
WEAKNESS = 0x65
# and one which is the esper of a character of the party, for scripts which call command_attacks_mod with mirror_cast
MIRROR_CAST = 0x66

def get_custom_ability_tier(category_tier):
    if category_tier >= 0x55:
        category_tier -= 1
    return category_tier % 3

class EnemyScriptCommands:
    def __init__(self, rom, args, enemy_scripts, enemies):
        self.rom = rom
        self.args = args
        self.enemy_scripts = enemy_scripts
        self.enemies = enemies

    def hp_check_command_mod(self):
        # modify script command [0xfc, 0x06, target, hp_value]
        # change hp_value to a percentage of the target's maximum hp

        # NOTE: small rounding errors can occur from division
        src = [
            asm.LDA(0x3a2f, asm.ABS),   # a = percent
            asm.STA(0xe8, asm.DIR),     # $e8 = percent
            asm.A16(),
            asm.LDA(0x3c1c, asm.ABS_Y), # a = max_hp
            asm.PHX(),
            asm.LDX(0x64, asm.IMM8),    # x = 100
            asm.CMP(0x028f, asm.IMM16), # compare max_hp with 655 (prevent 2 byte multiplication overflow)
            asm.BCC("HP < 655"),        # branch if max_hp < 655 (safe for 16 bit hp and 8 bit percent multiply)

            "HP >= 655",
            asm.JSR(0x4792, asm.ABS),   # a = max_hp / 100
            asm.JSR(0x47b7, asm.ABS),   # $e8 = (max_hp / 100) * percent
            asm.LDA(0xe8, asm.DIR),     # a = (max_hp / 100) * percent
            asm.BRA("RETURN"),

            "HP < 655",
            asm.JSR(0x47b7, asm.ABS),   # $e8 = max_hp * percent
            asm.LDA(0xe8, asm.DIR),     # a = max_hp * percent
            asm.JSR(0x4792, asm.ABS),   # a = (max_hp * percent) / 100

            "RETURN",
            asm.PLX(),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "enemy script calculate percent of max hp")
        hp_percent_calculate = space.start_address

        space = Reserve(0x21bbd, 0x21bc3, "enemy script command 0xfc 0x06 calculate hp threshold", asm.NOP())
        space.write(
            asm.JSR(hp_percent_calculate, asm.ABS),
        )

    def jump_attack_mod(self):
        # the attack JUMP is the jump command, as script command [0xf4, 0x16, ...] uses it (umaro's
        # script), so that a script can choose between jumping and its attacks with 0xf0.
        # for the scripts which need it (final_boss/ultimaro.py): not part of mod()
        JUMP_COMMAND = 0x16
        CHOOSE_ATTACK_COMMAND = 0x1dbf      # a = command to use the attack in a with, b = the attack

        src = [
            asm.CMP(JUMP, asm.IMM8),
            asm.BEQ("JUMP"),
            asm.JMP(CHOOSE_ATTACK_COMMAND, asm.ABS),

            "JUMP",
            asm.TDC(),                      # no attack
            asm.LDA(JUMP_COMMAND, asm.IMM8),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "enemy script jump attack")
        choose_command = space.start_address

        space = Reserve(0x21b25, 0x21b27, "enemy script choose command for attack", asm.NOP())
        space.write(
            asm.JSR(choose_command, asm.ABS),
        )

    def command_attacks_mod(self, attacks, weakness_attacks = None, no_weakness_attack = None, mirror_cast = None):
        # as jump_attack_mod, for more than the jump: {attack value : (command, its argument)}, so
        # that a script can choose with 0xf0 between its attacks and JUMP: (0x16, 0), or throwing an
        # item, THROW: (0x08, the item) (script command [0xf6, 0x01, ...] does that)
        #
        # with weakness_attacks (8 attacks, for fire, ice, bolt, poison, wind, pearl, earth and
        # water), the attack value WEAKNESS is the one for the element the monster is weak to (the
        # first of them), or no_weakness_attack: what master pug does after wallchange
        #
        # with mirror_cast (espers not to cast, the attack if there is none to cast, the enemy who casts,
        # the attack it is named by), the attack value
        # MIRROR_CAST is the esper that one of the party has equipped: a character of the party is
        # chosen, and the next ones are tried if that one is not there, has no esper or has one
        # of those not to cast. (an esper's attack in a script is summoned as it is: 0x36 and up)
        # it is named at the top of the screen by an attack's name, not the esper's (as the magicite
        # item is by the item's), and shown as it is to a party attacked from behind: from the other
        # side (the espers' animations choose what they do by the side the party is on). a bit of
        # the battle's memory says that the enemy's last attack was this
        # the espers that attack are not to hit characters (a flag of their data: "abort on
        # characters", which takes the characters out of an attack's targets), so that does not hold
        # for this enemy
        # for the scripts which need it (final_boss/): not part of mod()
        # a = the attack, y = the monster. 8 bit a, x and y
        CHOOSE_ATTACK_COMMAND = 0x1dbf      # a = command to use the attack in a with, b = the attack
        weak_elements = 0x3be0

        src = []
        for index, attack in enumerate(attacks):
            src += [
                asm.CMP(attack, asm.IMM8),
                asm.BEQ(f"COMMAND_{index}"),
            ]
        if weakness_attacks is not None:
            assert len(weakness_attacks) == 8
            table = Write(Bank.C2, weakness_attacks, "enemy script attacks by weakness")
            src += [
                asm.CMP(WEAKNESS, asm.IMM8),
                asm.BNE("CHOOSE"),
                asm.LDA(weak_elements, asm.ABS_Y),
                asm.LDX(0x00, asm.IMM8),
                "ELEMENT",
                asm.LSR(),
                asm.BCS("WEAK"),
                asm.INX(),
                asm.CPX(len(weakness_attacks), asm.IMM8),
                asm.BNE("ELEMENT"),
                asm.LDA(no_weakness_attack, asm.IMM8),
                asm.BRA("CHOOSE"),
                "WEAK",
                asm.LDA(table.start_address_snes, asm.LNG_X),
                "CHOOSE",
            ]
        if mirror_cast is not None:
            # (bank c2 has little room: what can be is in bank f0)
            RANDOM = 0x4b65                 # 0 to a - 1
            FIRST_ESPER_ATTACK = 0x36
            CHARACTERS = 4
            FIRST_ENEMY = 8
            character_bit, present, esper = 0x3018, 0x3a74, 0x3344
            no_espers, no_esper_attack, caster, name_attack = mirror_cast
            mirror_casting, MIRROR_CASTING = 0x3f2e, 0x80   # (its low bits: the characters who have used their espers)

            # the name at the top of the screen: for a summon it is the esper's attack, by its number
            # y = the attacker. 8 bit a, x and y
            SUMMON_NAME_START, SUMMON_NAME_END = 0x2368e, 0x23693
            ATTACK_NAME = 0x00
            name_type, attack = 0x3a29, 0xb6
            # (every summon is named here as it is carried out: the bit is set for his, and cleared for
            # the party's, which may come between his choice and his summon)
            summon_name = Write(Bank.F0, [
                asm.LDA(MIRROR_CASTING, asm.IMM8),
                asm.CPY(FIRST_ENEMY, asm.IMM8),
                asm.BLT("ESPER"),
                asm.TSB(mirror_casting, asm.ABS),
                asm.LDA(ATTACK_NAME, asm.IMM8),
                asm.STA(name_type, asm.ABS),
                asm.LDA(name_attack, asm.IMM8),
                asm.RTL(),
                "ESPER",
                asm.TRB(mirror_casting, asm.ABS),
                asm.SEC(),
                asm.LDA(attack, asm.DIR),
                asm.SBC(FIRST_ESPER_ATTACK, asm.IMM8),
                asm.RTL(),
            ], "enemy script mirror cast: name")
            assert Read(SUMMON_NAME_START, SUMMON_NAME_END) == [0x38, 0xa5, attack, 0xe9, FIRST_ESPER_ATTACK, 0x60]
            space = Reserve(SUMMON_NAME_START, SUMMON_NAME_END, "summon name", asm.NOP())
            space.write(
                asm.JSL(summon_name.start_address_snes),
                asm.RTS(),
            )

            # an animation's script asks how the battle began (0: as usual, 1: the party attacked from
            # behind, 2: from both sides, 3: with the enemies between the party) to choose what it does
            # x = the animation. 8 bit a
            BATTLE_TYPE_START, BATTLE_TYPE_END = 0x1d408, 0x1d40c
            FROM_BEHIND = 0x01
            caster_position = 0x6a38                # bit 7: an enemy
            battle_type = Write(Bank.F0, [
                asm.LDA(caster_position, asm.ABS_X),
                asm.BPL("AS_IT_IS"),
                asm.LDA(mirror_casting, asm.ABS),
                asm.BPL("AS_IT_IS"),
                asm.LDA(FROM_BEHIND, asm.IMM8),
                asm.RTL(),
                "AS_IT_IS",
                Read(BATTLE_TYPE_START, BATTLE_TYPE_END),
                asm.RTL(),
            ], "enemy script mirror cast: battle type for animations")
            space = Reserve(BATTLE_TYPE_START, BATTLE_TYPE_END, "animation battle type", asm.NOP())
            space.write(
                asm.JSL(battle_type.start_address_snes),
            )

            # a summon hides the party while the esper is there (how each of the four characters is
            # shown: 0x30 as it is, 0x00 not at all). for his espers the party stays
            # 8 bit a
            HIDE_PARTY_START, HIDE_PARTY_END = 0x192fb, 0x192fe
            shown = [0x61bd, 0x61dd, 0x61fd, 0x621d]
            assert Read(HIDE_PARTY_START, HIDE_PARTY_END) == [0x7b, 0x20, 0x5e, 0x92]
            hide_party = Write(Bank.F0, [
                asm.LDA(mirror_casting, asm.ABS),
                asm.BMI("STAYS"),
                [asm.STZ(character, asm.ABS) for character in shown],
                "STAYS",
                asm.TDC(),
                asm.RTL(),
            ], "enemy script mirror cast: the party stays")
            space = Reserve(HIDE_PARTY_START, HIDE_PARTY_END, "summon: hide the party")
            space.write(
                asm.JSL(hide_party.start_address_snes),
            )

            # (before that the party fades out: 0x20, set for the first character and then, with what a
            # has, for the others)
            FADE_PARTY_START, FADE_PARTY_END = 0x19673, 0x19677
            FADING, SHOWN = 0x20, 0x30
            assert Read(FADE_PARTY_START, FADE_PARTY_END) == [0xa9, FADING, 0x8d, 0xbd, 0x61]
            fade_party = Write(Bank.F0, [
                asm.LDA(mirror_casting, asm.ABS),
                asm.BMI("STAYS"),
                asm.LDA(FADING, asm.IMM8),
                asm.BRA("SET"),
                "STAYS",
                asm.LDA(SHOWN, asm.IMM8),
                "SET",
                asm.STA(shown[0], asm.ABS),
                asm.RTL(),
            ], "enemy script mirror cast: the party does not fade")
            space = Reserve(FADE_PARTY_START, FADE_PARTY_END, "summon: fade the party", asm.NOP())
            space.write(
                asm.JSL(fade_party.start_address_snes),
            )

            # (and two commands of the animations' scripts set it for the four characters, one with its
            # value after the command and one at the script's place)
            SHOW_CHARACTERS_START, SHOW_CHARACTERS_END = 0x1d45c, 0x1d45f
            SET_CHARACTERS_START, SET_CHARACTERS_END = 0x1e746, 0x1e74a
            assert Read(SHOW_CHARACTERS_START, SHOW_CHARACTERS_END) == [0xb7, 0x5b, 0x85, 0x10]
            assert Read(SET_CHARACTERS_START, SET_CHARACTERS_END) == [0xa7, 0x5b, 0x8d, 0xbd, 0x61]

            def party_stays(value, rest):
                return [
                    asm.LDA(mirror_casting, asm.ABS),
                    asm.BPL("AS_IT_IS"),
                    asm.LDA(SHOWN, asm.IMM8),
                    asm.BRA("SET"),
                    "AS_IT_IS",
                    value,                              # the value the script has
                    "SET",
                    rest,
                    asm.RTL(),
                ]
            show = Write(Bank.F0, party_stays([0xb7, 0x5b], [0x85, 0x10]), "enemy script mirror cast: the party is shown")
            space = Reserve(SHOW_CHARACTERS_START, SHOW_CHARACTERS_END, "animation: show characters")
            space.write(
                asm.JSL(show.start_address_snes),
            )
            show = Write(Bank.F0, party_stays([0xa7, 0x5b], [0x8d, 0xbd, 0x61]), "enemy script mirror cast: the party is set")
            space = Reserve(SET_CHARACTERS_START, SET_CHARACTERS_END, "animation: set characters", asm.NOP())
            space.write(
                asm.JSL(show.start_address_snes),
            )

            # (and one command stops the characters' palettes from being set, each frame, while their
            # colors are faded out: for his espers they keep being set)
            KEEP_PALETTES_START, KEEP_PALETTES_END = 0x1d493, 0x1d497
            assert Read(KEEP_PALETTES_START, KEEP_PALETTES_END) == [0xb7, 0x5b, 0x8d, 0xbf, 0x62]
            palettes = Write(Bank.F0, [
                [0xb7, 0x5b],                           # the value the script has
                asm.BIT(mirror_casting, asm.ABS),
                asm.BPL("SET"),
                asm.LDA(0x00, asm.IMM8),
                "SET",
                [0x8d, 0xbf, 0x62],
                asm.RTL(),
            ], "enemy script mirror cast: the party's palettes")
            space = Reserve(KEEP_PALETTES_START, KEEP_PALETTES_END, "animation: characters' palettes", asm.NOP())
            space.write(
                asm.JSL(palettes.start_address_snes),
            )

            # (and one command says whether the characters are drawn at all: for his espers they are)
            DRAW_CHARACTERS_START, DRAW_CHARACTERS_END = 0x1d48b, 0x1d48f
            assert Read(DRAW_CHARACTERS_START, DRAW_CHARACTERS_END) == [0xb7, 0x5b, 0x8d, 0xbd, 0x62]
            drawn = Write(Bank.F0, [
                [0xb7, 0x5b],                           # the value the script has
                asm.BIT(mirror_casting, asm.ABS),
                asm.BPL("SET"),
                asm.LDA(0x00, asm.IMM8),
                "SET",
                [0x8d, 0xbd, 0x62],
                asm.RTL(),
            ], "enemy script mirror cast: the party is drawn")
            space = Reserve(DRAW_CHARACTERS_START, DRAW_CHARACTERS_END, "animation: draw characters", asm.NOP())
            space.write(
                asm.JSL(drawn.start_address_snes),
            )

            # "abort on characters": the characters are taken out of the targets
            # x = the attacker (8 and up are the enemies). 8 bit a, x and y
            ABORT_ON_CHARACTERS_START, ABORT_ON_CHARACTERS_END = 0x25905, 0x2590a
            target_flags, character_targets, enemy_ids = 0xba, 0xb8, 0x33a8
            assert Read(ABORT_ON_CHARACTERS_START, ABORT_ON_CHARACTERS_END) == [0xa5, target_flags, 0x10, 0x02, 0x64, character_targets]
            abort = Write(Bank.F0, [
                asm.LDA(target_flags, asm.DIR),
                asm.BPL("RETURN"),                  # not abort on characters
                asm.CPX(FIRST_ENEMY, asm.IMM8),
                asm.BLT("ABORT"),
                asm.A16(),
                asm.LDA(enemy_ids, asm.ABS_X),
                asm.CMP(caster, asm.IMM16),
                asm.A8(),
                asm.BEQ("NO_ABORT"),
                "ABORT",
                asm.STZ(character_targets, asm.DIR),
                "NO_ABORT",
                asm.LDA(target_flags, asm.DIR),
                "RETURN",
                asm.RTL(),
            ], "enemy script mirror cast: abort on characters")
            space = Reserve(ABORT_ON_CHARACTERS_START, ABORT_ON_CHARACTERS_END, "abort on characters", asm.NOP())
            space.write(
                asm.JSL(abort.start_address_snes),
            )

            # the esper of a character: a = where to start (0 to 3). returns the attack in a
            find = [
                asm.PHY(),
                asm.ASL(),
                asm.TAY(),
                asm.LDX(CHARACTERS, asm.IMM8),
                "CHARACTER",
                asm.LDA(character_bit, asm.ABS_Y),
                asm.BIT(present, asm.ABS),
                asm.BEQ("NEXT_CHARACTER"),          # not there, or dead
                asm.LDA(esper, asm.ABS_Y),
                asm.BMI("NEXT_CHARACTER"),          # none equipped
            ]
            for no_esper in no_espers:
                find += [
                    asm.CMP(no_esper, asm.IMM8),
                    asm.BEQ("NEXT_CHARACTER"),
                ]
            find += [
                asm.CLC(),
                asm.ADC(FIRST_ESPER_ATTACK, asm.IMM8),
                asm.PHA(),
                asm.LDA(MIRROR_CASTING, asm.IMM8),
                asm.TSB(mirror_casting, asm.ABS),
                asm.PLA(),
                asm.PLY(),
                asm.RTL(),
                "NEXT_CHARACTER",
                asm.INY(),
                asm.INY(),
                asm.TYA(),
                asm.AND(CHARACTERS * 2 - 1, asm.IMM8),
                asm.TAY(),
                asm.DEX(),
                asm.BNE("CHARACTER"),
                asm.PLY(),
                asm.LDA(no_esper_attack, asm.IMM8),
            ]
            not_mirror_cast = [
                asm.PHA(),
                asm.LDA(MIRROR_CASTING, asm.IMM8),
                asm.TRB(mirror_casting, asm.ABS),
                asm.PLA(),
                asm.RTL(),
            ]
            find_space = Write(Bank.F0, find + not_mirror_cast, "enemy script mirror cast: find an esper")
            not_mirror_cast_space = Write(Bank.F0, not_mirror_cast, "enemy script mirror cast: not this")
            src += [
                asm.CMP(MIRROR_CAST, asm.IMM8),
                asm.BNE("NO_MIRROR_CAST"),
                asm.LDA(CHARACTERS, asm.IMM8),
                asm.JSR(RANDOM, asm.ABS),
                asm.JSL(find_space.start_address_snes),
                asm.BRA("CHOSEN"),
                "NO_MIRROR_CAST",
                asm.JSL(not_mirror_cast_space.start_address_snes),
                "CHOSEN",
            ]
        src += [
            asm.JMP(CHOOSE_ATTACK_COMMAND, asm.ABS),
        ]
        for index, (command, argument) in enumerate(attacks.values()):
            src += [
                f"COMMAND_{index}",
                asm.LDA(argument, asm.IMM8),
                asm.XBA(),
                asm.LDA(command, asm.IMM8),
                asm.RTS(),
            ]
        space = Write(Bank.C2, src, "enemy script command attacks")
        choose_command = space.start_address

        space = Reserve(0x21b25, 0x21b27, "enemy script choose command for attack", asm.NOP())
        space.write(
            asm.JSR(choose_command, asm.ABS),
        )

    def hp_conditions_mod(self):
        # change hp value checks to hp percent checks

        # enemies and the number of hp checks they have
        enemy_checks = [("Intangir", 1), ("Vargas", 2), ("TunnelArmr", 1), ("Dadaluma", 1), ("Umaro", 1), ("AtmaWeapon", 3),
                        ("SrBehemoth", 1), ("Dullahan", 1), ("Doom", 1), ("Goddess", 1), ("Poltrgeist", 1), ("Kefka (Final)", 4),
                        ("Ultros 3", 2), ("Laser Gun", 1), ("MissileBay", 1), ("Chadarnook (Demon)", 1),
                        ("Storm Drgn", 1), ("Blue Drgn", 1), ("Red Dragon", 1), ("Short Arm", 1), ("Long Arm", 1), ("Face", 1),
                        ("Tiger", 1), ("Tools", 1), ("Magic", 4), ("Sleep", 2), ("Ultros 4", 1), ("Phunbaba 2", 1),
                        ("Phunbaba 3", 1), ("Atma", 1)]

        import math
        import data.enemy_script_commands as ai_instr
        for enemy_name, check_count in enemy_checks:
            enemy_id = self.enemies.get_enemy(enemy_name)
            enemy = self.enemies.enemies[enemy_id]
            script = self.enemy_scripts.scripts[enemy_id]

            search_start = 0
            replacement_count = 0
            hp_check_prefix = [0xfc, 0x06, 0x36] # check hp of self (self was only target i found used)
            for instruction_index, instruction in enumerate(script.instructions):
                values = instruction()
                if values[:len(hp_check_prefix)] == hp_check_prefix:
                    hp_value = values[3]
                    hp_percent = min(100, math.ceil(((hp_value * 128) / enemy.original_hp) * 100))
                    values[3] = hp_percent

                    script.instructions[instruction_index] = ai_instr.If(*values[1 : ])
                    replacement_count += 1
            assert(replacement_count == check_count)

    def random_tiered_ability_mod(self, space):
        # modify script command [0xf0, possible_id, possible_id, possible_id]
        # returns a random tiered spell if possible_id is an esper/swdtech/blitz id

        # tier = min(enemy level / levels_per_tier, 8) + (argument offset) + (random offset in range [-2, 2])
        # e.g. with a level 10 enemy, 5 = levels_per_tier and argument offset +1 the tier will be between 1 and 5
        # arguments now indicate the category as well as a tier offset of either +0, +1, or +2
        #   original argument ids still valid as long as not esper/swdtech/blitz id

        # for special attacks there are 16 damage tiers in vanilla, this function sets them dynamically
        # tier = min(enemy_level / 4, 11) + (argument offset) + (random offset in range [-2, 2])

        from data.spells import Spells
        from data.spell_names import name_id
        import data.enemy_ability_tiers as ability_tiers
        import instruction.c4 as c4

        # max tier reachable based only on enemy level (can be increased further from argument/distortion)
        MAX_ENEMY_LEVEL_TIER = 8
        ENEMY_LEVELS_PER_TIER = self.args.ability_scaling_factor + 3
        MAX_ENEMY_LEVEL_SPECIAL_TIER = 11
        ENEMY_LEVELS_PER_SPECIAL_TIER = 4
        MAX_SPECIAL_TIER = 15

        categories = [ability_tiers.fire, ability_tiers.ice, ability_tiers.bolt, ability_tiers.earth,
                      ability_tiers.wind, ability_tiers.water, ability_tiers.poison, ability_tiers.pearl,
                      ability_tiers.non_elemental, ability_tiers.cure, ability_tiers.tek, ability_tiers.damage]

        # with -fb, the final boss's own attacks are not in the tiers
        import final_boss
        own_abilities = [name_id[name] for name in final_boss.own_abilities()]

        tier_addresses = []
        for category in categories:
            for tier in category:
                tier = [ability for ability in tier if ability not in own_abilities]
                assert tier, "an ability tier is empty"
                tier_addresses.append(space.next_address)
                space.write(tier)
        tier_addresses.append(space.next_address)

        tier_table_pointers = space.next_address
        for address in tier_addresses:
            space.write(address.to_bytes(3, "little")[:2]),

        # ability tier is distorted by between [-2, 2], the distortion amounts are weighted
        # store thresholds for mapping 0-255 random number generator to distribution
        tier_distribution_thresholds = [
            0x00, #   0 -  24 = tier-2 (~10%)
            0x19, #  25 -  88 = tier-1 (~25%)
            0x59, #  89 - 177 = tier   (~35%)
            0xb2, # 178 - 241 = tier+1 (~25%)
            0xf2, # 242 - 255 = tier+2 (~05%)
        ]
        tier_distribution_table = space.next_address
        space.write(tier_distribution_thresholds)

        get_tier_distortion = space.next_address
        space.write(
            # distort the tier based on tier_distribution_table
            asm.JSR(c4.battle_rng, asm.ABS),# a = random number (0-255)
            asm.LDX(len(tier_distribution_thresholds) - 1, asm.IMM8),

            "THRESHOLD_LOOP_START",
            asm.CMP(tier_distribution_table + START_ADDRESS_SNES, asm.LNG_X),
            asm.BGE("THRESHOLD_LOOP_EXIT"), # branch if random value >= tier_threshold[x]
            asm.DEX(),
            asm.BPL("THRESHOLD_LOOP_START"),# branch if x >= 0

            "THRESHOLD_LOOP_EXIT",
            asm.TXA(),                      # a = random_tier_offset + 2 (not shifted to [-2, 2] range yet)
            asm.CLC(),
            asm.ADC(0xee, asm.DIR),         # a = random_tier_offset + 2 + current offset
            asm.CMP(0x02, asm.IMM8),        # check if shifting random tier offset will result in negative value
            asm.BGE("MIN_CHECKED"),         # branch if final tier >= 2
            asm.LDA(0x02, asm.IMM8),        # shifting random_tier_offset will result in negative tier, clamp to zero

            "MIN_CHECKED",
            asm.DEC(),                      # subtract 2 (convert random_tier_offset range to [-2, 2])
            asm.DEC(),
            asm.RTS(),
        )

        # tier based on enemy level (0 to 8) + random offset (-2 to 2) + argument offset (0 to 2)
        get_random_tiered_spell = space.next_address
        space.write(
            asm.SEC(),
            asm.SBC(Spells.SPELL_COUNT, asm.IMM8),  # convert argument to 0 based index
            asm.CMP(0x1b, asm.IMM8),
            asm.BLT("GET_CATEGORY"),                # branch if id < 0x1b (args < 0x1b now 0 based)

            # the randomization flags are not contiguous because of skean/edge/storm
            # if id comes after 0x50 then subtract another 4 from the argument to make the indices contigous
            asm.SEC(),
            asm.SBC(0x04, asm.IMM8),                # convert argument to 0 based index

            # 0 based argument indicates category and an offset (+0, +1, or +2)
            "GET_CATEGORY",
            asm.LDX(0x03, asm.IMM8),                # a = divisor (number of values per category: +0, +1, +2)
            asm.JSR(c4.divide, asm.ABS),            # a = argument / 3 = category (e.g. fire/ice/cure/tek/damage/...)
            asm.STX(0xee, asm.DIR),                 # $ee = argument % 3 = offset (+0, +1, or +2)
            asm.XBA(),                              # b = category
            asm.LDA(ability_tiers.TIER_COUNT, asm.IMM8),
            asm.JSR(c4.multiply, asm.ABS),          # a = num addresses * category (i.e. index of tier 0 for category)
            asm.PHA(),                              # push index of tier 0 for category

            # add the enemy tier to the above category tier offset
            asm.LDA(ENEMY_LEVEL, asm.ABS_Y),        # a = enemy's level
            asm.CMP(int(ENEMY_LEVELS_PER_TIER * MAX_ENEMY_LEVEL_TIER), asm.IMM8),
            asm.BLT("TIER<MAX"),                    # branch if enemy tier is < max tier (no high level overflow)
            asm.LDA(MAX_ENEMY_LEVEL_TIER, asm.IMM8),# clamp enemy tier to max enemy tier
            asm.BRA("TIER_OFFSET"),

            "TIER<MAX",
            asm.ASL(),                              # a = enemy level * 2
            asm.LDX(int(ENEMY_LEVELS_PER_TIER * 2), asm.IMM8),  # doubled to allow 0.5 increments
            asm.JSR(c4.divide, asm.ABS),            # a = (enemy level * 2) / (levels per tier * 2)

            "TIER_OFFSET",
            asm.CLC(),
            asm.ADC(0xee, asm.DIR),                 # a = enemy tier + argument tier offset
            asm.STA(0xee, asm.DIR),

            asm.JSR(get_tier_distortion, asm.ABS),  # a = enemy tier + argument tier offset + random offset
            asm.CMP(ability_tiers.TIER_COUNT, asm.IMM8),
            asm.BLT("MAX_CHECKED"),                 # branch if final tier < max tier + 1
            asm.LDA(ability_tiers.TIER_COUNT - 1, asm.IMM8),    # clamp final tier to max tier

            "MAX_CHECKED",
            asm.STA(0xee, asm.DIR),                 # $ee = final tier = random offset + enemy tier + argument offset

            # find index of category's final tier in tier_table_pointers
            asm.PLA(),                              # a = index of tier 0 for category
            asm.CLC(),
            asm.ADC(0xee, asm.DIR),                 # a = final tier + index of tier 0 for category

            # find number of elements in tier and pick one of them randomly
            asm.AXY16(),
            asm.ASL(),                              # multiply tier by 2 (pointers are 2 bytes each in table)
            asm.TAX(),                              # x = tier pointer offset
            asm.LDA(tier_table_pointers + START_ADDRESS_SNES, asm.LNG_X),
            asm.STA(0xee, asm.DIR),                 # $ee = tier table pointer
            asm.INX(),
            asm.INX(),
            asm.LDA(tier_table_pointers + START_ADDRESS_SNES, asm.LNG_X),
            asm.SEC(),
            asm.SBC(0xee, asm.DIR),                 # a = (tier+1 pointer) - (tier pointer) = number abilities in tier
            asm.JSR(c4.battle_rng_a, asm.ABS),      # a = random number (0 to number abilities in tier - 1)
            asm.CLC(),
            asm.ADC(0xee, asm.DIR),                 # a = tier pointer + index of random ability in tier
            asm.TAX(),
            asm.LDA(0xc40000, asm.LNG_X),           # a = randomly chosen spell id from the tier
            asm.AXY8(),
            asm.RTL(),
        )

        get_random_tiered_special = space.next_address
        space.write(
            asm.SEC(),
            asm.SBC(SPECIAL0, asm.IMM8),            # convert argument to 0, 1, or 2
            asm.STA(0xee, asm.DIR),                 # $ee = argument tier

            asm.LDA(ENEMY_LEVEL, asm.ABS_Y),        # a = enemy's level
            asm.LDX(ENEMY_LEVELS_PER_SPECIAL_TIER, asm.IMM8),
            asm.JSR(c4.divide, asm.ABS),            # a = enemy's level / ENEMY_LEVELS_PER_SPECIAL_TIER
            asm.CMP(MAX_ENEMY_LEVEL_SPECIAL_TIER + 1, asm.IMM8),
            asm.BLT("TIER<MAX_SPECIAL+1"),          # branch if enemy tier is < max tier + 1
            asm.LDA(MAX_ENEMY_LEVEL_SPECIAL_TIER, asm.IMM8),    # clamp enemy tier to max enemy special tier

            "TIER<MAX_SPECIAL+1",
            asm.CLC(),
            asm.ADC(0xee, asm.DIR),                 # a = enemy tier + argument tier offset
            asm.STA(0xee, asm.DIR),

            asm.JSR(get_tier_distortion, asm.ABS),  # a = enemy tier + argument tier offset + random offset
            asm.CMP(MAX_SPECIAL_TIER + 1, asm.IMM8),# compare final tier with (max tier + 1)
            asm.BLT("MAX_SPECIAL_CHECKED"),         # branch if final tier < max tier + 1
            asm.LDA(MAX_SPECIAL_TIER, asm.IMM8),    # clamp final tier to max tier

            "MAX_SPECIAL_CHECKED",
            asm.STA(0xee, asm.DIR),                 # $ee = final tier = random offset + enemy tier + argument offset

            asm.LDA(0x33a8, asm.ABS_Y),             # a = enemy id
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),                              # a = enemy id * 32 (enemy data is 32 bytes each)
            asm.TAX(),                              # x = enemy id * 32
            asm.A8(),

            asm.LDA(0xcf001f, asm.LNG_X),           # a = enemy special attack data
            asm.AND(0x0c, asm.IMM8),                # extract no damage/always hit flags
            asm.STA(0x322d, asm.ABS_Y),
            asm.LDA(0xee, asm.DIR),                 # a = tier
            asm.ADC(0x20, asm.IMM8),                # add index of effects tier 0 (convert tier to effects value)
            asm.ORA(0x322d, asm.ABS_Y),             # or tier with no damage/always hit flags
            asm.STA(0x322d, asm.ABS_Y),             # store tier + no damage/always hit flags

            asm.XY8(),
            asm.LDA(0x06, asm.IMM8),                # a = attack type (6 = special attack)
            asm.STA(0x3412, asm.ABS),               # store special attack type to show attack name at top of screen

            asm.LDA(name_id["Special"], asm.IMM8),  # a = special attack id to execute chosen/stored special
            asm.RTL(),
        )

        space = Reserve(0x2a76a, 0x2a7af, "enemy script parse 0xf0 command arguments and return ability id")
        get_ability_id = space.next_address
        space.write(
            asm.LDA(0x3a2c, asm.ABS),               # a = current enemy command
            asm.CMP(0xf0, asm.IMM8),                # compare to 0xf0 (lowest command value)
            asm.BLT("GET_ABILITY_ID"),              # branch if current command < 0xf0 (it is a single spell id)

            asm.LDA(0x03, asm.IMM8),                # a = number of arguments
            asm.JSR(0x4b65, asm.ABS),               # pick random argument index
            asm.TAX(),
            asm.LDA(0x3a2d, asm.ABS_X),             # a = random argument
            asm.CMP(0xfe, asm.IMM8),                # compare with do nothing argument
            asm.BNE("GET_ABILITY_ID"),              # branch if not do nothing

            asm.PLA(),
            asm.PLA(),                              # pull return address from stack
            asm.JMP(0x1ab4, asm.ABS),               # jump to skip executing this command and continue with ai script

            "GET_ABILITY_ID",
            asm.CMP(Spells.SPELL_COUNT, asm.IMM8),
            asm.BLT("RETURN"),                      # branch if a contains a regular spell id

            # use 0x36 to 0x50 as elemental/non-elemental flags instead of esper ids
            asm.CMP(name_id["Fire Skean"], asm.IMM8),
            asm.BLT("RANDOM_SPELL"),                # branch if a is a random elemental/non-elemental spell

            # elemental skean/edge ids are used by some scripts (and storm could be used)
            # do not use them as flags for randomization, skip them
            asm.CMP(name_id["Storm"] + 1, asm.IMM8),
            asm.BLT("RETURN"),                      # branch if a is fire skean, water edge, bolt edge, or storm

            # use 0x55 to 0x64 as cure/tek/damage/special flags instead of swdtech/blitz ids
            asm.CMP(SPECIAL0, asm.IMM8),
            asm.BLT("RANDOM_SPELL"),                # branch if a is a cure/tek/damage spell

            asm.CMP(SPECIAL2 + 1, asm.IMM8),
            asm.BLT("RANDOM_SPECIAL"),              # branch if a is a random special enemy ability

            "RETURN",
            asm.RTS(),

            "RANDOM_SPELL",
            asm.JSL(get_random_tiered_spell + START_ADDRESS_SNES),
            asm.RTS(),

            "RANDOM_SPECIAL",
            asm.JSL(get_random_tiered_special + START_ADDRESS_SNES),
            asm.RTS(),
        )

        space = Reserve(0x21b22, 0x21b24, "enemy script 0xf0, call custom get ability", asm.NOP())
        random_attack_command = space.next_address
        space.write(
            asm.JSR(get_ability_id, asm.ABS),
        )

        # vanilla spell ids branch to 0xf0 after the random one is chosen
        # instead, branch to the start of customized 0xf0 which can execute random abilities
        space = Reserve(0x21afd, 0x21afd, "enemy script spell id, call custom get ability")
        space.add_label("RANDOM ATTACK COMMAND", random_attack_command)
        space.write(
            space.label_distance("RANDOM ATTACK COMMAND") - 1,
        )

    def mod(self):
        self.hp_check_command_mod()
        self.hp_conditions_mod()

        scaling_space = Allocate(Bank.C4, 946, "enemy script get random tiered ability")
        if self.args.ability_scaling:
            self.random_tiered_ability_mod(scaling_space)
