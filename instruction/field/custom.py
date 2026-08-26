from memory.space import Bank, START_ADDRESS_SNES, Reserve, Write, Read
from instruction.event import _Instruction, _Branch
import instruction.asm as asm
import instruction.c0 as c0
import args
from enum import IntEnum

def _set_opcode_address(opcode, address):
    # Claiming a field opcode reserves its slot in the event command
    # pointer table, so two features claiming the same opcode fail the
    # build with a space conflict rather than silently overwriting one
    # another.  (The description is interpolated so that error names the
    # opcode - it used to be a plain string printing "{opcode}".)
    FIRST_OPCODE = 0x35
    opcode_table_address = 0x098c4 + (opcode - FIRST_OPCODE) * 2
    space = Reserve(opcode_table_address, opcode_table_address + 1,
                    f"field opcode table, {hex(opcode)} -> {hex(address)}")
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


class BedHealCharacter(_Instruction):
    # -nfh bed heal, per character. Character arg is 0x00..0x0F for a
    # specific actor or 0x31..0x34 for PARTY0..PARTY3 (resolved via $9DAD).
    # Effect per character (mutually exclusive):
    #   dead                   -> revive to 1 HP (no-op if -permadeath)
    #   alive + any status     -> clear all field status bytes ($1614, $1615)
    #   alive + HP < max HP or MP < max MP:
    #                          -> current HP += max HP / 4 (capped at max)
    #                          -> current MP += max MP / 4 (capped at max)
    def __init__(self, character):
        from instruction.c0 import character_data_offset

        CURRENT_HP = 0x1609
        CURRENT_MP = 0x160d
        STATUS1    = 0x1614  # death bit is bit 7 here (matches permadeath.py)
        STATUS4    = 0x1615
        DEATH_MASK = 0x80

        MAX_HP_INTO_1E = 0xaee8  # JSR -> $1E = boosted max HP (capped at 9999)
        MAX_MP_INTO_1E = 0xafa3  # JSR -> $1E = boosted max MP
        NEXT_COMMAND   = 0x9b5c

        src = [
            # Resolve character data offset. Y = offset such that char data
            # lives at $1600+Y. Sentinel Y>=$0250 means no such slot.
            asm.JSR(character_data_offset, asm.ABS),
            asm.CPY(0x0250, asm.IMM16),
            asm.BCS("DONE"),

            # Is this character dead?
            asm.LDA(STATUS1, asm.ABS_Y),
            asm.AND(DEATH_MASK, asm.IMM8),
            asm.BEQ("NOT_DEAD"),
        ]

        if args.permadeath:
            # Permadeath: dead characters get no effect from the bed.
            src += [
                asm.BRA("DONE"),
            ]
        else:
            # Revive: clear death bit, HP = 1.
            src += [
                asm.LDA(STATUS1, asm.ABS_Y),
                asm.AND(0xff - DEATH_MASK, asm.IMM8),
                asm.STA(STATUS1, asm.ABS_Y),
                asm.A16(),
                asm.LDA(0x0001, asm.IMM16),
                asm.STA(CURRENT_HP, asm.ABS_Y),
                asm.A8(),
                asm.BRA("DONE"),
            ]

        src += [
            "NOT_DEAD",
            # Any non-death status bit in $1614?
            asm.LDA(STATUS1, asm.ABS_Y),
            asm.AND(0xff - DEATH_MASK, asm.IMM8),
            asm.BNE("HAS_STATUS"),
            # Any bit in $1615?
            asm.LDA(STATUS4, asm.ABS_Y),
            asm.BEQ("NO_STATUS"),

            "HAS_STATUS",
            # Clear both field status bytes. (Death is already 0 here.)
            asm.LDA(0x00, asm.IMM8),
            asm.STA(STATUS1, asm.ABS_Y),
            asm.STA(STATUS4, asm.ABS_Y),
            asm.BRA("DONE"),

            "NO_STATUS",
            # Alive + no status: heal HP if below max, AND heal MP.
            asm.JSR(MAX_HP_INTO_1E, asm.ABS),   # $1E = max HP, returns A8
            asm.A16(),
            asm.LDA(CURRENT_HP, asm.ABS_Y),
            asm.CMP(0x1e, asm.DIR),
            asm.BCS("HEAL_MP"),                 # current HP >= max -> heal MP

            # current HP += max HP / 4, capped at max HP.
            asm.LDA(0x1e, asm.DIR),
            asm.LSR(),
            asm.LSR(),
            asm.CLC(),
            asm.ADC(CURRENT_HP, asm.ABS_Y),
            asm.CMP(0x1e, asm.DIR),
            asm.BCC("STORE_HP"),
            asm.LDA(0x1e, asm.DIR),
            "STORE_HP",
            asm.STA(CURRENT_HP, asm.ABS_Y),
            asm.A8(),

            "HEAL_MP",
            # Reached from BCS above while still in A16. Vanilla MAX_MP
            # routine expects A8, so switch back before the JSR.
            asm.A8(),
            asm.JSR(MAX_MP_INTO_1E, asm.ABS),   # $1E = max MP, returns A8
            asm.A16(),
            asm.LDA(CURRENT_MP, asm.ABS_Y),
            asm.CMP(0x1e, asm.DIR),
            asm.BCS("DONE"),            # already at max MP, nothing to do

            # current MP += max MP / 4, capped at max MP.
            asm.LDA(0x1e, asm.DIR),
            asm.LSR(),
            asm.LSR(),
            asm.CLC(),
            asm.ADC(CURRENT_MP, asm.ABS_Y),
            asm.CMP(0x1e, asm.DIR),
            asm.BCC("STORE_MP"),
            asm.LDA(0x1e, asm.DIR),
            "STORE_MP",
            asm.STA(CURRENT_MP, asm.ABS_Y),

            "DONE",
            asm.TDC(),
            asm.A8(),
            asm.LDA(0x02, asm.IMM8),   # command size: opcode + 1 arg byte
            asm.JMP(NEXT_COMMAND, asm.ABS),
        ]

        space = Write(Bank.C0, src, "nfh bed heal single character")
        address = space.start_address

        opcode = 0xa4
        _set_opcode_address(opcode, address)

        BedHealCharacter.__init__ = lambda self, character: super().__init__(opcode, character)
        self.__init__(character)


