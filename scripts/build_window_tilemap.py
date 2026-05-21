"""Derive FF6's window-engine tilemap from the existing screenshot set.

For each on-screen 8x8 cell in the config menu, the engine places a
specific tile from the active window's 4x7 = 28-tile source sheet
(possibly flipped).  The tilemap is the SAME across all eight window
styles -- only the source-sheet content differs -- so deriving it
once gives us a faithful map we can apply to any custom design.

Output: ``web/window_tilemap.js`` -- sets ``window.WINDOW_TILEMAP``
to ``{B: {y_off, width, height, tile: Uint8Array, flip: Uint8Array,
mapped: Uint8Array}, A: {...}}``.  ``tile[ty*width + tx]`` is the
source tile index 0..27 (0 = top-left tile of the sheet, scanning
right then down); ``flip[ty*width + tx]`` is a 2-bit flag (1=hflip,
2=vflip).  ``mapped[ty*width + tx]`` is 1 if the cell is part of
the window's chrome, 0 if it's wallpaper / text / unmapped.

Pre-baked into a JS module rather than computed in-browser because
it depends on the existing per-window-style isolation screenshots
which are slow to fetch + decode on page load.

Methodology:
  1. Pick a "reference" window with distinct, textured tiles in its
     source sheet (W3's water pattern works because every interior
     tile is visually unique -- W1's solid-color tiles are all
     interchangeable and produce ambiguous matches).
  2. For each pixel in the reference window's slot screenshots,
     derive the "vanilla slot index" by argmaxing
     |slot[k] - baseline| over k=1..7.
  3. The engine's on-screen tile grid is offset from the screen
     origin by (0, 7) -- determined by sweeping x_off, y_off and
     picking the alignment that maximizes per-tile pattern match.
  4. For each on-screen 8x8 cell aligned to (0, 7), find the source
     tile + flip orientation that matches the cell's slot pattern.
  5. Verify against multiple other textured windows (W2, W4, W5,
     W6, W8) -- if the SAME tilemap fits their screenshots too,
     it really is the engine's tilemap (and not a W3-specific
     artifact).

Run as:
    python scripts/build_window_tilemap.py
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from config import window_graphics as wg


REFERENCE_WINDOW = 3       # textured enough for unambiguous matches
VERIFY_WINDOWS = (2, 4, 5, 6, 8)   # other textured windows
Y_OFFSET = 7               # engine's vertical tile-grid offset


def _slot_indices(screenshot_dir: Path, prefix: str):
    """Build a 256x224 per-pixel slot-index map (0 = not chrome, 1..7 = slot K)."""
    baseline = np.array(Image.open(screenshot_dir / f"{prefix}_0.png").convert("RGB"))
    slots = [
        np.array(Image.open(screenshot_dir / f"{prefix}_{i}.png").convert("RGB"))
        for i in range(1, 8)
    ]
    diffs = np.stack([
        np.max(np.abs(s.astype(np.int16) - baseline.astype(np.int16)), axis=2)
        for s in slots
    ])
    slot_idx = (np.argmax(diffs, axis=0) + 1).astype(np.uint8)
    slot_idx[np.max(diffs, axis=0) < 8] = 0
    return slot_idx


def _source_tiles(window_n: int):
    raw = wg.parse_hex_dump(
        (REPO_ROOT / "romdata" / "ED0000_MenuWindowGraphics.txt").read_text())
    raw += [0] * (8 * wg.WINDOW_GRAPHICS_SIZE - len(raw))
    base = (window_n - 1) * wg.WINDOW_GRAPHICS_SIZE
    sheet = np.array(
        wg.decode_window_sheet(raw[base : base + wg.WINDOW_GRAPHICS_SIZE]),
        dtype=np.uint8,
    )
    return [
        sheet[ty * 8 : (ty + 1) * 8, tx * 8 : (tx + 1) * 8]
        for ty in range(7)
        for tx in range(4)
    ]


def derive_tilemap(slot_idx, src_tiles, y_off=Y_OFFSET, match_threshold=0.95):
    """Return (tilemap, flipmap, mapped_mask) for an aligned 8x8 grid."""
    H, W = slot_idx.shape
    TY = (H - y_off) // 8
    TX = W // 8
    tilemap = np.zeros((TY, TX), dtype=np.uint8)
    flipmap = np.zeros((TY, TX), dtype=np.uint8)
    mapped  = np.zeros((TY, TX), dtype=np.uint8)
    for ty in range(TY):
        for tx in range(TX):
            y0 = y_off + ty * 8
            patch = slot_idx[y0 : y0 + 8, tx * 8 : (tx + 1) * 8]
            visible = int((patch > 0).sum())
            if visible < 16:
                continue
            best_score, best_ti, best_flip = 0, 0, 0
            for ti, st in enumerate(src_tiles):
                for flip in range(4):
                    t = st
                    if flip & 1: t = t[:, ::-1]
                    if flip & 2: t = t[::-1, :]
                    score = int(((t == patch) & (patch > 0)).sum())
                    if score > best_score:
                        best_score, best_ti, best_flip = score, ti, flip
            if best_score / visible >= match_threshold:
                tilemap[ty, tx] = best_ti
                flipmap[ty, tx] = best_flip
                mapped[ty, tx] = 1
    return tilemap, flipmap, mapped


def verify(tilemap, flipmap, mapped, slot_idx, src_tiles, y_off=Y_OFFSET):
    """Apply tilemap to a different window's source sheet + screenshots; return mismatch count."""
    TY, TX = tilemap.shape
    bad = 0
    checked = 0
    for ty in range(TY):
        for tx in range(TX):
            if not mapped[ty, tx]:
                continue
            fl = flipmap[ty, tx]
            expected = src_tiles[tilemap[ty, tx]]
            if fl & 1: expected = expected[:, ::-1]
            if fl & 2: expected = expected[::-1, :]
            y0 = y_off + ty * 8
            patch = slot_idx[y0 : y0 + 8, tx * 8 : (tx + 1) * 8]
            visible = int((patch > 0).sum())
            if visible < 16:
                continue
            checked += 1
            if ((expected == patch) & (patch > 0)).sum() / visible < 0.85:
                bad += 1
    return bad, checked


