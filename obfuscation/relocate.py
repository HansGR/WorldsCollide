"""Patch the game's readers to follow relocated tables (race builds).

Every reader of a relocated table is listed here as the rom offset of
its instruction's 24-bit operand together with the exact vanilla SNES
address that operand contains.  Patching asserts the vanilla bytes
before overwriting, so a disassembly/rom mismatch - or a future patch
landing on the same instruction - fails the build instead of silently
corrupting a reader.  Reserve() additionally makes any overlap with
another feature's patches fail loudly.

Reader inventory (see RACE_OBFUSCATION_PLAN.md section 3):

Chest tables - two routines in bank C0, twelve operands total:
  C0/15D7  map-load pass over the current map's chest records
  C0/4BD4  chest interaction: position match, then contents/type read
The pointer values inside the table are offsets relative to the record
base, so they survive relocation unchanged; only the base addresses
compiled into these instructions move.

Shop table - three operands in the bank C3 menu code.

Esper spell/rate/bonus table - three operands in the bank C2 battle
code (learn rates and spells at battle end, level-up bonus) and five in
the bank C3 esper menu code.  (Two additional apparent matches in a rom
scan at 0x02d7aa/0x02d809 are `JMP $D86E` instructions read at the
wrong alignment, not operands.)

Enemy steal/drop table - two operands in bank C2: battle-init steal
slot load and battle-end drop roll.

Coliseum match table - three operands in the bank C3 item-select menu
(opponent, reward, hide-reward flag).  The battle itself receives the
opponent through RAM, so the menu operands are the complete reader set.
"""

VANILLA_CHEST_PTRS = 0xed82f4
VANILLA_CHEST_DATA = 0xed8634
VANILLA_SHOP_DATA = 0xc47ac0
VANILLA_ESPER_DATA = 0xd86e00
VANILLA_ENEMY_ITEMS = 0xcf3000
VANILLA_COLISEUM = 0xdfb600

# (rom offset of operand, vanilla operand value, table it addresses)
CHEST_SITES = [
    # C0/15D7 map-load pass
    (0x015de, 0xed82f6, "chest_ptrs"),
    (0x015e4, 0xed82f4, "chest_ptrs"),
    (0x015f2, 0xed8634, "chest_data"),
    (0x015f8, 0xed8635, "chest_data"),
    (0x015ff, 0xed8636, "chest_data"),
    (0x0160a, 0xed8636, "chest_data"),
    # C0/4BD4 chest interaction
    (0x04bdb, 0xed82f6, "chest_ptrs"),
    (0x04be1, 0xed82f4, "chest_ptrs"),
    (0x04bed, 0xed8634, "chest_data"),
    (0x04bf5, 0xed8635, "chest_data"),
    (0x04c09, 0xed8638, "chest_data"),
    (0x04c0f, 0xed8636, "chest_data"),
]

SHOP_SITES = [
    (0x3b9b0, 0xc47ac0, "shop_data"),  # C3/B9AF shop item
    (0x3ba33, 0xc47ac0, "shop_data"),  # C3/BA32 shop flags
    (0x3bff4, 0xc47ac0, "shop_data"),  # C3/BFF3 shop flags
]

ESPER_SITES = [
    # bank C2 battle code (record: 5 x [rate, spell id] + bonus at +10)
    (0x26033, 0xd86e01, "esper_data"),  # C2/6032 spell id
    (0x2603d, 0xd86e00, "esper_data"),  # C2/603C learn rate
    (0x260ea, 0xd86e0a, "esper_data"),  # C2/60E9 level-up bonus
    # bank C3 esper menu
    (0x359f7, 0xd86e00, "esper_data"),  # C3/59F6
    (0x359fe, 0xd86e00, "esper_data"),  # C3/59FD
    (0x35a2c, 0xd86e00, "esper_data"),  # C3/5A2B
    (0x35b7d, 0xd86e00, "esper_data"),  # C3/5B7C
    (0x35b8b, 0xd86e00, "esper_data"),  # C3/5B8A
]

ENEMY_ITEM_SITES = [
    (0x22c42, 0xcf3000, "enemy_items"),  # C2/2C41 battle-init steal slot
    (0x25f2e, 0xcf3002, "enemy_items"),  # C2/5F2D battle-end drop roll
]

COLISEUM_SITES = [
    (0x3b238, 0xdfb600, "coliseum"),  # C3/B237 opponent
    (0x3b23f, 0xdfb602, "coliseum"),  # C3/B23E reward
    (0x3b246, 0xdfb603, "coliseum"),  # C3/B245 hide-reward flag
]

VANILLA_BASES = {
    "chest_ptrs": VANILLA_CHEST_PTRS,
    "chest_data": VANILLA_CHEST_DATA,
    "shop_data": VANILLA_SHOP_DATA,
    "esper_data": VANILLA_ESPER_DATA,
    "enemy_items": VANILLA_ENEMY_ITEMS,
    "coliseum": VANILLA_COLISEUM,
}


def table_address(args, table):
    """Effective 24-bit SNES address of a relocatable table.

    WC writes fresh code each build with table addresses compiled in
    (shop empty guard, limited-inventory compaction, esper mastered
    icon, coliseum rewards menu).  Those readers must follow the real
    table when a race build relocates it; everywhere else they read the
    vanilla address.  The static vanilla readers (the *_SITES lists)
    are patched separately by the patch_*_readers functions.
    """
    if args.race:
        from obfuscation import claim
        return claim.snes(claim.layout(args)[table])
    return VANILLA_BASES[table]


def shop_data_address(args):
    return table_address(args, "shop_data")


def _patch_sites(sites, layout, skip=()):
    from memory.space import Reserve, Read
    from obfuscation.claim import snes

    for operand_offset, vanilla_operand, table in sites:
        if operand_offset in skip:
            continue
        current = int.from_bytes(bytes(Read(operand_offset, operand_offset + 2)), "little")
        assert current == vanilla_operand, (
            f"race reader patch at 0x{operand_offset:06x}: expected vanilla "
            f"operand 0x{vanilla_operand:06x}, found 0x{current:06x}")

        delta = vanilla_operand - VANILLA_BASES[table]
        new_operand = snes(layout[table]) + delta
        space = Reserve(operand_offset, operand_offset + 2,
                        f"race reader: {table}+{delta} operand")
        space.write(new_operand.to_bytes(3, "little"))


def patch_chest_readers(layout):
    _patch_sites(CHEST_SITES, layout)


def patch_shop_readers(layout, skip=()):
    """Patch the vanilla shop readers to the relocated table.

    skip: operand offsets to leave alone because another feature already
    replaced the instruction with code that reads the effective address
    (e.g. the limited-inventory item-load hook at C3/B9AF).
    """
    _patch_sites(SHOP_SITES, layout, skip)


def patch_esper_readers(layout):
    _patch_sites(ESPER_SITES, layout)


def patch_enemy_item_readers(layout):
    _patch_sites(ENEMY_ITEM_SITES, layout)


def patch_coliseum_readers(layout):
    _patch_sites(COLISEUM_SITES, layout)