class ToggleWorlds(_Instruction):
    def __init__(self):
        fade_load_map = 0xab47

        src = [
            asm.LDA(0x1f69, asm.ABS),           # a = low 8 bits of parent map
            asm.XOR(1, asm.IMM8),               # toggle last bit of parent map id
            asm.STA(0x1f69, asm.ABS),           # update parent map
            asm.JMP(fade_load_map, asm.ABS),    # jump to original fade load map command
        ]
        space = Write(Bank.C0, src, "custom toggle worlds instruction")
        address = space.start_address

        opcode = 0x6d
        _set_opcode_address(opcode, address)

        # same args as airship lift-off load map
        # special map 0x1ff, return to parent map at same position/direction
        args = [0xff, 0x25, 0x00, 0x00, 0x01]

        ToggleWorlds.__init__ = lambda self : super().__init__(opcode, *args)
        self.__init__()

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

# --- L3: check rewards -------------------------------------------------
#
# Everything about a check reward - which kind it is and which one - lives
# in one masked table (obfuscation/rewards.py); scripts carry only an
# opaque slot.  Items and espers deliberately share the table, the grant
# command and the name-rendering control code, so nothing static tells an
# esper check from an item check: each dispatches on the kind byte it
# decodes at runtime.
#
# Control codes are installed by chaining onto the end of the message
# engine's control-code dispatch, where a byte matching nothing falls
# through to the literal-character path:
#
#   $1C <reward>   name of the reward whose slot is in $0584
#   $1D <reward2>  name of the reward in the NEXT slot, for the one dialog
#                  that names two rewards at once (the Narshe WOR choice)
#
# $0584 is "Spell Index for Dialog Window Display", documented as unused
# in the US release (a leftover from FF6j).  $0583 is deliberately left
# alone: it is the item index vanilla's own <item> code reads, and the
# chest-opening path sets it.
CHAIN_END = 0x0844b             # C0/844B: SEC : SBC #$1b, the literal path
CHAIN_RESUME = 0x844e

REWARD_CODE = 0x1c
REWARD2_CODE = 0x1d
REWARD_SLOT = 0x0584

ESPER_NAMES_SNES = 0xe6f6e1     # 8 bytes/entry, $ff padded
ESPER_NAME_LENGTH = 8
ESPER_NAME_STRIDE = 8
ITEM_NAMES_SNES = 0xd2b301      # 13 bytes/entry: icon byte then 12 chars
ITEM_NAME_LENGTH = 12
ITEM_NAME_STRIDE = 13
CHARACTER_NAMES_WRAM = 0x1602   # in character data, 37 bytes/record
CHARACTER_NAME_LENGTH = 6
CHARACTER_NAME_STRIDE = 37      # sizeof character data record

TEXT_BUFFER = 0x9183            # $7E9183, the message engine's text buffer
TEXT2_TO_TEXT1 = 0x60           # name charset -> dialog charset
NAME_PAD = 0xff - TEXT2_TO_TEXT1

_name_codes = None

def _reward_table():
    from obfuscation import claim
    from obfuscation.claim import snes
    layout = claim.layout(args)
    return snes(layout["rewards"]), snes(layout["rewards_pad"])

def _decode_slot_src(field):
    """asm reading one masked byte of the reward slot in X (X = slot * 2)."""
    table, pad = _reward_table()
    return [asm.LDA(table + field, asm.LNG_X),
            asm.EOR(pad + field, asm.LNG_X)]

