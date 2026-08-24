"""Static verification of race-build relocation + decoys (Phase 1).

Builds a control ROM (no -race) and two race ROMs of the same seed, then
checks, reading the ROMs the way an attacker's tool would:

  1. determinism: the two race builds are byte-identical
  2. control: all reader operands still hold vanilla addresses; the
     obfuscation claim region is untouched
  3. race: every reader operand points into the claim, and all operands
     of a table agree on one relocated base
  4. race: walking the relocated chest/shop tables via the patched
     operands yields structurally correct data whose fixed fields
     (chest x/y/bit layout, shop types) match the control build
  5. race: the decoy tables at the vanilla addresses parse identically
     in structure but differ from the real data in contents

Usage: python3 tools/verify_race_build.py -i <vanilla rom> [-keep]
"""

import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obfuscation.claim import CLAIM_START, CLAIM_END
from obfuscation.relocate import CHEST_SITES, SHOP_SITES, VANILLA_BASES

FLAGS = ("-s racecheckseed -cg -oa 59.3.3.11.29.11.30.11.31.10.12.12"
         " -sc1 random -stl 6 -ccsr 20 -sisr 20 -comfr 100.50.100").split()

CHEST_PTRS = (0x2d82f4, 0x2d8633)
CHEST_DATA = (0x2d8634, 0x2d8e5a)
SHOP_DATA = (0x47ac0, 0x47f3f)
SHOP_SIZE = 9
CHEST_SIZE = 5
MAPS = (CHEST_PTRS[1] - CHEST_PTRS[0] + 1) // 2

checks = 0

def check(condition, message):
    global checks
    assert condition, message
    checks += 1


def build(rom_in, rom_out, race, extra=None):
    args = [sys.executable, "wc.py", "-i", rom_in, "-o", rom_out] + FLAGS
    if race:
        args.append("-race")
    if extra:
        args.extend(extra)
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(rom_out):
        raise SystemExit(f"build failed:\n{result.stdout}\n{result.stderr}")
    return open(rom_out, "rb").read()


def operand(rom, offset):
    return int.from_bytes(rom[offset:offset + 3], "little")


def rom_offset(snes_address):
    return snes_address - 0xc00000


def read_chest_tables(rom, ptrs_base, data_base):
    """Walk the chest tables exactly as C0/15D7 does: per-map [start, end)
    offsets from the pointer table, 5-byte records off the data base."""
    maps = []
    for map_index in range(MAPS):
        start = int.from_bytes(rom[ptrs_base + 2 * map_index:][:2], "little")
        if map_index + 1 < MAPS:
            end = int.from_bytes(rom[ptrs_base + 2 * (map_index + 1):][:2], "little")
        else:
            # the final map has no next pointer to bound it (the engine
            # would read past the table); it has no chests - treat as empty
            end = start
        check(start <= end, f"map {map_index}: pointers not monotonic")
        records = []
        for off in range(start, end, CHEST_SIZE):
            records.append(tuple(rom[data_base + off:data_base + off + CHEST_SIZE]))
        maps.append(records)
    return maps


