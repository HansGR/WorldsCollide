"""Smoke tests for config/config.py and the ff6_config CLI parsers.

Run as:
    python tests/test_config.py
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config as cfg
import ff6_config
import install_trampoline as inst


# ---- RGB / bit math --------------------------------------------------

def test_rgb_round_trip():
    for rgb in [[0, 0, 0], [31, 31, 31], [25, 28, 28], [17, 12, 4], [1, 0, 31]]:
        got = cfg.bytes2rgb(cfg.rgb2bytes(rgb))
        assert got == rgb, f"round-trip {rgb} -> {got}"


def test_rgb2bytes_known_values():
    # White: R=G=B=31 -> 0_11111_11111_11111 = 0x7FFF -> [0xFF, 0x7F]
    assert cfg.rgb2bytes([31, 31, 31]) == [0xFF, 0x7F]
    # Pure red: 0x001F -> [0x1F, 0x00]
    assert cfg.rgb2bytes([31, 0, 0]) == [0x1F, 0x00]
    # Pure green: 0x03E0 -> [0xE0, 0x03]
    assert cfg.rgb2bytes([0, 31, 0]) == [0xE0, 0x03]
    # Pure blue: 0x7C00 -> [0x00, 0x7C]
    assert cfg.rgb2bytes([0, 0, 31]) == [0x00, 0x7C]


# ---- Config byte packing --------------------------------------------

def test_pack_config1_defaults():
    # Command=False(0), MsgSpeed=3->010, BatMode=True(1), BatSpeed=3->010
    # => 0_010_1_010 = 0b00101010
    byte = cfg.pack_config_byte(cfg.CONFIG_BYTES["Config1"], {})
    assert byte == 0b00101010, f"{byte:#04x}"


def test_pack_config1_overrides():
    # Command=True, MsgSpeed=6->101, BatMode=False, BatSpeed=1->000
    # => 1_101_0_000 = 0b11010000
    byte = cfg.pack_config_byte(
        cfg.CONFIG_BYTES["Config1"],
        {"Command": True, "MsgSpeed": 6, "BatMode": False, "BatSpeed": 1},
    )
    assert byte == 0b11010000, f"{byte:#04x}"


def test_pack_config2_defaults():
    # Controller2=0, CustomButtons=0, FontWPS=1->000, SpellOrder=1->000 => 0
    assert cfg.pack_config_byte(cfg.CONFIG_BYTES["Config2"], {}) == 0


def test_pack_config4_player2():
    # Default: no slots -> 0
    assert cfg.pack_config_byte(cfg.CONFIG_BYTES["Config4"], {}) == 0
    # Slots 1 and 3 -> ----0101 = 0x05 (upper nibble stays clear)
    byte = cfg.pack_config_byte(cfg.CONFIG_BYTES["Config4"],
                                {"Player2Controls": 0b0101})
    assert byte == 0b0101, f"{byte:#04x}"
    # All four slots -> ----1111 = 0x0F
    byte = cfg.pack_config_byte(cfg.CONFIG_BYTES["Config4"],
                                {"Player2Controls": 0b1111})
    assert byte == 0x0F, f"{byte:#04x}"


def test_pack_config3_all_set():
    byte = cfg.pack_config_byte(
        cfg.CONFIG_BYTES["Config3"],
        {"Gauge": True, "Cursor": True, "Sound": True, "Reequip": True, "Wallpaper": 8},
    )
    # 1_1_1_1_0111 = 0b11110111
    assert byte == 0b11110111, f"{byte:#04x}"


# ---- CLI parsing -----------------------------------------------------

def test_cli_parses_basic_flags():
    parser = ff6_config.build_parser()
    ns = parser.parse_args([
        "-i", "rom.smc",
        "--bat-speed", "5",
        "--msg-speed", "2",
        "--bat-mode", "active",
        "--command", "short",
        "--gauge", "off",
        "--controller", "multiple",
        "--font", "31,0,0",
        "-w3", "1=10,10,10;4=20,20,20",
    ])
    assert ns.input == "rom.smc"
    assert ns.BatSpeed == 5
    assert ns.MsgSpeed == 2
    assert ns.BatMode is False
    assert ns.Command is True
    assert ns.Gauge is True
    assert ns.Controller2 is True
    assert ns.Font == [31, 0, 0]
    assert ns.Window3 == {1: [10, 10, 10], 4: [20, 20, 20]}
    # Unset options come through as None and get filtered out
    assert ns.Window1 is None


def test_cli_rejects_out_of_range_int():
    parser = ff6_config.build_parser()
    try:
        parser.parse_args(["-i", "rom.smc", "--bat-speed", "7"])
    except SystemExit:
        return  # argparse exits on type-check failure -- good
    raise AssertionError("expected SystemExit for out-of-range bat-speed")


def test_cli_rejects_bad_bool():
    parser = ff6_config.build_parser()
    try:
        parser.parse_args(["-i", "rom.smc", "--bat-mode", "kinda"])
    except SystemExit:
        return
    raise AssertionError("expected SystemExit for bad bat-mode")


def test_cli_rejects_bad_rgb():
    parser = ff6_config.build_parser()
    for bad in ["32,0,0", "1,2", "a,b,c", "1,2,3,4"]:
        try:
            parser.parse_args(["-i", "rom.smc", "--font", bad])
        except SystemExit:
            continue
        raise AssertionError(f"expected SystemExit for --font {bad}")


# ---- Window-image flag ----------------------------------------------

def test_cli_parses_window_image_flag():
    parser = ff6_config.build_parser()
    ns = parser.parse_args([
        "-i", "rom.smc",
        "--window-image", "3:gfx3.bin",
        "--window-image", "8:gfx8.bin",
    ])
    assert ns.WindowImage == [(3, "gfx3.bin"), (8, "gfx8.bin")]


def test_cli_rejects_bad_window_image():
    parser = ff6_config.build_parser()
    for bad in ["9:foo.bin", "0:foo.bin", "foo.bin", "abc:foo.bin"]:
        try:
            parser.parse_args(["-i", "rom.smc", "--window-image", bad])
        except SystemExit:
            continue
        raise AssertionError(f"expected SystemExit for --window-image {bad}")


def test_apply_window_image_writes_both_regions(tmp_path=None):
    import io
    import os
    import tempfile

    # 928 bytes: 896 graphics + 32 palette (well-formed)
    blob = bytes(range(256)) * 4  # 1024 bytes
    blob = blob[:928]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tf:
        tf.write(blob)
        blob_path = tf.name

    try:
        # Fake ROM big enough to cover $2D/1C20 (W2 palette).
        class _FakeRom:
            def __init__(self):
                self.data = bytearray(0x2E0000)
            def get_bytes(self, addr, count):
                return list(self.data[addr : addr + count])
            def set_bytes(self, addr, values):
                self.data[addr : addr + len(values)] = bytes(values)
                return addr + len(values)

        rom = _FakeRom()
        ff6_config._apply_window_image(rom, 2, blob_path)

        # Graphics landed at W2's graphics base.
        from config import window_graphics as wg_mod
        assert bytes(rom.data[wg_mod.graphics_addr(2):
                              wg_mod.graphics_addr(2) + 896]) == blob[:896]
        # Palette landed at W2's palette base.
        assert bytes(rom.data[wg_mod.palette_addr(2):
                              wg_mod.palette_addr(2) + 32]) == blob[896:928]
    finally:
        os.unlink(blob_path)


# ---- JSON --config bundle -------------------------------------------

def test_load_json_config_rejects_unknown_version():
    import os
    import tempfile
    import json as _json
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tf:
        _json.dump({"version": 99, "flags": ""}, tf)
        path = tf.name
    try:
        try:
            ff6_config._load_json_config(path)
        except SystemExit:
            return
        raise AssertionError("expected SystemExit for unsupported version")
    finally:
        os.unlink(path)


def test_load_json_config_parses_v1():
    import os
    import tempfile
    import json as _json
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tf:
        _json.dump({
            "version": 1,
            "flags": "-bs 5 -ms 2",
            "graphics": {"3": "abc="},
        }, tf)
        path = tf.name
    try:
        d = ff6_config._load_json_config(path)
        assert d["version"] == 1
        assert d["flags"] == "-bs 5 -ms 2"
        assert "3" in d["graphics"]
    finally:
        os.unlink(path)


def test_main_with_config_file_applies_embedded_flags_and_graphics(tmp_path=None):
    """Build a tiny WC-style ROM, a config JSON, run main(), verify writes."""
    import os
    import base64
    import json as _json
    import tempfile
    import io
    import builtins

    # 928-byte blob: 896 of 0x55 + 32 of palette bytes
    blob = bytes([0x55] * 896 + [0x00, 0x38] * 16)
    config = {
        "version": 1,
        "flags": "-bs 5 -ms 2",
        "graphics": {"7": base64.b64encode(blob).decode("ascii")},
    }

    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "cfg.json")
        with open(cfg_path, "w") as f:
            _json.dump(config, f)

        # Fake ROM with the trampoline already installed.
        rom_bytes = bytearray(0x2E0000)
        rom_bytes[0x0370C2] = 0x20  # JSR
        rom_bytes[0x0370C5] = 0x20
        rom_bytes[0x0370C3] = 0x91  # Config2 sub address: $C3/F091 + 1
        rom_bytes[0x0370C4] = 0xF0
        rom_bytes[0x0370C6] = 0x97  # Config3 sub address: $C3/F097 + 1
        rom_bytes[0x0370C7] = 0xF0
        rom_in = os.path.join(td, "in.smc")
        with open(rom_in, "wb") as f:
            f.write(rom_bytes)
        rom_out = os.path.join(td, "out.smc")

        ff6_config.main(["-i", rom_in, "-o", rom_out, "--config", cfg_path])

        with open(rom_out, "rb") as f:
            out = f.read()

        # Config1: BatSpeed=5 (offset 5-1=4=100), MsgSpeed=2 (offset 1=001)
        # Defaults: Command=0, BatMode=1. Bits: 0_001_1_100 = 0x1C
        from config import config as _cfg
        c1 = out[_cfg.CONFIG1_ADDR]
        assert c1 == 0b00011100, f"Config1 = {c1:#04x}, expected 0x1C"

        # W7 graphics at file offset 0x2D0000 + 6*0x380 = 0x2D1500
        gfx_off = 0x2D0000 + 6 * 0x380
        assert out[gfx_off : gfx_off + 896] == blob[:896]
        # W7 palette at 0x2D1C00 + 6*0x20 = 0x2D1CC0
        pal_off = 0x2D1C00 + 6 * 0x20
        assert out[pal_off : pal_off + 32] == blob[896:]


def test_main_explicit_cli_flag_overrides_config_flag(tmp_path=None):
    """Explicit -bs 6 on the CLI should beat --config's -bs 5."""
    import os
    import json as _json
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "cfg.json")
        with open(cfg_path, "w") as f:
            _json.dump({"version": 1, "flags": "-bs 5"}, f)

        rom_bytes = bytearray(0x2E0000)
        rom_bytes[0x0370C2] = 0x20; rom_bytes[0x0370C5] = 0x20
        rom_bytes[0x0370C3] = 0x91; rom_bytes[0x0370C4] = 0xF0
        rom_bytes[0x0370C6] = 0x97; rom_bytes[0x0370C7] = 0xF0
        rom_in = os.path.join(td, "in.smc")
        with open(rom_in, "wb") as f:
            f.write(rom_bytes)
        rom_out = os.path.join(td, "out.smc")

        ff6_config.main(["-i", rom_in, "-o", rom_out, "--config", cfg_path, "-bs", "6"])

        with open(rom_out, "rb") as f:
            out = f.read()
        from config import config as _cfg
        c1 = out[_cfg.CONFIG1_ADDR]
        # BatSpeed=6 means offset 5=101.  Defaults for other fields:
        # Command=0, MsgSpeed=3->010, BatMode=1.  Bits: 0_010_1_101 = 0x2D
        assert c1 == 0b00101101, f"Config1 = {c1:#04x}, expected 0x2D"


