"""Shared, stateless application logic.

Ratings are not stored: we replay the vote log through Glicko-2 on each request
(cheap, and identical across serverless instances).  Seeds come from the
curated Gamer Corner threat scores in ``data/enemies.json``.
"""
import os
import json
import time

import glicko2
from pairing import select_pair
from storage import get_store

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "enemies.json")

SEED_RD = float(os.environ.get("COLISEUM_SEED_RD", "200"))

# Tier sizes as a fraction of the ranked roster, deliberately bottom-heavy:
# most enemies aren't that dangerous, so the lower tiers are the largest and
# the bottom tier is wider than the mid tiers.
TIER_PROPORTIONS = [("S", 0.05), ("A", 0.10), ("B", 0.15),
                    ("C", 0.18), ("D", 0.22), ("E", 0.30)]

_ENEMIES = None      # slug -> static display record (included only)
_SEEDS = None        # slug -> seed rating
_store = None
_cache = None        # (votes_len, state, pair_counts, votes)


def _load_dataset():
    global _ENEMIES, _SEEDS
    if _ENEMIES is not None:
        return
    raw = json.load(open(DATA_PATH, encoding="utf-8"))
    _ENEMIES, _SEEDS = {}, {}
    for e in raw["enemies"]:
        if e.get("include"):
            _ENEMIES[e["slug"]] = e
            _SEEDS[e["slug"]] = float(e.get("seed_rating", glicko2.DEFAULT_RATING))


def store():
    global _store
    if _store is None:
        _store = get_store()
    return _store


def enemies():
    _load_dataset()
    return _ENEMIES


def _replay(votes):
    """Replay the vote log -> (state, pair_counts).

    state: slug -> {rating, rd, vol, n}; pair_counts: frozenset({a,b}) -> count.
    """
    state = {s: {"rating": _SEEDS[s], "rd": SEED_RD, "vol": glicko2.DEFAULT_VOL, "n": 0}
             for s in _ENEMIES}
    pair_counts = {}
    for v in votes:
        w, l = v.get("winner"), v.get("loser")
        if w not in state or l not in state:
            continue
        ws, ls = state[w], state[l]
        wr = glicko2.Rating(ws["rating"], ws["rd"], ws["vol"])
        lr = glicko2.Rating(ls["rating"], ls["rd"], ls["vol"])
        nw = glicko2.rate(wr, [(lr, 1.0)])
        nl = glicko2.rate(lr, [(wr, 0.0)])
        ws.update(rating=nw.rating, rd=nw.rd, vol=nw.vol, n=ws["n"] + 1)
        ls.update(rating=nl.rating, rd=nl.rd, vol=nl.vol, n=ls["n"] + 1)
        key = frozenset((w, l))
        pair_counts[key] = pair_counts.get(key, 0) + 1
    return state, pair_counts


def _compute():
    """Return (state, pair_counts, votes), memoised by vote count within a warm
    process so repeated reads don't re-replay the same log."""
    global _cache
    _load_dataset()
    votes = store().get_votes()
    if _cache is None or _cache[0] != len(votes):
        state, pair_counts = _replay(votes)
        _cache = (len(votes), state, pair_counts, votes)
    return _cache[1], _cache[2], _cache[3]


def _tiers_by_rank(ranked):
    """Assign a tier label to each slug in a rating-descending list."""
    n = len(ranked)
    tiers = {}
    idx = 0
    for label, frac in TIER_PROPORTIONS:
        count = round(frac * n)
        for _ in range(count):
            if idx < n:
                tiers[ranked[idx]] = label
                idx += 1
    while idx < n:                      # rounding remainder -> bottom tier
        tiers[ranked[idx]] = TIER_PROPORTIONS[-1][0]
        idx += 1
    return tiers


def public_enemy(slug, state, tier=None):
    e = _ENEMIES[slug]
    s = state[slug]
    return {
        "slug": slug,
        "name": e["name"],
        "sprite": f"/sprites/{e['sprite']}" if e.get("sprite") else None,
        "sprite_cdn": e.get("sprite_cdn"),
        "location": e.get("location") or "",
        "atk": e.get("bat_pwr"),
        "matk": e.get("mag_pwr"),
        "dfn": e.get("defense"),
        "mdef": e.get("magic_def"),
        "description": e.get("description") or "",
        "coliseum": e.get("coliseum", False),
        "rating": round(s["rating"]),
        "rd": round(s["rd"]),
        "comparisons": s["n"],
        "tier": tier,
    }


def get_pair():
    state, pair_counts, _ = _compute()
    pair = select_pair(state, pair_counts)
    if not pair:
        return None
    a, b = pair
    return {"a": public_enemy(a, state), "b": public_enemy(b, state)}


