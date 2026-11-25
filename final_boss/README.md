# Final bosses

`-fb VALUE` (`--final-boss`) chooses who the last tier of the final battle is.

| Value | Final boss |
|-------|------------|
| `kefka` | Kefka, as he is. The default; `-fb` is then left out of the flag string, so seeds rolled without it stay the same |
| `ultimaro` | Ultimaro: a giant Umaro |
| `uncleulty` | Uncle Ulty: a giant Ultros |
| `grampaluma` | Grampaluma: a giant Dadaluma who calls in ChromeFists |
| `kingpug` | King Pug: a giant Pug with WallChange and Life Mine |
| `czardragon` | CzarDragon: the game's unused boss, with the highest magic of all eight elements |
| `juggernaut` | Juggernaut: a giant TunnelArmr, armored against blows, who answers magic |
| `random` | One of the above, chosen by the seed. The spoiler log names it |

## Battle programs

Each boss below has its **battle program** first (the turn order and the odds, by the names the attacks have in the battle), then what its attacks are. **Keep the programs up to date when a script changes**: they are what a playtester reads. Write amounts as decimals or fractions (1.2x speed, 1/3), and every turn as its three choices (A / B / C), not as odds in words.

How to read them:

- Each turn the boss does the first thing, from the top, whose condition is true. "Every turn" entries are extra: they are done and the turn goes on with what follows.
- A numbered list is one turn per entry, in order, then again from its first entry.
- "A / B / C" is one of the three, 1/3 each: a name written twice is 2/3 ("Tentacle / nothing / nothing" is Tentacle 1/3, nothing 2/3). "Then" is a second action in the same turn.
- HP conditions are percentages of his full HP. He changes list as soon as his HP crosses one (also upward, if he is healed), and the new list starts at its first entry.
- Battle is his plain attack. With `-sfb` and ability scaling (`-ase`, `-asr`), the spells in a program (Ice 3, Train, Fallen One, Meteor, Ultima...) are scaled as final Kefka's are; the boss's own attacks are not.

## Ultimaro

Umaro at 2x the size of his sprite (without the shadow under his feet: he is in the air).

**Stats:** final Kefka's, with +5 levels (after scaling and objectives) and 1.2x speed. Absorbs ice, as Umaro does.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Yeti used a Green Cherry!", and he charges up as a green cherry appears
2. U'ghaaaa
3. Meteor

**At 53% HP and below:**
1. "Yeti used a Green Cherry!", and he charges up as a green cherry appears
2. U'ghaaaa
3. Yeti Punch / Ice 3 / Enrager, then Yeti Punch / nothing / nothing
4. Train / Yeti Punch / Jump, then Yeti Punch / Jump / nothing

**Above 53% HP:**
1. Fallen One
2. Battle / nothing / Yeti Punch
3. Storm / Train / Yeti Punch
4. Battle / nothing / Yeti Punch
5. Ice 3 / Train / Yeti Punch
6. Battle / nothing / Yeti Punch
7. Surge / nothing / Yeti Punch

**When he is hit** (not while he charges up or in the turns after U'ghaaaa):
- Below 17% HP, when damaged: nothing / Battle / Ultima
- Below 49% HP, when damaged: nothing / Battle / Yeti Blast

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Yeti Punch** is Havoc Wing (his special: a blow at 4x damage), with the looks of Umaro's Tackle.
- **Yeti Blast** is HyperDrive and **U'ghaaaa** is Goner, renamed.
- **Enrager** is Revenger remade: the Bserk spell on the whole party at 0.5x its hit rate (75), which Reflect and Runic do not stop.
- **Jump**: as Umaro jumps. He lands 2 to 4 times, as with a Dragon Horn: down and straight back up for each landing, with the damage showing as he leaves.
- The green cherry is in the place of Kefka's laughing head. Its art is `graphics/green_cherry.py`.
- From final Kefka's script: Storm was Fire 3, Surge was Bolt 3, the Ice 3 at 53% and below was Train, and the two Jumps were a Revenger and a Havoc Wing.

## Uncle Ulty

Ultros (the one with all his tentacles) at 2x the size of his sprite, without his shadow, and low enough on the screen to be clear of the boxes at the top.

**Stats:** final Kefka's, with +5 levels (after scaling and objectives), 1.0x speed, and 65535 HP (1.1x Kefka's 62000 would be 68200: 65535 is the most an enemy can have, 1.057x). Absorbs water.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Gwee-hee-hee...", "It's my special recipe!", and he charges up as a shrimp appears
2. Gumbo
3. Meteor

