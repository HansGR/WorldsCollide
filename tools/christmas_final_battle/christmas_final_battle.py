#!/usr/bin/env python3
"""A Christmas final battle for a rolled Worlds Collide rom.

usage: python3 christmas_final_battle.py IN.smc OUT.smc [christmas_data.json]

The three tiers of the Statue of the Gods become three stories of a christmas tree with reindeer,
and final Kefka becomes Santa in his sleigh on top of it. Only looks change: every enemy keeps its
stats and its script, and the enemies of the tiers are where the reindeer are.

It runs on a rom that Worlds Collide has made (4 MB, with the default final boss: not with -fb),
needs nothing but python, and changes nothing if anything is not as it expects.

What it writes:
  - tiers 1 to 3 are battle backgrounds 0x33 to 0x35:
    2 sets of 128 tiles, a tilemap and 2 palettes of 16 colors each (what the scroll from one tier
    to the next has room for), and tier 4's (0x36) as well.
    The sets and tilemaps go to a bank of the rom that is empty, and the tilemaps, which the game
    takes from bank E7 only, get a pointer table of their own there with the code to read it
  - Santa is final Kefka's sprite: its tiles (he has room for 149), its mold and its palette, and
    his name
  - the enemies of the tiers get a sprite that is not seen (they all have the same beast's)
  - the positions of the enemies in the three tiers' formations, and Santa's
christmas_data.json has all of them, made from the picture by build_data.py.
"""
import json, os, sys

PROPERTIES, PROPERTY_SIZE = 0x270000, 6     # a battle background: 3 tile sets, 2 tilemaps, palette
SET_POINTERS = 0x271650                     # 3 bytes each. the index is taken times 3 in a byte: 0x55 is the last
PALETTES, PALETTE_SIZE = 0x270150, 0x60
NEW_SETS = {0x33: 0x4b, 0x34: 0x4c, 0x35: 0x4d, 0x36: 0x4e}     # a third set, for a background that has one: indices the game does not use
NEW_MAPS = {0x33: 0x40, 0x34: 0x41, 0x35: 0x42, 0x36: 0x43}     # tilemaps from this index on are in the new table

LOAD_MAP, LOAD_MAP_CODE = 0x011c85, bytes.fromhex("0aaabf4818e785f3bf4918e785f4a9e785f5")    # C1/1C85: the tilemap's address

KEFKA = 298
SPECS, GRAPHICS, LARGE_MOLDS, MONSTER_PALETTES = 0x127000, 0x297000, 0x12ac24, 0x127820
KEFKA_SPEC = bytes.fromhex("3650820c20")
KEFKA_TILES = 149
SMALL_MOLDS, SMALL_MOLD_COUNT, ENEMIES = 0x12a824, 128, 384

FORMATIONS, FORMATION_SIZE, SLOTS = 0xf6200, 15, 6
ENEMY_NAMES, ENEMY_NAME_SIZE = 0xfc050, 10
LETTERS = {**{chr(ord('A') + n): 0x80 + n for n in range(26)}, **{chr(ord('a') + n): 0x9a + n for n in range(26)}}
KEFKA_FORMATION = 0x202
TIER_ENEMIES = {0x1d7: [343, 344, 345], 0x200: [349, 346, 347, 348], 0x201: [350, 351]}

def fail(why):
    sys.exit("christmas_final_battle: " + why + " (nothing was written)")

def formation_slots(rom, formation):
    at = FORMATIONS + formation * FORMATION_SIZE
    used, high = rom[at + 1] & 0x3f, rom[at + 14]
    return at, [(slot, rom[at + 2 + slot] | (0x100 if high & (1 << slot) else 0)) for slot in range(SLOTS) if used & (1 << slot)]