def read_shop_table(rom, base):
    count = (SHOP_DATA[1] - SHOP_DATA[0] + 1) // SHOP_SIZE
    return [tuple(rom[base + i * SHOP_SIZE:base + (i + 1) * SHOP_SIZE])
            for i in range(count)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", dest="rom", required=True)
    parser.add_argument("-keep", action="store_true", help="keep built roms")
    args = parser.parse_args()

    tmp = tempfile.mkdtemp(prefix="race_verify_")
    control = build(args.rom, f"{tmp}/control.smc", race=False)
    race1 = build(args.rom, f"{tmp}/race1.smc", race=True)
    race2 = build(args.rom, f"{tmp}/race2.smc", race=True)

    # 1. determinism
    check(race1 == race2, "race builds of the same seed are not byte-identical")
    race = race1

    # 2. control build untouched
    for offset, vanilla, _ in CHEST_SITES + SHOP_SITES:
        check(operand(control, offset) == vanilla,
              f"control: operand at 0x{offset:06x} is not vanilla")
    check(all(b == 0xff for b in control[CLAIM_START:CLAIM_END + 1]),
          "control: obfuscation claim region is not empty")

    # 3. race operands agree on relocated bases inside the claim
    bases = {}
    for offset, vanilla, table in CHEST_SITES + SHOP_SITES:
        delta = vanilla - VANILLA_BASES[table]
        base = operand(race, offset) - delta
        bases.setdefault(table, set()).add(base)
    for table, found in bases.items():
        check(len(found) == 1, f"race: {table} operands disagree: {found}")
        base = rom_offset(found.pop())
        check(CLAIM_START <= base <= CLAIM_END,
              f"race: {table} relocated outside the claim: 0x{base:06x}")
        bases[table] = base

    # 4. real data via the patched operands, fixed fields vs control
    control_chests = read_chest_tables(control, CHEST_PTRS[0], CHEST_DATA[0])
    real_chests = read_chest_tables(race, bases["chest_ptrs"], bases["chest_data"])
    check(len(control_chests) == len(real_chests), "map count differs")
    fixed = lambda maps: [[record[:3] for record in records] for records in maps]
    check(fixed(control_chests) == fixed(real_chests),
          "race: relocated chest x/y/bit layout differs from control")

    control_shops = read_shop_table(control, SHOP_DATA[0])
    real_shops = read_shop_table(race, bases["shop_data"])
    check([shop[0] for shop in control_shops] == [shop[0] for shop in real_shops],
          "race: relocated shop types differ from control")

    # 5. decoys at the vanilla addresses: same structure, different contents
    decoy_chests = read_chest_tables(race, CHEST_PTRS[0], CHEST_DATA[0])
    check(fixed(decoy_chests) == fixed(real_chests),
          "race: decoy chest x/y/bit layout differs")
    real_flat = [record for records in real_chests for record in records]
    decoy_flat = [record for records in decoy_chests for record in records]
    differing = sum(1 for a, b in zip(real_flat, decoy_flat) if a[3:] != b[3:])
    check(differing > len(real_flat) // 10,
          f"race: chest decoy too similar to real data ({differing} differ)")

    decoy_shops = read_shop_table(race, SHOP_DATA[0])
    check([shop[0] for shop in decoy_shops] == [shop[0] for shop in real_shops],
          "race: decoy shop types differ")
    differing = sum(1 for a, b in zip(real_shops, decoy_shops) if a[1:] != b[1:])
    check(differing > len(real_shops) // 4,
          f"race: shop decoy too similar to real data ({differing} differ)")

    # 6. limited inventory (-sli) rewrites the C3/B9AF item load itself
    #    (menus/buy.py hook_load_item), so the race build must patch the
    #    remaining vanilla shop readers and leave that site to the hook
    sli = build(args.rom, f"{tmp}/sli.smc", race=True, extra=["-sli"])
    check(sli[0x3b9af] == 0x22,
          "sli race: C3/B9AF is not the limited-inventory JSL hook")
    for offset, vanilla, table in SHOP_SITES:
        if offset == 0x3b9b0:
            continue
        base = rom_offset(operand(sli, offset) - (vanilla - VANILLA_BASES[table]))
        check(CLAIM_START <= base <= CLAIM_END,
              f"sli race: shop operand at 0x{offset:06x} not relocated")

    print(f"all {checks} checks passed")
    print("relocated bases:", {t: hex(b) for t, b in bases.items()})
    print(f"chest records: {len(real_flat)}, chest contents differing from decoy: "
          f"{sum(1 for a, b in zip(real_flat, decoy_flat) if a[3:] != b[3:])}")
    if args.keep:
        print("kept roms in", tmp)
    else:
        import shutil
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
