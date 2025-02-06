from memory.space import Bank, START_ADDRESS_SNES, Reserve, Allocate, Write, Read
import instruction.asm as asm
import args

class SaveMenu:
    def __init__(self):
        self.mod()

    def save_and_quit(self):
        # Click on Save --> automatically save in slot 1
        src = [
            asm.LDA(0x01, asm.IMM8),    #     LDA #$01        ; Save slot 1
            asm.STA(0x021f, asm.ABS),   #     STA $021F       ; Set game's file number
            asm.JSR(0x0eb9, asm.ABS),   #     JSR $0EB9       ; Play save sound effect
            asm.JSR(0x25e8, asm.ABS),   #     JSR $25DF       ; Save game data, skipping "restore data from SRAM"
            asm.RTS(),
        ]
        space = Write(Bank.C3, src, "edited save capability")
        mod_save_addr = space.start_address

        space = Reserve(0x32eaf, 0x32ebe, "Edit save behavior", asm.NOP())
        space.write(
            asm.JMP(mod_save_addr, asm.ABS)
        )

        # Trash the save game data if the player loses a battle.
        # In the battle program at 0x25fcd
        #   C25FCA:  PHA            ;Put on stack
        #   C25FCB:  LDA #$01
        #   C25FCD:  TSB $3EBC      ;set event bit indicating battle ended in loss
        src = [
            asm.TSB(0x3ebc, asm.ABS),    # complete previous action: indicate battle ended in loss
            asm.LDA(0x00, asm.IMM8),
            asm.STA(0x307ff8, asm.LNG),  # overwrite marker file 1
            asm.STA(0x307ffa, asm.LNG),  # overwrite marker file 2
            asm.STA(0x307ffc, asm.LNG),  # overwrite marker file 3
            asm.STA(0x307ffe, asm.LNG),  # overwrite marker file 4
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "Junk save data")
        clear_data_addr = space.start_address

        space = Reserve(0x25fcd, 0x25fcf, "Annihilation toss save data", asm.NOP())
        space.write(asm.JSR(clear_data_addr, asm.ABS))


    def mod(self):
        if args.ruination_mode:
            self.save_and_quit()
