#!/usr/bin/env python3
"""
Export map data (events, NPCs, exits) to JSON format for analysis.
Run this script after the ROM is loaded to export the original data.
"""

import json
import sys
import args

def export_map_data():
    """Export map events, NPCs, and exits to JSON files."""

    print("Loading ROM and data...")
    from memory.memory import Memory
    memory = Memory()

    from data.data import Data
    data = Data(memory.rom, args)

    print(f"Loaded {len(data.maps.maps)} maps")
    print(f"Total NPCs: {len(data.maps.npcs.npcs)}")
    print(f"Total Events: {len(data.maps.events.events)}")
    print(f"Total Short Exits: {len(data.maps.exits.short_exits)}")
    print(f"Total Long Exits: {len(data.maps.exits.long_exits)}")
    print(f"Total Chests: {len(data.maps.chests.all_chests)}")

    # Export all data grouped by map
    print("\nExporting map data...")
    export_maps_with_data(data.maps)

    # Export raw data tables for reference
    print("Exporting raw NPC data...")
    export_npcs(data.maps.npcs)

    print("Exporting raw event data...")
    export_events(data.maps.events)

    print("Exporting raw exit data...")
    export_exits(data.maps.exits)

    print("Exporting raw chest data...")
    export_chests(data.maps.chests)

    print("\nExport complete!")
    print("Files created:")
    print("  - maps_data.json (all maps with their properties, chests, events, NPCs, exits)")
    print("  - npcs_raw.json (all NPCs indexed)")
    print("  - events_raw.json (all events indexed)")
    print("  - exits_raw.json (all exits indexed)")
    print("  - chests_raw.json (all chests indexed)")

def export_maps_with_data(maps):
    """Export all maps with their associated events, NPCs, exits, properties, and chests."""
    maps_data = []

    for map_id in range(maps.MAP_COUNT):
        map_info = maps.maps[map_id]
        map_property = maps.properties[map_id]

        # Get map properties
        properties = {
            "name_index": map_property.name_index,
            "song": map_property.song,
            "enable_random_encounters": bool(map_property.enable_random_encounters),
            "raw_data": [hex(b) for b in map_property.data],  # All 33 bytes
        }

        # Get chests for this map
        chests_list = []
        for chest in maps.chests.map_chests[map_id]:
            chests_list.append({
                "id": chest.id,
                "x": chest.x,
                "y": chest.y,
                "bit": chest.bit,
                "type": chest.get_type_string(),
                "type_raw": hex(chest.type),
                "contents": chest.contents,
            })

        # Get NPCs for this map
        npcs_list = []
        npc_count = maps.get_npc_count(map_id)
        if npc_count > 0:
            first_npc_index = (map_info["npcs_ptr"] - maps.maps[0]["npcs_ptr"]) // 9
            for i in range(npc_count):
                npc = maps.npcs.npcs[first_npc_index + i]
                npcs_list.append({
                    "index": first_npc_index + i,
                    "npc_id": 0x10 + i,  # NPC IDs start at 0x10
                    "x": npc.x,
                    "y": npc.y,
                    "direction": npc.direction,
                    "no_face_on_trigger": npc.no_face_on_trigger,
                    "speed": npc.speed,
                    "movement": npc.movement,
                    "sprite": npc.sprite,
                    "split_sprite": npc.split_sprite,
                    "const_sprite": npc.const_sprite,
                    "palette": npc.palette,
                    "vehicle": npc.vehicle,
                    "event_byte": npc.event_byte,
                    "event_bit": npc.event_bit,
                    "event_address": hex(npc.event_address),
                    "map_layer": npc.map_layer,
                    "background_scrolls": npc.background_scrolls,
                    "background_layer": npc.background_layer,
                })

        # Get events for this map
        events_list = []
        event_count = maps.get_event_count(map_id)
        if event_count > 0:
            first_event_id = (map_info["events_ptr"] - maps.maps[0]["events_ptr"]) // 5
            for i in range(event_count):
                event = maps.events.events[first_event_id + i]
                events_list.append({
                    "index": first_event_id + i,
                    "x": event.x,
                    "y": event.y,
                    "event_address": hex(event.event_address),
                })

        # Get short exits for this map
        short_exits_list = []
        short_exit_count = maps.get_short_exit_count(map_id)
        if short_exit_count > 0:
            first_exit_id = (map_info["short_exits_ptr"] - maps.maps[0]["short_exits_ptr"]) // 6
            for i in range(short_exit_count):
                exit = maps.exits.short_exits[first_exit_id + i]
                short_exits_list.append({
                    "index": first_exit_id + i,
                    "x": exit.x,
                    "y": exit.y,
                    "dest_map": exit.dest_map,
                    "dest_x": exit.dest_x,
                    "dest_y": exit.dest_y,
                    "unknown": hex(exit.unknown),
                })

        # Get long exits for this map
        long_exits_list = []
        long_exit_count = maps.get_long_exit_count(map_id)
        if long_exit_count > 0:
            first_exit_id = (map_info["long_exits_ptr"] - maps.maps[0]["long_exits_ptr"]) // 7
            for i in range(long_exit_count):
                exit = maps.exits.long_exits[first_exit_id + i]
                long_exits_list.append({
                    "index": first_exit_id + i,
                    "x": exit.x,
                    "y": exit.y,
                    "size": exit.size,
                    "direction": "horizontal" if exit.direction == 0 else "vertical",
                    "direction_raw": exit.direction,
                    "dest_map": exit.dest_map,
                    "dest_x": exit.dest_x,
                    "dest_y": exit.dest_y,
                    "unknown": hex(exit.unknown),
                })

        maps_data.append({
            "map_id": map_id,
            "name_index": map_info["name_index"],
            "entrance_event_address": hex(map_info["entrance_event_address"]),
            "properties": properties,
            "pointers": {
                "events_ptr": hex(map_info["events_ptr"]),
                "npcs_ptr": hex(map_info["npcs_ptr"]),
                "short_exits_ptr": hex(map_info["short_exits_ptr"]),
                "long_exits_ptr": hex(map_info["long_exits_ptr"]),
            },
            "chests": chests_list,
            "npcs": npcs_list,
            "events": events_list,
            "short_exits": short_exits_list,
            "long_exits": long_exits_list,
        })

    with open("maps_data.json", "w") as f:
        json.dump(maps_data, f, indent=2)

    print(f"Exported {len(maps_data)} maps to maps_data.json")

