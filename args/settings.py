def name():
    return "Settings"

def parse(parser):
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("-open", "--open-world", action = "store_true",
                      help = "Unrestricted event access")
    mode.add_argument("-cg", "--character-gating", action = "store_true",
                      help = "Events locked until required characters recruited")

    seed_spoilers = parser.add_argument_group("seed_spoilers")
    seed_spoilers.add_argument("-s", dest = "seed", type = str, required = False, help = "RNG seed")
    seed_spoilers.add_argument("-sl", "--spoiler-log", action = "store_true",
                               help = "Generated log file also contains event rewards and other detailed information")
    seed_spoilers.add_argument("-race", dest = "race", action = "store_true",
                               help = "Race build: hide the seed in-game and enable per-seed data obfuscation."
                                      " Assumes the flags are public and the seed is secret")

def process(args):
    pass

def flags(args):
    flags = ""

    if args.character_gating:
        flags += " -cg"
    elif args.open_world:
        flags += " -open"

    if args.spoiler_log:
        flags += " -sl"
    if args.race:
        flags += " -race"

    return flags

def options(args):
    game_mode = "Open World"
    if args.character_gating:
        game_mode = "Character Gating"

    # race builds assume public flags but a secret seed: keep the flags
    # menu/log but never write the seed string into them
    seed = "hidden" if args.race else args.seed

    return [
        ("Mode", game_mode, "game_mode"),
        ("Seed", seed, "seed"),
        ("Spoiler Log", args.spoiler_log, "spoiler_log"),
    ]

def menu(args):
    entries = options(args)
    for index, entry in enumerate(entries):
        if entry[0] == "Seed":
            if len(entry[1]) > 18:
                entries[index] = (entry[0], entry[1][:15] + "...", "seed")
            break
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
