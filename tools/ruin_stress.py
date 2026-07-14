"""Exercise harness for the ruination planner.

Runs the ROM-free planner at scale (no ROM, no build) to answer:

  sweep [n]    Failure study + usage statistics at the default -ruin
               config (6 chars / 9 espers / -maze iso / -rkt, random
               3-character party). Reports the whole-plan failure rate
               (all 10 attempts exhausted),
               a per-attempt failure-cause taxonomy, and usage tables:
               party/recruit frequency per character, area frequency,
               and per-check reward-kind distribution.

  matrix [n]   Config stress grid: requested characters {3,6,10,14} x
               requested espers {0,9,18,27}, n plans per cell. Reports
               per-cell success rate, mean attempts, and mean plan time.
               (14 characters means EVERY character is planned and the
               reserve pool is empty; 27 espers demands more esper slots
               than some area draws contain - the interesting corners.)

Mirrors doors/plan/ruination/plan.py's retry semantics exactly: party
fixed per seed, fresh derived RNG per attempt, MAX_ATTEMPTS = 10.

Usage: python3 tools/ruin_stress.py sweep 1000
       python3 tools/ruin_stress.py matrix 60
"""

import collections
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from data.ruin_constants import ALL_CHARACTERS
from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
from doors.plan.ruination.finalize import finalize_plan

MAX_ATTEMPTS = 10


def classify(err):
    """Bucket a RuinPlanError message into a stable cause label."""
    msg = str(err)
    for tag, label in (
            ('character-gated softlock', 'softlock-verifier'),
            ('No reserve areas', 'stuck-no-reserve'),
            ('No branches have remaining checks', 'no-checks-left'),
            ('finalize step 1', 'finalize-1-pit-feed'),
            ('finalize step 2 post-check', 'finalize-2-postcheck'),
            ('finalize step 2', 'finalize-2-downstream'),
            ('finalize step 3', 'finalize-3-traps'),
            ('finalize step 5b', 'finalize-5b-orphan'),
            ('finalize step 6', 'finalize-6-deadends'),
            ('finalize hit max iterations', 'finalize-max-iter'),
            ('inject_door', 'finalize-inject-door'),
            ('insufficient characters', 'insufficient-chars'),
            ('insufficient espers', 'insufficient-espers'),
            ('not merged into hub', 'terminus-unmerged'),
            ('hub has unconnected exits', 'hub-not-closed'),
            ('before its', 'gate-order'),
    ):
        if tag in msg:
            return label
    return 'other: ' + msg[:60]


def run_plan(seed, char_range=(6, 6), esper_range=(9, 9), maze='iso',
             kt=True, open_world=False, max_attempts=MAX_ATTEMPTS):
    """One full plan with the production retry loop. Returns
    (planner_or_None, attempts_used, [cause labels], party, elapsed)."""
    rng = random.Random(seed)
    party = rng.sample(ALL_CHARACTERS, 3)
    base = rng.random()
    causes = []
    t0 = time.time()
    for attempt in range(max_attempts):
        attempt_rng = random.Random(f'{base}:{attempt}')
        cfg = RuinConfig(party, char_range=char_range, esper_range=esper_range,
                         maze=maze, kefka_tower=kt, open_world=open_world,
                         blitz_characters=['SABIN'])
        try:
            planner = RuinPlanner(cfg, attempt_rng)
            planner.grow()
            finalize_plan(planner)
            return planner, attempt + 1, causes, party, time.time() - t0
        except (RuinPlanError, RecursionError) as e:
            causes.append(classify(e) if isinstance(e, RuinPlanError)
                          else 'recursion-error')
    return None, max_attempts, causes, party, time.time() - t0


