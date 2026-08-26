"""L3 - check-reward indirection (race builds).

A check that grants an item, an esper or a character does it with an
event command whose operand names the reward in plaintext, sitting in
the event script - the single most valuable thing for a cheater to
grep, at every check.

Race builds put every reward in one masked table and refer to it only by
an opaque *slot*.  One table for all kinds matters: with separate item
and esper tables (or separate grant opcodes, or separate receive
dialogs) an attacker could still tell which checks hold espers without
knowing which esper, and that alone is most of the routing value.  So a
single `AddCheckReward` command grants any kind, and a single
`<reward>` control code renders any name, both dispatching on the
kind byte they read out of the masked table at runtime.  Character
rewards additionally need their scene machinery - showing the joining
character's sprite, naming them, playing their theme - driven off the
same slot; that is the RewardEntity command family in
instruction/field/custom.py.

Slots are handed out in registration order and carry no meaning.  Where
one dialog names two rewards (the Narshe WOR choice), the pair is
registered consecutively and the second is rendered by `<reward2>`,
which simply reads the slot after the one it is given - so no second ram
byte is needed.

Flow across a build:
  1. event generation registers rewards and gets slots, which are what
     land in the script.
  2. Data.write() calls `write_tables()` to lay the tables into the claim.
  3. the end-of-write masking pass XORs them like every other table.
"""

TABLE = "rewards"
SLOT_SIZE = 2                   # (kind, id)

DIALOG_TABLE = "reward_dialogs"
DIALOG_SLOT_SIZE = 6            # (reward slot, item dialog, esper dialog)

KIND_ITEM, KIND_ESPER, KIND_CHARACTER = 0x00, 0x01, 0x02
KINDS = {"item": KIND_ITEM, "esper": KIND_ESPER, "character": KIND_CHARACTER}

_rewards = []
_dialogs = []

# the two shared receive-dialog wordings ("Received X!" and the magicite
# one).  Both kinds' receive dialogs carry both ids so the command that
# shows them is identical either way; the handler picks at runtime.
_wordings = {"item": None, "esper": None}


def set_wording(kind, dialog_id):
    _wordings[kind] = dialog_id


def wordings():
    """(item wording, esper wording); either may be unset in odd flag
    combinations, in which case the other stands in."""
    item, esper = _wordings["item"], _wordings["esper"]
    return (item if item is not None else esper,
            esper if esper is not None else item)


def reset():
    """Start a fresh build's collection (safe to call between in-process
    builds; a normal wc.py run is one process and starts empty)."""
    global _rewards, _dialogs, _wordings
    _rewards = []
    _dialogs = []
    _wordings = {"item": None, "esper": None}


def register(kind, value):
    """Record one reward, returning its opaque slot."""
    _rewards.append((KINDS[kind], value & 0xff))
    return len(_rewards) - 1


def register_check(reward):
    """Record an event check's reward (an EventReward with .type and
    .id), returning its opaque slot - the one number a converted event
    script carries for its grant, dialogs and scene commands alike."""
    from event.event_reward import RewardType
    names = {RewardType.CHARACTER: "character",
             RewardType.ESPER: "esper",
             RewardType.ITEM: "item"}
    return register(names[reward.type], reward.id)


def register_pair(kind, value, second_item):
    """Record a reward plus a second (item) reward named by the same
    dialog.  They are adjacent so <reward2> can find the second one by
    reading the slot after the first."""
    slot = register(kind, value)
    register("item", second_item)
    return slot


def register_dialog(slot, item_dialog, esper_dialog):
    """Record a dialog that names the reward in `slot`, returning the
    dialog's own slot.

    Two dialog ids are stored: the handler shows whichever matches the
    reward's kind, so that a receive dialog can keep vanilla's separate
    item and magicite wordings without the script revealing which kind it
    is.  Bespoke dialogs pass the same id for both.
    """
    _dialogs.append((slot,
                     item_dialog & 0xff, (item_dialog >> 8) & 0xff,
                     esper_dialog & 0xff, (esper_dialog >> 8) & 0xff,
                     0x00))
    return len(_dialogs) - 1


def count():
    return len(_rewards)


def write_tables(rom, args):
    """Lay the reward and dialog tables into the claim as plaintext
    (masked later by obfuscation.mask.apply_all)."""
    from obfuscation import claim
    layout = claim.layout(args)

    size = claim.TABLE_SIZES[TABLE]
    # slots are addressed by a one-byte operand, so 256 is the hard cap
    # whatever the table size
    assert len(_rewards) <= min(size // SLOT_SIZE, 256), (
        f"race: {len(_rewards)} rewards exceed the {min(size // SLOT_SIZE, 256)} "
        f"a one-byte slot can address")
    entries = [b for reward in _rewards for b in reward]
    # unused slots decode to an invalid id so a stray decode is visibly
    # wrong rather than a plausible fake
    rom.set_bytes(layout[TABLE], entries + [0xff] * (size - len(entries)))

    size = claim.TABLE_SIZES[DIALOG_TABLE]
    slots = [b for slot in _dialogs for b in slot]
    assert len(slots) <= size, (
        f"race: {len(_dialogs)} reward dialogs exceed the "
        f"{size // DIALOG_SLOT_SIZE}-slot table; grow "
        f"claim.TABLE_SIZES['{DIALOG_TABLE}']")
    rom.set_bytes(layout[DIALOG_TABLE], slots + [0xff] * (size - len(slots)))
