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


# --- availability-aware placement (ruination / away-party safe) -------------
#
# In ruination mode a party can be "away" on another map while the player
# reforms parties at the Narshe school hub (or splits at Phoenix Cave). A
# required character that is away must stay with its away party: adding it to
# the party being formed here would silently pull it across maps and corrupt
# the away party. These helpers therefore guard every placement with the
# character's availability bit, and distribute the available required
# characters round-robin across the parties being formed (the same idea as
# the fixed _KT_*_PARTIES distributions above). Round-robin never forces a
# party to be empty as long as the flow only offers `count` parties when at
# least `count` characters are available -- and two required characters can
# still trade places afterwards via the like-lock swap (see
# menus/required_character_swap.py).

_available_placement_addresses = {}

def available_party_placement(count):
    """Address of a subroutine placing each *available* required character
    into a party, round-robin across the `count` parties being formed."""
    if count in _available_placement_addresses:
        return _available_placement_addresses[count]

    src = []
    for index, character in enumerate(args.required_character_ids):
        src += [
            field.BranchIfEventBitClear(event_bit.character_available(character),
                                        f"SKIP_{index}"),
            field.AddCharacterToParty(character, (index % count) + 1),
            f"SKIP_{index}",
        ]
    src += [field.Return()]

    space = Write(Bank.CA, src,
                  f"require characters: available pre-place for {count}-party select")
    _available_placement_addresses[count] = space.start_address
    return _available_placement_addresses[count]


_remove_available_address = None

def remove_available_characters():
    """Address of a subroutine removing every *available* character from all
    parties, preserving the assignments of away characters.

    The away-party-safe replacement for vanilla's clear bit (opcode 99 with
    bit 7 of the count byte set) at party selects that must pre-place
    required characters. (event/narshe_wob.py builds its own copy of this
    routine for the school reform; kept separate so that non--rc seeds stay
    byte-identical.)"""
    global _remove_available_address
    if _remove_available_address is not None:
        return _remove_available_address

    src = []
    for character in range(CHARACTER_COUNT):
        src += [
            field.BranchIfEventBitClear(event_bit.character_available(character),
                                        f"SKIP_{character}"),
            field.RemoveCharacterFromParties(character),
            f"SKIP_{character}",
        ]
    src += [field.Return()]

    space = Write(Bank.CA, src, "require characters: remove available characters from parties")
    _remove_available_address = space.start_address
    return _remove_available_address
