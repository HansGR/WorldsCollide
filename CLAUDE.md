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
- Event script decompile: @https://drive.google.com/file/d/1onKV8AgBBjj-pTVEJV57nH_ED2UAgtC6/view?usp=drive_link
- Event bits: @data/event_bit.py
- Original map, event, and npc JSON files: see MAP_DATA_STRUCTURES.md for information on these files.
- - Chests data:  @https://drive.google.com/file/d/1XQQ0A3YWqgtBDxR84ib6q32lgXAsoGjA/view?usp=drive_link
  - MapEvents data: @https://drive.google.com/file/d/1CONaDksmi3Qyis_DXl-vc06M6IrN-u4t/view?usp=drive_link
  - MapExits data: @https://drive.google.com/file/d/1MIlD-nRo4r9aNGiLZzI94FV7rnyUJeW_/view?usp=drive_link
  - Maps data: @https://drive.google.com/file/d/1O1Hs7EUsUM_a1LZtzVZZktgacy6sl5nn/view?usp=drive_link
  - NPC data: @https://drive.google.com/file/d/1W2N0B99VtgR8-JyqDwtJLzj1HTjSnZ4K/view?usp=drive_link
