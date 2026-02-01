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

4. **Finalization** (`finalize_map`): Closes all remaining connections in 6 steps:
   - Step 1: Balance traps vs pits
   - Step 2: Connect downstream nodes to upstream
   - Step 3: Connect remaining traps to pits
   - Step 4: Connect the terminus
   - Step 5: Pair excess hub doors
   - Step 6: Connect dead ends to remaining doors

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

**event/ruination.py** (~1530 lines) - Main implementation
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
