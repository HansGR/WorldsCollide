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

    # Full randomization
    doors.add_argument("-drdc", "--door-randomize-dungeon-crawl", action="store_true",
                       help="Randomize all doors to create a single giant dungeon")
    doors.add_argument("-dra", "--door-randomize-all", action = "store_true",
                         help = "Randomize all currently-implemented doors")
    doors.add_argument("-dre", "--door-randomize-each", action = "store_true",
                         help = "Randomize doors in each currently-implemented area")

def process(args):
    #pass
    if args.door_randomize_all or args.door_randomize_dungeon_crawl or args.door_randomize_each or \
            args.door_randomize_umaro or args.door_randomize_upper_narshe or args.door_randomize_upper_narshe_wob or \
            args.door_randomize_upper_narshe_wor or args.door_randomize_esper_mountain or \
            args.door_randomize_owzer_basement or args.door_randomize_magitek_factory or \
            args.door_randomize_sealed_gate or args.door_randomize_zozo_wob or args.door_randomize_zozo_wor \
            or args.door_randomize_mt_zozo or args.door_randomize_lete_river or args.door_randomize_zone_eater \
            or args.door_randomize_serpent_trench or args.door_randomize_burning_house \
            or args.door_randomize_daryls_tomb or args.door_randomize_south_figaro_cave_wob:
        args.door_randomize = True
    else:
        args.door_randomize = False

def flags(args):
    flags = ""

    if args.door_randomize_all:
        # -dra supercedes all
        flags += " -dra"

    elif args.door_randomize_dungeon_crawl:
        # -drdc supercedes all but -dra
        flags += " -drdc"

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

    return flags

def options(args):

    if args.door_randomize_all:
        return [
            ("Randomize All", args.door_randomize_all),
        ]
    elif args.door_randomize_dungeon_crawl:
        return [
            ("Dungeon Crawl", args.door_randomize_dungeon_crawl)
        ]
    elif args.door_randomize_each:
        return [
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

        return [
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
        ]

def menu(args):
    return (name(), options(args))

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log