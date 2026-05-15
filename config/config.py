"""Apply default-config overrides to an already-patched FF6WC ROM.

The FF6 SNES config menu is backed by three packed bytes plus per-window
palette tables.  Their layout in ROM:

* Config1 at $03/70B9 -- byte loaded into $1D4D: cmmm wbbb
    c   = command set      (window=0, short=1)
    mmm = message speed    (0..5, displayed as 1..6)
    w   = battle mode      (active=0, wait=1)
    bbb = battle speed     (0..5, displayed as 1..6)
* Config2 -- byte loaded into $1D54: mbcc csss
* Config3 -- byte loaded into $1D4E: gcsr wwww

Config1 lives at a fixed address.  Config2/Config3 default writes are done
by a pair of small subroutines whose addresses are stored as JSR operands
at $03/70C3 and $03/70C6 -- we read those, then add 1 to skip past the
"LDA #$NN" opcode and land on the immediate byte that we want to patch.

Window palettes live at $2D/1C02 etc., 14 bytes (7 BGR15 colors) each.
"""

from dataclasses import dataclass


# ---- ROM addresses ---------------------------------------------------

CONFIG1_ADDR = 0x0370B9

# JSR opcode at $03/70C2 is followed by a 2-byte little-endian target.
# Same for $03/70C5.  Reading at +1 / +4 skips the opcode byte.
CONFIG2_JSR_OPERAND = 0x0370C3
CONFIG3_JSR_OPERAND = 0x0370C6

FONT_PALETTE_ADDRS = (
    0x18E806,  # actual font color (2 bytes)
    0x03709F,  # font color "controls" (2 bytes)
)

WINDOW_PALETTE_BASE = {
    f"Window{i}": 0x2D1C02 + 0x20 * (i - 1)
    for i in range(1, 9)
}


# ---- Declarative bit-packing spec ------------------------------------

@dataclass(frozen=True)
class Field:
    """One slice of a packed config byte, listed MSB-first.

    The value written is ``int(values[name]) - offset`` truncated to
    ``bits`` bits.  ``offset`` lets us store a user-facing 1..N value as a
    0..N-1 bit field.
    """
    name: str
    bits: int
    default: object  # bool or int
    offset: int = 0


CONFIG_BYTES = {
    "Config1": [   # cmmmwbbb
        Field("Command",  bits=1, default=False),
        Field("MsgSpeed", bits=3, default=3, offset=1),
        Field("BatMode",  bits=1, default=True),
        Field("BatSpeed", bits=3, default=3, offset=1),
    ],
    "Config2": [   # mbcccsss
        Field("Controller2",             bits=1, default=False),
        Field("CustomButtons",           bits=1, default=False),
        Field("FontWindowPaletteSelect", bits=3, default=1, offset=1),
        Field("SpellOrder",              bits=3, default=1, offset=1),
    ],
    "Config3": [   # gcsrwwww
        Field("Gauge",     bits=1, default=False),
        Field("Cursor",    bits=1, default=False),
        Field("Sound",     bits=1, default=False),
        Field("Reequip",   bits=1, default=False),
        Field("Wallpaper", bits=4, default=1, offset=1),
    ],
}


WINDOW_DEFAULTS = {
    "Window1": [[25, 28, 28], [20, 22, 22], [16, 16, 16], [10, 10, 10], [5, 6, 6],    [6, 6, 17],  [5, 5, 16]],
    "Window2": [[14, 15, 15], [8, 9, 9],    [7, 8, 8],    [6, 7, 7],    [5, 6, 6],    [4, 5, 5],   [1, 2, 2]],
    "Window3": [[7, 13, 16],  [6, 10, 13],  [4, 7, 10],   [3, 6, 7],    [2, 4, 5],    [2, 3, 4],   [10, 15, 19]],
    "Window4": [[17, 12, 4],  [15, 11, 4],  [14, 9, 3],   [12, 8, 2],   [19, 21, 20], [7, 9, 8],   [4, 6, 5]],
    "Window5": [[13, 11, 8],  [12, 11, 8],  [12, 10, 7],  [11, 9, 6],   [10, 8, 4],   [7, 7, 4],   [2, 2, 2]],
    "Window6": [[19, 19, 19], [13, 15, 15], [10, 12, 11], [8, 10, 9],   [6, 8, 7],    [4, 6, 5],   [1, 3, 2]],
    "Window7": [[15, 21, 14], [12, 17, 11], [9, 15, 8],   [7, 13, 6],   [5, 10, 4],   [4, 7, 4],   [2, 5, 3]],
    "Window8": [[20, 12, 13], [25, 24, 22], [20, 19, 16], [26, 17, 0],  [25, 13, 0],  [20, 11, 0], [4, 4, 4]],
}


# ---- Bit / byte helpers ----------------------------------------------

def rgb2bytes(rgb):
    """Pack (R, G, B) (each 0..31) into 2 little-endian BGR15 bytes."""
    r, g, b = rgb
    v = (b << 10) | (g << 5) | r
    return [v & 0xFF, (v >> 8) & 0xFF]


def bytes2rgb(byts):
    """Unpack 2 little-endian BGR15 bytes into [R, G, B]."""
    v = byts[0] | (byts[1] << 8)
    return [v & 0x1F, (v >> 5) & 0x1F, (v >> 10) & 0x1F]


def pack_config_byte(fields, values):
    """Pack a list of Fields into a single byte using ``values`` (with defaults)."""
    byte = 0
    for f in fields:
        raw = int(values.get(f.name, f.default)) - f.offset
        mask = (1 << f.bits) - 1
        byte = (byte << f.bits) | (raw & mask)
    return byte


def _read_default_config_addr(rom, jsr_operand_addr):
    """Read the LDA-immediate address pointed to by a JSR operand."""
    lo, hi = rom.get_bytes(jsr_operand_addr, 2)
    # +1 skips the "LDA #" opcode and lands on the immediate byte.
    return ((0x03 << 16) | (hi << 8) | lo) + 1


# ---- Public API ------------------------------------------------------

def set_config(rom, config_set):
    """Write user overrides in ``config_set`` to ``rom``.

    Keys are field names (e.g. ``"BatSpeed"``, ``"Window3"``, ``"Font"``).
    Unset keys keep their ROM default.  ``Font`` is an ``[R, G, B]`` triple;
    ``Window*`` is a dict mapping 1-based palette slot (1..7) to an
    ``[R, G, B]`` triple.
    """
    addresses = {
        "Config1": CONFIG1_ADDR,
        "Config2": _read_default_config_addr(rom, CONFIG2_JSR_OPERAND),
        "Config3": _read_default_config_addr(rom, CONFIG3_JSR_OPERAND),
    }
    for name, fields in CONFIG_BYTES.items():
        rom.set_bytes(addresses[name], [pack_config_byte(fields, config_set)])

    for i in range(1, 9):
        key = f"Window{i}"
        if key in config_set:
            set_window_palette(rom, key, config_set[key])

    if "Font" in config_set:
        font_bytes = rgb2bytes(config_set["Font"])
        for addr in FONT_PALETTE_ADDRS:
            rom.set_bytes(addr, font_bytes)


def set_window_palette(rom, window_name, slot_overrides):
    """Write palette overrides for one window.

    ``slot_overrides`` is a dict mapping 1-based slot index (1..7) to an
    ``[R, G, B]`` triple.  Slots not in the dict are left untouched.
    """
    base = WINDOW_PALETTE_BASE[window_name]
    for slot, rgb in slot_overrides.items():
        rom.set_bytes(base + 2 * (slot - 1), rgb2bytes(rgb))
