# FF6WC Config Builder — development archive

A scratch log of how the `web/` config builder grew, in roughly the order
things landed.  Each entry pairs a goal with the trick used to get it
working, so future tweaks (or a future port to a different FF6 menu) can
pick up the underlying ideas rather than reverse-engineering them from
the code.

## Top of mind

`ff6_config.py` turns a CLI flagstring into a patched ROM.  The web UI's
one job is to **let users build that flagstring without typing it** — by
clicking through a recolored copy of FF6's actual config menu.  Three
sub-problems came along for the ride:

1. **Recolor the SNES menu** in the browser using only flat PNG
   screenshots as input — no emulator, no palette in code.
2. **Make the menu feel interactive** — cursor navigation, value
   selection, sliders, page wrap — without re-implementing FF6's font
   from scratch.
3. **Match the live game closely enough** that the preview is trustworthy
   when picking colors.

## Repository layout

```
ff6_config.py                # the CLI tool the flagstring drives
config/                      # ROM-side encoding for that CLI
scripts/build_window_assets.py
                             # one-shot preprocessor: screenshots → web assets
screenshots/W{1..8}/         # raw isolation captures for each window style
screenshots/W1/partials/     # single-channel + intermediate-value probes
screenshots/MagOrder/        # spell-order text variants
web/                         # the static-site builder
  index.html · style.css · main.js
  assets/manifest.json
  assets/W{1..8}/baseline.png · slot{1..7}.png · font.png
                              · default{A,B}.png · correction.json
                              · baselineA.png · slot{1..7}A.png
                              · fontA.png · correctionA.json
  assets/magorder/{1..6}.png
```

## Window recolor pipeline

### The screenshot set

Each window style ships eight screenshots:

* `W{i}_0.png` — baseline (all seven slots at `[0, 0, 0]`).
* `W{i}_{n}.png` for `n ∈ 1..7` — only slot `n` is bright, rest black.
* `W{i}_font.png` — font color bright, all slots black.

Plus two reference shots with the default palette: `W{i}_defaultA.png`
(Page A) and `W{i}_defaultB.png` (Page B).

Page A ships a parallel set under `screenshots/W{i}A/` (`W{i}A_0.png`,
`W{i}A_{n}.png`, `W{i}A_font.png`) using the same conventions, so the
preview can recolor Page A through the same math.  The captures park
the cursor on Bat.Mode → Active, identical to the existing defaultA
reference shots — so the build pipeline reuses the W5_defaultA-derived
cursor mask and the `+128` source offset for cleanup, no new
per-window detection needed.  Page A has none of Page B's special
cases (no slot-selection arrow, no Color-row orientation flip, no
slider bars), so its `build_window_page_a()` reduces to cursor cleanup
→ save → y-correction fit against `W{i}_defaultA.png`.  Outputs land
next to Page B's under the same window dir as `baselineA.png` /
`slot{n}A.png` / `fontA.png` / `correctionA.json`.

### The math

Every output pixel ends up as a linear combination of the baseline and
the seven "slot-bright" frames plus the font-bright frame, with weights
equal to the chosen palette values divided by 31:

```
output[p] =  baseline[p] · (1 − Σ c_n/31 − c_font/31)
           + Σ raw_n[p] · c_n / 31
           + raw_font[p] · c_font / 31
```

This is just `baseline + Σ (raw_n − baseline) · c_n/31 + (font − baseline) · c_font/31`
rewritten to avoid storing signed deltas.

Two non-obvious bits:

* **Storing raw screenshots, not pre-subtracted deltas** — the first cut
  stored `clip(raw_n − baseline, 0, 255)` to save space, but clipping
  the negative range destroyed the pixels where turning a slot ON makes
  the menu *darker* (the wallpaper getting averaged into a new
  contributor).  W3's "lightning bolt" wallpaper completely disappeared
  until that was fixed.  See `scripts/build_window_assets.py` and the
  comment on `recolor()` in `main.js`.
* **Float accumulator** — JS `ImageData.data` is a `Uint8ClampedArray`
  which clamps on every write, so the signed intermediates would still
  be lost mid-sum.  `recolor()` accumulates into a `Float32Array` and
  only commits to `out.data` at the end.

### Linearity check

`screenshots/W1/partials/W1_1_[...]` are four extra captures with slot 1
at `[31,0,0]`, `[0,31,0]`, `[0,0,31]`, and `[15,15,15]`.  Two things
verified:

* **Channel additivity** — `W1_R + W1_G + W1_B − 2·W1_0 ≈ W1_RGB` with
  L1 mean error 1.48/255, so the R/G/B contributions are independent.
