"""Narshe School party reform: drive the ghost-NPC interaction that splits the
ruination hub party into 1/2/3 field parties, so tests can field a *second*
party (e.g. the Phoenix Cave two-party collision).

Three interactive UIs stand between "talking to the ghost" and "two parties on
the map", each reverse-engineered against live WRAM:

1. **Dialog choice boxes** (``reform_parties`` -> ``how many parties?``).
   The live choice cursor is a single byte at ``0x056E`` (documented as
   "last selected choice", but it tracks the *highlighted* choice as you move,
   not just the committed one). ``choose`` navigates it to a target index by
   feedback, trying both axes so it works for vertical *and* 2x2-grid layouts.

2. **The SelectParties "form groups" menu** (FF6 opcode 0x99). The cursor is
   located unambiguously by pixel coords: ``0x55`` = pixel-X (column),
   ``0x57`` = pixel-Y (row: roster=100, group-box top=164, bottom=192).
   Character->party assignment is one byte per character id at ``0x1850+``:
   bit6 (0x40)=available, bits0-2=party (1/2/3), bits3-4=slot, bit7=party
   leader. The group boxes live at FIXED pixel coords regardless of occupancy,
   so ``place`` navigates the held cursor straight to the next empty slot --
   filling each party's slots *contiguously* (0x41,0x49,... for P1), which the
   menu requires or it will not accept the formation.

3. **Finalizing.** The form-groups menu does NOT auto-close and A opens a
   character's status; the confirm is **B pressed repeatedly**. ``finalize``
   taps B until ENABLE_Y_PARTY_SWITCHING flips, which is the reform event
   resuming and positioning the parties.

Validated on a ``-ruin -s 1002`` seed: a [1,1,2] plan yields party 1 =
{Terra, Locke}, party 2 = {Cyan}, both placed in the school, Y-switch working.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.playtest import navigate, route
import data.event_bit as event_bit

# --- RAM ------------------------------------------------------------------
CHOICE_CURSOR = 0x056e        # live highlighted choice in a multi-choice dialog
CURSOR_PX = 0x55              # form-groups cursor pixel X (column)
CURSOR_PY = 0x57              # form-groups cursor pixel Y (row)
PARTY_ASSIGN = 0x1850         # per-character party byte (0x1850 + char id)

# form-groups cursor rows / cells (pixel coords, fixed regardless of occupancy)
ROSTER_PY = 100
def _roster_px(col):
    return 8 + 28 * col
_P1_SLOTS = [(8, 164), (8, 192), (40, 164), (40, 192)]
_P2_SLOTS = [(88, 164), (88, 192), (120, 164), (120, 192)]
_GROUP_SLOTS = {1: _P1_SLOTS, 2: _P2_SLOTS}

# Ghost NPC talk spot in the Narshe School (ghost at 110,49 facing left).
GHOST_TALK_XY = (109, 49)
SCHOOL_MAP = route.SCHOOL_MAP  # 104


def _tap(h, button):
    h.hold(button, frames=2)
    h.run(9)


def choose(h, target, budget=10):
    """Move the dialog choice cursor (0x056E) to `target` and press A.

    Works for vertical and 2x2-grid choice boxes: to step toward the target it
    tries the horizontal axis first, then the vertical, whichever actually
    moves the live cursor.
    """
    W = h.core.wram
    for _ in range(budget):
        cur = W[CHOICE_CURSOR]
        if cur == target:
            break
        if cur < target:
            before = cur
            _tap(h, 'RIGHT')
            if W[CHOICE_CURSOR] == before:
                _tap(h, 'DOWN')
        else:
            before = cur
            _tap(h, 'LEFT')
            if W[CHOICE_CURSOR] == before:
                _tap(h, 'UP')
    h.press('A', hold=6, wait=30)


def available_characters(h):
    """Character ids currently available in the reform roster (bit6 set)."""
    W = h.core.wram
    return [c for c in range(14) if W[PARTY_ASSIGN + c] & 0x40]


def _nav_cursor(h, tx, ty, budget=25):
    """Feedback-navigate the form-groups cursor to pixel (tx, ty)."""
    W = h.core.wram
    for _ in range(budget):
        cx, cy = W[CURSOR_PX], W[CURSOR_PY]
        if (cx, cy) == (tx, ty):
            return True
        if cy < ty:
            _tap(h, 'DOWN')
        elif cy > ty:
            _tap(h, 'UP')
        elif cx < tx:
            _tap(h, 'RIGHT')
        else:
            _tap(h, 'LEFT')
    return (W[CURSOR_PX], W[CURSOR_PY]) == (tx, ty)


def place(h, roster_col, group, slot):
    """Grab the roster character at `roster_col` and drop it into `group`
    (1 or 2) at `slot` (0-based). Roster characters keep their original column
    even as others are placed (gaps are preserved), so `roster_col` is the
    character's index in `available_characters`.
    """
    assert _nav_cursor(h, _roster_px(roster_col), ROSTER_PY), "roster nav failed"
    _tap(h, 'A')                                   # grab
    assert _nav_cursor(h, *_GROUP_SLOTS[group][slot]), "group-slot nav failed"
    _tap(h, 'A')                                   # drop


def finalize(h, budget=10):
    """Confirm the formation: tap B until the reform event resumes (sets
    ENABLE_Y_PARTY_SWITCHING). Returns True on success."""
    for _ in range(budget):
        if h.event_bit(event_bit.ENABLE_Y_PARTY_SWITCHING):
            return True
        h.press('B', hold=4, wait=18)
    h.run(60)
    return h.event_bit(event_bit.ENABLE_Y_PARTY_SWITCHING)


def reform_two_parties(h, plan=(1, 1, 2)):
    """Full macro: from field control in the Narshe School, talk to the ghost,
    choose "reform / 2 parties", assign the roster per `plan`, and finalize.

    `plan[k]` is the party (1 or 2) for available character k. Slots fill
    contiguously per party. Defaults to {c0,c1}->P1, {c2}->P2.

    Assumes the current map is the school and the party is at field control.
    Leaves two parties placed in the school with Y-switching enabled.
    """
    assert h.map_id == SCHOOL_MAP, f"expected school map {SCHOOL_MAP}, got {h.map_id:#x}"

    # Talk to the ghost.
    h.set_party_xy(*GHOST_TALK_XY)
    h.run(6)
    h.hold('RIGHT', frames=2)            # face the ghost (to the right)
    h.press('A', hold=6, wait=90)        # open the reform choice box; let it print

    choose(h, 0)                         # "Reform parties." (choice 0)
    h.run(40)
    choose(h, 1)                         # "How many parties?" -> "2" (choice 1)
    h.run(40)

    # Assign the roster. slot counters per party.
    slots = {1: 0, 2: 0}
    for col, group in enumerate(plan):
        place(h, col, group, slots[group])
        slots[group] += 1

    ok = finalize(h)
    h.run(90)
    assert ok, "reform did not finalize (Y-party-switching never enabled)"
    return ok
