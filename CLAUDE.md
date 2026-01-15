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

## NPC and Event Editing

### NPC ID Indexing

**CRITICAL**: NPC IDs used in `maps.get_npc(map_id, npc_id)` are **offset by 0x10** from the map-local index:
```python
npc_id = map_local_index + 0x10
```

This is because **slots 0x00 through 0x0f are reserved for the 14 playable characters**.

**Examples**:
- Tritoch Peak Lone Wolf: map-local index 11 (0x0b) → `npc_id = 0x1b`
- Tritoch Peak Mog: map-local index 12 (0x0c) → `npc_id = 0x1c`
- Narshe WoB Lone Wolf: map-local index 25 (0x19) → `npc_id = 0x29`

**Code reference** (data/maps.py:231):
```python
def get_npc_index(self, map_id, npc_id):
    first_npc_index = (self.maps[map_id]["npcs_ptr"] - self.maps[0]["npcs_ptr"]) // NPC.DATA_SIZE
    return first_npc_index + (npc_id - 0x10)
```

### NPC_BIT Calculation

Each NPC has a visibility bit (NPC_BIT) that determines whether it appears when the map loads. NPC_BITs range from **0x300 to 0x6ff**.

**Formula** (stored in each NPC):
```python
npc_bit = (event_byte + 0x60) * 8 + event_bit
```

**Reverse calculation** (data/npc_bit.py:170-176):
```python
def event_byte(npc_bit):
    return (npc_bit // 8) - 0x60

def event_bit(npc_bit):
    return npc_bit % 8
```

**Example** (Narshe WoB Lone Wolf):
- Stored: `event_byte=103, event_bit=7`
- Calculated: `npc_bit = (103 + 0x60) * 8 + 7 = 1599 = 0x63f`

**Special NPC_BITs** (data/npc_bit.py):
- `ALWAYS_OFF = 0x6ff` - NPC never appears
- `ALWAYS_ON = 0x301` - NPC always appears

### Copying NPCs Between Maps

When moving/copying NPCs between maps (e.g., in ruination mode), copy **all properties** from the source NPC:

**Essential properties** (data/npc.py:9-33):
- **Visual**: `sprite`, `palette`, `split_sprite`, `const_sprite`
- **Behavior**: `direction`, `speed`, `movement`, `no_face_on_trigger`, `vehicle`
- **Positioning**: `x`, `y`, `map_layer`, `background_layer`, `background_scrolls`
- **Events**: `event_address`, `event_byte`, `event_bit`
- **Unknown**: `unknown1`, `unknown2` (copy these too for safety)

**Pattern**:
```python
# Load source NPC
source_npc = self.maps.get_npc(source_map_id, source_npc_id)

# Get or create destination NPC
dest_npc = self.maps.get_npc(dest_map_id, dest_npc_id)

# Copy all properties
dest_npc.sprite = source_npc.sprite
dest_npc.palette = source_npc.palette
dest_npc.direction = source_npc.direction
dest_npc.no_face_on_trigger = source_npc.no_face_on_trigger
dest_npc.speed = source_npc.speed
dest_npc.movement = source_npc.movement
dest_npc.split_sprite = source_npc.split_sprite
dest_npc.const_sprite = source_npc.const_sprite
dest_npc.vehicle = source_npc.vehicle
dest_npc.event_address = source_npc.event_address
dest_npc.map_layer = source_npc.map_layer
dest_npc.background_scrolls = source_npc.background_scrolls
dest_npc.background_layer = source_npc.background_layer
dest_npc.unknown1 = source_npc.unknown1
dest_npc.unknown2 = source_npc.unknown2

# Override position-specific properties
dest_npc.x = new_x
dest_npc.y = new_y
dest_npc.event_bit = npc_bit.event_bit(new_npc_bit)
dest_npc.event_byte = npc_bit.event_byte(new_npc_bit)
```

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

### Key Data Structures

