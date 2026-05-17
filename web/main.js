/* FF6WC config builder — web UI.
 *
 * State model is divided into three groups:
 *   - simple toggles / index options (BatMode, BatSpeed, ..., Wallpaper)
 *   - Font color (one RGB triple in BGR15, 0..31 per channel)
 *   - Window1..8 palettes (each 7 RGB triples in BGR15)
 *
 * The canvas displays a recolored copy of a reference screenshot of FF6's
 * config menu (page A or B).  The recoloring uses precomputed alpha maps
 * extracted from per-slot isolation screenshots — see
 * scripts/build_window_assets.py for how those are built.
 *
 * Interactive overlays (cursor sprite, value highlights) sit on top of the
 * canvas via positioned hit-layer divs.  Clicking an option, or moving the
 * cursor over it with the keyboard and pressing Enter/Space, toggles or
 * cycles its value.
 */

// ---------------- defaults (must match config/config.py) ----------------

const WINDOW_DEFAULTS = {
  1: [[25,28,28],[20,22,22],[16,16,16],[10,10,10],[5,6,6],   [6,6,17],  [5,5,16]],
  2: [[14,15,15],[8,9,9],   [7,8,8],   [6,7,7],   [5,6,6],   [4,5,5],   [1,2,2]],
  3: [[7,13,16], [6,10,13], [4,7,10],  [3,6,7],   [2,4,5],   [2,3,4],   [10,15,19]],
  4: [[17,12,4], [15,11,4], [14,9,3],  [12,8,2],  [19,21,20],[7,9,8],   [4,6,5]],
  5: [[13,11,8], [12,11,8], [12,10,7], [11,9,6],  [10,8,4],  [7,7,4],   [2,2,2]],
  6: [[19,19,19],[13,15,15],[10,12,11],[8,10,9],  [6,8,7],   [4,6,5],   [1,3,2]],
  7: [[15,21,14],[12,17,11],[9,15,8],  [7,13,6],  [5,10,4],  [4,7,4],   [2,5,3]],
  8: [[20,12,13],[25,24,22],[20,19,16],[26,17,0], [25,13,0], [20,11,0], [4,4,4]],
};

const FONT_DEFAULT = [31, 31, 31];

const TOGGLE_DEFAULTS = {
  BatMode:    'wait',
  BatSpeed:   3,
  MsgSpeed:   3,
  Command:    'window',
  Gauge:      'on',
  Sound:      'stereo',
  Cursor:     'reset',
  Reequip:    'optimum',
  SpellOrder: 1,
  Wallpaper:  1,
  WindowStyle: 1,   // which Window* palette is "active" for editing/preview
};

// Toggles whose value is a binary string.  Order: [false-mapped, true-mapped]
// where the first label is the default-False display (matches config.py Field
// `default=False`) and the second is default-True.
const BINARY_OPTS = {
  BatMode:  ['active', 'wait'],     // default wait (true)
  Command:  ['window', 'short'],    // default window (false)
  Gauge:    ['on',     'off'],      // default on (false → label "on")
  Sound:    ['stereo', 'mono'],     // default stereo
  Cursor:   ['reset',  'memory'],
  Reequip:  ['optimum','empty'],
};

const NUMERIC_OPTS = {
  BatSpeed:   [1,2,3,4,5,6],
  MsgSpeed:   [1,2,3,4,5,6],
  SpellOrder: [1,2,3,4,5,6],
  Wallpaper:  [1,2,3,4,5,6,7,8],
  WindowStyle:[1,2,3,4,5,6,7,8],
};

// ---------------- state ----------------

const state = {
  page: 'A',
  // toggles
  ...structuredClone(TOGGLE_DEFAULTS),
  font: [...FONT_DEFAULT],
  windows: structuredClone(WINDOW_DEFAULTS),
  // editing: 'font' or {window: N, slot: 1..7}
  editing: { kind: 'font' },
  cursor: 0, // index into current page's selectable rows
};

// ---------------- menu layout ----------------
//
// All coordinates are in native 256x224 pixel space.  These rectangles are
// where the cursor "lands" on each value; they are also the clickable hit
// targets for mouse users.  Coords are eyeballed from W1_defaultA.png /
// W1_defaultB.png and tuned visually.

// Y coords correspond to the top of each row's text in the 256x224
// W1_defaultA / W1_defaultB screenshots.  X coords are the left edge of
// each individual value's text, so the cursor (drawn at x-10) lands in the
// gutter just to the left of the word.
const PAGE_A_OPTIONS = [
  { key: 'BatMode',  y: 44, values: [['active', 112], ['wait', 176]] },
  { key: 'BatSpeed', y: 60,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'MsgSpeed', y: 76,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'Command',  y: 92,  values: [['window', 112], ['short', 176]] },
  { key: 'Gauge',    y:108,  values: [['on',     112], ['off',   176]] },
  { key: 'Sound',    y:124,  values: [['stereo', 112], ['mono',  176]] },
  { key: 'Cursor',   y:140,  values: [['reset',  112], ['memory',176]] },
  { key: 'Reequip',  y:156,  values: [['optimum',112], ['empty', 176]] },
];

const PAGE_B_OPTIONS = [
  { key: 'SpellOrder',  y: 44,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'WindowStyle', y:108,
    values: [1,2,3,4,5,6,7,8].map((v,i)=>[v, 112 + i*16])  },
  // Color row: selects what the R/G/B sliders edit.  "font" sits on the
  // text row at y=128, but the seven slot swatches FF6 draws live one
  // line below in a tighter row of small color blocks.
  { key: 'Color',       y:124, kind: 'color',
    values: [
      ['font', 112, 124],
      ...([1,2,3,4,5,6,7].map((s,i)=>[`slot${s}`, 180 + i*8, 139]))
    ] },
  // R / G / B sliders.  Pressing Down from the Color row lands on R;
  // Down from R goes to G, then B.  On each slider row, Left/Right
  // decrements/increments the corresponding channel of whichever target
  // the Color row picked (font or one of the seven window slots).  We
  // don't redraw the slider bar in the canvas — the side-panel slider
  // already reflects the live value and that's the source of truth.
  { key: 'R', y:154, kind: 'slider', channel: 0, cursorX: 112 },
  { key: 'G', y:170, kind: 'slider', channel: 1, cursorX: 112 },
  { key: 'B', y:186, kind: 'slider', channel: 2, cursorX: 112 },
];

