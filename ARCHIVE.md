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
      stamps the live font palette scaled by source brightness
      (`font_8bit · md[i] / 255` per channel), overpainting any shadow
      that lands on an adjacent glyph cell.  The crops were captured
      under W1's default (white) font, so the source is grayscale and
      the multiply collapses to a flat font-colour tint at the source's
      brightness — bright letter strokes get the full font colour, the
      dim bullet outlines stay proportionally dimmer.  Previously the
      stamp just copied `md[i]` unchanged, which left the Mag.Order
      text frozen at white even when the rest of the menu's text
      recoloured.

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

## Window graphics encoding (ROM $ED/0000 – $ED/1BFF)

Aside from the palette table at `$ED/1C00`, each of the eight FF6 menu
window styles also ships its own 32×56-pixel source-graphics sheet at
`$ED/0000 + (N − 1) × 896`.  The ff6hacking wiki labels them "Menu
Window Graphics (8 items, 896 bytes each)" without specifying the
format; the actual encoding is **standard SNES 4bpp**, **28 tiles per
window** laid out as a **4-wide × 7-tall** image.

### Per-window layout

* **Graphics**: 28 tiles × 32 bytes = 896 bytes at file offset
  `0x2D0000 + (N − 1) × 0x380`.  Tile order is left-to-right,
  top-to-bottom of a 4×7 grid → final image is 32 px wide, 56 px tall.
* **Palette**: 16 BGR15 colors × 2 bytes = 32 bytes at file offset
  `0x2D1C00 + (N − 1) × 0x20`.  Color 0 is always `(0,0,0)` (transparent
  against the wallpaper).  Colors 1..7 are the seven user-editable slots
  shown in the config menu.  Colors 8..15 are filler — every shipped
  ROM stores `0x3800` there and the graphics never reference them.

The visible content of each sheet:

* Top six tile-rows (32×48 px) — the **interior fill / texture** the
  engine tiles across the window background (the wood / water / stone
  patterns in W2..W8; a near-solid gradient in W1).
* Bottom tile-row (32×8 px) — the **frame pieces**: rounded corner,
  edge, and a small "I/II" gauge marker.

### Tile encoding (standard SNES 4bpp)

Each 32-byte tile is two 2bpp planar tiles concatenated:

```
bytes  0..15 : 8 rows × (bp0_byte, bp1_byte)   -- low planes
bytes 16..31 : 8 rows × (bp2_byte, bp3_byte)   -- high planes
```

Per pixel `x` in row `r` (MSB-first within each byte):

```
color = bp0_bit(7-x) | (bp1_bit(7-x) << 1) | (bp2_bit(7-x) << 2) | (bp3_bit(7-x) << 3)
```

So a "solid color 7" tile is `bp0=bp1=bp2=0xFF`, `bp3=0x00` repeated 8
times — which is exactly the pattern of every "fill" tile in W1's
sheet.  Confirmed by round-tripping `romdata/ED0000_MenuWindowGraphics.txt`
through `decode_window_sheet` → `encode_window_sheet` (bit-perfect) and
by visual inspection: under any other tile size / arrangement, W1's
"II" gauge tile reads as garbled vertical stripes.

### Constraints for custom graphics

* **Image dimensions**: exactly 32 × 56 pixels.
* **Color count**: at most 7 distinct foreground colors (palette
  indices 1..7) plus the transparent index 0.
* **Color resolution**: each channel quantizes to BGR15 (5 bits =
  32 levels), so RGB888 must be divided by 8 before packing.
* **ROM payload**: 896 bytes of graphics + 32 bytes of palette per
  window, written with `rom.set_bytes` exactly like the existing
  palette-only patch.

`config/window_graphics.py` provides the encode/decode pair plus
`get_/set_window_graphics` and `get_/set_window_palette_full` for the
two-region ROM IO.  `scripts/window_graphics.py` is a thin CLI: extract
the eight stock sheets as indexed PNGs for visual reference, or pack a
hand-edited PNG back into a `(896, 32)` byte pair.

## Custom window image designer (web)

The web UI gained a "Custom window image" section below the main
config-menu preview.  It lets a user upload a 32×32 image, pick a
border treatment, paint individual pixel tweaks, then download a
928-byte binary that the CLI applies via:

```
python ff6_config.py -i rom.smc --window-image N:file.bin
```

### Three-file split

* `web/encoder.js` — pure SNES 4bpp encoder + median-cut quantizer.
  No DOM access; ships under a UMD wrapper so both the browser and the
  Node smoke test in `tests/test_encoder_js.js` can `require` /
  `script src=` it.  This is the single source of truth that the
  Python decoder in `config/window_graphics.py` is round-tripped
  against in CI.
