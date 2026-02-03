# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Memory Routine

**How this works:** I (Setzer) maintain a prioritized list of the 10 most important concepts for working on this project. After each request, I revisit the list and decide whether the order should change or a new item should be added. Items that fall past #10 are moved to ARCHIVE.md, which I can scan when looking for specific information.

**To interface with this system:**
- The Top 10 list below contains the most critical knowledge, ranked by importance
- Reference sections below the Top 10 contain detailed supporting information
- ARCHIVE.md contains useful but less frequently needed information
- After completing a task, I update the list based on what proved most important

---

## Top 10 Most Important Concepts

### 1. FinishCheck Timing (Critical Bug Source)
When modifying events that give rewards and then transition to another map, `field.FinishCheck()` must be called **before** any screen transitions. The relevant event bit must be set **before** `FinishCheck()` is called. Getting this wrong causes rewards to not register.

### 2. NPC ID Offset (+0x10)
NPC IDs used in `maps.get_npc(map_id, npc_id)` are **offset by 0x10** from the map-local index. Slots 0x00-0x0f are reserved for the 14 playable characters. Formula: `npc_id = map_local_index + 0x10`.

### 3. Door ID Ranges
- **< 2000**: Two-way connections (normal doors)
- **2000-2999**: One-way exits (traps)
- **3000+**: One-way entrances (pits)

### 4. Event Exit Info Runtime Updates
Event tiles (IDs 1500-2000) acting as doors need runtime connection data. When adding new event tile connections, ensure **BOTH sides' partners** are included in `used_events` if they need runtime updates. Connections are stored as `[exit_id, entrance_id]`, so check both `m[0]` and `m[1]` partners.

### 5. Code Organization Principle
Event-specific modifications go in their respective event files (e.g., `event/burning_house.py`), not in top-level files like `event/events.py` or generic modules. For mode-specific changes, add a method like `ruination_mod()` to the event class and call it conditionally from `mod()`.

### 6. Execution Flow (wc.py)
1. **Memory** - Loads ROM, initializes free space tracking
2. **Data** - Reads/modifies game data (including door randomization)
3. **Events** - Modifies event scripts, distributes rewards
4. **Memory.write()** - Outputs the modified ROM

### 7. Key Module Locations
- **memory/space.py** - ROM space management (`Reserve`, `Allocate`)
- **data/maps.py** - Map/exit handling, door randomization via `Doors` class
- **data/doors.py** - Door randomizer orchestration
- **data/rooms.py** - Room and connection definitions
- **event/ruination.py** - Ruination mode implementation (~4400 lines)

### 8. Finding Map IDs by Name
1. Search `data/map_exit_extra.py` for location name in `exit_data`
2. Identify the entrance door ("Door Outside" goes INTO building)
3. Look up entrance door in `claude_reference/exits_raw.json` - the `dest_map` field is the interior map ID

### 9. NPC_BIT Calculation
Each NPC has a visibility bit determining if it appears when the map loads. Formula: `npc_bit = (event_byte + 0x60) * 8 + event_bit`. Special values: `ALWAYS_OFF = 0x6ff`, `ALWAYS_ON = 0x301` (in `data/npc_bit.py`).

### 10. SNES Addressing
- **SNES to ROM conversion**: `ROM_address = SNES_address - 0xC00000`
  - Example: SNES `$CEF100` → ROM `$0EF100` (not `$2EF100`!)
- ROM uses little-endian byte order
- The codebase constant `START_ADDRESS_SNES = 0xc00000` reflects this offset

---

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

## Resources

Note these files are LARGE. Only access them when necessary and be smart about reading them. Don't just load the entire file into context.

- **ROM offset reference**: `./claude_reference/ff3infov2.txt` - Comprehensive FF6 ROM map with addresses for all data structures
- Event script decompile: `./claude_reference/EventScriptTxt.txt`
- Event bits: `./data/event_bit.py`
- Dialog decompile: `./claude_reference/dialog_file.txt`
- Location names: `./claude_reference/location_names.json` - Maps `name_index` to display names
- Original map, event, and NPC JSON files: see `MAP_DATA_STRUCTURES.md`
  - Chests data: `./claude_reference/chests_raw.json`
  - MapEvents data: `./claude_reference/events_raw.json`
  - MapExits data: `./claude_reference/exits_raw.json`
  - Maps data: `./claude_reference/maps_data.json`
  - NPC data: `./claude_reference/npcs_raw.json`
