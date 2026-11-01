from memory.space import Bank, Reserve, Write
import instruction.asm as asm
import instruction.c0 as c0
import data.event_bit as event_bit
import args

# -psu: Possess is single use -- the possessor is gone for good.
#
# Possess (special effect C2/3B98) gives the possessor Wound and Hide and flags it in
# $3a88; at battle end C2/4954 calls C2/47E3, which zeroes its $1850 party byte. The
# character stays available ($1ede) though, so the next party select (airship, Kefka's
# Tower, Phoenix Cave: CA/CBAF; WC's REFRESH_CHARACTERS_AND_SELECT_PARTY: CA/C90B) creates
# it again -- CA/CBAF even revives it -- and Possess is effectively rechargeable.
#
# Here every possessor also loses its available bit, so no party select can pick it again.
# The recruited bit ($1edc) and CHARACTERS_AVAILABLE are kept: objectives ("recruit N
# characters"), the progress menu and character gating (-cg) count recruited characters,
# so a possessor's checks stay open. Without Leap, "recruited but not available" means
# "possessed", which the rest of -psu relies on:
#   - the party-size gates that open a two or three party select (Narshe Battle, Phoenix
#     Cave, Kefka's Tower) count the available bits instead (instruction/field/available.py)
#   - the Phantom Train ghost and the Veldt reward character test the recruited bit, and
#     recruit_character (instruction/c0.py) ignores a character already recruited
#   - the airship unequip options strip recruited characters (event/airship.py)
#   - required characters (-rc) are only pre-placed when available
#     (instruction/field/required_characters.py)
#
# $3a88 is also set by BabaBreath (special effect $66, C2/3966), which blows a living
# character away (Hide, no Wound). Only a possessor is both wounded and hidden, so
# BabaBreath keeps the vanilla behaviour. Wrexsoul's Zinger uses $33f8/$33f9, not $3a88.

CHARACTER_COUNT = 14            # ids 0-13 have event bits; the Phantom Train ghosts ($10, $11) do not
CHARACTER_AVAILABLE = event_bit.address(event_bit.character_available(0))   # $1ede

def mod():
    if not args.possess_single_use:
        return

    src = [
        asm.JSR(0x47e3, asm.ABS),               # vanilla: out of the party ($1850)
        asm.LDA(0x3ee4, asm.ABS_X),             # status 1
        asm.BPL("RETURN"),                      # not wounded: not a possessor
        asm.LDA(0x3ef9, asm.ABS_X),             # status 4
        asm.AND(0x20, asm.IMM8),
        asm.BEQ("RETURN"),                      # not hidden: not a possessor
        asm.LDA(0x3ed8, asm.ABS_X),             # character id
        asm.CMP(CHARACTER_COUNT, asm.IMM8),
        asm.BGE("RETURN"),
        asm.PHX(),
        asm.TAY(),                              # y = id
        asm.AND(0x07, asm.IMM8),
        asm.TAX(),
        asm.LDA(c0.power_of_two_table, asm.LNG_X),
        asm.XOR(0xff, asm.IMM8),                # a = ~(1 << id % 8)
        asm.PHA(),
        asm.TYA(),
        asm.LSR(),
        asm.LSR(),
        asm.LSR(),
        asm.TAY(),                              # y = id / 8
        asm.PLA(),
        asm.AND(CHARACTER_AVAILABLE, asm.ABS_Y),
        asm.STA(CHARACTER_AVAILABLE, asm.ABS_Y),    # no longer available to any party select
        asm.PLX(),
        "RETURN",
        asm.RTS(),
    ]
    space = Write(Bank.C2, src, "possess: possessor is no longer available")
    leave = space.start_address

    # C2/4954: JSR $47e3 (party member flagged in $3a88, or a dead guest)
    space = Reserve(0x24954, 0x24956, "possess: call possessor leaves")
    space.write(
        asm.JSR(leave, asm.ABS),
    )

mod()