* `web/borders.js` — auto-generated by `scripts/build_borders.py`.
  Six hand-curated border presets extracted from the bottom 4×3 tile
  region of vanilla W1 / W2 / W4 / W5 / W6 / W8, plus an all-transparent
  `plain` preset.  Each border pixel keeps its **vanilla slot index
  verbatim** (0 = transparent, 1..7 = palette slot).  The texture
  quantizer sorts user colours light→dark into slots 1..7 with the
  same convention, so a border pixel marked "slot 7" automatically
  picks up the user texture's darkest colour — which is also the
  texture's bottom-edge colour, so the frame's interior blends with
  the texture sitting above it instead of standing out as a bright
  highlight.

  Two earlier attempts at this mapping fell short:

  * **First cut: collapse to {1, 7}.**  Every vanilla pixel was
    bucketed into "highlight" or "outline" based on luminosity
    threshold.  Textured frames (W2 bolts, W4 wood grain, W6 stone)
    read as noise because all their mid-tone shading was thrown
    away.
  * **Second cut: rank by numerical luminosity.**  Each window's
    vanilla slots were re-sorted by their computed luminosity
    before assigning output indices, so "lightest vanilla →
    output 1" regardless of the artist's slot numbering.  That
    works for most palettes but mis-handles W1: vanilla slot 7 =
    `[5, 5, 16]` is dark blue with a small blue boost, which the
    `0.299/0.587/0.114` luminance formula scores *brighter* than
    slot 5 = `[5, 6, 6]` (almost grey) by 0.55 units.  W1's
    button-face pixels (vanilla slot 7) ended up at output rank 6
    instead of 7, so the texture's 2nd-darkest colour showed up on
    the button face instead of the darkest one.

  Using vanilla slot indices verbatim trusts the artist's intent
  ("slot 7 = the dark one") and produces correct results for W1
  with no remap.  But it still fails for **button-style** frames
  whose artist used a non-slot-7 slot for the button face: W8 fills
  the ornate button with slot 1 (pinkish peach -- the artist's
  "highlight" slot).  Used verbatim, that lands on the texture's
  lightest colour and makes the button stand out as a bright
  stripe.

  Final step: button-style presets (W1 + W8) get **one auto-swap**.
  The script finds the most-used non-zero slot in the border
  pixels (= the button face) and swaps it with slot 7.  For W1
  the dominant is already slot 7, so the swap is a no-op.  For
  W8 it exchanges slot 1 ↔ slot 7, putting the button face at
  the texture's darkest colour and the outline at the texture's
  lightest.  Textured presets (W2/W4/W5/W6) skip the swap so
  their wood/stone/parchment/metal patterns keep their natural
  shading.
* `web/designer.js` — DOM + interaction.  State is the 32×56 sheet of
  palette indices + an 8-slot palette (index 0 = transparent, slots
  1..7 = user colors).  Texture upload runs cover-fit center-crop
  into a 32×32 ImageData, then through `WGEncoder.medianCut` (7
  buckets) + `WGEncoder.sortByLuminosity` + `rgb8_to_bgr5`.  Border
  upload runs a brightness-thresholded 3-bucket pass into
  `{transparent, highlight=1, outline=7}` so it doesn't compete with
  the texture for palette slots.

### Pipeline at a glance

```
Upload (32×32) -> ImageData -> medianCut(7) -> sortByLuminosity ->
  rgb8_to_bgr5 -> slots[1..7] + texture indices
                                          \
                                           --> ds.pixels[top 32 rows]
Border preset / upload                          ds.pixels[bottom 24 rows]
                                          /
                                    composite 32×56
                                          |
                                    paint / palette edit
                                          |
                                    encodeSheet -> 896 bytes
                                    encodePalette(8 + 8 filler) -> 32 bytes
                                                                 \
                                                                  -> .bin (928 B)
```

### Script load order

`index.html` injects the four scripts dynamically (cache-bust query
string), which makes them default to `async=true` and execute out of
order — `designer.js` would race ahead of `borders.js` and find the
preset dropdown empty.  Setting `s.async = false` on each tag forces
in-order execution, matching the array `[borders.js, encoder.js,
main.js, designer.js]`.

### Test surface

* `tests/test_window_graphics.py` — Python encode/decode + ROM IO.
* `tests/test_config.py` — extended with `--window-image` CLI
  parsing + `_apply_window_image` ROM writes.
* `tests/test_encoder_js.js` — Node-loadable smoke test of
  `web/encoder.js` against the shipped `romdata/` dump: encodes every
  stock window from decoded indices and checks the bytes match.

## Configurator ↔ designer integration

The designer started as a standalone panel that produced a single
928-byte `.bin` for one window; later it grew to per-window state
that shares the configurator's window-style selection and palette,
producing a single JSON config bundle.  Key pieces:

### Shared state via `window.ff6c`

`main.js` exposes its `state` object on `window.ff6c` and dispatches
a single `ff6c:stateChange` `CustomEvent` after every mutation
(window-style change, palette slider, reset-color, reset-all,
designer-initiated palette bulk-set, …).  The designer listens to
that event:

* If `SHARED.WindowStyle` moved, call `loadWindow(newN)` to swap in
  that window's pixels (from `customGraphics[N]` if it's been
  edited; otherwise from `window.VANILLA_GRAPHICS[N]`).
