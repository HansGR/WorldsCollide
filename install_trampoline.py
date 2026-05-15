"""Install the FF6 default-config trampoline into a ROM.

`ff6_config.py` only edits the immediate byte baked into a pair of
config-default subroutines.  In a vanilla FF6 ROM those subroutines
don't exist -- the boot code at file offset 0x0370C2 zeros $1D54 and
$1D4E in place with two ``STZ ABS`` instructions and provides no way
to override the defaults.

This script replaces those 6 bytes with two ``JSR ABS`` calls into a
pair of 6-byte trampoline subroutines that `ff6_config` can later
patch.

Default placement is at file offset 0x03F091 (SNES $C3/F091), which
the published FF6 ROM map lists as the start of a 3951-byte unused
region.  The boot code at $C3/70C2 is in the same bank, so the
16-bit JSR ABS reaches the trampoline.

WARNING: if you maintain your own FF6 hacking project, install the
trampoline as part of that project's build using its own free-space
allocator -- relying on this script can collide with code that other
patches also write into the "unused" region.
"""

import argparse
import sys

from config.rom import ROM
from config import config as cfg


# ---- ROM layout constants -------------------------------------------

BOOT_JSR_SITE = cfg.CONFIG_TRAMPOLINE_JSR        # 0x0370C2

# Bank C3 in the file (WC's HiROM-style mapping: SNES = file + 0xC00000).
# The boot code is at file 0x370C2 == SNES $C3/70C2, so the trampoline
# must live in the same bank for the 16-bit JSR ABS to reach it.
BANK_C3_FILE_START = 0x30000
BANK_C3_FILE_END   = 0x40000   # exclusive

DEFAULT_TRAMPOLINE_ADDR = 0x03F091
TRAMPOLINE_SIZE = 12  # two 6-byte subroutines

STZ_OPCODE = 0x9C
JSR_OPCODE = 0x20


# ---- Trampoline byte builders ---------------------------------------

def build_subroutines():
    """Return the 12 trampoline bytes: two LDA/STA/RTS subroutines.

    ff6_config patches the second byte of each subroutine (the LDA
    immediate operand) to set the default value of Config2 / Config3.
    """
    return [
        # Config2 (writes $1D54)
        0xA9, 0x00,        # LDA #$00
        0x8D, 0x54, 0x1D,  # STA $1D54
        0x60,              # RTS
        # Config3 (writes $1D4E)
        0xA9, 0x00,        # LDA #$00
        0x8D, 0x4E, 0x1D,  # STA $1D4E
        0x60,              # RTS
    ]


def build_jsr_pair(snes_low_addr):
    """Return the 6 bytes that replace the two STZ instructions.

    ``snes_low_addr`` is the low 16 bits of the SNES address of the
    Config2 subroutine; the Config3 subroutine lives 6 bytes later.
    """
    sub2 = snes_low_addr & 0xFFFF
    sub3 = (snes_low_addr + 6) & 0xFFFF
    return [
        JSR_OPCODE, sub2 & 0xFF, (sub2 >> 8) & 0xFF,
        JSR_OPCODE, sub3 & 0xFF, (sub3 >> 8) & 0xFF,
    ]


# ---- CLI -------------------------------------------------------------

def parse_address(s):
    """Accept a hex address as ``0x3F091``, ``3F091``, or ``$C3F091``.

    SNES-style addresses (``0xC00000``..``0xFFFFFF``) are converted to
    file offsets by subtracting ``0xC00000``.
    """
    raw = s.strip().lstrip("$")
    if raw.lower().startswith("0x"):
        raw = raw[2:]
    try:
        v = int(raw, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(f"address must be hex, got {s!r}")
    if 0xC00000 <= v <= 0xFFFFFF:
        v -= 0xC00000
    return v


def _default_output_path(input_path):
    if input_path.endswith(".smc"):
        return input_path[:-4] + "_tramp.smc"
    return input_path + "_tramp.smc"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install the FF6 default-config trampoline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If you maintain your own FF6 hacking project, install the\n"
            "trampoline as part of that project's build, not via this\n"
            "script -- the default free-space region may also be used\n"
            "by other patches applied to the same ROM."
        ),
        allow_abbrev=False,
    )
    parser.add_argument("-i", "--input", required=True, metavar="FILE",
                        help="Input .smc ROM")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="Output .smc ROM (default: <input>_tramp.smc)")
    parser.add_argument("--address", type=parse_address, default=None,
                        metavar="HEX",
                        help=("File offset (or SNES $C3XXXX) for the 12-byte "
                              "trampoline. Must be in bank $C3 "
                              f"(file 0x{BANK_C3_FILE_START:05X}.."
                              f"0x{BANK_C3_FILE_END - TRAMPOLINE_SIZE:05X}). "
                              f"Default: 0x{DEFAULT_TRAMPOLINE_ADDR:05X}."))
    parser.add_argument("--force", action="store_true",
                        help="Overwrite an existing trampoline.")
    args = parser.parse_args(argv)

    target = args.address if args.address is not None else DEFAULT_TRAMPOLINE_ADDR
    if not (BANK_C3_FILE_START <= target <= BANK_C3_FILE_END - TRAMPOLINE_SIZE):
        sys.exit(
            f"error: trampoline address 0x{target:05X} is not in bank $C3 "
            f"(file 0x{BANK_C3_FILE_START:05X}.."
            f"0x{BANK_C3_FILE_END - TRAMPOLINE_SIZE:05X}); "
            "a 16-bit JSR ABS cannot reach across banks."
        )

    rom = ROM(args.input)

    boot_byte = rom.get_byte(BOOT_JSR_SITE)
    if boot_byte == JSR_OPCODE:
        if not args.force:
            sys.exit(
                "error: a JSR trampoline is already installed at $03/70C2. "
                "Re-run with --force to overwrite, or use ff6_config.py "
                "directly on this ROM."
            )
        print("note: trampoline already present; overwriting (--force).")
    elif boot_byte != STZ_OPCODE:
        print(
            f"WARNING: byte at file 0x{BOOT_JSR_SITE:05X} is 0x{boot_byte:02X}, "
            f"expected STZ (0x{STZ_OPCODE:02X}) or JSR (0x{JSR_OPCODE:02X}). "
            "This ROM may have other patches that this install will clobber.",
            file=sys.stderr,
        )

    snes_low = target & 0xFFFF
    sub_bytes = build_subroutines()
    jsr_bytes = build_jsr_pair(snes_low)

    print(
        f"WARNING: writing 12 bytes at file 0x{target:05X} (SNES $C3/{snes_low:04X}).\n"
        "The FF6 ROM map lists this region as unused, but any other patch\n"
        "applied to this ROM that also writes here will be clobbered. If\n"
        "you're maintaining an FF6 project, install the trampoline as part\n"
        "of your own build instead of using this script.",
        file=sys.stderr,
    )
    print()
    print("Installing trampoline:")
    print(f"  Config2 sub  @ file 0x{target:05X}: "
          f"{' '.join(f'{b:02X}' for b in sub_bytes[:6])}")
    print(f"  Config3 sub  @ file 0x{target + 6:05X}: "
          f"{' '.join(f'{b:02X}' for b in sub_bytes[6:])}")
    print(f"  JSR pair     @ file 0x{BOOT_JSR_SITE:05X}: "
          f"{' '.join(f'{b:02X}' for b in jsr_bytes)}")

    rom.set_bytes(target, sub_bytes)
    rom.set_bytes(BOOT_JSR_SITE, jsr_bytes)

    output_path = args.output or _default_output_path(args.input)
    rom.write(output_path)
    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