def _copy_name_src(tag, names_snes, stride, length, wram = False):
    """asm copying a name into the message engine's text buffer.

    A holds the id on entry.  Mirrors vanilla's <item>/<skill> handlers:
    multiply by the table stride, convert each character from the name
    charset to the dialog charset, and stop at the name's $ff padding.

    `wram` reads the name from work ram instead of a rom table (character
    names live at $1602 + 37*id): the data bank is already $7E for the
    text buffer stores, and $7E1602 addresses the same low WRAM the
    vanilla name code reads through the bank $00 mirror.
    """
    copy, done = f"COPY_{tag}", f"DONE_{tag}"
    load = (asm.LDA(names_snes, asm.ABS_X) if wram
            else asm.LDA(names_snes, asm.LNG_X))
    return [
        asm.STA(0x4202, asm.ABS),
        asm.LDA(stride, asm.IMM8),
        asm.STA(0x4203, asm.ABS),
        asm.NOP(),
        asm.NOP(),
        asm.NOP(),
        asm.NOP(),                          # multiplier settle time
        asm.LDX(0x4216, asm.ABS),           # X = id * stride (16-bit X)
        asm.LDY(0x00, asm.DIR),             # Y = text buffer offset
        asm.LDA(0x7e, asm.IMM8),
        asm.PHA(),
        asm.PLB(),                          # data bank = $7E for the stores

        copy,
        load,
        asm.SEC(),
        asm.SBC(TEXT2_TO_TEXT1, asm.IMM8),
        asm.STA(TEXT_BUFFER, asm.ABS_Y),
        asm.CMP(NAME_PAD, asm.IMM8),        # name padding: stop here
        asm.BEQ(done),
        asm.INX(),
        asm.INY(),
        asm.CPY(length, asm.IMM16),
        asm.BNE(copy),

        done,
        asm.TDC(),
        asm.STA(TEXT_BUFFER, asm.ABS_Y),    # terminate the substitution
        asm.TDC(),
        asm.PHA(),
        asm.PLB(),                          # data bank back to $00
        asm.STZ(0xcf, asm.DIR),
        asm.JMP(0x8263, asm.ABS),           # back to the message engine
    ]

def name_codes():
    """Install the <reward>/<reward2> control codes (once)."""
    global _name_codes
    if _name_codes is not None:
        return _name_codes

    src = [
        # dispatch: ours, or the displaced literal-character path
        asm.CMP(REWARD_CODE, asm.IMM8),
        asm.BEQ("REWARD"),
        asm.CMP(REWARD2_CODE, asm.IMM8),
        asm.BEQ("REWARD2"),
        asm.SEC(),                          # displaced from C0/844B
        asm.SBC(0x1b, asm.IMM8),
        asm.JMP(CHAIN_RESUME, asm.ABS),

        # entry state at every control code: A 8-bit, X/Y 16-bit,
        # direct page $00 = current offset into the text buffer
        "REWARD2",
        asm.LDA(REWARD_SLOT, asm.ABS),
        asm.INC(),                        # the reward after this one
        asm.BRA("LOOKUP"),

        "REWARD",
        asm.LDA(REWARD_SLOT, asm.ABS),

        "LOOKUP",
        asm.REP(0x20),                      # X = slot * 2 (entry size)
        asm.AND(0x00ff, asm.IMM16),
        asm.ASL(),
        asm.TAX(),
        asm.SEP(0x20),

        *_decode_slot_src(0),               # kind
        asm.BNE("NOT_ITEM_NAME"),
        *_decode_slot_src(1),               # item id
        *_copy_name_src("ITEM", ITEM_NAMES_SNES, ITEM_NAME_STRIDE, ITEM_NAME_LENGTH),

        "NOT_ITEM_NAME",
        asm.CMP(0x01, asm.IMM8),
        asm.BNE("CHARACTER_NAME"),
        *_decode_slot_src(1),               # esper id
        *_copy_name_src("ESPER", ESPER_NAMES_SNES, ESPER_NAME_STRIDE, ESPER_NAME_LENGTH),

        # character names live in work ram (so renames render right), in
        # the same charset as the rom name tables - the same copy loop
        # with a wram source, exactly as vanilla's own <TERRA>-style
        # codes read them (C0/82CC)
        "CHARACTER_NAME",
        *_decode_slot_src(1),               # character id
        *_copy_name_src("CHARACTER", CHARACTER_NAMES_WRAM,
                        CHARACTER_NAME_STRIDE, CHARACTER_NAME_LENGTH,
                        wram = True),
    ]
    space = Write(Bank.C0, src, "race: <reward>/<reward2> message control codes")
    _name_codes = space.start_address

    space = Reserve(CHAIN_END, CHAIN_END + 2, "race: reward name control code hook")
    space.write(asm.JMP(_name_codes, asm.ABS))
    return _name_codes


ADD_CHECK_REWARD_OPCODE = 0x9e  # unused by vanilla, WC dev and the fork
_add_check_reward_handler = None

