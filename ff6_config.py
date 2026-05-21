"""Command-line entry point: apply default-config overrides to a ROM.

Usage:
    python ff6_config.py -i ff6.smc [options]
"""

import argparse
import sys

from config import config as cfg
from config import window_graphics as wg
from config.rom import ROM


# ---- argparse value parsers -----------------------------------------

def _int_in_range(lo, hi):
    def parse(s):
        try:
            i = int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"expected integer {lo}..{hi}, got {s!r}")
        if not lo <= i <= hi:
            raise argparse.ArgumentTypeError(f"expected {lo}..{hi}, got {i}")
        return i
    return parse


def _bool_choice(true_label, false_label):
    """Parse a boolean from a small set of common aliases.

    The two labels are the canonical names; '1' / '0' / 'true' / 'false'
    also map to True / False respectively.
    """
    true_set = {true_label.lower(), "1", "true"}
    false_set = {false_label.lower(), "0", "false"}
    def parse(s):
        v = s.lower()
        if v in true_set:
            return True
        if v in false_set:
            return False
        raise argparse.ArgumentTypeError(
            f"expected {true_label!r} or {false_label!r}, got {s!r}")
    return parse


def _parse_rgb(s):
    """Parse ``R,G,B`` (each 0..31) into ``[R, G, B]``."""
    parts = s.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"expected R,G,B (each 0..31), got {s!r}")
    rgb = []
    for p in parts:
        try:
            v = int(p)
        except ValueError:
            raise argparse.ArgumentTypeError(f"non-integer component {p!r} in {s!r}")
        if not 0 <= v <= 31:
            raise argparse.ArgumentTypeError(f"component {v} out of range 0..31 in {s!r}")
        rgb.append(v)
    return rgb


def _parse_window_image(s):
    """Parse ``N:path/to/file.bin`` into ``(window_index, path)``.

    ``N`` is 1..8 (target window slot to overwrite).  The file is read
    later by ``main`` -- here we only validate the syntax and existence.
    """
    if ":" not in s:
        raise argparse.ArgumentTypeError(
            f"expected 'N:path' (N=1..8), got {s!r}")
    n_str, path = s.split(":", 1)
    try:
        n = int(n_str)
    except ValueError:
        raise argparse.ArgumentTypeError(f"bad window index {n_str!r}")
    if not 1 <= n <= 8:
        raise argparse.ArgumentTypeError(f"window index {n} out of range 1..8")
    return (n, path)


def _parse_window_palette(s):
    """Parse ``slot=R,G,B;slot=R,G,B`` into a ``{slot: [R, G, B]}`` dict.

    Slots are 1..7.  E.g. ``1=25,28,28;4=10,10,10`` sets slots 1 and 4
    and leaves the others alone.
    """
    out = {}
    for entry in s.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        if "=" not in entry:
            raise argparse.ArgumentTypeError(
                f"window palette entry {entry!r} missing '=' (expected slot=R,G,B)")
        slot_str, rgb_str = entry.split("=", 1)
        try:
            slot = int(slot_str)
        except ValueError:
            raise argparse.ArgumentTypeError(f"bad slot {slot_str!r}")
        if not 1 <= slot <= 7:
            raise argparse.ArgumentTypeError(f"slot {slot} out of range 1..7")
        if slot in out:
            raise argparse.ArgumentTypeError(f"slot {slot} specified twice in {s!r}")
        out[slot] = _parse_rgb(rgb_str)
    if not out:
        raise argparse.ArgumentTypeError(f"no palette entries in {s!r}")
    return out


# ---- CLI -------------------------------------------------------------

# Dest names match Field names in config.CONFIG_BYTES so we can pass the
# argparse namespace straight through to set_config.
CLI_OPTIONS = [
    "BatMode", "BatSpeed", "MsgSpeed", "Command", "Gauge", "Sound",
    "Cursor", "Reequip", "SpellOrder", "Font", "Wallpaper",
    *(f"Window{i}" for i in range(1, 9)),
]


