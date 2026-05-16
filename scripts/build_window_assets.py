"""Build web-UI assets from window-style isolation screenshots.

Per window style i, the screenshots/Wi/ folder is expected to contain:
  - Wi_0.png         all 7 slots set to [0,0,0]; font set to [0,0,0]
  - Wi_1.png ... Wi_7.png   only slot N is bright; everything else [0,0,0]
  - Wi_font.png      font color bright; all 7 slots [0,0,0]
  - Wi_defaultA.png, Wi_defaultB.png   reference shots with default palette

We extract:
  - baseline.png   = Wi_0.png (output when all slots are [0,0,0])
  - slot{N}.png    = clamp(Wi_N - Wi_0, 0, 255) per channel, N in 1..7
  - font.png       = clamp(Wi_font - Wi_0, 0, 255)

The web UI composites these as:
    output[p] = baseline[p] + sum_n slot{n}[p] * c_n / 31 + font[p] * c_font / 31
where c_n is the [0..31] BGR15 slot color (per channel).

This script writes the per-window assets into web/assets/W{i}/ and emits a
manifest.json so the UI can know which window styles have art available.
"""

from __future__ import annotations

import json
import os
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


def _strip_cursor_ghosts(deltas: list[np.ndarray]) -> list[np.ndarray]:
    """Heuristic: a pixel that is bright in only ONE slot's delta and is part
    of a small cluster (< ~64 pixels) is almost certainly the menu cursor in
    that slot's source screenshot — the cursor moves between screenshots while
    the actual window border / fill pixels light up in adjacent slots too.

    We zero out such pixels so the recoloring math doesn't keep ghost cursors.
    """
    if not deltas:
        return deltas
    H, W, _ = deltas[0].shape
    intensities = np.stack([d.max(-1) for d in deltas])
    BRIGHT = 80
    bright = intensities > BRIGHT
    counts = bright.sum(0)  # how many slots light up each pixel
    out = [d.copy() for d in deltas]
    for n, d in enumerate(out):
        unique_mask = bright[n] & (counts == 1)
        if not unique_mask.any():
            continue
        # Connected components on `unique_mask`; tiny components (cursor-sized)
        # get zeroed out.  Avoid scipy dep — use a basic flood fill.
        visited = np.zeros_like(unique_mask)
        for y0 in range(H):
            for x0 in range(W):
                if not unique_mask[y0, x0] or visited[y0, x0]:
                    continue
                stack = [(y0, x0)]
                pts = []
                while stack:
                    y, x = stack.pop()
                    if y < 0 or y >= H or x < 0 or x >= W: continue
                    if visited[y, x] or not unique_mask[y, x]: continue
                    visited[y, x] = True
                    pts.append((y, x))
                    stack.extend(((y+1,x),(y-1,x),(y,x+1),(y,x-1)))
                # Cursors are localized hand sprites (~100-160 px including the
                # arrow body).  Window borders are LONG connected strips
                # (hundreds of pixels along an edge).  Strip only the small
                # blobs.
                if 0 < len(pts) <= 200:
                    for (py, px) in pts:
                        d[py, px] = 0
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

    slot_indices = []
    raw_deltas = []
    for n in range(1, 8):
        p = src / f"W{window_index}_{n}.png"
        if not p.exists():
            raw_deltas.append(None)
            continue
        img = _load(p)
        delta = np.clip(img.astype(int) - baseline.astype(int), 0, 255).astype(np.uint8)
        raw_deltas.append(delta)
        slot_indices.append(n)

    # Strip cursor ghosts using cross-slot agreement.
    nonempty = [d for d in raw_deltas if d is not None]
    cleaned = _strip_cursor_ghosts(nonempty)
    ci = 0
    for n in range(1, 8):
        if raw_deltas[n - 1] is None:
            continue
        _save(cleaned[ci], out_dir / f"slot{n}.png")
        ci += 1
    slot_present = slot_indices

    font_path = src / f"W{window_index}_font.png"
    font_present = False
    if font_path.exists():
        img = _load(font_path)
        delta = np.clip(img.astype(int) - baseline.astype(int), 0, 255)
        _save(delta, out_dir / "font.png")
        font_present = True

    for tag in ("A", "B"):
        ref = src / f"W{window_index}_default{tag}.png"
        if ref.exists():
            _save(_load(ref), out_dir / f"default{tag}.png")

    return {
        "window": window_index,
        "slots": slot_present,
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
