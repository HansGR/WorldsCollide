from memory.space import Bank, Reserve, Write
import instruction.asm as asm

# With probability-randomized commands (-comfr/-compr) a character's whole
# menu can be commands that are illegal while Imped (only Fight, Item,
# Magic, Revert, Mimic, Row, Def, Jump, X-Magic, Health and Shock carry the
# imp-usable bit in the CF/FE00 command info table).  The per-turn menu
# routine C2/527D then grays all four slots (bit 7 of each slot's second
# byte at the character's menu block, $202E/$203A/$2046/$2052), and the C1
# battle menu - which assumes at least one selectable slot, an invariant
# vanilla always meets because Fight and Item are ever-present and
# imp-legal - never places the hand cursor: the menu draws, the ATB stalls
# and the battle hard-locks on that character's turn.  The same all-grayed
# state is reachable without Imp (e.g. a menu of only Runic/SwdTech with a
# weapon supporting neither, plus Morph with an empty gauge).
#
# Restore the invariant at the source instead of patching the C1 cursor:
# after C2/527D's gray-out loop, if no non-empty slot is selectable,
# un-gray the FIRST non-empty slot.  The hand then lands on it normally
# and the player can act (using a nominally imp-illegal command while
# Imped - the alternative is the hard-lock).  Empty ($FF) slots are left
# alone: vanilla menus with empties (e.g. MagiTek) rely on them staying
# unselectable.

def mod():
    import args
    if not args.commands_probability_mode:
        return

    MENU_TABLE = 0xc2544a   # per-screen-slot menu block addresses (16-bit)

    # x <- this character's menu block.  C2/527D's entry pushes are still on
    # the stack under our JSR return address ($03,S = P, $04-$05,S = the
    # party screen slot 0/2/4/6).  DB is $7E in battle, so absolute
    # addressing reaches the menu blocks; the ROM table needs long indexing.
    src = [
        asm.TDC(),
        asm.LDA(0x04, asm.S),           # party screen slot (0/2/4/6)
        asm.TAX(),
        asm.REP(0x20),
        asm.LDA(MENU_TABLE, asm.LNG_X), # this character's menu block
        asm.TAX(),
        asm.SEP(0x20),
        asm.RTS(),
    ]
    menu_base = Write(Bank.C2, src, "battle menu guard: menu block lookup")

    # jumped to (not called) from C2/527D's epilogue: a is 8-bit, x/y are
    # 16-bit, and the epilogue's PLP/PLX/RTS is displaced to the end here.
    src = [
        asm.JSR(menu_base.start_address, asm.ABS),
        asm.LDY(0x0004, asm.IMM16),     # four menu slots
        "SCAN",
        asm.LDA(0x0000, asm.ABS_X),     # slot command id (bit 7 = empty)
        asm.BMI("SCAN_NEXT"),
        asm.LDA(0x0001, asm.ABS_X),     # bit 7 set = grayed out
        asm.BPL("DONE"),                # something is selectable: leave it be
        "SCAN_NEXT",
        asm.INX(),
        asm.INX(),
        asm.INX(),
        asm.DEY(),
        asm.BNE("SCAN"),

        # nothing selectable: un-gray the first non-empty slot
        asm.JSR(menu_base.start_address, asm.ABS),
        asm.LDY(0x0004, asm.IMM16),
        "FIX",
        asm.LDA(0x0000, asm.ABS_X),
        asm.BMI("FIX_NEXT"),
        asm.LDA(0x0001, asm.ABS_X),
        asm.AND(0x7f, asm.IMM8),
        asm.STA(0x0001, asm.ABS_X),     # clear the disabled bit
        asm.BRA("DONE"),
        "FIX_NEXT",
        asm.INX(),
        asm.INX(),
        asm.INX(),
        asm.DEY(),
        asm.BNE("FIX"),                 # all four empty: nothing we can do

        "DONE",
        asm.PLP(),                      # displaced C2/527D epilogue
        asm.PLX(),
        asm.RTS(),
    ]
    guard = Write(Bank.C2, src, "battle menu guard: keep one selectable command slot")

    space = Reserve(0x252e6, 0x252e8, "battle menu gray-out epilogue -> guard")
    space.write(
        asm.JMP(guard.start_address, asm.ABS),
    )

mod()
