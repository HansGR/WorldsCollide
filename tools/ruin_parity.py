"""Distribution-parity harness for the ruination planner (Stage D
milestone 6).

Compares the v2 planner's whole-plan output against legacy
ruination_map across many seeds, using the established methodology:
project connections to ROOM pairs (higher statistical power), compare by
total variation distance against the legacy split-half self-baseline,
plus scalar graph stats (pairs/oneways counts, rooms placed, characters
and espers granted).

Three modes (legacy runs one seed per process - a second in-process
build is unsupported):

  legacy <rom> <seed> <outdir>   run a real -ruin build, dump the map
                                 right after generation, exit early
  v2 <n> <outdir>                run the v2 planner offline for n seeds
  compare <legacy_dir> <v2_dir>  TVD + scalar comparison
"""

import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MODE = sys.argv[1] if len(sys.argv) > 1 else 'compare'


def room_owner_map():
    """exit id -> owning room, from static room_data (locks included;
    sorted for shared WoB/WoR variants)."""
    from data.rooms import room_data
    owner = {}
    for rid in sorted(room_data, key=str):
        data = room_data[rid]
        groups = [g for g in data[:3] if isinstance(g, (list, tuple, set))]
        if len(data) >= 6 and isinstance(data[4], dict):
            groups += list(data[4].values())
        for group in groups:
            for e in group:
                owner.setdefault(e, rid)
    return owner


def dump_stats(full_map, meta, path):
    out = {'pairs': [[str(a), str(b)] for a, b in full_map[0]],
           'oneways': [[str(a), str(b)] for a, b in full_map[1]]}
    out.update(meta)
    with open(path, 'w') as f:
        json.dump(out, f)


# ---------------------------------------------------------------------------
def legacy_main():
    rom, seed, outdir = sys.argv[2], sys.argv[3], sys.argv[4]
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, f'{seed}.json')
    sys.argv = ['wc.py', '-i', rom, '-o', os.path.join(outdir, 'x.smc'),
                '-s', seed, '-ruin']
    import args
    import log  # noqa: F401
    from memory.memory import Memory
    memory = Memory()
    from data.data import Data
    data = Data(memory.rom, args)

    import event.ruination as er
    orig = er.ruination_map.generate_map_with_characters

    def patched(self, characters, espers, items):
        full_map = orig(self, characters, espers, items)
        kinds = [e['type'] for e in self.reward_log]
        from event.event_reward import RewardType
        meta = {
            'party': sorted(self.PARTY),
            'requested': list(self.Requested),
            'chars_granted': sum(1 for k in kinds if k is RewardType.CHARACTER),
            'espers_granted': sum(1 for k in kinds if k is RewardType.ESPER),
            'areas_used': len(self.AreasUsed),
            'rooms_placed': sum(len(b.all_rooms_added) for b in self.branches),
        }
        dump_stats(full_map, meta, out_path)
        os._exit(0)                                  # skip ROM write

    er.ruination_map.generate_map_with_characters = patched
    from event.events import Events
    Events(memory.rom, args, data)


# ---------------------------------------------------------------------------
def v2_main():
    n, outdir = int(sys.argv[2]), sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    from data.ruin_constants import ALL_CHARACTERS
    from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
    from doors.plan.ruination.finalize import finalize_plan
    from event.event_reward import RewardType

    done = failures = 0
    i = 0
    while done < n and i < n * 3:
        seed = f'v2ruin{i}'
        i += 1
        rng = random.Random(seed)
        party = rng.sample(ALL_CHARACTERS, 3)
        cfg = RuinConfig(party, char_range=(6, 6), esper_range=(9, 9),
                         maze='iso', kefka_tower=True,
                         blitz_characters=['SABIN'])
        try:
            p = RuinPlanner(cfg, rng)
            p.grow()
            full_map = finalize_plan(p)
        except (RuinPlanError, RecursionError):
            failures += 1                            # legacy also regenerates
            continue
        kinds = [e['kind'] for e in p.reward_log]
        meta = {
            'party': sorted(party),
            'requested': list(p.Requested),
            'chars_granted': sum(1 for k in kinds if k is RewardType.CHARACTER),
            'espers_granted': sum(1 for k in kinds if k is RewardType.ESPER),
            'areas_used': len(p.AreasUsed),
            'rooms_placed': sum(len(b.rooms) for b in p.branches),
        }
        dump_stats(full_map, meta, os.path.join(outdir, f'{seed}.json'))
        done += 1
    print(f'v2: {done} plans dumped, {failures} rejected/regenerated')


# ---------------------------------------------------------------------------
def compare_main():
    import collections
    legacy_dir, v2_dir = sys.argv[2], sys.argv[3]
    owner = room_owner_map()

    def load(d):
        out = []
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.json'):
                with open(os.path.join(d, fn)) as f:
                    out.append(json.load(f))
        return out

    def as_id(s):
        try:
            return int(s)
        except ValueError:
            return s

    def room_counts(runs):
        doors = collections.Counter()
        ones = collections.Counter()
        for r in runs:
            for a, b in r['pairs']:
                ra = owner.get(as_id(a), a)
                rb = owner.get(as_id(b), b)
                doors[frozenset((str(ra), str(rb)))] += 1
            for a, b in r['oneways']:
                ra = owner.get(as_id(a), a)
                rb = owner.get(as_id(b), b)
                ones[(str(ra), str(rb))] += 1
        return doors, ones

    def tvd(c1, c2):
        n1, n2 = sum(c1.values()) or 1, sum(c2.values()) or 1
        keys = set(c1) | set(c2)
        return 0.5 * sum(abs(c1.get(k, 0) / n1 - c2.get(k, 0) / n2)
                         for k in keys)

    L, V = load(legacy_dir), load(v2_dir)
    print(f'legacy runs: {len(L)}, v2 runs: {len(V)}')

    ld, lo = room_counts(L)
    vd, vo = room_counts(V)
    half = len(L) // 2
    h1d, h1o = room_counts(L[:half])
    h2d, h2o = room_counts(L[half:])
    print(f'room-adjacency TVD  self-baseline={tvd(h1d, h2d):.3f}  '
          f'v2-vs-legacy={tvd(ld, vd):.3f}')
    print(f'oneway room TVD     self-baseline={tvd(h1o, h2o):.3f}  '
          f'v2-vs-legacy={tvd(lo, vo):.3f}')

    def scalar(runs, key, f=lambda r: 1):
        vals = [r[key] if key in r else 0 for r in runs]
        m = sum(vals) / len(vals)
        sd = (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5
        return m, sd

    for key in ('chars_granted', 'espers_granted', 'areas_used',
                'rooms_placed'):
        lm, ls = scalar(L, key)
        vm, vs = scalar(V, key)
        print(f'{key:15s} legacy {lm:7.2f} +/- {ls:5.2f}   '
              f'v2 {vm:7.2f} +/- {vs:5.2f}')
    lp = [len(r['pairs']) for r in L]
    vp = [len(r['pairs']) for r in V]
    lo_n = [len(r['oneways']) for r in L]
    vo_n = [len(r['oneways']) for r in V]
    print(f'{"pairs":15s} legacy {sum(lp)/len(lp):7.2f}            '
          f'v2 {sum(vp)/len(vp):7.2f}')
    print(f'{"oneways":15s} legacy {sum(lo_n)/len(lo_n):7.2f}            '
          f'v2 {sum(vo_n)/len(vo_n):7.2f}')


if __name__ == '__main__':
    {'legacy': legacy_main, 'v2': v2_main, 'compare': compare_main}[MODE]()
