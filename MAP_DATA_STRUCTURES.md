# Map Data Structures - Summary

## Overview

This document describes how map-related data (NPCs, Events, and Exits) is read from the ROM and stored in Python objects in the WorldsCollide codebase.

## Data Flow

1. **wc.py** - Entry point that initializes everything:
   - Creates `Memory()` which loads the ROM file
   - Creates `Data(memory.rom, args)` which loads all game data

2. **data/data.py** - Main data loader:
   - Creates `maps.Maps(rom, args, items)` which handles all map-related data

3. **data/maps.py** - Maps coordinator:
   - Loads 416 maps from the ROM
   - Initializes three main collections:
     - `npcs.NPCs(rom)` - All NPC data
     - `events.MapEvents(rom)` - All map event data
     - `exits.MapExits(rom)` - All exit data (short and long)

## Core Data Structures

### Maps (data/maps.py)

The `Maps` class manages 416 maps and their associations with NPCs, events, and exits.

**Key Attributes:**
- `maps`: List of 416 dictionaries, each containing:
  - `id`: Map index (0-415)
  - `name_index`: Index for map name lookup
  - `entrance_event_address`: Address of event executed when entering map
  - `events_ptr`: Pointer to first event for this map
  - `npcs_ptr`: Pointer to first NPC for this map
  - `short_exits_ptr`: Pointer to first short exit for this map
  - `long_exits_ptr`: Pointer to first long exit for this map

**ROM Addresses:**
- Event pointers: `0x40000 + (map_id * 2)`
- NPC pointers: `0x41a10 + (map_id * 2)`
- Short exit pointers: `0x1fbb00 + (map_id * 2)`
- Long exit pointers: `0x2df480 + (map_id * 2)`
- Entrance events: `0x11fa00 + (map_id * 3)`

**Pointer System:**
Each map has pointers that define ranges in the global arrays. For example:
- Events for map 5 start at `maps[5]["events_ptr"]` and end at `maps[6]["events_ptr"]`
- Number of events = `(maps[6]["events_ptr"] - maps[5]["events_ptr"]) / 5` (5 bytes per event)

### NPCs (data/npc.py, data/npcs.py)

**Total Count:** 2192 NPCs
**Data Size:** 9 bytes per NPC
**ROM Start Address:** `0x041d52`

**NPC Attributes:**
- **Position & Movement:**
  - `x`, `y`: Tile coordinates (0-127 for x, 0-63 for y)
  - `direction`: Facing direction (0=up, 1=right, 2=down, 3=left)
  - `speed`: Movement speed (0=slowest, 1=slow, 2=fast, 3=fastest)
  - `movement`: Movement type (0=no move, 1=script, 2=player, 3=random, 4=activated)
  - `no_face_on_trigger`: If 1, NPC doesn't turn to face player when triggered

- **Graphics:**
  - `sprite`: Sprite ID (0-255)
  - `palette`: Color palette (0-7)
  - `split_sprite`: If sprite uses multiple tiles
  - `const_sprite`: If 1, sprite doesn't animate
  - `vehicle`: Vehicle type (0=none, 1-3=various vehicles)

- **Event Handling:**
  - `event_address`: 18-bit address of event code (0x000000-0x03ffff)
  - `event_byte`: Event byte for conditional visibility (0-127)
  - `event_bit`: Event bit for conditional visibility (0-7)

- **Layers:**
  - `map_layer`: Which map layer NPC appears on (0-3)
  - `background_layer`: Background layer setting (0-3)
  - `background_scrolls`: If background scrolls with NPC

**Data Format (9 bytes):**
```
Byte 0: Event address bits 0-7
Byte 1: Event address bits 8-15
Byte 2: [bits 0-1: event addr 16-17] [bits 2-4: palette] [bit 5: bg scrolls] [bits 6-7: event bit 0-1]
Byte 3: [bit 0: event bit 2] [bits 1-7: event byte]
Byte 4: [bits 0-6: x] [bit 7: no_face_on_trigger]
Byte 5: [bits 0-5: y] [bits 6-7: speed]
Byte 6: sprite
Byte 7: [bits 0-3: movement] [bits 4-5: map_layer] [bits 6-7: vehicle]
Byte 8: [bits 0-1: direction] [bit 2: const_sprite] [bits 3-4: bg_layer] [bit 6: split_sprite] [other bits: unknown]
```

### MapEvents (data/map_event.py, data/map_events.py)

**Total Count:** 1164 events
**Data Size:** 5 bytes per event
**ROM Start Address:** `0x040342`

**MapEvent Attributes:**
- `x`: X coordinate on map tile (0-255)
- `y`: Y coordinate on map tile (0-255)
- `event_address`: 24-bit address of event code to execute

