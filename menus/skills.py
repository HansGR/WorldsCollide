from memory.space import Bank, Reserve, Write
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
# This rewrite keeps every row keyed to its command, then adds two overrides
# in a helper (the in-place region stays the vanilla 59 bytes; the command
# scan indexes the table from its second entry and stores to $7A,X so the
# Espers row is never command-enabled):
# - ESPERS row: enabled by character id alone -- ids below Gogo (0x0C);
#   greyed for Gogo/Umaro and any special record above them.
# - MAGIC row: also enabled when the character KNOWS at least one spell
#   (a $FF in their 54-byte spell-mastery list at $1A6E + 54*id), so a
#   character without the Magic battle command can still cast known magic
#   out of battle (same union rule the battle engine uses for keeping MP
#   live -- see battle/keep_battle_mp.py). Command-based enabling is kept,
#   so a Magic-command character with no spells yet keeps the (empty)
#   submenu, and Gogo's vanilla command-configured Magic still works.
#   Gogo/Umaro take neither override: they have no spell-mastery table.


class SkillsMenu:
    def __init__(self):
        self.row_enable_mod()

    def row_enable_mod(self):
        ROW_TABLE_MAGIC_ONWARD = 0xc34d79   # vanilla row table at C3/4D78, minus the espers entry
        GOGO = 0x0c                         # gogo 0x0c, umaro 0x0d, moogles/specials above
        SPELL_MASTERY = 0x1a6e              # 54 bytes per character (ids 0-11), $ff = learned
        SPELL_COUNT = 0x36

        # espers-by-id + magic-by-knowledge overrides, applied after the
        # command scan. On entry y = character record base; clobbers a/x/y
        # (nothing after the JSR needs them).
        src = [
            asm.LDA(0x0000, asm.ABS_Y),     # a = character id
            asm.CMP(GOGO, asm.IMM8),
            asm.BCS("RETURN"),              # gogo/umaro/specials: command scan only
            asm.PHA(),
            asm.LDA(0x20, asm.IMM8),
            asm.STA(0x79, asm.DIR),         # real characters: espers always enabled
            asm.PLA(),

            asm.STA(0x4202, asm.ABS),       # spell list offset = id * 54,
            asm.LDA(SPELL_COUNT, asm.IMM8), # via the hardware multiplier
            asm.STA(0x4203, asm.ABS),       # (same recipe as vanilla C3/0D45)
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),                      # wait out the multiply
            asm.LDY(0x0036, asm.IMM16),     # 54 spells to check
            asm.LDX(0x4216, asm.ABS),       # x = id * 54
            "SPELL_LOOP",
            asm.LDA(SPELL_MASTERY, asm.ABS_X),
            asm.CMP(0xff, asm.IMM8),        # spell fully learned?
            asm.BEQ("KNOWS_MAGIC"),
            asm.INX(),
            asm.DEY(),
            asm.BNE("SPELL_LOOP"),
            asm.RTS(),                      # no spells known: magic row as the command scan left it

            "KNOWS_MAGIC",
            asm.LDA(0x20, asm.IMM8),
            asm.STA(0x7a, asm.DIR),         # knows a spell: enable magic row
            "RETURN",
            asm.RTS(),
        ]
        overrides = Write(Bank.C3, src, "skills menu row enable: espers by id, magic by known spells")

        space = Reserve(0x34d3d, 0x34d77, "skills menu row enable: command scan + overrides")
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

            asm.PLY(),                      # y = character record base again
            asm.JSR(overrides.start_address, asm.ABS),
            asm.RTS(),
        )
