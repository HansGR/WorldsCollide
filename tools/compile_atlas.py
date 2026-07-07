"""Atlas compiler for door randomization (rewrite Stage A).

Derives the mechanical layer of the door-rando atlas from the vanilla ROM
data dumps in claude_reference/ and cross-checks it against the curated
tables in data/map_exit_extra.py:

  1. Assigns every vanilla exit (short 0-1128, long 1129-1280) to its map
     using the per-map exit counts (the same concatenation convention
     Maps.exit_maps uses), giving each exit a ROM-free record of
     kind/map/position/destination.
  2. Derives each exit's vanilla PARTNER (the door you return through)
     from destination coordinates + round-trip agreement, instead of
     trusting the hand-maintained partner column.
  3. Applies the explicit curation in doors/atlas/curation.py (semantic
     choices coordinates cannot express: world-return doors, shared
     interiors, event-mediated doors, unused exits).
  4. Verifies the result reproduces data/map_exit_extra.exit_data exactly
     for every vanilla exit, and reports every non-derived entry with its
     category - so any future edit to either side that breaks agreement
     fails loudly.

Usage:
    python3 tools/compile_atlas.py            # check + emit doors/atlas/compiled.py
    python3 tools/compile_atlas.py --check    # verify only (exit code 1 on failure)
    python3 tools/compile_atlas.py --report   # verbose per-category report

Runs without a ROM: only the reference JSONs and importable data tables
are consulted.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

WORLD_RETURN = 511      # dest_map sentinel: "return to parent (world) map"
WORLD_MAPS = (0, 1)     # WoB, WoR
NUM_SHORT = 1129
NUM_EXITS = 1281        # short + long
MAX_SNAP = 3            # max Chebyshev distance between arrival point and partner tile


def _load_curation():
    """Load doors/atlas/curation.py directly by path.

    The compiler is the producer of doors/atlas/compiled.py; importing the
    doors.atlas package here would require compiled.py to already be up to
    date (bootstrap circle), so curation is loaded standalone.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'atlas_curation', os.path.join(ROOT, 'doors/atlas/curation.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_exit_records():
    """Build one record per vanilla exit, keyed by global exit id.

    Global ids follow the ROM convention Maps.exit_maps re-derives at
    runtime: short exits concatenated in map order (0-1128), then long
    exits (1129-1280).
    """
    with open(os.path.join(ROOT, 'claude_reference/exits_raw.json')) as f:
        raw = json.load(f)
    with open(os.path.join(ROOT, 'claude_reference/maps_data.json')) as f:
        maps_data = json.load(f)

    num_short = {m['map_id']: len(m['short_exits']) for m in maps_data}
    num_long = {m['map_id']: len(m['long_exits']) for m in maps_data}

    exit_map = {}
    gid = 0
    for map_id in sorted(num_short):
        for _ in range(num_short[map_id]):
            exit_map[gid] = map_id
            gid += 1
    if gid != NUM_SHORT:
        raise AssertionError(f'short exit count {gid} != {NUM_SHORT}')
    for map_id in sorted(num_long):
        for _ in range(num_long[map_id]):
            exit_map[gid] = map_id
            gid += 1
    if gid != NUM_EXITS:
        raise AssertionError(f'total exit count {gid} != {NUM_EXITS}')

    records = {}
    for i, r in enumerate(raw['short_exits']):
        if r['index'] != i:
            raise AssertionError(f'short exit {i} has index {r["index"]}')
        records[i] = {
            'kind': 'short', 'map': exit_map[i],
            'x': r['x'], 'y': r['y'], 'size': 1, 'direction': None,
            'dest_map': r['dest_map'], 'dest_x': r['dest_x'], 'dest_y': r['dest_y'],
        }
    for i, r in enumerate(raw['long_exits']):
        if r['index'] != i:
            raise AssertionError(f'long exit {i} has index {r["index"]}')
        gid = NUM_SHORT + i
        records[gid] = {
            'kind': 'long', 'map': exit_map[gid],
            'x': r['x'], 'y': r['y'], 'size': r['size'], 'direction': r['direction'],
            'dest_map': r['dest_map'], 'dest_x': r['dest_x'], 'dest_y': r['dest_y'],
        }
    return records


def load_event_tiles():
    """Event-tile records with map assignment (same concatenation convention).

    Used to validate the 'event-tile-return' tag: a door whose return is an
    event tile has no vanilla exit partner, but an event tile must exist
    near its arrival point.
    """
    with open(os.path.join(ROOT, 'claude_reference/events_raw.json')) as f:
        raw = json.load(f)
    with open(os.path.join(ROOT, 'claude_reference/maps_data.json')) as f:
        maps_data = json.load(f)
    num_events = {m['map_id']: len(m['events']) for m in maps_data}
    tiles = []
    gid = 0
    for map_id in sorted(num_events):
        for _ in range(num_events[map_id]):
            r = raw[gid]
            tiles.append({'map': map_id, 'x': r['x'], 'y': r['y']})
            gid += 1
    if gid != len(raw):
        raise AssertionError(f'event tile count mismatch: {gid} != {len(raw)}')
    return tiles


def _event_tile_near(tiles, map_id, x, y, snap=MAX_SNAP):
    return any(t['map'] == map_id and max(abs(t['x'] - x), abs(t['y'] - y)) <= snap
               for t in tiles)


def load_oneway_records():
    """Trap and event-door records from data.event_exit_data (ROM-free).

    Traps (2000-2999, plus '2035a'-style variants) are one-way exits; their
    pit twin (trap + 1000) is purely logical - the landing side of the
    connection - and has no record of its own. Event doors (1500-1999, plus
    logical WoR copies at +4000) are doors realized as event tiles.
    Returns (traps, event_doors): {id: {'map','x','y','desc'}}.
    """
    from data.event_exit_data import event_exit_info
    traps, event_doors = {}, {}
    for eid, info in event_exit_info.items():
        loc, desc = info[5], info[4]
        rec = {'map': loc[0], 'x': loc[1], 'y': loc[2], 'desc': desc}
        if isinstance(eid, str) or 2000 <= eid < 3000:
            traps[eid] = rec
        else:
            event_doors[eid] = rec
    return traps, event_doors


def build_extended_partners(records):
    """Vanilla partner table extended with the event-door and logical-WoR
    layers carried from exit_data (they are curated there, not derivable;
    the compiler validates their structure and copies them).
    """
    from data.map_exit_extra import exit_data
    final, derived = build_partner_table(records)
    extended = dict(final)
    for key, entry in exit_data.items():
        if isinstance(key, int) and (1500 <= key < 2000 or 4000 <= key < 6000):
            extended[key] = entry[0]
    return extended, final, derived


def _span(rec):
    """Tile positions covered by an exit (long exits span several)."""
    if rec['kind'] == 'short' or rec['size'] <= 1:
        return [(rec['x'], rec['y'])]
    if rec['direction'] == 'horizontal':
        return [(rec['x'] + i, rec['y']) for i in range(rec['size'])]
    return [(rec['x'], rec['y'] + i) for i in range(rec['size'])]


def _dist(rec, x, y):
    """Chebyshev distance from point (x, y) to the exit's tile span."""
    return min(max(abs(px - x), abs(py - y)) for (px, py) in _span(rec))


def derive_partners(records):
    """Derive each exit's vanilla partner from coordinates.

    The partner of exit X is the exit standing at (or next to) X's arrival
    point whose own destination leads back to X's map near X's position.
    Exits to the world map (dest_map == WORLD_RETURN) are matched against
    both world maps; the round-trip test picks the right world when the
    coordinates alone are ambiguous. Returns {id: partner id or None}.
    """
    by_map = {}
    for gid, rec in records.items():
        by_map.setdefault(rec['map'], []).append(gid)

    partners = {}
    for gid, rec in sorted(records.items()):
        dest_map = rec['dest_map']
        candidate_maps = WORLD_MAPS if dest_map == WORLD_RETURN else (dest_map,)
        dx, dy = rec['dest_x'], rec['dest_y']
        best, best_score = None, None
        for cm in candidate_maps:
            for cid in by_map.get(cm, ()):
                if cid == gid:
                    continue
                cand = records[cid]
                d_here = _dist(cand, dx, dy)
                if d_here > MAX_SNAP:
                    continue
                # Round trip: does the candidate lead back to us?
                if cand['dest_map'] == rec['map'] or \
                        (cand['dest_map'] == WORLD_RETURN and rec['map'] in WORLD_MAPS):
                    d_back = _dist(rec, cand['dest_x'], cand['dest_y'])
                else:
                    d_back = 50  # no round trip: usable only if nothing better
                score = (d_here + d_back, d_here, cid)
                if best_score is None or score < best_score:
                    best_score, best = score, cid
        if best is None:
            # Reverse fallback: some arrivals land far from the return door
            # (drops/falls, e.g. KT falldown 885 lands 5 tiles above 1110).
            # Accept a unique exit on the destination map whose OWN
            # destination points back at us within snap distance.
            reverse = [cid for cm in candidate_maps for cid in by_map.get(cm, ())
                       if cid != gid
                       and records[cid]['dest_map'] == rec['map']
                       and _dist(rec, records[cid]['dest_x'], records[cid]['dest_y']) <= MAX_SNAP]
            if len(reverse) == 1:
                best = reverse[0]
        partners[gid] = best
    return partners


def build_partner_table(records):
    """Derived partners with curation applied: the atlas's final answer."""
    curation = _load_curation()
    partners = derive_partners(records)
    final = {}
    for gid in sorted(records):
        if gid in curation.PARTNER_OVERRIDES:
            final[gid] = curation.PARTNER_OVERRIDES[gid][0]
        elif gid in curation.NO_VANILLA_PARTNER:
            final[gid] = None
        else:
            final[gid] = partners[gid]
    return final, partners


def check(records, report=False):
    """Verify the atlas reproduces data/map_exit_extra.exit_data exactly.

    Every vanilla exit must either derive to the curated partner, or be
    explained by an entry in curation (with a reason). Returns the number
    of failures.
    """
    from data.map_exit_extra import exit_data
    from data.rooms import shared_exits
    curation = _load_curation()

    extended, final, derived = build_extended_partners(records)

    failures = []
    stats = {'derived': 0, 'override': 0, 'no-partner': 0}
    shared_group = {}
    for k, sibs in shared_exits.items():
        group = {k, *sibs}
        for member in group:
            shared_group.setdefault(member, set()).update(group)

    for gid in sorted(records):
        curated = exit_data.get(gid)
        if curated is None:
            failures.append(f'exit {gid}: present in ROM data but missing from exit_data')
            continue
        curated_partner = curated[0]

        if final[gid] != curated_partner:
            failures.append(
                f'exit {gid} ({curated[1]}): atlas says {final[gid]}, '
                f'exit_data says {curated_partner} (derived: {derived[gid]})')
            continue

        if gid in curation.PARTNER_OVERRIDES:
            stats['override'] += 1
            # Overrides should stay honest: if derivation now agrees, the
            # override is stale and should be deleted.
            if derived[gid] == curated_partner:
                failures.append(
                    f'exit {gid}: PARTNER_OVERRIDES entry is redundant '
                    f'(derivation already yields {curated_partner})')
        elif gid in curation.NO_VANILLA_PARTNER:
            stats['no-partner'] += 1
        else:
            stats['derived'] += 1

    # Shared-exit groups (multi-tile doorways sharing one destination): all
    # members must resolve to the same partner. This also makes the silent
    # reciprocity exemption below auditable - use --report to list groups.
    seen_groups = set()
    for member, group in shared_group.items():
        key = tuple(sorted(group, key=str))
        if key in seen_groups:
            continue
        seen_groups.add(key)
        group_partners = {final[m] for m in group if m in final}
        if len(group_partners) > 1:
            # Partners may legitimately differ if they are sibling tiles of
            # one doorway themselves (normalize logical-WoR ids to their
            # base first, e.g. Nikeah tiles 65/66 -> 5199/5200 -> 1199/1200).
            bases = {p - 4000 if isinstance(p, int) and 4000 <= p < 6000 else p
                     for p in group_partners}
            sample = next(iter(bases))
            if not (len(bases) == 1 or
                    (isinstance(sample, int) and bases <= shared_group.get(sample, set()) | {sample})):
                failures.append(
                    f'shared-exit group {sorted(group, key=str)}: members resolve to '
                    f'different partners {sorted(group_partners, key=str)}')

    # NO_VANILLA_PARTNER tags are validated mechanically where possible:
    #   door-as-trap      must be listed in data.rooms.doors_as_traps
    #   event-tile-return an event tile must exist near the arrival point
    #   unreachable       must be neither of the above
    from data.rooms import doors_as_traps
    tiles = load_event_tiles()
    for gid, tag in curation.NO_VANILLA_PARTNER.items():
        rec = records.get(gid)
        if rec is None:
            failures.append(f'NO_VANILLA_PARTNER {gid}: no such exit')
            continue
        is_trap = gid in doors_as_traps
        near_tile = _event_tile_near(tiles, rec['dest_map'], rec['dest_x'], rec['dest_y'])
        if tag == 'door-as-trap' and not is_trap:
            failures.append(f'NO_VANILLA_PARTNER {gid}: tagged door-as-trap but not in doors_as_traps')
        elif tag == 'event-tile-return' and not near_tile:
            failures.append(f'NO_VANILLA_PARTNER {gid}: tagged event-tile-return but no event tile near arrival')
        elif tag in ('unreachable', 'scenario-variant') and is_trap:
            failures.append(f'NO_VANILLA_PARTNER {gid}: tagged {tag} but is a door-as-trap')
    for gid in doors_as_traps:
        if gid in curation.NO_VANILLA_PARTNER and curation.NO_VANILLA_PARTNER[gid] != 'door-as-trap':
            failures.append(f'{gid}: in doors_as_traps but tagged {curation.NO_VANILLA_PARTNER[gid]}')

    # Reciprocity: partner(partner(x)) == x over the EXTENDED table (vanilla
    # exits + event doors + logical-WoR copies), except where curation
    # declares the pairing asymmetric (multi-tile entrances, WoB/WoR shared
    # interiors, dead returns, event-mediated chains). Declared entries must
    # actually be asymmetric, so a stale declaration also fails. Sibling
    # groups apply across the +4000 layer (5199/5200 are siblings because
    # 1199/1200 are).
    def sibling_set(gid):
        if isinstance(gid, int) and 4000 <= gid < 6000:
            return {s + 4000 for s in shared_group.get(gid - 4000, ())}
        return shared_group.get(gid, set())

    for gid, partner in extended.items():
        if partner is None or not isinstance(partner, int) or partner not in extended:
            continue
        back = extended[partner]
        reciprocal = (back == gid) or \
                     (back is not None and back in sibling_set(gid))
        declared = gid in curation.ASYMMETRIC_PARTNERS
        if reciprocal and declared:
            failures.append(
                f'exit {gid}: ASYMMETRIC_PARTNERS entry is stale (pairing is reciprocal)')
        elif not reciprocal and not declared:
            failures.append(
                f'reciprocity: {gid} -> {partner} but {partner} -> {back} '
                f'(declare in ASYMMETRIC_PARTNERS with a tag if intentional)')

    failures += check_layers(records)
    failures += check_rooms(records)
    failures += check_room_names()
    failures += check_realization(records)
    failures += check_pools(records)

    if report:
        print(f"derived: {stats['derived']}  overrides: {stats['override']}  "
              f"no-partner: {stats['no-partner']}  failures: {len(failures)}")
        by_reason = {}
        for gid, (partner, reason) in sorted(curation.PARTNER_OVERRIDES.items()):
            by_reason.setdefault(reason, []).append(gid)
        for reason, gids in sorted(by_reason.items()):
            print(f'  [{reason}] {len(gids)}: {gids}')
        # Multi-tile doorways whose reciprocity resolves through a sibling
        # tile (handled automatically; listed here so the handling is
        # visible rather than silent).
        sibling_recip = []
        for gid, partner in sorted(final.items(), key=lambda kv: str(kv[0])):
            if partner is None or not isinstance(partner, int) or partner not in final:
                continue
            back = final[partner]
            if back != gid and back is not None and back in shared_group.get(gid, ()):
                sibling_recip.append((gid, partner, back))
        print(f'  reciprocal-via-sibling-tile ({len(sibling_recip)}):')
        for gid, partner, back in sibling_recip:
            print(f'    {gid} -> {partner} -> {back} (sibling of {gid})')

    for f in failures:
        print('FAIL:', f)
    return len(failures)


def check_layers(records):
    """Validate the non-vanilla id layers against each other.

    - exit_data's event-door (1500+) and trap (2000+) entries must exist in
      event_exit_info (they describe the same objects);
    - logical ids (+4000) must have a base in the vanilla records or the
      event-door table;
    - eei's own logical entries likewise.
    """
    from data.map_exit_extra import exit_data
    from data.event_exit_data import event_exit_info as eei
    failures = []
    for key, entry in exit_data.items():
        if not isinstance(key, int) or key < 1281:
            continue
        if 1500 <= key < 2000 or 2000 <= key < 3000:
            # Partner-less trap entries are description-only stubs (e.g. 2018,
            # whose one-way is realized by its sibling's event script).
            if key not in eei and entry[0] is not None:
                failures.append(
                    f'exit_data[{key}] ({entry[1]}): no event_exit_info record')
        elif 4000 <= key < 6000:
            base = key - 4000
            if base not in records and base not in eei:
                failures.append(
                    f'exit_data[{key}] ({entry[1]}): logical id has no base exit {base}')
    for eid in eei:
        if isinstance(eid, int) and 4000 <= eid < 6000:
            if (eid - 4000) not in eei:
                failures.append(
                    f'event_exit_info[{eid}]: logical event door has no base {eid - 4000}')
    return failures


# All world event-door tiles (both worlds) live on the shared world event
# layer, map 5 - a virtual layer, not a physical map. Rooms may pair such a
# tile with physical exits (world rooms, Phoenix Cave 536), so map 5 never
# counts toward a room's physical-map coherence.
WORLD_EVENT_LAYER = 5


def check_rooms(records):
    """Validate room_data's element references against the layered id space.

    Every element of every room must resolve: vanilla exits (0-1280) to the
    exit records; event doors (1500-1999, and +4000 logical copies) to
    event_exit_info; traps (2000-2999) to event_exit_info OR to the
    'trickery' shape (a logical reward-route one-way: no ROM record, but a
    forced connection onto its own +1000 pit); pits (3000-3999) to a trap
    twin; door-as-trap pits (6000-7999) to a base door; synthetic ids
    (10000+) are the planner's own. Physical (int-id) rooms must not span
    maps, except within the world cluster.
    """
    from data.rooms import room_data, forced_connections, doors_as_traps
    from data.event_exit_data import event_exit_info as eei
    failures = []

    def trap_exists(t):
        if t in eei:
            return True
        # Trickery one-way: forced onto its own logical pit.
        return t in forced_connections and forced_connections[t] == [t + 1000]

    for rid, rd in room_data.items():
        doors, traps, pits = rd[0], rd[1], rd[2]
        maps = set()
        for d in doors:
            if not isinstance(d, int):
                failures.append(f'room {rid!r}: non-int door {d!r}')
            elif d < 1281:
                if d in records:
                    maps.add(records[d]['map'])
                else:
                    failures.append(f'room {rid!r}: unknown vanilla exit {d}')
            elif d < 1500:
                failures.append(f'room {rid!r}: door {d} in reserved range 1281-1499')
            elif d < 2000:
                if d in eei:
                    maps.add(eei[d][5][0])
                else:
                    failures.append(f'room {rid!r}: event door {d} not in event_exit_info')
            elif d < 4000:
                failures.append(f'room {rid!r}: trap/pit id {d} listed as a door')
            elif d < 6000:
                if (d - 4000) not in records and (d - 4000) not in eei:
                    failures.append(f'room {rid!r}: logical door {d} has no base exit')
            elif d < 10000:
                failures.append(f'room {rid!r}: door {d} in unassigned range')
            # >= 10000: synthetic (roots, crossworld, shuffle-protected) - planner-owned
        for t in traps:
            if isinstance(t, str):
                if t not in eei:
                    failures.append(f'room {rid!r}: variant trap {t!r} not in event_exit_info')
            elif t < 1281:
                # A door acting as a one-way exit (its landing is 6000 + id).
                if t not in doors_as_traps:
                    failures.append(
                        f'room {rid!r}: door {t} in trap bucket but not in doors_as_traps')
                elif t in records:
                    maps.add(records[t]['map'])
                else:
                    failures.append(f'room {rid!r}: door-as-trap {t} is not a vanilla exit')
            elif 2000 <= t < 3000:
                if not trap_exists(t):
                    failures.append(
                        f'room {rid!r}: trap {t} has no event_exit_info record '
                        f'and is not a forced trickery one-way')
            elif 6000 <= t < 8000:
                if (t - 6000) not in records:
                    failures.append(f'room {rid!r}: door-as-trap {t} has no base door')
            else:
                failures.append(f'room {rid!r}: trap id {t} out of range')
        for p in pits:
            if isinstance(p, str):
                continue
            if 3000 <= p < 4000:
                if not trap_exists(p - 1000) and \
                        not any(isinstance(k, str) and k.startswith(str(p - 1000)) for k in eei):
                    failures.append(f'room {rid!r}: pit {p} has no trap twin {p - 1000}')
            elif 6000 <= p < 8000:
                if (p - 6000) not in records:
                    failures.append(f'room {rid!r}: door-as-trap pit {p} has no base door')
            else:
                failures.append(f'room {rid!r}: pit id {p} out of range')
        # Physical rooms are single-map (ignoring the virtual world layer).
        maps.discard(WORLD_EVENT_LAYER)
        if isinstance(rid, int) and len(maps) > 1:
            failures.append(f'room {rid!r}: elements span maps {sorted(maps)}')
    return failures


def check_room_names():
    """Validate doors/atlas/room_names.py against data/rooms.room_data.

    Bijection (every room mapped, no extras), unique names, area code
    registered, and the world letter consistent with the room's world
    field (b=0, r=1, x=None). Kefka's Tower rooms may keep their legacy
    structured ids (KTa1...).
    """
    import importlib.util, re
    spec = importlib.util.spec_from_file_location(
        'atlas_room_names', os.path.join(ROOT, 'doors/atlas/room_names.py'))
    rn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rn)
    from data.rooms import room_data
    failures = []

    mapped, rooms = set(rn.ROOM_NAMES), set(room_data)
    for missing in sorted(rooms - mapped, key=str):
        failures.append(f'room_names: room {missing!r} has no atlas name')
    for extra in sorted(mapped - rooms, key=str):
        failures.append(f'room_names: {extra!r} is not a room_data room')

    seen = {}
    pat = re.compile(r'^([A-Z][A-Z0-9])([brx])(\d{2,3})([a-z]*)(-[a-z-]+)?$')
    kt_pat = re.compile(r'^KT[abcx]?\d*[ab]?(-[a-z-]+)?$')
    for rid, name in rn.ROOM_NAMES.items():
        if name in seen:
            failures.append(f'room_names: {name!r} used by both {seen[name]!r} and {rid!r}')
        seen[name] = rid
        if name == str(rid) and name.startswith('KT'):
            # Kefka's Tower rooms keep their legacy structured ids; the
            # letter is the LANE (a/b/c), not a world marker.
            continue
        m = pat.match(name)
        if not m:
            if kt_pat.match(name):
                continue
            failures.append(f'room_names: {rid!r} -> {name!r} does not match the format')
            continue
        code, world = m.group(1), m.group(2)
        if code not in rn.AREA_CODES:
            failures.append(f'room_names: {rid!r} -> {name!r}: code {code!r} not in AREA_CODES')
        if rid in room_data:
            rd = room_data[rid]
            w = rd[5] if len(rd) == 6 else rd[3]
            expect = {0: 'b', 1: 'r'}.get(w, 'x')
            if world != expect:
                failures.append(
                    f'room_names: {rid!r} -> {name!r}: world letter {world!r} '
                    f'but room world field says {expect!r}')
    return failures


