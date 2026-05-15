# ff6_config

A standalone post-processor that rewrites the **default** in-game config
values stored in an already-patched FF6 ROM (battle speed, message
speed, window palettes, font color, etc.).

Originally built for FF6 [Worlds Collide][wc] ROMs, it works on any FF6
ROM that uses the WC default-config trampoline at `$03/70C2` for
Config2 and Config3.  Config1 lives at a fixed address and works on any
vanilla-layout FF6 ROM.

[wc]: https://www.ff6wc.com

## Usage

```sh
python3 ff6_config.py -i ff6.smc [options]
python3 ff6_config.py -h
```

`-i` is required; everything else is optional.  Any option you don't
set keeps the ROM's existing default.

Invalid input now exits with a usage message (no silent fallback to a
hard-coded default).

## Options

| Option       | Flags                        | Argument                                       |
|--------------|------------------------------|------------------------------------------------|
| Input file   | `-i`, `--input`              | `path/to/rom.smc` (required)                   |
| Output file  | `-o`, `--output`             | path; defaults to `<input>_config.smc`         |
| Battle mode  | `-b`, `--bat-mode`           | `active` \| `wait`                             |
| Battle speed | `-bs`, `--bat-speed`         | integer `1`..`6`                               |
| Msg. speed   | `-ms`, `--msg-speed`         | integer `1`..`6`                               |
| Command set  | `-com`, `--command`          | `window` \| `short`                            |
| ATB gauge    | `-g`, `--gauge`              | `on` \| `off`                                  |
| Sound        | `-s`, `--sound`              | `stereo` \| `mono`                             |
| Cursor       | `-c`, `--cursor`             | `reset` \| `memory`                            |
| Re-equip     | `-r`, `--reequip`            | `optimum` \| `empty`                           |
| Spell order  | `-so`, `--spell-order`       | integer `1`..`6`                               |
| Font color   | `-f`, `--font`               | `R,G,B` (each component `0`..`31`)             |
| Wallpaper    | `-w`, `--wallpaper`          | integer `1`..`8`                               |
| Window 1..8  | `-w1`..`-w8`, `--window1`..  | `slot=R,G,B;slot=R,G,B;...` (slot `1`..`7`)    |

For each boolean option, `0` / `1` / `true` / `false` are also accepted
as synonyms for the two named values.

### Window palette format

Each window has seven palette slots.  Pass any subset as
`slot=R,G,B` entries separated by `;`.  Unlisted slots are left alone.

```
--window2 "1=12,16,12;4=5,6,10"
```

sets palette slots 1 and 4 of window 2 and leaves the other five
untouched.

## Example

```sh
python3 ff6_config.py -i ff6wc_test.smc \
    --gauge off \
    --bat-speed 6 \
    --msg-speed 1 \
    --spell-order 2 \
    --wallpaper 2 \
    --font 22,31,22 \
    --window2 "1=12,16,12;2=2,9,4;3=0,9,0;4=5,6,10;5=5,8,6;6=4,9,5;7=0,0,1"
```

writes `ff6wc_test_config.smc` with the chosen defaults baked in.

## Layout

```
ff6_config.py        CLI entry point (argparse)
config/
  config.py          declarative config-byte spec, bit packing, ROM patching
  rom.py             tiny ROM I/O class
tests/
  test_config.py     smoke tests; run with `python tests/test_config.py`
```

## Tests

```sh
python3 tests/test_config.py
```

No external dependencies -- standard library only.

## License

MIT.  See `LICENSE.txt`.  Original codebase by AtmaTek; this
configurator is a derivative work.
