# ARCHIVE.md

This file contains useful reference information that has been moved from the Top 10 in CLAUDE.md. Scan this file when looking for specific detailed information.

---

## Table of Contents

Sections are grouped by theme. The file is append-only, so on-disk order doesn't match this grouping — use the links below or the section headings as anchors.

### FF6 Internals (vanilla reference)
- [Field Object Data Structure (41 bytes per object)](#field-object-data-structure-41-bytes-per-object-0867-1068)
- [FF6 Text Encoding Types](#ff6-text-encoding-types)
- [Battle MP Zeroing & MP-Drain Criticals (2026-08)](#battle-mp-zeroing--mp-drain-criticals-2026-08)
- [Battle Command-Menu Cursor Engine & the All-Invalid Hardlock (2026-08)](#battle-command-menu-cursor-engine--the-all-invalid-hardlock-2026-08)
- [Experience Table & Level Cap (`-lc`) (2026-10)](#experience-table--level-cap--lc-2026-10) (table encoding, the three readers, 15M cap, 24-bit wrap)

### Ruination Mode — Architecture
- [Ruination Mode (`-ruin`) — Detailed Architecture](#ruination-mode--ruin---detailed-architecture)
- [Narshe Battle Exclusion + Ruination Boss Budget (2026-07)](#narshe-battle-exclusion--ruination-boss-budget-2026-07)
- [Ruination Esper-Capacity Corner (High Esper Counts) (2026-07)](#ruination-esper-capacity-corner-high-esper-counts-2026-07)
- [Post-Rewrite Structural Review + Commentary Sweep (2026-07)](#post-rewrite-structural-review--commentary-sweep-2026-07)

### Ruination Mode — Mapping Algorithm
- [Mapping Algorithm Analysis](#ruination-mode---mapping-algorithm-analysis)
- [Key/Lock Softlock Analysis & Fix (2026-02-10)](#keylock-softlock-analysis--fix-2026-02-10)
- [finalize_map Debug Patterns (2026-02-09)](#ruination-mode---finalize_map-debug-patterns-2026-02-09)
- [Keyless One-Way Softlock — Walk Rule + Keychain-Lattice Verifier (2026-08)](#keyless-one-way-softlock--walk-rule--keychain-lattice-verifier-2026-08)
- [Branch Area Detection for Narshe Clues (2026-04)](#branch-area-detection-for-narshe-clues-2026-04)
- [Walk Reachability Rules G/H + Short Restarts (2026-09)](#walk-reachability-rules-gh--short-restarts-2026-09)

### Ruination Mode — Party Formation
- [Party Formation & Away-Party System (2026-02)](#ruination-mode---party-formation--away-party-system-2026-02)
- [SET_PARTY_INTERACTION_POINTERS shared subroutine (2026-04)](#set_party_interaction_pointers-shared-subroutine-2026-04)
- [Y-Party-Switch Disable Shared Subroutines (2026-06)](#y-party-switch-disable-shared-subroutines-2026-06)

### Ruination Mode — Event Patterns
- [Conditional Area Checks](#ruination-mode---conditional-area-checks)
- [Duplicate Event Tiles for Reverse Entrances (2026-02)](#ruination-mode---duplicate-event-tiles-for-reverse-entrances-2026-02)
- [Patching NPC Events](#ruination-mode---patching-npc-events)
- [Persistent Event State Across Reloads (2026-04)](#persistent-event-state-across-reloads-2026-04)
- [Dialog ID Reservations (2026-05)](#ruination-mode--dialog-id-reservations-2026-05)
- [Floating Continent Tube-Maze Randomizer (2026-06)](#floating-continent-tube-maze-randomizer-2026-06)
- [Kefka's Tower Lane Randomizer (`-rkt`) (2026-06)](#kefkas-tower-lane-randomizer--rkt-2026-06)
- [Terminus Already-Used Events (2026-10)](#terminus-already-used-events-2026-10)

### Door Randomizer
- [Event Exit Info — Detailed Data Structures](#event-exit-info---detailed-data-structures)
- [Local Character Gating (Door Rando)](#local-character-gating-door-rando)
- [entrance_door_patch must fall through (2026-04)](#entrance_door_patch-must-fall-through-2026-04)

### Feature Flags (deep dives)
- [Limited Inventory Shops (`-sli` flag)](#limited-inventory-shops--sli-flag)
- [No Free Heals (`-nfh` / `--no-free-heals`)](#no-free-heals--nfh----no-free-heals)
- [DISABLE_B_DASH Event Bit (2026-08)](#disable_b_dash-event-bit-2026-08)
- [Out-of-Battle Magic Submenu by Spell Knowledge (2026-08, SHELVED)](#out-of-battle-magic-submenu-by-spell-knowledge-2026-08-shelved)
- [Starting Level Random (`-stlr`) (2026-10)](#starting-level-random--stlr-2026-10)
- [Command Probability Modes (`-compr`/`-compru`) — Rolls, Unique Pool, Calculator (2026-10)](#command-probability-modes--compr-compru--rolls-unique-pool-calculator-2026-10)
- [Experience Table & Level Cap (`-lc`) (2026-10)](#experience-table--level-cap--lc-2026-10)

### Custom Opcodes
- [Custom Opcodes Reference](#custom-opcodes-reference) (consolidated table)
- [BranchProbability vehicle-script opcode (0xE1) (2026-04)](#branchprobability-vehicle-script-opcode-0xe1-2026-04)

### Bug Post-Mortems
- [SelectParties Inventory Corruption Bug & Fix (2026-04)](#selectparties-inventory-corruption-bug--fix-2026-04)
- [Persistent Raft Graphic After Re-riding the Magitek Minecart (2026-06)](#persistent-raft-graphic-after-re-riding-the-magitek-minecart-2026-06)
- [Floating Continent Save-Room Return — LoadMap Entrance-Event Flag (2026-08)](#floating-continent-save-room-return--loadmap-entrance-event-flag-2026-08)
- [Mt Zozo Arrival Hardlock (2026-08)](#mt-zozo-arrival-hardlock-2026-08-quick-post-mortem)
- [Phantom Train Car Bits on One-Way Landings (2026-09)](#phantom-train-car-bits-on-one-way-landings-2026-09)
- [Albrook Dock Sailor Showed General Leo (2026-09)](#albrook-dock-sailor-showed-general-leo-2026-09)

### Conventions
- [Debug Output Routing (`-debug` vs `-debug-verbose`) (2026-04)](#debug-output-routing--debug-vs--debug-verbose-2026-04)

### Race ROM Obfuscation (`-race`, branch `feature/race-obfuscation`)
- [Race ROM Obfuscation — Pointers, Resource Claims & Lessons (2026-09)](#race-rom-obfuscation--pointers-resource-claims--lessons-2026-09)

### Testing & Harness
- [Headless Playtest Harness Patterns (2026-08)](#headless-playtest-harness-patterns-2026-08) (incl. the s9xsnp savestate format — inside the FC post-mortem above)
- [World-Map Navigation in the Harness (2026-08)](#world-map-navigation-in-the-harness-2026-08) (airship, on-foot teleporting, routing tables, Figaro Castle route, Lineup screen)
- [Harness Recipes from the Race Project (2026-09)](#harness-recipes-from-the-race-project-2026-09) (savestate transplant, debug-room warp, event-engine state, byte-identity A/B, entrance-event flag)

### Lookups (see CLAUDE.md "How to Find X" cheat sheet first)
- [Finding NPCs in Reference Data — Detailed Procedure](#finding-npcs-in-reference-data---detailed-procedure)
- [Finding Map IDs by Name — Detailed Example](#finding-map-ids-by-name---detailed-example)
- [Bank C1 Annotation Project — Status & Resume Notes (2026-08)](#bank-c1-annotation-project--status--resume-notes-2026-08)

---

## Field Object Data Structure (41 bytes per object, $0867-$1068)

50 objects total: $00-$0F = characters, $10-$2F = NPCs, $30 = camera, $31 = showing character.

### Key offsets within each object:

| Offset | Size | Description |
|--------|------|-------------|
| $00 | 1 | Settings: `verbbppp` — v=Visible, e=Enabled, r=Battle Row, bb=Battle Order, ppp=Party |
| $01 | 1 | Sprite settings: `vvvddoom` — v=Vehicle, d=facing dir, o=layer priority, m=walk anim |
| $02-$04 | 3 | X position (sub-pixel): `tttttttt ttttpppp xxxxxxxx` — tile=(byte0<<4\|byte1>>4) |
| $05-$07 | 3 | Y position (sub-pixel): same format as X |
| $12 | 1 | Character/NPC index (matches slot number for characters) |
| $13 | 1 | **Tile X position** — authoritative tile coordinate used by collision engine |
| $14 | 1 | **Tile Y position** — authoritative tile coordinate used by collision engine |

**Critical:** Offsets $02-$07 are the sub-pixel *rendering* position. Offsets $13-$14 are the *tile-level collision* position. If these desync (e.g., entity not properly deleted before map transition), the object creates an **invisible collision block** at its tile position with no visible sprite.

### Tile Properties (field RAM $A3-$B9)

Adjacent tile indices (BG1) around the party object:
```
+----+----+----+
| A3 | A4 | A5 |
+----+----+----+
| A6 | A7 | A8 |
+----+----+----+
| A9 |*AA*| AB |  <-- party object
+----+----+----+
| AC | AD | AE |
+----+----+----+
```

- **$AF-$B0**: Party tile position (X, Y)
- **$B2**: Party z-level (`------lu`, l=lower, u=upper)
- **$B6-$B7**: Tile properties from A7 (tile above party) — byte 1 + byte 2
- **$B8-$B9**: Tile properties from AA (party's tile) — byte 1 + byte 2

**Tile properties byte 1** (`lrdbtslu`): l/r=stair dirs, d=door, b/t=sprite priority, s=solid/bridge, l=passable-lower-z, u=passable-upper-z. `$F7`=always impassable.

**Tile properties byte 2** (`nu--btrl`): n=NPC can move, u=always face up, b/t/r/l=directional passability.

### Debugging invisible blocks

Check in order: (1) NPC objects $10-$2F enabled at target tile, (2) character objects $00-$0F with tile position ($13-$14) at target tile, (3) tile passability via $B6-$B9. A desynced character (rendering pos != tile pos) is the hardest to spot — look for enabled objects where offsets $02-$07 don't match $13-$14.

---

## Ruination Mode - Mapping Algorithm Analysis

### Overview

The ruination mapping algorithm in `event/ruination.py` constructs a procedurally generated dungeon with **3 branches** from a central hub (Narshe school). Each branch terminates at a "terminus" room providing access to Kefka's Tower.

### Algorithm Phases

1. **Pre-Planning** (`pre_plan_character_acquisition`): Determines which characters will be obtained and ensures sufficient reward capacity before generation begins.

2. **Initialization** (`__init__`): Creates 3 hub rooms, assigns termini, distributes starting party's areas to branches.

3. **Main Generation Loop** (`generate_map_with_characters`): Iteratively extends branches via `extend_branch_path()`, processes rewards, distributes new areas when characters are obtained.

4. **Finalization** (`finalize_map`): Closes all remaining connections (see detailed section below)

### Location-Aware Branch Extension Algorithm

The `extend_branch_path()` method uses a **location-aware** algorithm that understands the branch's topology:

**Branch Regions:**
- **HUB (level 0)**: The central room connected to Narshe school - player can always return here
- **UPSTREAM (level -1)**: Rooms connected TO the hub via pits (forced connections only)
- **DOWNSTREAM (levels 1, 2, ...)**: Rooms reached by falling through traps from hub

**Core Rule**: Never make a connection that leaves no exits at the current level.

**Algorithm Steps:**
1. **Analyze topology** via `classify_topology()` - identifies hub, upstream, and room levels
2. **Check forced exits** - handle any forced connections first
3. **Collect available exits** from the deepest downstream rooms
4. **Determine exit order** - prefer traps, but adjust based on target availability
5. **Validate each connection** using:
   - `get_valid_pit_targets()` for trap→pit (checks PITO/PIDO/HUB room types, loop compression)
   - `get_valid_door_targets()` for door→door (checks DIDO/HUB room types, dead-end restrictions)
6. **Diagnose failure** if no valid connections found

**Room Type Classifications** (for unconnected rooms):
- **PITO**: Pit-in, trap-out - can extend downstream
- **PIDO**: Pit-in, door-out - can reconnect to upstream
- **DITO**: Door-in, trap-out - converts door path to trap
- **DIDO**: Door-in, door-out - forms door loops
- **DEAD_END**: Single door, no other exits - deferred to finalize_map unless has check
- **HUB**: 3+ doors+traps - can become a hub

**Dead-End Room Restriction** (added 2026-02): When the current level has only 1 door and 0 traps, dead-end rooms (with checks) are NOT valid targets. To connect to a dead-end, need either:
- At least 2 doors at current level, OR
- 1 door + 1 trap AND hub/upstream has a pit (loop can be closed)

### Stuck Branch Conditions

A branch becomes **stuck** when:

1. **No hub rooms**: Branch has no rooms with 3+ doors+traps (detected by `has_a_hub()`)
2. **extend_branch_path() fails 3 times**: Returns `(None, None)` when:
   - No exits available from active room + downstream
   - All exits fail to find matching entrances (no available doors/pits)
3. **No recovery possible**: Both reserve areas (from unplanned characters) AND EXTRA areas are exhausted

### Recovery Mechanisms

1. **Retry logic**: Up to 3 retries per branch before marking as stuck
2. **Reserve areas**: Areas from `reserve_characters` can be added to provide more hub rooms
3. **EXTRA areas**: Fallback areas (like ImperialCastle) that can be added to any branch

### Failure Modes (Now Raise Exceptions)

- `RuinationMappingError`: Raised when:
  - No branches have remaining checks
  - No reserve areas available to unstick branches
  - Insufficient characters/espers obtained after main loop
  - `finalize_map` fails on any branch
  - Unconnected exits remain after finalization

- `RuntimeError` in `finalize_map`:
  - Traps remaining with no pits (step 3)
  - Max iterations exceeded (step 6 iteration loop)

### finalize_map - Detailed Step-by-Step Reference

`finalize_map()` (in `RuinationBranch`, ~lines 1849-2580) closes all remaining connections in a branch after the main generation loop. It runs as an **iteration loop** (max 10 iterations) because connecting rooms can apply keys that unlock new traps/doors, requiring a restart from step 1.

**Pre-processing:**
- `ForceConnections()` applies pre-defined forced connections (e.g., multi-room areas that must link internally)
- `_inject_door_if_needed_for_terminus()` handles edge case where network has traps but no doors at all — finds a room with (pit, door, other_exit) and connects a trap to its pit to inject a door

**Topology model** (critical for understanding steps 1-2):
- **Hub (level 0)**: The central merged room. Player can always return here via normal doors.
- **Upstream**: Rooms connected TO the hub via one-way pits (from hub's pit → upstream room). These are accessible from the hub but can only return by falling through their own traps.
- **Downstream (levels 1, 2, ...)**: Rooms reached by falling through traps FROM the hub. These must be reconnected back to the hub/upstream to be escapable.

**Step (1): Trap-to-pit balancing** (~lines 1884-1988)
- Counts unprotected traps and pits in hub + upstream + downstream
- If traps > pits, finds rooms with excess pits (more pits than traps) and connects traps to them
- Ensures the hub doesn't have more one-way exits than one-way entrances

**Step (2): Connect downstream nodes to upstream/hub** (~lines 1989-2270)
- The core reconnection step. Each downstream room must be connected back to the hub or an upstream room so the player can escape.
- Computes a **delta** for each downstream room: `(entrance_count - exit_count)`, processes highest delta first.
- **Fix A (trap priority)**: Rooms with traps are processed BEFORE door-only rooms. This conserves doors for the terminus (step 4). Sort key: `(has_traps, delta)`.
- For each downstream room:
  - Prefer trap→upstream pit (one-way back)
  - Fall back to door→upstream door (two-way connection)
- **Fix B (door guard)**: Before making a door→door connection, counts total branch doors. If ≤ 2 remain, searches reserve areas for a **hub room** (3+ doors), adds it, connects, and restarts finalization. This prevents exhausting all doors before the terminus can be connected.
- **Converter search**: When a downstream room has a trap but upstream has no pits (or vice versa), searches for converter rooms:
  - **PIDO** (pit-in, door-out): Receives a trap, provides a door to upstream
  - **DITO** (door-in, trap-out): Receives a door, provides a trap to connect to upstream pit
  - Falls back to reserve areas if no converter exists in the network
- **Post-step-2 checks**:
  - Verifies all downstream nodes are merged into hub (raises `RuntimeError` if not)
  - **Rescue check**: If no doors remain but terminus still needs connecting, searches reserve areas for a room with (1+ trap, 1+ pit, 1+ door), adds it, and restarts finalization with a WARNING. Step 3 will connect the trap/pit, and the door becomes available for step 4.

**Step (3): Connect remaining traps to pits** (~lines 2309-2340)
- Exhaustively pairs all remaining unlocked traps with pits via `collect_network_traps_and_pits()`
- Re-collects after each connection (keys may unlock new traps)
- Falls back to reserve areas if no pits available

**Step (4): Connect the terminus** (~lines 2345-2373)
- The terminus is the dead-end room that leads to Kefka's Tower
- Uses one of the hub's remaining unprotected doors to connect to the terminus's door
- If terminus was already merged into hub (via loop compression), skip
- If no hub doors available, defers to step 6 (adds terminus to dead_ends list)

**Step (5): Pair excess hub doors** (~lines 2375-2460)
- Connects hub door pairs until `remaining_doors <= dead_ends`
- **Step 5b**: Handles orphan doors (when doors - dead_ends is odd) by finding unconnected rooms with doors to absorb the excess

**Step (6): Connect dead ends to remaining doors** (~lines 2465-2568)
- Assigns each remaining hub door to a dead-end room
- **Key safety**: Key-bearing dead ends are connected FIRST so if they unlock new traps, keyless dead ends remain available. The LAST connection must be keyless.
- If new elements are unlocked during step 6, breaks early to preserve remaining entrances, then restarts from step 1.

**Key invariant**: After finalization, the terminus MUST be merged into the hub. If not, `generate_map_with_characters()` raises `RuinationMappingError`.

**Common failure pattern**: Step (2) consuming all doors via door→door connections, leaving none for step (4) to connect the terminus. Fixes A, B, and the rescue check address this.

---

## Key/Lock Softlock Analysis & Fix (2026-02-10)

### Problem

The mapping algorithm applies keys when rooms are **connected** (during path building), but the player applies keys when rooms are **visited**. Since the player can explore rooms in any order, the algorithm's key ordering guarantee does not hold for the player. This can cause softlocks when a player enters a room (via a one-way pit) whose exits are all locked by keys found in other rooms they haven't visited yet.

The risk directly applies to **pit (one-way) entrances**, because players cannot return through pits. However, it can indirectly apply to doors as well, if the connection to the door results in a downstream node whose only exit was once locked.

### Catalog of All Keyed Rooms in RUIN_ROOM_SETS

#### Character-Keyed Locks

| Room | Area | Free Exits | Locked Exits | Key |
|------|------|-----------|-------------|-----|
| `ruin-thamasa` | VeldtCave | 2 doors, 2 pits | trap 2054 (STRAGO) | Character |
| `ruin-whelk` | Narshe | 2 doors | door 1155 (TERRA) | Character |
| `ruin-zozo` | Zozo | 5 doors | door 4608 (TERRA), key 'zr1' (CYAN) | Character |

#### Self-Unlocking Rooms (key provided by same room -- no softlock risk)

| Room | Area | Free Exits | Lock | Key Source |
|------|------|-----------|------|-----------|
| 216 | PhantomTrain | 1 door | doors 493/494 (pt1) | Self (pt1) |
| 472 | VeldtCave | 1 door | door 989 (vc1) | Self (vc1) |
| 435 | Doma | 1 door | doors 865/866 (cd3) | Self (cd3) |
| `ruin-daryl` | DarylsTomb | 1 door | door 1563 (dtboss) | Self (dtboss) |

#### Non-Character Locks with Free Exits (key from other room -- moderate risk)

These rooms always have at least one free exit. The player may be trapped if the last remaining exit in the downstream node is the initially-locked door, or if the locked door is physically impassible without the key (e.g. door 618 in Zozo).

| Room | Area | Free Exits | Locked Exits | Key Source |
|------|------|-----------|-------------|-----------|
| 202 | PhantomTrain | 9 doors | trap 2068 (pt2) | Room 212 |
| 383 | DarylsTomb | 1 door | door 1512 (dt1) | Room 392 |
| 429 | Doma | 1 door | trap 2070 (cd1+cd2) | Rooms 423, 427 |
| 531 | AncientCastle | 1 door | door 1106 (ac2) | Room 528 |
| `296r` | Zozo | 2 doors | door 618 (zr1) | `ruin-zozo` + CYAN |

#### Key-Providing Rooms (no softlock risk -- these rooms give keys, not locks)

| Room | Area | Keys Provided | Free Exits |
|------|------|-------------|-----------|
| 212 | PhantomTrain | pt2 | 1 door |
| 389 | DarylsTomb | dt2 | 1 door |
| 390 | DarylsTomb | dt3 | 2 doors, 1 trap, 1 pit |
| 392 | DarylsTomb | dt1 | 1 door |
| `301r` | Zozo | clock1 | 3 doors |
| `306r` | Zozo | clock2 | 1 door |
| 299 | ZozoTower | clock5 | 2 doors |
| `303a`/`303b` | ZozoTower | clock3 | 1 door + trap/pit |
| 304 | ZozoTower | clock4 | 2 doors |
| 423 | Doma | cd1 | 1 trap, 1 pit |
| 427 | Doma | cd2 | 1 trap, 1 pit |
| 528 | AncientCastle | ac2 | 4 doors |

#### HIGH RISK -- All Exits Locked, Key From Other Rooms

| Room | Area | Free Exits | Locked Exits | Key Sources |
|------|------|-----------|-------------|------------|
| **391** | **DarylsTomb** | **0 doors, 0 traps, 1 pit (entrance only)** | **door 795 (dt2), trap 2060 (dt3)** | **Room 389 (dt2), Room 390 (dt3)** |

### Room 391 Softlock Scenario

Room 391 is the right-half of the physical map that also contains room 390. It is the only room in ruination mode with zero initially-free exits where all exits are locked by non-character keys from other rooms. The softlock scenario:

1. During `extend_branch_path`, rooms 389 and 390 are connected to the hub. Their keys (dt2, dt3) are applied via `apply_key()`, promoting room 391's locked elements to free: door 795 and trap 2060.
2. Room 391 is now in the upstream and downstream of the hub, due to the forced connection. The algorithm closes the loop, thinking door 795 is now available.
3. Subsequently, `extend_branch_path` connects another trap in the hub to a pit-in, door-out room, creating a downstream node with one door.
4. `get_valid_door_targets` evaluates door 795 as a target. It closes the loop back to the hub, and is deemed valid.
5. Algorithm connects the downstream node door to door 795. Valid from the algorithm's perspective.
6. Player enters the hub, falls through a trap to the downstream room, walks through the door into room 391.
7. The player hasn't visited rooms 389/390 yet. Keys dt2 and dt3 haven't been obtained. Room 391's exits are still locked. **SOFTLOCK.**

### Solution: Track "Initially Locked" Exits (implemented 2026-02-11)

When `apply_key()` unlocks an element (moves it from locks to free), it is recorded in `self.initially_locked_exits` (a set on the Network class in `data/walks.py`). The algorithm then enforces these rules:

1. **`apply_key()`** (`data/walks.py`): When a door or trap is unlocked, adds it to `self.initially_locked_exits`.
2. **`get_valid_door_targets`**: Excludes doors in `initially_locked_exits` from the candidate target list (they can't serve as entrances the player can use without keys).
3. **`get_valid_pit_targets` Rule A1**: After checking `target_exits > 0`, requires at least one originally-free exit (not in `initially_locked_exits`). Rooms with only key-unlocked exits are skipped.
4. **`finalize_map` step 1**: When selecting target rooms for trap-to-pit balancing, skips rooms with no originally-free exits.
5. **`extend_branch_path` STEP 2**: When the active node is downstream (`active_level > 0`), initially-locked doors and traps are excluded from available exits. From the hub, they remain available since the player can visit key-providing rooms first.

This correctly handles all cases:
- Self-unlocking rooms (216, 472, 435, ruin-daryl) always have >= 1 free exit
- Room 391's door 795 is rejected as a door target since it's initially-locked
- Room 391 is rejected as a pit target since it has 0 originally-free exits

---

## Ruination Mode - finalize_map Debug Patterns (2026-02-09)

### Invariant: Hub must always retain entrances
When `get_valid_door_targets` Rule A2 evaluates a door merge for a room in hub/upstream, the merged result must have **both** exits (doors+traps) > 0 **and** entrances (doors+pits) > 0. A room with exits but no entrances creates downstream nodes that can never reconnect. This check only applies when `exit_room_id in hub_and_upstream`; downstream merges only need exits.

Similarly, `get_valid_pit_targets` Rule A1 must not create downstream nodes (via trap→pit to unconnected rooms) when hub+upstream already has 0 entrances.

### Invariant: Upstream is inaccessible from hub
Upstream rooms are connected TO the hub via one-way pits. The player can reach the hub FROM upstream, but NOT the reverse. Therefore:
- Upstream doors cannot serve terminus connections
- Upstream doors/traps must NOT be counted as "accessible exits" when checking if the terminus can be connected
- Only hub + downstream exits are accessible

### Step (2) terminus exit preservation
Before connecting a downstream trap to a hub/upstream pit, step (2) must check: if the terminus is still unconnected, will consuming this trap leave 0 accessible exits (hub+downstream)? If so, reject all hub/upstream pits and instead find a converter room (1+ pit, 1+ door, 1+ other exit) from the network or reserves.

### Reserve area searches must filter by self.protected
All `room_data` lookups MUST filter elements by `self.protected` before evaluating suitability:
```python
# WRONG: list(data[0])
# RIGHT: [d for d in data[0] if d not in self.protected]
```
Protected elements come from forced connections on other branches. A room may appear to have 3 pits in raw data but all 3 could be protected, causing `random.choice([])` → `IndexError`.

### Rescue rooms must be CONNECTED, not just added
`self.add_room(rid)` only adds a room to the network — it does NOT connect it to the topology. Unconnected rooms are invisible to `collect_network_traps_and_pits()` and to steps 1-3 (which only see hub+upstream+downstream). The rescue room logic must:
1. Check for existing unconnected rooms in the network first (from prior iterations)
2. Connect the hub's trap to the room's pit immediately via `self.connect()`
3. Then restart finalization so step (2) can process the now-downstream room

### collect_network_traps_and_pits already includes hub+upstream
Do not add `upstream_doors` to `len(all_branch_doors)` from `collect_network_traps_and_pits(include_doors=True)` — that method already collects from hub + upstream + downstream. Adding upstream_doors again double-counts.

### Break scope in if/else vs for/while
A `break` inside an `if/else` block but outside a `for` loop breaks the nearest enclosing loop — which may be the outer `while` rather than just exiting the `if` block. This caused step (6)'s key-unlock detection to exit the finalize_map loop entirely instead of allowing a restart from step (1).

### Key Data Structures

- **Room elements**: doors (0-1999, 4000-5999), traps (2000-2999), pits (3000-3999, 6000-7999), keys (strings), locks (dict)
- **`stuck_branches`**: Set tracking branches that can't progress
- **`branch.all_rooms_added`**: Tracks rooms including those merged via loop compression
- **`protected`**: Set of elements from forced connections that shouldn't be used for random connections

### Diagnostic Method

`_collect_mapping_diagnostics()` provides detailed state dump when failures occur:
- Rewards state (requested/obtained/available)
- Per-branch state (active room, terminus, hub status, check rooms, dead ends, element counts)
- Areas state (used areas, keychain, locked rewards)
- Troubleshooting hints

---

## Ruination Mode - Party Formation & Away-Party System (2026-02)

### Overview

The ruination hub (Narshe school, map 0x068) allows the player to form up to 3 parties and send them down separate branches. The ghost NPC triggers party reform. Parties that leave the hub through branch doors are marked "away" and their characters become unavailable for new party formation until they return.

### Key RAM / Event Addresses

| Address | Purpose |
|---------|---------|
| `$1850+char` | Party assignment bitmask per character. Bit 0 = party 1, bit 1 = party 2, bit 2 = party 3 |
| `$1A6D` | Active party mask (0x01, 0x02, or 0x04) |
| `$1E9C` bits 1-3 | `PARTY_1/2/3_AWAY` event bits (0x0e1-0x0e3) |
| Event word 2 (`$1FC6`) | `CHARACTERS_AVAILABLE` counter |
| `$1EDE-$1EDF` | `character_available` bitfield (chars 0-7 in $1EDE, 8-13 in $1EDF) |

### Custom Event Opcodes (instruction/field/custom.py)

| Opcode | Class | Purpose |
|--------|-------|---------|
| `0x66` | `MarkActivePartyAway` | Sets PARTY_N_AWAY bit, clears character_available for party members, decrements CHARACTERS_AVAILABLE. Idempotent. Fired by event tiles on branch door exits. |
| `0x67` | `RestoreActivePartyAvailable` | Clears PARTY_N_AWAY bit, restores character_available, increments CHARACTERS_AVAILABLE. Idempotent. Fired by hub entrance event when a party returns. |
| `0x68` | `RemapPartiesToFreeSlots` | Remaps $1850 party assignments from SelectParties slots (always 1..count) to actual free slots. Uses character_available to distinguish new from away characters. |

### Party Formation Flow (event/narshe_wob.py, reform_src)

**Step 1 - Determine max new parties:**
```
free_slots = 3 - count(PARTY_N_AWAY bits set)
max_new = min(free_slots, CHARACTERS_AVAILABLE-based cap)
```
- 0 away → up to 3 new parties (subject to character count)
- 1 away → up to 2 new parties
- 2 away → forced to 1 new party (no dialog)

The branching checks each combination of PARTY_1/2/3_AWAY to classify into MAX_1_NEW, MAX_2_NEW, or MAX_3_NEW, then intersects with CHARACTERS_AVAILABLE.

**Step 2 - Select parties:**
1. `remove_available_addr` strips available (non-away) characters from all parties, preserving away characters' $1850 assignments
2. `REFRESH_CHARACTERS_AND_SELECT_N_PARTIES` deletes all entities, creates entities for available characters only, calls `SelectParties(count)` (vanilla opcode 0x99)
3. SelectParties always assigns to slots 1..count regardless of away parties

**Step 3 - Remap to free slots (RemapPartiesToFreeSlots, opcode 0x68):**
1. Reads PARTY_N_AWAY bits from $1E9B to build a free_slots mapping in scratch RAM ($e8-$ea). For each party not away, stores its mask (0x01/0x02/0x04) at the next index.
2. Iterates through all 14 characters. For each with `character_available` set AND `$1850+char != 0`:
   - If $1850 == 0x01: replace with free_slots[0]
   - If $1850 == 0x02: replace with free_slots[1]
   - If $1850 == 0x04: replace with free_slots[2]
3. Characters with character_available clear (away parties) are untouched.

Example: P1 away → free_slots = [0x02, 0x04]. SelectParties(2) assigns to slots 1,2. Remap changes 0x01→0x02 and 0x02→0x04.

**Step 4 - Placement:**
Event script branches on away bits to determine which specific slots to use for `SetPartyMap(N, map_id)` and `SetParty(N)`, then calls position subroutines:
- 1 party: center position (109, 49), Y-switching disabled
- 2 parties: center + upper-right (110, 48), Y-switching enabled
- 3 parties: center + upper-right + lower-right (110, 50), Y-switching enabled

The last party placed becomes active (placed last so SetParty sticks).

### Why character_available Is the Discriminator

When away party P1 occupies slot 1 ($1850 = 0x01) and SelectParties also assigns a new party to slot 1 ($1850 = 0x01), both old and new characters share the same $1850 value. The `character_available` bit distinguishes them:
- Away characters: character_available = 0 (cleared by MarkActivePartyAway)
- Newly assigned characters: character_available = 1

The remap only touches characters with character_available set, leaving away characters' $1850 intact.

### Problems This Architecture Solved

1. **Slot collision**: Without remap, the new party overwrites $1850 for the same slot number as an away party. When the away party returns, RestoreActivePartyAvailable can't find its characters because their party bit was cleared by the overwrite.

2. **Count overflow**: Without the cap, a player could create more parties than available slots (e.g., 3 new + 1 away = 4 total, but only 3 slots exist with SetPartyMap/SetParty support).

### Branch Character Recruitment (2026-02)

When a party on a branch recruits a character, the standard party select flow would show ALL available characters (including hub characters) and assign to slot 1. Two new opcodes fix this:

| Opcode | Class | Purpose |
|--------|-------|---------|
| `0xec` | `SetupBranchRecruit` (alias `SetupBranchPartySelect`) | Takes character ID argument. If active party is away: saves party mask to $e7, zeros character_available, re-sets it only for current party members and the new recruit, clears $1850 for party members (clean slate for SelectParties), recomputes CHARACTERS_AVAILABLE. No-op if not on branch. |
| `0xed` | `FinalizeBranchRecruit` (alias `FinalizeBranchPartySelect`) | No argument. If $e7 is non-zero: remaps slot 1 → saved party mask ($e7), recomputes character_available as `recruited AND NOT in_away_party`, recomputes CHARACTERS_AVAILABLE count, clears $e7. No-op if $e7 is zero. |

**Execution flow (branch recruitment):**
```
RecruitCharacter(char)       → sets recruited + available for new char
SetupBranchRecruit(char)     → restricts select screen to party + new char
Call(REFRESH_CHARACTERS_AND_SELECT_PARTY) → shows party select screen
FinalizeBranchRecruit()      → remaps slot, restores correct available state
```

**After finalization**, the state is correct:
- Selected chars: in original party slot, party is still away → character_available=0
- Unselected former party members: $1850=0 (removed by SelectParties) → character_available=1 (available at hub)
- Unselected new recruit: $1850=0 → character_available=1 (available at hub)
- Hub characters: untouched $1850, character_available=1
- Other away parties: untouched, character_available=0

**Two integration patterns:**
1. Events using `RecruitAndSelectParty(char)` (35+ events): Automatically wrapped in `instructions.py` when `args.ruin` is set
2. Events with separate `RecruitCharacter` + `Call(REFRESH)` (6 events): Individually modified with branch-aware refresh subroutine (baren_falls, lone_wolf, mt_kolts, floating_continent, lete_river, narshe_moogle_defense)

---

## SelectParties Inventory Corruption Bug & Fix (2026-04)

### Symptom

After certain Narshe ghost-NPC reform-parties menus, a phantom Dirk (item $00) appeared in inventory slot 23 (SRAM $1880) and/or a phantom Cat Hood (item $80) in slot 24 (SRAM $1881). Corruption was reproducible and tied to specific pre-menu party configurations with away parties.

### Root Cause: C0/6F67 Leader-Finder

Vanilla opcode 0x99 (SelectParties, body at C0/B035) calls a post-menu leader-finder subroutine `C0/6F67`. The subroutine's job is to update the four "leader offset" cache slots ($07FB/$07FD/$07FF/$0801) and active-party leader ($0803). It does this by:

1. Snapshotting entry `$0803` into zero-page `$1E`.
2. Using SNES hardware divide ($4204/$4206, result `$4214`) to convert `$1E / 41` → character index in Y.
3. Writing the active-party mask to SRAM: `STA $1850,Y` at **C0/7049**.
4. Searching the 14 character objects for the first match belonging to the newly-selected party, stashing the found offset at `$07FB`.
5. Loading `$07FB`, dividing by 41 again, and writing the new party mask with another `STA $1850,Y` at **C0/7062**.

The vanilla code assumes Y is always a character index in `[0, 13]`. That assumption breaks when the divisor input is a **sentinel** value:

| Offset | Decimal | Meaning | `/ 41` quotient |
|--------|---------|---------|-----------------|
| `$07B0` | 1968 | camera object ($30) | **48** |
| `$07D9` | 2009 | empty/vacant object ($31) | **49** |
| `$0867..$106F` | 2151..4207 | valid char slots $00..$0D | 0..13 |

A quotient of 48 or 49 directs the `STA $1850,Y` into `$1850+48=$1880` or `$1850+49=$1881` — inventory slots 23 and 24. The low byte of A at that point is the party mask being written (0x01/0x02/0x04 → Dirk/Cat Hood variants).

### How a Sentinel Reaches the Divider

- **Entry site (C0/7049)**: Uses `$1E` = snapshot of entry `$0803`. `$0803` holds the *active-party* leader offset. If the map was entered without a true active party (e.g., the hub just loaded after returning from a branch and the last placed party's leader wasn't yet cached properly), `$0803` can still hold a sentinel.
- **New-leader site (C0/7062)**: Uses `$07FB`. The SelectParties body (C0/B038) seeds `$07FB` from `$0803` *before* the menu runs. If the subsequent search loop in C0/6F67 finds no character belonging to party 1 (which happens when the menu produced a party assigned to a different slot, or when the away-party machinery has cleared the expected characters), `$07FB` retains that pre-menu sentinel.

In ruination mode, both conditions are routinely produced by the reform flow in `event/narshe_wob.py` (away parties + `RemapPartiesToFreeSlots` remapping slot 1 to a different mask). Neither condition occurs in vanilla flows (e.g., Phoenix Cave's `SelectParties(2)`), so the bug was latent until ruination exercised it.

### Fix: Minimal Range Check (`instruction/field/custom.py`)

Two 3-byte in-place patches replace each `STA $1850,Y` with `JSR safe_store`, where `safe_store` is a small tramp:

```
safe_store:
    CPY #$000E      ; Y is 16-bit (event engine invariant)
    BCS .skip
    STA $1850,Y
.skip:
    RTS
```

The patch is applied only when `args.ruination_mode is not None`. Because event-engine ASM entry to C0/6F67 has `REP #$10` in effect, `CPY #$000E` is a 16-bit compare and correctly distinguishes 0-13 from 48/49. When the quotient is valid the write is identical to vanilla; when it is a sentinel the write is skipped.

### Why the Minimal Approach

An earlier attempt tried to sanitize `$1A6D` / `$07FB` / `$0803` and save/restore `$1E9C` around SelectParties via new hooks on the gen. act. 99 body. That broke unrelated party state (leader-offset caches went stale, Y-switching regressed). Root-causing the corruption to just these two store instructions and guarding only those writes was safer: every register, zero-page, SRAM slot, and control flow path outside the two patched instructions stays byte-identical to vanilla.

### Code Location

- `instruction/field/custom.py` — `_leader_finder_safe_store_mod()` (gated on `args.ruination_mode is not None`)
- Patched ROM addresses: **C0/7049** (first store) and **C0/7062** (second store)
- Safe-store tramp: allocated in Bank.C0 via `Write(Bank.C0, ..., "leader-finder safe store")`

### Testing Notes

- Detection method: write a debug hook that copies `$1880`/`$1881` to a known scratch address and inspect after reform-parties menu invocations.
- Corruption was reproduced by reform sequences involving at least one away party; the vanilla flow (no away parties, no RemapPartiesToFreeSlots, no branch recruitment) does not trigger it because the pre-menu `$0803` always refers to a real character object.

---

## Persistent Raft Graphic After Re-riding the Magitek Minecart (2026-06)

### Symptom

In ruination / door-rando, a playtester took the Returner's Hideout raft exit, which connected (via the shuffled door graph) to the Magitek minecart. On a later pass the party was drawn **persistently on a raft** in Vector. Cosmetic only (gameplay unaffected, fixed by reforming the party), but undesirable.

### Background: how raft state is normally handled

Whether the party is drawn on a raft is a persistent field-RAM sprite state (vehicle `$60`). `data/transitions.py` `Transitions.mod()` is the single source of truth for correcting it across a shuffled connection: when `t.exit.is_on_raft != t.entr.is_on_raft` it appends a `Call` to one of two vanilla subroutines into the `en_patch` byte list:

- **CB/050F** — place party on raft (`field.Call(0xb050f)`, bytes `b2 0f 05 01`)
- **CB/04AA** — remove raft / set vehicle to "none" (`field.Call(0xb04aa)`, bytes `b2 aa 04 01`). Only changes the vehicle; leaves visibility untouched, so it is safe to call even when the party is *not* on a raft.

`en_patch` (raft fix, entity-unhide, song-override, screen-hold, world-bit, parent-map, `require_event_bit`) is inserted into `src_end` — i.e. it only runs on the **default, randomized destination** of a transition.

### Root cause

The Magitek minecart exit (event tile `2028`) is the only entry in `exit_event_patch`/`entrance_event_patch` (`data/event_exit_info.py`) that introduces **alternate fixed destinations**. `minecart_event_mod()` injects two completion-gated branches *before* the default load:

- `DEFEATED_CRANES` (`0x06b`) set → `go_to_vector` (Vector outdoors `0xf2`)
- `RODE_MINE_CART_MAGITEK_FACTORY` (`0x069`) set → `go_to_mtek3_vector` (Vector outdoors `0xf0`)
- otherwise → fall through to the randomized destination (the only path `en_patch` is attached to)

Both `go_to_*` blocks build their **own** `LoadMap … ShowEntity … FadeInScreen … Return` tail and `Return` before reaching `src_end`, so they **bypass `en_patch` entirely**, including the raft correction. When the minecart's randomized destination is an on-raft location (Lete River / Returner's Hideout raft), the default path correctly placed the party on a raft (CB/050F via `en_patch`); once the party was carrying the raft graphic and re-rode the cart with one of those bits set, control diverted to a Vector branch that never removed the raft → stuck raft sprite.

(Note: in door rando the part of the vanilla minecart event that sets `0x069` lives *after* the LoadMap split — CC/8148 — so it is replaced by the randomized destination; the bits that actually drive these branches are set by the crane scene / the `DEFEATED_NUMBER128` revisit hook in `event/magitek_factory.py:minecart_mod`.)

### Fix (`data/event_exit_info.py`, `minecart_event_mod`)

`go_to_vector` and `go_to_mtek3_vector` always land in Vector, which is never an on-raft map, so unconditionally clear the raft graphic by inserting `field.Call(0xb04aa)` immediately after each block's `LoadMap`. Verified in a generated ROM (ruination, `-s 12345`, minecart used as exit `2028 -> 3026`): both Vector blocks now read `6b f2/f0 30 3e 0d c0  b2 aa 04 01  41 31  45 96 fe` (LoadMap, **Call CB/04AA**, ShowEntity, Refresh, FadeIn, Return).

### Generalizable lesson

Any event patch that creates an alternate `LoadMap`+`Return` destination (rather than just inserting instructions into the default tail) sidesteps **all** of `Transitions.mod()`'s common `en_patch`/`ex_patch` state corrections. Such custom destinations must reproduce whatever state the destination map requires. `minecart_event_mod` was the only such patch in the transitions framework; the same pattern occurred twice within it (both Vector branches), and both were fixed.

---

## Ruination Mode - Duplicate Event Tiles for Reverse Entrances (2026-02)

In vanilla FF6, some maps have animation event tiles (e.g., Vargas shadow appearances on Mt Kolts) placed near only one entrance. In ruination mode, players may enter rooms from the opposite side, missing the trigger entirely.

**Fix pattern**: In the event file's `ruination_mod()`, copy the event tile to a second location near the alternate entrance:
```python
old_event = self.maps.get_event(map_id, orig_x, orig_y)
new_event = MapEvent()
new_event.x = new_x
new_event.y = new_y
new_event.event_address = old_event.event_address
self.maps.add_event(map_id, new_event)
```

**Mt Kolts fixes** (`event/mt_kolts.py`):
- Map 0x060: (14,12) → duplicate at (11,8)
- Map 0x060: (16,22) → duplicate at (21,21)
- Map 0x061: (34,24) → duplicate at (47,10)

---

## Ruination Mode - Conditional Area Checks

After `ruin_map.generate_map_with_characters()` is called, `ruin_map.AreasUsed` contains all mapped areas as a dict of `{'AreaName': branch_id}`.

**To check if an area is mapped:**
```python
if 'SouthFigaro' in ruin_map.AreasUsed:
    # South Figaro is accessible in this seed
```

**Area names** (from `RUIN_ROOM_SETS` in ruination.py): `'SouthFigaro'`, `'Nikeah'`, `'Kohlingen'`, `'Jidoor'`, `'Veldt'`, `'Thamasa'`, `'Mobliz'`, `'Maranda'`, `'Albrook'`, `'Vector'`, `'Zozo'`, `'Narshe'`, `'OperaHouse'`, `'FigaroCastle'`, etc.

**For "which branch is area X on?" queries**, use `args.ruination_areas_used` (populated from `ruin_map.compute_actual_areas_used()`, NOT `AreasUsed`). `AreasUsed` records the branch an area was *distributed* to, which can be wrong if the area's rooms ended up in another branch (forced_same_branch, shared rooms, or `CHARACTER_AREAS['ALL']` pre-claim) or if rooms were added but never connected. See "Branch Area Detection for Narshe Clues".

---

## Ruination Mode - Patching NPC Events

To disable an NPC's dialog choice and make them just display a message:

```python
# Patch event to: display dialog (4B), return (FE)
event_bytes = bytes([0x4B, dialog_id & 0xFF, dialog_id >> 8, 0xFE])
rom.set_bytes(event_addr, event_bytes)
```

**Finding NPC event addresses**: Use `maps_data.json` - each map's `npcs` array contains `event_address` for each NPC. The event address is the offset from 0xCA0000 (e.g., `"event_address": "0x77d7"` = ROM address 0x0A77D7).

See `disable_chocobo_stables()` and `fix_ferry_connections()` in `event/ruination.py` for examples.

---

## Ruination Mode (`-ruin`) - Detailed Architecture

Ruination Mode creates a roguelike-style dungeon with three independent branches emanating from a central hub.

### Core Concept

- **Hub**: Narshe School (3 exits)
- **Three Branches**: Each branch connects hub → starting area → Kefka's Tower (left/middle/right)
- **Progression**: Finding characters unlocks new areas, distributed across all branches
- **Goal**: Collect required characters/espers before accessing Kefka's Tower via airship

### Key Files and Functions

**event/ruination.py** (~4400 lines) - Main implementation
- `ruination_map` - Orchestrates three branches, distributes areas, assigns rewards
- `RuinationBranch(Network)` - Individual branch management
- `pre_plan_character_acquisition()` - Pre-plans character distribution
- `generate_map_with_characters()` - Main loop: extends branches until objectives met
- `extend_branch_path()` - Adds one connection to a branch
- `finalize_map()` - Connects remaining loose ends

**event/events.py** - Entry point
- `ruination_mod()` - Populates `ROOM_REWARD` with actual Reward objects, calls map generation

**data/rooms.py** - Custom ruination rooms (prefix `'ruin-'`)
- `ruin_hub`, `ruin_terminus_1/2/3`, etc.

---

## Event Exit Info - Detailed Data Structures

Event tiles (IDs 1500-2000) that act as doors need connection data at runtime. Some are vanilla tiles with existing event code in the ROM; others are new "switchyard" tiles created for door randomization/ruination.

### Data Structures

- **`event_exit_info`** (data/event_exit_info.py): Contains `[event_addr, length, split, state, desc, location, method]` for each event tile. Switchyard tiles have `event_addr = None` because they don't exist in vanilla ROM.

- **`event_door_connection_data`** (data/map_exit_extra.py): Contains door-style connection data `[dest_map, dest_x, dest_y, ...]` for event tiles acting as doors.

- **`exit_data`** (data/map_exit_extra.py): Maps door IDs to their vanilla partners `[partner_id, description]`.

### Runtime Update Flow (maps.py:write)

1. **Build `used_events`**: Collects all event tile IDs that need their `event_exit_info` updated, INCLUDING vanilla partners of event tiles whose partners are also event tiles.

2. **Update addresses**: For each event in `used_events` with `event_addr = None`, find the event at its switchyard location and update `event_exit_info[e][0]` with the actual address.

3. **Transitions**: When `Transitions` creates entrance `EventExit` objects, if the entrance is an event tile (1500-2000) and its vanilla partner is also an event tile, it uses `use_event_info=partner_id` to get the partner's event code. **The partner's `event_exit_info` must have been updated first.**

---

## Finding NPCs in Reference Data - Detailed Procedure

Reference JSON files are located in the remote `claude_ruination` branch under `claude_reference/`:
- `npcs_raw.json` - All NPCs with properties (index, x, y, sprite, event_byte, event_bit, etc.)
- `maps_data.json` - Maps with their NPCs listed (includes map-local index)

**To find an NPC**:
1. Locate the map in `maps_data.json` by map_id (e.g., Narshe WoB = 0x14 = 20 decimal)
2. Find the NPC in that map's `npcs` array by position (x, y) or other properties
3. Note the map-local index (array position) and sprite properties
4. Calculate `npc_id = map_local_index + 0x10` for use in `get_npc()`
5. Cross-reference global index in `npcs_raw.json` for full property details

---

## Finding Map IDs by Name - Detailed Example

**Example**: Sabin's House

1. Search `data/map_exit_extra.py`:
   ```
   grep "Sabin.*House" data/map_exit_extra.py
   ```
   Reveals: `361: [362, "Sabin's House Door Outside"]` - door 361 leads to door 362

2. The "Door Outside" (361) is the entrance going INTO the building

3. Look up in `exits_raw.json`:
   ```
   grep -A5 '"index": 361' claude_reference/exits_raw.json
   ```
   The `dest_map` field shows: `"dest_map": 94` = Interior map ID

- Door 361 ("Outside") → `dest_map: 94` = Interior map ID
- Door 362 ("Inside") → `dest_map: 93` = Exterior map ID

---

## FF6 Text Encoding Types

The codebase has three text encoding types in `data/text/`:

- **TEXT1** (`text1.py`): DTE (Dual-Tile Encoding) compressed format. Used for dialog text and **location names**. Many byte values represent two characters for compression.

- **TEXT2** (`text2.py`): Simple encoding for item names, spell names, esper names, etc. Single bytes map to single characters. Letters: A-Z = 0x80-0x99, a-z = 0x9A-0xB3, 0-9 = 0xB4-0xBD, space = 0xFE.

- **TEXT3** (`text3.py`): Menu/battle text encoding. Similar structure to TEXT2 but with different special codes.

**Usage**: Use `data.text.get_string(bytes, text.TEXT1)` or `text.TEXT2` to decode ROM data. Use `data.text.get_bytes(string, text.TEXT1)` to encode for writing.

**ROM Data Types** (from ff3infov2.txt):
- `TXT1` = TEXT1 encoding (DTE compressed)
- `TXT2` = TEXT2 encoding (simple)

---

## Local Character Gating (Door Rando)

In standard (non-door-rando) modes, character gating is enforced at the area level (e.g., you can't enter Mt. Zozo without Cyan). In door rando modes, the player can reach any room through randomized connections, so gating must be enforced **locally** — inside the room where the reward is given.

### Implementation Patterns

There are three complementary mechanisms:

**1. `entrance_door_patch` (for entrance-event-based checks)**
Used when the reward is triggered by an entrance event (map load). The patch is a static method on the event class that takes `args` and returns event code. When `args.character_gating` is true, use `BranchIfAll` to combine the "not finished" and "character recruited" checks. **Do NOT terminate the returned source with `field.Return()`** — see "entrance_door_patch must fall through" below for why:
```python
@staticmethod
def entrance_door_patch(args):
    CYAN = 2
    if args.character_gating:
        src = [
            field.BranchIfAll([event_bit.FINISHED_MT_ZOZO, False,
                               event_bit.character_recruited(CYAN), True], continue_addr),
            # No Return() — fall through to caller's LoadMap on the miss path
        ]
    else:
        src = [
            field.BranchIfEventBitClear(event_bit.FINISHED_MT_ZOZO, continue_addr),
        ]
    return src
```
In `event_exit_info.py`, store as a callable (not called): `mt_zozo_cliff_check = MtZozo.entrance_door_patch`. The `maps.py` consumption sites detect callables and pass `self.args` at runtime.

**2. In-event gating (for boss/NPC-triggered checks)**
Used when the reward is behind a boss fight or NPC interaction triggered by an event tile. Add the gate check to the existing door-rando event code. Pattern: check with `BranchIfAll`, and if the gate character is missing, play a rejection animation and return. Example rejection animation (from Wrexsoul):
- `FlashScreen(Flash.WHITE)` + `PlaySoundEffect(174)`
- `DisableWalkingAnimation`, `SetSpeed(FAST)`, `AnimateAttacked`, `Move(DOWN, 2)`
- `EnableWalkingAnimation`, `Turn(UP)`, `FreeScreen`, `Return`

**3. `ruin-*` room variants in `data/rooms.py`**
Create a copy of the room with the reward exit locked behind a character gate. This tells the ruination mapping algorithm that the exit is only available when the character is recruited. Format: move the gated exit from the normal list to the lock dict:
```python
# Original:
193 : [ [456], [2074], [ ], 1],  # Doma Dream Throne Room
# Ruination variant with Cyan gate:
'ruin-wrexsoul' : [ [456], [ ], [ ], [], {'CYAN': [2074]}, 1],
```
Then update `ROOM_REWARD` and `RUIN_ROOM_SETS` in `event/ruination.py` to reference the new room key.

### Progress Tracker

Locally gated (ruination-specific, added for door rando):
- [x] **TERRA — Lete River** (LeteRiver3): Boss not fought if Terra not recruited
- [x] **LOCKE — South Figaro Cave** (room 104): Boss not fought if Locke not recruited
- [x] **CYAN — Mt. Zozo** (room 256): `entrance_door_patch` in `event/mt_zozo.py`
- [x] **CYAN — Doma WOR Wrexsoul** (ruin-wrexsoul): In-event gate in `event/doma_wor.py` + room variant
- [x] **SHADOW — Floating Continent** (ms-wob-1556): Need Shadow to land on floating continent
- [X] **SHADOW — Veldt Cave WOR** (room ruin-cotv):  Interceptor animation if Shadow not recruited
- [x] **EDGAR — Ancient Castle** (room 532): Statue unresponsive if Edgar not recruited
- [x] **EDGAR — Figaro Castle Engine Room** (ruin-figarocastle): Can't enter engine room if Edgar not recruited
- [x] **SABIN — Imperial Camp** (dc-1501): Already locally gated in door rando mode
- [x] **SABIN — Mt. Kolts** (room 151): Vargas doesn't attack if no Sabin
- [x] **SABIN — Phantom Train** (ruin-202): NPC in caboose hidden & can't fight boss if Sabin not recruited
- [x] **CELES — Magitek Factory 1** (ruin-mtek1): Can't fight boss if Celes not recruited
- [x] **CELES — Magitek Factory 2** (ruin-mtek2): Can't fight boss if Celes not recruited
- [x] **STRAGO — Burning House** (ruin-bh): Can't fight boss if Strago not recruited
- [x] **RELM — Owzer Mansion** (room 284): Locally gated at Chadarnook painting interaction (tint black + rejection animation)
- [x] **SETZER — Daryl's Tomb** (ruin-daryl): Can't fight boss if Setzer not recruited
- [x] **MOG — Narshe Moogle Defense** (room 65): Collapsed Terra NPC hidden if Mog not recruited via map entrance event (narshe_moogle_defense.py:657-671, ruination_start_mod). Non-ruin path gates via Arvis NPC (lines 278-282).
- [X] **MOG — Lone Wolf** (ruin-lonewolf):  Gated in ruin-narshe.  Mapping logic protected by logical reward room. 
- [x] **GOGO — Zone Eater** (room 363): NPC hidden if Gogo not recruited
- [x] **UMARO — Umaro's Cave** (room 368): Event at Bone statue gated

Locally gated in standard Worlds Collide (no ruination-specific work needed):
- [x] **TERRA — Whelk** (ruin-whelk)
- [x] **TERRA — Zozo** (313)
- [x] **TERRA — Mobliz WOR** (ms-wor-52)
- [x] **LOCKE — Narshe WOR** (ruin-narshe)
- [x] **LOCKE — Phoenix Cave** (ms-wor-1554)
- [x] **SHADOW — Gau Father House** (ms-wob-14)
- [x] **EDGAR — Figaro Castle Throne** (ruin-figarocastle)
- [x] **SABIN — Baren Falls** (ruin-baren-falls)
- [x] **SABIN — Collapsing House** (ms-wor-51)
- [x] **CELES — South Figaro** (ms-wor-58)
- [x] **CELES — Opera House** (ms-wob-40)
- [x] **STRAGO — Fanatic's Tower** (ms-wor-69)
- [x] **STRAGO — Ebot's Rock** (ms-wor-78)
- [x] **RELM — Esper Mountain** (room 488)
- [x] **SETZER — Kohlingen** (ms-wor-59)
- [x] **GAU — Veldt** (wor-veldt)

Not yet locally gated (need gating or decision to ungate):
- [ ] **CYAN — Doma WOR stooges** (room 429): Doma Dream 1
- [ ] **CYAN — Doma WOR throne** (room dc-76): Doma Dream 3 (currently gated by Wrexsoul event)
- [ ] **CELES — Magitek Factory 3** (ruin-mtek3)
- [ ] **GAU — Serpent Trench** (ruin-st-exit)

Not currently used in ruination mode:
- [-] **CYAN — Doma WOB** (ms-wob-18): Doma Siege

---

## Limited Inventory Shops (`-sli` flag)

Pack-based purchasing system for ruination mode. Each shop item slot sells a fixed-size "pack" (1-15 items) and can only be bought once. Tracked via 1 bit per item slot in Save RAM. After purchase, remaining items are compacted (no gaps) in the buy list.

### Original FF6 Buy Menu Code (Bank C3)

**State Machine (driven by jump table at B792):**

| State | Address | Description |
|-------|---------|-------------|
| 25 | B49B | Main shop menu — BUY/SELL/EXIT cursor |
| 26 | B4BD | Buy item list — navigate items, A=select, B=back |
| 27 | B505 | Order menu — quantity ±1/±10, A=confirm, B=cancel |
| 28 | B60E | Post-purchase delay (32 frames), then return to buy list |

**Key Routines:**

| Address | Description |
|---------|-------------|
| B466 | Shop menu initialization |
| B760 | Exit submenu, return to main shop menu |
| B792 | Handle BUY/SELL/EXIT choice via jump table at B79A |
| B7A3 | Initialize buy menu (calls B8A0, B8A9, B986, BCFD) |
| B7B3 | Return to buy list after purchase (redraws via B986, sets state 26) |
| B7BC | `JSR $B986` — draw all buy text (hooked for redraw trampoline) |
| B7E6 | Check GP and stock before entering order menu |
| B82F | Set buy limit: `$6A = 99 - owned_quantity` |
| B850 | Enter order menu (set state 27, draw "How many?") |
| B87D | Set exit delay: state→28, 32-frame timer |
| B986 | Draw all buy text; item list loop at B998-B9EC |
| B9AF | `LDA $C47AC0,X` — load shop item ID from ROM |
| BA0C | Define item price with shop type multiplier, store to $7E9F09 |
| BB53 | Get order value: price × quantity ($28) |
| BB81 | Hardware multiplication via SNES registers $4202/$4203/$4216 |
| BBAE | Draw order size and value |
| BBC0 | Draw order size (reads $28, displays 2 digits) |
| BC84 | Draw quantity owned |
| BC92 | Define $64 (quantity in stock) |
| BCA8 | Draw quantity worn |
| BCFD | Build sign list (E/^/v/= equip indicators) |
| BFC2 | Get selected buy item from `$7E9D89[$4B]` |
| BFD3 | Draw shop title, compute `$67 = shop_num × 9` |
| B5B7 | Execute purchase (find/create inventory slot, add qty) |
| B5EA | Reduce GP (3-byte subtraction from $1860-$1862) |

**Key RAM Variables:**

| Address | Description |
|---------|-------------|
| $0201 | Shop number (0-85) |
| $28 | Buy/sell quantity |
| $4B | Cursor slot (selected item index 0-7) |
| $4E | Cursor position (visual position in list) |
| $54 | Cursor limit (number of items in list) |
| $64/$65 | Qty in stock / qty worn |
| $67-$68 | Shop index (`shop_num × 9`, 16-bit byte offset into shop data) |
| $69/$6A | Total owned / buy limit |
| $E6 | List size counter |
| $F1-$F3 | Price/order value (also $F1 = current menu slot in load loop) |
| $1860-$1862 | Party gold (3 bytes, little-endian) |
| $1869+Y | Item inventory IDs (256 slots) |
| $1969+Y | Item inventory quantities |
| $7E9D89+X | Menu display list (item IDs) |
| $7E9F09+X | Menu display prices (16-bit per item) |

### Implementation Overview

**Files modified/created:**
- `args/shops.py` — `-sli` / `--shop-limited-inventory` flag
- `data/shops.py` — Pack size computation, Save RAM pointer assignment, ROM table writing, compact_init subroutine, redraw trampoline
- `menus/buy.py` — NEW: BuyMenu class with 4 ASM hooks
- `menus/menus.py` — BuyMenu instantiation
- `event/events.py` — Integration call in `ruination_mod()`

### Data Tables (ROM)

| Table | SNES Address | ROM Address | Size | Format |
|-------|-------------|-------------|------|--------|
| Pack sizes | $C47FA8 | $047FA8 | 688 bytes | 8 bytes/shop × 86 shops |
| Tracking pointers | $C48258 | $048258 | 172 bytes | 2 bytes/shop × 86 shops |

**Pack size table:** Each byte = pack size for that item slot (1-15, or 0 for empty slots).
**Tracking pointer table:** Each 16-bit word = Save RAM address for that shop's tracking byte, or $0000 for non-limited (normal) shops.

**Save RAM range:** $1E1D-$1E3F (35 bytes available, one per limited shop). Each byte tracks 8 item slots via individual bits.

### Pack Size Rules

| Category | Size | Items |
|----------|------|-------|
| Weapons, Armor, Shields, Helmets | 1 | IDs 0-162 |
| Tools, Skeans | 1 | IDs 163-175 |
| Special Relics | 1 | Economizer, Offering, Hero Ring, etc. |
| Normal Relics | 1-4 | IDs 176-230 (not special) |
| Basic Healing | 3-10 | Tonic, Potion, Fenix Down, Antidote, etc. |
| High Healing | 1-3 | X-Potion, Tincture, Ether, Tent, Remedy, etc. |
| Elixirs | 1 | Elixir, Megalixir |
| Dried Meat | 5 | Fixed |
| Other consumables | 1-3 | Everything else |

### Custom Direct Page Variables

These addresses are verified unused during shop menu operations (Bank C3 B4xx-BAxx range). Many commonly-used DP addresses ($E0, $E1, $C0-$CF, $39-$3A, etc.) are actively used by the menu system for cursor/state/window positioning and **must not** be used.

| Address | Size | Purpose |
|---------|------|---------|
| $25 | 1 byte | Compact mode flag (0=normal shop, 1=limited shop with valid compact buffers) |
| $30 | 1 byte | Limited mode flag / pack size (0=unlimited, 1-15=pack size for order menu qty lock) |
| $36 | 1 byte | Temp: tracking byte during compact_init |
| $37 | 1 byte | Temp: item ID during compact_init |
| $38 | 1 byte | Temp: original slot index in hook_buy_setup |
| $40-$41 | 2 bytes | Temp: shop_num×8 in hook_buy_setup (16-bit) |
| $42 | 1 byte | SLOT_TEMP_DP: temp for slot index or pack size |
| $60-$61 | 2 bytes | UNIT_PRICE_SAVE_DP: saved unit price (for restore after pack-price inflation) |
| $62-$63 | 2 bytes | PACK_TEMP_DP: 16-bit scratch for pack table computation / multiply results |
| $66 | 1 byte | SUBMENU_FLAG_DP: non-zero while the order submenu is open; set by the BAAB label hook, cleared by the B98F label hook; read by the qty-value hook (BCAB) to suppress repainting the "Qty: N" indicator under the submenu's window dressing |
| $78-$7F | 8 bytes | compact_items buffer (available items packed to top, rest $FF) |
| $B8-$BF | 8 bytes | slot_map buffer (display position → original shop slot index) |

**Verified safe DP addresses (from in-game testing):** $25, $30, $36, $37, $38, $40, $41, $42, $60, $61, $62, $63, $66, $78-$7F, $B8-$BF.

**⚠️ DO NOT USE $49 or $4A as scratch:** Despite being in the previous "verified safe" list, these are actually the sell menu's persistent state — `$49` is the sell menu's "Top BG1 write row" (read at C3/83F7 → `$E6`) and `$4A` is its "List scroll position" (read at C3/83F7 and C3/BBF8). The shop init at C3/B47C only zeros `$4A` once on shop entry and never re-initializes either between submenu transitions. Clobbering them inside the buy hooks causes a desync on first Sell-menu open after Buy: items draw at wrong BG1 rows (cursor appears at visual row 0 while `$4B` points to a different inventory slot). Pressing L/R fixes it because the scroll handler at C3/1F64 recomputes both registers. Earlier versions of the `-sli` hooks used `$49-$4A` as PACK_TEMP_DP and hit this bug; the fix is to use `$62-$63` instead.

### Item Compaction System

When items are purchased in limited shops, they are removed from the display. Without compaction, this leaves blank rows (0xFF) in the middle of the item list, causing: unreachable items below gaps (cursor limit is correct but items aren't contiguous), and character animation glitches when selecting blank rows.

**compact_init subroutine** (written to Bank C3 by `data/shops.py` `_build_compact_init_asm()`):
1. Clears compact buffers ($78-$7F and $B8-$BF) to $FF
2. Checks tracking pointer table — if $0000, this is a normal shop → sets $25=0, returns
3. For limited shops: sets $25=1, loads tracking byte from SRAM
4. Scans original slots 0-7: for each non-empty, non-purchased item, writes item ID to compact_items[write_pos] and original slot index to slot_map[write_pos], increments write_pos
5. Result: available items are packed into $78-$7F[0..N-1], rest are $FF

**Redraw trampoline** (hooks `JSR $B986` at B7BC via Reserve 0x3B7BD-0x3B7BE):
- Runs on every buy list redraw (initial entry AND post-purchase returns)
- Calls compact_init to rebuild buffers with current tracking state
- Checks if all items purchased ($25=1 and $78=$FF): if so, pops JSR return address and `JMP $B760` to exit to main shop menu
- Otherwise falls through to `JMP $B986` (draw all text)

### ASM Hooks (menus/buy.py)

#### Hook 1: Load Item (hook_load_item)
- **Original:** `LDA $C47AC0,X` at C3/B9AF (4 bytes)
- **Replaced with:** `JSL <custom>` (4 bytes, exact fit)
- **Reserve:** 0x3B9AF-0x3B9B2
- **Purpose:** In compact mode, reads from compact_items buffer instead of ROM. Items are already packed with no gaps.
- **Logic:** If $25=0 (normal shop), load from ROM as usual. If $25≠0 (compact mode), load compact_items[$F1] via `LDA $78,X` where X=$F1.

#### Hook 2: Buy Setup (hook_buy_setup)
- **Original:** `JSR $B82F` at C3/B4DF
- **Replaced:** Address bytes at B4E0-B4E1 changed to point to custom routine
- **Reserve:** 0x3B4E0-0x3B4E1
- **Purpose:** After calling original set_buy_limit, looks up pack size using the original slot index (resolved via slot_map in compact mode) and sets quantity/limit to pack size.
- **Logic:** Call original B82F → look up tracking pointer → if 0 skip → resolve $4B to original slot via slot_map[$4B] if compact mode → compute pack table index (shop_num×8 + original_slot) → load pack size → store to $28 (qty), $6A (limit), $30 (flag)

#### Hook 3: Pre-Order (hook_pre_order)
- **Original:** `JSR $BB53` at C3/B50B
- **Replaced:** Address bytes at B50C-B50D changed to point to custom routine
- **Reserve:** 0x3B50C-0x3B50D
- **Purpose:** Every frame in order menu, forces quantity back to pack size if limited mode active. Prevents player from changing quantity via left/down.
- **Logic:** If $30≠0, store $30→$28 → tail-call JMP $BB53

#### Hook 4: Execute Buy (hook_execute_buy)
- **Original:** `JSR $B5B7` at C3/B5B3
- **Replaced:** Address bytes at B5B4-B5B5 changed to point to custom routine
- **Reserve:** 0x3B5B4-0x3B5B5
- **Purpose:** After purchase completes, sets the tracking bit so item disappears on next draw. Resets cursor position. Resolves display position to original slot via slot_map in compact mode.
- **Logic:** Call original B5B7 → look up tracking pointer → if 0 skip → resolve $4B to original slot via slot_map → build bitmask (1 << original_slot via ASL loop) → ORA into tracking byte → clear $30 → `STZ $4E` (reset cursor to top)

#### Register State Notes
- Entry at B9AF: A=8-bit (SEP #$20 at B9AD), X=16-bit, Y=16-bit
- `SEP #$20` does NOT modify the Z flag — BEQ after SEP tests Z from preceding instruction
- Hidden B register: 16-bit Y/X transfers include B register in high byte. When loading $4B for TAX/TAY, must use REP #$20 + AND #$00FF to get clean 16-bit value
- $67 is a 16-bit value (shop_num × 9); ROM index computation must use 16-bit ADC $67 (reads $67-$68)
- All hooks preserve and restore caller's register state

### Buy Menu Entry (disable_buy_if_empty)

In `data/shops.py` `disable_buy_if_empty()`, the buy menu entry hook (Reserve 0x3B79A-0x3B79B) handles two cases:

**Without `-sli`:** Checks if first ROM item is $FF (empty shop) → buzzer + return. Otherwise clears $30 and `JMP $B7A3`.

**With `-sli`:** Same empty-shop check, then:
1. Clears $30 (limited mode flag)
2. Calls compact_init to build compacted item list
3. If compact mode active ($25=1) and first compact item is $FF (all purchased) → buzzer + return to main shop menu
4. Otherwise `JMP $B7A3` (normal buy menu init)

### Integration Flow

1. `data/shops.py` `mod()` → `compute_pack_sizes()` (determines pack sizes for all shop items)
2. `data/shops.py` `disable_buy_if_empty()` → writes compact_init subroutine + redraw trampoline + buy menu entry hook if `-sli` active
3. `menus/menus.py` → `BuyMenu()` constructor → writes 4 ASM hooks if `-sli` active
4. `event/events.py` `ruination_mod()` → `shops.enable_limited_shops(accessible_shops)` (assigns Save RAM bytes)
5. `data/shops.py` `write()` → `write_limited_inventory_data()` (writes pack size + pointer tables to ROM)

---

## No Free Heals (`-nfh` / `--no-free-heals`)

Bundles every free-heal removal/restriction behind a single flag so they can be
enabled together (default in `-ruin`) or used standalone in any other mode.
Added to the `-ruin` defaults in `args/ruin_preprocessor.py` under
`RUIN_DEFAULT_FLAGS['other']`. Users can opt out with `-no nfh`. The two flags
are now fully orthogonal — `-ruin` just bundles `-nfh`; `-nfh` works without
`-ruin`; `-ruin` without `-nfh` leaves all heals vanilla.

### Argument Wiring

- **Flag definition:** `args/misc.py` — `misc.add_argument("-nfh", "--no-free-heals", action="store_true", ...)`. Also exposed via `flags()` and `options()` ("No Free Heals").
- **Default in `-ruin`:** `args/ruin_preprocessor.py` `RUIN_DEFAULT_FLAGS['other']` includes `'-nfh'`.
- **Top-level call site:** `event/events.py` `mod()` calls `self.no_free_heals_mod()` immediately after `create_party_interaction_scripts` whenever `args.no_free_heals` is true. This works in both ruination and standalone contexts.
- **Top-level method:** `event/events.py` `no_free_heals_mod()` invokes the group sweepers from `event/free_heals.py`:
  - `modify_inn_costs(maps, rom, dialogs, args)` — multiplies all paid inn costs by `INN_COST_MULTIPLIER` (`= 3`) and converts free inns at Returners Hideout and Figaro Castle into paid ones. Includes the Coliseum inn (Take-GP opcode at `CB/786F`, amount byte `0xb7870`, base 400 GP, dialog `$0973`), which was missed in the original sweep.
  - `modify_free_bed_heals(maps, dialogs, enemies, args)` — replaces the six free bed-heal tiles (Narshe Weapon Shop, Sabin's House x3, Gau's Father's House, Mobliz Relic Shop) with: 50% pincer ambush (`FREE_BED_AMBUSH_PACK = 416`, escape allowed), then per-character state-dependent heal via the `BedHealCharacter` (0xa4) field opcode (revive→cure→HP→MP, mutually exclusive). If the party flees the ambush no heal is applied. Uses `multipurpose_map(0)` to debounce per map load. Two random pincer-capable formations are written into the ambush pack.
  - `modify_recovery_springs(maps, rom, dialogs, args)` — randomises the spring effects in `SPRING_LOCATIONS` (Phantom Forest pool, Cave to South Figaro) into one of nine outcomes (`SpringEffect`): FULL_RECOVERY, RECOVER_HP, RECOVER_MP, RECOVER_STATUS, POISON, IMP, ZOMBIE, STONE, REDUCE_TO_1_HP. Flash colour is keyed by outcome; dialog ID base is `SPRING_DIALOG_BASE = 1480`.
  - `remove_coliseum_heal(args)` — removes the start-of-battle full heal applied to the selected Coliseum fighter. The battle setup at `C2/27A8` ("copy out-of-battle stats into battle stats") restores current HP/MP to max and clears Death/Petrify/Zombie/Clear for any character flagged in zero-page `$B8`. NOPs the `LDA #$01 / TSB $B8` at `C2/2F83` (file `0x22f83`–`0x22f86`) that flags the chosen fighter (always loaded as character 1). Special-event-installed characters are flagged separately at `C2/3023` and keep their heal; the rest of the Coliseum logic keys off `$3A97`, so it is untouched.
  - `modify_vector_inn(dialogs, args)` — reworks Vector's free inn (`N = 1000 * INN_COST_MULTIPLIER`). The innkeeper NPC event (`CC/945D`, file `0xc945d`–`0xc9467`) is redirected via `Branch` into a new entry-gate routine: `RemoveGP(N/4)` then refund — too poor → "No room for yeh!" and no stay option; otherwise the still-free "Have a snooze?" prompt (dialog `$0559`) is offered, with Yes branching into the original sleep event at `CC/9468`. The scripted theft (`Take 1000 GP` at `CC/94D4`, file `0xc94d4`–`0xc94e0`) is redirected to a scaled-theft routine that steals N, falling back to N/2 then N/4, reporting the actual amount, then returns to `CC/94E1`. The N/4 entry gate guarantees the final N/4 theft always succeeds, so the heal is never free.
- **Ruination-only sweepers** (still in `event/ruination.py`, called from `ruination_mod`, NOT `no_free_heals_mod`): `disable_chocobo_stables`, `fix_ferry_connections`.

### Per-Event Heal Modifications (gated locally)

Each event file checks `args.no_free_heals` directly so the changes apply with or without `-ruin`.

| Location | File / Function | Change |
|----------|-----------------|--------|
| Baren Falls free heal | `event/baren_falls.py` `remove_free_heal_mod()` | NOPs `Call $CACFBD` at `0xbc0b2-0xbc0b5`. |
| Collapsing House innkeeper | `event/collapsing_house.py` `no_free_heals_mod()` | NOPs the heal `Call` at `0xc5c9d-0xc5ca0` and the flash/SFX at `0xc5c95-0xc5c98`; rewrites dialog `0x08B3`. |
| Doma WoB Leader battle | `event/doma_wob.py` `end_mod()` | `Reserve(0xb9fd5, 0xb9fd8, ..., NOP())` removes `Call $CACFBD` (full heal). |
| Doma WoR post-Wrexsoul | `event/doma_wor.py` `doma_mod()` | NOPs the post-Wrexsoul heal at `0xb9802-0xb9805`. |
| Magitek 3 pre-crane | `event/magitek_factory.py` `crane_battle_mod()` | `Reserve(0xb40e1, 0xb40e4, ..., NOP())` removes the pre-crane full heal. |
| Vector heal hut NPC | `event/magitek_factory.py` `ruination_mod()` (called when `args.no_free_heals` alone — gate dropped from `args.ruination_mode` in commit 3acecb4) | NPC at `0xc9371` patched to branch into one-off heal subroutine that sets `event_bit.VECTOR_FULL_HEAL_USED` (`0x149`) on first use; subsequent talks dialog-only. `init_event_bits` clears the bit at start. |
| Phantom Train restaurant | `event/phantom_train.py` `restaurant_mod()` → `ruination_restaurant_mod()` | Replaces free meal with three priced choices (Cheap 10 GP / Filling 500 GP / Chef's Special 2000 GP) with random / risky / full-heal effects respectively. |
| Narshe school heal bucket | `event/narshe_wob.py` `limited_heals()` | Limits the bucket to `NUM_HEALS = 3` uses tracked via two new event bits `SCHOOL_LIMITED_HEALS_1` (`0x0ce`) / `SCHOOL_LIMITED_HEALS_2` (`0x0cf`) encoding 3/2/1/0 drinks. **No longer uses `NARSHE_CHECKPOINT` event word** (which conflicted with the "Complete Narshe Checkpoint" objective). Gated solely by `-nfh` (works without `-ruin`). |
| Thamasa inn pricing | `event/burning_house.py` `ruination_inn_mod()` | When `no_free_heals` is on, "strangers" path receives `1500 * INN_COST_MULTIPLIER` GP. The companion burning-house re-trigger patch (use `character_recruited(STRAGO)` instead of `MET_STRAGO_RELM`) stays unconditional inside `ruination_inn_mod` since it is part of ruination's hub architecture. |
| Returners / Figaro free inns | `modify_inn_costs()` (`event/free_heals.py`) | Replaces free sleep events with `RemoveGP` followed by branch into the original sleep code; included via `no_free_heals_mod`. |

### Notes / Caveats

- **Narshe school bucket bits**: encoded as `(SCHOOL_LIMITED_HEALS_1, SCHOOL_LIMITED_HEALS_2) = (1,1)=3, (1,0)=2, (0,1)=1, (0,0)=0`. Init in `init_event_bits` writes `(1,1)` whenever `args.no_free_heals` is set. Dialog IDs 1467-1470 (1471 reserved); 1462-1466 are reserved for ruination reform dialogs.
- **Vector heal hut**: The one-use restriction is gated by `no_free_heals` alone — the Vector heal hut exists in vanilla, so the patch is safe outside ruination. The container `magitek_factory.ruination_mod()` is still gated by `ruination_mode`; the heal-hut block inside it now checks `no_free_heals`.
- **Thamasa inn**: The `ruination_inn_mod()` call site in `event/burning_house.py` still requires `ruination_mode`; only the price-bump portion checks `no_free_heals` internally.
- **`BedHealCharacter` (opcode 0xa4)**: Defined in `instruction/field/custom.py`. Argument is `0x00..0x0F` for a specific actor or `0x31..0x34` for `PARTY0..PARTY3` (resolved via `$9DAD` in vanilla). Effects (mutually exclusive): dead → revive to 1 HP (no-op under `-permadeath`); alive + status → clear field status bytes `$1614`/`$1615`; alive + HP < max → +max/4 HP capped; alive + HP == max → +max/4 MP capped. Always emits A8 on exit and dispatches `JMP $9b5c`.
- **Recovery springs**: `phantom_forest auto recovery spring` reserve in `event/phantom_train.py` `add_gating_condition()` repurposes the spring tile for character-gating walking and is unrelated to `-nfh`.
- **Inn cost ordering**: `modify_inn_costs`/`modify_free_bed_heals`/`modify_recovery_springs` do not access door-map postprocessed data, so calling `no_free_heals_mod()` before the event mod loop (and before `postprocess_door_map`) is safe.
- **Coliseum fighter heal**: `remove_coliseum_heal` works by *not flagging* the fighter (NOP at `C2/2F83`), rather than editing the heal at `C2/27A8` itself — this keeps the heal for special-event installs (`C2/2F2F` → `C2/3023`). With the heal gone, sending a KO'd/petrified character into the Coliseum means they enter the match in that state.
- **Vector inn entry gate**: requires `N/4` GP (`= 250 * INN_COST_MULTIPLIER`) to rest at all; assumes `$1BE`/`NOT_ENOUGH_GP` is clear on NPC entry (same convention as the Returners/Figaro inn rewrites). Both redirects use trampoline `Branch`es from the original NPC/Take-GP sites, so the NPC pointer and the `CC/94E1` thief-leaving code are unchanged.

---

## entrance_door_patch must fall through (2026-04)

`entrance_door_patch` is the door-rando hook used by `event_exit_info.py` to inject a per-event check before the door's normal load logic. The returned event source is **prepended** to the caller's source by both consumption sites:

1. `shared_map_exit_event`: `wor_src = edp + [FadeLoadMap(...), Return()]`
2. `create_exit_event`: builds `src[:-1] + edp + src[-1:]` so the original terminal `Return()` still ends the script.

**The patch source must NOT end with `field.Return()`.** If it does, the trailing `Return()` short-circuits the caller's `LoadMap`/`FadeLoadMap`, leaving the underlying long exit to fire its vanilla `dest_map = 0x1ff` ("return to parent map"). The branch-taken path goes elsewhere via the `BranchIfAll`/`BranchIfEventBitClear` jump; the branch-missed path needs to fall through into the caller's load.

**Caught/fixed (2026-04)**:
- `event/mt_zozo.py` — Cyan's Cliff door 1204: missed branches sent the player back to the world map instead of Cyan's Cliff (commit `c23fb5e`).
- `event/doma_wob.py` and `event/mt_zozo.py`: trailing `field.Return()` removed from `entrance_door_patch` returns (commit `8a8cd0e`).

**Pattern (correct)**:
```python
@staticmethod
def entrance_door_patch(args):
    if args.character_gating:
        return [
            field.BranchIfAll([event_bit.FINISHED_X, False,
                               event_bit.character_recruited(CHAR), True], continue_addr),
            # NO Return() here — fall through to caller's LoadMap
        ]
    else:
        return [
            field.BranchIfEventBitClear(event_bit.FINISHED_X, continue_addr),
        ]
```

The `Local Character Gating` section above has been updated to reflect this; older copies in commit history still show the incorrect shape with trailing `Return()`s.

---

## Custom Opcodes Reference

Single source of truth for every opcode added by this codebase. Verified against source on 2026-04-25.

### Field opcodes (`instruction/field/custom.py`)

Vanilla field-event opcode table is at SNES `$C098C4`, 256 entries × 2 bytes. `_set_opcode_address(opcode, address)` patches one entry; the implicit Bank.C0 provides the high byte. Pattern: write ASM to Bank.C0, register via `_set_opcode_address`, set `_Instruction.__init__` to forward `opcode + args`.

| Opcode | Class | Purpose |
|--------|-------|---------|
| `0x66` | `MarkActivePartyAway` | Sets `PARTY_N_AWAY` bit, clears `character_available` for party members, decrements `CHARACTERS_AVAILABLE`. Idempotent. Fired by event tiles on branch door exits. |
| `0x67` | `RestoreActivePartyAvailable` | Clears `PARTY_N_AWAY` bit, restores `character_available`, increments `CHARACTERS_AVAILABLE`. Idempotent. Fired by hub entrance event when a party returns. |
| `0x68` | `RemapPartiesToFreeSlots` | Remaps `$1850` party assignments from SelectParties slots (always 1..count) to actual free slots. Uses `character_available` to distinguish new from away characters. |
| `0x69` | `UpdateWorldReturnToParentMap` | Map Shuffle / door rando: read parent map, update world bit (`$1E94` bit 4) to match, return to parent map. |
| `0x6d` | `SetParentWorld` | Map Shuffle / door rando: set the parent-world bit. |
| `0x6e` | `_InvokeBattleType` (internal — used by `field.InvokeBattleType`) | Invoke a battle with explicit type (e.g. `BattleType.PINCER`). |
| `0x6f` | `RemoveDeath` | Special command for events like Moogle Defense — clears the death status bit even with `-permadeath`. |
| `0x76` | `RecruitCharacter` | Recruit a single character (sets recruited + available bits). |
| `0x83` | `LoadEsperFound` | Load esper-found event word into A. |
| `0x8f` | `LongCall` | Bank-tagged subroutine call. **Overwrites the vanilla "learn all swdtech" opcode.** |
| `0x9e` | `SetYNPCGraphics` (in `instruction/field/y_npc/instructions.py`) | Set Y-NPC graphics for the `-y*` flags. |
| `0x9f` | `YNPCEffect` (in `instruction/field/y_npc/instructions.py`) | Trigger Y-NPC effect. |
| `0xa3` | `SetEquipmentAndCommands` | Copy equipment and commands from one character slot to another. |
| `0xa4` | `BedHealCharacter` | **`-nfh` only.** Per-character state-dependent heal. Argument: `0x00..0x0F` for a specific actor, or `0x31..0x34` for `PARTY0..PARTY3` (resolved via `$9DAD`). Effects (mutually exclusive): dead → revive to 1 HP (no-op under `-permadeath`); alive + status → clear `$1614`/`$1615`; alive + HP < max → +max/4 HP capped; alive + HP == max → +max/4 MP capped. Always emits A8, dispatches `JMP $9b5c`. |
| `0xa5` | `BranchChance` | Branch with given probability — field equivalent of `BranchProbability`. |
| `0xe5` | `LoadPartiesWithCharacters` | Load parties pre-populated with a list of characters (used by Branch Recruit setup). |
| `0xec` | `SetupBranchRecruit` (alias `SetupBranchPartySelect`) | Pre-recruitment hook for ruination branch recruits. Saves party_away_byte, restricts party-select pool to current party + new recruit. **First** (before reorganising party slots) JSRs a Bank.C0 subroutine that syncs every party's members to their visible leader's object position (render offsets `$02-$07` + tile/collision `$13-$14`), fixing the field party-swap "teleport" bug: when a party's leader is changed mid-field and the party walks away, a demoted member keeps a stale object position; re-promoting it (e.g. via the two-party swap menu) would redraw the party at the stale spot. No-op for already-synced members. See `_write_sync_party_member_positions`. |
| `0xed` | `FinalizeBranchRecruit` (alias `FinalizeBranchPartySelect`) | Post-recruitment hook. Restores party_away_byte saved by `SetupBranchRecruit`, recomputes `character_available` and `CHARACTERS_AVAILABLE`. |

**Other helpers in `instruction/field/custom.py`**:
- `_leader_finder_safe_store_mod()` (ruin-gated, called once at module load) — patches the two `STA $1850,Y` writes inside vanilla `C0/6F67` to range-check Y (`CPY #$000E / BCS .skip`). Avoids inventory corruption when a leader offset is a sentinel (`$07B0`/`$07D9`). See "SelectParties Inventory Corruption Bug & Fix".

### Vehicle-script opcodes (`instruction/vehicle.py`)

Vanilla vehicle-script opcode table is at SNES `$EE76FB`, 256 entries × 2 bytes. Opcodes E1-F2 are unused in vanilla (their entries dispatch to a no-op stub at `$EE74A4`). `_set_vehicle_opcode_address(opcode, snes_handler_addr)` patches one entry.

| Opcode | Class | Purpose |
|--------|-------|---------|
| `0xE1` | `BranchProbability` | Inline RNG roll → branch with given chance (0-255). Handler is lazily installed on first use; see the section below. |

### Battle-event opcodes (`instruction/battle_event.py`)

| Opcode | Class | Purpose |
|--------|-------|---------|
| `0x15` | `IncrementChecksComplete` | Increment the "checks complete" counter at end of battle. |

### Adding a new opcode

1. Pick an unused opcode. Field unused list (commented at top of `instruction/field/custom.py`): `0x4a`, `0x5b`, `0xe6`, `0xfc`, `0xfd`. Plus `0xa4` (now used by `-nfh`). Vehicle: `0xE2-0xF2` unused.
2. Write the ASM body. Field opcodes typically end with `LDA #<size> / JMP $9b5c` (next command); vehicle opcodes end with `JMP $7093` (return to dispatcher).
3. Register: `_set_opcode_address(opcode, address)` (field/y_npc) or `_set_vehicle_opcode_address(...)` (vehicle).
4. Subclass `_Instruction` (or `_Branch`) and forward `opcode + args` via `super().__init__(opcode, *args)`.
5. **Update the table above.**

---

## BranchProbability vehicle-script opcode (0xE1) (2026-04)

Vanilla vehicle scripts (Bank EE, used by Lete River, Serpent Trench, ending sequence) have no random-branch primitive. Custom opcode `0xE1` (`BranchProbability(chance, destination)`, in `instruction/vehicle.py`) adds one.

**Format**: `E1 cc dd_lo dd_mid dd_hi` (5 bytes)
- `cc` — 1-byte chance 0-255. Branch is taken iff RNG byte `<` cc.
- `dd_lo/mid/hi` — 3-byte destination, encoded the same way as the existing `B0` conditional-branch destination (caller passes a ROM offset; handler adds `0xCA` to rebase to bank CA).

**Installation**: Lazy. The first `BranchProbability(...)` constructor in a build calls `_install_branch_probability_handler()` once, which:
1. Writes the handler ASM to Bank EE free space (memory/free.py declares 0x2eaf01-0x2eb1ff = SNES `$EEAF01-$EEB1FF`).
2. Patches the dispatch table entry at SNES `$EE76FB + 0xE1*2` to point at the new handler. Vehicle opcodes E1-F2 are all unused in vanilla (their pointer-table entries dispatch to a no-op stub at `$EE74A4`).

**Handler logic**:
1. `SEP #$20` to put A in 8-bit mode; fetch chance byte at script offset `$ED` into scratch DP `$58`.
2. Inline RNG (X-mode-safe variant of `c0.rng`): increment `$1F6D`, read `$C0FD00,X` after switching to X8.
3. `CMP $58 / BCC` to branch.
4. **Branch-taken**: rewrite script PC `$EA/$EB/$EC` from operand bytes (mirroring the tail of vanilla B0 at `$EE715F`), zero `$ED/$EE`, `JMP $7093`.
5. **Fall-through**: advance `$ED` past 4 operand bytes, `JMP $7093`.

**Use site**: `event/serpent_trench.py` `ruination_battles_mod` — first visit to a fixed battle is forced; subsequent visits use `BranchProbability(p, FIGHT)` so re-rides don't re-fight every encounter. Replaces an earlier field-mode pre-script + entry wrapper that had the same effect with much more code (commit `1c65837`).

---

## SET_PARTY_INTERACTION_POINTERS shared subroutine (2026-04)

`event/ruination.py` exports `SET_PARTY_INTERACTION_POINTERS` — the SNES address of a Bank.CA subroutine that re-binds every recruited character's NPC talk event to its corresponding party-interaction script. Populated by `create_party_interaction_scripts()` (which runs **before** the event mod loop, so it's available when individual events build their own scripts).

**Why it exists**: Field RAM NPC pointers (`ChangeNPCEventAddress`) are not preserved in saves. Whenever the player loads a saved game and enters a hub-adjacent map, every recruited character's NPC needs its talk-event pointer re-applied. The shared subroutine consolidates the per-character `ChangeNPCEventAddress` calls so callers don't inline them.

**Two consumers**:
1. `event/narshe_wob.py` Narshe school entrance event: `field.Call(SET_PARTY_INTERACTION_POINTERS)` after `RestoreActivePartyAvailable`.
2. `event/esper_world.py` `cleanup_esper_world()`: assigns `SET_PARTY_INTERACTION_POINTERS - EVENT_CODE_START` as the entrance event for the three repurposed esper-world maps (only in ruination mode; non-ruin uses a bare `Return` at `0x5eb3`).

**Pattern when adding new consumers**: Import lazily inside the method (not at module top) — `from event.ruination import SET_PARTY_INTERACTION_POINTERS`. Reads happen during event mod, after `create_party_interaction_scripts()` has populated it. If used as an `entrance_event_address`, subtract `EVENT_CODE_START`; if invoked from event source, use `field.Call(SET_PARTY_INTERACTION_POINTERS)`.

---

## Y-Party-Switch Disable Shared Subroutines (2026-06)

`event/ruination.py` exports `DISABLE_Y_PARTY_SWITCH` and `RESTORE_Y_PARTY_SWITCH` — the SNES addresses of a pair of Bank.CB subroutines that save-and-disable, and restore, the `ENABLE_Y_PARTY_SWITCHING` event bit. Both are populated by `create_y_party_switch_subroutines()`, which runs **before** the event mod loop (in `event/events.py` `mod()`, in the same `args.ruination_mode` block as `create_party_interaction_scripts()`), so the addresses are available when individual events build their scripts.

**Why it exists**: Several ruination-mode events make dynamic map edits that get reset — breaking or softlocking the event — if the player presses "y" to switch parties mid-scene. Each such event disables y-party switching when its scene begins and restores it at the end. `DISABLE_Y_PARTY_SWITCH` saves the current `ENABLE_Y_PARTY_SWITCHING` value into the `SAVED_Y_PARTY_SWITCHING` event bit (`0x0bb`) then clears `ENABLE`; `RESTORE_Y_PARTY_SWITCH` reads `SAVED` back into `ENABLE`. The protected scenes never overlap, so a single pair of subroutines and a single save bit serve all of them. Both subroutines end in `Return`, so they work either as a `field.Call` target or directly as a map-event tile script.

**Five consumers** (all ruination-only):
1. `event/doma_wob.py` `enter_exit_functions_mod()`: `field.Call(DISABLE_Y_PARTY_SWITCH)` at the start of `enter_event_function` (siege scene begins), `field.Call(RESTORE_Y_PARTY_SWITCH)` in `exit_function` (after the boss is defeated).
2. `event/fanatics_tower.py` `ruination_mod()`: assigns `DISABLE_Y_PARTY_SWITCH - EVENT_CODE_START` / `RESTORE_Y_PARTY_SWITCH - EVENT_CODE_START` as the `event_address` of two map-event tiles on maps `0x16a` / `0x16b` (entry/exit).
3. `event/floating_continent.py` `escape_mod()` and `map_shuffle_mod()`: `field.Call` the disable on landing and the restore on each of the three exit paths.
4. `event/narshe_moogle_defense.py` `event_start_mod()` / `after_battle_mod()`: `field.Call` the disable before the battle and the restore after victory.
5. `event/imperial_camp.py` `leo_and_chasing_kefka_mod()` / `restore_y_party_switch_src()`: `field.Call` the disable in the activation tile script (the "player jumps in front of kefka" scene that activates the camp, guarded by `BRIDGE_BLOCKED_IMPERIAL_CAMP` so it only fires once), and the restore in each of the three reward-finish blocks (`character_mod` / `esper_mod` / `item_mod`).

**History**: Originally each event wrote its own private copy of the two subroutines (and Moogle Defense used a raw magic bit `0x1ca` instead of the named `SAVED_Y_PARTY_SWITCHING`). Consolidated into the single shared write in 2026-06.

**Pattern when adding new consumers**: Import lazily inside the method (not at module top, to avoid circular imports) — `from event.ruination import DISABLE_Y_PARTY_SWITCH, RESTORE_Y_PARTY_SWITCH`. Reads happen during event mod, after `create_y_party_switch_subroutines()` has populated them. If used as an `event_address`/`entrance_event_address`, subtract `EVENT_CODE_START`; if invoked from event source, use `field.Call(...)`. Mirrors the `SET_PARTY_INTERACTION_POINTERS` convention above.

---

## Branch Area Detection for Narshe Clues (2026-04)

The Narshe school NPC clue scripts read `args.ruination_areas_used` (a `dict[area_name, branch_id]`) to tell the player which areas are on which branch. **Do not source this dict from `ruin_map.AreasUsed`** — use `ruin_map.compute_actual_areas_used()` instead.

**Why**: `AreasUsed` records which branch an area was *distributed* to, but two failure modes can cause the recorded branch to hold none of the area's rooms:
1. **Distribution skips already-claimed rooms**: When `forced_same_branch`, shared rooms, or `CHARACTER_AREAS['ALL']` placed an area's rooms in another branch first, the later distribution still tags itself as "the" branch for that area.
2. **Added but unreachable**: `finalize_map` only guarantees the hub has no dangling exits. Non-hub rooms can remain unconnected; counting `branch.all_rooms_added` would credit those.

**Implementation** (`event/ruination.py` `compute_actual_areas_used`):
- For each branch, find its hub node (id contains `'ruin_hub_'`); use the hub's compound id (joined by `_` via `compress_loop`) as a substring oracle.
- A room `R` is reachable iff `_R_` is a substring of the bracketed hub id. Underscore boundaries avoid false positives (e.g. 78 vs 278, 501 vs 1501) and handle ids that contain underscores (`share_east`, `ruin_hub_0`).
- For each area in `RUIN_ROOM_SETS`, count reachable rooms per branch; pick the branch holding the most.
- Skip areas with zero reachable rooms across all branches.

**Branch selection weighting** (`event/ruination.py` generation loop, commit `6fb1624`): To avoid one branch staying a stub while the other two grow long, viable branches are picked with weight `1 + total_rewards_found - branch_rewards_found[b]` (always `>= 1`). `branch_rewards_found` is incremented after each successful reward placement.

---

## Persistent Event State Across Reloads (2026-04)

Several ruination-mode events need post-defeat state to persist when the player saves and reloads. The pattern is: **clear or set the relevant event bit(s) on init, then update them in-event when the trigger fires**, so reloading doesn't replay the event.

### Burning House Fireballs (commit `54e05b4`)

Each of the 12 fireball NPCs in the burning house has its own visibility bit (`0x3a1-0x3ac`). On init, all 12 bits are **set** so the fireballs appear; the back half of each fireball event is replaced with a `Call` that **clears** that fireball's bit when defeated. Only 75% of fireballs clear per defeat (commit `df47838`/`0e4a363` — the original probability was inverted).

This adds 12 `SetEventBit` writes (24 bytes) to the shared `init_event_bits` buffer. The buffer was bumped from 400 → 450 bytes in ruination mode (`event/events.py`, commit `298736b`) to accommodate. **Add more init writes carefully** — overflow throws an allocator error.

### Kefka Tower Switches (commits `2604cc8`, `d62cda7`, `bb6e1ce`)

The KT left/right switch event bits (`KEFKA_TOWER_LEFT_SWITCH`/`KEFKA_TOWER_RIGHT_SWITCH`) are **cleared** on `init_event_bits` so the switches start unpressed regardless of vanilla pre-state. The clear-bit event tiles wrap their `ClearEventBit` call in the standard step-debounce pattern using multipurpose bit `0x1b5` (cleared every step):

```
ReturnIfEventBitSet(0x1b5)
ClearEventBit(<switch bit>)
SetEventBit(0x1b5)
Return
```

In-place patching of the existing scripts is preferred over rewriting them (commit `d62cda7`).

### Minecart (commit `5e85dbb`)

In dungeon-crawl/ruination modes the minecart event exit (CC/8022) can be revisited. A 4-byte hook at CC/80A8-CC/80AB routes through a check/set block: first pass replays the displaced PlaySong+SetEventBit bytes; subsequent passes branch over the ride to CC/80B9 (the LoadMap, which `Transition` has already patched to the new destination). `event_bit.DEFEATED_NUMBER128` (`0x06d`) is the gating bit. Hook footprint is disjoint from `number128_battle_mod`'s reserve at CC/80AD-CC/80B0. `MagitekFactory.minecart_mod` uses `Branch` (not `Call`) for the revisit hook (commit `ba450c3`); the post-ride event-bit block runs on revisit too (commit `5bccfe3`).

---

## Debug Output Routing (`-debug` vs `-debug-verbose`) (2026-04)

`log/verbose.py` `vprint()` is the canonical helper for debug logging in the door randomizer and ruination code. It routes based on flags:
- `-debug` (`args.debug`) — prints to stdout.
- `-debug-verbose` / `-dv` (`args.debug_verbose`) — appends to a temp file that joins the spoiler log.
- Neither — `vprint` is a no-op.

**Don't** wrap `vprint(...)` calls in `if self.verbose:` — the no-op handling is built in. **Don't** use raw `print()` for diagnostic output: it leaks to stdout whenever `-debug` is set, even without `-dv`. The fix in commit `85b1703` replaced `print()` with `vprint()` in `data/map_exits.py` `patch_exits()` and removed the redundant `Doors.verbose` instance attribute (replaced with a property that delegates to `verbose.is_enabled()`).

When introducing new debug output, prefer `vprint(...)` and let the user's flag choice decide where it goes.

---

## Ruination Mode — Dialog ID Reservations (2026-05)

Ruination mode repurposes a contiguous block of vanilla dialog IDs that belong to the Maduin/Madonna esper-world conversation (dialog 1424-1496, hex `$0590-$05D8`). 
That conversation is part of the WoB intro and **never plays in ruination mode**, so the IDs are safe to overwrite. 
Several systems claim slices of this block independently, and `dialogs.set_text(id, ...)` happily clobbers an ID written earlier — there was no allocator. 

**UPDATE 7/23/26:** an allocator was added to `data/dialogs/dialogs.py`. The method `allocate_dialog(text_str)` returns the next dialog_id from the range (1424-1496), including throwing an error if the list runs out.  To use it:
```
new_id = dialogs.allocate_dialog("This text will display in-game!<end>")
```

Here's the old reservation table in case you need to check it:

### Maduin/Madonna Block — Reservation Table

| Dialog IDs (hex) | Decimal | Owner | Variable / purpose | File | Gated on |
|---|---|---|---|---|---|
| `$0590` | 1424 | ruination start | `ruination_start_1` ("After Kefka broke the world…") | `event/ruination.py` `ruination_start_game_mod` | `-ruin` |
| `$0591` | 1425 | ruination start | `ruination_start_2` ("This new world is dark…") | `event/ruination.py` `ruination_start_game_mod` | `-ruin` |
| `$0592-$05B4` | 1426-1460 | warp points | `WARP_DIALOG_IDS` (35 IDs = 1 esper-world prompt + 2 per warp point × 17 points) | `data/warps.py` (`WarpPoints.mod`, called from `event/events.py`) | `-ruin` |
| `$05B5` | 1461 | -nfh Figaro inn | `FIGARO_DIALOG_ID` (paid Figaro Castle rest dialog) | `event/free_heals.py` `modify_inn_costs` | `-nfh` |
| `$05B6-$05BA` | 1462-1466 | school reform | `NARSHE_DIALOG_IDS` (reform / how-many-parties dialogs) | `event/narshe_wob.py` `ruination_mod` | `-ruin` |
| `$05BB-$05BE` | 1467-1470 | -nfh limited heals | `empty_id` / `one_id` / `two_id` / `three_id` (school bucket prompts) | `event/narshe_wob.py` `limited_heals` | `-nfh` |
| `$05BF-$05C1` | 1471-1473 | ferry flavor | `FERRY_FLAVOR_DIALOG['SouthFigaro' / 'Nikeah' / 'Albrook']` | `event/ruination.py` `_ferry_install_enabled` | `-ruin` |
| `$05C2-$05C4` | 1474-1476 | -nfh Vector inn | `VECTOR_NO_ROOM_DIALOG_ID` (1474, "No room for yeh!"), `VECTOR_STOLEN_HALF_DIALOG_ID` (1475, "<N/2> GP stolen!"), `VECTOR_STOLEN_QUARTER_DIALOG_ID` (1476, "<N/4> GP stolen!") | `event/free_heals.py` `modify_vector_inn` | `-nfh` |
| `$05C5-$05C7` | 1477-1479 | **free** | — | — | — |
| `$05C8-$05D7` | 1480-1495 | -nfh recovery springs | `SPRING_DIALOG_BASE` reservation (1 drink prompt + 1 result per spring area; currently uses 1480-1482, range reserved) | `event/free_heals.py` `modify_recovery_springs` | `-nfh` |
| `$05D8+` | 1496+ | **out of block** | Vanilla "What's happening in Narshe?" dialog runs here — do not claim. | — | — |

### Other Vanilla Dialogs Repurposed by Ruination Mode

These claims live outside the Maduin block. They overwrite vanilla dialogs whose original event paths are unreachable in ruination mode (e.g. the WoR airship console, the chocobo stables, the WoR ferry sailors), so collisions there are safer — but still worth knowing about.

| Dialog ID(s) | Owner | File | Notes |
|---|---|---|---|
| `0x0113` (275) | Jidoor chocobo | `event/ruination.py` `disable_chocobo_stables` | "The chocobos won't go outside anymore." |
| `0x0258` (600) | Narshe info NPC | `event/narshe_wob.py` `ruination_mod` (`info_id`) | Reform-school welcome / how-to text |
| `601` | Narshe water shortage | `event/narshe_wob.py` `ruination_mod` | Water-supply rep dialog |
| `602-610` | Narshe school clue NPCs (3 branches × 3 clues) | `event/narshe_wob.py` `ruination_mod` | Per-area clue text from `compute_actual_areas_used()` |
| `0x032A`, `0x032C`, `0x0785` (810, 812, 1925) | Ferry prompts | `event/ruination.py` `_ferry_install_enabled` (`FERRY_PROMPT_DIALOG`) | Vanilla SF / Nikeah / Albrook (Leo cargo) ferry NPC dialogs |
| `0x0507` (1287) | KT statues/entrance choice | `event/kefka_tower.py` `entrance_landing_mod` | "(Statues)/(Entrance)/(Not just yet)" |
| `0x050D` (1293) | "There's no returning…" | `event/airship.py` `controls_mod`, `event/sealed_gate.py` `ruination_mod`, `event/esper_mountain.py` `ruination_mod` | Shared text for all three KT terminuses |
| `0x050E` (1294) | "Three parties needed…" | same three sites as 1293 | Shared text |
| `0x0523` (1315) | `fly_wor_fc_cancel_dialog` | `event/airship.py` `controls_mod` | Falcon WoR-FC console rewritten for ruination |
| `0x0526` (1318) | `fly_wor_cancel_dialog` | `event/airship.py` `controls_mod` | Falcon WoR console rewritten for ruination |
| `0x0528` (1320) | `PARTY_INTERACT_CHOICE_DIALOG` | `event/ruination.py` `create_party_interaction_scripts` | Vanilla "Change party members?" repurposed for the join/swap/nothing menu |
| `0x055A` (1370) | -nfh Vector inn theft (`VECTOR_STOLEN_FULL_DIALOG_ID`) | `event/free_heals.py` `modify_vector_inn` | Vanilla "1000 GP stolen!" → "<N> GP stolen!" (full-amount case). Half/quarter cases use 1475/1476 in the Maduin block. Gated on `-nfh`. |
| `0x0666`, `0x0667` (1638, 1639) | KT entry prompts | `event/sealed_gate.py`, `event/esper_mountain.py` ruination_mods | "Enter Kefka's Tower? There's no going back." |
| `0x068B`, `0x068D`, `0x068F`, `0x0690` | Mog/Gau/Gogo/Umaro airship quotes | `event/ruination.py` `create_party_interaction_scripts` (`CHARACTER_AIRSHIP_DIALOG_IDS`) | Per-character party-interaction dialog |
| `0x08D0`, `0x08D2`, `0x08D8`, `0x08D9` (2256, 2258, 2264, 2265) | Mobliz "you're not gonna take…" | `event/mobliz_wor.py` (ruination branches) | Replaces character or esper item name |
| `0x0B8E` (2958) | SF / Nikeah chocobo | `event/ruination.py` `disable_chocobo_stables` | Shared dialog with Nikeah |
| `0x0B94-0x0B9D` (2964-2973) | Terra/Locke/Cyan/Shadow/Edgar/Sabin/Celes/Strago/Relm/Setzer airship quotes | `event/ruination.py` `create_party_interaction_scripts` (`CHARACTER_AIRSHIP_DIALOG_IDS`) | Per-character party-interaction dialog |
| `0x0BA6` (2982) | KT "need more allies" | `event/kefka_tower.py` `entrance_landing_mod` | — |
| `0x0BCF` (3023) | KT objectives-incomplete | `event/kefka_tower.py` `final_kefka_access_mod` | — |

### Lessons (after the Albrook ↔ KT-warp clobber, 2026-05)

- **Order matters when two systems write the same range.** `WarpPoints.mod()` runs early in `Events.mod()`; `fix_ferry_connections` runs later, so any ferry overlap silently overwrote the warp prompts. Symptoms surfaced as warp dialogs containing ferry text at runtime.
- **No allocator.** `dialogs.set_text(id, …)` is a raw write — there is no "is this ID already claimed?" check. Document the reservation here whenever you grab a new slot.
- **Pick from the documented free range.** `1471-1479` is the current free band inside the Maduin block. If you need a contiguous run larger than 9, expand into the trailing reservation deliberately and update this table.

---

## Floating Continent Tube-Maze Randomizer (2026-06)

Self-contained, **ruination-only** randomization of the Floating Continent (map `0x18A`) tube maze. All of it lives in `event/floating_continent.py` (module-level `_FC_*` data + `_fc_reachable`/`_fc_randomize_maze`, and the `FloatingContinent.ruination_tube_maze_mod()` method, called last in `mod()`). The player still enters at FC1 (falling in) and exits via FC8 (to the Atma/statues area), but the route is shuffled.

### Model

- **12 tube endpoints** paired into 6 bidirectional connections; **4 buttons** (FCa–d) assigned, as a bijection, to **4 locks** {Fixed1-2 wall FC2↔FC3, Fixed3-4 wall FC3↔FC7, Fixed5-6 wall FC3↔FC5, Tube9 reveal}. `_fc_randomize_maze` retries random matchings until a keys-and-locks fixed point (`_fc_reachable`) shows every room reachable from FC1 **and** FC8 reachable fresh from the Save Room's partner room (a save detour reloads the map and resets the locks). Constraints: no two tubes in the same room pair; never pair Tube9 with Tube12. 0 failures over 5000 seeds.
- Tube positions / open-close subroutine addresses / event-tile ranges are in `_FC_TUBES`; buttons in `_FC_BUTTONS`; locks (with reset-on-map-load bits + camera-pan targets) in `_FC_LOCKS`.

### Gotchas worth remembering (these caused real bugs)

1. **Scripted entity moves collide with terrain — never walk the party across the map.** The vanilla tube transit moves the hidden *party* along a clear vanilla corridor; on a randomized route that path crosses walls and the move jams (party stranded on the wrong tile) or hard-locks the event (`WaitForEntityAct` never completes — "camera freezes, exit never happens"). Fix: `HoldScreen`, pan the **CAMERA** (object `0x30`, which ignores terrain), then `SetPosition` the hidden party straight onto the destination tile, then `FreeScreen` + exit animation. See `tube_transition`.
2. **The exit animation belongs to the tube being EXITED.** Every tube emerges *down* (vanilla slide-out `CAD577`, hops in place at dst+2) **except Tube11**, which emerges *up* (jump up 3 to dst-1, reconstructed from its vanilla save-room return `C2 C6 DD 88`). Getting this backwards softlocks the party on an unwalkable tile. See `exit_sequence(dst)`. On the Save Room return, the LoadMap camera must centre on where the party *ends* (`dst-1` for Tube11, else `dst+2`).
3. **`$1B5` (`$1EB6` bit 5) is a universal "run once per map visit" scratch bit**, set+checked in hundreds of events and cleared on every map load. The Save Room round trip is rebuilt around it verbatim — only the FC-side LoadMap coords + tube graphics are substituted (`x_to_save`/`save_to_x`).
4. **`event_bit.multipurpose_map(i)` → `0x1f0+i` are "cleared on map load."** The four lock/reveal bits use these (the vanilla FC switch bits `$1F6–$1F9` already are), so the layer-2 walls — which also reset on reload — stay in sync with their bits. Don't use a permanent bit here or a reload desyncs wall vs. bit and softlocks.
5. **`MoveDiagonal` (opcodes A0–AB, 1:1 / 1:2 / 2:1) is already fully implemented** in `instruction/field/entity.py` as `MoveDiagonal(dir1, dist1, dir2, dist2)`. `pan_path(dx,dy)` uses it for a near-straight, symmetric camera pan (diagonal run split around a central linear/diagonal run), which also makes rides take `~max(dx,dy)` time instead of the L-shape's `dx+dy`.
6. **`save_point_hole_mod` overlaps Tube12's event** (`0xad951–0xad95c` ⊂ `0xad940–0xad979`); it early-returns under `args.ruination_mode`, and the light-deletion it did is folded into `save_to_x`.

### Reusing vanilla code space (best practice for limited free ROM)

`ruination_tube_maze_mod` reclaims the superseded vanilla tube/button **event bodies** rather than burning fresh free space:
1. After the `Read` snapshot block (tubes 9/10 inline graphics + Save Room bytes — all *inside* ranges about to be freed), `Free(...)` every `_FC_TUBES`/`_FC_BUTTONS` `"range"` (~832 bytes). The open/close, slide-in/out (`0xad566`/`0xad577`) and wall subroutines those events *called* live outside these ranges and are kept — the new code still calls them by address.
2. Write the new (more compact) animations with `Write(Bank.CA, …)`; the allocator packs them into the reclaimed space first and spills into ordinary free space only when it runs out. Net cost dropped from ~1050 bytes of free space to ~255.
3. **Re-point the event tile directly** instead of stamping a `Branch` over the vanilla entry: `event = self.maps.get_event(map_id, x, y); event.event_address = new_code.start_address - EVENT_CODE_START` (`EVENT_CODE_START = 0xA0000`; see `instruction.event`). Tube12's tile is on the Save Room map `0x166`, all others on `0x18A`. This is the same convention `event/switchyard.py` and `data/maps.py` use.

## Kefka's Tower Lane Randomizer (`-rkt`) (2026-06)

Self-contained, **ruination-only** randomization of the three lanes of Kefka's Tower (the `KT*` rooms in `data/rooms.py`). Flag `-rkt` / `--ruin-kefka-tower` (`args/doors.py`). All logic lives in `event/ruination.py`: the `ruination_map._randomize_kefka_tower()` method plus `KT_*` class constants. Wiring: `ruination_map.__init__` calls it once (`self.kt_lane_map = self._randomize_kefka_tower()` when the flag is set), and `generate_map_with_characters` injects the result into the global door/trap map near the end (`map[0].extend(kt_lane_map[0]); map[1].extend(kt_lane_map[1])`), right after the isolated-maze injection. Returns `[[door pairs], [trap→pit pairs]]`, or `None` to fall back to the vanilla KT layout.

### Why it drives the real network walk (not random matching, like Dream Maze)

KT's door graph is **deliberately sparse** — ~28 two-way door-edges across ~34 door-bearing rooms — so a lane **cannot be connected by doors alone**; connectivity also depends on the one-way conveyor/pipe **traps** and the two key-gated **platforms**. The first cut used the Dream-Maze approach (random door↔door / trap→pit matching + verify); it reliably produced *completable* layouts but connected *every* room only **~0.012%** of the time, orphaning bosses/switches onto islands. The fix drives the **same constructive solver the ruination branches use** — `data.walks.Network.connect_network` — once per lane.

### The coupling (why lanes can't be solved independently of keys)

Two switches couple the lanes: pressing `KTb8` sets key `KT1`, pressing `KTc10` sets key `KT2`. Each key unlocks a **forced crossing** in *another* lane: `KTa5a↔KTa5b` (switch platform `1565↔1566`, needs `KT1`) and `KTa8a↔KTa8b` (broken stairs `1567↔1568`, needs `KT2`). Once unlocked, both crossings are walkable in either direction (confirmed in game by Hans, 2026-09). Hand-set design constants: `KT_ENTRIES`, `KT_FINALS`, `KT_BOSSES`, `KT_MAX_SPLITS = 400`. Everything about the crossings is **derived from room data** by `derive_tower_tables()` (2026-09): `KT_CROSSINGS` (`(a, b, keys, two_way)`: the locked elements of tower rooms joined by a forced connection; two-way when the pair is door-range, one-way when trap->pit, decided by the walk's own `WorldModel._element_kind`), `KT_FORCED`, `KT_PLATFORM_IDS`, `KT_KEY_ROOM` (tower rooms' key slots) and `KT_KEYS`. Malformed data (an unpaired locked element, a forced partner outside the tower locks, a door paired with a pit, a key no room grants) raises `ValueError`. To change a crossing, edit `data/rooms.py` / `forced_connections` - never a table in `kefka_tower.py`.

### Three-phase design (propose → verify, in a retry loop, up to `KT_MAX_SPLITS`)

1. **`split_lanes()` — partition + cheap *necessary* filter.** Randomly assigns every KT room to one of three lanes (one entry + one ending each; the two `KT_CROSSINGS` pairs kept atomic so a crossing never spans lanes). Rejects (`None`) any partition where a lane has unequal traps≠pits, an odd door count, or >2 of the 4 bosses. Fast pre-filter only — *not* sufficient.
2. **`connect_lane(lane)` — drive the walk (optimistic).** `Network(list(lane))` → **apply every key in `KT_KEYS`** (`KT1`, `KT2`; see gotcha 2) → `ForceConnections(KT_FORCED)` → `attach_dead_ends()` → `active` = room with the most exits → `connect_network()`. Catches the walk's failure-raise and returns `None` (→ re-roll). **Strips `KT_PLATFORM_IDS` from the returned map** (gotcha 2). The walk is deliberately optimistic — it treats both platforms as open and ignores key timing.
3. **`verify()` — the ground truth (honest), via a joint state-space.** The three lanes are physically disjoint; their *only* coupling is the **global, monotonic keychain** (pressing `KTb8`/`KTc10` sets `KT1`/`KT2`, opening a gated crossing that may be in a different lane). The player drives all three parties asynchronously and switches between them freely, so verify models the true dynamics as a search over joint states **`(roomA, roomB, roomC, keychain)`**:
   - a move steps **one** party along a door (two-way), a trap (one-way), or a gated crossing (two-way, only if its key is already held);
   - a party standing on a switch room may add that key to the shared keychain (permanent — it never shrinks).

   Forward-BFS the reachable joint states from the three entries, then accept iff **(a)** every room is occupied by its lane's party in some reachable state (no orphans — all bosses/switches reachable) **and (b)** from EVERY reachable state the players can still herd all three parties onto their endings (reverse-BFS the all-at-endings goal over the forward edges; require it covers the forward set). The state space is tiny (product of lane sizes × 4 keychains ≈ a few thousand; verify ≈ 10 ms).

The soundness argument is the **optimistic-generator / pessimistic-verifier split**: the walk only proposes (treating both platforms as open); `verify` re-checks under the *true* asynchronous-party / key-timing semantics, so a layout ships only if no situation the player could reach is a dead end.

**Why the old single-flood check was wrong (the bug that prompted this, 2026-06).** verify originally did a key-collecting reachability *fixpoint* (flood from entries, add keys as rooms become reachable) plus a "no one-way strand" pass that assumed **both keys already held**. That pass is too optimistic: it cannot see a party that rides a one-way into a pocket whose only exit is a gated crossing whose key it can *no longer collect* (e.g. the key is in that party's own lane but now upstream of the one-way it just took). Measured on 150 fully-connected candidates, **11/29 layouts the old check accepted were actually softlockable** — the new joint check rejects exactly those and is strictly stronger (0 cases where it accepts something the old check rejected). The expensive joint BFS is affordable because it runs only on the rare candidate whose three lanes all connected; ~0 fallbacks remain within `KT_MAX_SPLITS = 400` (median ~0.6 s, max ~3.6 s per build).

### Gotchas worth remembering (these caused real bugs)

1. **`ForceConnections` must always be called**, even for a lane with no platform — it initialises `Network.protected` (which is `None` otherwise). Skipping it makes `connect_network` crash with `'NoneType' object is not iterable` when it filters against `self.protected`.
2. **The platform traps live in `room_data` *locks*, not in the door/trap slots**, so they are invisible to the walk until unlocked — hence the up-front `apply_key('KT1'/'KT2')`, which lets the walk *use* the platforms for connectivity. They must then be **stripped** from the output: `1565–1568` are vanilla map features, **not writable ROM exits**, and re-enter only as *gated* edges inside `verify`. (Also why `room_of` — built from slots `[0]/[1]/[2]` — does **not** contain them; don't filter `KT_FORCED` through `room_of`.)
3. **Suppress verbose during the search.** The walk is extremely chatty and far slower with logging on; the search toggles `log.verbose._to_stdout/_to_file` off around the loop and restores them in a `finally`, then logs the *chosen* layout. Under `-debug` an unsuppressed search would emit hundreds of pages.
4. **Latent walks.py bug fixed here:** `Network.connect_network`'s verbose "Invalid network state" branch did `vprint(k.id, …)` where `k` is already a string room-id (→ `AttributeError`). The KT search is the first caller to exercise that path heavily; fixed to `vprint(k, …)`.

### Validation

Integrated method across 40 seeds (joint-verifier): **0 fallbacks, 0 invalid-or-softlockable layouts** (checked by an independently-written joint dead-state detector — all rooms reachable AND 0 dead states), median 0.60s (p90 2.71s, max 3.64s). Full `-ruin -rkt` ROM compiles (several seeds): every KT room reachable, every door/trap/pit used exactly once, no self-loops, no platform-id leakage into written exits.

**Regression and fix (2026-09): walk and verify must agree on the crossings.**
Commit `9bd584c` (2026-07-08) moved the platform ids from the trap range
(2182-2185) into the door range (1565-1568), because the crossings behave as
doors. From then on the lane walk treated each crossing as a two-way forced
door pair, but `verify()` still modelled it as one-way `a -> b`, so every
layout that used a crossing backwards was rejected. Vanilla fallbacks went
from 0/200 (legacy, 2026-06-09) to 16/200 (legacy, just before cutover) and
18/200 (v2, through 2026-09); bisected on the legacy engine to `9bd584c`.
Fix: `verify()` adds the reverse gated edge (two-way once its key is held),
and a follow-up commit derives every crossing table from room data so the
walk and `verify()` read one definition.
Result 0/200 fallbacks and the 200-seed sweep drops from 191 s to 28 s;
`tests/doors/test_ruin_submaps.py` now asserts 0/20 fallbacks. Lesson: a
data edit that changes an element's KIND (trap vs door) changes the
planner's semantics; any separate verifier must change with it.

**Open caveat:** several KT "rooms" share one physical SNES map (e.g. `KTa5a`/`KTa5b`/`KTb8` on `0x124`; many outdoor rooms on `0x14E`). The model is purely logical (room graph); whether parties can *physically* walk between lane regions on a shared map is map geometry the randomizer doesn't capture — worth a playtest on a generated ROM.

## Narshe Battle Exclusion + Ruination Boss Budget (2026-07)

The "Narshe Battle" check (room 22, Kefka @ Narshe, listed UNGATED in
`ROOM_REWARD`) is **deliberately unclaimable** in ruination: room 22 appears
in no `RUIN_ROOM_SETS` area, so its check is never registered during map
generation and is always backfilled as a dead check by events.py. Two
reasons (HansGR, 2026-07):

1. **Mirrored-map avoidance.** The check plays on Narshe Snowfield **WoB**,
   which mirrors the Narshe Snowfield **WoR** map already used for both a
   warp point and a dragon. Ruination avoids mirrored maps. It *could* be
   mirrored unobtrusively the way Opera House is (the WoR dragon only
   available after the WoB check completes), but the entry doors and the
   warp point would then need special logic choosing which map (WoB/WoR) to
   send the player to based on check completion.

2. **The unique-boss budget is spent.** Ruination uses every unique boss,
   including three transpositions: Doom Gaze → KT airship entry;
   Ultros 4 → Sealed Gate; **Narshe Battle → Ferry Boss**. Including the
   Narshe Battle check would require duplicating a boss or removing a
   transposition — both rejected.

**Guidelines if inclusion is ever attempted:** (a) add room 22 to a
Narshe-area room set; (b) implement Opera-House-style WoB/WoR mirroring
with completion-dependent routing for the Snowfield entry doors and the
warp point; (c) find the check a boss — either a new duplicate or by
unwinding the Ferry Boss transposition (which then needs its own boss).

## Ruination Esper-Capacity Corner (High Esper Counts) (2026-07)

Found by the 2026-07 v2 exercise (`tools/ruin_stress.py`), shared verbatim
with legacy. At extreme requested-esper counts (≥18, especially 27), plans
fail at rates up to ~48% whole-plan (derived) with `no-checks-left` /
`stuck-no-reserve`. Root causes:

1. **Pre-plan capacity overcount**: `pre_plan_character_acquisition` counts
   esper-capable slots in planned areas WITHOUT the `REWARD_OWNERS` filter.
   Checks owned by never-planned characters are permanently unclaimable, so
   believed capacity exceeds true capacity; plans die at N−1 espers with
   every claimable check spent.
2. **No esper-forcing rule**: only the last character-capable slot is
   forced (`process_rewards`); an item/character draw near the esper
   boundary can waste a needed esper slot.
3. At 14 requested characters the reserve pool is empty by construction,
   so stuck branches have no rescue (`stuck-no-reserve`).

Empirically (27 espers): pre-plan extension pulls a mean of 10.1/14
characters into the game regardless of the requested count (min 8, max 12,
~34/47 checks claimed) — the esper demand, not the character request,
determines the roster. Defaults (≤9 espers) have ample slack and are
unaffected (0/1000 whole-plan failures).

**Status: accepted for now** (fringe config; it builds, retries recover
most seeds). **Sanctioned future fix** (HansGR, 2026-07), if the failure
rate ever matters:

- Force a CHARACTER when it is the last character-capable slot and we do
  not have enough characters, OR we do not have enough total slots left to
  deliver all required espers (character areas are what add slots).
- Force an ESPER (never an item) once the character count is satisfied and
  the number of claimable slots remaining equals the number of espers still
  required — from then on every remaining slot must be an esper.
- Additionally, pre-plan should count only owner-satisfiable slots
  (owners ⊆ party ∪ planned) and keep planning characters until TRUE
  capacity suffices.

Implementation sites: `doors/plan/ruination/growth.py` `_choose_kind` /
`process_rewards` (forcing) and `_pre_plan` (capacity count); legacy
equivalents in `event/ruination.py` if ever backported.

## Post-Rewrite Structural Review + Commentary Sweep (2026-07)

The review pass after V2 completion (HISTORY.md milestone 22; commits
`06b1c88`…`931596a` + the commentary sweep). This section records the
doctrine those commits put in force and the deliberate non-fixes, in the
detail I'll want when touching this code again.

### Doctrine now in force

1. **No shared-table mutation, anywhere.** Mode adjustments are per-plan
   views: `plan.shared_exits` (town split for -drdc/-ruin, from
   `split_shared_view()` / `RuinConfig._shared`) and `plan.forcing`
   (ruination exclusions, from `RuinConfig.forcing`). Realization
   (`postprocess_door_map` conflict sets) and the spoiler
   (`Doors.print`) read the plan, never `data/rooms.py`. Ruination patch
   suppressions are view builders next to their tables
   (`entrance_door_patch_view` / `require_event_bit_view` in
   `data/event_exit_patches.py`); realization stashes them on `maps`.
   The force-explicit list is `maps.force_explicit_ids`.
2. **Exactly two blessed scratch tables**, reset in `Doors.__init__`:
   `exit_data` (dc-override rewrites partner entries; a read-only view
   is impractical — consumers span events AND realization) and the
   `event_exit_info` runtime address column (`reset_event_exit_addresses`;
   the `is None` guard means a stale address would silently survive a
   second in-process build without the reset). Do not add a third.
3. **`shuffle_transform` ordering is a seed contract**: protected doors'
   30000+ stand-ins are APPENDED after the room's other doors. The walk
   offers doors in list order, so changing this reshuffles every
   map-shuffle+door-rando seed.
4. **Never draw RNG at import.** Found the hard way: map_exit_extra drew
   `random.random()` at module scope (Darill/Daryl spelling flip). An
   import-time draw's stream position depends on which module imports
   the file first, so ANY import reordering silently shifts every seed —
   my args-time import of the planner moved the draw before
   `random.seed` entirely, which is how it surfaced. The flip now draws
   at its consumption site (event/airship.py, partner == 53). All 15
   goldens re-anchored once at `06b1c88`.
5. **One flag registry**: `INDIVIDUAL_AREA_ATTRS` in `doors/plan/modes.py`
   (INDIVIDUAL_FLAGS + the upper-narshe trio) drives
   `args.door_randomize`. New areas register in modes.py only.
6. **Element id space**: `doors/ids.py` is the contract. Literals in
   established range arithmetic are blessed; named constants are for
   spots where the number alone says nothing (planner synthetics).

### Deliberate non-fixes (agreed with Hans, revisit conditions noted)

- `-dv` stays bundled in RUIN_DEFAULT_FLAGS while ROM failures are being
  debugged. Consequence: every -ruin spoiler carries planner
  diagnostics, and the golden -ruin spoiler hashes include them. Remove
  it later → shrinks spoilers, decouples goldens from diagnostics.
- Verbose double-gating in realize (`if maps.doors.verbose: vprint`) is
  intentional extra verbosity control for door rando (may export to WC
  broadly later). Don't "fix" it to bare vprint.
- In-process rebuilds: door rando's resets are necessary but NOT
  sufficient — memory/space heap state and import-time event allocations
  also persist. A reroll server needs WC-wide work, not just door rando.
- `Transitions` reads several tables as module globals despite receiving
  `event_data` as a parameter. Converting the runtime-address fills to a
  passed view requires ending that dual access first.

### Deleted as dead this cycle (don't resurrect from old branches)

`apply_mode_table_adjustments`, `reset_room_tables`, `multi_events`
(empty table + never-taken reads), `has_event_entrance` /
`exit_event_addr_to_call` (superseded by entrance_door_patch),
`Doors.force_vanilla` / `door_rooms` / `door_descr`, `find_room_for_door`
(door_map.py), RuinPlan's six mirrored planner attributes,
`generate_map_image`.

### Golden-sweep operational lessons

- After rebasing Hans's concurrent pushes, RECAPTURE the baseline before
  measuring your own change: his gameplay/flag commits legitimately move
  -ruin outputs (default-flag expansion feeds `random.seed(seed+flags)`).
- ROM-only mismatch = realization/event-code change; spoiler-only =
  presentation/section order; both = planning/RNG stream. Use the
  pattern to locate the layer before diffing bytes.
- The sweep prints per-config lines; failed builds emit tracebacks that
  can push earlier lines out of a tail. When triaging, rebuild single
  configs against a `git stash` baseline and `cmp -l` the ROMs (byte
  runs cluster: one contiguous run = one rewritten event block; scattered
  single bytes = shifted pointers).
- Room ids/names are display-only in non-ruin spoilers, but -ruin
  spoiler paths print room ids and `-dv` prints planner diagnostics —
  registry/naming changes need only -ruin re-records, never ROM changes.

---

## Keyless One-Way Softlock — Walk Rule + Keychain-Lattice Verifier (2026-08)

First mapping softlock in months (preset `Ruin_C13`): a trap chain `pit 3068
(PHT01-ruin) -> exit 469<->1079 (HUB52-ruin) -> trap 2065 -> pit 3070 (CDA03)`
landed the player in CDA03, whose only door (482<->618, ZOZr04) sat behind the
`zr1` lock — no key, no way out. The old "initially locked exits can't serve as
entrances" rule (2026-02, above) missed it because the *landing region's* free
egress had been consumed by the mapping order.

Two complementary fixes (both in `doors/plan/ruination/`):

1. **Walk-side rule** (`extend.py` `valid_door_targets`): when mapping a
   key-released exit (`door_exit in w.initially_locked_exits`) into a cluster
   outside hub-and-upstream, if the region (cluster + downstream) contains a
   pit or has upstream, require **>= 2 free (keyless) door/trap exits** in the
   region. Deliberately narrow after two refinement rounds with Hans: a
   single-door, pit-free room (e.g. the Opera House) may still sit behind a
   lock — there's no other way in, so no softlock.
2. **Endgame verifier** (`finalize.py` `verify_no_keyless_oneway_softlock`):
   explores the lattice of achievable keychains by single-key expansion with a
   memoized reach BFS; for every randomized one-way (vanilla-matched
   `d2 == d1+1000` pairs and terminal landings exempt) requires the landing to
   escape to the hub — collecting keys en route — under every achievable
   keychain. 4096-state cap. Measured: 1.7ms mean / 14.7ms max (default),
   17.8ms mean / 285.7ms max (14char/27esper) — Hans: worth "a few wall-clock
   seconds ... for the player". Runs after `verify_no_character_gated_softlock`
   in assemble. NOTE: `doors/` is argv-free — no `log.verbose` import there
   (importing `log` parses argv); the cap falls back silently.

Tests: `tests/doors/test_keyless_verifier.py` — 5 cases built from the real
incident rooms (PHT01-ruin trap 2065 -> CDA03 pit 3070; ZOZr04 `zr1:[618]`;
ZOZr01 grants zr1; DAR14; UMA02 free-landing control). Per Hans: do NOT use
DAR13's 2059/3060 in tests — forced exits that can never be remapped.

Related: the spoiler header now logs `Commit <shorthash>[+]` ("+" = dirty
checkout) via `version.git_commit()` — hub deployments drift from branch tip,
and seed+flags only reproduce a map on the same code version. The golden
hasher strips the `Commit` and `Generated` lines.

---

## Floating Continent Save-Room Return — LoadMap Entrance-Event Flag (2026-08)

**Symptoms** (ruination, fresh post-Atma re-entry to map `0x18A` via the
save-room tube): statue scene froze after Kefka throws the sparkles, and the
Three Statues showed a wrong palette. Battle returns to the same spot were
fine.

**Root cause — one byte.** `save_to_x` (tube-maze Save Room -> FC return)
rebuilt the vanilla save-exit LoadMap from raw bytes with flags `$00`; vanilla
uses **`$C0`** = run entrance event (bit `$80`) + no auto fade-in (bit `$40`).
Its comment claimed the bytes "match vanilla flags exactly" — they didn't.
Skipping the entrance event (CA/F30A) on that reload lost everything it does:

- `60 0F 10` — load ROM palette $10 into CGRAM slot $0F = **sprite palette 7**,
  the statues' palette (the palette swap);
- `78` pass-through for the light NPCs $1D–$21 (the scene freeze: the
  thrown-light moves collide with the cast and wedge
  `WaitForEntityAct($21)/($1F)`);
- the arrangement subroutines that re-apply opened maze walls from the lock
  bits.

Battle returns never showed it because **entrance events replay on battle
return** — that's what the `$1B6` check inside them is for (skip only the
ambient/animation setup, keep palette + pass-through + tiles).

**Workaround falsified and reverted.** An earlier fix added five
`DisableEntityCollision($1D..$21)` in `statues_scene_mod` after the scene's
CreateEntity block. Once the flags fix landed, a neutralization A/B (swap the
`78 xx` ops for inert `41 xx` in the built ROM) showed the scene completes on
both paths without it — the entrance-event grant survives the
delete-lights/recreate cycle. Full 2x2: flags $00 without workaround = FROZEN;
either fix alone = OK. The workaround was compensation, not an independent
defect, so it was removed and the real dependency documented at both sites.
*Lesson: when a workaround and a suspected root-cause fix coexist, falsify the
workaround before keeping it "as belt-and-braces."*

**Diagnostic method — offline savestate diffing** (standalone-Snes9x `.00N`
files, s9xsnp format): gzip wrapper; header line `#!s9xsnp:VVVV\n`; then
`TAG:NNNNNN:payload` sections — `RAM` = 128KB WRAM, `VRA` = 64KB VRAM, `PPU` =
2652 bytes with **CGDATA (512B CGRAM) at payload offset 0x40** (sum of the
SnapPPU fields before it), `SRA` = SRAM. Our libretro core (snes9x 1.54.1)
serializes v0009; standalone Snes9x 1.60+ writes v0011 — can't live-load those,
so diff the sections offline. WRAM/event-bit diffs found `$1B6`; the frozen
event PC (WRAM `$E5-$E7`) pinpointed the wedge; the CGRAM diff isolated sprite
palette 7 (words 241–255) and killed two wrong theories (ambient queues,
arrangement subs — all decoded arrangement subs are maze-region tile edits,
none near the statues). FF6 keeps a CGRAM shadow in WRAM: sprite palette 7 =
**$7E73E0** (32 bytes) — a clean harness assertion point.

Commits: `e41603d` (workaround, superseded), `7ab34a5` (flags fix),
`bc8abe2` (workaround revert). The Top 10 "LoadMap Must Opt Into Entrance
Events" entry in CLAUDE.md is this bug's distilled rule.

---

## Battle MP Zeroing & MP-Drain Criticals (2026-08)

Why Illumina/Ragnarok auto-crits "require the Magic command" in vanilla — and
how WC now decouples that (`battle/keep_battle_mp.py`, unconditional).

**The vanilla mechanism is indirect — three cooperating pieces:**

1. **MP-crit** (C2/3F22, weapon special effect $07: Illumina, Ragnarok, Rune
   Edge, Punisher; dispatched per strike via the C2/42E1 table): cost =
   12 + rand(0..7); if attacker battle MP (`$3C08,Y`) covers it, deduct and
   force the critical. **No command check anywhere in it.** Only other gates:
   targets exist, and the no-critical bit (`$B2` bit 1 — set by Offering).
2. **Battle-menu setup** (C2/532C, per character at battle start): after
   building the 4 command slots, `LSR $F8` — bit 0 was set by C2/5445 iff the
   character has **Lore**, or **Magic/X-Magic with >= 1 spell known or an esper
   equipped** (the Magic/X-Magic menu function C2/5429 tests `$F6` = spell
   count, `$F7` = equipped esper, $FF = none; both set by C2/568D immediately
   before, which also stores the count to `$3CF8,X`; Gogo's party-mirrored
   menu counts into $F6 too; Umaro/guests always $F6=0/$F7=$FF). If the flag
   is clear: **STZ `$3C08,X` and `$3C30,X`** — current AND max battle MP
   zeroed. That zero is the entire "requires Magic" behavior.
3. **Battle-end writeback** (C2/496E region): MP copies back to the field stat
   (`$160D`) **only if battle max MP is nonzero** — so zeroed characters don't
   get their field MP wiped. Any change here must preserve this pairing.

**The WC change** (motivated by `-comfr`/`-compr`: characters can lack Magic
yet have MP, equip espers, learn spells): `battle/keep_battle_mp.py` replaces
the 15-byte zeroing epilogue (ROM 0x253f9–0x25407) with a JSR to a C2-bank
helper: keep MP if vanilla carry set (Lore loophole preserved as the first
check, verbatim `LSR $F8`), **or $F6 != 0, or $F7 != $FF** — i.e. exactly "the
battle menu would show a Magic command", per-character. Falls through to the
vanilla `PLP/PLX/RTS` at C2/5408. Stack note: the character offset vanilla
read as `LDA $02,S` becomes `$04,S` inside the JSR. Umaro/guests stay zeroed;
qualifying characters get working crits, meaningful Rasp/Osmose/Elixir, and
persistent MP drain.

Deliberately NOT the main-menu MP-display rule: C3/0D2B shows menu MP if the
**party owns any esper at all** ($1A69–$1A6C bitfield) OR Gogo OR the character
knows a spell (WC's `Lores.show_mp_mod` adds Lore-command holders). That
party-wide esper test would make crits near-universal; Hans chose the
per-character rule.

Verified in the harness (field char blocks force-edited, Ragnarok equipped,
commands Fight/Item only): spell-known character keeps 50/50 battle MP, drains
12–19 per strike, field MP persists the drain; no-spells/no-esper character
stays zeroed, no drain, field MP untouched.

Commits: `3983c6c` on `door_rando_ruin_rewrite`; cherry-picked as `a0e7123`
onto `feature/command-fully-randomize` (that branch predates `-ruin` and has
no golden manifest — code files only travel in cherry-picks to it).

---

## DISABLE_B_DASH Event Bit (2026-08)

`event_bit.DISABLE_B_DASH = 0x0c1` (verified vanilla-unused). The `-move bd` /
`-move ssbd` speed subroutine (`settings/movement.py`, Bank F0, hooked at
0x04e21) checks `$1E98` bit 1 (= `$1E80 + byte(0x0c1)`); while set, dash falls
back to SPRINT. Use it whenever an event breaks at dash speed.

Users:
- **Imperial Camp Kefka chase** (`event/imperial_camp.py`): set at camp event
  activation, cleared at all three reward finishes; `init_event_bits` clears
  it (all gated on movement being a b-dash variant).
- **Owzer's Mansion switching-door room `OWZr04`** (door-timer glitch):
  `data/event_exit_patches.py` `room_require_event_bit['OWZr04'] =
  {DISABLE_B_DASH: True}` (auto-propagates to `require_event_bit` on its doors
  586/587); its exits clear the bit via `exit_door_patch`/`exit_event_patch`.
  The legacy whole-map-0xCF dash disable in `settings/movement.py` survives
  only when OwzerBasement doors aren't randomized and not ruination.

`room_require_event_bit` is the general tool here: per-ROOM event-bit
requirements on entry, with the exits responsible for clearing.

---

## Headless Playtest Harness Patterns (2026-08)

Recipes that took real debugging to establish (see also `tools/playtest/README`):

- **`tools/playtest/regressions.py` takes the vanilla ROM positionally**
  (`python3 tools/playtest/regressions.py $SP/vanilla.smc`), not `-i`.
- **`route.route_from_start(spoiler, target)` needs the spoiler's `Map:`
  section** — written only when `-sl` AND a door mode (`door_randomize` /
  `map_shuffle` / ruination) are on. A build without `-sl` still writes a
  short settings-only `.txt`; routing then silently finds nothing.
- **Battle detection**: the battle actor table `$3ED8+{0,2,4,6}` is $FF-filled
  on the field and holds actor ids in battle — poll it; don't trust leftover
  monster stats in battle RAM as an "in battle" signal. At battle end battle
  RAM refills with $FFFF — filter those when sampling (an MP read of 0xffff is
  the end-of-battle fill, not a value).
- **Winning battles from a script**: mash A; pin monster HP to 1 and party HP
  to max each iteration (HP words `$3BF4+2*slot`, chars 0-3 / monsters 4-9,
  max at `$3C1C`). `-debug` makes enemies one-strike, but boss-rando bosses
  with reviving parts (Number 128) can still be unwinnable by mashing — pin HP
  or pick another route. Battle MP/max-MP: `$3C08` / `$3C30` (+2*slot);
  right-hand item in battle menu data: `$2B86 + 5*(slot/2)` (left hand +20).
- **Field character blocks** (`$1600 + 37*n`, n = actor for 0-13): +0x00
  actor, +0x09/+0x0B cur/max HP, +0x0D/+0x0F cur/max MP, +0x16..0x19 the four
  commands, +0x1E esper ($FF = none), +0x1F..0x24 weapon/shield/helmet/armor/
  relic1/relic2. Known-spell lists: `$1A6E + 54*actor`, $FF = learned.
  Editing these pre-battle is a clean way to force loadouts for battle tests.
- **A one-byte A/B beats a rebuild** when the tree has drifted: patching the
  byte(s) under test directly into a known-good ROM keeps the arrival
  recipe/RNG identical (rebuilding from a changed tree shifts encounter RNG
  and can strand the script in an unwinnable boss). Same trick works in
  reverse to *neutralize* a suspected-redundant fix (replace ops with inert
  same-length ops) and re-test.
- FC-specific: arrival at the statues map needs paced single A presses
  (hold=6, wait=60); the save-room hole exit is guarded by `$1B5`, which only
  cycles via real steps — teleporting to it does nothing.

---

## Mt Zozo Arrival Hardlock (2026-08, quick post-mortem)

Uploaded-seed hardlock on arrival at Mt Zozo: `mt_zozo.entrance_event_mod`
lacked a terminal `field.Return()` on the ruination-without-character-gating
path, so execution ran off the end into whatever followed. Sibling gotcha to
"entrance_door_patch must fall through" (2026-04, above) — but in the
*opposite* direction: entrance **event mods** must terminate with `Return()`;
entrance **door patches** must NOT. Check which of the two you are writing.

---

## Out-of-Battle Magic Submenu by Spell Knowledge (2026-08, SHELVED)

Implemented, verified, shipped as `5d3b541` (main) / `1a616b0` (feature
branch), then **reverted by design decision**: Hans polled playtesters and
they prefer the vanilla rule — a character without the Magic battle command
should NOT cast magic from the menu outside battle, even when they know
spells (e.g. natural magic under `-comfr`/`-compr`). The MP-crit change
(battle/keep_battle_mp.py) is unaffected and stands: such characters still
auto-crit in battle; they just can't menu-cast.

Kept here in case it's revisited — the implementation worked and its
verification passed; the full code is in the reverted commits.

**Mechanism** (what gates the menu): the Skills submenu rows are enabled at
C3/4D3D — all seven row bytes ($79-$7F) start greyed ($24), then each of the
character's four command bytes is matched against the row table at C3/4D78
(`02 02 07 0A 0C 10 13`); a match writes $20. The row byte is both draw
color and the selection gate (C3/208B: `LDA $79,X / CMP #$20 / BNE deny`) —
one gate, nothing else consulted. Spell knowledge never enters into it.
X-Magic (0x17) is not in the table, so an X-Magic-only character is also
locked out. WC already rewrote this region once (`menus/skills.py`
`espers_row_mod`): Espers row by character id (< 0x0C), other rows vanilla.

**The shelved change**: shave the espers-id tail of the in-place rewrite to
a `JSR` into C3 free space; helper applies espers-by-id, then enables the
Magic row ($7A) additionally when the character knows >= 1 spell — a $FF in
the spell-mastery list at `$1A6E + 54*id`, computed via the hardware
multiplier exactly like the menu MP-display check (C3/0D45). Union rule:
command-based enabling kept (Magic-command char with 0 spells keeps the
empty submenu; Gogo's command-configured Magic untouched); Gogo/Umaro
excluded from the overrides (id >= 0x0C — they have no spell-mastery table
to scan). Verified in the harness: row bytes $79/$7A per character +
opening/casting from the submenu.

**Why reverted**: the buff surface is global — ANY character who ever
learns one spell gains permanent out-of-battle utility casting (cure/heal
economy), not just natural-magic characters; playtesters preferred keeping
menu casting a Magic-command privilege.

**If revisited**: cherry-pick `5d3b541` back (plus its feature-branch twin),
or gate the helper behind a flag if it should be opt-in. The knows-spells
notion ($FF = fully learned) matches both the battle engine's count
($3CF8 via C2/568D) and the menu MP display (C3/0D2B), so the union rule
stays consistent with battle/keep_battle_mp.py.

---

## Battle Command-Menu Cursor Engine & the All-Invalid Hardlock (2026-08)

Probability commands (-comfr/-compr) can produce a character whose four
commands are all illegal while Imped (imp-legal = the CF/FE00 info-table
bit: Fight, Item, Magic, Revert, Mimic, Row, Def, Jump, X-Magic, Health,
Shock).  C2/527D then grays all four menu slots and the C1 command window
hard-locks: menu drawn, hand never placed, ATB stalled.  Fix:
`battle/command_menu_guard.py` (gated on `commands_probability_mode`).

**C1 facts worth keeping** (all found via `claude_reference/bankC1.txt`):
- Row validity: C1/7A4E — cursor memory ($890F,X, masked `AND #$03`) times
  3 into the character's menu block ($202E/$203A/$2046/$2052), tests bit 7
  of the slot's SECOND byte; carry clear = selectable.  Menu slot layout:
  byte0 command id ($FF/bit7 = empty), byte1 bit7 = grayed, byte2 aiming.
- THREE unbounded skip-invalid cursor loops consume it: initial settle
  C1/7AEF (`INC $890F,X / JSR $7A4E / BCS back`), and the second window
  layout's up/down navigation C1/7BE9 (DEC) and C1/7BF3 (INC).  With zero
  valid rows they spin forever (music continues — SPC700 is independent).
  The d-pad handlers of the first layout (C1/7AFD-7B89) are try-and-REVERT
  instead — bounded, safe.
- **No confirm-time validity check exists**: both A-press sites (C1/7BAA,
  C1/7BFF: `INC $96 / INC $2F41 / JMP $7CC8`) dispatch whatever the cursor
  rests on (C1/7CC8 → per-command jump table at C1/7CE9).  Vanilla's
  invariant "cursor only ever rests on a valid row" is what makes that
  safe — anything that relaxes the cursor rules must add the check.
- The guard: bounded scans (one full lap of all four rows, exactly what
  vanilla's loop walks; nothing valid → restore the entry row so the hand
  rests motionless on the remembered row) + guarded confirms (re-check
  C1/7A4E, swallow invalid presses; $96/$2F41 advance only on real
  confirms).  Two earlier versions were rejected/revised: un-graying a
  slot (REJECTED by design — Imp must actually forbid imp-illegal
  commands), and a 3-try scan that parked on row 0 on failure (revised
  2026-08: when the cursor's own row was the only valid one, a press
  parked the hand on the wrong row for a frame and the next frame's
  settle walked it back — visible per-frame hopping, since the hand is
  drawn once per frame from the FINAL cursor memory at C1/7BB2/7C23; the
  full-lap scan restores vanilla-identical behavior whenever any row is
  valid).  The resting hand keeps the real options live: Row/Def, L+R
  run, Y next-character.
- Menu rebuild trigger: setting Imp via WRAM ($3EE4,X bit 5) alone does
  NOT rebuild the menu — the engine rebuilds when **$3204,X bit 3**
  ("imp/mute toggled") is set (consumed by the C2/088C ASL-walk loop).
  Harness tests must set both.

**Diagnosis technique (reusable)**: reproduce the hang in the headless
harness, then build a PC histogram — `h.save_state()`, parse the s9xsnp
`REG` section (PB byte 0, S bytes 8-9, PC bytes 14-15, big-endian), sample
every few frames, and diff healthy-vs-stuck histograms.  The stuck-unique
hot PCs (here C1/18B0 multiplier + C1/7A52/7A6E) named the spinning
routine directly after static reading had stalled.  Stack unwinding from
S works for the first JSR/JSL frames but degrades past data pushes.

---

## Bank C1 Annotation Project — Status & Resume Notes (2026-08)

`claude_reference/bankC1.txt` is being annotated in the style of the other
bank decompiles (`ff6_bank_c2.txt`, `ff6_bank_c3.txt`).  **Paused, not
finished** — the file is fully usable at every checkpoint, since each pass
only adds prose.

### Ground rules

The applier **never** touches an instruction's address, byte or mnemonic
fields; it only appends `(comment)` after the mnemonic column and inserts
routine-header prose blocks between routines.  That invariant is
machine-checked:

```sh
git show f2827ab:claude_reference/bankC1.txt > /tmp/bankC1_orig.txt
python3 tools/annotate_c1.py check /tmp/bankC1_orig.txt   # 30568 lines unchanged
```

`f2827ab` is the commit that added the pristine (upstream) copy — that is
the only place the un-annotated original survives, so always diff against
it rather than trusting a local backup.

### Workflow

Per region: read a few hundred lines → write a directive file → apply →
periodically `check` and commit.

```sh
python3 tools/annotate_c1.py apply <directives.txt>
```

Directive format (documented in the tool's docstring): `C <ADDR> <text>`
adds a comment but skips a line that already has one, `C! <ADDR> <text>`
overwrites (and merges any existing `(from ...)` caller note), and
`H <ADDR>` followed by tab-indented lines inserts a header block before
that address.  Headers are applied bottom-up so earlier insertions don't
shift later ones.  The directive files themselves are scratch — once
applied, `bankC1.txt` is the artifact, so they are not kept.

### Coverage so far

~1,640 lines of new prose across 30,568 instruction lines.  Depth by
region (the menu/UI half got the deep pass; the animation half has only
structural banners so far):

| Region | Subsystem | Depth |
|---|---|---|
| C1/0000-1808 | boot, NMI, frame driver, math/DMA helpers | medium |
| C1/1808-4504 | sprite/OAM builders, VRAM plumbing | light |
| C1/4504-5529 | window draw states, list-row builders | light |
| C1/5529-5D99 | menu program dispatcher, per-command programs | deep |
| C1/5D99-66B1 | battle dialog engine, glyph renderer | deep |
| C1/66B1-6B47 | window/list text interpreters | deep |
| C1/6B47-7A4E | targeting engine | deep |
| C1/7A4E-8D98 | command window, all list menus | deep |
| C1/8D98-9196 | equipment window, dynamics entry | medium |
| C1/9196-A000 | dynamics script engine, battle messages | medium |
| C1/A000-FFFF | animation interpreter | light (banners only) |

### Resume here

Next region is **C1/A1EF onward** — the animation tile loader and its
bit-depth expansion/transfer plumbing (through ~C1/A4B2), then the
animation interpreter proper.  Planned depth for C1/A000-FFFF is
structural banners plus entry-point headers, not line-by-line.

Two useful things fell out of the passes already done and are recorded in
their own sections: the command-menu cursor engine (see "Battle
Command-Menu Cursor Engine & the All-Invalid Hardlock"), and the
observation that the Magitek command layout at C1/7C5A/7C64 carries the
same unbounded skip-invalid loops that `battle/command_menu_guard.py`
bounds in the main window.

### Known disassembly defects found (annotated in place)

The upstream disassembler lost byte alignment in a few spots; each is
flagged with a header explaining the real instruction sequence rather
than being silently trusted:

- **C1/5CF7** — menu program X = 18; the real code mirrors C1/5C91.
- **C1/78A1** — two bytes shown as `BIT $AA7B,X` are `TDC / TAX`.
- **C1/957C**, **C1/9609** — split CPX/BNE pairs shown as `BRK #$D0`.
- **C1/5EF8**, **C1/8280**, **C1/A013** — data tables shown as code.
- **C1/969A** — `LDX #$5800` shown byte-swapped.

One genuine **vanilla bug** was also found and annotated: **C1/6B0F**
reads `E6/F675`, a misaligned address inside the spell-name table, where
the parallel list path at C1/65CC correctly uses the Esper name table
`E6/F6E1`.


---

## World-Map Navigation in the Harness (2026-08)

Everything learned driving a real WC ROM from the airship deck to a
check on the far side of the world (Figaro Castle WOB throne room),
end to end, with `tools/playtest` (`Harness`, `navigate`).  Verified in
play on `-open` builds; none of it is mode- or branch-specific.  All
ROM offsets are headerless file offsets.

### Open-world start and the airship (map 0x006)

- `-open` seeds start on the **Blackjack deck, map 0x006, at (16, 6)**.
- The flight console is the tile event at **(14, 6)** (event code
  CA/F532).  It is an **A-press interaction, not a step trigger**: take
  two steps LEFT from the start, face LEFT, press A.  Stepping on or
  across the tile does nothing, and interacting from any other tile
  does nothing — which looks exactly like an unresponsive console.
- The console menu's **first option is (Lift-off)**; selecting it plays
  a short animation and puts you in mode-7 flight (map id reads 0x000).
- The deck holds WC utility NPCs, and `-debug` builds add more: a
  **teleport NPC at (15, 4)** to the debug room (map 0x009, one recruit
  NPC per character at (1..14, 8)), and at least one NPC that starts a
  battle when spoken to.  Careless A-presses near the top of the deck
  can drop you into a fight.

### Flight, and why not to bother with it

- While flying, the party/field object is **stale** — `party_xy` keeps
  reporting the deck coordinates and `set_party_xy` does nothing.  The
  flight position lives elsewhere (not `$1F61-$1F64`; the bytes that
  move during flight, `$009B-$009E`, oscillate like rotation state, not
  coordinates — never conclusively found).
- Screenshots mid-flight are not trustworthy anyway (see the
  stale-scroll note below).
- **The productive pattern: press B immediately after lift-off.**  B
  lands on the spot (in the tested seeds, right outside Narshe); after
  the landing animation (`run(600)` + `wait_for_control`) the party is
  **on foot on the world map**, where everything below works.

### On-foot world map: the position words

- On a world map `set_party_xy` **does not work** (it writes the field
  object block, which the world map does not use).
- The party's world coordinates are plain WRAM words: **X at `$00E0`
  (u16 LE), Y at `$00E2` (u16 LE)** — poke these and the party is
  there.  (`$1FA1` and `$005F` track Y in parallel — save/warp copies;
  writing `$00E0/$00E2` alone is sufficient.)  Walking works normally
  after a poke.
- **The screen does not re-render on a poke.**  Terrain and minimap
  catch up only as the party walks, so a screenshot right after a
  teleport shows the OLD location — trust decoded map data, not the
  screen.  (This cost a whole detour: probe screenshots "showed" ocean
  where the decoded map correctly said desert.)
- Coordinates are top-left-origin tiles on a 256×256 map and match the
  exit/event tables exactly: verified by teleporting to (84, 34) and
  walking UP into Narshe's world entrance at **(84, 33) → map 0x014**.

### Reading the world map from the ROM

- The WoB tilemap is compressed at **0x2ED434** (WoR: 0x2F6A56), FF6's
  standard LZ: `u16 compressed-size` header, then flag bytes (LSB
  first; 1 = literal, 0 = two-byte back-reference
  `offset = b1 | (b2 & 0x07) << 8`, `length = (b2 >> 3) + 3`) over a
  0x800-byte ring buffer whose write pointer starts at **0x07DE**.
  Decompresses to exactly 65536 bytes = 256×256 tile ids, row-major.
- Town/dungeon entrances sit on distinctive rare tiles (a whole-map
  tile-frequency scan surfaces every structure; tile 0x43 marks several
  entrances, Narshe's among them).  An ASCII render of a region with
  the dozen most common tile ids as characters is enough to locate
  deserts, bridges, coastlines by eye.
- **Figaro Castle is NOT in the tilemap** — like the airship it is a
  sprite overlay (graphics under "Misc. World Graphics", EE/579A sprite
  pointers), so no rare-tile scan or exit-table entry reveals it.  Its
  entrance is code in the world program.  Found empirically: **walk
  DOWN at (64, 74) on WoB → map 0x037 (castle exterior), arriving at
  (28, 42)**.  The sweep that found it: teleport across a grid, take
  one step, check `map_id != 0`.

### Routing tables (verified against built ROMs)

| table | pointer table | record | fields |
|---|---|---|---|
| tile events | 0x40000 (u16/map) | 5 B | x, y, event addr (3 B; + 0xA0000 for the file offset) |
| short exits | 0x1FBB00 (u16/map) | 6 B | x, y, dest (2 B; `& 0x1FF` = map id), dest x, dest y |
| long exits | 0x2DF480 (u16/map) | 7 B | x, y, size\|vert flag, dest (2 B), dest x, dest y |
| NPCs | 0x41A10 (u16/map) | 9 B | x = d[4] & 0x7F, y = d[5] & 0x3F, sprite = d[6], palette = (d[2] & 0x1C) >> 2; NPC ids start at 0x10 |

Records live at `pointer_table_base + ptr[map]`.  These four tables
answer "where can I go from here and what will I find" for any map
without booting the emulator.

### Figaro Castle WOB: the full route

From the world map: DOWN at (64, 74) → **0x037** exterior (28, 42).
Then walk **UP the whole way**, taking each transition as it comes:

    0x037 (28,42) --UP--> 0x03B hall (12,49)
    0x03B          --UP--> 0x037 upper courtyard (28,31)
    0x037          --UP--> 0x03B (27,28)
    0x03B          --UP--> 0x03A throne room (102,55)

Throne room: the check NPC (id 0x10) sits at **(101, 42)**; talk to it
from (101, 41) facing DOWN.  A `walk_until_transition(button)` helper —
hold a direction 16 frames at a time until `map_id` changes, then
`run(60)` — chains the whole route without knowing tile-exact door
positions.

### Harness gotchas that cost real time

- **Teleport-then-walk can leave the party stuck.**  Several probes
  placed next to a door via `set_party_xy` could not move at all in any
  direction, while the identical approach on foot (arriving through a
  real transition, then holding a direction) sailed through the same
  door.  Prefer natural walking from a real arrival; teleport only
  across open ground, and verify the party actually moves afterwards.
- `navigate.step_through` raises unless the **map id changes** — it
  cannot operate tiles that open dialogs or menus (the airship
  console).  Drive those with explicit hold/press.
- When a tile seems dead, dump the map's tile-event table, then try
  both stepping on it and pressing A at it from each adjacent side.

### The party-select (Lineup) screen

Reached from recruit scenes (`REFRESH_CHARACTERS_AND_SELECT_PARTY`):

- A on a roster character adds them / picks them up; **A on a character
  already in the group opens their Status screen** (B backs out — easy
  to mistake for a softlock).
- **START confirms** once at least one member is placed, then the scene
  continues on the field.
- Blind A-mashing does form a group eventually, but the robust script
  is: A once or twice, B (in case Status opened), then START.

### Verifying outcomes in WRAM

- Recruited characters: bitfield at **$1EDC/$1EDD** (bit = character
  id); available bits at $1EDE.
- Espers owned: bitfield at **$1A69+** (bit = esper id).
- Inventory: item ids at **$1869-$1968**, counts at **$1969-$1A68**
  (0xFF = empty slot).
- These plus a screenshot of the receive dialog make a complete
  end-to-end check proof without trusting any menu.

---

## Race ROM Obfuscation — Pointers, Resource Claims & Lessons (2026-09)

The `-race` feature (public flags, secret seed, distributed ROMs) lives on
`feature/race-obfuscation`, forked from `34abad1`; it is not merged here
yet.  Its own documents are the authority — read them there:

- `RACE_OBFUSCATION_OVERVIEW.md` — admin-facing summary: what is protected,
  attacker tiers, player-visible differences, shared resources claimed,
  and (appendix) the **developer recipe for converting a check**.
- `RACE_OBFUSCATION_PLAN.md` — design history, phase by phase.
- `RACE_OBFUSCATION_REVIEW.md` — end-of-phase code review: what was
  consolidated, and the pending resource reductions.
- Code: `obfuscation/` (keying, claim, relocate, mask, rewards,
  veldt_battle), `instruction/field/race.py` (the reward command family),
  `tools/verify_race_build.py` (~1700 checks), `tools/race_slot_map.py`,
  `tools/race_redteam.py`.

**Design in one paragraph.**  Every spoiler-valuable table (chests,
shops, esper spells, steals/drops, coliseum, and one unified
`(kind, id)` check-reward table) is relocated into a 32 KB claim at
`0x340000`, XORed with a per-seed pad, and replaced at its vanilla
address by a decoy generated by the *same* randomizer under a
domain-separated RNG.  Readers are patched to JSL decode shims.  Check
scripts carry only an opaque slot: one grant opcode decodes and
dispatches by kind; one dialog opcode picks the wording; `<reward>`
renders names at draw time; an umbrella opcode (`$EC sub slot …`)
re-enters the vanilla entity handlers with the decoded character id so a
recruit scene (create/show/act/party/theme/name/hp…) runs without the id
in the script.  NPC records get a decoy sprite and are repainted at map
entrance.  Non-race builds are byte-identical to before the feature.

**Shared resources it claims (coordinate before merging here).**

| Resource | Race branch | Collision with this branch |
|---|---|---|
| Field opcodes | `$E6` grant, `$FC` umbrella (the reward dialog is vanilla `$4B` with operand bit 13 set — a bit `$4B` masks away and no WC dialog id reaches) | **None.**  Chosen as the two vanilla-unused bytes free on both branches (the feature originally used `$9E`/`$EC`/`$EE`; `$9E` is `SetYNPCGraphics`, `$EC`/`$ED` the ruination recruit hooks).  `$EE`/`$FF` remain free everywhere. |
| Bank C0 | 20 bytes: five 4-byte stubs (two opcode trampolines, the message-code entry, two `JSR/RTL` wrappers) | none — every handler runs in bank F0; the opcode table needs only C0 entry points. |
| Expanded ROM | claim at `0x340000`, sized from its tables (~20 KB) | Music randomizers / door rando use expanded space — the claim is `Reserve`d so overlaps fail loudly. |
| Dialog control codes | `$1C` `<reward>`, `$1D` `<reward2>` | none (vanilla-unused). |
| Battle text `$12` sub-codes | 4 and 5 | none; relocates the 8 data bytes at C1/5EF8 into F0. |
| Bank C1 | 16 bytes of JML/JSR stubs | none. |
| RAM / event bits | `$0584` (unused since FF6j); multipurpose event bit 0 | none known. |

**Sharp edges (each one cost a playtest bug).**

- *B high byte*: `slot*2` via `REP #$20 / AND #$00FF / ASL / TAX / SEP
  #$20` leaves the accumulator's high byte set for slots >= 0x80, and
  vanilla handlers' `TAX/TAY` with 8-bit A transfer it — indexed writes
  land 0x100 off.  Always `TDC` before re-entering vanilla code
  (`race._index_slot_src`, verifier-guarded).
- *Reward table entry order is `(kind, id)`*, kind first.
- *Create wipes repaint*: a scene that `$3D`-creates its reward NPC
  re-derives the look from the record; repaint after the create.
- *Entrance-event flag*: a scripted `LoadMap` with flags bit `$80` clear
  skips the entrance event, so entrance repaints never run (same root
  cause as this branch's "Floating Continent Save-Room Return").  Repaint
  inline after such loads.  Bit four times in playtest: Narshe Moogle
  Defense (chase/collapsed loads), Narshe Battle (CC/C673, flags
  `$40`, the reload that Kefka's arrival plays on; the second reload at
  CC/C850 has `$C0` and repaints, which is why the sprite "became"
  the character when the battle event started), Umaro's Cave
  (the carving room 0x11B has no exits into it - only the fall from
  0x119 at CC/D989, flags `$40`), and Imperial Camp (battle map 0x077,
  entered only by the "Cyan rushes in" load at CB/134C, flags `$40`).
  Object RAM: the sprite index of object n is at `$0867 + $29*n + $12`
  (and `+$19/+$1A` change with the palette) - dumping that byte across
  a scene shows exactly when a repaint lands.  Game loads DO run the
  entrance event (saved at the snowfield save point, reset the core
  with `lib.retro_reset()`, reloaded: the repainted npc was right), as
  do battle returns.  `tools/race_entrance_audit.py` on the race branch
  does the scan below for every repaint map and found three more sites
  (Mobliz Phunbaba reload, Kohlingen inn sleep, Esper Mountain crack
  landings); an unconditional `field.Branch` is 6 bytes (`C0` + an
  always-clear bit + address), a `Call` 4 - size reserves accordingly.
  Finding them: scan the event banks
  (file 0x0A0000-0x0EFFFF) for `6A/6B <map lo> <byte2 & 3 == map hi>`
  and read the flags byte; a map with no exits in the short/long exit
  tables is script-entered only.  Diagnosis trap: a debug-room warp
  with `entrance_event=True` hides this bug class - warp with the flag
  the real load uses.  Battle return does run the entrance event
  (observed: the post-battle npc showed the repaint without any
  scripted repaint).
- *Re-emit fades*: reserving over vanilla bytes that fade the screen back
  in (post-battle `96 5C`) leaves the screen black.
- *Guest character objects leak into the lineup*: `$3D` on a character
  object (`$00-$0F`) sets that character's `$1850+id` availability byte
  (observed `$C0` for the FC escape guest `$0F`).  WC's
  `REFRESH_CHARACTERS_AND_SELECT_PARTY` deletes and re-creates only the
  fourteen real characters, so a guest left alive shows in the party
  select as a nameless Shock-wielding copy of whatever sprite it was
  last painted with, until some later select deletes it.  Always
  `DeleteEntity(guest)` + refresh before the select (the FC esper arm
  did; the race character arm did not - fixed 2026-09).  Quick repro:
  a debug-room npc that creates `$0F`, refreshes and calls the select.
- *No kind-conditional slot registration*: `AddItem`/`AddEsper`/receive
  dialogs register a reward slot when constructed; one kind-conditional
  build path shifted every later slot between seeds (Lone Wolf's moogle
  room).  Verifier tripwire: equal slot counts across two seeds.
- *Slot numbers are seed-specific by contract* — never map slot → check
  across seeds; run `tools/race_slot_map.py` for the build in hand.

---

## Phantom Train Car Bits on One-Way Landings (2026-09)

**Symptom** (hub seed `mgw54jqqi32s`, `-ruin hard`): the planner's route to
the Falcon went Veldt Cave boss trap -> pit 3066 (Car 2 interior) -> "Car 2
Right Exit" (1524) -> Esper Mountain pit room; in-game the right exit put the
player in Thamasa (1516's partner, Car 1's right exit).

**Mechanism.** Cars 1/2/3 interiors are ONE map (0x91) with the exit tiles
at the same coordinates ((1,7)/(30,7)); the tile's vanilla dispatch reads
`$180` (car 3) then `$17E` (car 2), else car 1, and jumps to the
car-specific script (1514/1523/1515... at their own addresses). Entering a
car by door sets the bits through `require_event_bit` (keyed by the interior
exit ids 1515/1516, 1523/1524, 1514). A randomized one-way landing in a car
reuses the vanilla trapdoor script's LoadMap only (`Writing: 2075 --> 2066`
keeps `6b 91 ...` and the continuation call, not the `d2 7e db 06 da 07 ...`
prefix), so the bits stayed whatever they were - clear - and the exits acted
as Car 1's. With no other way into Car 2 in that seed, the branch's terminus
was unreachable by the intended route.

**Fix.** `require_event_bit` entries for the two landings. Note the key:
`Transition` builds a pit entrance as `EventExit(entr_id - 1000)`, so pit
entries are keyed by their TRAP id (2065 car 1, 2066 car 2), like the Lete
River entries 2035/2037 - a `3066:` key is silently ignored (found out the
hard way). Golden manifest re-recorded (transition bytes changed in every
door-rando config).

**Workaround on an existing ROM**: set `$17E` first by entering any Car 7
interior tile (all of 1539-1543 set it and never clear it) - in that seed
Car 2's left outside door led into the Car 7 cabin - then take the one-way.
Verified in-emulator on the player's ROM: direct -> Thamasa, detour -> Esper
Mountain; fixed ROM direct -> Esper Mountain.

**The class, audited.** `tools/oneway_bit_audit.py` decompiles the exit
half of every trap and event-tile door script and lists its event-bit
writes against `require_event_bit` coverage. 22 scripts write bits there;
after this review 11 remain uncovered and are judged fine: music-only
(`TEMP_SONG_OVERRIDE` etc.: Umaro jump, Cid's elevator, Daryl quick exit,
Serpent Trench jump), source-side or map-local (Zone Eater tract menu bit,
multipurpose-map bits, Lete raft clears re-applied by the cave entries), or
handled by WC's own event code (burning house avoids `$507`, minecart NPC
bits, Wrexsoul landing NPC bits, dream locomotive's multipurpose clears -
deliberately left). One more was fixed with the train: the Owzer
floating-chest drop (trap 2019) sets `BRIGHTEN_OWZER_BASEMENT`, read by the
basement entrance event (CB/4629), so pit 3019 now sets it on any arrival.
Run the audit after touching an exit script or the table.

**Also learned.** `-debug_dest` (and any non-graphics flag) is part of the
RNG seed (`args.seed_rng_flags`), so a route query rebuilds a DIFFERENT
map; `-debug` alone is safe and prints the branch terminus routes in the
spoiler. To identify an uploaded ROM's seed/flags, rebuild candidates and
compare the exit tables (0x1fbb00-0x1fda00, 0x2df480-0x2dfe00) and the
title hash; the school doors are (93,45)/(99,45)/(108,45) on map 104, and
the exit-table rows are rewritten, so read them by owner map + position, not
by atlas index.

## Albrook Dock Sailor Showed General Leo (2026-09)

**Symptom.** Some ruination seeds had a General Leo sprite on the Albrook
dock as the NPC who starts the custom boat event (aesthetic only).

**Mechanism.** The dock NPC (map 0x14C, NPC 0x22) is a vanilla General Leo
record (sprite 16, palette 0) whose visibility bit `$565` is set by
`event/albrook_wob.py init_event_bits` whenever `'Albrook' in
args.ruination_areas_used`. The sprite promotion to the sailor (54) lived in
`_ferry_install_enabled`, which only runs with two or more mapped ports, so
a lone mapped Albrook (e.g. `mgw54jqqi32s -ruin hard`) left Leo standing
there with the "disabled" message. The palette was never set either, and
sprite 54 wears palette 1 in every vanilla NPC record.

**Fix.** `fix_ferry_connections` now sets sprite and palette
(`FERRY_PORTS['Albrook']['sailor_palette']`) on the same condition as the
visibility bit, before the enabled/disabled split. Golden `ruinsep`
re-recorded (one byte: the record's palette bits).

## Walk Reachability Rules G/H + Short Restarts (2026-09)

Found while writing the map-construction retrospective: the door walk
(`doors/plan/walk.py`, every non-ruination mode) guaranteed consumption and
a DAG-clean cluster graph, but **never that the player can get out**. Rules
A-F are counting rules; a fully consumed cluster contributes nothing to
them, and `walk()` returned the moment everything was matched, before any
check. The structural validator checks consumption only.

**Serpent Trench (`plan_dre(seed=1001)`).** Forced currents: 01a->01b,
01b->01c, Nikeah->start. The walk sent start->01a->01b->Nikeah->start,
consuming the home loop's last pit while 01c (forced from 01b) and the caves
were still downstream, then closed 01c->03c->03a/03b->02->01c into a sealed
loop. Cave map 0x0AF has only the 529/530 exits, so no unmodelled escape.
Over 200 `-dre` seeds a model-level check flagged 164 pool layouts (Zozo WoR
108, Zozo 27, Serpent Trench 15, Cyan's Dream 6, Phantom Train 5, Magitek
Factory 2, Owzer 1). The Zozo ones escape in game through the clock passage
the pools leave out (2061/2063); the others were not playtested.

**Rules G/H (`plan/prune.py check_home_reachable`).** Home = rooms touching
the outside world (`walk.home_rooms`: 'root' + 'branch' rooms; -drdc 'root'
only; else the start cluster; KT lanes disabled). E = home + upstream (can
get home); R = home + downstream (reachable). While a cluster is outside E:
E keeps an entrance (G2) and the cluster + downstream keeps an exit (G1).
Mirror for R (H1/H2). Locked elements count. Both are necessary conditions,
so pruning is sound; with `final=True` any cluster outside E or R fails the
finished map. Rooms with no elements at all (`walk.inert_rooms`) are
ignored: under `-dre -maps` the map-shuffle transform drops Zone Eater's
ids (IGNORE_MAPS), leaving `MAPr-ZON` empty, and H would otherwise call
every state "sealed from home" (caught by the `dremaps` golden build). This is the walk-level form of ruination's "never consume the
hub region's last entrance".

**`-drx` failures and slowness.** Seed 1013 (planner seed, `plan_drx`)
failed after 5 x 50,000 connections (319 s); 6 of 14 seeds took 60-213 s.
Every failed attempt reached 1-3 unmatched elements at depth ~150, then
burned the budget backtracking the last ~12 levels. Closest state of the
first attempt: the start region had no elements left while four clusters
were cut off - one held Daryl's Tomb key `dt3` and forced pit 3060, whose
only feeder is the `dt3`-locked trap 2060 in a cluster reachable only from
the first (a circular key dependency). The mistake sat 10+ levels up, where
chronological backtracking never gets. A successful attempt needs ~180
connections, so the fix is **short restarts**: `run()` spends the same total
budget (attempts x budget_limit) in tries of `restart_budget=2000`
(attempts=1 callers - KT lanes - keep one full try). -drx: 14-34 s, 0/20
failures. Restarts also cure Zozo WoR, whose dead-end pre-pass (not
backtracked) is infeasible 64% of the time: with G/H and 5 fixed attempts it
failed 10% of plans; with restarts 0/400.

**Tried and dropped: Rule R**, an optimistic-completion reachability check
with a key fixpoint (catches the `dt3` cycle directly). Sound, but it made
each walk step ~1.6x slower on the 250-room pools, and short restarts alone
already recover from what it catches.

**Known limits.** Home detection is by room-name tags; an explicit per-pool
home list would be sturdier (and could name scripted exits such as Cyan's
room if wanted). The order-aware keychain verifier from ruination is not run
for door-rando modes (a naive port flags vanilla-matched pairs; it needs the
same exemptions). Every door-rando seed changed; goldens re-recorded.
Tests: `tests/doors/test_home_reachability.py`.

## Terminus Already-Used Events (2026-10)

Each KT terminus already locked itself after one party used it
(`SEALED_GATE_TERMINUS_USED` 0x14A, `AIRSHIP_TERMINUS_USED` 0x14B,
`ESPER_MTN_TERMINUS_USED` 0x14C). These events only tell a returning party
so, with one shared dialog "This path is closed. / Gotta find another way…"
(`data/ruin_constants.py` `TERMINUS_USED_TEXT`, allocated once through
`dialogs.allocate_shared_dialog(TERMINUS_USED_DIALOG_KEY, ...)` - a new
allocate-once-per-key wrapper around `allocate_dialog`).

| Terminus | Where | Behaviour |
|---|---|---|
| Esper Sanctuary (map 0x177) | the existing entrance music tile (16, 9) | after the song: hold screen, camera down 8 to show where the (gone) warp point stood at (17, 20), dialog, camera back. Once per entry: the tile already sets `multipurpose_map(1)` (cleared on map load). |
| Sealed Gate (map 0x187) | new tile at the foot of the stairs (8, 13) | hold screen, camera up 6 (centres the gate, rows 5-7), lightning (`self.lightning_strike`), dialog, camera back, party steps down to (8, 14). Fires every time. |
| Falcon (map 0x12d) | the existing bottom door tile (7, 25) | if used: dialog, then the party steps diagonally back up the stairs to (8, 24) (`MoveDiagonal(UP, 1, RIGHT, 1)`), so it repeats on every approach; else the usual load of the Falcon. |

**Why (8, 13) and not "four tiles above the entrance".** The approach widens
from the 1-wide entrance corridor (x=8, y=20-21) to a 13-tile landing
(row 17 is x=3..15, rows 15-16 x=1..15) before narrowing to the 1-wide
stairs (x=8, y=10-13). A single tile on the landing can be walked around;
the stairs are the only choke point. Measured by flood-filling real steps in
the emulator (teleporting with `set_party_xy` onto arbitrary tiles bypasses
collision and reports every tile walkable).

**Harness notes.** On the Daryl's Tomb staircase the last step is diagonal:
LEFT from (8, 24) lands on the door tile (7, 25). After `load_state`, start
a move with a short tap (`run(2); hold(btn, frames=4); run(24)`); a long
hold right after a restore can be dropped. Setting `SEALED_GATE_OPENED` by
hand skips the opening cutscene, which can leave gate sprites missing in
screenshots - not a bug in the event.

## Harness Recipes from the Race Project (2026-09)

Additions to "Headless Playtest Harness Patterns" that came out of the
race playtests (all with `tools/playtest`, `Harness`, `navigate`).

- **Transplanting a user's snes9x savestate.**  A `.000` savestate is
  gzip; inside, `#!s9xsnp` blocks with `NAM:len:` headers.  Copy ONLY
  the `RAM`, `SRA`, `VRA`, `REG`, `DMA`, `FIL` blocks into a fresh
  harness state at the matching offsets — transplanting the whole CPU/PPU
  state wedges the core.  That was enough to reproduce a hardlock from a
  player's save, instrument the ROM with a shim, and confirm the fix on
  the same save.
- **Reaching any scene fast: a temporary debug-room warp NPC.**  In
  `event/debug_room.py` add `_add_teleport_npc(self.DEBUG_ROOM, 6, 10,
  direction.DOWN, <map>, <x>, <y>)` (local only — never commit), build
  with `-debug`, then: deck (16,6) → `set_party_xy(15,5)`, face UP, A →
  debug room → `set_party_xy(6,11)`, face UP, A.  NPC talks sometimes
  need 2-3 attempts (re-poke position, `hold('UP',4)`, `press('A',
  hold=8)`).  Pass `entrance_event=True` to the LoadMap when the scene is
  triggered from the map's entrance event; loading straight onto a tile
  event fires it (Doma: map 0x78 tile (33,42)).  Find tile events by
  decoding the map's event table (`0x40000` + 2*map → 5-byte records
  `x, y, addr24`) instead of walking blind.
- **Event-engine state for a hardlock**: script pointer `$E5-$E7`; wait
  flags `$E1` (`$80` = waiting on an object, `$E2` = which); call stack
  `$0594+` (3-byte frames, index `$E8`, sentinel `CA0000`); last opcode
  `$EA`, operands `$EB-$EF`.  A stuck event with `$E1` set on entity 0
  meant a vanilla handler had been entered with the wrong B (see the
  B-high-byte edge above).
- **Field objects**: `$0867 + 0x29*n`, tile X/Y at `+0x13/+0x14`; n
  0x10+ are map NPCs.  Dumping them answers "is the NPC really there?"
  when a screenshot lies (camera does not follow `set_party_xy`).
- **Battle**: enemy HP words `$3BF4 + 2*i`, i = 4..9; pin to 1 and mash
  A.  "Enemy hp 1" *before* the battle starts is stale RAM, not a battle
  — wait for the field to actually go dark/return.
- **Byte-identity as the refactor oracle.**  For code motion or helper
  extraction, build the *race* ROM for two seeds before and after (not
  just the non-race build) and `cmp`; three differing bytes is a branch
  target, hundreds is an allocation shift.  Dump the differing ranges
  and disassemble both sides before deciding whether it matters.
- **Static verification of an injection**: follow the `Call`/`Branch`
  operand (`+0xA0000`) in the built ROM and read the block back; the
  `$EC 0C slot 02 / C0 A0 01 dest` prefix is the runtime kind branch,
  `9E slot` the grant, `EC 0A slot` the theme.
- **Lineup screen**: `A, A, B, B` (second A opens Status; B backs out;
  second B confirms when a group already exists).

## Starting Level Random (`-stlr`) (2026-10)

`-stlr MIN MAX` (`--start-level-random`): each character starts at its own
random level in MIN..MAX (3-99), mutually exclusive with `-stl`. Merged
upstream as ff6wc/dev `b4cff32` (PR #172), branch
`feature/starting-level-random`. Requested as `-slr`, which clashed with
`--start-lores-random`.

**Vanilla mechanism.** `C0/9F78` sets a joining character's level to the
average of the *available* characters' levels (`$1EDE` bits), or to a constant
when nobody is available (`C0/9FC5 LDA #$03`; `-stl` patches the immediate at
`0x09fc6`). `-sal` raises recruits to the roster average (the new recruit is not
part of the average), and is meant to override `-stl`/`-stlr` for characters
recruited in the field.

**Patch** (`data/characters_asm.set_random_starting_levels`): `Reserve
0x09fc3-0x09fc7` becomes RTS / NOP / JMP to a lookup in free C0 space:
`TDC; LDA $EB; CMP #16; BCS default; TAX; LDA table,X; RTS` with a 16-byte
per-character table. The rolled levels are listed in a "Starting Levels"
spoiler section. Uses only C0 free space and no event bits, so it composes
with door rando and ruination. Ruination injects `-stl 6` (easy too, since
the 2026-10 easy rework), so `args/ruin_preprocessor.py` groups `{'-stl', '-stlr'}`: a user
`-stlr` replaces the injected `-stl` instead of failing argparse's mutual
exclusion (merged into this branch 2026-10-12).

## Command Probability Modes (`-compr`/`-compru`) — Rolls, Unique Pool, Calculator (2026-10; superseded 2026-10-29, see "Command Randomization Overhaul")

Prompted by a player report that Shock showed up far more than its 10% in a
flagset with `-com 98989898989898989898989898 -compr ...`.

### How a character is rolled (`data/commands.py`)

1. `-com` explicit picks claim their slots first; 97 holds a slot empty;
   98/99 *reserve* slots for unique/random backfill **before any roll**.
2. `roll_probability_commands`: declarations (`-compr` plus `-comfr` folded
   in) are grouped by percent, highest first, shuffled within a group; each is
   rolled **at most once per character**, stopping when the free slots are
   full. Gau never rolls Fight, so with Fight/Magic/Item at 100% he has two
   skill slots and everyone else one (13 skill slots per seed).
3. Leftovers backfill from the pool: 21 randomizable skills minus `-rec`,
   minus Morph once declared or placed (only one character may hold Morph).

**The report explained:** the `-com 98` marks took every skill slot before
the rolls, so the 25%/10% declarations never applied; every pool command came
from the unique draft and landed in 13/19 ≈ 68% of seeds. **A roll percent is a
per-character chance, not a seed frequency**: a tier is only reached when
every higher tier missed, and a seed has 12 characters, so per-seed odds
compound. Players think in seed frequencies; see the parked tiered-mode idea
below.

### Unique means unique across the seed (PR #173, ff6wc/dev `283d9ef`)

Before the fix `-compru`/`-comfru` only kept the backfill draft unique among
its own slots: rolls were independent (a 100% skill went to all twelve) and the
draft restarted from the full pool. Now one `UniquePool` per seed counts every
skill dealt (explicit, rolled, random fill, draft) and only offers a character
the **least-dealt** legal skills it does not hold, so no skill repeats while
another has been dealt fewer times. In the unique modes the rolls use it too
(a dealt skill is skipped without a roll), characters roll in random order,
and 99 random fills run before the 98/unique draft (matching legacy `-com`).
Counting replaced the old draft refill, which could strand a skill the drafting
character already held (Runic dealt once while ten skills had three).
Consequence: with 13 slots every seed has 13 distinct skills, so seed
frequencies sum to 13. The player's tuned flag
(`100.100.100.12.10.10...` with Shock 2) gives common 61% / rare 26% / Shock 11%
under `-compr`, but 76% / 53% / 33% under the new `-compru`.

**Suplex A Train** (review follow-up, same PR): `guarantee_blitz` now runs
*before* backfill and sees explicit and rolled skills; if nobody holds Blitz
it is dealt into one open backfill slot (counted by the pool), else, with no
backfill slot left, a rolled skill (never explicit or Morph) gives way. It
previously overwrote a backfilled slot even when Blitz was already rolled or
picked, giving two holders. Tests: `tests/test_commands.py`
`test_suplex_train_blitz` (objective switched on).

### Measuring without a ROM

`mod_probability_random_commands` runs on stand-in characters: set
`sys.argv`, `import args`, stub `sys.modules["objectives"]` with
`suplex_train_condition_exists`, give `Commands` a list of 0x20 objects with
`.commands = [0, 0, 0, 0]`. 20,000 seeds take ~12 s and match 1000 real ROM
builds. This is the ground truth for any command-distribution question (the
same pattern as the invariant scripts in `tests/test_commands.py`).

### The calculator (`compr_calculator.xlsx`, delivered to Hans, not in the repo)

- **Flag Builder**: one row per command (percent, `-rec` x), outputs per
  non-Gau character and per seed for `-compr` and `-compru`, plus ready flag
  strings. `-compr` model: each command's keep chance = p × P(fewer than 4
  earlier successes), Poisson-binomial over higher tiers via elementary
  symmetric sums plus the within-tier shuffle. Backfill (rebuilt 2026-10-13):
  a character with b open slots after rolling r pool skills deals a given pool
  skill with chance b/(pool - r), multiplied out over the 12 characters.
  `-compru` model (rebuilt 2026-10-13; "Model Unique" plus hidden MU sheets):
  12 turns, Gau at a uniform position. Per turn, each tier's chance of K
  skills still unrolled (MU Counts) gives the availability; one character
  rolls tier by tier (MU Rolls), with a tier's surplus successes resolved by a
  random subset (hypergeometric, MU Const). The seed's rolled-skill total R
  comes from the tiers' own counts, since a skill is rolled at most once; the
  characters' joint (MU Joint) supplies only how F/M/I varies with R. The draft
  is then exact given (F, R): D = 48 - F - R open slots, U = pool - R unrolled
  skills (+1 if a declared Morph is among the R), each drafted with chance
  min(1, D/U). Accuracy on 104 random flag sets against the real code:
  typically 0.5 points, 9 in 10 within 1.3, worst 2.8 (in-a-seed, tier
  averaged). `-compr` on 48 sets: typically 0.5, worst 1.8. The previous
  mean-field version was off by up to 35 points on sparse declarations.
  Python twins: `compr_model_u4e.py` and `compr_twin.py` (variant `new2`) in
  the session scratchpad.
- **Calculator** tab: tier-based `-compr` only.

### Ruination default (2026-10)

`-ruin` (and easy/hard) injects `-compru` with Fight/Magic/Item 90%, every
skill 24% and Possess 12% (no `-com`, no `-rec`: a declared skill cannot be
excluded). Under seed-wide uniqueness the regular skills sit near 81% of seeds
whatever their percent (about 16-17 skill slots for 21 skills); the main
tier's percent sets how many slots are left for the unique draft, and so how
often the lower-tier Possess (and roll-only Morph) appear. Measured with the
real code (20,000 seeds): 12/11 gives Possess 67% vs 80%; 24/12 gives 40% vs
81% (Morph 73%). Since 2026-10-16 Shock shares Possess's 12% tier (players
asked for both at half the seeds of the rest): Possess 41.1%, Shock 42.0%,
others 82.7% (0.50x / 0.51x; Morph 75.7%).

Expensive checks (2026-10-15): Tzen's thief and both Auction House slots are
`BONUS_ESPER_CHECKS` (`data/ruin_constants.py`). They stay mapped and can hold
an esper or item, but the planner never counts an esper there toward the
required espers (`RewardsObtained[1]`), the available-esper count, or the
pre-plan's esper slots. Before this, 25% of standard seeds (28% hard, 16% easy)
met their required espers only through them. The planner also honours `-ame`
now: at `-ame 1` (the ruination default) the 10,000 GP slot ("Auction House_2")
is item-only, as in the event; it used to get an esper anyway.

Dead checks (accessible checks that could hold a character or esper but hold an
item), measured in-process on 400 standard / 200 easy / 200 hard seeds: about
2.2% of accessible checks in standard and hard (0.3 per seed, 74% of seeds have
none) and 4.7% in easy (0.5 per seed). The planner itself never places an item
where a character or esper fits; every dead check is a check the growth loop
never claimed, filled by the safety backfill in `Events.ruination_mod`.

Fixed: seed 10352 with plain `-ruin` crashed in finalize (`ValueError: 1162 is
not in list`, about 1 seed in 400). Step 5b's last-resort orphan-door pass looks
for a target door in every member cluster, the hub's own included, whose doors
are the `remaining_doors` being spent: it paired South Figaro WoR's door 1162
with itself. It now never picks the door being spent, and a remaining door
chosen as the target is spent too (two hub doors paired, as in step 5). The
2000-plan `tools/ruin_stress.py sweep` then completes every plan.

### Item reward chance: `-rirc` (2026-10-15)

Named `-rdcc` (`--ruination-dead-check-chance`) for its first day; renamed
2026-10-16, since "dead check" only means something when collecting characters
and espers for a Kefka's Tower unlock.

**Flagset default 1% (2026-10-17).** Playtests felt worse without getting all
the espers, so every `-ruin` flagset (standard, hard, easy) now injects
`-rirc 1`: an item on a character/esper check is a rare surprise, and items
come from the ruination-only boss rewards (Dadaluma, Sealed Gate, Phantom
Train smokestack) instead. The formula below remains the default when the
flag is absent (`-ruin custom`, `-no rirc`); a user `-rirc` overrides.

`-rirc PERCENT` (`--ruination-item-reward-chance`): when the planner claims a
check that can hold an item and a character or esper, it is made an item with
this chance. Default: vanilla WC's item share on the slots that can hold a
character or esper and an item,
`(50 - (14 - starting characters + 27 - starting espers)) / 44`
(`data/ruin_constants.standard_item_reward_chance`). A vanilla `-cg` build has 62
reward slots: 33 character/esper/item, 11 esper/item, 6 character/esper and 12
item-only. Item-only slots always hold items, so they stay out (2026-10-16; the
first version divided by all 62). The characters and espers fill the 50
character/esper-capable slots, the 6 character/esper-only ones always take one,
and the leftover items land on the 44 mixed slots. Starting espers are rolled
after planning, so the midpoint of `-stesp` stands in. The default is 22.7% for
vanilla's one-character start, 27.3% with three starting characters, 29.5% with
four. `-rirc 0` draws nothing and is the previous planner exactly (identical
plans on 300 fixed RNG streams).

An item roll happens only while the game keeps enough checks for every
character and esper still to place (`_item_reward_affordable`): the unclaimed
"usable" checks - in the plan's areas, able to hold a character or esper, not
a bonus check, reachable with the game's characters - must still cover the
characters left plus the espers still required (since 2026-10-16, espers or
items, the rolled item itself counting as one). Reserve areas pulled in later
add their usable checks. If the map still runs out of checks
(`_add_reserve_checks`, active only above 0), a reserve area is pulled onto the
branch with the fewest rewards. Measured at the default (full builds, 400
standard / 200 easy / 200 hard): every seed builds; 17.0 accessible checks per
standard seed (14.4 at `-rirc 0`), 3.7 of them items where a character or esper
could have been (25% of item-capable checks);
easy 13.6 and 3.4; hard 17.1 and 3.6. At the first default (38.7%) a standard
seed had 18.3 and 5.2.

**Items count toward `-rce`'s second number (2026-10-16).** `-rce C.E` asks
for C characters and E espers *or item rewards*: a non-bonus check the planner
claims as an item counts like an esper (`process_rewards`), the pre-plan's
slot count takes every non-bonus check (`slots_in`), and the affordability
rule counts the item being rolled (`second_left = E - obtained - 1`). Bonus
checks (Tzen, Auction House) count for neither. Before, item rolls made the
map grow to find E espers anyway. Planner-only measurement (150 plans,
`-rce 6.9`, three-character start, rooms / non-bonus checks per plan):

| `-rirc` | before | after |
|---|---|---|
| 0 | 141 / 12.3 | 141 / 12.3 (identical) |
| 27.3 (default) | 163 / 15.5 | 147 / 12.6 |
| 50 | 180 / 17.8 | 154 / 13.1 |
| 100 | 193 / 18.7 | 188 / 15.6 |

At very high chances maps still grow: once E is met, items keep rolling on
character-capable checks and delay the remaining characters (at 100%: 11.8
items + 0.8 espers for E = 9). Not changed; a possible rule is no item rolls
once E is met while characters are still owed.

The item rolls exposed planner reward types the events don't have: Floating
Continent 1/3 and the Veldt are character/esper slots in their events but were
listed with ITEM. Fixed in `ROOM_REWARD`; `tests/test_ruin_item_rewards.py`
compares every planner type with its event slot when `ff3.smc` is present.

Level cap by mode: standard `-ruin` injects a soft cap `-lc 48 10`, `-ruin hard`
a hard cap `-lc 48` (`RUIN_HARD_OVERRIDES`), and `-ruin easy` none
(`RUIN_EASY_OVERRIDES` drops it). Until 2026-10-16 these were `-lc 43 5` /
`-lc 43`; players found the 43 soft cap too sharp and too early for late-game
strategies. The injector reads a flag's values up to the
next flag token (`value_count`), so an override may give fewer values than the
`FLAGS_WITH_ARGS` maximum.

### Ruination boss item rewards (2026-10-16)

Two item-only rewards exist only in ruination. On a shuffled map, the bosses
that guard them are often optional:

- **Dadaluma** (Zozo, map 0xdd, object 0x1d at (30,14)).
  `Zozo.init_rewards` adds a second, ITEM slot, `dadaluma_reward`. After his
  battle, CA/96B5 now calls a routine that runs the original
  `42 1D B9 4B D7 4A 96` (hide him, update his bits, start the fade-in), then
  `WaitForFade`, `AddItem`, the item's "Received" dialog and `FinishCheck`.
  Without the wait, the dialog box opened while the screen was still dark. His
  show bit, NPC bit 0x34a, is already set at game start, so he is there
  without any setup.

  Walking route from the 12F door (615; the party lands at (35,16)): left to
  (30,16), down to (30,17), right up the flight to (34,14), up to (34,13),
  left along the walkway to (30,13), then face down and talk. Afterwards his
  tile is free: down to (30,14), right up the top flight to (34,11), up to
  (34,10), left to (33,10), and up into the 14F door (619).

  The 10F door (614) also connects: a staircase climbs from its ledge to 12F
  and Dadaluma, so `ZOZb08` is one room as defined (confirmed in play; an
  emulator walk on 2026-10-16 missed the staircase and wrongly called the
  ledge a dead end).
- **Sealed Gate terminus boss** (map 0x187, room `HUB52-ruin`). The gate's
  reward slot, formerly character/esper/item, is item-only in ruination. Its
  ruination script was never installed, but the backfill could still put a
  spare character or esper in it, where nobody could reach them. The reward is
  given after the post-battle `FadeInScreen` + `WaitForFade`, before the party
  turns to the gate and it opens.

- **Phantom Train smokestack boss** (added 2026-10-16). `PhantomTrain.init_rewards`
  adds an ITEM slot, `smokestack_reward`, in ruination. The first smokestack
  win runs the "ensure reward" script (`phantom_train_mod`, reached from
  CB/BA06). In classic WC that gives the Phantom Train reward if the caboose
  hasn't; in ruination it never does (the reward is the caboose's alone, where
  the planner puts it). Instead, if `DEFEATED_PHANTOM_TRAIN` is still clear:
  `FadeInScreen` + `WaitForFade`, the item, its dialog and `FinishCheck`, then
  the existing exit. Repeat
  fights (for the Suplex A Train objective) take the `door_rando_mod` branch
  at the smokestack, which fights the vanilla GhostTrain pack and goes
  straight to the exit, so the item comes once. Checked by the compiled
  bytes (bit 0x03B skip, `96 5C 80 xx`, dialog, FinishCheck, no main reward);
  play-test seed `-s 76 -ruin -debug -debug_dest PHT02-ruin PHT08 PHT12`
  (Sabin starts; all three rooms off the school's middle door). Note the
  smokestack event also needs map bits 0x1B0/0x1B4 (set in the locomotive)
  besides the `pt2` switches and Sabin.

- **Ferry sea boss** (added 2026-10-24). Ruination moves the Narshe Battle
  boss (Kefka at Narshe) to the ferry. The reward is its own ruination-only
  event, `event/ferry_boss.py` (`FerryBoss`, "Ferry Boss", one ITEM slot),
  so the Narshe Battle check keeps its own C|E|I slot in case it ever joins
  the ruination map (for now it is still a never-mapped backfill).
  `Events.ruination_mod` passes the Ferry Boss item to
  `fix_ferry_connections`. (The first version, the same day, made the Narshe
  Battle slot item-only instead.) The first voyage's battle runs on field map 0x009
  (the world map can't show dialogs); right after it, the shared routine
  `_ferry_build_boss_reward` hides NPC slots 0x10-0x2F (WC puts a character
  lineup on that map; `-debug` adds more) and the party, fades in on the map's
  black background, gives the item with its dialog and `FinishCheck`, fades
  out, and the voyage resumes to the destination. Later voyages skip the
  battle (`FINISHED_NARSHE_BATTLE`) and so the item. If fewer than two ports
  are mapped the ferry doesn't run and the item can't be had (still logged).
  Regression scenario `ruin_ferry_boss_item` (searches for a seed whose ferry
  runs from South Figaro under `-maptest SFIb30`).

None of these slots is in the planner (`ROOM_REWARD`). Both are filled by the
`Events.ruination_mod` backfill and stay out of the `-rirc` math, like every
item-only slot. The spoiler lists them as "Item (Dadaluma)",
"Item (terminus boss)", "Item (smokestack boss)", and a "Ferry Boss" event
line for the sea boss. In the emulator, the item arrives 45 frames after the
battle, with the map on screen, and at the gate the opening animation plays
once the dialog closes. The regression scenario `ruin_boss_items` walks both
for real on one seed, `-ruin -maptest ZOZb08@615/619 HUB52-ruin` (the
`ROOM@IN/OUT` syntax, `doors/plan/ruination/maptest.py`, picks the door each
`-maptest` room is entered by and the door it chains onward by). The
extra slots add RNG draws, so every ruination seed's rewards reshuffled, but
the maps did not: the ruination goldens were re-recorded and the non-ruination
ones are unchanged.

**Changing any -ruin default reshuffles every seed** (`seed.py`:
`random.seed(seed + flags)`), maps included: re-record the golden ruination
configs, and expect fixed-seed regression scenarios to lose their routes. The
Phoenix and lite-save scenarios now search for a routable seed
(`build_routable` in `tools/playtest/regressions.py`).

### Parked idea: tiered command mode (not implemented)

Seed-level targets instead of per-character percents: tiers Required /
Common 60 / Rare 25 / Very Rare 10 / Ultra Rare 5 / Removed (`-rec`), one flag
per tier listing ids. Back end: flip one coin per skill at its seed
percentage (redraw if more skills than slots, with a startup calibration so the
redraw doesn't bias), give each chosen skill one slot, fill leftovers with
tier-weighted duplicates (or uniquely from Common), shuffle onto characters.
Fight/Magic/Item tiers would act per character.

## Experience Table & Level Cap (`-lc`) (2026-10)

### The table (vanilla)

`ED/8220-ED/82E3`: 98 little-endian words; entry *i* = experience from level
*i*+1 to *i*+2, **divided by 8**. No totals are stored: every reader sums the
entries in 24 bits and shifts left 3 times.

| Reader | What it does |
|---|---|
| `C0/A235` (called from `C0/9F70`, `C0/A158`) | set a character's experience (`$1611-$1613`) to the total for their level (`$1608,Y`); used by `-stl`/`-stlr`/`-sal` |
| `C3/60CA` | menu: total for the next level (32-bit shift) |
| `C2/606D` | battle level-up: `ADC $ED821E,X` from level×2 down, compare with experience, `JSR C2/60C2` to gain a level, loop (multiple level-ups per battle), stop at 99 |

Level-up gains: HP `E6/F49E + new level` (table starts at `E6/F4A0`), MP
`E6/F500 + new level` (starts `E6/F502`: 4, 4, 5, 5, 6...). `C2/6235` adds
battle experience and caps it at **15,000,000** (constant at `C2/6276`). Level
99 needs 2,637,112; the last step (98→99) is a hand-set 11111 × 8 = 88,888. The
largest one step can cost is 65535 × 8 = 524,280 (≈ total for level 58).

### `-lc` (branch `feature/level-cap`; merged into `door_rando_ruin_rewrite` 2026-10-12 for playtesting, not yet upstream)

`-lc LEVEL` = hard cap: battle's experience cap at `C2/6276` (vanilla
15,000,000, read only by `C2/6235`, which clamps the total after every award,
Exp. Egg included) is set to the total for LEVEL, so LEVEL is reachable and
LEVEL+1 never is; the experience table stays vanilla. Verified in the emulator
(2026-10-13, `-lc 10`): party at L9 with 2,926 went to L10 with exactly 2,976
after one battle and did not move after a second. A character placed above
the cap keeps their level and never levels again. (The first version filled
the table with 65535 from LEVEL on, which grinding could still pass, up to
L58 for a cap of 30.) The status screen shows 0 "for level up" at or above
the cap: vanilla's level-99 check (`C3/60A6 CMP #$63 / BEQ`, in `C3/60A0`,
whose only caller is the status screen) becomes `CMP #LEVEL / BCS`
(`set_menu_level_cap`); checked in the emulator at, below and above the cap. `-lc MEAN WIDTH` = soft cap, table plus vanilla battle cap; when the
highest level reachable under the 15,000,000 battle cap is below 99, the same
status-menu patch is applied at that level (`level_cap.highest_level`), so
the screen shows 0 there instead of freezing on an unreachable remainder
(104,720 at L73 for `-lc 40 5`; emulator-checked: L73 at 15M shows 0, L72 at
14,156,160 shows 424,280, a placed L75 shows 0). Harness note: when poking
level/experience into WRAM for a menu check, keep the experience at or above
the level's own total; below it the menu shows a "for level up" larger than any
one step (an unreachable state, not a bug). Soft cap (LEVEL 2-98 and MEAN 1-99 whole numbers; WIDTH 0.1-99 with at most one
decimal place):
`step(L) = min(65535, round(default(L) × (1 + 10^((L - MEAN) / WIDTH))))`,
never below default, doubling from MEAN to MEAN+1; every WIDTH levels past
MEAN multiply the extra cost by 10. Base 10 replaced e after playtesting
(2026-10-12): width 1 in base e (×2, ×3.7, ×8.4, ×21...) turned on too
slowly; base 10 gives ×2, ×11, ×101, then the maximum. It is the old curve
with WIDTH / ln 10. Code:
`data/level_cap.py` (pure, ROM-free; tested in `tests/test_level_cap.py`),
applied by `Characters.mod_level_cap`, flag in `args/xpmpgp.py`, spoiler
section "Level Cap: Total Exp (Default)" (with the experience cap). The flags menu ("Exp, MP, GP")
always has a Level Cap row: the level for a hard cap, "Soft M/W", or "None"
(longest "Soft 99/98.5", 23 of the row's 26 characters).
That row lengthens the menu text and shifts later free-space allocations, so
adding it changed every golden ROM (re-recorded; verified byte-identical to
the pre-merge tree plus only that row).

**Two hazards the soft cap handles.** (1) Past the 15,000,000 battle cap no
level can be reached. (2) The 24-bit sum wraps once the
summed entries reach 2^21 (~16.8M experience); a character *placed* there by
`-stl`/`-stlr`/`-sal` would get garbage experience and level straight to 99 in
the next battle. `guard_wrap` sets every step past the 15M point to 1
(unreachable anyway), keeping the sum below the wrap for every cap. Rounding
note: rounding *up* turned 4 × 1.0004 into 5 (+25% at level 1); use nearest.

## Ruination Treasure Chests & `-rrtc` (2026-10-25)

### The chest table

`tools/ruin_chest_rooms.py VANILLA.smc [--write]` puts each vanilla chest
(MIAB included) in the ruination room(s) it can be opened from.
`--write` regenerates two files:

- `claude_reference/ruination_chests.csv`: one row per chest, with id,
  `area_chests` area, map, map name, x/y, type, rooms, and `how`, which is
  `flood`, `reviewed` or `kt`.
- `data/ruin_chests.py`: `ROOM_CHESTS`, the chest count per room;
  `KT_CHESTS`, Kefka's Tower's 16 chests, which are tallied apart because
  its lanes are not branch rooms; and `CHEST_GATES`.

`tests/test_ruin_treasure.py` checks the data file still matches the
generator.

Method: a flood fill over each map's BG1 layout and tile properties.

- **Decoding.** The tile-property set is **planar**: 256 first bytes, then
  256 second bytes.
- **Movement** follows C0/4E3D:
  - The second byte holds the exits the current tile allows: up 08,
    right 01, down 04, left 02.
  - A destination whose first byte has `&7 == 7` is a wall.
  - Z-levels are bits 0–1; bit 2 marks a bridge.
  - First-byte bits 6 and 7 mark up-right and up-left stairs. On stairs,
    horizontal steps go diagonal and **ignore the exit bits**.
- **Doors** are often wall tiles. Each room floods from its door tiles'
  neighbours, and an exit is taken from any tile next to it.
- **Room boundaries.** Exits that ruination does not shuffle carry the fill
  to their arrival point. Shuffled doors **and locked exits** stop it (the
  lock bug had leaked MTZ04 into ZOZr04).

What the fill cannot see was settled by Hans's review (`REVIEWED_*` in the
tool): event-driven areas (Magitek Factory, Zone Eater, Fanatic's Tower, the
Imperial Base basement, Phoenix Cave, Floating Continent), NPC-blocked splits
(the Phantom Train cars, Umaro's cave), replicas, unused maps, and WoB/WoR
copies.

- **South Figaro: 23.** 8 outside (WoR map 0x4a, ids 35–42) and 15 inside.
  The WoB outside chests 43–50 sit on the same tiles on 0x4b. The fill leaks
  onto 0x4b through the shared interiors, so they are excluded.
- **Thamasa: 6.** 5 outside and 1 in Strago's house. The outside five are
  the pre-Leo map 0x157's chests, which `data/chests.py` `copy_thamasa_chests`
  copies onto WoR 0x158 (they don't show in a map editor). `CHEST_COPIES`
  places them there.
- **Albrook: 6.** Outside: 203 (WoR) and 208 (docks). Inside: 204–207.
- **Tzen: 8**, all in the collapsing house. `CHEST_GATES` counts them only
  when the Collapsing House check can be done (SABIN in the game).

Totals: 227 room chests plus 16 in Kefka's Tower.

Per seed (census of 100 seeds per mode, verifier reachability, Kefka's Tower
excluded):

| Mode | Mean | Sd | p10 | Median | p90 | Range |
|---|---|---|---|---|---|---|
| Easy | 67 | 19 | 43 | 67 | 95 | 30–117 |
| Standard | 75 | 19 | 55 | 75 | 101 | 38–135 |
| Hard | 76 | 18 | 55 | 77 | 105 | 41–123 |

- About 3 per seed are MIAB.
- The census script (`ht_census.py`, scratchpad only) builds the seed
  in-process and takes reachable rooms from the softlock-verifier graph, keyed
  with the party plus the planned characters. About a third of branch member
  rooms are never wired in.
- High-tier (`-ir ruin`) items before Kefka's Tower, from the same census:
  easy 6.4, standard 4.4, hard 4.4, plus 3 in Kefka's Tower. The Opera House
  needs Celes, so a Dirt Drgn there is Celes-gated; the census ignores this,
  which hardly moves the means.

### `-rrtc MIN` (`--ruination-require-treasure-count`)

Default 0 (off). With 0, nothing draws differently and the goldens are
unchanged. It is not in any `-ruin` flagset. The code is in
`doors/plan/ruination/finalize.py`, section "Treasure rescue".

**Target.** Branches close in order. Branch i of n aims for a cumulative
share, `ceil(MIN*(i+1)/n)`, minus what the earlier branches already hold.
"Holds" means the rooms in the hub cluster plus downstream clusters,
counted with `_room_chests`, which applies the gates.

**Treasure rooms** (`_treasure_shape`) must have:

- 1 or 2 doors;
- no traps, pits, keys or locks;
- not be a terminus;
- no forced or protected exits;
- no unclaimed check that can't hold an esper or item.

**Where they come from.** The branch's own unwired rooms come first, then
rooms of unused reserve areas. Pulled rooms go through `_take_room`, which
is now shared with `_pull_town` and registers the area's shops.

**Unclaimed checks** in a treasure room go into `dead_check_restrictions` as
ESPER|ITEM, the same treatment Ebot's Rock gets, so the backfill never puts
an unplanned character there. `RuinMap.restore_restricted_types()` puts the
slots' original `possible_types` back after the safety pass. Without that,
`Events.validate` (the count of char/esper-only slots) fails. Ebot's Rock
had the same latent bug.

**The algorithm:**

1. **Before step 5.** While the hub has more doors than dead ends (step 5
   would pair the spare doors together) and the branch is short, single-door
   treasure rooms are added as dead ends. Each one saves a door from being
   paired.
2. **Just before step 6** (doors ≤ dead ends). While the branch is short,
   either:
   - add a single-door room with more chests than the poorest dead end step 6
     would pick (it displaces that one), or
   - wire a two-door room in line. It is door-neutral: its other door
     replaces the spent one.
3. **Step 6** sorts the dead ends terminus first, then richest first. The
   sort comes after the usual shuffle, so ties stay random.
4. **The pick** is weighted by chest count.
5. **`finalize_plan`** raises `RuinPlanError` if the total is short, and
   `plan.py` re-rolls (up to 10 attempts).

Measured (grow+finalize, 60 seeds, std-like config):

| MIN | Plans OK | Mean | Median | Mean attempts |
|---|---|---|---|---|
| 0 | 60/60 | 73 | 67 | 1.2 |
| 80 | 60/60 | 98 | 93 | 1.5 |
| 100 | 60/60 | 110 | 106 | 1.8 |
| 120 | 59/60 | 125 | 121 | 2.2 |
| 140 | 53/60 | 142 | 140 | 3.4 |

- An independent verifier census of `-ruin -rrtc 110` builds found 110–126
  chests, against 37–93 for the same seeds without the flag.
- Allowing esper/item check rooms (South Figaro's 23, Phoenix Cave's 9,
  Tzen's 8, Fanatic's Tower's 6) is what made 120 work. Without them,
  candidates ran out (49/60 plans at 120).
- **Default since 2026-10-28:** every `-ruin` flagset injects `-rrtc 55`
  (`RUIN_DEFAULT_FLAGS`, after `-rirc`; `-no rrtc` removes it). About a
  tenth of plain plans fall below 55 (p10 is 43–55 by mode), so the cost
  is small. Over 60 plans each: 1.25 attempts per plan at -rce 6.9 and
  1.38 at 6.6, against 1.22 without it; every plan built; means 86 and 78
  chests.
  - The flag-string change reshuffled every ruin seed; the six ruin goldens
    were re-recorded.
  - Two emulator scenarios lost their routes. `unequip_all_away` now uses
    `build_routable`.
  - `lite_save_markers`' new seed routes through Owzer's painting room,
    whose exit 581 sits at the foot of diagonal stairs.
    `tools/playtest/route.step_door` now also tries horizontal steps from
    one row above or below (`navigate.step_through(..., rise=±1)`).
    `navigate.jumped` counts a landing on the same map as a transition
    (581 itself leads to map 207 in the atlas).
- Possible refinements:
  - three-or-more-door rooms as in-line candidates;
  - a per-branch floor rather than a cumulative one;
  - counting only chests the walk passes (a dead end is a detour).

## In-game Flags menu blank on `-ruin easy` (2026-10-27)

**Symptom.** `-ruin easy` seeds showed an empty Flags page in the pregame
menu. Standard and hard seeds were fine.

**Cause.** The Flags menu (`menus/flags.py`) is one scroll area with a line
per option, a title per group and a blank line between groups. The scroll
area code (`menus/pregame_track_scroll_area.py`) works in 8-bit line
indices. The draw routine compares the line index against `len(self.lines)`
as an 8-bit immediate, so at 256 lines the compare value is 0 and every line
draws blank.

Line counts for seed 5:

| Mode | Lines |
|---|---|
| Standard | 252 |
| Hard | 253 |
| Easy | 256 |

Easy has extra flags (starting items, `-rrt`, ...) on top of the 24
per-command `-compru` chance lines and the ruination entries.

**Fix.**

- `MAX_LINES = 255`. `ScrollArea` now asserts it at build time, so an
  overflow fails the build instead of shipping a blank menu.
- `Flags.fit_lines()` only acts when the menu is over the limit. It drops
  just enough of the blank separators between groups, starting from the
  bottom (group titles stay blue). Easy loses one, the blank line before
  Doors, and lands at exactly 255; there are about 30 to spare. If the menu
  is still too long with every separator gone, it cuts the end and adds a
  "(more in the log)" line. Submenu line indices are shifted to match.
- Test: `tests/test_flags_menu.py`.
- Verified in the emulator: the old easy ROM shows an empty Flags page; the
  fixed one scrolls from Settings to the last Doors line.

**Follow-up (same day): command chances moved to a submenu.** The 24
per-command `-compr`/`-compru` lines are now one Flags line, "Chances 24 …".
It opens `menus/flags_command_chances.py` (`FlagsCommandChances`, menu
number 18), laid out in two columns like the Item Rewards submenu. The
spoiler log still lists every chance (`args/commands.options` is
unchanged; only `menu()` swaps the lines out).

Flags line counts for seed 5:

| Mode | Lines |
|---|---|
| Standard | 229 |
| Hard | 230 |
| Easy | 233 |

All three keep every separator. `fit_lines` stays as the safety net.

**Bank C3 was the real constraint.** A new scroll area costs C3 code, and
C3 had 96 bytes free with the new submenu on `-ruin hard`; `-rc` (the
Require Characters submenu) then failed with `RomSpaceError` in
`menus/buy.py`. Each scroll area's invoke routine (91 bytes, seven of
them) now lives in F0. It calls the C3 routines through
`c3.eggers_jump`, and leaves a 5-byte `JSL; RTS` stub in C3. That brings
C3 free to 698 bytes on `-ruin hard`.

Verified in the emulator:

- Pregame: Objectives, Flags, and the Chances, Item Rewards, Remove Spells
  and Require Chars submenus.
- In-game Track menu: Objectives, Checks, Progress and Flags.
- B from a submenu returns to the top of Flags, as before.

**Commands section trimmed (2026-10-27, menu only; the log keeps every
row).**

- Random Exclude shows one row per actual exclusion, and a single "None"
  row when there are none (it used to pad to six).
- In the probability modes, the blank row before Shuffle Commands is
  dropped unless a per-character `-com` list is shown above it.
- Shuffle Commands appears only when `-scc` is on. There, `-scc`
  (`shuffle_full_random_commands`) only swaps whole command sets between
  characters. The rolls are already per character, and in unique mode the
  roll order is shuffled, so `-scc` only matters for commands pinned with
  `-com`.
- Ruin menus now read: Random Mode / Chances 24 … / Random Exclude None.

Goldens were re-recorded: ROM bytes only, logs identical. Measure C3 use
with a wrapper on `memory.space.Allocate`; `Space.heaps[Bank.C3].available`
is a property.

## `-ruin fast` preset (2026-10-28)

Hans's spec: standard, plus these pieces of easy.

| Flag | Fast | Standard |
|---|---|---|
| `-rce` | `6.6` (6 characters + 6 espers/items) | `6.9` |
| `-oc` / `-od` | `58.1.1.4.3.3` / `58.1.1.4.6.6`: High Tier Item at 3 and 6 espers found | none |
| Starting party | four (`-sc4 random`) | three |
| `-esr` | `5 5` | `3 5` |
| `-ebr` | `100` | `88` |
| `-lc` | none (no level cap) | `48 10` |
| `-rrt` | on: a shop town on every branch | off |
| `-sj` | `12` junk items (easy's) | none |
| `-xpm` | `10`; fast's own | `8` |
| `-lsced` / `-hmced` / `-xgced` | `2.5` each; fast's own | `2` each |

Everything else is standard: 6000 gp, 1/4 sell
prices, `-chrm 7 0`, no potions, fenix downs or Warp Stones, `-rrtc 55`,
`-rirc 1`. Revised the same day: the first version had `-sws 3` and no
junk, with standard's `-xpm 8`; enemy scaling went to 2.5 (from 2) on
2026-10-29.

Implementation:

- `RUIN_FAST_OVERRIDES` and `RUIN_FAST_EXTRAS` in `args/ruin_preprocessor.py`.
- `fast` added to the `-ruin` choices and to the flag-string modes in
  `args/doors.py`, so a logged string re-expands as fast.
- Tests: `test_fast_is_standard_with_easy_map_size`, which checks that the
  only flags added beyond standard are `-oc -od -rrt -sc4 -sj`.
- Golden config `ruinfast` (`-ruin fast -s 1002`).
- The `-ruin` help's stale easy objective text ("2, 4 and 6") now reads
  "3 and 6".

Checks:

- Eight seeds built, with 3 plan re-rolls in total.
- Flags menu: 224 lines.
- Emulator (first version): four party members and three Warp Stones at the
  start, from a build without `-debug` (`-debug` adds 99 Warp Stones and 3
  Dried Meat).

Like easy, the 6-espers objective relies on the map's six esper/item
checks; a 1% `-rirc` item roll there leaves it to bonus or auction espers.

## Command Randomization Overhaul: `-comr`/`-comru`/`-comw` (2026-10-29)

Branch `feature/command-randomization-utility-update` (off `ff6wc/dev`
92c5c32, meant as the upstream PR that replaces `-compr`/`-compru`/
`-comfr`/`-comfru`/`-rec`, which were only on `dev`). Cherry-picked onto
`door_rando_ruin_rewrite`. `main` was fast-forwarded to `ff6wc/dev` first.

### Why the percent tiers were unintuitive (measured on the real code)

1. **Higher tiers took the slots first.** Each character rolled the highest
   tier first, so a skill set 1% above the rest won its slot by ordering.
   With Jump 26, Lore 25 and the rest at 24, Jump and Lore appeared in 98% of
   seeds against 81% for the others.
2. **The unique backfill floored every skill.** Unrolled slots were drafted
   from the least-dealt skills, so a 1% skill still landed in about 45% of
   seeds. Doubling every percent (52.51.50.25) put Jump and Lore at 100% and
   Shock at 16%.
3. **Fight/Magic/Item were in the same tier list.** Skills at 90% shared their
   tier, and every skill appeared in every seed.
4. **Shared mode (`-compr`) was worse.** Per character, 24/12 gave Shock 0.5%
   against 7.3% for the others.

### The constraint

With F/M/I at 90%, a seed has about 16.5 skill slots for 21 skills (13 at
100%). Under `-comru` the seed frequencies sum to about 16.5, and the slot
count swings with the F/M/I rolls. A seed with more slots than the heavy
skills can fill uniquely has to give the rest to lighter skills. Hans
accepted that distortion as the price of `u`.

### Design

- **`-comr F.M.I` / `-comru F.M.I`** randomize every slot. One percent covers
  all three. Gau never gets Fight.
- **`-comw GROUP:WEIGHT,...`**
  - Groups use names or ids joined by `.` (names ignore case and punctuation).
  - Unlisted skills weigh 1.
  - Tier names: `common` 1, `uncommon` 0.5, `rare` 0.25, `veryrare` 0.1,
    `legendary` 0.03, `never` 0.
  - `always[:W]` (Hans: default W 1) guarantees one holder, through the Blitz
    guarantee's slot logic (`deal_always`), and others draw at W.
  - `none` sets the empty-slot weight (replaces `-compr 97`).
  - Canonical output: always first, then heaviest; skills in id order.
- **`-comr` draw:** per-character `weighted_choice` among the skills it lacks.
  Morph has one holder.
- **`-comru` draw:** `unique_skills` takes the least-dealt legal skills first.
  Each round's skills are chosen together by `share_sample` (systematic
  sampling, inclusion `min(1, c*w)`) and matched to slots so no character
  gets a skill it holds (`place_skills`, augmenting paths). Drawing one at a
  time, "each pick 0.1x as likely", is less faithful because the commons run
  out mid-draw:

  | Setting | One at a time | Share draw |
  |---|---|---|
  | weight 0.5, F/M/I 90% | 0.72x | 0.51x |
  | weight 0.5, F/M/I 100% | 0.62x | 0.50x |
  | four skills at 0.1, F/M/I 100% | 0.16x | 0.10x |

- **Order of dealing:** explicit `-com` picks, then always, then repeat draws
  (99 slots and `-comr`), then unique draws (98 slots and `-comru`). A 98
  never repeats a 99's pick.
- **`-com` alone:** equal weights draw through `random.choice` exactly as
  before. Uneven weights use `weighted_choice` for 99 slots and `share_sample`
  for 98 slots.
  - Verified: `main` and feature builds of `-s 7` with no command flags,
    `-com 99…` and `-com 98… -scc` have identical spoilers except the flags
    summary rows. The ROM differs only through the menu text.
- **Retired flags** keep hidden argparse stubs that error with the new form.
  `-rec1`–`-rec6` (in `main`) become weight 0; using one together with a
  `-comw` weight on the same skill is an error.
- **Menu:** Random Mode (Unique/Repeats), Fight/Magic/Item, Shuffle Commands
  (hidden under `-comr`/`-comru` unless on), and a Skill Weights submenu
  (`FlagsCommandWeights`, menu number 18). The log lists every weight.
- **C3 on `dev`:** 996 bytes free with all four submenus (1200 before). The
  ruin branch also has the F0 invoke move.
- **Tests:** `tests/test_commands.py`, rewritten. A fake-character harness
  checks:
  - invariants: unique, repeat, composed with `-com`, cycling;
  - ratios within tolerance;
  - doubling every weight gives identical seeds;
  - the empty-slot rate and the Suplex Blitz guarantee.
- **`tools/command_odds.py`:** prints seed and character frequencies for any
  flags.
- **Ruin defaults:** `-comru 90 -comw shock.possess:0.5` gives 82.5% / 42%,
  as the tiers did. Same day, Hans moved Shock/Possess to `rare` (0.25,
  logged as `:0.25`): 23% of seeds against 84.5% for other skills (0.28x;
  the commons saturate slightly). Morph now behaves like any skill (about 81%; it was 75%
  when roll-only).
  - Exclusivity groups: `{-com, -comr, -comru}` and `{-comw, -rec1..6}`.
  - A user `-comw` comes after the injected one and argparse's last value
    wins.

### Harness fixes found by the reshuffled seeds

- **Random encounters** (Narshe WoR) stalled `step_through`.
  `navigate.step_through` now sets `$1EB9` bit 5 (encounters disabled) for
  the walk and restores it afterwards; `in_battle` (`$3ED8 != $FF`) and
  `clear_battle` remain as a fallback.
- **A teleport onto a door's step tile** (Narshe WoR school door 144) left
  the party unable to walk in. `step_door` now also tries straight walks from
  two tiles out.
- **The same-map jump check** measured from the door. A teleport off the map
  edge (South Figaro's long edge exits) looked like a jump; it now measures
  from where the party started, and off-map approaches are skipped.
- **`unequip_all_away`:** a 2-frame RIGHT tap right after the Y party switch
  could be dropped. It now holds RIGHT for 8 frames (the ghost blocks the
  step).

### Old flags kept for presets (ruin branch only, 2026-10-30)

Hans asked that `-compr`, `-compru`, `-comfr` and `-comfru` keep working on
`door_rando_ruin_rewrite`, because some presets use them. The PR branch
still retires them.

- **Legacy mode.** `args/commands.py` `_legacy_mode` turns on when a seed has
  only old flags (the percent families, `-rec`, `-recN`) and none of
  `-comr`/`-comru`/`-comw`. It then runs the pre-overhaul code verbatim:
  - `args/legacy_commands.py`: parsing, canonical flags, options, menu;
  - `data/commands_legacy.py` `LegacyCommands`: the tier rolls, `UniquePool`
    and backfill;
  - `menus/flags_command_chances.py`: menu number 18, shared with Weights,
    since a seed only ever uses one of them.
- **Errors and new mode.** Mixing old percent flags with new flags is an
  error. `-rec` alongside new flags is weight 0.
- **`-ruin` interplay.** The old percent flags also suppress the injected
  `-comw` (`EXTRA_SUPPRESSED` in the ruin preprocessor), and `-rec` joined
  the `-comw` exclusivity group.
- **Verified.** Six old presets built at `c6019a2` (pre-overhaul) and now give
  byte-identical ROMs:
  - `-ruin -compru <the old ruin lists>`;
  - `-ruin hard -comfru 90.90.90 -rec 28.27`;
  - `-com 99… -rec1 28 -rec2 27`;
  - `-comfr … -rec 16 -scc`;
  - `-compr …`;
  - `-com 05999898… -compru 28.27 50.25 -comfru 100.100.100`.
- **Pitfall.** The first version named the module `args/commands_legacy.py`.
  The `args` package copies every parsed attribute onto itself, so the
  `args.commands_legacy = True` flag shadowed the submodule. The module is
  now `args/legacy_commands.py`.

### `other` and `randomN` weight groups (2026-10-30)

- **`other:W`** weighs every skill no other `-comw` entry names (or `-recN`
  excludes), wherever it is listed; never the empty slot; not `always`; a group
  of its own. The canonical `-comw` is the shortest of the plain and `other`
  forms, so the long list and `dance:1,other:0` print and seed the same.
- **`randomN:W`** (`random` = `random1`) gives weight W to N skills drawn per
  seed from the unnamed ones. Draws happen after the rng is seeded
  (`args/arguments.py`, beside the `-rc` resolve; no rng use without groups), so
  the flag string keeps `randomN` and the seed decides the picks. Groups draw
  disjointly; `other` weighs what they leave; named skills stay listed in the
  canonical form (naming one keeps it out of the draws). The Flags menu and log
  show the resulting weights, and the log names each group's draw.
  - `random:1,other:0` with `-comru 75.0.100`: everyone has the same random skill.
  - `random3:1,other:0`: everyone draws from the same three.
  - Until the Morph change below, a draw that left Morph as the only dealable
    skill was redrawn (Morph had one holder).

## Morph for any number of characters (2026-10-30)

Upstream branch `feature/morph-multiple-characters`, cherry-picked here. Since
2026-10-31 it sits on top of PR #178's branch (`04add1e`), so its PR (to follow
#178) carries only `bd78d94` (battle) and `b286eca` (commands, reconciled with
#178's code). The first version, on `dev`, is kept locally as
`backup/morph-on-dev` (`4307f45`, `39e4ba4`).

**Why Morph had one holder.** Vanilla keeps one timer and one morphed entity:
`$3EE2` (morphed entity, `$FF` none), gauge `$3F30-31` (counts down from
`$FFFF`), drain `$3F32` (from the supply at morph start), supply `$1CF6`
(save data). Morph starting (C2/0B01) returns if `$3EE2` holds anyone, the
battle loop (C2/1141) ticks only `X == $3EE2`, and morph ending (C2/0AE7)
clears `$3EE2` and the gauge whoever ends it. A second user got Morph with no
timer, and the first revert stopped the other's timer: unlimited Morph. After
battle (C2/5E2F) one character id (Terra; `update_morph_character` patched in
the holder) added the battle's magic points to the supply.

**`battle/morph.py`.** `$3EE2` now means "timer running"; who is morphed is
each character's status bit (`$3EF9,X` bit 3). Hooks:
- C2/1143: every morphed party member drains the shared gauge each tick (two
  morphed use the supply twice as fast);
- C2/122C: the gauge running out queues Revert for every morphed member;
- C2/0AE8 (+ NOPs at C2/0AFA): a revert stops the timer and keeps the unused
  supply share only when nobody else is still morphed;
- C2/2461: the battle-start/phase flag marks every morphed character;
- C2/5E2F: after battle, every living party member with Morph among its four
  commands (`$1616-$1619` + `$3010,Y`) adds 2 x the battle's magic points (the
  `-mpm` divide at C2/5E3F still applies to each).
Morph starting is unchanged: the first starts the timer, later ones join it.

**When the supply grows.** The add needs only the Magic Points battle bit
(`$1DD1` bit 3, set from game start by `event/start.py`), the holder alive at
the end, and a formation with magic points; it does not need a Magic command or
anyone learning. The "Got N Magic Points" message (C2/5E77) shows when `$F0`
has that bit: set by a learner (C2/6068, characters with an esper equipped) or
by a holder's add (C2/5E3A).

**Verified** in the snes9x harness (scratch scripts: a battle started by
injecting an event script `4D 01 3F FE` at `$E5-$E7`): two morphed drain 2x;
one reverting early keeps the other on the running timer; the timeout reverts
everyone and empties the supply; the last manual revert keeps 116/200; one
holder matches unpatched `main` exactly (9.9/frame, 6048 frames); supply after a
3-MP battle from 10: 16 (one holder), 22 (two), 22 (two, `-mpm 2`).

**Commands on this branch.** The new system (`data/commands.py`) no longer
special-cases Morph (explicit picks, 99 draws, `repeat_skills`,
`unique_skills`, Moogle Defense), and `resolve_random_weights` dropped the
Morph-only redraw. The legacy engine (`data/commands_legacy.py`) keeps its
one-holder rules so old presets assign exactly as before; only its call to
the deleted holder patch is gone. Every ROM changes (the battle patch), and
seeds that deal Morph roll differently after the command draws, so all
goldens were re-recorded.

**Merging with PR #178** (`feature/command-randomization-utility-update`): done
on the Morph branch (2026-10-31) by rebasing it onto #178. If #178 is
squash-merged upstream, `git rebase --onto <dev after the merge> 04add1e
feature/morph-multiple-characters` moves the two Morph commits over. What the
reconciliation changed:
- `data/commands.py`: #178 rewrites the file the Morph PR edits. Resolve by
  taking #178's file and removing its Morph special cases, as done here:
  `mod_moogle_commands` exclusion, `mod_commands` (explicit-morph removal,
  `always` removal, `index != 0` clause, 99-draw removal), `repeat_skills` and
  `unique_skills` (`dealt[morph_id]` filters), and the explicit "morph only in
  terra's slot" clause in `mod_probability_random_commands`.
- `data/commands.py` `mod()`: drop #178's `characters_asm.update_morph_character`
  call (the function is gone).
- `args/commands.py` `resolve_random_weights`: drop the Morph-only redraw.
- `tests/test_commands.py`: #178's suite replaces dev's (where the Morph PR
  rewrote four tests); apply this branch's edits instead (no Morph-once
  assertion in `BASIC_CHECKS`, `random:1` may pick all 21, strict unique
  cycling, `test_morph_for_everyone`).

## Possess is single use in ruination (2026-10-31)

**Report.** Relm, Umaro and Mog went out a branch door; Mog possessed. Back at the
school, the ghost's Reform Parties did not list Mog, yet offered three parties, and
the three-party select could not be finished with two characters: a softlock.

**Vanilla Possess.** Command `$1C` (C2/17E5) sets special effect `$A0` (C2/3B98):
attacker and target both get Wound (`$3DD4` bit 7) and Hide (`$3DE9` bit 5), and the
attacker is flagged in `$3A88`. The target dies even if immune to death (Whelk's Head,
immunity `$FF`, died). At battle end (C2/494C) a `$3A88` party member goes through
C2/47E3, which zeroes its `$1850` party byte; status and HP are written back as for
any KO (HP 0, Wound), with no `-pd` dependence. The available (`$1EDE`) and recruited
(`$1EDC`) bits are untouched, so in standard mode the character can be picked again on
the airship (and revived normally unless `-pd`).

**Why ruination lost it.** `MarkActivePartyAway` (branch door) clears
`character_available` for the active party's members and `RestoreActivePartyAvailable`
(back at the school) sets it again, both finding members by their `$1850` party bits.
A possessor's party byte is zeroed mid-trip, so its bit was never restored; the select
screen lists only characters CA/C90B creates (available bit set) with `$1850` bit 6
(C3/7645). The party-count dialog read `CHARACTERS_AVAILABLE`, which counts recruited
characters (never decremented), so it offered a third party. A possession from a party
that was not away left the character available instead: the outcome depended on the
route. The count bug also exists without Possess (a party away holding most
characters).

**Fix (Hans chose "single use": the possessor is gone for good).**
- `battle/possess.py` (ruination only): C2/4954 calls a wrapper that runs C2/47E3 and,
  for a character id below 14 that is wounded and hidden, clears its available bit.
  `$3A88` is also set by BabaBreath (special effect `$66`, C2/3966), which blows a living
  character away, and the same C2/47E3 call removes the dead Phantom Train ghosts
  (`$10`/`$11`); neither is both wounded and hidden with an id below 14, so both keep
  vanilla behaviour. Recruited and `CHARACTERS_AVAILABLE` stay: objectives ("character
  X recruited", "N characters"), character gates (Mobliz, Kohlingen, Fanatics' Tower) and
  Kefka's Tower's "3 allies" read them.
- `event/narshe_wob.py`: at REFORM an F0 routine (`LongCall`) counts the available bits
  (characters 0-13) into `SCRATCH`; the "How many parties?" branches use it.
- The risk is accepted by design: possessing too many characters can leave too few for
  the three-party finish.

**Verified** (snes9x, scratch scripts; event scripts placed in a copy of the rom at
CA/0490 because a battle overwrites free bank `$7F` memory, and ending in a jump to the
idle address CA/0000 because a return with an empty event stack pops garbage):
away party + Mog possesses + return: Mog unavailable, still recruited, Terra and Locke
available, `CHARACTERS_AVAILABLE` 3, reform count 2 (dialog offers 1 or 2 parties); the
same without the away trip; standard mode keeps the possessor available. Ruin goldens
re-recorded (rom only; spoilers unchanged).
