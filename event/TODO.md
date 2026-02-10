# Todo list for Claude (-ruin mode updates)

## Key/Lock Softlock Analysis (2026-02-10)

### Summary

The mapping algorithm applies keys when rooms are **connected** (during path building), but the player applies keys when rooms are **visited**. Since the player can explore rooms in any order, the algorithm's key ordering guarantee does not hold for the player. This can cause softlocks when a player enters a room (via a one-way pit) whose exits are all locked by keys found in other rooms they haven't visited yet.

The risk only applies to **pit (one-way) entrances**, because doors are bidirectional -- the player can always retrace through a door. Pits are irreversible.

### Catalog of All Keyed Rooms in RUIN_ROOM_SETS

#### Character-Keyed Locks (no softlock risk -- characters are persistent party members)

| Room | Area | Free Exits | Locked Exits | Key |
|------|------|-----------|-------------|-----|
| `ruin-thamasa` | VeldtCave | 2 doors, 2 pits | trap 2054 (STRAGO) | Character |
| `ruin-whelk` | Narshe | 2 doors | door 1155 (TERRA) | Character |
| `ruin-zozo` | Zozo | 5 doors | door 4608 (TERRA), key 'zr1' (CYAN) | Character |

#### Self-Unlocking Rooms (key provided by same room -- no softlock risk)

| Room | Area | Free Exits | Lock | Key Source |
|------|------|-----------|------|-----------|
| 216 | PhantomTrain | 1 door | doors 493/494 (pt1) | Self (pt1) |
| 472 | VeldtCave | 1 door | door 989 (vc1) | Self (vc1) |
| 435 | Doma | 1 door | doors 865/866 (cd3) | Self (cd3) |
| `ruin-daryl` | DarylsTomb | 1 door | door 1563 (dtboss) | Self (dtboss) |

#### Non-Character Locks with Free Exits (key from other room -- low risk)

These rooms always have at least one free exit, so the player is never trapped.

| Room | Area | Free Exits | Locked Exits | Key Source |
|------|------|-----------|-------------|-----------|
| 202 | PhantomTrain | 9 doors | trap 2068 (pt2) | Room 212 |
| 383 | DarylsTomb | 1 door | door 1512 (dt1) | Room 392 |
| 429 | Doma | 1 door | trap 2070 (cd1+cd2) | Rooms 423, 427 |
| 531 | AncientCastle | 1 door | door 1106 (ac2) | Room 528 |
| `296r` | Zozo | 2 doors | door 618 (zr1) | `ruin-zozo` + CYAN |

#### Key-Providing Rooms (no softlock risk -- these rooms give keys, not locks)

| Room | Area | Keys Provided | Free Exits |
|------|------|-------------|-----------|
| 212 | PhantomTrain | pt2 | 1 door |
| 389 | DarylsTomb | dt2 | 1 door |
| 390 | DarylsTomb | dt3 | 2 doors, 1 trap, 1 pit |
| 392 | DarylsTomb | dt1 | 1 door |
| `301r` | Zozo | clock1 | 3 doors |
| `306r` | Zozo | clock2 | 1 door |
| 299 | ZozoTower | clock5 | 2 doors |
| `303a`/`303b` | ZozoTower | clock3 | 1 door + trap/pit |
| 304 | ZozoTower | clock4 | 2 doors |
| 423 | Doma | cd1 | 1 trap, 1 pit |
| 427 | Doma | cd2 | 1 trap, 1 pit |
| 528 | AncientCastle | ac2 | 4 doors |

#### HIGH RISK -- All Exits Locked, Key From Other Rooms

| Room | Area | Free Exits | Locked Exits | Key Sources |
|------|------|-----------|-------------|------------|
| **391** | **DarylsTomb** | **0 doors, 0 traps, 1 pit (entrance only)** | **door 795 (dt2), trap 2060 (dt3)** | **Room 389 (dt2), Room 390 (dt3)** |

### Softlock Scenario (Room 391)

Room 391 is the only room in ruination mode with zero initially-free exits where all exits are locked by non-character keys from other rooms.

1. During `extend_branch_path`, rooms 389 and 390 are connected. Their keys (dt2, dt3) are applied via `apply_key()`, which promotes room 391's locked elements to free: door 795 and trap 2060.
2. `get_valid_pit_targets_v2` evaluates room 391. It checks `room.doors` (1 free) + `room.traps` (1 free) = 2 exits. Target accepted.
3. Algorithm connects some trap to pit 3059 (room 391). Valid from the algorithm's perspective.
4. Player enters the hub. They see a door (to some room) and a trap (leading to room 391). Player falls through the trap into room 391.
5. The player hasn't visited rooms 389/390 yet. In the player's game state, dt2 and dt3 haven't been obtained. Room 391's exits are still locked. **SOFTLOCK.**

