"""Active match-up selection for fast convergence on noisy pairwise votes.

Random pairing wastes votes: comparing a Lvl 1 enemy with a Lvl 60 one tells
us almost nothing.  Research on active ranking from noisy comparisons (e.g.
Jamieson & Nowak 2011; Heckel et al. 2018) shows that adaptively choosing
*informative* pairs reaches a good ranking with a small fraction of the
comparisons.  We combine three well-known ideas:

1. **Uncertainty sampling** - prefer enemies whose rating is still uncertain
   (high Glicko rating deviation) or rarely shown.
2. **Information / disagreement maximisation** - given an anchor, the most
   informative opponent is one the model thinks is a near toss-up
   (win probability ~ 0.5).  These are exactly the overlapping, high-variance
   clusters the user wants disambiguated.
3. **Novelty + softmax exploration** - down-weight pairs already seen a lot and
   sample stochastically so many visitors don't all get the same match-up.

The result: pairs are close in strength (never wildly mismatched), focus on the
fuzzy boundaries of the ordering, and spread coverage across the roster.
"""
import math
import random

# Tunables (exposed so they are easy to experiment with).
ANCHOR_TEMP = 250.0      # softmax temperature for anchor selection (rating units)
OPP_TEMP = 0.15          # softmax temperature for opponent informativeness
RD_WEIGHT = 1.0          # how much opponent uncertainty matters
NOVELTY_WEIGHT = 0.6     # penalty per prior comparison of the same pair
COLD_RD = 100.0          # below this RD an enemy is considered "well measured"


def _g(phi):
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / (math.pi * math.pi))


def _win_prob(a, b):
    # a, b are (rating, rd) tuples on the Glicko scale.
    from glicko2 import SCALE, DEFAULT_RATING
    mu_a = (a[0] - DEFAULT_RATING) / SCALE
    mu_b = (b[0] - DEFAULT_RATING) / SCALE
    phi_b = b[1] / SCALE
    return 1.0 / (1.0 + math.exp(-_g(phi_b) * (mu_a - mu_b)))


def _softmax_choice(items, scores, temp):
    if not items:
        return None
    m = max(scores)
    weights = [math.exp((s - m) / temp) for s in scores]
    total = sum(weights)
    r = random.random() * total
    upto = 0.0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def select_pair(states, pair_counts, rng=random):
    """Pick the next ``(slug_a, slug_b)`` to show.

    ``states``      : dict slug -> {"rating", "rd", "n"}  (n = times shown)
    ``pair_counts`` : dict frozenset({a, b}) -> int  (how often pair was shown)
    """
    slugs = list(states.keys())
    if len(slugs) < 2:
        return None

    # --- 1. Anchor: favour high uncertainty and low exposure -------------
    anchor_scores = []
    for s in slugs:
        st = states[s]
        # Higher RD and fewer appearances => higher score.
        exposure_penalty = 40.0 * math.log1p(st["n"])
        anchor_scores.append(st["rd"] - exposure_penalty)
    anchor = _softmax_choice(slugs, anchor_scores, ANCHOR_TEMP)

    # --- 2. Opponent: informative (near toss-up), uncertain, novel -------
    a_state = states[anchor]
    a_tuple = (a_state["rating"], a_state["rd"])
    candidates, scores = [], []
    for s in slugs:
        if s == anchor:
            continue
        st = states[s]
        p = _win_prob(a_tuple, (st["rating"], st["rd"]))
        # Closeness: 1.0 at p=0.5, ->0 at the extremes.
        closeness = 1.0 - abs(p - 0.5) * 2.0
        # Skip near-hopeless mismatches entirely.
        if closeness < 0.05:
            continue
        uncertainty = st["rd"] / 350.0
        seen = pair_counts.get(frozenset((anchor, s)), 0)
        score = closeness + RD_WEIGHT * uncertainty - NOVELTY_WEIGHT * seen
        candidates.append(s)
        scores.append(score)

    if not candidates:
        # Fallback: nearest by rating.
        others = [s for s in slugs if s != anchor]
        opponent = min(others, key=lambda s: abs(states[s]["rating"] - a_state["rating"]))
    else:
        opponent = _softmax_choice(candidates, scores, OPP_TEMP)

    # Randomise display order so "A" isn't always the anchor.
    pair = [anchor, opponent]
    rng.shuffle(pair)
    return pair[0], pair[1]
