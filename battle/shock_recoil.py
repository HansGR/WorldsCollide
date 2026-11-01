from memory.space import Bank, Reserve, Write
import instruction.asm as asm
import args

# -shr: Shock also damages its user for 1/8 of their max HP, in the same animation.
#
# Every attack runs its special effect twice: once per attack before the targets are
# processed (C2/33A6 -> C2/3E7D, table C2/42E1, attacker in y) and once per target
# (C2/387E, table C2/3DCD). Damage is collected per entity in $33d0 ($ffff = none);
# after the attack the animation shows a number for every entity with a value and
# C2/62EF applies them all to HP (KO included), targets or not -- the same way Drain
# shows the attacker's healing. Shock (attack $82) has no special effect, so it gets an
# unused slot whose once-per-attack routine writes the caster's $33d0 = max hp / 8.
# The caster is not a target, so no damage roll touches it (a muddled caster that
# targets itself adds the two). It skips the damage formula: exactly 1/8, no defense,
# variance, Shell or Morph.

SHOCK = 0x82
ABILITY_DATA_START = 0x046ac0
ABILITY_DATA_SIZE = 14
EFFECT_OFFSET = 9
# special effect $14: a bare RTS in both effect tables and used by no attack
RECOIL_EFFECT = 0x14
ONCE_PER_ATTACK_TABLE = 0x242e1
PER_TARGET_TABLE = 0x23dcd
DAMAGE = 0x33d0
MAX_HP = 0x3c1c
PARTY_END = 0x08                # party entities are 0, 2, 4, 6

def mod():
    if not args.shock_recoil:
        return

    from memory.space import Space
    for table in (ONCE_PER_ATTACK_TABLE, PER_TARGET_TABLE):
        pointer = Space.rom.get_bytes(table + 2 * RECOIL_EFFECT, 2)
        routine = 0x20000 + int.from_bytes(bytes(pointer), "little")
        assert Space.rom.get_byte(routine) == 0x60, f"effect {RECOIL_EFFECT:#x} is in use"

    src = [
        asm.CPY(PARTY_END, asm.IMM8),
        asm.BGE("RETURN"),                  # an enemy's Shock does not recoil
        asm.A16(),
        asm.LDA(MAX_HP, asm.ABS_Y),
        asm.LSR(),
        asm.LSR(),
        asm.LSR(),                          # max hp / 8
        asm.BNE("STORE"),
        asm.INC(),                          # at least 1
        "STORE",
        asm.STA(DAMAGE, asm.ABS_Y),         # the caster's damage this attack
        asm.A8(),
        "RETURN",
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "shock recoil: caster takes max hp / 8")
    recoil = space.start_address

    space = Reserve(ONCE_PER_ATTACK_TABLE + 2 * RECOIL_EFFECT, ONCE_PER_ATTACK_TABLE + 2 * RECOIL_EFFECT + 1,
                    "shock recoil once-per-attack effect pointer")
    space.write((recoil & 0xffff).to_bytes(2, "little"))

    effect = ABILITY_DATA_START + SHOCK * ABILITY_DATA_SIZE + EFFECT_OFFSET
    space = Reserve(effect, effect, "shock special effect: recoil")
    space.write(RECOIL_EFFECT)

mod()
