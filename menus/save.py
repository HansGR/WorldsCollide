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

    # Resetting mid-battle must not be an escape hatch. The game validates SRAM
    # by comparing the four marker words at $30:7FF8/FFA/FFC/FFE against the
    # magic value $E41B (checker C3/7023, writer C3/7083 -- the save routine
    # C3/151D ends by jumping to the writer, so every save revalidates). When a
    # battle begins we stash the markers at $30:7FE0-$30:7FE7 (unused SRAM) and
    # zero them; the battle-end hook in battle/end_checks.py restores the stash
    # for any outcome except annihilation. Restoring the stash rather than the
    # magic keeps an unsaved game's markers invalid (zeros in, zeros out), and
    # makes fleeing or a scripted no-reward battle safe: only a reset while the
    # battle is unresolved (or a party wipe) leaves no loadable file.
    SRAM_MARKERS = [0x307ff8, 0x307ffa, 0x307ffc, 0x307ffe]
    SRAM_MARKER_STASH = [0x307fe0, 0x307fe2, 0x307fe4, 0x307fe6]

    def corrupt_save_on_battle_start(self):
        # battle program entry C2/000C sets up and calls JSR $261E at C2/0013;
        # stash and zero the markers first, then tail-call the displaced init
        src = [
            asm.PHP(),
            asm.A16(),
        ]
        for marker, stash in zip(self.SRAM_MARKERS, self.SRAM_MARKER_STASH):
            src += [
                asm.LDA(marker, asm.LNG),
                asm.STA(stash, asm.LNG),
            ]
        src.append(asm.LDA(0x0000, asm.IMM16))
        for marker in self.SRAM_MARKERS:
            src.append(asm.STA(marker, asm.LNG))
        src += [
            asm.PLP(),
            asm.JMP(0x261e, asm.ABS),
        ]
        space = Write(Bank.C2, src, "ironmog lite stash and corrupt save markers on battle start")
        corrupt_addr = space.start_address

        space = Reserve(0x20013, 0x20015, "ironmog lite battle start hook", asm.NOP())
        space.write(asm.JSR(corrupt_addr, asm.ABS))

    def mod(self):
        if args.no_saves == 'lite':
            self.save_and_quit()
            self.corrupt_save_on_battle_start()
