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

# Field opcodes for the race commands.  Vanilla leaves $64-$69, $9E-$9F,
# $E6, $EE and a few others unused (they share the unused-opcode stub in
# the pointer table, and the Event Command List doc shows the vanilla set
# jumping $63 -> $6A).  These three are additionally unclaimed by both WC
# dev and the door randomizer fork, which already uses $66-$69 - so a
# future merge of the two feature sets does not collide.  Claiming an
# opcode reserves its pointer-table slot, so any collision that did arise
# would fail the build (see _set_opcode_address).
ADD_CHECK_ITEM_OPCODE = 0x9e
_add_check_item_handler = None

def add_check_item_opcode():
    """Write the race item-decode handler once and return its opcode.

    The handler reads a one-byte index (the command operand at $eb) into
    the relocated + masked item-reward table (obfuscation/rewards.py),
    decodes it, hands the id to the vanilla add-item routine at C0/ACFC,
    and leaves the id at direct-page $1A so a single shared "Received the
    <item>!" dialog (field message code $1A) renders the real name at
    runtime.  Nothing in the script or a fixed rom address names the
    reward at its check.
    """
    global _add_check_item_handler
    if _add_check_item_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes

        layout = claim.layout(args)
        table = snes(layout["item_rewards"])
        pad = snes(layout["item_rewards_pad"])

        src = [
            # X/Y must STAY 16-bit: the event engine and the C0/ACFC
            # inventory scan (CPX #$0100) both depend on it.  standard
            # idiom to index with a byte: clear 16-bit A, load, transfer
            asm.TDC(),                     # clear the full accumulator
            asm.LDA(0xeb, asm.DIR),        # reward index (command operand)
            asm.TAX(),                     # X = index, high byte zero
            asm.LDA(table, asm.LNG_X),     # masked item id
            asm.EOR(pad, asm.LNG_X),       # decoded item id (8-bit A)
            asm.STA(0x1a, asm.DIR),        # DP $1A: the add-inventory routine
            asm.STA(0x0583, asm.ABS),      # $0583: the <item> dialog's name index
                                           # (both set, exactly as the vanilla
                                           # found-item flow at C0/4C86 does)
            asm.JSR(0xacfc, asm.ABS),      # vanilla add-to-inventory (uses $1A)
            asm.LDA(0x02, asm.IMM8),       # command size (opcode + index)
            asm.JMP(0x9b5c, asm.ABS),      # next command
        ]
        space = Write(Bank.C0, src, "race: add check item (decode + grant)")
        _set_opcode_address(ADD_CHECK_ITEM_OPCODE, space.start_address)
        _add_check_item_handler = space.start_address
    return ADD_CHECK_ITEM_OPCODE

class AddCheckItem(_Instruction):
    """Drop-in for AddItem in race builds (see add_check_item_opcode)."""
    def __init__(self, index):
        super().__init__(add_check_item_opcode(), index)

    def __str__(self):
        return super().__str__(self.args[0])

ADD_CHECK_ESPER_OPCODE = 0x9f   # (unused by vanilla, WC dev and the door rando fork)
_add_check_esper_handler = None

def add_check_esper_opcode():
    """Write the race esper-decode handler once and return its opcode.

    Mirror of add_check_item_opcode for espers: reads a one-byte index
    (the command operand at $eb) into the relocated + masked esper-reward
    table, decodes the esper id, then reuses the vanilla AddEsper handler
    ($86 at C0/ADB8) for the actual grant - which already sets the
    owned-esper bit and (via the ESPERS_FOUND patch) bumps the found
    counter.  The receive dialog is a generic "Received the Magicite!"
    (there is no <esper> renderer), so no esper name sits in the rom next
    to a check.
    """
    global _add_check_esper_handler
    if _add_check_esper_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes

        layout = claim.layout(args)
        table = snes(layout["esper_rewards"])
        pad = snes(layout["esper_rewards_pad"])

        src = [
            asm.TDC(),                     # clear the full accumulator
            asm.LDA(0xeb, asm.DIR),        # reward index (command operand)
            asm.TAX(),                     # X = index, high byte zero (16-bit X)
            asm.LDA(table, asm.LNG_X),     # masked esper id
            asm.EOR(pad, asm.LNG_X),       # decoded esper id (0..26)
            asm.CLC(),
            asm.ADC(0x36, asm.IMM8),       # + 0x36: the form the $86 handler reads
            asm.STA(0xeb, asm.DIR),        # hand it to the vanilla esper grant
            asm.JMP(0xadb8, asm.ABS),      # $86 AddEsper handler (grant + found + next)
        ]
        space = Write(Bank.C0, src, "race: add check esper (decode + grant)")
        _set_opcode_address(ADD_CHECK_ESPER_OPCODE, space.start_address)
        _add_check_esper_handler = space.start_address
    return ADD_CHECK_ESPER_OPCODE

