"""Encode / decode FF6 menu window source graphics.

Each of the eight window styles ships two ROM regions:

  * Graphics  -- 896 bytes at file offset 0x2D0000 + (N-1) * 0x380
                 (SNES $ED/0000 + (N-1) * 0x380).
                 28 tiles of standard SNES 4bpp, laid out 4 wide x 7 tall
                 => a 32x56 indexed image per window.
  * Palette   -- 32 bytes at file offset 0x2D1C00 + (N-1) * 0x20
                 (SNES $ED/1C00 + (N-1) * 0x20).
                 16 BGR15 colors; index 0 is transparent black, indices
                 1..7 are the user-editable slots shown in the config
                 menu, indices 8..15 are stock filler (0x3800).

See ARCHIVE.md for how the format was identified.

Coordinates throughout this module are (row, col) with row 0 at the
top.  Pixel values are palette indices 0..15.  ``config.config`` already
exposes a slot-only palette writer at $2D/1C02 (which skips color 0 to
match the menu's "7 editable slots" model); the helpers here read and
write the full 16-color table at $2D/1C00 so the graphics encoding
round-trips bit-for-bit.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple


# ---- ROM layout ------------------------------------------------------

WINDOW_GRAPHICS_BASE = 0x2D0000  # file offset of Window 1's tile sheet
WINDOW_GRAPHICS_STRIDE = 0x380   # 896 bytes
WINDOW_GRAPHICS_SIZE = 0x380     # bytes per window

WINDOW_PALETTE_FULL_BASE = 0x2D1C00
WINDOW_PALETTE_FULL_STRIDE = 0x20
WINDOW_PALETTE_FULL_SIZE = 0x20  # 16 colors * 2 bytes

# Sheet shape -- (tiles wide, tiles tall) and the resulting pixel size.
SHEET_TILES_W = 4
SHEET_TILES_H = 7
TILES_PER_SHEET = SHEET_TILES_W * SHEET_TILES_H   # 28
TILE_BYTES = 32                                   # 4bpp
SHEET_WIDTH = SHEET_TILES_W * 8                   # 32 px
SHEET_HEIGHT = SHEET_TILES_H * 8                  # 56 px

NUM_WINDOWS = 8


# ---- 4bpp tile codec -------------------------------------------------

def decode_tile_4bpp(data: Sequence[int]) -> List[List[int]]:
    """Decode 32 bytes of SNES 4bpp into an 8x8 grid of palette indices."""
    if len(data) != TILE_BYTES:
        raise ValueError(f"4bpp tile is {TILE_BYTES} bytes, got {len(data)}")
    rows: List[List[int]] = []
    for r in range(8):
        bp0 = data[2 * r]
        bp1 = data[2 * r + 1]
        bp2 = data[16 + 2 * r]
        bp3 = data[16 + 2 * r + 1]
        row: List[int] = []
        for x in range(8):
            bit = 7 - x
            px = ((bp0 >> bit) & 1) \
               | (((bp1 >> bit) & 1) << 1) \
               | (((bp2 >> bit) & 1) << 2) \
               | (((bp3 >> bit) & 1) << 3)
            row.append(px)
        rows.append(row)
    return rows


def encode_tile_4bpp(pixels: Sequence[Sequence[int]]) -> List[int]:
    """Encode an 8x8 grid of palette indices (0..15) into 32 4bpp bytes."""
    if len(pixels) != 8 or any(len(row) != 8 for row in pixels):
        raise ValueError("tile must be 8 rows of 8 pixels")
    low = [0] * 16   # bp0/bp1, alternating per row
    high = [0] * 16  # bp2/bp3, alternating per row
    for r in range(8):
        bp0 = bp1 = bp2 = bp3 = 0
        for x in range(8):
            v = pixels[r][x]
            if not 0 <= v <= 15:
                raise ValueError(f"pixel index {v} out of range 0..15 at ({r},{x})")
            bit = 7 - x
            bp0 |= ( v       & 1) << bit
            bp1 |= ((v >> 1) & 1) << bit
            bp2 |= ((v >> 2) & 1) << bit
            bp3 |= ((v >> 3) & 1) << bit
        low[2 * r] = bp0
        low[2 * r + 1] = bp1
        high[2 * r] = bp2
        high[2 * r + 1] = bp3
    return low + high


# ---- Whole-sheet codec ----------------------------------------------

def decode_window_sheet(data: Sequence[int]) -> List[List[int]]:
    """Decode a 896-byte window graphics blob into a 56x32 index grid."""
    if len(data) != WINDOW_GRAPHICS_SIZE:
        raise ValueError(
            f"window sheet is {WINDOW_GRAPHICS_SIZE} bytes, got {len(data)}")
    pixels = [[0] * SHEET_WIDTH for _ in range(SHEET_HEIGHT)]
    for ty in range(SHEET_TILES_H):
        for tx in range(SHEET_TILES_W):
            t = ty * SHEET_TILES_W + tx
            tile = decode_tile_4bpp(data[t * TILE_BYTES : (t + 1) * TILE_BYTES])
            for y in range(8):
                for x in range(8):
                    pixels[ty * 8 + y][tx * 8 + x] = tile[y][x]
    return pixels


def encode_window_sheet(pixels: Sequence[Sequence[int]]) -> List[int]:
    """Encode a 56x32 index grid into a 896-byte window graphics blob."""
    if len(pixels) != SHEET_HEIGHT or any(len(r) != SHEET_WIDTH for r in pixels):
        raise ValueError(
            f"sheet must be {SHEET_HEIGHT} rows of {SHEET_WIDTH} pixels")
    out: List[int] = []
    for ty in range(SHEET_TILES_H):
        for tx in range(SHEET_TILES_W):
            tile = [
                [pixels[ty * 8 + y][tx * 8 + x] for x in range(8)]
                for y in range(8)
            ]
            out.extend(encode_tile_4bpp(tile))
    return out


# ---- Palette codec ---------------------------------------------------

def decode_palette(data: Sequence[int]) -> List[Tuple[int, int, int]]:
    """Unpack a 32-byte BGR15 palette into 16 (R, G, B) triples (0..31 each)."""
    if len(data) != WINDOW_PALETTE_FULL_SIZE:
        raise ValueError(
            f"palette is {WINDOW_PALETTE_FULL_SIZE} bytes, got {len(data)}")
    colors: List[Tuple[int, int, int]] = []
    for i in range(16):
        v = data[2 * i] | (data[2 * i + 1] << 8)
        r = v & 0x1F
        g = (v >> 5) & 0x1F
        b = (v >> 10) & 0x1F
        colors.append((r, g, b))
    return colors


def encode_palette(colors: Sequence[Tuple[int, int, int]]) -> List[int]:
    """Pack 16 (R, G, B) triples (0..31 each) into 32 little-endian BGR15 bytes."""
    if len(colors) != 16:
        raise ValueError(f"palette must have 16 colors, got {len(colors)}")
    out: List[int] = []
    for r, g, b in colors:
        for c, name in ((r, "R"), (g, "G"), (b, "B")):
            if not 0 <= c <= 31:
                raise ValueError(f"{name} channel {c} out of range 0..31")
        v = (b << 10) | (g << 5) | r
        out.append(v & 0xFF)
        out.append((v >> 8) & 0xFF)
    return out


# ---- ROM IO ----------------------------------------------------------

def _check_window(n: int) -> None:
    if not 1 <= n <= NUM_WINDOWS:
        raise ValueError(f"window number must be 1..{NUM_WINDOWS}, got {n}")


def graphics_addr(window_num: int) -> int:
    """File offset of window N's 896-byte graphics blob."""
    _check_window(window_num)
    return WINDOW_GRAPHICS_BASE + (window_num - 1) * WINDOW_GRAPHICS_STRIDE


