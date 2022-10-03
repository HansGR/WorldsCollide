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

    # Full randomization
    doors.add_argument("-drdc", "--door-randomize-dungeon-crawl", action="store_true",
                       help="Randomize all doors to create a single giant dungeon")
    doors.add_argument("-dra", "--door-randomize-all", action = "store_true",
                         help = "Randomize all currently-implemented doors")


def process(args):
    pass

def flags(args):
    flags = ""

    if args.door_randomize_all:
        # -dra supercedes all
        flags += " -dra"

    elif args.door_randomize_dungeon_crawl:
        # -drdc supercedes all but -dra
        flags += " -drdc"

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
    else:
        un_state = args.door_randomize_upper_narshe
        if not un_state:
            if args.door_randomize_upper_narshe_wob and not args.door_randomize_upper_narshe_wor:
                un_state = 'WoB'
            elif not args.door_randomize_upper_narshe_wob and args.door_randomize_upper_narshe_wor:
                un_state = 'WoR'
            elif args.door_randomize_upper_narshe_wob and args.door_randomize_upper_narshe_wor:
                un_state = 'WoB+WoR'

        return [
            ("Umaro's Cave", args.door_randomize_umaro),
            ("Upper Narshe", un_state),
            ("Esper Mountain", args.door_randomize_esper_mountain),
            ("Owzer Basement", args.door_randomize_owzer_basement),
            ("Magitek Factory", args.door_randomize_magitek_factory)
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
