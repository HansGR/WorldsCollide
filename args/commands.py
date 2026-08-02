from constants.commands import (COMMAND_OPTIONS, COMMON_COMMANDS, FULL_RANDOM_MODES, FULL_RANDOM_UNIQUE_MODE,
                                RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND, RANDOM_EXCLUDE_COMMANDS,
                                id_name, name_id)

def name():
    return "Commands"

COMMANDS_HELP = ("Character commands: either one id per character ('%s' 2 digit command ids) or a full random mode "
                 "('fr' / 'fru' followed by 'FIGHT.MAGIC.ITEM' percent chances, e.g. 'fr 10.50.90')"
                 % len(COMMAND_OPTIONS))

def parse(parser):
    commands = parser.add_argument_group("Commands")
    commands.add_argument("-com", "--commands", type = str, nargs = "*", help = COMMANDS_HELP)
    commands.add_argument("-scc", "--shuffle-commands", action = "store_true", help = "Shuffle selected/randomized commands")
    commands.add_argument("-rec1", "--random-exclude-command1", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")
    commands.add_argument("-rec2", "--random-exclude-command2", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")
    commands.add_argument("-rec3", "--random-exclude-command3", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")
    commands.add_argument("-rec4", "--random-exclude-command4", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")
    commands.add_argument("-rec5", "--random-exclude-command5", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")
    commands.add_argument("-rec6", "--random-exclude-command6", type = int, choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND, help = "Exclude selected command from random possibilities")

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

def process(args):
    tokens = []
    for value in args.commands or []:
        tokens.extend(value.split())

    args.commands_random_mode = None
    args.character_commands = []
    args.command_strings = []
    args.command_fight_percent = 0
    args.command_magic_percent = 0
    args.command_item_percent = 0

    if not tokens:
        args.commands = None
        args.blitz_command_possible = True
        return

    # store the normalized value back so flags()/options() have a single canonical string
    args.commands = " ".join(tokens)

    if tokens[0].lower() in FULL_RANDOM_MODES:
        _process_full_random(args, tokens)
    else:
        _process_character_commands(args, tokens)

    args.random_exclude_commands = []
    if args.random_exclude_command1 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command1)
    if args.random_exclude_command2 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command2)
    if args.random_exclude_command3 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command3)
    if args.random_exclude_command4 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command4)
    if args.random_exclude_command5 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command5)
    if args.random_exclude_command6 != NONE_COMMAND:
        args.random_exclude_commands.append(args.random_exclude_command6)

    blitz_excluded = name_id["Blitz"] in args.random_exclude_commands
    if args.commands_random_mode:
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

    if args.random_exclude_command1 != NONE_COMMAND:
        flags += f" -rec1 {args.random_exclude_command1}"
    if args.random_exclude_command2 != NONE_COMMAND:
        flags += f" -rec2 {args.random_exclude_command2}"
    if args.random_exclude_command3 != NONE_COMMAND:
        flags += f" -rec3 {args.random_exclude_command3}"
    if args.random_exclude_command4 != NONE_COMMAND:
        flags += f" -rec4 {args.random_exclude_command4}"
    if args.random_exclude_command5 != NONE_COMMAND:
        flags += f" -rec5 {args.random_exclude_command5}"
    if args.random_exclude_command6 != NONE_COMMAND:
        flags += f" -rec6 {args.random_exclude_command6}"

    return flags

def options(args):
    result = []
    if args.commands is None:
        for option in COMMAND_OPTIONS:
            result.append((option, option, option))
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

    add_exclude_command = lambda command, i : result.append(("Random Exclude", "None" if command == NONE_COMMAND else id_name[command], f"random_exclude_command{i}"))

    add_exclude_command(args.random_exclude_command1, 1)
    add_exclude_command(args.random_exclude_command2, 2)
    add_exclude_command(args.random_exclude_command3, 3)
    add_exclude_command(args.random_exclude_command4, 4)
    add_exclude_command(args.random_exclude_command5, 5)
    add_exclude_command(args.random_exclude_command6, 6)

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