// Row labels drawn at the leftmost column when a non-screenshot page is shown.
// (Currently the canvas just shows the actual recolored screenshot so we
//  only rely on the hit positions above for navigation.)

// ---------------- assets ----------------

const assets = {
  manifest: null,
  windowAssets: {},   // {1: {baseline, slot1..7, font, defaultA, defaultB}}
  magOrder: {},       // {1: HTMLImageElement, ..., 6: HTMLImageElement}
  magOrderBbox: null, // [x0, y0, x1, y1]
};

async function loadMagOrderOverlays() {
  const info = assets.manifest && assets.manifest.magOrder;
  if (!info) {
    console.warn('manifest.magOrder missing — Mag.Order text overlay disabled');
    return;
  }
  assets.magOrderBbox = info.bbox;
  const [x0, y0, x1, y1] = info.bbox;
  const w = x1 - x0, h = y1 - y0;
  const tmp = document.createElement('canvas');
  tmp.width = w; tmp.height = h;
  const tctx = tmp.getContext('2d');
  for (const n of info.presets) {
    try {
      const img = await loadImage(`assets/magorder/${n}.png`);
      tctx.clearRect(0, 0, w, h);
      tctx.drawImage(img, 0, 0);
      assets.magOrder[n] = tctx.getImageData(0, 0, w, h);
    } catch (e) {
      console.warn(`Failed to load MagOrder preset ${n}:`, e);
    }
  }
}

// Per-session cache-bust for every asset fetch.  The static-server cache
// in the typical hosting setup is aggressive enough that a redeploy of
// the assets (new manifest.json, new MagOrder crops, ...) goes unnoticed
// until the user does a hard-reload — that's been catching real users.
// Pinning a single timestamp at boot means assets are fetched fresh on
// every page load without churning the cache on every individual call.
const CB = '?v=' + Date.now();

async function loadImage(url) {
  const img = new Image();
  img.src = url + CB;
  await img.decode();
  return img;
}

async function loadManifest() {
  const r = await fetch('assets/manifest.json' + CB);
  return r.json();
}

async function getFontDataFallback() {
  // Many windows ship without their own W{i}_font.png.  The font is rendered
  // at fixed positions on the menu regardless of window style, so we reuse
  // whichever window's font.png we do have (W1 if available).
  for (const k of Object.keys(assets.manifest.windows || {})) {
    const info = assets.manifest.windows[k];
    if (info.font) {
      const a = await loadWindowAssets(parseInt(k, 10));
      return a?.fontData || null;
    }
  }
  return null;
}

async function loadWindowAssets(n) {
  if (assets.windowAssets[n]) return assets.windowAssets[n];
  const info = assets.manifest.windows[String(n)];
  if (!info) return null;
  const base = `assets/W${n}/`;
  const promises = [loadImage(base + 'baseline.png')];
  for (let s = 1; s <= 7; s++) {
    if (info.slots.includes(s)) promises.push(loadImage(base + `slot${s}.png`));
    else promises.push(Promise.resolve(null));
  }
  promises.push(info.font ? loadImage(base + 'font.png') : Promise.resolve(null));
  if (info.hasDefaultA) promises.push(loadImage(base + 'defaultA.png'));
  else promises.push(Promise.resolve(null));
  if (info.hasDefaultB) promises.push(loadImage(base + 'defaultB.png'));
  else promises.push(Promise.resolve(null));
  if (info.hasCorrection)
    promises.push(fetch(base + 'correction.json' + CB).then(r => r.json()));
  else
    promises.push(Promise.resolve(null));

  const imgs = await Promise.all(promises);
  const a = {
    baseline: imgs[0],
    slots: imgs.slice(1, 8),
    font: imgs[8],
    defaultA: imgs[9],
    defaultB: imgs[10],
    correction: imgs[11],  // (H rows) × [r, g, b] residual to add per pixel.
  };
  // Convert each to ImageData so we can do per-pixel math fast.
  const toData = (im) => {
    if (!im) return null;
    const c = document.createElement('canvas');
    c.width = 256; c.height = 224;
    const cx = c.getContext('2d');
    cx.drawImage(im, 0, 0);
    return cx.getImageData(0, 0, 256, 224);
  };
  a.baselineData = toData(a.baseline);
  a.slotsData    = a.slots.map(toData);
  a.fontData     = toData(a.font);
  a.fontFromFallback = false;
  assets.windowAssets[n] = a;
  if (!a.fontData) {
    a.fontData = await getFontDataFallback();
    a.fontFromFallback = !!a.fontData;
  }
  return a;
}

// ---------------- rendering ----------------

const canvas = document.getElementById('menu-canvas');
const ctx    = canvas.getContext('2d');
const hitLayer = document.getElementById('hit-layer');

// Cursor sprite — a small bitmap drawn at the active option.
// Simple 8x8 right-pointing arrow.
const CURSOR_SPRITE = (() => {
  const c = document.createElement('canvas');
  c.width = 8; c.height = 8;
  const cx = c.getContext('2d');
  const px = [
    "X.......",
    "XX......",
    "XXX.....",
    "XXXX....",
    "XXXX....",
    "XXX.....",
    "XX......",
    "X.......",
  ];
  cx.fillStyle = '#fff';
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    if (px[y][x] === 'X') cx.fillRect(x, y, 1, 1);
  }
  return c;
})();

