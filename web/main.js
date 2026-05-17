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
  { key: 'BatSpeed', y: 64,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'MsgSpeed', y: 80,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'Command',  y: 96,  values: [['window', 112], ['short', 176]] },
  { key: 'Gauge',    y:112,  values: [['on',     112], ['off',   176]] },
  { key: 'Sound',    y:128,  values: [['stereo', 112], ['mono',  176]] },
  { key: 'Cursor',   y:144,  values: [['reset',  112], ['memory',176]] },
  { key: 'Reequip',  y:160,  values: [['optimum',112], ['empty', 176]] },
];

const PAGE_B_OPTIONS = [
  { key: 'SpellOrder',  y: 44,
    values: [1,2,3,4,5,6].map((v,i)=>[v, 112 + i*16])  },
  { key: 'WindowStyle', y:108,
    values: [1,2,3,4,5,6,7,8].map((v,i)=>[v, 112 + i*16])  },
  // Color row: selects what the R/G/B sliders edit.  "font" sits on the
  // text row at y=128, but the seven slot swatches FF6 draws live one
  // line below in a tighter row of small color blocks.
  { key: 'Color',       y:128, kind: 'color',
    values: [
      ['font', 112, 128],
      ...([1,2,3,4,5,6,7].map((s,i)=>[`slot${s}`, 175 + i*8, 136]))
    ] },
];

// Row labels drawn at the leftmost column when a non-screenshot page is shown.
// (Currently the canvas just shows the actual recolored screenshot so we
//  only rely on the hit positions above for navigation.)

// ---------------- assets ----------------

const assets = {
  manifest: null,
  windowAssets: {},   // {1: {baseline, slot1..7, font, defaultA, defaultB}}
};

async function loadImage(url) {
  const img = new Image();
  img.src = url;
  await img.decode();
  return img;
}

async function loadManifest() {
  const r = await fetch('assets/manifest.json');
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
    promises.push(fetch(base + 'correction.json').then(r => r.json()));
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

  drawCursorOverlay();
  drawSelectionOverlay();
  updateHitTargets();
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
  const cur = currentValueOf(row);
  const i = row.values.findIndex(([v]) => v === cur);
  return i < 0 ? 0 : i;
}

function currentValueOf(row) {
  if (row.kind === 'color') {
    if (state.editing.kind === 'font') return 'font';
    return `slot${state.editing.slot}`;
  }
  return state[row.key];
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
  const v = row.values[activeValueIndex()];
  if (!v) return;
  const { x, y } = valuePos(row, v);
  ctx.save();
  ctx.drawImage(CURSOR_SPRITE, x - 10, y + 1);
  ctx.restore();
}

function drawSelectionOverlay() {
  // Draw a small marker under each row's current value so the user can see
  // every chosen setting at a glance (the cursor only marks the active row).
  const opts = getCurrentOptions();
  ctx.save();
  ctx.fillStyle = 'rgba(255, 240, 120, 0.85)';
  for (const row of opts) {
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
  const opts = getCurrentOptions();
  if (dRow !== 0) {
    state.cursor = (state.cursor + dRow + opts.length) % opts.length;
  }
  if (dCol !== 0) {
    const row = opts[state.cursor];
    const cur = activeValueIndex();
    const next = (cur + dCol + row.values.length) % row.values.length;
    selectValue(row, row.values[next][0]);
    return;
  }
  render();
  syncSidePanel();
}

function selectCurrent() {
  const row = activeRow();
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
  updateTabUI();
  syncSidePanel();
  render();
  updateFlagString();
  canvas.focus();
})();