**At 53% HP and below:**
1. "Gwee-hee-hee...", "It's my special recipe!", and he charges up as a shrimp appears
2. Gumbo
3. Tentacle / CleanSweep / Imp Sonata, then Tentacle / nothing / nothing
4. Train / Tentacle / Imp Sonata, then Tentacle / Tentacle / nothing

**Above 53% HP:**
1. Fallen One
2. Battle / nothing / Tentacle
3. Fire 3 / Train / Tentacle
4. Battle / nothing / Tentacle
5. Ice 3 / Train / Tentacle
6. Battle / nothing / Tentacle
7. CleanSweep / nothing / Tentacle

**When he is hit** (not while he charges up or in the turns after Gumbo):
- Below 17% HP, when damaged: nothing / Battle / Ultima
- Below 49% HP, when damaged: nothing / Battle / Ink Blast

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Tentacle** is Havoc Wing (his special: a blow at 4x damage), with the looks and sound of the Tentacle attack.
- **Ink Blast** is HyperDrive with its palettes in ink, and it blinds.
- **Gumbo** is Goner, in blue and black where Goner was red. It blinds everyone it hits, and may muddle each of them, as his Lv.3 Muddle did: a hit rate of 65 against magic block, rolled for each target (`status_chance_mod`, a special effect for the attack, since its own statuses always take).
- **Imp Sonata** is Revenger remade: the Imp spell on the whole party with a hit rate of 110, which Reflect and Runic do not stop. As the spell does, it turns an imp back.
- The shrimp is in the place of Kefka's laughing head (`graphics/shrimp.py`).
- From final Kefka's script: the CleanSweep above 53% was Bolt 3, and the one at 53% and below was Train. Fire 3 and Ice 3 stay.

## Grampaluma