function recolor(asset) {
  // Compose:  output[p] = baseline[p]
  //                     + Σ (slot_n_raw[p] - baseline[p]) * c_n / 31
  //                     +  (font_raw[p]    - baseline[p]) * c_f / 31
  // The stored slot{N}.png and font.png are the RAW W_N / W_font
  // screenshots (with cursor sprites scrubbed), not pre-subtracted deltas,
  // so this preserves *signed* per-channel contributions — including the
  // pixels whose intensity drops when a slot turns on (e.g. wallpaper
  // pixels that get averaged with the slot color instead of rendered at
  // full brightness).
  if (!asset || !asset.baselineData) return null;
  const W = 256, H = 224;
  const out = ctx.createImageData(W, H);
  const N = W * H * 4;
  const base = asset.baselineData.data;

  const winN = state.WindowStyle;
  const slotColors = state.windows[winN];
  const fontColor = state.font;

  // Per-channel scalar weight on the *baseline* contribution:
  //   weight_base = 1 - Σ c_n_ch/31 - c_font_ch/31
  // (this lets us rewrite  baseline + Σ (raw_n - baseline) * c_n/31
  //                     =  baseline * weight_base + Σ raw_n * c_n/31
  //  in a single linear pass per channel.)
  let wBaseR = 1, wBaseG = 1, wBaseB = 1;
  for (let s = 0; s < 7; s++) {
    if (!asset.slotsData[s]) continue;
    const c = slotColors[s];
    wBaseR -= c[0] / 31; wBaseG -= c[1] / 31; wBaseB -= c[2] / 31;
  }
  if (asset.fontData) {
    wBaseR -= fontColor[0] / 31;
    wBaseG -= fontColor[1] / 31;
    wBaseB -= fontColor[2] / 31;
  }

  // ImageData backing arrays are Uint8ClampedArray which clamp on every
  // write — that erases the signed intermediate sums we need.  Accumulate
  // into a Float32Array, then commit.
  const acc = new Float32Array(N);
  for (let i = 0; i < N; i += 4) {
    acc[i  ] = base[i  ] * wBaseR;
    acc[i+1] = base[i+1] * wBaseG;
    acc[i+2] = base[i+2] * wBaseB;
  }
  for (let s = 0; s < 7; s++) {
    const sd = asset.slotsData[s];
    if (!sd) continue;
    const c = slotColors[s];
    const rs = c[0] / 31, gs = c[1] / 31, bs = c[2] / 31;
    if (rs === 0 && gs === 0 && bs === 0) continue;
    const d = sd.data;
    for (let i = 0; i < N; i += 4) {
      acc[i  ] += d[i  ] * rs;
      acc[i+1] += d[i+1] * gs;
      acc[i+2] += d[i+2] * bs;
    }
  }
  if (asset.fontData) {
    const c = fontColor;
    const rs = c[0] / 31, gs = c[1] / 31, bs = c[2] / 31;
    const d = asset.fontData.data;
    for (let i = 0; i < N; i += 4) {
      acc[i  ] += d[i  ] * rs;
      acc[i+1] += d[i+1] * gs;
      acc[i+2] += d[i+2] * bs;
    }
  }
  // Per-row residual correction: fits the SNES per-scanline color-math
  // pass that the linear baseline + Σ slot · c/31 model doesn't capture.
  // The values are fit against the default-palette screenshot, so they're
  // exact at defaults and "shifted in the right direction" for other
  // palettes.
  if (asset.correction) {
    const corr = asset.correction;
    for (let y = 0; y < H; y++) {
      const cr = corr[y][0], cg = corr[y][1], cb = corr[y][2];
      const row = y * W * 4;
      for (let x = 0; x < W; x++) {
        const i = row + x * 4;
        acc[i  ] += cr;
        acc[i+1] += cg;
        acc[i+2] += cb;
      }
    }
  }

  for (let i = 0; i < N; i += 4) {
    out.data[i  ] = acc[i  ];   // Uint8ClampedArray clamps to [0,255]
    out.data[i+1] = acc[i+1];
    out.data[i+2] = acc[i+2];
    out.data[i+3] = 255;
  }
  return out;
}

function currentAsset() {
  return assets.windowAssets[state.WindowStyle] || null;
}

function getCurrentOptions() {
  return state.page === 'A' ? PAGE_A_OPTIONS : PAGE_B_OPTIONS;
}

function render() {
  const asset = currentAsset();
  if (asset) {
    const data = recolor(asset);
    if (data) ctx.putImageData(data, 0, 0);

    // The recolored image is page B (it's what was screenshotted for slot
    // isolation).  If the user wants page A, overlay the (recolored) defaultA
    // — but we only have defaultA as a flat screenshot.  Approximation: draw
    // it directly when page A is selected and we have it.
    if (state.page === 'A' && asset.defaultA) {
      // Use defaultA pixel data as a passthrough — colors are already
      // baked in.  For windows that have isolation data, we could try to
      // re-derive, but the user only isolated page B.  Best effort:
      // show the default-palette page A for whichever window style is
      // selected.  If the user changed window colors, page A preview
      // can't reflect that.
      ctx.drawImage(asset.defaultA, 0, 0);
      drawPaletteHintBar();
    }
  } else {
    drawPlaceholder();
  }

  if (state.page === 'B') {
    drawMagOrderText();
    drawColorEditValues();
  }
  highlightValueText();
  drawCursorOverlay();
  drawSelectionOverlay();
  updateHitTargets();
}

function drawMagOrderText() {
  // The "A.. Healing / B.. Attack / C.. Effect" block under the Mag.Order
  // row changes with each spell-order preset.  We swap it in two steps:
  //
  // 1. ERASE — the menu wallpaper repeats on a 32-px horizontal period,
  //    so we tile-copy the 32 px immediately to the left of the
  //    MagOrder region across it (L-to-R, in place, so the third 32-px
  //    block reads freshly-cleared pixels from the second one).  This
  //    removes preset 1's text that was baked into the W_N isolation
  //    shots without leaving any ghost outlines.
  //
  // 2. STAMP — composite the chosen preset's text on top by copying
  //    only the bright pixels (max channel > threshold) from the
  //    cropped MagOrder_N image.  The crops were captured under W1's
  //    default palette so the text uses W1's colors; the background
  //    around the glyphs comes from the live recolored wallpaper.
  const n = state.SpellOrder;
  const img = assets.magOrder[n];
  if (!img || !assets.magOrderBbox) return;

  const [x0, y0, x1, y1] = assets.magOrderBbox;
  const w = x1 - x0, h = y1 - y0;
  const TILE = 32;
  if (x0 - TILE < 0) return;

  // 1) Tile-erase.
  const ext = ctx.getImageData(x0 - TILE, y0, w + TILE, h);
  const d = ext.data;
  const W_EXT = w + TILE;
  for (let y = 0; y < h; y++) {
    const row = y * W_EXT * 4;
    for (let x = TILE; x < W_EXT; x++) {
      const off = row + x * 4;
      const src = off - TILE * 4;
      d[off    ] = d[src    ];
      d[off + 1] = d[src + 1];
      d[off + 2] = d[src + 2];
    }
  }
  ctx.putImageData(ext, x0 - TILE, y0);

  // 2) Stamp text glyphs.
  const TEXT_THRESHOLD = 70;
  const region = ctx.getImageData(x0, y0, w, h);
  const rd = region.data, md = img.data;
  for (let i = 0; i < rd.length; i += 4) {
    const mx = Math.max(md[i], md[i+1], md[i+2]);
    if (mx > TEXT_THRESHOLD) {
      rd[i    ] = md[i    ];
      rd[i + 1] = md[i + 1];
      rd[i + 2] = md[i + 2];
    }
  }
  ctx.putImageData(region, x0, y0);
}