def check_realization(records):
    """Structural validation of the realization-time edit tables.

    These tables stay in data/map_exit_extra.py (they are consumed at ROM
    write time); the atlas validates that every id they name resolves
    through the layered id space, so a typo'd key fails the build here
    instead of silently patching nothing.
    """
    from data.map_exit_extra import (exit_data, exit_data_patch, exit_make_explicit,
                                     dungeon_crawl_exit_destination_override,
                                     event_door_connection_data)
    from data.event_exit_data import event_exit_info as eei
    failures = []

    def resolves(key):
        if not isinstance(key, int):
            return False
        if key in records or key in eei:
            return True
        if 4000 <= key < 6000:
            return (key - 4000) in records or (key - 4000) in eei
        return False

    for name, table in (('exit_data_patch', exit_data_patch),
                        ('exit_make_explicit', exit_make_explicit),
                        ('dungeon_crawl_exit_destination_override',
                         dungeon_crawl_exit_destination_override),
                        ('event_door_connection_data', event_door_connection_data)):
        for key in table:
            if not resolves(key):
                failures.append(f'{name}[{key!r}]: id does not resolve to any exit layer')
    for key, val in dungeon_crawl_exit_destination_override.items():
        if len(val) != 13:
            failures.append(
                f'dungeon_crawl_exit_destination_override[{key}]: expected 13 fields, got {len(val)}')

    # Maps.door_rando_cleanup relocates the redundant-shadow exits; the
    # curation tags and the cleanup routine must agree.
    curation = _load_curation()
    shadows = {gid for gid, tag in curation.NO_VANILLA_PARTNER.items()
               if tag == 'redundant-shadow'}
    cleanup_src = ''
    maps_src = open(os.path.join(ROOT, 'data/maps.py')).read()
    if 'def door_rando_cleanup' in maps_src:
        i = maps_src.index('def door_rando_cleanup')
        cleanup_src = maps_src[i:i + 2000]
    for gid in sorted(shadows):
        if str(gid) not in cleanup_src:
            failures.append(
                f'exit {gid}: tagged redundant-shadow but not relocated by Maps.door_rando_cleanup')
    return failures


