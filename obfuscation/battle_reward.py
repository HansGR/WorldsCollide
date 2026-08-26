"""In-battle reward rendering for race roms (the Veldt check).

The Veldt grants its reward mid-battle, and battle event scripts have no
conditionals: the dialog id shown when the wild character/esper carrier
is fed Dried Meat is baked into battle event $0d, so character and esper
builds bake different dialogs ("Uwaoo~!!" vs "Received the Magicite
...") - a kind oracle in a race rom.  Race builds bake ONE dialog whose
text is only two new battle-text substitution codes and render the
kind-appropriate lines from the masked reward table at runtime:

    <battle reward>    line 1: "      Received the Magicite"  (esper)
                               "Uwaoo~!!"                     (character)
    <battle reward2>   line 2: "              <esper name>."  (esper)
                               nothing                        (character)

so each kind displays exactly what its non-unified build displays today.

Battle text code $12 is the engine's substitution opcode: C1/5EE6
fetches an operand byte, doubles it into X and dispatches through the
pointer table at C1/5EF0 (0 actor, 1 item, 2 attack, 3 command).  The
eight bytes after those four pointers (C1/5EF8) are DATA - the wram
name-buffer pointers the actor handler reads via `LDA $C15EF8,X` - so
operands 4+ dispatch into data today.  We relocate the eight data bytes
into our claim, repoint the actor handler's long operand at the copy,
and turn C1/5EF8-5EFB into table entries for sub-codes 4 and 5.

The table dispatch is a plain JMP and the renderer's helpers return with
RTS, so the entry points and the helper calls must execute in bank C1 -
but C1's heap is tiny.  Following the same pattern WC itself uses to
make room in C1 (color_absolute_* in instruction/c1.py), only four
2-instruction stubs live in C1 - two JMLs into the real handlers and two
JSL-able wrappers around the renderer helpers ($6111 prints the glyph in
A, $5FEF prints an esper's name from A = id + $36) - and the handlers
live in bank F0, returning through `JML $C15EE5` (an RTS) so the program
bank is C1 again when the engine's return address is popped.

Entry state, per the vanilla dispatch at C1/5EED: A 8-bit, X/Y 16-bit,
B = 0, DBR = $7E (so absolute data addresses below reference $7Exxxx).
"""

import instruction.asm as asm
from memory.space import Bank, Allocate, Reserve, Write, Read, START_ADDRESS_SNES
from data.text import get_bytes, TEXT3

# bank C1 battle text renderer addresses
GLYPH_OUT = 0x6111          # render one glyph, a = text3 byte, preserves x
ESPER_NAME_OUT = 0x5fef     # render an esper's name, a = esper id + $36
NEAREST_RTS = 0xc15ee5      # any RTS in bank C1 returns to the text loop
COUNTER = 0x616d            # the renderer's remaining-length scratch

ACTOR_PTRS_START = 0x15ef8  # the four wram name-buffer pointers (data)
ACTOR_PTRS_END = 0x15eff
TABLE_ENTRY_4 = 0x15ef8     # where sub-code 4/5 pointers go after relocation
TABLE_ENTRY_5_END = 0x15efb
ACTOR_OPERAND = 0x15f48     # long operand of the actor handler's LDA $C15EF8,X

def _text3(string):
    return [value for value in get_bytes(string, TEXT3) if value is not None]

def decode_src(args, slot, field):
    """asm loading one unmasked byte of the reward slot (0 id, 1 kind)."""
    from obfuscation import claim
    layout = claim.layout(args)
    table = claim.snes(layout["rewards"]) + slot * 2
    pad = claim.snes(layout["rewards_pad"]) + slot * 2
    return [asm.LDA(table + field, asm.LNG),
            asm.EOR(pad + field, asm.LNG)]

