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
# Asymmetric dilation around the detected cursor sprite (in pixels).
# The bare CC misses the drop shadow under the hand (pad down) and a thin
# bright outline around the sides; on the right the sprite sits flush
# against menu text so we trim that direction a little.
CURSOR_DILATE_LEFT  = 3
CURSOR_DILATE_RIGHT = 2
CURSOR_DILATE_UP    = 3
CURSOR_DILATE_DOWN  = 6


# Per-window default palette (matches config/config.py WINDOW_DEFAULTS).  We
# need this to render a "synth at defaults" image so we can fit a y-axis
# correction against the real defaultB screenshot.
WINDOW_DEFAULTS = {
    1: [[25,28,28],[20,22,22],[16,16,16],[10,10,10],[5,6,6],   [6,6,17],  [5,5,16]],
    2: [[14,15,15],[8,9,9],   [7,8,8],   [6,7,7],   [5,6,6],   [4,5,5],   [1,2,2]],
    3: [[7,13,16], [6,10,13], [4,7,10],  [3,6,7],   [2,4,5],   [2,3,4],   [10,15,19]],
    4: [[17,12,4], [15,11,4], [14,9,3],  [12,8,2],  [19,21,20],[7,9,8],   [4,6,5]],
    5: [[13,11,8], [12,11,8], [12,10,7], [11,9,6],  [10,8,4],  [7,7,4],   [2,2,2]],
    6: [[19,19,19],[13,15,15],[10,12,11],[8,10,9],  [6,8,7],   [4,6,5],   [1,3,2]],
    7: [[15,21,14],[12,17,11],[9,15,8],  [7,13,6],  [5,10,4],  [4,7,4],   [2,5,3]],
    8: [[20,12,13],[25,24,22],[20,19,16],[26,17,0], [25,13,0], [20,11,0], [4,4,4]],
}
FONT_DEFAULT = [31, 31, 31]


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
    if mask.any():
        mask = _dilate(mask, CURSOR_DILATE_LEFT, CURSOR_DILATE_RIGHT,
                       CURSOR_DILATE_UP, CURSOR_DILATE_DOWN)
    return mask


def _dilate(mask: np.ndarray, left: int, right: int,
            up: int, down: int) -> np.ndarray:
    """Asymmetric binary dilation (4-connected, per direction)."""
    out = mask.copy()
    for _ in range(up):
        out[:-1] |= out[1:]
    for _ in range(down):
        out[1:] |= out[:-1]
    for _ in range(left):
        out[:, :-1] |= out[:, 1:]
    for _ in range(right):
        out[:, 1:] |= out[:, :-1]
    return out


def _synth_at_defaults(window_index: int,
                       baseline: np.ndarray,
                       slots: list[np.ndarray | None],
                       font: np.ndarray | None) -> np.ndarray:
    """Mirror the JS recolor pass for window i with its default palette."""
    palette = WINDOW_DEFAULTS[window_index]
    H, W, _ = baseline.shape
    acc = np.zeros((H, W, 3), dtype=np.float32)
    # baseline weight = 1 − Σ c_n/31 − c_font/31  per channel
    wb = np.ones(3, dtype=np.float32)
    for n, im in enumerate(slots):
        if im is None: continue
        c = palette[n]
        wb -= np.array(c, dtype=np.float32) / 31.0
    if font is not None:
        wb -= np.array(FONT_DEFAULT, dtype=np.float32) / 31.0
    acc += baseline.astype(np.float32) * wb
    for n, im in enumerate(slots):
        if im is None: continue
        c = np.array(palette[n], dtype=np.float32) / 31.0
        acc += im.astype(np.float32) * c
    if font is not None:
        c = np.array(FONT_DEFAULT, dtype=np.float32) / 31.0
        acc += font.astype(np.float32) * c
    return np.clip(acc, 0, 255)


def _fit_y_correction(real_default: np.ndarray,
                      synth_default: np.ndarray) -> np.ndarray:
    """Return a (H, 3) per-row, per-channel correction.

    The SNES menu applies a per-scanline operation (color math + a
    gradient against another BG layer) that the linear baseline + Σ
    delta · c/31 model doesn't capture.  Empirically the residual is
    a smooth, almost-linear function of y across the active menu area,
    so we fit a single line per channel rather than carry the
    row-by-row noise from a per-row mean.

    The fit ignores the top-most and bottom-most rows where there's no
    actual window content (and so no informative residual signal).
    """
    res = (real_default.astype(np.float32)
           - synth_default.astype(np.float32))  # (H, W, 3)
    H = res.shape[0]
    per_row = res.mean(axis=1)                  # (H, 3)
    y = np.arange(H, dtype=np.float32)

    # Active menu vertical span — covers all 8 window styles.
    y_lo, y_hi = 8, 210
    mask = (y >= y_lo) & (y < y_hi)
    y_fit = y[mask]
    out = np.zeros_like(per_row)
    for ch in range(3):
        # Plain least-squares: corr(y) = slope·y + intercept.
        slope, intercept = np.polyfit(y_fit, per_row[mask, ch], 1)
        out[:, ch] = slope * y + intercept
    return out


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

    # Fit a per-row, per-channel correction against the default-palette
    # screenshot.  Stored as raw float arrays under correction.json so
    # the renderer can load them once and add a small constant to each
    # pixel based on its row.
    correction = None
    ref_default = src / f"W{window_index}_defaultB.png"
    if ref_default.exists():
        real = _load(ref_default)
        synth = _synth_at_defaults(window_index, baseline,
                                   list(cleaned_slots), font_clean)
        corr = _fit_y_correction(real, synth)  # (H, 3)
        # Round to 2 decimals to keep the JSON readable.
        correction = [[round(float(v), 2) for v in row] for row in corr]
        with open(out_dir / "correction.json", "w") as f:
            json.dump(correction, f)

    for tag in ("A", "B"):
        ref = src / f"W{window_index}_default{tag}.png"
        if ref.exists():
            _save(_load(ref), out_dir / f"default{tag}.png")

    return {
        "window": window_index,
        "slots": slot_indices,
        "font": font_present,
        "hasCorrection": correction is not None,
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
