"""L2 - mask the relocated tables (race builds).

Every relocated table is stored XORed with a per-seed keystream ("pad")
of its own size, placed independently inside the claim.  The reader
shims (obfuscation/relocate.py) decode on access with a single EOR, so
gameplay cost is a few cycles at chest-open/menu/battle-end frequency.

What this buys, per the plan's threat model: a tool that finds the
moved tables by following the reader operands can no longer assume
plaintext - it must also follow the shim code to the pad and reimplement
the decode, i.e. behave like a faithful reimplementation of the game's
own reader.  It is deliberately not cryptography (the generator is open
source; the seed is the only secret, and the whole layout and keystream
rotate per seed and per release).

The decoys at the vanilla addresses stay plaintext on purpose: their
job is to be read.

apply_all() runs once at the end of Data.write(), after every table has
written its plaintext into the claim and before the rom is emitted.
"""

import obfuscation
from obfuscation import claim


def pad_bytes(args, table, size):
    """The table's keystream: a domain-separated pure function of the
    nonce, so shims and verification can regenerate it."""
    rng = obfuscation.rng_for_args(args, "mask/" + table)
    return bytes(rng.getrandbits(8) for _ in range(size))


def apply_all(args, rom):
    """XOR every relocated table with its pad and store the pads."""
    layout = claim.layout(args)

    # chest pointer sentinel: the map-load reader fetches one entry past
    # the pointer table for the final map's end bound.  equal start and
    # end bounds = the final map has no chests (true in vanilla)
    base = layout["chest_ptrs"]
    rom.set_bytes(base + 0x340, rom.get_bytes(base + 0x33e, 2))

    for table in claim.TABLE_SIZES:
        size = claim.sizeof(table)
        pad = pad_bytes(args, table, size)
        base = layout[table]
        plain = rom.get_bytes(base, size)
        rom.set_bytes(base, [b ^ p for b, p in zip(plain, pad)])
        rom.set_bytes(layout[table + "_pad"], list(pad))
