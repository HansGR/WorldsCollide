/* Custom window image designer.
 *
 * Integrated with the flagstring builder above: the active window is
 * whichever one ``state.WindowStyle`` (controlled by the configurator's
 * dropdown / Page B WindowStyle row) is on, and the palette this
 * designer shows for that window is the SAME palette the configurator
 * edits via its R/G/B sliders.  Per-window pixel grids live in
 * ``ds.customGraphics[N]``; switching to a window the user hasn't
 * touched loads its vanilla pixels.
 *
 * Download produces a single ``ff6config.json`` blob containing:
 *   - ``flags``: the configurator's current flagstring (palette/font/
 *     toggle overrides), unchanged from the existing "Copy" button.
 *   - ``graphics``: ``{ N: base64(928 bytes) }`` for every window the
 *     user actually edited.  The CLI applies this via:
 *
 *       python ff6_config.py -i rom.smc --config ff6config.json
 *
 * Per-pixel format: ``ds.pixels`` is a 32x56 Uint8Array of palette
 * indices 0..7.  Index 0 is transparent (always rendered as black on
 * the canvas; never written into ``state.windows``).  Indices 1..7
 * track ``state.windows[currentWindow][0..6]`` exactly.
 */

(function () {
  const enc = window.WGEncoder;            // 4bpp encoder + quantizer
  const ff6c = window.ff6c || (window.ff6c = {});
  const SHARED = ff6c.state;               // configurator's state object

  // ---- shape constants -----------------------------------------------
  const TEX_W = 32, TEX_H = 32;
  const BORDER_W = 32, BORDER_H = 24;
  const SHEET_W = enc.SHEET_W, SHEET_H = enc.SHEET_H;
  const NUM_PALETTE_SLOTS = 8;     // index 0 (transparent) + slots 1..7
  const SCALE = 8;
  const BLOB_BYTES = enc.BLOB_BYTES;

  // ---- per-window state ---------------------------------------------

  const ds = {
    pixels: new Uint8Array(SHEET_W * SHEET_H),
    currentWindow: SHARED.WindowStyle || 1,
    borderId: '__current__',          // synthetic "what's already there" entry
    selectedIndex: 1,
    tool: 'paint',                    // 'paint' | 'fill'
    brushSize: 1,                     // 1, 2, 4, 8 (pixels per side)
    brushShape: 'square',             // 'square' | 'circle'
    isPainting: false,
    lastTexUpload: null,              // for "Re-quantize" -- per-window
    // For each window the user has touched, store a snapshot so cycling
    // away and back preserves the design.  Entries:
    //   N -> { pixels: Uint8Array, borderId: string, lastTexUpload: ImageData|null }
    customGraphics: {},
  };

  // Mark the current window as customized.  Called from any edit path.
  function markCustomized() {
    if (!ds.customGraphics[ds.currentWindow]) {
      ds.customGraphics[ds.currentWindow] = {};
    }
    snapshotCurrent();   // keep the cache in sync with ds.pixels
    updateWindowBanner();
    // The configurator's menu preview reads from
    // window.__designer.customGraphics, so prod it to re-render.
    ff6c.refresh && ff6c.refresh();
  }

  function snapshotCurrent() {
    if (!ds.customGraphics[ds.currentWindow]) return;
    ds.customGraphics[ds.currentWindow].pixels = ds.pixels.slice();
    ds.customGraphics[ds.currentWindow].borderId = ds.borderId;
    ds.customGraphics[ds.currentWindow].lastTexUpload = ds.lastTexUpload;
  }

  function loadWindow(n) {
    if (ds.currentWindow === n) return;
    snapshotCurrent();
    ds.currentWindow = n;
    const cached = ds.customGraphics[n];
    if (cached && cached.pixels) {
      ds.pixels = new Uint8Array(cached.pixels);
      ds.borderId = cached.borderId || '__current__';
      ds.lastTexUpload = cached.lastTexUpload || null;
    } else {
      // Load vanilla pixels for this window; palette is already in
      // SHARED.windows[n] (or has been edited there by the configurator).
      const v = window.VANILLA_GRAPHICS && window.VANILLA_GRAPHICS[n];
      if (v) {
        ds.pixels = new Uint8Array(v.pixels);
      } else {
        ds.pixels = new Uint8Array(SHEET_W * SHEET_H);
      }
      ds.borderId = '__current__';
      ds.lastTexUpload = null;
    }
    updateWindowBanner();
    render();
    // Configurator's overlay reads customGraphics[currentWindow], so
    // tell it to redraw with the right window's data.
    ff6c.refresh && ff6c.refresh();
  }

  function revertCurrentToDefault() {
    delete ds.customGraphics[ds.currentWindow];
    ds.lastTexUpload = null;
    // Restore the vanilla palette through the configurator so its
    // sliders + flagstring update too.
    const v = window.VANILLA_GRAPHICS && window.VANILLA_GRAPHICS[ds.currentWindow];
    if (v) {
      ds.pixels = new Uint8Array(v.pixels);
      // VANILLA_GRAPHICS[n].palette has 8 entries; slots 1..7 go to
      // the configurator (which stores 7 entries per window).  This
      // call already triggers an ff6c:stateChange + main.js render, so
      // the menu preview drops back to the vanilla appearance.
      ff6c.setPaletteBulk(ds.currentWindow, v.palette.slice(1, 8));
    } else {
      ds.pixels = new Uint8Array(SHEET_W * SHEET_H);
      ff6c.refresh && ff6c.refresh();
    }
    ds.borderId = '__current__';
    updateWindowBanner();
    render();
  }

  // ---- palette read/write through SHARED.windows --------------------

  function getColor(slot) {
    if (slot === 0) return [0, 0, 0];
    // slot 1..7 -> SHARED.windows[N][0..6]
    return SHARED.windows[ds.currentWindow][slot - 1];
  }

  function setColor(slot, rgb) {
    if (slot === 0) return;
    SHARED.windows[ds.currentWindow][slot - 1] = rgb.slice();
    // Notify the configurator to re-render its preview + flagstring.
    document.dispatchEvent(new CustomEvent('ff6c:stateChange',
      { detail: { kind: 'palette-from-designer',
                  window: ds.currentWindow, slot } }));
  }

  // ---- helpers ------------------------------------------------------

  function idx(x, y) { return y * SHEET_W + x; }
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  const lumin = enc.lumin;
  const bgr5_to_rgb8 = enc.bgr5_to_rgb8;
  const rgb8_to_bgr5 = enc.rgb8_to_bgr5;

  function applyBorderPixels(borderPx) {
    for (let y = 0; y < BORDER_H; y++) {
      for (let x = 0; x < BORDER_W; x++) {
        ds.pixels[idx(x, TEX_H + y)] = borderPx[y * BORDER_W + x];
      }
    }
  }
  function applyTexturePixels(texPx) {
    for (let y = 0; y < TEX_H; y++) {
      for (let x = 0; x < TEX_W; x++) {
        ds.pixels[idx(x, y)] = texPx[y * TEX_W + x];
      }
    }
  }

  // ---- image -> quantized texture / border --------------------------

  function loadImageToCanvas(file, w, h) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas');
        c.width = w; c.height = h;
        const ctx = c.getContext('2d');
        const srcAspect = img.width / img.height;
        const dstAspect = w / h;
        let sx, sy, sw, sh;
        if (srcAspect > dstAspect) {
          sh = img.height; sw = sh * dstAspect;
          sx = (img.width - sw) / 2; sy = 0;
        } else {
          sw = img.width; sh = sw / dstAspect;
          sx = 0; sy = (img.height - sh) / 2;
        }
        ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
        resolve(ctx.getImageData(0, 0, w, h));
      };
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  }

  function imageDataToRGB(imgData) {
    const out = new Array(imgData.width * imgData.height);
    const d = imgData.data;
    for (let i = 0, j = 0; i < d.length; i += 4, j++) {
      out[j] = [d[i], d[i + 1], d[i + 2]];
    }
    return out;
  }

  function quantizeTexture(rgbPixels) {
    const { palette, indices } = enc.medianCut(rgbPixels, 7);
    const sorted = enc.sortByLuminosity(palette, indices);
    const shifted = sorted.indices.map(i => i + 1);
    const snapped = sorted.palette.map(c => [
      rgb8_to_bgr5(c[0]), rgb8_to_bgr5(c[1]), rgb8_to_bgr5(c[2]),
    ]);
    return { palette: snapped, indices: shifted };
  }

  // 32x24 border quantizer -- 7 equal-population luminosity bins, plus
  // index 0 for pixels darker than TRANSPARENT_CUTOFF.
  function quantizeBorder(rgbPixels) {
    const TRANSPARENT_CUTOFF = 24;
    const visibleLums = [];
    for (const p of rgbPixels) {
      const L = lumin(p);
      if (L >= TRANSPARENT_CUTOFF) visibleLums.push(L);
    }
    visibleLums.sort((a, b) => b - a);
    const cuts = [];
    for (let k = 1; k < 7; k++) {
      cuts.push(visibleLums[Math.floor(k * visibleLums.length / 7)] || 0);
    }
    const out = new Uint8Array(rgbPixels.length);
    for (let i = 0; i < rgbPixels.length; i++) {
      const L = lumin(rgbPixels[i]);
      if (L < TRANSPARENT_CUTOFF) { out[i] = 0; continue; }
      let bin = 0;
      while (bin < 6 && L < cuts[bin]) bin++;
      out[i] = bin + 1;
    }
    return out;
  }

  // ---- rendering -----------------------------------------------------

  const canvas = document.getElementById('ds-sheet');
  const ctx = canvas.getContext('2d');

  function paletteRGB8(index) {
    const c = getColor(index);
    return [bgr5_to_rgb8(c[0]), bgr5_to_rgb8(c[1]), bgr5_to_rgb8(c[2])];
  }

  function render() {
    const im = ctx.createImageData(SHEET_W * SCALE, SHEET_H * SCALE);
    const w = im.width;
    for (let y = 0; y < SHEET_H; y++) {
      for (let x = 0; x < SHEET_W; x++) {
        const v = ds.pixels[idx(x, y)];
        let rgb;
        if (v === 0) {
          rgb = ((Math.floor(x / 2) + Math.floor(y / 2)) & 1) ? [60, 60, 70] : [40, 40, 50];
        } else {
          rgb = paletteRGB8(v);
        }
        for (let dy = 0; dy < SCALE; dy++) {
          for (let dx = 0; dx < SCALE; dx++) {
            const px = ((y * SCALE + dy) * w + (x * SCALE + dx)) * 4;
            im.data[px]     = rgb[0];
            im.data[px + 1] = rgb[1];
            im.data[px + 2] = rgb[2];
            im.data[px + 3] = 255;
          }
        }
      }
    }
    ctx.putImageData(im, 0, 0);
    ctx.fillStyle = 'rgba(255,255,255,0.18)';
    ctx.fillRect(0, TEX_H * SCALE, SHEET_W * SCALE, 1);
    renderSwatches();
    syncRgbSliders();
  }

  // ---- palette swatch UI --------------------------------------------

  const swatchHost = document.getElementById('ds-swatches');

  function renderSwatches() {
    swatchHost.innerHTML = '';
    for (let i = 0; i < NUM_PALETTE_SLOTS; i++) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'swatch' + (i === ds.selectedIndex ? ' active' : '');
      btn.dataset.index = i;
      const [r, g, b] = paletteRGB8(i);
      if (i === 0) {
        btn.style.background =
          'repeating-conic-gradient(#555 0 25%, #333 0 50%) 0/12px 12px';
        btn.title = 'index 0 -- transparent';
      } else {
        btn.style.background = `rgb(${r},${g},${b})`;
        const c = getColor(i);
        btn.title = `index ${i} -- rgb(${c.join(', ')})`;
      }
      btn.textContent = String(i);
      btn.addEventListener('click', () => {
        ds.selectedIndex = i;
        renderSwatches();
        syncRgbSliders();
      });
      swatchHost.appendChild(btn);
    }
  }

  // ---- R/G/B sliders -------------------------------------------------

  const rgbInputs = ['r', 'g', 'b'].map(c => document.getElementById('ds-' + c));
  const rgbLabels = ['r', 'g', 'b'].map(c => document.getElementById('ds-' + c + '-val'));

  function syncRgbSliders() {
    const c = getColor(ds.selectedIndex);
    for (let i = 0; i < 3; i++) {
      rgbInputs[i].value = c[i];
      rgbLabels[i].textContent = c[i];
      rgbInputs[i].disabled = (ds.selectedIndex === 0);
    }
  }

  rgbInputs.forEach((input, i) => {
    input.addEventListener('input', () => {
      if (ds.selectedIndex === 0) return;
      const v = clamp(parseInt(input.value, 10), 0, 31);
      const cur = getColor(ds.selectedIndex).slice();
      cur[i] = v;
      setColor(ds.selectedIndex, cur);
      rgbLabels[i].textContent = String(v);
      markCustomized();
      render();
    });
  });

  // ---- paint interaction ---------------------------------------------

  function canvasToPixel(evt) {
    const rect = canvas.getBoundingClientRect();
    const cssX = evt.clientX - rect.left;
    const cssY = evt.clientY - rect.top;
    const x = Math.floor(cssX * (SHEET_W * SCALE) / rect.width / SCALE);
    const y = Math.floor(cssY * (SHEET_H * SCALE) / rect.height / SCALE);
    if (x < 0 || x >= SHEET_W || y < 0 || y >= SHEET_H) return null;
    return { x, y };
  }

  // Stamp the current brush (size + shape) centred on pixel (cx, cy).
  function stampBrush(cx, cy) {
    const s = ds.brushSize;
    if (s <= 1) {
      if (cx >= 0 && cx < SHEET_W && cy >= 0 && cy < SHEET_H)
        ds.pixels[idx(cx, cy)] = ds.selectedIndex;
      return;
    }
    // Top-left of the brush square, roughly centred on the cursor pixel.
    const off = Math.floor((s - 1) / 2);
    const x0 = cx - off, y0 = cy - off;
    const r = s / 2;
    const bcx = x0 + r, bcy = y0 + r;   // brush centre in pixel-space
    for (let dy = 0; dy < s; dy++) {
      for (let dx = 0; dx < s; dx++) {
        const px = x0 + dx, py = y0 + dy;
        if (px < 0 || px >= SHEET_W || py < 0 || py >= SHEET_H) continue;
        if (ds.brushShape === 'circle') {
          const ex = (px + 0.5) - bcx, ey = (py + 0.5) - bcy;
          if (ex * ex + ey * ey > r * r) continue;
        }
        ds.pixels[idx(px, py)] = ds.selectedIndex;
      }
    }
  }

  function paintLine(a, b) {
    let x0 = a.x, y0 = a.y, x1 = b.x, y1 = b.y;
    const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx - dy;
    while (true) {
      stampBrush(x0, y0);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 > -dy) { err -= dy; x0 += sx; }
      if (e2 < dx)  { err += dx; y0 += sy; }
    }
  }

  // 4-connected flood fill seeded at (sx, sy).  Constrained to the region
  // the seed lives in (texture: y<32, border: y>=32) so a fill never bleeds
  // across the divider between the two areas.
  function floodFill(sx, sy) {
    const target = ds.pixels[idx(sx, sy)];
    const repl = ds.selectedIndex;
    if (target === repl) return;
    const yLo = sy < TEX_H ? 0 : TEX_H;
    const yHi = sy < TEX_H ? TEX_H : SHEET_H;
    const stack = [sx, sy];
    while (stack.length) {
      const y = stack.pop(), x = stack.pop();
      if (x < 0 || x >= SHEET_W || y < yLo || y >= yHi) continue;
      if (ds.pixels[idx(x, y)] !== target) continue;
      ds.pixels[idx(x, y)] = repl;
      stack.push(x + 1, y, x - 1, y, x, y + 1, x, y - 1);
    }
  }

  let lastPaintPx = null;
  canvas.addEventListener('mousedown', (e) => {
    const p = canvasToPixel(e);
    if (!p) return;
    e.preventDefault();
    if (ds.tool === 'fill') {
      floodFill(p.x, p.y);
      markCustomized();
      render();
      return;
    }
    ds.isPainting = true;
    lastPaintPx = p;
    stampBrush(p.x, p.y);
    markCustomized();
    render();
  });
  canvas.addEventListener('mousemove', (e) => {
    if (!ds.isPainting) return;
    const p = canvasToPixel(e);
    if (!p) return;
    if (lastPaintPx) paintLine(lastPaintPx, p);
    else stampBrush(p.x, p.y);
    lastPaintPx = p;
    render();
  });
  const endPaint = () => {
    if (ds.isPainting) { ds.isPainting = false; snapshotCurrent(); }
    lastPaintPx = null;
  };
  canvas.addEventListener('mouseup', endPaint);
  canvas.addEventListener('mouseleave', endPaint);
  window.addEventListener('mouseup', endPaint);

  // ---- tool / brush selectors ----------------------------------------

  // Wire a segmented button group: clicking a button marks it active and
  // calls onPick with its data-* value.
  function wireSegGroup(hostId, dataAttr, onPick) {
    const host = document.getElementById(hostId);
    if (!host) return;
    host.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-' + dataAttr + ']');
      if (!btn || !host.contains(btn)) return;
      for (const b of host.querySelectorAll('button')) b.classList.remove('active');
      btn.classList.add('active');
      onPick(btn.dataset[dataAttr]);
    });
  }

  // Brush size/shape only apply to the brush; grey them out under Fill.
  function syncToolUi() {
    const fill = ds.tool === 'fill';
    for (const id of ['ds-brush-row', 'ds-shape-row']) {
      const row = document.getElementById(id);
      if (row) row.classList.toggle('disabled', fill);
    }
    canvas.style.cursor = fill ? 'cell' : 'crosshair';
  }

  wireSegGroup('ds-tool', 'tool', (v) => { ds.tool = v; syncToolUi(); });
  wireSegGroup('ds-brush-size', 'size', (v) => { ds.brushSize = parseInt(v, 10); });
  wireSegGroup('ds-brush-shape', 'shape', (v) => { ds.brushShape = v; });
  syncToolUi();

  // ---- border preset / upload ----------------------------------------

  const borderSelect = document.getElementById('ds-border-preset');

  function populateBorderOptions() {
    if (!window.BORDER_PRESETS) return;
    borderSelect.innerHTML = '';
    // Synthetic "current" entry: keep whatever is in the bottom of
    // ds.pixels right now (vanilla on first load, or whatever the user
    // painted later).  Lets the user upload only a texture without
    // disturbing the existing border.
    const cur = document.createElement('option');
    cur.value = '__current__';
    cur.textContent = '(keep current)';
    borderSelect.appendChild(cur);
    const order = window.BORDER_PRESETS_ORDER || Object.keys(window.BORDER_PRESETS);
    for (const key of order) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = window.BORDER_PRESETS[key].name;
      borderSelect.appendChild(opt);
    }
    borderSelect.value = ds.borderId;
  }

  borderSelect.addEventListener('change', () => {
    ds.borderId = borderSelect.value;
    const preset = window.BORDER_PRESETS && window.BORDER_PRESETS[ds.borderId];
    if (preset) {
      applyBorderPixels(preset.pixels);
      markCustomized();
      render();
    }
  });

  document.getElementById('ds-border-upload').addEventListener('change', async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try {
      const imgData = await loadImageToCanvas(f, BORDER_W, BORDER_H);
      const px = quantizeBorder(imageDataToRGB(imgData));
      applyBorderPixels(px);
      let opt = [...borderSelect.options].find(o => o.value === '__upload__');
      if (!opt) {
        opt = document.createElement('option');
        opt.value = '__upload__';
        opt.textContent = 'Custom upload';
        borderSelect.appendChild(opt);
      }
      borderSelect.value = '__upload__';
      ds.borderId = '__upload__';
      markCustomized();
      render();
    } catch (err) {
      setStatus('border upload failed: ' + err.message, true);
    }
  });

  // ---- texture upload ------------------------------------------------

  document.getElementById('ds-tex-upload').addEventListener('change', async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try {
      const imgData = await loadImageToCanvas(f, TEX_W, TEX_H);
      ds.lastTexUpload = imgData;
      requantizeTexture();
    } catch (err) {
      setStatus('texture upload failed: ' + err.message, true);
    }
  });

  document.getElementById('ds-tex-revert').addEventListener('click', () => {
    if (!ds.lastTexUpload) {
      setStatus('upload a texture first', true);
      return;
    }
    requantizeTexture();
  });

  function requantizeTexture() {
    const rgb = imageDataToRGB(ds.lastTexUpload);
    const { palette, indices } = quantizeTexture(rgb);
    // Push palette to shared state in one batch so the configurator
    // doesn't render 7 times.
    ff6c.setPaletteBulk(ds.currentWindow, palette);
    applyTexturePixels(indices);
    markCustomized();
    setStatus('texture re-quantized from upload', false);
    render();
  }

  // ---- bitmap export / import (32x56 sheet) --------------------------
  //
  // A round-trip path parallel to the "interpret any image" texture upload:
  // export writes the current sheet exactly, and import reads back a 32x56
  // bitmap pixel-for-pixel.  Index 0 (transparent) uses a magenta sentinel
  // so the editor shows it as a real, distinct colour.

  const MAGENTA = [255, 0, 255];
  function isMagenta(c) { return c[0] === 255 && c[1] === 0 && c[2] === 255; }
  function colorKey(c) { return (c[0] << 16) | (c[1] << 8) | c[2]; }

  // 8 RGB8 entries indexed by pixel value; slot 0 -> magenta sentinel.
  function sheetPaletteRGB8() {
    const pal = [MAGENTA.slice()];
    for (let s = 1; s < NUM_PALETTE_SLOTS; s++) pal.push(paletteRGB8(s));
    return pal;
  }

  document.getElementById('ds-bmp-export').addEventListener('click', () => {
    const bmp = enc.encodeBMP(ds.pixels, sheetPaletteRGB8());
    const file = new Blob([bmp], { type: 'image/bmp' });
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ff6window${ds.currentWindow}.bmp`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setStatus(`exported window ${ds.currentWindow} as a ${SHEET_W}x${SHEET_H} .bmp`, false);
  });

  document.getElementById('ds-bmp-import').addEventListener('change', async (e) => {
    const input = e.target;
    const f = input.files && input.files[0];
    if (!f) return;
    try {
      const decoded = enc.decodeBMP(await f.arrayBuffer());
      if (decoded.width !== SHEET_W || decoded.height !== SHEET_H)
        throw new Error(
          `image is ${decoded.width}x${decoded.height}; need ${SHEET_W}x${SHEET_H}. ` +
          `Use the texture upload to auto-fit other sizes.`);

      // Collect distinct, non-transparent colours (first-seen order).
      const seen = new Map();   // colorKey -> [r,g,b]
      for (const c of decoded.pixels) {
        if (isMagenta(c)) continue;
        const k = colorKey(c);
        if (!seen.has(k)) seen.set(k, c);
      }
      const maxColors = NUM_PALETTE_SLOTS - 1;   // 7 visible slots
      if (seen.size > maxColors)
        throw new Error(
          `image has ${seen.size} colors; bitmap import supports at most ` +
          `${maxColors} plus magenta transparency. ` +
          `Use the texture upload to auto-quantize instead.`);

      // Assign slots 1..7 light-to-dark, matching the quantiser's ordering.
      const colors = [...seen.values()].sort((a, b) => lumin(b) - lumin(a));
      const slotOf = new Map();
      colors.forEach((c, i) => slotOf.set(colorKey(c), i + 1));

      // Update slots 1..7.  rgb8 -> bgr5 is exact for colours that came from
      // our own export; external colours snap to the nearest SNES value.
      // Pad untouched slots with their current palette so nothing is lost.
      const cur = SHARED.windows[ds.currentWindow];
      const pal7 = [];
      for (let i = 0; i < 7; i++) {
        pal7.push(i < colors.length
          ? [rgb8_to_bgr5(colors[i][0]), rgb8_to_bgr5(colors[i][1]), rgb8_to_bgr5(colors[i][2])]
          : cur[i].slice());
      }
      ff6c.setPaletteBulk(ds.currentWindow, pal7);

      // Map every pixel to its slot (magenta -> 0).
      const px = new Uint8Array(SHEET_W * SHEET_H);
      for (let i = 0; i < decoded.pixels.length; i++) {
        const c = decoded.pixels[i];
        px[i] = isMagenta(c) ? 0 : slotOf.get(colorKey(c));
      }
      ds.pixels = px;
      ds.lastTexUpload = null;
      ds.borderId = '__current__';
      markCustomized();
      render();
      setStatus(
        `imported ${f.name} (${seen.size} color` + (seen.size === 1 ? '' : 's') +
        ') pixel-exact', false);
    } catch (err) {
      setStatus('bitmap import failed: ' + err.message, true);
    } finally {
      input.value = '';   // let the same file re-trigger "change"
    }
  });

  // ---- window banner + revert ----------------------------------------

  const banner = document.getElementById('ds-window-banner');
  const revertBtn = document.getElementById('ds-revert');

  function updateWindowBanner() {
    const n = ds.currentWindow;
    const customized = !!(ds.customGraphics[n] && ds.customGraphics[n].pixels);
    banner.textContent =
      `Editing window ${n} ` + (customized ? '(customized)' : '(default)');
    banner.classList.toggle('customized', customized);
    revertBtn.disabled = !customized;
  }

  revertBtn.addEventListener('click', () => {
    revertCurrentToDefault();
    setStatus(`window ${ds.currentWindow} reverted to default`, false);
  });

  // ---- download (unified config JSON) --------------------------------

  // Build the unified { version, flags, graphics } config object from the
  // current designer + configurator state.  Shared by the JSON download and
  // the "patch a ROM" upload so the two can never drift apart.
  function buildConfigObject() {
    snapshotCurrent();
    const graphics = {};
    for (const [nStr, c] of Object.entries(ds.customGraphics)) {
      if (!c.pixels) continue;
      const gfx = enc.encodeSheet(c.pixels);
      // Palette comes from SHARED.windows -- single source of truth.
      const pal8 = [[0, 0, 0], ...SHARED.windows[parseInt(nStr, 10)]];
      const palBytes = enc.encodePalette(pal8);
      const all = new Uint8Array(BLOB_BYTES);
      all.set(gfx, 0);
      all.set(palBytes, enc.SHEET_BYTES);
      let bin = '';
      for (const b of all) bin += String.fromCharCode(b);
      graphics[nStr] = btoa(bin);
    }
    return {
      version: 1,
      flags: (ff6c.getFlagString && ff6c.getFlagString()) || '',
      graphics,
    };
  }

  document.getElementById('ds-download').addEventListener('click', () => {
    const cfg = buildConfigObject();
    const json = JSON.stringify(cfg, null, 2);
    const file = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ff6config.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    const customCount = Object.keys(cfg.graphics).length;
    setStatus(
      `downloaded ff6config.json (${customCount} custom window` +
      (customCount === 1 ? '' : 's') + ') -- apply with ' +
      '`ff6_config.py -i rom.smc --config ff6config.json`', false);
  });

  // ---- patch a ROM on the server (upload -> patch -> download) -------
  //
  // POSTs the uploaded ROM + the current config to the /api/patch function,
  // which patches it in memory and streams the result straight back.  The
  // ROM is never stored server-side.
  const romInput = document.getElementById('ds-rom-upload');
  const patchBtn = document.getElementById('ds-rom-patch');
  if (romInput && patchBtn) {
    patchBtn.addEventListener('click', async () => {
      const f = romInput.files && romInput.files[0];
      if (!f) {
        setStatus('choose a ROM (.smc / .sfc) to patch first', true);
        return;
      }
      const cfg = buildConfigObject();
      patchBtn.disabled = true;
      setStatus(`patching ${f.name}…`, false);
      try {
        const form = new FormData();
        form.append('rom', f, f.name);
        form.append('config', JSON.stringify(cfg));
        form.append('filename', f.name);

        const resp = await fetch('/api/patch', { method: 'POST', body: form });
        if (!resp.ok) {
          const msg = (await resp.text().catch(() => '')).trim();
          throw new Error(msg || `HTTP ${resp.status} ${resp.statusText}`);
        }

        const blob = await resp.blob();
        // Prefer the server's suggested filename; fall back locally.
        let name = (f.name || 'ff6').replace(/\.(smc|sfc)$/i, '') + '_config.smc';
        const cd = resp.headers.get('Content-Disposition') || '';
        const m = cd.match(/filename="([^"]+)"/);
        if (m) name = m[1];

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);

        const customCount = Object.keys(cfg.graphics).length;
        setStatus(
          `patched ${f.name} → ${name} (${customCount} custom window` +
          (customCount === 1 ? '' : 's') + ')', false);
      } catch (err) {
        setStatus('patch failed: ' + err.message, true);
      } finally {
        patchBtn.disabled = false;
      }
    });
  }

  // ---- upload (restore from previously downloaded JSON) -------------

  document.getElementById('ds-config-upload').addEventListener('change', async (e) => {
    const input = e.target;
    const f = input.files && input.files[0];
    if (!f) return;
    try {
      const text = await f.text();
      let cfg;
      try { cfg = JSON.parse(text); }
      catch (err) { throw new Error('not valid JSON: ' + err.message); }
      if (cfg.version !== 1)
        throw new Error(`unsupported config version: ${cfg.version}`);

      // Decode graphics first so we can fail before mutating state if any
      // blob is malformed.  Each entry: { n, pixels, palette }.
      const decoded = [];
      const graphics = cfg.graphics || {};
      for (const [nStr, b64] of Object.entries(graphics)) {
        const n = parseInt(nStr, 10);
        if (!(n >= 1 && n <= 8))
          throw new Error(`bad window number ${JSON.stringify(nStr)}`);
        if (typeof b64 !== 'string')
          throw new Error(`window ${n} blob is not a string`);
        let bin;
        try { bin = atob(b64); }
        catch (err) { throw new Error(`window ${n}: bad base64`); }
        if (bin.length !== BLOB_BYTES)
          throw new Error(`window ${n} blob is ${bin.length} bytes, ` +
                          `expected ${BLOB_BYTES}`);
        const blob = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) blob[i] = bin.charCodeAt(i);
        const pixels  = enc.decodeSheet(blob.subarray(0, enc.SHEET_BYTES));
        const palette = enc.decodePalette(blob.subarray(enc.SHEET_BYTES));
        decoded.push({ n, pixels, palette });
      }
      decoded.sort((a, b) => a.n - b.n);

      // Push the flagstring through the configurator -- this resets every
      // toggle, font color, and window palette to either the embedded value
      // or its default (so a flag that's absent snaps back instead of
      // inheriting the previous session's value).
      await ff6c.applyFlagString(cfg.flags || '');

      // Replace customGraphics from scratch.  The flagstring already wrote
      // each window's palette into SHARED.windows, but the graphics blob
      // carries the palette too and we treat that as authoritative for the
      // saved design (in practice they always match, since the download
      // side reads them from the same source).
      ds.customGraphics = {};
      ds.lastTexUpload = null;
      for (const { n, pixels, palette } of decoded) {
        ff6c.setPaletteBulk(n, palette.slice(1, 8));
        ds.customGraphics[n] = {
          pixels: new Uint8Array(pixels),
          borderId: '__current__',
          lastTexUpload: null,
        };
      }

      // Snap the designer's view to the first customized window so the
      // user lands on something visible instead of an untouched window.
      const target = decoded.length ? decoded[0].n : ds.currentWindow;
      ds.currentWindow = target;
      if (SHARED.WindowStyle !== target && ff6c.setWindowStyle) {
        ff6c.setWindowStyle(target);
      }
      const cur = ds.customGraphics[target];
      if (cur && cur.pixels) {
        ds.pixels = new Uint8Array(cur.pixels);
        ds.borderId = cur.borderId;
      } else {
        const v = window.VANILLA_GRAPHICS && window.VANILLA_GRAPHICS[target];
        ds.pixels = v ? new Uint8Array(v.pixels) : new Uint8Array(SHEET_W * SHEET_H);
        ds.borderId = '__current__';
      }
      updateWindowBanner();
      render();
      ff6c.refresh && ff6c.refresh();

      const n = decoded.length;
      setStatus(`loaded ${f.name} (${n} custom window` +
                (n === 1 ? '' : 's') + ')', false);
    } catch (err) {
      setStatus('config upload failed: ' + err.message, true);
    } finally {
      // Reset so picking the same file again still fires "change".
      input.value = '';
    }
  });

  // ---- status line ---------------------------------------------------

  const statusEl = document.getElementById('ds-status');
  function setStatus(text, isError) {
    statusEl.textContent = text;
    statusEl.classList.toggle('error', !!isError);
  }

  // ---- configurator -> designer sync --------------------------------

  document.addEventListener('ff6c:stateChange', (e) => {
    const detail = (e && e.detail) || {};
    if (detail.kind === 'reset-all') {
      // The user hit "Reset everything to defaults" in the configurator.
      // Drop every custom-graphics entry so the configurator's window
      // styles snap back to vanilla too.
      ds.customGraphics = {};
      ds.lastTexUpload = null;
      const v = window.VANILLA_GRAPHICS && window.VANILLA_GRAPHICS[SHARED.WindowStyle];
      if (v) ds.pixels = new Uint8Array(v.pixels);
      ds.currentWindow = SHARED.WindowStyle;
      ds.borderId = '__current__';
      updateWindowBanner();
      render();
      return;
    }
    const newWindow = SHARED.WindowStyle;
    if (newWindow !== ds.currentWindow) {
      loadWindow(newWindow);   // re-renders inside
    } else {
      // A configurator palette edit aimed at a specific slot: mirror the
      // selection so this designer's swatch + R/G/B sliders track the same
      // color instead of drifting out of sync.  (font edits send no slot.)
      if (detail.slot >= 1 && detail.slot <= 7) ds.selectedIndex = detail.slot;
      render();   // re-reads SHARED.windows for the canvas image + sliders
    }
  });

  // ---- init ----------------------------------------------------------

  populateBorderOptions();
  // Initial load: whatever WindowStyle the configurator boots with.
  // We can't reuse loadWindow() because that early-returns if the target
  // matches ds.currentWindow.
  const v = window.VANILLA_GRAPHICS && window.VANILLA_GRAPHICS[ds.currentWindow];
  if (v) ds.pixels = new Uint8Array(v.pixels);
  updateWindowBanner();
  render();

  window.__designer = ds;   // debug handle
})();
