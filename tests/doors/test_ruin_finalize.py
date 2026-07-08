"""End-to-end tests for the ruination planner: grow + finalize
(Stage D milestone 4).

Runs the full v2 pipeline (growth loop, six-step branch closing, map
assembly, softlock verifier) on the real room pool and checks closure:
- every branch hub ends with zero live unprotected exits (checked inside
  finalize_plan) and the terminus merged into the hub
- no element appears twice in the model's connections
- the KT entry traps (2077-79) are wired to pits 3077-79
- growth-claimed check rooms are all inside their branch's hub component

Run: python3 tests/doors/test_ruin_finalize.py [n_seeds]
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
from doors.plan.ruination.finalize import finalize_plan

PARTIES = [
    ['TERRA', 'LOCKE', 'EDGAR'],
    ['CELES', 'SABIN', 'GAU'],
    ['MOG', 'STRAGO', 'RELM', 'SETZER'],
    ['CYAN', 'SHADOW', 'UMARO'],
]


def run_one(seed, party, maze=None):
    rng = random.Random(seed)
    cfg = RuinConfig(party, char_range=(2, 6), esper_range=(1, 4),
                     maze=maze, blitz_characters=['SABIN'])
    planner = RuinPlanner(cfg, rng)
    planner.grow()
    full_map = finalize_plan(planner)
    return planner, full_map


def check_closure(p, full_map):
    w = p.world
    pairs, oneways = full_map
    # Model-level connections use each element once.
    used = [e for m in w.door_pairs for e in m] + [e for m in w.oneways for e in m]
    assert len(used) == len(set(used)), 'element used twice'
    # KT entry wiring present.
    kt = {t: pt for t, pt in oneways if t in (2077, 2078, 2079)}
    assert sorted(kt) == [2077, 2078, 2079]
    assert sorted(kt.values()) == [3077, 3078, 3079]
    for i, branch in enumerate(p.branches):
        hub = branch.hub_class()
        assert w.class_of_room(branch.terminus) == hub, f'branch {i} terminus'
        # Claimed check rooms must be in the hub component (they were
        # reached during growth and nothing disconnects them).
        for rid in branch.rooms:
            if rid in branch.check_ids and rid not in branch.check_rooms:
                c = w.class_of_room(rid)
                assert (c == hub or c in w.upstream(hub)
                        or c in w.downstream(hub)), (i, rid)


def main(n=40):
    ok = fail = 0
    failures = []
    for i in range(n):
        party = PARTIES[i % len(PARTIES)]
        maze = [None, 'sep', 'iso'][i % 3]
        try:
            p, full_map = run_one(f'fin{i}', party, maze=maze)
            check_closure(p, full_map)
            ok += 1
        except RuinPlanError as e:
            fail += 1
            failures.append((i, str(e)[:110]))
    print(f'grow+finalize: {ok}/{n} complete, {fail} failed')
    for i, msg in failures[:6]:
        print(f'  seed {i}: {msg}')
    # Legacy's whole-map retry rate is a few percent; grow+finalize should
    # complete for the large majority of seeds.
    assert ok >= n * 0.8, f'too many failures: {fail}/{n}'
    print('PASS: grow+finalize closure across seeds')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