def test_apply_window_image_rejects_wrong_size():
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tf:
        tf.write(b"\x00" * 100)
        bad_path = tf.name

    try:
        class _FakeRom:
            def __init__(self):
                self.data = bytearray(0x2E0000)
            def get_bytes(self, addr, count):
                return list(self.data[addr : addr + count])
            def set_bytes(self, addr, values):
                self.data[addr : addr + len(values)] = bytes(values)

        try:
            ff6_config._apply_window_image(_FakeRom(), 1, bad_path)
        except SystemExit:
            return
        raise AssertionError("expected SystemExit for wrong-size blob")
    finally:
        os.unlink(bad_path)


# ---- Default config address read ------------------------------------

class _FakeRom:
    def __init__(self, bytes_at):
        self._bytes_at = bytes_at
        self.writes = []

    def get_byte(self, addr):
        return self._bytes_at[addr]

    def get_bytes(self, addr, count):
        return list(self._bytes_at[addr:addr + count])

    def set_bytes(self, addr, values):
        self.writes.append((addr, list(values)))


def test_read_default_config_addr():
    # JSR operand at 0x0370C3 = little-endian (0x18, 0xFC) -> 0xFC18
    # Result should be 0x03FC18 + 1 = 0x03FC19
    rom_bytes = bytearray(0x040000)
    rom_bytes[0x0370C3] = 0x18
    rom_bytes[0x0370C4] = 0xFC
    rom = _FakeRom(rom_bytes)
    addr = cfg._read_default_config_addr(rom, 0x0370C3)
    assert addr == 0x03FC19, f"{addr:#08x}"


