from memory.space import Bank, START_ADDRESS_SNES, Reserve, Write, Read
from instruction.event import _Instruction, _Branch
import instruction.asm as asm
import instruction.c0 as c0
from enum import IntEnum

# Remaining unused opcodes: 0x4a, 0x5b, 0xa4, 0xe6, 0xfc, 0xfd
# Also used in y_npc/instructions.py: 0x9e (SetYNPCGraphics), 0x9f (YNPCEffect)
def _set_opcode_address(opcode, address):
    FIRST_OPCODE = 0x35
    opcode_table_address = 0x098c4 + (opcode - FIRST_OPCODE) * 2
    space = Reserve(opcode_table_address, opcode_table_address + 1, f"field opcode table, {opcode} {hex(address)}")
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

    PARTY_1/2/3_AWAY event bits (0x0e1-0x0e3) are all in byte 0x1e9c at bits 1,2,3.
    The party index at $1A6D (1, 2, 3) equals the bit position directly,
    which indexes into the power_of_two_table to get the mask (0x02, 0x04, 0x08)."""
    def __init__(self):
        import data.event_word as event_word
        import data.event_bit as event_bit
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x1850
        current_party = 0x1a6d
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9c

        src = [
            # Compute party_away_mask: convert party index (1,2,3) to bit mask (0x02,0x04,0x08)
            # $1A6D stores party index (1, 2, 3), which equals the bit position directly.
            asm.TDC(),                                   # clear full 16-bit accumulator for clean TAX
            asm.LDA(current_party, asm.ABS),             # a = party index (1, 2, or 3) = bit position
            asm.TAX(),                                   # x = bit position index
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # a = 0x02, 0x04, or 0x08
            asm.STA(0x0e, asm.DIR),                  # store party_away_mask in field RAM scratchpad $0E-$3F

            # Check if already away (idempotent guard)
            asm.AND(party_away_byte, asm.ABS),           # test if bit already set
            asm.BNE("DONE"),                             # already away, skip

            # Set PARTY_N_AWAY event bit
            asm.LDA(0x0e, asm.DIR),                      # reload party_away_mask
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
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9c

        src = [
            # Compute party_away_mask: convert party index (1,2,3) to bit mask (0x02,0x04,0x08)
            asm.TDC(),                                   # clear full 16-bit accumulator for clean TAX
            asm.LDA(current_party, asm.ABS),             # a = party index (1, 2, or 3) = bit position
            asm.TAX(),                                   # x = bit position index
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # a = 0x02, 0x04, or 0x08
            asm.STA(0x0e, asm.DIR),                      # store party_away_mask in field RAM scratchpad $0E-3F

            # Check if party is actually away (idempotent guard)
            asm.AND(party_away_byte, asm.ABS),           # test if bit is set
            asm.BEQ("DONE"),                             # not away, skip

            # Clear PARTY_N_AWAY event bit
            asm.LDA(0x0e, asm.DIR),                      # reload party_away_mask
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

    Takes one argument: the number of remapped parties to mark as AWAY (0, 1, or 2).
    - 0: Don't mark any parties AWAY (used for hub reform).
    - 2: Mark free_slots[0] and free_slots[1] as AWAY (used for Phoenix Cave split).

    Uses scratchpad RAM $10-$13 during execution."""
    def __init__(self, mark_away_count=0):
        import data.event_bit as event_bit
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x0867  # field RAM object data (0x1850, save ram)
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9c
        char_byte_len = 0x0029  # = 41 bytes per character in object data

        src = [
            # Step 1: Build free_slots mapping at DP $10..$12
            # free_slots[i] = party index for the (i+1)th free slot
            # X tracks the index into the free_slots array

            asm.LDX(0x0000, asm.IMM16),          # free_slot_index = 0

            # Check party 1 (away bit 1 = mask 0x02)
            asm.LDA(party_away_byte, asm.ABS),   # load away byte
            asm.AND(0x02, asm.IMM8),             # test P1 away
            asm.BNE("SKIP_P1"),                  # if P1 is away, "zero"=false --> BNE triggers
            asm.LDA(0x01, asm.IMM8),             # party 1 index
            asm.STA(0x10, asm.DIR_X),            # free_slots[idx] = 0x01
            asm.INX(),
            "SKIP_P1",

            # Check party 2 (away bit 2 = mask 0x04)
            asm.LDA(party_away_byte, asm.ABS),   # reload away byte
            asm.AND(0x04, asm.IMM8),             # test P2 away
            asm.BNE("SKIP_P2"),
            asm.LDA(0x02, asm.IMM8),             # party 2 index
            asm.STA(0x10, asm.DIR_X),            # free_slots[idx] = 0x02
            asm.INX(),
            "SKIP_P2",

            # Check party 3 (away bit 3 = mask 0x08)
            asm.LDA(party_away_byte, asm.ABS),   # reload away byte
            asm.AND(0x08, asm.IMM8),             # test P3 away
            asm.BNE("SKIP_P3"),
            asm.LDA(0x03, asm.IMM8),             # party 3 index
            asm.STA(0x10, asm.DIR_X),            # free_slots[idx] = 0x03
            "SKIP_P3",

            # Step 2: Remap characters' party assignments
            # For each character: if character_available and party != 0,
            # remap their party index using free_slots[]
            asm.LDX(0x0000, asm.IMM16),          # character index
            asm.LDY(0x00, asm.DIR),           # offset in object data

            "CHAR_LOOP",
            asm.PHY(),                            # store offset
            asm.PHX(),                            # save char index
            asm.TDC(),                            # clear A (both bytes) for clean $BAED call
            asm.TXA(),                            # A = char index
            asm.JSR(0xbaed, asm.ABS),             # X = char mod 8, Y = char // 8
            asm.LDA(c0.power_of_two_table, asm.LNG_X),  # bit mask
            asm.AND(char_available_addr, asm.ABS_Y),     # test character_available
            asm.BEQ("CHAR_NEXT"),                 # not available -> skip (PLX at CHAR_NEXT)

            # Character is available. Restore char index and check party assignment.
            asm.PLX(),                            # restore char index
            asm.PLY(),                            # restore offset
            asm.LDA(character_party_start, asm.ABS_Y),  # load party assignment byte
            asm.AND(0xf8, asm.IMM8),             # isolate non-party bits (enabled flag, etc.)
            asm.STA(0x13, asm.DIR),              # save non-party bits for STORE_REMAP
            asm.LDA(character_party_start, asm.ABS_Y),  # reload full byte
            asm.AND(0x07, asm.IMM8),             # isolate party bits (1, 2, or 3)
            asm.BEQ("CHAR_NEXT_NO_PLX"),          # 0 = unassigned, skip

            # Remap: check which SelectParties slot and replace with free_slots[]
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("NOT_SLOT1"),
            asm.LDA(0x10, asm.DIR),               # free_slots[0]
            asm.BRA("STORE_REMAP"),

            "NOT_SLOT1",
            asm.CMP(0x02, asm.IMM8),
            asm.BNE("NOT_SLOT2"),
            asm.LDA(0x11, asm.DIR),               # free_slots[1]
            asm.BRA("STORE_REMAP"),

            "NOT_SLOT2",
            # Must be 0x03 (party 3)
            asm.LDA(0x12, asm.DIR),               # free_slots[2]

            "STORE_REMAP",
            asm.ORA(0x13, asm.DIR),               # merge with preserved non-party bits
            asm.STA(character_party_start, asm.ABS_Y),  # write remapped party

            "CHAR_NEXT_NO_PLX",
            asm.INX(),  # Increment character ID
            asm.REP(0x21),  # reset carry, set A --> 16bit
            asm.TYA(),  # Transfer Y --> A
            asm.ADC(char_byte_len, asm.IMM16),  # Add with carry 0x29 = 41 (move to next character)
            asm.TAY(),  # Transfer A --> Y
            asm.TDC(),  # Transfer DP register to A
            asm.SEP(0x20),  # (8 bit accum./memory)
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("CHAR_LOOP"),
            asm.BRA("DONE"),

            "CHAR_NEXT",
            asm.PLX(),                            # restore char index
            asm.PLY(),                            # restore object offset
            asm.BRA("CHAR_NEXT_NO_PLX"),

            "DONE",
            # Check argument: how many parties to mark AWAY
            asm.LDA(0xeb, asm.DIR),               # argument = mark_away_count
            asm.BEQ("NO_MARK_AWAY"),              # 0 → skip

            # Mark free_slots[0] party as AWAY
            asm.TDC(),                             # clear A:B for clean 16-bit TAX
            asm.LDA(0x10, asm.DIR),                # A = free_slots[0] (party index 1-3)
            asm.TAX(),                             # X = party index (16-bit clean)
            asm.LDA(party_away_byte, asm.ABS),     # current away byte
            asm.ORA(c0.power_of_two_table, asm.LNG_X),  # set AWAY bit for this party
            asm.STA(party_away_byte, asm.ABS),     # write back

            asm.LDA(0xeb, asm.DIR),                # check if marking 2
            asm.CMP(0x02, asm.IMM8),
            asm.BCC("NO_MARK_AWAY"),               # < 2 → done (only marked 1)

            # Mark free_slots[1] party as AWAY
            asm.TDC(),                             # clear A:B
            asm.LDA(0x11, asm.DIR),                # A = free_slots[1] (party index 1-3)
            asm.TAX(),                             # X = party index (16-bit clean)
            asm.LDA(party_away_byte, asm.ABS),     # current away byte
            asm.ORA(c0.power_of_two_table, asm.LNG_X),  # set AWAY bit for this party
            asm.STA(party_away_byte, asm.ABS),     # write back

            "NO_MARK_AWAY",
            asm.LDA(0x02, asm.IMM8),             # command size = 2 (opcode + arg)
            asm.JMP(0x9b5c, asm.ABS),            # advance to next event command
        ]
        space = Write(Bank.C0, src, "custom remap parties to free slots")
        address = space.start_address

        opcode = 0x68
        _set_opcode_address(opcode, address)

        RemapPartiesToFreeSlots.__init__ = lambda self, mark_away_count=0: super().__init__(opcode, mark_away_count)
        self.__init__(mark_away_count)

