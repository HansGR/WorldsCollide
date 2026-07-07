"""End-to-end -dre parity: legacy Doors.mod vs v2 plan_dre (Stage B).

Legacy side runs the REAL data.doors.Doors class (args-module attribute
injection; no ROM - Doors only reads tables). Compares full-map
connection distributions by TVD with the legacy split-half self-baseline
as the noise floor, and validates every v2 area with the structural gate.

Usage: python3 tools/dre_parity.py [-n RUNS]
"""

import argparse
import collections
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _shim_argv():
    stub = tempfile.NamedTemporaryFile(suffix='.smc', delete=False)
    stub.write(b'\x00' * 0x300000)
    stub.close()
    sys.argv = ['dre_parity.py', '-i', stub.name,
                '-o', os.path.join(tempfile.gettempdir(), 'dre_parity_out.smc')]


def legacy_dre(seed):
    import args
    args.door_randomize_each = True
    args.door_randomize = True
    args.map_shuffle = False
    from data.doors import Doors
    random.seed(seed)
    doors = Doors(args)
    try:
        doors.mod()
    except Exception:
        return None
    return doors.map[0], doors.map[1]


def v2_dre(seed):
    from doors.plan.modes import plan_dre
    from doors.validate.structural import check_solved
    try:
        pairs, oneways, worlds = plan_dre(seed)
        for area, world in worlds.items():
            check_solved(world, world.forcing)
    except Exception as e:
        print('  v2 failure:', type(e).__name__, str(e)[:70])
        return None
    return pairs, oneways


def counts(results):
    doors, ones = collections.Counter(), collections.Counter()
    for pairs, oneways in results:
        for a, b in pairs:
            doors[frozenset((a, b))] += 1
        for t, p in oneways:
            ones[(t, p)] += 1
    return doors, ones


def tvd(c1, c2):
    n1, n2 = sum(c1.values()) or 1, sum(c2.values()) or 1
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) / n1 - c2.get(k, 0) / n2) for k in keys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', type=int, default=100)
    args_ns = ap.parse_args()
    n = args_ns.n
    _shim_argv()

    legacy = [r for r in (legacy_dre(f'L{i}') for i in range(n)) if r]
    new = [r for r in (v2_dre(f'V{i}') for i in range(n)) if r]
    print(f'legacy ok {len(legacy)}/{n}   v2 ok {len(new)}/{n}')

    ld, lo = counts(legacy)
    nd, no = counts(new)
    half = len(legacy) // 2
    h1d, _ = counts(legacy[:half])
    h2d, _ = counts(legacy[half:])
    h1o = counts(legacy[:half])[1]
    h2o = counts(legacy[half:])[1]
    print(f'door-TVD  self={tvd(h1d, h2d):.3f}  v2-vs-legacy={tvd(ld, nd):.3f}')
    print(f'oneway-TVD self={tvd(h1o, h2o):.3f}  v2-vs-legacy={tvd(lo, no):.3f}')
    # connection-set sanity: same universe of possible connections seen?
    only_l = set(ld) - set(nd)
    only_n = set(nd) - set(ld)
    print(f'connections seen only by legacy: {len(only_l)}, only by v2: {len(only_n)}')
    for k in list(only_l)[:5]:
        print('   legacy-only:', sorted(k, key=str), f'{ld[k]}x')
    for k in list(only_n)[:5]:
        print('   v2-only:', sorted(k, key=str), f'{nd[k]}x')


if __name__ == '__main__':
    main()