def build_for_page(prefix_b, screenshot_subdir):
    """Derive the tilemap for one page from the reference window's screenshots."""
    ref_dir = REPO_ROOT / "screenshots" / screenshot_subdir
    slot_ref = _slot_indices(ref_dir, prefix_b)
    tiles_ref = _source_tiles(REFERENCE_WINDOW)
    tm, fm, mm = derive_tilemap(slot_ref, tiles_ref)
    mapped_count = int(mm.sum())
    print(f"  {screenshot_subdir}/{prefix_b}: mapped {mapped_count} / {tm.size} cells")

    for vn in VERIFY_WINDOWS:
        # The Page A screenshots live in screenshots/W{n}A/ with prefix W{n}A.
        if screenshot_subdir.endswith("A"):
            vdir = REPO_ROOT / "screenshots" / f"W{vn}A"
            vprefix = f"W{vn}A"
        else:
            vdir = REPO_ROOT / "screenshots" / f"W{vn}"
            vprefix = f"W{vn}"
        if not (vdir / f"{vprefix}_0.png").exists():
            print(f"    (skipping W{vn}; missing isolations)")
            continue
        slot_v = _slot_indices(vdir, vprefix)
        bad, checked = verify(tm, fm, mm, slot_v, _source_tiles(vn))
        print(f"    vs W{vn}: {checked - bad}/{checked} cells consistent")
    return tm, fm, mm


def main():
    print("Deriving Page B tilemap from W3's slot screenshots...")
    tm_b, fm_b, mm_b = build_for_page("W3", "W3")
    print()
    print("Deriving Page A tilemap from W3A's slot screenshots...")
    tm_a, fm_a, mm_a = build_for_page("W3A", "W3A")

    out_path = REPO_ROOT / "web" / "window_tilemap.js"
    with out_path.open("w") as f:
        f.write("// Auto-generated by scripts/build_window_tilemap.py -- do not edit.\n")
        f.write("// FF6 config menu window tilemap: for each 8x8 on-screen cell,\n")
        f.write("// which tile of the active window's 4x7 source sheet sits there\n")
        f.write("// (and how it's flipped).\n//\n")
        f.write(f"// Engine tile grid starts at y = {Y_OFFSET} (not the screen origin)\n")
        f.write("// because the menu's window doesn't start on an 8-pixel boundary.\n")
        f.write("// `tile[ty * width + tx]` is the source tile index (0..27,\n")
        f.write("// scanning the sheet left-to-right, top-to-bottom).\n")
        f.write("// `flip[ty * width + tx]` encodes hflip in bit 0, vflip in bit 1.\n")
        f.write("// `mapped[ty * width + tx]` is 1 for chrome cells, 0 for cells\n")
        f.write("// not part of the window (wallpaper/text/unmapped).\n\n")
        f.write("window.WINDOW_TILEMAP = {\n")
        f.write(f"  Y_OFFSET: {Y_OFFSET},\n")
        for page_key, (tm, fm, mm) in (
            ("B", (tm_b, fm_b, mm_b)),
            ("A", (tm_a, fm_a, mm_a)),
        ):
            ty_n, tx_n = tm.shape
            f.write(f"  {json.dumps(page_key)}: {{\n")
            f.write(f"    width: {tx_n}, height: {ty_n},\n")
            f.write("    tile: new Uint8Array([" + ",".join(str(v) for v in tm.flatten()) + "]),\n")
            f.write("    flip: new Uint8Array([" + ",".join(str(v) for v in fm.flatten()) + "]),\n")
            f.write("    mapped: new Uint8Array([" + ",".join(str(v) for v in mm.flatten()) + "]),\n")
            f.write("  },\n")
        f.write("};\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
