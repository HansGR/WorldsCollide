# FF6WC Config Builder — web UI

A point-and-click builder for the `ff6_config.py` flagstring.  Move the cursor
through a recolored copy of the FF6 SNES config menu, pick options, tune
window-palette RGB sliders, and copy the assembled CLI flags.

## Running it

The page is a static site with relative asset paths, so any static-file
server works:

```sh
# from the repo root
python3 -m http.server --directory web 8000
# then open http://localhost:8000/
```

## Layout

* **Canvas (left)** — the FF6 config menu, page A or B, displayed at native
  256x224 and scaled 2x.  Cursor sits next to the current value for the
  active row; the yellow underline marks every row's current value.
* **Side panel (right)** — preview-window picker, wallpaper picker,
  controller (`single`/`multiple`) picker, R/G/B sliders for the
  currently-targeted color, reset buttons, and the generated flagstring.
  Choosing `multiple` reveals four "Player 2 controls" checkboxes
  (battle slots 1–4) that map to the `-p2` flag and the in-game
  controller-assignment submenu; they hide again under `single`.

### Keyboard

| Key                | Action                                |
| ------------------ | ------------------------------------- |
| Arrows / WASD      | Move cursor (rows)/ cycle value (cols)|
| Enter / Space      | Toggle / cycle at cursor              |
| Tab                | Switch between page A and page B      |

Mouse clicks on values work too — every value in the canvas is a hit target
that selects that value.

### Picking what the R/G/B sliders edit

On page B, the **Color** row has options `Font` and `slot1` … `slot7`.
The R/G/B sliders always edit whichever target is selected on that row
for the currently-previewed window style.

### Flagstring

The flagstring textbox only emits flags for values that *differ* from
`ff6_config.py`'s defaults (matching the defaults in `config/config.py`),
so the output is minimal.  Paste it after `python3 ff6_config.py -i rom.smc`.

## Window-preview internals

The live preview is a per-pixel linear composite:

```
output[p] = baseline[p]
          + Σ  slot_n_alpha[p] * (slot_n_color / 31)
          + font_alpha[p] * (font_color / 31)
```

`baseline`, `slot_n_alpha`, and `font_alpha` come from the screenshots
under `screenshots/W{i}/`, processed by
`scripts/build_window_assets.py`:

* `W{i}_0.png` — baseline (all slots black)
* `W{i}_N.png` — N=1..7, slot N at full intensity
* `W{i}_font.png` — font color at full intensity (optional)

Run the script after adding screenshots for new window styles:

```sh
python3 scripts/build_window_assets.py
```

It populates `web/assets/W{i}/` with PNGs and writes a `manifest.json`
the UI reads at boot.  Windows without isolation screenshots fall back to
a placeholder; the flagstring side of the tool still works fully.

### Caveats

* The page A canvas is a flat copy of `W{i}_defaultA.png` — palette
  edits only re-render in page B's preview.  Page A is a navigation
  surface; the side-panel preview-window picker is what drives the
  page-B recolor.
* Faint "ghost cursor" hand sprites can show up in the recolored window
  because the cursor was at different positions in each isolation
  screenshot.  `build_window_assets.py` strips small unique clusters,
  but anything sharing pixels with the window's bright borders survives.
  Re-taking the screenshots with the cursor parked off-window would
  give a perfectly clean preview.
* When a window style has no `W{i}_font.png`, the UI falls back to W1's
  font alpha (font glyph positions are the same across window styles
  on the same page).
