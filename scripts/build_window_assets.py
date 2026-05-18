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


def _find_cursor_mask(baseline: np.ndarray,
                      y_lo: int = 0, y_hi: int | None = None) -> np.ndarray:
    """Return a boolean mask of cursor-sprite pixels in the baseline image.

    The screenshots are captured with the menu cursor parked in a fixed
    spot (consistent across W_0, W_1..W_7, and W_font for a given window).
    That sprite shows up as a tight bright cluster in the cursor X-gutter
    (x ∈ [90, 116]).

    For images that have menu chrome / text in the gutter (e.g. the
    default-palette references), pass y_lo/y_hi to restrict the search to
    the row band where the cursor is parked.
    """
    H, W, _ = baseline.shape
    if y_hi is None:
        y_hi = H
    # Bright pixels in the gutter (the cursor is the brightest thing here
    # when all slots are [0,0,0]).
    gray = baseline.mean(-1)
    cand = gray > 130
    cand[:, :CURSOR_X_LO] = False
    cand[:, CURSOR_X_HI:] = False
    cand[:y_lo, :] = False
    cand[y_hi:, :] = False
    if not cand.any():
        return np.zeros((H, W), bool)
    # Take all CCs in the cursor-sprite size band and union them.
    visited = np.zeros_like(cand)
    mask = np.zeros_like(cand)
    for y0 in range(y_lo, y_hi):
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
                       cursor_mask: np.ndarray,
                       offset: int = CURSOR_COPY_OFFSET) -> list[np.ndarray | None]:
    """Inpaint cursor pixels in each image by copying from ``offset`` px to the left.

    The menu wallpaper tiles on a 32-px horizontal period, so any multiple
    of 32 works as a source.  The default −32 lands in the gutter where
    the cursor sprite usually sits; the defaultA screenshot needs a
    larger offset because both x±32 and x+64 collide with menu text
    around the BatMode row, so callers pass +128 to source from past
    the "Wait" value instead.
    """
    if not cursor_mask.any():
        return [im.copy() if im is not None else None for im in images]
    H, W = cursor_mask.shape
    ys, xs = np.where(cursor_mask)
    src_xs = xs - offset
    # Wallpaper is 32-px periodic, so any in-bounds multiple of 32 works.
    # Step the offset to fit when the requested source falls off the edge.
    while (src_xs < 0).any() or (src_xs >= W).any():
        src_xs = np.where(src_xs < 0, src_xs + 32, src_xs)
        src_xs = np.where(src_xs >= W, src_xs - 32, src_xs)
    out = []
    for im in images:
        if im is None:
            out.append(None); continue
        patched = im.copy()
        patched[ys, xs] = im[ys, src_xs]
        out.append(patched)
    return out


COLOR_ROW_Y_LO, COLOR_ROW_Y_HI = 124, 132
COLOR_ROW_FONT_X = slice(112, 160)
COLOR_ROW_WINDOW_X = slice(176, 228)


def _fix_color_row_orientation(baseline: np.ndarray,
                               reference_strip: np.ndarray) -> np.ndarray:
    """If the baseline was captured with Window selected (Window label
    rendered bright, Font label invisible), overwrite the Color row strip
    with the reference (captured with Font selected).

    The Color-row strip in baseline.png is otherwise uniform black across
    every window — only the menu labels themselves carry signal — so we
    can wholesale-copy the y band from a known-good window without
    disturbing window-specific wallpaper.
    """
    g = baseline.max(-1)
    font_bright = int(g[COLOR_ROW_Y_LO:COLOR_ROW_Y_HI, COLOR_ROW_FONT_X].max())
    win_bright  = int(g[COLOR_ROW_Y_LO:COLOR_ROW_Y_HI, COLOR_ROW_WINDOW_X].max())
    if win_bright > font_bright + 30:
        baseline = baseline.copy()
        baseline[COLOR_ROW_Y_LO:COLOR_ROW_Y_HI] = reference_strip
    return baseline