def test_set_config_writes_three_bytes():
    rom_bytes = bytearray(0x300000)
    # Plant valid JSR operands for Config2 and Config3
    rom_bytes[0x0370C3] = 0x00; rom_bytes[0x0370C4] = 0xFC  # -> 0x03FC01
    rom_bytes[0x0370C6] = 0x10; rom_bytes[0x0370C7] = 0xFC  # -> 0x03FC11
    rom = _FakeRom(rom_bytes)
    cfg.set_config(rom, {})
    written_addrs = {addr for addr, _ in rom.writes}
    assert cfg.CONFIG1_ADDR in written_addrs
    assert 0x03FC01 in written_addrs
    assert 0x03FC11 in written_addrs


def test_parse_player2_masks():
    assert ff6_config._parse_player2("") == 0
    assert ff6_config._parse_player2("1") == 0b0001
    assert ff6_config._parse_player2("13") == 0b0101
    assert ff6_config._parse_player2("1,3") == 0b0101
    assert ff6_config._parse_player2("1234") == 0b1111
    # Order doesn't matter
    assert ff6_config._parse_player2("42") == 0b1010


def test_parse_player2_rejects_bad():
    for bad in ["5", "0", "a", "12,5"]:
        try:
            ff6_config._parse_player2(bad)
        except argparse.ArgumentTypeError:
            pass
        else:
            raise AssertionError(f"expected rejection for {bad!r}")
    # Duplicate slot
    try:
        ff6_config._parse_player2("11")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("expected rejection for duplicate slot")


