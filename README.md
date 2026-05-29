# ff6_config

A standalone post-processor that rewrites the **default** in-game config
values stored in an FF6 ROM (battle speed, message speed, window
palettes, font color, etc.).

Originally built for FF6 [Worlds Collide][wc] ROMs.  Config1 (battle
mode, battle speed, command set, message speed) lives at a fixed
address that works on any vanilla-layout FF6 ROM.  Config2 (controller
2, spell order, …), Config3 (gauge, cursor, sound, re-equip, wallpaper)
and Config4 (`$1D4F` — which battle characters player 2 controls when
the controller is set to `multiple`) require a small **trampoline** to
be installed in the ROM first; if you don't have a WC-patched ROM, run
[`install_trampoline.py`](#trampoline) first.

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
| Controller   | `-ctrl`, `--controller`      | `single` \| `multiple`                         |
| Player 2     | `-p2`, `--player2`           | subset of `1,2,3,4` (e.g. `13`); needs `multiple` |
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

## Trampoline

In a vanilla FF6 ROM, the boot code at file offset `0x0370C2`
(SNES `$C3/70C2`) zeroes the Config2, Config3 and Config4 RAM bytes
(`$1D54`, `$1D4E` and `$1D4F`) inline with three consecutive `STZ ABS`
instructions — there's no settable default to override.

`install_trampoline.py` replaces those three `STZ`s with `JSR` calls to
a trio of 6-byte subroutines elsewhere in bank `$C3`.  Each subroutine
is `LDA #$NN; STA $1Dxx; RTS`; `ff6_config` works by patching the `NN`
immediate inside each one.  The third subroutine (`$1D4F`) is what backs
the `-p2`/`--player2` controller assignments; if a ROM only has the
older two-`JSR` trampoline, a non-zero `-p2` is rejected with a hint to
re-run the installer (a `single`/all-player-1 default still works).

If your ROM was patched by WC, the trampoline is already there
(installed in `settings/__init__.py`).  For a vanilla ROM, run:

```sh
python3 install_trampoline.py -i ff6_vanilla.smc -o ff6_ready.smc
python3 ff6_config.py -i ff6_ready.smc --bat-speed 6 ...
```

The installer writes 18 bytes at file offset `0x03F091`
(SNES `$C3/F091`) by default, a region the published FF6 ROM map lists
as unused (3951 bytes starting at `$C3/F091`).  The boot code at
`$C3/70C2` is in the same bank, so the 16-bit `JSR ABS` reaches it.

**If you're maintaining your own FF6 hacking project**, install the
trampoline as part of your own build using your project's free-space
allocator — relying on `install_trampoline.py` can collide with code
that other patches also write into the "unused" region.

The installer accepts `--address HEX` (file offset or SNES `$C3XXXX`)
to place the trampoline elsewhere within bank `$C3`, and `--force` to
overwrite an existing trampoline.  `ff6_config` refuses to run on a
ROM where the trampoline isn't installed.

## Layout

```
ff6_config.py            CLI: apply default-config overrides
install_trampoline.py    CLI: install the trampoline into a vanilla ROM
config/
  config.py              declarative config-byte spec, bit packing, ROM patching
  rom.py                 tiny ROM I/O class
  window_graphics.py     4bpp tile/palette encode/decode + ROM IO for $ED/0000
scripts/
  window_graphics.py        CLI: extract/inject window graphics as indexed PNGs
  build_borders.py          regenerate web/borders.js from romdata/
  build_vanilla_graphics.py regenerate web/vanilla_graphics.js from romdata/
tests/
  test_config.py         smoke tests; run with `python tests/test_config.py`
  test_window_graphics.py
  test_encoder_js.js     mirror of the Python codec in JS; run with `node ...`
```

## Tests

```sh
python3 tests/test_config.py
python3 tests/test_window_graphics.py
node tests/test_encoder_js.js     # cross-checks web/encoder.js vs the Python codec
```

Python tests use the standard library only.  `tests/test_encoder_js.js`
needs Node 18+; on systems without Node you can skip it (the same
encoding is round-tripped against the shipped romdata in the Python
suite).

## License

MIT.  See `LICENSE.txt`.  Original codebase by AtmaTek; this
configurator is a derivative work.
