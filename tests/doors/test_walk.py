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

POOLS = ['Umaro', 'UpperNarshe_WoB', 'UpperNarshe_WoR', 'EsperMountain',
         'OwzerBasement', 'MagitekFactory', 'SealedGate', 'Zozo', 'MtZozo',
         'ZoneEater', 'SerpentTrench', 'BurningHouse', 'DarylsTomb',
         'SouthFigaroCaveWOB', 'PhantomTrain', 'CyansDream', 'MtKolts',
         'VeldtCave']
SEEDS = 10


def main():
    total = solved = 0
    for pool in POOLS:
        specs = load_pool(ROOM_SETS[pool])
        forcing = pool_forcing(specs)
        ok = 0
        for s in range(SEEDS):
            total += 1
            w = run(specs, forcing, seed=f'{pool}-{s}')
            assert w.total_unmatched() == 0, f'{pool} seed {s}: leftovers'
            used = [x for p in w.door_pairs for x in p] + \
                   [x for p in w.oneways for x in p]
            assert len(used) == len(set(used)), f'{pool} seed {s}: element reuse'
            for c in w.classes():
                assert w.find(c) not in w.downstream(c), f'{pool} seed {s}: cycle'
            ok += 1
            solved += 1
        print(f'PASS: {pool} {ok}/{SEEDS}')
    print(f'\nAll walk tests passed ({solved}/{total}).')


if __name__ == '__main__':
    main()
