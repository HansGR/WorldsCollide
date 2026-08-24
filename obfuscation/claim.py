"""Explicit expanded-ROM claim for race obfuscation data.

All ROM bytes the race obfuscation layers place live inside this single
claimed range, and every placement is computed relative to CLAIM_START -
so if the claim ever collides with another feature, moving it is a
one-line change here and nothing else cares.

Known users of expanded ROM space to coordinate with:
  - WC itself allocates code/data in bank F0 (and touches F2).
  - The door randomizer (fork) relocates event pointers into expanded
    space.
  - External music randomizers place music data in expanded space.

The claim is registered with the memory allocator via Reserve(), which
removes it from the free-space heap and makes any overlapping
reservation by another feature fail loudly at build time.

Placement inside the claim is per-seed: the tables land in a
nonce-shuffled order at nonce-random offsets, so their locations are
not fixed across race ROMs.
"""

import obfuscation

CLAIM_START = 0x340000   # ROM offset (SNES $F4:0000)
CLAIM_END   = 0x343fff   # 16 KB claimed; Phase 1 uses ~4 KB

# name -> table size in bytes (vanilla sizes; these do not change)
TABLE_SIZES = {
    "chest_ptrs": 0x340,   # 0x2d82f4-0x2d8633
    "chest_data": 0x827,   # 0x2d8634-0x2d8e5a
    "shop_data":  0x480,   # 0x47ac0-0x47f3f
}

_layout = None


def layout(args):
    """Per-seed placement of the relocated tables inside the claim.

    Returns {table name: rom offset}.  First call reserves the claim
    with the allocator.  Deterministic for a given seed+flags+version.
    """
    global _layout
    if _layout is not None:
        return _layout

    from memory.space import Reserve
    Reserve(CLAIM_START, CLAIM_END, "race obfuscation claim")

    rng = obfuscation.rng_for_args(args, "claim/layout")

    names = sorted(TABLE_SIZES)   # sort first: dict order is not contract
    rng.shuffle(names)

    total = sum(TABLE_SIZES[name] for name in names)
    slack = (CLAIM_END - CLAIM_START + 1) - total
    assert slack >= 0, "race obfuscation claim too small for its tables"

    # uniformly partition the slack into a gap before each table
    cuts = sorted(rng.randrange(slack + 1) for _ in names)
    previous = 0
    address = CLAIM_START
    _layout = {}
    for name, cut in zip(names, cuts):
        address += cut - previous
        previous = cut
        _layout[name] = address
        address += TABLE_SIZES[name]
    return _layout


def snes(rom_offset):
    """SNES (HiROM) address of a rom offset."""
    return 0xc00000 + rom_offset
