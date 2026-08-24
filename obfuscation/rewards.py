"""L3 - item-reward indirection (race builds).

A check that grants an item does it with event command $80 (AddItem),
whose operand is the item id in plaintext, sitting in the event script -
the single most valuable thing for a cheater to grep, at every check.

In race builds each grant instead carries an opaque one-byte *index*
into a per-seed relocated + masked reward table (in the obfuscation
claim, masked exactly like the L1/L2 tables).  A custom field opcode
(instruction/field/custom.py AddCheckItem) decodes T[index] at grant
time and hands the id to the vanilla add-item routine, and one shared
"Received the <item>!" dialog renders the decoded name at runtime (the
field message code <item> reads the same direct-page byte the grant
just set), so nothing in the rom statically names the reward at its
check.

Flow across a build:
  1. event generation calls AddItem; in race mode `register()` records
     the id and returns its index, which is what lands in the script.
  2. Data.write() calls `write_table()` to lay the collected ids into
     the claim as plaintext.
  3. the end-of-write masking pass (obfuscation/mask.py) XORs the table
     with its pad like every other relocated table.
"""

TABLE = "item_rewards"

_items = []


def reset():
    """Start a fresh build's collection (safe to call between in-process
    builds; a normal wc.py run is one process and starts empty)."""
    global _items
    _items = []


def register(item_id):
    """Record one granted item id, returning its table index."""
    _items.append(item_id & 0xff)
    return len(_items) - 1


def count():
    return len(_items)


def write_table(rom, args):
    """Lay the collected ids into the claim as plaintext (masked later)."""
    from obfuscation import claim
    layout = claim.layout(args)
    size = claim.TABLE_SIZES[TABLE]
    # the opcode operand is one byte, so the index range (256) is the hard
    # cap regardless of table size; assert against it, not just the bytes
    assert len(_items) <= min(size, 256), (
        f"race: {len(_items)} item-reward checks exceed the 256 the "
        f"one-byte AddCheckItem index can address; widen the index/operand")
    # unused slots are 0xff (an invalid item id) so a stray decode is
    # visibly wrong rather than a plausible fake
    padded = _items + [0xff] * (size - len(_items))
    rom.set_bytes(layout[TABLE], padded)
