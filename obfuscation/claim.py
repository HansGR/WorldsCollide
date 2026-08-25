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
CLAIM_END   = 0x347fff   # 32 KB claimed; L1 tables + L2 pads use ~17 KB

# name -> table size in bytes (vanilla sizes; these do not change).
# every table also gets an equal-size "<name>_pad" region holding the
# L2 xor keystream, placed independently inside the claim (see mask.py)
TABLE_SIZES = {
    "chest_ptrs":  0x342,  # 0x2d82f4-0x2d8633, plus a 2-byte sentinel:
                           # the map-load reader fetches one entry past
                           # the pointer table for the final map's end
                           # bound (contiguous data in vanilla, arbitrary
                           # neighbors in the claim), so the relocated
                           # table carries an explicit empty bound
    "chest_data":  0x827,  # 0x2d8634-0x2d8e5a
    "shop_data":   0x480,  # 0x47ac0-0x47f3f
    "esper_data":  0x200,  # 0x186e00-0x186fff (spells/rates/bonus)
    "enemy_items": 0x600,  # 0xf3000-0xf35ff (steals/drops)
    "coliseum":    0x400,  # 0x1fb600-0x1fb9ff (matches)
    # L3 reward tables: new (no vanilla address), one byte per check
    # grant, indexed by the custom opcode's 1-byte operand - so each is
    # capped at 256.  item ~100-110 grants/seed; esper ~20-27.  If a seed
    # ever exceeds 256 grants the index would need a second byte
    # (rewards.write_tables asserts the count fits).  Masked like the rest.
    "item_rewards":  0x100,
    "esper_rewards": 0x40,
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

    names = sorted(TABLE_SIZES) + sorted(name + "_pad" for name in TABLE_SIZES)
    rng.shuffle(names)   # sorted first: dict order is not contract

    total = sum(sizeof(name) for name in names)
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
        address += sizeof(name)
    return _layout


def sizeof(name):
    """Size in bytes of a claim entry (table or its equal-size pad)."""
    if name.endswith("_pad"):
        name = name[:-len("_pad")]
    return TABLE_SIZES[name]


def snes(rom_offset):
    """SNES (HiROM) address of a rom offset."""
    return 0xc00000 + rom_offset