* **Linearity at v=15** — `(W1[15,15,15] − W1_0) / (W1[31,31,31] − W1_0)`
  comes out to 0.502 ± noise at every bright pixel, matching v/31.

No gamma curve needed.

### Per-window y-correction

The pure linear model leaves a residual that *looks* like a smooth
vertical gradient on the live preview.  It's the SNES's per-scanline
color-math step against the wallpaper BG layer, which can't be folded
into `baseline + Σ delta·c` directly.

`build_window_assets.py` fits one residual per window: for each row `y`
and channel `c`, the average `real_default[y, x, c] − synth_default[y, x, c]`
across `x`, then fits a single `slope·y + intercept` over the active
menu region.  Stored as `correction.json` (a 224×3 float array per
window) and added to every pixel after the recolor sum.

Two-line linear-fit chosen over per-row mean residual because the per-row
version inherited the source screenshot's row-to-row dithering noise and
showed as a faint horizontal banding near the bottom of the preview.

### Cursor masking

Every isolation screenshot has the menu cursor (the hand sprite) parked
in one spot.  Pre-asking the user to *consistently* park it (any spot
that's inside the menu's 32-px-tiling wallpaper) makes the deletion
trivial:

1. Locate the cursor blob — biggest bright connected component in the
   x ∈ [90, 116] gutter.
2. Dilate the mask asymmetrically: `3 left / 2 right / 3 up / 6 down` so
   the cursor's drop shadow gets caught without further clipping the
   menu text on the right.
3. Inpaint by copying each masked pixel from `(x − 32, y)`.  The
   wallpaper tiles every 32 px horizontally, so the source is the
   "underlying" wallpaper pixel the cursor was hiding.

Three follow-up refinements landed once the menu was readable enough to
spot residual artifacts:

* **Right-edge cap + shadow patch on the baseline mask** (Page B
  cleanup).  The baseline cursor is parked on the B-slider row, so the
  raw CC + 2-px right dilation reaches `x=112` — the leading column of
  the "B" glyph.  Cap the mask at `x ≤ 111` and stamp a 3×3 patch over
  the drop-shadow tip (`y=197..199, x=109..111`) that the bright-pixel
  CC misses.
