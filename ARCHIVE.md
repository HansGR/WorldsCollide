# ARCHIVE.md

This file contains useful reference information that has been moved from the Top 10 in CLAUDE.md. Scan this file when looking for specific detailed information.

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
4. `get_valid_door_targets_v2` evaluates door 795 as a target. It closes the loop back to the hub, and is deemed valid.
5. Algorithm connects the downstream node door to door 795. Valid from the algorithm's perspective.
6. Player enters the hub, falls through a trap to the downstream room, walks through the door into room 391.
7. The player hasn't visited rooms 389/390 yet. Keys dt2 and dt3 haven't been obtained. Room 391's exits are still locked. **SOFTLOCK.**

### Solution: Track "Initially Locked" Exits (implemented 2026-02-11)

When `apply_key()` unlocks an element (moves it from locks to free), it is recorded in `self.initially_locked_exits` (a set on the Network class in `data/walks.py`). The algorithm then enforces these rules:

1. **`apply_key()`** (`data/walks.py`): When a door or trap is unlocked, adds it to `self.initially_locked_exits`.
2. **`get_valid_door_targets_v2`**: Excludes doors in `initially_locked_exits` from the candidate target list (they can't serve as entrances the player can use without keys).
3. **`get_valid_pit_targets_v2` Rule A1**: After checking `target_exits > 0`, requires at least one originally-free exit (not in `initially_locked_exits`). Rooms with only key-unlocked exits are skipped.
4. **`finalize_map` step 1**: When selecting target rooms for trap-to-pit balancing, skips rooms with no originally-free exits.
5. **`extend_branch_path` STEP 2**: When the active node is downstream (`active_level > 0`), initially-locked doors and traps are excluded from available exits. From the hub, they remain available since the player can visit key-providing rooms first.

This correctly handles all cases:
- Self-unlocking rooms (216, 472, 435, ruin-daryl) always have >= 1 free exit
- Room 391's door 795 is rejected as a door target since it's initially-locked
- Room 391 is rejected as a pit target since it has 0 originally-free exits

---

## Ruination Mode - finalize_map Debug Patterns (2026-02-09)

### Invariant: Hub must always retain entrances
When `get_valid_door_targets_v2` Rule A2 evaluates a door merge for a room in hub/upstream, the merged result must have **both** exits (doors+traps) > 0 **and** entrances (doors+pits) > 0. A room with exits but no entrances creates downstream nodes that can never reconnect. This check only applies when `exit_room_id in hub_and_upstream`; downstream merges only need exits.

Similarly, `get_valid_pit_targets_v2` Rule A1 must not create downstream nodes (via trap→pit to unconnected rooms) when hub+upstream already has 0 entrances.

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
| `0x8a` | `MarkActivePartyAway` | Sets PARTY_N_AWAY bit, clears character_available for party members, decrements CHARACTERS_AVAILABLE. Idempotent. Fired by event tiles on branch door exits. |
| `0x8b` | `RestoreActivePartyAvailable` | Clears PARTY_N_AWAY bit, restores character_available, increments CHARACTERS_AVAILABLE. Idempotent. Fired by hub entrance event when a party returns. |
| `0x8c` | `RemapPartiesToFreeSlots` | Remaps $1850 party assignments from SelectParties slots (always 1..count) to actual free slots. Uses character_available to distinguish new from away characters. |

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

**Step 3 - Remap to free slots (RemapPartiesToFreeSlots, opcode 0x8c):**
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
| `0x8d` | `SetupBranchPartySelect` | Takes character ID argument. If active party is away: saves party mask to $e7, zeros character_available, re-sets it only for current party members and the new recruit, clears $1850 for party members (clean slate for SelectParties), recomputes CHARACTERS_AVAILABLE. No-op if not on branch. |
| `0x8e` | `FinalizeBranchPartySelect` | No argument. If $e7 is non-zero: remaps slot 1 → saved party mask ($e7), recomputes character_available as `recruited AND NOT in_away_party`, recomputes CHARACTERS_AVAILABLE count, clears $e7. No-op if $e7 is zero. |

**Execution flow (branch recruitment):**
```
RecruitCharacter(char)       → sets recruited + available for new char
SetupBranchPartySelect(char) → restricts select screen to party + new char
Call(REFRESH_CHARACTERS_AND_SELECT_PARTY) → shows party select screen
FinalizeBranchPartySelect()  → remaps slot, restores correct available state
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
- **Top-level method:** `event/events.py` `no_free_heals_mod()` invokes the three group sweepers from `event/free_heals.py`:
  - `modify_inn_costs(maps, rom, dialogs, args)` — multiplies all paid inn costs by `INN_COST_MULTIPLIER` (`= 3`) and converts free inns at Returners Hideout and Figaro Castle into paid ones.
  - `modify_free_bed_heals(maps, dialogs, enemies, args)` — replaces the six free bed-heal tiles (Narshe Weapon Shop, Sabin's House x3, Gau's Father's House, Mobliz Relic Shop) with: 50% pincer ambush (`FREE_BED_AMBUSH_PACK = 416`, escape allowed), then per-character state-dependent heal via the `BedHealCharacter` (0xa4) field opcode (revive→cure→HP→MP, mutually exclusive). If the party flees the ambush no heal is applied. Uses `multipurpose_map(0)` to debounce per map load. Two random pincer-capable formations are written into the ambush pack.
  - `modify_recovery_springs(maps, rom, dialogs, args)` — randomises the spring effects in `SPRING_LOCATIONS` (Phantom Forest pool, Cave to South Figaro) into one of nine outcomes (`SpringEffect`): FULL_RECOVERY, RECOVER_HP, RECOVER_MP, RECOVER_STATUS, POISON, IMP, ZOMBIE, STONE, REDUCE_TO_1_HP. Flash colour is keyed by outcome; dialog ID base is `SPRING_DIALOG_BASE = 1480`.
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
