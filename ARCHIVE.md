# ARCHIVE.md

This file contains useful reference information that has been moved from the Top 10 in CLAUDE.md. Scan this file when looking for specific detailed information.

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
