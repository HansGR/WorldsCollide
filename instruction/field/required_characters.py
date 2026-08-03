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

def one_party_placement():
    """Instructions placing every required character into the single active party."""
    return [field.AddCharacterToParty(character, 1) for character in args.required_character_ids]

def three_party_placement(skip):
    """Instructions distributing the required characters across the three Kefka Tower parties."""
    parties = _KT_SKIP_PARTIES if skip else _KT_NORMAL_PARTIES
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
    for character in required[:-1]:
        src += [field.AddCharacterToParty(character, 1)]
    src += [
        field.AddCharacterToParty(required[-1], 2),
        field.Return(),

        "ALL_REQUIRED_PARTY1",
    ]
    for character in required:
        src += [field.AddCharacterToParty(character, 1)]
    src += [field.Return()]

    space = Write(Bank.CA, src, "require characters: pre-place for two-party select")
    _two_party_placement_address = space.start_address
    return _two_party_placement_address
