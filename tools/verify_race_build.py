"""Static verification of race-build relocation + decoys (Phase 1).

Builds a control ROM (no -race) and two race ROMs of the same seed, then
checks, reading the ROMs the way an attacker's tool would:

  1. determinism: the two race builds are byte-identical
  2. control: all reader operands still hold vanilla addresses; the
     obfuscation claim region is untouched
  3. race: every reader site is a JSL to a LDA/EOR/RTL decode shim,
     all shims of a table agree on one table base and one pad base in
     the claim, and the tables are actually masked (the chest pointer
     sentinel decodes to an empty bound)
  4. race: decoding the masked tables with the pads - following the
     code the way an attacker's meta-tool would have to - yields
     structurally correct data whose fixed fields (chest x/y/bit
     layout, shop types) match the control build
  5. race: the decoy tables at the vanilla addresses parse identically
     in structure but differ from the real data in contents (chests,
     shops, espers, enemy steals/drops, coliseum matches)
  6. race with -sli: the limited-inventory hook replaces the C3/B9AF
     reader and the remaining shop operands still relocate

Usage: python3 tools/verify_race_build.py -i <vanilla rom> [-keep]
"""

import argparse
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obfuscation.claim import CLAIM_START, CLAIM_END
from obfuscation.relocate import (CHEST_SITES, SHOP_SITES, ESPER_SITES,
                                  ENEMY_ITEM_SITES, COLISEUM_SITES, VANILLA_BASES)

FLAGS = ("-s racecheckseed -cg -oa 59.3.3.11.29.11.30.11.31.10.12.12"
         " -sc1 random -stl 6 -ccsr 20 -sisr 20 -comfr 100.50.100"
         " -esrt -elrt -ebs -emi -ssd 100 -cosr 50 -crsr 50 -crvr 64 192 -crm").split()

CHEST_PTRS = (0x2d82f4, 0x2d8633)
CHEST_DATA = (0x2d8634, 0x2d8e5a)
SHOP_DATA = (0x47ac0, 0x47f3f)
ESPER_DATA = (0x186e00, 0x186fff)
ENEMY_ITEMS = (0xf3000, 0xf35ff)
COLISEUM = (0x1fb600, 0x1fb9ff)
SHOP_SIZE = 9
CHEST_SIZE = 5
ESPER_SIZE = 11
ESPER_COUNT = 27
ENEMY_ITEM_SIZE = 4
MATCH_SIZE = 4
MAPS = (CHEST_PTRS[1] - CHEST_PTRS[0] + 1) // 2