* **Unified defaultA mask from W5.**  The Page A reference shots
  (`W{i}_defaultA.png`) carry a *different* cursor parked on
  BatMode → Active.  Each window's CC was picking up different gutter
  false-positives (menu top frame, slot 1's outline, etc.), so masks
  varied per window.  Derive a single mask from W5 (the cleanest CC),
  trim 4 px off the top, cap at `x ≤ 111`, and stamp a shadow patch
  at `(y=53..55, x=109..111)`.  Apply uniformly to every window's
  `defaultA.png`.  Inpaint with a `+128 px` offset so the source lands
  past "Wait" on the same row — the standard `−32` would copy from
  the "Bat.Mode" label text.
* **`_apply_cursor_mask(offset=…)`.**  The cursor copy offset is no
  longer hard-coded.  Callers pass a multiple of 32; if the source
  would fall off the canvas edge the helper steps it by ±32 until in
  range.

### Slot-selection arrow

In-game, FF6 draws a small black up-arrow under the selected slot
colour swatch on the Color row.  Whichever slot the user happened to
have selected during capture leaves that arrow baked into every
isolation shot for that window.  Each window has the arrow at a
different x, but always in the 8-pixel strip immediately under the
slot swatches.

Erase the entire strip `y=148..155, x=176..240` in baseline / slot /
font and inpaint from 96 px to the left (3 wallpaper tiles).  The same
y band has no menu chrome anywhere across the slot range, so the
inpaint stitches even W3's lightning and W8's moogle clouds without a
seam.

## Page-by-page interactive layer

### Page A (toggles)

`PAGE_A_OPTIONS` is the source of truth for cursor positions and
selectable values.  Each row is

```js
{ key: 'BatMode', y: 44, values: [['active', 112], ['wait', 176]] }
```

with `y` in native pixels (canvas is 256×224, displayed 2x).  Cursor
draws at `(x − 10, y + 1)` so the sprite's tip lands in the gutter
just left of the value's first glyph.

Page A used to be rendered by blitting the static `defaultA.png` and
showing a "(live recolor preview is on Page B)" hint bar — the menu
chrome on Page A is tinted by the slot palette via SNES color math,
which the linear recolor model can't fake from Page B's isolations
alone (the chrome geometry differs between pages).  Once the parallel
`W{i}A_*` capture set landed, `recolor()` switched to picking
`baselineDataA` / `slotsDataA` / `fontDataA` / `correctionA` when
`state.page === 'A'`; the same `highlightValueText` / `drawCursorOverlay`
overlays run on top of the recolored Page A as they do for Page B.
The defaultA blit fallback survives in `render()` for windows that
ship without Page A isolations (none currently).

### Page B (color picker)

`PAGE_B_OPTIONS` has rows for `SpellOrder`, `WindowStyle`, the
`Color` meta-row (font / slot 1..7), and `R`/`G`/`B` sliders.  The
Color row's `values` entry takes an optional third element for a `y`
override, since the seven slot swatches FF6 draws sit one line below
the Font/Window text:

```js
{ key: 'Color', y: 124, kind: 'color', values: [
    ['font', 112, 124],
    ['slot1', 180, 139], ['slot2', 188, 139], …
  ]
}
```

### Vertical wrap

Pressing Down from the last row of one page lands on row 0 of the
other (and Up wraps the same way).  Done in `move()`'s vertical
clause; matches FF6's own A↔B traversal.

### R / G / B sliders

`kind: 'slider'` rows have no `values` array — instead they carry a
`channel` (0/1/2) and a fixed `cursorX`.  Left/Right on a slider row
calls `adjustChannel(ch, ±1)`, which mutates whichever target the
Color row picked (font or `windows[i][slot − 1]`), clamps to [0, 31],
then triggers a full render + side-panel sync + flagstring update.

The slider bar and value text are repainted on every render:

* `redrawNumber()` — tile-copies a 18×9 patch of clean menu fill from
  `x = 80` over the old `"31"` and stamps fresh digit masks (right-
  aligned at `tens=128, ones=137`).  Numbers paint in the font color
  scaled to 8-bit so they tint with whatever colour the menu is using
  for its labels.
* `redrawBarFill()` — overpaints the 3-row interior of the bar with a
  font-color stripe of width `round(value · 62 / 31)`.  The empty
  remainder is intentionally left untouched: the build script erases
  the bar interior out of every baseline / slot / font screenshot
  (4-tile left inpaint), so the recolored composite already shows the
  wallpaper under the bar.  Painting only the filled portion lets the
  wallpaper texture read as "transparent" through the empty section
  instead of a solid SNES-rendered colour that tints with the slot
  palette (which is what the raw screenshots' bar interiors did,
  noticeable as a dark block under the dynamic fill on busy wallpapers
  like W3).

The bar's outline (rounded capsule, top/bottom edges, inner border
rows) is never touched — only the value-dependent interior changes.
The y-correction is fit *before* the bar mask runs so the per-row mean
residual isn't skewed by 62 px of bar-vs-wallpaper diff at bar rows.

### Mag.Order text overlay

The three lines under the spell-order picker (`A• Healing`, `B•
Attack`, `C• Effect` and the other five orderings) change per preset.
The user shipped one full-menu screenshot per preset, captured under
the same recolor state as W1's `defaultB`.

Two-pass overlay:

1. **Erase** by sequential L-to-R copy with offset −32 across the
   90 × 44 text rectangle.  The 32 px immediately left of the rectangle
   is clean wallpaper, and because we write left-to-right *in place*,
   the second 32-px column reads freshly-cleared pixels from the first
   one and so on — the whole rectangle gets tiled with clean wallpaper.
2. **Stamp** the chosen preset's glyphs.  Three passes:
   1. Procedural drop shadow at `(+1, +1)` of every pixel with
      `max channel > 70`.
   2. Dark-pixel pass: any source pixel with `max channel < 10` stamps
      pure black.  This pass exists for the Attack row's filled black
      ball icon — its outline is pure black and was being filtered out
      by the brightness gate, leaving only the dim grey interior; the
      procedural shadow only covers the down-right side of bright
      pixels, not the full ring.  Letter outlines coincide with the
      procedural shadow and are unaffected.
   3. Bright-pixel stamp: any source pixel with `max channel > 70`
      copies its own colour, overpainting any shadow that lands on an
      adjacent glyph cell.

## Text-highlight masks

FF6 dims the *unselected* value on every binary option (the selected
one stays white; the others go grey).  `highlightValueText()` walks each
visible row and rescales pixel brightness so the currently-selected
value's peak channel becomes 255 and every other value's peak becomes
128 — preserving per-pixel hue (so a window-tinted glyph stays the same
colour, just brighter or darker).

Three dispatch arms:

