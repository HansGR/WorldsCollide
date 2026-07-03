# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Memory Routine

**How this works:** I (Setzer) maintain a prioritized list of the 10 most important concepts for working on this project. After each request, I revisit the list and decide whether the order should change or a new item should be added. Items that fall past #10 are moved to ARCHIVE.md, which I can scan when looking for specific information.

**To interface with this system:**
- The Top 10 list below contains the most critical knowledge, ranked by importance
- Reference sections below the Top 10 contain detailed supporting information
- ARCHIVE.md contains useful but less frequently needed information
- After completing a task, I update the list based on what proved most important

---

## Top 10 Most Important Concepts

### 1. FinishCheck Timing (Critical Bug Source)
When modifying events that give rewards and then transition to another map, `field.FinishCheck()` must be called **before** any screen transitions. The relevant event bit must be set **before** `FinishCheck()` is called. Getting this wrong causes rewards to not register.

### 2. NPC ID Offset (+0x10)
NPC IDs used in `maps.get_npc(map_id, npc_id)` are **offset by 0x10** from the map-local index. Slots 0x00-0x0f are reserved for the 14 playable characters. Formula: `npc_id = map_local_index + 0x10`.

### 3. Door ID Ranges
- **< 2000**: Two-way connections (normal doors)
- **2000-2999**: One-way exits (traps)
- **3000+**: One-way entrances (pits)

### 4. Event Exit Info Runtime Updates
Event tiles (IDs 1500-2000) acting as doors need runtime connection data. When adding new event tile connections, ensure **BOTH sides' partners** are included in `used_events` if they need runtime updates. Connections are stored as `[exit_id, entrance_id]`, so check both `m[0]` and `m[1]` partners.

### 5. Code Organization Principle
Event-specific modifications go in their respective event files (e.g., `event/burning_house.py`), not in top-level files like `event/events.py` or generic modules. For mode-specific changes, add a method like `ruination_mod()` or `no_free_heals_mod()` to the event class and call it conditionally from `mod()` (gated on `args.ruination_mode` / `args.no_free_heals` etc.). Cross-event "sweepers" that run once per build belong in their own module (e.g., `event/free_heals.py` for `-nfh`), invoked from a top-level `Events` method (e.g., `events.no_free_heals_mod()`).

### 6. Execution Flow (wc.py)
1. **Memory** - Loads ROM, initializes free space tracking
2. **Data** - Reads/modifies game data (including door randomization)
3. **Events** - Modifies event scripts, distributes rewards
4. **Memory.write()** - Outputs the modified ROM