function drawPlaceholder() {
  ctx.fillStyle = '#222';
  ctx.fillRect(0, 0, 256, 224);
  ctx.fillStyle = '#fc8';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText(`No preview art for Window ${state.WindowStyle}`, 128, 100);
  ctx.fillText('(slot-isolation screenshots missing)', 128, 116);
  ctx.fillText('Settings still apply to the flagstring.', 128, 132);
  ctx.textAlign = 'start';
}

function drawPaletteHintBar() {
  // Page A renders a flat copy of the default screenshot — palette
  // adjustments only re-color in the page-B preview.
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(0, 210, 256, 14);
  ctx.fillStyle = '#bcd';
  ctx.font = '9px monospace';
  ctx.fillText('(live recolor preview is on Page B)', 4, 220);
  ctx.restore();
}

function activeRow() {
  const opts = getCurrentOptions();
  return opts[state.cursor];
}

function activeValueIndex() {
  const row = activeRow();
  if (!row) return 0;
  if (row.kind === 'slider') return 0;  // no discrete values
  const cur = currentValueOf(row);
  const i = row.values.findIndex(([v]) => v === cur);
  return i < 0 ? 0 : i;
}

function currentValueOf(row) {
  if (row.kind === 'color') {
    if (state.editing.kind === 'font') return 'font';
    return `slot${state.editing.slot}`;
  }
  if (row.kind === 'slider') return editedRgb()[row.channel];
  return state[row.key];
}

function editedRgb() {
  return state.editing.kind === 'font'
    ? state.font
    : state.windows[state.WindowStyle][state.editing.slot - 1];
}

function valuePos(row, item) {
  // Each row.values entry is [value, x] or [value, x, y].  The y override
  // is used by the Color row's slot swatches, which sit one line below
  // the row's text label.
  const [, x, yOverride] = item;
  return { x, y: yOverride ?? row.y };
}

function drawCursorOverlay() {
  const row = activeRow();
  if (!row) return;
  let cx, cy;
  if (row.kind === 'slider') {
    cx = row.cursorX; cy = row.y;
  } else {
    const v = row.values[activeValueIndex()];
    if (!v) return;
    ({ x: cx, y: cy } = valuePos(row, v));
  }
  ctx.save();
  ctx.drawImage(CURSOR_SPRITE, cx - 10, cy + 1);
  ctx.restore();
}

// Bitmap masks of digits 1-8 in the FF6 menu font, extracted from
// W1_defaultB.png's "Window" row.  Each entry is 10 rows × 8 columns
// (MSB on the left of each row) representing exactly which pixels are
// part of the glyph.  Used by highlightValueText() to recolor only the
// glyph strokes — not the surrounding rectangle — when a numeric option
// is selected vs. dimmed.
// Bitmap masks of digits 0-9 in the FF6 menu font.  Indices 1-8 were
// extracted from the Window row of W1_defaultB.png; 0 and 9 were
// hand-constructed to match the same style (closed oval / mirror of 6).
// Each entry is 10 rows × 8 columns, MSB on the left, so the renderer
// can walk the same bitloop as before.  Index matches the digit value.
const DIGIT_MASKS = [
  /* 0 */ [0, 0b01111100, 0b11000110, 0b11000110, 0b11000110, 0b11000110, 0b11000110, 0b01111100, 0, 0],
  /* 1 */ [0, 0b00110000, 0b01110000, 0b00110000, 0b00110000, 0b00110000, 0b00110000, 0b01111000, 0, 0],
  /* 2 */ [0, 0b01111100, 0b10000110, 0b00000110, 0b00001100, 0b00110000, 0b01100000, 0b11111110, 0, 0],
  /* 3 */ [0, 0b11111110, 0b00001100, 0b00011000, 0b00111100, 0b00000110, 0b10000110, 0b01111100, 0, 0],
  /* 4 */ [0, 0b00011100, 0b00101100, 0b01001100, 0b10001100, 0b10001100, 0b11111110, 0b00001100, 0, 0],
  /* 5 */ [0, 0b11111110, 0b11000000, 0b11111100, 0b00000110, 0b00000110, 0b10000110, 0b01111100, 0, 0],
  /* 6 */ [0, 0b00111100, 0b01100000, 0b11000000, 0b11111100, 0b11000110, 0b11000110, 0b01111100, 0, 0],
  /* 7 */ [0, 0b11111110, 0b00000110, 0b00000110, 0b00001100, 0b00011000, 0b00110000, 0b00110000, 0, 0],
  /* 8 */ [0, 0b01111100, 0b11000110, 0b11000110, 0b01111100, 0b11000110, 0b11000110, 0b01111100, 0, 0],
  /* 9 */ [0, 0b01111100, 0b11000110, 0b11000110, 0b01111110, 0b00000110, 0b00001100, 0b01111000, 0, 0],
];
const DIGIT_MASK_W = 8;
const DIGIT_MASK_H = 10;

