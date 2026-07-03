# Programmer's Guide: Door Randomization Modes

A map of the Dungeon Crawl (`-drdc`) and Ruination (`-ruin`) codebases: what
the pieces are, how a seed flows through them, and the invariants and gotchas
you must respect when extending them. Findings from the accompanying review
live in `DOOR_RANDO_CODE_REVIEW.md`; known design debts are in `event/TODO.md`
and the deep-dive notes in `ARCHIVE.md`.

---

## 1. The two modes in one paragraph each

**Dungeon Crawl (`-drdc`)** re-wires (nearly) every door in the game into one
fully-connected dungeon spanning both worlds. It runs a single constructive
graph walk (`data/walks.py:Network.connect_network`) over a large fixed room
set (`ROOM_SETS['DungeonCrawl']`, ~304 rooms), then writes the resulting
connection list to the ROM. World-map areas are modeled as "connector" rooms
so towns become hallways of the dungeon. Rewards/character logic is standard
open-world; only geography changes.

**Ruination (`-ruin`)** is a roguelike: no airship, no overworld. Three
"branches" grow outward from the Narshe school hub, each terminating in a lane
of Kefka's Tower. Rooms are grouped into named *areas* owned by characters;
areas are added to branches as their characters are planned/recruited, and a
bespoke incremental mapper (`event/ruination.py:RuinationBranch`) grows each
branch reward-by-reward, then `finalize_map` closes all loose ends. Reward
placement, key/lock logic, softlock verification, shops, the ferry network,
and a large amount of event scripting are all mode-specific.

Both modes share: the element-ID vocabulary, `room_data`, the `Network`/`Rooms`
/`Room` classes, forced/shared-exit machinery, and the entire ROM-writing layer
(`data/maps.py`, `data/transitions.py`).

---

## 2. Vocabulary: elements, rooms, and the ID space

Everything the mapper connects is an integer "element" belonging to a **room**.

| ID range | Meaning |
|---|---|
| 0–1128 | vanilla short exits ("doors", two-way) |
| 1129–1280 | vanilla long exits (also doors) |
| 1281–1300 | reserved as `safe_id` scratch range for DC/ruin destination overrides (`data/maps.py:646`) |
| 1500–1999 | event tiles acting as doors (need runtime connection data; see §7) |
| 2000–2999 | **traps** — one-way exits (`event_exit_info`) |
| 3000–3999 | **pits** — one-way entrances; vanilla pairing is `trap + 1000 = pit` |
| 4000–5999 | logical WoR copies of doors on shared WoB/WoR maps (`id − 4000` = base door) |
| 6000–7999 | pits associated with doors that behave as one-ways (`id − 6000` = door) |
| 10000+ | virtual "root" doors invented by `Doors.mod()` for `-dra`/`-drx` meta-connectivity |
| 30000+ | "protected" copies used by map-shuffle to shield a door from randomization (`id − 30000` = base) |
| strings | **keys** (e.g. `'TERRA'`, `'pt1'`, `'lw1'`, `'KT1'`) |

A **room** (`data/rooms.py:room_data`) is
`[doors, traps, pits, world]` or the six-slot form
`[doors, traps, pits, start_keys, locks, world]`, where `locks` maps a key (or
tuple of keys — normalized to sorted tuples by `Room.add_locks`) to a list of
locked elements/keys. Rooms are identified by ints (vanilla map rooms),
`'37a'`-style variants, or names (`'ruin-*'`, `'ms-*'`, `'dc-*'`, `'root-*'`,
`'KT*'`, `'LeteRiver1'`, ...). **Many doors appear in several room entries**
(variants of the same physical room used by different modes); each mode's room
*set* must include at most one variant.

Doors listed in `shared_exits` (multi-tile entrances that must share one
destination) are stripped from `Room`s at construction and re-attached to the
final map afterward — so "shared" doors intentionally look duplicated in
`room_data` vs `shared_exits`.

`forced_connections` lists trap→pit (and a few door) pairs that must always be
wired to each other (in-map mechanisms: bridge jumps, elevators, "trickery"
reward routes). Their IDs are added to `Network.protected`, which excludes
them from random target selection everywhere.