### Proposed Solution: Track "Initially Locked" Exits

When `apply_key()` unlocks an element (moves it from locks to free), record it in a set `initially_locked_exits`. When evaluating pit targets, require that the target room has at least one exit that was **originally free** (not just unlocked by key application during path building).

1. Add `self.initially_locked_exits = set()` to the Branch class.
2. In `apply_key()` (walks.py:135), when an element is unlocked and added to the room, also add it to `self.initially_locked_exits`.
3. In `get_valid_pit_targets_v2` Rule A1 (unconnected room check), add after the `target_exits > 0` check:
   ```python
   originally_free_exits = (
       len([d for d in room.doors if d not in self.protected
            and d not in self.initially_locked_exits])
       + len([t for t in room.traps if t not in self.protected
              and t not in self.initially_locked_exits])
   )
   if originally_free_exits == 0:
       continue  # All exits were key-unlocked; player could be trapped
   ```
4. Apply the same check in finalize_map steps (1) and (3) when pairing traps with pits.

This correctly handles all cases:
- Rooms with originally-free exits (383, 202, 429, 531, etc.) always pass
- Self-unlocking rooms (216, 472, 435, ruin-daryl) always have >= 1 free exit
- Room 391 is rejected as a pit target since all its exits are key-unlocked
- Door connections don't need this check (doors are bidirectional, player can retrace)

---

## Updates to branch mapping code (event/ruination.py)
1. ✅ **FIXED** - Esper slot check (line 1023): Now accounts for character slots when checking if enough esper slots exist. The check now compares `total_esper_slots < self.Requested[1] + len(planned_characters)`.

2. ✅ **FIXED** - Dead checks calculation (line 1048): Now uses `len(planned_characters)` instead of stale `characters_needed` value, since the esper slot check loop may add more characters.

3. ✅ **FIXED** - Loop termination condition (line 1229): Now compares `RewardsObtained[0]` against `len(self.planned_characters)` instead of `self.Requested[0]`. The latter includes starting party, but rewards only count characters obtained from checks.

4. ✅ **FIXED** - Character selection restriction (events.py:247-250): generate_map_with_characters now only selects from planned characters determined by pre_plan_character_acquisition(). The available_characters list is restricted to planned_char_ids before map generation.  



## Updates to overall behavior of -ruin
1. ✅ **FIXED** - Dried meat availability for Gau: The -sdm flag now correctly ensures dried meat is available in accessible, non-Veldt-gated shops in ruination mode. Implementation includes:
   - Tracking of accessible shops during map generation (event/ruination.py:1190-1196)
   - Filtering of Veldt-gated shops via character dependency paths (event/ruination.py:1234-1317)
   - Assignment of dried meat to filtered shops (data/shops.py:215-274)
   - Optimization: skips Veldt-gating logic when Gau is not in planned characters
   - Fallback: uses all accessible shops with warning if no non-Veldt-gated shops exist

2. ✅ **IMPLEMENTED** - Implement -ruin as a "meta-flag", that sets a default flagset which can subsequently be modified by calling other flags.  This bakes in some desired flags to -ruin while allowing the player flexibility to define other options.  The option of `-ruin custom` could skip the defaults and require the player to choose everything.
- **Implementation**: args/ruin_preprocessor.py provides argument preprocessing that expands `-ruin` into ~70 default flags
- **Usage**:
    - `-ruin` - Injects all default flags (recommended settings)
    - `-ruin custom` - Skips all defaults, requires manual flag selection
    - `-ruin -no <flag1> <flag2> ...` - Disables specific default flags (e.g., `-ruin -no fst brl sal`)
    - `-ruin -sc1 TERRA` - Automatically removes default starting characters when user specifies their own