def test_cli_parses_player2_and_controller():
    parser = ff6_config.build_parser()
    ns = parser.parse_args(["-i", "rom.smc", "-ctrl", "multiple", "-p2", "13"])
    assert ns.Controller2 is True
    assert ns.Player2Controls == 0b0101


def test_set_config_writes_player2_when_extended():
    rom_bytes = bytearray(0x300000)
    rom_bytes[0x0370C3] = 0x00; rom_bytes[0x0370C4] = 0xFC  # Config2 -> 0x03FC01
    rom_bytes[0x0370C6] = 0x10; rom_bytes[0x0370C7] = 0xFC  # Config3 -> 0x03FC11
    rom_bytes[0x0370C8] = 0x20                              # extended trampoline JSR
    rom_bytes[0x0370C9] = 0x20; rom_bytes[0x0370CA] = 0xFC  # Config4 -> 0x03FC21
    rom = _FakeRom(rom_bytes)
    cfg.set_config(rom, {"Player2Controls": 0b1010})
    assert (0x03FC21, [0b1010]) in rom.writes


def test_set_config_rejects_player2_without_extended_trampoline():
    rom_bytes = bytearray(0x300000)
    rom_bytes[0x0370C3] = 0x00; rom_bytes[0x0370C4] = 0xFC
    rom_bytes[0x0370C6] = 0x10; rom_bytes[0x0370C7] = 0xFC
    rom_bytes[0x0370C8] = 0x9C  # vanilla STZ $1D4F -- no Config4 override
    rom = _FakeRom(rom_bytes)
    # Zero request is fine (the STZ already gives a zero default).
    cfg.set_config(rom, {"Player2Controls": 0})
    # Non-zero request must fail loudly.
    try:
        cfg.set_config(rom, {"Player2Controls": 0b0001})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError without extended trampoline")


# ---- Trampoline detection -------------------------------------------

def test_trampoline_detection():
    rom_bytes = bytearray(0x040000)
    # Vanilla: two STZ instructions -- not detected as installed
    rom_bytes[0x0370C2] = 0x9C
    rom_bytes[0x0370C5] = 0x9C
    assert cfg.is_trampoline_installed(_FakeRom(rom_bytes)) is False

    # WC-style: two JSRs
    rom_bytes[0x0370C2] = 0x20
    rom_bytes[0x0370C5] = 0x20
    assert cfg.is_trampoline_installed(_FakeRom(rom_bytes)) is True

    # Only one JSR -- not enough
    rom_bytes[0x0370C5] = 0x9C
    assert cfg.is_trampoline_installed(_FakeRom(rom_bytes)) is False