class SetupBranchRecruit(_Instruction):
    """Prepares the party select screen for branch recruitment or party management
    in ruination mode.

    Takes one argument byte: xxspcccc
      bits 0-3 (cccc): character ID (0x0-0xD) or 0xF for no recruit
      bit 4 (p): if set, include all members of cccc's current party
      bit 5 (s): if set, place cccc's party into Party 2 (for 2-party formation)

    Steps:
    0. Mark all characters unavailable.
    1. Park all characters currently in parties 1,2,3 → 4,5,6 respectively.
       This hides them from SelectParties' post-menu routines ($714A/$6F67).
    2. Move active party members to Party 1. Mark them available.
    3. If cccc != 0xF:
       3a. If p=1: look up cccc's party. Mark everyone in that party available.
           If s=1, move them to Party 2. Otherwise, move them to Party 0.
       3b. If p=0: make cccc recruited, available, and in Party 0.
    4. Store active party index in SCRATCH. Set active_party ($1A6D) = 0x01.

    Use cases:
    - Normal branch recruiting: arg = 0b0000_cccc, form 1 party.
    - Mobliz_WoR phunbaba:     arg = 0x0F (0b0000_1111), form 1 party, no recruit.
    - Phoenix Cave split:       arg = 0x0F, form 2 parties (via event script).
    - Join forces:              arg = 0b0001_cccc, form 1 party from two.
    - Swap members:             arg = 0b0011_cccc, form 2 parties (swap)."""
    def __init__(self, argument):
        import data.event_bit as event_bit
        import data.event_word as event_word
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x0867  # field RAM object data (41 bytes/char)
        save_ram_party_start = 0x1850   # save RAM party data (1 byte/char, same verbbppp format)
        char_byte_len = 0x0029          # 41 bytes per character in object data
        current_party = 0x1a6d
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        char_recruited_addr = event_bit.address(event_bit.character_recruited(0))  # 0x1edc
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9c

        # Define helper functions
        park_parties_src = [
            # For each character:
            #   - If in active party: move to P1, mark available
            #   - If in P1: park at P4
            #   - If in P2: park at P5
            #   - If in P3: park at P6
            # (Active party members get moved to P1 before parking check,
            #  so if active=P1, they become P1 via SET_AVAIL_PARTY, not parked.)
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),  # Y = field RAM offset

            "LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),  # isolate party bits
            asm.CMP(current_party, asm.ABS),  # in active party?
            asm.BEQ("SET_AVAIL_PARTY"),  # yes → move to P1, make available

            # Not in active party. Park: P1→4, P2→5, P3→6
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("CHECK_P2"),
            asm.LDA(character_party_start, asm.ABS_Y),  # reload
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x04, asm.IMM8),  # P1 → P4
            asm.STA(character_party_start, asm.ABS_Y),
            asm.BRA("NEXT"),

            "CHECK_P2",
            asm.CMP(0x02, asm.IMM8),
            asm.BNE("CHECK_P3"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x05, asm.IMM8),  # P2 → P5
            asm.STA(character_party_start, asm.ABS_Y),
            asm.BRA("NEXT"),

            "CHECK_P3",
            asm.CMP(0x03, asm.IMM8),
            asm.BNE("NEXT"),  # party 0 or other → skip
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x06, asm.IMM8),  # P3 → P6
            asm.STA(character_party_start, asm.ABS_Y),
            asm.BRA("NEXT"),

            "SET_AVAIL_PARTY",
            # Move active party member to Party 1
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),  # keep non-party bits
            asm.ORA(0x01, asm.IMM8),  # set to Party 1
            asm.STA(character_party_start, asm.ABS_Y),

            # Set character_available bit
            asm.PHY(),
            asm.PHX(),
            asm.TDC(),
            asm.TXA(),  # A = char index
            asm.JSR(0xbaed, asm.ABS),  # X = bit pos, Y = byte offset
            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),
            asm.PLX(),
            asm.PLY(),

            "NEXT",
            asm.INX(),
            asm.REP(0x21),  # A → 16-bit, carry clear
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),  # A → 8-bit
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("LOOP"),

            asm.RTS(),
        ]
        space = Write(Bank.C0, park_parties_src, "Park Parties helper function")
        _park_parties = space.start_address

        recruit_single_char_src = [
            asm.TDC(),
            asm.LDA(0x14, asm.DIR),  # A = cccc
            asm.JSR(0xbaed, asm.ABS),  # X = bit pos, Y = byte offset
            # Set recruited
            asm.LDA(char_recruited_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_recruited_addr, asm.ABS_Y),
            # Set available
            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),

            # Clear party bits in field RAM for cccc (set to party 0).
            # Loop through characters to find cccc by index, then clear party bits.
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),
            "RECRUIT_FIND",
            asm.TXA(),
            asm.CMP(0x14, asm.DIR),  # X == cccc?
            asm.BEQ("RECRUIT_CLEAR"),
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.BRA("RECRUIT_FIND"),
            "RECRUIT_CLEAR",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),  # clear party bits (party 0)
            asm.STA(character_party_start, asm.ABS_Y),

            asm.RTS(),
        ]
        space = Write(Bank.C0, recruit_single_char_src, "Recruit Single Character helper function")
        _recruit_single_char = space.start_address

        include_char_party_src = [
            # First, look up cccc's party index from save RAM ($1850+cccc)
            asm.TDC(),
            asm.LDA(0x14, asm.DIR),  # A = cccc
            asm.TAX(),  # X = cccc (16-bit clean from TDC)
            asm.LDA(save_ram_party_start, asm.ABS_X),  # load save RAM byte for cccc
            asm.AND(0x07, asm.IMM8),  # isolate party index
            asm.STA(0x10, asm.DIR),  # $10 = cccc's party index

            # Determine target: if s=1, target=2 (Party 2); else target=0 (unassigned)
            asm.LDA(0x13, asm.DIR),  # s flag
            asm.BEQ("TARGET_ZERO"),
            asm.LDA(0x02, asm.IMM8),  # target = Party 2
            asm.BRA("SET_TARGET"),
            "TARGET_ZERO",
            asm.LDA(0x00, asm.IMM8),  # target = Party 0 (unassigned)
            "SET_TARGET",
            asm.STA(0x11, asm.DIR),  # $11 = target party for cccc's members

            # Loop through all characters. For each in cccc's party ($10):
            #   - Mark available
            #   - Move to target party ($11)
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),  # Y = field RAM offset

            "PARTY_LOOP",
            # Characters in cccc's party were parked (P_orig → P_orig+3).
            # cccc's original party N is now at N+3 (parked in step 1).
            # So we need to check if parked party index == $10 + 3.
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),  # isolate current party bits
            asm.STA(0x15, asm.DIR),  # save current party value
            asm.LDA(0x10, asm.DIR),  # A = cccc's original party
            asm.CLC(),
            asm.ADC(0x03, asm.IMM8),  # A = parked sentinel (orig + 3)
            asm.CMP(0x15, asm.DIR),  # compare with char's current party
            asm.BNE("PARTY_NEXT"),  # not in cccc's parked party → skip

            # This character is in cccc's party. Move to target and mark available.
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),  # keep non-party bits
            asm.ORA(0x11, asm.DIR),  # set to target party
            asm.STA(character_party_start, asm.ABS_Y),

            # Set character_available bit
            asm.PHY(),
            asm.PHX(),
            asm.TDC(),
            asm.TXA(),
            asm.JSR(0xbaed, asm.ABS),
            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),
            asm.PLX(),
            asm.PLY(),

            "PARTY_NEXT",
            asm.INX(),
            asm.REP(0x21),  # A → 16-bit, carry clear
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("PARTY_LOOP"),

            asm.RTS(),
        ]
        space = Write(Bank.C0, include_char_party_src, "Include Character's Party helper function")
        _include_char_party = space.start_address


        # Scratchpad usage:
        #   $10 = cccc's party index (looked up in step 3a)
        #   $11 = target party for cccc's members (0 or 2, based on s flag)
        #   $12 = p flag (bit 4 of argument)
        #   $13 = s flag (bit 5 of argument)
        #   $14 = cccc (bits 0-3 of argument)

        src = [
            # === Step 0: Parse argument and zero availability ===
            asm.LDA(0xeb, asm.DIR),                          # A = argument byte
            asm.AND(0x0f, asm.IMM8),                         # isolate cccc
            asm.STA(0x14, asm.DIR),                          # $14 = cccc
            asm.LDA(0xeb, asm.DIR),                          # reload argument
            asm.AND(0x10, asm.IMM8),                         # isolate p flag
            asm.STA(0x12, asm.DIR),                          # $12 = p flag (0x00 or 0x10)
            asm.LDA(0xeb, asm.DIR),                          # reload argument
            asm.AND(0x20, asm.IMM8),                         # isolate s flag
            asm.STA(0x13, asm.DIR),                          # $13 = s flag (0x00 or 0x20)

            # Zero character_available and CHARACTERS_AVAILABLE
            asm.STZ(char_available_addr, asm.ABS),           # chars 0-7 available = 0
            asm.STZ(char_available_addr + 1, asm.ABS),       # chars 8-13 available = 0
            asm.STZ(characters_available_address, asm.ABS),  # count = 0

            # === Step 1 & 2: Park parties and move active party to P1 ===
            asm.JSR(_park_parties, asm.ABS),

            # === Step 3: Handle recruit / party inclusion ===
            asm.LDA(0x14, asm.DIR),                          # A = cccc
            asm.CMP(0x0f, asm.IMM8),                         # 0xF = no recruit
            asm.BEQ("STEP4"),                                # skip to step 4

            # Check p flag
            asm.LDA(0x12, asm.DIR),                          # p flag
            asm.BNE("INCLUDE_PARTY"),                        # p=1 → include cccc's party

            # === Step 3b: p=0, single recruit ===
            # Make cccc recruited, available, and in party 0 (unassigned).
            # Set recruited and available bits
            asm.JSR(_recruit_single_char, asm.ABS),
            asm.BRA("STEP4"),

            # === Step 3a: p=1, include cccc's party ===
            "INCLUDE_PARTY",
            asm.JSR(_include_char_party, asm.ABS),

            # === Step 4: Store active party in SCRATCH, set current_party = 1 ===
            "STEP4",
            asm.LDA(current_party, asm.ABS),                 # original active party (still set)
            asm.STA(event_word.address(event_word.SCRATCH), asm.ABS),

            # If s flag is set, also store has_party2 flag in SCRATCH bit 3
            asm.LDA(0x13, asm.DIR),                          # s flag
            asm.BEQ("NO_P2_FLAG"),
            asm.LDA(event_word.address(event_word.SCRATCH), asm.ABS),
            asm.ORA(0x08, asm.IMM8),                         # set bit 3 = has_party2
            asm.STA(event_word.address(event_word.SCRATCH), asm.ABS),
            "NO_P2_FLAG",

            # Save party_away_byte before setting current_party = 1.
            # Vanilla SelectParties clears bit current_party of $1E9C,
            # which would destroy PARTY_N_AWAY for whichever party index
            # we temporarily use. We restore it in FinalizeBranchRecruit.
            asm.LDA(party_away_byte, asm.ABS),
            asm.STA(event_word.address(event_word.SCRATCH) + 1, asm.ABS),  # SCRATCH high byte ($1FFB)

            asm.LDA(0x01, asm.IMM8),
            asm.STA(current_party, asm.ABS),                 # set active party to 1

            "DONE",
            asm.LDA(0x02, asm.IMM8),                         # command size = 2 (opcode + arg)
            asm.JMP(0x9b5c, asm.ABS),
        ]
        space = Write(Bank.C0, src, "custom setup branch recruit")
        address = space.start_address

        opcode = 0xec
        _set_opcode_address(opcode, address)

        SetupBranchRecruit.__init__ = lambda self, argument: super().__init__(opcode, argument)
        self.__init__(argument)