def cast_vote(winner, loser, voter="", name=""):
    ens = enemies()
    if winner not in ens or loser not in ens or winner == loser:
        return None
    try:
        store().append_vote(voter or "anon", name or "", winner, loser)
    except Exception as e:
        # Surface storage failures (e.g. Sheets misconfig) instead of pretending
        # the vote was recorded.
        return {"ok": False, "error": str(e)[:400]}
    global _cache
    _cache = None     # force recompute on next read
    state, _ = _replay(store().get_votes())
    return {"ok": True,
            "winner": public_enemy(winner, state),
            "loser": public_enemy(loser, state)}


def health(write_test=False):
    """Report which storage backend is active and whether it actually works.

    GET /api/health           - backend + a live read test
    GET /api/health?write=1   - also append a 'healthcheck' vote (writes a row)
    """
    s = store()
    info = {
        "backend": type(s).__name__,
        "env": {k: bool(os.environ.get(k)) for k in
                ("SHEETS_WEBAPP_URL", "SHEETS_TOKEN", "POSTGRES_URL",
                 "DATABASE_URL", "VERCEL")},
    }
    if hasattr(s, "url"):
        info["sheets_token_set"] = bool(getattr(s, "token", ""))
    try:
        if hasattr(s, "_cache"):
            s._cache = None              # force a fresh read for the check
        info["vote_count"] = len(s.get_votes())
        info["can_read"] = True
    except Exception as e:
        info["can_read"] = False
        info["error"] = str(e)[:400]
        return info

    if write_test:
        _load_dataset()
        a, b = list(_ENEMIES)[:2]
        try:
            s.append_vote("healthcheck", "healthcheck", a, b)
            if hasattr(s, "_cache"):
                s._cache = None
            info["can_write"] = True
            info["vote_count_after_write"] = len(s.get_votes())
            info["note"] = "Wrote a 'healthcheck' row; you can delete it from the sheet."
        except Exception as e:
            info["can_write"] = False
            info["error"] = str(e)[:400]
    return info


def standings():
    state, _, votes = _compute()
    ranked = sorted(state, key=lambda s: state[s]["rating"], reverse=True)
    tiers = _tiers_by_rank(ranked)
    out = []
    for rank, slug in enumerate(ranked, 1):
        d = public_enemy(slug, state, tiers[slug])
        d["rank"] = rank
        out.append(d)
    return {"standings": out, "total_votes": len(votes)}


def stats():
    state, _, votes = _compute()
    rds = [s["rd"] for s in state.values()]
    ns = [s["n"] for s in state.values()]
    return {
        "enemies": len(state),
        "total_votes": len(votes),
        "avg_rd": round(sum(rds) / len(rds), 1) if rds else 0,
        "unrated": sum(1 for n in ns if n == 0),
    }


def leaderboard(min_votes=10):
    """Rank voters by how well their picks agree with the crowd consensus.

    Using the final replayed ratings, each of a voter's picks scores the
    consensus probability that their chosen winner beats the loser
    (Glicko expected score). ``accuracy`` is the share of picks where their
    winner ended up higher-rated; ``calibration`` is the mean consensus
    win-probability of their picks. (There is mild circularity - voters shape
    the consensus they're judged against - acceptable for a fun one-off.)
    """
    state, _, votes = _compute()
    agg = {}
    for v in votes:
        w, l = v.get("winner"), v.get("loser")
        if w not in state or l not in state:
            continue
        voter = v.get("voter") or "anon"
        a = agg.setdefault(voter, {"name": "", "n": 0, "correct": 0, "prob": 0.0})
        if v.get("name"):
            a["name"] = v["name"]
        p = glicko2.expected_score(glicko2.Rating(state[w]["rating"], state[w]["rd"]),
                                   glicko2.Rating(state[l]["rating"], state[l]["rd"]))
        a["n"] += 1
        a["prob"] += p
        if state[w]["rating"] >= state[l]["rating"]:
            a["correct"] += 1

    board = []
    for voter, a in agg.items():
        if a["n"] < min_votes:
            continue
        board.append({
            "voter": voter,
            "name": a["name"] or f"Anon-{voter[:4]}",
            "votes": a["n"],
            "accuracy": round(100 * a["correct"] / a["n"], 1),
            "calibration": round(100 * a["prob"] / a["n"], 1),
        })
    board.sort(key=lambda x: (x["accuracy"], x["calibration"], x["votes"]), reverse=True)
    for i, row in enumerate(board, 1):
        row["rank"] = i
    return {"leaderboard": board, "min_votes": min_votes,
            "total_voters": len(agg)}
