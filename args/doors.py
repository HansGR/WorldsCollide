import argparse
def name():
    return "Doors"

def parse(parser):
    doors = parser.add_argument_group("Doors")

    # Individual zone randomization
    doors.add_argument("-dru", "--door-randomize-umaro", action = "store_true",
                         help = "Randomize the doors in Umaro's cave")
    doors.add_argument("-drun", "--door-randomize-upper-narshe", action="store_true",
                       help="Randomize the doors in Upper Narshe")
    doors.add_argument("-drunb", "--door-randomize-upper-narshe-wob", action="store_true",
                       help="Randomize the doors in Upper Narshe WoB")
    doors.add_argument("-drunr", "--door-randomize-upper-narshe-wor", action="store_true",
                       help="Randomize the doors in Upper Narshe WoR")
    doors.add_argument("-drem", "--door-randomize-esper-mountain", action="store_true",
                       help="Randomize the doors in Esper Mountain")
    doors.add_argument("-drob", "--door-randomize-owzer-basement", action="store_true",
                       help="Randomize the doors in Owzer's Basement")
    doors.add_argument("-drmf", "--door-randomize-magitek-factory", action="store_true",
                       help="Randomize the doors in Magitek Factory")
    doors.add_argument("-drsg", "--door-randomize-sealed-gate", action="store_true",
                       help="Randomize the doors in Cave to the Sealed Gate")
    doors.add_argument("-drzb", "--door-randomize-zozo-wob", action="store_true",
                       help="Randomize the doors in Zozo WoB")
    doors.add_argument("-drzr", "--door-randomize-zozo-wor", action="store_true",
                       help="Randomize the doors in Zozo WoR")
    doors.add_argument("-drmz", "--door-randomize-mt-zozo", action="store_true",
                       help="Randomize the doors in Mt Zozo")
    doors.add_argument("-drlr", "--door-randomize-lete-river", action="store_true",
                       help="Randomize the doors in Lete River")
    doors.add_argument("-drze", "--door-randomize-zone-eater", action="store_true",
                       help="Randomize the doors in Zone Eater")
    doors.add_argument("-drst", "--door-randomize-serpent-trench", action="store_true",
                       help="Randomize the doors in Serpent Trench")
    doors.add_argument("-drbh", "--door-randomize-burning-house", action="store_true",
                       help="Randomize the doors in Burning House")
    doors.add_argument("-drdt", "--door-randomize-daryls-tomb", action="store_true",
                       help="Randomize the doors in Darills Tomb")
    doors.add_argument("-drsfcb", "--door-randomize-south-figaro-cave-wob", action="store_true",
                       help="Randomize the doors in South Figaro Cave WoB")
    doors.add_argument("-drpt", "--door-randomize-phantom-train", action="store_true",
                       help="Randomize the doors in Phantom Train")
    doors.add_argument("-drcd", "--door-randomize-cyans-dream", action="store_true",
                       help="Randomize the doors in Cyan's Dream")
    doors.add_argument("-drmk", "--door-randomize-mt-kolts", action="store_true",
                       help="Randomize the doors in Mt Kolts")
    doors.add_argument("-drvc", "--door-randomize-veldt-cave", action="store_true",
                       help="Randomize the doors in Cave on the Veldt")

    # Full randomization
    doors.add_argument("-drdc", "--door-randomize-dungeon-crawl", action="store_true",
                       help="Randomize all doors to create a single giant dungeon")
    doors.add_argument("-dra", "--door-randomize-all", action = "store_true",
                         help = "Randomize all currently-implemented doors in each world")
    doors.add_argument("-drx", "--door-randomize-crossworld", action="store_true",
                       help="Randomize all currently-implemented doors across worlds")
    doors.add_argument("-dre", "--door-randomize-each", action = "store_true",
                         help = "Randomize doors in each currently-implemented area")
    doors.add_argument("-ruin", "--ruination-mode", nargs="?", const="default", default=None,
                       choices=["default", "hard", "easy", "custom"],
                       help="Rogue-like mode with randomized dungeon and no airship. "
                            "Automatically sets recommended flags. '-ruin hard' additionally adds "
                            "permadeath, 3 starting Fenix Downs, lite ironmog saves, and removes "
                            "Life 3/Warp/Antdot/Remedy from learnable sources. "
                            "'-ruin easy' is open world on a smaller map (6 characters + 6 espers) "
                            "with 3 starting espers, level 12, 12000 gp, standard sell prices, "
                            "6 Potions, 10 Warp Stones, 12 junk items, no monsters-in-a-box and "
                            "High Tier Item rewards at 3, 6 and 9 checks "
                            "('-ruin custom' skips defaults entirely, "
                            "'-no <flags>' disables specific defaults)")

    doors.add_argument("-maze", "--ruin-dream-maze", default=None, choices=["full", "sep", "iso"],
                       help="Dream Maze handling in ruination mode: "
                            "'full' includes maze in Doma Dream (default), "
                            "'sep' separates maze from Doma Dream (gated by ALL instead of CYAN), "
                            "'iso' isolates maze as a single composite room (internally randomized)")

    doors.add_argument("-rkt", "--ruin-kefka-tower", action="store_true",
                       help="Randomize the three lanes of Kefka's Tower in ruination mode: "
                            "rooms are repartitioned into three non-overlapping lanes "
                            "(each entry to a 4-ton-switch-room ending) with internal "
                            "connections shuffled, while preserving switch/boss constraints")

    doors.add_argument("-rce", "--required-characters-espers", type=str, default=None,
                       help="Ruination mode: number of characters and espers required to be obtainable, "
                            "as 'CC.EE' exact counts or 'cc.cc.ee.ee' min/max ranges "
                            "(default 6.9, minimum 3.0)")

    # Map shuffle
    doors.add_argument("-maps", "--map-shuffle-separate", action="store_true",
                       help="Randomize overworld entrances in each world")
    doors.add_argument("-mapx", "--map-shuffle-crossworld", action="store_true",
                       help="Randomize overworld entrances across worlds")

    # Debug options
    doors.add_argument("-debug_dest", "--debug-route-destination", nargs='+', type=str, default=None,
                       help="Output the shortest route to specified room(s). Supports multiple rooms. (use with -drdc or -ruin)")
    doors.add_argument("-maptest", "--maptest-rooms", nargs='+', type=str, default=None,
                       help="TESTING ONLY: rewire the first ruination branch door straight into the "
                            "listed room(s), chained in order (each room but the last needs two doors). "
                            "The seed is likely uncompletable -- it exists to test event mechanics in "
                            "rooms without routing a full seed. (use with -ruin)")

