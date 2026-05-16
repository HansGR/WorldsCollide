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
CURSOR_MAX_SIZE = 200


def _strip_cursor_ghosts(raw_images: list[np.ndarray | None],
                         baseline: np.ndarray) -> list[np.ndarray | None]:
    """Erase the menu cursor sprite from each slot-isolation screenshot.

    The cursor is the FF6 hand pointer drawn in the gutter just left of
    each value column.  An earlier "any small CC unique to one slot"
    heuristic worked for most artwork but trimmed shadows / gradient
    bands that are themselves small CCs unique to a slot — visible as
    softer-than-expected borders.  Restrict cleanup to the cursor's
    natural X gutter (90..116 in native pixels) where window borders
    don't live, so we only stomp on the cursor blob and nothing else.
    """
    if not any(im is not None for im in raw_images):
        return raw_images
    H, W, _ = baseline.shape
    out = [im.copy() if im is not None else None for im in raw_images]
    for n in range(len(raw_images)):
        im = raw_images[n]
        if im is None:
            continue
        diff = np.abs(im.astype(int) - baseline.astype(int)).max(-1)
        cand = (diff > 80)
        cand[:, :CURSOR_X_LO] = False
        cand[:, CURSOR_X_HI:] = False
        if not cand.any():
            continue
        visited = np.zeros_like(cand)
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
                if 0 < len(pts) <= CURSOR_MAX_SIZE:
                    for (py, px) in pts:
                        out[n][py, px] = baseline[py, px]
    return out


def build_window(window_index: int) -> dict | None:
    src = SHOTS_DIR / f"W{window_index}"
    baseline_path = src / f"W{window_index}_0.png"
    if not baseline_path.exists():
        return None

    out_dir = ASSETS_DIR / f"W{window_index}"
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline = _load(baseline_path)
    _save(baseline, out_dir / "baseline.png")

    raw_slots: list[np.ndarray | None] = []
    slot_indices: list[int] = []
    for n in range(1, 8):
        p = src / f"W{window_index}_{n}.png"
        if p.exists():
            raw_slots.append(_load(p))
            slot_indices.append(n)
        else:
            raw_slots.append(None)

    cleaned = _strip_cursor_ghosts(raw_slots, baseline)
    for n, im in zip(range(1, 8), cleaned):
        if im is not None:
            _save(im, out_dir / f"slot{n}.png")

    font_present = False
    font_path = src / f"W{window_index}_font.png"
    if font_path.exists():
        font_raw = _load(font_path)
        # Don't run cursor cleanup here — every text glyph is a small
        # bright CC and would be eaten.  The font screenshot has one
        # cursor ghost; we leave it in.
        _save(font_raw, out_dir / "font.png")
        font_present = True

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
