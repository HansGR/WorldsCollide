# Debug Shortest Route Feature

This feature allows you to output the shortest route from any world map room to a specified destination room when using door randomization in dungeon crawl mode.

## Usage

To use this feature, you need to:

1. Enable door randomization in dungeon crawl mode with `-drdc`
2. Enable the debug output with `--debug-shortest-route`
3. Specify the destination room with `--debug-route-destination <room_name_or_number>`

Example:
```bash
python3 wc.py -i ffiii.smc -drdc --debug-shortest-route --debug-route-destination "355"
```

Or with a room name:
```bash
python3 wc.py -i ffiii.smc -drdc --debug-shortest-route --debug-route-destination "root-mf"
```

## Output Format

The debug output will show:
- The starting world map room (closest to the destination)
- The path length (number of rooms)
- Each step of the route with door connections:
  - `<-->` indicates a two-way door connection
  - `-->` indicates a one-way connection

Example output:
```
================================================================================
DEBUG: SHORTEST ROUTE FROM WORLD MAP TO '355'
================================================================================
Starting from world map room: wob-empire
Path length: 5 rooms

wob-empire: DOOR 31 (Maranda Top Tile WoB) <--> DOOR 1238 (Some Location)
room-123: DOOR 456 (Location Name) --> DOOR 789 (Another Location)
room-234: DOOR 890 (Third Location) <--> DOOR 345 (Fourth Location)
room-345: DOOR 678 (Fifth Location) --> DOOR 901 (Sixth Location)
355: (destination)
================================================================================
```

## Finding Room Names/Numbers

Room names and numbers are defined in `data/rooms.py` in the `room_data` dictionary. World map rooms are named:
- `wob-*` for World of Balance map rooms (e.g., `wob-narshe`, `wob-figaro`)
- `wor-*` for World of Ruin map rooms (e.g., `wor-island`, `wor-kefkastower`)

You can also use numeric room IDs (e.g., `355`, `488`) or special room names (e.g., `root-mf` for Magitek Factory root).

## Notes

- This feature only works with door randomization modes, particularly `-drdc` (dungeon crawl)
- The destination room must be in the randomized network for the route to be found
- If no path exists from any world map room to the destination, an error message will be displayed