def process(args):
    # The individual-area flag list is owned by doors/plan/modes.py; a new
    # area added there is picked up here automatically.
    from doors.plan.modes import INDIVIDUAL_AREA_ATTRS
    args.door_randomize = bool(
        args.door_randomize_all or args.door_randomize_crossworld
        or args.door_randomize_dungeon_crawl or args.door_randomize_each
        or args.ruination_mode is not None
        or any(getattr(args, attr) for attr in INDIVIDUAL_AREA_ATTRS))

    if args.ruination_mode is not None:
        # Override:  ruination mode is incompatible with map shuffle and other door rando modes, and takes precedence
        args.door_randomize_all = False
        args.door_randomize_each = False
        args.door_randomize_crossworld = False
        args.door_randomize_dungeon_crawl = False
        args.map_shuffle_separate = False
        args.map_shuffle_crossworld = False

    if args.maptest_rooms:
        if args.ruination_mode is None:
            raise ValueError("-maptest requires -ruin")
        from data.rooms import room_data
        for rid in args.maptest_rooms:
            data = room_data.get(rid)
            if data is None:
                raise ValueError(f"-maptest: unknown room id {rid!r}")
        # every room but the last needs a second door to chain onward
        for rid in args.maptest_rooms[:-1]:
            if len([d for d in room_data[rid][0] if isinstance(d, int)]) < 2:
                raise ValueError(f"-maptest: {rid!r} has fewer than two doors "
                                 "and cannot chain to the next room")

    # -rce: characters/espers required to unlock Kefka's Tower (ruination map
    # generation). 'CC.EE' exact or 'cc.cc.ee.ee' min/max ranges; the planner
    # consumes these as [min, max] and rolls within its own RNG window.
    _rce = args.required_characters_espers
    if _rce is None:
        _rce = "6.9"
    def _rce_error(message):
        import sys
        args.parser.print_usage()
        print(f"{sys.argv[0]}: error: -rce: {message}")
        sys.exit(1)
    fields = _rce.split('.')
    if len(fields) not in (2, 4) or not all(f.lstrip('-').isdigit() for f in fields):
        _rce_error(f"expected 'CC.EE' or 'cc.cc.ee.ee' integer counts, got '{_rce}'")
    fields = [int(f) for f in fields]
    if len(fields) == 2:
        char_range = [fields[0], fields[0]]
        esper_range = [fields[1], fields[1]]
    else:
        char_range = [fields[0], fields[1]]
        esper_range = [fields[2], fields[3]]
    if char_range[0] > char_range[1] or esper_range[0] > esper_range[1]:
        _rce_error(f"min above max in '{_rce}'")
    if char_range[0] < 3 or esper_range[0] < 0:
        _rce_error(f"minimum allowable is 3.0 (characters.espers), got '{_rce}'")
    if char_range[1] > 14 or esper_range[1] > 27:
        _rce_error(f"maximum allowable is 14.27 (characters.espers), got '{_rce}'")
    args.ruin_characters_required = char_range
    args.ruin_espers_required = esper_range

    if args.door_randomize_dungeon_crawl:
        # Override: dungeon crawl is incompatible with map shuffle and takes precedence
        args.map_shuffle_separate = False
        args.map_shuffle_crossworld = False

    # Door randomization (except ruination) is incompatible with character gating
    # Force open world when door randomization is enabled
    if args.door_randomize and args.ruination_mode is None:
        if args.character_gating:
            print("Note: Door randomization is incompatible with character gating (-cg). Forcing open world mode.")
        args.character_gating = False
        args.open_world = True

    if args.map_shuffle_separate or args.map_shuffle_crossworld:
        args.map_shuffle = True
    else:
        args.map_shuffle = False

    #print('-drdc overrides -maps and -mapx: ', args.door_randomize_dungeon_crawl, args.map_shuffle_separate,
    #      args.map_shuffle_crossworld, args.map_shuffle)