Two intentionally-surprising data facts:
- `forced_connections[2085]`'s source trap exists in **no** `room_data` entry:
  it is injected onto the live Ebot's Rock room at runtime only when its
  reward is a character (`ruination.py:process_rewards`).
- `ruin_hub`'s pit `3039` (Lete River return) is likewise added dynamically in
  `RuinationBranch.add_room` when `LeteRiver3` joins a branch.

---

## 3. File map

| File | Role |
|---|---|
| `args/doors.py` | flag definitions for all door-rando modes; mode precedence in `process()` |
| `args/ruin_preprocessor.py` | expands `-ruin` into ~90 default flags before argparse runs |
| `data/rooms.py` | `room_data` + `shared_exits`, `forced_connections`, `logical_links`, `dungeon_crawl_split_exits`, `doors_as_traps` (derived), `exit_room`/`exit_world` lookups |
| `data/walks.py` | `Network` (graph + walk algorithm), `Rooms`/`Room` (element containers, key/lock semantics) |
| `data/doors.py` | `Doors` orchestrator: picks room sets per flags, runs walks, post-processes (logical links, shared exits, WOB↔WOR mirroring), `ROOM_SETS` |
| `data/map_exit_extra.py` | `exit_data` (door → [vanilla partner, description]), `doors_WOB_WOR`, `eventname_to_door` |
| `data/event_exit_info.py` | trap/pit event metadata (address, length, transition state, location) + `exit_door_patch` / `entrance_door_patch` script injections. **Imports `instruction.field` at module scope — cannot be imported without a loaded ROM.** |
| `data/transitions.py` | writes one-way (and event-tile door) connections as event-code rewrites |
| `data/maps.py` | `postprocess_door_map()` (pairing table + WoR logical exits + DC overrides), `connect_exits()` (two-way door writing), `write()` (runtime event-address fixup + Transitions) |
| `event/ruination.py` | everything Ruination: constants/areas/rewards, `RuinationBranch`, `ruination_map`, KT lane randomizer, dream-maze randomizer, start-game/party/ferry event mods |
| `event/events.py` | `ruination_mod()` — the integration point: retry loop, reward slot wiring, spoiler log, `postprocess_door_map()` call |
| `instruction/field/instructions.py` | `RecruitAndSelectParty` wraps recruitment with `SetupBranchRecruit`/`FinalizeBranchRecruit` in ruin mode |

Reference data for humans: `claude_reference/exits_raw.json` (vanilla exit
records), `claude_reference/room_map_reference.json` (room → SNES map),
`DEBUG_SHORTEST_ROUTE.md` (the `-debug_dest` tool).

---

## 4. Execution flow

### Common skeleton (`wc.py`)
`Memory` (loads ROM) → `Data` (all `data/*` mods, including
`Maps.mod()` → `Doors.mod()`) → `Events` (event script mods, rewards) →
`Memory.write()`.

### Dungeon Crawl / `-dra` / `-drx` / `-dre` / individual flags
1. `Doors.__init__` selects room sets from `ROOM_SETS` based on flags, applies
   mode-specific data surgery (splitting `dungeon_crawl_split_exits` out of
   `shared_exits`), and stores areas in `self.rooms`.
2. `Doors.mod()` — per area: build a `Network`, apply immediate keys, force
   connections, `attach_dead_ends()`, pick a start room, then
   `connect_with_timeout(walks, 10s)` runs the recursive walk. Post-processing
   patches logical links, applies shared exits, strips virtual root doors,
   mirrors WoB→WoR (`-drun`), and stores `self.map = [[door pairs], [trap→pit pairs]]`.
3. `Maps.mod()` immediately calls `postprocess_door_map()` (non-ruin), which
   builds `door_map` (symmetric pairing dict), appends vanilla-connected
   logical WoR exits, applies the DC destination overrides (rewriting
   `exit_data` with `safe_id`s), and validates reciprocity.
4. `Maps.write()` fixes up switchyard event addresses, runs `Transitions` for
   one-ways, and `connect_exits()` for doors (copying each door's *partner's
   vanilla exit record* onto the randomized door — this is why `exit_data`'s
   partner field must be correct), plus the `exit_door_patch` /
   `entrance_door_patch` script injections.

### Ruination
1. `Doors.__init__` runs but selects **no room sets** (mapping happens later);
   it still performs the shared-exit splits and drops `forced_connections[1079]`.
