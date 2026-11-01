# Helpers for the -rc/--require-characters challenge flag.
#
# Required characters are marked "unmovable" on the party-select screen (see SelectParties in
# instruction/field/instructions.py).  A character that is unmovable but not already placed in a
# party cannot be placed by the player, so required characters must additionally be added to a
# valid party before each party-select screen is shown.  These helpers generate the event code
# that performs that pre-placement for the one-, two- and three-party selection events.
#
# This module lives in instruction.field (rather than the event package) so that the shared
# select-party subroutines in functions.py can pre-place required characters without a circular
# import.
#
# Possess single use (-psu) takes priority: a required character who possessed is no longer
# available and must not be placed (it would be put into a party without being created). With
# -psu the placement is decided at run time from the available bits:
#   - one party: each required character is placed only if available
#   - two parties: the "every available character is required" split puts an available required
#     character into party 2
#   - three parties (Kefka's Tower): the n-th *available* required character goes where the n-th
#     required character would, so the parties a required character fills are filled first
# The party-size gates (instruction/field/available_characters.py) guarantee enough available
# characters for the two and three party selects, so no party is left empty with nobody movable.

import args
import instruction.field.instructions as field
import data.event_bit as event_bit
from constants.entities import CHARACTER_COUNT
from memory.space import Bank, Write

# Distribution of required characters across the three Kefka Tower parties.  The list index is
# the required-character order (as given to -rc); the value is the party the character goes into.
_KT_NORMAL_PARTIES = [3, 1, 2, 3]   # entering the normal location
_KT_SKIP_PARTIES   = [2, 3, 1, 2]   # entering at the switches ("skip")

_two_party_placement_address = None

def _available_placement(characters, parties, label):
    """-psu: instructions placing the available characters (in order) into parties: the n-th
    available one goes into parties[n]. A branch per (character index, placed count) state; label
    makes the labels unique within the write."""
    def state(index, placed):
        return f"{label}_{index}_{placed}"

    src = []
    for index, character in enumerate(characters):
        for placed in range(index + 1):
            src += [
                state(index, placed),
                field.BranchIfEventBitClear(event_bit.character_available(character), state(index + 1, placed)),
                field.AddCharacterToParty(character, parties[placed]),
                field.Branch(state(index + 1, placed + 1)),
            ]
    src += [state(len(characters), placed) for placed in range(len(characters) + 1)]
    return src

def one_party_placement():
    """Instructions placing every required character into the single active party."""
    if args.possess_single_use:
        return _available_placement(args.required_character_ids, [1] * len(args.required_character_ids),
                                    "RC_ONE_PARTY")
    return [field.AddCharacterToParty(character, 1) for character in args.required_character_ids]

def three_party_placement(skip):
    """Instructions distributing the required characters across the three Kefka Tower parties."""
    parties = _KT_SKIP_PARTIES if skip else _KT_NORMAL_PARTIES
    if args.possess_single_use:
        return _available_placement(args.required_character_ids, parties,
                                    "RC_KT_SKIP" if skip else "RC_KT_NORMAL")
    return [field.AddCharacterToParty(character, parties[index])
            for index, character in enumerate(args.required_character_ids)]

def two_party_placement():
    """Address of a subroutine that pre-places the required characters before a two-party select
    (Narshe Battle, Phoenix Cave).

    Required characters are unmovable, so they must be pre-placed into a party.  If at least one
    non-required character is available to fill the second party, all required characters are
    placed in party 1.  If every available character is required, the last required character is
    placed in party 2 so that neither party is forced to be empty.

    The subroutine is shared between callers and only generated once."""
    global _two_party_placement_address
    if _two_party_placement_address is not None:
        return _two_party_placement_address

    required = args.required_character_ids
    non_required = [character for character in range(CHARACTER_COUNT)
                    if character not in required]

    src = []
    # if any non-required character is available it can fill the second party, so keep every
    # required character together in party 1
    for character in non_required:
        src += [field.BranchIfEventBitSet(event_bit.character_available(character), "ALL_REQUIRED_PARTY1")]

    # otherwise every available character is required: split them so party 2 is not empty
    if args.possess_single_use:
        # the last available required character goes into party 2 (walk the list backwards: the
        # first one found goes into party 2, the rest into party 1)
        src += _available_placement(list(reversed(required)), [2] + [1] * (len(required) - 1),
                                    "RC_SPLIT")
    else:
        for character in required[:-1]:
            src += [field.AddCharacterToParty(character, 1)]
        src += [
            field.AddCharacterToParty(required[-1], 2),
        ]
    src += [
        field.Return(),

        "ALL_REQUIRED_PARTY1",
    ]
    if args.possess_single_use:
        src += _available_placement(required, [1] * len(required), "RC_TOGETHER")
    else:
        for character in required:
            src += [field.AddCharacterToParty(character, 1)]
    src += [field.Return()]

    space = Write(Bank.CA, src, "require characters: pre-place for two-party select")
    _two_party_placement_address = space.start_address
    return _two_party_placement_address
