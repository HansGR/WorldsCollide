"""Build web-UI assets from window-style isolation screenshots.

Per window style i, the screenshots/Wi/ folder is expected to contain:
  - Wi_0.png         all 7 slots set to [0,0,0]; font set to [0,0,0]
  - Wi_1.png ... Wi_7.png   only slot N is bright; everything else [0,0,0]
  - Wi_font.png      font color bright; all 7 slots [0,0,0]
  - Wi_defaultA.png, Wi_defaultB.png   reference shots with default palette

The web UI composites these per-pixel as:

    output[p] = baseline[p]
              + Σ (raw{n}[p] - baseline[p]) * c_n / 31
              + (font_raw[p] - baseline[p]) * c_font / 31

so we need to preserve the *signed* delta.  Storing raw screenshots is the
simplest way to do that — JS does the subtraction at render time, with
full precision in either direction.

This script copies the relevant screenshots into ``web/assets/W{i}/`` and
emits a ``manifest.json`` so the UI knows which window styles ship with
art and which need a placeholder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parent.parent
SHOTS_DIR = REPO_ROOT / "screenshots"
ASSETS_DIR = REPO_ROOT / "web" / "assets"


def _load(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def _save(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr.astype(np.uint8), "RGB").save(path, optimize=True)


CURSOR_X_LO = 90
CURSOR_X_HI = 116
CURSOR_COPY_OFFSET = 32  # The wallpaper tiles every 32 px horizontally, so
                         # copying from x-32 recovers the "underlying"
                         # background that the cursor sprite is hiding.
CURSOR_MIN_SIZE = 30
CURSOR_MAX_SIZE = 200


def _find_cursor_mask(baseline: np.ndarray) -> np.ndarray:
    """Return a boolean mask of cursor-sprite pixels in the baseline image.

    The screenshots are captured with the menu cursor parked in a fixed
    spot (consistent across W_0, W_1..W_7, and W_font for a given window).
    That sprite shows up as a tight bright cluster in the cursor X-gutter
    (x ∈ [90, 116]).
    """
    H, W, _ = baseline.shape
    # Bright pixels in the gutter (the cursor is the brightest thing here
    # when all slots are [0,0,0]).
    gray = baseline.mean(-1)
    cand = gray > 130
    cand[:, :CURSOR_X_LO] = False
    cand[:, CURSOR_X_HI:] = False
    if not cand.any():
        return np.zeros((H, W), bool)
    # Take all CCs in the cursor-sprite size band and union them.
    visited = np.zeros_like(cand)
    mask = np.zeros_like(cand)
    for y0 in range(H):
        for x0 in range(CURSOR_X_LO, CURSOR_X_HI):
            if not cand[y0, x0] or visited[y0, x0]:
                continue
            stack = [(y0, x0)]; pts = []
            while stack:
                y, x = stack.pop()
                if not (0 <= y < H and 0 <= x < W): continue
                if visited[y, x] or not cand[y, x]: continue
                visited[y, x] = True
                pts.append((y, x))
                stack.extend(((y+1,x),(y-1,x),(y,x+1),(y,x-1)))
            if CURSOR_MIN_SIZE <= len(pts) <= CURSOR_MAX_SIZE:
                for (py, px) in pts:
                    mask[py, px] = True
    return mask


def _apply_cursor_mask(images: list[np.ndarray | None],
                       cursor_mask: np.ndarray) -> list[np.ndarray | None]:
    """Inpaint cursor pixels in each image by copying from 32 px to the left.

    The menu wallpaper tiles on a 32-px horizontal period, so the pixel
    at (y, x-32) is essentially what would be visible at (y, x) if the
    cursor weren't there.  We apply the same copy to baseline, every slot
    raw, and the font raw, so the *delta* the recolor pass sees over the
    cursor region is the same as everywhere else.
    """
    if not cursor_mask.any():
        return [im.copy() if im is not None else None for im in images]
    ys, xs = np.where(cursor_mask)
    src_xs = xs - CURSOR_COPY_OFFSET
    if (src_xs < 0).any():
        # If the offset would step outside the image, fall back to +32 instead.
        src_xs = np.where(src_xs >= 0, src_xs, xs + CURSOR_COPY_OFFSET)
    out = []
    for im in images:
        if im is None:
            out.append(None); continue
        patched = im.copy()
        patched[ys, xs] = im[ys, src_xs]
        out.append(patched)
    return out


def build_window(window_index: int) -> dict | None:
    src = SHOTS_DIR / f"W{window_index}"
    baseline_path = src / f"W{window_index}_0.png"
    if not baseline_path.exists():
        return None

    out_dir = ASSETS_DIR / f"W{window_index}"
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_baseline = _load(baseline_path)

    raw_slots: list[np.ndarray | None] = []
    slot_indices: list[int] = []
    for n in range(1, 8):
        p = src / f"W{window_index}_{n}.png"
        if p.exists():
            raw_slots.append(_load(p))
            slot_indices.append(n)
        else:
            raw_slots.append(None)

    font_path = src / f"W{window_index}_font.png"
    font_present = font_path.exists()
    raw_font = _load(font_path) if font_present else None

    # The user parks the menu cursor in the same spot for every shot of
    # a given window.  Detect the sprite from the baseline (only bright
    # thing in the gutter when all slots are [0,0,0]) and inpaint it in
    # all images by copying from 32 px to the left, where the wallpaper's
    # tile pattern places the same content.
    cursor_mask = _find_cursor_mask(raw_baseline)
    if cursor_mask.any():
        patched = _apply_cursor_mask([raw_baseline, raw_font, *raw_slots], cursor_mask)
        baseline = patched[0]
        font_clean = patched[1]
        cleaned_slots = patched[2:]
    else:
        baseline = raw_baseline
        font_clean = raw_font
        cleaned_slots = raw_slots

    _save(baseline, out_dir / "baseline.png")
    for n, im in zip(range(1, 8), cleaned_slots):
        if im is not None:
            _save(im, out_dir / f"slot{n}.png")
    if font_clean is not None:
        _save(font_clean, out_dir / "font.png")

    for tag in ("A", "B"):
        ref = src / f"W{window_index}_default{tag}.png"
        if ref.exists():
            _save(_load(ref), out_dir / f"default{tag}.png")

    return {
        "window": window_index,
        "slots": slot_indices,
        "font": font_present,
        "hasDefaultA": (src / f"W{window_index}_defaultA.png").exists(),
        "hasDefaultB": (src / f"W{window_index}_defaultB.png").exists(),
    }


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"windows": {}}
    for i in range(1, 9):
        info = build_window(i)
        if info is not None:
            manifest["windows"][str(i)] = info
            print(f"built W{i}: {info}")
    out = ASSETS_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
