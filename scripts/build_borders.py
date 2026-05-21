"""Build the hand-curated border presets for the web designer.

The custom-window designer asks the user to upload a 32x32 texture plus
pick a "border" -- a 32x24 strip of frame pieces (corner / edge / gauge
marker) that goes underneath the texture in the final 32x56 source sheet.

This script generates that border preset set by extracting the bottom
4x3 tile region from each chosen vanilla window's source sheet and
preserving its slot indices verbatim:

  - vanilla index 0      -> output index 0  (transparent)
  - vanilla slot 1       -> output slot 1
  - vanilla slot 7       -> output slot 7

The designer's texture quantizer sorts the user's 7 chosen colours by
luminosity into slots 1..7 (slot 1 lightest, slot 7 darkest), so a
border pixel marked "slot 7" automatically picks up the user texture's
darkest colour.

That works directly for windows whose vanilla artist already used
slot 7 as the dominant frame-interior colour (the big filled area
behind the gauge marker).  W1 is the prime example: vanilla slot 7
is dark blue and fills the rounded button's interior, so the button
face blends with the texture's dark edge without any remap.

But other artists used different conventions.  W8 fills the ornate
button's interior with slot 1 (pinkish peach -- the artist's
"highlight" slot, not the dark one).  Used verbatim, that lands on
the texture's lightest colour and makes the button stand out as a
bright stripe against a dark texture -- the opposite of blending.

To normalize, button-style presets (``button=True`` in
PRESET_SOURCES) get one extra step: find the dominant slot in the
border (the slot that fills the most pixels = the button face), and
SWAP it with slot 7.  All other slots stay where they are.  After
the swap the button face is always at slot 7 = texture's darkest =
matches the texture's edge.  For W1 the dominant is already slot 7
so the swap is a no-op; for W8 it exchanges slot 1 <-> slot 7.

Textured presets (W2/W4/W5/W6) skip the swap so their panel
patterns keep their natural shading.

Output: ``web/borders.js`` -- a non-module script that sets
``window.BORDER_PRESETS`` (matches the rest of ``web/main.js``).

Run as:
    python scripts/build_borders.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from config import window_graphics as wg


PRESET_SOURCES = [
    # key,         vanilla window, displayed name,    button-style?
    ('rounded',    1, 'Rounded (W1)',    True),
    ('bolted',     2, 'Bolted (W2)',     False),
    ('wood',       4, 'Wood (W4)',       False),
    ('parchment',  5, 'Parchment (W5)',  False),
    ('stone',      6, 'Stone (W6)',      False),
    ('ornate',     8, 'Ornate (W8)',     True),
]


def _load_gfx():
    raw = wg.parse_hex_dump(
        (REPO_ROOT / "romdata" / "ED0000_MenuWindowGraphics.txt").read_text())
    raw += [0] * (8 * wg.WINDOW_GRAPHICS_SIZE - len(raw))
    return raw


def _swap_dominant_with_slot7(pixels):
    """Swap the most-used non-zero slot with slot 7 in the whole grid."""
    counter = Counter(px for row in pixels for px in row if px != 0)
    if not counter:
        return pixels, None
    dominant = counter.most_common(1)[0][0]
    if dominant == 7:
        return pixels, dominant
    swap = {dominant: 7, 7: dominant}
    return [[swap.get(px, px) for px in row] for row in pixels], dominant


def extract_border(n, gfx_all, button_style=False):
    """Return the bottom 24 rows of window n's source sheet.

    Each pixel keeps its vanilla slot index (0 = transparent, 1..7 =
    palette slot) by default.  For ``button_style=True`` presets, the
    dominant slot (= the button face's colour) is swapped with slot 7
    so it always lands on the texture's darkest colour after the
    designer's light->dark quantization.
    """
    base = (n - 1) * wg.WINDOW_GRAPHICS_SIZE
    pixels = wg.decode_window_sheet(gfx_all[base : base + wg.WINDOW_GRAPHICS_SIZE])
    bottom = [row[:] for row in pixels[32:]]   # rows 32..55
    swapped_from = None
    if button_style:
        bottom, swapped_from = _swap_dominant_with_slot7(bottom)
    used = {px for row in bottom for px in row}
    return bottom, used, swapped_from


def main():
    gfx_all = _load_gfx()
    presets = {}
    for key, n, label, button in PRESET_SOURCES:
        grid, used, swap = extract_border(n, gfx_all, button_style=button)
        presets[key] = {'name': label, 'pixels': grid}
        note = ''
        if button and swap is not None:
            note = f' (button-style: swapped slot {swap} <-> 7)' if swap != 7 else ' (button-style: dominant already at slot 7)'
        print(f"  {key:8s} -> {label}  uses slots {sorted(used)}{note}")

    presets['plain'] = {
        'name': 'Plain (no border)',
        'pixels': [[0] * 32 for _ in range(24)],
    }

    out_path = REPO_ROOT / "web" / "borders.js"
    order = ['plain'] + [key for key, _, _, _ in PRESET_SOURCES]
    with out_path.open('w') as f:
        f.write('// Auto-generated by scripts/build_borders.py -- do not edit.\n')
        f.write('// 32x24 border presets, using vanilla slot indices verbatim:\n')
        f.write('//   0 = transparent, 1 = palette slot 1 (lightest by texture\n')
        f.write('//   quantizer convention), ..., 7 = palette slot 7 (darkest).\n')
        f.write('// The texture quantizer sorts the user\'s 7 chosen colours\n')
        f.write('// light->dark into slots 1..7, so a border pixel marked "slot 7"\n')
        f.write('// always picks up the texture\'s darkest colour and blends with\n')
        f.write('// the texture\'s edges/background.\n')
        f.write('// Each "pixels" field is a Uint8Array of 768 entries, row-major.\n\n')
        f.write('window.BORDER_PRESETS = {\n')
        for key in order:
            flat = [px for row in presets[key]['pixels'] for px in row]
            f.write(f'  {key}: {{\n')
            f.write(f'    name: {json.dumps(presets[key]["name"])},\n')
            f.write('    pixels: new Uint8Array([\n')
            for r in range(24):
                row = flat[r * 32 : (r + 1) * 32]
                f.write('      ' + ','.join(str(v) for v in row) + ',\n')
            f.write('    ]),\n')
            f.write('  },\n')
        f.write('};\n')
        f.write('window.BORDER_PRESETS_ORDER = ' + json.dumps(order) + ';\n')
    print(f"wrote {out_path}")


if __name__ == '__main__':
    main()