* **Digits** — `DIGIT_MASKS[0..9]`, 10 rows × 8 cols each, packed as
  bytes per row.  Indices 1–8 were extracted from the Window row of
  `W1_defaultB.png`; 0 and 9 were hand-constructed in the same style
  (closed oval / mirror of 6).  Used by BatSpeed / MsgSpeed /
  SpellOrder / WindowStyle and by the slider value text.
* **Words** — `WORD_MASKS`, 13 entries, packed as 32-bit ints per row
  (with `ipr ≥ 2` for words wider than 32 px like "optimum").  The
  twelve Page A binary-option words were extracted from
  `W1_defaultA.png` (which has the default values bright) and
  `W1_defaultA_opposite.png` (the rest — six rows toggled to the
  non-default value, captured deliberately so we have a *bright* copy
  of every word).  The `font` mask came from Page B's Color row, and
  the existing `window` mask doubles for both the Cmd.Set row and the
  Color row's "Window" label.
* **Color row special case** — the Color row has two text labels
  (`Font`, `Window`) whose highlighted state tracks `state.editing`
  rather than a discrete value in `values[]`, so it gets a dedicated
  branch in `highlightValueText` that stamps both labels at fixed
  positions.

Originally the highlight was a per-pixel rescale that preserved hue:
`scale = target / max(r,g,b)`, where `target` was 255 for the selected
option and 128 for the others.  This worked under the default white
font palette but fell apart once the font colour was edited — a purple
font (`[31,0,31]`) left a baked-in green channel of 0 in the recolored
composite, and the y-correction's per-channel residual then nudged it
back up a few units.  Rescaling that pixel to bright passed through
the small green and read as near-white; rescaling the dim version
preserved (R≈G=0, B≈) and read as dark purple, not grey.

Replace the rescale with a flat colour stamp on mask-driven paths:

* **Bright** = `state.font * 255/31` exactly.  Whatever colour the
  user picked is the colour the selected option shows in.
* **Dim**    = `[128, 128, 128]` neutral grey, regardless of font.

The fallback bounding-box path still uses the hue-preserving rescaler
(`adjustPixel`, with the `max > TEXT_THRESHOLD` gate) because it has
no mask to distinguish glyph strokes from wallpaper.

### Color-row capture orientation

`W4_0.png`, `W7_0.png`, and `W8_0.png` were captured with the *Window*
sub-label selected on the Color row, while every other window was
captured with Font selected.  That asymmetry leaks into the recolored
composite as a dim "Window" label with no way to brighten it.

The strip `y=124..132` in baseline.png is otherwise uniform black
wallpaper across every window — only the menu labels themselves carry
signal.  So the build script processes W1 first, harvests its strip
as a reference, and then for any subsequent window whose Window
brightness exceeds Font brightness by > 30, it wholesale-copies the
W1 strip into the affected baseline.  Wallpaper texture elsewhere is
untouched.

## Cache-busting

The static-server cache turned out to be aggressive enough that
redeploying a new `assets/manifest.json` (the one that grew the
`magOrder` key) was invisible to repeat visitors — the new
`loadMagOrderOverlays` found `manifest.magOrder` undefined and bailed.

Fix: pin `const CB = '?v=' + Date.now()` once at boot and append it to
every asset fetch — `manifest.json`, every per-window `correction.json`,
every baseline / slot / font / default / magorder PNG, and `main.js`
itself (via an inline script tag in `index.html`).  Single timestamp
per page load so we don't churn the cache on every individual call.

## Background preload

`loadWindowAssets(n)` is lazy — the first switch to a never-seen
window would briefly flash the "No preview" placeholder while the
fetches resolved.  After the active window's assets are loaded at
boot, `init()` fires `Promise.all` over every other window in the
manifest and lets it run in the background.  By the time the user
cycles styles, the assets are already cached.

## Side panel (right column)

Mirrors the canvas so users who'd rather not arrow-key everything can
still drive it:

* **Preview window style** dropdown — swaps which W1..W8 the recolor
  uses.
* **Wallpaper** dropdown — purely a flagstring affordance; FF6's
  wallpaper isn't part of the recolored preview.
* **Target** segmented control + slot dropdown — picks `font` or one
  of `slot 1..7`, kept in sync with the canvas Color row both ways.
* **R / G / B sliders** — the source of truth for the live value; the
  canvas slider bar mirrors the same number.
* **Reset this color / Reset everything to defaults**.
* **Flagstring** textarea + Copy button — only emits flags for values
  that *differ* from `config/config.py`'s defaults, so the output is
  minimal.

## Build and run

```sh
python3 scripts/build_window_assets.py        # only when screenshots change
python3 -m http.server --directory web 8000   # any static server works
```

Then visit <http://localhost:8000/>.  Cache-bust means a normal refresh
picks up any redeployed assets.