def check_pools(records):
    """Validate mode pool definitions (ROOM_SETS, RUIN_ROOM_SETS).

    Every member must be a room_data room, and no pool may contain the
    same physical room twice via different mode variants (guide section 2:
    "each mode's room set must include at most one variant").
    """
    from data.room_sets import ROOM_SETS
    from data.ruin_areas import RUIN_ROOM_SETS
    from data.rooms import room_data
    rn = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'atlas_room_names', os.path.join(ROOT, 'doors/atlas/room_names.py'))
        rn = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rn)
    except Exception:
        pass
    failures = []
    for src_name, pools in (('ROOM_SETS', ROOM_SETS), ('RUIN_ROOM_SETS', RUIN_ROOM_SETS)):
        for pool, members in pools.items():
            seen_base = {}
            for m in members:
                if m not in room_data:
                    failures.append(f'{src_name}[{pool!r}]: {m!r} is not a room_data room')
                    continue
                if rn:
                    name = rn.ROOM_NAMES.get(m)
                    base = name.split('-')[0] if name else None
                    if base and base in seen_base and seen_base[base] != m:
                        failures.append(
                            f'{src_name}[{pool!r}]: {m!r} and {seen_base[base]!r} are '
                            f'variants of the same physical room ({base})')
                    elif base:
                        seen_base[base] = m
    return failures


