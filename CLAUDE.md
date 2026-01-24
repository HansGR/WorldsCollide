# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Worlds Collide is an open-worlds randomizer for Final Fantasy VI (SNES). It takes a vanilla US v1.0 ROM file, applies randomization and modifications based on configurable flags, and outputs a modified ROM.

## Running the Randomizer

```sh
# Basic usage
python3 wc.py -i ffiii.smc

# Show all available flags
python3 wc.py -h

# Common modes
python3 wc.py -i ffiii.smc -drdc   # Dungeon crawl mode
python3 wc.py -i ffiii.smc -ruin   # Ruination mode
python3 wc.py -i ffiii.smc -debug  # Enable spoiler log
```

## Architecture

### Execution Flow (wc.py)

1. **Memory** - Loads ROM, initializes free space tracking
2. **Data** - Reads/modifies game data (including door randomization)
3. **Events** - Modifies event scripts, distributes rewards
4. **Memory.write()** - Outputs the modified ROM

### Key Modules

**memory/space.py** - ROM space management
- `Reserve(start, end, desc)` - Reserve fixed address range
- `Allocate(bank, size, desc)` - Allocate from bank's free space

**data/maps.py** - Map/exit handling, integrates door randomization via `Doors` class

**data/doors.py** - Main door randomizer orchestration
- Uses `data/walks.py` Network algorithm to create connected room graphs

**data/rooms.py** - Room and connection definitions
- Door IDs < 2000: two-way connections
- 2000-2999: one-way exits (traps)
- 3000+: one-way entrances (pits)

**instruction/asm.py** - 65816 assembly instructions
**instruction/field/** - Field event scripting commands

### Important Notes

- SNES addresses use `START_ADDRESS_SNES = 0xc00000` offset
- ROM uses little-endian byte order
- **FinishCheck timing**: When modifying events that give rewards and then transition to another map, `field.FinishCheck()` must be called **before** any screen transitions. The relevant event bit must be set **before** `FinishCheck()` is called.

## Code Organization

Event-specific modifications should be placed in their respective event files (e.g., `event/burning_house.py`, `event/lone_wolf.py`), not in top-level files like `event/events.py` or generic modules like `event/ruination.py`. This keeps related logic together, makes it easier to find later, and clarifies how changes interact with other modifications to the same event. For mode-specific changes (e.g., ruination mode), add a method like `ruination_mod()` or `ruination_inn_mod()` to the event class and call it conditionally from `mod()`.

## NPC and Event Editing

### NPC ID Indexing
NPC IDs used in `maps.get_npc(map_id, npc_id)` are **offset by 0x10** from the map-local index.  This is because **slots 0x00 through 0x0f are reserved for the 14 playable characters**.


### NPC_BIT Calculation
Each NPC has a visibility bit (NPC_BIT) that determines whether it appears when the map loads. NPC_BITs range from **0x300 to 0x6ff**.

**Formula** (stored in each NPC):
```python
npc_bit = (event_byte + 0x60) * 8 + event_bit
```

**Special NPC_BITs** (data/npc_bit.py):
- `ALWAYS_OFF = 0x6ff` - NPC never appears
- `ALWAYS_ON = 0x301` - NPC always appears

### Finding NPCs in Reference Data
Reference JSON files are located in the remote `claude_ruination` branch under `claude_reference/`:
- `npcs_raw.json` - All NPCs with properties (index, x, y, sprite, event_byte, event_bit, etc.)
- `maps_data.json` - Maps with their NPCs listed (includes map-local index)

**To find an NPC**:
1. Locate the map in `maps_data.json` by map_id (e.g., Narshe WoB = 0x14 = 20 decimal)
2. Find the NPC in that map's `npcs` array by position (x, y) or other properties
3. Note the map-local index (array position) and sprite properties
4. Calculate `npc_id = map_local_index + 0x10` for use in `get_npc()`
5. Cross-reference global index in `npcs_raw.json` for full property details

## Finding Map IDs by Name

To find a map ID when given a location name (e.g., "Sabin's House interior"):

1. **Search `data/map_exit_extra.py`** for the location name in `exit_data`:
   ```
   grep "Sabin.*House" data/map_exit_extra.py
   ```
   This reveals door relationships like:
   - `361: [362, "Sabin's House Door Outside"]` - door 361 leads to door 362

2. **Identify the entrance door**: The "Door Outside" (361) is the entrance going INTO the building

3. **Look up the entrance door in `exits_raw.json`**:
   ```
   grep -A5 '"index": 361' claude_reference/exits_raw.json
   ```
   The `dest_map` field shows where that door leads:
   - `"dest_map": 94` means the interior is map 94

**Example**: Sabin's House
- Door 361 ("Outside") → `dest_map: 94` = Interior map ID
- Door 362 ("Inside") → `dest_map: 93` = Exterior map ID

## Ruination Mode (`-ruin`)

Ruination Mode creates a roguelike-style dungeon with three independent branches emanating from a central hub.

### Core Concept

- **Hub**: Narshe School (3 exits)
- **Three Branches**: Each branch connects hub → starting area → Kefka's Tower (left/middle/right)
- **Progression**: Finding characters unlocks new areas, distributed across all branches
- **Goal**: Collect required characters/espers before accessing Kefka's Tower via airship

### Key Files

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

## Event Exit Info and Runtime Updates

**Key concept**: Event tiles (IDs 1500-2000) that act as doors need connection data at runtime. Some are vanilla tiles with existing event code in the ROM; others are new "switchyard" tiles created for door randomization/ruination.

### Data Structures

- **`event_exit_info`** (data/event_exit_info.py): Contains `[event_addr, length, split, state, desc, location, method]` for each event tile. Switchyard tiles have `event_addr = None` because they don't exist in vanilla ROM.

- **`event_door_connection_data`** (data/map_exit_extra.py): Contains door-style connection data `[dest_map, dest_x, dest_y, ...]` for event tiles acting as doors.

- **`exit_data`** (data/map_exit_extra.py): Maps door IDs to their vanilla partners `[partner_id, description]`.

### Runtime Update Flow (maps.py:write)

1. **Build `used_events`**: Collects all event tile IDs that need their `event_exit_info` updated, INCLUDING vanilla partners of event tiles whose partners are also event tiles.

2. **Update addresses**: For each event in `used_events` with `event_addr = None`, find the event at its switchyard location and update `event_exit_info[e][0]` with the actual address.

3. **Transitions**: When `Transitions` creates entrance `EventExit` objects, if the entrance is an event tile (1500-2000) and its vanilla partner is also an event tile, it uses `use_event_info=partner_id` to get the partner's event code. **The partner's `event_exit_info` must have been updated first.**

### Common Pitfall

When adding new event tile connections, ensure BOTH sides' partners are included in `used_events` if they need runtime updates. Connections are stored as `[exit_id, entrance_id]`, so check both `m[0]` and `m[1]` partners.

## Resources
Note these files are LARGE.  Only access them when necessary and be smart about reading them.  Don't just load the entire file into context. 
- Event script decompile: ./claude_reference/EventScriptTxt.txt
- Event bits: ./data/event_bit.py
- Dialog decompile:  ./claude_reference/dialog_file.txt
- Original map, event, and npc JSON files: see MAP_DATA_STRUCTURES.md for information on these files.
  - Chests data:  ./claude_reference/chests_raw.json
  - MapEvents data: ./claude_reference/events_raw.json
  - MapExits data: ./claude_reference/exits_raw.json
  - Maps data: ./claude_reference/maps_data.json
  - NPC data: ./claude_reference/npcs_raw.json
