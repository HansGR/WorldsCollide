# ARCHIVE.md

This file contains useful reference information that has been moved from the Top 10 in CLAUDE.md. Scan this file when looking for specific detailed information.

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
Used when the reward is triggered by an entrance event (map load). The patch is a static method on the event class that takes `args` and returns event code. When `args.character_gating` is true, use `BranchIfAll` to combine the "not finished" and "character recruited" checks:
```python
@staticmethod
def entrance_door_patch(args):
    CYAN = 2
    if args.character_gating:
        src = [
            field.BranchIfAll([event_bit.FINISHED_MT_ZOZO, False,
                               event_bit.character_recruited(CYAN), True], continue_addr),
            field.Return()
        ]
    else:
        src = [
            field.BranchIfEventBitClear(event_bit.FINISHED_MT_ZOZO, continue_addr),
            field.Return()
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
