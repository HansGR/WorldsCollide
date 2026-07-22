from objectives.results._objective_result import *
from objectives.results._apply_characters_party import ApplyToCharacters

CURRENT_HP_ADDRESS = 0x1609
MAX_HP_ADDRESS = 0x160b     # bbhhhhhh hhhhhhhh, b = equipment hp boost, h = max hp
MAX_HP_MASK = 0x3fff
HP_BOOST_MASK = 0xc000
MAX_HP = 9999
MIN_HP = 1

# max hp is a 14 bit value so the amount cannot be passed in the 8 bit
# field.LongCall argument like the other stats, bake it into the routine instead

def AddMaxHP(amount):
    return [
        asm.A16(),
        asm.LDA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.AND(HP_BOOST_MASK, asm.IMM16),
        asm.PHA(),                              # save equipment hp boost bits
        asm.LDA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.AND(MAX_HP_MASK, asm.IMM16),        # a = max hp
        asm.CLC(),
        asm.ADC(amount, asm.IMM16),
        asm.CMP(MAX_HP + 1, asm.IMM16),
        asm.BLT("STORE_MAX"),                   # if <= 9999, skip to STORE_MAX
        asm.LDA(MAX_HP, asm.IMM16),             # else, cap at 9999

        "STORE_MAX",
        asm.STA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.PLA(),
        asm.ORA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.STA(MAX_HP_ADDRESS, asm.ABS_Y),     # restore equipment hp boost bits
        asm.A8(),
    ]

def SubMaxHP(amount):
    return [
        asm.A16(),
        asm.LDA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.AND(HP_BOOST_MASK, asm.IMM16),
        asm.PHA(),                              # save equipment hp boost bits
        asm.LDA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.AND(MAX_HP_MASK, asm.IMM16),        # a = max hp
        asm.SEC(),
        asm.SBC(amount, asm.IMM16),
        asm.BCC("MINIMUM"),                     # if borrowed, set to minimum
        asm.CMP(MIN_HP, asm.IMM16),
        asm.BGE("STORE_MAX"),                   # if >= 1, skip to STORE_MAX

        "MINIMUM",
        asm.LDA(MIN_HP, asm.IMM16),

        "STORE_MAX",
        asm.STA(MAX_HP_ADDRESS, asm.ABS_Y),     # boost bits clear until restored below

        asm.LDA(CURRENT_HP_ADDRESS, asm.ABS_Y),
        asm.CMP(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.BLT("CURRENT_OK"),
        asm.BEQ("CURRENT_OK"),
        asm.LDA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.STA(CURRENT_HP_ADDRESS, asm.ABS_Y), # clamp current hp to new max hp

        "CURRENT_OK",
        asm.PLA(),
        asm.ORA(MAX_HP_ADDRESS, asm.ABS_Y),
        asm.STA(MAX_HP_ADDRESS, asm.ABS_Y),     # restore equipment hp boost bits
        asm.A8(),
    ]

_routines = {}
def _routine(count):
    if count not in _routines:
        if count > 0:
            src = ApplyToCharacters(AddMaxHP(count))
            description = f"add max hp all {count}"
        else:
            src = ApplyToCharacters(SubMaxHP(-count))
            description = f"sub max hp all {-count}"
        src += [
            asm.RTL(),
        ]
        _routines[count] = Write(Bank.F0, src, description).start_address
    return _routines[count]

class Field(field_result.Result):
    def src(self, count):
        if count == 0:
            return []
        return [
            field.LongCall(START_ADDRESS_SNES + _routine(count)),
        ]

class Battle(battle_result.Result):
    def src(self, count):
        if count == 0:
            return []
        return [
            asm.JSL(START_ADDRESS_SNES + _routine(count)),
        ]

class Result(ObjectiveResult):
    NAME = "MaxHP All"
    def __init__(self, min_count, max_count):
        self.count = random.randint(min_count, max_count)
        super().__init__(Field, Battle, self.count)