// Bitmap masks of Page A's twelve binary-option words, extracted from
// W1_defaultA.png (defaults: wait, window, on, stereo, reset, optimum)
// and W1_defaultA_opposite.png (the rest).  Rows are packed as 32-bit
// unsigned ints, with column 0 in the MSB of the first int.  Masks
// wider than 32 px take multiple ints per row (`ipr`).
const WORD_MASKS = {
  'wait':    { w: 30, h: 7, ipr: 1, rows: [0xb6003030, 0xb67830fc, 0xb68c0030, 0xb67c3030, 0xb6cc3030, 0xb6cc3030, 0xfc7c301c] },
  'window':  { w: 47, h: 7, ipr: 2, rows: [0xb630000c, 0x00000000, 0xb630f80c, 0x78b60000, 0xb600cc7c, 0xccb60000, 0xb630cccc, 0xccb60000, 0xb630cccc, 0xccb60000, 0xb630cccc, 0xccb60000, 0xfc30cc7c, 0x78fc0000] },
  'on':      { w: 14, h: 7, ipr: 1, rows: [0x7c000000, 0xc6f80000, 0xc6cc0000, 0xc6cc0000, 0xc6cc0000, 0xc6cc0000, 0x7ccc0000] },
  'stereo':  { w: 46, h: 7, ipr: 2, rows: [0x7c300000, 0x00000000, 0xc2fc78dc, 0x78780000, 0xe030cce0, 0xcccc0000, 0x7830fcc0, 0xfccc0000, 0x1c30c0c0, 0xc0cc0000, 0x8e30c4c0, 0xc4cc0000, 0x7c1c78c0, 0x78780000] },
  'reset':   { w: 38, h: 7, ipr: 2, rows: [0xfc000000, 0x30000000, 0xc6787878, 0xfc000000, 0xc6ccc4cc, 0x30000000, 0xfcfc70fc, 0x30000000, 0xc6c038c0, 0x30000000, 0xc6c48cc4, 0x30000000, 0xc6787878, 0x1c000000] },
  'optimum': { w: 55, h: 8, ipr: 2, rows: [0x7c003030, 0x00000000, 0xc6f8fc30, 0xfcccfc00, 0xc6cc3000, 0xb6ccb600, 0xc6cc3030, 0xb6ccb600, 0xc6cc3030, 0xb6ccb600, 0xc6f83030, 0xb6ccb600, 0x7cc01c30, 0xb67cb600, 0x00c00000, 0x00000000] },
  'active':  { w: 46, h: 7, ipr: 2, rows: [0x7c003030, 0x00000000, 0xc678fc30, 0xcc780000, 0xc6c43000, 0xcccc0000, 0xc6c03030, 0xccfc0000, 0xfec03030, 0xccc00000, 0xc6c43030, 0xc8c40000, 0xc6781c30, 0xf0780000] },
  'short':   { w: 38, h: 7, ipr: 2, rows: [0x7cc00000, 0x30000000, 0xc2c078dc, 0xfc000000, 0xe0f8cce0, 0x30000000, 0x78ccccc0, 0x30000000, 0x1cccccc0, 0x30000000, 0x8eccccc0, 0x30000000, 0x7ccc78c0, 0x1c000000] },
  'off':     { w: 22, h: 7, ipr: 1, rows: [0x7c1c1c00, 0xc6303000, 0xc6fcfc00, 0xc6303000, 0xc6303000, 0xc6303000, 0x7c303000] },
  'mono':    { w: 30, h: 7, ipr: 1, rows: [0x86000000, 0xce78f878, 0xfecccccc, 0xb6cccccc, 0x86cccccc, 0x86cccccc, 0x8678cc78] },
  'memory':  { w: 46, h: 8, ipr: 2, rows: [0x86000000, 0x00000000, 0xce78fc78, 0xdccc0000, 0xfeccb6cc, 0xe0cc0000, 0xb6fcb6cc, 0xc0cc0000, 0x86c0b6cc, 0xc07c0000, 0x86c4b6cc, 0xc00c0000, 0x8678b678, 0xc08c0000, 0x00000000, 0x00780000] },
  'empty':   { w: 38, h: 8, ipr: 2, rows: [0xfe000030, 0x00000000, 0xc0fcf8fc, 0xcc000000, 0xc0b6cc30, 0xcc000000, 0xfcb6cc30, 0xcc000000, 0xc0b6cc30, 0x7c000000, 0xc0b6f830, 0x0c000000, 0xfeb6c01c, 0x8c000000, 0x0000c000, 0x78000000] },
};

// ---------------- Slider value + bar repaint -------------------------

// Layout constants for the three R/G/B rows on page B.  Numbers and the
// slider-fill stripe both live within these bands; the bar's outline
// (rounded capsule with a 1-px white top/bottom edge) lives in the same
// y range but at columns that the renderer never touches.
const SLIDER_ROWS = [
  { y: 154, channel: 0 },   // R
  { y: 170, channel: 1 },   // G
  { y: 186, channel: 2 },   // B
];
const SLIDER_NUM_TENS_X = 128;
const SLIDER_NUM_ONES_X = 137;
const SLIDER_NUM_Y_OFF  = 2;        // top of the digit row, relative to row.y
const SLIDER_NUM_ERASE_X = 127;
const SLIDER_NUM_ERASE_W = 18;
const SLIDER_NUM_ERASE_H = 9;
const SLIDER_NUM_ERASE_SRC_X = 80;  // clean menu fill, just left of "R"
const SLIDER_BAR_X0    = 152;       // first column of the fill region
const SLIDER_BAR_W31   = 62;        // total fill width when value = 31
const SLIDER_BAR_Y_OFF = 5;         // first of three interior fill rows
const SLIDER_BAR_FILL_H = 3;        // bar interior is three pixels tall
const SLIDER_BAR_DARK_SAMPLE_OFF = 4;  // dark inner-border row (always 99-ish)

function drawColorEditValues() {
  // Repaint each R/G/B row's value text and slider-fill to reflect the
  // current target's channel value.  The user's tip: just paint over
  // the numbers and the bar's white stripe — the bar's outline rows
  // (top/bottom edges, rounded ends) stay untouched.
  const rgb = editedRgb();
  // Number text + bar fill use the font palette in the real game, so
  // they tint with whatever font colour the user has chosen.  Mirror
  // that by painting in state.font scaled to 8-bit; matches the recolored
  // canvas's R / G / B labels closely enough that they blend.
  const fr = Math.round(state.font[0] * 255 / 31);
  const fg = Math.round(state.font[1] * 255 / 31);
  const fb = Math.round(state.font[2] * 255 / 31);
  const fontCss = `rgb(${fr}, ${fg}, ${fb})`;
  for (const row of SLIDER_ROWS) {
    redrawNumber(row.y, rgb[row.channel], fontCss);
    redrawBarFill(row.y, rgb[row.channel], fontCss);
  }
}

