"""Command-line entry point: apply default-config overrides to a ROM.

Usage:
    python ff6_config.py -i ff6.smc [options]
    python ff6_config.py -i ff6.smc --config ff6config.json
"""

import argparse
import base64
import json
import shlex
import sys

from config import config as cfg
from config import window_graphics as wg
from config.rom import ROM


class ConfigError(Exception):
    """Invalid input while applying a config to an in-memory ROM.

    Library callers (the web service) catch this and turn it into a 400 so a
    bad upload never crashes the process; the CLI catches it and turns it into
    a ``sys.exit`` message.
    """


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


def _parse_player2(s):
    """Parse a subset of battle slots {1,2,3,4} into a 4-bit mask.

    Accepts the digits 1..4 in any order, optionally separated by commas
    or spaces (e.g. ``"13"``, ``"1,3"``).  Each listed slot N sets bit
    N-1, matching the in-game submenu's ``----4321`` layout in $1D4F
    ("if on, player 2 controls that character").  An empty string means
    no slots (player 1 controls everyone).
    """
    mask = 0
    seen = set()
    for ch in s:
        if ch in ", ":
            continue
        if ch not in "1234":
            raise argparse.ArgumentTypeError(
                f"player-2 slots must be a subset of {{1,2,3,4}}, got {s!r}")
        n = int(ch)
        if n in seen:
            raise argparse.ArgumentTypeError(f"slot {n} listed twice in {s!r}")
        seen.add(n)
        mask |= 1 << (n - 1)
    return mask


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
    "Cursor", "Reequip", "SpellOrder", "Controller2", "Player2Controls",
    "Font", "Wallpaper",
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
    p.add_argument("-ctrl","--controller",  dest="Controller2",
                   type=_bool_choice("multiple", "single"),
                   help="single | multiple  (default: single)")
    p.add_argument("-p2",  "--player2",      dest="Player2Controls",
                   type=_parse_player2,
                   help="battle slots player 2 controls: subset of 1,2,3,4 "
                        "(e.g. 13 or 1,3). Requires --controller multiple.")
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
    p.add_argument("--config", dest="Config", metavar="FILE",
                   help="JSON config bundle produced by the web designer's "
                        "'Download configuration' button.  Contains a "
                        "flagstring + (optional) custom graphics for any of "
                        "the 8 window slots.  When given, the embedded "
                        "flagstring is parsed first, then any CLI flags "
                        "the user explicitly passed override on top, then "
                        "graphics blobs are applied last.")
    return p


def _default_output_path(input_path):
    if input_path.endswith(".smc"):
        return input_path[:-4] + "_config.smc"
    return input_path + "_config.smc"


# ---- reusable, file-free patching core ------------------------------
#
# These functions never touch the filesystem, so the web service can patch
# an uploaded ROM entirely in memory and hand the bytes straight back without
# ever storing a copy.  The CLI (``main``) layers file I/O on top of them.

def _graphics_blobs_from_config(cfg_data):
    """Decode a config dict's ``graphics`` map into ``[(window, blob), ...]``.

    Each value is base64 of a 928-byte (graphics + palette) blob.  Raises
    ConfigError on a bad window number, bad base64, or wrong-size blob.
    """
    expected = wg.WINDOW_GRAPHICS_SIZE + wg.WINDOW_PALETTE_FULL_SIZE
    blobs = []
    for n_str, b64 in (cfg_data.get("graphics") or {}).items():
        try:
            n = int(n_str)
        except (TypeError, ValueError):
            raise ConfigError(f"bad window number {n_str!r}")
        if not 1 <= n <= 8:
            raise ConfigError(f"bad window number {n}")
        try:
            blob = base64.b64decode(b64, validate=True)
        except (ValueError, TypeError) as e:
            raise ConfigError(f"window {n}: invalid base64 ({e})")
        if len(blob) != expected:
            raise ConfigError(
                f"window {n} blob is {len(blob)} bytes, expected {expected}")
        blobs.append((n, blob))
    return blobs


def apply_config(rom, args, graphics_blobs=()):
    """Apply a parsed argparse namespace + graphics blobs to an in-memory ROM.

    Mutates ``rom`` in place and returns it.  Raises ConfigError on any
    invalid input (missing trampoline, bad palette, player-2 without
    ``multiple``, duplicate window image, ...).  Touches no files.
    """
    config_set = {
        name: getattr(args, name)
        for name in CLI_OPTIONS
        if getattr(args, name) is not None
    }

    # Player-2 assignments only make sense in "multiple" controller mode --
    # the in-game submenu they map to is unreachable otherwise.
    if config_set.get("Player2Controls") and not config_set.get("Controller2"):
        raise ConfigError("-p2/--player2 requires -ctrl/--controller multiple")

    if not cfg.is_trampoline_installed(rom):
        raise ConfigError(
            "ROM does not have the default-config trampoline installed at "
            "$03/70C2. Patch the ROM with Worlds Collide first (or run "
            "install_trampoline.py on a vanilla ROM).")

    try:
        cfg.set_config(rom, config_set)
    except ValueError as e:
        raise ConfigError(str(e))

    seen = set()
    for n, blob in graphics_blobs:
        if n in seen:
            raise ConfigError(f"window {n} graphics specified twice")
        seen.add(n)
        _apply_window_image_bytes(rom, n, blob)
    return rom