def flags(args):
    flags = ""

    if args.map_shuffle_separate:
        # -maps is separate from door randomization for now
        flags += " -maps"
    elif args.map_shuffle_crossworld:
        # -mapx is separate from door randomization for now
        flags += " -mapx"


    if args.ruination_mode is not None:
        # -ruin supercedes all.  The mode value must round-trip so that
        # re-running a logged flag string re-expands the same defaults
        # (a bare '-ruin' must not re-expand as hard or easy).
        flags += " -ruin"
        if args.ruination_mode in ("custom", "hard", "easy"):
            flags += " " + args.ruination_mode

        if args.ruin_dream_maze:
            flags += f" -maze {args.ruin_dream_maze}"

        if getattr(args, "ruin_kefka_tower", False):
            flags += " -rkt"

        if args.required_characters_espers is not None:
            flags += f" -rce {args.required_characters_espers}"

        if args.debug_route_destination:
            flags += " -debug_dest " + " ".join(args.debug_route_destination)

        if args.maptest_rooms:
            flags += " -maptest " + " ".join(args.maptest_rooms)

    elif args.door_randomize_all:
        # -dra supercedes all but -ruin
        flags += " -dra"

    elif args.door_randomize_crossworld:
        # -drx supercedes all but -dra
        flags += " -drx"

    elif args.door_randomize_dungeon_crawl:
        # -drdc supercedes all but -dra
        flags += " -drdc"

        if args.debug_route_destination:
            flags += " -debug_dest " + " ".join(args.debug_route_destination)

    elif args.door_randomize_each:
        # -dre supercedes all but -dra, -drdc
        flags += " -dre"

    else:
        if args.door_randomize_umaro:
            flags += " -dru"

        if args.door_randomize_upper_narshe:
            flags += " -drun"
        else:
            # -drun supercedes -drunb, drunr
            if args.door_randomize_upper_narshe_wob:
                flags += " -drunb"
            if args.door_randomize_upper_narshe_wor:
                flags += " -drunr"

        if args.door_randomize_esper_mountain:
            flags += " -drem"

        if args.door_randomize_owzer_basement:
            flags += " -drob"

        if args.door_randomize_magitek_factory:
            flags += " -drmf"

        if args.door_randomize_sealed_gate:
            flags += " -drsg"

        if args.door_randomize_zozo_wob:
            flags += " -drzb"

        if args.door_randomize_zozo_wor:
            flags += " -drzr"

        if args.door_randomize_mt_zozo:
            flags += " -drmz"

        if args.door_randomize_lete_river:
            flags += " -drlr"

        if args.door_randomize_zone_eater:
            flags += " -drze"

        if args.door_randomize_serpent_trench:
            flags += " -drst"

        if args.door_randomize_burning_house:
            flags += " -drbh"

        if args.door_randomize_daryls_tomb:
            flags += " -drdt"

        if args.door_randomize_south_figaro_cave_wob:
            flags += " -drsfcb"

        if args.door_randomize_phantom_train:
            flags += " -drpt"

        if args.door_randomize_cyans_dream:
            flags += " -drcd"

        if args.door_randomize_mt_kolts:
            flags += " -drmk"

        if args.door_randomize_veldt_cave:
            flags += " -drvc"

    return flags