# Keep old name as alias for backward compatibility during transition
SetupBranchPartySelect = SetupBranchRecruit

class FinalizeBranchRecruit(_Instruction):
    """Finalizes party selection after SetupBranchRecruit in ruination mode.

    Reads SCRATCH to determine the original active party and flags.
    SCRATCH layout:
      Low byte ($1FFA): 0000hppp
        bits 0-2 (ppp): original active party index (1-3)
        bit 3 (h): has_party2 flag (Party 2 was populated by Setup)
      High byte ($1FFB): saved party_away_byte ($1E9C) from before
        SelectParties ran (vanilla clears bit current_party of $1E9C)

    Steps:
    0. Load SCRATCH. Extract party index and has_party2 flag.
       If has_party2: park Party 2 in slot 7, note it for step 3.
       Build a "parties used" scratchpad for slots 1-3.
    1. Restore active party from SCRATCH. Move Party 1 → original active party.
       Mark that party slot as used. Mirror to save RAM.
    2. Restore parked parties: 4→1, 5→2, 6→3. Mark restored parties used.
       Mirror to save RAM.
    3. If party7 exists (has_party2): find first unused party slot from scratchpad.
       Move party 7 → that slot. Write the slot ID to SCRATCH for the caller.
       Mirror to save RAM. If the active party is AWAY, set AWAY for the new
       party too (so both parties from a swap/join are treated the same).
    4. Clear PARTY_N_AWAY for any now-unused party slots.
    5. Recompute character_available = recruited AND NOT in_away_party.
       Recompute CHARACTERS_AVAILABLE count.

    Party leader visible bits are also recomputed (step 1b from old Finalize).

    Uses scratchpad RAM:
      $10 = has_party2 flag, $11 = parties_used bitmask,
      $12-$13 = temp, $14 = original party index,
      $30-$33 = away-party lookup table.

    No arguments."""
    def __init__(self):
        import data.event_bit as event_bit
        import data.event_word as event_word
        from constants.entities import CHARACTER_COUNT

        character_party_start = 0x0867  # field RAM object data (41 bytes/char)
        save_ram_party_start = 0x1850   # save RAM party data (1 byte/char, same verbbppp format)
        char_byte_len = 0x0029          # 41 bytes per character in object data
        char_available_addr = event_bit.address(event_bit.character_available(0))  # 0x1ede
        char_recruited_addr = event_bit.address(event_bit.character_recruited(0))  # 0x1edc
        characters_available_address = event_word.address(event_word.CHARACTERS_AVAILABLE)
        party_away_byte = event_bit.address(event_bit.PARTY_1_AWAY)  # 0x1e9c
        current_party = 0x1a6d

        src = [
            # Restore party_away_byte saved by SetupBranchRecruit.
            # Vanilla SelectParties clears bit current_party of $1E9C,
            # which destroys PARTY_N_AWAY for the temporary current_party
            # that SetupBranchRecruit set.
            asm.LDA(event_word.address(event_word.SCRATCH) + 1, asm.ABS),  # SCRATCH high byte ($1FFB)
            asm.STA(party_away_byte, asm.ABS),

            # === Step 0: Load SCRATCH, extract flags ===
            asm.LDA(event_word.address(event_word.SCRATCH), asm.ABS),
            asm.AND(0x07, asm.IMM8),                         # isolate original party index
            asm.STA(0x14, asm.DIR),                          # $14 = original active party (1-3)
            asm.STA(current_party, asm.ABS),                 # restore current_party

            asm.LDA(event_word.address(event_word.SCRATCH), asm.ABS),
            asm.AND(0x08, asm.IMM8),                         # isolate has_party2 flag
            asm.STA(0x10, asm.DIR),                          # $10 = has_party2 (0x00 or 0x08)

            asm.STZ(0x11, asm.DIR),                          # $11 = parties_used bitmask (clear)

            # If has_party2: park Party 2 members at slot 7
            asm.LDA(0x10, asm.DIR),
            asm.BEQ("SKIP_PARK_P2"),

            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),
            "PARK_P2_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),
            asm.CMP(0x02, asm.IMM8),                         # in Party 2?
            asm.BNE("PARK_P2_NEXT"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x07, asm.IMM8),                         # move to slot 7
            asm.STA(character_party_start, asm.ABS_Y),
            "PARK_P2_NEXT",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("PARK_P2_LOOP"),

            "SKIP_PARK_P2",

            # === Step 1: Move Party 1 → original active party ===
            # Mark original party as used
            asm.TDC(),
            asm.LDA(0x14, asm.DIR),                          # original party index
            asm.TAX(),
            asm.LDA(c0.power_of_two_table, asm.LNG_X),
            asm.ORA(0x11, asm.DIR),
            asm.STA(0x11, asm.DIR),                          # mark party used

            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),
            "REMAP_P1_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),
            asm.CMP(0x01, asm.IMM8),                         # in Party 1?
            asm.BNE("REMAP_P1_NEXT"),
            # Remap to original party
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x14, asm.DIR),                          # merge original party index
            asm.STA(character_party_start, asm.ABS_Y),
            # Mirror to save RAM
            asm.LDA(save_ram_party_start, asm.ABS_X),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x14, asm.DIR),
            asm.STA(save_ram_party_start, asm.ABS_X),
            "REMAP_P1_NEXT",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("REMAP_P1_LOOP"),

            # === Step 2: Restore parked parties 4→1, 5→2, 6→3 ===
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),
            "RESTORE_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),

            asm.CMP(0x04, asm.IMM8),                         # parked from P1?
            asm.BNE("REST_CHECK5"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x01, asm.IMM8),                         # restore to P1
            asm.STA(character_party_start, asm.ABS_Y),
            asm.LDA(save_ram_party_start, asm.ABS_X),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x01, asm.IMM8),
            asm.STA(save_ram_party_start, asm.ABS_X),
            # Mark P1 used
            asm.LDA(0x11, asm.DIR),
            asm.ORA(0x02, asm.IMM8),                         # bit 1 = P1
            asm.STA(0x11, asm.DIR),
            asm.BRA("RESTORE_NEXT"),

            "REST_CHECK5",
            asm.CMP(0x05, asm.IMM8),                         # parked from P2?
            asm.BNE("REST_CHECK6"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x02, asm.IMM8),                         # restore to P2
            asm.STA(character_party_start, asm.ABS_Y),
            asm.LDA(save_ram_party_start, asm.ABS_X),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x02, asm.IMM8),
            asm.STA(save_ram_party_start, asm.ABS_X),
            # Mark P2 used
            asm.LDA(0x11, asm.DIR),
            asm.ORA(0x04, asm.IMM8),                         # bit 2 = P2
            asm.STA(0x11, asm.DIR),
            asm.BRA("RESTORE_NEXT"),

            "REST_CHECK6",
            asm.CMP(0x06, asm.IMM8),                         # parked from P3?
            asm.BNE("RESTORE_NEXT"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x03, asm.IMM8),                         # restore to P3
            asm.STA(character_party_start, asm.ABS_Y),
            asm.LDA(save_ram_party_start, asm.ABS_X),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x03, asm.IMM8),
            asm.STA(save_ram_party_start, asm.ABS_X),
            # Mark P3 used
            asm.LDA(0x11, asm.DIR),
            asm.ORA(0x08, asm.IMM8),                         # bit 3 = P3
            asm.STA(0x11, asm.DIR),

            "RESTORE_NEXT",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("RESTORE_LOOP"),

            # === Step 3: If has_party2, find unused slot and move party 7 there ===
            asm.LDA(0x10, asm.DIR),                          # has_party2?
            asm.BEQ("STEP4"),                                # no → skip

            # Find first unused party slot (1, 2, or 3)
            asm.LDA(0x11, asm.DIR),                          # parties_used bitmask
            asm.AND(0x02, asm.IMM8),                         # bit 1 = P1
            asm.BEQ("USE_SLOT1"),
            asm.LDA(0x11, asm.DIR),
            asm.AND(0x04, asm.IMM8),                         # bit 2 = P2
            asm.BEQ("USE_SLOT2"),
            # Must be slot 3
            asm.LDA(0x03, asm.IMM8),
            asm.BRA("MOVE_P7"),
            "USE_SLOT1",
            asm.LDA(0x01, asm.IMM8),
            asm.BRA("MOVE_P7"),
            "USE_SLOT2",
            asm.LDA(0x02, asm.IMM8),

            "MOVE_P7",
            asm.STA(0x12, asm.DIR),                          # $12 = target slot for party 7
            # Write target slot to SCRATCH for caller to use
            asm.STA(event_word.address(event_word.SCRATCH), asm.ABS),

            # Remap party 7 → target slot
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),
            "P7_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),
            asm.CMP(0x07, asm.IMM8),                         # in slot 7?
            asm.BNE("P7_NEXT"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x12, asm.DIR),                          # move to target slot
            asm.STA(character_party_start, asm.ABS_Y),
            asm.LDA(save_ram_party_start, asm.ABS_X),
            asm.AND(0xf8, asm.IMM8),
            asm.ORA(0x12, asm.DIR),
            asm.STA(save_ram_party_start, asm.ABS_X),
            # Mark target slot used
            asm.PHX(),
            asm.TDC(),
            asm.LDA(0x12, asm.DIR),
            asm.TAX(),
            asm.LDA(c0.power_of_two_table, asm.LNG_X),
            asm.ORA(0x11, asm.DIR),
            asm.STA(0x11, asm.DIR),
            asm.PLX(),
            "P7_NEXT",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("P7_LOOP"),

            # Mirror AWAY bit: if active party is AWAY, set AWAY for the new party too
            asm.TDC(),
            asm.LDA(0x14, asm.DIR),                          # A = original active party index
            asm.TAX(),                                       # X = active party index (16-bit clean)
            asm.LDA(c0.power_of_two_table, asm.LNG_X),      # A = active party AWAY mask
            asm.AND(party_away_byte, asm.ABS),               # test if active party is AWAY
            asm.BEQ("STEP4_AFTER_SCRATCH"),                  # not away → skip

            # Active party is AWAY: set AWAY for the new party's slot ($12)
            asm.TDC(),
            asm.LDA(0x12, asm.DIR),                          # A = new party slot
            asm.TAX(),
            asm.LDA(party_away_byte, asm.ABS),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),      # set AWAY bit for new party
            asm.STA(party_away_byte, asm.ABS),

            asm.BRA("STEP4_AFTER_SCRATCH"),                  # skip SCRATCH clear

            # === Step 4: Clear PARTY_N_AWAY for unused slots ===
            "STEP4",
            # Clear SCRATCH (no party2 to report)
            asm.STZ(event_word.address(event_word.SCRATCH), asm.ABS),

            "STEP4_AFTER_SCRATCH",
            # For each party 1-3: if not in parties_used, clear its AWAY bit
            asm.LDA(0x11, asm.DIR),                          # parties_used
            asm.AND(0x02, asm.IMM8),                         # P1 used?
            asm.BNE("P1_USED"),
            # P1 not used: clear AWAY bit 1
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0xfd, asm.IMM8),                         # clear bit 1
            asm.STA(party_away_byte, asm.ABS),
            "P1_USED",

            asm.LDA(0x11, asm.DIR),
            asm.AND(0x04, asm.IMM8),                         # P2 used?
            asm.BNE("P2_USED"),
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0xfb, asm.IMM8),                         # clear bit 2
            asm.STA(party_away_byte, asm.ABS),
            "P2_USED",

            asm.LDA(0x11, asm.DIR),
            asm.AND(0x08, asm.IMM8),                         # P3 used?
            asm.BNE("P3_USED"),
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0xf7, asm.IMM8),                         # clear bit 3
            asm.STA(party_away_byte, asm.ABS),
            "P3_USED",

            # === Step 1b: Set visible bit on party leader for each party (1-3) ===
            # After remapping, ensure each party has exactly one visible leader.
            # For each party, find the enabled character with lowest battle order
            # and set bit 7. Mirrors vanilla logic at C0/6D91-6DC7.
            asm.LDA(0x01, asm.IMM8),
            asm.STA(0x15, asm.DIR),                          # $15 = target party (start at 1)

            "VIS_PARTY_LOOP",
            asm.LDA(0x20, asm.IMM8),
            asm.STA(0x16, asm.DIR),                          # $16 = best battle order (init $20 = none)
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),

            "VIS_CHAR_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x40, asm.IMM8),                         # enabled? (bit 6)
            asm.BEQ("VIS_NEXT_CHAR"),

            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),                         # isolate party bits
            asm.CMP(0x15, asm.DIR),                          # matches target party?
            asm.BNE("VIS_NEXT_CHAR"),

            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x18, asm.IMM8),                         # isolate battle order bits
            asm.CMP(0x16, asm.DIR),                          # < best so far?
            asm.BCS("VIS_NEXT_CHAR"),
            asm.STA(0x16, asm.DIR),                          # update best battle order
            asm.STY(0x17, asm.DIR),                          # save winning Y offset (16-bit)

            "VIS_NEXT_CHAR",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("VIS_CHAR_LOOP"),

            asm.LDA(0x16, asm.DIR),
            asm.CMP(0x20, asm.IMM8),                         # no match?
            asm.BEQ("VIS_NEXT_PARTY"),

            asm.LDY(0x17, asm.DIR),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.ORA(0x80, asm.IMM8),                         # set visible bit
            asm.STA(character_party_start, asm.ABS_Y),

            "VIS_NEXT_PARTY",
            asm.INC(0x15, asm.DIR),
            asm.LDA(0x15, asm.DIR),
            asm.CMP(0x04, asm.IMM8),                         # done with party 3?
            asm.BNE("VIS_PARTY_LOOP"),

            # === Step 5: Recompute character_available ===
            # Build away-party lookup table at $30..$33
            asm.STZ(0x30, asm.DIR),                          # party 0 - never away
            asm.STZ(0x31, asm.DIR),                          # party 1
            asm.STZ(0x32, asm.DIR),                          # party 2
            asm.STZ(0x33, asm.DIR),                          # party 3

            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x02, asm.IMM8),
            asm.BEQ("NO_P1_AWAY"),
            asm.INC(0x31, asm.DIR),
            "NO_P1_AWAY",
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x04, asm.IMM8),
            asm.BEQ("NO_P2_AWAY"),
            asm.INC(0x32, asm.DIR),
            "NO_P2_AWAY",
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0x08, asm.IMM8),
            asm.BEQ("NO_P3_AWAY"),
            asm.INC(0x33, asm.DIR),
            "NO_P3_AWAY",

            # Recompute character_available from scratch
            asm.STZ(char_available_addr, asm.ABS),
            asm.STZ(char_available_addr + 1, asm.ABS),
            asm.STZ(characters_available_address, asm.ABS),

            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),

            "AVAIL_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),                         # isolate party index
            asm.PHX(),
            asm.PHA(),
            asm.TDC(),
            asm.PLA(),                                       # A = party index, B = 0
            asm.TAX(),                                       # X = clean 16-bit party index
            asm.LDA(0x30, asm.DIR_X),                        # 0 = available, non-zero = away
            asm.BNE("AVAIL_NEXT"),                           # in away party → skip

            # Not in away party. Check if recruited.
            asm.PLX(),
            asm.PHY(),
            asm.PHX(),
            asm.TDC(),
            asm.TXA(),
            asm.JSR(0xbaed, asm.ABS),
            asm.LDA(char_recruited_addr, asm.ABS_Y),
            asm.AND(c0.power_of_two_table, asm.LNG_X),
            asm.BEQ("AVAIL_NOT_RECRUITED"),

            asm.LDA(char_available_addr, asm.ABS_Y),
            asm.ORA(c0.power_of_two_table, asm.LNG_X),
            asm.STA(char_available_addr, asm.ABS_Y),
            asm.INC(characters_available_address, asm.ABS),

            "AVAIL_NOT_RECRUITED",
            asm.PLX(),
            asm.PLY(),
            asm.PHX(),

            "AVAIL_NEXT",
            asm.PLX(),
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("AVAIL_LOOP"),

            # === Step 6: Set/clear THREE_PARTIES_CREATED (event_bit 0x0e0, bit 0 of party_away_byte) ===
            # Loop through all characters. For each enabled character, note which party slot it occupies.
            # If all three party slots (1, 2, 3) have at least one enabled character → set the bit.
            # $34 = party 1 seen, $35 = party 2 seen, $36 = party 3 seen
            asm.STZ(0x34, asm.DIR),
            asm.STZ(0x35, asm.DIR),
            asm.STZ(0x36, asm.DIR),
            asm.LDX(0x0000, asm.IMM16),
            asm.LDY(0x00, asm.DIR),

            "COUNT_3PC_LOOP",
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x40, asm.IMM8),                         # enabled? (bit 6)
            asm.BEQ("COUNT_3PC_NEXT"),
            asm.LDA(character_party_start, asm.ABS_Y),
            asm.AND(0x07, asm.IMM8),                         # isolate party bits (0=none, 1-3=party slot)
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("COUNT_3PC_CHK_P2"),
            asm.INC(0x34, asm.DIR),
            asm.BRA("COUNT_3PC_NEXT"),
            "COUNT_3PC_CHK_P2",
            asm.CMP(0x02, asm.IMM8),
            asm.BNE("COUNT_3PC_CHK_P3"),
            asm.INC(0x35, asm.DIR),
            asm.BRA("COUNT_3PC_NEXT"),
            "COUNT_3PC_CHK_P3",
            asm.CMP(0x03, asm.IMM8),
            asm.BNE("COUNT_3PC_NEXT"),
            asm.INC(0x36, asm.DIR),

            "COUNT_3PC_NEXT",
            asm.INX(),
            asm.REP(0x21),
            asm.TYA(),
            asm.ADC(char_byte_len, asm.IMM16),
            asm.TAY(),
            asm.TDC(),
            asm.SEP(0x20),
            asm.CPX(CHARACTER_COUNT, asm.IMM16),
            asm.BNE("COUNT_3PC_LOOP"),

            # If all three party slots have chars → set THREE_PARTIES_CREATED (bit 0), else clear it
            asm.LDA(0x34, asm.DIR),
            asm.BEQ("CLEAR_3PC"),                            # party 1 empty
            asm.LDA(0x35, asm.DIR),
            asm.BEQ("CLEAR_3PC"),                            # party 2 empty
            asm.LDA(0x36, asm.DIR),
            asm.BEQ("CLEAR_3PC"),                            # party 3 empty
            asm.LDA(party_away_byte, asm.ABS),
            asm.ORA(0x01, asm.IMM8),                         # set bit 0 = THREE_PARTIES_CREATED
            asm.STA(party_away_byte, asm.ABS),
            asm.BRA("DONE_3PC"),
            "CLEAR_3PC",
            asm.LDA(party_away_byte, asm.ABS),
            asm.AND(0xFE, asm.IMM8),                         # clear bit 0 = THREE_PARTIES_CREATED
            asm.STA(party_away_byte, asm.ABS),
            "DONE_3PC",

            "DONE",
            asm.LDA(0x01, asm.IMM8),                        # command size = 1
            asm.JMP(0x9b5c, asm.ABS),
        ]
        space = Write(Bank.C0, src, "custom finalize branch recruit")
        address = space.start_address

        opcode = 0xed
        _set_opcode_address(opcode, address)

        FinalizeBranchRecruit.__init__ = lambda self: super().__init__(opcode)
        self.__init__()

# Keep old name as alias for backward compatibility during transition
FinalizeBranchPartySelect = FinalizeBranchRecruit
