"""Shared, stateless application logic.

Both the local dev server (``app.py``) and the Vercel serverless function
(``api/index.py``) import this.  Nothing is kept in module-level mutable state
across requests: ratings live in the store and are read fresh each call, so the
behaviour is identical whether one process or many serverless instances handle
the traffic.
"""
import os
import json

import glicko2
from pairing import select_pair
from storage import get_store

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "enemies.json")

# Trust the vanilla-power seed moderately (lower than the 350 max deviation) so
# the active pairer makes sensible match-ups from the very first vote.
SEED_RD = float(os.environ.get("COLISEUM_SEED_RD", "200"))

_ENEMIES = None      # slug -> static display record (included enemies only)
_SEEDS = None        # slug -> (rating, rd, vol)
_store = None
_seeded = False


def _load_dataset():
    global _ENEMIES, _SEEDS
    if _ENEMIES is not None:
        return
    raw = json.load(open(DATA_PATH, encoding="utf-8"))
    _ENEMIES, _SEEDS = {}, {}
    for e in raw["enemies"]:
        if e.get("include"):
            _ENEMIES[e["slug"]] = e
            _SEEDS[e["slug"]] = (
                float(e.get("seed_rating", glicko2.DEFAULT_RATING)),
                SEED_RD, glicko2.DEFAULT_VOL)


def store():
    """Return the process store, seeding initial ratings once."""
    global _store, _seeded
    _load_dataset()
    if _store is None:
        _store = get_store()
    if not _seeded:
        _store.ensure_seed(_SEEDS)
        _seeded = True
    return _store


def enemies():
    _load_dataset()
    return _ENEMIES


def public_enemy(slug, state):
    e = _ENEMIES[slug]
    s = state[slug]
    return {
        "slug": slug,
        "name": e["name"],
        "sprite": f"/sprites/{e['sprite']}" if e.get("sprite") else None,
        "sprite_cdn": e.get("sprite_cdn"),
        "level": e["level"],
        "hp": e["hp"],
        "type": e.get("type") or "",
        "location": e.get("location") or "",
        "coliseum": e.get("coliseum", False),
        "rating": round(s["rating"]),
        "rd": round(s["rd"]),
    }


def get_pair():
    st = store()
    state = st.all_ratings()
    pair = select_pair(state, st.pair_counts())
    if not pair:
        return None
    a, b = pair
    return {"a": public_enemy(a, state), "b": public_enemy(b, state)}


def cast_vote(winner, loser):
    ens = enemies()
    if winner not in ens or loser not in ens or winner == loser:
        return None
    st = store()
    state = st.all_ratings()
    w, l = state[winner], state[loser]
    wr = glicko2.Rating(w["rating"], w["rd"], w["vol"])
    lr = glicko2.Rating(l["rating"], l["rd"], l["vol"])
    new_w = glicko2.rate(wr, [(lr, 1.0)])
    new_l = glicko2.rate(lr, [(wr, 0.0)])
    nw = {"rating": new_w.rating, "rd": new_w.rd, "vol": new_w.vol, "n": w["n"] + 1}
    nl = {"rating": new_l.rating, "rd": new_l.rd, "vol": new_l.vol, "n": l["n"] + 1}
    st.record_vote(winner, loser, nw, nl)
    new_state = {winner: nw, loser: nl}
    return {"ok": True,
            "winner": public_enemy(winner, new_state),
            "loser": public_enemy(loser, new_state)}


def standings():
    st = store()
    state = st.all_ratings()
    ranked = sorted(state, key=lambda s: state[s]["rating"], reverse=True)
    out = []
    for rank, slug in enumerate(ranked, 1):
        d = public_enemy(slug, state)
        d["rank"] = rank
        out.append(d)
    return {"standings": out, "total_votes": st.vote_count()}


def stats():
    st = store()
    state = st.all_ratings()
    rds = [s["rd"] for s in state.values()]
    ns = [s["n"] for s in state.values()]
    return {
        "enemies": len(state),
        "total_votes": st.vote_count(),
        "avg_rd": round(sum(rds) / len(rds), 1) if rds else 0,
        "min_appearances": min(ns) if ns else 0,
        "unrated": sum(1 for n in ns if n == 0),
    }