def options(args):

    opts = []
    if args.map_shuffle:
        if args.map_shuffle_separate:
            opts += [
                ("Map Shuffle", args.map_shuffle),
            ]
        else:
            opts += [
                ("Map Shuffle", 'Crossworld')
            ]
        if not args.door_randomize:
            return opts

    if args.ruination_mode is not None:
        mode_desc = "Custom" if args.ruination_mode == "custom" else ""
        cr, er = args.ruin_characters_required, args.ruin_espers_required
        def _range_desc(lo, hi):
            return str(lo) if lo == hi else f"{lo}-{hi}"
        opts += [
            ("Ruination Mode", mode_desc),
            (" available c/e", f"{_range_desc(*cr)}/{_range_desc(*er)}"),
        ]

    elif args.door_randomize_all:
        opts += [
            ("Randomize All", args.door_randomize_all),
        ]
    elif args.door_randomize_crossworld:
        opts += [
            ("Randomize All", 'Crossworld'),
        ]
    elif args.door_randomize_dungeon_crawl:
        opts += [
            ("Dungeon Crawl", args.door_randomize_dungeon_crawl)
        ]
    elif args.door_randomize_each:
        opts += [
            ("Umaro's Cave", True),
            ("Upper Narshe", 'WoB+WoR'),
            ("Esper Mountain", True),
            ("Owzer Basement", True),
            ("Magitek Factory", True),
            ("Sealed Gate", True),
            ("Zozo", 'WoB+WoR'),
            ("Mt. Zozo", True),
            ("Lete River", True),
            ("Zone Eater", True),
            ("Serpent Trench", True),
            ("Burning House", True),
            ("Daryl's Tomb", True),
            ("SF Cave WOB", True),
            ("Phantom Train", True),
            ("Cyan's Dream", True),
            ("Mt. Kolts", True),
            ("Veldt Cave", True),
        ]
    else:
        un_state = args.door_randomize_upper_narshe
        if not un_state:
            if args.door_randomize_upper_narshe_wob and not args.door_randomize_upper_narshe_wor:
                un_state = 'WoB'
            elif not args.door_randomize_upper_narshe_wob and args.door_randomize_upper_narshe_wor:
                un_state = 'WoR'
            elif args.door_randomize_upper_narshe_wob and args.door_randomize_upper_narshe_wor:
                un_state = 'WoB+WoR'

        zozo_state = False
        if args.door_randomize_zozo_wob and args.door_randomize_zozo_wor:
            zozo_state = 'WoB+WoR'
        elif args.door_randomize_zozo_wob:
            zozo_state = 'WoB'
        elif args.door_randomize_zozo_wor:
            zozo_state = 'WoR'

        opts += [
            ("Umaro's Cave", args.door_randomize_umaro),
            ("Upper Narshe", un_state),
            ("Esper Mountain", args.door_randomize_esper_mountain),
            ("Owzer Basement", args.door_randomize_owzer_basement),
            ("Magitek Factory", args.door_randomize_magitek_factory),
            ("Sealed Gate", args.door_randomize_sealed_gate),
            ("Zozo", zozo_state),
            ("Mt. Zozo", args.door_randomize_mt_zozo),
            ("Lete River", args.door_randomize_lete_river),
            ("Zone Eater", args.door_randomize_zone_eater),
            ("Serpent Trench", args.door_randomize_serpent_trench),
            ("Burning House", args.door_randomize_burning_house),
            ("Darill's Tomb", args.door_randomize_daryls_tomb),
            ("SF Cave WOB", args.door_randomize_south_figaro_cave_wob),
            ("Phantom Train", args.door_randomize_phantom_train),
            ("Cyan's Dream", args.door_randomize_cyans_dream),
            ("Mt. Kolts", args.door_randomize_mt_kolts),
            ("Veldt Cave", args.door_randomize_veldt_cave),
        ]

    return opts

def menu(args):
    return (name(), options(args))

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log