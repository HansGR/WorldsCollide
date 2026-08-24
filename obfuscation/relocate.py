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
"""

VANILLA_CHEST_PTRS = 0xed82f4
VANILLA_CHEST_DATA = 0xed8634
VANILLA_SHOP_DATA = 0xc47ac0

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

VANILLA_BASES = {
    "chest_ptrs": VANILLA_CHEST_PTRS,
    "chest_data": VANILLA_CHEST_DATA,
    "shop_data": VANILLA_SHOP_DATA,
}


def _patch_sites(sites, layout):
    from memory.space import Reserve, Read
    from obfuscation.claim import snes

    for operand_offset, vanilla_operand, table in sites:
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


def patch_shop_readers(layout):
    _patch_sites(SHOP_SITES, layout)
