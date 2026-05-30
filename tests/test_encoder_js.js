/* Node test: verify web/encoder.js produces bytes identical to the Python
 * window_graphics codec on the shipped romdata reference dump.
 *
 * Run as:
 *   node tests/test_encoder_js.js
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const enc = require(path.join(ROOT, 'web', 'encoder.js'));

// ---- shared helpers --------------------------------------------------

function parseHexDump(text) {
  return text.split(/\s+/).filter(Boolean).map(s => parseInt(s, 16));
}

function decodeTile4bpp(bytes32) {
  const rows = [];
  for (let r = 0; r < 8; r++) {
    const bp0 = bytes32[2 * r];
    const bp1 = bytes32[2 * r + 1];
    const bp2 = bytes32[16 + 2 * r];
    const bp3 = bytes32[17 + 2 * r];
    const row = [];
    for (let x = 0; x < 8; x++) {
      const bit = 7 - x;
      row.push(((bp0 >> bit) & 1) |
               (((bp1 >> bit) & 1) << 1) |
               (((bp2 >> bit) & 1) << 2) |
               (((bp3 >> bit) & 1) << 3));
    }
    rows.push(row);
  }
  return rows;
}

function decodeSheet(bytes896) {
  const pixels = new Uint8Array(enc.SHEET_W * enc.SHEET_H);
  for (let ty = 0; ty < enc.TILES_H; ty++) {
    for (let tx = 0; tx < enc.TILES_W; tx++) {
      const t = ty * enc.TILES_W + tx;
      const tile = decodeTile4bpp(bytes896.slice(t * 32, (t + 1) * 32));
      for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
          pixels[(ty * 8 + y) * enc.SHEET_W + (tx * 8 + x)] = tile[y][x];
        }
      }
    }
  }
  return pixels;
}

function decodePalette(bytes32) {
  const colors = [];
  for (let i = 0; i < 16; i++) {
    const v = bytes32[2 * i] | (bytes32[2 * i + 1] << 8);
    colors.push([v & 0x1F, (v >> 5) & 0x1F, (v >> 10) & 0x1F]);
  }
  return colors;
}

function bytesEqual(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

// ---- tests -----------------------------------------------------------

let passed = 0, failed = [];
function run(name, fn) {
  try { fn(); console.log('PASS:', name); passed++; }
  catch (e) { console.log('FAIL:', name, '-', e.message); failed.push(name); }
}

function loadDump(file, expected) {
  const arr = parseHexDump(fs.readFileSync(file, 'utf8'));
  while (arr.length < expected) arr.push(0);
  return arr;
}

const gfxAll = loadDump(path.join(ROOT, 'romdata', 'ED0000_MenuWindowGraphics.txt'), 8 * 896);
const palAll = loadDump(path.join(ROOT, 'romdata', 'ED1C00_MenuWindowPalettes.txt'), 8 * 32);

run('encodeSheet round-trips every stock window', () => {
  for (let n = 1; n <= 8; n++) {
    const base = (n - 1) * 896;
    const orig = gfxAll.slice(base, base + 896);
    const decoded = decodeSheet(orig);
    const reEncoded = enc.encodeSheet(decoded);
    if (!bytesEqual(orig, reEncoded)) throw new Error(`W${n} mismatch`);
  }
});

run('encodePalette round-trips every stock palette', () => {
  for (let n = 1; n <= 8; n++) {
    const base = (n - 1) * 32;
    const orig = palAll.slice(base, base + 32);
    // The first 8 colors are the user-editable + transparent slots; slots
    // 8..15 in the encoder always write the vanilla 0x3800 filler.  W8's
    // stock dump is one byte short, so the last filler entry is zero
    // there -- compare against what the encoder would actually write for
    // that input, i.e. allow slots 8..15 to differ from the truncated dump
    // but not slots 0..7.
    const colors = decodePalette(orig).slice(0, 8);
    const reEncoded = enc.encodePalette(colors);
    if (!bytesEqual(orig.slice(0, 16), reEncoded.slice(0, 16))) {
      throw new Error(`W${n} slot-0..7 bytes mismatch`);
    }
  }
});

run('encodeTile4bpp matches a hand-computed reference', () => {
  // Solid color 7 tile: bp0=bp1=bp2=0xFF, bp3=0x00 per row.
  const rows = new Uint8Array(64).fill(7);
  const got = enc.encodeTile4bpp(rows);
  for (let r = 0; r < 8; r++) {
    if (got[2 * r] !== 0xFF || got[2 * r + 1] !== 0xFF ||
        got[16 + 2 * r] !== 0xFF || got[17 + 2 * r] !== 0x00) {
      throw new Error(`row ${r}: ` + Array.from(got.slice(2*r, 2*r+2)).concat(
        Array.from(got.slice(16+2*r, 18+2*r))).join(','));
    }
  }
});

run('encodePalette pads slots 8..15 with vanilla filler', () => {
  const got = enc.encodePalette([
    [0,0,0], [31,0,0], [0,31,0], [0,0,31], [0,0,0], [0,0,0], [0,0,0], [0,0,0],
  ]);
  for (let i = 8; i < 16; i++) {
    if (got[2 * i] !== 0x00 || got[2 * i + 1] !== 0x38) {
      throw new Error(`slot ${i}: ${got[2*i]}, ${got[2*i+1]}`);
    }
  }
});

run('medianCut produces requested color count and a valid index map', () => {
  // 100 random-ish RGB pixels.
  const pixels = [];
  for (let i = 0; i < 100; i++) {
    pixels.push([(i * 53) & 0xFF, (i * 91) & 0xFF, (i * 23) & 0xFF]);
  }
  const { palette, indices } = enc.medianCut(pixels, 7);
  if (palette.length !== 7) throw new Error(`palette has ${palette.length} colors`);
  if (indices.length !== 100) throw new Error(`indices has ${indices.length} entries`);
  for (const i of indices) {
    if (i < 0 || i >= 7) throw new Error(`bad index ${i}`);
  }
});

run('sortByLuminosity orders light first and updates indices consistently', () => {
  const palette = [[0,0,0], [255,255,255], [128,128,128]];
  const indices = [0, 1, 2, 1];
  const { palette: sp, indices: si } = enc.sortByLuminosity(palette, indices);
  // After sort: lightest first.  [255,255,255] should be index 0.
  if (sp[0][0] !== 255 || sp[2][0] !== 0) throw new Error('palette not sorted');
  // The pixel that was originally 1 (white) should now be 0.
  if (si[1] !== 0) throw new Error('index remap wrong: ' + si[1]);
});

run('bgr5_to_rgb8 + rgb8_to_bgr5 round-trip every 5-bit value', () => {
  for (let c = 0; c < 32; c++) {
    const r = enc.rgb8_to_bgr5(enc.bgr5_to_rgb8(c));
    if (r !== c) throw new Error(`${c} -> ${enc.bgr5_to_rgb8(c)} -> ${r}`);
  }
});

run('encodeBMP -> decodeBMP recovers every pixel index exactly', () => {
  const W = enc.SHEET_W, H = enc.SHEET_H;
  const pixels = new Uint8Array(W * H);
  for (let i = 0; i < pixels.length; i++) pixels[i] = (i * 7) % 8;
  // Slot 0 = magenta sentinel; 1..7 distinct colours snapped to BGR5.
  const pal = [[255, 0, 255]];
  for (let s = 1; s < 8; s++) {
    pal.push([enc.bgr5_to_rgb8((s * 3) % 32),
              enc.bgr5_to_rgb8((s * 5) % 32),
              enc.bgr5_to_rgb8((s * 7) % 32)]);
  }
  const bmp = enc.encodeBMP(pixels, pal);
  if (bmp[0] !== 0x42 || bmp[1] !== 0x4D) throw new Error('missing BM magic');
  const ab = bmp.buffer.slice(bmp.byteOffset, bmp.byteOffset + bmp.byteLength);
  const dec = enc.decodeBMP(ab);
  if (dec.width !== W || dec.height !== H)
    throw new Error(`decoded ${dec.width}x${dec.height}`);
  const key = c => (c[0] << 16) | (c[1] << 8) | c[2];
  const slot = new Map(); pal.forEach((c, i) => slot.set(key(c), i));
  for (let i = 0; i < pixels.length; i++) {
    if (slot.get(key(dec.pixels[i])) !== pixels[i])
      throw new Error(`pixel ${i} mismatch`);
  }
});

run('decodeBMP reads a 24-bit bottom-up bitmap top-to-bottom', () => {
  // Hand-build a 2x2 24-bit BMP.  File rows are bottom-up, so the first
  // pixel row in the file is the *bottom* image row.
  const W = 2, H = 2;
  const rowSize = Math.floor((24 * W + 31) / 32) * 4;   // 8 bytes (6 + 2 pad)
  const dataOff = 54;
  const buf = new Uint8Array(dataOff + rowSize * H);
  const dv = new DataView(buf.buffer);
  buf[0] = 0x42; buf[1] = 0x4D;
  dv.setUint32(2, buf.length, true);
  dv.setUint32(10, dataOff, true);
  dv.setUint32(14, 40, true);
  dv.setInt32(18, W, true);
  dv.setInt32(22, H, true);            // positive -> bottom-up
  dv.setUint16(26, 1, true);
  dv.setUint16(28, 24, true);
  dv.setUint32(30, 0, true);
  // BGR triples.  bottom row (file row 0): red, green; top row: blue, white.
  const put = (off, r, g, b) => { buf[off] = b; buf[off + 1] = g; buf[off + 2] = r; };
  put(dataOff + 0 * rowSize + 0, 255, 0, 0);   // bottom-left  red
  put(dataOff + 0 * rowSize + 3, 0, 255, 0);   // bottom-right green
  put(dataOff + 1 * rowSize + 0, 0, 0, 255);   // top-left     blue
  put(dataOff + 1 * rowSize + 3, 255, 255, 255); // top-right  white
  const dec = enc.decodeBMP(buf.buffer);
  const eq = (c, r, g, b) => c[0] === r && c[1] === g && c[2] === b;
  if (!eq(dec.pixels[0], 0, 0, 255)) throw new Error('top-left not blue');
  if (!eq(dec.pixels[1], 255, 255, 255)) throw new Error('top-right not white');
  if (!eq(dec.pixels[2], 255, 0, 0)) throw new Error('bottom-left not red');
  if (!eq(dec.pixels[3], 0, 255, 0)) throw new Error('bottom-right not green');
});

console.log(`\n${passed}/${passed + failed.length} passed`);
if (failed.length) process.exit(1);
