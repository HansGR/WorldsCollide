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

## Navigation (`navigate.py`)

Cross-map travel = teleport beside a door, then let the engine run its
own transition:

- `wait_for_control(h)` — advance past the start cinematic until the
  player has control (party idle + camera free), by state not timing.
- `doors_on_map(map_id)` — atlas doors physically on a map, as
  `(door_id, (x, y))`.
- `step_through(h, x, y, facing)` — teleport beside door tile `(x, y)`,
  walk into it, return the new map id once it changes.

`Harness.set_party_xy` teleports by setting the **authoritative pixel
position** (tile*16 at object block +0x03/+0x06) plus the derived tile
coords; setting the tile alone is overwritten from the pixel store
within a frame (found the hard way -- see the block-offset notes in
`harness.py`). Poking coordinates moves the party only within the loaded
map; a real door-step is what loads a new map and resyncs the camera.

Validated by `nav_test.py`: boots a `-ruin` seed, teleports to the hub
door, steps through, and confirms the map changed (0xDA -> 0xD9) with the
camera not held on the far side.

## Regressions (`regressions.py`)

Behavioral tests for recent fixes. Each scenario builds the seed(s) it
needs from a vanilla ROM, boots headless, and asserts on live state.
Runner exits nonzero on any failure.

```sh
python3 tools/playtest/regressions.py <vanilla.smc>
```

Current scenarios:
- `maxhp_objective` — the +100 Max HP start objective raises slot-0 max HP
  by exactly 100 (before/after in one build, via the max-HP change; a
  cross-build differential would change RNG and thus the character).
- `full_heal_objective` — every party member is at full HP after start.
- `camera_after_transition` — a normal door transition leaves the camera
  free (the invariant behind the reported camera-hold bugs).
- `minecart_camera`, `phoenix_collision` — scaffolded, **skipped** until
  Phase 4 plan-driven routing can reach those dungeon locations.

Lesson baked into the scenarios: cross-build "same seed" comparisons do
**not** hold a variable fixed -- any flag change (even `-no od`) perturbs
the shared RNG stream and changes the party. Isolate an effect within a
single build (before/after) instead.

## Route chaining (`route.py`)

Reach an arbitrary map by walking a seed's realized connectivity:

- `parse_spoiler_map(spoiler)` — `{exit: entrance}` from the spoiler's
  `Map:` section.
- `build_graph(edges)` — map-level adjacency (two-way doors add reverse
  edges; traps/pits stay one-way).
- `bfs` / `reachable_from` — shortest hop list, and reverse closure (used
  to pick which branch a target sits in).
- `step_door(h, door_id)` — teleport to a door by id and step through it.
- `execute_route(h, hops)` — drive a whole hop list.

Validated by `route_test.py`: offline BFS routes to Phoenix Cave's
approach map (a few hops inside its branch), and the live executor chains
real overworld maps (218 -> 217 -> 219) with the camera free.

**Known limit (deep-dungeon reproduction):** branch entry is gated by the
ruination away-party deployment flow at the Narshe School -- an
interactive party-formation mechanic, not a door step -- so the world-map
branch entrances don't trigger from a fresh start. Automating that hub
flow is the prerequisite for the minecart-camera and phoenix-collision
scenarios; the routing to walk the branch *after* deployment is in place.

## Status

- Phase 0 (spike) complete: `spike.py`.
- Phase 1 (harness API) complete: `harness.py` + `selftest.py`.
- Phase 2 (navigation) complete: `navigate.py` + `nav_test.py`.
- Phase 3 (regressions) complete: `regressions.py` (3 passing, 2 scaffolded).
- Phase 4 (route chaining) complete: `route.py` + `route_test.py`
  (offline graph/BFS + live executor; deep-dungeon reproduction gated on
  the Narshe School deployment flow).

Next: automate the Narshe School away-party deployment so a party can be
sent into a branch (and a second left on a landing tile), which unlocks
the minecart-camera and phoenix-collision behavioral tests.
