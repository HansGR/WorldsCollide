"""Phase 1 harness API: a game-aware wrapper over the raw Core.

Bridges the randomizer's own data modules (data.event_bit, data.event_word)
into named RAM accessors, and provides the boot-to-game-start macro plus
input helpers, so tests read like game actions rather than frame counts.

WRAM addresses (SNES $7E0000 = WRAM offset 0), cross-checked against
instruction/field/custom.py and claude_reference/ff3infov2.txt, and the
empirically-measured layout confirmed with the live core:

  Character records  0x1600 + 0x25*slot   (37-byte stride, measured)
    name   +0x02 (6)   cur HP +0x09 (u16)   max HP +0x0b (u16 & 0x3fff)
    cur MP +0x0d       max MP +0x0f         status +0x14/+0x15
  Event bits          0x1e80 + bit//8, mask 1<<(bit%8)   (via data.event_bit)
  Event words         address via data.event_word
  Current GP          0x1860 (u24)
  Active party        0x1a6d
  Current map         0x1f64 (u16)
  Screen scroll hold  0x0559 (0 = camera scrolls, 1 = held)   [$00/0559]
  Party leader entity 0x0867 + u16@0x0803;  tile X +0x13, tile Y +0x14
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.playtest.core import Core
import data.event_bit as event_bit

# data.event_word runs ROM allocation at import time, which needs an
# initialized Memory; the harness stays ROM-free, so inline its trivial
# address formula (event words are a contiguous u16 array at $1FC2).
EVENT_WORD_BASE = 0x1fc2


def _event_word_address(word_id):
    return EVENT_WORD_BASE + word_id * 2

# --- RAM layout constants -------------------------------------------------

CHAR_BASE = 0x1600
CHAR_STRIDE = 0x25
CHAR_CUR_HP = 0x09
CHAR_MAX_HP = 0x0b
CHAR_CUR_MP = 0x0d
CHAR_MAX_MP = 0x0f
CHAR_STATUS1 = 0x14
CHAR_STATUS2 = 0x15
MAX_HP_MASK = 0x3fff

GP_ADDR = 0x1860
ACTIVE_PARTY = 0x1a6d
CURRENT_MAP = 0x1f64
SCREEN_HOLD = 0x0559          # 0 = scroll (camera tracks party), 1 = held
LEADER_PTR = 0x0803           # u16 offset into object data
OBJECT_BASE = 0x0867
ENTITY_X = 0x13               # tile X within object block
ENTITY_Y = 0x14               # tile Y within object block


class Harness:
    """Game-aware driver: a Core plus named FF6 state accessors."""

    def __init__(self, rom_path, core=None):
        self.core = core or Core(rom_path=rom_path)
        self.rom_path = rom_path

    # --- passthroughs -----------------------------------------------------

    def run(self, frames=1):
        self.core.run(frames)

    def run_until(self, predicate, timeout=3600, step=1):
        return self.core.run_until(lambda c: predicate(self), timeout, step)

    def screenshot(self, path):
        return self.core.screenshot(path)

    def save_state(self):
        return self.core.save_state()

    def load_state(self, state):
        self.core.load_state(state)

    # --- input ------------------------------------------------------------

    def press(self, *buttons, hold=6, wait=8):
        """Tap one or more buttons for `hold` frames, then idle `wait`."""
        self.core.buttons = set(buttons)
        self.core.run(hold)
        self.core.buttons = set()
        if wait:
            self.core.run(wait)

    def hold(self, *buttons, frames=1):
        """Hold buttons for `frames` frames (movement), then release."""
        self.core.buttons = set(buttons)
        self.core.run(frames)
        self.core.buttons = set()

    # --- event bits / words -----------------------------------------------

    def event_bit(self, bit_id):
        """Read an event bit by its data.event_bit id (e.g. 0xe9 or a
        named constant like event_bit.DEFEATED_NUMBER128)."""
        addr = event_bit.address(bit_id)
        return bool(self.core.wram[addr] & (1 << event_bit.bit(bit_id)))

    def set_event_bit(self, bit_id, value=True):
        addr = event_bit.address(bit_id)
        mask = 1 << event_bit.bit(bit_id)
        if value:
            self.core.wram[addr] |= mask
        else:
            self.core.wram[addr] &= ~mask & 0xff

    def event_word(self, word_id):
        return self.core.read_u16(_event_word_address(word_id))

    # --- character state --------------------------------------------------

    def _char(self, slot, offset):
        return CHAR_BASE + CHAR_STRIDE * slot + offset

    def max_hp(self, slot):
        return self.core.read_u16(self._char(slot, CHAR_MAX_HP)) & MAX_HP_MASK

    def cur_hp(self, slot):
        return self.core.read_u16(self._char(slot, CHAR_CUR_HP))

    def max_mp(self, slot):
        return self.core.read_u16(self._char(slot, CHAR_MAX_MP))

    def cur_mp(self, slot):
        return self.core.read_u16(self._char(slot, CHAR_CUR_MP))

    def status(self, slot):
        """Return the 16-bit (status2<<8 | status1) affliction flags."""
        return (self.core.read_u8(self._char(slot, CHAR_STATUS2)) << 8) \
            | self.core.read_u8(self._char(slot, CHAR_STATUS1))

    # --- field state ------------------------------------------------------

    @property
    def gp(self):
        return (self.core.wram[GP_ADDR]
                | (self.core.wram[GP_ADDR + 1] << 8)
                | (self.core.wram[GP_ADDR + 2] << 16))

    @property
    def map_id(self):
        return self.core.read_u16(CURRENT_MAP)

    @property
    def screen_held(self):
        """True when the camera is frozen (scroll-hold flag set)."""
        return self.core.wram[SCREEN_HOLD] != 0

    @property
    def _leader_block(self):
        return OBJECT_BASE + self.core.read_u16(LEADER_PTR)

    @property
    def party_xy(self):
        """(tile_x, tile_y) of the party leader object."""
        blk = self._leader_block
        return (self.core.wram[blk + ENTITY_X], self.core.wram[blk + ENTITY_Y])

    def set_party_xy(self, x, y):
        """Poke the party leader tile position (for door-step teleport)."""
        blk = self._leader_block
        self.core.wram[blk + ENTITY_X] = x & 0xff
        self.core.wram[blk + ENTITY_Y] = y & 0xff

    # --- boot macro -------------------------------------------------------

    def boot_to_game_start(self, mode="ruination", timeout=40000):
        """Drive title -> file select -> new game up to the point where the
        game hands control to the start script (event bits go live).

        Returns frames consumed. Uses state predicates, not frame counts,
        so it is robust to intro timing.
        """
        # 1) Advance to the title screen: the WC title is up once rendering
        #    has settled; press START to reach file select.
        self.core.run(3000)
        self.press('START', wait=180)

        # 2) File select -> confirm new game.  Two A presses clear the
        #    file-select menu and the new-game confirmation.
        self.press('A', wait=150)
        self.press('A', wait=150)

        # 3) The start script runs on the first game map: event bits leave
        #    their all-zero pre-game state once it begins.
        def bits_live(core):
            return any(core.wram[a] for a in range(0x1e80, 0x1e90))

        elapsed = 3000 + self.core.run_until(bits_live, timeout=timeout, step=10)
        return elapsed
