"""Mode orchestration for the v2 planner (rewrite Stage C).

Assembles the same per-area pools Doors.__init__/mod select for every
door-randomization mode (including map shuffle and the individual-area
flags), walks them with the v2 planner, and applies the legacy
post-steps - without mutating any shared table (flaw F3): split exits
and protect-door replacements become pool-spec transforms, virtual
root/crossworld doors are injected into fresh specs.

This is the ModeSpec layer of the rewrite plan (section 3.3).
"""

import random

from data.room_sets import ROOM_SETS
from data.rooms import (logical_links, shared_exits,
                        dungeon_crawl_split_exits,
                        map_shuffle_protected_doors)
from data.map_exit_extra import doors_WOB_WOR
from doors.plan.pools import load_pool, pool_forcing
from doors.plan.walk import run

META_SETS = ('All', 'WoB', 'WoR', 'MapShuffleWOB', 'MapShuffleWOR',
             'MapShuffleXW', 'DungeonCrawl', 'Ruination')
IGNORE_MAPS = (1552, 1553)    # zone eater stays a transition, not a shuffled door
IGNORE_DOORS = (1554, 1555)   # phoenix cave doors dropped when map shuffle is on

# (args attribute, area key, gets _mapsafe under map shuffle)
INDIVIDUAL_FLAGS = (
    ('door_randomize_umaro', 'Umaro', False),
    ('door_randomize_esper_mountain', 'EsperMountain', True),
    ('door_randomize_owzer_basement', 'OwzerBasement', False),
    ('door_randomize_magitek_factory', 'MagitekFactory', False),
    ('door_randomize_sealed_gate', 'SealedGate', False),
    ('door_randomize_zozo_wob', 'Zozo', False),
    ('door_randomize_zozo_wor', 'Zozo-WOR', False),
    ('door_randomize_mt_zozo', 'MtZozo', False),
    ('door_randomize_lete_river', 'Lete', False),
    ('door_randomize_zone_eater', 'ZoneEater', False),
    ('door_randomize_serpent_trench', 'SerpentTrench', False),
    ('door_randomize_burning_house', 'BurningHouse', False),
    ('door_randomize_daryls_tomb', 'DarylsTomb', False),
    ('door_randomize_south_figaro_cave_wob', 'SouthFigaroCaveWOB', True),
    ('door_randomize_phantom_train', 'PhantomTrain', False),
    ('door_randomize_cyans_dream', 'CyansDream', False),
    ('door_randomize_mt_kolts', 'MtKolts', True),
    ('door_randomize_veldt_cave', 'VeldtCave', True),
)


def dre_area_names(map_shuffle=False):
    """The area list Doors.__init__ builds for -dre, in ROOM_SETS order."""
    use_mapsafe = ['MtZozo', 'Zozo-WOR']
    names = []
    for key in ROOM_SETS:
        if key in META_SETS:
            continue
        if map_shuffle:
            if '_mapsafe' in key or key + '_mapsafe' not in ROOM_SETS:
                names.append(key)
        else:
            if key in [n + '_mapsafe' for n in use_mapsafe]:
                names.append(key)
            elif '_mapsafe' not in key and key not in use_mapsafe:
                names.append(key)
    return names


def split_shared_view():
    """shared_exits with the dungeon-crawl split exits removed (-drdc and
    -ruin; legacy mutates the global table in Doors.__init__ instead)."""
    view = {k: list(v) for k, v in shared_exits.items()}
    for se, splits in dungeon_crawl_split_exits.items():
        view[se] = [x for x in view[se] if x not in splits]
    return view


def inject_meta_root(specs, forcing, meta_name, offset):
    """Legacy Doors.mod root-door meta room (-dra/-drx): every root room
    gains a virtual door (offset+i), a meta room holds the partners
    (offset+n+i), each partner forced onto its virtual door."""
    root_rooms = [r for r in specs if 'root' in str(r)]
    n = len(root_rooms)
    meta_doors = []
    for i, rr in enumerate(root_rooms):
        specs[rr] = dict(specs[rr], doors=specs[rr]['doors'] + [offset + i])
        meta_doors.append(offset + n + i)
        forcing[offset + n + i] = [offset + i]
    specs[meta_name] = {'doors': meta_doors, 'traps': [], 'pits': [],
                        'keys': [], 'locks': {}}
    return meta_doors, offset + 2 * n


def shuffle_transform(specs, protect):
    """Legacy deconflict for shuffle pools under door randomization:
    remove the ignore_maps ids and replace protected doors with their
    30000+ stand-ins (legacy mutates room_data instead)."""
    for rid, s in specs.items():
        doors = [d for d in s['doors'] if d not in IGNORE_MAPS]
        doors = [protect.get(d, d) for d in doors]
        specs[rid] = dict(s, doors=doors)
    return specs


def apply_logical_links(door_pairs):
    """Patch out logical-link virtual doors (Doors.mod post-step)."""
    link_of = {}
    for a, b in logical_links:
        link_of[a] = b
        link_of[b] = a
    partner = {}
    kept = []
    for m in door_pairs:
        ends = [e for e in m if e in link_of]
        if ends:
            for e in ends:
                partner[e] = m[1] if m[0] == e else m[0]
        else:
            kept.append(m)
    for a, b in logical_links:
        if a in partner and b in partner:
            kept.append((partner[a], partner[b]))
    return kept


