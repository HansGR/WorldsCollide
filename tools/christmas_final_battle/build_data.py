"""Builds christmas_data.json for christmas_final_battle.py from the two pictures.

usage (from the repository, for its compression):
    python3 tools/christmas_final_battle/build_data.py TREE SANTA VANILLA_ROM OUT.json [PREVIEW_DIR]

TREE (895x1200) is a christmas tree with three rows of reindeer, in a storm. It is cut into what
the final battle shows, at half its size:
  - tiers 1 to 3 are battle backgrounds 0x33 to 0x35: a slice of the tree each
  - tier 4's background (0x36) is the top of the tree
SANTA (1024x1024) is santa in his sleigh with his whip, on white: pixel art shown large. Its own
pixels are found and taken as they are (they are the size the tree's are on the screen), and are
final kefka's sprite, placed on the top of the tree.
Needs PIL and numpy.
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter
from utils.compression import decompress
import utils.compression

def compress(data):
    # the repository's, without the flag byte it ends with when the last group of 8 is full: a flag
    # byte with nothing after it. the game stops when it has read as many bytes as the size says,
    # which it checks after each literal or reference, never after a flag byte: it would read on
    # past such an end and not stop (the battle does not start)
    result = utils.compression.compress(data)
    at = 2
    while at < len(result):
        flags, at = result[at], at + 1
        if at == len(result):
            result = result[:-1]
            result[0:2] = list(len(result).to_bytes(2, "little"))
            break
        for bit in range(8):
            if at >= len(result): break
            at += 1 if flags & (1 << bit) else 2
    assert decompress(result) == list(data)
    return result

picture, santa_picture, vanilla, out = sys.argv[1:5]
preview = sys.argv[5] if len(sys.argv) > 5 else None
rom = open(vanilla, "rb").read()
# the tree's picture is soft: it is sharpened before it is made small (and a little after), so that
# its edges are still there at half the size
SHARPEN, SHARPEN_SMALL = (2, 110, 2), (1, 50, 2)        # unsharp masks: radius, percent, threshold
source = np.asarray(Image.open(picture).convert("RGB").filter(ImageFilter.UnsharpMask(*SHARPEN))).astype(int)

W, H, T = 256, 152, 8                       # a battle background on the screen, and a tile
SCALE = 2                                   # picture pixels to one on the screen
LEFT = 252                                  # the picture's column at the left of the screen
TIER_TOPS = {0x33: 800, 0x34: 590, 0x35: 370}       # background : the picture's row at its top
# what a background can have: different tiles (sets of 128), and palettes of 15 colors. the tiers
# scroll into one another (santa's as well), and the game shows the one that comes with its tiles
# and its palettes in another place, which has room for 2 sets and 2 palettes only: a third set or
# palette is drawn over the menus and as garbage while it scrolls
LIMITS = {0x33: (256, 2), 0x34: (256, 2), 0x35: (256, 2), 0x36: (256, 2)}
SKY_BLUR = 2.5                              # the sky is blurred first: its tiles are then more alike, and are the ones that are made one
TREE_AXIS, TREE_TOP, TREE_TOP_HALF_WIDTH, TREE_SLOPE = 446, 80, 16, 0.18       # the tree in its picture: its column, its top row, and how it widens
KEFKA_TILES = 149                           # tiles final kefka's sprite has room for

def kmeans(data, k, rounds = 25):
    centers = [data[data.sum(axis = 1).argmin()]]
    while len(centers) < k:
        d = np.min([((data - c) ** 2).sum(axis = 1) for c in centers], axis = 0)
        centers.append(data[d.argmax()])
    centers = np.array(centers, dtype = float)
    for _ in range(rounds):
        label = ((data[:, None, :] - centers[None]) ** 2).sum(axis = 2).argmin(axis = 1)
        for j in range(k):
            if (label == j).any(): centers[j] = data[label == j].mean(axis = 0)
    return centers

def snes(c):
    return np.clip(np.round(c / 8), 0, 31) * 8

def parts(mask):
    # the connected parts of a mask: lists of (y, x)
    h, w = mask.shape
    seen, found = np.zeros((h, w), bool), []
    for y0, x0 in np.argwhere(mask):
        if seen[y0, x0]: continue
        part, stack = [], [(y0, x0)]
        while stack:
            y, x = stack.pop()
            if not (0 <= y < h and 0 <= x < w) or seen[y, x] or not mask[y, x]: continue
            seen[y, x] = True; part.append((y, x))
            stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
        found.append(part)
    return found

def small(pixels, left, top):
    # a slice at the size of the screen, its sky blurred. the sky is what is blue or a speck (the
    # snow in the wind: no more than 40 pixels), and not within the tree's outline, whose dark
    # green is as blue as the sky's
    image = Image.fromarray(pixels.astype("uint8")).crop((left, top, left + W * SCALE, top + H * SCALE))
    px = np.asarray(image.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(*SHARPEN_SMALL)), dtype = float)
    blurred = np.asarray(Image.fromarray(px.astype("uint8")).filter(ImageFilter.GaussianBlur(SKY_BLUR)), dtype = float)
    things = ~((px[..., 2] - px[..., 0] > 14) & (px[..., 2] >= px[..., 1]))
    for part in parts(things):
        if len(part) <= 40:
            for y, x in part: things[y, x] = False
    ys, xs = np.mgrid[0:H, 0:W]
    column, row = left + xs * SCALE, top + ys * SCALE
    things |= np.abs(column - TREE_AXIS) < TREE_TOP_HALF_WIDTH + (row - TREE_TOP) * TREE_SLOPE
    sky = np.asarray(Image.fromarray((~things * 255).astype("uint8")).filter(ImageFilter.MinFilter(3))) > 127     # not at the edges of what is not sky
    return np.where(sky[..., None], blurred, px)

def background(px, TILES, PALETTES):
    # 32x19 tiles, each in one of PALETTES palettes of 15 colors, no more than TILES different (also used flipped)
    rng = np.random.default_rng(1)
    tiles = px.reshape(H // T, T, W // T, T, 3).transpose(0, 2, 1, 3, 4).reshape(-1, T * T, 3)
    N = len(tiles)
    mean = tiles.mean(axis = 1)
    group = ((mean[:, None, :] - kmeans(mean, PALETTES)[None]) ** 2).sum(axis = 2).argmin(axis = 1)
    for _ in range(6):
        palettes = []
        for g in range(PALETTES):
            pixels = tiles[group == g].reshape(-1, 3)
            if len(pixels) > 6000: pixels = pixels[rng.choice(len(pixels), 6000, replace = False)]
            palettes.append(snes(kmeans(pixels, 15)) if len(pixels) else np.zeros((15, 3)))
        errors = np.stack([((tiles[:, :, None, :] - p[None, None]) ** 2).sum(axis = 3).min(axis = 2).sum(axis = 1) for p in palettes], axis = 1)
        group = errors.argmin(axis = 1)
    index = np.stack([((tiles[i][:, None, :] - palettes[group[i]][None]) ** 2).sum(axis = 2).argmin(axis = 1) for i in range(N)])
    shown = np.stack([palettes[group[i]][index[i]] for i in range(N)])
    # the sky's tiles are the first to be made one: what is not blue costs 4x as much
    weight = np.where((mean[:, 2] - mean[:, 0] > 14) & (mean[:, 2] >= mean[:, 1]), 1.0, 4.0)

    rep, flip, uniq = list(range(N)), [0] * N, {}
    def flips(t):
        g = t.reshape(T, T)
        return [g.reshape(-1), g[:, ::-1].reshape(-1), g[::-1].reshape(-1), g[::-1, ::-1].reshape(-1)]
    for i in range(N):
        for f, v in enumerate(flips(index[i])):
            key = (group[i], v.tobytes())
            if key in uniq: rep[i], flip[i] = uniq[key], f; break
        else:
            uniq[(group[i], index[i].tobytes())] = i
    alive = sorted(set(rep))
    if len(alive) > TILES:
        rgbt = {i: shown[i].reshape(T, T, 3) for i in alive}
        count = {i: rep.count(i) for i in alive}
        def dist(a, b):
            best = None
            for f, v in enumerate((rgbt[b], rgbt[b][:, ::-1], rgbt[b][::-1], rgbt[b][::-1, ::-1])):
                d = ((rgbt[a] - v) ** 2).sum()
                if best is None or d < best[0]: best = (d, f)
            return best
        pairs = {(a, b): dist(a, b) for a in alive for b in alive if a < b and group[a] == group[b]}
        while len(alive) > TILES:
            (a, b), (d, f) = min(pairs.items(), key = lambda kv: kv[1][0] * max(weight[kv[0][0]], weight[kv[0][1]]) * min(count[kv[0][0]], count[kv[0][1]]))
            keep, drop = (a, b) if count[a] >= count[b] else (b, a)
            for i in range(N):
                if rep[i] == drop: rep[i] = keep; flip[i] ^= f
            count[keep] += count[drop]
            alive.remove(drop)
            pairs = {k: v for k, v in pairs.items() if drop not in k}
    number = {t: n for n, t in enumerate(alive)}
    cells = [(number[rep[i]], int(group[rep[i]]), flip[i]) for i in range(N)]
    result = np.zeros((H, W, 3))
    for i, (n, g, f) in enumerate(cells):
        t = index[alive[n]].reshape(T, T)
        if f & 1: t = t[:, ::-1]
        if f & 2: t = t[::-1]
        y, x = divmod(i, W // T)
        result[y * T:(y + 1) * T, x * T:(x + 1) * T] = palettes[g][t]
    return [index[t] for t in alive], cells, palettes, result

def tile_4bpp(t, first_color = 1):
    data = [0] * 32
    for y in range(8):
        for x in range(8):
            v = int(t[y * 8 + x]) + first_color
            for plane in range(4):
                if v & (1 << plane):
                    data[y * 2 + (plane & 1) + (16 if plane >= 2 else 0)] |= 0x80 >> x
    return data

def color(c):
    return (int(c[0]) >> 3) | ((int(c[1]) >> 3) << 5) | ((int(c[2]) >> 3) << 10)

def vanilla_tail(bg):
    # the rows of a tilemap under the 19 that are seen, as the game has them
    PROPS, MAP_POINTERS = 0x270000, 0x271848
    pointer = MAP_POINTERS + rom[PROPS + bg * 6 + 3] * 2
    at = 0x270000 + (rom[pointer] | (rom[pointer + 1] << 8))
    return decompress(list(rom[at:at + (rom[at] | (rom[at + 1] << 8))]))[(W // T) * (H // T) * 2:]

def background_data(bg, px):
    TILES, PALETTES = LIMITS[bg]
    tiles, cells, palettes, result = background(px, TILES, PALETTES)
    tiles = tiles + [np.zeros(64, int)] * (TILES - len(tiles))
    sets = [compress(sum((tile_4bpp(t) for t in tiles[s * 128:(s + 1) * 128]), [])) for s in range(TILES // 128)]
    palettes = list(palettes) + [np.zeros((15, 3))] * (3 - PALETTES)
    words = [(n if n < 256 else 0x380 + n - 256) | ((5 + g) << 10) | (0x4000 if f & 1 else 0) | (0x8000 if f & 2 else 0)
             for n, g, f in cells]
    tilemap = compress(sum(([w & 0xff, w >> 8] for w in words), []) + vanilla_tail(bg))
    palette = []
    for p in palettes:
        palette += [0, 0] + sum(([color(c) & 0xff, color(c) >> 8] for c in p), [])
    print("background", hex(bg), "sets", [hex(len(s)) for s in sets], "tilemap", hex(len(tilemap)))
    if preview: Image.fromarray(result.astype("uint8")).save(f"{preview}/bg_{bg:02x}.png")
    return {"sets": [bytes(s).hex() for s in sets], "tilemap": bytes(tilemap).hex(), "palette": bytes(palette).hex()}

# santa: the picture is pixel art shown large. where the lines between its pixels are (the pitch and
# the start that the most edges fall on), and the color in the middle of each
big = np.asarray(Image.open(santa_picture).convert("RGB")).astype(float)
def pixel_centers(axis):
    edges = np.abs(np.diff(big.sum(axis = 2), axis = axis)).sum(axis = 1 - axis)
    best = None
    for pitch in np.arange(7.0, 8.0, 0.004):
        for start in np.arange(0, pitch, 0.25):
            at = np.round(start + np.arange(0, (len(edges) - start) / pitch - 1) * pitch).astype(int)
            score = edges[at[at < len(edges)]].mean()
            if best is None or score > best[0]: best = (score, pitch, start)
    _, pitch, start = best
    centers = start + 1 + pitch / 2 + np.arange(-1, len(edges) / pitch + 1) * pitch
    return centers[(centers >= 1) & (centers < len(edges))]
columns, rows = pixel_centers(1), pixel_centers(0)
art = np.array([[np.median(big[int(y) - 1:int(y) + 2, int(x) - 1:int(x) + 2].reshape(-1, 3), axis = 0) for x in columns] for y in rows])
# he is what is not the white around him
white = art.min(axis = 2) > 225
h, w = white.shape
seen = np.zeros((h, w), bool)
stack = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
while stack:
    y, x = stack.pop()
    if not (0 <= y < h and 0 <= x < w) or seen[y, x] or not white[y, x]: continue
    seen[y, x] = True
    stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
# nor the white that he closes in (between the runners of his sleigh): parts that are all pure white
for part in parts(white & ~seen):
    if np.median([art[y, x].min() for y, x in part]) >= 250:
        for y, x in part: seen[y, x] = True
ys, xs = np.nonzero(~seen)
rgb, opaque = art[ys.min():ys.max() + 1, xs.min():xs.max() + 1], ~seen[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
sh, sw = opaque.shape
SIZE = 128
assert sw <= SIZE and sh <= SIZE
santa_palette = snes(kmeans(rgb[opaque], 15))
pixels = np.zeros((SIZE, SIZE), int)
for y, x in np.argwhere(opaque):
    pixels[y, x] = ((santa_palette - rgb[y, x]) ** 2).sum(axis = 1).argmin() + 1
mold, graphics, count = [0] * 32, [], 0
for row in range(16):
    for column in range(16):
        t = pixels[row * 8:row * 8 + 8, column * 8:column * 8 + 8].reshape(-1)
        if t.any():
            bit = row * 16 + column
            mold[bit // 8] |= 0x80 >> (bit % 8)
            graphics += tile_4bpp(t, first_color = 0); count += 1
assert count <= KEFKA_TILES, f"santa has {count} tiles"
# his place: the runners of his sleigh (the last rows of his sprite) on the tree, their middle on its
# axis. a sprite is at 8 * its position + 1 on the screen, and tier 4's slice is cut to fit
SLEIGH_BOTTOM = 295                         # in the tree's picture: the row his runners are on
runners = np.nonzero(opaque[-12:].any(axis = 0))[0]
sleigh_middle = (runners.min() + runners.max()) / 2
POSITION = (round(((TREE_AXIS - LEFT) / SCALE - sleigh_middle - 1) / 8), 1)
tier_4_left = round(TREE_AXIS - SCALE * (8 * POSITION[0] + 1 + sleigh_middle))
tier_4_top = SLEIGH_BOTTOM - SCALE * (8 * POSITION[1] + 1 + sh)
print("santa", sw, "x", sh, "tiles", count, "position", POSITION, "tier 4 from", tier_4_left, tier_4_top)

data = {
    "backgrounds": {str(bg): background_data(bg, small(source, LEFT, top)) for bg, top in TIER_TOPS.items()},
    "santa": {
        "graphics": bytes(graphics).hex(), "mold": bytes(mold).hex(), "position": POSITION,
        "palette": bytes([0, 0] + sum(([color(c) & 0xff, color(c) >> 8] for c in santa_palette), [])).hex(),
    },
    # where the enemies of each tier are: a point on each reindeer, in the order of the formation's
    # slots that are used. x and y in steps of 8 pixels (15 at most), and how many more steps of 8
    # to the right (their sprite, one tile that is not seen, is that far into its mold): the hand
    # points at about 16 pixels right of and 12 below that
    "positions": {
        str(0x1d7): [[6, 11, 0], [15, 11, 3], [12, 7, 0]],                 # short arm, long arm, face: the three reindeer
        str(0x200): [[5, 10, 0], [15, 12, 2], [15, 9, 2], [11, 10, 0]],    # hit, tiger, tools, magic: the four of the middle
        str(0x201): [[10, 8, 0], [14, 8, 0]],                              # girl, sleep: the two under santa
    },
}
data["backgrounds"][str(0x36)] = background_data(0x36, small(source, tier_4_left, tier_4_top))
json.dump(data, open(out, "w"))
if preview:
    image = Image.new("RGB", (SIZE, SIZE), (255, 0, 255))
    for y in range(SIZE):
        for x in range(SIZE):
            if pixels[y, x]: image.putpixel((x, y), tuple(int(v) for v in santa_palette[pixels[y, x] - 1]))
    image.save(f"{preview}/santa.png")
