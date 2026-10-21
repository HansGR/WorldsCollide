"""Audit the maps whose race npc repaints ride on the map's entrance event.

    python3 tools/race_entrance_audit.py -i vanilla.smc -s SEED [wc flags...]

Takes exactly the flags wc.py takes (-race is added if missing; -o is
ignored - the rom goes to a temp file).  Builds the seed in-process with
the space writer instrumented to catch every "race npc repaint entrance"
block, maps those blocks to the maps whose entrance-event pointer they
became, then reads the built rom and reports, per map:

  - how many exits (short and long, from every map) lead into it - a map
    with none is entered by script only;
  - every scripted load into it ($6A/$6B) in the event banks, with the
    flags byte: bit $80 clear means the entrance event - and so the
    repaint - does NOT run for that entry.

Loads without the entrance event that a conversion already repaints
inline are listed in HANDLED (with the fix site); anything else is an
UNHANDLED finding.  Four such sites bit during playtest (Narshe Moogle
Defense, Narshe Battle, Umaro's Cave, Imperial Camp) - see the sharp
edges in RACE_OBFUSCATION_OVERVIEW.md.  Exit code 1 on any unhandled
finding, so the tool can gate a release build.

The scan is a byte-pattern scan of the event banks, so a data byte can
masquerade as a load: check any surprising offset against the event
script before acting on it.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EVENT_BANKS = (0x0a0000, 0x0f0000)      # CA-CE, where event scripts live
SHORT_EXIT_PTRS, SHORT_EXIT_SIZE = 0x1fbb00, 6
LONG_EXIT_PTRS, LONG_EXIT_SIZE = 0x2df480, 7
MAP_COUNT = 416

# a load whose next command is the reward-kind test ($FC $0C, the start of
# an inline repaint) is handled by construction; the sites below repaint
# further away (in a called block, or after the scene's create) and are
# listed by the file offset of the load
HANDLED = {
    0xcc673: "narshe battle: kefka-arrival reload, repainted by the block the reserve after it calls (narshe_battle.py)",
    0xcd989: "umaro's cave: fall into the carving room, npc repainted between the scene's create and show (umaro_cave.py)",
    0xbeeac: "esper mountain: crack landing, repainted in the landing block (esper_mountain.py)",
    0xbeedb: "esper mountain: crack landing, repainted in the landing block (esper_mountain.py)",
    0xbef09: "esper mountain: crack landing, repainted in the landing block (esper_mountain.py)",
}

# loads without the entrance event that were examined and need no repaint:
# unreachable in open world, or the repainted npc is hidden at that point
REVIEWED = {
    0xcbb11: "narshe wob: vanilla opening scene (locke leads terra out), nothing points into it in open world",
    0xcbba8: "narshe wob: vanilla opening scene (locke leads terra out), nothing points into it in open world",
    0xcbc55: "narshe battle: vanilla terra-esper scene after the battle; the wc end scene at CB/BCFF never returns to it",
    0xcbd2f: "narshe wob: continuation of that vanilla scene, unreachable for the same reason",
    0xcadf3: "narshe moogle defense: victory reload; the collapsed npc's bit ($631) is cleared right before it",
    0xa7202: "figaro castle wob: kefka-burns-the-castle scene, skipped (MET_KEFKA_FIGARO_CASTLE is set at game start)",
    0xa74af: "figaro castle wob: kefka-burns-the-castle scene, skipped (MET_KEFKA_FIGARO_CASTLE is set at game start)",
    0xa86cc: "south figaro basement: occupied-town guard scenes; their tiles do nothing in open world (walked in the emulator)",
    0xa8789: "south figaro basement: occupied-town guard scenes; their tiles do nothing in open world (walked in the emulator)",
    0xb829f: "doma wor: dream-start reload; the throne-room magicite npcs' bit ($549) is only set at the dream's end (CB/9985)",
    0xba2da: "doma wor: in-dream reload; the throne-room magicite npcs' bit ($549) is only set at the dream's end (CB/9985)",
    0xbf0d0: "esper mountain: statue-room reload after ultros; the relm npc bit ($521) is cleared just before it (`db 21`)",
}
INLINE_REPAINT = bytes((0xfc, 0x0c))    # LOAD_KIND: the first command of every inline repaint


def u16(rom, offset):
    return rom[offset] | (rom[offset + 1] << 8)


def exits_into(rom, target):
    """(count, [(from_map, x, y)]) of exits whose destination is target."""
    found = []
    for ptrs, size, dest_at in ((SHORT_EXIT_PTRS, SHORT_EXIT_SIZE, 2),
                                (LONG_EXIT_PTRS, LONG_EXIT_SIZE, 3)):
        for map_id in range(MAP_COUNT):
            start, end = u16(rom, ptrs + 2 * map_id), u16(rom, ptrs + 2 * map_id + 2)
            for offset in range(start, end, size):
                entry = rom[ptrs + offset:ptrs + offset + size]
                dest = entry[dest_at] | ((entry[dest_at + 1] & 0x01) << 8)
                if dest == target:
                    found.append((map_id, entry[0], entry[1]))
    return found


def loads_into(rom, target):
    """[(file_offset, flags)] of $6A/$6B loads whose map id is target.

    The map word is: bits 0-8 map id, $200 update parent map, $400 keep
    the current song, $800 unknown, $1000-$3000 facing; the flags byte is
    $80 entrance event, $40 no fade-in, $01 airship, $02 chocobo.  A
    match with any other bit set is a data byte, not a load."""
    lo, hi = target & 0xff, (target >> 8) & 0x01
    found = []
    start, end = EVENT_BANKS
    for offset in range(start, end - 6):
        if (rom[offset] in (0x6a, 0x6b) and rom[offset + 1] == lo
                and (rom[offset + 2] & 0x01) == hi and (rom[offset + 2] & 0xc0) == 0
                and (rom[offset + 5] & 0x3c) == 0):
            found.append((offset, rom[offset + 5]))
    return found


def main():
    user_args = sys.argv[1:]
    if "-i" not in user_args or "-s" not in user_args:
        raise SystemExit(__doc__)
    if "-race" not in user_args:
        user_args.append("-race")
    if "-o" in user_args:
        at = user_args.index("-o")
        del user_args[at:at + 2]
    tmp = tempfile.mkdtemp(prefix="race_entrance_audit_")
    rom_path = os.path.join(tmp, "race.smc")
    sys.argv = ["wc.py", *user_args, "-o", rom_path]

    # the event modules cannot be imported before the build sets up the
    # rom heap, so hook the space writer instead: every entrance repaint
    # is a Write described "<event> race npc repaint entrance" whose
    # start address then becomes the map's entrance event pointer
    import memory.space as space_module
    from instruction.event import EVENT_CODE_START

    repaint_writes = {}     # event-code address -> event name
    original_write = space_module.Write

    def instrumented_write(bank, src, description, *args, **kwargs):
        space = original_write(bank, src, description, *args, **kwargs)
        if description.endswith(" race npc repaint entrance"):
            repaint_writes[space.start_address - EVENT_CODE_START] = description[:-len(" race npc repaint entrance")]
        return space
    space_module.Write = instrumented_write

    import wc
    wc.main()

    with open(rom_path, "rb") as f:
        rom = f.read()
    if len(rom) % 0x400 == 0x200:
        rom = rom[0x200:]

    ENTRANCE_EVENTS = 0x11fa00
    repaints = {}           # map id -> [event name]
    for map_id in range(MAP_COUNT):
        at = ENTRANCE_EVENTS + 3 * map_id
        pointer = rom[at] | (rom[at + 1] << 8) | (rom[at + 2] << 16)
        if pointer in repaint_writes:
            repaints.setdefault(map_id, []).append(repaint_writes[pointer])
    missing = set(repaint_writes.values()) - {n for names in repaints.values() for n in names}
    if missing:
        print("repaint writes not found in the entrance pointer table:", sorted(missing))

    unhandled = 0
    for map_id in sorted(repaints):
        owners = ", ".join(repaints[map_id])
        exits = exits_into(rom, map_id)
        loads = loads_into(rom, map_id)
        print(f"map 0x{map_id:03x}: {owners}")
        print(f"  exits into it: {len(exits)}" + ("  (script-entered only)" if not exits else ""))
        for offset, flags in loads:
            runs = bool(flags & 0x80)
            if runs:
                note = "entrance event runs"
            elif rom[offset + 6:offset + 8] == INLINE_REPAINT:
                note = "NO entrance event - repainted inline right after the load"
            elif offset in HANDLED:
                note = f"NO entrance event - handled: {HANDLED[offset]}"
            elif offset in REVIEWED:
                note = f"NO entrance event - reviewed, no repaint needed: {REVIEWED[offset]}"
            else:
                note = "NO entrance event - UNHANDLED"
                unhandled += 1
            print(f"  load at 0x{offset:06x} flags ${flags:02x}: {note}")
            if not runs:
                before = rom[offset - 16:offset].hex(" ")
                after = rom[offset + 6:offset + 14].hex(" ")
                print(f"      {before} | {rom[offset:offset + 6].hex(' ')} | {after}")
        if not loads:
            print("  no scripted loads into it")

    print(f"\n{len(repaints)} maps with entrance repaints, {unhandled} unhandled loads")
    return 1 if unhandled else 0


if __name__ == "__main__":
    sys.exit(main())
