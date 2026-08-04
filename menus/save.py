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

    # Every battle must be won, not merely survived. The game validates SRAM by
    # comparing the four marker words at $30:7FF8/FFA/FFC/FFE against the magic
    # value $E41B (checker C3/7023, writer C3/7083 -- saving rewrites them). We
    # corrupt the markers the moment a battle begins and rewrite them only when
    # the battle ends in victory, so resetting mid-battle (or after fleeing,
    # until the next save) leaves no loadable file.
    SRAM_MARKER_MAGIC = 0xe41b
    SRAM_MARKERS = [0x307ff8, 0x307ffa, 0x307ffc, 0x307ffe]

    def corrupt_save_on_battle_start(self):
        # battle program entry C2/000C sets up and calls JSR $261E at C2/0013;
        # corrupt the markers first, then tail-call the displaced init
        src = [
            asm.PHP(),
            asm.A16(),
            asm.LDA(0x0000, asm.IMM16),
        ]
        for marker in self.SRAM_MARKERS:
            src.append(asm.STA(marker, asm.LNG))
        src += [
            asm.PLP(),
            asm.JMP(0x261e, asm.ABS),
        ]
        space = Write(Bank.C2, src, "ironmog lite corrupt save markers on battle start")
        corrupt_addr = space.start_address

        space = Reserve(0x20013, 0x20015, "ironmog lite battle start hook", asm.NOP())
        space.write(asm.JSR(corrupt_addr, asm.ABS))

    def restore_save_on_battle_victory(self):
        # C2/488C calls the end-of-battle victory rewards routine (JSR $5D57);
        # the battle-end dispatcher only takes this path for a won battle, so
        # rewriting the markers here is exactly "proved you beat the battle".
        # a fled battle leaves the markers corrupted until the next save (the
        # save routine rewrites them)
        src = [
            asm.JSR(0x5d57, asm.ABS),   # displaced: victory rewards
            asm.PHP(),
            asm.A16(),
            asm.LDA(self.SRAM_MARKER_MAGIC, asm.IMM16),
        ]
        for marker in self.SRAM_MARKERS:
            src.append(asm.STA(marker, asm.LNG))
        src += [
            asm.PLP(),
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "ironmog lite restore save markers on battle victory")
        restore_addr = space.start_address

        space = Reserve(0x2488c, 0x2488e, "ironmog lite battle victory hook", asm.NOP())
        space.write(asm.JSR(restore_addr, asm.ABS))

    def mod(self):
        if args.no_saves == 'lite':
            self.save_and_quit()
            self.corrupt_save_on_battle_start()
            self.restore_save_on_battle_victory()
