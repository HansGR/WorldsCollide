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
  Controller: 'single',
  Wallpaper:  1,
  WindowStyle: 1,   // which Window* palette is "active" for editing/preview
};

// Toggles whose value is a binary string.  Order: [false-mapped, true-mapped]
// where the first label is the default-False display (matches config.py Field
// `default=False`) and the second is default-True.
const BINARY_OPTS = {
  BatMode:    ['active', 'wait'],     // default wait (true)
  Command:    ['window', 'short'],    // default window (false)
  Gauge:      ['on',     'off'],      // default on (false → label "on")
  Sound:      ['stereo', 'mono'],     // default stereo
  Cursor:     ['reset',  'memory'],
  Reequip:    ['optimum','empty'],
  Controller: ['single', 'multiple'], // default single (false), maps to -ctrl
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

// ---------------- integration with the custom-window designer ----------
//
// designer.js shares the same window-style selection and palette state
// as the configurator.  We expose ``state`` (plus a few helpers) on
// window.ff6c and dispatch a single ``ff6c:stateChange`` CustomEvent
// after every state mutation.  The designer listens to the event and
// re-renders or switches windows accordingly.
//
// Helpers go further down once syncSidePanel / render / updateFlagString
// are defined.

if (typeof window !== 'undefined') {
  window.ff6c = window.ff6c || {};
  window.ff6c.state = state;
}

function notifyStateChange(detail) {
  document.dispatchEvent(new CustomEvent('ff6c:stateChange',
                                         { detail: detail || {} }));
}

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
  { key: 'Controller', y:172, values: [['single', 112], ['multiple', 176]] },
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
  const pageA = info.pageA || null;
  // Slot count varies per page in principle; only Page A actually ships
  // its own isolations, so we still index slots 1..7 per page.
  const slotPaths = (suffix, present) => {
    const out = [];
    for (let s = 1; s <= 7; s++) {
      out.push(present && present.includes(s)
        ? loadImage(`${base}slot${s}${suffix}.png`)
        : Promise.resolve(null));
    }
    return out;
  };
  const promises = [
    loadImage(base + 'baseline.png'),
    ...slotPaths('', info.slots),
    info.font ? loadImage(base + 'font.png') : Promise.resolve(null),
    info.hasDefaultA ? loadImage(base + 'defaultA.png') : Promise.resolve(null),
    info.hasDefaultB ? loadImage(base + 'defaultB.png') : Promise.resolve(null),
    info.hasCorrection
      ? fetch(base + 'correction.json' + CB).then(r => r.json())
      : Promise.resolve(null),
    pageA ? loadImage(base + 'baselineA.png') : Promise.resolve(null),
    ...slotPaths('A', pageA ? pageA.slots : null),
    (pageA && pageA.font) ? loadImage(base + 'fontA.png') : Promise.resolve(null),
    (pageA && pageA.hasCorrection)
      ? fetch(base + 'correctionA.json' + CB).then(r => r.json())
      : Promise.resolve(null),
  ];

  const imgs = await Promise.all(promises);
  const a = {
    baseline: imgs[0],
    slots: imgs.slice(1, 8),
    font: imgs[8],
    defaultA: imgs[9],
    defaultB: imgs[10],
    correction: imgs[11],  // (H rows) × [r, g, b] residual to add per pixel.
    baselineA: imgs[12],
    slotsA: imgs.slice(13, 20),
    fontA: imgs[20],
    correctionA: imgs[21],
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
  a.baselineData  = toData(a.baseline);
  a.slotsData     = a.slots.map(toData);
  a.fontData      = toData(a.font);
  a.fontFromFallback = false;
  a.baselineDataA = toData(a.baselineA);
  a.slotsDataA    = a.slotsA.map(toData);
  a.fontDataA     = toData(a.fontA);
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

// Page-switch arrow sprites — static graphics blitted at fixed positions
// after the recolour pass.  Pixel colours extracted from W1_defaultA /
// W1_defaultB at the arrow positions; the bitmap is intentionally not
// re-tinted by the live palette since the in-game arrow is rendered
// from a fixed chrome palette that doesn't follow the user's font/slot
// colours.  The build script erases the underlying arrow out of every
// isolation so the bg behind these sprites is just recoloured chrome
// / wallpaper.
//
// Page A's arrow lives at the bottom (y=205..211, "go down to Page B");
// Page B's at the top (y=28..34, "go up to Page A").  7×13 bounding box
// captures the 5×9 visible triangle plus the SNES halo: a (24,24,41)
// anti-alias outline one cell out from each triangle edge, and a solid
// drop-shadow row on the base side (y=34 for up arrow, y=205 for down).
const ARROW_X0 = 121;
const ARROW_DOWN_Y0 = 205;  // Page A
const ARROW_UP_Y0   = 28;   // Page B
const ARROW_W = 13, ARROW_H = 7;

const ARROW_DOWN_SPRITE = (() => {
  const H = [24,24,41], A = [123,156,156], B = [165,198,198], C = [247,255,255];
  const rows = [
    [H, H, H, H, H, H, H, H, H, H, H, H, H],
    [null, H, A, B, B, B, B, B, B, B, A, H, null],
    [null, null, H, A, B, C, C, C, B, A, H, null, null],
    [null, null, null, H, A, B, C, B, A, H, null, null, null],
    [null, null, null, null, H, A, B, A, H, null, null, null, null],
    [null, null, null, null, null, H, A, H, null, null, null, null, null],
    [null, null, null, null, null, null, H, null, null, null, null, null, null],
  ];
  const c = document.createElement('canvas');
  c.width = ARROW_W; c.height = ARROW_H;
  const cx = c.getContext('2d');
  const im = cx.createImageData(ARROW_W, ARROW_H);
  for (let y = 0; y < ARROW_H; y++) for (let x = 0; x < ARROW_W; x++) {
    const px = rows[y][x];
    const i = (y * ARROW_W + x) * 4;
    if (px) { im.data[i] = px[0]; im.data[i+1] = px[1]; im.data[i+2] = px[2]; im.data[i+3] = 255; }
  }
  cx.putImageData(im, 0, 0);
  return c;
})();

const ARROW_UP_SPRITE = (() => {
  const c = document.createElement('canvas');
  c.width = ARROW_W; c.height = ARROW_H;
  const cx = c.getContext('2d');
  // Vertical flip of the down arrow.
  cx.translate(0, ARROW_H);
  cx.scale(1, -1);
  cx.drawImage(ARROW_DOWN_SPRITE, 0, 0);
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
  //
  // Page A and Page B ship parallel isolation sets (the menu layout
  // changes between pages, so a single set of captures can't drive
  // both).  Pick the matching bundle based on state.page; fall back to
  // Page B's data when Page A's isolations aren't available so older
  // builds keep rendering something.
  if (!asset || !asset.baselineData) return null;
  const useA = state.page === 'A' && asset.baselineDataA;
  const baselineData = useA ? asset.baselineDataA : asset.baselineData;
  const slotsData    = useA ? asset.slotsDataA    : asset.slotsData;
  const fontData     = useA ? asset.fontDataA     : asset.fontData;
  const correction   = useA ? asset.correctionA   : asset.correction;
  const W = 256, H = 224;
  const out = ctx.createImageData(W, H);
  const N = W * H * 4;
  const base = baselineData.data;

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
    if (!slotsData[s]) continue;
    const c = slotColors[s];
    wBaseR -= c[0] / 31; wBaseG -= c[1] / 31; wBaseB -= c[2] / 31;
  }
  if (fontData) {
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
    const sd = slotsData[s];
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
  if (fontData) {
    const c = fontColor;
    const rs = c[0] / 31, gs = c[1] / 31, bs = c[2] / 31;
    const d = fontData.data;
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
  if (correction) {
    const corr = correction;
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

// ---- custom-graphics overlay --------------------------------------
//
// When the user customizes a window in the designer, the configurator's
// menu canvas needs to swap in the user's design where the vanilla
// chrome would otherwise show.  We use a reverse-engineered tilemap
// (web/window_tilemap.js, built by scripts/build_window_tilemap.py from
// the existing slot screenshots) that records, for each 8x8 on-screen
// cell, which of the 4x7 = 28 source tiles the engine places there and
// in what orientation.  Combining that tilemap with the user's custom
// 32x56 pixel grid gives a faithful per-pixel rendering: corners stay
// at corners, edges along edges, interior tiles tile through the
// interior -- exactly the way the SNES draws it.
//
// The tilemap is shared across all 8 window styles (the engine doesn't
// care which source sheet is loaded), and split by page (A vs B) since
// the menu's window dimensions differ.
//
// Pixels that aren't part of the window's chrome (wallpaper, text,
// cursor sprites) fall through to recolor()'s output as before.

function overlayCustomGraphics(imageData, asset) {
  const customWindows = window.__designer && window.__designer.customGraphics;
  const cur = customWindows && customWindows[state.WindowStyle];
  if (!cur || !cur.pixels) return;
  const TM = window.WINDOW_TILEMAP;
  if (!TM) return;
  const page = state.page === 'A' ? TM.A : TM.B;
  if (!page) return;

  const Y_OFFSET = TM.Y_OFFSET || 0;
  const palette = state.windows[state.WindowStyle];   // slots 1..7

  // Per-pixel chrome / font mask -- only paint where the pixel is part
  // of the window's chrome AND not occluded by the font (text/cursor).
  // Cached per asset+page to keep render() fast.
  const mask = getChromeMaskOnly(asset);
  if (!mask) return;

  const W = 256, H = 224;
  const data = imageData.data;
  const tileW = page.width, tileH = page.height;
  const customPixels = cur.pixels;     // Uint8Array, 32x56 source pixels

  for (let ty = 0; ty < tileH; ty++) {
    const cellY = Y_OFFSET + ty * 8;
    for (let tx = 0; tx < tileW; tx++) {
      const cellIdx = ty * tileW + tx;
      if (!page.mapped[cellIdx]) continue;
      const ti = page.tile[cellIdx];
      const fl = page.flip[cellIdx];
      // Source-sheet tile coordinates (4 wide, 7 tall, scan right-then-down)
      const srcTileX = (ti % 4) * 8;
      const srcTileY = ((ti / 4) | 0) * 8;
      const cellX = tx * 8;
      for (let py = 0; py < 8; py++) {
        for (let px = 0; px < 8; px++) {
          const screenY = cellY + py;
          const screenX = cellX + px;
          if (screenY >= H || screenX >= W) continue;
          if (!mask[screenY * W + screenX]) continue;
          // Apply flips when looking up the source pixel.
          const sx = (fl & 1) ? 7 - px : px;
          const sy = (fl & 2) ? 7 - py : py;
          const srcIdx = customPixels[(srcTileY + sy) * 32 + (srcTileX + sx)];
          if (srcIdx === 0) continue;
          const c = palette[srcIdx - 1];
          const off = (screenY * W + screenX) * 4;
          data[off]     = (c[0] << 3) | (c[0] >> 2);
          data[off + 1] = (c[1] << 3) | (c[1] >> 2);
          data[off + 2] = (c[2] << 3) | (c[2] >> 2);
        }
      }
    }
  }
}

// Mask of pixels we're allowed to paint: window-chrome AND not text.
// Window-chrome = some slot screenshot diverges from baseline at this
// pixel (the recolor pipeline's own definition of "this pixel belongs
// to the window").  Text = font screenshot diverges -- those pixels
// should keep the recolored glyph color from recolor().
function getChromeMaskOnly(asset) {
  const useA = state.page === 'A' && asset.baselineDataA;
  const cacheKey = useA ? '_chromeMaskA' : '_chromeMask';
  if (asset[cacheKey]) return asset[cacheKey];
  const baseline = useA ? asset.baselineDataA : asset.baselineData;
  const slots    = useA ? asset.slotsDataA    : asset.slotsData;
  const fontD    = useA ? asset.fontDataA     : asset.fontData;
  if (!baseline || !slots) return null;
  const W = 256, H = 224;
  const mask = new Uint8Array(W * H);
  const base = baseline.data;
  for (let i = 0, p = 0; i < base.length; i += 4, p++) {
    // Chrome iff some slot diverges from baseline by > THRESH.
    let chromeDiff = 0;
    for (let s = 0; s < 7; s++) {
      if (!slots[s]) continue;
      const d = slots[s].data;
      const m = Math.max(
        Math.abs(d[i]     - base[i]),
        Math.abs(d[i + 1] - base[i + 1]),
        Math.abs(d[i + 2] - base[i + 2]));
      if (m > chromeDiff) chromeDiff = m;
    }
    if (chromeDiff <= 6) continue;
    // Exclude font pixels (let recolor's text rendering stand).
    if (fontD) {
      const f = fontD.data;
      const fontDiff = Math.max(
        Math.abs(f[i]     - base[i]),
        Math.abs(f[i + 1] - base[i + 1]),
        Math.abs(f[i + 2] - base[i + 2]));
      if (fontDiff > chromeDiff) continue;
    }
    mask[p] = 1;
  }
  asset[cacheKey] = mask;
  return mask;
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
    if (data) {
      overlayCustomGraphics(data, asset);
      ctx.putImageData(data, 0, 0);
    }

    // If Page A is selected but this window has no Page A isolations,
    // fall back to the flat defaultA screenshot (colours are frozen at
    // the default palette).  Windows that ship pageA assets recolour
    // through the same path as Page B above — no overlay needed.
    if (state.page === 'A' && !asset.baselineDataA && asset.defaultA) {
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
  drawPageSwitchArrow();
  highlightValueText();
  drawCursorOverlay();
  drawSelectionOverlay();
  updateHitTargets();
}

function drawPageSwitchArrow() {
  // Each page draws the indicator that points toward the *other* page —
  // Page A → down arrow at the bottom, Page B → up arrow at the top.
  if (state.page === 'A') ctx.drawImage(ARROW_DOWN_SPRITE, ARROW_X0, ARROW_DOWN_Y0);
  else                    ctx.drawImage(ARROW_UP_SPRITE,   ARROW_X0, ARROW_UP_Y0);
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

  // 2) Stamp text glyphs.  Three passes so the 1-px FF6 drop shadow
  //    comes back AND filled-icon outlines survive:
  //    a) Black pixel one cell down-right of every bright source pixel
  //       (the procedural FF6 drop shadow).
  //    b) Black pixel wherever the source itself is pure black — this
  //       brings back the outline around the filled "black ball" icon
  //       on the Attack row, whose outline is below TEXT_THRESHOLD and
  //       would otherwise be skipped (the procedural shadow only covers
  //       the down-right side of bright pixels, not a full ring).
  //    c) Bright source pixel itself, tinted with the live font palette
  //       so the overlay text matches whatever colour the rest of the
  //       menu's text uses.  The crops were captured under W1's default
  //       (white) font so source[i] is grayscale — scaling by the user's
  //       font colour preserves the per-pixel brightness ramp (the dim
  //       bullet outlines stay dimmer than the bright letter strokes).
  //       Pure black survives as black since md[i] · anything = 0.
  const TEXT_THRESHOLD = 70;
  const DARK_THRESHOLD = 10;
  const fr = state.font[0] * 255 / 31;
  const fg = state.font[1] * 255 / 31;
  const fb = state.font[2] * 255 / 31;
  const region = ctx.getImageData(x0, y0, w, h);
  const rd = region.data, md = img.data;
  const stride = w * 4;
  for (let py = 0; py < h - 1; py++) {
    for (let px = 0; px < w - 1; px++) {
      const i = py * stride + px * 4;
      const mx = Math.max(md[i], md[i + 1], md[i + 2]);
      if (mx > TEXT_THRESHOLD) {
        const sh = i + stride + 4;  // (px+1, py+1)
        rd[sh    ] = 0;
        rd[sh + 1] = 0;
        rd[sh + 2] = 0;
      }
    }
  }
  for (let i = 0; i < rd.length; i += 4) {
    const mx = Math.max(md[i], md[i + 1], md[i + 2]);
    if (mx < DARK_THRESHOLD) {
      rd[i    ] = 0;
      rd[i + 1] = 0;
      rd[i + 2] = 0;
    }
  }
  for (let i = 0; i < rd.length; i += 4) {
    const mx = Math.max(md[i], md[i + 1], md[i + 2]);
    if (mx > TEXT_THRESHOLD) {
      const t = mx / 255;
      rd[i    ] = Math.round(fr * t);
      rd[i + 1] = Math.round(fg * t);
      rd[i + 2] = Math.round(fb * t);
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
  // Page A Controller row: extracted from W1/fontA.png at x=112 / x=176, y=172.
  'single':  { w: 46, h: 8, ipr: 2, rows: [0x7c300000, 0x70000000, 0xc230f87c, 0x30780000, 0xe000cccc, 0x30cc0000, 0x7830cccc, 0x30fc0000, 0x1c30cc7c, 0x30c00000, 0x8e30cc0c, 0x30c40000, 0x7c30cc8c, 0x30780000, 0x00000078, 0x00000000] },
  'multiple':{ w: 62, h: 8, ipr: 2, rows: [0x86007030, 0x30007000, 0xcecc30fc, 0x30f83078, 0xfecc3030, 0x00cc30cc, 0xb6cc3030, 0x30cc30fc, 0x86cc3030, 0x30cc30c0, 0x86cc3030, 0x30f830c4, 0x867c301c, 0x30c03078, 0x00000000, 0x00c00000] },
  // Page B Color row's "Font" word (the existing 'window' mask above
  // works for the same-row "Window" label since the font is uniform).
  'font':    { w: 30, h: 7, ipr: 1, rows: [0xfe000030, 0xc078f8fc, 0xc0cccc30, 0xfccccc30, 0xc0cccc30, 0xc0cccc30, 0xc078cc1c] },
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
  // First pass: 1-px black shadow offset +1, +1 from every set bit.  FF6
  // renders all menu glyphs with this drop shadow; we paint it first and
  // let the glyph itself overpaint the cells where shadow overlaps a
  // neighbouring glyph pixel.
  ctx.fillStyle = '#000000';
  for (let dy = 0; dy < DIGIT_MASK_H; dy++) {
    const py = y + dy - 1;
    if (py + 1 < 0 || py + 1 >= 224) continue;
    const bits = mask[dy];
    if (!bits) continue;
    for (let dx = 0; dx < DIGIT_MASK_W; dx++) {
      const px = x + dx;
      if (px + 1 < 0 || px + 1 >= 256) continue;
      if (bits & (1 << (DIGIT_MASK_W - 1 - dx))) {
        ctx.fillRect(px + 1, py + 1, 1, 1);
      }
    }
  }
  // Second pass: the glyph itself.
  ctx.fillStyle = fillCss;
  for (let dy = 0; dy < DIGIT_MASK_H; dy++) {
    const py = y + dy - 1;
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
  // The bar's interior is 3 px tall.  The build script masks the
  // interior out of the source screenshots (inpainted with wallpaper
  // from 4 tiles to the left), so the recolored composite already
  // shows the wallpaper under the bar — we only need to paint the
  // filled portion on top.  Leaving the empty portion untouched lets
  // the wallpaper texture show through "behind" the bar instead of a
  // solid SNES-rendered colour that tints with the slot palette.
  const fillW = Math.round(value * SLIDER_BAR_W31 / 31);
  if (fillW <= 0) return;
  ctx.fillStyle = fontCss;
  for (let i = 0; i < SLIDER_BAR_FILL_H; i++) {
    ctx.fillRect(SLIDER_BAR_X0, rowY + SLIDER_BAR_Y_OFF + i, fillW, 1);
  }
}

function stampWordHighlight(word, x, y, adjuster, target) {
  const m = WORD_MASKS[word];
  if (!m) return;
  const W = 256, H = 224;
  for (let dy = 0; dy < m.h; dy++) {
    const py = y + dy;
    if (py < 0 || py >= H) continue;
    for (let dx = 0; dx < m.w; dx++) {
      const px = x + dx;
      if (px < 0 || px >= W) continue;
      const intIdx = dx >> 5;
      const bitIdx = 31 - (dx & 31);
      const word32 = m.rows[dy * m.ipr + intIdx];
      if (word32 & (1 << bitIdx)) {
        adjuster((py * W + px) * 4, target);
      }
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

  // Mask-driven highlights use a flat colour stamp: bright pixels get
  // the current font colour exactly (so a purple font reads as purple,
  // not a per-channel rescale of whatever was baked into the screenshot),
  // and dim pixels get neutral grey regardless of font colour. This
  // matches FF6's own menu — the selected option uses the font palette
  // entry, while unselected options use a fixed secondary text colour.
  const BRIGHT_COLOR = [
    Math.round(state.font[0] * 255 / 31),
    Math.round(state.font[1] * 255 / 31),
    Math.round(state.font[2] * 255 / 31),
  ];
  const DIM_COLOR = [DIM_TARGET, DIM_TARGET, DIM_TARGET];

  const adjustPixel = (i, target) => {
    const r = d[i], g = d[i+1], b = d[i+2];
    const m = Math.max(r, g, b);
    if (m <= TEXT_THRESHOLD) return;
    const scale = target / m;
    d[i  ] = Math.min(255, r * scale);
    d[i+1] = Math.min(255, g * scale);
    d[i+2] = Math.min(255, b * scale);
  };

  const stampGlyphPixel = (i, color) => {
    d[i  ] = color[0];
    d[i+1] = color[1];
    d[i+2] = color[2];
  };

  for (const row of opts) {
    if (row.kind === 'slider') continue;
    if (row.kind === 'color') {
      // Color row has two text labels ("Font" / "Window") whose
      // highlighted state tracks state.editing rather than a discrete
      // value in row.values.  Stamp them with the per-word mask.
      const fontBright = state.editing.kind === 'font';
      stampWordHighlight('font',   112, 124, stampGlyphPixel,
                          fontBright ? BRIGHT_COLOR : DIM_COLOR);
      stampWordHighlight('window', 176, 124, stampGlyphPixel,
                          fontBright ? DIM_COLOR : BRIGHT_COLOR);
      continue;
    }
    const cur = currentValueOf(row);
    for (const item of row.values) {
      const [val] = item;
      const { x, y } = valuePos(row, item);
      const target = val === cur ? BRIGHT_TARGET : DIM_TARGET;
      const color  = val === cur ? BRIGHT_COLOR  : DIM_COLOR;

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
              stampGlyphPixel((py * W + px) * 4, color);
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
              stampGlyphPixel((py * W + px) * 4, color);
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
  // Use the exact mask width when we have one (avoids the underline
  // clipping at the 56-px guess for longer words like 'multiple').
  if (typeof v === 'string' && WORD_MASKS[v]) return WORD_MASKS[v].w;
  // ~6px per char roughly
  return Math.min(56, String(v).length * 7 + 4);
}

// ---------------- hit targets / mouse ----------------

function updateHitTargets() {
  hitLayer.innerHTML = '';
  const opts = getCurrentOptions();
  for (let r = 0; r < opts.length; r++) {
    const row = opts[r];
    if (row.kind === 'slider') {
      // Whole bar (outline included, ~70 px wide) is clickable; the click
      // position maps linearly to a [0, 31] value.  Clicking parks the
      // cursor on the row too so keyboard nudges resume from there.
      const el = document.createElement('div');
      el.className = 'hit slider';
      el.style.left   = (SLIDER_BAR_X0 - 4) * 2 + 'px';
      el.style.top    = (row.y + 3) * 2 + 'px';
      el.style.width  = (SLIDER_BAR_W31 + 8) * 2 + 'px';
      el.style.height = 7 * 2 + 'px';
      el.title = `${row.key}: click to set`;
      const setFromEvent = (e) => {
        const rect = el.getBoundingClientRect();
        const xCanvas = (e.clientX - rect.left) / 2 + (SLIDER_BAR_X0 - 4);
        const t = (xCanvas - SLIDER_BAR_X0) / SLIDER_BAR_W31;
        const v = Math.round(Math.max(0, Math.min(1, t)) * 31);
        state.cursor = r;
        setChannel(row.channel, v);
      };
      el.addEventListener('click', setFromEvent);
      hitLayer.appendChild(el);
      continue;
    }
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

  // Page-switch arrow hit target — slightly bigger than the 9×5 sprite so
  // it's easy to click.  Tab key still works via keyHandler.
  const arrow = document.createElement('div');
  arrow.className = 'hit page-switch';
  const ay = state.page === 'A' ? ARROW_DOWN_Y0 : ARROW_UP_Y0;
  arrow.style.left   = (ARROW_X0 - 3) * 2 + 'px';
  arrow.style.top    = (ay - 2) * 2 + 'px';
  arrow.style.width  = (ARROW_W + 6) * 2 + 'px';
  arrow.style.height = (ARROW_H + 4) * 2 + 'px';
  arrow.title = state.page === 'A' ? 'Go to Page B' : 'Go to Page A';
  arrow.addEventListener('click', switchPage);
  hitLayer.appendChild(arrow);
}

function switchPage() {
  state.page = state.page === 'A' ? 'B' : 'A';
  state.cursor = 0;
  updateTabUI();
  render();
  syncSidePanel();
}

function setChannel(ch, value) {
  const rgb = editedRgb();
  rgb[ch] = Math.max(0, Math.min(31, value | 0));
  render();
  syncSidePanel();
  updateFlagString();
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
  notifyStateChange({ kind: 'select', row: row.key, value: val });
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

  // Side-panel selects that mirror state.  Controller can be cycled both
  // from the canvas (PAGE_A_OPTIONS) and the side-panel dropdown, so keep
  // the dropdown synced after every state mutation.
  document.getElementById('controller').value = state.Controller;

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
    notifyStateChange({ kind: 'palette',
                        window: state.editing.kind === 'slot' ? state.WindowStyle : null,
                        slot:   state.editing.kind === 'slot' ? state.editing.slot : null });
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
  notifyStateChange({ kind: 'reset-color' });
});

document.getElementById('reset-all').addEventListener('click', () => {
  Object.assign(state, structuredClone(TOGGLE_DEFAULTS));
  state.font = [...FONT_DEFAULT];
  state.windows = structuredClone(WINDOW_DEFAULTS);
  state.editing = { kind: 'font' };
  state.cursor = 0;
  document.getElementById('window-style').value = '1';
  document.getElementById('wallpaper').value = '1';
  document.getElementById('controller').value = 'single';
  loadWindowAssets(1).then(() => {
    syncSidePanel(); render(); updateFlagString();
    notifyStateChange({ kind: 'reset-all' });
  });
});

document.getElementById('window-style').addEventListener('change', (e) => {
  const v = parseInt(e.target.value, 10);
  state.WindowStyle = v;
  loadWindowAssets(v).then(() => {
    syncSidePanel(); render(); updateFlagString();
    notifyStateChange({ kind: 'windowStyle', value: v });
  });
});

document.getElementById('wallpaper').addEventListener('change', (e) => {
  state.Wallpaper = parseInt(e.target.value, 10);
  updateFlagString();
});

document.getElementById('controller').addEventListener('change', (e) => {
  state.Controller = e.target.value;
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
  if (state.Controller !== TOGGLE_DEFAULTS.Controller)
    args.push(`-ctrl ${state.Controller}`);
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

// ---------------- designer integration helpers ----------------
//
// Called from designer.js when an in-editor action touches multiple
// palette slots at once (a fresh texture quantization, "revert to
// vanilla", etc.).  Doing each write through the existing per-slider
// handler would cause N renders + N flag-string rebuilds for one user
// gesture; this batches them into one.

// ---------------- flagstring parser (for config-JSON upload) ----------
//
// Inverse of buildFlagString(): split a flagstring into tokens, then
// map each `-flag value` pair into ``state``.  Reset to defaults first
// so flags that are *absent* from the upload snap back rather than
// inheriting the previous session's value.
//
// The Python CLI accepts the same arguments and is the source of truth
// for the format; mirror its parsers for the small handful of value
// shapes we have to read (rgb triples, window palettes).

function shlexSplit(s) {
  // Minimal POSIX-ish split: handles single and double quotes and
  // backslash escapes.  buildFlagString only quotes -wN values, so we
  // don't need anything fancier.
  const out = [];
  let cur = '', has = false, sq = false, dq = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (!sq && !dq && /\s/.test(c)) {
      if (has) { out.push(cur); cur = ''; has = false; }
      continue;
    }
    if (!sq && c === '"') { dq = !dq; has = true; continue; }
    if (!dq && c === "'") { sq = !sq; has = true; continue; }
    if (!sq && c === '\\' && i + 1 < s.length) {
      cur += s[++i]; has = true; continue;
    }
    cur += c; has = true;
  }
  if (has) out.push(cur);
  return out;
}

function parseRgbTriple(s) {
  const parts = s.split(',');
  if (parts.length !== 3) throw new Error(`bad rgb triple ${JSON.stringify(s)}`);
  const out = parts.map(p => parseInt(p, 10));
  for (const v of out) {
    if (!Number.isInteger(v) || v < 0 || v > 31)
      throw new Error(`rgb component out of 0..31 in ${JSON.stringify(s)}`);
  }
  return out;
}

const FLAG_MAP = {
  '-b':   { key: 'BatMode'  },
  '-bs':  { key: 'BatSpeed',   int: true },
  '-ms':  { key: 'MsgSpeed',   int: true },
  '-com': { key: 'Command'  },
  '-g':   { key: 'Gauge'    },
  '-s':   { key: 'Sound'    },
  '-c':   { key: 'Cursor'   },
  '-r':   { key: 'Reequip'  },
  '-so':  { key: 'SpellOrder', int: true },
  '-ctrl':{ key: 'Controller'  },
  '-w':   { key: 'Wallpaper',  int: true },
};

function applyFlagString(flags) {
  // Hard reset to defaults so anything missing from the flagstring is
  // restored, not left over from a previous session.
  Object.assign(state, structuredClone(TOGGLE_DEFAULTS));
  state.font = [...FONT_DEFAULT];
  state.windows = structuredClone(WINDOW_DEFAULTS);
  state.editing = { kind: 'font' };
  state.cursor = 0;

  const toks = shlexSplit(flags || '');
  for (let i = 0; i < toks.length; i++) {
    const flag = toks[i];
    const val  = toks[i + 1];
    if (val === undefined) throw new Error(`flag ${flag} missing value`);
    if (FLAG_MAP[flag]) {
      const spec = FLAG_MAP[flag];
      state[spec.key] = spec.int ? parseInt(val, 10) : val;
    } else if (flag === '-f') {
      state.font = parseRgbTriple(val);
    } else if (/^-w[1-8]$/.test(flag)) {
      const n = parseInt(flag.slice(2), 10);
      for (const entry of val.split(';')) {
        if (!entry) continue;
        const eq = entry.indexOf('=');
        if (eq < 0) throw new Error(`bad palette entry ${JSON.stringify(entry)}`);
        const slot = parseInt(entry.slice(0, eq), 10);
        if (!(slot >= 1 && slot <= 7))
          throw new Error(`slot ${slot} out of range in ${flag} ${JSON.stringify(val)}`);
        state.windows[n][slot - 1] = parseRgbTriple(entry.slice(eq + 1));
      }
    } else {
      throw new Error(`unknown flag ${JSON.stringify(flag)}`);
    }
    i++;
  }

  // Sync side panels + canvas to the freshly-loaded state.
  document.getElementById('window-style').value = String(state.WindowStyle);
  document.getElementById('wallpaper').value    = String(state.Wallpaper);
  document.getElementById('controller').value   = state.Controller;
  return loadWindowAssets(state.WindowStyle).then(() => {
    updateTabUI();
    syncSidePanel();
    render();
    updateFlagString();
    notifyStateChange({ kind: 'config-load' });
  });
}

if (typeof window !== 'undefined') {
  window.ff6c.setPaletteBulk = function (windowN, palette7) {
    for (let i = 0; i < 7; i++) {
      state.windows[windowN][i] = palette7[i].slice();
    }
    syncSidePanel(); render(); updateFlagString();
    notifyStateChange({ kind: 'palette-bulk', window: windowN });
  };
  // Used by designer.js to embed the configurator's current flagstring
  // into a single downloadable JSON config.
  window.ff6c.getFlagString = function () {
    return document.getElementById('flag-out').value;
  };
  // Triggered by designer.js whenever the user changes pixels / border /
  // anything else that doesn't go through setPaletteBulk.  Re-renders
  // the menu preview so the custom graphics overlay updates.
  window.ff6c.refresh = function () {
    render();
  };
  window.ff6c.applyFlagString = applyFlagString;
}

// ---------------- boot ----------------

(async function init() {
  try {
    assets.manifest = await loadManifest();
  } catch (e) {
    console.error('Failed to load manifest', e);
    assets.manifest = { windows: {} };
  }
  // Preload the active window first so the initial render isn't blocked
  // on the others, then pull the remaining windows in parallel so cycling
  // through styles never falls back to the "No preview" placeholder.
  await loadWindowAssets(state.WindowStyle);
  const others = Object.keys(assets.manifest.windows || {})
    .map(k => parseInt(k, 10))
    .filter(n => n !== state.WindowStyle);
  Promise.all(others.map(n => loadWindowAssets(n))).catch(e => {
    console.warn('Background preload of window assets failed:', e);
  });
  await loadMagOrderOverlays();
  updateTabUI();
  syncSidePanel();
  render();
  updateFlagString();
  canvas.focus();
})();
