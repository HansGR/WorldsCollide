from memory.space import Bank, Reserve, Allocate, Free, Write, Read, START_ADDRESS_SNES
import instruction.asm as asm
import args

# replace vanilla commands with calls to extracted functions
def _extract_original(original_start, original_end):
    space = Allocate(Bank.C0, original_end - original_start + 1, "extracted c0 command")
    new_address = space.start_address

    original_exit_length = 5
    original_exit_start = original_end - original_exit_length + 1

    # extract function contents except for exit and add return
    space.copy_from(original_start, original_exit_start - 1)
    space.write(
        asm.RTS(),
    )

    # call extracted function from original command
    call_length = 3
    new_end = original_start + call_length + original_exit_length - 1
    space = Reserve(original_start, new_end, "original c0 command replacement")
    space.write(
        asm.JSR(new_address, asm.ABS),
    )

    # copy original command exit
    space.copy_from(original_exit_start, original_end)

    # free remaining space
    Free(space.next_address, original_end)

    return new_address

# 0xbafc = 0x01, 0xbafd = 0x02, 0xbafe = 0x04, 0xbaff = 0x08, ..., 0xbb03 = 0x80
power_of_two_table = 0xbafc + START_ADDRESS_SNES

def _multiply_mod():
    # 16 bit a = low a * high a
    data = Read(0x24781, 0x24791) # multiply function
    space = Write(Bank.C0, data, "c0 multiply a = low a * high a")
    return space.start_address
multiply = _multiply_mod()

def _divide_mod():
    # 16-bit a = 16-bit a / 8-bit x
    #  8-bit x = 16-bit a % 8-bit x
    data = Read(0x24792, 0x247b6) # divide function
    space = Write(Bank.C0, data, "c0 divide 16-bit a / 8-bit x")
    return space.start_address
divide = _divide_mod()

def _rng_mod():
    # a = random number (0 to 255)
    return 0x062e
rng = _rng_mod()