- Default flags include:
    - `-gpm 0` (zero GP from all battles: only starting money + selling equipment).
    - `-oa 2.2.2.2.6.6.4.9.9`  (Unlock final kefka: 6 characters, 9 espers.  This information is used by the ruination mapping algorithm and sets the 'size' of the game)
    - Party flags:  `-sc1 random -sc2 random -sc3 random -sal -eu -csrp 80 125`  (starting with 3 random characters, starting average level, equippable umaro, randomized stats between 80--125).
    - Command flags:  `-fst -brl -slr 3 5 -lmprp 75 125 -lel -srr 25 35 -rnl -rnc -sdr 1 2 -das -dda -dns -sch -scis -com 98989898989898989898989898 -rec1 28 -rec2 27`  (Standard Ultros League command settings)
    - Battle flags:  `-xpm 3 -mpm 5 -nxppd -lsced 2 -hmced 2 -xgced 2 -ase 2 -msl 40 -sed -bbs -drloc shuffle -stloc mix -be -bnu -res -fer 0 -escr 100 -dgne -wnz -mmnu -cmd`
    - Magic flags: `-esr 2 5 -elrt -ebr 82 -emprp 75 125 -nm1 random -rnl1 -rns1 -nm2 random -rnl2 -rns2 -nmmi -mmprp 75 125`
    - Item flags:  `-gp 5000 -smc 3 -sto 1 -ieor 33 -ieror 33 -ir stronger -csb 6 14 -mca -stra -saw -sisr 20 -sprp 75 125 -sdm 4 -npi -sebr -snsb -snee -snil -ccsr 20 -chrm 5 0 -cms`
    - Other flags: `-frw -wmhc -cor 100 -crr 100 -crvr 100 120 -crm -ari -anca -adeh -ame 1 -nmc -noshoes -u254 -nfps -fs -fe -fvd -fr -fj -fbs -fedc -fc -ond -etn`

4. Ruination mode needs to get rid of the abundance of healing options in the standard game.
- Decide what to do with unlimited healing spots: either make them a limited resource, add a cost, or make them heal HP only (not MP).  Identify all unlimited heals and make a decision for each
  - Bucket in School: 3 uses (implemented)
  - Healing Spring in Phantom Forest:  Randomize outcome from a list (incl. bad outcomes)
  - ✅ Free beds: heal only HP (implemented in modify_free_beds function)
      - Narshe Weapon Shop, Sabin's House (3 beds), Gau's Father's House, Mobliz WoR Relic Shop
      - Includes a 3/8 chance of being attacked in the night (forced back attack before healing)
  - Phantom Train food:  Add a cost to the meal?  Or randomize outcome from a list (incl. bad outcomes).  Or both: "Premium meal" for [1000---10000] GP, or "cheap meal" for [1-100] GP, with differently chosen outcomes.  I like it!
- ✅ **IMPLEMENTED** - Increase all inn costs by a multiplier (2x). Implementation:
  - Inn costs doubled via INN_COST_MULTIPLIER in event/ruination.py
  - Dialog text updated to reflect new prices (modify_inn_costs function)
  - In-town chocobo stables disabled (South Figaro, Nikeah, Jidoor) - NPCs now say "The chocobos won't go outside anymore."
  - Thamasa inn has special handling (event/burning_house.py:ruination_inn_mod):
    - 1 GP if burning house not done (to allow event access)
    - Normal price (400 GP) after burning house completed
  - ✅ Free inns converted to paid inns (modify_free_inns function):
    - Returners Hideout inn: Base price 100 GP (200 GP with 2x multiplier)
    - Figaro Castle rest: Base price 150 GP (300 GP with 2x multiplier)
    - Both affected by INN_COST_MULTIPLIER

