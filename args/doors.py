def name():
    return "Doors"

def parse(parser):
    doors = parser.add_argument_group("Doors")

    doors.add_argument("-dru", "--door-randomize-umaro", action = "store_true",
                         help = "Randomize the doors in Umaro's cave")
    doors.add_argument("-drun", "--door-randomize-upper-narshe", action="store_true",
                       help="Randomize the doors in Upper Narshe")
    doors.add_argument("-drunb", "--door-randomize-upper-narshe-wob", action="store_true",
                       help="Randomize the doors in Upper Narshe WoB")
    doors.add_argument("-drunr", "--door-randomize-upper-narshe-wor", action="store_true",
                       help="Randomize the doors in Upper Narshe WoR")

def process(args):
    pass

def flags(args):
    flags = ""

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

    return flags

def options(args):

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
