/* SNES 4bpp tile encoder + median-cut quantizer for the FF6 window
 * graphics designer.  No DOM access; safe to load in Node for tests.
 *
 * Mirrors config/window_graphics.py — round-trip with the Python codec is
 * covered by tests/test_window_graphics_js.js.
 */

(function (root, factory) {
  const mod = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = mod;
  else root.WGEncoder = mod;
})(typeof self !== 'undefined' ? self : this, function () {

  // ---- shape constants (match config/window_graphics.py) ------------
  const TILES_W = 4, TILES_H = 7;
  const TILE_BYTES = 32;
  const SHEET_W = 32, SHEET_H = 56;
  const SHEET_BYTES = SHEET_W / 8 * SHEET_H / 8 * TILE_BYTES;  // 896
  const PAL_BYTES = 32;
  const BLOB_BYTES = SHEET_BYTES + PAL_BYTES;
  // Vanilla filler the stock ROM puts in unreferenced palette slots 8..15.
  const FILLER_BGR15 = [0x00, 0x38];

  // ---- 4bpp encoder -------------------------------------------------

  function encodeTile4bpp(rows) {
    const out = new Uint8Array(32);
    for (let r = 0; r < 8; r++) {
      let bp0 = 0, bp1 = 0, bp2 = 0, bp3 = 0;
      for (let x = 0; x < 8; x++) {
        const v = rows[r * 8 + x];
        const bit = 7 - x;
        bp0 |= ( v       & 1) << bit;
        bp1 |= ((v >> 1) & 1) << bit;
        bp2 |= ((v >> 2) & 1) << bit;
        bp3 |= ((v >> 3) & 1) << bit;
      }
      out[2 * r]      = bp0;
      out[2 * r + 1]  = bp1;
      out[16 + 2 * r] = bp2;
      out[17 + 2 * r] = bp3;
    }
    return out;
  }

  function encodeSheet(pixels) {
    const out = new Uint8Array(SHEET_BYTES);
    let off = 0;
    for (let ty = 0; ty < TILES_H; ty++) {
      for (let tx = 0; tx < TILES_W; tx++) {
        const tile = new Uint8Array(64);
        for (let y = 0; y < 8; y++) {
          for (let x = 0; x < 8; x++) {
            tile[y * 8 + x] = pixels[(ty * 8 + y) * SHEET_W + (tx * 8 + x)];
          }
        }
        out.set(encodeTile4bpp(tile), off);
        off += TILE_BYTES;
      }
    }
    return out;
  }

  // Inverse of encodeTile4bpp: read 32 bytes back into 64 pixel indices.
  function decodeTile4bpp(bytes32) {
    const out = new Uint8Array(64);
    for (let r = 0; r < 8; r++) {
      const bp0 = bytes32[2 * r];
      const bp1 = bytes32[2 * r + 1];
      const bp2 = bytes32[16 + 2 * r];
      const bp3 = bytes32[17 + 2 * r];
      for (let x = 0; x < 8; x++) {
        const bit = 7 - x;
        out[r * 8 + x] = ((bp0 >> bit) & 1) |
                         (((bp1 >> bit) & 1) << 1) |
                         (((bp2 >> bit) & 1) << 2) |
                         (((bp3 >> bit) & 1) << 3);
      }
    }
    return out;
  }

  function decodeSheet(bytes) {
    const pixels = new Uint8Array(SHEET_W * SHEET_H);
    let off = 0;
    for (let ty = 0; ty < TILES_H; ty++) {
      for (let tx = 0; tx < TILES_W; tx++) {
        const tile = decodeTile4bpp(bytes.subarray(off, off + TILE_BYTES));
        for (let y = 0; y < 8; y++) {
          for (let x = 0; x < 8; x++) {
            pixels[(ty * 8 + y) * SHEET_W + (tx * 8 + x)] = tile[y * 8 + x];
          }
        }
        off += TILE_BYTES;
      }
    }
    return pixels;
  }

  // Read the first 8 palette entries (slots 0..7) from a 32-byte BGR15 block.
  // Vanilla filler in slots 8..15 is ignored.
  function decodePalette(bytes32) {
    const out = [];
    for (let i = 0; i < 8; i++) {
      const v = bytes32[2 * i] | (bytes32[2 * i + 1] << 8);
      out.push([v & 0x1F, (v >> 5) & 0x1F, (v >> 10) & 0x1F]);
    }
    return out;
  }

  // palette: 8 entries (R,G,B 0..31 each).  Pad to 16 with vanilla filler.
  function encodePalette(palette) {
    const out = new Uint8Array(PAL_BYTES);
    for (let i = 0; i < 8; i++) {
      const c = palette[i] || [0, 0, 0];
      const v = (c[2] << 10) | (c[1] << 5) | c[0];
      out[2 * i] = v & 0xFF;
      out[2 * i + 1] = (v >> 8) & 0xFF;
    }
    for (let i = 8; i < 16; i++) {
      out[2 * i] = FILLER_BGR15[0];
      out[2 * i + 1] = FILLER_BGR15[1];
    }
    return out;
  }

  // ---- median cut quantizer -----------------------------------------
  // pixels: Array<[r,g,b]> in 0..255.  n: target color count.
  // Returns { palette: Array<[r,g,b]>, indices: Array<int> }.

  function medianCut(pixels, n) {
    const initial = pixels.map((p, i) => ({ p: p, i: i }));
    let boxes = [initial];

    function channelRange(box, c) {
      let min = 255, max = 0;
      for (const e of box) {
        if (e.p[c] < min) min = e.p[c];
        if (e.p[c] > max) max = e.p[c];
      }
      return max - min;
    }

    while (boxes.length < n) {
      let bestIdx = -1, bestRange = 0, bestCh = 0;
      for (let bi = 0; bi < boxes.length; bi++) {
        const box = boxes[bi];
        if (box.length < 2) continue;
        for (let c = 0; c < 3; c++) {
          const r = channelRange(box, c);
          if (r > bestRange) { bestRange = r; bestIdx = bi; bestCh = c; }
        }
      }
      if (bestIdx < 0) break;
      const box = boxes[bestIdx];
      box.sort((a, b) => a.p[bestCh] - b.p[bestCh]);
      const mid = Math.floor(box.length / 2);
      boxes.splice(bestIdx, 1, box.slice(0, mid), box.slice(mid));
    }

    const palette = boxes.map(box => {
      let r = 0, g = 0, b = 0;
      for (const e of box) { r += e.p[0]; g += e.p[1]; b += e.p[2]; }
      const k = Math.max(1, box.length);
      return [Math.round(r / k), Math.round(g / k), Math.round(b / k)];
    });
    const indices = new Array(pixels.length);
    boxes.forEach((box, bi) => {
      for (const e of box) indices[e.i] = bi;
    });
    return { palette: palette, indices: indices };
  }

  function lumin(rgb) {
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2];
  }

  // Sort a palette light-to-dark and remap the corresponding indices.
  function sortByLuminosity(palette, indices) {
    const order = palette
      .map((c, i) => [i, lumin(c)])
      .sort((a, b) => b[1] - a[1])
      .map(([i]) => i);
    const remap = new Array(palette.length);
    order.forEach((oldIdx, newIdx) => { remap[oldIdx] = newIdx; });
    return {
      palette: order.map(i => palette[i]),
      indices: indices.map(i => remap[i]),
    };
  }

  // 5-bit <-> 8-bit channel conversion (matches scripts/window_graphics.py).
  function bgr5_to_rgb8(c5) { return (c5 << 3) | (c5 >> 2); }
  function rgb8_to_bgr5(c8) {
    const v = Math.round(c8 * 31 / 255);
    return v < 0 ? 0 : v > 31 ? 31 : v;
  }

  // ---- BMP import / export (32x56 sheet) ----------------------------
  // Lets the user round-trip a sheet through an external pixel editor.
  // encodeBMP writes an 8-bit indexed, uncompressed (BI_RGB), bottom-up
  // Windows BMP whose colour table is the 8-entry window palette and whose
  // pixel bytes are palette indices 0..7 -- so it carries exactly the same
  // information ds.pixels does.  decodeBMP reads it (and most editor output)
  // back to per-pixel RGB.

  // pixels: Uint8Array(SHEET_W*SHEET_H) of indices 0..7.
  // paletteRGB8: array indexed by pixel value -> [r,g,b] 0..255.
  function encodeBMP(pixels, paletteRGB8) {
    const w = SHEET_W, h = SHEET_H;
    const rowSize = (w + 3) & ~3;          // pad each row to 4 bytes (32 stays 32)
    const pixelArraySize = rowSize * h;
    const TABLE = 256;                      // full colour table; only 0..7 used
    const headerSize = 14 + 40 + TABLE * 4;
    const fileSize = headerSize + pixelArraySize;
    const buf = new Uint8Array(fileSize);
    const dv = new DataView(buf.buffer);
    // BITMAPFILEHEADER
    buf[0] = 0x42; buf[1] = 0x4D;          // 'BM'
    dv.setUint32(2, fileSize, true);
    dv.setUint32(10, headerSize, true);    // pixel-data offset
    // BITMAPINFOHEADER
    dv.setUint32(14, 40, true);
    dv.setInt32(18, w, true);
    dv.setInt32(22, h, true);              // positive height -> bottom-up
    dv.setUint16(26, 1, true);             // colour planes
    dv.setUint16(28, 8, true);             // bits per pixel
    dv.setUint32(30, 0, true);             // BI_RGB (uncompressed)
    dv.setUint32(34, pixelArraySize, true);
    dv.setInt32(38, 2835, true);           // ~72 DPI (X)
    dv.setInt32(42, 2835, true);           // ~72 DPI (Y)
    dv.setUint32(46, TABLE, true);         // colours used
    dv.setUint32(50, 0, true);             // all colours important
    // colour table, stored BGRA
    let p = 54;
    for (let i = 0; i < TABLE; i++) {
      const c = paletteRGB8[i] || [0, 0, 0];
      buf[p++] = c[2]; buf[p++] = c[1]; buf[p++] = c[0]; buf[p++] = 0;
    }
    // pixel array, bottom-up
    for (let y = 0; y < h; y++) {
      const srcRow = (h - 1 - y) * w;
      let dst = headerSize + y * rowSize;
      for (let x = 0; x < w; x++) buf[dst++] = pixels[srcRow + x] & 0xFF;
    }
    return buf;
  }

  // Decode an uncompressed Windows BMP into { width, height, pixels }, where
  // pixels is a flat Array of [r,g,b] in row-major top-to-bottom order.
  // Handles 1/4/8-bit indexed and 24/32-bit truecolour (BI_RGB, plus 32-bit
  // BI_BITFIELDS read as BGRA).  Throws on anything it can't read.
  function decodeBMP(arrayBuffer) {
    const buf = new Uint8Array(arrayBuffer);
    if (buf.length < 54 || buf[0] !== 0x42 || buf[1] !== 0x4D)
      throw new Error('not a BMP file');
    const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
    const dataOffset = dv.getUint32(10, true);
    const dibSize = dv.getUint32(14, true);
    const width = dv.getInt32(18, true);
    const rawHeight = dv.getInt32(22, true);
    const bpp = dv.getUint16(28, true);
    const compression = dv.getUint32(30, true);
    const topDown = rawHeight < 0;
    const height = Math.abs(rawHeight);
    if (width <= 0 || height <= 0) throw new Error('bad BMP dimensions');
    if (compression !== 0 && !(compression === 3 && bpp === 32))
      throw new Error('compressed BMPs are not supported -- save as an ' +
                      'uncompressed (BI_RGB) bitmap');

    let palette = null;
    if (bpp <= 8) {
      let clrUsed = dv.getUint32(46, true);
      if (clrUsed === 0) clrUsed = 1 << bpp;
      const tableOff = 14 + dibSize;
      palette = [];
      for (let i = 0; i < clrUsed; i++) {
        const o = tableOff + i * 4;
        palette.push([buf[o + 2], buf[o + 1], buf[o]]);   // BGRA -> RGB
      }
    }

    const rowSize = Math.floor((bpp * width + 31) / 32) * 4;
    const pixels = new Array(width * height);
    for (let ry = 0; ry < height; ry++) {        // ry: output row, 0 = top
      const fileRow = topDown ? ry : (height - 1 - ry);
      const rowOff = dataOffset + fileRow * rowSize;
      for (let x = 0; x < width; x++) {
        let rgb;
        if (bpp === 8) {
          rgb = palette[buf[rowOff + x]] || [0, 0, 0];
        } else if (bpp === 4) {
          const b = buf[rowOff + (x >> 1)];
          rgb = palette[(x & 1) ? (b & 0x0F) : (b >> 4)] || [0, 0, 0];
        } else if (bpp === 1) {
          const b = buf[rowOff + (x >> 3)];
          rgb = palette[(b >> (7 - (x & 7))) & 1] || [0, 0, 0];
        } else if (bpp === 24) {
          const o = rowOff + x * 3;
          rgb = [buf[o + 2], buf[o + 1], buf[o]];
        } else if (bpp === 32) {
          const o = rowOff + x * 4;
          rgb = [buf[o + 2], buf[o + 1], buf[o]];          // assume BGRA
        } else {
          throw new Error('unsupported BMP bit depth ' + bpp);
        }
        pixels[ry * width + x] = rgb;
      }
    }
    return { width, height, pixels };
  }

  return {
    encodeTile4bpp, encodeSheet, encodePalette,
    decodeTile4bpp, decodeSheet, decodePalette,
    encodeBMP, decodeBMP,
    medianCut, sortByLuminosity, lumin,
    bgr5_to_rgb8, rgb8_to_bgr5,
    SHEET_W, SHEET_H, SHEET_BYTES, PAL_BYTES, BLOB_BYTES,
    TILES_W, TILES_H, TILE_BYTES,
  };
});
