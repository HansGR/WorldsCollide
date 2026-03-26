from memory.space import Reserve, Bank, Write
import instruction.asm as asm
import args


def rgb_to_snes_bytes(rgb):
    """Convert RGB value [R, G, B] (each 0-31) to SNES 2-byte BGR format."""
    r, g, b = rgb
    # SNES colors are 15-bit BGR: 0bbbbbgg gggrrrrr
    color_value = (b << 10) | (g << 5) | r
    return [color_value & 0xff, (color_value >> 8) & 0xff]


class Config:
    def __init__(self):
        self.mod()

    def mod(self):
        # Thanks to DoctorDT for most of this code

        # Set default configuration options to the most popular:
        # Config1: Msg Speed = 1 (Fastest), Bat Speed = 6 (Slowest), Bat Mode = 1 (Wait)

        # Config 1, set by this code:
        #   C3/70B8:	A92A    	LDA #$2A       ; Bat.Mode, etc.
        # RAM $1D4D, one byte sets: cmmm wbbb (command set c, message spd mmm + 1, battle mode w, battle speed bbb + 1)
        space = Reserve(0x370b9, 0x370b9, "config 1 default")
        space.write(0x0D) # default: 0x2A

        # Moving default location for Config 2 and 3 to support command line re-configuration
        # Set default memory location for Config #2:
        src = [
            asm.LDA(0x00, asm.IMM8),                    # LDA #$00;
            asm.STA(0x1D54, asm.ABS),                   # STA $1D54;  # Config #2
            asm.RTS(),
            ]
        space = Write(Bank.C3, src, "Config #2 default value")

        # Update the JSR for Config default #2
        config2_loc = space.start_address
        space = Reserve(0x370c2, 0x370c4, "Config_2_default")  # 0x0370C2: ['20', PP, NN, '20', PP + 06, NN]])  # JSR #$CONF2; JSR #$CONF3
        space.write(
            asm.JSR(config2_loc, asm.ABS),
        )
        # Config 3, set by this code:
        #   C3/70C5:	9C4E1D  	STZ $1D4E      ; Wallpaper, etc.
        # RAM $1D4E, one byte sets: gcsr wwww (gauge g, cursor c, sound s, reequip r, wallpaper wwww (0-7))
        # Ruination mode uses wallpaper 2 (index 1), standard mode uses wallpaper 1 (index 0)
        config3_default = 0x01 if args.ruination_mode else 0x00
        src = [
            asm.LDA(config3_default, asm.IMM8),
            asm.STA(0x1D4E, asm.ABS),
            asm.RTS(),
        ]
        space = Write(Bank.C3, src, "Config_3_default")

        # Update the JSR for Config default #3
        config3_loc = space.start_address
        space = Reserve(0x370c5, 0x370c7, "Config_3_default")
        space.write(
            asm.JSR(config3_loc, asm.ABS),
        )

        # Fix: When "New Game" is selected from the load menu, the load menu init
        # (C3/160E) has already cleared the wallpaper bits in $1D4E to 0 (blue).
        # Patch the load menu's "New Game" handler (C3/2A12) to restore Config 3
        # and reload skin colors so the correct wallpaper is used.
        src = [
            asm.STZ(0x021F, asm.ABS),                   # original: Game's file = None
            asm.LDA(config3_default, asm.IMM8),
            asm.STA(0x1D4E, asm.ABS),                   # restore wallpaper default
            asm.JSR(0x6BBC, asm.ABS),                   # reset skin colors from ROM
            asm.RTS(),
        ]
        space = Write(Bank.C3, src, "load menu new game restore config 3")
        load_menu_new_game_fix = space.start_address

        space = Reserve(0x32a12, 0x32a14, "load menu new game config fix")
        space.write(
            asm.JSR(load_menu_new_game_fix, asm.ABS),
        )

        # Ruination mode: Set custom Window 2 colors (dark red theme)
        if args.ruination_mode:
            window2_colors = [
                [15, 11, 10],  # color 1
                [10, 6, 6],    # color 2
                [9, 5, 5],     # color 3
                [8, 4, 4],     # color 4
                [7, 3, 3],     # color 5
                [6, 2, 2],     # color 6
                [2, 0, 0],     # color 7
            ]
            window2_bytes = []
            for rgb in window2_colors:
                window2_bytes.extend(rgb_to_snes_bytes(rgb))
            # Window 2 palette colors are at ROM address 0x2d1c22 (14 bytes)
            space = Reserve(0x2d1c22, 0x2d1c2f, "ruination mode window 2 colors")
            space.write(*window2_bytes)