### 7. Persistent Event State Across Reloads
Field RAM (NPC pointers, party state, etc.) is **not** preserved in saves. Events that need post-defeat state to persist across reloads must use event bits, with two halves:
1. **`init_event_bits`** (called once on every game start, in each event's `init_event_bits(space)`) sets/clears the bit so the world starts in a known state.
2. **In-event update** when the trigger fires, set/clear the bit to record progress.

Companion gotchas:
- The shared `init_event_bits` buffer is **450 bytes in ruination mode, 400 otherwise** (`event/events.py`). Overflow throws an allocator error — bump the size or reduce writes.
- NPC talk-event pointers (`ChangeNPCEventAddress`) are field RAM. In ruination mode, re-bind them on map entry via `field.Call(SET_PARTY_INTERACTION_POINTERS)`. See ARCHIVE.md "Persistent Event State Across Reloads" for examples (burning house fireballs, KT switches, minecart revisit).

### 8. Finding Map IDs by Name
1. Search `data/map_exit_extra.py` for location name in `exit_data`
2. Identify the entrance door ("Door Outside" goes INTO building)
3. Look up entrance door in `claude_reference/exits_raw.json` - the `dest_map` field is the interior map ID

### 9. NPC_BIT Calculation
Each NPC has a visibility bit determining if it appears when the map loads. Formula: `npc_bit = (event_byte + 0x60) * 8 + event_bit`. Special values: `ALWAYS_OFF = 0x6ff`, `ALWAYS_ON = 0x301` (in `data/npc_bit.py`).

### 10. SNES Addressing
- **SNES to ROM conversion**: `ROM_address = SNES_address - 0xC00000`
  - Example: SNES `$CEF100` → ROM `$0EF100` (not `$2EF100`!)
- ROM uses little-endian byte order
- The codebase constant `START_ADDRESS_SNES = 0xc00000` reflects this offset

---

## How to Find X (Cheat Sheet)

Quick lookup procedures I re-derive every session. Most JSONs are in `claude_reference/` and large — open with `grep`, not `Read`, unless you've narrowed it down.

| Looking for | Where / how |
|-------------|-------------|
| **Map ID by name** | `grep "<name>" data/map_exit_extra.py` → identify the entrance door (e.g. "Door Outside" goes INTO the building) → `grep '"index": <door_id>' claude_reference/exits_raw.json` → `dest_map` is the interior map ID. (Top 10 #8.) |
| **NPC by sprite/position** | `claude_reference/maps_data.json` `maps[map_id].npcs` array (position, sprite). Index in array = map-local index; **`npc_id = map_local_index + 0x10`** for `maps.get_npc(map_id, npc_id)` (Top 10 #2). Cross-reference `claude_reference/npcs_raw.json` for full properties (event_byte, event_bit). |
| **Event bit by name** | `grep -i "<name>" data/event_bit.py`. `npc_bit = (event_byte + 0x60) * 8 + event_bit` (Top 10 #9). Special: `ALWAYS_OFF = 0x6ff`, `ALWAYS_ON = 0x301` in `data/npc_bit.py`. |
| **Event word by name** | `grep -i "<name>" data/event_word.py`. Address: `event_word.address(event_word.NAME)`. |
| **Item ID by name** | `grep -in "<name>" data/items.py`. ID is the index in the `items` list. |
| **Esper / spell / character ID** | `data/espers.py`, `data/spells.py`. Character IDs (constant): 0=Terra, 1=Locke, 2=Cyan, 3=Shadow, 4=Edgar, 5=Sabin, 6=Celes, 7=Strago, 8=Relm, 9=Setzer, 10=Mog, 11=Gau, 12=Gogo, 13=Umaro. |
| **Custom opcode → file/class** | ARCHIVE.md "Custom Opcodes Reference" table. |
| **Vanilla event script for a ROM address** | `claude_reference/EventScriptTxt.txt` — search by SNES address (e.g. `CC/8022`). Decompile is comprehensive. |
| **Dialog text by ID** | `claude_reference/dialog_file.txt` — IDs are decimal. Modify with `dialogs.set_text(dialog_id, "...")`. |
| **Room ID → SNES map ID + name** | `claude_reference/room_map_reference.json` (covers 784/801; Mobliz/switchyard/ruin-logical rooms unresolved). |
| **Door ID → endpoints** | `data/map_exit_extra.py` `exit_data[door_id]` = `[partner_id, description]`. Door ranges: <2000 two-way, 2000-2999 trap (one-way exit), 3000+ pit (one-way entrance) — Top 10 #3. Full data: `claude_reference/exits_raw.json` (`dest_map`/`dest_x`/`dest_y`). |
| **Reward room for character X (ruin)** | `ROOM_REWARD` dict in `event/ruination.py`. |
| **Area name → rooms (ruin)** | `RUIN_ROOM_SETS` dict in `event/ruination.py`. |
| **Which branch holds area X (ruin)** | `args.ruination_areas_used[area_name]` (populated from `ruin_map.compute_actual_areas_used()`, NOT raw `AreasUsed`). |
| **ROM address ↔ SNES** | `ROM = SNES - 0xC00000`. SNES `$CEF100` → ROM `$0EF100`. Constant: `START_ADDRESS_SNES = 0xc00000`. (Top 10 #10.) |
| **ROM data structure offset** | `claude_reference/ff3infov2.txt` — comprehensive FF6 ROM map (large; grep). |
| **Chest contents at coords** | `claude_reference/chests_raw.json`. |
| **Map event tile at coords** | `claude_reference/events_raw.json` (one record per event tile). |

For the lookups above, prefer the JSON files over reading the corresponding .py because the JSONs are structured for grep-and-jump.

---

## Module Map

Quick orientation by file. Detailed sections are in ARCHIVE.md.
For the door-randomization modes (`-drdc`, `-ruin`): **DOOR_RANDO_GUIDE.md** is the programmer's guide (execution flow, ID conventions, mapper algorithms, global-mutable-state table, extension recipes); **DOOR_RANDO_CODE_REVIEW.md** is the 2026-07 review of known bugs/fragilities in those modes — check it before "fixing" surprising behavior there.

### Memory & ROM
- **memory/space.py** — `Reserve` (in-place patch), `Allocate` (new code into free space), `Write` (Allocate + write), `Read` (extract bytes), `Free` (mark range free). All take `Bank.XX` enum.
- **memory/free.py** — Static table of vanilla free-space ranges per bank.

### Maps & Doors
- **data/maps.py** — `Maps` class: NPC/event tile management, `door_map`, runtime patching.
- **data/doors.py** — `Doors` orchestrator. `verbose` is a property of `verbose.is_enabled()` — don't add an instance attribute.
- **data/rooms.py** — Room definitions (incl. `ruin-*` variants) and `forced_connections`.
- **data/map_exit_extra.py** — `exit_data` (door ID → `[partner_id, description]`), `eventname_to_door`, `doors_WOB_WOR`.
- **data/event_exit_info.py** — Event tile (1500-2000) connection metadata. `entrance_door_patch` callables live here.
- **data/walks.py** — `Network` class: connection graph, `apply_key()`, `initially_locked_exits` (excluded as targets — see ARCHIVE.md "Key/Lock Softlock Analysis"). `add_room()` assesses the new room's locks against the current keychain (`_assess_room_locks`) — rooms can arrive after their lock's key was applied (character areas are distributed *after* the character key in `process_rewards`), and without this the lock stays shut forever (the Mog→lw1→Lone Wolf bug).

### Ruination Mode
- **event/ruination.py** (~4700 lines) — `ruination_map` orchestrator, `RuinationBranch(Network)`, `generate_map_with_characters`, `extend_branch_path`, `finalize_map`, `RUIN_ROOM_SETS`, `ROOM_REWARD`. All `room_data` lookups in reserve searches must filter by `self.protected`.
  - `compute_actual_areas_used()` — area_name → branch_id from rooms actually placed AND reachable. Use this (not raw `AreasUsed`) for Narshe school clue scripts. See ARCHIVE.md "Branch Area Detection for Narshe Clues".
  - Branch selection weighted toward less-extended branches via `branch_rewards_found`.
  - `SET_PARTY_INTERACTION_POINTERS` (Bank.CA, populated by `create_party_interaction_scripts()` before the event mod loop) — shared subroutine to re-bind NPC talk events.
  - `DISABLE_Y_PARTY_SWITCH` / `RESTORE_Y_PARTY_SWITCH` (Bank.CB, populated by `create_y_party_switch_subroutines()` before the event mod loop) — shared save/disable and restore subroutines for events that must suppress y-party switching mid-scene (doma wob, fanatics tower, floating continent, narshe moogle defense). Use the named `SAVED_Y_PARTY_SWITCHING` event bit. See ARCHIVE.md "Y-Party-Switch Disable Shared Subroutines".
  - `_randomize_kefka_tower()` + `KT_*` constants (`-rkt`) — randomizes KT's three lanes by driving the `Network.connect_network` walk once per lane (not random matching: KT's door graph is too sparse), then `verify()` rejects softlocks via a joint state-space over `(roomA,roomB,roomC,keychain)` — three parties moving asynchronously over a shared monotonic keychain — requiring every room reachable AND every reachable situation can still finish (NOT the old "assume both keys held" strand check, which missed one-way-into-a-locked-pocket softlocks). Result stored on `self.kt_lane_map`, injected into the global door/trap map in `generate_map_with_characters`. See ARCHIVE.md "Kefka's Tower Lane Randomizer".
- **args/ruin_preprocessor.py** — `RUIN_DEFAULT_FLAGS` expansion. `-ruin` bundles `-nfh` here.
- **event/narshe_wob.py** — `ruination_mod()` (hub party formation, see ARCHIVE.md "Party Formation & Away-Party System") and `limited_heals()` (gated by `-nfh`, uses `SCHOOL_LIMITED_HEALS_1/2` event bits — does NOT use the `NARSHE_CHECKPOINT` event word any more).

### Feature flags
- **event/free_heals.py** — `-nfh` cross-event sweepers, orchestrated by `Events.no_free_heals_mod()`: `modify_inn_costs` (×3 paid + convert free Returners/Figaro), `modify_free_bed_heals` (50% pincer ambush + per-character `BedHealCharacter`), `modify_recovery_springs` (9 randomised outcomes). Per-event `-nfh` patches stay in their own files. See ARCHIVE.md "No Free Heals" for the full table.
- **menus/buy.py** + **data/shops.py** — `-sli` limited-inventory shops (pack-based purchasing). See ARCHIVE.md "Limited Inventory Shops".

### Custom opcodes
- **instruction/field/custom.py** — Field opcodes (65816 ASM). Pattern: write ASM to Bank.C0, register via `_set_opcode_address`, create `_Instruction` subclass.
- **instruction/field/y_npc/instructions.py** — Y-NPC opcodes (also via `_set_opcode_address`).
- **instruction/vehicle.py** — Vehicle-script opcodes (Bank.EE). `BranchProbability` (0xE1) handler installed lazily on first use.
- **instruction/battle_event.py** — Battle-event opcodes.
- See ARCHIVE.md "Custom Opcodes Reference" for the consolidated table.

### Door-rando integration
- **instruction/field/instructions.py** `RecruitAndSelectParty` — In ruin mode, wraps recruitment with `SetupBranchRecruit`/`FinalizeBranchRecruit` to restrict party select on branches.
- **Local character gating** (door rando) — Three mechanisms: `entrance_door_patch` (callable taking `args`), in-event gating, `ruin-*` room variants with lock dicts. See ARCHIVE.md "Local Character Gating".
  - **Gotcha:** `entrance_door_patch` source must NOT terminate with `field.Return()` — see ARCHIVE.md "entrance_door_patch must fall through".

### Conventions
- **log/verbose.py** `vprint()` — debug output helper. `-debug` → stdout, `-debug-verbose`/`-dv` → spoiler-log temp file, neither → no-op. **Don't** wrap `vprint(...)` in `if self.verbose:`.

---

## Project Overview

Worlds Collide is an open-worlds randomizer for Final Fantasy VI (SNES). It takes a vanilla US v1.0 ROM file, applies randomization and modifications based on configurable flags, and outputs a modified ROM.

## Running the Randomizer

```sh
# Basic usage
python3 wc.py -i ffiii.smc

# Show all available flags
python3 wc.py -h

# Common modes
python3 wc.py -i ffiii.smc -drdc   # Dungeon crawl mode
python3 wc.py -i ffiii.smc -ruin   # Ruination mode
python3 wc.py -i ffiii.smc -debug  # Enable spoiler log
```

## Resources

Note these files are LARGE. Only access them when necessary and be smart about reading them. Don't just load the entire file into context.

- **ROM offset reference**: `./claude_reference/ff3infov2.txt` - Comprehensive FF6 ROM map with addresses for all data structures
- Event script decompile: `./claude_reference/EventScriptTxt.txt`
- Event bits: `./data/event_bit.py`
- Dialog decompile: `./claude_reference/dialog_file.txt`
- Location names: `./claude_reference/location_names.json` - Maps `name_index` to display names
- **Room-to-map reference**: `./claude_reference/room_map_reference.json` - Maps each room ID (from `data/rooms.py`) to its SNES map ID and map name. Covers 784/801 rooms. Unresolved rooms are Mobliz event rooms (no exits), switchyard-based virtual entries, and ruination logical rooms.
- Original map, event, and NPC JSON files: see `MAP_DATA_STRUCTURES.md`
  - Chests data: `./claude_reference/chests_raw.json`
  - MapEvents data: `./claude_reference/events_raw.json`
  - MapExits data: `./claude_reference/exits_raw.json`
  - Maps data: `./claude_reference/maps_data.json`
  - NPC data: `./claude_reference/npcs_raw.json`