def _rng_a_mod():
    # a = random number (0 to a register - 1)
    src = [
        asm.PHX(),
        asm.PHP(),

        asm.AXY8(),
        asm.XBA(),
        asm.PHA(),

        asm.JSR(rng, asm.ABS),
        asm.JSR(multiply, asm.ABS),

        asm.PLA(),
        asm.XBA(),
        asm.PLP(),
        asm.PLX(),
        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0 rng_a (0 to a - 1)")
    return space.start_address
rng_a = _rng_a_mod()

def _set_palette_mod():
    # assign palette $eb to object $ec
    return _extract_original(0x9ca9, 0x9cc9)
set_palette = _set_palette_mod()

def _set_sprite_mod():
    # assign sprite $eb to object $ec
    return _extract_original(0x9c8f, 0x9ca8)
set_sprite = _set_sprite_mod()

def _set_vehicle_mod():
    return _extract_original(0x9cca, 0x9ce1)
set_vehicle = _set_vehicle_mod()

def _random_sprite_palette_mod():
    # apply random sprite/palette to object $eb
    src = [
        asm.LDA(6, asm.IMM8),       # a = max palette + 1
        asm.JSR(rng_a, asm.ABS),    # a = random number between 0 and a - 1
        asm.STA(0xec, asm.DIR),

        asm.JSR(set_palette, asm.ABS),

        asm.LDA(61, asm.IMM8),      # a = max sprite + 1
        asm.JSR(rng_a, asm.ABS),    # a = random number between 0 and a - 1
        asm.STA(0xec, asm.DIR),

        asm.JSR(set_sprite, asm.ABS),

        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0 random_sprite_palette")
    return space.start_address
random_sprite_palette = _random_sprite_palette_mod()

def _any_random_sprite_palette_mod():
    # apply random sprite/palette to object $eb (including glitchy sprites/palettes)
    src = [
        asm.LDA(6, asm.IMM8),       # a = max palette + 1
        asm.JSR(rng_a, asm.ABS),    # a = random number between 0 and a - 1
        asm.STA(0xec, asm.DIR),

        asm.JSR(set_palette, asm.ABS),

        asm.LDA(169, asm.IMM8),     # a = max sprite + 1 (168 = 1 beyond max sprite of 167)
        asm.JSR(rng_a, asm.ABS),    # a = random number between 0 and a - 1
        asm.STA(0xec, asm.DIR),

        asm.JSR(set_sprite, asm.ABS),

        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0 any_random_sprite_palette")
    return space.start_address
any_random_sprite_palette = _any_random_sprite_palette_mod()

def _show_object_mod():
    return _extract_original(0xa2fa, 0xa335)
show_object = _show_object_mod()

def _hide_object_mod():
    return _extract_original(0xa336, 0xa369)
hide_object = _hide_object_mod()

def _character_data_offset_mod():
    # input: $eb = character id
    # output: y = character data offset (character data address = y + 0x1600)
    return 0x09dad
character_data_offset = _character_data_offset_mod()

def _average_level_mod():
    # set character in $eb to average level of available characters
    src = [
        Read(0x9f32, 0x9f6c), # set character to average level
        # updating magic/skills now requires that the character has been recruited
        # but recruiting before performing level averaging will include the recruited character in the average
        # so skip copying update magic/skills call and expect users to call it separately later
        Read(0x9f70, 0x9f72), # update experience needed
        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0 average_level")
    average_level = space.start_address

    space = Reserve(0x9f32, 0x9f39, "original average level command replacement")
    space.write(
        asm.JSR(average_level, asm.ABS),
    )
    space.copy_from(0x9f73, 0x9f77) # exit

    # free remaining space
    Free(space.next_address, 0x9f77)

    # In ruination mode, the averaging subroutine at $9F78 loads character_available
    # ($1ede) to determine which characters to include. Away-party characters have
    # their available bit cleared, so only the current party's levels are counted.
    # Patch to use character_recruited ($1edc) so all recruited characters contribute.
    if args.ruination_mode is not None:
        space = Reserve(0x9f78, 0x9f7a, "average level: use recruited instead of available")
        space.write(
            asm.LDX(0x1edc, asm.ABS),
        )

    return average_level
average_level = _average_level_mod()

def _update_magic_skills_mod():
    # update magic/skills for character in $eb based on their current level
    # i.e. after a character's level is changed, call to learn magic/skills
    return 0xa17f
update_magic_skills = _update_magic_skills_mod()

def _esper_found_mod():
    # input: a = esper id
    # output: a = 1 if esper found, else a = 0
    src = [
        asm.PHX(),
        asm.PHY(),

        asm.JSR(0xbaed, asm.ABS),       # x = a mod 8 (bit), y = a // 8 (byte)
        asm.LDA(0x1a69, asm.ABS_Y),     # a = esper found byte
        asm.AND(power_of_two_table, asm.LNG_X), # & esper found bit
        asm.BNE("FOUND"),

        asm.LDA(0x00, asm.IMM8),        # return 0 in a register
        asm.BRA("ESPER_FOUND_RETURN"),

        "FOUND",
        asm.LDA(0x01, asm.IMM8),        # return 1 in a register

        "ESPER_FOUND_RETURN",
        asm.PLY(),
        asm.PLX(),
        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0 esper_found")
    return space.start_address
esper_found = _esper_found_mod()

def _recruit_character_mod():
    import data.event_word as event_word
    characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)

    space = Allocate(Bank.C0, 43, "c0 recruit_character")
    if args.start_average_level:
        # set level to average before recruiting character so new character not included in average
        space.write(
            asm.LDA(0xeb, asm.DIR),                 # a = character argument
            asm.JSR(average_level, asm.ABS),
        )
    space.write(
        asm.TDC(),
        asm.LDA(0xeb, asm.DIR),                     # a = character argument
        asm.JSR(0xbaed, asm.ABS),                   # x = a mod 8 (bit), y = a // 8 (byte)

        asm.LDA(0x1edc, asm.ABS_Y),                 # a = character recruited byte
        asm.ORA(power_of_two_table, asm.LNG_X),     # set character recruited bit
        asm.STA(0x1edc, asm.ABS_Y),                 # store result

        asm.LDA(0x1ede, asm.ABS_Y),                 # a = character available byte
        asm.ORA(power_of_two_table, asm.LNG_X),     # set character available bit
        asm.STA(0x1ede, asm.ABS_Y),                 # store result

        asm.INC(characters_available_address, asm.ABS),

        asm.LDA(0xeb, asm.DIR),                     # a = character argument
        asm.JSR(character_data_offset, asm.ABS),    # y = character data offset (+0x1600)
        asm.JSR(update_magic_skills, asm.ABS),      # update magic/skills based on character's level
        asm.RTL(),
    )
    return space.start_address
recruit_character = _recruit_character_mod()

def _character_recruited_mod():
    # input: a = character id
    # output: a = 1 if character recruited (in menus), else a = 0
    src = [
        asm.PHX(),
        asm.PHY(),

        asm.JSR(0xbaed, asm.ABS),       # x = a mod 8 (bit), y = a // 8 (byte)
        asm.LDA(0x1edc, asm.ABS_Y),     # a = character recruited byte
        asm.AND(power_of_two_table, asm.LNG_X), # & character recruited bit
        asm.BNE("RECRUITED"),

        asm.LDA(0x00, asm.IMM8),        # return 0 in a register
        asm.BRA("CHARACTER_RECRUITED_RETURN"),

        "RECRUITED",
        asm.LDA(0x01, asm.IMM8),        # return 1 in a register

        "CHARACTER_RECRUITED_RETURN",
        asm.PLY(),
        asm.PLX(),
        asm.RTL(),
    ]
    space = Write(Bank.C0, src, "c0 charcter_recruited")
    return space.start_address
character_recruited = _character_recruited_mod()

def _character_available_mod():
    # input: a = character id
    # output: a = 1 if character available, else a = 0
    src = [
        asm.PHX(),
        asm.PHY(),

        asm.JSR(0xbaed, asm.ABS),       # x = a mod 8 (bit), y = a // 8 (byte)
        asm.LDA(0x1ede, asm.ABS_Y),     # a = character recruited byte
        asm.AND(power_of_two_table, asm.LNG_X), # & character recruited bit
        asm.BNE("AVAILABLE"),

        asm.LDA(0x00, asm.IMM8),        # return 0 in a register
        asm.BRA("CHARACTER_AVAILABLE_RETURN"),

        "AVAILABLE",
        asm.LDA(0x01, asm.IMM8),        # return 1 in a register

        "CHARACTER_AVAILABLE_RETURN",
        asm.PLY(),
        asm.PLX(),
        asm.RTL(),
    ]
    space = Write(Bank.C0, src, "c0 character_available")
    return space.start_address
character_available = _character_available_mod()

def _is_skill_learner_mod():
    # input: a = character id, x = 16 bit offset to end of learners table + 1, y = size of learners table
    # output: a = 1 if character in skill learner table, else a = 0

    from memory.space import START_ADDRESS_SNES
    src = [
        "LEARNER_CHECK_LOOP_START",
        asm.CPY(0x0000, asm.IMM16),
        asm.BEQ("LEARNER_FALSE"),

        asm.DEX(),                      # decrement offset
        asm.DEY(),                      # decrement learners count
        asm.CMP(Bank.CF + START_ADDRESS_SNES, asm.LNG_X),
        asm.BEQ("LEARNER"),
        asm.BRA("LEARNER_CHECK_LOOP_START"),

        "LEARNER_FALSE",
        asm.LDA(0x00, asm.IMM8),        # return 0 in a register
        asm.BRA("IS_SKILL_LEARNER_RETURN"),

        "LEARNER",
        asm.LDA(0x01, asm.IMM8),        # return 1 in a register

        "IS_SKILL_LEARNER_RETURN",
        asm.RTS(),
    ]
    space = Write(Bank.C0, src, "c0, is_skill_learner")
    return space.start_address
is_skill_learner = _is_skill_learner_mod()

def _add_item_mod():
    # input: 16 bit a = item id

    src = [
        asm.STA(0x1a, asm.DIR),
        asm.JSR(0xacfc, asm.ABS),
        asm.RTL(),
    ]
    space = Write(Bank.C0, src, "c0 add item")
    return space.start_address
add_item = _add_item_mod()

def _y_party_switch_mod():
    """Patch Y-party switch to save/restore IN_WOR per-party and clear
    SAVE_ENABLED so the destination party cannot save/heal unless they
    are actually standing on a savepoint.

    Without the IN_WOR fix, switching parties via Y leaves IN_WOR at
    whatever the previous party set it to.  Maps shared between WoB/WoR
    (e.g. Zozo) then behave as if the party is in the wrong world.

    Without the SAVE_ENABLED fix, if one party is on a savepoint and
    the player presses Y, the second party inherits the save-enabled
    state and can heal/save from anywhere.

    Hook strategy — leave the original C0/6D77-6E87 completely intact:

      Entry hook at C0/6D71: replace STZ $0762 (3 bytes) with
        JSR save_in_wor.  save_in_wor does the original STZ $0762
        plus saves IN_WOR into the departing party's PARTY_N_IN_WOR.
        The existing BRA $6D77 at C0/6D74 is untouched.

      Exit hooks at C0/6E37 and C0/6E7B: replace the 10-byte
        LDA $1A6D / TAY / LDA $1FF3,Y / AND #$03 / STA $0744
        sequences (before the RTS) with JSR restore_and_exit.
        restore_and_exit restores IN_WOR from the new party's
        PARTY_N_IN_WOR, clears SAVE_ENABLED, then does the original
        facing-restore code.  Remaining bytes are NOP-filled so
        execution slides to the original RTS at C0/6E43 / C0/6E87.
    """
    import data.event_bit as event_bit

    current_party    = 0x1a6d
    in_wor_addr      = event_bit.address(event_bit.IN_WOR)          # $1E94
    in_wor_bit_mask  = 1 << event_bit.bit(event_bit.IN_WOR)        # 0x10 (bit 4)
    party_state_byte = event_bit.address(event_bit.PARTY_1_IN_WOR) # $1E9C
    save_addr_eb     = event_bit.address(event_bit.SAVE_ENABLED)   # $1EB7
    save_bit_mask    = 1 << event_bit.bit(event_bit.SAVE_ENABLED)  # 0x80 (bit 7)

    # --- Save routine: called at entry before the switch begins ---
    # Replaces original STZ $0762 at C0/6D71.
    # At this point $1A6D still holds the OLD party index.
    save_src = [
        asm.STZ(0x0762, asm.ABS),           # original instruction

        # Save IN_WOR → PARTY_N_IN_WOR for old party
        # Party index (1-3) + 3 = power_of_two index (4-6)
        asm.LDA(current_party, asm.ABS),
        asm.CLC(),
        asm.ADC(0x03, asm.IMM8),
        asm.TAX(),
        asm.LDA(in_wor_addr, asm.ABS),
        asm.AND(in_wor_bit_mask, asm.IMM8),
        asm.BNE("SET_OLD"),

        asm.LDA(power_of_two_table, asm.LNG_X),
        asm.TRB(party_state_byte, asm.ABS),
        asm.RTS(),

        "SET_OLD",
        asm.LDA(power_of_two_table, asm.LNG_X),
        asm.TSB(party_state_byte, asm.ABS),
        asm.RTS(),
    ]
    save_space = Write(Bank.C0, save_src, "c0 y-party switch save state")
    save_addr = save_space.start_address

    # --- Exit routine: restores IN_WOR then does original facing restore ---
    # Replaces the identical 10-byte sequences at C0/6E37-6E40 and C0/6E7B-6E84.
    # At this point $1A6D holds the NEW party index.
    exit_src = [
        # Restore IN_WOR from PARTY_N_IN_WOR for new party
        asm.LDA(current_party, asm.ABS),
        asm.CLC(),
        asm.ADC(0x03, asm.IMM8),
        asm.TAX(),
        asm.LDA(power_of_two_table, asm.LNG_X),
        asm.AND(party_state_byte, asm.ABS),
        asm.BEQ("CLEAR_WOR"),

        asm.LDA(in_wor_bit_mask, asm.IMM8),
        asm.TSB(in_wor_addr, asm.ABS),
        asm.BRA("CLEAR_SAVE"),

        "CLEAR_WOR",
        asm.LDA(in_wor_bit_mask, asm.IMM8),
        asm.TRB(in_wor_addr, asm.ABS),

        # Clear SAVE_ENABLED so new party can't save/heal from a remote savepoint
        "CLEAR_SAVE",
        asm.LDA(save_bit_mask, asm.IMM8),
        asm.TRB(save_addr_eb, asm.ABS),

        # Original exit: restore facing from saved party data
        "ORIG_EXIT",
        Read(0x6e37, 0x6e42),               # LDA $1A6D / TAY / LDA $1FF3,Y / AND #$03 / STA $0744
        asm.RTS(),
    ]
    exit_space = Write(Bank.C0, exit_src, "c0 y-party switch restore state + exit")
    exit_addr = exit_space.start_address

    # --- Hook entry: C0/6D71, replace STZ $0762 with JSR save_addr ---
    # BRA $6D77 at C0/6D74 is untouched.
    space = Reserve(0x6d71, 0x6d73, "y-party switch entry hook: save state")
    space.write(asm.JSR(save_addr, asm.ABS))

    # --- Hook exit 1 (same-map): C0/6E37-6E42, JSR + NOP sled to RTS at 6E43 ---
    space = Reserve(0x6e37, 0x6e42, "y-party switch same-map exit hook", asm.NOP())
    space.write(asm.JSR(exit_addr, asm.ABS))
    # Remaining 9 bytes (6E3A-6E42) are NOP-filled; RTS at 6E43 is untouched.
    # BEQ $6E43 at C0/6DD7 still hits the original RTS.

    # --- Hook exit 2 (different-map): C0/6E7B-6E86, JSR + NOP sled to RTS at 6E87 ---
    space = Reserve(0x6e7b, 0x6e86, "y-party switch diff-map exit hook", asm.NOP())
    space.write(asm.JSR(exit_addr, asm.ABS))
    # Remaining 9 bytes (6E7E-6E86) are NOP-filled; RTS at 6E87 is untouched.

if args.ruination_mode is not None:
    _y_party_switch_mod()
