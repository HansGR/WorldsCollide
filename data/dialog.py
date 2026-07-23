# Central registry of dialog (message) IDs that WC references from more than one
# place, so the numeric ID lives in exactly one location instead of being
# duplicated as a magic number.  Use it the same way as data/event_bit.py:
#
#     import data.dialog as dialog
#     ...
#     field.Dialog(dialog.NOT_ENOUGH_GP)
#     self.dialogs.set_text(dialog.CID_FEEDING, "...")
#
# For brand-new scratch dialogs that just need some unused slot (rather than a
# specific, meaningful ID), don't hardcode one here -- claim it from the free
# pool at the bottom of this file via Dialogs.allocate_dialog(text).
#
# IDs are the dialog indices used by data/dialogs/dialogs.py (Dialogs.set_text /
# field.Dialog / field.DialogBranch).  Values are given in decimal with the hex
# form in a comment, since the codebase refers to them both ways.
#
# Scope: an ID belongs here when it is written/referenced in more than one place
# in WC's logic (either reused across modules, or the same slot repurposed by a
# feature in several statements).  The bulk vanilla-text replacement done by
# Dialogs.mod() under -ndt (npc_dialog_tips) is intentionally NOT catalogued
# here -- it rewrites hundreds of vanilla slots as gameplay tips and is a content
# module rather than a set of shared logic constants.


# =============================================================================
# Shared across the -nfh (no free heals) paid-heal conversions
# =============================================================================
# Vanilla "You don't have enough money." message.  Already contains the right
# text in the base ROM, so the paid heals only need to display it -- no set_text.
# Reused by the converted Returners Hideout / Figaro Castle inns (free_heals.py),
# the WoB airship heal (airship.py) and the Phantom Train restaurant
# (phantom_train.py).
NOT_ENOUGH_GP = 2748            # 0xABC


# =============================================================================
# -nfh converted free inns / rest points (event/free_heals.py)
# =============================================================================
RETURNERS_HIDEOUT_INN = 273     # 0x111  "<price> GP per night! Take a nap?"
# "Take a nap?" prompt shared by the vanilla free bed heals (Gau's Father's
# House, Sabin's House, ...) that -nfh reworks into a state-dependent heal.
FREE_BED = 443                  # 0x1BB


# =============================================================================
# -nfh Vector inn rework (event/free_heals.py)
# =============================================================================
# The Vector inn's own dialogs, rewritten in place by -nfh.  (The reworked inn's
# extra messages -- "no room", half/quarter thefts -- are scratch dialogs pulled
# from the free pool below via Dialogs.allocate_dialog.)
VECTOR_INN_STAY = 1369          # 0x559  "Have a snooze?" prompt
VECTOR_INN_STOLEN_FULL = 1370   # 0x55A  "<N> GP stolen!"


# =============================================================================
# Vanilla dialog slots each repurposed by a single event feature, referenced
# from more than one statement (set the text in one place, display it in
# another).  Named here so the slot number is written only once.
# =============================================================================
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
# are free real estate for brand-new custom dialogs.
#
# Rather than hand out fixed IDs from this band (and risk two features claiming
# the same one), request slots at build time, first-come first-served, via
#
#     new_id = dialogs.allocate_dialog("...text...<end>")
#
# which sets the text and returns the claimed ID.  It raises DialogSpaceError
# once the pool is exhausted.  Existing users: the -nfh Vector inn extra
# messages and recovery-spring messages (event/free_heals.py) and the school
# limited-heals bucket prompts (event/narshe_wob.py).
FREE_RANGE = range(1423, 1498)  # 0x58F - 0x5D9 inclusive


class DialogSpaceError(Exception):
    """Raised when Dialogs.allocate_dialog() exhausts the free dialog pool
    (dialog.FREE_RANGE). Free up slots or widen the range."""