function redrawNumber(rowY, value, fontCss) {
  // Erase the two-digit number area with a tile copy from a clean
  // patch of menu fill just left of the R/G/B labels.
  const yTop = rowY + SLIDER_NUM_Y_OFF;
  const src = ctx.getImageData(SLIDER_NUM_ERASE_SRC_X, yTop,
                                SLIDER_NUM_ERASE_W,   SLIDER_NUM_ERASE_H);
  ctx.putImageData(src, SLIDER_NUM_ERASE_X, yTop);
  if (value >= 10) drawDigit(SLIDER_NUM_TENS_X, yTop, Math.floor(value / 10), fontCss);
  drawDigit(SLIDER_NUM_ONES_X, yTop, value % 10, fontCss);
}

function drawDigit(x, y, digit, fillCss) {
  const mask = DIGIT_MASKS[digit];
  if (!mask) return;
  ctx.fillStyle = fillCss;
  for (let dy = 0; dy < DIGIT_MASK_H; dy++) {
    const py = y + dy - 1;     // same -1 offset as highlightValueText
    if (py < 0 || py >= 224) continue;
    const bits = mask[dy];
    if (!bits) continue;
    for (let dx = 0; dx < DIGIT_MASK_W; dx++) {
      const px = x + dx;
      if (px < 0 || px >= 256) continue;
      if (bits & (1 << (DIGIT_MASK_W - 1 - dx))) {
        ctx.fillRect(px, py, 1, 1);
      }
    }
  }
}

function redrawBarFill(rowY, value, fontCss) {
  // The bar's interior is 3 px tall.  When empty, it's the same dark
  // colour as the inner-border row just above; when filled, it's solid
  // white.  Sample the inner-border row to track each window's
  // y-correction automatically.
  const refY = rowY + SLIDER_BAR_DARK_SAMPLE_OFF;
  const ref  = ctx.getImageData(180, refY, 1, 1).data;
  const darkCss = `rgb(${ref[0]}, ${ref[1]}, ${ref[2]})`;
  const fillW   = Math.round(value * SLIDER_BAR_W31 / 31);
  const restW   = SLIDER_BAR_W31 - fillW;
  for (let i = 0; i < SLIDER_BAR_FILL_H; i++) {
    const y = rowY + SLIDER_BAR_Y_OFF + i;
    if (fillW > 0) {
      ctx.fillStyle = fontCss;
      ctx.fillRect(SLIDER_BAR_X0, y, fillW, 1);
    }
    if (restW > 0) {
      ctx.fillStyle = darkCss;
      ctx.fillRect(SLIDER_BAR_X0 + fillW, y, restW, 1);
    }
  }
}

function highlightValueText() {
  // FF6 renders the selected option's text white and other options grey.
  // We bake the selected state in at render time: scale text pixels so
  // the selected value's peak channel goes to 255 and the rest go to 128,
  // preserving per-pixel hue.
  //
  // For numeric options (BatSpeed, MsgSpeed, SpellOrder, WindowStyle)
  // we use precomputed digit bitmap masks so only the glyph strokes are
  // touched and the surrounding background is left alone.  String
  // options still use a brightness-threshold fallback over the bbox.
  const opts = getCurrentOptions();
  if (!opts.length) return;
  const W = 256, H = 224;
  const data = ctx.getImageData(0, 0, W, H);
  const d = data.data;
  const TEXT_THRESHOLD = 80;
  const BRIGHT_TARGET = 255;
  const DIM_TARGET    = 128;

  const adjustPixel = (i, target) => {
    const r = d[i], g = d[i+1], b = d[i+2];
    const m = Math.max(r, g, b);
    if (m <= TEXT_THRESHOLD) return;
    const scale = target / m;
    d[i  ] = Math.min(255, r * scale);
    d[i+1] = Math.min(255, g * scale);
    d[i+2] = Math.min(255, b * scale);
  };

  for (const row of opts) {
    if (row.kind === 'color' || row.kind === 'slider') continue;
    const cur = currentValueOf(row);
    for (const item of row.values) {
      const [val] = item;
      const { x, y } = valuePos(row, item);
      const target = val === cur ? BRIGHT_TARGET : DIM_TARGET;

      if (typeof val === 'number' && val >= 0 && val < DIGIT_MASKS.length) {
        // Digit: walk only the glyph pixels.  The captured masks include
        // an empty padding row at index 0, so the first glyph row lives
        // at mask[1] — offset by -1 so mask[1] lands on row.y, which is
        // the actual top of the digit in every numeric row.
        const mask = DIGIT_MASKS[val];
        for (let dy = 0; dy < DIGIT_MASK_H; dy++) {
          const py = y + dy - 1;
          if (py < 0 || py >= H) continue;
          let bits = mask[dy];
          if (!bits) continue;
          for (let dx = 0; dx < DIGIT_MASK_W; dx++) {
            const px = x + dx;
            if (px < 0 || px >= W) continue;
            if (bits & (1 << (DIGIT_MASK_W - 1 - dx))) {
              adjustPixel((py * W + px) * 4, target);
            }
          }
        }
      } else if (typeof val === 'string' && WORD_MASKS[val]) {
        // String option: walk the per-word bitmap mask so only the glyph
        // strokes are touched (no halo around the word).
        const m = WORD_MASKS[val];
        for (let dy = 0; dy < m.h; dy++) {
          const py = y + dy;
          if (py < 0 || py >= H) continue;
          for (let dx = 0; dx < m.w; dx++) {
            const px = x + dx;
            if (px < 0 || px >= W) continue;
            const intIdx = dx >> 5;            // 0 for first 32 cols, 1 for next 32
            const bitIdx = 31 - (dx & 31);
            const word = m.rows[dy * m.ipr + intIdx];
            if (word & (1 << bitIdx)) {
              adjustPixel((py * W + px) * 4, target);
            }
          }
        }
      } else {
        // Anything else: fall back to brightness-threshold rectangle.
        const w = approxValueWidth(row, val);
        const h = 9;
        for (let py = y; py < y + h && py < H; py++) {
          for (let px = x; px < x + w && px < W; px++) {
            adjustPixel((py * W + px) * 4, target);
          }
        }
      }
    }
  }
  ctx.putImageData(data, 0, 0);
}

