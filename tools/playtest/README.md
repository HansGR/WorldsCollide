# Playtest harness

Headless emulation harness for behaviorally testing built seeds: boot a
ROM, drive it with scripted inputs, and assert on live WRAM.

## Stack

- **Core:** snes9x via its libretro C ABI, loaded with ctypes
  (`core.py`). No RetroArch, no display, no audio device.
- **Core sourcing:** `pip install stable-retro` — the wheel bundles a
  Linux x86_64 `snes9x_libretro.so` (`core.find_core()` locates it).
  No separate download or toolchain needed.
- One `Core` instance per process (libretro cores are stateful
  singletons); fork for parallelism.

## Capabilities (proven by `spike.py`)

- Frame-stepping at ~900 fps headless (~15x realtime).
- `core.wram` — live read/write view of the full 128KB WRAM
  ($7E0000+): event bits at `0x1e80 + byte` (addresses from
  `data/event_bit.py`), character blocks at `0x1600 + 37*slot`
  (max HP at +0x0B, 14-bit), etc.
- `run_until(predicate, timeout)` — condition-driven stepping; prefer
  this over frame counts for robustness.
- Savestates (`save_state`/`load_state`), verified deterministic:
  reload + N frames reproduces WRAM exactly.
- `buttons` set + JOYPAD map for scripted input.
- `screenshot(path)` — RGB565/XRGB8888/1555 framebuffer to PNG,
  stdlib-only encoder.

## Usage

```sh
pip install stable-retro          # once per environment
python3 tools/playtest/spike.py <rom.smc> [shot_dir]
```

```python
from tools.playtest.core import Core
core = Core(rom_path="seed.smc")
core.run(3000)                                   # boot to title
core.buttons = {'START'}; core.run(6); core.buttons = set()
core.run_until(lambda c: c.wram[0x1e9d] & 0x02)  # objective D fired
```

## Status

Phase 0 (spike) complete: core loads, WC seeds boot through the
ruination start cinematic, WRAM assertions and screenshots work, and
the -oss silent-start objectives were verified behaviorally (bits set,
max HP +100, full heal, no message window).

Next phases (see session plan): harness API with RAM map bridged from
`data/`, boot/menu macros, door-step navigation from `doors/atlas`
coordinates, then regression scenarios (minecart camera, phoenix cave
collision, -oss, warp safety).