def add_check_reward_opcode():
    """Write the reward-grant handler once and return its opcode.

    One command grants any kind: it decodes (kind, id) from the masked
    table and runs the vanilla add-inventory routine, the vanilla
    AddEsper handler, or WC's recruit_character function accordingly.
    It also leaves the slot in $0584 so a receive dialog that follows
    the grant can name it without carrying its own copy.
    """
    global _add_check_reward_handler
    if _add_check_reward_handler is None:
        name_codes()

        src = [
            asm.LDA(0xeb, asm.DIR),         # slot (command operand)
            asm.STA(REWARD_SLOT, asm.ABS),  # for a dialog after the grant
            asm.REP(0x20),                  # X = slot * 2
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),
            asm.TAX(),
            asm.SEP(0x20),

            *_decode_slot_src(0),           # kind
            asm.BNE("NOT_ITEM"),

            *_decode_slot_src(1),           # item id
            asm.STA(0x1a, asm.DIR),         # the add-inventory routine
            asm.STA(0x0583, asm.ABS),       # vanilla's <item> index, as the
                                            # chest path at C0/4C86 sets it
            asm.JSR(0xacfc, asm.ABS),       # vanilla add-to-inventory
            asm.LDA(0x02, asm.IMM8),        # command size (opcode + slot)
            asm.JMP(0x9b5c, asm.ABS),       # next command

            "NOT_ITEM",
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("GRANT_CHARACTER"),

            *_decode_slot_src(1),           # esper id
            asm.CLC(),
            asm.ADC(0x36, asm.IMM8),        # the form the $86 handler reads
            asm.STA(0xeb, asm.DIR),
            asm.JMP(0xadb8, asm.ABS),       # vanilla AddEsper (grant + next)

            "GRANT_CHARACTER",
            *_decode_slot_src(1),           # character id
            asm.STA(0xeb, asm.DIR),         # recruit_character's argument
            asm.JSL(START_ADDRESS_SNES + c0.recruit_character),
            asm.LDA(0x02, asm.IMM8),        # command size (opcode + slot)
            asm.JMP(0x9b5c, asm.ABS),       # next command
        ]
        space = Write(Bank.C0, src, "race: add check reward (decode + grant)")
        _set_opcode_address(ADD_CHECK_REWARD_OPCODE, space.start_address)
        _add_check_reward_handler = space.start_address
    return ADD_CHECK_REWARD_OPCODE

class AddCheckReward(_Instruction):
    """Race builds: grant the reward in a slot, kind decided at runtime."""
    def __init__(self, slot):
        super().__init__(add_check_reward_opcode(), slot)

    def __str__(self):
        return super().__str__(self.args[0])


REWARD_DIALOG_OPCODE = 0xee     # unused by vanilla, WC dev and the fork
_reward_dialog_handler = None

def reward_dialog_opcode():
    """Write the reward-dialog handler once and return its opcode.

    Three bytes, so it drops straight onto a vanilla Dialog command with
    no script shifting.  Its operand is a slot in the masked dialog side
    table, holding the reward slot and two dialog ids; the handler puts
    the reward slot where <reward> will find it, picks the dialog whose
    wording matches the reward's kind, and hands off to $4B at C0/A4BC -
    which advances the script by 3, exactly this command's length.

    Because the dialog decodes the reward itself, it works whether the
    event grants before or after showing the text; and because the kind
    only decides things at runtime, the script looks the same either way.
    """
    global _reward_dialog_handler
    if _reward_dialog_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes
        from obfuscation.rewards import DIALOG_SLOT_SIZE

        name_codes()

        layout = claim.layout(args)
        slots, slots_pad = snes(layout["reward_dialogs"]), snes(layout["reward_dialogs_pad"])

        def dialog_field(offset):
            return [asm.LDA(slots + offset, asm.LNG_X),
                    asm.EOR(slots_pad + offset, asm.LNG_X)]

        src = [
            # X = dialog slot * entry size, via the hardware multiplier
            asm.LDA(0xeb, asm.DIR),
            asm.STA(0x4202, asm.ABS),
            asm.LDA(DIALOG_SLOT_SIZE, asm.IMM8),
            asm.STA(0x4203, asm.ABS),
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),                      # multiplier settle time
            asm.LDX(0x4216, asm.ABS),

            *dialog_field(0),               # reward slot
            asm.STA(REWARD_SLOT, asm.ABS),  # what <reward> will render

            # pick the wording that matches the reward's kind.  X is still
            # the dialog slot offset, so read both ids before touching it
            *dialog_field(1), asm.STA(0xeb, asm.DIR),
            *dialog_field(2), asm.STA(0xec, asm.DIR),
            *dialog_field(3), asm.PHA(),
            *dialog_field(4), asm.PHA(),

            # kind of the reward this dialog names
            asm.LDA(REWARD_SLOT, asm.ABS),
            asm.REP(0x20),
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),
            asm.TAX(),
            asm.SEP(0x20),
            *_decode_slot_src(0),
            asm.CMP(0x01, asm.IMM8),
            asm.BNE("SHOW"),                # not an esper: first wording.
                                            # characters only appear in
                                            # bespoke dialogs, which are
                                            # registered with one wording
                                            # in both ids, so the first is
                                            # always right for them

            asm.PLA(),                      # esper: use the second
            asm.STA(0xec, asm.DIR),
            asm.PLA(),
            asm.STA(0xeb, asm.DIR),
            asm.JMP(0xa4bc, asm.ABS),       # $4B dialog handler (advances 3)

            "SHOW",
            asm.PLA(),                      # discard the esper wording
            asm.PLA(),
            asm.JMP(0xa4bc, asm.ABS),
        ]
        space = Write(Bank.C0, src, "race: reward dialog (decode name + show)")
        _set_opcode_address(REWARD_DIALOG_OPCODE, space.start_address)
        _reward_dialog_handler = space.start_address
    return REWARD_DIALOG_OPCODE

