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

There are **two committed configs**, so either Root Directory works:

| Vercel **Root Directory** | Config used | Best for |
|---|---|---|
| `./` (repo root) | `/vercel.json` | An existing project that already points at `./` |
| `coliseum` | `coliseum/vercel.json` | A dedicated project for this app |

**Option A — Root Directory = `./` (matches an existing `./` project).**
The repo-root `vercel.json` builds the app out of `coliseum/` via the
`@vercel/python` + static builders, so nothing else needs to change. Since
`vercel.json` is per-branch, this only affects deployments of this branch.

**Option B — a separate Vercel project (recommended; isolated).**
You can create more than one Project from the same Git repo:
1. Vercel → **Add New… → Project** → import this repo again.
2. **Settings → Git → Production Branch** = `claude/ff6-coliseum-tier-voting-…`.
3. **Settings → Build & Output → Root Directory** = `coliseum`.
   That folder's `coliseum/vercel.json` (rewrites) takes over.

Either way you need **durable storage** for votes — serverless filesystems are
ephemeral, so the default `/tmp` SQLite store is wiped between cold starts. Two
options, picked automatically by environment variable (`storage.py`):

* **Google Sheet** (zero-infrastructure, good for a one-off): set
  `SHEETS_WEBAPP_URL` + `SHEETS_TOKEN`. Step-by-step in
  [`sheets/SETUP.md`](sheets/SETUP.md).
* **Postgres** (durable, for heavier use): add a Vercel Postgres / Neon
  integration — it sets `POSTGRES_URL` and the app switches over, no code change.

Votes are stored as an append-only log and the ratings are recomputed by
replay, so all three backends (Sheets / Postgres / SQLite) behave identically.

---

## Data

The roster lives in [`data/enemies.json`](data/enemies.json): name, sprite,
membership flags, a transparent `seed_power`/`seed_rating`, an `include` flag,
and the display fields the card UI shows — **location**, the non-scaling combat
stats **ATK / M.ATK / DEF / M.DEF**, and a brief battle **description**.

Level and HP are intentionally *not* shown: in WorldsCollide both change through
the game and with scaling, so they are poor, misleading difficulty cues. The
displayed stats are the ones that don't scale.

The dataset is built in two passes:

1. **Membership + base stats from a vanilla ROM** (`export_from_rom.py`) — the
   authoritative `include` / `enemy_id` / random-encounter / coliseum flags.
2. **Display enrichment from the Gamer Corner guide** (`build_from_gamercorner.py`)
   — the comprehensive per-monster location, attack/defense, and battle notes.

```bash
python coliseum/tools/export_from_rom.py /path/to/ff3.smc   # pass 1 (repo root)
python coliseum/tools/build_from_gamercorner.py             # pass 2
```

`build_from_gamercorner.py` reads the saved guide pages in
[`resources/monsters/`](../resources/monsters) (matched by ROM short-name) and
trims each strategy note to a brief 1–2 sentences. The older Caves of Narshe
importer (`build_dataset.py`) remains as a no-ROM fallback for the sprites.

`export_from_rom.py` sets `include` precisely: an enemy is included when it is a
**random encounter or a Coliseum opponent and is not a boss** (currently 230 of
371 enemy slots), and stays correct for any (including randomized) ROM. Sprites
come from the Caves of Narshe set, copied by `build_dataset.py` (a no-ROM
fallback importer that also parses the CoN bestiary).

---

## Layout

```
coliseum/
├── app.py                 Local dev server (serves public/ + the API)
├── api/index.py           Vercel serverless function (API only)
├── core.py                Shared, stateless request logic
├── storage.py             Append-only vote log: Sheets | Postgres | SQLite
├── sheets/                Google Sheets backend: Code.gs + SETUP.md
├── glicko2.py             Dependency-free Glicko-2
├── pairing.py             Active match-up selection
├── vercel.json            Vercel routing + file bundling
├── data/
│   ├── enemies.json       Roster + seed ratings (ROM export)
│   └── tier_list.{json,md}  Exported ranking (sample = seed order, 0 votes)
├── public/                Static frontend (index.html, app.js, style.css) + sprites/
└── tools/
    ├── export_from_rom.py        ROM            -> enemies.json (membership + ids)
    ├── build_from_gamercorner.py guide pages    -> location/stats/description
    ├── build_dataset.py          CoN bestiary   -> enemies.json + sprites (no-ROM)
    ├── build_tier_list.py        store          -> tier_list.{json,md}
    └── simulate.py               convergence check (active vs random pairing)
```

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/pair` | GET | Next match-up (two enemies, chosen actively) |
| `/api/vote` | POST | `{winner, loser, voter, name}`; appends to the vote log |
| `/api/standings` | GET | Full ranked list with bottom-heavy tier labels |
| `/api/leaderboard` | GET | Players ranked by how well their picks match consensus |
| `/api/stats` | GET | Vote count, coverage, average uncertainty |

**Tiers** are bottom-heavy by design (`core.TIER_PROPORTIONS`: S 5% / A 10% /
B 15% / C 18% / D 22% / E 30% of the roster) — most enemies aren't that
dangerous, so the lower tiers are the largest.

**Calibration leaderboard:** each voter gets an anonymous id (stored in their
browser) and an optional display name. Their *accuracy* is how often their
picked winner ends up higher-rated in the consensus; *calibration* is the mean
consensus win-probability of their picks. A fun way to see who reads enemies
best. (Mildly circular — voters shape the consensus they're judged against.)

**Seeding** uses Gamer Corner's curated 0–1 threat scores (offense, durability,
physical/magic tankiness) plus magic power — a far better starting point than
enemy level — then votes take over.

## Notes & next steps

* This is a **draft**. The vote endpoint isn't abuse-hardened (no rate limiting /
  dedup) — add protection before a public link.
* Glicko-2 updates per single vote (a one-game rating period). For very high
  traffic, batch into periodic rating periods for slightly better accuracy.
* Tier thresholds are simple rating cutoffs (in `build_tier_list.py` and the
  frontend) — tune to taste or switch to gap-based clustering once data is in.
