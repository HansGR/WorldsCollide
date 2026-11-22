# Final bosses

`-fb VALUE` (`--final-boss`) chooses who the last tier of the final battle is.

| Value | Final boss |
|-------|------------|
| `kefka` | Kefka, as he is. The default; `-fb` is then left out of the flag string, so seeds rolled without it stay the same |
| `ultimaro` | Ultimaro: a giant Umaro |
| `uncleulty` | Uncle Ulty: a giant Ultros |
| `grampaluma` | Grampaluma: a giant Dadaluma who calls in ChromeFists |
| `random` | One of the above, chosen by the seed. The spoiler log names it |

## Battle programs

Each boss below has its **battle program** first (the turn order and the odds, by the names the attacks have in the battle), then what its attacks are. **Keep the programs up to date when a script changes**: they are what a playtester reads.

How to read them:

- Each turn the boss does the first thing, from the top, whose condition is true. "Every turn" entries are extra: they are done and the turn goes on with what follows.
- A numbered list is one turn per entry, in order, then again from its first entry.
- "A, B or C" is one of the three, each as likely (1 in 3). "A or nothing (1 in 3 / 2 in 3)" gives other odds. "Then" is a second action in the same turn.
- HP conditions are percentages of his full HP. He changes list as soon as his HP crosses one (also upward, if he is healed), and the new list starts at its first entry.
- Battle is his plain attack. With `-sfb` and ability scaling (`-ase`, `-asr`), the spells in a program (Ice 3, Train, Fallen One, Meteor, Ultima...) are scaled as final Kefka's are; the boss's own attacks are not.

## Ultimaro

Umaro at twice the size of his sprite (without the shadow under his feet: he is in the air).

**Stats:** final Kefka's, 5 levels higher (after scaling and objectives) and a fifth faster. Absorbs ice, as Umaro does.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Yeti used a Green Cherry!", and he charges up as a green cherry appears
2. U'ghaaaa
3. Meteor

**At 53% HP and below:**
1. "Yeti used a Green Cherry!", and he charges up as a green cherry appears
2. U'ghaaaa
3. Yeti Punch, Ice 3 or Enrager; then Yeti Punch or nothing (1 in 3 / 2 in 3)
4. Train, Yeti Punch or Jump; then Yeti Punch, Jump or nothing

**Above 53% HP:**
1. Fallen One
2. Battle, nothing or Yeti Punch
3. Storm, Train or Yeti Punch
4. Battle, nothing or Yeti Punch
5. Ice 3, Train or Yeti Punch
6. Battle, nothing or Yeti Punch
7. Surge, nothing or Yeti Punch