4. ✅ **IMPLEMENTED** - Change the starting menu to be -ruin specific.  In Ruination mode, there is only one save slot, and it gets wiped when you die.  Get rid of the "load a save file" menu; replace it with alternate starting menu (New Game, Flags, Config) with an added "Load Saved Game" option

   **Implementation (menus/pregame.py):**
   - Boot sequence always shows pregame menu in ruination mode (no auto-load)
   - Conditional menu rendering based on save detection:
     - No save: 3 options (New Game, Flags, Config)
     - Save exists: 4 options (New Game, Load Saved Game, Flags, Config)
   - Uses memory flag at 0x1300 to track active menu layout
   - "Load Saved Game" handler invokes load menu (command 0x20) for single-slot save

   **Original Investigation Notes (for reference):**
   - **menus/pregame.py** (lines 228-248): `invoke_load_game_mod()` modifies boot behavior
     - At ROM address 0x3017c-0x301b1: "load pregame menu if no saves else invoke load menu"
     - Calls JSR 0x7023 to test save file validity
     - If no saves → initialize pregame menu (command 0x2f)
     - If saves exist → initialize load menu (command 0x20)
   - **Current pregame menu** has 4 options (lines 18-23):
     1. "New Game" - starts new game
     2. "Objectives" - shows objectives menu
     3. "Flags" - shows flags menu
     4. "Config" - shows config menu
   - **Ruination mode detection:**
     - `args.ruination_mode` is Python build-time flag only
     - ROM has no runtime flag to detect ruination mode
     - `menus/save.py` already modifies save behavior in ruination mode (auto-save slot 1, wipe on death)

   **Implementation Strategy:**
   Since the ROM is built with `-ruin` flag, we simply modify the ROM code during build time - no runtime detection needed.

   1. **Modify boot sequence** (menus/pregame.py:228-248 in `invoke_load_game_mod()`):
      - **If `args.ruination_mode`:** Always show pregame menu (skip load menu auto-invoke)
      - **Otherwise:** Use existing logic (show load menu if saves exist)

   2. **Modify pregame menu options** (menus/pregame.py:15-47 in `draw_options_mod()`):
      - **If `args.ruination_mode`:** Two menu variants based on save detection:

        **Approach A (Recommended): Conditional menu generation**
        - Test save validity at menu initialization (JSR 0x7023)
        - **If no save detected:** Draw 3 options:
          1. "New Game" - starts new game
          2. "Flags" - shows flags menu
          3. "Config" - shows config menu
        - **If save detected:** Draw 4 options:
          1. "New Game" - starts new game
          2. "Load Saved Game" - loads the save
          3. "Flags" - shows flags menu
          4. "Config" - shows config menu

        **Approach B (Alternative): Grey out option**
        - Always draw 4 options, but grey out "Load Saved Game" when no save exists
        - Use `set_gray_text_color` (see menus/checks.py:34 for example)
        - Make option unselectable by skipping cursor position
        - More complex but provides consistent menu layout

      - **Otherwise:** Draw standard 4 options (New Game, Objectives, Flags, Config)

   3. **Implement "Load Saved Game" option** (menus/pregame.py:93-186 in `sustain_mod()`):
      - Create new handler similar to existing option handlers
      - For Approach A: Only exists when save is detected
      - For Approach B: Check save validity, skip if greyed out
      - When active: initialize load menu (command 0x20) or directly load game

   4. **Files to modify:**
      - menus/pregame.py - main implementation (wrap logic in `if args.ruination_mode:` checks)
      - menus/save.py - already handles ruination save behavior (lines 48-49)

   5. **Key ROM addresses/commands:**
      - 0x7023: subroutine to test save file validity
      - 0x2f: initialize pregame menu command
      - 0x20: initialize load menu command
      - 0x26/0x27: menu command queue addresses

   **Additional considerations:**
   - The custom menu should be visually distinct or have a title indicating "Ruination Mode"
   - "Load Saved Game" should handle the single-slot constraint gracefully
   - May want to show a warning on "New Game" if a save exists (since it will be overwritten on first save)
   
5. [low priority] Add a custom splash graphic for RUINATION - Final Fantasy 6 Roguelike

   
## Updates to specific checks to work with -ruin
1. Checks in the WoB that must be "moved" to WoR:
- ✅ **DONE** - Lone Wolf (must be moved to WoR Narshe treasure hut; animation moved to WoR Narshe; event must be added to Narshe Peak with Tritoch & deconflicted from Tritoch event)
  - **Status**: Implemented in event/lone_wolf.py:323-440 (ruination_mod method).  Needs testing.
  - Moves Lone Wolf event to WOR Narshe, edits NPCs and event tiles for Tritoch Peak WOR