Dadaluma, in purple pants (the strong reds, oranges and yellows of his palette in purple: his ornaments too), at 1.21x his size (107x68 pixels; he is 88 wide, so the most that fits a formation's 128 pixels is 1.43x, which crowded the screen and its sprites). He calls in two ChromeFists, as Dadaluma does his Iron Fists.

**Stats:** final Kefka's, with +0 levels, 1.2x speed and 0.8x vigor (the power of his blows: Battle, Tiger Claw and the jump). Weak to poison as Dadaluma is, where final Kefka takes no damage from it (he is still protected from the poison status). He can be slowed and hasted.

### Battle program

**Every turn** (extra actions: his turn goes on with the lists below):
- When his timer is above 30 (about a minute; it then starts over) and both ChromeFists are dead or gone: he whistles and calls in two. They are not in the battle at its start.
- Once, below 25% HP: X-Potion / X-Potion / Potion, 3 times, then Safe on himself.
- Once, when he has been hit by Fight 4 times: he throws a Wing Edge at a random character.

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Friends! Lovely to see you.", and he charges up
2. Chi Shock
3. Meteor

**At 53% HP and below:**
1. "Friends! Lovely to see you.", and he charges up
2. Chi Shock
3. Tiger Claw / MithrilKnife / Time Warp, then Sweep / nothing / nothing
4. Train / Tiger Claw / Jump, then MithrilKnife / Sweep / nothing

**Above 53% HP:**
1. Fallen One
2. Battle / nothing / Sweep
3. MithrilKnife / Train / Tiger Claw
4. Battle / nothing / Tiger Claw
5. HyperDrive / Train / Sweep
6. Battle / nothing / Tiger Claw
7. Sweep / nothing / Tiger Claw

**When he is hit:**
- By Fight: one more hit counted for the Wing Edge (and then what follows)
- Below 17% HP, when damaged (not while he charges up or in the turns after Chi Shock): nothing / Battle / Ultima
- Below 49% HP, when damaged (the same): nothing / Battle / HyperDrive

**When he dies:** the final death, and every enemy goes with him.

**ChromeFist, each turn:** a thrown Dirk at a random character (1/2), or Battle 2 times (1/2).

The heal usually takes him back above 53% HP (an X-Potion is 9999 HP to him): he then leaves the list he was in, Chi Shock or not, and starts the one above 53%.

### Attacks

- **Tiger Claw** is Havoc Wing (his special: a blow at 4x damage), renamed. **HyperDrive** is as it was.
- **Chi Shock** is Goner, and also saps everyone it hits. He charges up before it as final Kefka does, without the laughing head (it is replaced by an empty picture).
- **Time Warp** is Revenger remade: Slow 2 on the whole party (hit rate 150, which Reflect and Runic do not stop), and Haste for every enemy in the battle, whether it hits or not. An enemy protected from Slow or Haste is protected from both, so he and the ChromeFists are protected from neither.
- **Sweep**, Dadaluma's special, is an attack of its own (in the place of Confusion, which nothing in the game uses): a blow on one character with 0.44x Tentacle's power (0.5x, and then lowered as his vigor was: an attack's power is its own), which saps. It looks and sounds like Dadaluma's own Sweep: the blow his special attack is shown with (`attack_special_animation_mod`).
- **MithrilKnife** is thrown at a character. **Jump** is Ultimaro's (2 to 4 landings).
- From final Kefka's script: above 53% the MithrilKnife was Fire 3, HyperDrive was Ice 3, the last Sweep was Bolt 3 and the other two Sweeps were Havoc Wings. At 53% and below the MithrilKnife in the third turn was Train, the Jump was a Revenger, and the turn's second actions were Havoc Wings.

### ChromeFists

A ChromeFist is a Scrapper (the highest of the enemies with the Iron Fist's looks: speed 37, defense 125, magic defense 145, absorbs poison) with 3500 HP, level 38 (the Scrapper's is 34), vigor 14 (10) and evade 60 (120), in a dark chrome palette (the Iron Fist's colors by their brightness, as greys). It is an enemy of its own in the place of one no formation has (382), so the others are as they were. It is protected from all statuses but death, slow and haste. When Grampaluma dies they go with him.

### How his script is made

A script is blocks: each turn, from the top, the first block whose conditions are all true is the monster's turn. What Dadaluma does (the call, the heal, the Wing Edge) is blocks before final Kefka's, so they are tested every turn. A block that ends a turn also has the script start over, which for final Kefka's is Fallen One, so each of them ends with a condition that is never true: what is before it is done, and the turn goes on with final Kefka's script where it was. The hits are counted the same way where his script answers being hit, before what final Kefka's does there.

## King Pug

Pug (the green one) at 3x the size of his sprite, crowned (96x96 pixels). His sprite is Pug's at 1.5x (`graphics/king_pug.py`, 48x48 pixels: scale3x, then every 2x2 pixels as one) shown at 2x, so its pixels are as large as Ultimaro's. The crown is drawn by hand at the 1.5x size, so its pixels are as large as his: two golds that take the place of two colors of Pug's palette, whose pixels have the nearest of his others (the brighter for the near points and the band, the darker for the far points between them).

**Stats:** final Kefka's, with +0 levels, 1.0x speed, 1.2x vigor (the power of his blows: Battle and Cleaver) and 65535 HP (1.057x). Absorbs water, as the pugs do, until his first WallChange.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "......", and he charges up as his lantern lights up and shines
2. Grudge Ray
3. Meteor

**At 53% HP and below:**
1. "......", and he charges up as his lantern lights up and shines
2. Grudge Ray
3. Cleaver / Life Mine / Lullaby, then Cleaver / nothing / nothing
4. Train / Cleaver / Lullaby, then Cleaver / Cleaver / nothing

**Above 53% HP:**
1. Fallen One
2. Battle / nothing / Cleaver
3. Weakness spell / Train / Cleaver
4. Battle / Slow 2 / Cleaver
5. Life Mine / Train / Cleaver
6. Battle / nothing / Cleaver
7. Stop / Slow 2 / Cleaver

**When he is hit:**
- When an attack with an element (a spell, or a weapon with one) damages him: WallChange. Nothing else below is done for that hit. An attack with no element, or one that does him no damage (he takes none from 7 of the 8 elements after a WallChange, and absorbs one), does not.
- Below 17% HP, when damaged (not while he charges up or in the turns after Grudge Ray): nothing / Battle / Ultima
- Below 49% HP, when damaged (the same): nothing / Battle / Life Mine
- At 49% HP and above, when damaged (the same): nothing / Battle / Battle. Final Kefka does nothing when hit there.

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Cleaver** is Havoc Wing (his special: a blow at 4x damage), renamed. The pugs' own Cleaver is 8x.
- **WallChange**, on himself: he is weak to one element (chosen at random each time), takes no damage from the other seven, and absorbs one of those. Attacks with no element are as they were.
- **Weakness spell** is the spell Master Pug casts for the element he is weak to: fire Ice 3, ice Fire 3, bolt W Wind, poison Pearl, wind Bolt 3, pearl Bio, earth CleanSweep, water Quake. Before his first WallChange it is Battle. (`WEAKNESS` in `data/enemy_script_custom_commands.py`: an attack value a script can choose as it does attacks.)
- **Life Mine** is an attack of its own (in the place of Confusion, which nothing in the game uses, as Grampaluma's Sweep is: a seed has one final boss): Step Mine's looks, on one character, for that character's experience / 64, whatever the defenses. 1067 at level 30, 3668 at level 45, 8773 at level 60, and 9999 from level 63 on (`experience_damage_mod`). A character who joins at a level has that level's experience.
- **Lullaby** is Revenger remade: the Sleep spell on the whole party with a hit rate of 90 (the spell's is 111), which Reflect and Runic do not stop.
- **Stop** is the spell, on one character.
- **Slow 2** is the spell, on the whole party.
- **Grudge Ray** is Goner, renamed, in green and gold where Goner was red: the background and he turn green, then gold, then green again, and its streaks are gold (`goner_colors_mod`). It may also stop each one it hits: a hit rate of 65 against magic block, rolled for each target, as Uncle Ulty's Gumbo may muddle. Before it his lantern lights up and shines: a picture of its glass lit, with rays (`graphics/lantern_glow.py`), is shown over it in the place of Kefka's laughing head and taken away. The picture can only be put in steps of 16 pixels (`goner_sprite_mod(..., move)`), so he is where in his mold puts the glass under it (`giant_sprite_mod(..., lower, right)`), and the lit glass is 4 pixels below the middle of the picture.
- From final Kefka's script: the weakness spell was Fire 3, the Life Mine above 53% was Ice 3 and Stop was Bolt 3. At 53% and below Life Mine was Train, and when he is hit it was HyperDrive.

## CzarDragon

CzarDragon, a boss the game has an enemy for and never uses. His sprite is the one a later release of the game gave him, with wings and a tail (`graphics/czar_dragon.py`: from a picture of it, 118x111 pixels in 15 colors), shown at its own size, which nearly fills a formation's 128 pixels, and low enough to be clear of the boxes at the top. The enemy's own looks in this game are the Blue Dragon's sprite in a black, red and gold palette (64x96 pixels).

**Stats:** final Kefka's, with +0 levels, 1.2x speed, 0.9x defense (105) and 1.2x magic defense (162). He takes half the damage of fire, ice and bolt, absorbs wind (his own Merton, fire and wind, hits both sides and heals him) and takes the full damage of poison (final Kefka takes none), pearl, earth and water. He flies, as final Kefka and every final boss does (Float, which is not taken away), so what misses those who float misses him: his own Quake, which hits both sides, and the party's.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Mwa ha ha... Prepare yourselves!", and he charges up as his eye flashes and fire comes out of his nostrils
2. Megiddo
3. Meteor

**At 53% HP and below:**
1. "Mwa ha ha... Prepare yourselves!", and he charges up as his eye flashes and fire comes out of his nostrils
2. Megiddo
3. Merton / N. Cross / Terror, then Giga Volt / Bio / nothing
4. Aero / Quake / Terror, then Pearl / El Nino / Havoc Wing

**Above 53% HP:**
1. Fallen One
2. Fire 3 / Ice 3 / Bolt 3
3. Battle / nothing / Havoc Wing
4. Bio / Aero / Quake
5. Battle / Train / nothing
6. Pearl / El Nino / Train
7. Battle / nothing / Havoc Wing

**When he is hit** (as final Kefka):
- Below 17% HP, when damaged (not while he charges up or in the turns after Megiddo): nothing / Battle / Ultima
- Below 49% HP, when damaged (the same): nothing / Battle / HyperDrive

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **His eight elements**, the highest attack of each that an enemy can use on the party: Fire 3, Ice 3, Bolt 3 and Bio (one character), Pearl (one character), Aero (wind, the whole party), Quake (earth, everyone on both sides who does not float: he does) and El Nino (water, the whole party, not dodged). With ability scaling at random (`-sfb -asr`) these are scaled as final Kefka's spells are and may not keep their elements.
- **At 53% HP and below** three of them are stronger: Merton (fire and wind, everyone on both sides, not dodged: he absorbs it), N. Cross (ice: it freezes whom it hits, at random among the party, with no damage) and Giga Volt (bolt).
- **Havoc Wing** is final Kefka's (his special: a blow at 4x damage), in 3 turns of the lists above where Kefka has it in 9.
- **Megiddo** is Goner, renamed, and it sets one status on each one it hits, chosen for each: Dark, Poison, Imp, Mute, Muddle, Sleep, Slow or Stop, 1/8 each (`random_status_mod`). One who is protected from the status chosen gets none. As he charges up before it his eye flashes and fire comes out of his nostrils: a picture of them (`graphics/czar_fire.py`) is shown over his head in the place of Kefka's laughing head and taken away, as King Pug's lantern lights up.
- **Terror** is Revenger remade: the Drain spell on the whole party with a power of 100 (the spell's is 38), with Revenger's looks, which Reflect and Runic do not stop and which is not dodged. He gets the HP each one loses.

## Juggernaut

TunnelArmr at 1.33x the size of his sprite (127x79 pixels, the most that fits a formation's 128 pixels wide), without his shadow, low on the screen, and in chrome: his purple body in a dark cerulean chrome, his wheels and claws in bright chrome, and the red mark on his nose as it was.

**Stats:** final Kefka's, with +0 levels, 1.8x defense (211: a blow does 0.32x what it does to final Kefka) and 0.75x magic defense (101: a spell does 1.28x). Weak to bolt and water, as TunnelArmr is. Image, Clear, Reflect, Safe, Shell and Regen can be set on him, by the party or by his own MirrorCast (Fenrir, Phantom, Carbunkl, ZoneSeek, Kirin), where final Kefka is protected from every status. He can be sapped too: the game blocks Regen and Seizure together or not at all. Since he can be made clear, the seed has the vanish/doom fix whether `-fvd` is set or not: a spell that kills does not get past his protection.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "MagiTek engine going critical!", and he charges up
2. Soul Flare
3. Meteor

**At 53% HP and below:**
1. "MagiTek engine going critical!", and he charges up
2. Soul Flare
3. Drill / Train / MirrorCast, then Drill / nothing / nothing
4. Train / Drill / MirrorCast, then Drill / Launcher / nothing

**Above 53% HP:**
1. Fallen One
2. Battle / nothing / Drill
3. Atomic Ray / Train / Drill
4. Battle / nothing / Drill
5. Shrapnel / Train / Drill
6. Battle / nothing / Drill
7. Diffuser / nothing / Drill

**When he is hit:**
- By Magic, X-Magic, a Lore or an Esper, at any HP (not while he charges up): Missile / Diffuser / Atomic Ray. Nothing else below is done for that hit.
- Below 17% HP, when damaged (not while he charges up or in the turns after Soul Flare): nothing / Battle / Ultima
- Below 49% HP, when damaged (the same): nothing / Battle / Crush

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Drill** is Havoc Wing (his special: a blow at 4x damage), with the looks of TunnelArmr's Drill.
- **Soul Flare** is Goner with a power of 120 (12x Rasp's; Goner's is 220), and it takes from each one's MP what it takes from their HP, which is no more than the MP they have: one with 300 MP loses 300 HP and 300 MP, and one with 0 MP loses nothing (`mp_damage_mod` with `mp_cap`). He charges up before it, and in the place of Kefka's laughing head the red logo on his nose glows and gives off rays up and to the right (`graphics/juggernaut_logo.py`).
- **MirrorCast**, in the place of Revenger: he casts the esper that one of the party has equipped. A character of the party is chosen at random, and the next ones are tried if that one is dead or gone, has no esper, or has Ragnarok (which changes its target into an item). With none to cast it is Diffuser. It is named MirrorCast at the top of the screen (as the Magicite item names itself and not its esper), and the esper is shown as it is to a party attacked from behind: on his side. The party stays where it is while his esper is there (a summon hides the party; its colors still flicker dark as the esper comes and goes). It is his: it hits the party with his level and magic power, and one that heals or protects does so for him: Fenrir's Image, Phantom's Clear, Carbunkl's Reflect, ZoneSeek's Shell and Kirin's Regen take. With Golem he has a wall of his own: it has 9999 HP, and while it has any a physical attack takes its damage from the wall and not from his HP, the damage the wall took is shown on him (as for a character, it is worked out with a defense of 192 in place of his own), and Golem's hand comes up in front of him to take a Fight (`golem_mod`; the game's wall is the party's, whoever calls it). Odin and Raiden kill and Shoat turns to stone whoever is not protected. With Palidor he is carried off, and he lands on one of the party in a later turn (`carried_jump_mod`). (`MIRROR_CAST` in `data/enemy_script_custom_commands.py`. The espers that attack are kept from hitting characters by a flag of their data, which does not hold for him.)
- **Launcher**, once in the lists: several strikes on the party that each take a part of what HP the one hit has left. It does not kill.
- **Missile** takes 1/4 of the HP its target has left, and saps.
- **Atomic Ray** (fire, the whole party), **Shrapnel** (no element) and **Diffuser** (bolt, the whole party) are the armors' attacks, where final Kefka has Fire 3, Ice 3 and Bolt 3.
- **Crush** is HyperDrive, renamed, with the looks of Io's Crush (`attack_special_animation_mod`).


## Negarapa

Nerapa at 1.75x the size of her sprite (112 pixels high: at twice the size her head would be behind the boxes at the top of the screen), 16 pixels lower and 20 to the right. Death on a clock: she starts as Nerapa does, with Condemned on each of the party, and her attacks kill outright or take a part of the HP there is, with Nerapa's fire.

**Stats:** final Kefka's, with +0 levels. She absorbs fire, as Nerapa does, and is weak to ice and pearl.

### Battle program

**Her first turn:** Condemned on each of the party.

**Below 13% HP** (if she is charging up from the list below when her HP gets here, she does that one first):
1. "Mwa-ha-ha... You think", then "I'm going to let you escape?", and she charges up
2. Last Rites
3. Meteor

**At 53% HP and below:**
1. "Mwa-ha-ha... You think", then "I'm going to let you escape?", and she charges up
2. Last Rites
3. Quartr / Fire 3 / X-Zone, then Demon Whip / Doom / nothing
4. Merton / Quartr / Battle, then Flare / nothing / nothing

**Above 53% HP:**
1. Fire 3 / S. Cross / Demon Whip
2. Battle / Demi / nothing
3. Fire 3 / Doom / Demon Whip
4. Battle / Roulette / nothing
5. S. Cross / Demi / Demon Whip
6. Battle / Doom / nothing

**When she is hit:**
- Below 17% HP, when damaged (not while she charges up or in the turns after Last Rites): nothing / Battle / Ultima
- At any other HP (not while she charges up): Demi / Shimsham / nothing, on who hit her

**When she dies:** the final death, and every enemy goes with her.

### Attacks

- **Condemned** counts down over each one's head, and Doom is cast on them when it gets to 0. The count starts at 81 - (her level + a number below her level), and at 20 at the least: at her level of 71 it is always 20, which was 40 seconds for a party that did nothing. One who dies and is raised is no longer condemned.
- What she says before Last Rites is Nerapa's one line in the game. The box at the top holds 32 letters, so it is said in two texts, one after the other.
- **Last Rites** is Goner, renamed, and it sets Condemned on those it hits: on those who are no longer condemned. One who still is keeps the count they have.
- **Demon Whip** is final Kefka's Havoc Wing (her special: a blow at 4x damage), renamed, and shown as a red line across its target with the sound of a flail (a blow of its own in the table of the blows that specials are shown with, which no monster used).
- **Demi** takes 1/2 of the HP its target has, **Quartr** 3/4 from the whole party, and **Shimsham** 1/2. **Doom** and **X-Zone** (the whole party) kill those who are not protected from death. **Roulette** kills the one its cursor stops on, of everyone in the battle: she is protected. Reflect sends Demi, Quartr, Doom and X-Zone back at her, and they do nothing to her.
- **S. Cross** is fire on the whole party, and **Merton** is fire and wind on everyone on both sides, not dodged: she absorbs it.
- **When she dies** the counters over the condemned are stopped and taken away (`no_counters_in_final_death_mod`). It is the game's own bug that with any of them shown, dark bars are over the whole background while the final boss crumbles.
- Before Last Rites final Kefka's laughing head is shown as a skull with skin hanging off it: his head as it is in the game, in other colors (its four lighter colors are bone, its two darkest the skin, and what trails under the head is all skin), and a few details changed. His head is in profile, looking up and to the right: the eye is an empty socket, the nose is hollow and without its tip (the bone of a nose goes about halfway), the open mouth is empty behind the row of teeth he shows, and the lower jaw has a row of teeth too (`graphics/skull.py`).

## How a final boss is made

Every final boss is final Kefka's enemy (298), in his formation and running his battle script, made over. A final boss is a subclass of `FinalBoss` (`final_boss/final_boss.py`), whose methods are called as the seed is built:

| Method | Called from | For |
|--------|-------------|-----|
| `enemies_mod(enemies)` | `data/enemies.py`, with the other enemies | Name, stats, elements: `self.enemy(enemies)` is his `Enemy` |
| `scripts_mod(scripts)` | `data/enemy_scripts.py`, before abilities are scaled | His battle script: `scripts.get_script(self.ENEMY)` |
| `data_mod(data)` | `data/data.py`, as the data is written | Attack names, spell data, battle text |
| `battle_mod()` | `battle/final_boss.py` | Code and graphics of the battle |

`final_boss.OWN_ABILITIES` are the attacks only final Kefka has, which the other final bosses change (HyperDrive and Goner). With `-fb` (a named boss or `random`, even when the random one is Kefka, so that the scaled attacks of other enemies do not tell which it is) ability scaling (`-ase`, `-asr`) gives them to no other enemy, as they are taken out of its tiers, and with `-sfb` the final boss's own are not scaled into other attacks. Without `-fb` (or with `-fb kefka`, the default, which is not in the flags) scaling is as it was. No other enemy's script has them. In the vanilla data HyperDrive is also one of Siegfried's (enemy 55) attacks under Control, which is left as it is.

`LEVELS` is how many levels he is above final Kefka (`battle/load_enemy_level.py` adds them when the battle loads him, so they follow level scaling and the objectives' levels).

`FinalBoss` itself is Kefka: it changes nothing. It also has what the others share:

- `giant_sprite_mod(enemy, shadow_color, shadow_rows)` gives him the sprite of an enemy, giant and in that enemy's palette: at twice its size if that fits the 128x128 pixels of a large mold (a monster with a small mold, up to 64x64 pixels, does), or else as large as fits (Dadaluma, 88 pixels wide, is 1.45 times his size), or at `scale = (factor, divisor)`. The enemy needs 4bpp graphics. A shadow under its feet can be removed.
- `giant_sprite_mod(..., pixels = rows, palette = colors)` shows a sprite drawn for him (rows of palette indices) in the place of the enemy's, and 16 colors in the place of the enemy's palette.
- `giant_sprite_mod(..., lower = pixels)` puts a sprite less high than the mold lower in it, to be clear of the boxes at the top of the screen. His place in the formation is Kefka's, so the death animation is too.
- `golem_mod(hp, hand = (130, 88))` gives him Golem's wall when he calls it: physical attacks do him no damage until they have done it this much (the damage is shown, and taken from the wall). Golem's hand is shown at `hand` on the screen when the wall takes a Fight (the game only shows it for a character: the Fight animation is given Golem's block for him too, and the hand's place, which the game reads from the character, is given).
- `mp_damage_mod(data, attack)` has an attack take from its targets' MP what it takes from their HP.
- `half_damage_mod(elements)` has him take half the damage of elements, which an enemy's data has no place for.
- `random_status_mod(data, attack, statuses)` has an attack also set one of 8 statuses, chosen for each target it hits.
- `goner_sprite_mod(pixels, palette)` shows a 32x32 picture where Kefka's laughing head appears before Goner.
- `goner_text_mod(data, text)` is what is said before Goner. A line holds some 32 letters.
- `special_attack_animation_mod(attack)` gives his special attack (Havoc Wing) the looks and sound of another attack.
- `party_status_attack_mod(data, spell, hit_rate)` makes Revenger a spell cast on the whole party.
- `add_palette(colors)` adds a battle animation palette (there is room for 8).

To add a final boss:

1. Write its class in a module of its own here. `ultimaro.py` is the example.
2. Add its name and class to `_FINAL_BOSSES` in `final_boss/__init__.py`. The name is the `-fb` value.
3. Add `-fb <name>` to `EXTRA_FLAGS` in `tests/rom_smoke.py`.

Rules to keep:

- Change nothing unless the final boss is chosen. With `-fb kefka` a seed must be what it was before the final boss existed: no space allocated, no random number drawn.
- The order of final bosses in `_FINAL_BOSSES` is what `-fb random` chooses from. Add new ones at the end, or old random seeds change.
- A final boss that changes something shared (an attack another enemy uses, an animation, a palette) changes it for the whole seed. Ultimaro only changes what final Kefka alone uses: check before reusing.
- `helpers_mod(enemies, helper, positions, boss_position)` puts helpers in his formation, and `helpers_layout_mod(boss_tiles, helper_tiles)` makes the room for their graphics. A formation's monsters share 16x16 tiles of graphics (128x128 pixels) which its mold divides between them, and the final formation's mold gives all of it to one monster: this adds a mold (13) where the boss has the top and the helpers a row under him. The molds, the sprite lists of each mold's monsters, the pointers to both and the sprites themselves are all moved to bank F0 to make room for it (bank C2 has little). In the final battle the monsters are drawn as sprites of 32x32 pixels, which do not divide such a mold, so the code that writes them is taught 16x16 sprites for what is left at the right and bottom of each monster (`_small_sprites_mod`). Not handled: a monster of this mold flipped (the flipped lists assume 32x32 sprites), which the final battle does not do.
- `helper_enemy_mod(enemies, source, name)` makes the helpers an enemy of their own from another (`HELPER_ENEMY`), and `helper_palette_mod(source, palette)` gives them that enemy's looks in another palette (`monster_palette(enemy)` reads one).
- `chance_condition_mod()` adds a script condition the game does not have, in the place of one it does not use: `If(CHANCE, n, 0)` is true n times in 256. Conditions are tested as the script is read and variables are set when the turn is taken, so a choice between two blocks is made by a variable set from the chance the turn before (the ChromeFists' script).
- `party_statuses_mod(data, attack, statuses_byte, statuses)` makes an attack also set statuses on every enemy in the battle. `new_attack_mod(data, attack, source, name, animation_source)` makes an attack nothing uses into a new one. `jump_mod()` and `jump_animation_mod()` are the Dragon Horn jump and its landings. In a script, `JUMP` and `THROW` (`data/enemy_script_custom_commands.py`, `command_attacks_mod`) can be chosen as attacks are.
- The final boss's death (he crumbles from his feet up as he sinks) is made for final Kefka: it crumbles the formation's 16x16 tiles of graphics from the last row up, and puts the falling sand on a layer at (16, 16), where Kefka is. With the helpers' mold `_helpers_death_mod` puts the sand's layer where the boss is and starts the crumbling at his last row (the rows under his are the helpers', which crumble at once). A boss alone in the formation at Kefka's place, as Ultimaro and Uncle Ulty are, needs neither.
- `damaged_condition_mod()` adds another script condition in that same place (a final boss has one or the other): `If(DAMAGED, 0, 0)` is true when the monster has lost more HP than at its last test, for a block of the answers to being hit ("this hit damaged him": put it first in the block). The game's own "if damaged" (0x05) is true for every hit once anyone has ever damaged the monster.
