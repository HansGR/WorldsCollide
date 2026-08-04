from memory.space import Bank, Reserve, Write
import instruction.asm as asm
import instruction.c2 as c2
import args

from battle.check_dragon_boss import CheckDragonBoss
from battle.check_objectives import CheckObjectives

class _EndChecks:
    def __init__(self):
        src = [
            # replaced code
            asm.JSR(0x4936, asm.ABS),   # copy battle data to sram, update characters/enemies, ...
        ]

        if args.no_saves == 'lite':
            # -nosaves lite: the battle-start hook stashed the SRAM validity
            # markers and zeroed them (menus/save.py). Every battle end passes
            # through here, so restoring the stash for any outcome except
            # annihilation covers wins, fled battles, and scripted no-reward
            # battles in one place. A file that was invalid before the battle
            # stays invalid (zeros were stashed), so an unsaved game never
            # gains a loadable file; only a reset mid-battle or a party wipe
            # leaves the markers corrupted.
            from menus.save import SaveMenu
            src += [
                asm.LDA(0x01, asm.IMM8),
                asm.BIT(0x3ebc, asm.ABS),           # was party annihilated?
                asm.BNE("SKIP_MARKER_RESTORE"),     # wiped: leave markers corrupted
                asm.A16(),
            ]
            for marker, stash in zip(SaveMenu.SRAM_MARKERS, SaveMenu.SRAM_MARKER_STASH):
                src += [
                    asm.LDA(stash, asm.LNG),
                    asm.STA(marker, asm.LNG),
                ]
            src += [
                asm.A8(),
                "SKIP_MARKER_RESTORE",
            ]

        src += [
            asm.LDA(0x01, asm.IMM8),
            asm.BIT(0x3ebc, asm.ABS),   # was party annihilated?
            asm.BNE("AFTER_CHECKS"),    # if annihilated, skip checks

            CheckDragonBoss(),
            CheckObjectives(),

            "AFTER_CHECKS",
            asm.RTS(),
        ]
        space = Write(Bank.C2, src, "battle end checks")
        end_checks = space.start_address

        space = Reserve(0x2488f, 0x24891, "call battle end checks", asm.NOP())
        space.write(
            asm.JSR(end_checks, asm.ABS),
        )
end_checks = _EndChecks()