def patch_rom_bytes(rom_bytes, config=None, extra_flags=None):
    """Patch an FF6 ROM held in memory and return the patched bytes.

    ``config`` is a parsed ``ff6config.json`` dict (``version`` / ``flags`` /
    ``graphics``) as produced by the web app, or None.  ``extra_flags`` is an
    optional list of additional CLI flag tokens applied on top (they win over
    the config's embedded flags, matching the CLI's ``--config`` behaviour).

    Never reads or writes the filesystem.  Raises ConfigError on bad input.
    """
    flag_argv = []
    graphics_blobs = []
    if config is not None:
        if config.get("version") != 1:
            raise ConfigError(
                f"unsupported config version {config.get('version')!r}")
        flag_argv += shlex.split(config.get("flags", "") or "")
        graphics_blobs = _graphics_blobs_from_config(config)
    if extra_flags:
        flag_argv += list(extra_flags)
    try:
        # "-i" is required by the parser but unused for in-memory patching.
        args = build_parser().parse_args(["-i", "<memory>", *flag_argv])
    except SystemExit:
        raise ConfigError("invalid configuration flags")
    rom = ROM(data=rom_bytes)
    apply_config(rom, args, graphics_blobs)
    return rom.get_data()


def main(argv=None):
    raw_argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(raw_argv)

    # If the user passed --config, merge in the embedded flagstring.
    # Explicit CLI flags win over the embedded ones, so we re-parse with
    # the embedded flags PREPENDED (later args override earlier ones in
    # argparse for the same option).
    graphics_blobs = []  # list of (window_num, 928-byte bytes) to apply
    if args.Config:
        cfg_data = _load_json_config(args.Config)
        embedded = shlex.split(cfg_data.get("flags", "") or "")
        if embedded:
            # -i / -o stay from the CLI; everything else comes from a
            # reparse with embedded flags ahead of the CLI flags.
            re_argv = ["-i", args.input]
            if args.output is not None:
                re_argv += ["-o", args.output]
            re_argv += embedded + raw_argv
            args = build_parser().parse_args(re_argv)
        # Pull graphics out of the JSON.
        try:
            graphics_blobs = _graphics_blobs_from_config(cfg_data)
        except ConfigError as e:
            sys.exit(f"error: {args.Config}: {e}")

    output_path = args.output or _default_output_path(args.input)

    rom = ROM(args.input)
    try:
        apply_config(rom, args, graphics_blobs)
    except ConfigError as e:
        sys.exit(f"error: {e}")

    # --config graphics are applied above; explicit --window-image files on
    # the CLI come last so they override whatever the JSON had for that slot.
    if args.WindowImage:
        seen = set()
        for n, path in args.WindowImage:
            if n in seen:
                sys.exit(f"error: --window-image specified twice for window {n}")
            seen.add(n)
            _apply_window_image(rom, n, path)

    rom.write(output_path)


def _load_json_config(path):
    try:
        with open(path) as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"error: --config {path}: {e}")
    if d.get("version") != 1:
        sys.exit(f"error: {path}: unsupported config version {d.get('version')}")
    return d


def _apply_window_image_bytes(rom, n, blob):
    expected = wg.WINDOW_GRAPHICS_SIZE + wg.WINDOW_PALETTE_FULL_SIZE
    if len(blob) != expected:
        raise ConfigError(
            f"window {n} blob: expected {expected} bytes "
            f"({wg.WINDOW_GRAPHICS_SIZE} graphics + "
            f"{wg.WINDOW_PALETTE_FULL_SIZE} palette), got {len(blob)}")
    wg.set_window_graphics(rom, n, list(blob[: wg.WINDOW_GRAPHICS_SIZE]))
    rom.set_bytes(wg.palette_addr(n), list(blob[wg.WINDOW_GRAPHICS_SIZE :]))


def _apply_window_image(rom, n, path):
    """Read a 928-byte graphics+palette blob from ``path`` and patch window ``n``."""
    with open(path, "rb") as f:
        try:
            _apply_window_image_bytes(rom, n, f.read())
        except ConfigError as e:
            sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