class RewardDialog(_Instruction):
    """Race builds: a dialog naming a reward, decoded at display time."""
    def __init__(self, slot, item_dialog, esper_dialog):
        from obfuscation import rewards
        entry = rewards.register_dialog(slot, item_dialog, esper_dialog)
        # third byte pads to the 3 bytes the vanilla dialog handler
        # advances by
        super().__init__(reward_dialog_opcode(), entry, 0x00)

    def __str__(self):
        return super().__str__(self.args[0])


def _dialog_arg(dialog_id, wait_for_input = True, inside_text_box = True,
                top_of_screen = True):
    """The 16-bit operand the vanilla $4B dialog handler expects: the
    dialog id with the display flags in bits 14-15 (same encoding as
    field.Dialog).  RewardDialog stores this whole value in its side
    table, so the flags survive the indirection."""
    # the handler hands off to the $4B path; $48 (no input wait) has a
    # different handler, and no reward dialog uses it
    assert wait_for_input, "RewardDialog only supports wait_for_input"
    if not inside_text_box and top_of_screen:
        return dialog_id | 0x4000
    elif inside_text_box and not top_of_screen:
        return dialog_id | 0x8000
    elif not inside_text_box and not top_of_screen:
        return dialog_id | 0xc000
    return dialog_id


def reward_dialog(kind, value, dialog_id, second_item = None, **dialog_args):
    """Dialog naming a check reward: opaque in race builds, plain otherwise.

    `second_item` is for a dialog naming two rewards at once; it is
    registered in the next slot and rendered by <reward2>.
    """
    if not args.race:
        import instruction.field as field
        return field.Dialog(dialog_id, **dialog_args)
    from obfuscation import rewards
    if second_item is None:
        slot = rewards.register(kind, value)
    else:
        slot = rewards.register_pair(kind, value, second_item)
    arg = _dialog_arg(dialog_id, **dialog_args)
    return RewardDialog(slot, arg, arg)


def reward_slot_dialog(slot, dialog_id, **dialog_args):
    """Race builds: a bespoke dialog naming an already-registered slot
    (one wording for every kind - <reward> renders the right name)."""
    arg = _dialog_arg(dialog_id, **dialog_args)
    return RewardDialog(slot, arg, arg)


def receive_reward_dialog(slot):
    """Race builds: the standard receive dialog for a slot - vanilla's
    item wording or magicite wording, picked by the decoded kind."""
    from obfuscation import rewards
    item_wording, esper_wording = rewards.wordings()
    return RewardDialog(slot, item_wording, esper_wording)


# --- L3-C: character rewards - the RewardEntity command family ---------
#
# A character check's scene needs the character's id in many more places
# than the grant: the map NPC's sprite and palette, create/show/hide and
# action-queue commands (whose operand - or opcode, for action queues -
# is the entity id, which for party characters IS the character id), the
# party add, the naming screen, the character theme.  Every one of those
# id-valued operands is a placement leak.
#
# One umbrella opcode replaces them all: `$EC sub slot [extra...]`.  Each
# sub-command decodes the character id out of the masked reward table and
# then jumps INTO the corresponding vanilla handler with the id placed
# where that handler's own operand would be ($eb/$ec/$ea), so the runtime
# semantics are exactly vanilla's.  Where the vanilla command is shorter
# than ours (our sub and slot bytes replace its one id byte), the
# sub-handler first advances the script pointer by the difference, so the
# vanilla handler's own "advance by n" lands past our whole command.
#
# An umbrella rather than a dozen opcodes because vanilla only leaves 21
# unused slots in the command table and most are already claimed (WC dev,
# this branch, and the door-rando fork); $EC is one of the last four
# genuinely free bytes ($EC/$ED/$FC/$FF).
REWARD_ENTITY_OPCODE = 0xec     # unused by vanilla, WC dev and the fork

(SUB_CREATE, SUB_DELETE, SUB_SHOW, SUB_HIDE, SUB_WAIT, SUB_SPRITE,
 SUB_PALETTE, SUB_PARTY, SUB_PROPERTIES, SUB_NAME, SUB_THEME, SUB_ACT,
 SUB_LOAD_KIND, SUB_VEHICLE) = range(14)

