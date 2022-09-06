def name():
    return "Doors"

def parse(parser):
    doors = parser.add_argument_group("Doors")

    doors.add_argument("-dru", "--door-randomize-umaro", action = "store_true",
                         help = "Randomize the doors in Umaro's cave")

def process(args):
    pass

def flags(args):
    flags = ""

    if args.doors_umaro:
        flags += " -dru"

    return flags

def options(args):
    return [
        ("Doors Randomize Umaro", args.doors_umaro),
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