def test_controller_trampoline_detection():
    rom_bytes = bytearray(0x040000)
    rom_bytes[0x0370C8] = 0x9C  # vanilla STZ $1D4F
    assert cfg.is_controller_trampoline_installed(_FakeRom(rom_bytes)) is False
    rom_bytes[0x0370C8] = 0x20  # extended trampoline JSR
    assert cfg.is_controller_trampoline_installed(_FakeRom(rom_bytes)) is True


# ---- Installer -------------------------------------------------------

def test_build_subroutines_layout():
    b = inst.build_subroutines()
    assert len(b) == 18
    # Subroutine 1: LDA #$00; STA $1D54; RTS
    assert b[0:6] == [0xA9, 0x00, 0x8D, 0x54, 0x1D, 0x60]
    # Subroutine 2: LDA #$00; STA $1D4E; RTS
    assert b[6:12] == [0xA9, 0x00, 0x8D, 0x4E, 0x1D, 0x60]
    # Subroutine 3: LDA #$00; STA $1D4F; RTS (player-2 controller byte)
    assert b[12:18] == [0xA9, 0x00, 0x8D, 0x4F, 0x1D, 0x60]


def test_build_jsrs_default_address():
    # Default trampoline at file 0x3F091 -> SNES $C3/F091, low 16 bits 0xF091.
    # Subroutines at offsets +0/+6/+12 -> $F091/$F097/$F09D.
    jsrs = inst.build_jsrs(0xF091)
    assert jsrs == [0x20, 0x91, 0xF0, 0x20, 0x97, 0xF0, 0x20, 0x9D, 0xF0]


def test_parse_address_forms():
    # File offset forms
    assert inst.parse_address("0x3F091") == 0x3F091
    assert inst.parse_address("3F091") == 0x3F091
    # SNES form -- subtracts 0xC00000
    assert inst.parse_address("0xC3F091") == 0x03F091
    assert inst.parse_address("$C3F091") == 0x03F091


def test_installer_main_writes_expected_bytes(tmp_path=None):
    """Run main() end-to-end with a tiny in-memory ROM via monkey-patched IO."""
    import io
    rom_bytes = bytearray(0x40000)
    rom_bytes[0x0370C2] = 0x9C  # vanilla STZ
    rom_bytes[0x0370C5] = 0x9C
    rom_bytes[0x0370C3] = 0x54  # arbitrary STZ operand
    rom_bytes[0x0370C4] = 0x1D

    # Patch open() to use our buffer for both read and write.
    read_calls = []
    write_calls = []
    original_open = inst.__builtins__["open"] if isinstance(inst.__builtins__, dict) else open

    class _Reader(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()

    class _Writer(io.BytesIO):
        def __init__(self, path):
            super().__init__()
            self.path = path
        def __enter__(self): return self
        def __exit__(self, *a):
            write_calls.append((self.path, self.getvalue()))
            self.close()

    def fake_open(path, mode, *args, **kwargs):
        if mode == "rb":
            read_calls.append(path)
            return _Reader(bytes(rom_bytes))
        if mode == "wb":
            return _Writer(path)
        return original_open(path, mode, *args, **kwargs)

    import builtins
    saved = builtins.open
    builtins.open = fake_open
    try:
        inst.main(["-i", "fake.smc", "-o", "out.smc"])
    finally:
        builtins.open = saved

    assert len(write_calls) == 1
    out_path, out = write_calls[0]
    assert out_path == "out.smc"
    # Expect the JSR trio to the default address ($C3/F091)
    assert out[0x0370C2:0x0370CB] == bytes(inst.build_jsrs(0xF091))
    # Expect the 18 trampoline bytes
    assert out[0x03F091:0x03F0A3] == bytes(inst.build_subroutines())


def test_installer_rejects_out_of_bank_address():
    try:
        inst.main(["-i", "fake.smc", "--address", "0x0FEE8"])
    except SystemExit as e:
        assert "bank $C3" in str(e) or "not in bank" in str(e)
        return
    raise AssertionError("expected SystemExit for out-of-bank address")


# ---- runner ----------------------------------------------------------

def main():
    tests = sorted(
        (name, fn) for name, fn in globals().items()
        if name.startswith("test_") and callable(fn)
    )
    failed = []
    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"FAIL: {name}: {type(e).__name__}: {e}")
            failed.append(name)
        else:
            print(f"PASS: {name}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
