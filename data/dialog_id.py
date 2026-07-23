# Central registry of dialog IDs that WC references from more than one
# place, so the numeric ID lives in exactly one location instead of being
# duplicated.  Use it the same way as data/event_bit.py.
#
# For brand-new scratch dialogs that just need some unused slot (rather than a
# specific, meaningful ID), claim it from the free pool at the bottom of this
# file via Dialogs.allocate_dialog(text).
#
NOT_ENOUGH_GP = 2748            # 0xABC:  Vanilla "You don't have enough money." message.

RETURNERS_HIDEOUT_INN = 273     # 0x111  "<price> GP per night! Take a nap?"
FREE_BED = 443                  # 0x1BB  # "Take a nap?" prompt shared by the vanilla free bed heals
                                         # (Gau's Father's House, Sabin's House, ...)
VECTOR_INN_STAY = 1369          # 0x559  "Have a snooze?" prompt
VECTOR_INN_STOLEN_FULL = 1370   # 0x55A  "<N> GP stolen!"

ZOZO_CLOCK_CLUE = 1059           # 0x423  event/zozo.py  clock-puzzle divisor clue
UMARO_CAVE_CARVING = 1525        # 0x5F5  event/umaro_cave.py  "touch the eye of the carving?"
LONE_WOLF_GOT_ITEM = 1742        # 0x6CE  event/lone_wolf.py  "Got <item>!"
THAMASA_STRANGERS_INN = 1936     # 0x790  event/burning_house.py  Thamasa "strangers" inn
CID_FEEDING = 2175               # 0x87F  event/cid_island.py  Cid feeding intro line
MOBLIZ_CHILD_TAKE_AWAY = 2264    # 0x8D8  event/mobliz_wor.py  "You're not gonna take <x> away?"
MOBLIZ_CHILD_CRY = 2265          # 0x8D9  event/mobliz_wor.py  "I'm not gonna cry..."
FIGARO_CAVE_SIEGFRIED = 2379     # 0x94B  event/figaro_castle_wor.py  Siegfried gate line


# =============================================================================
# Free dialog slot pool
# =============================================================================
# The vanilla Maduin/Madonna esper-world conversation occupies dialog IDs
# 1423-1497 (0x58F-0x5D9).  That conversation never plays in WC, so these slots
# are available for custom dialogs.
#
# Rather than hand out fixed IDs from this band (and risk two features claiming
# the same one), request slots at build time, first-come first-served, via
#
#     new_id = dialogs.allocate_dialog("...text...<end>")
#
# which sets the text and returns the claimed ID.  It raises DialogSpaceError
# once the pool is exhausted.
FREE_RANGE = range(1423, 1498)  # 0x58F - 0x5D9 inclusive

class DialogSpaceError(Exception):
    """Raised when Dialogs.allocate_dialog() exhausts the free dialog pool
    (dialog_id.FREE_RANGE). Free up slots or widen the range."""
