# FF6 Coliseum

A small head-to-head voting site for building a **difficulty tier list of FF6
random-encounter and Coliseum enemies** for the
[WorldsCollide](https://github.com/HansGR/WorldsCollide) project.

Visitors are shown two enemies and click the one they think would *win in a
fight*. Each vote updates a [Glicko-2](http://www.glicko.net/glicko/glicko2.pdf)
rating, and an **active pairing** strategy keeps serving informative, closely
matched bouts so the ranking converges fast. The result is exported as an
ordered S/A/B/... tier list.

![arena](static/sprites/brachosaur.png)

---

## Why this design

* **The tier list is the goal, not raw stats.** Vanilla enemy *level* is only a
  rough proxy for difficulty — some enemies (Orog, Outsider, Intangir, ...)
  punch far above their level. A simulation against synthetic "true" difficulty
  shows the vanilla-stat prior correlates only **~0.42** with truth, so the
  crowd's votes are what actually build the ranking.
* **Glicko-2** gives every enemy a rating *and* an uncertainty (rating
  deviation). That uncertainty is what lets us pick good match-ups and know when
  a placement is settled.
* **Active pair selection** (see [`pairing.py`](pairing.py)) combines three
  ideas from the active-ranking literature:
  1. *Uncertainty sampling* — show enemies whose rating is still fuzzy or that
     haven't appeared much.
  2. *Information maximisation* — given an anchor, pick an opponent the model
     thinks is a near toss-up (win probability ≈ 0.5). These are exactly the
     overlapping, high-variance clusters worth disambiguating, and it guarantees
     pairs are never wildly mismatched.
  3. *Novelty + softmax exploration* — down-weight pairs already seen and sample
     stochastically so coverage spreads.

  In simulation, active pairing reaches a given rank correlation with
  meaningfully fewer votes than random pairing (run `tools/simulate.py`).

---

## Quick start

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

Environment knobs: `PORT`, `HOST`, `COLISEUM_DB` (vote DB path),
`COLISEUM_SEED_RD` (how much to trust the vanilla prior; lower = more).

---

## Data

The roster lives in [`data/enemies.json`](data/enemies.json): name, sprite,
vanilla stats, a transparent `seed_power`/`seed_rating`, and an `include` flag.
There are two ways to (re)build it.

### 1. Draft data — Caves of Narshe bestiary (what ships here)

```bash
python tools/build_dataset.py /path/to/saved/"FF6_enemies"
```

Parses a saved copy of the
[Caves of Narshe SNES bestiary](https://www.cavesofnarshe.com/ff6/enemies.php?ff6mode=snes)
(271 enemies) into `data/enemies.json` and copies the sprites into
`static/sprites/`. Clear bosses / scripted-event enemies are excluded by a small
curated list (easy to edit); everything else defaults to included. Five sprites
that weren't lazy-loaded in the saved page fall back to the CoN CDN URL in the
browser.

### 2. Authoritative data — straight from a ROM

```bash
# run from the WorldsCollide repo root
python coliseum/tools/export_from_rom.py /path/to/ff3.smc
```

Reads the real game data through this repo's own data classes and sets
`include` precisely: an enemy is included when it is a **random encounter or a
Coliseum opponent and is not a boss**. Also fills `enemy_id`, World of
Balance/Ruin presence, and mod-aware stats — so the dataset stays correct for
any (including randomized) ROM. Sprites/CDN URLs are carried over from the
existing dataset by name.

---

## Layout

```
coliseum/
├── app.py                 Flask backend: pairing, voting, Glicko-2 updates, API
├── glicko2.py             Dependency-free Glicko-2
├── pairing.py             Active match-up selection
├── data/
│   ├── enemies.json       Roster + seed ratings (generated)
│   └── tier_list.{json,md}  Exported ranking (sample = seed order, 0 votes)
├── static/                Frontend (index.html, app.js, style.css) + sprites/
└── tools/
    ├── build_dataset.py     Caves of Narshe HTML  -> enemies.json + sprites
    ├── export_from_rom.py   WorldsCollide ROM     -> enemies.json (authoritative)
    ├── build_tier_list.py   votes.db              -> tier_list.{json,md}
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

* This is a **draft**. The voting endpoint isn't abuse-hardened (no rate
  limiting / dedup) — fine for trusted/community use; add protections before a
  public deploy.
* Glicko-2 updates per single vote (a one-game rating period). For very high
  traffic, batch into periodic rating periods for slightly better accuracy.
* Tier thresholds are simple rating cutoffs in `build_tier_list.py` and the
  frontend; tune to taste, or switch to gap-based clustering once data is in.
