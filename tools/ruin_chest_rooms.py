"""Which ruination room holds each treasure chest.

usage: python3 tools/ruin_chest_rooms.py VANILLA.smc [--write]

Reads every chest (MIAB included) from the vanilla ROM, decodes each field
map's BG1 layout + tile properties, and floods each ruination room
(data/ruin_areas.RUIN_ROOM_SETS + hubs/termini) out from its door tiles:

  - movement follows the field code (C0/4E3D): the current tile's second
    property byte holds the directions it can be left by (up 08, right 01,
    down 04, left 02); a destination whose first byte has bits 0-2 all set
    is a wall; z-levels (bits 0-1: 1 upper, 2 lower, 3 both) and bridges
    (bit 2) gate steps; first-byte bit 6 / 7 make horizontal steps diagonal
    (up-right / up-left stairs, which ignore the exit bits);
  - property sets are planar (256 first bytes, then 256 second bytes);
  - doors are often wall tiles entered from the step tile below, so a door
    tile's neighbours seed the fill and an exit is taken from any tile next
    to it; exits that ruination does not shuffle carry the fill to their
    arrival point; shuffled doors and locked exits are room boundaries.

A chest belongs to a room whose region reaches its tile or a neighbour.
REVIEWED (HansGR, 2026-10-25) settles what the fill cannot: event-driven
areas (Magitek Factory, Zone Eater, Fanatic's Tower, the Sealed Gate cave,
Phoenix Cave, Floating Continent), NPC-blocked splits, WoB/WoR copies and
unused maps. Kefka's Tower chests are tallied apart (its lanes are not
branch rooms).

--write regenerates claude_reference/ruination_chests.csv (one row per
chest) and data/ruin_chests.py (ROOM_CHESTS: room -> chest count, used by
-rrtc). See ARCHIVE.md "Ruination treasure chests"."""
import os
import sys
import csv
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import doors.atlas as atlas
from data.rooms import room_data
from data.ruin_areas import RUIN_ROOM_SETS
from data.area_chests import area_chests
from data.event_exit_data import event_exit_info
from utils.compression import decompress

SIZES = [16, 32, 64, 128]
WORLD = {0x000, 0x001, 0x1ff}
EXTRA_ROOMS = {'HUB50-ruin', 'HUB52-ruin', 'HUB53-ruin', 'HUB54-ruin', 'DRM50-ruin'}
KT_CHESTS = set(range(173, 176)) | {182} | set(range(209, 219)) | {282, 283}
TYPE = {0x08: 'empty', 0x20: 'MIAB', 0x40: 'item', 0x80: 'gold'}

# chest id -> rooms ([] = never reachable in ruination)
REVIEWED_IDS = {}
for _i in range(1, 10): REVIEWED_IDS[_i] = ['NARr01-ruin']  # Narshe WoR treasure room, Arvis, Elder (0x1e)
REVIEWED_IDS[10] = REVIEWED_IDS[11] = ['NARr20']             # Moogle's Cave
REVIEWED_IDS[12] = REVIEWED_IDS[13] = ['NARr18']             # South Caves, 3-door room
for _i in (14, 15, 16): REVIEWED_IDS[_i] = []                # Narshe mines WoB copies (maps unused)
for _i in range(74, 78): REVIEWED_IDS[_i] = []               # Narshe School classrooms
for _i in range(191, 200): REVIEWED_IDS[_i] = ['MAPr-PHO']   # Phoenix Cave: all nine
for _i in range(267, 271): REVIEWED_IDS[_i] = ['MAPb-FLO']   # Floating Continent: all four (MIAB too)
for _i in (27, 28, 66): REVIEWED_IDS[_i] = []                # South Figaro cave WoR: unused
for _i in (67, 126, 202): REVIEWED_IDS[_i] = []              # Duncan WoB, Coliseum owner WoB, Albrook outside WoB
REVIEWED_IDS[203] = ['MAPr-ALB']                             # Albrook outside WoR (area_chests "duplicate")
REVIEWED_IDS[108] = []                                       # Mobliz bookshelf room
for _i in range(240, 253): REVIEWED_IDS[_i] = ['SEA03']      # Imperial Base basement
for _i in range(152, 158): REVIEWED_IDS[_i] = ['MTF03']      # Magitek Factory 2nd map
for _i in range(230, 236): REVIEWED_IDS[_i] = ['MAPr-FAN']   # Fanatic's Tower treasure rooms
for _i in range(43, 51): REVIEWED_IDS[_i] = []               # South Figaro outside WoB: ruination's town is WoR 0x4a
                                                             # (48-50 sit where WoR's 40-42 do); the fill leaks in via shared interiors
