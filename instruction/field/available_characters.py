# Count the characters a party select can offer right now.
#
# CHARACTERS_AVAILABLE is a count of recruited characters (objectives, the progress menu and
# the party-size gates read it). With -psu a possessor stays recruited but is no longer
# available, so a gate that opens a two or three party select must count the available bits
# instead: offering more parties than there are characters to fill them softlocks the select
# screen.
#
# Usage (event code):
#     field.LongCall(available_characters.count_address()),     # SCRATCH = available count
#     field.BranchIfEventWordLess(event_word.SCRATCH, n, "NOT_ENOUGH"),

import data.event_bit as event_bit
import data.event_word as event_word
import instruction.asm as asm
from constants.entities import CHARACTER_COUNT
from memory.space import Bank, Write

_count_address = None

def count_address():
    """24-bit address of a LongCall-able function: event word SCRATCH = number of characters
    whose available bit is set. Generated on first use."""
    global _count_address
    if _count_address is not None:
        return _count_address

    scratch = event_word.address(event_word.SCRATCH)
    src = [
        asm.PHP(),
        asm.SEP(0x20),
        asm.REP(0x10),
        asm.STZ(scratch, asm.ABS),
        asm.STZ(scratch + 1, asm.ABS),
        asm.LDA(event_bit.address(event_bit.character_available(0)), asm.ABS),
        asm.LDY(0x0008, asm.IMM16),
        "LOW",
        asm.ASL(),
        asm.BCC("LOW_NEXT"),
        asm.INC(scratch, asm.ABS),
        "LOW_NEXT",
        asm.DEY(),
        asm.BNE("LOW"),
        asm.LDA(event_bit.address(event_bit.character_available(8)), asm.ABS),
        asm.AND((1 << (CHARACTER_COUNT - 8)) - 1, asm.IMM8),
        asm.LDY(0x0008, asm.IMM16),
        "HIGH",
        asm.ASL(),
        asm.BCC("HIGH_NEXT"),
        asm.INC(scratch, asm.ABS),
        "HIGH_NEXT",
        asm.DEY(),
        asm.BNE("HIGH"),
        asm.PLP(),
        asm.RTL(),
    ]
    space = Write(Bank.F0, src, "count characters available to party select")
    _count_address = space.start_address_snes
    return _count_address

def party_size_word():
    """(instructions, event word) for a gate that opens a multi-party select: run the
    instructions, then compare the word with the number of parties. Without -psu this is
    CHARACTERS_AVAILABLE as before; with it, the live count of available characters."""
    import args
    if args.possess_single_use:
        import instruction.field as field
        return [field.LongCall(count_address())], event_word.SCRATCH
    return [], event_word.CHARACTERS_AVAILABLE
