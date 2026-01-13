# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Worlds Collide is an open-worlds randomizer for Final Fantasy VI (SNES). It takes a vanilla US v1.0 ROM file, applies randomization and modifications based on configurable flags, and outputs a modified ROM.

## Running the Randomizer

```sh
# Basic usage - generate randomized ROM
python3 wc.py -i ffiii.smc

# Show all available flags and options
python3 wc.py -h

# Example with door randomization
python3 wc.py -i ffiii.smc -drdc   # Dungeon crawl mode
python3 wc.py -i ffiii.smc -dra    # Randomize all doors by world
python3 wc.py -i ffiii.smc -maps   # Map shuffle (overworld entrances)

# Debug mode (enables spoiler log)
python3 wc.py -i ffiii.smc -debug
```

## Door Randomizer System

The door randomizer is the primary feature of this branch. It shuffles connections between rooms/areas to create new exploration experiences.

### Door Randomizer Flags (args/doors.py)

| Flag | Description |
|------|-------------|
| `-drdc` | **Dungeon Crawl** - Creates one giant connected dungeon across all areas |
| `-dra` | **Randomize All** - Shuffles doors within each world (WoB/WoR separately) |
| `-drx` | **Crossworld** - Shuffles all doors across both worlds |
| `-dre` | **Each Area** - Randomizes each dungeon independently |
| `-maps` | **Map Shuffle Separate** - Randomizes overworld entrances within each world |
| `-mapx` | **Map Shuffle Crossworld** - Randomizes overworld entrances across worlds |
| `-ruin` | **Ruination Mode** - Rogue-like mode with procedural dungeon, no airship |

Individual area flags: `-dru` (Umaro), `-drun` (Upper Narshe), `-drem` (Esper Mountain), `-drob` (Owzer), `-drmf` (Magitek Factory), `-drsg` (Sealed Gate), `-drzb/-drzr` (Zozo WoB/WoR), `-drmz` (Mt Zozo), `-drlr` (Lete River), `-drze` (Zone Eater), `-drst` (Serpent Trench), `-drbh` (Burning House), `-drdt` (Daryl's Tomb), `-drpt` (Phantom Train), `-drcd` (Cyan's Dream), `-drmk` (Mt Kolts), `-drvc` (Veldt Cave)

### Core Files

**data/doors.py** - Main door randomizer orchestration
- `ROOM_SETS` dictionary defines which rooms belong to each randomization mode
- `Doors.__init__()` - Selects room sets based on flags, handles flag conflicts
- `Doors.mod()` - Creates randomized connections using the Network walk algorithm
- `Doors.map` - Output: `[[door_pairs], [oneway_pairs]]`

**data/rooms.py** - Room and connection definitions
- `room_data` dictionary: `room_id -> [doors, traps, pits, keys, locks, world]`
  - **doors** (int < 2000): Two-way connections
  - **traps** (2000-2999): One-way exits
  - **pits** (3000+): One-way entrances
  - **keys** (strings): Items that unlock locked elements
  - **locks** (dict): `{key_tuple: [locked_elements]}`
  - **world**: 0 = WoB, 1 = WoR
- `forced_connections` - Connections that must always be made
- `shared_exits` - Multiple exits that go to same destination
- `shared_oneways` - One-way exits that share destinations
- Root rooms (`'root-xx'`) serve as entry points for each area

**data/walks.py** - Graph connectivity algorithm
- `Network` class uses NetworkX directed graph to model room connections
- `Room` class tracks doors/traps/pits/keys/locks per room
- `Rooms` class manages collection with O(1) element lookups
- Key algorithm steps:
  1. `ForceConnections()` - Apply required connections
  2. `attach_dead_ends()` - Connect dead-end rooms first
  3. `connect_network()` - Recursive DFS to connect remaining rooms
  4. Validates network: ensures all areas reachable, balanced entrances/exits

**data/map_exit_extra.py** - Exit metadata
- `exit_data` dictionary: `exit_id -> [partner_door_id, description]`
- `doors_WOB_WOR` - Maps WoB doors to WoR equivalents
- `eventname_to_door` - Maps event names to door IDs