**When he is hit** (not while he charges up or in the turns after U'ghaaaa):
- Below 17% HP, when damaged: nothing, Battle or Ultima
- Below 49% HP, when damaged: nothing, Battle or Yeti Blast

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Yeti Punch** is Havoc Wing (his special: a blow at 4 times the damage), with the looks of Umaro's Tackle.
- **Yeti Blast** is HyperDrive and **U'ghaaaa** is Goner, renamed.
- **Enrager** is Revenger remade: the Bserk spell on the whole party at half its hit rate (75), which Reflect and Runic do not stop.
- **Jump**: as Umaro jumps. He lands 2 to 4 times, as with a Dragon Horn: down and straight back up for each landing, with the damage showing as he leaves.
- The green cherry is in the place of Kefka's laughing head. Its art is `graphics/green_cherry.py`.
- From final Kefka's script: Storm was Fire 3, Surge was Bolt 3, the Ice 3 at 53% and below was Train, and the two Jumps were a Revenger and a Havoc Wing.

## Uncle Ulty

Ultros (the one with all his tentacles) at twice the size of his sprite, without his shadow, and low enough on the screen to be clear of the boxes at the top.

**Stats:** final Kefka's, 5 levels higher (after scaling and objectives), at Kefka's speed, with 65535 HP (a tenth more than Kefka's 62000 would be 68200: 65535 is the most an enemy can have). Absorbs water.

### Battle program

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Gwee-hee-hee...", "It's my special recipe!", and he charges up as a shrimp appears
2. Gumbo
3. Meteor

**At 53% HP and below:**
1. "Gwee-hee-hee...", "It's my special recipe!", and he charges up as a shrimp appears
2. Gumbo
3. Tentacle, CleanSweep or Imp Sonata; then Tentacle or nothing (1 in 3 / 2 in 3)
4. Train, Tentacle or Imp Sonata; then Tentacle or nothing (2 in 3 / 1 in 3)

**Above 53% HP:**
1. Fallen One
2. Battle, nothing or Tentacle
3. Fire 3, Train or Tentacle
4. Battle, nothing or Tentacle
5. Ice 3, Train or Tentacle
6. Battle, nothing or Tentacle
7. CleanSweep, nothing or Tentacle

**When he is hit** (not while he charges up or in the turns after Gumbo):
- Below 17% HP, when damaged: nothing, Battle or Ultima
- Below 49% HP, when damaged: nothing, Battle or Ink Blast

**When he dies:** the final death, and every enemy goes with him.

### Attacks

- **Tentacle** is Havoc Wing (his special: a blow at 4 times the damage), with the looks and sound of the Tentacle attack.
- **Ink Blast** is HyperDrive with its palettes in ink, and it blinds.
- **Gumbo** is Goner, in blue and black where Goner was red. It blinds everyone it hits, and may muddle each of them, as his Lv.3 Muddle did: a hit rate of 65 against magic block, rolled for each target (`status_chance_mod`, a special effect for the attack, since its own statuses always take).
- **Imp Sonata** is Revenger remade: the Imp spell on the whole party with a hit rate of 110, which Reflect and Runic do not stop. As the spell does, it turns an imp back.
- The shrimp is in the place of Kefka's laughing head (`graphics/shrimp.py`).
- From final Kefka's script: the CleanSweep above 53% was Bolt 3, and the one at 53% and below was Train. Fire 3 and Ice 3 stay.

## Grampaluma

Dadaluma, in purple pants (the strong reds, oranges and yellows of his palette in purple: his ornaments too), at 1.21 times his size (107x68 pixels; he is 88 wide, so the most that fits a formation's 128 pixels is 1.43 times, which crowded the screen and its sprites). He calls in two ChromeFists, as Dadaluma does his Iron Fists.

**Stats:** final Kefka's, at his level, a fifth faster, with a fifth less vigor (the power of his blows: Battle, Tiger Claw and the jump). Weak to poison as Dadaluma is, where final Kefka takes no damage from it (he is still protected from the poison status). He can be slowed and hasted.

### Battle program

**Every turn** (extra actions: his turn goes on with the lists below):
- When his timer is above 30 (about a minute; it then starts over) and both ChromeFists are dead or gone: he whistles and calls in two. They are not in the battle at its start.
- Once, below 25% HP: X-Potion or Potion (2 in 3 / 1 in 3) three times, then Safe on himself.
- Once, when he has been hit by Fight four times: he throws a Wing Edge at a random character.

**Below 13% HP** (if he is charging up from the list below when his HP gets here, he does that one first):
1. "Friends! Lovely to see you.", and he charges up
2. Chi Shock
3. Meteor

**At 53% HP and below:**
1. "Friends! Lovely to see you.", and he charges up
2. Chi Shock
3. Tiger Claw, MithrilKnife or Time Warp; then Sweep or nothing (1 in 3 / 2 in 3)
4. Train, Tiger Claw or Jump; then MithrilKnife, Sweep or nothing

**Above 53% HP:**
1. Fallen One
2. Battle, nothing or Sweep
3. MithrilKnife, Train or Tiger Claw
4. Battle, nothing or Tiger Claw
5. HyperDrive, Train or Sweep
6. Battle, nothing or Tiger Claw
7. Sweep, nothing or Tiger Claw

**When he is hit:**
- By Fight: one more hit counted for the Wing Edge (and then what follows)
- Below 17% HP, when damaged (not while he charges up or in the turns after Chi Shock): nothing, Battle or Ultima
- Below 49% HP, when damaged (the same): nothing, Battle or HyperDrive

**When he dies:** the final death, and every enemy goes with him.

**ChromeFist, each turn:** a thrown Dirk at a random character, or Battle twice (1 in 2 each).

The heal usually takes him back above 53% HP (an X-Potion is 9999 HP to him): he then leaves the list he was in, Chi Shock or not, and starts the one above 53%.

### Attacks

- **Tiger Claw** is Havoc Wing (his special: a blow at 4 times the damage), renamed. **HyperDrive** is as it was.
- **Chi Shock** is Goner, and also saps everyone it hits. He charges up before it as final Kefka does, without the laughing head (it is replaced by an empty picture).
- **Time Warp** is Revenger remade: Slow 2 on the whole party (hit rate 150, which Reflect and Runic do not stop), and Haste for every enemy in the battle, whether it hits or not. An enemy protected from Slow or Haste is protected from both, so he and the ChromeFists are protected from neither.
- **Sweep**, Dadaluma's special, is an attack of its own (in the place of Confusion, which nothing in the game uses): a blow on one character with 0.44 of Tentacle's power (it was halved, and then lowered as his vigor was: an attack's power is its own), which saps. It looks and sounds like Dadaluma's own Sweep: the blow his special attack is shown with (`attack_special_animation_mod`).
- **MithrilKnife** is thrown at a character. **Jump** is Ultimaro's (2 to 4 landings).
- From final Kefka's script: above 53% the MithrilKnife was Fire 3, HyperDrive was Ice 3, the last Sweep was Bolt 3 and the other two Sweeps were Havoc Wings. At 53% and below the MithrilKnife in the third turn was Train, the Jump was a Revenger, and the turn's second actions were Havoc Wings.

### ChromeFists

A ChromeFist is a Scrapper (the highest of the enemies with the Iron Fist's looks: speed 37, defense 125, magic defense 145, absorbs poison) with 3500 HP, level 38 for the Scrapper's 34, vigor 14 for 10 and evade 60 for 120, in a dark chrome palette (the Iron Fist's colors by their brightness, as greys). It is an enemy of its own in the place of one no formation has (382), so the others are as they were. It is protected from all statuses but death, slow and haste. When Grampaluma dies they go with him.

### How his script is made

A script is blocks: each turn, from the top, the first block whose conditions are all true is the monster's turn. What Dadaluma does (the call, the heal, the Wing Edge) is blocks before final Kefka's, so they are tested every turn. A block that ends a turn also has the script start over, which for final Kefka's is Fallen One, so each of them ends with a condition that is never true: what is before it is done, and the turn goes on with final Kefka's script where it was. The hits are counted the same way where his script answers being hit, before what final Kefka's does there.

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
- `giant_sprite_mod(..., lower = pixels)` puts a sprite less high than the mold lower in it, to be clear of the boxes at the top of the screen. His place in the formation is Kefka's, so the death animation is too.
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
