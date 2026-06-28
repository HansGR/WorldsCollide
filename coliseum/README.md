# FF6 Coliseum

A small head-to-head voting site for building a **difficulty tier list of FF6
random-encounter and Coliseum enemies** for the
[WorldsCollide](https://github.com/HansGR/WorldsCollide) project.

Visitors are shown two enemies and click the one they think would *win in a
fight*. Each vote updates a [Glicko-2](http://www.glicko.net/glicko/glicko2.pdf)
rating per enemy, and an **active pairing** strategy keeps serving informative,
closely matched bouts so the ranking converges fast. The result is exported as
an ordered S/A/B/... tier list.

---

## Why this design

* **The tier list is the goal, not raw stats.** Vanilla enemy *level* is only a
  rough proxy for difficulty — some enemies (Orog, Outsider, Intangir, ...)
  punch far above their level. A simulation against synthetic "true" difficulty
  shows the vanilla-stat prior correlates only **~0.42** with truth, so the
  crowd's votes are what actually build the ranking.
* **Glicko-2** gives every enemy a rating *and* an uncertainty (rating
  deviation) — used both to pick good match-ups and to know when a placement is
  settled.
* **Active pair selection** ([`pairing.py`](pairing.py)) combines three ideas
  from the active-ranking literature: *uncertainty sampling* (show fuzzy / rarely
  seen enemies), *information maximisation* (pick a near toss-up opponent, win
  prob ≈ 0.5 — exactly the overlapping clusters worth disambiguating, and never a
  blowout), and *softmax exploration* (spread coverage). In simulation it beats
  random pairing at every vote budget (`python tools/simulate.py`).

---

## Run locally

```bash
cd coliseum
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py                      # -> http://127.0.0.1:5000
```

Vote a while, then export the tier list:

```bash
python tools/build_tier_list.py    # -> data/tier_list.json + data/tier_list.md
```

Env knobs: `PORT`, `HOST`, `COLISEUM_DB` (SQLite path), `COLISEUM_SEED_RD`
(how much to trust the vanilla prior; lower = more), `POSTGRES_URL` (see below).

---

## Deploy on Vercel

The app is split the way Vercel expects: static frontend in `public/` (served by
the CDN) and a Python serverless function in `api/index.py` for the API. The
logic is **stateless** — every request reads/writes ratings through the store —
so it is correct across multiple serverless instances.

1. In Vercel, **import the repo** and set **Root Directory = `coliseum`**.
   (This is the key step — without it Vercel sees the WorldsCollide Python repo,
   finds nothing web-servable, and returns 404.)
2. Deploy. `vercel.json` routes `/api/*` to the function and serves `public/`
   statically; `requirements.txt` installs Flask.
3. **For durable votes, add storage.** Serverless filesystems are ephemeral, so
   without a database the bundled SQLite store lives in `/tmp` and is wiped
   between cold starts (fine for a quick demo, not for real crowd-sourcing).
   Add a Vercel Postgres / Neon integration to the project — it sets
   `POSTGRES_URL` automatically and the app switches to Postgres on the next
   deploy (`storage.py`). No code change needed.

> Prefer Vercel Postgres/Neon (one-click) over SQLite for any shared link.

---

## Data

The roster lives in [`data/enemies.json`](data/enemies.json): name, sprite,
vanilla stats, membership flags, a transparent `seed_power`/`seed_rating`, and an
`include` flag. **The shipped dataset is exported from a vanilla ROM** (below);
the Caves of Narshe path is the fallback when no ROM is handy.

### Authoritative — straight from a ROM (what ships here)

```bash
# run from the WorldsCollide repo root
python coliseum/tools/export_from_rom.py /path/to/ff3.smc
```

Reads the real game data through this repo's own data classes and sets `include`
precisely: an enemy is included when it is a **random encounter or a Coliseum
opponent and is not a boss** (currently 230 of 371 enemy slots). Also fills
`enemy_id`, World of Balance/Ruin presence, and mod-aware stats — so it stays
correct for any (including randomized) ROM. Sprites are matched over from the
Caves of Narshe set by name (exact → normalised → fuzzy).

### Fallback — Caves of Narshe bestiary

```bash
python tools/build_dataset.py /path/to/saved/"FF6_enemies"
```

Parses a saved copy of the
[CoN SNES bestiary](https://www.cavesofnarshe.com/ff6/enemies.php?ff6mode=snes)
(271 enemies) and copies sprites into `public/sprites/`. Uses a small curated
boss-exclusion list since the bestiary has no encounter/location flags.

---

## Layout

```
coliseum/
├── app.py                 Local dev server (serves public/ + the API)
├── api/index.py           Vercel serverless function (API only)
├── core.py                Shared, stateless request logic
├── storage.py             Vote/rating store: SQLite (local) | Postgres (prod)
├── glicko2.py             Dependency-free Glicko-2
├── pairing.py             Active match-up selection
├── vercel.json            Vercel routing + file bundling
├── data/
│   ├── enemies.json       Roster + seed ratings (ROM export)
│   └── tier_list.{json,md}  Exported ranking (sample = seed order, 0 votes)
├── public/                Static frontend (index.html, app.js, style.css) + sprites/
└── tools/
    ├── export_from_rom.py   WorldsCollide ROM     -> enemies.json (authoritative)
    ├── build_dataset.py     Caves of Narshe HTML  -> enemies.json + sprites
    ├── build_tier_list.py   store                 -> tier_list.{json,md}
    └── simulate.py          convergence check (active vs random pairing)
```

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/pair` | GET | Next match-up (two enemies, chosen actively) |
| `/api/vote` | POST | `{winner, loser}` slugs; updates ratings |
| `/api/standings` | GET | Full ranked list |
| `/api/stats` | GET | Vote count, coverage, average uncertainty |

## Notes & next steps

* This is a **draft**. The vote endpoint isn't abuse-hardened (no rate limiting /
  dedup) — add protection before a public link.
* Glicko-2 updates per single vote (a one-game rating period). For very high
  traffic, batch into periodic rating periods for slightly better accuracy.
* Tier thresholds are simple rating cutoffs (in `build_tier_list.py` and the
  frontend) — tune to taste or switch to gap-based clustering once data is in.
