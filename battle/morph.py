from memory.space import Bank, Reserve, Write
import instruction.asm as asm

# Morph for any number of characters, sharing one timer.
#
# Vanilla keeps one Morph timer and remembers one morphed character:
#   $1cf6       morph supply (save data), shared by the party
#   $3ee2       entity index of the morphed character ($ff = none)
#   $3f30-$3f31 the morph gauge, counting down from $ffff
#   $3f32       how much the gauge drains per tick (from the supply when morph starts)
#   $3b04,x     each entity's displayed gauge
# Morph starting (C2/0B01) does nothing when $3ee2 already holds someone, the battle
# loop (C2/1141) ticks the gauge only for the entity in $3ee2, and morph ending
# (C2/0AE7) clears $3ee2 and the gauge whoever ends it. A second Morph user therefore
# got the status with no timer, and whichever reverted first stopped the other's timer.
# After battle (C2/5E2F) only one character id (vanilla: Terra) added the battle's
# magic points to the supply.
#
# Here $3ee2 only says whether the timer is running, and who is morphed comes from
# each character's own Morph status bit ($3ef9,x bit 3). The first character to morph
# starts the timer as in vanilla; later ones join it, and every morphed character
# drains it each tick, so two morphed characters use the supply twice as fast. When
# it runs out every morphed character reverts; when the last one reverts, the supply
# keeps the unused share as in vanilla. After battle every party member with the
# Morph command adds to the supply, so two Morph users also build it twice as fast.

MORPH_STATUS = 0x3ef9       # status byte 4: morph is bit 3
MORPH_BIT = 0x08
MORPH_TIMER = 0x3ee2        # vanilla: morphed entity; here: $ff = timer not running
MORPH_GAUGE = 0x3f30
COMMAND_QUEUE = 0x3a7a      # command to queue (C2/4EB2)
REVERT = 0x04
MORPH = 0x03
PARTY_LAST = 0x06           # party entities are 0, 2, 4, 6

def tick_mod():
    # battle loop, per entity x (a8, xy8): drain the gauge for every morphed party member
    src = [
        asm.LDA(MORPH_TIMER, asm.ABS),
        asm.BMI("RETURN"),                  # timer not running
        asm.CPX(PARTY_LAST + 2, asm.IMM8),
        asm.BGE("RETURN"),                  # party members only
        asm.LDA(MORPH_STATUS, asm.ABS_X),
        asm.AND(MORPH_BIT, asm.IMM8),
        asm.BEQ("RETURN"),                  # not morphed
        asm.JMP(0x1211, asm.ABS),           # drain the gauge, show it as this entity's
        "RETURN",
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "morph: tick the shared gauge for every morphed character")
    tick = space.start_address

    # C2/1143: CPX $3ee2, BNE, JSR $1211 (only the one morphed entity)
    space = Reserve(0x21143, 0x2114a, "morph: tick every morphed character", asm.NOP())
    space.write(
        asm.JSR(tick, asm.ABS),
    )

def timeout_mod():
    # gauge ran out (C2/1221: supply emptied, timer stopped): every morphed party member reverts
    src = [
        asm.PHX(),
        asm.LDX(PARTY_LAST, asm.IMM8),
        "LOOP",
        asm.LDA(MORPH_STATUS, asm.ABS_X),
        asm.AND(MORPH_BIT, asm.IMM8),
        asm.BEQ("NEXT"),
        asm.LDA(REVERT, asm.IMM8),
        asm.STA(COMMAND_QUEUE, asm.ABS),
        asm.JSR(0x4eb2, asm.ABS),           # queue revert for entity x
        "NEXT",
        asm.DEX(),
        asm.DEX(),
        asm.BPL("LOOP"),
        asm.PLX(),
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "morph: revert every morphed character when the gauge runs out")
    revert_all = space.start_address

    # C2/122C: LDA #$04, STA $3a7a, JSR $4eb2 (revert the one morphed entity)
    space = Reserve(0x2122c, 0x21233, "morph: revert every morphed character", asm.NOP())
    space.write(
        asm.JSR(revert_all, asm.ABS),
    )