def emit(records):
    """Write doors/atlas/compiled.py (generated; do not edit by hand)."""
    extended, final, derived = build_extended_partners(records)
    traps, event_doors = load_oneway_records()
    path = os.path.join(ROOT, 'doors/atlas/compiled.py')

    def sort_key(k):
        return (0, k, '') if isinstance(k, int) else (1, 0, k)

    with open(path, 'w') as f:
        f.write('"""GENERATED by tools/compile_atlas.py - do not edit.\n\n')
        f.write('Mechanical layer of the door-rando atlas: one record per vanilla\n')
        f.write('exit (id, kind, map, position, destination), the partner table\n')
        f.write('(coordinate-derived, curation applied, extended with the\n')
        f.write('event-door and logical-WoR layers), and the one-way (trap) and\n')
        f.write('event-door location records.\n')
        f.write('"""\n\n')
        f.write('EXIT_RECORDS = {\n')
        for gid in sorted(records):
            r = records[gid]
            f.write(f"    {gid}: {{'kind': {r['kind']!r}, 'map': {r['map']}, "
                    f"'x': {r['x']}, 'y': {r['y']}, 'size': {r['size']}, "
                    f"'direction': {r['direction']!r}, 'dest_map': {r['dest_map']}, "
                    f"'dest_x': {r['dest_x']}, 'dest_y': {r['dest_y']}}},\n")
        f.write('}\n\n')
        f.write('# Vanilla partner of each exit, including the event-door (1500+) and\n')
        f.write('# logical-WoR (4000+) layers (None = no vanilla exit-table partner).\n')
        f.write('PARTNERS = {\n')
        for gid in sorted(extended, key=sort_key):
            f.write(f'    {gid}: {extended[gid]!r},\n')
        f.write('}\n\n')
        f.write("# One-way exits (traps): {id: {'map','x','y','desc'}}. The pit twin\n")
        f.write('# (trap + 1000) is the logical landing side and has no record.\n')
        f.write('TRAP_RECORDS = {\n')
        for tid in sorted(traps, key=sort_key):
            f.write(f'    {tid!r}: {traps[tid]!r},\n')
        f.write('}\n\n')
        f.write('# Doors realized as event tiles (1500-1999, +4000 logical copies).\n')
        f.write('EVENT_DOOR_RECORDS = {\n')
        for did in sorted(event_doors, key=sort_key):
            f.write(f'    {did}: {event_doors[did]!r},\n')
        f.write('}\n')
    print(f'wrote {os.path.relpath(path, ROOT)} '
          f'({len(records)} exits, {sum(1 for v in final.values() if v is not None)} partnered, '
          f'{len(traps)} traps, {len(event_doors)} event doors)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify only')
    parser.add_argument('--report', action='store_true', help='verbose category report')
    args = parser.parse_args()

    records = load_exit_records()
    n_fail = check(records, report=args.report)
    if n_fail:
        print(f'{n_fail} failure(s)')
        return 1
    if not args.check:
        emit(records)
    print('atlas check OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
