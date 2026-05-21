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

console.log(`\n${passed}/${passed + failed.length} passed`);
if (failed.length) process.exit(1);