class AddCheckEsper(_Instruction):
    """Drop-in for AddEsper in race builds (see add_check_esper_opcode)."""
    def __init__(self, esper_index):
        super().__init__(add_check_esper_opcode(), esper_index)

    def __str__(self):
        return super().__str__(self.args[0])

# ---------------------------------------------------------------------------
# race builds: render an esper name inside a dialog at runtime
#
# Vanilla has message control codes that substitute a name into dialog text:
# $1A <item> (item names, 13-byte entries at $D2B300) and $1B <skill>.  Each
# reads an index from a fixed ram byte, converts the name from the item/esper
# TEXT2 charset to the dialog TEXT1 charset (SBC #$60) and copies it into the
# text buffer at $7E9183.  There is no such code for espers, so L3 adds one:
# $1C <esper>, which renders the esper whose id is in $0583 (the same byte the
# item code uses for its index - the two never appear in one dialog).
#
# The control-code dispatch chain in bank C0 ends at C0/844B, where a byte
# that matched no code falls through to `SEC : SBC #$1b` (the literal
# character path).  Hooking there is additive: the new code is tested last,
# and anything else takes the displaced original path unchanged.
# ---------------------------------------------------------------------------

# --- runtime name rendering -------------------------------------------
# Codes installed by chaining onto the end of the control-code dispatch
# chain: each one is tested in turn, and a byte matching none of them
# takes the displaced original literal-character path.
#
#   $1C <esper>  esper name from $0583   (the byte vanilla's <item> uses)
#   $1D <item2>  item name from $0584    (the byte vanilla's <skill> uses)
#
# <item2> exists because one dialog can name two rewards - the Narshe WOR
# choice offers "Leave it X" against "Make it Y" - and a single ram byte
# can only carry one of them.
CHAIN_END = 0x0844b             # C0/844B: SEC : SBC #$1b, the literal path
CHAIN_RESUME = 0x844e

ESPER_NAME_CODE = 0x1c
ESPER_NAME_INDEX = 0x0583
ESPER_NAMES_SNES = 0xe6f6e1     # 8 bytes/entry, $ff padded
ESPER_NAME_LENGTH = 8

ITEM2_NAME_CODE = 0x1d
ITEM2_NAME_INDEX = 0x0584
ITEM_NAMES_SNES = 0xd2b301      # 13 bytes/entry: icon byte then 12 chars
ITEM_NAME_LENGTH = 12
ITEM_NAME_STRIDE = 13

_name_codes = None

