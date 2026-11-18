# FFVI Worlds Collide
Worlds Collide is an open worlds randomizer for Final Fantasy VI (originally Final Fantasy III in the US).

You start with the airship and can travel freely between the World of Balance and the World of Ruin.  
Complete objectives while searching the worlds for characters, espers, and items until you are ready to challenge Kefka.

## UMAROS COLLIDE

This branch is a spinoff of Worlds Collide made for an event. Every seed rolled from it has these changes:

- The frozen esper (Tritoch) fight in the World of Ruin Narshe is always Umaro: level 99, with the HP and MP of a level 99 enemy and twice his usual speed. With shuffled or original bosses, the boss he replaces takes his place.
- Kefka is not the final boss. At the top of his tower he knocks every party off the screen instead of fighting: the tower is reset, y party switching is turned off, and party 1 lands in Umaro's Den (as if through the trapdoor in Umaro's Cave). The airship waits outside Narshe.
- In the den, the bone carving asks "Touch the eye of the carving?". Yes brings Umaro stomping in, then the final battle's lineup with every available character, then the final battle. From then on the carving no longer gives the cave's reward, so that reward is always an item.
- The last tier of the final battle is Ultimaro: Umaro at twice the size of his usual sprite, 10 levels higher and a tenth faster than final Kefka would be. Havoc Wing is Yeti Punch, HyperDrive is Yeti Blast, and Goner is U'ghaaaa ("Yeti used a Green Cherry!").
- The Moogle Charm is the Yeti Charm: no random encounters, and its wearer is always berserk.
- Kefka looks like Umaro wherever he appears on a map. Choosing sprites with `-cspr` chooses Kefka's too.
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