# ---------------------------------------------------------------------------
def sweep(n):
    attempt_causes = collections.Counter()
    fail_parties = []
    total_attempts = 0
    completed = failed = 0
    times = []

    party_uses = collections.Counter()        # starting party slots
    recruit_uses = collections.Counter()      # planned + granted recruits
    area_uses = collections.Counter()         # AreasUsed keys
    check_kind = collections.defaultdict(collections.Counter)  # name -> kind
    all_check_names = set()

    for i in range(n):
        planner, attempts, causes, party, dt = run_plan(f'sweep{i}')
        total_attempts += attempts
        attempt_causes.update(causes)
        times.append(dt)
        if planner is None:
            failed += 1
            fail_parties.append((f'sweep{i}', party, causes))
            continue
        completed += 1
        party_uses.update(party)
        for name, (kind, char) in planner.assignments.items():
            if kind == 'CHARACTER':
                recruit_uses[char] += 1
        area_uses.update(planner.AreasUsed.keys())
        for rid, rewards in planner.config.room_reward.items():
            for name in rewards:
                all_check_names.add(name)
        for name, (kind, _) in planner.assignments.items():
            check_kind[name][kind] += 1

    print(f'=== FAILURE STUDY (default config: 6 chars / 9 espers / iso / rkt) ===')
    print(f'plans: {n}   completed: {completed}   '
          f'FAILED (all {MAX_ATTEMPTS} attempts): {failed}  '
          f'({failed / n:.2%} whole-plan failure rate)')
    print(f'attempts per plan: mean {total_attempts / n:.2f}')
    per_attempt_fail = sum(attempt_causes.values())
    print(f'per-attempt rejections: {per_attempt_fail}/{total_attempts} '
          f'({per_attempt_fail / max(total_attempts, 1):.1%}), by cause:')
    for cause, c in attempt_causes.most_common():
        print(f'    {c:5d}  {cause}')
    if fail_parties:
        print('whole-plan failures (seed, party, cause sequence):')
        for seed, party, causes in fail_parties[:10]:
            print(f'    {seed}: {party} -> {causes}')
    print(f'plan time: mean {sum(times) / len(times):.2f}s, '
          f'max {max(times):.2f}s')

    print(f'\n=== CHARACTER USAGE ({completed} completed plans) ===')
    print(f'{"character":10s} {"in party":>9s} {"recruited":>10s} {"total":>7s} {"in-game %":>10s}')
    for ch in ALL_CHARACTERS:
        p, r = party_uses[ch], recruit_uses[ch]
        print(f'{ch:10s} {p:9d} {r:10d} {p + r:7d} {(p + r) / completed:9.1%}')

    print(f'\n=== AREA USAGE ===')
    print(f'{"area":18s} {"used":>6s} {"of plans":>9s}')
    for area, c in area_uses.most_common():
        print(f'{area:18s} {c:6d} {c / completed:8.1%}')

    print(f'\n=== CHECK / REWARD USAGE ===')
    print(f'{"check":22s} {"claimed":>8s} {"char":>6s} {"esper":>6s} {"item":>6s}')
    rows = []
    for name in sorted(all_check_names):
        k = check_kind[name]
        claimed = sum(k.values())
        rows.append((claimed, name, k))
    for claimed, name, k in sorted(rows, reverse=True):
        print(f'{name:22s} {claimed / completed:8.1%} '
              f'{k["CHARACTER"] / completed:6.1%} {k["ESPER"] / completed:6.1%} '
              f'{k["ITEM"] / completed:6.1%}')


# ---------------------------------------------------------------------------
def matrix(n):
    """Per-ATTEMPT success probability per cell (attempts capped at 3 to
    bound runtime on pathological cells); the production whole-plan failure
    rate is (1 - p)^10 and is derived in the summary column."""
    cap = 3
    print(f'=== CONFIG STRESS MATRIX ({n} plans per cell, attempts capped at {cap}) ===')
    print(f'{"chars":>5s} {"espers":>6s} {"att ok%":>8s} {"whole-plan fail (derived)":>26s} '
          f'{"mean s/att":>10s}  top causes')
    for chars in (3, 6, 10, 14):
        for espers in (0, 9, 18, 27):
            successes = attempts_total = 0
            times = []
            causes = collections.Counter()
            for i in range(n):
                planner, attempts, cs, _, dt = run_plan(
                    f'mx{chars}.{espers}.{i}',
                    char_range=(chars, chars), esper_range=(espers, espers),
                    max_attempts=cap)
                attempts_total += attempts
                times.append(dt / attempts)
                causes.update(cs)
                if planner is not None:
                    successes += 1
            p = successes / max(attempts_total, 1)
            derived = (1 - p) ** MAX_ATTEMPTS
            top = ', '.join(f'{c} {k}' for k, c in causes.most_common(2))
            print(f'{chars:5d} {espers:6d} {p:8.1%} {derived:26.2%} '
                  f'{sum(times) / n:10.2f}  {top}', flush=True)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'sweep'
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    {'sweep': sweep, 'matrix': matrix}[mode](count)