function drawSelectionOverlay() {
  // Draw a small marker under each row's current value so the user can see
  // every chosen setting at a glance (the cursor only marks the active row).
  const opts = getCurrentOptions();
  ctx.save();
  ctx.fillStyle = 'rgba(255, 240, 120, 0.85)';
  for (const row of opts) {
    if (row.kind === 'slider') continue;  // no per-value highlight on sliders
    const cur = currentValueOf(row);
    const item = row.values.find(([v]) => v === cur);
    if (!item) continue;
    const { x, y } = valuePos(row, item);
    const w = approxValueWidth(row, item[0]);
    ctx.fillRect(x, y + 10, w, 1);
  }
  ctx.restore();
}

function approxValueWidth(row, v) {
  if (row.kind === 'color') {
    // 'font' is a word, slot1..7 are tiny swatches.
    return v === 'font' ? 22 : 4;
  }
  if (row.kind === 'wallpaper') return 12;
  if (typeof v === 'number') return 8;
  // ~6px per char roughly
  return Math.min(56, String(v).length * 7 + 4);
}

// ---------------- hit targets / mouse ----------------

function updateHitTargets() {
  hitLayer.innerHTML = '';
  const opts = getCurrentOptions();
  for (let r = 0; r < opts.length; r++) {
    const row = opts[r];
    if (row.kind === 'slider') continue;  // sliders are keyboard-only for now
    for (let v = 0; v < row.values.length; v++) {
      const item = row.values[v];
      const val = item[0];
      const { x, y } = valuePos(row, item);
      const w = approxValueWidth(row, val);
      const el = document.createElement('div');
      el.className = 'hit';
      // hit-layer occupies the canvas; canvas displays at 2x.
      el.style.left   = (x - 2) * 2 + 'px';
      el.style.top    = y * 2 + 'px';
      el.style.width  = (w + 4) * 2 + 'px';
      el.style.height = 12 * 2 + 'px';
      el.title = `${row.key}: ${val}`;
      el.addEventListener('click', () => {
        state.cursor = r;
        selectValue(row, val);
      });
      hitLayer.appendChild(el);
    }
  }
}

// ---------------- input handling ----------------

function move(dRow, dCol) {
  if (dRow !== 0) {
    // Vertical movement wraps both within and across pages: pressing down
    // from the last row of page A drops into row 0 of page B and vice
    // versa.  Same direction wraps from row 0 back to the last row of
    // the other page.
    const opts = getCurrentOptions();
    const next = state.cursor + dRow;
    if (next < 0) {
      state.page = state.page === 'A' ? 'B' : 'A';
      const otherOpts = getCurrentOptions();
      state.cursor = otherOpts.length - 1;
      updateTabUI();
    } else if (next >= opts.length) {
      state.page = state.page === 'A' ? 'B' : 'A';
      state.cursor = 0;
      updateTabUI();
    } else {
      state.cursor = next;
    }
  }
  if (dCol !== 0) {
    const opts = getCurrentOptions();
    const row = opts[state.cursor];
    if (row.kind === 'slider') {
      adjustChannel(row.channel, dCol);
      return;
    }
    const cur = activeValueIndex();
    const next = (cur + dCol + row.values.length) % row.values.length;
    selectValue(row, row.values[next][0]);
    return;
  }
  render();
  syncSidePanel();
}

function adjustChannel(ch, delta) {
  const rgb = editedRgb();
  rgb[ch] = Math.max(0, Math.min(31, rgb[ch] + delta));
  render();
  syncSidePanel();
  updateFlagString();
}

function selectCurrent() {
  const row = activeRow();
  if (row.kind === 'slider') return;   // Enter on a slider is a no-op
  const idx = activeValueIndex();
  const [val] = row.values[idx];
  selectValue(row, val);
}

function selectValue(row, val) {
  if (row.kind === 'color') {
    if (val === 'font') state.editing = { kind: 'font' };
    else {
      const slot = parseInt(String(val).slice(4), 10);
      state.editing = { kind: 'slot', slot };
    }
  } else if (row.key === 'WindowStyle') {
    state.WindowStyle = val;
    loadWindowAssets(val).then(render);
    document.getElementById('window-style').value = String(val);
  } else {
    state[row.key] = val;
  }
  render();
  syncSidePanel();
  updateFlagString();
}

function keyHandler(e) {
  const k = e.key.toLowerCase();
  if (k === 'arrowup'    || k === 'w') { move(-1, 0); e.preventDefault(); return; }
  if (k === 'arrowdown'  || k === 's') { move( 1, 0); e.preventDefault(); return; }
  if (k === 'arrowleft'  || k === 'a') { move( 0,-1); e.preventDefault(); return; }
  if (k === 'arrowright' || k === 'd') { move( 0, 1); e.preventDefault(); return; }
  if (k === 'enter' || k === ' ')      { selectCurrent(); e.preventDefault(); return; }
  if (k === 'tab') {
    state.page = state.page === 'A' ? 'B' : 'A';
    state.cursor = 0;
    updateTabUI();
    render();
    syncSidePanel();
    e.preventDefault();
  }
}

// Bind on window only, but ignore when a form control is focused so the
// user can still type in the flagstring textarea / slider / select.
window.addEventListener('keydown', (e) => {
  const ae = document.activeElement;
  if (ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA' ||
             ae.tagName === 'SELECT')) return;
  keyHandler(e);
});

// ---------------- side panel sync ----------------

function syncSidePanel() {
  const title = document.getElementById('color-edit-title');
  let rgb;
  if (state.editing.kind === 'font') {
    title.textContent = 'Editing: Font color';
    rgb = state.font;
  } else {
    const s = state.editing.slot;
    title.textContent = `Editing: Window ${state.WindowStyle}, slot ${s}`;
    rgb = state.windows[state.WindowStyle][s - 1];
  }
  document.getElementById('rgb-r').value = rgb[0];
  document.getElementById('rgb-g').value = rgb[1];
  document.getElementById('rgb-b').value = rgb[2];
  document.getElementById('rgb-r-val').textContent = rgb[0];
  document.getElementById('rgb-g-val').textContent = rgb[1];
  document.getElementById('rgb-b-val').textContent = rgb[2];

  // Target selector (Font / Window + slot index)
  const isFont = state.editing.kind === 'font';
  document.querySelectorAll('#target-kind .seg-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.kind === (isFont ? 'font' : 'slot'));
  });
  const slotSel = document.getElementById('target-slot');
  slotSel.disabled = isFont;
  if (!isFont) slotSel.value = String(state.editing.slot);

  // preview-warning
  const warn = document.getElementById('preview-warning');
  const info = assets.manifest?.windows?.[String(state.WindowStyle)];
  if (!info) warn.textContent = '(no screenshot art available)';
  else if (!info.font) warn.textContent = '(using fallback font alpha)';
  else warn.textContent = '';
}

