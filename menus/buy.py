from memory.space import START_ADDRESS_SNES, Bank, Reserve, Write
from data.shops import Shops
import instruction.asm as asm
import args

class BuyMenu:
    # ROM table addresses (must match data/shops.py Shops class constants)
    PACK_SIZE_TABLE_SNES  = 0xc47fa8
    TRACK_PTR_TABLE_SNES  = 0xc48258

    # Direct page addresses for compaction buffers (must match data/shops.py)
    COMPACT_ITEMS_DP = Shops.COMPACT_ITEMS_DP   # $C0
    SLOT_MAP_DP      = Shops.SLOT_MAP_DP         # $C8
    COMPACT_FLAG_DP  = Shops.COMPACT_FLAG_DP     # $E1

    def __init__(self):
        if args.shop_limited_inventory:
            self.mod()

    def mod(self):
        self.hook_load_item()
        self.hook_buy_setup()
        self.hook_pre_order()
        self.hook_execute_buy()

    def hook_load_item(self):
        """Hook at C3/B9AF: replace LDA $C47AC0,X with JSL to custom routine.

        If compact mode is active ($E1 != 0), reads from the pre-built compact
        buffer at $C0-$C7 using $F1 (display position) as the index. This ensures
        available items are packed into the first N rows with no gaps.

        If compact mode is not active, loads from ROM as normal.

        Entry state: A=8-bit, X=16-bit, Y=16-bit
        $F1 = current menu slot (0-7)
        X = shop data offset (shop_index + menu_slot + 1) [unused in compact mode]
        """
        src = [
            # Check if compact mode is active
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $E1
            asm.BNE("USE_COMPACT"),

            # Normal mode: load from ROM as usual
            asm.LDA(0xc47ac0, asm.LNG_X),     # Load item from ROM
            asm.RTL(),

            # Compact mode: read from pre-built compact buffer
            "USE_COMPACT",
            asm.PHX(),                          # Save original X
            asm.LDX(0xf1, asm.DIR),            # X = display position (menu slot)
            asm.LDA(self.COMPACT_ITEMS_DP, asm.DIR_X),  # LDA $C0,X
            asm.PLX(),                          # Restore X
            asm.RTL(),
        ]

        space = Write(Bank.C3, src, "limited inventory: load shop item with compaction")
        custom_load_item_addr = space.start_address + START_ADDRESS_SNES

        # Replace the 4-byte LDA $C47AC0,X at B9AF with JSL to our routine
        space = Reserve(0x3b9af, 0x3b9b2, "shop buy menu load item hook")
        space.write(
            asm.JSL(custom_load_item_addr),
        )

    def hook_buy_setup(self):
        """Hook at C3/B4DF: replace JSR $B82F with JSR to custom routine.

        When player presses A on an item in the buy list, this sets the buy
        quantity ($28) and buy limit ($6A) to the pack size, and stores the
        pack size in $E0 as a "limited mode" flag for the order menu.

        In compact mode, $4B is the display position. The original shop slot
        is looked up from slot_map[$4B] at $C8+$4B.

        Entry state: A=8-bit, X=16-bit, Y=16-bit
        $4B = selected cursor slot (display position in buy list)
        """
        src = [
            asm.JSR(0xb82f, asm.ABS),         # Call original set_buy_limit

            asm.PHA(),                         # Save A
            asm.PHX(),                         # Save X

            # Check if limited shop
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),        # Clean
            asm.ASL(),                         # *2
            asm.TAX(),
            asm.LDA(self.TRACK_PTR_TABLE_SNES, asm.LNG_X),  # Tracking pointer
            asm.SEP(0x20),                     # 8-bit A
            asm.BEQ("DONE"),                  # 0 = normal shop (Z from 16-bit LDA)

            # Resolve display position to original slot via slot_map
            # If compact mode active, original_slot = slot_map[$4B]; else use $4B directly
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $E1
            asm.BEQ("USE_4B"),                # not compact mode, use $4B
            # Clean 16-bit X from $4B (only low byte is meaningful)
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x4b, asm.DIR),            # A = $4B-$4C (16-bit)
            asm.AND(0x00ff, asm.IMM16),        # clean to 0-7
            asm.TAX(),                         # X = clean display position
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.SLOT_MAP_DP, asm.DIR_X),  # A = original slot from $C8,X
            asm.BRA("HAVE_SLOT"),
            "USE_4B",
            asm.LDA(0x4b, asm.DIR),           # A = $4B (original slot = display pos)
            "HAVE_SLOT",
            asm.STA(0xeb, asm.DIR),            # $EB = original slot index

            # Get pack size: table index = shop_num * 8 + original_slot
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),        # Clean
            asm.ASL(),                         # *2
            asm.ASL(),                         # *4
            asm.ASL(),                         # *8
            asm.STA(0xec, asm.DIR),            # Temp store in $EC-$ED (shifted by 1 to not overwrite $EB)
            asm.LDA(0xeb, asm.DIR),            # Original slot (in $EB; 16-bit read includes $EC)
            asm.AND(0x00ff, asm.IMM16),        # Clean to just the slot byte
            asm.CLC(),
            asm.ADC(0xec, asm.DIR),            # Add shop_num * 8
            asm.TAX(),                         # X = pack table index
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.PACK_SIZE_TABLE_SNES, asm.LNG_X),  # Pack size
            asm.BEQ("DONE"),                  # 0 = no pack (shouldn't happen)

            asm.STA(0x28, asm.DIR),            # Set buy quantity
            asm.STA(0x6a, asm.DIR),            # Set buy limit (locks quantity up)
            asm.STA(0xe0, asm.DIR),            # Set limited mode flag/pack size

            "DONE",
            asm.PLX(),
            asm.PLA(),
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: buy setup with pack size")
        custom_buy_setup_addr = space.start_address

        # Replace address in JSR $B82F at B4DF (opcode at B4DF, address at B4E0-B4E1)
        space = Reserve(0x3b4e0, 0x3b4e1, "shop buy menu set buy limit hook")
        space.write(
            (custom_buy_setup_addr & 0xffff).to_bytes(2, "little"),
        )

    def hook_pre_order(self):
        """Hook at C3/B50B: replace JSR $BB53 with JSR to custom routine.

        In the order menu (state 27), this runs every frame. If limited mode
        is active ($E0 != 0), it forces $28 back to the pack size, preventing
        the player from changing the quantity via left/down inputs.

        Then falls through to the original BB53 (get order value).
        """
        src = [
            asm.LDA(0xe0, asm.DIR),            # Limited mode flag
            asm.BEQ("NORMAL"),                # 0 = unlimited, skip
            asm.STA(0x28, asm.DIR),            # Force quantity = pack size
            "NORMAL",
            asm.JMP(0xbb53, asm.ABS),         # Tail call to original get_order_value
        ]

        space = Write(Bank.C3, src, "limited inventory: pre-order quantity lock")
        custom_pre_order_addr = space.start_address

        # Replace address in JSR $BB53 at B50B (opcode at B50B, address at B50C-B50D)
        space = Reserve(0x3b50c, 0x3b50d, "shop order menu get value hook")
        space.write(
            (custom_pre_order_addr & 0xffff).to_bytes(2, "little"),
        )

    def hook_execute_buy(self):
        """Hook at C3/B5B3: replace JSR $B5B7 with JSR to custom routine.

        After the purchase is executed, sets the tracking bit in Save RAM
        for the purchased item slot, so it won't appear in the shop next time.

        In compact mode, $4B is the display position. The original shop slot
        is looked up from slot_map[$4B] at $C8+$4B.
        """
        src = [
            asm.JSR(0xb5b7, asm.ABS),         # Call original execute_purchase

            asm.PHA(),
            asm.PHX(),
            asm.PHY(),

            # Check if limited shop
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),                         # *2
            asm.TAX(),
            asm.LDA(self.TRACK_PTR_TABLE_SNES, asm.LNG_X),  # Tracking pointer
            asm.TAX(),                         # X = Save RAM address
            asm.SEP(0x20),                     # 8-bit A
            asm.CPX(0x0000, asm.IMM16),       # Zero pointer? (16-bit X compare)
            asm.BEQ("DONE"),                  # Normal shop, skip

            # Resolve display position to original slot
            asm.PHX(),                         # Save SRAM address
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $E1
            asm.BEQ("USE_4B"),
            # Clean 16-bit X from $4B (only low byte is meaningful)
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x4b, asm.DIR),            # A = $4B-$4C (16-bit)
            asm.AND(0x00ff, asm.IMM16),        # clean to 0-7
            asm.TAX(),                         # X = clean display position
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.SLOT_MAP_DP, asm.DIR_X),  # A = original slot from $C8,X
            asm.BRA("HAVE_SLOT"),
            "USE_4B",
            asm.LDA(0x4b, asm.DIR),           # A = $4B directly
            "HAVE_SLOT",
            asm.PLX(),                         # Restore SRAM address

            # Build bit mask for the original item slot (in A, 0-7)
            asm.REP(0x20),                     # 16-bit A (to get clean TAY)
            asm.AND(0x0007, asm.IMM16),       # Mask to 0-7 (clean both bytes)
            asm.TAY(),                         # Y = clean slot number
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(0x01, asm.IMM8),          # Start with bit 0
            asm.CPY(0x0000, asm.IMM16),       # Slot 0?
            asm.BEQ("SET_BIT"),               # No shifting needed

            "SHIFT_LOOP",
            asm.ASL(),                         # Shift bit left
            asm.DEY(),
            asm.BNE("SHIFT_LOOP"),

            "SET_BIT",
            asm.ORA(0x7e0000, asm.LNG_X),    # OR with tracking byte
            asm.STA(0x7e0000, asm.LNG_X),    # Store back

            # Clear limited mode flag (will be re-set if player buys again)
            asm.STZ(0xe0, asm.DIR),

            "DONE",
            asm.PLY(),
            asm.PLX(),
            asm.PLA(),
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: execute buy with tracking")
        custom_execute_buy_addr = space.start_address

        # Replace address in JSR $B5B7 at B5B3 (opcode at B5B3, address at B5B4-B5B5)
        space = Reserve(0x3b5b4, 0x3b5b5, "shop buy menu execute purchase hook")
        space.write(
            (custom_execute_buy_addr & 0xffff).to_bytes(2, "little"),
        )