**Data Format (5 bytes):**
```
Byte 0: x coordinate
Byte 1: y coordinate
Byte 2: Event address bits 0-7
Byte 3: Event address bits 8-15
Byte 4: Event address bits 16-23
```

**Purpose:**
Map events trigger when the player steps on specific tile coordinates. They're different from NPCs because:
- They're invisible (no sprite)
- They trigger on exact tile position
- They don't have movement or AI

### MapExits (data/map_exit.py, data/map_exits.py)

There are two types of exits: Short and Long.

#### Short Exits

**Total Count:** 1129 (0x469) exits
**Data Size:** 6 bytes per exit
**ROM Start Address:** `0x1fbf02`

**ShortMapExit Attributes:**
- `x`: X coordinate of exit trigger (0-255)
- `y`: Y coordinate of exit trigger (0-255)
- `dest_map`: Destination map ID (0-415, 9 bits)
- `dest_x`: Destination X coordinate (0-255)
- `dest_y`: Destination Y coordinate (0-255)
- `unknown`: Unknown flags (7 bits)

**Data Format (6 bytes):**
```
Byte 0: x coordinate
Byte 1: y coordinate
Byte 2: Destination map bits 0-7
Byte 3: [bit 0: dest map bit 8] [bits 1-7: unknown]
Byte 4: dest_x
Byte 5: dest_y
```

#### Long Exits

**Total Count:** 152 (0x98) exits
**Data Size:** 7 bytes per exit
**ROM Start Address:** `0x2df882`

**LongMapExit Attributes:**
- `x`: X coordinate of exit start (0-255)
- `y`: Y coordinate of exit start (0-255)
- `size`: Length of exit line (0-127 tiles)
- `direction`: 0x00=horizontal, 0x80=vertical
- `dest_map`: Destination map ID (0-415, 9 bits)
- `dest_x`: Destination X coordinate (0-255)
- `dest_y`: Destination Y coordinate (0-255)
- `unknown`: Unknown flags (7 bits)

**Data Format (7 bytes):**
```
Byte 0: x coordinate
Byte 1: y coordinate
Byte 2: [bits 0-6: size] [bit 7: direction]
Byte 3: Destination map bits 0-7
Byte 4: [bit 0: dest map bit 8] [bits 1-7: unknown]
Byte 5: dest_x
Byte 6: dest_y
```

**Purpose:**
Long exits create a line of exit triggers (horizontal or vertical) rather than a single point. This is more efficient for doorways and corridors.

## Important Implementation Details

### Pointer-Based Architecture

All NPCs, events, and exits are stored in global arrays. Each map doesn't own its data; instead, it has pointers defining its range in these arrays:

```python
# Example: Get NPCs for map 10
first_npc_ptr = maps.maps[10]["npcs_ptr"]
next_npc_ptr = maps.maps[11]["npcs_ptr"]
npc_count = (next_npc_ptr - first_npc_ptr) // 9  # 9 bytes per NPC

# Calculate index in global NPC array
first_npc_index = (first_npc_ptr - maps.maps[0]["npcs_ptr"]) // 9
```

### Adding/Removing Data

When adding or removing NPCs, events, or exits from a map, all subsequent maps' pointers must be updated:

```python
# When adding an NPC to map_id:
for map_index in range(map_id + 1, MAP_COUNT):
    maps[map_index]["npcs_ptr"] += NPC.DATA_SIZE
```

### Event Addresses

Event addresses in the data are relative to the event code start address. When setting an event address:

```python
from instruction.event import EVENT_CODE_START
relative_address = absolute_address - EVENT_CODE_START
```

## Export Script Usage

I've created `export_map_data.py` which exports all this data to JSON format:

```bash
# Run the export script with a ROM file
python export_map_data.py -i path/to/ff3.smc
```

**Output Files:**

1. **maps_data.json** - All 416 maps with their NPCs, events, and exits grouped together
   - Easy to understand which data belongs to which map
   - Includes pointer information
   - Best for map-by-map analysis

2. **npcs_raw.json** - All 2192 NPCs in global array order
   - Indexed by position in global array
   - Useful for cross-referencing

3. **events_raw.json** - All 1164 events in global array order
   - Indexed by position in global array
   - Useful for cross-referencing

4. **exits_raw.json** - All exits (short and long) in global array order
   - Separated into "short_exits" and "long_exits" arrays
   - Indexed by position in global arrays
   - Useful for cross-referencing

## Reading the Exported Data

Once you run the export script, you can upload the JSON files for reference. The data will be in a format that's easy to parse and understand, with:
- Numeric values preserved
- Hex addresses formatted as strings (e.g., "0x5eb3")
- Clear structure showing relationships between maps and their data
- Index values for cross-referencing between files