# (map, x, y) -> rooms
REVIEWED_XY = {
    (0x106, 14, 53): ['MTF01'],
    **{(0x106, x, y): ['MTF02'] for x, y in ((3, 25), (17, 27), (7, 44), (25, 52), (25, 44))},
    **{(0x114, x, y): ['ZON02'] for x, y in ((25, 31), (42, 32), (43, 32))},
    **{(0x114, x, y): ['ZON03'] for x, y in ((35, 16), (40, 13))},
    **{(0x118, x, y): ['ZON04b'] for x, y in ((27, 44), (41, 43), (46, 47))},
    (0x118, 1, 45): ['ZON06'],
    (0x17e, 36, 39): ['SEA04'], (0x17f, 48, 56): ['SEA05'], (0x180, 113, 6): ['SEA07'],
    (0x180, 29, 23): ['SEA08'], (0x180, 47, 11): ['SEA08'],
    (0x180, 71, 30): ['SEA09'], (0x180, 88, 23): ['SEA09'],
    **{(0x180, x, y): ['SEA10'] for x, y in ((88, 53), (89, 51), (91, 49), (92, 49))},
    (0x181, 3, 8): ['SEA11'], (0x181, 14, 4): ['SEA11'], (0x182, 77, 52): ['SEA12'],
    (0x60, 27, 14): ['MTK05'], (0x60, 28, 27): ['MTK03'], (0x61, 27, 14): [], (0x61, 28, 27): [],
    (0x4a, 22, 18): ['MAPr-SFI'],                # reached through the houses
    (0x7b, 33, 34): [],                          # replica of the chest on 0x7c
    (0x90, 25, 5): ['CDA04'],                    # an event tile changes the map
    (0xaf, 52, 11): ['SER02'],
    (0x93, 5, 5): ['PHT10a'],                    # blocked by NPCs, not the map
    (0x99, 20, 7): ['PHT07a'], (0x99, 21, 7): ['PHT07a'],
    **{(0x99, x, 24): ['PHT07b'] for x in (22, 23, 24, 25)},
    (0x11a, 13, 34): ['UMA04a'], (0x11a, 14, 25): ['UMA04b'],
    **{(0xb3, x, y): ['MTZ04'] for x, y in ((19, 30), (11, 21), (13, 16), (3, 51))},
}
REVIEWED_MAPS = {}
# chests WC copies onto another map (data/chests.py copy_thamasa_chests: the
# pre-Leo Thamasa map's five go to the WoB and WoR towns): placed on the copy
CHEST_COPIES = {0x157: 0x158}
# rooms whose chests only open up with a check: they count only when the
# check can be done (its reward owners are in the game)
CHEST_GATES = {'MAPr-TZE': 'Collapsing House'}  # Tzen's 8 are inside the collapsing house


class Rom:
    def __init__(self, path):
        self.d = open(path, 'rb').read()

    def u(self, a, n):
        return int.from_bytes(self.d[a:a + n], 'little')

    def lz(self, a):
        return decompress(list(self.d[a:a + self.u(a, 2)]))


def load_map(rom, m):
    p = rom.d[0x2d8f00 + m * 33:0x2d8f00 + m * 33 + 33]
    bg1 = int.from_bytes(p[0x0d:0x11], 'little') & 0x3ff
    w, h = SIZES[(p[0x17] >> 6) & 3], SIZES[(p[0x17] >> 4) & 3]
    tiles = rom.lz(0x19d1b0 + rom.u(0x19cd90 + 3 * bg1, 3)) if bg1 else []
    tp = rom.lz(0x19a800 + rom.u(0x19cd10 + 2 * p[4], 2))
    half = len(tp) // 2
    return dict(w=w, h=h, tiles=tiles, props=[(tp[i], tp[half + i]) for i in range(half)])


def prop(M, x, y):
    if M is None or not (0 <= x < M['w'] and 0 <= y < M['h']):
        return None
    i = y * M['w'] + x
    if i >= len(M['tiles']):
        return None
    t = M['tiles'][i]
    return M['props'][t] if t < len(M['props']) else None


def base(e):
    return e - 4000 if e >= 4000 else e


