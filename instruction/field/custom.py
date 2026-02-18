from memory.space import Bank, START_ADDRESS_SNES, Reserve, Write, Read
from instruction.event import _Instruction, _Branch
import instruction.asm as asm
import instruction.c0 as c0
from enum import IntEnum

def _set_opcode_address(opcode, address):
    FIRST_OPCODE = 0x35
    opcode_table_address = 0x098c4 + (opcode - FIRST_OPCODE) * 2
    space = Reserve(opcode_table_address, opcode_table_address + 1, "field opcode table, {opcode} {hex(address)}")
    space.write(
        (address & 0xffff).to_bytes(2, "little"),
    )

def _add_esper_increment():
    import data.event_word as event_word
    src = [
        asm.INC(event_word.address(event_word.ESPERS_FOUND), asm.ABS),
        Read(0xadd4, 0xadd6),   # advance event script
    ]
    space = Write(Bank.C0, src, "add esper command increment espers found event word")
    increment_found = space.start_address

    space = Reserve(0xadd4, 0xadd6, "add esper command jmp to increment event word", asm.NOP())
    space.write(asm.JMP(increment_found, asm.ABS))
_add_esper_increment()

class RemoveDeath(_Instruction):
    def __init__(self, character):
        import instruction.field as field
        from instruction.c0 import character_data_offset

        self.current_status = 0x1614 # character status effects address
        self.death_mask = field.Status.DEATH >> 8
        # add a special command specifically for removing death. 
        # This is used in special events (like Moogle Defense), where we want to revive even with permadeath
        # Code based on C0/AE2D - AE44 (gen. act. 88 to Remove status effects)
        src = [
            asm.JSR(character_data_offset, asm.ABS),
            asm.CPY(0x0250, asm.IMM16),
            asm.BCS("DONE"),
            asm.A16(),
            asm.LDA(self.current_status, asm.ABS_Y),
            asm.AND(~self.death_mask, asm.IMM16), # clear the DEATH bit
            asm.STA(self.current_status, asm.ABS_Y),
            asm.TDC(),
            asm.A8(),
            "DONE",
            asm.LDA(0x02, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom remove_death command")
        address = space.start_address

        opcode = 0x6f
        _set_opcode_address(opcode, address)

        RemoveDeath.__init__ = lambda self, character : super().__init__(opcode, character)
        self.__init__(character)

class SetEquipmentAndCommands(_Instruction):
    def __init__(self, to_character, from_character):
        from instruction.c0 import character_data_offset

        # subset of SetProperties vanilla command (0x40), which only sets equipment, commands, and character ID
        src = [
            #C0/A07C:	20AD9D  	JSR $9DAD		
            asm.JSR(character_data_offset, asm.ABS),
            # C0/A07F:	A916    	LDA #$16
            asm.LDA(0x16, asm.IMM8),
            # C0/A081:	8D0242  	STA $4202
            asm.STA(0x4202, asm.ABS),
            # C0/A084:	A5EC    	LDA $EC
            asm.LDA(0xEC, asm.DIR),
            # C0/A086:	8D0342  	STA $4203
            asm.STA(0x4203, asm.ABS),
            # C0/A089:	EA      	NOP
            asm.NOP(),
            # C0/A08A:	EA      	NOP
            asm.NOP(),
            # C0/A08B:	EA      	NOP
            asm.NOP(),
            # C0/A08C:	AE1642  	LDX $4216
            asm.LDX(0x4216, asm.ABS),
            # Commands
            # C0/A08F:	BFA27CED	LDA $ED7CA2,X	(command 1)
            asm.LDA(0xED7CA2, asm.LNG_X),
            # C0/A093:	991616  	STA $1616,Y
            asm.STA(0x1616, asm.ABS_Y),
            # C0/A096:	BFA37CED	LDA $ED7CA3,X	(command 2)
            asm.LDA(0xED7CA3, asm.LNG_X),
            # C0/A09A:	991716  	STA $1617,Y
            asm.STA(0x1617, asm.ABS_Y),
            # C0/A09D:	BFA47CED	LDA $ED7CA4,X	(command 3)
            asm.LDA(0xED7CA4, asm.LNG_X),
            # C0/A0A1:	991816  	STA $1618,Y
            asm.STA(0x1618, asm.ABS_Y),
            # C0/A0A4:	BFA57CED	LDA $ED7CA5,X	(command 4)
            asm.LDA(0xED7CA5, asm.LNG_X),
            # C0/A0A8:	991916  	STA $1619,Y
            asm.STA(0x1619, asm.ABS_Y),
            # Equipment
            # C0/A0CC:	BFAF7CED	LDA $ED7CAF,X	(R-hand)
            asm.LDA(0xED7CAF, asm.LNG_X),
            # C0/A0D0:	991F16  	STA $161F,Y
            asm.STA(0x161F, asm.ABS_Y),
            # C0/A0D3:	BFB07CED	LDA $ED7CB0,X	(L-hand)
            asm.LDA(0xED7CB0, asm.LNG_X),
            # C0/A0D7:	992016  	STA $1620,Y
            asm.STA(0x1620, asm.ABS_Y),
            # C0/A0DA:	BFB17CED	LDA $ED7CB1,X	(Body)
            asm.LDA(0xED7CB1, asm.LNG_X),
            # C0/A0DE:	992116  	STA $1621,Y
            asm.STA(0x1621, asm.ABS_Y),
            # C0/A0E1:	BFB27CED	LDA $ED7CB2,X	(Head)
            asm.LDA(0xED7CB2, asm.LNG_X),
            # C0/A0E5:	992216  	STA $1622,Y
            asm.STA(0x1622, asm.ABS_Y),
            # C0/A0E8:	BFB37CED	LDA $ED7CB3,X	(Relic 1)
            asm.LDA(0xED7CB3, asm.LNG_X),
            # C0/A0EC:	992316  	STA $1623,Y
            asm.STA(0x1623, asm.ABS_Y),
            # C0/A0EF:	BFB47CED	LDA $ED7CB4,X	(Relic 2)
            asm.LDA(0xED7CB4, asm.LNG_X),
            # C0/A0F3:	992416  	STA $1624,Y
            asm.STA(0x1624, asm.ABS_Y),

            # C0/A10D:	A5EC    	LDA $EC        (load parameter)
            asm.LDA(0xec, asm.DIR),
            # C0/A10F:	990016  	STA $1600,Y    (save character ID)
            asm.STA(0x1600, asm.ABS_Y),

            # C0/A17A:	A903    	LDA #$03
            asm.LDA(0x03, asm.IMM8),        # command size
            # C0/A17C:	4C5C9B  	JMP $9B5C
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom swap equipment and commands command")
        address = space.start_address

        opcode = 0xa3
        _set_opcode_address(opcode, address)

        SetEquipmentAndCommands.__init__ = lambda self, to_character, from_character : super().__init__(opcode, to_character, from_character)
        self.__init__(to_character, from_character)


class UpdateWorldReturnToParentMap(_Instruction):
    def __init__(self):
        # For Map Shuffle & door rando purposes
        # Custom command to: Read parent map, update world bit ($1E94 bit 4) to match parent map, return to parent map.
        fade_load_map = 0xab47
        load_map = 0xab55

        src = [
            asm.LDA(0x1f69, asm.ABS),           # a = low 8 bits of parent map (00 or 01)
            asm.CMP(0x00, asm.IMM8),            # compare if the map is 0x00 (WoB)
            asm.BEQ("GO_TO_WOB"),               # Branch to WoB code
            asm.LDA(0x1e94, asm.ABS),           # a = event bits incl. bit 4 (IS_WOR)
            asm.AND(0xEF, asm.IMM8),            # delete event bit (aaaxaaaa & 11101111 = aaa0aaaa)
            asm.CLC(),                          # Clear carry flag, otherwise the addition is off by one.
            asm.ADC(0x10, asm.IMM8),            # set event bit = 1 (aaa1aaaa) (WoR).
            asm.STA(0x1e94, asm.ABS),           # update event byte
            asm.JMP(load_map, asm.ABS),         # jump to original load map command
            "GO_TO_WOB",
            asm.LDA(0x1e94, asm.ABS),           # a = event bits incl. bit 4 (IS_WOR)
            asm.AND(0xEF, asm.IMM8),            # delete event bit (aaaxaaaa & 11101111 = aaa0aaaa)
            asm.STA(0x1e94, asm.ABS),           # update event byte
            asm.JMP(load_map, asm.ABS),         # jump to original load map command
        ]
        space = Write(Bank.C0, src, "custom return to parent map & update event bit IN_WOR")
        address = space.start_address

        opcode = 0x69
        _set_opcode_address(opcode, address)

        # basic return to parent map arguments
        # special map 0x1ff, return to parent map at same position/direction, not on airship
        args = [0xff, 0x21, 0x00, 0x00, 0x00]  # last bit: 0x80 run entrance event? this works (on non-world-map screens) - but character can't move!  all inputs are off.

        UpdateWorldReturnToParentMap.__init__ = lambda self : super().__init__(opcode, *args)
        self.__init__()


# class ToggleWorlds(_Instruction):
#     def __init__(self):
#         fade_load_map = 0xab47
#
#         src = [
#             asm.LDA(0x1f69, asm.ABS),           # a = low 8 bits of parent map
#             asm.XOR(1, asm.IMM8),               # toggle last bit of parent map id
#             asm.STA(0x1f69, asm.ABS),           # update parent map
#             asm.JMP(fade_load_map, asm.ABS),    # jump to original fade load map command
#         ]
#         space = Write(Bank.C0, src, "custom toggle worlds instruction")
#         address = space.start_address
#
#         opcode = 0x6d
#         _set_opcode_address(opcode, address)
#
#         # same args as airship lift-off load map
#         # special map 0x1ff, return to parent map at same position/direction
#         args = [0xff, 0x25, 0x00, 0x00, 0x81]  # map shuffle mod to run entrance event; final bit was 0x01
#
#         ToggleWorlds.__init__ = lambda self : super().__init__(opcode, *args)
#         self.__init__()


class SetParentWorld(_Instruction):
    def __init__(self, world):
        # Add a special command to set the parent map to a particular world.
        # This is used for event_bit.IN_WOR safety in door randomizer
        src = [
            # Load value of next script byte into A
            asm.A8(),
            asm.LDA(0xeb, asm.DIR),         # Load the next script byte (in direct page @ $EB)
                                            # now A = world
            # Update value of parent map lower bit
            asm.STA(0x1f69, asm.ABS),       # update low 8 bits of parent map
            # Cleanup & continue
            asm.LDA(0x02, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom set_parent_world command")
        address = space.start_address

        opcode = 0x6d
        _set_opcode_address(opcode, address)

        SetParentWorld.__init__ = lambda self, world : super().__init__(opcode, world)
        self.__init__(world)


class LoadEsperFound(_Instruction):
    def __init__(self, esper):
        import data.event_bit as event_bit
        result_byte = event_bit.address(event_bit.multipurpose(0))
        src = [
            asm.LDA(0xeb, asm.DIR),
            asm.JSR(c0.esper_found, asm.ABS),
            asm.STA(result_byte, asm.ABS),
            asm.LDA(0x02, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom load esper found instruction")
        address = space.start_address

        opcode = 0x83
        _set_opcode_address(opcode, address)

        LoadEsperFound.__init__ = lambda self, esper : super().__init__(opcode, esper)
        self.__init__(esper)

class LoadPartiesWithCharacters(_Instruction):
    ''' Sets bits 0-2 in event word when those parties have characters.'''
    def __init__(self):
        import data.event_bit as event_bit
        result_byte = event_bit.address(event_bit.multipurpose(0))
        src = [
            asm.STZ(result_byte, asm.ABS),
            asm.LDX(0x0000, asm.IMM16),
            "START_CHARACTER_LOOP",
            asm.LDA(0x1850, asm.ABS_X), # load the character data 
            asm.AND(0x47, asm.IMM8),    # isolate the enabled bit and party bits (note: there are 3 party bits, but we only use 2.)
            "CHECK_PARTY_1",
            asm.CMP(0x41, asm.IMM8),
            asm.BNE("CHECK_PARTY_2"),
            # character enabled and in party 1
            asm.LDA(result_byte, asm.ABS),
            asm.ORA(0x01, asm.IMM8), # set bit 0 in the result to indicate party 1 has an enabled character
            asm.STA(result_byte, asm.ABS),
            asm.BRA("NEXT_CHARACTER"),
            "CHECK_PARTY_2",
            asm.CMP(0x42, asm.IMM8),
            asm.BNE("CHECK_PARTY_3"),
            # character enabled and in party 2
            asm.LDA(result_byte, asm.ABS),
            asm.ORA(0x02, asm.IMM8), # set bit 1 in the result to indicate party 2 has an enabled character 
            asm.STA(result_byte, asm.ABS),
            asm.BRA("NEXT_CHARACTER"),
            "CHECK_PARTY_3",
            asm.CMP(0x43, asm.IMM8),
            asm.BNE("NEXT_CHARACTER"),
            # character enabled and in party 3
            asm.LDA(result_byte, asm.ABS),
            asm.ORA(0x04, asm.IMM8), # set bit 2 in the result to indicate party 3 has an enabled character
            asm.STA(result_byte, asm.ABS),
            # end of loop iteration -- increment X for another go
            "NEXT_CHARACTER",
            asm.INX(),
            asm.CPX(0x000f, asm.IMM16), # did we check all 16 characters?
            asm.BNE("START_CHARACTER_LOOP"), # if not, check the next one
            asm.LDA(0x01, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]

        space = Write(Bank.C0, src, "custom load parties with characters instruction")
        address = space.start_address

        opcode = 0xe5
        _set_opcode_address(opcode, address)

        LoadPartiesWithCharacters.__init__ = lambda self : super().__init__(opcode)
        self.__init__()

class RecruitCharacter(_Instruction):
    def __init__(self, character):
        recruit_character_function = START_ADDRESS_SNES + c0.recruit_character
        src = [
            asm.JSL(recruit_character_function),
            asm.LDA(0x02, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom recruit_character command")
        address = space.start_address

        opcode = 0x76
        _set_opcode_address(opcode, address)

        RecruitCharacter.__init__ = lambda self, character : super().__init__(opcode, character)
        self.__init__(character)

    def __str__(self):
        return super().__str__(self.args[0])

class _InvokeBattleType(_Instruction):
    # invoke battle with given type (front/back/pincer/side) regardless of formation settings
    def __init__(self, pack, battle_type, background):
        self.pack = pack
        self.battle_type = battle_type

        # i did not see anywhere in the event script using the sound flag and only 7 (removed)
        #   scenes using battle animation flag
        # this custom function replaces the battle sound/animation flags with battle type bits
        # front = 0, back = 1, pincer = 2, side = 3
        super().__init__(self.write(), pack - 0x100, background | (battle_type << 6))

    def __str__(self):
        return super().__str__(f"{str(self.pack)}, {str(self.battle_type)}")

    def write(self):
        src = [
            asm.A8(),
            asm.LDA(0xec, asm.DIR),         # a = type bits and background
            asm.AND(0xc0, asm.IMM8),        # a = battle type bits
            asm.ROL(),
            asm.ROL(),
            asm.ROL(),                      # shift type bits to the beginning of the byte
            asm.ORA(0x04, asm.IMM8),        # add 4 to indicate a battle type is given (even if type is zero)
            asm.TAY(),                      # y = battle type (y is unused by battle setup function)
            asm.LDA(0xc0, asm.IMM8),        # a = mask for sound/animation flags
            asm.TRB(0xec, asm.DIR),         # overwrite custom battle type bits with sound/animation true
            asm.JSR(0xa5a7, asm.ABS),       # battle setup (formation, background, music, transition animation)
            asm.TYA(),                      # a = battle type
            asm.STA(0x11e3, asm.ABS),       # store battle type in upper byte of battle background
            asm.JMP(0xa57b, asm.ABS),       # jmp to original invoke battle command code (after setup)
        ]
        space = Write(Bank.C0, src, "custom invoke_battle_type command")
        invoke_battle_type_address = space.start_address

        src = [
            asm.LDA(0x11e3, asm.ABS),       # a = battle type
            asm.CMP(0x00, asm.IMM8),        # compare to zero and set carry flag if a >= 0 (for sbc)
            asm.BEQ("LOAD_BATTLE_TYPE"),    # branch if battle type is zero
            asm.SBC(0x04, asm.IMM8),        # subtract 4 (the flag value i added)
            asm.STA(0x201f, asm.ABS),       # store battle type in correct battle ram location
            asm.LDA(0x00, asm.IMM8),
            asm.STA(0x11e3, asm.ABS),       # set upper byte of battle bg to 0 to prevent possible side-effects
            asm.RTS(),

            "LOAD_BATTLE_TYPE",
            Read(0x22e3a, 0x22e3c),
            asm.JMP(0x2e3d, asm.ABS),       # jmp back to normal battle type loading code
        ]
        space = Write(Bank.C2, src, "custom event instruction battle type check")
        battle_type_check = space.start_address

        space = Reserve(0x22e3a, 0x22e3c, "battle load relic effects 2", asm.NOP())
        space.write(
            asm.JMP(battle_type_check, asm.ABS),    # jmp to custom event instruction battle type check
        )

        opcode = 0x6e
        _set_opcode_address(opcode, invoke_battle_type_address)

        _InvokeBattleType.write = lambda self : opcode
        return self.write()

class BranchChance(_Branch):
    def __init__(self, chance, destination):
        self.chance = chance
        if chance > 255 or chance < 0:
            raise ValueError(f"branch_chance: invalid chance {chance}")
        elif chance <= 1:
            chance = int(chance * 255) # convert from decimal
        super().__init__(self.write(), [chance], destination)

    def __str__(self):
        return super().__str__(f"{self.chance:0.3}")

    def write(self):
        # after rng, jump inside event command 0xbd (50% branch command) to execute the result
        yes_branch = 0xb291
        no_branch = 0xb278

        src = [
            asm.JSR(c0.rng, asm.ABS),       # a = random number 0 to 255
            asm.CMP(0xeb, asm.DIR),         # compare to given chance
            asm.BLT("BRANCH"),              # if random number < chance

            # increment $e5 to account for branch_chance having 1 extra argument than 0xbd
            asm.INC(0xe5, asm.DIR),
            asm.JMP(no_branch, asm.ABS),

            "BRANCH",
            asm.LDX(0xec, asm.DIR),         # x = low bytes of destination
            asm.STX(0xe5, asm.DIR),
            asm.LDA(0xee, asm.DIR),         # a = high byte of destination
            asm.JMP(yes_branch, asm.ABS),
        ]
        space = Write(Bank.C0, src, "custom branch_chance command")
        address = space.start_address

        opcode = 0xa5
        _set_opcode_address(opcode, address)

        BranchChance.write = lambda self : opcode
        return self.write()

class LongCall(_Instruction):
    # call function outside of event code
    # input: 24 bit address of the function to call and an optional argument to call it with

    ARG_ADDRESS = 0xee
    def __init__(self, function_address, arg = 0):
        src = [
            asm.TDC(),
            asm.LDA(0x05, asm.IMM8),        # command size
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "custom long call return")
        return_address = space.start_address

        src = [
            # copy jsl behavior, bank/address will be popped from stack by rtl
            asm.PHK(),                              # push program bank register
            asm.A16(),
            asm.LDA(return_address - 1, asm.IMM16), # -1 because rtl pulls pc from stack and increments it
            asm.PHA(),                              # push address to return to

            # store 24 bit address to call, and jump to it
            asm.LDA(0xeb, asm.DIR),
            asm.STA(0x05f4, asm.ABS),               # 0x05f4 is same address field.Call uses in c0
            asm.A8(),
            asm.LDA(0xed, asm.DIR),
            asm.STA(0x05f6, asm.ABS),

            asm.JMP(0x05f4, asm.ABS_24),
        ]
        space = Write(Bank.C0, src, "custom long call")
        address = space.start_address

        opcode = 0x8f # overwrite learn all swdtech
        _set_opcode_address(opcode, address)

        LongCall.__init__ = (lambda self, function_address, arg = 0 :
                             super().__init__(opcode, function_address.to_bytes(3, "little"), arg))
        self.__init__(function_address, arg)

class MarkActivePartyAway(_Instruction):
    """Sets PARTY_N_AWAY event bit for the active party, clears character_available
    bits for all characters in the active party, and decrements CHARACTERS_AVAILABLE.

    Idempotent: if the party is already away, does nothing.

    PARTY_1/2/3_AWAY event bits (0x0dd-0x0df) are all in byte 0x1e9b at bits 5,6,7.
    The party index at $1A6D (1, 2, 3) plus 4 gives the bit position (5, 6, 7),
    which indexes into the power_of_two_table to get the mask (0x20, 0x40, 0x80)."""
    def __init__(self):
        import data.event_word as event_word
        import data.event_bit as event_bit
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        current_party = 0x1a6d
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9b

        src = [
            # Compute party_away_mask: convert party index (1,2,3) to bit mask (0x20,0x40,0x80)
            # $1A6D stores party index (1, 2, 3), not a bitmask. Add 4 to get bit position
            # (5, 6, 7), then look up the corresponding mask in the power_of_two_table.
            asm.TDC(),                                   # clear full 16-bit accumulator for clean TAX
            asm.LDA(current_party, asm.ABS),             # a = party index (1, 2, or 3)
            asm.CLC(),
            asm.ADC(0x04, asm.IMM8),                     # a = 5, 6, or 7  (bit position in away byte)
            asm.TAX(),                                   # x = bit position index
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # a = 0x20, 0x40, or 0x80
            asm.STA(0xee, asm.DIR),                      # store party_away_mask in direct page scratch

            # Check if already away (idempotent guard)
            asm.AND(party_away_byte, asm.ABS),           # test if bit already set
            asm.BNE("DONE"),                             # already away, skip

            # Set PARTY_N_AWAY event bit
            asm.LDA(0xee, asm.DIR),                      # reload party_away_mask
            asm.ORA(party_away_byte, asm.ABS),           # set the bit
            asm.STA(party_away_byte, asm.ABS),

            # Clear character_available for each character in the active party
            asm.LDX(0x0000, asm.IMM16),

            "LOOP_START",
            asm.LDA(character_party_start, asm.ABS_X),   # a = character data byte
            asm.AND(0x07, asm.IMM8),                     # isolate party bits (index 1, 2, or 3)
            asm.CMP(current_party, asm.ABS),             # is character in active party?
            asm.BNE("NEXT_CHAR"),                         # skip if not

            # Clear character_available bit using same pattern as recruit_character
            asm.PHX(),
            asm.TDC(),                                    # clear A (both bytes) for clean $BAED call
            asm.TXA(),                                    # a = character index
            asm.JSR(0xbaed, asm.ABS),                     # x = a mod 8 (bit), y = a // 8 (byte)
            asm.LDA(c0.power_of_two_table, asm.LNG_X),   # a = bit mask
            asm.EOR(0xff, asm.IMM8),                      # a = inverted mask
            asm.AND(char_available_addr, asm.ABS_Y),      # clear the bit
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.DEC(characters_available_address, asm.ABS),
            asm.PLX(),

            "NEXT_CHAR",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("LOOP_START"),

            "DONE",
            asm.LDA(0x01, asm.IMM8),                     # command size
            asm.JMP(0x9b5c, asm.ABS),                    # next command
        ]
        space = Write(Bank.C0, src, "custom mark active party away")
        address = space.start_address

        opcode = 0x66
        _set_opcode_address(opcode, address)

        MarkActivePartyAway.__init__ = lambda self: super().__init__(opcode)
        self.__init__()

class RestoreActivePartyAvailable(_Instruction):
    """Clears PARTY_N_AWAY event bit for the active party, sets character_available
    bits for all characters in the active party, and increments CHARACTERS_AVAILABLE.

    Idempotent: if the party is not away, does nothing."""
    def __init__(self):
        import data.event_word as event_word
        import data.event_bit as event_bit
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        current_party = 0x1a6d
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9b

        src = [
            # Compute party_away_mask: convert party index (1,2,3) to bit mask (0x20,0x40,0x80)
            asm.TDC(),                                   # clear full 16-bit accumulator for clean TAX
            asm.LDA(current_party, asm.ABS),             # a = party index (1, 2, or 3)
            asm.CLC(),
            asm.ADC(0x04, asm.IMM8),                     # a = 5, 6, or 7  (bit position in away byte)
            asm.TAX(),                                   # x = bit position index
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # a = 0x20, 0x40, or 0x80
            asm.STA(0xee, asm.DIR),                      # store party_away_mask in direct page scratch

            # Check if party is actually away (idempotent guard)
            asm.AND(party_away_byte, asm.ABS),           # test if bit is set
            asm.BEQ("DONE"),                             # not away, skip

            # Clear PARTY_N_AWAY event bit
            asm.LDA(0xee, asm.DIR),                      # reload party_away_mask
            asm.EOR(0xff, asm.IMM8),                     # invert
            asm.AND(party_away_byte, asm.ABS),           # clear the bit
            asm.STA(party_away_byte, asm.ABS),

            # Set character_available for each character in the active party
            asm.LDX(0x0000, asm.IMM16),

            "LOOP_START",
            asm.LDA(character_party_start, asm.ABS_X),   # a = character data byte
            asm.AND(0x07, asm.IMM8),                     # isolate party bits (index 1, 2, or 3)
            asm.CMP(current_party, asm.ABS),             # is character in active party?
            asm.BNE("NEXT_CHAR"),                         # skip if not

            # Set character_available bit using same pattern as recruit_character
            asm.PHX(),
            asm.TDC(),                                    # clear A (both bytes) for clean $BAED call
            asm.TXA(),                                    # a = character index
            asm.JSR(0xbaed, asm.ABS),                     # x = a mod 8 (bit), y = a // 8 (byte)
            asm.LDA(char_available_addr, asm.ABS_Y),      # a = character available byte
            asm.ORA(c0.power_of_two_table, asm.LNG_X),   # set the bit
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),
            asm.PLX(),

            "NEXT_CHAR",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("LOOP_START"),

            "DONE",
            asm.LDA(0x01, asm.IMM8),                     # command size
            asm.JMP(0x9b5c, asm.ABS),                    # next command
        ]
        space = Write(Bank.C0, src, "custom restore active party available")
        address = space.start_address

        opcode = 0x67
        _set_opcode_address(opcode, address)

        RestoreActivePartyAvailable.__init__ = lambda self: super().__init__(opcode)
        self.__init__()

class RemapPartiesToFreeSlots(_Instruction):
    """After SelectParties assigns characters to party slots 1..count,
    remaps those assignments to the actual free slots (not occupied by away parties).

    Only modifies characters with character_available set (non-away characters).
    When no parties are away, this is a no-op (maps 1->1, 2->2, 3->3).

    Uses direct page scratch $e8-$eb during execution."""
    def __init__(self):
        import data.event_bit as event_bit
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9b

        src = [
            # Step 1: Build free_slots mapping at DP $e8..$ea
            # free_slots[i] = party mask for the (i+1)th free slot
            # X tracks the index into the free_slots array

            asm.LDA(party_away_byte, asm.ABS),  # load away byte
            asm.STA(0xeb, asm.DIR),              # save for later checks
            asm.LDX(0x0000, asm.IMM16),          # free_slot_index = 0

            # Check party 1 (away bit 5 = mask 0x20)
            asm.AND(0x20, asm.IMM8),             # test P1 away
            asm.BNE("SKIP_P1"),
            asm.LDA(0x01, asm.IMM8),             # party 1 mask
            asm.STA(0xe8, asm.DIR_X),            # free_slots[idx] = 0x01
            asm.INX(),
            "SKIP_P1",

            # Check party 2 (away bit 6 = mask 0x40)
            asm.LDA(0xeb, asm.DIR),              # reload away byte
            asm.AND(0x40, asm.IMM8),             # test P2 away
            asm.BNE("SKIP_P2"),
            asm.LDA(0x02, asm.IMM8),             # party 2 mask
            asm.STA(0xe8, asm.DIR_X),            # free_slots[idx] = 0x02
            asm.INX(),
            "SKIP_P2",

            # Check party 3 (away bit 7 = mask 0x80)
            asm.LDA(0xeb, asm.DIR),              # reload away byte
            asm.AND(0x80, asm.IMM8),             # test P3 away
            asm.BNE("SKIP_P3"),
            asm.LDA(0x04, asm.IMM8),             # party 3 mask
            asm.STA(0xe8, asm.DIR_X),            # free_slots[idx] = 0x04
            "SKIP_P3",

            # Step 2: Remap characters' party assignments
            # For each character: if character_available AND party != 0,
            # remap their party mask using free_slots[]
            asm.LDX(0x0000, asm.IMM16),          # character index

            "CHAR_LOOP",
            asm.PHX(),                            # save char index
            asm.TDC(),                            # clear A (both bytes) for clean $BAED call
            asm.TXA(),                            # A = char index
            asm.JSR(0xbaed, asm.ABS),             # X = char mod 8, Y = char // 8
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # bit mask
            asm.AND(char_available_addr, asm.ABS_Y),     # test character_available
            asm.BEQ("CHAR_NEXT"),                 # not available -> skip (PLX at CHAR_NEXT)

            # Character is available. Restore char index and check party assignment.
            asm.PLX(),                            # restore char index
            asm.LDA(character_party_start, asm.ABS_X),  # load party assignment
            asm.BEQ("CHAR_NEXT_NO_PLX"),          # 0 = unassigned, skip

            # Remap: check which SelectParties slot and replace with free_slots[]
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("NOT_SLOT1"),
            asm.LDA(0xe8, asm.DIR),               # free_slots[0]
            asm.BRA("STORE_REMAP"),

            "NOT_SLOT1",
            asm.CMP(0x02, asm.IMM8),
            asm.BNE("NOT_SLOT2"),
            asm.LDA(0xe9, asm.DIR),               # free_slots[1]
            asm.BRA("STORE_REMAP"),

            "NOT_SLOT2",
            # Must be 0x04 (party 3)
            asm.LDA(0xea, asm.DIR),               # free_slots[2]

            "STORE_REMAP",
            asm.STA(character_party_start, asm.ABS_X),  # write remapped party

            "CHAR_NEXT_NO_PLX",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("CHAR_LOOP"),
            asm.BRA("DONE"),

            "CHAR_NEXT",
            asm.PLX(),                            # restore char index
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("CHAR_LOOP"),

            "DONE",
            asm.LDA(0x01, asm.IMM8),             # command size = 1 (opcode only)
            asm.JMP(0x9b5c, asm.ABS),            # advance to next event command
        ]
        space = Write(Bank.C0, src, "custom remap parties to free slots")
        address = space.start_address

        opcode = 0x68
        _set_opcode_address(opcode, address)

        RemapPartiesToFreeSlots.__init__ = lambda self: super().__init__(opcode)
        self.__init__()

class SetupBranchPartySelect(_Instruction):
    """Prepares the party select screen for branch recruitment in ruination mode.

    When the active party is on a branch (has its AWAY bit set):
    - Saves the current party mask to $e7 for FinalizeBranchPartySelect
    - Clears $1850 for current party members (clean slate for SelectParties)
    - Sets character_available only for current party members and the new recruit
    - Recomputes CHARACTERS_AVAILABLE count

    When not on a branch, this is a no-op.

    Takes one argument: the character ID of the newly recruited character."""
    def __init__(self, character):
        import data.event_bit as event_bit
        import data.event_word as event_word
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        current_party = 0x1a6d
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9b

        src = [
            # Check if on branch: party_away_mask = $1A6D << 5, test against $1E9B
            asm.LDA(current_party, asm.ABS),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),                                       # 0x20, 0x40, or 0x80
            asm.AND(party_away_byte, asm.ABS),               # test if party is away
            asm.BEQ("DONE"),                                 # not on branch → no-op

            # Save party mask for FinalizeBranchPartySelect
            asm.LDA(current_party, asm.ABS),
            asm.STA(0xe7, asm.DIR),

            # Zero character_available and CHARACTERS_AVAILABLE
            asm.STZ(char_available_addr, asm.ABS),           # chars 0-7 available = 0
            asm.STZ(char_available_addr + 1, asm.ABS),       # chars 8-13 available = 0
            asm.STZ(characters_available_address, asm.ABS),  # count = 0

            # For each char: make available if in current party or is the new recruit
            asm.LDX(0x0000, asm.IMM16),

            "LOOP",
            # Check if char is in current party
            asm.LDA(character_party_start, asm.ABS_X),
            asm.AND(current_party, asm.ABS),
            asm.BNE("SET_AVAIL_PARTY"),                      # in current party → make available

            # Check if char is the new recruit (argument at $eb)
            asm.TXA(),                                       # A = char index (low byte)
            asm.CMP(0xeb, asm.DIR),                          # compare with character argument
            asm.BEQ("SET_AVAIL"),                            # is new recruit → make available

            # Neither party member nor recruit → skip
            asm.BRA("NEXT"),

            "SET_AVAIL_PARTY",
            # Clear $1850 for party members so SelectParties starts from a clean slate
            asm.STZ(character_party_start, asm.ABS_X),

            "SET_AVAIL",
            # Set character_available bit
            asm.PHX(),
            asm.TDC(),
            asm.TXA(),                                       # A = char index
            asm.JSR(0xbaed, asm.ABS),                        # X = bit pos, Y = byte offset
            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),
            asm.PLX(),

            "NEXT",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("LOOP"),

            "DONE",
            asm.LDA(0x02, asm.IMM8),                        # command size = 2 (opcode + arg)
            asm.JMP(0x9b5c, asm.ABS),
        ]
        space = Write(Bank.C0, src, "custom setup branch party select")
        address = space.start_address

        opcode = 0x9e
        _set_opcode_address(opcode, address)

        SetupBranchPartySelect.__init__ = lambda self, character: super().__init__(opcode, character)
        self.__init__(character)

class FinalizeBranchPartySelect(_Instruction):
    """Finalizes party selection after branch recruitment in ruination mode.

    When $e7 is non-zero (set by SetupBranchPartySelect):
    - Remaps characters assigned to slot 1 by SelectParties to the saved party slot ($e7)
    - Recomputes character_available: available = recruited AND NOT in_away_party
    - Recomputes CHARACTERS_AVAILABLE count
    - Clears $e7

    When $e7 is zero (not on branch or Setup wasn't called), this is a no-op.

    No arguments."""
    def __init__(self):
        import data.event_bit as event_bit
        import data.event_word as event_word
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        char_recruited_addr = event_bit.address(event_bit.character_recruited(0))  # 0x1edc
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9b

        src = [
            # Check if we were on a branch
            asm.LDA(0xe7, asm.DIR),
            asm.BEQ("DONE"),                                 # 0 = not on branch → no-op

            # Step 1: Remap characters from slot 1 → saved party slot
            asm.LDX(0x0000, asm.IMM16),

            "REMAP_LOOP",
            asm.LDA(character_party_start, asm.ABS_X),
            asm.CMP(0x01, asm.IMM8),                         # assigned to slot 1 by SelectParties?
            asm.BNE("REMAP_NEXT"),
            asm.LDA(0xe7, asm.DIR),                          # load saved party mask
            asm.STA(character_party_start, asm.ABS_X),       # remap to original slot

            "REMAP_NEXT",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("REMAP_LOOP"),

            # Step 2: Build away_party_mask at $e8
            # P1 away (bit 5) → mask 0x01, P2 away (bit 6) → mask 0x02, P3 away (bit 7) → mask 0x04
            asm.LDA(0x00, asm.IMM8),
            asm.STA(0xe8, asm.DIR),                          # away_party_mask = 0

            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x20, asm.IMM8),                         # P1 away?
            asm.BEQ("NO_P1_AWAY"),
            asm.LDA(0x01, asm.IMM8),
            asm.STA(0xe8, asm.DIR),
            "NO_P1_AWAY",

            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x40, asm.IMM8),                         # P2 away?
            asm.BEQ("NO_P2_AWAY"),
            asm.LDA(0xe8, asm.DIR),
            asm.ORA(0x02, asm.IMM8),
            asm.STA(0xe8, asm.DIR),
            "NO_P2_AWAY",

            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x80, asm.IMM8),                         # P3 away?
            asm.BEQ("NO_P3_AWAY"),
            asm.LDA(0xe8, asm.DIR),
            asm.ORA(0x04, asm.IMM8),
            asm.STA(0xe8, asm.DIR),
            "NO_P3_AWAY",

            # Step 3: Recompute character_available from scratch
            asm.STZ(char_available_addr, asm.ABS),
            asm.STZ(char_available_addr + 1, asm.ABS),
            asm.STZ(characters_available_address, asm.ABS),

            asm.LDX(0x0000, asm.IMM16),

            "AVAIL_LOOP",
            # Check if character is in an away party
            asm.LDA(character_party_start, asm.ABS_X),
            asm.AND(0xe8, asm.DIR),                          # AND with away_party_mask
            asm.BNE("AVAIL_NEXT"),                           # in away party → not available

            # Not in away party. Check if recruited.
            asm.PHX(),
            asm.TDC(),
            asm.TXA(),
            asm.JSR(0xbaed, asm.ABS),                        # X = bit pos, Y = byte offset
            asm.LDA(char_recruited_addr, asm.ABS_Y),
            asm.AND(c0.power_of_two_table, asm.LNG_X),
            asm.BEQ("AVAIL_NOT_RECRUITED"),                  # not recruited → skip

            # Set available
            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),

            "AVAIL_NOT_RECRUITED",
            asm.PLX(),

            "AVAIL_NEXT",
            asm.INX(),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("AVAIL_LOOP"),

            # Clear $e7 so future calls are no-ops
            asm.STZ(0xe7, asm.DIR),

            "DONE",
            asm.LDA(0x01, asm.IMM8),                        # command size = 1 (opcode only)
            asm.JMP(0x9b5c, asm.ABS),
        ]
        space = Write(Bank.C0, src, "custom finalize branch party select")
        address = space.start_address

        opcode = 0x9f
        _set_opcode_address(opcode, address)

        FinalizeBranchPartySelect.__init__ = lambda self: super().__init__(opcode)
        self.__init__()