2. `Events.ruination_mod()` (`event/events.py:245`):
   - binds each `ROOM_REWARD` name to its live `Reward` slot object,
   - snapshots character/esper/reward-slot state,
   - constructs `ruination_map(...)` and calls
     `generate_map_with_characters()`, retrying up to 10× on
     `RuinationMappingError` (≈1 in 25 seeds fails; failures are unlucky
     rolls, not unsatisfiable configs),
   - stores `args.ruination_areas_used = compute_actual_areas_used()` (use
     this, **not** raw `AreasUsed`, for anything player-facing),
   - handles dried meat / limited shops / spoiler log / map image,
   - calls `maps.postprocess_door_map()`,
   - disables chocobo stables and wires the ferry network.
3. `Maps.write()` proceeds as above (with `force_explicit` behavior for ruin).

---

## 5. The core walk: `Network.connect_network` (used by DC and KT lanes)

The walk is a recursive backtracking search. Each frame:
1. **Deep-copies the whole network** (`net_state = deepcopy(self)`) — all
   mutations happen on the copy; backtracking = discarding it. This is
   correct-by-construction and very expensive (see review §4.1).
2. Runs `check_network_invalidity()` — rule-based rejection (network
   bifurcation, one-way imbalance, door in/out imbalance, dead-ends with
   internally-locked exits). Invalid ⇒ raise ⇒ caller backtracks.
3. Gathers exits from the active room + everything downstream, shuffles,
   prioritizes forced exits ("fail fast"), then for each exit gathers
   candidate entrances (excluding `protected`), shuffles, and recurses after
   each `connect()`.

`connect(d1, d2)` adds graph edges (both directions for doors), appends to
`self.map[0]`/`map[1]`, removes both elements from their rooms, then looks for
a newly-formed loop and **compresses** it: all rooms in the loop merge into a
compound room whose ID is the member IDs joined by `'_'`. Keys found in the
newly-active room are applied (`apply_key`), which may unlock locked elements
anywhere (`_assess_room_locks`), turning them live and (for exits) recording
them in `initially_locked_exits` (they may be *used* by the mapper but not
*targeted*, since the player may lack the key on first arrival).

**Compound-room convention:** membership tests against compound IDs must
bracket with underscores (`f'_{room_id}_' in f'_{compound_id}_'`) — bare
substring tests false-positive on numeric prefixes (78 vs 278).

**Terminology used throughout ruination code:** PITO = pit-in/trap-out room,
PIDO = pit-in/door-out, DITO = door-in/trap-out, DIDO = door-in/door-out.
These describe what a room can do for connectivity (a PIDO converts a one-way
descent back into two-way territory, etc.).

---

## 6. The Ruination mapper

### 6.1 Setup (`ruination_map.__init__`)
- Rolls requested character/esper counts from `args.ruin_characters_required`
  / `ruin_espers_required` (min 3 characters).
- `pre_plan_character_acquisition()` picks the planned character list and
  verifies the implied areas contain enough character/esper reward slots;
  unplanned characters become the **reserve** (their areas are the rescue pool).
- Configures the dream maze (`-maze full|sep|iso`; `iso` pre-randomizes a
  composite maze room with an exact solvability check) and Kefka's Tower
  (`-rkt`, see §6.5).
- Creates three `RuinationBranch`es, each seeded with a synthetic one-door hub
  room (`ruin_hub_0/1/2`, appended to `room_data` at runtime) plus one shuffled
  terminus (`ruin_terminus_1/2/3` — Sealed Gate / Esper Mtn / Daryl's Tomb
  staircase, the KT connection points).
- `distribute_areas()` spreads the starting party's areas across branches
  (respecting `forced_same_branch`, spreading `STANDALONE_TOWNS` evenly, and
  prioritizing stuck branches by the connector type they need).

### 6.2 Growth loop (`generate_map_with_characters`)
Repeat until planned characters + requested espers are placed:
1. Pick a viable branch (has a hub-capable room and pending checks), weighted
   toward branches with fewer rewards found.
