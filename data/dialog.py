# Central registry of dialog (message) IDs that WC references from more than one
# place, so the numeric ID lives in exactly one location instead of being
# duplicated as a magic number.  Use it the same way as data/event_bit.py:
#
#     import data.dialog as dialog
#     ...
#     field.Dialog(dialog.NOT_ENOUGH_GP)
#     self.dialogs.set_text(dialog.CID_FEEDING, "...")
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
# Figaro Castle rest uses 0x5B5 rather than the original 0xB80 because 0xB80 is
# also used by a Doma Castle event.
FIGARO_CASTLE_REST = 1461       # 0x5B5  "<price> GP per night! Need a rest?"
# "Take a nap?" prompt shared by the vanilla free bed heals (Gau's Father's
# House, Sabin's House, ...) that -nfh reworks into a state-dependent heal.
FREE_BED = 443                  # 0x1BB


# =============================================================================
# -nfh Vector inn rework (event/free_heals.py)
# =============================================================================
# 0x559/0x55A are vanilla Maduin/Madonna esper-world slots repurposed for the
# reworked inn's stay prompt and full-theft message.
VECTOR_INN_STAY = 1369          # 0x559  vanilla "Have a snooze?" prompt
VECTOR_INN_STOLEN_FULL = 1370   # 0x55A  repurposed for "<N> GP stolen!"
# Free slots in the same esper-world block (that conversation never plays in
# WC).  1474-1479 (0x5C2-0x5C7) is the reserved free band; three are used:
VECTOR_INN_FREE_BAND = range(1474, 1480)  # 0x5C2 - 0x5C7 reserved
VECTOR_INN_NO_ROOM = 1474        # 0x5C2  "No room for yeh!"
VECTOR_INN_STOLEN_HALF = 1475    # 0x5C3  "<N/2> GP stolen!"
VECTOR_INN_STOLEN_QUARTER = 1476 # 0x5C4  "<N/4> GP stolen!"


# =============================================================================
# Ruination recovery springs (event/free_heals.py)
# =============================================================================
# Spring "drink?" prompt + per-area result messages are laid out sequentially
# from this base.  1480-1495 (0x5C8-0x5D7) is reserved; it sits in the vanilla
# Maduin/Madonna esper-world conversation block that never plays in WC.
SPRING_MESSAGE_BASE = 1480       # 0x5C8
SPRING_MESSAGE_RANGE = range(1480, 1496)  # 0x5C8 - 0x5D7 reserved


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
