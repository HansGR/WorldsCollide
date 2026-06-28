#!/usr/bin/env python3
"""Convergence simulation for the FF6 Coliseum ranking.

Validates that the Glicko-2 + active-pairing pipeline recovers a true ordering
from noisy votes, and that active pairing beats random pairing.

We invent a hidden "true strength" for every included enemy (their vanilla
seed power plus noise so it is *not* identical to the seed), then simulate
voters who pick the stronger enemy with a realistic error rate (a
Bradley-Terry coin flip).  We measure Spearman rank correlation between the
recovered ratings and the hidden truth as votes accumulate.

    python tools/simulate.py
"""
import os
import sys
import json
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, PROJECT)

import glicko2
from pairing import select_pair

SEED_RD = 200.0
BT_SCALE = 220.0   # how decisively voters favour the stronger enemy


def load_truth():
    data = json.load(open(os.path.join(PROJECT, "data", "enemies.json"), encoding="utf-8"))
    enemies = [e for e in data["enemies"] if e["include"]]
    truth, seed = {}, {}
    for e in enemies:
        seed[e["slug"]] = e["seed_rating"]
        # Hidden truth = seed shifted by noise, so the prior is good-but-wrong.
        truth[e["slug"]] = e["seed_rating"] + random.gauss(0, 180)
    return seed, truth


def true_win_prob(ta, tb):
    return 1.0 / (1.0 + 10 ** (-(ta - tb) / BT_SCALE))


def spearman(rank_a, rank_b):
    keys = list(rank_a)
    n = len(keys)
    ra = {k: i for i, k in enumerate(sorted(keys, key=lambda k: rank_a[k]))}
    rb = {k: i for i, k in enumerate(sorted(keys, key=lambda k: rank_b[k]))}
    d2 = sum((ra[k] - rb[k]) ** 2 for k in keys)
    return 1 - 6 * d2 / (n * (n * n - 1))


def run(strategy, seed, truth, n_votes, rng):
    state = {s: {"rating": seed[s], "rd": SEED_RD, "vol": glicko2.DEFAULT_VOL, "n": 0}
             for s in seed}
    pair_counts = {}
    slugs = list(seed)
    snapshots = {}
    checkpoints = {int(x) for x in [n_votes * f for f in (.1, .25, .5, 1.0)]}

    for v in range(1, n_votes + 1):
        if strategy == "active":
            a, b = select_pair(state, pair_counts, rng=rng)
        else:
            a, b = rng.sample(slugs, 2)

        p = true_win_prob(truth[a], truth[b])
        winner, loser = (a, b) if rng.random() < p else (b, a)

        w, l = state[winner], state[loser]
        nw = glicko2.rate(glicko2.Rating(w["rating"], w["rd"], w["vol"]),
                          [(glicko2.Rating(l["rating"], l["rd"], l["vol"]), 1.0)])
        nl = glicko2.rate(glicko2.Rating(l["rating"], l["rd"], l["vol"]),
                          [(glicko2.Rating(w["rating"], w["rd"], w["vol"]), 0.0)])
        for s, nr in ((winner, nw), (loser, nl)):
            state[s].update(rating=nr.rating, rd=nr.rd, vol=nr.vol)
            state[s]["n"] += 1
        pair_counts[frozenset((a, b))] = pair_counts.get(frozenset((a, b)), 0) + 1

        if v in checkpoints:
            est = {s: state[s]["rating"] for s in slugs}
            snapshots[v] = spearman(est, truth)
    return snapshots, state


def main():
    rng = random.Random(42)
    seed, truth = load_truth()
    n = len(seed)
    votes = n * 40  # ~40 comparisons per enemy

    print(f"{n} enemies, simulating {votes} votes "
          f"(~{votes // n} per enemy), BT noise scale {BT_SCALE}\n")

    baseline = spearman(seed, truth)
    print(f"Seed-only rank correlation vs truth : {baseline:+.3f}  "
          f"(the vanilla prior before any votes)\n")

    print(f"{'votes':>8} | {'random':>8} | {'active':>8}")
    print("-" * 30)
    snaps_a, final_state = run("active", seed, truth, votes, random.Random(1))
    snaps_r, _ = run("random", seed, truth, votes, random.Random(1))
    for v in sorted(snaps_a):
        print(f"{v:>8} | {snaps_r[v]:>+8.3f} | {snaps_a[v]:>+8.3f}")

    avg_rd = sum(s["rd"] for s in final_state.values()) / n
    print(f"\nFinal avg rating deviation (active): {avg_rd:.1f} "
          f"(lower = more confident)")
    print("Active pairing should reach high correlation with fewer votes.")


if __name__ == "__main__":
    main()
