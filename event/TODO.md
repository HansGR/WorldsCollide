# Todo list for Claude (-ruin mode updates)

## Updates to branch mapping code
1. Revise check if there are enough esper slots (line 1030):
As written, it will fail because it doesn't take into account the slots that were used for characters. For example: if requirements are 6 char and 9 espers, and the starting party is MOG, GOGO, UMARO, with added members RELM, GAU, SETZER, then we will have six characters, total_checks = 10, total_character_slots = 10, total_esper_slots = 10, and the check would pass. However, we actually used three of those checks to recruit three characters, so the actual remaining esper slots is just 7, and the check should fail.

2. Clean up unnecessary code at line 1008:
"planned_areas" is populated from CHARACTER_AREAS, and filled with items that are keys to RUIN_ROOM_SETS. None of these are also room names (the example 'ruin-whelk' does not appear).  The first check (lines 1004-1007) is correct and sufficient:

  if area_name in RUIN_ROOM_SETS and room_id in RUIN_ROOM_SETS[area_name]:

... correctly checks if 'ruin-whelk' (a ROOM_REWARD key) is in RUIN_ROOM_SETS['Narshe'] (which it is).  The second check (lines 1008-1015) is probably doing nothing, and should be removed.


## Updates to overall behavior of -ruin
1. When Gau is a character, the item "dried meat" must be available for purchase in at least one shop.  Something similar is done in the original randomizer via the flag -sdm N (--shops-dried-meat), which enforces N shops with dried meat available.  For -ruin, we must ensure that this flag specifically makes this number of dried meat available in accessible item shops, as not all shops will be accessible in ruination mode.  Accessible shops may be in WoR towns with item shops (Kohlingen, Nikeah, Thamasa, South Figaro, Albrook, Tzen, Jidoor... Maranda?), plus WoR Figaro Castle, Returners Hideout, Phantom Train shops, and possibly the merchant at Gau's Dad's House (if the WoB version is used).  However, which shops are actually accessible depends on the branch mapping, which must be taken into account: the accessible shops must be used and NOT be gated by the Veldt check.  Probably this will require some modification of Veldt check to make sure that it is not added as a character check until some item shop has been added, and the list of pre-Veldt item shops must be recorded for forcing dried meat to be available.

2. Ruination mode needs to get rid of the abundance of healing options in the standard game.
- Force '-gpm 0' (zero GP from all battles) for all -ruin seeds: only starting money + selling equipment.
- Decide what to do with unlimited healing spots: either make them a limited resource, add a cost, or make them heal HP only (not MP).  Identify all unlimited heals and make a decision for each
  - Bucket in School: 3 uses (implemented)
  - Healing Spring in Phantom Forest:  Randomize outcome from a list (incl. bad outcomes)
  - Free beds: heal only HP.
      - Sabin's house, Mobliz WoR relic shop, Narshe Weapon shop, Duncan's house, Gau's Dad's House, ...
      - Include a 3/8 chance of being attacked in the night: forced back attack, selected boss or difficult mob, attacked before healing.
  - Phantom Train food:  Add a cost to the meal?  Or randomize outcome from a list (incl. bad outcomes).  Or both: "Premium meal" for [1000---10000] GP, or "cheap meal" for [1-100] GP, with differently chosen outcomes.  I like it! 
- Increase all inn costs by a multiplier (3x?)

3. Change the starting menu to be -ruin specific.  In Ruination mode, there is only one save slot, and it gets wiped when you die.  Get rid of the "load a save file" menu; replace it with alternate starting menu (New Game, Flags, Config) with an added "Load Saved Game" option

4. Decide what to do with Warp spell.  It could move the current party to Esper World, or reset all parties and move to Esper World, or do nothing since we have the Warp Points (but still usable in battle).
   
5. [low priority] Add a custom splash graphic for RUINATION - Final Fantasy 6 Roguelike

   
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