def tiles_of(e):
    rec = atlas.exit_record(e)
    if rec and rec.get('map') is not None:
        if rec.get('kind') == 'long':
            if rec.get('direction') == 'vertical':
                return [(rec['map'], rec['x'], rec['y'] + i) for i in range(rec['size'])]
            return [(rec['map'], rec['x'] + i, rec['y']) for i in range(rec['size'])]
        return [(rec['map'], rec['x'], rec['y'])]
    info = event_exit_info.get(e)
    if info and info[5] and info[5][1] is not None:
        return [tuple(info[5])]
    return []


STEP = [(0x08, 0, -1), (0x01, 1, 0), (0x04, 0, 1), (0x02, -1, 0)]
NEIGH = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))


class Flood:
    def __init__(self, rom):
        self.rom = rom
        self.maps = {}
        self.rooms = {r for rs in RUIN_ROOM_SETS.values() for r in rs} | EXTRA_ROOMS
        self.room_doors, rando = {}, set()
        for rid in self.rooms:
            spec = room_data.get(rid)
            if not spec:
                continue
            self.room_doors[rid] = [base(e) for e in spec[0] if isinstance(e, int)]
            rando.update(self.room_doors[rid])
            for part in spec[3:]:               # locked exits are shuffled doors too
                if isinstance(part, dict):
                    for items in part.values():
                        rando.update(base(e) for e in items if isinstance(e, int))
        self.static_at = {}
        for e, rec in atlas.EXIT_RECORDS.items():
            if not rec or e in rando or rec.get('map') is None or rec.get('dest_map') is None:
                continue
            if rec['map'] in WORLD or rec['dest_map'] in WORLD:
                continue
            for t in tiles_of(e):
                self.static_at[t] = (rec['dest_map'], rec['dest_x'], rec['dest_y'])
        self.shuffled_tiles = {t for e in rando for t in tiles_of(e)}

    def mp(self, m):
        if m not in self.maps:
            try:
                self.maps[m] = load_map(self.rom, m)
            except Exception:
                self.maps[m] = None
        return self.maps[m]

    def moves(self, m, x, y, z):
        M = self.mp(m)
        cur = prop(M, x, y)
        if cur is None:
            return
        c1, c2 = cur
        stairs = c1 & 0xc0
        for bit, dx, dy in STEP:
            if not c2 & bit and not (stairs and dy == 0):
                continue
            nx, ny = x + dx, y + dy
            if dy == 0 and c1 & 0x40:
                ny = y - dx
            elif dy == 0 and c1 & 0x80:
                ny = y + dx
            dst = prop(M, nx, ny)
            if dst is None or dst[0] & 7 == 7:
                continue
            d1 = dst[0]
            if c1 & 4:
                if (z == 1 and d1 & 2) or (z == 2 and d1 & 1):
                    continue
            else:
                c, t = c1 & 3, d1 & 3
                if t != 3:
                    if c == 3:
                        if d1 & 4:
                            continue
                    elif t & (c ^ 3):
                        continue
            t = d1 & 3
            yield nx, ny, (z if (d1 & 4 or t in (0, 3)) else t)

    def region(self, rid):
        seeds = [t for e in self.room_doors.get(rid, []) for t in tiles_of(e)]
        seen, todo, seed_set, tiles = set(), [], set(), set()
        for (m, x, y) in seeds:
            if self.mp(m) is None:
                continue
            for dx, dy in NEIGH:
                seed_set.add((m, x + dx, y + dy))
                todo += [(m, x + dx, y + dy, 1), (m, x + dx, y + dy, 2)]
        while todo:
            s = todo.pop()
            if s in seen:
                continue
            seen.add(s)
            m, x, y, z = s
            here = prop(self.mp(m), x, y)
            if here is None or here[0] & 7 == 7:
                continue
            tiles.add((m, x, y))
            for dx, dy in NEIGH:
                t = (m, x + dx, y + dy)
                if t in self.static_at:
                    dm, ax, ay = self.static_at[t]
                    if self.mp(dm) is not None:
                        todo += [(dm, ax, ay, 1), (dm, ax, ay, 2)]
            if (m, x, y) in self.shuffled_tiles and (m, x, y) not in seed_set:
                continue
            for nx, ny, nz in self.moves(m, x, y, z):
                todo.append((m, nx, ny, nz))
        return tiles


