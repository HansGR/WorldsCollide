from constants.commands import (COMMAND_OPTIONS, COMMON_COMMANDS, FULL_RANDOM_MODES, FULL_RANDOM_UNIQUE_MODE,
                                PROBABILITY_RANDOM_MODES, PROBABILITY_COMMAND_IDS,
                                RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND, RANDOM_EXCLUDE_COMMANDS,
                                id_name, name_id)

def name():
    return "Commands"

COMMANDS_HELP = ("Character commands: either one id per character ('%s' 2 digit command ids), a full random mode "
                 "('fr' / 'fru' followed by 'FIGHT.MAGIC.ITEM' percent chances, e.g. 'fr 10.50.90'), or a "
                 "probability list ('pr' / 'pru' followed by dot-separated command ids and matching percent "
                 "chances, e.g. 'pr 0.1.2.28 50.50.50.100'; 97 = a chance at an empty slot; unfilled slots "
                 "are backfilled randomly, respecting -rec)"
                 % len(COMMAND_OPTIONS))

def parse(parser):
    commands = parser.add_argument_group("Commands")
    commands.add_argument("-com", "--commands", type = str, nargs = "*", help = COMMANDS_HELP)
    commands.add_argument("-scc", "--shuffle-commands", action = "store_true", help = "Shuffle selected/randomized commands")
    commands.add_argument("-rec", "--random-exclude-command-ids", type = str, default = None, metavar = "VALUE",
                          help = "Exclude commands from random possibilities, as dot-separated command ids "
                                 "with an arbitrary number of entries (e.g. '-rec 05.07.10')")
    # legacy single-command forms, kept for backward compatibility: each value is folded into the
    # same exclusion list as -rec (and the canonical flag string re-emits them as -rec)
    commands.add_argument("-rec1", "--random-exclude-command1", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec2", "--random-exclude-command2", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec3", "--random-exclude-command3", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec4", "--random-exclude-command4", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec5", "--random-exclude-command5", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")
    commands.add_argument("-rec6", "--random-exclude-command6", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities (legacy form of -rec)")

def _process_character_commands(args, tokens):
    # one explicitly selected (or random) command id per character
    if len(tokens) != 1:
        args.parser.error(f"commands: expected a single value of command ids, got '{' '.join(tokens)}'")

    digits = 2 # number of digits each command id substring is
    value = tokens[0]
    expected_length = digits * len(COMMAND_OPTIONS)
    if not value.isdigit() or len(value) != expected_length:
        args.parser.error(f"commands: '{value}' must be {expected_length} digits "
                          f"({len(COMMAND_OPTIONS)} {digits} digit command ids)")

    args.character_commands = [int(value[index : index + digits]) for index in range(0, len(value), digits)]

    for index, command in enumerate(args.character_commands):
        if command == RANDOM_COMMAND:
            args.command_strings.append("Random")
        elif command == RANDOM_UNIQUE_COMMAND:
            args.command_strings.append("Random Unique")
        elif command == NONE_COMMAND:
            args.command_strings.append("None")
        elif command in id_name:
            args.command_strings.append(id_name[command])
        else:
            args.parser.error(f"commands: '{command:02}' is not a valid command id for {COMMAND_OPTIONS[index]}")

def _process_full_random(args, tokens):
    # "fr"/"fru" followed by the percent chance each character keeps fight, magic and item
    mode = tokens[0].lower()
    if len(tokens) != 2:
        args.parser.error(f"commands: '{mode}' requires one '{'.'.join(name.upper() for name in COMMON_COMMANDS)}' "
                          f"percent chance value, e.g. -com {mode} 10.50.90")

    percents = tokens[1].split(".")
    if len(percents) != len(COMMON_COMMANDS):
        args.parser.error(f"commands: '{tokens[1]}' must be {len(COMMON_COMMANDS)} percent chances separated by "
                          f"'.', one each for {', '.join(COMMON_COMMANDS)}")

    values = []
    for command_name, percent in zip(COMMON_COMMANDS, percents):
        try:
            value = int(percent)
        except ValueError:
            args.parser.error(f"commands: '{percent}' is not a valid {command_name} percent chance")
        if value < 0 or value > 100:
            args.parser.error(f"commands: {command_name} percent chance '{value}' must be between 0 and 100")
        values.append(value)

    args.commands_random_mode = mode
    args.command_fight_percent, args.command_magic_percent, args.command_item_percent = values

def _process_probability_random(args, tokens):
    # "pr"/"pru" followed by dot-separated command ids and matching percent chances,
    # e.g. 'pr 0.1.2.28 50.50.50.100'. Rolled slots come from the declared list
    # (grouped by likelihood, capped at four); unfilled slots are backfilled
    # randomly from the non-excluded pool. 97 declares a chance at an empty slot.
    mode = tokens[0].lower()
    if len(tokens) != 3:
        args.parser.error(f"commands: '{mode}' requires dot-separated command ids and matching percent "
                          f"chances, e.g. -com {mode} 0.1.2.28 50.50.50.100")

    ids = []
    for part in tokens[1].split("."):
        try:
            command = int(part)
        except ValueError:
            args.parser.error(f"commands: '{part}' is not a valid command id")
        if command != NONE_COMMAND and command not in PROBABILITY_COMMAND_IDS:
            args.parser.error(f"commands: '{command:02}' is not a valid probability command id "
                              f"(one of the {len(PROBABILITY_COMMAND_IDS)} real commands, or 97 for None)")
        if command in ids:
            args.parser.error(f"commands: duplicate probability command id '{command:02}'")
        if command in args.random_exclude_commands:
            args.parser.error(f"commands: '{id_name[command]}' ({command:02}) is both given a probability "
                              "and excluded by -rec")
        ids.append(command)

    percents = tokens[2].split(".")
    if len(percents) != len(ids):
        args.parser.error(f"commands: {len(ids)} command ids but {len(percents)} percent chances")

    probabilities = []
    for command, percent in zip(ids, percents):
        try:
            value = int(percent)
        except ValueError:
            args.parser.error(f"commands: '{percent}' is not a valid percent chance")
        if value < 0 or value > 100:
            args.parser.error(f"commands: percent chance '{value}' must be between 0 and 100")
        probabilities.append((command, value))

    args.commands_random_mode = mode
    args.command_probabilities = probabilities

def _process_excluded_commands(args):
    # merge -rec (dot-separated, arbitrary length) with the legacy -recN single
    # values into one exclusion list. -rec entries come first, then the legacy
    # flags in order; duplicates are preserved (they were legal before and are
    # harmless to the consumers).
    from constants.commands import RANDOM_POSSIBLE_COMMANDS
    excluded = []
    if args.random_exclude_command_ids is not None:
        for part in args.random_exclude_command_ids.split("."):
            try:
                command = int(part)
            except ValueError:
                args.parser.error(f"random-exclude-command-ids: '{part}' is not a valid command id")
            if command not in RANDOM_EXCLUDE_COMMANDS:
                args.parser.error(f"random-exclude-command-ids: '{command:02}' is not an excludable command id")
            if command != NONE_COMMAND:
                excluded.append(command)

    for legacy in (args.random_exclude_command1, args.random_exclude_command2,
                   args.random_exclude_command3, args.random_exclude_command4,
                   args.random_exclude_command5, args.random_exclude_command6):
        if legacy != NONE_COMMAND:
            excluded.append(legacy)

    possible = [name_id[name] for name in RANDOM_POSSIBLE_COMMANDS]
    if excluded and not [command for command in possible if command not in excluded]:
        args.parser.error("random-exclude-command-ids: cannot exclude every "
                          "randomly-selectable command")

    args.random_exclude_commands = excluded

def process(args):
    _process_excluded_commands(args)

    tokens = []
    for value in args.commands or []:
        tokens.extend(value.split())

    args.commands_random_mode = None
    args.character_commands = []
    args.command_strings = []
    args.command_fight_percent = 0
    args.command_magic_percent = 0
    args.command_item_percent = 0
    args.command_probabilities = []

    if not tokens:
        args.commands = None
        args.blitz_command_possible = True
        return

    if tokens[0].lower() in FULL_RANDOM_MODES:
        _process_full_random(args, tokens)
    elif tokens[0].lower() in PROBABILITY_RANDOM_MODES:
        _process_probability_random(args, tokens)
        # canonical value: mode, two-digit-padded ids, percents
        tokens = [args.commands_random_mode,
                  ".".join(f"{command:02}" for command, _ in args.command_probabilities),
                  ".".join(str(percent) for _, percent in args.command_probabilities)]
    else:
        _process_character_commands(args, tokens)

    # store the normalized value back so flags()/options() have a single canonical string
    args.commands = " ".join(tokens)

    blitz_id = name_id["Blitz"]
    blitz_excluded = blitz_id in args.random_exclude_commands
    if args.commands_random_mode in PROBABILITY_RANDOM_MODES:
        # blitz can come from its declared probability or from the random backfill
        blitz_declared = any(command == blitz_id and percent > 0
                             for command, percent in args.command_probabilities)
        args.blitz_command_possible = blitz_declared or not blitz_excluded
    elif args.commands_random_mode:
        # every character always has at least one randomly filled skill slot
        args.blitz_command_possible = not blitz_excluded
    else:
        random_exists = "Random" in args.command_strings or "Random Unique" in args.command_strings
        args.blitz_command_possible = ("Blitz" in args.command_strings) or (random_exists and not blitz_excluded)

def flags(args):
    flags = ""

    if args.commands:
        flags += " -com " + args.commands

    if args.shuffle_commands:
        flags += " -scc"

    # canonical form: every exclusion (from -rec or the legacy -recN wrappers)
    # is re-emitted as one dot-separated -rec value
    if args.random_exclude_commands:
        flags += " -rec " + ".".join(f"{command:02}" for command in args.random_exclude_commands)

    return flags

def options(args):
    result = []
    if args.commands is None:
        for option in COMMAND_OPTIONS:
            result.append((option, option, option))
    elif args.commands_random_mode in PROBABILITY_RANDOM_MODES:
        mode_name = "Custom Unique" if args.commands_random_mode == PROBABILITY_RANDOM_MODES[1] else "Custom"
        result.append(("Random Mode", mode_name, "commands"))
        for command, percent in args.command_probabilities:
            command_name = "None" if command == NONE_COMMAND else id_name[command]
            result.append((f"{command_name} Chance", f"{percent}%", f"command_probability_{command}"))
    elif args.commands_random_mode:
        mode_name = "Full Unique" if args.commands_random_mode == FULL_RANDOM_UNIQUE_MODE else "Full"
        result.append(("Random Mode", mode_name, "commands"))
        result.append(("Fight Chance", f"{args.command_fight_percent}%", "command_fight_percent"))
        result.append(("Magic Chance", f"{args.command_magic_percent}%", "command_magic_percent"))
        result.append(("Item Chance", f"{args.command_item_percent}%", "command_item_percent"))
    else:
        for index, command_string in enumerate(args.command_strings):
            result.append((COMMAND_OPTIONS[index], command_string, COMMAND_OPTIONS[index]))

    result.append(("", "", ""))
    result.append(("Shuffle Commands", args.shuffle_commands, "shuffle_commands"))

    # one row per exclusion, padded with "None" rows to the fixed six the menu
    # has always shown (extra exclusions beyond six simply add rows)
    exclude_rows = list(args.random_exclude_commands)
    while len(exclude_rows) < 6:
        exclude_rows.append(NONE_COMMAND)
    for i, command in enumerate(exclude_rows, start = 1):
        result.append(("Random Exclude", "None" if command == NONE_COMMAND else id_name[command],
                       f"random_exclude_command{i}"))

    return result

def menu(args):
    return (name(), options(args))

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
