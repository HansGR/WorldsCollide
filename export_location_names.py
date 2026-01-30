#!/usr/bin/env python3
"""
Export FF6 location names from the ROM to JSON format.

Location name pointers are at ROM address 0x268400 (SNES $E68400).
Location name strings are at ROM address 0x2EF100 (SNES $CEF100).
Names use TXT1 encoding (DTE compressed) and are variable length.
The name_index in maps_data.json corresponds to the index in the pointer table.

Run: python3 export_location_names.py -i ffiii.smc
Output: location_names.json
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data.text as text

# ROM constants for location names (from ff3infov2.txt)
# Pointers at $E68400-$E6877F, names at $CEF100-$CEF5FF
# SNES to ROM conversion: subtract $C00000
LOCATION_NAME_PTRS_START = 0x268400  # SNES $E68400 -> ROM $268400
LOCATION_NAMES_BASE = 0x0EF100       # SNES $CEF100 -> ROM $0EF100
LOCATION_NAME_COUNT = 73


def read_pointer(rom_data, offset, ptr_offset):
    """Read a 2-byte little-endian pointer and add base offset."""
    addr = ptr_offset + (rom_data[offset] | (rom_data[offset + 1] << 8))
    return addr


def read_name_string(rom_data, start_addr, max_len=32):
    """Read bytes until we hit a terminator (0x00) or max length."""
    name_bytes = []
    for i in range(max_len):
        byte = rom_data[start_addr + i]
        if byte == 0x00:  # End marker in TXT1
            break
        name_bytes.append(byte)
    return name_bytes


def export_location_names(rom_path):
    """Read location names from ROM and export to JSON."""

    print(f"Reading ROM: {rom_path}")

    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    # Check for header (512 bytes) - if ROM size % 0x8000 == 512, it has a header
    if len(rom_data) % 0x8000 == 512:
        print("ROM has 512-byte header, adjusting offset...")
        header_offset = 512
    else:
        header_offset = 0

    location_names = []

    print(f"\nReading {LOCATION_NAME_COUNT} location names...")
    print(f"Pointer table at 0x{LOCATION_NAME_PTRS_START:X}")
    print(f"Name strings base at 0x{LOCATION_NAMES_BASE:X}")

    for i in range(LOCATION_NAME_COUNT):
        # Read the 2-byte pointer for this name
        ptr_addr = LOCATION_NAME_PTRS_START + (i * 2) + header_offset
        # Pointers are relative to $CEF100, stored as offset from that base
        ptr_value = rom_data[ptr_addr] | (rom_data[ptr_addr + 1] << 8)

        # The actual string address
        name_addr = LOCATION_NAMES_BASE + ptr_value + header_offset

        # Read the variable-length name string
        name_bytes = read_name_string(rom_data, name_addr)

        # Decode using TEXT1 (DTE encoding)
        name = text.get_string(name_bytes, text.TEXT1)
        # Clean up the name
        name = name.rstrip('\0')
        # Remove any special tags
        first_pos = name.find('<')
        while first_pos >= 0:
            second_pos = name.find('>')
            if second_pos >= 0:
                name = name.replace(name[first_pos:second_pos + 1], "")
            else:
                break
            first_pos = name.find('<')
        name = name.strip()

        location_names.append({
            "name_index": i,
            "name": name,
            "pointer_address": f"0x{LOCATION_NAME_PTRS_START + (i * 2):X}",
            "string_address": f"0x{LOCATION_NAMES_BASE + ptr_value:X}",
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
