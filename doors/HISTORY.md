# Door Randomizer — Development History

Key milestones in the development of Worlds Collide door randomization,
from first alpha to the current architecture. Dates and commit ids refer
to the branches noted; everything here is reachable through git history
(`doorRandomizer`, `doorRandomizer-beta`, `doorRandomizer-new`,
`claude_ruination`, `door_rando_ruin_rewrite`).

| # | Date | Commit | Milestone |
|---|------|--------|-----------|
| 1 | 2022-01-13 | `6266892` | Fork point: door randomization begins as a fork of the Worlds Collide open-worlds randomizer. |
| 2 | 2022-09-06 | `b0120e1` | **alpha.01** (`doorRandomizer`): first door-randomizer alpha; the alpha series (01–57) builds out exit data and per-area randomization through spring 2023. |
| 3 | 2023-04-20 | `d068379` | First working door randomization built on the **constructive walk**: grow from a start room, connect frontier exits to random entrances, backtrack on infeasibility. The walk remains the heart of every mode. |
| 4 | 2023-05-12 | `3432b07` | **beta.01** (`doorRandomizer-beta`/`-new`): individual-area flags mature (`-dru`, `-drem`, `-drmf`, …); walk logic handles keys, locks, and forced connections (beta.04–05). |
| 5 | 2023-05–06 | `87dfb13`, `16c7723`, `4d9c9f3` | beta.03–06: Phantom Train, Cyan's Dream, Mt. Kolts, and Cave on the Veldt join the randomizable areas; `-dra` (all areas) assembles them. |
| 6 | 2024-12-17 | `117e229` | **gamma.01: Map Shuffle** (`-maps`, later `-mapx` crossworld): overworld entrances randomize, with protections to keep door rando and map shuffle composable. |
| 7 | 2025-01-20 | `21650b5` | **gamma.04: Dungeon Crawl** (`-drdc`) becomes its own mode: all doors form one giant dungeon, world map made into dead ends, towns become walk-through rooms via split exits. |
| 8 | 2025-01-30 | `260fa28` | **gamma.06: Ruination mode** (`-ruin`) first push — rogue-like mode: no airship, Narshe hub, three branches, rewards discovered by exploration. |
| 9 | 2025-02 | `c69cc24`–`acf9c1c` | Ruination mapping algorithm: hub/branch growth toward reward rooms, character-locked rewards, per-event scene rework (moogle defense, Zozo, Lone Wolf, KT entry). |
| 10 | 2026-04-27 | `54ca556` | Matured ruination lands on `claude_ruination`: six-step branch finalize, warp/reserve rescues, ferry network with sea boss, dream maze, party-interaction and y-switch machinery. |
| 11 | 2026-05-13 | `91a500c`, `b1f5304` | Mode deconfliction: ruination, dungeon crawl, door rando, and map shuffle coexist in one codebase with defined precedence. |
| 12 | 2026-07-01–05 | `1bd211c`–`89e505c` | Full door-rando **code review** and seven remediation phases (p1–p7): exit-table corrections, deterministic budgets, journaled backtracking, performance. The review's findings motivate a ground-up rewrite plan. |
| 13 | 2026-07-05 | `3f02164` | **Atlas**: the vanilla exit table becomes generated, consistency-checked data (`doors/atlas/`, `tools/compile_atlas.py`) with hand-owned curation, replacing 2,000 lines of hand-maintained partner data; room naming registry (59 areas, 851 rooms) follows after review (`b084dd3`). |
| 14 | 2026-07-07 | `3ca69ab`, `ab98341` | **World model + walk planner** (`doors/model.py`, `doors/plan/walk.py`): journaled union-find state with checkpoint/rollback backtracking (no copies), the walk and its feasibility rules ported and proven equivalent across all 18 `-dre` pools. |
| 15 | 2026-07-07 | `ec7d30d`, `7cc0328` | Every door-randomization and map-shuffle mode planned by the one engine (`doors/plan/modes.py`); whole-mode distribution parity confirmed statistically. |
| 16 | 2026-07-08 | `f584fb1`–`196b9fc` | **Ruination planner** rebuilt on the shared world model (`doors/plan/ruination/`): branch growth, six-step finalize, BFS softlock verifier, dream maze and Kefka's Tower lane randomizers; whole-plan distribution parity with the original generator. |
| 17 | 2026-07-09 | `7204a9d` | **One planning site**: every mode — including ruination — produces a `DoorPlan` artifact in one contiguous RNG window during the Data phase; the Events phase only binds rewards (`event/ruination_bind.py`). The reward snapshot/retry machinery this replaced is deleted. |
| 18 | 2026-07-13 | `4ecb1fc` | **Cutover**: the `doors/` planner becomes the only implementation; the previous walk engine and ruination generator (~8,900 lines) are deleted, proven byte-identical across an 8-mode golden matrix. |
| 19 | 2026-07-13 | `4ee7994`–`10c6a51` | Event-layer mechanics: per-event flag chains replaced by the derived `doors_touched` predicate, lifecycle hooks dispatched by the Events loop, `DoorPlan` query API and unified `gates` table, generated mode × event manifest (`tools/mode_manifest.py`). |
| 20 | 2026-07-13 | `00369d7`–`dd97e8d` | **Realization** re-homed into `doors/realize/` (exit connection, one-way transitions, event-tile updates); per-mode table setup becomes the documented `apply_mode_table_adjustments`; `tools/golden_sweep.py` and its committed 15-config manifest become the permanent byte-level regression gate. |
| 21 | 2026-07-17 | `479f376`, `c05d065` | **Room names become the room ids**: after the naming registry converged (3-letter area codes, WoB/WoR twin ordinals, variant suffixes), `data/rooms.py` is re-keyed to the names and the registry layer is deleted — numbers are always exits, formatted strings are always rooms. `# was:` comments preserve the old numeric ids. Non-ruin output byte-identical; `-ruin` seeds re-recorded (room iteration order at the planner's sorted RNG boundaries follows the new ids). |
| 22 | 2026-07-24 | `06b1c88`…`931596a` | **Post-completion structural review**: door_randomize derives from the planner's flag table; `data/event_exit_patches.py` (patch machinery) splits from the pure tables by name; the atlas becomes self-contained (`doors/atlas/exits_raw.json`); the mutate-and-reset pattern is retired — mode table adjustments are per-plan views on the DoorPlan, and the only per-build scratch (exit_data dc-override, event_exit_info runtime addresses) is reset in `Doors.__init__`; `doors/ids.py` states the element id space once; an import-order-dependent RNG draw (the Daryl's Tomb spelling flip) moves to its consumption site, re-anchoring every seed once. A commentary sweep makes the remaining prose canonical. |

Design records that shaped these milestones (review findings, rewrite
rationale, parity results) live in the git history of
`DOOR_RANDO_CODE_REVIEW.md` and `DOOR_RANDO_REWRITE_PLAN.md` on the
`door_rando_ruin_rewrite` branch.