def reattach_shared_exits(door_pairs, shared=None):
    """Send each shared sibling tile to its canonical tile's destination
    (Doors.mod post-step, minus legacy's iterate-while-append duplicates)."""
    if shared is None:
        shared = shared_exits
    out = list(door_pairs)
    for a, b in door_pairs:
        if a in shared:
            out.extend((se, b) for se in shared[a])
        if b in shared:
            out.extend((a, se) for se in shared[b])
    return out


def door_rando_pool_keys(flags):
    """ROOM_SETS keys the active door-randomization mode walks.

    This mirrors plan_mode's segment selection and MUST stay in lockstep
    with it (tests/doors/test_walk.py asserts agreement across every flag
    combination). Map-shuffle pools are excluded on purpose: event files
    treat MAP_SHUFFLE as a separate concern."""
    g = lambda name: getattr(flags, name, False)
    map_shuffle = bool(g('map_shuffle'))
    if g('door_randomize_crossworld'):
        return ['All']
    if g('door_randomize_dungeon_crawl'):
        return ['DungeonCrawl']
    if g('door_randomize_all'):
        return ['WoB', 'WoR']
    if g('door_randomize_each'):
        return dre_area_names(map_shuffle)
    keys = []
    if g('door_randomize_upper_narshe'):
        keys.append('UpperNarshe_WoB')
    else:
        if g('door_randomize_upper_narshe_wob'):
            keys.append('UpperNarshe_WoB')
        if g('door_randomize_upper_narshe_wor'):
            keys.append('UpperNarshe_WoR')
    for attr, key, mapsafe in INDIVIDUAL_FLAGS:
        if g(attr):
            if mapsafe and map_shuffle:
                key += '_mapsafe'
            keys.append(key)
    return keys


def touched_rooms(flags):
    """Room ids whose exits the active door-randomization mode rewires.
    Static per flags (pool membership), seed-independent."""
    rooms = set()
    for key in door_rando_pool_keys(flags):
        rooms.update(ROOM_SETS[key])
    if getattr(flags, 'door_randomize_upper_narshe', False):
        # -drun walks WoB and mirrors the writes onto the WoR equivalents.
        rooms.update(ROOM_SETS['UpperNarshe_WoR'])
    return rooms


def doors_touch(flags, *area_keys, rooms=()):
    """The derived DOOR_RANDOMIZE predicate (plan section 3.7 item 1):
    True iff the active door-randomization mode rewires any door of the
    given ROOM_SETS areas / explicit room ids. Replaces the hand-maintained
    per-event flag or-chains; ruination stays an explicit separate test at
    the call sites that want it (its rewiring is seed-dependent and events
    opt in deliberately)."""
    touched = touched_rooms(flags)
    if not touched:
        return False
    for key in area_keys:
        if any(r in touched for r in ROOM_SETS[key]):
            return True
    return any(r in touched for r in rooms)


def gates_from_specs(specs):
    """Element-level gate table from pool specs: exit id -> key tuple
    (the room lock dicts, before the walk consumes them). This is the one
    place gate knowledge is derived for DoorPlan.gates (plan section 3.5:
    the emission side -- entrance scripts / in-event branches -- reads the
    plan instead of three ad-hoc sources; emission unification itself
    lands with the Stage F realization extraction)."""
    gates = {}
    for spec in specs.values():
        for keys, items in spec.get('locks', {}).items():
            key_tuple = tuple(keys) if isinstance(keys, tuple) else (keys,)
            for item in items:
                if not isinstance(item, str):
                    gates[item] = key_tuple
    return gates