def release_mod():
    # morph ended for entity x (a8, xy8; its status bit is already clear): stop the timer
    # only if nobody else is still morphed
    src = [
        asm.LDY(PARTY_LAST, asm.IMM8),
        "LOOP",
        asm.LDA(MORPH_STATUS, asm.ABS_Y),
        asm.AND(MORPH_BIT, asm.IMM8),
        asm.BNE("RETURN"),                  # someone else keeps the timer running
        asm.DEY(),
        asm.DEY(),
        asm.BPL("LOOP"),

        asm.JSR(0x0b36, asm.ABS),           # vanilla: supply keeps the unused share
        asm.LDA(0xff, asm.IMM8),
        asm.STA(MORPH_TIMER, asm.ABS),      # timer stopped
        asm.A16(),
        asm.STZ(MORPH_GAUGE, asm.ABS),
        asm.A8(),
        "RETURN",
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "morph: stop the shared timer when the last character reverts")
    release = space.start_address

    # C2/0AE8: JSR $0b36, LDA #$ff, STA $3ee2 (always stop the timer)
    space = Reserve(0x20ae8, 0x20aef, "morph: stop the timer only for the last morphed character", asm.NOP())
    space.write(
        asm.JSR(release, asm.ABS),
    )
    # C2/0AFA: REP #$20, STZ $3f30 (now in release, only for the last one)
    space = Reserve(0x20afa, 0x20afe, "morph: gauge cleared by release", asm.NOP())

def phase_flag_mod():
    # battle start and phase transitions (C2/2457 loop, a = flags, a8 xy8): vanilla marks
    # the morphed entity in $3204,x (bit 1); mark every morphed party member
    src = [
        asm.PHA(),
        asm.LDA(MORPH_TIMER, asm.ABS),
        asm.BMI("PLAIN"),
        asm.CPX(PARTY_LAST + 2, asm.IMM8),
        asm.BGE("PLAIN"),
        asm.LDA(MORPH_STATUS, asm.ABS_X),
        asm.AND(MORPH_BIT, asm.IMM8),
        asm.BEQ("PLAIN"),
        asm.PLA(),
        asm.ORA(0x02, asm.IMM8),
        asm.RTS(),
        "PLAIN",
        asm.PLA(),
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "morph: flag every morphed character")
    phase_flag = space.start_address

    # C2/2461: CPX $3ee2, BNE, ORA #$02
    space = Reserve(0x22461, 0x22467, "morph: flag every morphed character", asm.NOP())
    space.write(
        asm.JSR(phase_flag, asm.ABS),
    )

def supply_mod():
    # after battle, per party slot y (a8, xy16): z set if the character has the Morph command
    # (its save record's four commands, $1616-$1619 + record offset $3010,y)
    src = [
        asm.LDX(0x3010, asm.ABS_Y),
        asm.LDA(0x1616, asm.ABS_X),
        asm.CMP(MORPH, asm.IMM8),
        asm.BEQ("RETURN"),
        asm.LDA(0x1617, asm.ABS_X),
        asm.CMP(MORPH, asm.IMM8),
        asm.BEQ("RETURN"),
        asm.LDA(0x1618, asm.ABS_X),
        asm.CMP(MORPH, asm.IMM8),
        asm.BEQ("RETURN"),
        asm.LDA(0x1619, asm.ABS_X),
        asm.CMP(MORPH, asm.IMM8),
        "RETURN",
        asm.RTL(),
    ]
    space = Write(Bank.F0, src, "morph: does this party member have the morph command")
    has_morph = space.start_address_snes

    # C2/5E2F: LDA $3ed8,y, CMP #$00, BNE $5e49 (only character 0, or the one id
    # data/characters_asm used to patch in); the add below (C2/5E36, and the
    # -mmprp divide at C2/5E3F) now runs for every party member with Morph
    space = Reserve(0x25e2f, 0x25e35, "morph: every party member with morph builds the supply", asm.NOP())
    space.write(
        asm.JSL(has_morph),
        asm.BNE(0x5e49 - 0x5e35),           # no morph: skip the add (BNE $5e49)
    )

def mod():
    tick_mod()
    timeout_mod()
    release_mod()
    phase_flag_mod()
    supply_mod()

mod()
