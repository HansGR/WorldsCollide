from memory.space import START_ADDRESS_SNES, Bank, Reserve, Write
from data.shops import Shops
import instruction.asm as asm
import args

class BuyMenu:
    # ROM table addresses (must match data/shops.py Shops class constants)
    PACK_SIZE_TABLE_SNES  = 0xc47fa8
    TRACK_PTR_TABLE_SNES  = 0xc48258

    # Direct page addresses for compaction buffers (must match data/shops.py)
    COMPACT_ITEMS_DP = Shops.COMPACT_ITEMS_DP   # $78
    SLOT_MAP_DP      = Shops.SLOT_MAP_DP         # $B8
    COMPACT_FLAG_DP  = Shops.COMPACT_FLAG_DP     # $25
    LIMITED_MODE_DP  = Shops.LIMITED_MODE_DP      # $30

    # Free DP bytes used as temporaries for price inflation / pack lookup
    SLOT_TEMP_DP       = 0x42   # 1 byte: temp for slot index or pack size
    PACK_TEMP_DP       = 0x49   # 2 bytes ($49-$4A): temp for pack table computation
    UNIT_PRICE_SAVE_DP = 0x60   # 2 bytes ($60-$61): saved unit price for restore

    def __init__(self):
        if args.shop_limited_inventory:
            self.mod()

    def mod(self):
        # Write shared resources first
        self._write_get_pack_subroutine()
        self._write_qty_label_text()

        # Existing hooks
        self.hook_load_item()
        self.hook_buy_setup()
        self.hook_pre_order()
        self.hook_execute_buy()

        # New hooks for price display and Qty: panel
        self.hook_price_display()
        self.hook_affordability_restore()
        self.hook_draw_labels()
        self.hook_draw_qty_value()

    # ------------------------------------------------------------------
    # Shared resources
    # ------------------------------------------------------------------

    def _write_get_pack_subroutine(self):
        """Write a reusable subroutine to Bank C3 that looks up the pack size
        for a given display slot.

        Input:  A = display slot (8-bit, 0-7)
        Output: A = pack size (8-bit; 0 = normal shop, 1-15 = limited)
        Clobbers: X.  Preserves: Y.
        Entry state: 8-bit A, 16-bit X/Y.
        """
        src = [
            asm.PHY(),
            asm.STA(self.SLOT_TEMP_DP, asm.DIR),       # $42 = display slot

            # Check if limited shop
            asm.REP(0x20),                              # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),                 # shop number
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),                                   # *2
            asm.TAX(),
            asm.LDA(self.TRACK_PTR_TABLE_SNES, asm.LNG_X),
            asm.SEP(0x20),                               # 8-bit A
            asm.BEQ("RET_ZERO"),                         # Z from 16-bit LDA; 0 = normal

            # Resolve display slot → original slot (if compact mode)
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),      # $25
            asm.BEQ("DIRECT"),                           # not compact
            asm.REP(0x20),
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),
            asm.AND(0x00ff, asm.IMM16),
            asm.TAX(),
            asm.SEP(0x20),
            asm.LDA(self.SLOT_MAP_DP, asm.DIR_X),       # original slot from $B8,X
            asm.STA(self.SLOT_TEMP_DP, asm.DIR),         # update $42
            "DIRECT",

            # Compute pack table index = shop_num * 8 + original_slot
            asm.REP(0x20),
            asm.LDA(0x7e0201, asm.LNG),
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),
            asm.ASL(),
            asm.ASL(),                                   # *8
            asm.STA(self.PACK_TEMP_DP, asm.DIR),         # $49-$4A
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),
            asm.AND(0x00ff, asm.IMM16),
            asm.CLC(),
            asm.ADC(self.PACK_TEMP_DP, asm.DIR),
            asm.TAX(),
            asm.SEP(0x20),
            asm.LDA(self.PACK_SIZE_TABLE_SNES, asm.LNG_X),

            asm.PLY(),
            asm.RTS(),

            "RET_ZERO",
            asm.LDA(0x00, asm.IMM8),
            asm.PLY(),
            asm.RTS(),
        ]
        space = Write(Bank.C3, src, "limited inventory: get pack size subroutine")
        self._get_pack_addr = space.start_address   # ROM address in Bank C3

    def _write_qty_label_text(self):
        """Write the positioned text data for the 'Qty:' label to Bank C3.

        Format: 2-byte tilemap position (little-endian) + text bytes + $00.
        Position $7CB3 places the label one section below 'Equipped:' ($7BB3).

        FF6 menu text encoding: A=$80..Z=$99, a=$9A..z=$B3, ':'=$C1.
        'Qty:' = Q($90) t($AD) y($B2) :($C1)
        """
        qty_text = bytes([0xb3, 0x7c, 0x90, 0xad, 0xb2, 0xc1, 0x00])
        space = Write(Bank.C3, [qty_text], "limited inventory: Qty label text data")
        self._qty_text_addr = space.start_address   # ROM address in Bank C3

    # ------------------------------------------------------------------
    # Hook helpers
    # ------------------------------------------------------------------

    def _get_pack_addr_local(self):
        """Bank-C3-local (16-bit) address of get_pack_size subroutine."""
        return self._get_pack_addr & 0xffff

    def _qty_text_addr_local(self):
        """Bank-C3-local (16-bit) address of 'Qty:' text data."""
        return self._qty_text_addr & 0xffff

    # ------------------------------------------------------------------
    # Existing hooks (unchanged)
    # ------------------------------------------------------------------

    def hook_load_item(self):
        """Hook at C3/B9AF: replace LDA $C47AC0,X with JSL to custom routine.

        If compact mode is active ($25 != 0), reads from the pre-built compact
        buffer at $78-$7F using $F1 (display position) as the index. This ensures
        available items are packed into the first N rows with no gaps.

        If compact mode is not active, loads from ROM as normal.

        Entry state: A=8-bit, X=16-bit, Y=16-bit
        $F1 = current menu slot (0-7)
        X = shop data offset (shop_index + menu_slot + 1) [unused in compact mode]
        """
        src = [
            # Check if compact mode is active
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BNE("USE_COMPACT"),

            # Normal mode: load from ROM as usual
            asm.LDA(0xc47ac0, asm.LNG_X),     # Load item from ROM
            asm.RTL(),

            # Compact mode: read from pre-built compact buffer
            "USE_COMPACT",
            asm.PHX(),                          # Save original X
            asm.LDX(0xf1, asm.DIR),            # X = display position (menu slot)
            asm.LDA(self.COMPACT_ITEMS_DP, asm.DIR_X),  # LDA $78,X
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

        Sets $28 (qty), $6A (buy limit), and $30 (limited flag) to the pack
        size.  Then temporarily inflates the price in $7E9F09 for the cursor
        slot so the affordability check at B7E6 (which runs immediately after
        this hook) compares GP against the *total pack price*, not the unit
        price.  The original unit price is saved in $60-$61 so the next hook
        (hook_affordability_restore) can put it back.

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
            asm.BNE("IS_LIMITED"),            # nonzero = limited shop, continue
            # Normal shop: early exit (duplicated exit sequence to avoid long branch)
            asm.PLX(),
            asm.PLA(),
            asm.RTS(),

            "IS_LIMITED",
            # Resolve display position to original slot via slot_map
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BEQ("USE_4B"),                # not compact mode, use $4B
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x4b, asm.DIR),            # A = $4B-$4C (16-bit)
            asm.AND(0x00ff, asm.IMM16),        # clean to 0-7
            asm.TAX(),                         # X = clean display position
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.SLOT_MAP_DP, asm.DIR_X),  # A = original slot from $B8,X
            asm.BRA("HAVE_SLOT"),
            "USE_4B",
            asm.LDA(0x4b, asm.DIR),           # A = $4B (original slot = display pos)
            "HAVE_SLOT",
            asm.STA(0x38, asm.DIR),            # $38 = original slot index (temp)

            # Get pack size: table index = shop_num * 8 + original_slot
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x7e0201, asm.LNG),        # Shop number
            asm.AND(0x00ff, asm.IMM16),        # Clean
            asm.ASL(),                         # *2
            asm.ASL(),                         # *4
            asm.ASL(),                         # *8
            asm.STA(0x40, asm.DIR),            # Temp store in $40-$41
            asm.LDA(0x38, asm.DIR),            # Original slot
            asm.AND(0x00ff, asm.IMM16),        # Clean to just the slot byte
            asm.CLC(),
            asm.ADC(0x40, asm.DIR),            # Add shop_num * 8
            asm.TAX(),                         # X = pack table index
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.PACK_SIZE_TABLE_SNES, asm.LNG_X),  # Pack size
            asm.BNE("HAS_PACK"),              # nonzero = valid pack, continue
            # Zero pack: early exit
            asm.PLX(),
            asm.PLA(),
            asm.RTS(),
            "HAS_PACK",

            asm.STA(0x28, asm.DIR),            # Set buy quantity
            asm.STA(0x6a, asm.DIR),            # Set buy limit (locks quantity up)
            asm.STA(self.LIMITED_MODE_DP, asm.DIR),  # Set limited mode flag ($30)

            # ---- NEW: inflate $7E9F09[$4B*2] so the GP check sees pack price ----
            asm.STA(self.SLOT_TEMP_DP, asm.DIR),  # $42 = pack_size

            # Compute X = $4B * 2 (offset into price buffer)
            asm.REP(0x20),
            asm.LDA(0x4b, asm.DIR),
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),
            asm.TAX(),

            # Save the original unit price
            asm.LDA(0x7e9f09, asm.LNG_X),      # 16-bit unit price
            asm.STA(self.UNIT_PRICE_SAVE_DP, asm.DIR),  # → $60-$61
            asm.SEP(0x20),

            # 16-bit × 8-bit multiply: unit_price * pack_size
            # Step 1: price_low * pack
            asm.LDA(self.UNIT_PRICE_SAVE_DP, asm.DIR),     # $60 = price low byte
            asm.STA(0x4202, asm.ABS),           # hw multiplicand
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),            # $42 = pack
            asm.STA(0x4203, asm.ABS),           # trigger multiply
            asm.NOP(),                          # wait for hw multiply (8 cycles)
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),
            asm.LDA(0x4216, asm.ABS),           # R1_low
            asm.STA(self.PACK_TEMP_DP, asm.DIR),            # $49
            asm.LDA(0x4217, asm.ABS),           # R1_high (carry)
            asm.STA(self.PACK_TEMP_DP + 1, asm.DIR),        # $4A

            # Step 2: price_high * pack
            asm.LDA(self.UNIT_PRICE_SAVE_DP + 1, asm.DIR),  # $61 = price high byte
            asm.STA(0x4202, asm.ABS),
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),             # $42 = pack
            asm.STA(0x4203, asm.ABS),           # trigger multiply
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),
            asm.NOP(),

            # Combine: final_high = R2_low + R1_high
            asm.CLC(),
            asm.LDA(0x4216, asm.ABS),           # R2_low
            asm.ADC(self.PACK_TEMP_DP + 1, asm.DIR),  # + R1_high ($4A)
            asm.BCS("CAP_PRICE"),               # overflow → cap
            asm.STA(self.PACK_TEMP_DP + 1, asm.DIR),  # $4A = final high byte
            asm.LDA(0x4217, asm.ABS),           # R2_high
            asm.BNE("CAP_PRICE"),               # >0 → cap

            # Store inflated price: $49 = low, $4A = high
            asm.REP(0x20),
            asm.LDA(self.PACK_TEMP_DP, asm.DIR),  # 16-bit result from $49-$4A
            asm.STA(0x7e9f09, asm.LNG_X),
            asm.SEP(0x20),
            asm.BRA("DONE"),

            "CAP_PRICE",
            asm.REP(0x20),
            asm.LDA(0xffff, asm.IMM16),
            asm.STA(0x7e9f09, asm.LNG_X),
            asm.SEP(0x20),

            "DONE",
            asm.PLX(),
            asm.PLA(),
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: buy setup with pack size and price inflate")
        custom_buy_setup_addr = space.start_address

        # Replace address in JSR $B82F at B4DF (opcode at B4DF, address at B4E0-B4E1)
        space = Reserve(0x3b4e0, 0x3b4e1, "shop buy menu set buy limit hook")
        space.write(
            (custom_buy_setup_addr & 0xffff).to_bytes(2, "little"),
        )

    def hook_pre_order(self):
        """Hook at C3/B50B: replace JSR $BB53 with JSR to custom routine.

        In the order menu (state 27), this runs every frame. If limited mode
        is active ($30 != 0), it forces $28 back to the pack size, preventing
        the player from changing the quantity via left/down inputs.

        Then falls through to the original BB53 (get order value).
        """
        src = [
            asm.LDA(self.LIMITED_MODE_DP, asm.DIR),  # Limited mode flag ($30)
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
        is looked up from slot_map[$4B] at $B8+$4B.
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
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BEQ("USE_4B"),
            # Clean 16-bit X from $4B (only low byte is meaningful)
            asm.REP(0x20),                     # 16-bit A
            asm.LDA(0x4b, asm.DIR),            # A = $4B-$4C (16-bit)
            asm.AND(0x00ff, asm.IMM16),        # clean to 0-7
            asm.TAX(),                         # X = clean display position
            asm.SEP(0x20),                     # 8-bit A
            asm.LDA(self.SLOT_MAP_DP, asm.DIR_X),  # A = original slot from $B8,X
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
            asm.STZ(self.LIMITED_MODE_DP, asm.DIR),  # Clear $30
            asm.STZ(0x4e, asm.DIR),            # Reset cursor to top for redraw

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

    # ------------------------------------------------------------------
    # New hooks for pack-price display and Qty: panel
    # ------------------------------------------------------------------

    def hook_price_display(self):
        """Hook at C3/B9CF: replace JSR $052E with JSR to custom routine.

        In the buy-list draw loop, BA0C has just computed the per-unit price
        and stored it to $F3-$F4 (and to $7E9F09).  Before the number-to-text
        routine ($052E) converts $F3 for display, we multiply $F3-$F4 by the
        pack size so the player sees the *total pack cost* in the item list.

        $7E9F09 is intentionally left unchanged (it keeps the unit price).
        The affordability fix is handled separately in hook_buy_setup /
        hook_affordability_restore.

        Entry state: A=8-bit, X/Y=16-bit.  $F1 = display slot (0-7).
        """
        src = [
            # Quick check: skip everything for normal shops
            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BEQ("CONVERT"),

            # Get pack size for current display slot $F1
            asm.LDA(0xf1, asm.DIR),
            asm.JSR(self._get_pack_addr_local(), asm.ABS),
            asm.CMP(0x00, asm.IMM8),
            asm.BEQ("CONVERT"),
            asm.CMP(0x01, asm.IMM8),           # pack=1 → no multiply needed
            asm.BEQ("CONVERT"),

            # --- 16-bit multiply: $F3-$F4 *= pack_size (A) ---
            asm.STA(self.SLOT_TEMP_DP, asm.DIR),  # $42 = pack_size

            # Step 1: $F3 (low byte) * pack
            asm.LDA(0xf3, asm.DIR),
            asm.STA(0x4202, asm.ABS),           # hw multiplicand
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),
            asm.STA(0x4203, asm.ABS),           # trigger multiply
            asm.NOP(), asm.NOP(), asm.NOP(), asm.NOP(),
            asm.LDA(0x4216, asm.ABS),           # R1_low
            asm.STA(self.PACK_TEMP_DP, asm.DIR),            # $49
            asm.LDA(0x4217, asm.ABS),           # R1_high
            asm.STA(self.PACK_TEMP_DP + 1, asm.DIR),        # $4A

            # Step 2: $F4 (high byte) * pack
            asm.LDA(0xf4, asm.DIR),
            asm.STA(0x4202, asm.ABS),
            asm.LDA(self.SLOT_TEMP_DP, asm.DIR),
            asm.STA(0x4203, asm.ABS),
            asm.NOP(), asm.NOP(), asm.NOP(), asm.NOP(),

            # Combine: final_high = R2_low + R1_high
            asm.CLC(),
            asm.LDA(0x4216, asm.ABS),           # R2_low
            asm.ADC(self.PACK_TEMP_DP + 1, asm.DIR),
            asm.BCS("CAP"),
            asm.STA(self.PACK_TEMP_DP + 1, asm.DIR),
            asm.LDA(0x4217, asm.ABS),           # R2_high
            asm.BNE("CAP"),

            # Store result back to $F3-$F4 for $052E
            asm.LDA(self.PACK_TEMP_DP, asm.DIR),
            asm.STA(0xf3, asm.DIR),
            asm.LDA(self.PACK_TEMP_DP + 1, asm.DIR),
            asm.STA(0xf4, asm.DIR),
            asm.BRA("CONVERT"),

            "CAP",
            asm.LDA(0xff, asm.IMM8),
            asm.STA(0xf3, asm.DIR),
            asm.STA(0xf4, asm.DIR),

            "CONVERT",
            asm.JMP(0x052e, asm.ABS),          # tail-call original text conversion
        ]

        space = Write(Bank.C3, src, "limited inventory: price display multiply")
        custom_addr = space.start_address

        # Replace address in JSR $052E at B9CF (opcode B9CF, address B9D0-B9D1)
        space = Reserve(0x3b9d0, 0x3b9d1, "shop buy menu price display hook")
        space.write(
            (custom_addr & 0xffff).to_bytes(2, "little"),
        )

    def hook_affordability_restore(self):
        """Hook at C3/B4E2: replace JSR $B7E6 with JSR to custom routine.

        Calls the original affordability check (B7E6) which reads the inflated
        pack price from $7E9F09.  After B7E6 returns, restores the original
        unit price from $60-$61 so the order menu and execute-buy routines
        continue to see the per-unit price (they multiply by $28=pack_size
        themselves).

        Entry state: 8-bit A, 16-bit X/Y.
        """
        src = [
            asm.JSR(0xb7e6, asm.ABS),          # original affordability check

            # Restore unit price if we're in limited mode
            asm.LDA(self.LIMITED_MODE_DP, asm.DIR),  # $30 (set by hook_buy_setup)
            asm.BEQ("DONE"),

            asm.PHX(),
            asm.REP(0x20),
            asm.LDA(0x4b, asm.DIR),
            asm.AND(0x00ff, asm.IMM16),
            asm.ASL(),
            asm.TAX(),
            asm.LDA(self.UNIT_PRICE_SAVE_DP, asm.DIR),  # $60-$61 = saved unit price
            asm.STA(0x7e9f09, asm.LNG_X),       # restore
            asm.SEP(0x20),
            asm.PLX(),

            "DONE",
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: affordability restore")
        custom_addr = space.start_address

        # Replace address in JSR $B7E6 at B4E2 (opcode B4E2, address B4E3-B4E4)
        space = Reserve(0x3b4e3, 0x3b4e4, "shop buy menu affordability hook")
        space.write(
            (custom_addr & 0xffff).to_bytes(2, "little"),
        )

    def hook_draw_labels(self):
        """Hook JSR $C2E1 at B98F and BAAB to also draw 'Qty:' label.

        The original C2E1 draws 'Owned:' and 'Equipped:' in blue.  For
        limited shops ($25 != 0), we additionally draw 'Qty:' below
        'Equipped:' at tilemap position $7CB3.
        """
        qty_text_local = self._qty_text_addr_local()

        src = [
            asm.JSR(0xc2e1, asm.ABS),          # original: draw Owned:, Equipped:

            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BEQ("DONE"),

            # Draw "Qty:" in blue
            asm.JSR(0xc2f7, asm.ABS),          # Color: Blue
            asm.LDY(qty_text_local, asm.IMM16),
            asm.JSR(0x02f9, asm.ABS),          # Draw positioned text
            asm.JSR(0xc2f2, asm.ABS),          # Color: User's

            "DONE",
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: draw labels with Qty")
        labels_addr = space.start_address

        # Hook both call sites of JSR $C2E1
        # Site 1: B98F (initial buy list draw)
        space = Reserve(0x3b990, 0x3b991, "shop buy menu draw labels hook 1")
        space.write((labels_addr & 0xffff).to_bytes(2, "little"))

        # Site 2: BAAB (order menu redraw)
        space = Reserve(0x3baac, 0x3baad, "shop buy menu draw labels hook 2")
        space.write((labels_addr & 0xffff).to_bytes(2, "little"))

    def hook_draw_qty_value(self):
        """Hook JMP $BF69 at C3/BCAB to also draw the pack quantity.

        BCA8 (draw equipped count) does JSR $BFC2 then JMP $BF69.  We replace
        the JMP target so that after the equipped count is drawn, we also draw
        the pack size at tilemap position $7D3F (one section below the
        equipped count at $7C3F).

        For normal shops ($25 = 0), we clear the qty area to avoid stale data.
        """
        src = [
            # BF69 expects A = item ID (set by BFC2 before the JMP).
            # We must call it first before clobbering A.
            asm.JSR(0xbf69, asm.ABS),          # draw equipped qty (was a tail-call JMP)

            asm.LDA(self.COMPACT_FLAG_DP, asm.DIR),  # $25
            asm.BEQ("CLEAR"),

            # Get pack size for cursor slot $4B
            asm.LDA(0x4b, asm.DIR),
            asm.JSR(self._get_pack_addr_local(), asm.ABS),
            asm.CMP(0x00, asm.IMM8),
            asm.BEQ("CLEAR"),

            # Convert pack size to text and draw 2 digits at $7D3F
            asm.JSR(0x04e0, asm.ABS),          # 8-bit A → 3-digit text at $F7-$F9
            asm.LDX(0x7d3f, asm.IMM16),        # tilemap position
            asm.JSR(0x04b6, asm.ABS),          # draw 2 digits (skip 1 leading)
            asm.RTS(),

            "CLEAR",
            # Write two blank characters at $7D3F to clear stale data
            asm.LDA(0xff, asm.IMM8),           # blank tile
            asm.STA(0xf8, asm.DIR),
            asm.STA(0xf9, asm.DIR),
            asm.LDX(0x7d3f, asm.IMM16),
            asm.JSR(0x04b6, asm.ABS),
            asm.RTS(),
        ]

        space = Write(Bank.C3, src, "limited inventory: draw pack qty value")
        qty_value_addr = space.start_address

        # Replace JMP target at BCAB (opcode $4C at BCAB, address at BCAC-BCAD)
        space = Reserve(0x3bcac, 0x3bcad, "shop buy menu draw qty value hook")
        space.write((qty_value_addr & 0xffff).to_bytes(2, "little"))
