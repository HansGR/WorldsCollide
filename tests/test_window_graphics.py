"""Smoke tests for config/window_graphics.py.

Run as:
    python tests/test_window_graphics.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import window_graphics as wg
from config import config as cfg


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GFX_DUMP = os.path.join(REPO_ROOT, "romdata", "ED0000_MenuWindowGraphics.txt")
PAL_DUMP = os.path.join(REPO_ROOT, "romdata", "ED1C00_MenuWindowPalettes.txt")


def _load_dump(path: str, expected_size: int) -> list:
    """Parse a hex-dump file from romdata/, zero-padding to the expected size.

    ED1C00 is 256 bytes, ED0000 is 7168 bytes; both reference dumps end one
    byte short of those totals (trailing zero byte trimmed by whatever tool
    produced them), so pad with 0x00 to keep the round-trip honest.
    """
    with open(path) as f:
        data = wg.parse_hex_dump(f.read())
    if len(data) < expected_size:
        data = data + [0] * (expected_size - len(data))
    elif len(data) > expected_size:
        raise AssertionError(
            f"{path}: got {len(data)} bytes, expected at most {expected_size}")
    return data


# ---- 4bpp tile codec round-trip --------------------------------------

def test_decode_encode_4bpp_tile_round_trip():
    # A few hand-picked tile shapes that span all 16 palette indices.
    cases = [
        [[i] * 8 for i in range(8)],                       # horizontal bands 0..7
        [[(x + y) & 0xF for x in range(8)] for y in range(8)],   # diagonal mix 0..15
        [[0] * 8 for _ in range(8)],                       # all transparent
        [[15] * 8 for _ in range(8)],                      # all color 15
    ]
    for pixels in cases:
        encoded = wg.encode_tile_4bpp(pixels)
        assert len(encoded) == 32
        assert wg.decode_tile_4bpp(encoded) == pixels


def test_decode_tile_known_solid_color_pattern():
    """First tile of W1's stock sheet decodes to solid color 7.

    bp0=ff, bp1=ff, bp2=ff, bp3=00 per row -> every pixel = 0b0111 = 7.
    """
    raw = [0xFF] * 16 + [0xFF, 0x00] * 8
    pixels = wg.decode_tile_4bpp(raw)
    assert all(px == 7 for row in pixels for px in row)


def test_encode_tile_rejects_out_of_range():
    bad = [[16] + [0] * 7] + [[0] * 8 for _ in range(7)]
    try:
        wg.encode_tile_4bpp(bad)
    except ValueError:
        return
    raise AssertionError("expected ValueError for out-of-range pixel")


# ---- Sheet codec round-trip ------------------------------------------

def test_decode_encode_sheet_round_trip_on_stock_dump():
    """Decoding then re-encoding the shipped ROM data must be bit-perfect.

    This is the central correctness claim of the module: if either the tile
    layout (4x7) or the bitplane layout (low-then-high) were wrong, the
    re-encoded bytes would diverge from the original.
    """
    raw = _load_dump(GFX_DUMP, 8 * wg.WINDOW_GRAPHICS_SIZE)
    for n in range(1, wg.NUM_WINDOWS + 1):
        base = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
        window = raw[base : base + wg.WINDOW_GRAPHICS_SIZE]
        pixels = wg.decode_window_sheet(window)
        assert len(pixels) == wg.SHEET_HEIGHT
        assert len(pixels[0]) == wg.SHEET_WIDTH
        re_encoded = wg.encode_window_sheet(pixels)
        assert re_encoded == window, (
            f"W{n}: re-encoded sheet differs from ROM bytes")


def test_decoded_sheets_only_use_indices_1_through_7():
    """Stock window sheets reference only the seven user-editable colors.

    (Plus index 0 which would be transparent -- but the shipped sheets
    don't actually use it; every pixel falls in 1..7.)
    """
    raw = _load_dump(GFX_DUMP, 8 * wg.WINDOW_GRAPHICS_SIZE)
    for n in range(1, wg.NUM_WINDOWS + 1):
        base = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
        pixels = wg.decode_window_sheet(raw[base : base + wg.WINDOW_GRAPHICS_SIZE])
        used = {px for row in pixels for px in row}
        assert used <= set(range(1, 8)), f"W{n} uses {sorted(used)}"


# ---- Palette codec round-trip ----------------------------------------

def test_decode_encode_palette_round_trip_on_stock_dump():
    raw = _load_dump(PAL_DUMP, 8 * wg.WINDOW_PALETTE_FULL_SIZE)
    for n in range(1, wg.NUM_WINDOWS + 1):
        base = (n - 1) * wg.WINDOW_PALETTE_FULL_SIZE
        chunk = raw[base : base + wg.WINDOW_PALETTE_FULL_SIZE]
        colors = wg.decode_palette(chunk)
        assert len(colors) == 16
        assert wg.encode_palette(colors) == chunk, f"W{n} palette mismatch"


def test_stock_palette_matches_config_defaults():
    """Slots 1..7 of the shipped ROM palette must match config.WINDOW_DEFAULTS.

    This cross-checks the encoding against the values the existing config
    pipeline already trusts.
    """
    raw = _load_dump(PAL_DUMP, 8 * wg.WINDOW_PALETTE_FULL_SIZE)
    for n in range(1, wg.NUM_WINDOWS + 1):
        base = (n - 1) * wg.WINDOW_PALETTE_FULL_SIZE
        colors = wg.decode_palette(raw[base : base + wg.WINDOW_PALETTE_FULL_SIZE])
        expected = cfg.WINDOW_DEFAULTS[f"Window{n}"]
        for slot in range(7):
            got = list(colors[slot + 1])
            assert got == expected[slot], (
                f"W{n} slot {slot + 1}: ROM {got} != defaults {expected[slot]}")
        # Index 0 is transparent black.
        assert colors[0] == (0, 0, 0), f"W{n} index 0 is not (0,0,0)"
        # Indices 8..15 are filler 0x3800 = (0, 0, 14).  The shipped
        # romdata/ED1C00_*.txt is one byte short of the full region, so
        # W8's last byte is missing; skip that final entry only.
        last_filler = 15 if n < wg.NUM_WINDOWS else 14
        for i in range(8, last_filler + 1):
            assert colors[i] == (0, 0, 14), f"W{n} index {i} = {colors[i]}"


def test_encode_palette_rejects_out_of_range():
    colors = [(0, 0, 0)] * 16
    colors[3] = (32, 0, 0)
    try:
        wg.encode_palette(colors)
    except ValueError:
        return
    raise AssertionError("expected ValueError for out-of-range color channel")


# ---- ROM IO via _FakeRom ---------------------------------------------

class _FakeRom:
    def __init__(self, size):
        self.data = bytearray(size)

    def get_bytes(self, addr, count):
        return list(self.data[addr : addr + count])

    def set_bytes(self, addr, values):
        self.data[addr : addr + len(values)] = bytes(values)
        return addr + len(values)


def test_graphics_addr_and_palette_addr_progressions():
    # Window 1 sits at the bases; window 8 sits 7 strides higher.
    assert wg.graphics_addr(1) == 0x2D0000
    assert wg.graphics_addr(8) == 0x2D0000 + 7 * 0x380
    assert wg.palette_addr(1) == 0x2D1C00
    assert wg.palette_addr(8) == 0x2D1C00 + 7 * 0x20


def test_graphics_addr_rejects_out_of_range():
    for bad in [0, 9, -1]:
        try:
            wg.graphics_addr(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for window {bad}")


def test_set_then_get_window_image_round_trip():
    rom = _FakeRom(0x2E0000)
    pixels = [[(x + y) & 0xF for x in range(wg.SHEET_WIDTH)]
              for y in range(wg.SHEET_HEIGHT)]
    colors = [(i, (i * 2) & 0x1F, (i * 3) & 0x1F) for i in range(16)]
    wg.set_window_image(rom, 3, pixels, colors)
    got_pixels, got_colors = wg.get_window_image(rom, 3)
    assert got_pixels == pixels
    assert got_colors == colors
    # And the write only touched window 3's slots.
    assert rom.data[wg.graphics_addr(2) : wg.graphics_addr(3)] == bytes(0x380)
    assert rom.data[wg.graphics_addr(4) : wg.graphics_addr(4) + 0x380] == bytes(0x380)


def test_set_window_graphics_rejects_wrong_size():
    rom = _FakeRom(0x2E0000)
    try:
        wg.set_window_graphics(rom, 1, [0] * 895)
    except ValueError:
        return
    raise AssertionError("expected ValueError for wrong-size graphics blob")


def test_get_window_graphics_reads_stock_blob():
    """Plant the romdata dump in a fake ROM, read it back via the API."""
    raw = _load_dump(GFX_DUMP, 8 * wg.WINDOW_GRAPHICS_SIZE)
    rom = _FakeRom(0x2E0000)
    rom.data[wg.WINDOW_GRAPHICS_BASE :
             wg.WINDOW_GRAPHICS_BASE + 8 * wg.WINDOW_GRAPHICS_SIZE] = bytes(raw)
    for n in range(1, wg.NUM_WINDOWS + 1):
        base = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
        assert wg.get_window_graphics(rom, n) == raw[base : base + 0x380]


# ---- PNG round-trip via the scripts/ helpers -------------------------

def test_png_round_trip_through_scripts_module():
    """Extract -> read PNG -> re-encode reproduces the ROM bytes exactly.

    Skipped silently if Pillow isn't installed (the library itself doesn't
    need it; only the CLI does).
    """
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("  (PIL not installed; skipping PNG round-trip)")
        return

    import tempfile
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
    from scripts.window_graphics import write_indexed_png, read_indexed_png

    gfx_all = _load_dump(GFX_DUMP, 8 * wg.WINDOW_GRAPHICS_SIZE)
    pal_all = _load_dump(PAL_DUMP, 8 * wg.WINDOW_PALETTE_FULL_SIZE)

    with tempfile.TemporaryDirectory() as td:
        for n in range(1, wg.NUM_WINDOWS + 1):
            g_off = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
            p_off = (n - 1) * wg.WINDOW_PALETTE_FULL_SIZE
            pixels = wg.decode_window_sheet(gfx_all[g_off : g_off + 0x380])
            colors = wg.decode_palette(pal_all[p_off : p_off + 0x20])

            path = os.path.join(td, f"W{n}.png")
            write_indexed_png(pixels, colors, path)
            got_pixels, got_colors = read_indexed_png(path)

            # Pixels are exact; palette round-trips through RGB888 with the
            # bit-extended expansion + nearest-neighbor inverse.
            assert got_pixels == pixels, f"W{n}: pixels diverge after PNG round-trip"
            assert wg.encode_window_sheet(got_pixels) == gfx_all[g_off : g_off + 0x380]
            assert wg.encode_palette(got_colors) == pal_all[p_off : p_off + 0x20]


# ---- runner ----------------------------------------------------------

def main():
    tests = sorted(
        (name, fn) for name, fn in globals().items()
        if name.startswith("test_") and callable(fn)
    )
    failed = []
    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"FAIL: {name}: {type(e).__name__}: {e}")
            failed.append(name)
        else:
            print(f"PASS: {name}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
