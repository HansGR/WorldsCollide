"""Rules G/H: the walk never leaves a region cut off from home.

Run: python3 tests/doors/test_home_reachability.py

Built from the 2026-09 Serpent Trench incident: the walk sent the start's
current through section 1 -> section 2 -> Nikeah -> start, consuming the
home region's last landing while section 3 (reached by a forced current)
and the caves were still downstream; it then closed them into a sealed
loop. Counting rules A-F cannot see a fully consumed cluster, and nothing
checked the finished map.
"""
import os
import random
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from data.room_sets import ROOM_SETS
from doors.model import WorldModel
from doors.plan.modes import dre_area_names
from doors.plan.pools import load_pool, pool_forcing
from doors.plan.prune import check_invalid, check_home_reachable, PruneReject
from doors.plan.walk import run, force_connections, WalkFailed

SEEDS = 20


def serpent_world():
    specs = load_pool(ROOM_SETS['SerpentTrench'])
    forcing = pool_forcing(specs)
    world = WorldModel(specs)
    world.forcing = forcing
    force_connections(world, forcing)
    world.home_rooms = ['SER-root']
    return world


def rejected(fn):
    try:
        fn()
    except PruneReject:
        return True
    return False


def test_serpent_trench_partial_state():
    """The seed-1001 walk state: start -> 01a -> 01b -> Nikeah closes the
    home loop with no landing left in it while section 3 hangs below."""
    world = serpent_world()
    world.connect_oneway(2044, 3044)     # start -> section 1
    world.connect_oneway(2045, 3047)     # section 1 -> section 2
    check_invalid(world)                 # still completable here
    world.connect_oneway(2048, 3052)     # section 2 -> Nikeah (last home pit)
    assert rejected(lambda: check_invalid(world)), 'G2 missed the closed home'
    print('PASS: Serpent Trench - closing the home loop is rejected (G2)')


def test_serpent_trench_final_map():
    """The finished seed-1001 layout (sealed current loop) is refused."""
    world = serpent_world()
    for t, p in [(2044, 3044), (2045, 3047), (2048, 3052), (2052, 3050),
                 (2051, 3048), (2050, 3045), (2047, 3051)]:
        world.connect_oneway(t, p)
    world.connect_door(529, 530)
    assert world.total_unmatched() == 0
    assert rejected(lambda: check_home_reachable(world, final=True)), \
        'final check accepted a sealed loop'
    print('PASS: Serpent Trench - sealed-loop map refused as a finished map')


def reach_ok(world):
    """Independent check: every cluster is reachable from a home cluster
    and can reach one (outside world = home rooms)."""
    home = {world.cluster_of_room(r) for r in world.home_rooms}
    down = set(home)
    for c in home:
        down.update(world.downstream(c))
    for c in world.clusters():
        if c not in down:
            return f'{world.cluster_name(c)} unreachable from home'
        if not ({c} | set(world.downstream(c))) & home:
            return f'{world.cluster_name(c)} cannot get home'
    return None


def test_every_dre_pool():
    for area in dre_area_names():
        specs = load_pool(ROOM_SETS[area])
        forcing = pool_forcing(specs)
        for seed in range(SEEDS):
            world = run(specs, forcing, rng=random.Random(f'{area}:{seed}'))
            problem = reach_ok(world)
            assert problem is None, f'{area} seed {seed}: {problem}'
    print(f'PASS: every -dre pool x {SEEDS} seeds reachable both ways')


def test_zozo_wor_restarts():
    """Zozo WoR's dead-end pre-pass is infeasible ~64% of the time; short
    restarts must redraw it rather than fail the pool."""
    specs = load_pool(ROOM_SETS['Zozo-WOR_mapsafe'])
    forcing = pool_forcing(specs)
    failures = 0
    for seed in range(100):
        try:
            run(specs, forcing, rng=random.Random(seed))
        except WalkFailed:
            failures += 1
    assert failures == 0, f'Zozo-WOR failed {failures}/100'
    print('PASS: Zozo WoR solves 100/100 seeds')


def test_map_shuffle_with_door_rando():
    """Under -dre, map shuffle drops Zone Eater's ids and leaves its room
    elementless; G/H must ignore such inert rooms (else every state of the
    WoR map-shuffle pool is 'sealed from home')."""
    from doors.plan.modes import plan_mode, _Flags
    for flags in (dict(door_randomize_each=True, map_shuffle=True,
                       map_shuffle_separate=True),
                  dict(door_randomize_each=True, map_shuffle=True,
                       map_shuffle_crossworld=True)):
        for seed in range(5):
            plan_mode(_Flags(**flags), random.Random(seed))
    print('PASS: -dre with -maps / -mapx plans (inert rooms ignored)')


if __name__ == '__main__':
    test_serpent_trench_partial_state()
    test_serpent_trench_final_map()
    test_every_dre_pool()
    test_zozo_wor_restarts()
    test_map_shuffle_with_door_rando()
    print('\nAll home-reachability tests passed.')
