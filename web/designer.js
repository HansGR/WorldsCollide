/* Custom window image designer.
 *
 * Self-contained module that runs alongside the existing flagstring
 * builder.  Produces a 928-byte binary (896 bytes of SNES 4bpp graphics
 * + 32 bytes of BGR15 palette) for one of the 8 window slots in the
 * FF6 ROM, applied via:
 *
 *   ff6_config.py --window-image N:file.bin
 *
 * Pipeline:
 *   1. User uploads a 32x32 image.  Cover-fit center-crop to 32x32, then
 *      median-cut quantize to 7 colors, sort by luminosity (light->dark),
 *      snap to BGR15.  Palette index 0 is reserved as transparent black.
 *   2. User picks a border preset (or uploads a custom 32x24 image,
 *      which is bucketed by luminosity rank into indices 0 (transparent)
 *      and 1..7 (lightest..darkest) so it composes with whatever palette
 *      the texture left behind).
 *   3. User can paint individual pixels in the editor canvas, and adjust
 *      any of the 7 palette colors via R/G/B sliders.
 *   4. Download triggers encode_window_sheet + encode_palette to produce
 *      the 928-byte blob.
 *
 * Pixel coords inside the designer: (x in 0..31, y in 0..55).  Indices
 * 0..7 are used; 8..15 of the 16-color palette get the vanilla 0x3800
 * filler at encode time to keep the bytes faithful to the stock layout.
 */