ALL_SITES = CHEST_SITES + SHOP_SITES + ESPER_SITES + ENEMY_ITEM_SITES + COLISEUM_SITES

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
    for offset, vanilla, _ in ALL_SITES:
        check(operand(control, offset) == vanilla,
              f"control: operand at 0x{offset:06x} is not vanilla")
    check(all(b == 0xff for b in control[CLAIM_START:CLAIM_END + 1]),
          "control: obfuscation claim region is not empty")

    # 3. race: every reader site is a JSL to a LDA/EOR/RTL decode shim;
    #    all shims of a table agree on one table base and one pad base,
    #    both inside the claim.  this follows the code exactly the way
    #    an attacker's meta-tool would have to
    bases = {}
    pads = {}
    for offset, vanilla, table in ALL_SITES:
        delta = vanilla - VANILLA_BASES[table]
        instr = offset - 1
        check(race[instr] == 0x22, f"race: reader at 0x{instr:06x} is not a JSL")
        shim = rom_offset(operand(race, offset))
        check(race[shim] == 0xbf and race[shim + 4] == 0x5f and race[shim + 8] == 0x6b,
              f"race: shim at 0x{shim:06x} is not LDA/EOR/RTL")
        bases.setdefault(table, set()).add(operand(race, shim + 1) - delta)
        pads.setdefault(table, set()).add(operand(race, shim + 5) - delta)
    for table in sorted(bases):
        check(len(bases[table]) == 1, f"race: {table} shim table bases disagree")
        check(len(pads[table]) == 1, f"race: {table} shim pad bases disagree")
        table_base = rom_offset(bases[table].pop())
        pad_base = rom_offset(pads[table].pop())
        for what, at in (("table", table_base), ("pad", pad_base)):
            check(CLAIM_START <= at <= CLAIM_END,
                  f"race: {table} {what} outside the claim: 0x{at:06x}")
        bases[table] = table_base
        pads[table] = pad_base

    # decode the masked tables the way the shims do, and splice the
    # plaintext over the vanilla offsets so the walkers below can run
    # unchanged.  (the decoys stay where they are, in `race` itself.)
    from obfuscation.claim import sizeof
    SPLICE = {"chest_ptrs": CHEST_PTRS[0], "chest_data": CHEST_DATA[0],
              "shop_data": SHOP_DATA[0], "esper_data": ESPER_DATA[0],
              "enemy_items": ENEMY_ITEMS[0], "coliseum": COLISEUM[0]}
    real_view = bytearray(race)
    for table, start in SPLICE.items():
        size = sizeof(table)
        b, p = bases[table], pads[table]
        plain = bytes(x ^ y for x, y in zip(race[b:b + size], race[p:p + size]))
        check(bytes(race[b:b + size]) != plain,
              f"race: {table} is stored unmasked")
        if table == "chest_ptrs":
            # the 2-byte sentinel entry past the vanilla-size table must
            # decode to the final map's start bound (= no chests)
            check(plain[0x340:0x342] == plain[0x33e:0x340],
                  "race: chest pointer sentinel is not an empty bound")
            plain = plain[:0x340]
        real_view[start:start + len(plain)] = plain

    # 4. decoded real data, fixed fields vs control
    control_chests = read_chest_tables(control, CHEST_PTRS[0], CHEST_DATA[0])
    real_chests = read_chest_tables(real_view, CHEST_PTRS[0], CHEST_DATA[0])
    check(len(control_chests) == len(real_chests), "map count differs")
    fixed = lambda maps: [[record[:3] for record in records] for records in maps]
    check(fixed(control_chests) == fixed(real_chests),
          "race: relocated chest x/y/bit layout differs from control")

    control_shops = read_shop_table(control, SHOP_DATA[0])
    real_shops = read_shop_table(real_view, SHOP_DATA[0])
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

    # 5b. espers: real via operands and decoy at vanilla both hold valid
    #     spell ids; contents differ
    def esper_records(rom, base):
        return [rom[base + i * ESPER_SIZE:base + (i + 1) * ESPER_SIZE]
                for i in range(ESPER_COUNT)]

    real_espers = esper_records(real_view, ESPER_DATA[0])
    decoy_espers = esper_records(race, ESPER_DATA[0])
    for name, records in (("real", real_espers), ("decoy", decoy_espers)):
        for record in records:
            check(all(record[i] == 0xff or record[i] < 54 for i in (1, 3, 5, 7, 9)),
                  f"race: {name} esper record holds an invalid spell id: {record.hex()}")
    differing = sum(1 for a, b in zip(real_espers, decoy_espers) if a != b)
    check(differing > ESPER_COUNT // 4,
          f"race: esper decoy too similar to real data ({differing} differ)")

    # 5c. enemy steal/drop table: decoy differs from real
    def loot_records(rom, base):
        count = (ENEMY_ITEMS[1] - ENEMY_ITEMS[0] + 1) // ENEMY_ITEM_SIZE
        return [rom[base + i * ENEMY_ITEM_SIZE:base + (i + 1) * ENEMY_ITEM_SIZE]
                for i in range(count)]

    real_loot = loot_records(real_view, ENEMY_ITEMS[0])
    decoy_loot = loot_records(race, ENEMY_ITEMS[0])
    differing = sum(1 for a, b in zip(real_loot, decoy_loot) if a != b)
    check(differing > len(real_loot) // 4,
          f"race: enemy loot decoy too similar to real data ({differing} differ)")

    # 5d. coliseum: decoy differs from real
    def match_records(rom, base):
        count = (COLISEUM[1] - COLISEUM[0] + 1) // MATCH_SIZE
        return [rom[base + i * MATCH_SIZE:base + (i + 1) * MATCH_SIZE]
                for i in range(count)]

    real_matches = match_records(real_view, COLISEUM[0])
    decoy_matches = match_records(race, COLISEUM[0])
    differing = sum(1 for a, b in zip(real_matches, decoy_matches) if a != b)
    check(differing > len(real_matches) // 4,
          f"race: coliseum decoy too similar to real data ({differing} differ)")

    # 6. limited inventory (-sli) rewrites the C3/B9AF item load itself
    #    (menus/buy.py hook_load_item), so the race build must patch the
    #    remaining vanilla shop readers and leave that site to the hook
    sli = build(args.rom, f"{tmp}/sli.smc", race=True, extra=["-sli"])
    check(sli[0x3b9af] == 0x22,
          "sli race: C3/B9AF is not the limited-inventory JSL hook")
    for offset, vanilla, table in SHOP_SITES:
        if offset == 0x3b9b0:
            continue
        check(sli[offset - 1] == 0x22,
              f"sli race: reader at 0x{offset - 1:06x} is not a JSL")
        shim = rom_offset(operand(sli, offset))
        check(sli[shim] == 0xbf and sli[shim + 4] == 0x5f and sli[shim + 8] == 0x6b,
              f"sli race: shim at 0x{shim:06x} is not LDA/EOR/RTL")

    # 7. L3 check-reward indirection.  Items and espers deliberately share
    #    one command, one masked table and one control code, so nothing
    #    static distinguishes an esper check from an item check.
    FIELD_OPCODE_TABLE = 0x098c4
    def field_handler(rom, opcode):
        off = FIELD_OPCODE_TABLE + (opcode - 0x35) * 2
        return int.from_bytes(rom[off:off + 2], "little")

    # (kept in sync with instruction/field/custom.py by the checks below;
    # that module cannot be imported here - importing instruction.field runs
    # build-time rom writes that need an initialised Memory)
    ADD_CHECK_REWARD_OPCODE, REWARD_DIALOG_OPCODE = 0x9e, 0xee
    stub = field_handler(control, 0xed)          # an opcode nothing claims
    for opcode in (ADD_CHECK_REWARD_OPCODE, REWARD_DIALOG_OPCODE):
        check(field_handler(control, opcode) == stub,
              f"control: opcode {hex(opcode)} is not the unused stub "
              f"(is another feature already using it?)")
        check(field_handler(race, opcode) != stub,
              f"race: opcode {hex(opcode)} was not installed")
    # exactly one grant command: a second one would separate the kinds
    for opcode in (0x9f, 0xe6, 0x66, 0x67, 0x68):
        check(field_handler(race, opcode) == stub,
              f"race: opcode {hex(opcode)} is installed - a per-kind command "
              f"would reveal which checks hold espers")

    handler = field_handler(race, ADD_CHECK_REWARD_OPCODE)
    hb = race[handler:handler + 0x40]
    i = hb.index(0xbf)
    check(hb[i] == 0xbf and hb[i + 4] == 0x5f,
          "race: the reward handler is not LDA long,X / EOR long,X")
    tbase = rom_offset(int.from_bytes(hb[i + 1:i + 4], "little"))
    pbase = rom_offset(int.from_bytes(hb[i + 5:i + 8], "little"))
    for what, at in (("table", tbase), ("pad", pbase)):
        check(CLAIM_START <= at <= CLAIM_END,
              f"race: reward {what} outside the claim: 0x{at:06x}")
    rewards = bytes(race[tbase + k] ^ race[pbase + k] for k in range(0x200))
    check(bytes(race[tbase:tbase + 0x200]) != rewards, "race: reward table is not masked")

    items = espers = 0
    for slot in range(0x100):
        kind, value = rewards[slot * 2], rewards[slot * 2 + 1]
        if kind == 0xff:
            continue
        check(kind in (0x00, 0x01), f"race: reward slot {slot} has an invalid kind")
        if kind == 0x01:
            check(value < 27, f"race: reward slot {slot} has an invalid esper id")
            espers += 1
        else:
            items += 1
    check(items > 0 and espers > 0,
          "race: the reward table should hold both items and espers")

    # 10. the auction house presents every reward in a chest in race
    #     builds.  WC otherwise makes that swap only for item rewards, so
    #     its presence or absence - a plain diff against vanilla - would
    #     say whether the auction holds an esper or an item
    AUCTION_CHEST_SITES = (0xb532c, 0xb5a51, 0xb51b1, 0xb5914)
    for offset in AUCTION_CHEST_SITES:
        check(race[offset] == 0xb2,
              f"race: auction chest swap missing at 0x{offset:05x} - the "
              f"reward kind would be visible by diffing against vanilla")
    # and the announcements go through the reward dialog command
    for offset in (0xb5339, 0xb5a5e, 0xb51be, 0xb5921):
        check(control[offset] == 0x4b,
              f"control: auction announce at 0x{offset:05x} is not a Dialog")
        check(race[offset] == REWARD_DIALOG_OPCODE,
              f"race: auction announce at 0x{offset:05x} still names its reward")

    print(f"all {checks} checks passed")
    print(f"reward table: {items} item + {espers} esper slots in one masked table")
    print("relocated bases:", {t: hex(b) for t, b in bases.items()})
    print("pad bases:", {t: hex(p) for t, p in pads.items()})
    print(f"chest records: {len(real_flat)}, chest contents differing from decoy: "
          f"{sum(1 for a, b in zip(real_flat, decoy_flat) if a[3:] != b[3:])}")
    if args.keep:
        print("kept roms in", tmp)
    else:
        import shutil
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
