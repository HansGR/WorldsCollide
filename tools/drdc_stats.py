"""Whole-mode -drdc statistical comparison: legacy Doors.mod vs plan_drdc.

Door- and room-level connection TVD (with legacy split-half self-baseline)
plus per-map graph-shape stats (cycle rank, dead ends, mean degree).
Long-running (~10-20 min at N=40); intended as an offline job.
Run: python3 tools/drdc_stats.py
"""
import sys, os, tempfile, random, collections, statistics, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
stub = tempfile.NamedTemporaryFile(suffix='.smc', delete=False); stub.write(b'\0'*0x300000); stub.close()
sys.argv = ['x', '-i', stub.name, '-o', os.path.join(tempfile.gettempdir(), 'o.smc')]
import args
args.door_randomize_dungeon_crawl = True; args.door_randomize = True; args.map_shuffle = False
from data.doors import Doors
from data.rooms import exit_room
from doors.plan.modes import plan_drdc

N = 40
def counts(results, room_level=False):
    d, o = collections.Counter(), collections.Counter()
    for pairs, ones in results:
        for a, b in pairs:
            if room_level:
                ra, rb = exit_room.get(a), exit_room.get(b)
                if ra is not None and rb is not None:
                    d[frozenset((str(ra), str(rb)))] += 1
            else:
                d[frozenset((a, b))] += 1
        for t, p in ones:
            if room_level:
                rt, rp = exit_room.get(t), exit_room.get(p)
                if rt is not None and rp is not None:
                    o[(str(rt), str(rp))] += 1
            else:
                o[(t, p)] += 1
    return d, o

def tvd(c1, c2):
    n1, n2 = sum(c1.values()) or 1, sum(c2.values()) or 1
    return 0.5 * sum(abs(c1.get(k,0)/n1 - c2.get(k,0)/n2) for k in set(c1)|set(c2))

def shape(pairs, ones):
    """Room-graph shape: (cycle rank, dead-end rooms, mean degree)."""
    deg = collections.Counter()
    edges = 0
    for a, b in list(pairs) + list(ones):
        ra, rb = exit_room.get(a), exit_room.get(b)
        if ra is None or rb is None: continue
        deg[str(ra)] += 1; deg[str(rb)] += 1
        edges += 1
    v = len(deg)
    return (edges - v + 1, sum(1 for x in deg.values() if x == 1),
            2 * edges / v if v else 0)

legacy, new = [], []
for i in range(N):
    random.seed(f'dcL{i}')
    d = Doors(args)
    try:
        d.mod(); legacy.append((d.map[0], d.map[1]))
    except Exception: pass
    try:
        dp, ow, _ = plan_drdc(seed=f'dcV{i}')
        new.append((dp, ow))
    except Exception: pass

out = {'n': N, 'legacy_ok': len(legacy), 'v2_ok': len(new)}
h = len(legacy)//2
for level, tag in ((False, 'door'), (True, 'room')):
    ld, lo = counts(legacy, level); nd, no = counts(new, level)
    h1, _ = counts(legacy[:h], level); h2, _ = counts(legacy[h:], level)
    out[f'{tag}_self_tvd'] = round(tvd(h1, h2), 3)
    out[f'{tag}_v2_tvd'] = round(tvd(ld, nd), 3)
    out[f'{tag}_oneway_tvd'] = round(tvd(lo, no), 3)
ls = [shape(*r) for r in legacy]; ns = [shape(*r) for r in new]
for i, name in enumerate(('cycle_rank', 'dead_ends', 'mean_degree')):
    out[f'legacy_{name}'] = f'{statistics.mean(x[i] for x in ls):.2f}+-{statistics.stdev(x[i] for x in ls):.2f}'
    out[f'v2_{name}'] = f'{statistics.mean(x[i] for x in ns):.2f}+-{statistics.stdev(x[i] for x in ns):.2f}'
path = os.path.join(tempfile.gettempdir(), 'drdc_stats.json')
json.dump(out, open(path, 'w'), indent=1)
print(json.dumps(out, indent=1))
