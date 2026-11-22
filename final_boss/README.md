# Final bosses

`-fb VALUE` (`--final-boss`) chooses who the last tier of the final battle is.

| Value | Final boss |
|-------|------------|
| `kefka` | Kefka, as he is. The default; `-fb` is then left out of the flag string, so seeds rolled without it stay the same |
| `ultimaro` | Ultimaro: a giant Umaro |
| `uncleulty` | Uncle Ulty: a giant Ultros |
| `grampaluma` | Grampaluma: a giant Dadaluma who calls in ChromeFists |
| `random` | One of the above, chosen by the seed. The spoiler log names it |

## Ultimaro

Umaro at twice the size of his sprite (without the shadow under his feet: he is in the air).

- 5 levels above what final Kefka would be in the battle, after scaling and objectives, and a fifth faster.
- Absorbs ice, as Umaro does.
- Kefka's battle script with ice for fire and bolt: Storm for Fire 3 and Surge for Bolt 3 above 53% HP; below it, Ice 3 for the first Train.
- Jumps as Umaro does, in place of a Revenger and a Havoc Wing below 53% HP. He lands 2 to 4 times, as with a Dragon Horn: down and straight back up for each landing, with the damage showing as he leaves.
- Havoc Wing is Yeti Punch, with the looks of Umaro's Tackle. HyperDrive is Yeti Blast and Goner is U'ghaaaa.
- Revenger is Enrager: the Bserk spell on the whole party at half its hit rate (75), which Reflect and Runic do not stop.
- Before U'ghaaaa, "Yeti used a Green Cherry!" and a green cherry appears where Kefka's laughing head did. Its art is `graphics/green_cherry.py`.

## Uncle Ulty

Ultros (the one with all his tentacles) at twice the size of his sprite, without his shadow, and low enough on the screen to be clear of the boxes at the top.

- 5 levels above what final Kefka would be in the battle, as Ultimaro, but no faster than Kefka. A tenth more HP, up to the 65535 an enemy can have: Kefka's 62000 become 65535.
- Absorbs water.
- Kefka's battle script with water for bolt: CleanSweep for Bolt 3 above 53% HP, and for the first Train below it. Fire 3 and Ice 3 stay.
- Havoc Wing is Tentacle: the same attack, with the looks and sound of the Tentacle attack.
- HyperDrive is Ink Blast: its palettes in ink, and it blinds.
- Goner is Gumbo. Before it he says "Gwee-hee-hee..." and "It's my special recipe!" and a shrimp appears where Kefka's laughing head did (`graphics/shrimp.py`). Its animation is blue and black where Goner's was red, and it blinds everyone it hits. It may also muddle each of them, as his Lv.3 Muddle did: a hit rate of 65 against magic block, rolled for each target (`status_chance_mod`, a special effect for the attack, since its own statuses always take).
- Revenger is Imp Sonata: the Imp spell on the whole party with a hit rate of 110, which Reflect and Runic do not stop. As the spell does, it turns an imp back.

## Grampaluma

Dadaluma at 1.21 times his size (107x68 pixels; he is 88 wide, so the most that fits a formation's 128 pixels is 1.43 times, which crowded the screen and its sprites). His stats are final Kefka's (and his level), but he is a fifth faster, has a fifth less vigor (the power of his blows: Tiger Claw and the jump) and can be slowed and hasted. His attacks:

- Havoc Wing is Tiger Claw, otherwise the same. HyperDrive is as it was.
- Goner is Chi Shock, which also saps everyone it hits. Before it he says "Friends! Lovely to see you." and charges up as final Kefka does, without the laughing head (it is replaced by an empty picture).
- Revenger is Time Warp: Slow 2 on the whole party (hit rate 150, which Reflect and Runic do not stop), and Haste for every enemy in the battle, whether it hits or not. An enemy protected from Slow or Haste is protected from both, so he and the ChromeFists are protected from neither.
- Sweep, Dadaluma's special, is an attack of its own (in the place of Confusion, which nothing in the game uses): a blow on one character with 0.44 of Tentacle's power (it was halved, and then lowered as his vigor was: an attack's power is its own), which saps. It looks and sounds like Dadaluma's own Sweep: the blow his special attack is shown with (`attack_special_animation_mod`).
- He jumps as Ultimaro does (2 to 4 landings), and throws MithrilKnives.

In final Kefka's script, where a turn is one of three things, each as likely:

- Above 53% HP, after Fallen One: Battle, nothing or Sweep; a thrown MithrilKnife (was Fire 3), Train or Tiger Claw; Battle, nothing or Tiger Claw; HyperDrive (was Ice 3), Train or Sweep; Battle, nothing or Tiger Claw; Sweep (was Bolt 3), nothing or Tiger Claw. Then Fallen One again.
- At 53% and below, a turn each: his line and the charge; Chi Shock; Tiger Claw, a thrown MithrilKnife or Time Warp, and then Sweep or twice as likely nothing; Train, Tiger Claw or the jump, and then a thrown MithrilKnife, Sweep or nothing. Then his line again.

With what Dadaluma does in Zozo added:

- He calls in two ChromeFists when his timer is above 30 (about a minute) and both are dead or gone, with a whistle, as Dadaluma does his Iron Fists. They are not in the battle at its start. When he dies they go with him (final Kefka's script removes every enemy of the formation).
- Once, below 25% HP: X-Potion, X-Potion or Potion three times (an X-Potion is 9999 HP to him), and Safe.
- Once, when he has been hit by Fight four times: he throws a Wing Edge at a random character.

A script is blocks: each turn, from the top, the first block whose conditions are all true is the monster's turn. These three are blocks before final Kefka's, so they are tested every turn. A block that ends a turn also has the script start over, which for final Kefka's is Fallen One, so each ends with a condition that is never true: what is before it is done, and the turn goes on with final Kefka's script where it was. The hits are counted the same way where his script answers being hit, before what final Kefka's does there.

A ChromeFist is a Scrapper (the highest of the enemies with the Iron Fist's looks: speed 37, defense 125, magic defense 145, absorbs poison) with 3500 HP, level 38 for the Scrapper's 34, vigor 14 for 10 and evade 60 for 120, in a dark chrome palette (the Iron Fist's colors by their brightness, as greys). It is an enemy of its own in the place of one no formation has (382), so the others are as they were. It is protected from all statuses but death, slow and haste. Each turn it throws a Dirk at a random character or attacks twice, one as likely as the other.

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