_reward_entity_handler = None
_character_palette_table = None


def _slot_to_x_src(operand_dp):
    """asm: X = (slot at the given operand byte) * reward entry size."""
    return [
        asm.LDA(operand_dp, asm.DIR),
        asm.REP(0x20),
        asm.AND(0x00ff, asm.IMM16),
        asm.ASL(),
        asm.TAX(),
        asm.SEP(0x20),
    ]


def _decode_id_src(operand_dp):
    """asm: A = character id of the reward slot at the given operand."""
    return [*_slot_to_x_src(operand_dp), *_decode_slot_src(1)]


def _bump_src(tag, count = 1):
    """asm: advance the event script pointer ($e5-$e7, 24-bit) by count.

    Used before jumping into a vanilla handler whose command is `count`
    bytes shorter than ours, so its own final "advance by n" ends up
    exactly past our command.
    """
    src = []
    for i in range(count):
        done = f"BUMPED_{tag}_{i}"
        src += [
            asm.INC(0xe5, asm.DIR),
            asm.BNE(done),
            asm.INC(0xe6, asm.DIR),
            asm.BNE(done),
            asm.INC(0xe7, asm.DIR),
            done,
        ]
    return src


def character_palette_table():
    """rom address of the 16-entry character id -> palette table.

    Allocated (zeroed) with the handler; data.py fills it at write time
    from the build's Characters, because palettes can be customized by
    flags.  Flag-derived, so it is public information and lives in
    plaintext.
    """
    reward_entity_opcode()
    return _character_palette_table


def fill_character_palettes(get_palette):
    """Late-fill the palette table (no-op if no character command was
    ever emitted).  `get_palette` is Characters.get_palette."""
    if _character_palette_table is None:
        return
    from memory.space import Space
    from data.characters import Characters
    values = [get_palette(c) & 0xff for c in range(Characters.CHARACTER_COUNT)]
    Space.rom.set_bytes(_character_palette_table,
                        values + [0x00] * (16 - len(values)))


