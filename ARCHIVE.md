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
  font-color stripe of width `round(value · 62 / 31)` followed by the
  bar's empty-track dark gray for the remainder.  The dark gray is
  sampled per render from the bar's inner-border row so it tracks the
  y-correction automatically.

The bar's outline (rounded capsule, top/bottom edges, inner border
rows) is never touched — only the value-dependent interior changes.

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
2. **Stamp** the chosen preset's glyphs.  For each source pixel whose
   max channel > 70, first paint a 1-px black drop shadow at `(+1, +1)`
   and then paint the source pixel itself.  The shadow gets overpainted
   wherever a neighbouring glyph cell lands on top, matching FF6's
   natural drop shadow on every menu glyph.

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