(function () {
  const enc = window.WGEncoder;   // SNES 4bpp encoder + quantizer (encoder.js)

  // ---- shape constants -----------------------------------------------
  const TEX_W = 32, TEX_H = 32;
  const BORDER_W = 32, BORDER_H = 24;
  const SHEET_W = enc.SHEET_W, SHEET_H = enc.SHEET_H;
  const NUM_PALETTE_SLOTS = 8;  // index 0 (transparent) + slots 1..7
  const SCALE = 8;              // px per source pixel on the editor canvas
  const BLOB_BYTES = enc.BLOB_BYTES;

  // ---- default initial state -----------------------------------------

  // A simple greyscale ramp so the editor opens with something visible.
  const DEFAULT_PALETTE = [
    [0, 0, 0],            // 0 - transparent
    [28, 28, 28],         // 1 - lightest
    [22, 22, 22],
    [17, 17, 17],
    [13, 13, 13],
    [9, 9, 9],
    [5, 5, 5],
    [2, 2, 2],            // 7 - darkest
  ];

  // ---- state ---------------------------------------------------------

  const ds = {
    // Per-pixel palette indices for the whole 32x56 sheet.
    pixels: new Uint8Array(SHEET_W * SHEET_H),
    palette: DEFAULT_PALETTE.map(c => c.slice()),
    selectedIndex: 1,            // which palette slot is being edited / painted
    borderId: 'rounded',
    targetWindow: 8,
    lastTextureFile: null,       // for re-quantize
    isPainting: false,
    lastTexUpload: null,         // cached ImageData for re-quantize
  };

  // ---- helpers -------------------------------------------------------

  function idx(x, y) { return y * SHEET_W + x; }
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  const lumin = enc.lumin;
  const bgr5_to_rgb8 = enc.bgr5_to_rgb8;
  const rgb8_to_bgr5 = enc.rgb8_to_bgr5;

  // Apply a 32x24 border indices array into the bottom of ds.pixels.
  function applyBorderPixels(borderPx) {
    for (let y = 0; y < BORDER_H; y++) {
      for (let x = 0; x < BORDER_W; x++) {
        ds.pixels[idx(x, TEX_H + y)] = borderPx[y * BORDER_W + x];
      }
    }
  }

  // Apply a 32x32 texture indices array into the top of ds.pixels.
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
        // Cover-fit center-crop (preserve aspect, fill the target).
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

  // Quantize a freshly-uploaded 32x32 RGB array into:
  //   - a 7-color palette (indices 1..7 in the editor's 8-slot palette)
  //   - a 1024-entry index array (values 1..7)
  // Index 0 (transparent) is left untouched by this path.
  function quantizeTexture(rgbPixels) {
    const { palette, indices } = enc.medianCut(rgbPixels, 7);
    const sorted = enc.sortByLuminosity(palette, indices);
    // Shift indices to land in slots 1..7 (not 0..6).
    const shifted = sorted.indices.map(i => i + 1);
    // Snap to BGR15.
    const snapped = sorted.palette.map(c => [
      rgb8_to_bgr5(c[0]), rgb8_to_bgr5(c[1]), rgb8_to_bgr5(c[2]),
    ]);
    return { palette: snapped, indices: shifted };
  }

  // Quantize an uploaded 32x24 image to the editor's 8-slot palette by
  // luminosity rank, matching the preset borders' scheme:
  //   index 0 = (near-)transparent -- pixels darker than TRANSPARENT_CUTOFF
  //   index 1 = lightest visible band
  //   ...
  //   index 7 = darkest visible band
  // The non-transparent pixels get bucketed into 7 equal-population
  // luminosity bins so the upload preserves shading nuance instead of
  // collapsing to a two-color silhouette.
  function quantizeBorder(rgbPixels) {
    const TRANSPARENT_CUTOFF = 24;   // 0..255 luminance
    // Collect luminosities of the "visible" (non-transparent) pixels and
    // build the bin edges from their distribution.
    const visibleLums = [];
    for (const p of rgbPixels) {
      const L = lumin(p);
      if (L >= TRANSPARENT_CUTOFF) visibleLums.push(L);
    }
    visibleLums.sort((a, b) => b - a);  // brightest first
    // Six interior cut points carve the sorted list into seven equal-ish
    // populations: pixels in segment k -> output index k+1.
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
    const c = ds.palette[index] || [0, 0, 0];
    return [bgr5_to_rgb8(c[0]), bgr5_to_rgb8(c[1]), bgr5_to_rgb8(c[2])];
  }

  function render() {
    // Paint each source pixel as a SCALExSCALE square.  Background for
    // transparent (index 0) is a faint checkerboard so the user can see
    // its extent on the canvas.
    const im = ctx.createImageData(SHEET_W * SCALE, SHEET_H * SCALE);
    const w = im.width;
    for (let y = 0; y < SHEET_H; y++) {
      for (let x = 0; x < SHEET_W; x++) {
        const v = ds.pixels[idx(x, y)];
        let rgb;
        if (v === 0) {
          // checkerboard for transparent
          rgb = ((Math.floor(x / 2) + Math.floor(y / 2)) & 1) ? [60, 60, 70] : [40, 40, 50];
        } else {
          rgb = paletteRGB8(v);
        }
        for (let dy = 0; dy < SCALE; dy++) {
          for (let dx = 0; dx < SCALE; dx++) {
            const px = ((y * SCALE + dy) * w + (x * SCALE + dx)) * 4;
            im.data[px] = rgb[0];
            im.data[px + 1] = rgb[1];
            im.data[px + 2] = rgb[2];
            im.data[px + 3] = 255;
          }
        }
      }
    }
    ctx.putImageData(im, 0, 0);

    // Faint divider between the texture area (top 32 rows) and the
    // border area (bottom 24 rows).
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
        btn.title = 'index 0 — transparent';
      } else {
        btn.style.background = `rgb(${r},${g},${b})`;
        btn.title = `index ${i} — rgb(${ds.palette[i].join(', ')})`;
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
    const c = ds.palette[ds.selectedIndex] || [0, 0, 0];
    for (let i = 0; i < 3; i++) {
      rgbInputs[i].value = c[i];
      rgbLabels[i].textContent = c[i];
      rgbInputs[i].disabled = (ds.selectedIndex === 0);  // 0 stays transparent
    }
  }

  rgbInputs.forEach((input, i) => {
    input.addEventListener('input', () => {
      if (ds.selectedIndex === 0) return;
      const v = parseInt(input.value, 10);
      ds.palette[ds.selectedIndex][i] = clamp(v, 0, 31);
      rgbLabels[i].textContent = String(ds.palette[ds.selectedIndex][i]);
      render();
    });
  });

  // ---- paint interaction ---------------------------------------------

  function canvasToPixel(evt) {
    const rect = canvas.getBoundingClientRect();
    const cssX = evt.clientX - rect.left;
    const cssY = evt.clientY - rect.top;
    // The canvas is displayed at its intrinsic size (256x448) but the user
    // may have zoomed -- use the bounding rect to map.
    const x = Math.floor(cssX * (SHEET_W * SCALE) / rect.width / SCALE);
    const y = Math.floor(cssY * (SHEET_H * SCALE) / rect.height / SCALE);
    if (x < 0 || x >= SHEET_W || y < 0 || y >= SHEET_H) return null;
    return { x, y };
  }

  // Bresenham-ish line so dragged strokes don't skip pixels at high speeds.
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
  const endPaint = () => { ds.isPainting = false; lastPaintPx = null; };
  canvas.addEventListener('mouseup', endPaint);
  canvas.addEventListener('mouseleave', endPaint);
  window.addEventListener('mouseup', endPaint);

  // ---- border preset / upload ----------------------------------------

  const borderSelect = document.getElementById('ds-border-preset');

  function populateBorderOptions() {
    if (!window.BORDER_PRESETS) {
      console.warn('BORDER_PRESETS not loaded yet');
      return;
    }
    borderSelect.innerHTML = '';
    const order = window.BORDER_PRESETS_ORDER || Object.keys(window.BORDER_PRESETS);
    for (const key of order) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = window.BORDER_PRESETS[key].name;
      if (key === ds.borderId) opt.selected = true;
      borderSelect.appendChild(opt);
    }
  }

  function applyCurrentBorder() {
    const preset = window.BORDER_PRESETS && window.BORDER_PRESETS[ds.borderId];
    if (!preset) return;
    applyBorderPixels(preset.pixels);
  }

  borderSelect.addEventListener('change', () => {
    ds.borderId = borderSelect.value;
    applyCurrentBorder();
    render();
  });

  document.getElementById('ds-border-upload').addEventListener('change', async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    try {
      const imgData = await loadImageToCanvas(f, BORDER_W, BORDER_H);
      const px = quantizeBorder(imageDataToRGB(imgData));
      applyBorderPixels(px);
      // "Switch" to a synthetic preset entry so the dropdown reflects it.
      let opt = [...borderSelect.options].find(o => o.value === '__custom__');
      if (!opt) {
        opt = document.createElement('option');
        opt.value = '__custom__';
        opt.textContent = 'Custom upload';
        borderSelect.appendChild(opt);
      }
      borderSelect.value = '__custom__';
      ds.borderId = '__custom__';
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
    // Replace slots 1..7 with the quantized colors; slot 0 stays transparent.
    for (let i = 0; i < 7; i++) ds.palette[i + 1] = palette[i];
    applyTexturePixels(indices);
    setStatus('texture re-quantized from upload', false);
    render();
  }

  // ---- target window + download --------------------------------------

  const targetSelect = document.getElementById('ds-target');
  targetSelect.addEventListener('change', () => {
    ds.targetWindow = parseInt(targetSelect.value, 10);
  });

  document.getElementById('ds-download').addEventListener('click', () => {
    const gfx = enc.encodeSheet(ds.pixels);
    const pal = enc.encodePalette(ds.palette);
    const blob = new Uint8Array(BLOB_BYTES);
    blob.set(gfx, 0);
    blob.set(pal, enc.SHEET_BYTES);
    const file = new Blob([blob], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = `window${ds.targetWindow}.bin`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setStatus(
      `downloaded window${ds.targetWindow}.bin — apply with ` +
      `\`ff6_config.py --window-image ${ds.targetWindow}:window${ds.targetWindow}.bin\``,
      false);
  });

  // ---- status line ---------------------------------------------------

  const statusEl = document.getElementById('ds-status');
  function setStatus(text, isError) {
    statusEl.textContent = text;
    statusEl.classList.toggle('error', !!isError);
  }

  // ---- init ----------------------------------------------------------

  // Greyscale ramp texture so the editor opens with visible content.
  for (let y = 0; y < TEX_H; y++) {
    for (let x = 0; x < TEX_W; x++) {
      // Diagonal gradient mapped into indices 1..7.
      const t = ((x + y) / (TEX_W + TEX_H - 2));
      ds.pixels[idx(x, y)] = 1 + Math.min(6, Math.floor(t * 7));
    }
  }
  populateBorderOptions();
  applyCurrentBorder();
  render();

  // Expose for debugging from the console.
  window.__designer = ds;
})();