['r','g','b'].forEach((ch, i) => {
  const el = document.getElementById('rgb-' + ch);
  el.addEventListener('input', () => {
    const v = parseInt(el.value, 10);
    document.getElementById('rgb-' + ch + '-val').textContent = v;
    if (state.editing.kind === 'font') state.font[i] = v;
    else state.windows[state.WindowStyle][state.editing.slot - 1][i] = v;
    render();
    updateFlagString();
  });
});

// Target-kind buttons (Font / Window).
document.querySelectorAll('#target-kind .seg-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    if (btn.dataset.kind === 'font') {
      state.editing = { kind: 'font' };
    } else {
      // Default to last-edited slot, or slot 1.
      const slot = state.editing.kind === 'slot' ? state.editing.slot : 1;
      state.editing = { kind: 'slot', slot };
    }
    syncSidePanel();
    render();
  });
});

// Slot picker dropdown.
document.getElementById('target-slot').addEventListener('change', (e) => {
  const slot = parseInt(e.target.value, 10);
  state.editing = { kind: 'slot', slot };
  syncSidePanel();
  render();
});

document.getElementById('reset-color').addEventListener('click', () => {
  if (state.editing.kind === 'font') {
    state.font = [...FONT_DEFAULT];
  } else {
    const s = state.editing.slot;
    state.windows[state.WindowStyle][s - 1] =
      [...WINDOW_DEFAULTS[state.WindowStyle][s - 1]];
  }
  syncSidePanel(); render(); updateFlagString();
});

document.getElementById('reset-all').addEventListener('click', () => {
  Object.assign(state, structuredClone(TOGGLE_DEFAULTS));
  state.font = [...FONT_DEFAULT];
  state.windows = structuredClone(WINDOW_DEFAULTS);
  state.editing = { kind: 'font' };
  state.cursor = 0;
  document.getElementById('window-style').value = '1';
  document.getElementById('wallpaper').value = '1';
  loadWindowAssets(1).then(() => {
    syncSidePanel(); render(); updateFlagString();
  });
});

document.getElementById('window-style').addEventListener('change', (e) => {
  const v = parseInt(e.target.value, 10);
  state.WindowStyle = v;
  loadWindowAssets(v).then(() => {
    syncSidePanel(); render(); updateFlagString();
  });
});

document.getElementById('wallpaper').addEventListener('change', (e) => {
  state.Wallpaper = parseInt(e.target.value, 10);
  updateFlagString();
});

document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    state.page = t.dataset.page;
    state.cursor = 0;
    updateTabUI();
    render();
    syncSidePanel();
  });
});

function updateTabUI() {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.page === state.page);
  });
}

// ---------------- flagstring ----------------

function rgbStr(rgb) {
  return `${rgb[0]},${rgb[1]},${rgb[2]}`;
}

function deepEq(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

function buildFlagString() {
  const args = [];
  if (state.BatMode  !== TOGGLE_DEFAULTS.BatMode)
    args.push(`-b ${state.BatMode}`);
  if (state.BatSpeed !== TOGGLE_DEFAULTS.BatSpeed)
    args.push(`-bs ${state.BatSpeed}`);
  if (state.MsgSpeed !== TOGGLE_DEFAULTS.MsgSpeed)
    args.push(`-ms ${state.MsgSpeed}`);
  if (state.Command  !== TOGGLE_DEFAULTS.Command)
    args.push(`-com ${state.Command}`);
  if (state.Gauge    !== TOGGLE_DEFAULTS.Gauge)
    args.push(`-g ${state.Gauge}`);
  if (state.Sound    !== TOGGLE_DEFAULTS.Sound)
    args.push(`-s ${state.Sound}`);
  if (state.Cursor   !== TOGGLE_DEFAULTS.Cursor)
    args.push(`-c ${state.Cursor}`);
  if (state.Reequip  !== TOGGLE_DEFAULTS.Reequip)
    args.push(`-r ${state.Reequip}`);
  if (state.SpellOrder !== TOGGLE_DEFAULTS.SpellOrder)
    args.push(`-so ${state.SpellOrder}`);
  if (state.Wallpaper !== TOGGLE_DEFAULTS.Wallpaper)
    args.push(`-w ${state.Wallpaper}`);
  if (!deepEq(state.font, FONT_DEFAULT))
    args.push(`-f ${rgbStr(state.font)}`);
  for (let w = 1; w <= 8; w++) {
    const changed = [];
    for (let s = 0; s < 7; s++) {
      if (!deepEq(state.windows[w][s], WINDOW_DEFAULTS[w][s]))
        changed.push(`${s + 1}=${rgbStr(state.windows[w][s])}`);
    }
    if (changed.length) args.push(`-w${w} "${changed.join(';')}"`);
  }
  return args.join(' ');
}

function updateFlagString() {
  document.getElementById('flag-out').value = buildFlagString();
}

document.getElementById('copy-flags').addEventListener('click', async () => {
  const ta = document.getElementById('flag-out');
  try {
    await navigator.clipboard.writeText(ta.value);
  } catch (_) {
    ta.select();
    document.execCommand('copy');
  }
});

// ---------------- boot ----------------

(async function init() {
  try {
    assets.manifest = await loadManifest();
  } catch (e) {
    console.error('Failed to load manifest', e);
    assets.manifest = { windows: {} };
  }
  // Try to preload the default style.
  await loadWindowAssets(state.WindowStyle);
  await loadMagOrderOverlays();
  updateTabUI();
  syncSidePanel();
  render();
  updateFlagString();
  canvas.focus();
})();