def reward_entity_opcode():
    """Write the reward-entity sub-handlers once and return the opcode."""
    global _reward_entity_handler, _character_palette_table
    if _reward_entity_handler is not None:
        return REWARD_ENTITY_OPCODE

    from music.song_utils import character_to_song

    NEXT_COMMAND = 0x9b5c
    # vanilla handlers, each entered with the decoded id where its own
    # operand would be (addresses from the vanilla command pointer table)
    VANILLA = {
        "create": 0x9e3c,       # $3D, advance 2
        "delete": 0x9e67,       # $3E, advance 2
        "show": 0xa2fa,         # $41, advance 2
        "hide": 0xa336,         # $42, advance 2
        "wait": 0x9c44,         # $35, advance 2
        "sprite": 0x9c8f,       # $37, advance 3
        "palette": 0x9ca9,      # $43, advance 3
        "party": 0x9d3b,        # $3F, advance 3
        "properties": 0xa07c,   # $40, advance 3
        "name": 0xa03a,         # $7F, advance 3
        "theme": 0xb780,        # $F0, advance 2
        "act": 0x9ba5,          # action queue, entered with A = entity
        "vehicle": 0x9cca,      # $44, advance 3
    }

    # the sixteen-entry character id -> palette and -> theme song tables.
    # both mappings are public (palettes follow from flags, themes are
    # fixed knowledge), so plaintext is fine.
    space = Write(Bank.C0, [bytes(16)], "race: character palette table")
    _character_palette_table = space.start_address
    palette_table_snes = START_ADDRESS_SNES + _character_palette_table

    themes = bytes(character_to_song.get(c, 0) for c in range(16))
    space = Write(Bank.C0, [themes], "race: character theme table")
    theme_table_snes = START_ADDRESS_SNES + space.start_address

    def entity_sub(tag, target):
        # $EC sub slot (3 bytes); vanilla: $op id (2 bytes, reads $eb)
        return [
            *_decode_id_src(0xec),
            asm.STA(0xeb, asm.DIR),
            *_bump_src(tag),
            asm.JMP(target, asm.ABS),
        ]

    def pair_sub(tag, target):
        # $EC sub slot (3 bytes); vanilla: $op id id (3 bytes, and for
        # these commands both operands are the character id)
        return [
            *_decode_id_src(0xec),
            asm.STA(0xeb, asm.DIR),
            asm.STA(0xec, asm.DIR),
            asm.JMP(target, asm.ABS),
        ]

    def table_lookup_src(operand_dp, table_snes):
        # A = table[id of the reward slot at the operand].  TDC before
        # TAX so the high byte of 16-bit X is clean.
        return [
            *_decode_id_src(operand_dp),
            asm.STA(0x1a, asm.DIR),
            asm.TDC(),
            asm.LDA(0x1a, asm.DIR),
            asm.TAX(),
            asm.LDA(table_snes, asm.LNG_X),
        ]

    subs = {}

    subs[SUB_CREATE] = entity_sub("CREATE", VANILLA["create"])
    subs[SUB_DELETE] = entity_sub("DELETE", VANILLA["delete"])
    subs[SUB_SHOW] = entity_sub("SHOW", VANILLA["show"])
    subs[SUB_HIDE] = entity_sub("HIDE", VANILLA["hide"])
    subs[SUB_WAIT] = entity_sub("WAIT", VANILLA["wait"])

    # $EC sub entity slot (4 bytes); vanilla $37: entity sprite.  for
    # party characters the sprite id IS the character id.
    subs[SUB_SPRITE] = [
        *_decode_id_src(0xed),
        asm.PHA(),
        asm.LDA(0xec, asm.DIR),         # entity operand (not secret)
        asm.STA(0xeb, asm.DIR),
        asm.PLA(),
        asm.STA(0xec, asm.DIR),         # decoded id as the sprite
        *_bump_src("SPRITE"),
        asm.JMP(VANILLA["sprite"], asm.ABS),
    ]

    # $EC sub entity slot (4 bytes); vanilla $43: entity palette
    subs[SUB_PALETTE] = [
        *table_lookup_src(0xed, palette_table_snes),
        asm.PHA(),
        asm.LDA(0xec, asm.DIR),
        asm.STA(0xeb, asm.DIR),
        asm.PLA(),
        asm.STA(0xec, asm.DIR),
        *_bump_src("PALETTE"),
        asm.JMP(VANILLA["palette"], asm.ABS),
    ]

    # $EC sub slot party (4 bytes); vanilla $3F: character party
    subs[SUB_PARTY] = [
        *_decode_id_src(0xec),
        asm.STA(0xeb, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xec, asm.DIR),
        *_bump_src("PARTY"),
        asm.JMP(VANILLA["party"], asm.ABS),
    ]

    # vanilla $40/$7F take (character, data index) where the data index
    # equals the character id at every reward site
    subs[SUB_PROPERTIES] = pair_sub("PROPERTIES", VANILLA["properties"])
    subs[SUB_NAME] = pair_sub("NAME", VANILLA["name"])

    # $EC sub slot (3 bytes); vanilla $F0: song
    subs[SUB_THEME] = [
        *table_lookup_src(0xec, theme_table_snes),
        asm.STA(0xeb, asm.DIR),
        *_bump_src("THEME"),
        asm.JMP(VANILLA["theme"], asm.ABS),
    ]

    # $EC sub slot len actions... ; vanilla: id len actions...  The
    # vanilla routine is entered with A = the entity (normally the
    # command byte itself), re-reads it from $ea on the wait path, takes
    # the length byte from $eb, and treats script+2 as the queue start -
    # so give it all three and shift the script pointer under it by our
    # two extra bytes.
    subs[SUB_ACT] = [
        *_decode_id_src(0xec),
        asm.STA(0xea, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xeb, asm.DIR),
        *_bump_src("ACT", 2),
        asm.LDA(0xea, asm.DIR),
        asm.JMP(VANILLA["act"], asm.ABS),
    ]

    # $EC sub slot vehicle (4 bytes); vanilla $44: character vehicle
    subs[SUB_VEHICLE] = [
        *_decode_id_src(0xec),
        asm.STA(0xeb, asm.DIR),
        asm.LDA(0xed, asm.DIR),
        asm.STA(0xec, asm.DIR),
        *_bump_src("VEHICLE"),
        asm.JMP(VANILLA["vehicle"], asm.ABS),
    ]

    # $EC sub slot kind (4 bytes): multipurpose event bit 0 = (the
    # reward's kind == kind).  With the vanilla event-bit branches this
    # gives runtime branching on kind, so one script can carry every
    # kind's scene and a diff cannot tell which one runs.
    import data.event_bit as event_bit
    result_byte = event_bit.address(event_bit.multipurpose(0))
    subs[SUB_LOAD_KIND] = [
        *_slot_to_x_src(0xec),
        *_decode_slot_src(0),           # kind
        asm.CMP(0xed, asm.DIR),
        asm.BEQ("KIND_MATCH"),
        asm.LDA(0x00, asm.IMM8),
        asm.BRA("KIND_STORE"),
        "KIND_MATCH",
        asm.LDA(0x01, asm.IMM8),
        "KIND_STORE",
        asm.STA(result_byte, asm.ABS),
        asm.LDA(0x04, asm.IMM8),        # command size
        asm.JMP(NEXT_COMMAND, asm.ABS),
    ]

    addresses = {}
    for sub, src in subs.items():
        space = Write(Bank.C0, src, f"race: reward entity sub-command {sub}")
        addresses[sub] = space.start_address

    table = b"".join((addresses[sub] & 0xffff).to_bytes(2, "little")
                     for sub in range(len(subs)))
    space = Write(Bank.C0, [table], "race: reward entity dispatch table")
    table_address = space.start_address & 0xffff

    space = Write(Bank.C0, [
        asm.TDC(),
        asm.LDA(0xeb, asm.DIR),         # sub-command
        asm.ASL(),
        asm.TAX(),
        asm.JMP(table_address, asm.ABS_X_16),
    ], "race: reward entity dispatch")
    _set_opcode_address(REWARD_ENTITY_OPCODE, space.start_address)
    _reward_entity_handler = space.start_address
    return REWARD_ENTITY_OPCODE