def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    data_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "christmas_data.json")
    rom = bytearray(open(sys.argv[1], "rb").read())
    data = json.load(open(data_path))

    # is it what this expects?
    if len(rom) != 0x400000:
        fail("the rom is not 4 MB: it is not one Worlds Collide has made")
    if rom[LOAD_MAP:LOAD_MAP + len(LOAD_MAP_CODE)] != LOAD_MAP_CODE:
        fail("the code that loads a battle background's tilemap is not the game's (is it patched already?)")
    spec = SPECS + KEFKA * 5
    if rom[spec:spec + 5] != KEFKA_SPEC:
        fail("final Kefka's sprite is not the game's: the rom has another final boss (-fb)")
    for index in NEW_SETS.values():
        if any(rom[SET_POINTERS + index * 3:SET_POINTERS + index * 3 + 3]):
            fail("a tile set this needs is in use")
    for formation, enemies in list(TIER_ENEMIES.items()) + [(KEFKA_FORMATION, [KEFKA])]:
        if [enemy for slot, enemy in formation_slots(rom, formation)[1]] != enemies:
            fail(f"formation {formation:#x} does not have the final battle's enemies")
    banks = [bank for bank in range(0xff, 0xf0, -1) if all(byte == 0xff for byte in rom[(bank - 0xc0) << 16:(bank - 0xbf) << 16])]
    if not banks:
        fail("no bank of the rom is empty")
    bank = banks[0]
    at = (bank - 0xc0) << 16                # where the next of what is new goes

    def write(blob):
        nonlocal at
        start = at
        if (at & 0xffff) + len(blob) > 0x10000:
            fail("the empty bank has no room")
        rom[at:at + len(blob)] = blob
        at += len(blob)
        return start + 0xc00000             # its address in the game

    # the tilemaps' own pointer table (3 bytes each, from index 0x40), and the code that reads it
    table = write(bytes(3 * len(NEW_MAPS)))
    code = bytes.fromhex(
        "c940" "b013"                       # cmp #$40 / bcs own (past the 19 bytes of the game's)
        "0a" "aa" "bf4818e7" "85f3" "bf4918e7" "85f4" "a9e7" "85f5" "6b"   # the game's: the tilemap is in bank E7
        "38e940" "85f3" "0a" "1865f3" "aa") # own: x = (index - 0x40) * 3
    for byte, to in enumerate((0xf3, 0xf4, 0xf5)):
        address = table + byte
        code += bytes([0xbf, address & 0xff, (address >> 8) & 0xff, address >> 16, 0x85, to])       # lda table + byte,x / sta
    code += bytes([0x6b])
    routine = write(code)
    rom[LOAD_MAP:LOAD_MAP + len(LOAD_MAP_CODE)] = bytes([0x22, routine & 0xff, (routine >> 8) & 0xff, routine >> 16]) + bytes([0xea] * (len(LOAD_MAP_CODE) - 4))

    # the four backgrounds
    for bg, new in data["backgrounds"].items():
        bg = int(bg)
        properties = PROPERTIES + bg * PROPERTY_SIZE
        sets = [rom[properties] & 0x7f, rom[properties + 1] & 0x7f, NEW_SETS[bg]][:len(new["sets"])]
        for index, blob in zip(sets, new["sets"]):
            address = write(bytes.fromhex(blob))
            rom[SET_POINTERS + index * 3:SET_POINTERS + index * 3 + 3] = bytes([address & 0xff, (address >> 8) & 0xff, address >> 16])
        address = write(bytes.fromhex(new["tilemap"]))
        entry = (table - 0xc00000) + (NEW_MAPS[bg] - 0x40) * 3
        rom[entry:entry + 3] = bytes([address & 0xff, (address >> 8) & 0xff, address >> 16])
        rom[properties:properties + 5] = bytes((sets + [0xff])[:3] + [NEW_MAPS[bg], NEW_MAPS[bg]])
        palette = PALETTES + (rom[properties + 5] & 0x7f) * PALETTE_SIZE
        rom[palette:palette + PALETTE_SIZE] = bytes.fromhex(new["palette"])

    # santa: final kefka's sprite, in his own tiles, mold and palette
    santa = data["santa"]
    graphics, mold, palette = (bytes.fromhex(santa[name]) for name in ("graphics", "mold", "palette"))
    if len(graphics) > KEFKA_TILES * 32:
        fail("santa has more tiles than final Kefka")
    pointer = (rom[spec] | (rom[spec + 1] << 8)) & 0x7fff
    rom[GRAPHICS + pointer * 8:GRAPHICS + pointer * 8 + len(graphics)] = graphics
    rom[LARGE_MOLDS + rom[spec + 4] * 32:LARGE_MOLDS + rom[spec + 4] * 32 + 32] = mold
    at_palette = MONSTER_PALETTES + (((rom[spec + 2] & 0x03) << 8) | rom[spec + 3]) * 16
    rom[at_palette:at_palette + 32] = palette

    # the enemies of the three tiers have a sprite (all nine have the same, a beast that was a part
    # of the statue's picture): they get one that is not seen, of one tile of the monsters'
    # graphics that is empty. the hand that points at an enemy is where its sprite is: a position
    # is in steps of 8 pixels and no more than 15 of them, so the one tile is also this many tiles
    # to the right in its mold (the battle hangs on a mold with nothing in its first row: the tile
    # is in it). the molds are written over ones that no enemy has
    empty = [address for address in range(GRAPHICS, GRAPHICS + 0x7fff * 8, 8) if not any(rom[address:address + 32])]
    used = {rom[SPECS + enemy * 5 + 4] for enemy in range(ENEMIES) if not rom[SPECS + enemy * 5 + 2] & 0x80}
    free = [index for index in range(SMALL_MOLD_COUNT - 1, -1, -1) if index not in used]
    positions = {int(formation): where for formation, where in data["positions"].items()}
    shifts = sorted({shift for where in positions.values() for x, y, shift in where})
    if not empty or len(free) < len(shifts):
        fail("no empty tile, or no molds that are not in use, for the enemies of the tiers")
    molds = {}
    for shift, index in zip(shifts, free):
        rom[SMALL_MOLDS + index * 8:SMALL_MOLDS + index * 8 + 8] = bytes([0x80 >> shift, 0, 0, 0, 0, 0, 0, 0])
        molds[shift] = index
    pointer = (empty[0] - GRAPHICS) // 8
    for formation, enemies in TIER_ENEMIES.items():
        for enemy, (x, y, shift) in zip(enemies, positions[formation]):
            tier_spec = SPECS + enemy * 5
            rom[tier_spec:tier_spec + 5] = bytes([pointer & 0xff, pointer >> 8, rom[tier_spec + 2] & 0x03, rom[tier_spec + 3], molds[shift]])

    # his name, where the enemies are named
    name = ENEMY_NAMES + KEFKA * ENEMY_NAME_SIZE
    rom[name:name + ENEMY_NAME_SIZE] = bytes(LETTERS[letter] for letter in "Santa") + bytes([0xff] * (ENEMY_NAME_SIZE - 5))

    # where the enemies are
    positions[KEFKA_FORMATION] = [santa["position"] + [0]]
    for formation, where in positions.items():
        start, slots = formation_slots(rom, formation)
        for (slot, enemy), (x, y, shift) in zip(slots, where):
            rom[start + 8 + slot] = (x << 4) | y

    open(sys.argv[2], "wb").write(rom)
    print(f"written: {sys.argv[2]} (the new graphics are in bank {bank:02X}, {(at & 0xffff):#x} bytes)")

if __name__ == "__main__":
    main()
