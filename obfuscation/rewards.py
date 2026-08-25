"""L3 - check-reward indirection (race builds).

A check that grants an item or an esper does it with an event command
whose operand is the item/esper id in plaintext, sitting in the event
script - the single most valuable thing for a cheater to grep, at every
check.

In race builds each grant instead carries an opaque one-byte *index*
into a per-seed relocated + masked reward table (one table per reward
kind, in the obfuscation claim, masked exactly like the L1/L2 tables).
A custom field opcode decodes the id at grant time and hands it to the
vanilla grant routine; the receive dialog is neutralised so the reward
name is not spelled out in the rom next to the check (items render the
real name at runtime via the <item> code; espers use one generic
"Received the Magicite!" dialog, since there is no <esper> renderer).

Flow across a build:
  1. event generation calls AddItem/AddEsper; in race mode `register()`
     records the id under its kind and returns its index, which is what
     lands in the script.
  2. Data.write() calls `write_tables()` to lay the collected ids into
     the claim as plaintext.
  3. the end-of-write masking pass (obfuscation/mask.py) XORs each table
     with its pad like every other relocated table.
"""

# reward kind -> claim table name
TABLES = {
    "item": "item_rewards",
    "esper": "esper_rewards",
}

_collected = {kind: [] for kind in TABLES}


def reset():
    """Start a fresh build's collection (safe to call between in-process
    builds; a normal wc.py run is one process and starts empty)."""
    global _collected
    _collected = {kind: [] for kind in TABLES}


def register(kind, value):
    """Record one granted id of the given kind, returning its index."""
    _collected[kind].append(value & 0xff)
    return len(_collected[kind]) - 1


def count(kind):
    return len(_collected[kind])


def write_tables(rom, args):
    """Lay every kind's collected ids into the claim as plaintext
    (masked later by obfuscation.mask.apply_all)."""
    from obfuscation import claim
    layout = claim.layout(args)
    for kind, table in TABLES.items():
        ids = _collected[kind]
        size = claim.TABLE_SIZES[table]
        # the opcode operand is one byte, so 256 is the hard index cap
        # regardless of table size
        assert len(ids) <= min(size, 256), (
            f"race: {len(ids)} {kind} reward checks exceed the 256 a "
            f"one-byte index can address; widen the index/operand")
        # unused slots are 0xff (an invalid id) so a stray decode is
        # visibly wrong rather than a plausible fake
        rom.set_bytes(layout[table], ids + [0xff] * (size - len(ids)))