def _render_name_src(code, index_address, names_snes, stride, length, next_test):
    """asm for one name-substitution control code.

    Mirrors vanilla's <item>/<skill> handlers: multiply the id in
    `index_address` by the table stride, copy the name into the message
    engine's text buffer converting from the name charset to the dialog
    charset, and stop at the name's $ff padding.

    Entry state (as at every control code): A 8-bit, X/Y 16-bit, direct
    page $00 = the current offset into the text buffer.
    """
    TEXT_BUFFER = 0x9183        # $7E9183
    TEXT2_TO_TEXT1 = 0x60
    PAD = 0xff - TEXT2_TO_TEXT1

    label = f"RENDER_{code:02X}"
    copy = f"COPY_{code:02X}"
    done = f"DONE_{code:02X}"

    src = [
        asm.CMP(code, asm.IMM8),
        asm.BEQ(label),
        *next_test,

        label,
        # id * stride via the hardware multiplier, exactly as vanilla's
        # own <item>/<skill> handlers do (no direct-page scratch needed)
        asm.LDA(index_address, asm.ABS),
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
        asm.LDA(names_snes, asm.LNG_X),
        asm.SEC(),
        asm.SBC(TEXT2_TO_TEXT1, asm.IMM8),
        asm.STA(TEXT_BUFFER, asm.ABS_Y),
        asm.CMP(PAD, asm.IMM8),             # name padding: stop here
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
    return src

def name_codes():
    """Install the <esper> and <item2> control codes (once).

    Hooks the end of the control-code chain, where a byte that matched no
    vanilla code falls through to the literal-character path - so the new
    codes are tested last and everything else is unaffected.
    """
    global _name_codes
    if _name_codes is not None:
        return _name_codes

    literal_path = [
        asm.SEC(),                          # displaced from C0/844B
        asm.SBC(0x1b, asm.IMM8),
        asm.JMP(CHAIN_RESUME, asm.ABS),
    ]
    src = _render_name_src(
        ESPER_NAME_CODE, ESPER_NAME_INDEX, ESPER_NAMES_SNES, 8,
        ESPER_NAME_LENGTH,
        next_test=_render_name_src(
            ITEM2_NAME_CODE, ITEM2_NAME_INDEX, ITEM_NAMES_SNES,
            ITEM_NAME_STRIDE, ITEM_NAME_LENGTH, next_test=literal_path))

    space = Write(Bank.C0, src, "race: <esper>/<item2> message control codes")
    _name_codes = space.start_address

    space = Reserve(CHAIN_END, CHAIN_END + 2, "race: name control code hook")
    space.write(asm.JMP(_name_codes, asm.ABS))
    return _name_codes

def esper_name_code():
    return name_codes()


ESPER_DIALOG_OPCODE = 0xe6      # ditto
_esper_dialog_handler = None

def esper_dialog_opcode(dialog_id):
    """Write the race esper-dialog handler once and return its opcode.

    Displays the shared "Received the Magicite <esper>" dialog with the
    esper name filled in at runtime.  The command carries a one-byte index
    into the masked esper-reward table (never the esper id), decodes it into
    $0583 for the <esper> code, then hands off to the vanilla dialog handler
    ($4B at C0/A4BC) - which reads the dialog id from $eb/$ec and advances
    the script by 3, exactly this command's length (opcode + index + pad).

    Carrying its own index makes the command independent of whether the
    event grants the esper before or after showing the dialog (both orders
    occur in the event scripts).
    """
    global _esper_dialog_handler
    if _esper_dialog_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes

        esper_name_code()       # the dialog is useless without the renderer

        layout = claim.layout(args)
        table = snes(layout["esper_rewards"])
        pad = snes(layout["esper_rewards_pad"])

        src = [
            asm.TDC(),                          # clear the full accumulator
            asm.LDA(0xeb, asm.DIR),             # reward index (command operand)
            asm.TAX(),                          # X = index, high byte zero
            asm.LDA(table, asm.LNG_X),          # masked esper id
            asm.EOR(pad, asm.LNG_X),            # decoded esper id
            asm.STA(ESPER_NAME_INDEX, asm.ABS), # what <esper> will render

            # hand the shared dialog id to the vanilla dialog command
            asm.LDA(dialog_id & 0xff, asm.IMM8),
            asm.STA(0xeb, asm.DIR),
            asm.LDA((dialog_id >> 8) & 0xff, asm.IMM8),
            asm.STA(0xec, asm.DIR),
            asm.JMP(0xa4bc, asm.ABS),           # $4B dialog handler (advances 3)
        ]
        space = Write(Bank.C0, src, "race: esper receive dialog (decode + show)")
        _set_opcode_address(ESPER_DIALOG_OPCODE, space.start_address)
        _esper_dialog_handler = space.start_address
    return ESPER_DIALOG_OPCODE


REWARD_DIALOG_OPCODE = 0xee     # unused by vanilla, WC dev and the fork
_reward_dialog_handler = None

def reward_dialog_opcode():
    """Write the reward-dialog handler once and return its opcode.

    Several events write their own dialog text naming a check reward
    ("Make it “X”", "X SLEEPS HERE", ...).  In race builds that text uses
    the <item>/<esper> control code instead, and the Dialog command that
    shows it is replaced by this one - same three bytes, so it drops
    straight onto a vanilla Dialog with no script shifting.

    The operand is a slot in the masked side table (obfuscation/rewards.py
    register_dialog), holding the opaque reward index, its kind, and the
    dialog to show.  The handler decodes the reward into $0583 for the
    control code, puts the dialog id where the vanilla dialog command
    expects it, and hands off to $4B at C0/A4BC - which advances the
    script by 3, exactly this command's length.

    This works whether the event grants the reward before or after the
    dialog, because the dialog decodes the name itself.
    """
    global _reward_dialog_handler
    if _reward_dialog_handler is None:
        from obfuscation import claim
        from obfuscation.claim import snes

        esper_name_code()       # <esper> may be used by these dialogs

        layout = claim.layout(args)
        item_table, item_pad = snes(layout["item_rewards"]), snes(layout["item_rewards_pad"])
        esper_table, esper_pad = snes(layout["esper_rewards"]), snes(layout["esper_rewards_pad"])
        slots, slots_pad = snes(layout["reward_dialogs"]), snes(layout["reward_dialogs_pad"])

        def slot_field(offset):
            # one masked byte of the current slot (X = slot * slot size)
            return [asm.LDA(slots + offset, asm.LNG_X),
                    asm.EOR(slots_pad + offset, asm.LNG_X)]

        def reward_index_to_x():
            # A holds the opaque reward index; make it a 16-bit X
            return [asm.REP(0x20), asm.AND(0x00ff, asm.IMM16),
                    asm.TAX(), asm.SEP(0x20)]

        from obfuscation.rewards import DIALOG_SLOT_SIZE

        def slot_to_x():
            # X = slot * slot size, from the command operand still in $eb
            return [
                asm.LDA(0xeb, asm.DIR),
                asm.STA(0x4202, asm.ABS),
                asm.LDA(DIALOG_SLOT_SIZE, asm.IMM8),
                asm.STA(0x4203, asm.ABS),
                asm.NOP(),
                asm.NOP(),
                asm.NOP(),
                asm.NOP(),                      # multiplier settle time
                asm.LDX(0x4216, asm.ABS),
            ]

        src = [
            # the optional second name first, because decoding a reward
            # index clobbers X; $eb still holds the slot, so X can simply
            # be recomputed for the primary name afterwards
            *slot_to_x(),
            *slot_field(5),                 # second name present?
            asm.BEQ("PRIMARY"),
            *slot_field(4),                 # opaque item index
            *reward_index_to_x(),
            asm.LDA(item_table, asm.LNG_X),
            asm.EOR(item_pad, asm.LNG_X),
            asm.STA(0x0584, asm.ABS),       # what <item2> renders

            "PRIMARY",
            *slot_to_x(),

            # the dialog id next: $eb/$ec are where $4B reads it from, and
            # they are free once the slot has been read out of them
            *slot_field(2), asm.STA(0xeb, asm.DIR),
            *slot_field(3), asm.STA(0xec, asm.DIR),

            *slot_field(1),                 # kind
            asm.BNE("ESPER"),

            *slot_field(0),                 # item: opaque reward index
            *reward_index_to_x(),
            asm.LDA(item_table, asm.LNG_X),
            asm.EOR(item_pad, asm.LNG_X),
            asm.BRA("SHOW"),

            "ESPER",
            *slot_field(0),                 # esper: opaque reward index
            *reward_index_to_x(),
            asm.LDA(esper_table, asm.LNG_X),
            asm.EOR(esper_pad, asm.LNG_X),

            "SHOW",
            asm.STA(0x0583, asm.ABS),       # what <item>/<esper> renders
            asm.JMP(0xa4bc, asm.ABS),       # $4B dialog handler (advances 3)
        ]
        space = Write(Bank.C0, src, "race: reward dialog (decode name + show)")
        _set_opcode_address(REWARD_DIALOG_OPCODE, space.start_address)
        _reward_dialog_handler = space.start_address
    return REWARD_DIALOG_OPCODE

class RewardDialog(_Instruction):
    """Race builds: show a dialog that names a reward, decoded at runtime.

    Three bytes, like the vanilla Dialog command it replaces.
    """
    def __init__(self, kind, value, dialog_id, second_item=None):
        from obfuscation import rewards
        slot = rewards.register_dialog(kind, value, dialog_id, second_item)
        # third byte pads to the 3 bytes the vanilla dialog handler
        # advances by
        super().__init__(reward_dialog_opcode(), slot, 0x00)

    def __str__(self):
        return super().__str__(self.args[0])


def reward_dialog(kind, value, dialog_id, second_item=None, **dialog_args):
    """Dialog naming a check reward: opaque in race builds, plain otherwise.

    `second_item` is for a dialog naming two rewards at once; it renders
    through <item2>.
    """
    if args.race:
        return RewardDialog(kind, value, dialog_id, second_item)
    import instruction.field as field
    return field.Dialog(dialog_id, **dialog_args)
