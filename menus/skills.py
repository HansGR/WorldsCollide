from memory.space import Reserve
import instruction.asm as asm

# The Skills submenu (main menu -> Skills -> character) enables its seven rows
# per character in a routine at C3/4D3D: every row starts greyed ($24 at
# $79-$7F), then each of the character's four command bytes is compared against
# a per-row command-id table at C3/4D78 (02 02 07 0A 0C 10 13) and a match
# enables the row ($20). The row byte is both the draw color and the selection
# gate (C3/208B: LDA $79,X : CMP #$20 : BNE deny).
#
# Vanilla keys the ESPERS row (index 0) to the Magic command id (02) -- the
# same test as the Magic row -- with one extra rule greying it for Gogo. With
# randomized commands a character can be esper-capable yet lack the Magic
# command, which wrongly locks them out of equipping espers (level-up stat
# bonuses, spell learning, out-of-battle casting).
#
# This rewrite keeps every other row keyed to its command, but enables the
# Espers row by character id alone: enabled for ids below Gogo (0x0C), greyed
# for Gogo/Umaro and any special record above them. Byte-for-byte the same 59
# bytes, rewritten in place: the command scan indexes the table from its second
# entry and stores to $7A,X (rows 1-6), freeing the tail for the id check.


class SkillsMenu:
    def __init__(self):
        self.espers_row_mod()

    def espers_row_mod(self):
        ROW_TABLE_MAGIC_ONWARD = 0xc34d79   # vanilla row table at C3/4D78, minus the espers entry
        GOGO = 0x0c                         # gogo 0x0c, umaro 0x0d, moogles/specials above

        space = Reserve(0x34d3d, 0x34d77, "skills menu row enable: espers row by character id")
        space.write(
            asm.LDA(0x24, asm.IMM8),        # a = greyed
            asm.LDX(0x00, asm.DIR),         # x = 0 ($00 holds zero here, as vanilla relies on)
            "GREY_LOOP",
            asm.STA(0x79, asm.DIR_X),
            asm.INX(),
            asm.CPX(0x0007, asm.IMM16),
            asm.BNE("GREY_LOOP"),           # grey all seven rows

            asm.JSR(0x4edd, asm.ABS),       # y = character record base
            asm.PHY(),
            asm.LDX(0x0004, asm.IMM16),     # four command slots
            "COMMAND_LOOP",
            asm.PHX(),
            asm.LDX(0x00, asm.DIR),         # x = 0: row table index (row 1 = Magic)
            "ROW_LOOP",
            asm.LDA(0x0016, asm.ABS_Y),     # a = character's command byte
            asm.CMP(ROW_TABLE_MAGIC_ONWARD, asm.LNG_X),
            asm.BNE("NEXT_ROW"),
            asm.LDA(0x20, asm.IMM8),
            asm.STA(0x7a, asm.DIR_X),       # enable matching row (magic..dance)
            "NEXT_ROW",
            asm.INX(),
            asm.CPX(0x0006, asm.IMM16),
            asm.BNE("ROW_LOOP"),
            asm.INY(),                      # next command byte
            asm.PLX(),
            asm.DEX(),
            asm.BNE("COMMAND_LOOP"),

            asm.PLY(),
            asm.LDA(0x0000, asm.ABS_Y),     # a = character id
            asm.CMP(GOGO, asm.IMM8),
            asm.BCS("RETURN"),              # gogo/umaro/specials: espers stays greyed
            asm.LDA(0x20, asm.IMM8),
            asm.STA(0x79, asm.DIR),         # everyone else: espers always enabled
            "RETURN",
            asm.RTS(),
        )