## Commit-by-commit timeline (branch: claude/ff6-web-ui-F1r8A)

| Commit  | What landed |
| ------- | ----------- |
| `482be87` | Initial scaffolding: index.html / main.js / style.css + first preprocessor + W1/W3 art + manifest. |
| `152f915` | Switched slot assets from positive-clipped deltas to raw screenshots + Float32 accumulator — W3's lightning showed up. |
| `95d0684` | Added W4/W5/W6; narrowed cursor cleanup to the [90, 116] x-gutter so it stopped eating shadow/gradient bands. |
| `e3f6315` | Replaced "reset cursor pixels to baseline" with horizontal linear interpolation between left/right anchors. |
| `d4e668e` | Added W7/W8 + linearity probe partials; switched cursor inpaint to the 32-px tile copy. |
| `31fa4c2` | Per-row residual correction (228×3 floats per window) + dilated cursor mask. |
| `52405f3` | Collapsed correction to a single least-squares line per channel so the gradient is smooth. |
| `886a469` | Fixed Page B cursor y-positions; added the Font / Window + slot picker in the side panel. |
| `2a415fb` | WindowStyle digit spacing 16, slot swatches at `175 + i·8`. |
| `d1adaf1` | Page A y shifts (BatMode-only kept), page-wrap, slot swatch x=180, first cut of value highlights. |
| `f7fd017` | Per-digit bitmap masks for numeric values; precise highlight without bounding rectangle. |
| `91e59cf` | Off-by-one shift on digit masks (mask row 0 is padding). |
| `6c6bd20` | Mag.Order text overlay (signed-delta approach). |
| `da3c83c` | Color slot swatches y+1; cache-bust `main.js`. |
| `5c5de4f` | Cache-bust *every* asset fetch (manifest.json, correction.json, all PNGs). |
| `0074cde` | Switched Mag.Order overlay from delta math to tile-erase + bright-pixel stamp — preset 1 ghosts gone. |
| `c7bbbd9` | Per-word bitmap masks for the twelve Page A binary options (using `W1_defaultA_opposite.png`). |
| `43c72cc` | Keyboard-driven R / G / B slider rows on Page B. |
| `7022f65` | Live R/G/B number + slider-fill repaint; cursor y −4 px on those rows; digit masks reindexed 0–9. |
| `c4393ce` | 1-px drop shadow on slider digits + Mag.Order text; Color row Font / Window highlight tracks state.editing. |

### Follow-up polish (branch: claude/fix-highlight-position-HnXqr)

| Commit  | What landed |
| ------- | ----------- |
| `7d7601f` | Shift Color row "Window" highlight 4 px left to align with text. |
| `8b50dbf` | Mask cursor sprite out of `defaultA` window screenshots; add `y_lo/y_hi` filter on `_find_cursor_mask` and a configurable copy offset on `_apply_cursor_mask`. |
| `58f9578` | Trim defaultA cursor mask 4 px on top and right so the menu border and the leading "A" of "Active" stop getting scraped. |
| `dc90489` | Reuse W5's cursor mask for every defaultA cleanup so wallpaper-dependent CC variance no longer leaks per-window artifacts. |
| `15002f3` | Cap defaultA mask at `x ≤ 111` and stamp a shadow patch at `(y=53..55, x=109..111)` — the cursor's drop shadow tip the bright-pixel CC misses. |
| `c654bae` | Apply the same `x ≤ 111` cap + shadow patch to the baseline cursor mask used by Page B, so the recolored composite stops clipping "B". |
| `0d74f91` | Move the B-row shadow patch up to `y=197..199` (the actual shadow location, not y=200+). |
| `e1d3b25` | Erase the in-game slot-selection arrow with a strip mask at `y=148..155, x=176..240`, inpainted from 96 px to the left. |
| `e2da90e` | Stamp source pixels with `max < 10` in the Mag.Order overlay so the Attack row's black ball outline survives the brightness gate. |
| `349a339` | Add `adjustGlyphPixel` (no brightness gate) for mask-driven highlights; the existing gate was silently skipping the dim "Window" label on W4/W7/W8. |
| `269d4a3` | Normalize Color-row orientation in W4/W7/W8 baselines: copy W1's `y=124..132` strip to undo the Window-selected capture state. |
| `9046025` | Preload every window's assets in the background after first paint so style switches never flash "No preview". |
| `e107c8c` | Replace hue-preserving rescale with flat colour stamp on mask-driven highlights: bright = current font colour exactly, dim = neutral grey, so purple/etc. fonts read correctly. |