2. `extend_branch_path()` — topology-aware single-step extension:
   classify rooms into hub (level 0) / upstream (−1; rooms that flow *into*
   the hub) / downstream (1+; reached by falling through traps); prefer trap
   exits; validate each candidate connection with
   `get_valid_pit_targets_v2` / `get_valid_door_targets_v2`, whose rules
   guarantee the branch never loses its last exit and never strands pits
   (documented in ARCHIVE.md "Location-aware branch mapping").
3. `connect()`, tick warp/town cooldowns (anti-clustering counters), and check
   `check_for_rewards`: if the new room is a `ROOM_REWARD` room, its checks
   become claimable — unless locked by an unrecruited character
   (`REWARDS_LOCKED_BY_CHARACTER` for in-game locks, `REWARD_OWNERS` for
   area-level gating), in which case they're banked in `LockedRewards`.
4. `process_rewards()` assigns character/esper/item to the slot (characters
   get `set_character_path` for objective/gating bookkeeping), applies the new
   character as a key to all branches, distributes the character's
   `CHARACTER_AREAS` (+ satisfied `CONDITIONAL_AREAS`), and recursively
   processes any banked rewards the recruit unlocked.
5. A branch that can't extend after 3 retries is marked stuck with a
   `StuckReason`; `distribute_areas` and the reserve pool
   (`get_reserve_area_rooms`) are used to unstick it (adding the area of a
   reserve character, resetting the active room to the hub).

### 6.3 Closing (`finalize_map`)
Runs per branch, in a loop (max 10 iterations, restarting when keys unlock new
elements mid-close):
0. Honor newly-live forced connections (may pull partner rooms from reserve);
   rescue orphan warp rooms; pre-inject a door if the network has traps but no
   doors (terminus needs one).
1. While traps > pits in the connected network: connect a trap to the pit of
   the best unconnected pit-surplus room (reserve fallback).
2. Loop every downstream node back to hub/upstream (trap→upstream-pit
   preferred, door→door fallback with "don't consume the last two doors"
   guard, PIDO/DITO converter search, terminus-exit preservation). Ends with a
   hard check that no downstream nodes remain.
3. Connect all remaining trap/pit pairs (reserve rescue if traps remain).
4. Connect the terminus to a hub door (deferred to step 6 if none).
5. Pair off excess hub doors against each other until doors ≤ dead ends
   (orphan-door rescue against unconnected rooms).
6. Connect each remaining door to a dead-end room — key-bearing dead ends
   first so the **last** connection can't unlock anything new; if a key does
   unlock elements, break and restart the loop.

After all branches close, `generate_map_with_characters` validates: hub has no
dangling exits; the terminus was merged into the hub compound. Then it
assembles the global map, appends shared exits, splices in the isolated-maze
and KT-lane maps, randomly assigns the three hub-side KT traps (2077-79) to
the KT entry pits (3077-79), and runs
`_verify_no_character_gated_softlock` — a free-graph (starting party only) vs
full-graph reachability comparison that rerolls the seed if a region can be
entered but not exited without an elsewhere-recruited character.

### 6.4 Keys and locks — the timing rules
- The **global keychain** starts as the starting party (all characters under
  `-open`) and grows monotonically; `ruination_map.apply_key` fans out to all
  branches and promotes newly-accessible banked rewards.
- `Network.add_room` assesses a new room's locks against the *current*
  keychain (`_assess_room_locks`) — rooms can arrive after their key was
  applied (character areas distribute after the character key). This was the
  Mog→`lw1`→Lone Wolf bug; don't remove it.
- `initially_locked_exits` = exits that only became live via a key. They are
  excluded as *targets* during extension (the player may arrive before the
  key) but may be *sources*.

