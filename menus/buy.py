from memory.space import START_ADDRESS_SNES, Bank, Reserve, Write
import instruction.asm as asm
import args

class BuyMenu:
    # ROM table addresses (must match data/shops.py Shops class constants)
    PACK_SIZE_TABLE_SNES  = 0xc47fa8
    TRACK_PTR_TABLE_SNES  = 0xc48258

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

        When loading shop items for display, checks the tracking byte in Save RAM.
        If the item's bit is set (already purchased), returns $FF (empty) so the
        item is hidden from the buy list.

        Entry state: A=8-bit, X=16-bit, Y=16-bit
        $F1 = current menu slot (0-7)
        X = shop data offset (shop_index + menu_slot + 1)
        """
        src = [
            # Load original shop item
            asm.LDA(0xc47ac0, asm.LNG_X),     # Load item from ROM
            asm.CMP(0xff, asm.IMM8),           # Empty slot?
            asm.BEQ("RETURN"),                 # Skip check for empty items

            asm.PHA(),                         # Save item ID
            asm.PHX(),                         # Save X (16-bit)

            # Look up tracking pointer for this shop
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),        # Clean to 8-bit value
            asm.ASL(),                         # *2 for pointer table offset
            asm.TAX(),                         # X = offset
            asm.LDA(self.TRACK_PTR_TABLE_SNES, asm.LNG_X),  # Tracking pointer
            asm.TAX(),                         # X = Save RAM address (or 0)
            asm.SEP(0x20),                     # 8-bit A
            # Z flag still reflects the 16-bit LDA result
            asm.BEQ("RESTORE"),               # 0 = normal shop, skip

            # Load tracking byte from Save RAM and test bit for menu slot
            asm.LDA(0x7e0000, asm.LNG_X),     # Load tracking byte from WRAM
            asm.LDX(0xf1, asm.DIR),           # X = menu slot (0-7, 16-bit load)
            asm.BEQ("CHECK_BIT"),             # Slot 0: no shifting needed

            "SHIFT_LOOP",
            asm.LSR(),                         # Shift tracking byte right
            asm.DEX(),                         # Counter--
            asm.BNE("SHIFT_LOOP"),            # Loop until slot reached

            "CHECK_BIT",
            asm.AND(0x01, asm.IMM8),          # Test lowest bit
            asm.BEQ("RESTORE"),               # Not sold, use original item

            # Item is sold - return FF (empty)
            asm.PLX(),                         # Restore X (16-bit pop)
            asm.PLA(),                         # Discard saved item (8-bit pop)
            asm.LDA(0xff, asm.IMM8),          # Return empty
            asm.RTL(),

            "RESTORE",
            asm.PLX(),                         # Restore X
            asm.PLA(),                         # Restore original item
            "RETURN",
            asm.RTL(),
        ]

        space = Write(Bank.C3, src, "limited inventory: load shop item with tracking check")
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

        Entry state: A=8-bit, X=16-bit, Y=16-bit
        $4B = selected cursor slot (item index in buy list)
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

            # Get pack size: table index = shop_num * 8 + item_slot
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),        # Clean
            asm.ASL(),                         # *2
            asm.ASL(),                         # *4
            asm.ASL(),                         # *8
            asm.STA(0xeb, asm.DIR),            # Temp store in $EB-$EC
            asm.LDA(0x4b, asm.DIR),            # Item slot ($4B, 16-bit read)
            asm.AND(0x00ff, asm.IMM16),        # Clean
            asm.CLC(),
            asm.ADC(0xeb, asm.DIR),            # Add shop_num * 8
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

            # Build bit mask for item slot $4B
            asm.REP(0x20),                     # 16-bit A (to get clean TAY)
            asm.LDA(0x4b, asm.DIR),            # Item slot (16-bit load from $4B-$4C)
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
