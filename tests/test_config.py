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
        "--font", "31,0,0",
        "-w3", "1=10,10,10;4=20,20,20",
    ])
    assert ns.input == "rom.smc"
    assert ns.BatSpeed == 5
    assert ns.MsgSpeed == 2
    assert ns.BatMode is False
    assert ns.Command is True
    assert ns.Gauge is True
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


# ---- Default config address read ------------------------------------

class _FakeRom:
    def __init__(self, bytes_at):
        self._bytes_at = bytes_at
        self.writes = []

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