### 6.5 Kefka's Tower (`-rkt`)
KT is randomized independently of the branch graph: partition the 35 `KT*`
rooms into three lanes satisfying cheap invariants (one entry + one final
each, gated-crossing pairs glued, ≤2 bosses, trap/pit parity, even doors),
walk each lane with `Network.connect_network`, then verify the *joint* system
— three parties moving asynchronously over a shared monotonic keychain
(`KT1`/`KT2` switches) — demanding every room reachable and every reachable
joint state able to finish. Up to 400 partitions are tried; on failure the
vanilla KT layout is kept. Output is injected into the global map, with the
platform pseudo-IDs stripped (they're map features, not writable exits).

### 6.6 Beyond the map
The back half of `event/ruination.py` is event scripting, not mapping:
start-of-game cinematic (`ruination_start_game_mod`), party-interaction
dialogs (`create_party_interaction_scripts` + `SET_PARTY_INTERACTION_POINTERS`
re-binding, because NPC talk pointers are field RAM), the y-party-switch
disable/restore subroutines, chocobo stable disabling, and the ferry network
(`fix_ferry_connections`: SF/Nikeah/Albrook sailors link whichever of the
three ports actually have reachable rooms — 0-1 ports ⇒ disabled sailors).

---

## 7. The ROM-writing layer (shared by both modes)

`postprocess_door_map()` (`data/maps.py:538`) turns `doors.map` into
`door_map` (a symmetric dict), verifying reciprocity modulo shared-exit
groups. For every mapped WoB door on a shared map, the logical WoR twin
(`+4000`) is appended with its vanilla connection so shared-map exits still
work in the other world.

`connect_exits()` writes two-way doors: for each mapped door `m → map[m]`, the
exit record of **`map[m]`'s vanilla partner** is copied onto `m`'s exit
(`copy_exit_info`). This is the load-bearing use of `exit_data[id][0]` —
errors in that field produce doors that dump you at the wrong coordinates.

One-way connections and event-tile doors (IDs 1500-1999) go through
`Transitions`, which rewrites the tail of each exit event (after its
`split point` from `event_exit_info`) into a `LoadMap` to the new destination,
carrying the `transition state` flags (character hidden, song override, screen
hold, raft, parent-map update). Event tiles whose `event_exit_info` address is
`None` (switchyard tiles) get their addresses resolved at write time by
looking up the event at their map coordinates — and when an event-tile door's
*partner* is also an event tile, the partner's info is used
(`use_event_info`), which is why **both sides' partners must be included in
`used_events`** (CLAUDE.md Top-10 #4).

`exit_door_patch` / `entrance_door_patch` (`data/event_exit_info.py`) inject
extra script fragments before/after specific transitions (e.g. character
gating on an entrance). `entrance_door_patch` values may be callables taking
`args`; their scripts must **fall through** (no trailing `field.Return()` —
see ARCHIVE.md). Ruination pops a few of these (door 1558, Figaro
`require_event_bit`s) because its gating works differently.

The **switchyard** (map 0x005) is the trampoline for transitions that can't be
expressed as exits (Zone Eater engulf, serpent trench dives): each virtual
transition owns tile `(id % 128, id // 128)` there.

---

## 8. Global mutable state — read before writing any code here

These module-level tables are mutated at run time. Since the
`door-rando-review-p2` changes there is an explicit reset boundary:
`Doors.__init__` calls `data.rooms.reset_room_tables()` and
`data.map_exit_extra.reset_exit_data()`, and `ruination_map.__init__` calls
`event.ruination._reset_ruination_tables()`, so every build (and every
ruination retry attempt) starts from pristine tables. If you add a new
run-time mutation of module data, either make it idempotent or add it to the
appropriate reset function — and if it can fire inside a single generation
attempt (like the reward-slot `possible_types` pin), add it to the retry
rollback in `events.ruination_mod` as well. The mutation inventory:

| Table | Mutated by |
|---|---|
| `data.rooms.shared_exits` | `Doors.__init__` (DC/ruin split-exit removal) |
| `data.rooms.forced_connections` | `Doors.__init__` (ruin pops 1079); `generate_map_with_characters` (pops `ruination_dont_force`) |
| `data.rooms.room_data` | `ruination_map.__init__` (adds `ruin_hub_*`); `_randomize_isolated_maze` (rewrites `ruin-stooge-maze` pits); `Doors.mod` root-door appends (`-dra`/`-drx`); **aliased lock lists** mutated via `Room.remove`/`attach_dead_ends` (review §3.1) |
| `data.map_exit_extra.exit_data` | `postprocess_door_map` DC/ruin destination overrides |
| `data.event_exit_info.event_exit_info` | `Maps.write` fills in `None` addresses |
| `event.ruination.CHARACTER_AREAS`, `RUIN_ROOM_SETS`, `WARP_ROOMS`, `forced_same_branch`, `ROOM_REWARD` | `_configure_dream_maze`; `events.ruination_mod` (binds slot objects); `finalize_map` step 6 (pins Ebot's Rock `possible_types`) |
| `event.ruination.CHARACTER_LOCKED_REWARDS` / `REWARDS_LOCKED_BY_CHARACTER` | cleared under `-open` |

The ruination retry loop (`events.py:290-332`) manually snapshots/restores the
character pool, character paths, esper pool, and reward-slot fields. If you
add a new mutation of shared state inside map generation, **you must add it to
that rollback** (or better: stop mutating shared state).

Also: `import args` parses `sys.argv` at import time, and importing
`data/event_exit_info.py` (hence `data/doors.py`, `data/walks.py` consumers)
requires an initialized ROM. For standalone experiments, fake both first:

```python
import sys; sys.argv = ['wc.py', '-i', dummy_rom_path]
from memory.rom import ROM
from memory.space import Space
from memory.free import free
Space.rom = ROM(dummy_rom_path); free()
```

---

## 9. Debugging toolkit

- `-debug` — verbose mapping output to stdout; also makes all maps warpable.
- `-dv` / `-debug-verbose` — verbose output to a temp file appended to the
  spoiler log (`log/verbose.py:vprint`; it self-gates — never wrap it in
  `if self.verbose:`).
- `-debug_dest <room ...>` — prints the shortest route from any world-map/hub
  room to the target room(s) after mapping (`DEBUG_SHORTEST_ROUTE.md`).
- `-sl` with `-ruin` — ruination spoiler log section plus a rendered map image
  (`<seed>_ruination_map.png`).
- `RuinationMappingError` messages embed `_collect_mapping_diagnostics()`:
  per-branch topology visualizations (`visualize_branch_topology`), reward
  state, keychains, reserve areas. Read the "Troubleshooting Hints" footer.
- `NetworkRecursionError` (walks.py) snapshots nodes/edges/2-cycles/maps when
  a traversal exceeds its iteration cap — usually means an uncompressed
  2-cycle from a missed loop compression.
- `Doors.force_vanilla` / `Doors.OVERRIDE` — dev switches to force vanilla
  connections or pin specific pairs while testing event patches.

---

## 10. Recipes

**Add a room to Ruination.** Define/choose the `room_data` entry (mind door ID
conventions, and pick the right WoB/WoR/`ruin-*` variant); add it to the
appropriate `RUIN_ROOM_SETS` area. If it holds a check, add a `ROOM_REWARD`
entry whose name matches the event's `name()` (suffix `_N` selects
`event.rewards[N-1]`), plus `REWARD_OWNERS` if the area is character-owned.
If it has a save/warp point, add it to `WARP_ROOMS`; town entries to
`TOWN_ROOMS`. Check whether any of its exits appear in `shared_exits` or need
`forced_connections`.

**Add an area.** New `RUIN_ROOM_SETS` key; attach it to a character in
`CHARACTER_AREAS` (or `'ALL'`/`'EXTRA'`); add `AREA_SHOPS` if it has shops;
add `forced_same_branch` links if it must co-locate with another area. Ensure
the area contains at least one hub-capable room (3+ doors/traps) or PIDO
connector, or it can only ever be rescue-filler.

**Add a room to Dungeon Crawl.** Append to `ROOM_SETS['DungeonCrawl']` (and
usually `'WoB'`/`'WoR'` for `-dra`). Avoid dead ends where possible (the DC
set deliberately drops them); check `dungeon_crawl_split_exits` if the room's
town entrance is a multi-tile shared exit.

**Add a new one-way (trap/pit).** Allocate a 2xxx/3xxx pair, add an
`event_exit_info` entry (original event address, byte length, split point,
transition state, location — or `None` address + switchyard coords for
virtual tiles), reference them from the owning rooms, and add a
`forced_connections` entry if the pair must stay vanilla-wired.

**Touch `finalize_map` / `extend_branch_path`.** Re-read the invariants in
§6.2-6.3 and ARCHIVE.md ("Key/Lock Softlock Analysis",
"Location-aware branch mapping", "Kefka's Tower Lane Randomizer") first. Any
new connection path must preserve: never consume the branch's last exit; never
strand a pit; never let the *final* step-6 connection carry a key; terminus
must merge into the hub. When in doubt, add the check to
`_verify_no_character_gated_softlock` rather than trusting the constructive
rules.