class _RewardEntityInstruction(_Instruction):
    def __init__(self, sub, *operands):
        super().__init__(reward_entity_opcode(), sub, *operands)

    def __str__(self):
        return super().__str__(f"slot {self.args[1]}")


class CreateRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_CREATE, slot)

class DeleteRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_DELETE, slot)

class ShowRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_SHOW, slot)

class HideRewardEntity(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_HIDE, slot)

class WaitForRewardEntityAct(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_WAIT, slot)

class SetRewardSprite(_RewardEntityInstruction):
    def __init__(self, entity, slot):
        super().__init__(SUB_SPRITE, entity, slot)

    def __str__(self):
        return _Instruction.__str__(self, f"{self.args[1]} slot {self.args[2]}")

class SetRewardPalette(_RewardEntityInstruction):
    def __init__(self, entity, slot):
        super().__init__(SUB_PALETTE, entity, slot)

    def __str__(self):
        return _Instruction.__str__(self, f"{self.args[1]} slot {self.args[2]}")

class AddRewardToParty(_RewardEntityInstruction):
    def __init__(self, slot, party):
        super().__init__(SUB_PARTY, slot, party)

class SetRewardProperties(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_PROPERTIES, slot)

class SetRewardName(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_NAME, slot)

class PlayRewardTheme(_RewardEntityInstruction):
    def __init__(self, slot):
        super().__init__(SUB_THEME, slot)

class SetRewardVehicle(_RewardEntityInstruction):
    def __init__(self, slot, vehicle):
        super().__init__(SUB_VEHICLE, slot, vehicle)


class _RewardEntityAct(_Instruction):
    """Action queue for the reward character - the opaque twin of
    EntityAct, whose opcode byte would otherwise be the character id."""
    def __init__(self, slot, wait_until_complete, *actions):
        import instruction.field.entity as field_entity
        actions = list(actions) + [field_entity.End()]

        self.actions_size = 0
        for action in actions:
            if not isinstance(action, str):
                self.actions_size += len(action)
        self.wait_until_complete = wait_until_complete

        size_wait = self.actions_size
        if wait_until_complete:
            size_wait |= 0x80

        super().__init__(reward_entity_opcode(), SUB_ACT, slot, size_wait)

    def __str__(self):
        result = f"{type(self).__name__}, {self.actions_size} bytes"
        result += ", Wait" if self.wait_until_complete else ", No Wait"
        return result


def RewardEntityAct(slot, wait_until_complete, *actions):
    import instruction.field.entity as field_entity
    RewardEntityAct = type("RewardEntityAct", (_RewardEntityAct,), {})
    return (RewardEntityAct(slot, wait_until_complete, *actions),
            list(actions), field_entity.End())


class RewardEntityActRaw(_RewardEntityInstruction):
    """Header for an action queue whose action bytes are spliced in raw
    (Read from a vanilla script), for relocating a vanilla scene queue
    whose opcode byte was the character id.  `size_wait` is the vanilla
    length byte: action byte count with the wait bit in bit 7.  The
    caller appends exactly that many action bytes (including vanilla's
    own $FF terminator)."""
    def __init__(self, slot, size_wait):
        super().__init__(SUB_ACT, slot, size_wait)


class LoadRewardKind(_RewardEntityInstruction):
    """Multipurpose event bit 0 = (reward in slot is the given kind)."""
    def __init__(self, slot, kind):
        from obfuscation.rewards import KINDS
        if isinstance(kind, str):
            kind = KINDS[kind]
        super().__init__(SUB_LOAD_KIND, slot, kind)


def BranchIfRewardKind(slot, kind, destination):
    import data.event_bit as event_bit
    from instruction.field.instructions import BranchIfEventBitSet
    return (LoadRewardKind(slot, kind),
            BranchIfEventBitSet(event_bit.multipurpose(0), destination))


def BranchIfRewardKindNot(slot, kind, destination):
    import data.event_bit as event_bit
    from instruction.field.instructions import BranchIfEventBitClear
    return (LoadRewardKind(slot, kind),
            BranchIfEventBitClear(event_bit.multipurpose(0), destination))


def UpdateRewardNpc(entity, slot):
    """The NPC updater: repaint a map NPC as the reward character at
    runtime (entrance events run before fade-in, so the player sees
    exactly what a non-race build bakes into the NPC record)."""
    return SetRewardSprite(entity, slot), SetRewardPalette(entity, slot)