**ROOM_REWARD** (ruination.py) - Maps room IDs to reward locations (37 total)
**CHARACTER_AREAS** (ruination.py) - Maps characters to areas they unlock
**RUIN_ROOM_SETS** (ruination.py) - Maps area names to room lists (35 areas)
**CHARACTER_LOCKED_REWARDS** (ruination.py) - Rewards requiring specific characters
**AREA_SHOPS** (ruination.py) - Maps areas to shop IDs

### Algorithm Overview

1. **Pre-Planning**: Determine which characters to assign based on objectives and esper slot availability
2. **Map Generation Loop**:
   - Select viable branch
   - Extend branch path until reward found
   - Assign character/esper reward
   - Unlock new areas, distribute to branches
   - Repeat until objectives met
3. **Finalization**: Connect remaining dead-ends and balance trap/pit counts

### Reward Assignment Patterns

**Character assignment** - Use `Characters` class interface:
```python
# Get character (automatically marks unavailable)
slot.id = characters.get_random_available(exclude=non_planned_chars)
slot.type = RewardType.CHARACTER

# Set character path for dependency tracking
characters.set_character_path(slot.id, slot.event.character_gate())
```

**Reward updates** - Shared object references automatically propagate changes:
- `events.py` populates `ROOM_REWARD` with actual `Reward` objects
- `process_rewards()` modifies these objects
- Changes propagate to `rewards` list, `ROOM_REWARD`, and `reward_slots`

### Character Path Tracking

**Purpose**: Tracks transitive character dependencies (e.g., Edgar requires Locke who requires Terra)

**Pattern**: Always use `slot.event.character_gate()` as source of truth:
```python
characters.set_character_path(slot.id, slot.event.character_gate())
```
- Returns `None` for starting party areas
- Returns gating character ID for locked areas
- Automatically builds transitive dependency chain

### Dried Meat for Gau

**Problem**: If Gau is assigned to Veldt, ensure dried meat is available in non-Veldt-gated shops

**Solution**:
1. Track accessible shops during map generation (`self.accessible_shops`)
2. Use `get_non_veldt_gated_shops()` to filter out Veldt-gated shops
3. Assign dried meat only to accessible, non-Veldt-gated shops
4. Uses `character_paths` to identify Veldt-gated areas

### Ruination Mode Starting Menu

**Implementation** (menus/pregame.py):

Ruination mode has a custom starting menu that differs from standard mode to accommodate single-slot save system.

**Boot Sequence** (`invoke_load_game_mod()`):
- **Ruination mode**: Always shows pregame menu (skips auto-load menu)
- **Standard mode**: Shows load menu if saves exist, otherwise pregame menu
- ROM address: 0x3017c-0x301b1

**Menu Rendering** (`draw_options_mod()`, `initialize_mod()`):
- Tests save validity at initialization (JSR 0x7023)
- Creates two menu variants:
  - **No save**: 3 options (New Game, Flags, Config)
  - **Save exists**: 4 options (New Game, Load Saved Game, Flags, Config)
- Uses memory flag at 0x1300 to track active menu layout (0 = no save, 1 = has save)

**Menu Navigation** (`sustain_mod()`):
- Two separate option jump tables (one for each menu layout)
- "Load Saved Game" handler invokes load menu (command 0x20) for single-slot save
- Runtime checks flag at 0x1300 to route button presses to correct table

**Key Memory Locations**:
- 0x1300: Menu layout flag (ruination mode only)
- 0x7023: Save validity test subroutine (sets carry if save exists)
- 0x2f: Initialize pregame menu command
- 0x20: Initialize load menu command

**Integration**:
- Works with existing save system (menus/save.py) that auto-saves to slot 1 and wipes on death
- Conditional logic uses `if args.ruination_mode:` checks at build time

## Resources
- Event script decompile: @./claude_reference/EventScriptTxt.txt
- Event bits: @./data/event_bit.py
- Original map, event, and npc JSON files: see MAP_DATA_STRUCTURES.md for information on these files.
- - Chests data:  @./claude_reference/chests_raw.json
  - MapEvents data: @./claude_reference/events_raw.json
  - MapExits data: @./claude_reference/exits_raw.json
  - Maps data: @./claude_reference/maps_data.json
  - NPC data: @./claude_reference/npcs_raw.json
