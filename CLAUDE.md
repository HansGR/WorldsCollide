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

# Example with specific output file
python3 wc.py -i ffiii.smc -o output.smc

# Debug mode (enables spoiler log)
python3 wc.py -i ffiii.smc -debug

# Output log to stdout instead of file
python3 wc.py -i ffiii.smc -slog
```

## Architecture

### Execution Flow (wc.py)

1. **Memory** - Loads ROM, initializes free space tracking
2. **Data** - Reads and modifies game data (characters, items, spells, maps, enemies, etc.)
3. **Events** - Modifies event scripts and distributes rewards (characters, espers, items)
4. **Menus/Battle/Settings/BugFixes** - Apply additional modifications
5. **Memory.write()** - Outputs the modified ROM

### Key Modules

**memory/** - ROM manipulation and space management
- `space.py` - Core abstraction for managing ROM space. Use `Reserve(start, end, desc)` for fixed addresses, `Allocate(bank, size, desc)` for dynamic allocation. Banks are `Bank.C0` through `Bank.FF`.
- `rom.py` - Low-level ROM read/write operations
- `free.py` - Defines initially free ROM regions

**data/** - Game data structures
- `data.py` - Orchestrates all data modules; each module follows pattern: `__init__` reads data, `mod()` applies randomization, `write()` outputs changes
- Major subsystems: `characters`, `items`, `spells`, `maps`, `enemies`, `espers`, `shops`, `chests`
- `maps.py` - Complex module handling map exits, doors, NPCs, events, and door randomization
- `event_bit.py`, `npc_bit.py` - Game flag/bit definitions used for event state

**event/** - Event scripting system
- `event.py` - Base class for location events; subclasses implement specific locations (e.g., `narshe_wob.py`, `phantom_train.py`)
- `events.py` - Loads all event modules, handles reward distribution logic (open world vs character gating)
- `event_reward.py` - Reward types: `CHARACTER`, `ESPER`, `ITEM`
- `ruination.py` - Alternative game mode with procedural map generation

**instruction/** - SNES assembly and event scripting
- `asm.py` - 65816 assembly instructions (NOP, LDA, STA, JSR, etc.)
- `field/` - Field event instructions (dialogs, NPC movement, map transitions, etc.)
- `c0.py` through `c4.py`, `f0.py` - Bank-specific instruction definitions

**args/** - Command line flags organized by category
- `arguments.py` - Main parser; flag groups: settings, objectives, characters, scaling, items, graphics, etc.
- Each file (e.g., `characters.py`, `items.py`) defines `parse()`, `process()`, and `flags()` functions

**constants/** - Game constant definitions (items, spells, espers, commands, etc.)

### Writing ROM Modifications

```python
from memory.space import Bank, Reserve, Allocate, Write
import instruction.asm as asm
import instruction.field as field

# Reserve specific address range
space = Reserve(0x0a1234, 0x0a1240, "description")
space.write(asm.NOP(), asm.RTS())

# Allocate from bank's free space
space = Allocate(Bank.C2, 50, "description")
space.write(
    asm.LDA(0x42, asm.IMM8),
    asm.STA(0x7e0000, asm.LNG),
)

# Field event scripting
space.write(
    field.Dialog(dialog_id),
    field.AddItem(item_id),
    field.Return(),
)
```

### Event System Pattern

Event classes in `event/` follow this structure:
```python
class LocationName(Event):
    def name(self):
        return "Location Name"

    def character_gate(self):
        return None  # or character ID for gated locations

    def init_rewards(self):
        self.reward = self.add_reward(RewardType.CHARACTER | RewardType.ESPER)

    def mod(self):
        # Modify event scripts, use self.reward.id and self.reward.type
```

## Important Implementation Notes

- SNES addresses use `START_ADDRESS_SNES = 0xc00000` offset; `space.start_address_snes` gives SNES address
- ROM uses little-endian byte order
- Event bits control game state; defined in `data/event_bit.py`
- Door/exit randomization modifies `data/map_exit_extra.py` connections
- Label system in Space allows forward references in assembly code