def palette_addr(window_num: int) -> int:
    """File offset of window N's 32-byte (16-color) palette."""
    _check_window(window_num)
    return WINDOW_PALETTE_FULL_BASE + (window_num - 1) * WINDOW_PALETTE_FULL_STRIDE


def get_window_graphics(rom, window_num: int) -> List[int]:
    """Read window N's raw 896-byte graphics blob from ``rom``."""
    return rom.get_bytes(graphics_addr(window_num), WINDOW_GRAPHICS_SIZE)


def set_window_graphics(rom, window_num: int, data: Sequence[int]) -> None:
    """Write a 896-byte graphics blob to window N."""
    if len(data) != WINDOW_GRAPHICS_SIZE:
        raise ValueError(
            f"graphics blob must be {WINDOW_GRAPHICS_SIZE} bytes, "
            f"got {len(data)}")
    rom.set_bytes(graphics_addr(window_num), list(data))


def get_window_palette_full(rom, window_num: int) -> List[Tuple[int, int, int]]:
    """Read window N's full 16-color palette as (R, G, B) triples."""
    return decode_palette(
        rom.get_bytes(palette_addr(window_num), WINDOW_PALETTE_FULL_SIZE))


def set_window_palette_full(rom, window_num: int,
                            colors: Sequence[Tuple[int, int, int]]) -> None:
    """Write 16 (R, G, B) triples as window N's full palette."""
    rom.set_bytes(palette_addr(window_num), encode_palette(colors))


# ---- Convenience: write graphics + palette in one shot --------------

def set_window_image(rom, window_num: int,
                     pixels: Sequence[Sequence[int]],
                     colors: Sequence[Tuple[int, int, int]]) -> None:
    """Pack ``pixels`` (56x32 indices) + ``colors`` (16 RGB triples) into rom."""
    set_window_graphics(rom, window_num, encode_window_sheet(pixels))
    set_window_palette_full(rom, window_num, colors)


def get_window_image(rom, window_num: int):
    """Return ``(pixels, colors)`` for window N -- inverse of ``set_window_image``."""
    pixels = decode_window_sheet(get_window_graphics(rom, window_num))
    colors = get_window_palette_full(rom, window_num)
    return pixels, colors


# ---- Helpers for the romdata/ reference dumps -----------------------

def parse_hex_dump(text: str) -> List[int]:
    """Parse the space-separated hex byte format used in ``romdata/*.txt``."""
    return [int(tok, 16) for tok in text.split()]
