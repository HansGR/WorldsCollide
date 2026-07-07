"""Mode orchestration for the v2 planner (rewrite Stage B: -dre bring-up).

Assembles the same per-area pools Doors.__init__ selects, walks each with
the v2 planner, and applies the legacy post-steps to produce the mode's
full connection map. This is the seed of the ModeSpec layer (plan section
3.3); -dre first because its areas are the walk's native unit.
"""

import random

from data.room_sets import ROOM_SETS
from data.rooms import logical_links, shared_exits
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


def reattach_shared_exits(door_pairs):
    """Send each shared sibling tile to its canonical tile's destination
    (Doors.mod post-step)."""
    out = list(door_pairs)
    for a, b in door_pairs:
        if a in shared_exits:
            out.extend((se, b) for se in shared_exits[a])
        if b in shared_exits:
            out.extend((a, se) for se in shared_exits[b])
    return out


def plan_dre(seed, budget_limit=5000):
    """Plan a full -dre map. Returns (door_pairs, oneways, worlds) where
    worlds maps area name -> solved WorldModel (for validation)."""
    rng = random.Random(seed)
    door_pairs, oneways, worlds = [], [], {}
    for area in dre_area_names():
        specs = load_pool(ROOM_SETS[area])
        forcing = pool_forcing(specs)
        world = run(specs, forcing, rng=rng, budget_limit=budget_limit)
        worlds[area] = world
        door_pairs.extend(world.door_pairs)
        oneways.extend(world.oneways)
    door_pairs = apply_logical_links(door_pairs)
    door_pairs = reattach_shared_exits(door_pairs)
    return door_pairs, oneways, worlds
