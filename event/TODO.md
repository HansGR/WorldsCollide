# Todo list for Claude (-ruin mode updates)

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

2. ✅ **IMPLEMENTED** - Implement -ruin as a "meta-flag", that sets a default flagset which can subsequently be modified by calling other flags.  This bakes in some desired flags to -ruin while allowing the player flexibility to define other options.  The option of `-ruin minimum` could skip the defaults and require the player to choose everything.
- **Implementation**: args/ruin_preprocessor.py provides argument preprocessing that expands `-ruin` into ~70 default flags
- **Usage**:
    - `-ruin` - Injects all default flags (recommended settings)
    - `-ruin minimum` - Skips all defaults, requires manual flag selection
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
  - Free beds: heal only HP.
      - Sabin's house, Mobliz WoR relic shop, Narshe Weapon shop, Duncan's house, Gau's Dad's House, ...
      - Include a 3/8 chance of being attacked in the night: forced back attack, selected boss or difficult mob, attacked before healing.
  - Phantom Train food:  Add a cost to the meal?  Or randomize outcome from a list (incl. bad outcomes).  Or both: "Premium meal" for [1000---10000] GP, or "cheap meal" for [1-100] GP, with differently chosen outcomes.  I like it! 
- Increase all inn costs by a multiplier (3x?)

4. Change the starting menu to be -ruin specific.  In Ruination mode, there is only one save slot, and it gets wiped when you die.  Get rid of the "load a save file" menu; replace it with alternate starting menu (New Game, Flags, Config) with an added "Load Saved Game" option

5. Decide what to do with Warp spell.  It could move the current party to Esper World, or reset all parties and move to Esper World, or do nothing since we have the Warp Points (but still usable in battle).
   
6. [low priority] Add a custom splash graphic for RUINATION - Final Fantasy 6 Roguelike

   
## Updates to specific checks to work with -ruin
1. Checks in the WoB that must be "moved" to WoR:
- Lone Wolf (must be moved to WoR Narshe treasure hut; animation moved to WoR Narshe; event must be added to Narshe Peak with Tritoch & deconflicted from Tritoch event)
- Moogle Defense (WoB room must be used, possibly with palatte swap; event must be initialized in the room, rather than at Arvis' house)
- Kefka at Narshe (deconflict with Ice Fields dragon.  Possibly: use WoB map until check is completed; then replace with WoR map when returning?)
- Opera House (deconflict with OH dragon.  Probably same solution as for Kefka at Narshe)
- Shadow's check at gau's dad's house (just use WoB gau's dad's house with pallete swap)
- Whelk (must be moved to WoR Narshe.  Actually: just use WoB room, make that exit locked by Terra, do pallete swap if necessary)
- Serpent Trench (must end at WoR Nikeah.  Probably just use WoB Nikeah docks with palette swap & music change.)
- Doma Defense (Use WoB exterior doma map; lock entrance to Doma Dream behind this event)
- TunnelArmr check (how to deconflict with Figaro Castle?)

2. Modify checks that go to the world map, or go to the airship, so that they don't break the ruination map:
- Phantom Train (warp to train station?)
- Opera House (end up in lobby, not on airship)
- MTek 3 (end up in Vector, no battle on airship?)
- Lete River (end up in Esper World, hardcoded)
- Floating Continent (same solution as in -drdc)
- Phoenix Cave (same solution as -drdc)
- Kefka at Narshe (end on same screen)
- 

3. Figaro Castle is a special case: there's a conflict between the WoR entrance via the tunnel at SF cave, since it is reused as an entrance to Ancient Castle. Solution: remove the custom underground entrance before engine check is complete.  Player will walk into Figaro Castle from the main door, and the player can walk down to basement & fight engine boss at will.  Remove "resurfacing" animation.  Require fighting engine boss before accessing whatever is behind Ancient Castle entrance.  (Note this solution also deconflicts with Locke's Tunnelarmr check, since that room is now not used as part of engine room check.)

