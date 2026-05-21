"""Extract / inject FF6 menu window graphics as indexed PNGs.

Two subcommands:

  extract  Read window graphics + palettes from a ROM (or from the
           romdata/*.txt reference dumps) and write one indexed PNG per
           window.  Useful as a visual sanity check and as a starting
           point for hand-editing.

  pack     Read an indexed PNG and emit the 896-byte graphics blob plus
           the 32-byte palette as raw binary files (or patch them
           directly into a ROM, with ``--rom-out``).

PNG palette convention: 16-entry indexed PNG.  Index 0 is the
transparent / outside-window color (drawn as black in the PNG).
Indices 1..7 are the seven user-editable slots.  Indices 8..15 carry
the stock filler (0x3800 BGR15) but are unreferenced; ``pack`` accepts
PNGs that only define indices 0..7.

Examples
--------

  # Dump all eight stock sheets from the shipped romdata text files.
  python scripts/window_graphics.py extract --source romdata --outdir /tmp/wgfx

  # Pull them straight from a ROM.
  python scripts/window_graphics.py extract --source rom.smc --outdir /tmp/wgfx

  # Round-trip a hand-edited PNG back to the same window slot.
  python scripts/window_graphics.py pack /tmp/wgfx/W3.png --window 3 \\
      --rom-in rom.smc --rom-out rom_patched.smc
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from config import window_graphics as wg
from config.rom import ROM

try:
    from PIL import Image
except ImportError:
    print("scripts/window_graphics.py needs Pillow.  pip install Pillow.",
          file=sys.stderr)
    raise


# ---- BGR15 <-> 8-bit RGB --------------------------------------------

def _expand5(c: int) -> int:
    """5-bit channel -> 8-bit, matching the SNES PPU output (bit-extended)."""
    return (c << 3) | (c >> 2)


def palette_to_png_bytes(colors):
    """Build a 768-byte (16*3 RGB + 240*3 zeros) palette table for PIL."""
    flat = []
    for r, g, b in colors:
        flat.extend([_expand5(r), _expand5(g), _expand5(b)])
    # PIL requires 256 entries.  Pad the rest with the transparent color.
    flat.extend([0] * (256 * 3 - len(flat)))
    return flat


def png_palette_to_bgr15(pal_bytes):
    """Inverse of palette_to_png_bytes: take a 16-color RGB888 strip back to
    (R, G, B) 0..31 triples, rounding to nearest 5-bit value.

    Forward map is the bit-extended ``(c << 3) | (c >> 2)`` so the inverse
    must match: ``round(c * 31 / 255)`` is the nearest-neighbor of that.
    """
    def to5(c):
        v = (c * 31 + 127) // 255
        return min(31, max(0, v))
    colors = []
    for i in range(16):
        r, g, b = pal_bytes[3 * i : 3 * i + 3]
        colors.append((to5(r), to5(g), to5(b)))
    return colors


# ---- PNG IO ---------------------------------------------------------

def write_indexed_png(pixels, colors, path: Path) -> None:
    """Write a 32x56 indexed PNG with the given 16-color palette."""
    img = Image.new("P", (wg.SHEET_WIDTH, wg.SHEET_HEIGHT))
    img.putpalette(palette_to_png_bytes(colors))
    flat = bytes(px for row in pixels for px in row)
    img.frombytes(flat)
    img.save(path)


def read_indexed_png(path: Path):
    """Return (pixels, colors) from an indexed PNG.

    The PNG must be mode 'P', exactly 32x56, with a 16-entry palette.
    """
    img = Image.open(path)
    if img.mode != "P":
        raise ValueError(f"{path}: expected indexed PNG (mode 'P'), got {img.mode}")
    if img.size != (wg.SHEET_WIDTH, wg.SHEET_HEIGHT):
        raise ValueError(
            f"{path}: expected {wg.SHEET_WIDTH}x{wg.SHEET_HEIGHT}, got {img.size}")
    pal = img.getpalette()
    if pal is None:
        raise ValueError(f"{path}: indexed PNG has no palette")
    colors = png_palette_to_bgr15(pal[: 16 * 3])
    raw = img.tobytes()
    pixels = [
        [raw[y * wg.SHEET_WIDTH + x] for x in range(wg.SHEET_WIDTH)]
        for y in range(wg.SHEET_HEIGHT)
    ]
    used = {px for row in pixels for px in row}
    if any(p > 15 for p in used):
        raise ValueError(f"{path}: pixel index > 15 found ({sorted(used)})")
    return pixels, colors


# ---- Source readers --------------------------------------------------

def _load_romdata():
    """Read the shipped romdata/*.txt reference dumps as (gfx_bytes, pal_bytes).

    Each is zero-padded up to the full region size to compensate for the
    single trailing byte the dumps are missing.
    """
    gfx_path = REPO_ROOT / "romdata" / "ED0000_MenuWindowGraphics.txt"
    pal_path = REPO_ROOT / "romdata" / "ED1C00_MenuWindowPalettes.txt"
    gfx = wg.parse_hex_dump(gfx_path.read_text())
    pal = wg.parse_hex_dump(pal_path.read_text())
    gfx_full = 8 * wg.WINDOW_GRAPHICS_SIZE
    pal_full = 8 * wg.WINDOW_PALETTE_FULL_SIZE
    if len(gfx) < gfx_full:
        gfx = gfx + [0] * (gfx_full - len(gfx))
    if len(pal) < pal_full:
        pal = pal + [0] * (pal_full - len(pal))
    return gfx, pal


def _read_window_from_bytes(gfx_all, pal_all, n: int):
    gfx_off = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
    pal_off = (n - 1) * wg.WINDOW_PALETTE_FULL_SIZE
    gfx = gfx_all[gfx_off : gfx_off + wg.WINDOW_GRAPHICS_SIZE]
    pal = pal_all[pal_off : pal_off + wg.WINDOW_PALETTE_FULL_SIZE]
    return wg.decode_window_sheet(gfx), wg.decode_palette(pal)


# ---- Subcommands -----------------------------------------------------

def cmd_extract(args) -> int:
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.source == "romdata":
        gfx_all, pal_all = _load_romdata()
        def read_window(n):
            return _read_window_from_bytes(gfx_all, pal_all, n)
    else:
        rom = ROM(args.source)
        def read_window(n):
            return wg.get_window_image(rom, n)

    for n in range(1, wg.NUM_WINDOWS + 1):
        pixels, colors = read_window(n)
        out = outdir / f"W{n}.png"
        write_indexed_png(pixels, colors, out)
        print(f"wrote {out}")
    return 0


def cmd_pack(args) -> int:
    pixels, colors = read_indexed_png(Path(args.png))
    used = {px for row in pixels for px in row}
    if any(p > 7 for p in used):
        print(f"warning: PNG uses palette indices > 7: {sorted(p for p in used if p > 7)}",
              file=sys.stderr)

    gfx_bytes = wg.encode_window_sheet(pixels)
    pal_bytes = wg.encode_palette(colors)

    if args.rom_out:
        if not args.rom_in:
            print("--rom-out requires --rom-in", file=sys.stderr)
            return 2
        rom = ROM(args.rom_in)
        wg.set_window_graphics(rom, args.window, gfx_bytes)
        wg.set_window_palette_full(rom, args.window, colors)
        rom.write(args.rom_out)
        print(f"patched W{args.window} into {args.rom_out}")
        return 0

    # Otherwise dump the raw byte blobs.
    base = Path(args.gfx_out) if args.gfx_out else Path(args.png).with_suffix("")
    gfx_path = Path(args.gfx_out) if args.gfx_out else Path(f"{base}.gfx.bin")
    pal_path = Path(args.pal_out) if args.pal_out else Path(f"{base}.pal.bin")
    gfx_path.write_bytes(bytes(gfx_bytes))
    pal_path.write_bytes(bytes(pal_bytes))
    print(f"wrote {gfx_path} ({len(gfx_bytes)} bytes)")
    print(f"wrote {pal_path} ({len(pal_bytes)} bytes)")
    return 0


# ---- argparse --------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="dump window sheets as indexed PNGs")
    pe.add_argument("--source", default="romdata",
                    help="'romdata' (default) or a ROM file path")
    pe.add_argument("--outdir", required=True, help="directory to write W*.png into")
    pe.set_defaults(func=cmd_extract)

    pp = sub.add_parser("pack", help="encode an indexed PNG into ROM bytes")
    pp.add_argument("png", help="32x56 indexed PNG with up to 8 colors")
    pp.add_argument("--window", type=int, default=1, choices=range(1, 9),
                    help="target window slot 1..8 (only used with --rom-out)")
    pp.add_argument("--rom-in", help="source ROM (read before patching)")
    pp.add_argument("--rom-out", help="patched ROM output path")
    pp.add_argument("--gfx-out", help="raw 896-byte graphics blob output path")
    pp.add_argument("--pal-out", help="raw 32-byte palette output path")
    pp.set_defaults(func=cmd_pack)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
