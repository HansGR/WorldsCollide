# Door Randomization v2 — Ground-Up Rewrite Plan

*2026-07. Written after completing the full code review
(`DOOR_RANDO_CODE_REVIEW.md`) and seven remediation phases (p1–p7), with
the accumulated knowledge in `DOOR_RANDO_GUIDE.md` and `ARCHIVE.md`. This
is the answer to: "knowing everything we now know, how would we build door
randomization from scratch on top of `ff6wc/dev`?"*

---

## 0. What the thing actually is

Years of experimentation obscured a simple shape. Door randomization, in
every mode, is the same five-step pipeline:

1. **Atlas** — a static description of the vanilla world: exits, the rooms
   that group them, which transitions are one-way, what is locked behind
   what.
2. **Plan** — given a mode and a seed, sample a *legal matching*: every
   two-way door side paired with another, every one-way exit given a
   landing point, plus mode-specific structure (dungeon-crawl chain,
   ruination's three branches, shuffled world-map slots) and any reward /
   gating decisions that depend on the map.
3. **Validate** — prove the plan legal: reciprocity, trap/pit parity,
   reachability of every objective, no key/character softlocks.
4. **Realize** — write the plan into the ROM: exit tables, one-way
   transition scripts, event-tile connection data, character-gating
   patches, destination-dependent dialog, clue scripts.
5. **Report** — spoiler log, map image, debug routes.

The current code interleaves these five concerns across ~16,400 lines
(`data/rooms.py`, `walks.py`, `doors.py`, `map_exit_extra.py`,
`event_exit_info.py`, `transitions.py`, `maps.py`, `event/ruination.py`),
with planning happening in two different pipeline phases depending on mode
(Data for `-dr*`, Events for `-ruin`), and with the atlas stored as
mutable module globals that double as planner scratch space. The rewrite
is mostly the act of giving each of the five steps its own home.

## 1. Goals and non-goals

**Goals**
- Same game-mode outcomes: every current flag (`-drdc`, `-dra`, `-drx`,
  `-dre`, `-dru`…, `-maps`, `-mapx`, `-ruin`, `-rkt`, `-maze`) produces
  the same *kind* of map with the same player-facing guarantees.
- Preserve the **sampling character**, not the bytes: uniform random
  candidate selection with backtracking, rejection sampling for small
  maps (KT lanes, FC, dream maze). No new bias toward hubs or toward
  simpler maps (the standing 9.4/9.6 decisions).
- Deterministic and hardware-independent: a seed is a pure function of
  `(flags, seed string)`; no wall-clock, no hash-order dependence.
- Plannable without a ROM: steps 1–3 import and run standalone, so they
  are unit-testable and scriptable (the current code cannot even be
  imported without a loaded ROM — review 3.7).
- One directory. The feature should rebase onto upstream `dev` with
  minimal friction: thin hooks in `wc.py`/`data/maps.py`/`event/events.py`
  and per-event patches in their own `event/*.py` files (WC convention),
  everything else self-contained.

**Non-goals**
- Byte-identical seeds with the current implementation (explicitly waived).
- New game modes or new randomization features during the rewrite.
- Changing the flag surface, spoiler-log information content, or the
  player-visible contract of any mode.

## 2. What the current code taught us (design flaws to fix, ideas to keep)

Flaws that exist only because of history:

| # | Flaw | Rewrite answer |
|---|------|----------------|
| F1 | **ID arithmetic as type system** — element kind is encoded in numeric ranges (<2000 doors, 1500–1999 event tiles, 2000–2999 traps, 3000+ pits = trap+1000, 4000+ logical WoR = door+4000, 6000+ door-as-trap, 10000+ virtual roots, 20000+ crossworld, 30000+ shuffle-protected). Every layer re-derives kind with `element_type()` and ±offsets. | Typed `Exit` records. Vanilla exit indices remain the *handles* (they are the ROM's names), but kind/world/role are fields, not arithmetic. Synthetic exits (roots, crossworld links) are explicit objects with no magic ranges. |
| F2 | **Compound room IDs** — `compress_loop` merges rooms by joining IDs with `'_'`, forcing the `_<id>_` bracketed-substring convention everywhere and producing an entire bug class (review 1.9). | Merging is a union-find over stable integer node handles. Display names are derived for logs only; no code ever parses an ID. |
| F3 | **Module globals as scratch space** — `room_data`, `shared_exits`, `forced_connections`, `exit_data` are mutated per build; p2 added reset functions to make this survivable. | The atlas is immutable after load. All mutable state lives in planner-owned objects with explicit lifetimes. Reset functions become unnecessary. |
| F4 | **Copy-based backtracking** — deepcopy per attempt was ~80% of walk time pre-p5; even now (p7) copying is ~20%. It exists because the mutation surface grew too tangled to undo. | Journal-based undo designed in from day 1: exactly three mutating operations (`connect_door`, `connect_oneway`, `apply_key`), each journaled; union-find with rollback. Zero copies. |
| F5 | **Two planning sites** — `Doors.mod` (Data phase) for `-dr*`; `events.ruination_mod` (Events phase) for `-ruin`, which forced the fragile snapshot/rollback of character/esper/reward state around mapping retries (review 3.4). | One planning site. The ruination planner deals in *abstract* check sites and reward kinds (static data + args); the Events phase binds real `Reward` objects afterward. A failed plan is discarded and re-rolled with no rollback at all. |
| F6 | **Modes as code paths** — 400 lines of `if/elif` in `Doors.__init__` assembling room sets, protections, splits, and postprocessing by flag. | Modes as data: a `ModeSpec` names pools, constraints, start rule, protections, and post-steps; one engine interprets it. |
| F7 | **Hand-maintained partner table** — `exit_data`'s 2,060 lines of `[partner, description]` accumulated real errors (review 1.4/1.5, fixed by coordinate cross-checking in p1). | Compile partners from `exits_raw.json` coordinates at build time; hand-annotate only true exceptions. The p1 bug class becomes machine-checked. |
| F8 | **Three character-gating mechanisms** — `entrance_door_patch` callables, in-event gating, `ruin-*` room variants with lock dicts (ARCHIVE "Local Character Gating"). | One declaration in the atlas ("this entrance requires X locally"); the planner sees it as a lock, the realizer picks the patch technique per exit kind. |
| F9 | **Heuristic validity oracle rediscovered empirically** — Rules A–F in `check_network_invalidity` work but nobody can say which are invariants and which are prune heuristics. | Port the rules verbatim first (distribution parity), then document each with a soundness argument and a test that it never rejects a completable state on exhaustively-enumerable synthetic worlds. |
| F10 | **Dependency weight** — `networkx` (only DiGraph/relabel/plot) and `numpy` (only 3-vectors of counts) in the innermost loop; nx internals (`_pred` ordering) even became a determinism hazard in p5. | Plain dict adjacency and tuples. Removes both dependencies from the core and one whole class of iteration-order traps. |

Ideas that earned their place and **stay**:

- The **constructive random walk** itself — grow from a start room,
  connect frontier exits to random entrances, backtrack on infeasibility.
  This is what gives WC dungeons their characteristic long-chains-with-
  side-loops feel. It is the sampling algorithm, not an implementation
  detail.
- **Rejection sampling for small maps** (KT lanes, FC, dream maze): all
  legal layouts stay reachable.
- The **room/key/lock model** and `initially_locked_exits` semantics
  (an unlocked exit may be *used* by the mapper but not *targeted*).
- Ruination's **hub / upstream / downstream branch topology**, the
  reserve-area rescue pool, and the 6-step finalize with its parity
  reasoning — complex because the problem is.
- The **KT joint-state verifier** (three parties over a shared monotonic
  keychain) — it is exact; keep it as the acceptance gate.
- The **verifier-first definition of legality** (review 9.7): a map is
  legal because it passes the validators, not because the generator is
  trusted.
- The **deterministic walk budget** (p7) and the `-dv` logging levels.
- The realization approach of **copying the partner's vanilla exit
  record** onto a randomized door, and the runtime-patched event-tile
  connection data — the ROM-facing layer is sound (review §7).

## 3. Architecture

```
doors/
  atlas/          step 1  (static, immutable, ROM-free)
  model.py        shared   world-graph state + journal
  plan/           step 2  (pure, RNG-consuming, ROM-free)
  validate/       step 3  (pure, ROM-free)
  realize/        step 4  (ROM writes; thin, mostly ported code)
  report.py       step 5  (spoiler log, map image, routes)
tools/
  compile_atlas.py         build-time atlas generation + consistency check
```

Data flow per build:

```
args ──► ModeSpec ──► Planner(atlas, spec, rng) ──► DoorPlan
                                                      │
                              Validators(plan) ───────┤  (raise = re-roll)
                                                      ▼
        Data phase:   realize.exits / realize.transitions / maps hooks
        Events phase: realize.gating / event/*.py ruination_mod()s /
                      reward binding / clue scripts
        report:       spoiler log section, map image, debug routes
```

`wc.py` keeps its Memory → Data → Events → write skeleton. Data
constructs the plan (planning consumes RNG in one contiguous, documented
window) and owns it; Events receives it like it receives `maps` and
`dialogs` today.

### 3.1 The atlas (step 1)

Compiled by `tools/compile_atlas.py` from two sources:

- **Mechanical truth** from `exits_raw.json` (and the events/NPC JSONs
  for event tiles): exit index, map, coordinates, destination — from
  which door partnerships are *derived* (destination coordinates name the
  partner exit), not hand-typed.
- **Semantic curation**, migrated from today's tables and kept as
  reviewable Python data: room membership (which exits form a room),
  one-way designations (trap ↔ pit landing), keys/locks/gates
  (including character gates — F8), shared exits and their split rules,
  event-tile realization metadata (today's `event_exit_info`), pool
  definitions (today's `ROOM_SETS`), forced connections, descriptions.

The compiler cross-checks curation against mechanical truth (partner
symmetry, coordinates inside the named map, every curated exit exists,
every room's exits mutually consistent) and fails the build with a
specific message otherwise. Output is a plain importable module (no ROM
needed — fixes review 3.7); the checked-in generated file keeps diffs
reviewable.

Atlas objects (sketch, final style to match WC's plain-class idiom):

```python
Exit(id, kind, room_id, world, gate=None, desc="")   # kind: DOOR | TRAP | PIT | EVENT_DOOR | SYNTHETIC
Room(id, exits=(), keys=(), locks={})                 # locks: {(key,...): (member ids)}
Pool(name, room_ids, start_rule, protections, forced, post_steps)
```

### 3.2 The model (shared by all planners)

`doors/model.py` — the world graph under construction:

- Nodes are **room classes**: a rollback-capable union-find over room
  handles. Two-way connections union their endpoints' classes when a
  cycle forms (today's `compress_loop`, without string IDs — F2).
- Edges are one-way reachability between classes (traps, and the
  transient door edges before their cycle is compressed).
- Exactly **three mutating operations**, each appending to an undo
  journal: `connect_door(a, b)`, `connect_oneway(t, p)`,
  `apply_key(key)` (which may unlock elements and register
  `initially_locked_exits`). `checkpoint()` / `rollback(mark)` bound an
  attempt. No other code mutates state — this is what makes F4's
  journal reliable where the old code needed deepcopy.
- Read-only queries: `downstream(node)`, `upstream(node)` (BFS, dedup —
  the p7 semantics), `shortest_cycle(node)`, `unmatched(kind, node_set)`,
  counts. All iteration is over insertion-ordered structures; **sets are
  for membership only** — the single determinism rule that replaces the
  five ad-hoc fixes of p3/p5.

### 3.3 Planners (step 2)

- **`plan/walk.py`** — the backtracking walk, ~400 lines: frontier =
  active class + downstream; shuffle exits; shuffle legal entrances
  (minus protected); `checkpoint → connect → prune-check → recurse →
  rollback` per attempt; attempt budget (`WalkBudgetExceeded`) with
  start-room re-rolls, exactly as p7 calibrated. Pruning rules live in
  `plan/prune.py` as named, individually-documented predicates (ported
  verbatim from Rules A–F first — F9).
- **`plan/modes.py`** — `ModeSpec` table for every `-dr*`/shuffle flag
  (F6). Map shuffle is expressible either as a star-pool walk (as today)
  or as direct constrained matching; start with the walk for
  distribution parity, note the simplification for later.
- **`plan/ruination/`** — the big one, decomposed by concern:
  - `orchestrator.py` — branch lifecycle, growth loop, area
    distribution, stuck/rescue (reserve pool), retry loop (pure —
    re-roll requires no rollback, F5).
  - `topology.py` — hub/upstream/downstream classification and the v2
    target validators (the never-lose-the-last-exit / never-strand-pits
    rules).
  - `finalize.py` — the 6-step closing with its parity/terminus
    assertions.
  - `rewards.py` — abstract check-site → reward-kind assignment,
    character keys, `LockedRewards` banking. Deals only in static check
    IDs and kinds; Events binds objects later.
  - `kefka_tower.py`, `dream_maze.py` — the mini-planners with their
    exact verifiers, unchanged in approach.
- Every planner returns the same artifact:

```python
DoorPlan:
    door_pairs   [(exit, exit)]          # symmetric two-ways
    oneways      [(trap, pit)]
    gates        {exit: requirement}     # unified gating (F8)
    ruination    RuinPlan | None         # branches, reward kinds, areas-used,
                                         # hub party info, KT lanes, maze cells
    stats, seed_trace                    # for report + regression tests
```

with derived views (`destination_of(exit)`, `door_map` dict for
compatibility, `route(a, b)`).

### 3.4 Validation (step 3)

`validate/` runs on every plan in every mode — the acceptance gate:

- `structural.py` — reciprocity, bijective trap/pit matching, no
  dangling exits, shared-exit consistency (today's
  `postprocess_door_map` checks, promoted).
- `reachability.py` — every required room reachable from the start;
  every objective completable; **promote the `-debug_dest` shortest-route
  engine into an automatic completability proof** for the main
  progression of each mode. This is the strongest test we have and it
  already exists in embryo.
- `softlock.py` — key/character-gated softlock check (today's
  `_verify_no_character_gated_softlock`) and the KT joint-state
  verifier.

A plan that fails raises; the planner re-rolls (bounded), exactly like
today's ruination retry — but now uniformly for all modes and with no
state to restore.

### 3.5 Realization (step 4) and report (step 5)

Mostly a re-homing of code that already works:

- `realize/exits.py` — today's `Maps.connect_exits` + `patch_exits`
  partner-record copying, consuming `plan.door_pairs`.
- `realize/transitions.py` — today's `data/transitions.py` one-way
  writer.
- `realize/event_tiles.py` — today's `event_exit_info` runtime updates
  (both partners of used event connections — the Top-10 #4 gotcha gets
  encoded as a loop over `plan` pairs, not a curated list).
- `realize/gating.py` — emits the right patch per gated exit kind
  (entrance script, in-event branch), replacing the three mechanisms.
- Ruination *event* machinery stays in `event/` per WC convention:
  per-event `ruination_mod()` methods remain where they are; the shared
  subroutines (party interaction pointers, y-switch save/restore, ferry,
  school clues) live in `event/ruination_support.py` (or similar) and
  read the plan through its narrow API.
- `report.py` — spoiler-log section (format-compatible), map image,
  route dumps.

**Consumer API.** ~20 `event/*.py` files currently read
`maps.door_map`/`doors.map` directly (airship FC destination text,
serpent trench, ebot's rock, south figaro, lete river, phantom train,
etc.). The rewrite gives them `plan.destination_of(exit_id)` /
`plan.description_of(exit_id)` and — during migration — keeps a
`maps.door_map` property as an adapter so the event files can be
re-pointed one at a time. The airship 1.10 bug (interior door with no
world-map name) becomes impossible at the API level:
`plan.location_name(exit_id)` resolves through the atlas's room→area
naming rather than assuming the partner is a world-map door.

### 3.6 Cross-cutting policies

- **RNG**: keep WC's single seeded global `random` (style match), but
  all planner draws go through a thin `rng` façade that (a) only ever
  samples from explicitly ordered sequences and (b) logs draw counts to
  the seed trace, so distribution regressions are diagnosable. Planning
  is one contiguous RNG window in the Data phase.
- **Determinism**: the p7 rules, made law: attempt budgets not
  timeouts; no iteration over unordered collections at RNG or output
  boundaries; CI runs every sweep twice under different
  `PYTHONHASHSEED` and diffs outputs.
- **Errors**: one exception family (`PlanError` → `PruneReject`,
  `WalkBudgetExceeded`, `ValidationError(rule, evidence)`) so retry
  loops catch precisely what they mean to (the bare-`except` era ends).
- **Logging**: `vprint`/`-dv`/`-dv all` unchanged.

### 3.7 The event layer: mode-conditioned event code

The elephant the layers above don't cover: 45 `event/*.py` files carry
mode conditionals today — 144 `args.ruination_mode` sites, ~96
`args.door_randomize*`, 27 `args.map_shuffle*` — modifying event flow,
sometimes extensively. This is not an accident of door rando: vanilla WC
already conditions event code on flags (`character_gating`, boss/esper
settings, `-stray`, …). Game modes having different event-code
requirements is baked into WC's architecture.

**The organizing question is the classic expression problem**: the grid
is events × modes, and you must pick a major axis. WC picked
**event-major** (each event file owns all of its variants), and that is
the *right* choice — when Mt. Kolts misbehaves, everything about
Mt. Kolts is in `mt_kolts.py`, whatever combination of flags produced
the bug. A mode-major reorganization ("centralize all ruination event
patches") would just recreate today's 7,275-line `event/ruination.py`
problem in a new place and scatter each event's logic across N mode
modules. So the rewrite explicitly **keeps mode-specific event content
in the event files** (this is also CLAUDE.md's long-standing rule #5).

What should *not* stay ad-hoc are the mechanics around that content.
Four systematizations, all cheap:

1. **Derived capability predicates instead of flag or-chains.**
   28 files currently open with a hand-maintained variant of:

   ```python
   self.DOOR_RANDOMIZE = (args.door_randomize_mt_kolts
                     or args.door_randomize_all
                     or args.door_randomize_crossworld
                     or args.door_randomize_dungeon_crawl
                     or args.door_randomize_each
                     or args.ruination_mode)
   ```

   Every one of these lists is an opportunity to forget a flag (and
   adding a mode means editing 28 files). The plan already knows the
   answer: an event's maps/exits either were or were not rewired.
   Replace all of them with `plan.touches(<map ids / pool>)`, computed
   from the DoorPlan + atlas pool membership — zero per-event flag
   knowledge, automatically correct for any future mode.

   For behaviors rather than door-touching, the `ModeSpec` (§3.3)
   declares **capabilities** — `world_map_traversable`,
   `hub_recruitment`, `rebind_npc_pointers_on_entry`,
   `y_switch_control`, `airship_available`, … — and event code tests
   `caps.X` instead of naming the mode. Today's compound conditions
   become legible: `if args.character_gating and not
   args.ruination_mode` is really "character gating, but not when
   recruitment happens at the hub" — write that. The raw mode test
   remains available for genuinely mode-unique content (Narshe hub
   party formation *is* ruination); capabilities are a vocabulary, not
   a straitjacket. New modes then get most event behavior for free by
   composing existing capabilities.

2. **Uniform lifecycle hooks, dispatched by the framework.** The
   half-adopted convention (17 files define `ruination_mod()`, 13
   define `door_rando_mod()`/`dungeon_crawl_mod()`, each called — or
   forgotten — by that file's own `mod()`) becomes enforced: the
   Events loop invokes, in documented order, `mod()` (vanilla +
   generic), then `door_rando_mod()` when `plan.touches(event)`, then
   the mode hook (`dungeon_crawl_mod()` / `ruination_mod()`) when the
   mode is active and the method exists. Inline `if` blocks inside
   `mod()` remain legal only where variant code is genuinely
   interleaved mid-sequence; everything else migrates into hooks.
   `init_event_bits` stays a separate documented pass (its shared
   buffer-size contract stated once, not per event), and ordering
   guarantees make the FinishCheck-before-transition rule enforceable
   in one place.

3. **Shared machinery with a rule of three.** The good pattern that
   emerged late and ad hoc — `SET_PARTY_INTERACTION_POINTERS`,
   `DISABLE_Y_PARTY_SWITCH`/`RESTORE_Y_PARTY_SWITCH`, the
   `event/free_heals.py` cross-event sweeper — becomes policy:
   `event/door_rando_support.py` and `event/ruination_support.py` own
   shared subroutines and sweepers; the third event needing a pattern
   triggers extraction. Likewise the repeated plan-query idioms (e.g.
   Mt. Kolts' airship-teleport re-pointing via
   `get_connection_location`) become helpers on the plan API
   (`plan.teleport_target(exit_id)`), killing the copy-pasted lookup
   chains and their commented-out remains.

4. **A generated manifest, not a hand-maintained one.** "What does
   `-drdc` change?" is currently answerable only by grep. Introspecting
   the hook methods and capability tests yields a mode × event manifest
   table emitted by a tool (CI artifact / doc appendix). Tooling, not
   architecture — it never goes stale because it is derived.

Safety net for all event-layer refactoring: **event-script goldens** —
decompile the generated event code for touched events over a pinned
seed set and diff across changes (extends test #6 in §5). Moving an
inline block into a hook must produce a byte-identical script; the diff
proves it.

Notably, items 1, 2 and 4 do not depend on the rewrite at all — the
capability layer is args post-processing plus one helper, and the hook
dispatch is a small change to the Events loop. They are §8 fallback
candidates that would pay for themselves in the current codebase.

## 4. Package layout (proposed)

```
doors/
  __init__.py            # plan(args) entry point; owns mode dispatch
  model.py               # ~700  union-find world graph + journal + queries
  atlas/
    __init__.py          # loads compiled atlas, exposes Exit/Room/Pool
    compiled.py          # generated by tools/compile_atlas.py (checked in)
    curation.py          # ~1500 hand-maintained semantics (migrated tables)
  plan/
    walk.py              # ~400  backtracking walk + budget
    prune.py             # ~300  Rules A–F as named predicates + docs
    modes.py             # ~300  ModeSpec table for -dr*/-maps/-mapx
    ruination/
      orchestrator.py    # ~600
      topology.py        # ~600
      finalize.py        # ~600
      rewards.py         # ~350
      kefka_tower.py     # ~450
      dream_maze.py      # ~200
  validate/
    structural.py        # ~200
    reachability.py      # ~300  (absorbs the -debug_dest router)
    softlock.py          # ~250
  realize/
    exits.py             # ported from maps.connect_exits/patch_exits
    transitions.py       # ported
    event_tiles.py       # ported from event_exit_info write path
    gating.py            # ~250  unified character gating
  report.py              # ~250
tools/
  compile_atlas.py       # ~300  + consistency checker
tests/doors/             # ~1500 unit + property + sweep harnesses
```

Roughly 8–9k new/migrated lines replacing ~16.4k, with the largest
single file around 600 lines instead of 7,275 (`event/ruination.py`
today, 116 functions). Everything above `realize/` imports without a
ROM.

## 5. Testing strategy (the rewrite's safety net)

1. **Model property tests** — `connect*/apply_key` followed by
   `rollback` restores byte-equal state (compare full repr); randomized
   op sequences (hypothesis-style loops, no new dependency needed).
2. **Prune soundness** — on synthetic worlds small enough to enumerate
   every completion, assert no rule rejects a completable state; catalog
   any deliberately conservative rule.
3. **Validator-as-spec oracle** — during migration, run the *old*
   generator and feed its output through the *new* validators. Every
   rule the old maps satisfy is locked in before the new planner exists.
4. **Distribution parity** — old vs new over many seeds: exact
   per-pairing frequency (chi-square) on small pools (KT lanes, single
   `-dre` areas, map shuffle); aggregate stats (depth, dead-end count,
   loop count, branch sizes) on `-drdc`/`-ruin`. This is how "same
   outcomes, different bytes" is made checkable instead of vibes.
5. **Completability sweeps** — N seeds × every mode: build, validate,
   route-prove, twice under different hash seeds. This is the p7 sweep
   methodology, promoted into CI (`tests/doors/sweep.py`, callable
   locally with a vanilla ROM for full builds or ROM-free for plan-only).
6. **Realization goldens** — for a pinned seed set, diff the written
   exit tables/transition scripts between old and new realizers while
   both exist (they should be *identical* given the same plan — the
   realizer is a port, not a redesign).

## 6. Migration plan (strangler, every stage shippable)

The old and new implementations coexist behind a hidden dev flag
(`-doors2`); modes cut over one at a time once they pass parity; the old
module set is deleted at the end. On top of `ff6wc/dev`, the same stages
double as the porting sequence.

- **Stage A — atlas.** Write `compile_atlas.py` + curation migration +
  consistency checker. Prove it by *generating today's tables from it*
  (emit `exit_data`-shaped dicts and diff against the current, p1-fixed
  files). No behavior change lands. This stage alone would have caught
  every 1.4/1.5-class data bug ever introduced.
- **Stage B — model + walk + validators.** Implement `model.py`,
  `plan/walk.py`, `plan/prune.py`, `validate/*`. Bring up on the small
  single-area modes (`-dru`, `-drem`, …) and `-dre`: run old and new
  side-by-side, apply test #3 and #4. Cut over `-dre` and friends.
- **Stage C — big walks + shuffle.** `-drdc`, `-dra`, `-drx`, `-maps`,
  `-mapx` (crossworld links, WoB↔WoR mirroring, shuffle protections as
  ModeSpec data). Distribution comparison on the full DungeonCrawl pool.
  Cut over. At this point `data/walks.py`/`doors.py` are dead.
- **Stage D — ruination planner.** The largest stage: orchestrator,
  topology, finalize, rewards as §3.3; Events-side binding shrinks to
  "look up plan, bind Reward objects, call per-event `ruination_mod`s".
  The snapshot/rollback machinery in `events.ruination_mod` is deleted.
  Parity via test #4 aggregates + full sweeps; keep the old path callable
  until a few hundred-seed sweeps are clean.
- **Stage E — mini-planners, gating unification, event-layer cleanup.**
  KT lanes, dream maze, `realize/gating.py` replacing the three
  mechanisms (this touches the `ruin-*` room variants in curation —
  they become plain gate annotations). Event layer (§3.7): replace the
  28 `DOOR_RANDOMIZE` or-chains with `plan.touches()`, introduce
  capability predicates and framework-dispatched hooks, extract shared
  machinery into the support modules, re-point the ~20 event-file
  consumers at the plan API, and drop the `door_map` adapter — one
  event file at a time, each proven by script goldens.
- **Stage F — deletion + docs.** Remove the old modules and reset
  functions; rewrite `DOOR_RANDO_GUIDE.md` against the new layout; the
  code review retires to historical record. CI sweep harness becomes the
  permanent regression gate.

Each stage is a reviewable branch in the established `door-rando-*`
convention and leaves the tree in a releasable state.

## 7. Risks and mitigations

- **Distribution drift** (the subtle one): innocuous-looking changes —
  candidate ordering, prune strictness, key-application timing — change
  the map distribution, which players experience as "the rando feels
  different". Mitigation: port prune rules and candidate-collection
  semantics verbatim first; chi-square harness (test #4) before every
  cutover; improvements to rules land as separate, measured changes.
- **Hidden event-side coupling**: 20 event files read door structures
  directly, and some encode door IDs in scripts (serpent trench senders,
  ebot's rock, switchyard returns). Mitigation: the adapter property +
  one-file-at-a-time re-pointing in Stage E; the realization goldens
  (test #6) catch anything the adapter misses.
- **Ruination finalize edge cases**: finalize's six steps encode years
  of discovered failure modes (converter parity, terminus injection,
  orphan doors). Mitigation: port step-by-step with the ARCHIVE notes as
  spec; keep `StuckReason` telemetry; the retry loop tolerates a
  temporarily higher failure rate during bring-up without shipping bad
  maps (validators gate).
- **Curation migration errors**: re-keying room/lock tables invites
  typos. Mitigation: Stage A's generate-and-diff proves the atlas
  reproduces today's tables exactly before anything consumes it.
- **Scope creep**: the rewrite will surface tempting redesigns (better
  prune rules, constraint-guided KT partitioning — review 9.5). Rule:
  parity first, improvements as separate flagged changes after cutover.

## 8. If not the full rewrite: the 80/20 fallback

Should the full program be too much at once, the stages are severable and
independently worthwhile, in this order of value:

1. **Stage A alone** (atlas compiler + consistency check) kills the
   worst ongoing maintenance hazard (hand-edited partner data) with zero
   behavior risk.
2. **Validators + route-prover as a permanent CI sweep** (from §5) makes
   every future change to the *existing* code safe to attempt.
3. **F5 decoupling** (ruination planner goes pure; Events binds objects)
   deletes the snapshot/rollback machinery — the single most fragile
   contraption in the codebase — without touching the walk at all.
4. **Splitting `event/ruination.py`** along the §3.3 seams, mechanically,
   with no logic changes.
5. **Event-layer mechanics from §3.7** — capability predicates replacing
   the 28 `DOOR_RANDOMIZE` or-chains, framework-dispatched lifecycle
   hooks, and the generated mode × event manifest. None of these need
   the new planner; script goldens make each migration provable in the
   current codebase.

## 9. Rough effort map

| Stage | New/changed code | Dominant work |
|---|---|---|
| A | ~1,800 (mostly migrated data) | curation migration + differ |
| B | ~2,200 | model + walk + validators + parity harness |
| C | ~600 | mode specs + shuffle integration |
| D | ~2,800 | ruination decomposition + parity |
| E | ~1,200 | mini-planners + gating + consumer re-pointing |
| F | −16,000 / +docs | deletion, guide rewrite |

The realization layer is deliberately a port (it is the part that is
already sound and the part where mistakes brick ROMs); the planning and
data layers are where the redesign pays for itself: no ID arithmetic, no
compound-ID parsing, no global scratch state, no deepcopy, no reset
functions, no rollback snapshots, one planning site, one gating
mechanism, one validation gate, and a door-rando core that runs and
tests without a ROM.
