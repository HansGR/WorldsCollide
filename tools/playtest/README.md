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

## Harness API (`harness.py`)

`Harness` wraps a `Core` with FF6-aware, named accessors so tests read
as game actions. Imports ROM-free (no Memory/allocation side effects).

- `boot_to_game_start()` — title -> file select -> new game, via state
  predicates (event bits going live), not frame counts.
- Input: `press(*buttons)`, `hold(*buttons, frames=)`.
- Event state: `event_bit(id)` / `set_event_bit(id)` (ids from
  `data.event_bit`, names or literals), `event_word(id)`.
- Characters: `max_hp(slot)`, `cur_hp`, `max_mp`, `cur_mp`, `status`.
- Field: `map_id`, `gp`, `screen_held` (camera-hold flag), `party_xy`,
  `set_party_xy(x, y)` (for door-step teleport in Phase 2).

Validated by `selftest.py` on a `-ruin` seed: map id 0xDA (Esper Gate),
GP 6000 (matches `-gp 6000` default), party at hub, and the -oss bonuses
(max HP +100, full heal) firing silently.

**Ruination objective reindex gotcha:** in ruination mode the `-oa`
objective (result 2, Unlock Final Kefka) is filtered out of
`args.objectives` before `.id` assignment, so later objectives shift
down a slot. The `-od`/`-oe` start bonuses land in `OBJECTIVE` bit
slots **2 and 3**, not 3 and 4.

## Status

- Phase 0 (spike) complete: `spike.py`.
- Phase 1 (harness API) complete: `harness.py` + `selftest.py`.

Next (see session plan): Phase 2 door-step navigation from
`doors/atlas` coordinates (poke `set_party_xy` next to a door, step
through, let the engine run its own transition), then Phase 3
regression scenarios (minecart camera, phoenix cave collision, -oss,
warp safety).
