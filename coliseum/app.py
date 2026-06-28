#!/usr/bin/env python3
"""FF6 Coliseum - a head-to-head voting site for ranking FF6 enemies.

Visitors are shown two enemies and click the one they think would win a fight.
Votes drive a Glicko-2 rating per enemy; an active pairing strategy chooses
informative match-ups so the ranking converges quickly.  The resulting order is
exported as a tier list for the WorldsCollide project.

Run:
    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:5000
"""
import os
import json
import sqlite3
import threading

from flask import Flask, jsonify, request, send_from_directory

import glicko2
from pairing import select_pair

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "data", "enemies.json")
DB_PATH = os.environ.get("COLISEUM_DB", os.path.join(HERE, "votes.db"))

app = Flask(__name__, static_folder=os.path.join(HERE, "static"), static_url_path="/static")

# The vanilla-power seed is a useful but imperfect prior, so new enemies start
# with a moderate deviation rather than the maximum 350 -- this lets the active
# pairer pick sensibly-close match-ups from the very first vote while still
# leaving plenty of room for the crowd to move ratings.
SEED_RD = float(os.environ.get("COLISEUM_SEED_RD", "200"))

_lock = threading.Lock()       # serialise rating updates (SQLite + in-memory)
ENEMIES = {}                   # slug -> static display record (included only)
STATE = {}                     # slug -> {"rating","rd","vol","n"}  (live ratings)
PAIR_COUNTS = {}               # frozenset({a,b}) -> times shown together


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                slug   TEXT PRIMARY KEY,
                rating REAL NOT NULL,
                rd     REAL NOT NULL,
                vol    REAL NOT NULL,
                n      INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS votes (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                winner  TEXT NOT NULL,
                loser   TEXT NOT NULL,
                ts      DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_votes_pair ON votes(winner, loser);
            """
        )


def load_dataset():
    raw = json.load(open(DATA_PATH, encoding="utf-8"))
    for e in raw["enemies"]:
        if e.get("include"):
            ENEMIES[e["slug"]] = e
    return raw


def load_or_seed_state():
    """Load live ratings from the DB, seeding any new enemies from the dataset."""
    with db() as conn:
        rows = {r["slug"]: r for r in conn.execute("SELECT * FROM ratings")}
        for slug, e in ENEMIES.items():
            if slug in rows:
                r = rows[slug]
                STATE[slug] = {"rating": r["rating"], "rd": r["rd"],
                               "vol": r["vol"], "n": r["n"]}
            else:
                STATE[slug] = {"rating": float(e.get("seed_rating", glicko2.DEFAULT_RATING)),
                               "rd": SEED_RD, "vol": glicko2.DEFAULT_VOL, "n": 0}
                conn.execute(
                    "INSERT INTO ratings(slug, rating, rd, vol, n) VALUES (?,?,?,?,?)",
                    (slug, STATE[slug]["rating"], STATE[slug]["rd"],
                     STATE[slug]["vol"], 0),
                )
        # Rebuild pair counts from recorded votes.
        for row in conn.execute("SELECT winner, loser FROM votes"):
            key = frozenset((row["winner"], row["loser"]))
            PAIR_COUNTS[key] = PAIR_COUNTS.get(key, 0) + 1


def _persist_rating(conn, slug):
    s = STATE[slug]
    conn.execute(
        "UPDATE ratings SET rating=?, rd=?, vol=?, n=? WHERE slug=?",
        (s["rating"], s["rd"], s["vol"], s["n"], slug),
    )


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------
def public_enemy(slug):
    e = ENEMIES[slug]
    s = STATE[slug]
    sprite_url = f"/static/sprites/{e['sprite']}" if e.get("sprite") else None
    return {
        "slug": slug,
        "name": e["name"],
        "sprite": sprite_url,
        "sprite_cdn": e.get("sprite_cdn"),
        "level": e["level"],
        "hp": e["hp"],
        "type": e.get("type") or "",
        "location": e.get("location") or "",
        "coliseum": e.get("coliseum", False),
        "rating": round(s["rating"]),
        "rd": round(s["rd"]),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/pair")
def api_pair():
    pair = select_pair(STATE, PAIR_COUNTS)
    if not pair:
        return jsonify({"error": "not enough enemies"}), 500
    a, b = pair
    return jsonify({"a": public_enemy(a), "b": public_enemy(b)})


@app.route("/api/vote", methods=["POST"])
def api_vote():
    payload = request.get_json(force=True, silent=True) or {}
    winner = payload.get("winner")
    loser = payload.get("loser")
    if winner not in ENEMIES or loser not in ENEMIES or winner == loser:
        return jsonify({"error": "invalid pair"}), 400

    with _lock:
        w, l = STATE[winner], STATE[loser]
        w_rating = glicko2.Rating(w["rating"], w["rd"], w["vol"])
        l_rating = glicko2.Rating(l["rating"], l["rd"], l["vol"])

        # One-game rating period for each side against the other's prior rating.
        new_w = glicko2.rate(w_rating, [(l_rating, 1.0)])
        new_l = glicko2.rate(l_rating, [(w_rating, 0.0)])

        for slug, nr in ((winner, new_w), (loser, new_l)):
            STATE[slug].update(rating=nr.rating, rd=nr.rd, vol=nr.vol)
            STATE[slug]["n"] += 1

        key = frozenset((winner, loser))
        PAIR_COUNTS[key] = PAIR_COUNTS.get(key, 0) + 1

        with db() as conn:
            conn.execute("INSERT INTO votes(winner, loser) VALUES (?,?)", (winner, loser))
            _persist_rating(conn, winner)
            _persist_rating(conn, loser)

    return jsonify({
        "ok": True,
        "winner": public_enemy(winner),
        "loser": public_enemy(loser),
    })


@app.route("/api/standings")
def api_standings():
    ranked = sorted(STATE, key=lambda s: STATE[s]["rating"], reverse=True)
    out = []
    for rank, slug in enumerate(ranked, 1):
        d = public_enemy(slug)
        d["rank"] = rank
        out.append(d)
    return jsonify({"standings": out, "total_votes": total_votes()})


@app.route("/api/stats")
def api_stats():
    rds = [s["rd"] for s in STATE.values()]
    ns = [s["n"] for s in STATE.values()]
    return jsonify({
        "enemies": len(STATE),
        "total_votes": total_votes(),
        "avg_rd": round(sum(rds) / len(rds), 1) if rds else 0,
        "min_appearances": min(ns) if ns else 0,
        "unrated": sum(1 for n in ns if n == 0),
    })


def total_votes():
    with db() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM votes").fetchone()["c"]


def bootstrap():
    init_db()
    load_dataset()
    load_or_seed_state()


bootstrap()

if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=True)
