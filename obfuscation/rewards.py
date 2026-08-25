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

# side table for RewardDialog: one slot per bespoke dialog that names a
# reward - (reward index, kind, dialog id low, dialog id high, second
# item index, second-slot flag).  The second entry serves the one dialog
# that names two rewards at once (the Narshe WOR choice); it is always an
# item and renders through <item2>.
DIALOG_TABLE = "reward_dialogs"
DIALOG_SLOT_SIZE = 6
KINDS = {"item": 0x00, "esper": 0x01}

_collected = {kind: [] for kind in TABLES}
_dialogs = []


def reset():
    """Start a fresh build's collection (safe to call between in-process
    builds; a normal wc.py run is one process and starts empty)."""
    global _collected, _dialogs
    _collected = {kind: [] for kind in TABLES}
    _dialogs = []


def register_dialog(kind, value, dialog_id, second_item=None):
    """Record a dialog that names a reward, returning its slot.

    The slot is what the RewardDialog command carries; the handler reads
    this table to find which reward to decode and which dialog to show.
    `second_item` adds a second name, rendered by <item2>.
    """
    index = register(kind, value)
    if second_item is None:
        second, has_second = 0xff, 0x00
    else:
        second, has_second = register("item", second_item), 0x01
    _dialogs.append((index, KINDS[kind], dialog_id & 0xff, (dialog_id >> 8) & 0xff,
                     second, has_second))
    return len(_dialogs) - 1


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

    # the RewardDialog side table.  it is not masked: it holds only the
    # opaque reward index plus the dialog id being shown, so it reveals
    # which dialogs name a reward but never which reward
    size = claim.TABLE_SIZES[DIALOG_TABLE]
    slots = [b for slot in _dialogs for b in slot]
    assert len(slots) <= size, (
        f"race: {len(_dialogs)} reward dialogs exceed the "
        f"{size // DIALOG_SLOT_SIZE}-slot table; grow "
        f"claim.TABLE_SIZES['{DIALOG_TABLE}']")
    rom.set_bytes(layout[DIALOG_TABLE], slots + [0xff] * (size - len(slots)))