**data/event_exit_info.py** - One-way exit event metadata
- `event_exit_info` dictionary: `exit_id -> [address, length, split, state, desc, location, type]`
  - **address**: ROM address of the event code
  - **length**: Total byte length of the event
  - **split**: Byte offset where map load command begins
  - **state**: `[char_hidden, song_override, screen_hold, on_raft, update_parent]` - transition flags
  - **location**: `[map_id, x, y]` - destination coordinates
  - **type**: `'JMP'` (patchable subroutine) or `None` (logical only)
- Exit ID ranges:
  - 2001-2099: Standard one-way exits (trapdoors, jumps, conveyor belts, etc.)
  - 1501-1564: Event tiles that behave as doors (world map entrances, special triggers)
  - 5xxx: WoR variants of shared-map exits
- `event_return_map` - Maps switchyard exits back to their parent world map

**data/transitions.py** - Event script patching for one-way connections
- `Transitions` class handles event code modifications when connecting one-ways
- Patches map load commands to redirect to new destinations
- Uses `event_exit_info` to locate and modify exit event code

### Room Data Format

```python
room_data = {
    # Standard room: [doors, traps, pits, world]
    364: [[1797, 1798], [], [], 1],  # Umaro's Cave room

    # Room with keys and locks: [doors, traps, pits, keys, locks, world]
    'ms-wor-57': [[262], [], [], ['ac1'], {'ac1': [1558]}, 1],

    # Root room (entry point): provides entrance to area
    'root-u': [[], [2010], [3009], 1],  # Umaro entry
}
```

### Adding a New Area to Door Randomizer

1. Define rooms in `data/rooms.py` with door/trap/pit IDs
2. Add room set to `ROOM_SETS` in `data/doors.py`
3. Create root room for entry point
4. Add flag to `args/doors.py` if area should be individually toggleable
5. Handle any special connections in `forced_connections` or `shared_exits`

## General Architecture

### Execution Flow (wc.py)

1. **Memory** - Loads ROM, initializes free space tracking
2. **Data** - Reads/modifies game data; door randomization happens in `maps.mod()`
3. **Events** - Modifies event scripts, distributes rewards
4. **Memory.write()** - Outputs the modified ROM

### Key Modules

**memory/space.py** - ROM space management
- `Reserve(start, end, desc)` - Reserve fixed address range
- `Allocate(bank, size, desc)` - Allocate from bank's free space
- Banks: `Bank.C0` through `Bank.FF`

**data/maps.py** - Map/exit handling, integrates door randomization
- `Maps.__init__()` creates `Doors` instance
- `Maps.mod()` calls `self.doors.mod()` to generate randomized map
- `Maps.write()` writes exit data to ROM

