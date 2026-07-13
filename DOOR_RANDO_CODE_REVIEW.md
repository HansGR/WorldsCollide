# Door Randomization Code Review (Dungeon Crawl & Ruination Mode)

> **Status (2026-07): HISTORICAL RECORD.** The code this review covers was
> replaced by the `doors/` package and deleted in the Stage E2 cutover.
> Kept because the findings motivated the rewrite's flaw table (F1-F10).

Reviewed: `args/doors.py`, `args/ruin_preprocessor.py`, `data/doors.py`, `data/walks.py`,
`data/rooms.py`, `data/maps.py` (door-writing paths), `data/map_exit_extra.py`,
`data/event_exit_info.py`, `data/transitions.py` (skim), `event/ruination.py`,
`event/events.py` (ruination/DC integration), and the mode hooks in
`instruction/field/instructions.py`.

Scope: coding errors, fragility, data errors, inefficiency, dead code, and
misleading structure specific to the `-drdc` and `-ruin` code paths. Top-level
issues already tracked in the `code-review-p1`..`p5` branches are excluded.

Companion document: `DOOR_RANDO_GUIDE.md` (programmer's guide to these modes).

Severity legend:
- **[BUG]** — incorrect behavior reachable today (or a crash on a reachable path)
- **[LATENT]** — incorrect code that current data/config happens not to reach
- **[FRAGILE]** — works today, but breaks under plausible change (retries, new data, tests)
- **[PERF]** — significant algorithmic inefficiency
- **[DEAD]** — dead/duplicated code
- **[STYLE]** — misleading names/comments/structure worth fixing for maintainability

---

## 1. Confirmed bugs

### 1.1 [BUG] `-drmk` flag string emitted from the wrong variable
`args/doors.py:237-238` — the second of two consecutive checks tests
`args.door_randomize_cyans_dream` again instead of `args.door_randomize_mt_kolts`:

```python
if args.door_randomize_cyans_dream:
    flags += " -drcd"
if args.door_randomize_cyans_dream:   # should be door_randomize_mt_kolts
    flags += " -drmk"
```

Failure: a seed generated with `-drcd` (without `-drmk`) advertises `-drcd -drmk`
in its flag string; a seed generated with `-drmk` alone advertises neither. Since
flag strings are used for seed sharing/reproduction, reproduced seeds diverge.

### 1.2 [BUG] Broken timeout/exception handling in `Doors.mod()`
`data/doors.py:692-712` — three problems in a row:

```python
try:
    fully_connected = connect_with_timeout(walks, self.timeout)
    if fully_connected is None:
        print('Door connection timed out')
        #Ncount += 1
except Exception as e:
    vprint(f"Network connection failed: {e}")

fcm_doors = [m for m in fully_connected.map[0]]
```

- On timeout, `connect_with_timeout` returns `None`; the code prints a message
  and then dereferences `fully_connected.map[0]` → `AttributeError`.
- If `connect_with_timeout` raises, the `except` swallows it and
  `fully_connected` is unbound → `NameError` on the next line.
- The commented-out `Ncount += 1` shows a retry loop was intended but never
  implemented. There is **no retry** on timeout for `-drdc`/`-dra`/`-dre`; an
  unlucky seed dies with an unrelated-looking traceback instead of re-rolling.

Fix: make timeout/exception paths retry (bounded), and raise a diagnosable
error when retries are exhausted.

### 1.3 [BUG] List mutated while iterating when patching logical links
`data/doors.py:721-731`:

```python
for m in map[0]:
    ...
    if remove_flag:
        map[0].remove(m)
```

Removing the current element during iteration skips the following element. If
two connections involving logical-link doors (`30537/30618`, `30044/31047`)
happen to be adjacent in `map[0]`, the second is never recorded in `llink`,
so the link is patched with a stale/missing pair — a silently corrupted door
map. Reachable in `-dre`/`-dra` with map shuffle (the modes that use the
`_mapsafe` room variants). Iterate over a copy (`for m in list(map[0])`), or
build a new list.

### 1.4 [BUG] Vanilla-partner data errors in `exit_data`
`data/map_exit_extra.py` — the partner field (`exit_data[id][0]`) is consumed
by `data/transitions.py` and `data/maps.py:1008` (`exitB_pairID`) when writing
randomized doors, so wrong partners produce wrong return connections whenever
these doors participate in randomization. Verified against
`claude_reference/exits_raw.json` coordinates:

| Entry | Currently | Should be (coord-verified) |
|---|---|---|
| `exit_data[215]` (Figaro Castle Main Hallway South) | 198 | **199** |
| `exit_data[307]` (South Figaro Relics Inside) | 337 | **301** |
| `exit_data[337]` (South Figaro Item Inside) | 307 | **305** |
| `exit_data[331]` (Rich Man's House B1 to Clock Room) | 334 | **335** |
| `exit_data[546]` (Kohlingen Rachel's House Outside WoB) | 567 | **566** |
| `exit_data[552]` (Kohlingen Rachel's House Outside WoR) | 567 | **566** |
| `exit_data[506]` (Mobliz Inn Outside) | 517 | **516** |
| `exit_data[752]` (Maranda Armor Inside) | 741 | 742 (verify) |
| `exit_data[884]` (KT Falldown Room Entry Right Door) | 884 (self!) | **None** (unreachable in game, unused in any mode) |

Also suspicious (need domain confirmation): `exit_data[509]`/`exit_data[513]`
(Mobliz Mail House Outside → 519), `exit_data[519]` (→ 521), `exit_data[647]`
(Opera House Catwalk Stairwell South → 62, a world-map tile).
*(Resolved: HansGR reviewed and fixed 509/519/647 directly, 2026-07.)*

Most of these doors are in town interiors that current room sets don't
randomize, so the errors are latent — but they are landmines for any future
room-set expansion (Ruination is actively expanding into towns).

### 1.5 [BUG] Duplicate key `1203` in `exit_data`
`data/map_exit_extra.py:607` and `:1394` both define `1203:` ("Nikeah Chocobo
Stable Inside" WoB and WoR). Python keeps the second silently. Both map to
`[1202, ...]` so today only the description is lost, but the duplicate hides
the fact that the WoR interior entry probably wanted its own id (cf. the
`4xxx/5xxx` logical-WoR convention used everywhere else in that block).

### 1.6 [BUG→LATENT] `DEFAULT_NAME[None]` crash for ungated character checks
`event/ruination.py:5671`:

```python
characters.set_character_path(slot.id, slot.event.character_gate())
unlocker_name = characters.DEFAULT_NAME[slot.event.character_gate()]  # crashes if gate is None
if self.verbose and slot.event.character_gate() is not None:
```

`Event.character_gate()` defaults to `None` (`event/event.py:39`), and
`DEFAULT_NAME` is a list, so indexing with `None` raises `TypeError`. The retry
loop in `events.ruination_mod` only catches `RuinationMappingError`, so this
would abort the whole build. Currently unreachable only because the sole
ungated CHARACTER-capable check — `ROOM_REWARD[22]` ("Narshe Battle") — is in
no `RUIN_ROOM_SETS` entry and is never placed (see 2.1). Move the lookup
inside the `is not None` branch.

### 1.7 [BUG→LATENT] `finalize_map` step 1 crashes uninformatively when no pit-donor room exists
`event/ruination.py:2472-2531` — `winner` is initialized to `''`; if neither
the network scan nor the reserve-area fallback finds a room with more pits
than traps, `self.rooms.get_room('')` returns `None` and
`room.pits` raises `AttributeError` — losing the carefully-built diagnostic
machinery used everywhere else in this function. Raise a `RuntimeError` with
`visualize_branch_topology()` output like the sibling steps do.

### 1.8 [BUG] Stale loop variable in dead method `Maps.doorRandoOverride`
`data/maps.py:700-712` — the second loop (`for d in room_data[r][1]`) sits
*outside* the `for r in room_data.keys()` loop, so it only processes the last
room's traps. The method is never called (dead), so the practical fix is
deletion — but if it is ever resurrected, this indentation bug comes with it.

### 1.9 [BUG-risk] Un-bracketed substring matching on compound room IDs
`event/ruination.py:894-900` (`get_downstream_levels`) and `:928-944`
(`get_local_upstream`) match compound (merged) rooms with raw substring tests:

```python
trap_matches = ... or (str(prev_room) in str(trap_room.id) ...)
```

Numeric IDs are prefixes/suffixes of each other (`78` in `278`, `501` in
`1501`) — precisely the false-positive class that `compute_actual_areas_used`
(`ruination.py:5566-5570`) and `_classify_branch_warp_rooms` (`:2273-2275`)
explicitly guard against with the `_<id>_` bracketing convention. These two
methods feed topology levels and connection attribution during mapping, so a
false match mislabels a connection between merged rooms. Apply the same
bracketed convention here.

### 1.10 [BUG] Airship FC-destination text crash under `-dre -maps`
`event/airship.py:110` — the Blackjack console text looks up
`door_short_text[exit_data[door_map[1556]][0]]`, assuming the shuffled
Floating Continent slot leads to a location entrance whose `exit_data`
partner is a world-map door. When map shuffle lands the FC slot on Esper
Mountain with `-dre`, the logical link `[30044, 31047]` composes the slot
directly with a random re-randomized *interior* door, whose partner is
another interior door with no `door_short_text` entry → `KeyError`
(~1-3% of `-dre -maps` seeds; confirmed pre-existing by reproducing on the
pre-p7 baseline). Found by the p7 validation sweep.

**STATUS: fixed 2026-07 on branch `door-rando-review-p7`** — the lookup
falls back to "Esper Mountain", the only area protected this way
(`map_shuffle_protected_doors`).

---

## 2. Data errors and inconsistencies

### 2.1 [LATENT] Dead check: `ROOM_REWARD[22]` ("Narshe Battle")
Room 22 (Snow Battlefield WoB) is in no `RUIN_ROOM_SETS` entry, so the check
can never be placed in ruination. Combined with 1.6, if it were ever placed
and rolled a character, the build would crash. Either add the room to an area
set (and fix 1.6 first) or delete the entry with a comment.

### 2.2 [FRAGILE] `exit_room`/`exit_world` are last-writer-wins
`data/rooms.py:1336-1363` — many doors appear in several `room_data` entries
(base room, `'37a'`-style variants, `ruin-*` clones, `_mapsafe` variants,
`ms-*`/`dc-*` connectors). The lookup dictionaries silently keep whichever
room was defined last in the file, so `exit_room[1150]` is `'ruin-narshepeak'`
rather than room 41. Consumers must not assume they get the "real" room.
Document the invariant or key the lookup per-mode.

### 2.3 [STYLE] Inconsistent element classification between `Room.element_type` and `Room.locked`
`data/walks.py:1473-1489` vs `:1519-1545`:
- `locked('doors')` uses `d < 2000` — misses logical WoR doors (4000–5999) and
  wrongly *includes* `doors_as_traps` members;
- `locked('pits')` uses `d >= 3000` — would classify a locked 4000–5999 door
  as a pit;
- `element_type` handles both ranges plus `doors_as_traps` correctly.

No lock currently contains a 4xxx id, but Ruination's lock dictionaries grow
regularly (`ruin-zozo` already locks door `4608`!). `locked('doors')` will not
report 4608 as a locked door, while `element_type(4608)` calls it a door.
Centralize classification in one function and have both call it.
**Deliberately deferred (2026-07):** fixing this changes `alldoors`/
`full_count` for rooms with locked 4xxx doors, which feeds mapping decisions
— i.e., it changes generated maps. Schedule it together with the first
relaxed-compatibility change (§9).

### 2.4 [STYLE] `Room.element_type` returns `False` as its error sentinel
`data/walks.py:1545` — `return False` for unknown IDs, but callers compare
`element_type(x) == 0`, and `False == 0` is `True` in Python. An out-of-range
ID (e.g. ≥ 8000) is silently treated as a two-way door instead of failing.
Raise `InvalidElementError` (the class already exists) or return `None`.

---

## 3. Fragility: shared mutable module state

This is the single largest source of fragility in both modes. The mapping code
treats module-level data tables as scratch space, which works only because the
process builds exactly one seed and exits. Any second consumer in the same
process — the ruination retry loop, `-rkt`'s 400 partition attempts, a unit
test, a future "reroll seed" server — observes corrupted tables.

### 3.1 [FRAGILE] `Room` aliases `room_data` lock lists
`data/walks.py:1418-1431` — `add_locks` stores the caller's list object
(`self.elements['locks'][key_tuple] = locked_items`). For rooms constructed
from `room_data`, that list *is* the module-level list. Two live mutation
paths then write through the alias:
- `Room.remove()` (`:1448-1458`) does `locked_items.remove(element_id)`;
- `attach_dead_ends` (`data/walks.py:586`) does `Ra.locks[ka].append(kd)` —
  permanently moving a dead-end's key into `room_data`'s lock list.

The dead-end-with-key + locked-door combination exists in current data (room
212, Phantom Train Locomotive, carries `'pt2'`), so `-drdc` runs can mutate
`room_data` in ways that would poison a rebuild in the same process.
Fix: `add_locks` should copy (`list(locked_items)`).

### 3.2 [FRAGILE] `Doors.__init__` mutates shared tables destructively
`data/doors.py:167` binds `self.forcing = forced_connections` (the module
dict) and later `self.forcing.pop(1079)` (ruination) mutates it globally;
`:197-218` removes entries from `shared_exits` lists in place. Instantiating
`Doors` twice raises `ValueError` (removing an already-removed element) or
silently double-applies. Copy on init.

### 3.3 [FRAGILE] Runtime writes into `exit_data` and `room_data`
- `data/maps.py:649-656` rewrites `exit_data[d][0] = safe_id` and invents new
  entries for the DC/ruination destination overrides.
- `event/ruination.py:3926-3930` adds `ruin_hub_0/1/2` to `room_data`;
  `:4072` rewrites `room_data['ruin-stooge-maze'][2]`.
- `_configure_dream_maze` (`:3954-3993`) mutates `CHARACTER_AREAS`,
  `RUIN_ROOM_SETS`, `WARP_ROOMS`, `forced_same_branch`, and moves entries in
  `ROOM_REWARD`.
- `ruination_map.__init__` (`:3849-3852`) does `CHARACTER_LOCKED_REWARDS.clear()`
  under `-open`.
- `generate_map_with_characters` (`:4990-4992`) pops `ruination_dont_force`
  entries from `forced_connections`.

Individually each is guarded well enough to survive the *current* retry loop
(the `WARP_ROOMS.discard` comment shows the author has been bitten already),
but the guards are ad-hoc and scattered. Recommend a single
`reset_ruination_tables()` (or constructing per-instance copies) so retry
safety is a property of the design rather than of each call site's memory.

### 3.4 [FRAGILE] The retry loop must manually roll back external state
`event/events.py:290-332` snapshots character/esper pools and reward slots and
restores them on retry. This list of "external mutable state the generator
consumes" must be kept in sync by hand with everything in 3.3; forgetting one
(e.g. a future `possible_types` mutation like the Ebot's Rock pin at
`ruination.py:3277-3278` — which *is* currently reset only because the whole
slot tuple is restored) reintroduces cross-attempt contamination. Same
recommendation as 3.3.

### 3.5 [FRAGILE] Identity comparison of int IDs
`data/walks.py:909` (`R1.id is not R_active.id`) and `:934`
(`d is not d1`) use `is` on values that are ints/strings. This works today
only because the same int objects flow from the room sets into the candidate
lists. Any refactor that reconstructs an ID by arithmetic (the codebase is
full of `d + 4000`, `t + 1000`) silently breaks the comparison. Use `!=`.

### 3.6 [FRAGILE] `connect_with_timeout` leaves the worker thread alive
`data/doors.py:1831-1846` — on timeout the code sets `should_stop`, joins for
1s, and returns. `connect_network` only polls `should_stop` at frame entry
before an expensive `deepcopy`+validity check, so the thread routinely
outlives the join; it is non-daemon, so a "timed out" run may hang at
interpreter exit until the walk finishes anyway. Mark the thread `daemon=True`
and poll `should_stop` inside the entrance loop as well.

**STATUS: resolved 2026-07 on branch `door-rando-review-p7`** — the daemon
mitigation (p2) was superseded by 9.3: the threading machinery
(`NetworkConnector`, `connect_with_timeout`, `should_stop`) is deleted
entirely in favor of the deterministic walk budget.

### 3.7 [FRAGILE] `data/event_exit_info.py` mixes data with ROM-dependent code
Line 311 imports `instruction.field`, which allocates ROM space at import
time. Consequently *no* door-rando data module can be imported without a
loaded ROM (this bit this review's tooling immediately). Move the
`entrance_door_patch`/`exit_door_patch` builders into a separate module (or
defer the import into the functions) so the data tables are importable and
testable standalone.

### 3.8 [FRAGILE] `-rkt` reaches into `log.verbose` privates
`event/ruination.py:4323-4325` saves/clears `_verbose_mod._to_stdout/_to_file`
to silence the walk. Add a public `verbose.suppress()` context manager instead
of poking module privates.

### 3.9 [BUG] Ruination seeds are not reproducible across processes
Found while validating the p2 changes: building the same seed with the same
flags twice produces byte-identical ROMs for `-drdc`, but **different ROMs for
`-ruin`** — unless `PYTHONHASHSEED` is pinned, in which case `-ruin` is also
byte-identical. The cause is Python's per-process string-hash randomization:
ruination iterates unordered sets of strings in RNG-consuming paths (e.g.
`initial_areas`/`new_areas` sets feeding `distribute_areas`, `self.keychain`,
`WARP_ROOMS`/`TOWN_ROOMS` membership-driven choices, `net.nodes` insertion
orders derived from set-built room lists), so the sequence of `random.*` draws
differs between processes even with an identical seed. This breaks seed
sharing/racing for `-ruin`. Fix by sorting (with a `str()` key) anywhere a set
is iterated before a random choice, or by converting the relevant sets to
insertion-ordered structures. Not fixed in p2 (behavioral change requiring a
careful audit of every set-iteration site in the generation path).
**STATUS: fixed 2026-07 on branch `door-rando-review-p3`.** Canonicalized
(sorted, `key=str`) the RNG-facing set iterations: `distribute_areas`'s area
list and its area→room / room→branch expansion loops (which also set
`accessible_shops` order and `net.nodes` insertion order — the order every
downstream candidate list inherits), the keychain application loops,
`extend_branch_path`'s `deepest_rooms`, the `-rkt` lane `Network`
construction, and `_branch_exit_owner_map` (softlock-verifier edge
determinism). Set iterations that only feed order-free sums/booleans/
membership tests were left alone. Note int-only sets (door/trap/pit IDs)
were never affected — CPython only randomizes *string* hashing. Verified:
same-seed `-ruin` builds are now byte-identical across PYTHONHASHSEED values
(1, 2, and unpinned) for 5 seeds; `-drdc` output is byte-identical to
`door-rando-review-p2` (untouched by this change).

### 3.10 [OBSERVATION] `-sl` changes the generated game — vanilla WC behavior
Investigated 2026-07 (initially misreported as mid-build RNG consumption;
that was wrong). Two distinct mechanisms, **neither door-rando-specific**:

1. **`-sl` seeds a different game — vanilla WC since the initial public
   commit.** `args/settings.py:flags()` appends `" -sl"` to the settings
   flag string; `args/arguments.py` builds `seed_rng_flags` from every
   group's flags (excluding only `graphics`); `seed.py` then calls
   `random.seed(seed + flags)`. Same `-s` seed ± `-sl` therefore seeds the
   RNG with a different string and produces an entirely different game
   (verified: vanilla-flags build `-s dc001 -open` vs `-open -sl` differ in
   ~103k bytes / 148 regions). No spoiler-log code consumes RNG at all —
   probing `random.getstate()` at the Memory/Data/Events phase boundaries
   with `spoiler_log` toggled shows identical streams throughout.
2. **`-debug`/`-dv` do NOT change the seed** — they set `spoiler_log = True`
   *after* the flag string is computed (`arguments.py:73-78`). Their only
   ROM effect from the spoiler-log path is a single byte: the
   "Spoiler Log: T/F" value character in the in-game Flags menu
   (byte 0x303216 on the vanilla-flags build, 0x85 'F' vs 0x93 'T').
   (`-debug` additionally makes maps warpable by design.)

Decision needed (team-level, since it is core WC): if racers/players should
be able to generate a spoiler-logged copy of the *same* game, `-sl` must be
excluded from `seed_rng_flags` the way graphics flags are (or dropped from
`flags()` emission). Note the compatibility cost: any change breaks
reproduction of previously shared seed+flag strings that included `-sl`.
The late-set `-debug`/`-dv` path demonstrates the seed-neutral behavior
already works correctly.

### 3.11 [FRAGILE] `ruin_preprocessor` only sees flags *after* `-ruin`
`args/ruin_preprocessor.py:203-221` and `:192-201` scan
`argv[ruin_index + 1:]`, so a user flag placed *before* `-ruin`
(`wc.py -i rom.smc -lsa 3 -ruin`) is not seen by the mutual-exclusion
suppression and collides with the injected default (`-lsced 2`) as an argparse
error. Scan the whole argv (excluding the injected region). Also:
`FLAGS_WITH_ARGS` is a hand-maintained duplicate of argparse metadata (drift
hazard when a default flag's arity changes), and the docstring at `:228` says
`'minimum'` where the code checks `'custom'`.

---

## 4. Algorithmic inefficiency

### 4.1 [PERF] `connect_network` deep-copies the entire network per attempted connection
`data/walks.py:834-979` — every recursion level starts with
`net_state = deepcopy(self)` and every attempted entrance does
`net_backup = deepcopy(net_state)`. For `-drdc` (304 rooms, 531 doors,
~350 connections) that is ~350 recursion levels × (1 + attempts) full-graph
deep copies — the dominant cost and the reason the 10-second timeout exists at
all. Alternatives, in increasing order of effort:
- undo-log (record the ~4 mutations `connect()` makes and reverse them on
  backtrack) instead of copy-on-try;
- copy only the mutated rooms (persistent-map style);
- keep deepcopy but skip the second copy (`net_backup`) by restarting the
  frame from `net_state`'s own parent copy.

Also note recursion depth ≈ number of connections (~350 for DC) — within
Python's default 1000 limit but only ~3× headroom; a future larger room set
(or deepcopy's own recursion on a deep structure) hits `RecursionError`
inside the bare `except:` (see 4.4).

### 4.2 [PERF] Path enumeration is exponential in principle, capped in practice
`get_upstream_paths`/`get_downstream_paths` (`data/walks.py:324-400`) enumerate
all visited-node-disjoint paths recursively with no cap, and are called from
`get_loop` (every `connect`), `connect_network` (trail search), and
`get_downstream_levels`. The `_nodes` variants were rewritten iteratively with
a 200k iteration cap after real incidents (the cap converts a hang into a hard
failure), but the `_paths` variants were not. On the DC-sized graphs the
branching is low enough to pass; on dense compound graphs this is the next
hang. Same treatment (iterative + cap, or a proper SCC/condensation) is
warranted.
**STATUS: implemented 2026-07 on branch `door-rando-review-p6`** — both
`_paths` enumerators now carry a shared 200k step budget (threaded through
the recursion, so output order is untouched) and convert both budget
exhaustion and deep `RecursionError` into `NetworkRecursionError` with the
standard diagnostics, matching the `_nodes` variants. Verified: budget fires
on a pathological dense-DAG test, healthy outputs unchanged, and the full
8-seed matrix is byte-identical to `door-rando-review-p5`.

### 4.3 [PERF] `check_network_invalidity` recomputes global reachability per node, per connection
`data/walks.py:645-832` runs `get_upstream_nodes` + `get_downstream_nodes` for
*every* node on *every* `connect_network` frame (and its duplicate-emission
semantics make those lists larger than the node count). Combined with 4.1 this
makes each connection O(N²)-ish. Caching per-frame reachability (the graph
only changes by one edge between frames) would collapse most of this.

**STATUS (4.1 + 4.3): implemented 2026-07 on branch `door-rando-review-p5`,
under a byte-identical constraint.** Profiling showed generic `copy.deepcopy`
was ~80% of the `-drdc` walk. `Network.__deepcopy__` now uses hand-rolled,
order-preserving fast copies (`_fast_copy_digraph`, `Rooms.fast_copy`,
`Room.fast_copy`), with generic deepcopy retained for subclass attributes.
Two order-preservation subtleties are load-bearing and documented in the
code: (a) a DiGraph's `_pred` dicts must be copied directly — rebuilding via
`add_edges_from` reorders `predecessors()` iteration; (b) sets must be copied
as `set(list(s))`, not `set(s)` — the merge path presizes the hash table
differently and can change iteration order versus deepcopy's element-by-
element rebuild (this was caught because `-drdc` output diverged and was then
verified over 70 randomized trials). For 4.3, `check_network_invalidity` now
computes `count_unprotected` once per room per frame instead of per
(room, neighbor) pair, and the `_nodes` traversals use set-based visited
membership and O(1) `has_edge` two-way tests (result order untouched; the
full reachability-caching idea was deliberately NOT done — the duplicate-
emission semantics feed shuffled candidate lists, so replacing them risks
changing outputs). Result: walk time ~3× faster (3.3s → 1.1s on the profiled
`-drdc` workload; full 3-seed `-drdc` wall time 11.2s → 6.9s — the remainder
is ROM/data/event work). Verified byte-identical vs pre-change references on
8 seeds across `-drdc` ×3, `-dra`, `-mapx`, `-ruin` ×3. Caveat: seeds whose
walks previously hit the 10-second timeout may now complete within it and
produce a different (valid) map — but those outcomes were already
hardware-dependent by construction.

### 4.4 [FRAGILE] Bare `except:` hides real failures during the walk
`data/walks.py:967` — the backtracking `try/except` catches *everything*,
including `NetworkRecursionError`, `RecursionError`, `KeyboardInterrupt`, and
genuine bugs (e.g. an `AttributeError` from a data error), converting them
into "this connection failed, try the next entrance" — which multiplies the
cost of real failures by the full backtrack tree and hides their origin. Catch
a specific exception type raised for "invalid network state".
**STATUS: partially addressed on `door-rando-review-p5`** — narrowed to
`except Exception` so Ctrl-C/SystemExit abort the walk. Catching a dedicated
invalid-state exception type remains open (it would change which data-error
bugs surface vs. backtrack, so it needs its own careful pass).

### 4.5 [PERF] Reserve-area scans re-walk `room_data` lists repeatedly
`finalize_map` re-derives `[x for x in data[i] if x not in self.protected]`
for every reserve room on every rescue attempt (8 similar loops; see 5.3).
Small n, so low priority — fold into the shared helper when deduplicating.

---

## 5. Dead code and duplication

### 5.1 [DEAD] ~950 lines of commented-out legacy mapper in `data/doors.py`
Lines ~821-1769: `mod_original`, `draft_areas`, `map_doors`, `map_oneways` —
the pre-`Network` algorithm, fully superseded by `data/walks.py`. Also the
commented `zones`/`zone_counts` plumbing in `__init__` that only they used.
Git history preserves it; delete.

### 5.2 [DEAD] Superseded v1 target-finders and old extension in `event/ruination.py`
- `get_valid_pit_targets` / `get_valid_door_targets` (lines ~1190-1507,
  ~320 lines): only `_v2` variants are called (`extend_branch_path:3520-3526`).
- `extend_branch_path_old` (lines ~3648-3789, ~140 lines): never called.

Keeping both versions makes ARCHIVE.md references ambiguous (it documents
rules against both). Delete v1 and rename `_v2` → unsuffixed.

### 5.3 [DEAD/STYLE] The "pull a room from reserve matching a predicate" pattern is duplicated ~8×
`finalize_map` and `_inject_door_if_needed_for_terminus` each contain multiple
copies of:

```python
for area_name, area_rooms in reserve_areas:
    for rid in area_rooms:
        if rid in self.net.nodes: continue
        if rid in room_data:
            data = room_data[rid]
            r_doors = [d for d in data[0] if d not in self.protected] ...
            if <predicate>:
                self.add_room(rid); area_rooms.remove(rid); ...
```

(sites: ~2169, ~2506, ~2653, ~2691, ~2760, ~2807, ~2846, ~2955, ~3013). One
helper `self._pull_from_reserve(reserve_areas, predicate)` removes ~150 lines
and makes the rescue rules auditable in one place. It would also fix the
inconsistency that some copies use `for rid in list(area_rooms)` (safe against
mutation) and some use `for rid in area_rooms` while removing from it.

### 5.4 [DEAD] Other dead/duplicated items
- `Maps.doorRandoOverride` (`data/maps.py:700`): never called (and buggy, 1.8).
- `debug_print_shortest_route` exists in both `data/doors.py:431` and
  `event/ruination.py:6465` with near-identical logic; the inner
  `get_door_name` helper is additionally triplicated inside `ruination.py`
  (5826, 6229, 6486).
- `data/rooms.py` `shared_oneways` has all its *entries* commented out
  (superseded by logical rooms + forced connections), but the empty dict is
  still consulted live by `data/transitions.py:58` — so it is an extension
  point, not dead code. Only the unused import in `doors.py` can go.
  *(Correction: originally misclassified as fully dead.)*
- `data/walks.py:448-455` `get_top_nodes` commented out.
- `check_network_invalidity` contains a ~60-line commented "locked forced"
  block (`data/walks.py:689-750`).
- `Doors.OVERRIDE` / `Doors.force_vanilla` debug scaffolding, plus the
  door-360/1291 hardcoded debug traces in `data/maps.py:546,596,662,681-685`.
- `event/events.py` hardcoded `exit_data[360]` debug is part of the same
  scaffolding family; sweep them together.
- `ruination_start_game_mod` (`event/ruination.py:6656-7008`): the party==2/3/4
  choreography blocks share ~80% of their content; table-driving them is
  optional polish (they are content, not logic).

---

## 6. Misleading names, comments, structure

- **`Doors.read()`** (`data/doors.py:423`) doesn't read anything; it appends
  pre-built lists to `self.rooms`. Inline it or rename.
- **`self.rooms` in `Doors` is a list of room-*sets*** (one per area) while
  `Network.rooms` is a `Rooms` collection — same attribute name, different
  shape, in classes that interoperate. Rename one (`self.area_room_sets`).
- **`map` shadows the builtin** throughout `Doors.mod()`,
  `Maps.connect_exits()`, and `generate_map_with_characters`.
- **`ruin_preprocessor` docstring** says `'minimum'`; code says `'custom'`
  (`args/ruin_preprocessor.py:228`).
- **Hub discovery by substring** — `[n for n in self.net.nodes if 'ruin_hub_'
  in str(n)][0]` appears ~15 times in `ruination.py` even though
  `get_hub_id()` exists (and returns `None` instead of raising `IndexError`).
  Use the accessor everywhere; make it raise a diagnostic error when absent.
- **`node` shadowing in `finalize_map` step 2** (`ruination.py:2581` vs
  `:2596`): the downstream node variable is overwritten by the upstream loop
  variable; correctness currently survives because `room` was captured first.
- **Verbose conventions disagree**: `Network.verbose` is a read-only property
  with a no-op setter, `Room.verbose` is a mutable class attribute defaulting
  to False, and many call sites wrap `vprint` in `if self.verbose:` despite
  the CLAUDE.md rule that `vprint` self-gates. Pick one idiom.
- **`Rooms.count`/`Room.count` return raw lists** whose index meanings
  ([doors, traps, pits, keys, locks]) are only documented in one comment; a
  tiny NamedTuple would de-cripple every `nc[:3] == [1, 0, 0]` call site.
- **`ROOM_SETS` comments drift from data** — e.g. `'EsperMountain_mapsafe'`
  line says `# 495,` (removed?) while 495 is present in the list; the `WoB`
  meta-set says `495,` excluded while `DungeonCrawl` includes 495 as a
  connector. These may all be intentional, but each needs a one-line "why".
- **Intentional-oddity documentation gaps** now covered in the guide:
  `forced_connections[2085]`'s source trap exists nowhere in `room_data` (it
  is injected at runtime by `process_rewards`), and `ruin_hub`'s pit 3039 is
  added dynamically when `LeteRiver3` enters a branch. Both look like data
  errors until you find the injection sites.

**STATUS (2026-07, branches p4/p6):** implemented on `door-rando-review-p4`:
hub accessor, step-2 `node` shadowing, preprocessor docstring. Implemented on
`door-rando-review-p6`: `Doors.read()` inlined; `Doors.rooms` renamed to
`area_room_sets`; the `map` builtin shadowing renamed in `Doors.mod`
(`full_map`), `Maps.connect_exits` (`door_map`) and
`generate_map_with_characters` (`full_map`), with the obsolete commented-out
map-construction block at the top of `connect_exits` removed;
`Room.verbose` now delegates to the central verbose flags like
`Network.verbose` — refined per HansGR feedback: Room-level output is a
separate *detail* level enabled only by `-dv all`
(`log/verbose.py:detail_enabled`), since plain `-debug`/`-dv` should stay
at network/branch verbosity (the `if self.verbose:` guards stay — they
skip building debug strings); `Room.count`/`Rooms.count`/`full_count`
docstrings document
the index layout; the ROOM_SETS trailing-id comment convention is documented
and the stale/ambiguous 495 comments corrected. NOT converted:
`count` to a NamedTuple — tuple-vs-list comparisons (`nc[:3] == [1, 0, 0]`)
would silently change semantics; revisit only with a full call-site audit.
All verified byte-identical to `door-rando-review-p5` on the 8-seed matrix.

---

## 7. Notes on things checked and found sound

Recorded so future reviews don't re-litigate them:

- **Room-set consistency**: every room referenced by `ROOM_SETS` (doors.py)
  and `RUIN_ROOM_SETS` (ruination.py) exists in `room_data`; no door is
  duplicated *within* the DungeonCrawl/All/WoB/WoR sets; all element IDs in
  `room_data` resolve to `exit_data`/`event_exit_info` under the documented ID
  conventions (the `2097/2098/2099/2128/2153/2176/3xxx` "trickery" IDs are
  intentionally virtual). `ROOM_REWARD` names all match `Event.name()` values.
- **`-rkt` verifier**: the joint state-space model in `_randomize_kefka_tower`
  (three parties × monotonic keychain, forward reachability + reverse-BFS from
  goal states) is a correct softlock model for the lane structure, and the
  state space is small enough (~12³×4) to be exact.
- **`_verify_no_character_gated_softlock`**: the free-graph vs full-graph
  comparison correctly excludes pre-existing one-way pockets from triggering
  rerolls.
- **`_honor_forced_connections`**: the `_pulling_forced` reentrancy guard and
  the "partner may already be present" checks handle the recursive add_room
  cases correctly.
- **Retry rollback in `events.ruination_mod`**: snapshot/restore of character
  pools, character paths, esper pools, and reward-slot objects is currently
  complete (but see 3.4 for why it's fragile by construction).
- **`compress_loop` check-room re-pointing** and the compound-id bookkeeping
  in `RuinationBranch` are correct, including inherited components from prior
  merges.
- **Isolated dream maze verifier** (`_randomize_isolated_maze`): the
  "every room reaches the end + both stooge keys round-trip from the end"
  criterion is sufficient for its softlock claim.

---

## 8. Suggested priorities

1. **Quick wins (small diffs, real payoff):** 1.1, 1.2, 1.3, 1.6, 1.7, 2.4,
   3.5, and the `exit_data` corrections in 1.4/1.5 (one-line data edits after
   verification).
   **STATUS: implemented 2026-07 on this branch** (all of 1.1/1.2/1.3/1.6/1.7/
   2.4/3.5, the daemon-thread half of 3.6, and every coordinate-verified
   `exit_data` fix from 1.4/1.5 — including 752→742, confirmed against
   `exits_raw.json`; the self-referencing 884 was set to None per HansGR
   (unreachable in game, unused in any mode); the ambiguous 509/519/647
   entries were left untouched pending domain confirmation). Verified by building seeds
   against a vanilla ROM for: baseline, `-drdc` ×3, `-dra`, `-dre -maps` ×2
   (the timeout-retry path fired live and recovered), `-mapx`, `-drcd`/`-drmk`
   flag strings, and `-ruin` ×3.
2. **Robustness investment:** 3.1 (copy lock lists — one line), then converge
   the remaining shared-state mutations behind a reset/copy boundary (3.2-3.4).
   **STATUS: implemented 2026-07 on branch `door-rando-review-p2`**: 3.1
   (Room.add_locks copies), `reset_room_tables()` in data/rooms.py +
   `reset_exit_data()` in data/map_exit_extra.py (called from
   `Doors.__init__`), `_reset_ruination_tables()` in event/ruination.py
   (called from `ruination_map.__init__`, so the retry loop can no longer see
   consumed EXTRA areas / migrated ROOM_REWARD keys / dream-maze table edits
   from a failed attempt), and `slot.possible_types` added to the retry
   rollback in events.ruination_mod (the Ebot's Rock pin no longer leaks
   across attempts). Verified: reset-boundary idempotency tests (Doors
   constructed twice; lock-list aliasing gone; ruination tables restored with
   slot-object identity preserved) plus the full build matrix; same-seed
   builds are byte-identical p1 vs p2 under a pinned PYTHONHASHSEED (see 3.9
   for the pre-existing `-ruin` hash-randomization nondeterminism this
   validation uncovered).
3. **Deletions:** 5.1, 5.2, 5.4 — roughly 1,600 lines removed with zero
   behavior change; do this before further refactoring so diffs stay readable.
   **STATUS: implemented 2026-07 on branch `door-rando-review-p3`** (~1,590
   lines deleted): the legacy mapper in `data/doors.py` (5.1) plus its dead
   attributes and unused imports; the v1 target-finders and
   `extend_branch_path_old` in `event/ruination.py` (5.2), with the `_v2`
   methods renamed to the plain names (call sites, ARCHIVE.md and
   event/TODO.md updated); `Maps.doorRandoOverride`, the `get_top_nodes` and
   locked-forced commented blocks in `data/walks.py`, the door-360/1291 debug
   traces in `data/maps.py`, and the triplicated `get_door_name` hoisted to a
   module-level `_door_description` (5.4). Deliberately kept:
   `shared_oneways` (live extension point — see corrected 5.4 bullet),
   `Doors.OVERRIDE`/`force_vanilla` (documented dev switches, guide §9), the
   generic safe_id warnings in `postprocess_door_map` (real diagnostics), and
   the `ruination_start_game_mod` choreography (content, not logic).
   Verified: `-drdc` and `-ruin` builds byte-identical to
   `door-rando-review-p2` for the same seeds under pinned PYTHONHASHSEED.
4. **Refactors:** 5.3 (reserve-pull helper), 6 (hub accessor), then 4.1/4.3 if
   `-drdc` generation time or the timeout rate is a live complaint.
   **STATUS: 5.3 and the hub accessor implemented 2026-07 on branch
   `door-rando-review-p4`.** The nine reserve-search loops in `finalize_map` /
   `_inject_door_if_needed_for_terminus` are now one
   `RuinationBranch._pull_from_reserve(reserve_areas, score, description)` —
   a boolean predicate acts as first-match, a numeric score picks the
   strictly-best room (preserving step (1)'s best-pit-surplus semantics); all
   copies now share the `rid in self.net.nodes` guard some were missing. Hub
   discovery goes through `require_hub_id()` (17 former `[...][0]` sites; a
   missing hub now reports the branch's nodes instead of a bare IndexError),
   with `get_hub_id()` kept for the two call sites that handle absence
   gracefully. Also fixed here: the §6 `node` shadowing in finalize_map step 2
   and the `ruin_preprocessor` 'minimum'→'custom' docstring. Verified:
   `-ruin` ×3 and `-drdc` builds byte-identical to `door-rando-review-p3`;
   unit tests for `_pull_from_reserve` (first-match, best-score, pool
   consumption, None/empty/no-match) and `require_hub_id`; 12-seed `-ruin`
   sweep. 4.1/4.3 (walk-performance) subsequently implemented on
   `door-rando-review-p5` — see the STATUS note under 4.3.

---

## 9. Speedup menu if seed compatibility is relaxed

The p5 optimizations were done under a byte-identical constraint: the same
seed produces the same map. This section documents what *else* is on the
table if that constraint is dropped — i.e., a given seed may produce a
different map, but every map must still be legal and valid. Estimates are
grounded in post-p5 profiles (2026-07, this container; profiler overhead
~2.5×, ratios are what matter).

**Decisions (2026-07):** 9.2 + 9.3 and the one-copy-per-attempt phase of
9.1 are implemented on branch `door-rando-review-p7`; the full undo
journal is deferred (see 9.1 STATUS). 9.4 is **rejected** — no added bias
toward hub rooms beyond the multiplicity their door count already gives
them. 9.6 is **rejected** — racing parallel attempts and taking the first
success would bias output toward simpler/shorter maps. For 9.5, rejection
sampling is deliberately kept for the small maps (KT lanes, FC, dream
maze) so all legal layouts remain reachable, as long as they don't
dominate wall-clock; investigating the ~4% `-ruin` regeneration rate for
better controls remains open.

### 9.0 Where the time goes today (post-p5)

**`-drdc`** (~2.3s/seed wall, of which walk ≈ 1.1s, rest is ROM/data/event
work): inside the walk, ~48% is still the copy-per-attempted-connection in
`connect_network` (now the fast copy, not generic deepcopy), ~42% is
`check_network_invalidity` (per-frame, per-node path-enumeration
traversals), ~10% is `attach_dead_ends` + `nx.relabel_nodes` + misc.

**`-ruin`** (~1.4s/seed wall): the branch mapper itself is ~0.08s and
`finalize_map` costs are negligible; `-rkt` adds ~0.3s typical
(`connect_lane` walks 0.16s + `verify` 0.10s over ~3-20 partitions, budget
400). Everything else (~1s) is event-script writing and data mods —
outside door-rando scope. The dominant `-ruin` latency risk is the retry
loop: ~1 seed in 25 regenerates the whole map up to 10×.

*Post-p7 (9.1 phase 1 + 9.2 + 9.3 implemented):* inside the `-drdc` walk,
copying is down to ~20% and `check_network_invalidity` dominates at ~65%
(196 copies per healthy walk, one per attempt). The next meaningful walk
speedup would be incremental/cached reachability for the invalidity
check, not further copy elimination.

### 9.1 Undo-log backtracking (drop the copy entirely) — biggest `-drdc` win

Replace copy-per-attempt with mutate-live + undo-on-failure. `connect()`
makes a bounded, journalable set of mutations (2 element removals, ≤2
edges, 1 map append) — the hard part is `compress_loop` (node merges) and
key cascades (`apply_key`/`_assess_room_locks`), which are easiest to
handle by snapshotting only when they fire (they are a minority of
attempts). Under byte-identity this was rejected because restoring exact
hash-table iteration order after undo is impractical; without it, only
logical state must be restored.
**Estimated gain: removes ~48% of walk time; with 9.2, walk drops an
estimated 5-10× (to ~0.1-0.2s), making `-drdc` builds ROM-work-bound.**
Effort: the largest item here; needs care around compress_loop/keys.

**STATUS: phase 1 implemented 2026-07 on branch `door-rando-review-p7`.**
`connect_network` is now a thin copying wrapper around an in-place
recursive worker (`_connect_network_inplace`): each frame mutates its own
trial copy freely (frame-entry and trail key applications) and makes
exactly **one** deepcopy per attempted connection instead of two
(frame-entry copy + per-attempt backup). Copy count on a healthy `-drdc`
walk: 391 → 196; ~15% faster end-to-end over a 10-seed `-drdc` batch.
Side effect of in-place key application: doors unlocked by a key in the
active room become candidates in the *same* frame rather than the next
one (equally legal, different maps).
The full undo journal (phase 2) is **deferred**: after phase 1 plus 9.2,
copying is only ~20% of walk time (invalidity checking dominates at
~65%), while the journal would have to faithfully undo `connect`,
`compress_loop` (room merges + `Rooms` element reindexing + node renames)
and `apply_key` cascades — a wide, high-risk mutation surface for a small
remaining win. Revisit only if walk time matters again after the
invalidity check is attacked directly (e.g. incremental reachability).

### 9.2 Linear-time reachability instead of path enumeration

`check_network_invalidity`, `is_dead_end`, `is_attachable`, and `get_loop`
all consume the duplicate-emitting path enumerations
(`get_*_nodes`/`get_*_paths`) whose worst case is exponential (currently
fenced by the 200k-iteration cap). Their *consumers* only need
reachable-sets and cycle existence:
- up/down streams → plain BFS/DFS reachable sets, O(V+E) per node (or one
  Tarjan SCC condensation per frame for all nodes at once);
- `get_loop` after connecting d1→d2 → a targeted "path from R2 back to
  R1" search, O(V+E), instead of enumerating all upstream paths. When
  multiple cycles exist it may pick a different (equally valid) loop to
  compress — that is exactly the seed-compatibility break.
**Estimated gain: most of the ~42% invalidity share plus the get_loop cost
inside every connect; also removes the exponential worst case and the
NetworkRecursionError fence entirely (a robustness win, review 4.2).**
Effort: moderate; the invalidity rules must be re-derived on reachable-set
semantics and re-validated (the rules are documented in §5 of the guide
and ARCHIVE.md).

**STATUS: implemented 2026-07 on branch `door-rando-review-p7`.**
`get_upstream_nodes`/`get_downstream_nodes` are plain BFS reachability
(each room once, discovery order, linear, no iteration cap needed);
`get_loop` finds a shortest cycle by BFS; the key-trail in
`connect_network` uses a BFS shortest path (`_upstream_trail`). The
duplicate-emission semantics are gone, so rooms reachable multiple ways
are no longer double-weighted in exit-candidate lists (consistent with
the 9.4 rejection). Average-case timing on healthy seeds was flat — the
real graphs are chain-like, so the old enumeration was near-linear in
practice — but the exponential worst case (the thing that made the old
10s timeout fire) is gone. `get_upstream_paths`/`get_downstream_paths`
remain, budget-capped, for the ruination consumers that need path lists.

### 9.3 Deterministic backtrack budget instead of the 10s wall-clock timeout

Not a raw speedup, but strongly recommended the moment compatibility is
relaxed: replace `connect_with_timeout`'s wall-clock limit with a budget
counted in backtracks (or attempted connections). Today a seed whose walk
runs ~10s produces *different maps on faster vs slower hardware*; a
deterministic budget makes every seed hardware-independent, lets doomed
walks abort earlier (lower tail latency), and removes the last
reproducibility caveat noted in p5. The budget number can be calibrated
from the retry telemetry (a healthy dc walk completes in ~200 frames).

**STATUS: implemented 2026-07 on branch `door-rando-review-p7`.**
`Network.walk_budget` is a `[remaining]` counter shared by every copy the
recursive search makes; `connect_network` charges one unit per attempted
connection and raises `WalkBudgetExceeded` (re-raised past the
backtracker as a global stop signal). `Doors.mod` arms it at 5000 —
measured healthy usage is ≤~215 attempts (`-drdc`) and far less elsewhere
— around the existing 5-attempt start-room re-roll loop, and logs
consumption to the verbose log ("walk budget used: N/5000"). The
threading timeout machinery is deleted (resolves 3.6 and the p5
hardware-dependence caveat). KT lane walks keep no budget (9.5 decision:
pure rejection sampling). Same-seed output verified byte-identical across
different `PYTHONHASHSEED` values for `-drdc`/`-dra`/`-ruin`.

### 9.4 Candidate-ordering heuristics in the walk

`connect_network` currently shuffles exits/entrances uniformly; failures
burn deep backtrack trees. Biasing candidate order (e.g., prefer entrances
in rooms with more remaining exits; connect low-connectivity rooms early —
the intuition behind the deleted legacy "drafting" mapper) reduces
backtrack depth and, more importantly, failure/timeout variance. Gains are
seed-dependent: small on average, large on the tail that currently
retries. This is also the likely fix for the chronically retry-hungry
`-dre` MapShuffleWOR area.

### 9.5 `-ruin`: cut the retry tail, not the mapper

The mapper is not the cost; regeneration is. Options, in value order:
1. **Reduce the ~4% failure rate** — feed `StuckReason` telemetry back
   into area distribution more aggressively, or allow `finalize_map` to
   pull one extra converter room preemptively when trap/pit parity looks
   tight. Every avoided failure saves a full ~0.4s regeneration (×10 worst
   case).
2. **Constraint-guided `-rkt` partitioning** — `split_lanes` currently
   rejection-samples partitions against parity/boss constraints (guard
   5000) and then walks/verifies up to 400 of them. Placing the glued
   pairs and bosses first under running parity constraints would cut
   rejected partitions by an order of magnitude. Typical saving ~0.2s,
   worst case much more; `verify()` itself is exact and cheap, keep it.
3. **Cached topology in finalize/extend** — `classify_topology` and
   `get_downstream_levels` (which still does substring matching over
   `self.map[1]` per path node) are recomputed per step; a reachability
   cache invalidated on `connect` would simplify the code, but absolute
   numbers are small (<0.05s/seed). Do it for clarity, not speed.

### 9.6 Parallel seed racing (wall-clock, not CPU, savings)

For batch/website generation: run k generation attempts in parallel worker
processes with sub-seeds derived from the master seed (`seed:0`,
`seed:1`, ...) and deterministically take the lowest-index success. Output
is still a pure function of the master seed, retries overlap instead of
serializing, and the tail (retry-prone `-ruin` seeds, timeout-prone
`-drdc` walks) collapses toward the median. Costs: process startup and
memory; the walk itself needs no ROM, but module import currently does
(review 3.7) — fork-after-import sidesteps that on Linux.

### 9.7 Guardrails for any of the above

Legality does not come from seed stability; it comes from the constructive
rules plus the explicit verifiers. Whatever changes: keep (a)
`postprocess_door_map`'s reciprocity check, (b) the trap/pit parity and
terminus assertions in `finalize_map`, (c)
`_verify_no_character_gated_softlock`, and (d) the `-rkt` joint-state
`verify()` as the acceptance gate, and re-run the review's standard sweep
(N-seed build matrix across `-drdc`/`-dra`/`-dre -maps`/`-mapx`/`-ruin`)
plus a spot-check of spoiler-log routes. A seed that builds and passes all
four verifiers is a legal map regardless of which map it is.
