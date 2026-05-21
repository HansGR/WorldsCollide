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

  function paintLine(a, b) {
    let x0 = a.x, y0 = a.y, x1 = b.x, y1 = b.y;
    const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx - dy;
    while (true) {
      ds.pixels[idx(x0, y0)] = ds.selectedIndex;
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 > -dy) { err -= dy; x0 += sx; }
      if (e2 < dx)  { err += dx; y0 += sy; }
    }
  }

  let lastPaintPx = null;
  canvas.addEventListener('mousedown', (e) => {
    const p = canvasToPixel(e);
    if (!p) return;
    ds.isPainting = true;
    lastPaintPx = p;
    ds.pixels[idx(p.x, p.y)] = ds.selectedIndex;
    markCustomized();
    render();
    e.preventDefault();
  });
  canvas.addEventListener('mousemove', (e) => {
    if (!ds.isPainting) return;
    const p = canvasToPixel(e);
    if (!p) return;
    if (lastPaintPx) paintLine(lastPaintPx, p);
    else ds.pixels[idx(p.x, p.y)] = ds.selectedIndex;
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

  document.getElementById('ds-download').addEventListener('click', () => {
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
    const cfg = {
      version: 1,
      flags: (ff6c.getFlagString && ff6c.getFlagString()) || '',
      graphics,
    };
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
    const customCount = Object.keys(graphics).length;
    setStatus(
      `downloaded ff6config.json (${customCount} custom window` +
      (customCount === 1 ? '' : 's') + ') -- apply with ' +
      '`ff6_config.py -i rom.smc --config ff6config.json`', false);
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
      // Palette / other change for the current window -- just re-render.
      render();
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