def build_window(window_index: int,
                 default_a_cursor_mask: np.ndarray | None = None,
                 color_row_reference: np.ndarray | None = None) -> dict | None:
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
        # The cursor is parked on the B-slider row; the raw CC + right
        # dilation reaches x=112, which is the leading column of the "B"
        # glyph rendered into the font/slot images. Capping the mask at
        # x≤111 keeps the recolored Page B composite from clipping the
        # left edge of B. Then stamp the cursor's drop-shadow tip
        # (y=197..199, x=109..111) that the bright-pixel CC misses, so
        # it doesn't leak through as a black smudge below-left of B.
        cursor_mask[:, 112:] = False
        cursor_mask[197:200, 109:112] = True
        patched = _apply_cursor_mask([raw_baseline, raw_font, *raw_slots], cursor_mask)
        baseline = patched[0]
        font_clean = patched[1]
        cleaned_slots = patched[2:]
    else:
        baseline = raw_baseline
        font_clean = raw_font
        cleaned_slots = raw_slots

    # The 8-px strip just below the slot-color row and above the R bar
    # contains an in-game UI artifact: an up-pointing black arrow that
    # marks whichever slot was selected when the capture was taken. Its
    # x position differs per window, so erase the whole slot-row strip
    # (x=176..240, covering all seven 8-px swatches) and inpaint with
    # wallpaper from 96 px (3 tiles) to the left, where this y band is
    # uniformly wallpaper across every menu page.
    arrow_mask = np.zeros(raw_baseline.shape[:2], bool)
    arrow_mask[148:156, 176:240] = True
    patched = _apply_cursor_mask([baseline, font_clean, *cleaned_slots],
                                 arrow_mask, offset=96)
    baseline = patched[0]
    font_clean = patched[1]
    cleaned_slots = list(patched[2:])

    # W4 / W7 / W8 baselines were captured with the Color row's Window
    # label selected, leaving Font invisible and Window bright — the
    # opposite of W1's convention. Restore the Font-selected layout from
    # a reference strip (the strip is otherwise just black wallpaper, so
    # copying it doesn't disturb window-specific texture).
    if color_row_reference is not None:
        baseline = _fix_color_row_orientation(baseline, color_row_reference)

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
        if not ref.exists():
            continue
        img = _load(ref)
        if tag == "A" and default_a_cursor_mask is not None:
            # The cursor sprite is parked in the same spot in every
            # defaultA capture, but detecting it per-window yields
            # different bounding boxes (each wallpaper has a different
            # brightness profile around the gutter, so the CC search
            # picks up different false-positive pixels). Inpaint every
            # window with the same mask derived from W5, which gave the
            # cleanest result, so the cursor area is treated uniformly.
            img = _apply_cursor_mask([img], default_a_cursor_mask, offset=-128)[0]
        _save(img, out_dir / f"default{tag}.png")

    return {
        "window": window_index,
        "slots": slot_indices,
        "font": font_present,
        "hasCorrection": correction is not None,
        "hasDefaultA": (src / f"W{window_index}_defaultA.png").exists(),
        "hasDefaultB": (src / f"W{window_index}_defaultB.png").exists(),
    }


# --- Magic-order text overlays ----------------------------------------
#
# The three lines below "Mag.Order 1 2 3 4 5 6" change based on which
# spell-order preset is selected (e.g. A•Healing / B•Attack / C•Effect
# for preset 1).  The user shipped six full-menu screenshots showing
# each preset's text; we just need the rectangular region with the three
# text lines, which the renderer can blit over the recolored canvas
# whenever SpellOrder != 1.
MAGORDER_BBOX = (110, 56, 200, 100)  # x_lo, y_lo, x_hi, y_hi (inclusive_lo, exclusive_hi)


def build_magorder() -> dict | None:
    src = SHOTS_DIR / "MagOrder"
    if not src.exists():
        return None
    out_dir = ASSETS_DIR / "magorder"
    out_dir.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = MAGORDER_BBOX
    presets = []
    for n in range(1, 7):
        p = src / f"MagOrder_{n}.png"
        if not p.exists():
            continue
        img = _load(p)
        crop = img[y0:y1, x0:x1]
        _save(crop, out_dir / f"{n}.png")
        presets.append(n)
    return {"presets": presets, "bbox": [x0, y0, x1, y1]}


def _build_default_a_cursor_mask() -> np.ndarray | None:
    """Derive the canonical defaultA cursor mask from W5.

    W5's wallpaper happens to give the cleanest CC around the cursor
    sprite, so we detect there and reuse the resulting mask for every
    window.  Then:

      * Trim 4 px off the top: dilation pulls the menu's bright top
        frame (y≈38–39) into the mask and scrapes the border.
      * Cap the right edge at x≤111: "Active" starts at x=112 and the
        raw CC + 2-px right dilation overlaps the leading 'A'.
      * Add a 3-px shadow patch at (y=53..55, x=109..111): the FF6
        cursor sprite drops a darker shadow at its lower-right tip
        that the bright-pixel CC doesn't reach, so without this an
        obvious black smudge survives below-left of the 'A'.
    """
    ref = SHOTS_DIR / "W5" / "W5_defaultA.png"
    if not ref.exists():
        return None
    mask = _find_cursor_mask(_load(ref), y_lo=38, y_hi=58)
    if not mask.any():
        return None
    top = np.where(mask)[0].min()
    mask[: top + 4, :] = False
    mask[:, 112:] = False
    mask[53:56, 109:112] = True
    return mask


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"windows": {}}
    default_a_mask = _build_default_a_cursor_mask()
    # Build W1 first (Font-selected capture) to harvest a reference Color
    # row strip that the orientation-fix can apply to W4/W7/W8.
    color_row_ref: np.ndarray | None = None
    for i in [1] + list(range(2, 9)):
        info = build_window(i,
                            default_a_cursor_mask=default_a_mask,
                            color_row_reference=color_row_ref)
        if info is not None:
            manifest["windows"][str(i)] = info
            print(f"built W{i}: {info}")
        if i == 1:
            w1_baseline = _load(ASSETS_DIR / "W1" / "baseline.png")
            color_row_ref = w1_baseline[COLOR_ROW_Y_LO:COLOR_ROW_Y_HI].copy()
    mag = build_magorder()
    if mag is not None:
        manifest["magOrder"] = mag
        print(f"built magOrder: {mag}")
    out = ASSETS_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