def read_chests(rom):
    d = rom.d
    ptrs, ptrs_end, data = 0x2d82f4, 0x2d8633, 0x2d8634
    ptr = [int.from_bytes(d[ptrs + 2 * i:ptrs + 2 * i + 2], 'little')
           for i in range((ptrs_end + 1 - ptrs) // 2)]
    area_of = {i: n for n, ids in area_chests.items() for i in ids}
    out, cid = [], 0
    for m in range(len(ptr) - 1):
        for o in range(ptr[m], ptr[m + 1], 5):
            b = d[data + o:data + o + 5]
            out.append(dict(id=cid, map=m, x=b[0], y=b[1], type=b[3] & 0xfe,
                            area=area_of.get(cid)))
            cid += 1
    return out


def map_names():
    import re
    path = os.path.join(ROOT, 'claude_reference', 'ff3infov2.txt')
    names = {}
    if os.path.exists(path):
        txt = open(path, encoding='latin-1').read()
        i = txt.find('Locations\n\n000')
        for line in txt[i:i + 40000].splitlines()[2:]:
            m = re.match(r'^([0-9A-F]{3})\s+(.*)$', line)
            if m:
                names[int(m.group(1), 16)] = m.group(2).strip()
    return names


def assign(rom):
    """[(chest, rooms, how)] for every real chest (area_chests lists it),
    Kefka's Tower's flagged 'kt'."""
    fl = Flood(rom)
    regions = {rid: fl.region(rid) for rid in sorted(fl.room_doors)}
    out = []
    for c in read_chests(rom):
        if c['area'] is None and c['id'] != 203:
            continue                            # area_chests leaves it out: unreachable/duplicate
        if c['id'] in KT_CHESTS:
            out.append((c, ['KT'], 'kt'))
            continue
        if c['map'] in CHEST_COPIES:
            c = dict(c, map=CHEST_COPIES[c['map']])
        key = (c['map'], c['x'], c['y'])
        if c['id'] in REVIEWED_IDS:
            out.append((c, REVIEWED_IDS[c['id']], 'reviewed'))
        elif key in REVIEWED_XY:
            out.append((c, REVIEWED_XY[key], 'reviewed'))
        elif c['map'] in REVIEWED_MAPS:
            out.append((c, REVIEWED_MAPS[c['map']], 'reviewed'))
        else:
            near = {(c['map'], c['x'] + dx, c['y'] + dy) for dx, dy in NEIGH}
            rooms = sorted(r for r, reg in regions.items() if near & reg)
            out.append((c, rooms, 'flood' if len(rooms) == 1 else
                        ('flood-ambiguous' if rooms else 'unassigned')))
    return out


def main():
    rom = Rom(sys.argv[1])
    rows = assign(rom)
    how = collections.Counter(h for _, _, h in rows)
    print('chests', len(rows), dict(how))
    for c, rooms, h in rows:
        if h in ('flood-ambiguous', 'unassigned'):
            print('  open:', c['id'], c['area'], hex(c['map']), (c['x'], c['y']), rooms)
    if '--write' not in sys.argv:
        return
    names = map_names()
    with open(os.path.join(ROOT, 'claude_reference', 'ruination_chests.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['chest_id', 'area', 'map', 'map_name', 'x', 'y', 'type', 'rooms', 'how'])
        for c, rooms, h in rows:
            w.writerow([c['id'], c['area'] or "Albrook Outside WOR", hex(c['map']), names.get(c['map'], ''),
                        c['x'], c['y'], TYPE.get(c['type'], hex(c['type'])),
                        ' '.join(rooms) or '(unreachable)', h])
    counts = collections.Counter()
    for c, rooms, h in rows:
        if h != 'kt' and len(rooms) == 1:
            counts[rooms[0]] += 1
    kt = sum(1 for _, _, h in rows if h == 'kt')
    with open(os.path.join(ROOT, 'data', 'ruin_chests.py'), 'w') as f:
        f.write('"""Treasure chests (MIAB included) per ruination room, outside Kefka\'s Tower.\n'
                'Generated by tools/ruin_chest_rooms.py from the vanilla ROM; per-chest table in\n'
                'claude_reference/ruination_chests.csv. Used by -rrtc."""\n\n')
        f.write(f'KT_CHESTS = {kt}          # Kefka\'s Tower lanes (not branch rooms)\n\n')
        f.write('ROOM_CHESTS = {\n')
        for rid in sorted(counts):
            f.write(f'    {rid!r}: {counts[rid]},\n')
        f.write('}\n\n')
        f.write('# rooms whose chests count only when this check can be done\n')
        f.write(f'CHEST_GATES = {CHEST_GATES!r}\n')
    print('wrote claude_reference/ruination_chests.csv and data/ruin_chests.py:',
          sum(counts.values()), 'chests in', len(counts), 'rooms;', kt, 'in Kefka\'s Tower')


if __name__ == '__main__':
    main()
