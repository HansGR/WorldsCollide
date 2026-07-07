"""Distribution-parity harness: legacy walk vs v2 walk (rewrite plan test #4).

Runs both implementations on identical pools over many seeds, collects
per-connection frequencies (door pairs as unordered sets, oneways as
ordered trap->pit), and compares distributions by total variation
distance (TVD). The honest yardstick is the SELF-baseline: the legacy
sample split in half and compared against itself - v2-vs-legacy TVD in
the same ballpark means the sampling character is preserved; far above
it means a distribution shift to investigate.

Usage:
    python3 tools/walk_parity.py [-n RUNS] [pool ...]

Needs no ROM: a stub file satisfies the legacy import chain's argv
parsing (the ROM itself is only loaded by wc.py's Memory stage).
"""

import argparse
import collections
import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEFAULT_POOLS = ['Umaro', 'MtKolts', 'VeldtCave', 'SealedGate', 'PhantomTrain']


def _shim_argv():
    stub = tempfile.NamedTemporaryFile(suffix='.smc', delete=False)
    stub.write(b'\x00' * 0x300000)
    stub.close()
    out = os.path.join(tempfile.gettempdir(), 'walk_parity_out.smc')
    sys.argv = ['walk_parity.py', '-i', stub.name, '-o', out]


def legacy_run(pool_rooms, seed):
    """One legacy walk; returns (door_pairs, oneways) or None on failure."""
    from data.walks import Network
    from data.rooms import forced_connections
    random.seed(seed)
    net = Network(list(pool_rooms))
    net.ForceConnections(dict(forced_connections))
    net.attach_dead_ends()
    roots = [r for r in net.rooms.rooms if 'root' in str(r)]
    net.active = random.choice(roots) if roots else random.choice(list(net.net.nodes))
    net.walk_budget = [5000]
    try:
        done = net.connect_network()
    except Exception:
        return None
    return done.map[0], done.map[1]


def v2_run(specs, forcing, seed):
    from doors.plan.walk import run
    try:
        w = run(specs, forcing, seed=seed, attempts=1)
    except Exception:
        return None
    return w.door_pairs, w.oneways


def connection_counts(results):
    doors = collections.Counter()
    ones = collections.Counter()
    for pairs, oneways in results:
        for a, b in pairs:
            doors[frozenset((a, b))] += 1
        for t, p in oneways:
            ones[(t, p)] += 1
    return doors, ones


def tvd(c1, c2):
    """Total variation distance between two connection distributions
    (counters normalized by their own totals; 0 = identical, 1 = disjoint)."""
    n1, n2 = sum(c1.values()) or 1, sum(c2.values()) or 1
    keys = set(c1) | set(c2)
    return 0.5 * sum(abs(c1.get(k, 0) / n1 - c2.get(k, 0) / n2) for k in keys)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', type=int, default=400, help='runs per side')
    ap.add_argument('pools', nargs='*', default=DEFAULT_POOLS)
    args = ap.parse_args()
    n = args.n

    _shim_argv()
    from data.room_sets import ROOM_SETS
    from doors.plan.pools import load_pool, pool_forcing

    print(f'{"pool":15s} {"legacy ok":>9s} {"v2 ok":>6s} '
          f'{"self-TVD":>9s} {"door-TVD":>9s} {"oneway-TVD":>10s}')
    for pool in args.pools:
        rooms = ROOM_SETS[pool]
        specs = load_pool(rooms)
        forcing = pool_forcing(specs)

        legacy = [r for r in (legacy_run(rooms, f'L{pool}{i}') for i in range(n)) if r]
        new = [r for r in (v2_run(specs, forcing, f'V{pool}{i}') for i in range(n)) if r]

        ld, lo = connection_counts(legacy)
        nd, no = connection_counts(new)
        # Self baseline: legacy first half vs second half.
        half = len(legacy) // 2
        h1d, h1o = connection_counts(legacy[:half])
        h2d, h2o = connection_counts(legacy[half:])
        self_tvd = tvd(h1d, h2d)

        door_tvd = tvd(ld, nd)
        one_tvd = tvd(lo, no) if (lo or no) else 0.0
        print(f'{pool:15s} {len(legacy):6d}/{n:<3d} {len(new):4d}/{n:<3d} '
              f'{self_tvd:9.3f} {door_tvd:9.3f} {one_tvd:10.3f}')
        # Largest per-connection divergences, for eyeballing.
        keys = set(ld) | set(nd)
        diffs = sorted(keys, key=lambda k: -abs(ld.get(k, 0) / len(legacy)
                                                - nd.get(k, 0) / len(new)))
        for k in diffs[:3]:
            lf, nf = ld.get(k, 0) / len(legacy), nd.get(k, 0) / len(new)
            if abs(lf - nf) > 3 * max(self_tvd / 5, 0.02):
                print(f'    divergent pair {sorted(k, key=str)}: '
                      f'legacy {lf:.3f} vs v2 {nf:.3f}')


if __name__ == '__main__':
    main()
