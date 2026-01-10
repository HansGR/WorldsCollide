# CLAUDE.md - Development Notes

This document contains implementation notes and architectural insights for future development work.

## Door Randomization System

### Key Data Structures

#### 1. **walks.map** - Door Connection Mappings
The `walks.map` structure is the authoritative source for door connections after randomization:
- `walks.map[0]`: List of `[door1, door2]` pairs for **two-way doors**
- `walks.map[1]`: List of `[exit, entrance]` pairs for **one-way connections**

**Important**: Always use `walks.map` rather than `room_data` when working with the final door connections. The `walks.map` structure is updated during the randomization process and reflects the actual connections, including locked exits that may not appear in the standard room_data arrays.

#### 2. **walks.net** - NetworkX Graph
The `walks.net` is a `networkx.DiGraph()` representing room connectivity:
- Nodes are room IDs (strings like `'wob-narshe'` or integers like `355`)
- Edges represent traversable connections between rooms
- Two-way doors create bidirectional edges
- Use `nx.shortest_path(walks.net, source, target)` for pathfinding

#### 3. **walks.rooms** - Room Collection
The `walks.rooms` object (type: `Rooms`) provides efficient element lookups:
- `walks.rooms.rooms`: Dictionary mapping `room_id -> Room` object
- `walks.rooms.get_room_from_element(door_id)`: Returns the Room object that contains a given door/exit
  - This is the **preferred way** to find which room owns a door
  - O(1) lookup using internal `_element_to_room` mapping
  - Works for doors, traps (one-way exits), and pits (one-way entrances)

### Exit/Door Description Data

Two separate data structures provide human-readable door names:

#### **exit_data** (from `data/map_exit_extra.py`)
```python
exit_data = {
    door_id: [doorpair_id, "Description", required_world],
    ...
}
```
- Used for **two-way doors** (regular exits)
- Also includes **1500-series event exits** that function as doors
- Index `[1]` contains the human-readable description

#### **event_exit_info** (from `data/event_exit_info.py`)
```python
event_exit_info = {
    exit_id: [address, bit_length, split_point, transition_state, "Description", location, type],
    ...
}
```
- Used for **one-way exits** (traps, trapdoors, etc.)
- Index `[4]` contains the human-readable description
- Typically IDs are in the 2000+ range

**Lookup Pattern**:
```python
def get_door_name(door_id):
    if door_id in exit_data:
        return exit_data[door_id][1]
    elif door_id in event_exit_info:
        return event_exit_info[door_id][4]
    else:
        return f"Door {door_id}"
```

### Room Naming Conventions

Understanding room ID patterns in `data/rooms.py`:

- **`wob-*`**: World of Balance overworld map rooms (e.g., `'wob-narshe'`, `'wob-figaro'`)
- **`wor-*`**: World of Ruin overworld map rooms (e.g., `'wor-island'`, `'wor-kefkastower'`)
- **`root-*`**: Terminal entrance rooms for dungeons (e.g., `'root-mf'` = Magitek Factory, `'root-u'` = Umaro's cave)
- **`dc-*`**: Dungeon Crawl connector rooms (e.g., `'dc-4'`, `'dc-1501'`)
- **`ms-wob-*` / `ms-wor-*`**: Map Shuffle connector rooms
- **Numeric IDs**: Direct room numbers (e.g., `355`, `488`)

### Room Data Structure

```python
room_data = {
    'room-id': [
        [two_way_doors],      # Index 0
        [one_way_exits],      # Index 1 (traps)
        [one_way_entrances],  # Index 2 (pits)
        world,                # Index 3 (0=WoB, 1=WoR)
        # ... potentially more indices
    ]
}
```

**Warning**: Some exits may be in locked state arrays (e.g., `room_data[roomID][5]`) and won't appear in the standard `[0]`, `[1]`, `[2]` arrays. This is why using `walks.map` and `walks.rooms.get_room_from_element()` is more reliable.

### Door Randomization Flow

The door randomization process in `data/doors.py`:

1. **Initialization** (`__init__`):
   - Parse room sets based on command-line args
   - Build list of rooms to randomize

2. **Network Creation** (`mod()`):
   ```python
   for area_id in self.area_name:
       walks = Network(area)
       walks.ApplyImmediateKeys(self.args)
       walks.ForceConnections(self.forcing)
       walks.attach_dead_ends()
       fully_connected = walks.connect_network()
   ```

3. **Connection Algorithm** (`walks.connect_network()`):
   - Recursively connects rooms by matching exits to entrances
   - Updates `walks.net` graph with edges
   - Builds `walks.map[0]` and `walks.map[1]` with door pairs

4. **Post-processing**:
   - Handles logical links
   - Processes override rules
   - Adds shared exits
   - Matches WoR to WoB if needed

### Implementation Patterns

#### Adding Debug Features

When adding debug output for the door randomizer:

1. **Add command-line args** in `args/doors.py`
2. **Insert debug logic** in `data/doors.py` after `walks.connect_network()` completes
3. **Use the fully_connected network** - it contains the final state with all connections made
4. **Access the data correctly**:
   ```python
   # Good: Use walks.map directly
   for d1, d2 in walks.map[0]:
       r1 = walks.rooms.get_room_from_element(d1)
       r2 = walks.rooms.get_room_from_element(d2)

   # Avoid: Checking room_data arrays
   # (misses locked exits and is more complex)
   ```

#### Working with NetworkX

The `walks.net` NetworkX graph provides powerful pathfinding:

```python
import networkx as nx

# Find shortest path
try:
    path = nx.shortest_path(walks.net, source='wob-narshe', target=355)
    # Returns: ['wob-narshe', 'room-123', 'room-456', 355]
except nx.NetworkXNoPath:
    print("No path exists")

# Check connectivity
if walks.net.has_edge(room1, room2):
    print("Direct connection exists")

# Get all reachable rooms
reachable = nx.descendants(walks.net, 'wob-narshe')
```

### Common Pitfalls

1. **Don't assume room_data contains all doors** - locked exits may be elsewhere
2. **Remember walks.map is built during randomization** - it's empty until `connect_network()` runs
3. **Room IDs can be strings or ints** - handle both types when accepting user input
4. **Two-way doors create bidirectional edges** - check both directions if needed
5. **Event exits (1500s) in exit_data** - they function as doors despite being "events"

### Testing Tips

For door randomization features:
- Use `-drdc` (dungeon crawl) flag to create a large interconnected network
- World map rooms (`wob-*`, `wor-*`) are good starting points for pathfinding
- The `verbose` flag in `Doors` class enables detailed logging
- Check `walks.net.nodes()` and `walks.net.edges()` to inspect the graph state

### Command-Line Interface Principles

When adding new flags:
- **Avoid redundant flags** - if two flags are always used together, combine them
- **Use descriptive names** - `--debug-route-destination` is clearer than `--drd`
- **Provide good help text** - explain what the flag does and which mode it works with
- **Accept flexible input** - allow both room names (`'wob-narshe'`) and IDs (`355`)

## Code Style Notes

### Existing Import Pattern
```python
from data.map_exit_extra import exit_data, doors_WOB_WOR, eventname_to_door
from data.event_exit_info import event_exit_info
from data.walks import *
```

### Function Organization
- Helper functions prefixed with `_` (e.g., `_find_connecting_doors`)
- Main logic functions are public (e.g., `debug_print_shortest_route`)
- Keep related functionality grouped together

---

*Last updated: 2026-01-10*
*For door randomization debug features*