def install(args, slot):
    """Hook battle text sub-codes 4 and 5 up to renderers for the
    reward in the given slot."""

    line1_esper = _text3("      Received the Magicite")
    line1_char = _text3("Uwaoo~!!")
    line2_esper = _text3("              “")
    line2_close = _text3('."')

    # the C1-resident stubs: two renderer wrappers now, the two handler
    # entry points once the handlers below have addresses
    c1_stubs = Allocate(Bank.C1, 16, "battle reward c1 stubs", asm.NOP())
    glyph_stub = c1_stubs.next_address
    c1_stubs.write(
        asm.JSR(GLYPH_OUT, asm.ABS),
        asm.RTL(),
    )
    esper_name_stub = c1_stubs.next_address
    c1_stubs.write(
        asm.JSR(ESPER_NAME_OUT, asm.ABS),
        asm.RTL(),
    )

    # the relocated actor-name buffer pointers and our glyph strings
    actor_ptrs = Read(ACTOR_PTRS_START, ACTOR_PTRS_END)
    data_space = Write(Bank.F0, [
        actor_ptrs, line1_esper, line1_char, line2_esper, line2_close,
    ], "battle reward actor ptrs + glyph strings")
    data_address = data_space.start_address
    constants_snes = START_ADDRESS_SNES + data_address + len(actor_ptrs)

    offset_line1_esper = 0
    offset_line1_char = len(line1_esper)
    offset_line2_esper = offset_line1_char + len(line1_char)
    offset_line2_close = offset_line2_esper + len(line2_esper)

    # a = glyph count, x = offset into the strings above
    print_space = Write(Bank.F0, [
        asm.STA(COUNTER, asm.ABS),
        "PRINT_LOOP",
        asm.LDA(constants_snes, asm.LNG_X),
        asm.JSL(START_ADDRESS_SNES + glyph_stub),
        asm.INX(),
        asm.DEC(COUNTER, asm.ABS),
        asm.BNE("PRINT_LOOP"),
        asm.RTS(),
    ], "battle reward glyph string printer")
    print_address = print_space.start_address & 0xffff

    # sub-code 4, <battle reward>: the dialog's first line
    sub4_space = Write(Bank.F0, [
        *decode_src(args, slot, 1),                # a = reward kind
        asm.CMP(0x01, asm.IMM8),
        asm.BEQ("LINE1_ESPER"),
        asm.CMP(0x02, asm.IMM8),
        asm.BNE("LINE1_DONE"),                      # no item rewards here
        asm.LDX(offset_line1_char, asm.IMM16),
        asm.LDA(len(line1_char), asm.IMM8),
        asm.JSR(print_address, asm.ABS),
        asm.BRA("LINE1_DONE"),
        "LINE1_ESPER",
        asm.LDX(offset_line1_esper, asm.IMM16),
        asm.LDA(len(line1_esper), asm.IMM8),
        asm.JSR(print_address, asm.ABS),
        "LINE1_DONE",
        asm.JMP(NEAREST_RTS, asm.LNG),              # back to bank c1
    ], "battle reward sub-code 4 handler")

    # sub-code 5, <battle reward2>: the dialog's second line
    sub5_space = Write(Bank.F0, [
        *decode_src(args, slot, 1),                # a = reward kind
        asm.CMP(0x01, asm.IMM8),
        asm.BNE("LINE2_DONE"),                      # only espers print here
        asm.LDX(offset_line2_esper, asm.IMM16),
        asm.LDA(len(line2_esper), asm.IMM8),
        asm.JSR(print_address, asm.ABS),
        *decode_src(args, slot, 0),                # a = esper id
        asm.CLC(),
        asm.ADC(0x36, asm.IMM8),
        asm.JSL(START_ADDRESS_SNES + esper_name_stub),
        asm.LDX(offset_line2_close, asm.IMM16),
        asm.LDA(len(line2_close), asm.IMM8),
        asm.JSR(print_address, asm.ABS),
        "LINE2_DONE",
        asm.JMP(NEAREST_RTS, asm.LNG),              # back to bank c1
    ], "battle reward sub-code 5 handler")

    sub4_stub = c1_stubs.next_address & 0xffff
    c1_stubs.write(
        asm.JMP(START_ADDRESS_SNES + sub4_space.start_address, asm.LNG),
    )
    sub5_stub = c1_stubs.next_address & 0xffff
    c1_stubs.write(
        asm.JMP(START_ADDRESS_SNES + sub5_space.start_address, asm.LNG),
    )

    table_space = Reserve(TABLE_ENTRY_4, TABLE_ENTRY_5_END,
                          "battle text sub-code 4/5 pointers")
    table_space.write(
        sub4_stub & 0xff, sub4_stub >> 8,
        sub5_stub & 0xff, sub5_stub >> 8,
    )

    data_snes = START_ADDRESS_SNES + data_address
    operand_space = Reserve(ACTOR_OPERAND, ACTOR_OPERAND + 2,
                            "battle text actor name pointers relocated")
    operand_space.write(
        data_snes & 0xff, (data_snes >> 8) & 0xff, data_snes >> 16,
    )
