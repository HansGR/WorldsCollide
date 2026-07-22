from objectives.results._objective_result import *
from objectives.results._apply_characters_party import ApplyToCharacter
from objectives.results.max_hp_all import AddMaxHP, SubMaxHP

_routines = {}
def _routine(character, count):
    key = (character, count)
    if key not in _routines:
        if count > 0:
            src = ApplyToCharacter(character, AddMaxHP(count))
            description = f"add max hp {character} {count}"
        else:
            src = ApplyToCharacter(character, SubMaxHP(-count))
            description = f"sub max hp {character} {-count}"
        src += [
            asm.RTL(),
        ]
        _routines[key] = Write(Bank.F0, src, description).start_address
    return _routines[key]

class Field(field_result.Result):
    def src(self, count, character_name, character):
        if count == 0:
            return []
        return [
            field.LongCall(START_ADDRESS_SNES + _routine(character, count)),
        ]

class Battle(battle_result.Result):
    def src(self, count, character_name, character):
        if count == 0:
            return []
        return [
            asm.JSL(START_ADDRESS_SNES + _routine(character, count)),
        ]

class Result(ObjectiveResult):
    NAME = "MaxHP Random"
    def __init__(self, min_count, max_count):
        from constants.entities import id_character, CHARACTER_COUNT
        character = random.randint(0, CHARACTER_COUNT - 1)
        character_name = id_character[character]

        count = random.randint(min_count, max_count)
        super().__init__(Field, Battle, count, character_name, character)
