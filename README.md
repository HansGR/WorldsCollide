# FFVI Worlds Collide
Worlds Collide is an open worlds randomizer for Final Fantasy VI (originally Final Fantasy III in the US).

You start with the airship and can travel freely between the World of Balance and the World of Ruin.  
Complete objectives while searching the worlds for characters, espers, and items until you are ready to challenge Kefka.

## UMAROS COLLIDE

This branch is a spinoff of Worlds Collide made for an event. Every seed rolled from it has these changes:

- The frozen esper (Tritoch) fight in the World of Ruin Narshe is always Umaro: level 99, with the HP and MP of a level 99 enemy and twice his usual speed. With shuffled or original bosses, the boss he replaces takes his place. Beat him and the way to the final battle is open: jump into Umaro's Cave and find the den.
- Kefka is not the final boss. At the top of his tower he knocks every party off the screen instead of fighting: the tower is reset, y party switching is turned off, and party 1 lands in Umaro's Den (as if through the trapdoor in Umaro's Cave). The airship waits outside Narshe.
- In the den, the bone carving asks "Touch the eye of the carving?", whichever way the party got there. Yes brings Umaro stomping in, then the final battle's lineup with every available character, then the final battle. The carving no longer gives the cave's own check: its reward is always an item and can't be collected, and the boss in Umaro's place is not fought.
- The last tier of the final battle is Ultimaro: Umaro at twice the size of his usual sprite, 5 levels higher and a fifth faster than final Kefka would be. He absorbs ice as Umaro does, fights with ice where Kefka had fire and bolt (Storm, Surge, Ice 3), and sometimes jumps as Umaro does, landing 2 to 4 times as if he wore a Dragon Horn: down and straight back up for each landing, with the damage showing as he leaves, and back to his place only after the last. Havoc Wing is Yeti Punch, HyperDrive is Yeti Blast, Revenger is Enrager (the Bserk spell cast on the whole party, which Reflect and Runic do not stop), and Goner is U'ghaaaa: "Yeti used a Green Cherry!", and a green cherry appears before him where Kefka's laughing head did (the art is in `graphics/green_cherry.py`).
- The Moogle Charm is the Yeti Charm: no random encounters, and its wearer is always berserk.
- Kefka looks like Umaro wherever he appears on a map. Choosing sprites with `-cspr` chooses Kefka's too.
- The start menu reads "FFVI Umaros Collide" and plays Umaro's theme.
- The title screen reads UMAROS COLLIDE (`graphics/tools/umaros_collide_title.py` makes it from the Worlds Collide title).

## Links

###### Start playing: [ff6worldscollide.com](https://www.ff6worldscollide.com)
###### More Info: [wiki.ff6worldscollide.com](https://wiki.ff6worldscollide.com)
###### Community: [discord](https://discord.gg/5MPeng5)

## Usage

Requires Python 3.9+ and an unheadered FFIII US v1.0 ROM.

```sh
$ python3 wc.py -i ffiii.smc
```

```sh
$ python3 wc.py -h
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how the randomizer is put
together, how to add flags/events, and the rules that keep old seeds
reproducible. Never commit ROM files.