def build_parser():
    p = argparse.ArgumentParser(
        description="Set default config values in a patched FF6WC ROM.",
        allow_abbrev=False,
    )
    p.add_argument("-i", "--input", required=True, metavar="FILE",
                   help="Input .smc ROM (already WC-patched)")
    p.add_argument("-o", "--output", metavar="FILE",
                   help="Output .smc ROM (default: <input>_config.smc)")

    p.add_argument("-b",   "--bat-mode",    dest="BatMode",
                   type=_bool_choice("wait", "active"),
                   help="active | wait  (default: wait)")
    p.add_argument("-bs",  "--bat-speed",   dest="BatSpeed",
                   type=_int_in_range(1, 6),
                   help="1..6  (default: 3)")
    p.add_argument("-ms",  "--msg-speed",   dest="MsgSpeed",
                   type=_int_in_range(1, 6),
                   help="1..6  (default: 3)")
    p.add_argument("-com", "--command",     dest="Command",
                   type=_bool_choice("short", "window"),
                   help="window | short  (default: window)")
    p.add_argument("-g",   "--gauge",       dest="Gauge",
                   type=_bool_choice("off", "on"),
                   help="on | off  (default: on)")
    p.add_argument("-s",   "--sound",       dest="Sound",
                   type=_bool_choice("mono", "stereo"),
                   help="stereo | mono  (default: stereo)")
    p.add_argument("-c",   "--cursor",      dest="Cursor",
                   type=_bool_choice("memory", "reset"),
                   help="reset | memory  (default: reset)")
    p.add_argument("-r",   "--reequip",     dest="Reequip",
                   type=_bool_choice("empty", "optimum"),
                   help="optimum | empty  (default: optimum)")
    p.add_argument("-so",  "--spell-order", dest="SpellOrder",
                   type=_int_in_range(1, 6),
                   help="1..6  (default: 1)")
    p.add_argument("-f",   "--font",        dest="Font",
                   type=_parse_rgb,
                   help="font color as R,G,B (each 0..31)")
    p.add_argument("-w",   "--wallpaper",   dest="Wallpaper",
                   type=_int_in_range(1, 8),
                   help="1..8  (default: 1)")
    for i in range(1, 9):
        p.add_argument(f"-w{i}", f"--window{i}", dest=f"Window{i}",
                       type=_parse_window_palette,
                       help=f"window {i} palette: 'slot=R,G,B;...' (slot 1..7)")
    p.add_argument("--window-image", dest="WindowImage",
                   type=_parse_window_image, action="append", default=None,
                   metavar="N:FILE",
                   help="overwrite window N (1..8) with the 928-byte "
                        "graphics+palette blob in FILE (896 bytes of 4bpp "
                        "graphics followed by 32 bytes of BGR15 palette). "
                        "May be repeated for different windows.")
    return p


def _default_output_path(input_path):
    if input_path.endswith(".smc"):
        return input_path[:-4] + "_config.smc"
    return input_path + "_config.smc"


def main(argv=None):
    args = build_parser().parse_args(argv)

    output_path = args.output or _default_output_path(args.input)
    config_set = {
        name: getattr(args, name)
        for name in CLI_OPTIONS
        if getattr(args, name) is not None
    }

    rom = ROM(args.input)
    if not cfg.is_trampoline_installed(rom):
        sys.exit(
            f"error: {args.input} does not have the default-config trampoline "
            "installed at $03/70C2.\n"
            "Run `python3 install_trampoline.py -i <rom>` first, or apply a "
            "Worlds Collide patch."
        )
    cfg.set_config(rom, config_set)

    if args.WindowImage:
        seen = set()
        for n, path in args.WindowImage:
            if n in seen:
                sys.exit(f"error: --window-image specified twice for window {n}")
            seen.add(n)
            _apply_window_image(rom, n, path)

    rom.write(output_path)


def _apply_window_image(rom, n, path):
    """Read a 928-byte graphics+palette blob from ``path`` and patch window ``n``."""
    with open(path, "rb") as f:
        blob = f.read()
    expected = wg.WINDOW_GRAPHICS_SIZE + wg.WINDOW_PALETTE_FULL_SIZE
    if len(blob) != expected:
        sys.exit(
            f"error: {path}: expected {expected} bytes "
            f"({wg.WINDOW_GRAPHICS_SIZE} graphics + "
            f"{wg.WINDOW_PALETTE_FULL_SIZE} palette), got {len(blob)}")
    wg.set_window_graphics(rom, n, list(blob[: wg.WINDOW_GRAPHICS_SIZE]))
    rom.set_bytes(wg.palette_addr(n), list(blob[wg.WINDOW_GRAPHICS_SIZE :]))


if __name__ == "__main__":
    main()