* Otherwise just re-render — the palette swatches read from
  `SHARED.windows[N]` directly so they pick up the new colour.
* If `detail.kind === 'reset-all'`, drop every entry in
  `customGraphics` so the configurator's "Reset everything"
  cascades to the designer too.

The reverse direction goes through two helpers on `window.ff6c`:

* `setPaletteBulk(n, palette7)` — used by the designer when a fresh
  texture upload produces 7 new colours, so the configurator's
  preview + flagstring + side panel all update in one render
  instead of 7.
* `refresh()` — called by the designer after non-palette edits
  (paint, border switch) so the menu preview re-runs its overlay
  pass with the new pixel data.

### Per-window pixel state

`ds.customGraphics` is keyed by window number (1..8); only windows
the user actually touched have entries.  `loadWindow(n)` snapshots
the current edit (`snapshotCurrent()`) before swapping in the new
window's pixels, so cycling W3 → W5 → W3 round-trips losslessly.
"Revert this window to default" deletes the entry, restores the
vanilla palette via `setPaletteBulk(n, VANILLA_GRAPHICS[n].palette[1..8])`,
and reloads the vanilla pixels.

### Vanilla baseline

`scripts/build_vanilla_graphics.py` pre-decodes the shipped
`romdata/ED0000_*.txt` + `ED1C00_*.txt` into
`web/vanilla_graphics.js` — `window.VANILLA_GRAPHICS[1..8] = {pixels:
Uint8Array(32*56), palette: [[R,G,B] × 8]}`.  Doing this at build
time means the web UI doesn't need to fetch + parse the romdata
files at page load, and it bakes in the same encoding the round-trip
test suite verifies.

### Menu-preview overlay

`overlayCustomGraphics()` runs as a post-pass on the configurator's
`recolor()` output, swapping the user's custom design into the
menu's window chrome with engine-faithful tile placement.

The first cut just tiled the custom 32 × 56 sheet across the chrome
region with period (32, 56) — interior textures reproduced fine but
frame tiles (corners, gauge marker) landed at every 56-pixel
y-boundary instead of just along the window's edges.  Replaced with
a reverse-engineered tilemap.

**Tilemap derivation** (`scripts/build_window_tilemap.py`):

1. Pick a "reference" window with distinct interior tiles (W3, the
   water pattern — W1's solid-color interior tiles produce ambiguous
   matches because tile 0 and tile 2 are the same pattern).
2. Compute the per-pixel slot-index map from W3's slot screenshots
   (`argmax_K |slot[K] - baseline|` thresholded at > 8 / 255).
3. Find the engine's tile-grid offset by sweeping `(x_off, y_off)` and
   maximizing the per-tile pattern match.  The right answer is
   `(0, 7)` — the FF6 menu's window starts at screen y = 7 because
   the menu itself isn't aligned to an 8-pixel boundary.
4. For each on-screen 8 × 8 cell aligned to that offset, find the
   source tile + flip orientation that matches the cell's slot
   pattern at ≥ 95% agreement.
5. Verify against W2 / W4 / W5 / W6 / W8: the same tilemap should fit
   their screenshots too (every cell's slot pattern matches the cell
   the tilemap says it should match).  Achieved 100% on W2/W5/W6 and
   ≥ 98% on W4/W8 — the few mismatches there are dithering noise.
6. Repeat for Page A using `screenshots/W3A/`.

**Output**: `web/window_tilemap.js` — `window.WINDOW_TILEMAP = {Y_OFFSET:
7, B: {width, height, tile, flip, mapped}, A: {...}}`.
`tile[ty*width+tx]` is 0..27 (the index of the source-sheet tile at
that screen cell, scanning the 4 × 7 sheet left-to-right then
top-to-bottom); `flip` packs hflip (bit 0) + vflip (bit 1); `mapped`
is 1 where the cell is part of the window's chrome and 0 elsewhere.

**Overlay rendering**: for each cell where `mapped[i]` is 1, walk
the 8 × 8 pixels, look up the corresponding source-sheet pixel in
the user's custom 32 × 56 grid (applying the flip), map through the
active palette, and overwrite the recolored RGB.  A per-pixel chrome
mask (`getChromeMaskOnly`) excludes pixels where the font screenshot
diverges from baseline more than any slot screenshot — those are
text/cursor pixels that `recolor()` already drew correctly and we
shouldn't paint over.

### Unified config JSON

The "Download configuration" button serializes:

```json
{
  "version": 1,
  "flags": "<the existing flagstring textarea content>",
  "graphics": { "<window N>": "<base64 of 928 bytes>", ... }
}
```

The flagstring already encodes palette / font / toggle overrides
for every customized field; the `graphics` map only contains
windows in `ds.customGraphics`.  `ff6_config.py --config FILE.json`
re-parses the embedded flagstring (via `shlex.split`) with any
explicit CLI flags appended *after* it, so users can override an
individual field on the command line without re-opening the web
UI.  After `set_config` applies the merged flags, each base64 blob
is decoded and written via the existing `--window-image` byte
writer.

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
