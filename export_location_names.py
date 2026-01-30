#!/usr/bin/env python3
"""
Export FF6 location names from the ROM to JSON format.

Location names are stored at ROM address 0x2EF100.
There are 73 names, each 10 bytes long, using the text2 encoding table.
The name_index in maps_data.json corresponds to the index in this table.

Run: python3 export_location_names.py -i ffiii.smc
Output: location_names.json
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data.text as text

# ROM constants for location names
LOCATION_NAMES_START = 0x2EF100
LOCATION_NAME_SIZE = 10
LOCATION_NAME_COUNT = 73


def decode_name(data):
    """Decode a location name from ROM bytes using text2 encoding."""
    # Use the codebase's text decoding, same as spell names
    name = text.get_string(data, text.TEXT2)
    # Strip null terminators and clean up
    name = name.rstrip('\0')
    # Remove any special tags that might appear
    first_pos = name.find('<')
    while first_pos >= 0:
        second_pos = name.find('>')
        if second_pos >= 0:
            name = name.replace(name[first_pos:second_pos + 1], "")
        else:
            break
        first_pos = name.find('<')
    return name.strip()


def export_location_names(rom_path):
    """Read location names from ROM and export to JSON."""

    print(f"Reading ROM: {rom_path}")

    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Check for header (512 bytes) - if ROM size % 0x8000 == 512, it has a header
    if len(rom_data) % 0x8000 == 512:
        print("ROM has 512-byte header, adjusting offset...")
        offset = 512
    else:
        offset = 0

    location_names = []

    print(f"\nReading {LOCATION_NAME_COUNT} location names from 0x{LOCATION_NAMES_START:X}...")

    for i in range(LOCATION_NAME_COUNT):
        addr = LOCATION_NAMES_START + (i * LOCATION_NAME_SIZE) + offset
        name_bytes = list(rom_data[addr:addr + LOCATION_NAME_SIZE])
        name = decode_name(name_bytes)

        location_names.append({
            "name_index": i,
            "name": name,
            "rom_address": f"0x{LOCATION_NAMES_START + (i * LOCATION_NAME_SIZE):X}",
            "raw_bytes": [f"0x{b:02x}" for b in name_bytes]
        })

        print(f"  {i:3d}: {name}")

    # Write to JSON
    output_file = "location_names.json"
    with open(output_file, 'w') as f:
        json.dump(location_names, f, indent=2)

    print(f"\nExported {len(location_names)} location names to {output_file}")

    # Also create a simple lookup dictionary version
    simple_lookup = {entry["name_index"]: entry["name"] for entry in location_names}
    simple_file = "location_names_lookup.json"
    with open(simple_file, 'w') as f:
        json.dump(simple_lookup, f, indent=2)

    print(f"Created simple lookup file: {simple_file}")


if __name__ == "__main__":
    import args

    if not args.input_file:
        print("Error: Please provide input ROM file with -i flag")
        print("Usage: python3 export_location_names.py -i ffiii.smc")
        sys.exit(1)

    try:
        export_location_names(args.input_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
