"""Mode orchestration for the v2 planner (rewrite Stage C).

Assembles the same per-area pools Doors.__init__/mod select for each door
randomization mode, walks them with the v2 planner, and applies the
legacy post-steps to produce the mode's full connection map - without
mutating any shared table (flaw F3): split exits become a shared-exits
VIEW, virtual root doors are injected into fresh pool specs.

This is the seed of the ModeSpec layer (plan section 3.3).
"""

import random

from data.room_sets import ROOM_SETS
from data.rooms import (logical_links, shared_exits,
                        dungeon_crawl_split_exits)
from doors.plan.pools import load_pool, pool_forcing
from doors.plan.walk import run

META_SETS = ('All', 'WoB', 'WoR', 'MapShuffleWOB', 'MapShuffleWOR',
             'MapShuffleXW', 'DungeonCrawl', 'Ruination')


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
    (offset+n+i), each partner forced onto its virtual door. Returns
    (meta door ids incl. virtual sides, next free offset)."""
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


def apply_logical_links(door_pairs):
    """Patch out logical-link virtual doors (Doors.mod post-step): the two
    connections [L0, X] and [L1, Y] become one real connection [X, Y]."""
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
                other = m[1] if m[0] == e else m[0]
                partner[e] = other
        else:
            kept.append(m)
    for a, b in logical_links:
        if a in partner and b in partner:
            kept.append((partner[a], partner[b]))
    return kept


def reattach_shared_exits(door_pairs, shared=None):
    """Send each shared sibling tile to its canonical tile's destination
    (Doors.mod post-step; uses the mode's shared view)."""
    if shared is None:
        shared = shared_exits
    out = list(door_pairs)
    for a, b in door_pairs:
        if a in shared:
            out.extend((se, b) for se in shared[a])
        if b in shared:
            out.extend((a, se) for se in shared[b])
    return out


def _finish(door_pairs, oneways, shared=None, strip=()):
    door_pairs = apply_logical_links(door_pairs)
    door_pairs = reattach_shared_exits(door_pairs, shared)
    if strip:
        strip = set(strip)
        door_pairs = [m for m in door_pairs
                      if m[0] not in strip and m[1] not in strip]
    return door_pairs, oneways


def plan_dre(seed=None, rng=None, budget_limit=5000):
    """-dre: every area walked separately."""
    if rng is None:
        rng = random.Random(seed)
    door_pairs, oneways, worlds = [], [], {}
    for area in dre_area_names():
        specs = load_pool(ROOM_SETS[area])
        forcing = pool_forcing(specs)
        world = run(specs, forcing, rng=rng, budget_limit=budget_limit)
        worlds[area] = world
        door_pairs.extend(world.door_pairs)
        oneways.extend(world.oneways)
    door_pairs, oneways = _finish(door_pairs, oneways)
    return door_pairs, oneways, worlds


def plan_drdc(seed=None, rng=None, budget_limit=5000):
    """-drdc: one giant DungeonCrawl pool, split shared exits, start from
    the biggest class."""
    if rng is None:
        rng = random.Random(seed)
    shared = split_shared_view()
    specs = load_pool(ROOM_SETS['DungeonCrawl'], shared=shared)
    forcing = pool_forcing(specs)
    world = run(specs, forcing, rng=rng, start_rule='biggest',
                budget_limit=budget_limit)
    door_pairs, oneways = _finish(world.door_pairs, world.oneways, shared)
    return door_pairs, oneways, {'DungeonCrawl': world}


def plan_dra(seed=None, rng=None, budget_limit=5000):
    """-dra: WoB and WoR pools, each with a meta-root room; root pairs
    stripped afterward."""
    if rng is None:
        rng = random.Random(seed)
    door_pairs, oneways, worlds = [], [], {}
    offset = 10000
    strip = []
    for name in ('WoB', 'WoR'):
        specs = load_pool(ROOM_SETS[name])
        forcing = pool_forcing(specs)
        meta_doors, offset = inject_meta_root(specs, forcing,
                                              'root_' + name, offset)
        strip.extend(meta_doors)
        world = run(specs, forcing, rng=rng, budget_limit=budget_limit)
        worlds[name] = world
        door_pairs.extend(world.door_pairs)
        oneways.extend(world.oneways)
    door_pairs, oneways = _finish(door_pairs, oneways, strip=strip)
    return door_pairs, oneways, worlds


def plan_drx(seed=None, rng=None, budget_limit=50000):
    """-drx: the combined 'All' pool with one meta-root room. The ~300-room
    walk needs more budget headroom than the per-area walks; journal
    rollback makes that cheap (~4s at 50k)."""
    if rng is None:
        rng = random.Random(seed)
    specs = load_pool(ROOM_SETS['All'])
    forcing = pool_forcing(specs)
    meta_doors, _ = inject_meta_root(specs, forcing, 'root', 10000)
    world = run(specs, forcing, rng=rng, start_rule='first_root',
                budget_limit=budget_limit)
    door_pairs, oneways = _finish(world.door_pairs, world.oneways,
                                  strip=meta_doors)
    return door_pairs, oneways, {'All': world}


def plan_for_args(args, rng):
    """Mode dispatch for the -d2 dev flag in Doors.mod. Returns
    (door_pairs, oneways) or raises for modes not yet on the v2 path."""
    from doors.validate.structural import check_solved
    if getattr(args, 'ruination_mode', None):
        raise NotImplementedError('v2 planner: ruination is Stage D')
    if getattr(args, 'map_shuffle', False):
        raise NotImplementedError('v2 planner: map shuffle pending (Stage C)')
    if getattr(args, 'door_randomize_crossworld', False):
        pairs, oneways, worlds = plan_drx(rng=rng)
    elif getattr(args, 'door_randomize_dungeon_crawl', False):
        pairs, oneways, worlds = plan_drdc(rng=rng)
    elif getattr(args, 'door_randomize_all', False):
        pairs, oneways, worlds = plan_dra(rng=rng)
    elif getattr(args, 'door_randomize_each', False):
        pairs, oneways, worlds = plan_dre(rng=rng)
    else:
        raise NotImplementedError('v2 planner: individual-area flags pending')
    for world in worlds.values():
        check_solved(world, world.forcing)
    return pairs, oneways