def plan_mode(flags, rng, budget_limit=5000):
    """Plan the full map for any -dr*/-maps/-mapx combination.

    `flags` is args or any namespace with the door randomization
    attributes. Returns (door_pairs, oneways, worlds, gates)."""
    g = lambda name: getattr(flags, name, False)
    map_shuffle = bool(g('map_shuffle'))
    segments = []      # (name, specs, forcing, start_rule, budget)
    protect = {}
    strip = []
    shared_view = None
    match_wob_wor = False
    dr_active = False

    def add(name, pool, shared=None, start_rule='roots', budget=None,
            drop=()):
        specs = load_pool(pool, shared=shared, drop=drop)
        forcing = pool_forcing(specs)
        segments.append([name, specs, forcing, start_rule,
                         budget or budget_limit])
        return segments[-1]

    drop = IGNORE_DOORS if map_shuffle else ()

    if g('door_randomize_crossworld'):                       # -drx
        dr_active = True
        seg = add('All', ROOM_SETS['All'], start_rule='first_root',
                  budget=50000, drop=drop)
        meta, _ = inject_meta_root(seg[1], seg[2], 'root', 10000)
        strip += meta
    elif g('door_randomize_dungeon_crawl'):                  # -drdc
        dr_active = True
        shared_view = split_shared_view()
        add('DungeonCrawl', ROOM_SETS['DungeonCrawl'], shared=shared_view,
            start_rule='biggest')
        map_shuffle = False                                  # -drdc overrides
    elif g('door_randomize_all'):                            # -dra
        dr_active = True
        offset = 10000
        for name in ('WoB', 'WoR'):
            seg = add(name, ROOM_SETS[name], drop=drop)
            meta, offset = inject_meta_root(seg[1], seg[2],
                                            'root_' + name, offset)
            strip += meta
    elif g('door_randomize_each'):                           # -dre
        dr_active = True
        for area in dre_area_names(map_shuffle):
            add(area, ROOM_SETS[area], drop=drop)
            if map_shuffle and area in map_shuffle_protected_doors:
                d = map_shuffle_protected_doors[area]
                protect[d] = d + 30000
    else:                                                    # individual flags
        keys = door_rando_pool_keys(flags)   # shared key authority
        match_wob_wor = bool(g('door_randomize_upper_narshe'))
        for key in keys:
            if key.endswith('_mapsafe') and key in map_shuffle_protected_doors:
                d = map_shuffle_protected_doors[key]
                protect[d] = d + 30000
        if keys:
            dr_active = True
            combined = []
            for k in keys:
                combined.extend(ROOM_SETS[k])
            add('_'.join(keys), combined, drop=drop)

    if map_shuffle:
        deconflict = shuffle_transform if dr_active else (lambda s, p: s)
        if g('map_shuffle_separate'):                        # -maps
            for name in ('MapShuffleWOB', 'MapShuffleWOR'):
                seg = add(name, ROOM_SETS[name])
                seg[1] = deconflict(seg[1], protect)
        elif g('map_shuffle_crossworld'):                    # -mapx
            seg = add('MapShuffleXW', ROOM_SETS['MapShuffleXW'])
            seg[1] = deconflict(seg[1], protect)
            seg[1]['shuffle-wob'] = dict(
                seg[1]['shuffle-wob'],
                doors=seg[1]['shuffle-wob']['doors'] + [20000])
            seg[1]['shuffle-wor'] = dict(
                seg[1]['shuffle-wor'],
                doors=seg[1]['shuffle-wor']['doors'] + [20001])
            seg[2][20000] = [20001]
            strip += [20000, 20001]

    door_pairs, oneways, worlds, gates = [], [], {}, {}
    for name, specs, forcing, start_rule, budget in segments:
        gates.update(gates_from_specs(specs))
        world = run(specs, forcing, rng=rng, start_rule=start_rule,
                    budget_limit=budget)
        worlds[name] = world
        door_pairs.extend(world.door_pairs)
        oneways.extend(world.oneways)

    door_pairs = apply_logical_links(door_pairs)
    door_pairs = reattach_shared_exits(door_pairs, shared_view)
    if strip:
        s = set(strip)
        door_pairs = [m for m in door_pairs if m[0] not in s and m[1] not in s]
    if match_wob_wor:                                        # -drun mirror
        door_pairs += [(doors_WOB_WOR[a], doors_WOB_WOR[b])
                       for a, b in door_pairs
                       if a in doors_WOB_WOR and b in doors_WOB_WOR]
    return door_pairs, oneways, worlds, gates


class _Flags:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def plan_dre(seed=None, rng=None, budget_limit=5000):
    if rng is None:
        rng = random.Random(seed)
    return plan_mode(_Flags(door_randomize_each=True), rng, budget_limit)


def plan_drdc(seed=None, rng=None, budget_limit=5000):
    if rng is None:
        rng = random.Random(seed)
    return plan_mode(_Flags(door_randomize_dungeon_crawl=True), rng,
                     budget_limit)


def plan_dra(seed=None, rng=None, budget_limit=5000):
    if rng is None:
        rng = random.Random(seed)
    return plan_mode(_Flags(door_randomize_all=True), rng, budget_limit)


def plan_drx(seed=None, rng=None, budget_limit=5000):
    if rng is None:
        rng = random.Random(seed)
    return plan_mode(_Flags(door_randomize_crossworld=True), rng, budget_limit)


def plan_for_args(args, rng, characters=None):
    """Mode dispatch for Doors.mod (the one planning entry point since the
    Stage E2 cutover). Every mode returns the same DoorPlan artifact;
    ruination is just another view of it (plan.ruination carries the
    abstract reward plan + party) -- one planning site, in the Data phase
    (F5)."""
    from doors.plan.artifact import DoorPlan
    from doors.validate.structural import check_solved
    if getattr(args, 'ruination_mode', None):
        # Ruination's own verifiers run inside finalize_plan (hub closure,
        # terminus merge, softlock check); check_solved's full-consumption
        # rule doesn't apply there (orphan rooms are legal).
        from doors.plan.ruination.plan import plan_ruination
        return plan_ruination(args, rng, characters)
    pairs, oneways, worlds, gates = plan_mode(args, rng)
    for world in worlds.values():
        check_solved(world, world.forcing)
    return DoorPlan(pairs, oneways, gates=gates)