- ✅ **DONE** - Moogle Defense (WoB room must be used, possibly with palatte swap; event must be initialized in the room, rather than at Arvis' house)
  - **Status**: Implemented in event/narshe_moogle_defense.py:632-707 (ruination_start_mod method).  Needs testing.
  - Uses WOB map with custom entrance event, initializes event in the room
- ✅ **DONE** - Opera House (deconflict with OH dragon.  Probably same solution as for Kefka at Narshe)
  - **Status**: Implemented in event/opera_house_wob.py (ruination_set_wor_opera_bits method)
  - After reward, sets WoR NPC bits and places player in Opera House lobby (map 0xed) at (60, 44)
  - WoB version plays normally; transitions to WoR state after completion
- ✅ **DONE** - Shadow's check at gau's dad's house (just use WoB gau's dad's house with pallete swap)
  - **Status**: Implemented in event/gau_father_house.py:123-129 (ruination_mod method).  Needs testing.
  - Edits palette to look like WOR
- ✅ **DONE** - Whelk (must be moved to WoR Narshe.  Actually: just use WoB room, make that exit locked by Terra, do pallete swap if necessary)
  - **Status**: Implemented in event/whelk.py:167-172 (ruination_mod method).  Needs testing.
  - Modifies Whelk room palette to look like WOR
- ✅ **DONE** - Serpent Trench (must end at WoR Nikeah.  Probably just use WoB Nikeah docks with palette swap & music change.)
  - **Status**: Implemented in event/serpent_trench.py:290-306 (door_rando_mod method).  Needs testing.
  - Sets world to WOR and loads Nikeah entrance in ruination mode
- ❌ **TODO** - Doma Defense (Use WoB exterior doma map; lock entrance to Doma Dream behind this event)
  - **Status**: No ruination modifications found in event/doma_wob.py
- ❌ **TODO** - TunnelArmr check (how to deconflict with Figaro Castle?)
  - **Status**: No ruination modifications found in event/south_figaro_cave_wob.py
- **PASS** - Kefka at Narshe (deconflict with Ice Fields dragon.  Possibly: use WoB map until check is completed; then replace with WoR map when returning?)
  - **Status**: Not implemented in event/narshe_battle.py.  This is an option for future addition, but will not be in the initial release.

2. Modify checks that go to the world map, or go to the airship, so that they don't break the ruination map:
- ✅ **DONE** - Phantom Train (warp to train station?)
  - **Status**: Implemented in event/phantom_train.py:94-110 (door_rando_mod method)
  - In ruination mode, sends to Phantom Train station instead of world map
- ✅ **DONE** - Opera House (end up in lobby, not on airship)
  - **Status**: Implemented in event/opera_house_wob.py (character_mod and esper_item_mod methods)
  - In ruination mode, places player in Opera House lobby (map 0xed) at (60, 44) facing down
  - Sets WoR NPC bits before loading lobby map
- ✅ **DONE** - MTek 3 (end up in Vector, no battle on airship?)
  - **Status**: Implemented in event/magitek_factory.py:487-489, 421-442 (ruination_mod method and after_cranes_mod)
  - Returns to Vector in ruination mode instead of airship
- ✅ **DONE** - Lete River (end up in Esper World, hardcoded)
  - **Status**: Implemented in event/lete_river.py:227-319 (exit_river_mod method)
  - Hardcoded exit to Esper World with custom animation in ruination mode
- ✅ **DONE** - Floating Continent (same solution as in -drdc)
  - **Status**: Implemented in event/floating_continent.py (MAP_SHUFFLE flag includes ruination mode)
  - Uses door randomization/map shuffle handling
- ✅ **DONE** - Phoenix Cave (same solution as -drdc)
  - **Status**: Implemented in event/phoenix_cave.py (DOOR_RANDOMIZE flag includes ruination mode)
  - Uses door randomization handling

3. Figaro Castle is a special case: there's a conflict between the WoR entrance via the tunnel at SF cave, since it is reused as an entrance to Ancient Castle. Solution: remove the custom underground entrance before engine check is complete.  Player will walk into Figaro Castle from the main door, and the player can walk down to basement & fight engine boss at will.  Remove "resurfacing" animation.  Require fighting engine boss before accessing whatever is behind Ancient Castle entrance.  (Note this solution also deconflicts with Locke's Tunnelarmr check, since that room is now not used as part of engine room check.)
- ✅ **IMPLEMENTED** - Figaro Castle special handling
  - **Status**: Implemented in event/figaro_castle_wor.py and data/rooms.py
  - **Implementation details**:
    - Modified `ruin-figarocastle` room to enter via world map doors (1156-1159) instead of Ancient Cave door (1558)
    - Added key `fc-engine` to Engine Room (room 94) that unlocks door 1558 (Ancient Castle entrance)
    - Added `FIGARO_CASTLE_EMERGED_WOR` event bit constant (0x0c7) to prevent emerge animation
    - Set `PRISON_DOOR_OPEN_FIGARO_CASTLE` (0x2B7) after defeating Tentacles to graphically open jail cell door
    - Cleared blocker NPCs (BLOCK_INSIDE_DOORS_FIGARO_CASTLE) at game start so player can leave freely
    - Jail cell door starts closed and opens only after defeating Tentacles
    - Engine room guy dialog changed to "The passage to the Ancient Castle is now open" after boss defeat
    - No castle emerge/submerge animations in ruination mode