**instruction/asm.py** - 65816 assembly instructions
**instruction/field/** - Field event scripting commands

### Writing ROM Modifications

```python
from memory.space import Bank, Reserve, Allocate
import instruction.asm as asm
import instruction.field as field

# Reserve specific address
space = Reserve(0x0a1234, 0x0a1240, "description")
space.write(asm.NOP(), asm.RTS())

# Allocate from bank
space = Allocate(Bank.C2, 50, "description")
space.write(
    asm.LDA(0x42, asm.IMM8),
    asm.STA(0x7e0000, asm.LNG),
)

# Field event commands
space.write(
    field.LoadMap(map_id, x, y, direction),
    field.Return(),
)
```

## Important Notes

- SNES addresses use `START_ADDRESS_SNES = 0xc00000` offset
- ROM uses little-endian byte order
- Door IDs < 2000 are two-way; 2000-2999 are one-way exits (traps); 3000+ are one-way entrances (pits)
- The walk algorithm uses backtracking DFS with validity checks to ensure fully connected networks
- Ruination mode (`-ruin`) is a separate system in `event/ruination.py` that overrides standard door randomization (see detailed section below)
- **FinishCheck timing for door rando**: When modifying events that give rewards (espers, items, characters) and then transition to another map, `field.FinishCheck()` must be called **before** any screen transitions (mosaic effects, map loads) that could be redirected by door randomization. Otherwise the check may not trigger properly if the player is warped to a different location. Additionally, the relevant event bit (e.g., `FINISHED_DOMA_WOR`) must be set **before** `FinishCheck()` is called, or objective detection will fail.

## Ruination Mode (`-ruin`)

Ruination Mode is an **in-development** roguelike-style door randomization mode. Unlike standard door randomization which shuffles existing connections, Ruination Mode creates a completely new dungeon topology with three independent branches emanating from a central hub.

### Core Concept

- **Hub**: Narshe School (3 exits, doors 393/394/395)
- **Three Branches**: Each branch starts from one hub door and terminates at one of three endpoints:
  - Sealed Gate → Kefka's Tower Left
  - Esper Mountain → Kefka's Tower Middle
  - Daryl's Tomb → Kefka's Tower Right
- **Progression**: Finding characters unlocks new areas, which are distributed across all branches
- **Goal**: Collect required characters/espers (from objectives) before accessing Kefka's Tower via airship

### Key Files

**event/events.py** - Entry point for ruination mode
- `ruination_mod()` - Main orchestrator that:
  1. Initializes `ruination_map` with starting party
  2. **CRITICAL**: Restricts `characters.available_characters` to only `planned_characters` from pre-planning phase
  3. Calls `generate_map_with_characters()` to build the dungeon map and assign rewards
  4. This restriction ensures character selection respects the pre-planned set that accounts for esper slot requirements

**event/ruination.py** - Main implementation (~1530 lines)
- `RuinationBranch(Network)` - Extends Network class for individual branch management
- `ruination_map` - Orchestrates all three branches, tracks rewards, distributes areas
- `pre_plan_character_acquisition()` - Pre-plans which characters will be obtained before map generation
- `generate_map_with_characters()` - Builds branch map and assigns character/esper/item rewards
- `ruination_start_game_mod()` - Creates the opening cutscene at Esper Gate

**data/rooms.py** - Custom ruination rooms (prefix `'ruin-'`)
- `ruin_hub` - Narshe School hub with 3 doors + pit returns from KT/Lete River
- `ruin_terminus_1/2/3` - Terminal rooms connecting to Kefka's Tower
- Custom rooms for logical separation: `ruin-mtek3`, `ruin-st-exit`, `ruin-nikeah`, `ruin-daryl`, etc.

**event/airship.py** - Modified to only allow Kefka's Tower access
- `ruination_mod()` - Airship console only offers "Go to Kefka's Tower?" option

### Data Structures

**ROOM_REWARD** (ruination.py:25-106) - Maps room IDs to reward locations:
```python
ROOM_REWARD = {
    'ruin-whelk': {"Whelk": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},
    313: {"Zozo": [RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM]},
    # ... 37 total reward locations
}
```

**CHARACTER_AREAS** (ruination.py:125-142) - Maps characters to unlockable areas:
```python
CHARACTER_AREAS = {
    'TERRA': ['Narshe', 'ReturnersHideout', 'Zozo', 'ZozoTower', 'Mobliz', 'SealedGate'],
    'LOCKE': ['Kohlingen', 'PhoenixCave', 'SouthFigaroCave', 'Narshe'],
    # ... one entry per character
}
```

**RUIN_ROOM_SETS** (ruination.py:148-193) - Maps area names to room lists:
```python
RUIN_ROOM_SETS = {
    'Doma': [421, 422, 423, ...],  # All rooms in Doma
    'UmarosCave': [364, 365, 366, ...],
    # ... 35 named areas
}
```

**CHARACTER_LOCKED_REWARDS** (ruination.py:10-18) - Rewards requiring specific characters:
```python
CHARACTER_LOCKED_REWARDS = {
    'TERRA': ['Whelk', 'Zozo'],
    'LOCKE': ["Narshe WOR"],
    'STRAGO': ["Burning House"],
    # ...
}
```

**forced_same_branch** (ruination.py:110-120) - Areas that must be on the same branch:
```python
forced_same_branch = {
    'Zozo': {'ZozoTower', 'MtZozo'},
    'Thamasa': {'VeldtCave', 'EbotsRock'},
    'Nikeah': {'CrescentMtn'}
}
```

### Algorithm Overview

1. **Initialization** (`ruination_map.__init__`):
   - Parse objectives to determine required characters/espers
   - Call `pre_plan_character_acquisition()` to determine which characters will be obtained
   - Create 3 `RuinationBranch` objects, each with one hub door and one terminus
   - Distribute initial areas based on starting party characters

2. **Pre-Planning Phase** (`pre_plan_character_acquisition()`):
   - Randomly selects characters to meet the objective requirements
   - Calculates total reward slots in areas unlocked by starting party + planned characters
   - Ensures sufficient esper slots exist (accounting for character slots that can't hold espers)
   - Adds more characters if needed to unlock additional areas with esper slots
   - Returns: `(planned_characters, reserve_characters, dead_checks_allowed)`
   - **IMPORTANT**: The `planned_characters` list determines which characters can be assigned during map generation. The caller must restrict `characters.available_characters` to this list before calling `generate_map_with_characters()` (see events.py:247-250).

3. **Map Generation** (`generate_map_with_characters`):
   ```
   while (characters_obtained < required OR espers_obtained < required):
       select viable branch (has hub rooms AND has uncollected rewards)
       while not found_reward:
           extend_branch_path()  # Add one connection
           check_for_rewards()   # See if we reached a reward
       process_rewards()         # Assign character/esper, unlock new areas
   finalize_map() for each branch
   ```

4. **Branch Extension** (`extend_branch_path`):
   - Priority: forced connections > downstream traps > downstream doors
   - Find valid entrances: available hub connections or upstream path with enough exits
   - Connect exit to entrance, moving "active" room forward

5. **Branch Finalization** (`finalize_map`):
   - Balance trap/pit counts
   - Connect downstream nodes back to upstream
   - Connect terminus to hub
   - Connect remaining dead-end rooms

### Known Issues / Development Status

1. **Branch mapping issues**: The main reported problem is that branch mapping "doesn't work quite right yet" - likely related to edge cases in `extend_branch_path()` where valid connections can't be found.

2. **Dead-end-only branches** (ruination.py:1004-1006): If a branch gets only dead-end rooms initially (e.g., just 'Gau Father House' and 'Floating Continent'), it has no hub rooms and can get stuck. Current mitigation: add an "extra" hub room from `CHARACTER_AREAS['EXTRA']`.

3. **`extend_branch_path_old()`**: An older, more complex version is kept for reference. Comments indicate "the method keeps failing" due to running out of valid trapdoors.

4. **`ruination_dont_force`** (rooms.py:1017): Only contains door 1079 (Sealed Gate quick exit). More doors may need to be excluded from forced connections in ruination mode.

### Testing Ruination Mode

```sh
# Basic ruination mode
python3 wc.py -i ffiii.smc -ruin

# With debug output
python3 wc.py -i ffiii.smc -ruin -debug
```

The mode prints extensive debug output when `verbose = True` (default in ruination_map class), showing:
- Branch viability checks
- Connection decisions
- Reward discoveries
- Area distributions

### Adding Content to Ruination Mode

1. **New reward location**: Add entry to `ROOM_REWARD` with room ID and reward types
2. **New area**: Add to `RUIN_ROOM_SETS` and associate with character(s) in `CHARACTER_AREAS`
3. **Character lock**: Add to `CHARACTER_LOCKED_REWARDS` if reward requires specific character
4. **Same-branch constraint**: Add to `forced_same_branch` if areas must stay together

## Resources
- The event script begins at offset 0xa0000.  A full decompile of the event script is @https://drive.google.com/file/d/1onKV8AgBBjj-pTVEJV57nH_ED2UAgtC6/view?usp=drive_link
- Event bits tracking various events in the game are listed in @~/data/event_bit.py