def export_npcs(npcs):
    """Export all NPCs as a raw indexed list."""
    npcs_data = []

    for index, npc in enumerate(npcs.npcs):
        npcs_data.append({
            "index": index,
            "x": npc.x,
            "y": npc.y,
            "direction": npc.direction,
            "no_face_on_trigger": npc.no_face_on_trigger,
            "speed": npc.speed,
            "movement": npc.movement,
            "sprite": npc.sprite,
            "split_sprite": npc.split_sprite,
            "const_sprite": npc.const_sprite,
            "palette": npc.palette,
            "vehicle": npc.vehicle,
            "event_byte": npc.event_byte,
            "event_bit": npc.event_bit,
            "event_address": hex(npc.event_address),
            "map_layer": npc.map_layer,
            "background_scrolls": npc.background_scrolls,
            "background_layer": npc.background_layer,
        })

    with open("npcs_raw.json", "w") as f:
        json.dump(npcs_data, f, indent=2)

    print(f"Exported {len(npcs_data)} NPCs to npcs_raw.json")

def export_events(events):
    """Export all map events as a raw indexed list."""
    events_data = []

    for index, event in enumerate(events.events):
        events_data.append({
            "index": index,
            "x": event.x,
            "y": event.y,
            "event_address": hex(event.event_address),
        })

    with open("events_raw.json", "w") as f:
        json.dump(events_data, f, indent=2)

    print(f"Exported {len(events_data)} events to events_raw.json")

def export_exits(exits):
    """Export all map exits (short and long) as raw indexed lists."""
    exits_data = {
        "short_exits": [],
        "long_exits": []
    }

    for index, exit in enumerate(exits.short_exits):
        exits_data["short_exits"].append({
            "index": index,
            "x": exit.x,
            "y": exit.y,
            "dest_map": exit.dest_map,
            "dest_x": exit.dest_x,
            "dest_y": exit.dest_y,
            "unknown": hex(exit.unknown),
        })

    for index, exit in enumerate(exits.long_exits):
        exits_data["long_exits"].append({
            "index": index,
            "x": exit.x,
            "y": exit.y,
            "size": exit.size,
            "direction": "horizontal" if exit.direction == 0 else "vertical",
            "direction_raw": exit.direction,
            "dest_map": exit.dest_map,
            "dest_x": exit.dest_x,
            "dest_y": exit.dest_y,
            "unknown": hex(exit.unknown),
        })

    with open("exits_raw.json", "w") as f:
        json.dump(exits_data, f, indent=2)

    print(f"Exported {len(exits_data['short_exits'])} short exits and {len(exits_data['long_exits'])} long exits to exits_raw.json")

def export_chests(chests):
    """Export all chests as a raw indexed list."""
    chests_data = []

    for chest in chests.all_chests:
        chests_data.append({
            "id": chest.id,
            "x": chest.x,
            "y": chest.y,
            "bit": chest.bit,
            "type": chest.get_type_string(),
            "type_raw": hex(chest.type),
            "contents": chest.contents,
        })

    with open("chests_raw.json", "w") as f:
        json.dump(chests_data, f, indent=2)

    print(f"Exported {len(chests_data)} chests to chests_raw.json")

if __name__ == "__main__":
    try:
        export_map_data()
    except Exception as e:
        print(f"Error during export: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
