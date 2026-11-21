# Final bosses

`-fb VALUE` (`--final-boss`) chooses who the last tier of the final battle is.

| Value | Final boss |
|-------|------------|
| `kefka` | Kefka, as he is. The default; `-fb` is then left out of the flag string, so seeds rolled without it stay the same |
| `ultimaro` | Ultimaro: a giant Umaro |
| `uncleulty` | Uncle Ulty: a giant Ultros |
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

- 5 levels above what final Kefka would be in the battle and a fifth faster, as Ultimaro.
- Absorbs water.
- Kefka's battle script with water for bolt: CleanSweep for Bolt 3 above 53% HP, and for the first Train below it. Fire 3 and Ice 3 stay.
- Havoc Wing is Tentacle: the same attack, with the looks and sound of the Tentacle attack.
- HyperDrive is Ink Blast: its palettes in ink, and it blinds.
- Goner is Gumbo. Before it he says "Gwee-hee-hee..." and "It's my special recipe!" and a shrimp appears where Kefka's laughing head did (`graphics/shrimp.py`). Its animation is blue and black where Goner's was red, and it blinds everyone it hits. It may also muddle each of them, as his Lv.3 Muddle did: a hit rate of 65 against magic block, rolled for each target (`status_chance_mod`, a special effect for the attack, since its own statuses always take).
- Revenger is Imp Sonata: the Imp spell on the whole party with a hit rate of 125, which Reflect and Runic do not stop. As the spell does, it turns an imp back.

## How a final boss is made

Every final boss is final Kefka's enemy (298), in his formation and running his battle script, made over. A final boss is a subclass of `FinalBoss` (`final_boss/final_boss.py`), whose methods are called as the seed is built:

| Method | Called from | For |
|--------|-------------|-----|
| `enemies_mod(enemies)` | `data/enemies.py`, with the other enemies | Name, stats, elements: `self.enemy(enemies)` is his `Enemy` |
| `scripts_mod(scripts)` | `data/enemy_scripts.py`, before abilities are scaled | His battle script: `scripts.get_script(self.ENEMY)` |
| `data_mod(data)` | `data/data.py`, as the data is written | Attack names, spell data, battle text |
| `battle_mod()` | `battle/final_boss.py` | Code and graphics of the battle |

`LEVELS` is how many levels he is above final Kefka (`battle/load_enemy_level.py` adds them when the battle loads him, so they follow level scaling and the objectives' levels).

`FinalBoss` itself is Kefka: it changes nothing. It also has what the others share:

- `giant_sprite_mod(enemy, shadow_color, shadow_rows)` gives him the sprite of an enemy at twice its size, in that enemy's palette. The enemy needs a small mold (a sprite of up to 64x64 pixels) and 4bpp graphics. A shadow under its feet can be removed.
- `rename_abilities(data, {name: new name})` renames attacks in the box at the top of the screen.
- `lower_mod(enemies, pixels)` puts him lower on the screen than Kefka, for a sprite less high than his.
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
