"""Stage B walk regression: solve every -dre pool, verify structure.

Run: python3 tests/doors/test_walk.py
"""
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from data.room_sets import ROOM_SETS
from doors.plan.pools import load_pool, pool_forcing
from doors.plan.walk import run
from doors.validate.structural import check_solved

POOLS = ['Umaro', 'UpperNarshe_WoB', 'UpperNarshe_WoR', 'EsperMountain',
         'OwzerBasement', 'MagitekFactory', 'SealedGate', 'Zozo', 'MtZozo',
         'ZoneEater', 'SerpentTrench', 'BurningHouse', 'DarylsTomb',
         'SouthFigaroCaveWOB', 'PhantomTrain', 'CyansDream', 'MtKolts',
         'VeldtCave']
SEEDS = 10


def test_mode_predicates():
    """doors_touch: the derived DOOR_RANDOMIZE predicate (plan 3.7 item 1).
    Locks the truth table the event files rely on."""
    from doors.plan.modes import doors_touch, door_rando_pool_keys

    class F:
        def __init__(self, **kw):
            self.__dict__.update(kw)

        def __getattr__(self, name):
            return False

    # Own flag, each big mode, unrelated flag, no flags.
    assert doors_touch(F(door_randomize_mt_kolts=True), 'MtKolts')
    assert doors_touch(F(door_randomize_each=True), 'MtKolts')
    assert doors_touch(F(door_randomize_all=True), 'MtKolts')
    assert doors_touch(F(door_randomize_crossworld=True), 'MtKolts')
    assert doors_touch(F(door_randomize_dungeon_crawl=True), 'MtKolts')
    assert not doors_touch(F(door_randomize_umaro=True), 'MtKolts')
    assert not doors_touch(F(), 'MtKolts')

    # -drun mirrors WoR; -drunb touches WoB only; -drunr touches WoR only.
    assert doors_touch(F(door_randomize_upper_narshe=True), 'UpperNarshe_WoR')
    assert doors_touch(F(door_randomize_upper_narshe_wob=True), 'UpperNarshe_WoB')
    assert not doors_touch(F(door_randomize_upper_narshe_wor=True), 'UpperNarshe_WoB')

    # Room-id form: Phoenix Cave is in All/WoR/DungeonCrawl but no -dre area.
    assert doors_touch(F(door_randomize_all=True), rooms=('branch-pc',))
    assert doors_touch(F(door_randomize_dungeon_crawl=True), rooms=('branch-pc',))
    assert not doors_touch(F(door_randomize_each=True), rooms=('branch-pc',))
    # Ebot's Rock exists only in the DungeonCrawl pool.
    assert doors_touch(F(door_randomize_dungeon_crawl=True), rooms=('wor-ebots',))
    assert not doors_touch(F(door_randomize_all=True), rooms=('wor-ebots',))

    # Mapsafe variants still count as the area (-dre + map shuffle).
    assert doors_touch(F(door_randomize_each=True, map_shuffle=True), 'MtKolts')
    assert door_rando_pool_keys(F(door_randomize_mt_kolts=True, map_shuffle=True)) == ['MtKolts_mapsafe']
    print('PASS: mode predicates (doors_touch truth table)')



def main():
    test_mode_predicates()
    total = solved = 0
    for pool in POOLS:
        specs = load_pool(ROOM_SETS[pool])
        forcing = pool_forcing(specs)
        ok = 0
        for s in range(SEEDS):
            total += 1
            w = run(specs, forcing, seed=f'{pool}-{s}')
            check_solved(w, forcing)
            ok += 1
            solved += 1
        print(f'PASS: {pool} {ok}/{SEEDS}')
    print(f'\nAll walk tests passed ({solved}/{total}).')


if __name__ == '__main__':
    main()
