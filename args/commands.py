from constants.commands import (COMMAND_OPTIONS, COMMON_COMMANDS, RETIRED_COM_MODES, RETIRED_COMMAND_FLAGS,
                                RANDOM_POSSIBLE_COMMANDS, RANDOM_COMMAND, RANDOM_UNIQUE_COMMAND, NONE_COMMAND,
                                RANDOM_EXCLUDE_COMMANDS, WEIGHT_TIERS, ALWAYS, id_name, name_id)

def name():
    return "Commands"

# The command flags compose:
# -com     traditional: one 2-digit id per character slot (99 random, 98 random
#          unique, 97 none). Alone it behaves exactly as it always has; combined
#          with -comr/-comru its explicit picks claim slots first, its 99/98
#          values mark slots for random/unique draws, and its 97 values hold
#          slots empty.
# -comr    every slot of every character is randomized: 'FIGHT.MAGIC.ITEM'
#          percent chances for the common commands (or one percent for all
#          three), every other slot a skill drawn by weight (-comru: unique).
# -comw    skill weights for every random draw (-comr/-comru slots and -com's
#          99/98 slots): 'GROUP:WEIGHT,...', unlisted skills weigh 1.
# Unique means unique across the seed: no skill is dealt twice until every
# legal skill has been dealt once (data/commands.py).

def parse(parser):
    import argparse
    commands = parser.add_argument_group("Commands")
    commands.add_argument("-com", "--commands", type = str, nargs = "*",
                          help = "Character commands: one 2 digit command id per slot "
                                 f"({len(COMMAND_OPTIONS)} ids; 99 random, 98 random unique, 97 none). "
                                 "Composable with -comr/-comru: explicit picks claim slots first, "
                                 "99/98 mark random/unique slots, 97 holds a slot empty")
    commands.add_argument("-comr", "--commands-random", type = str, default = None, metavar = "F.M.I",
                          help = "Randomize every command slot: each character gets Fight, Magic and Item "
                                 "with these percent chances ('FIGHT.MAGIC.ITEM', or one percent for all "
                                 "three; Gau never gets Fight) and every other slot gets a skill drawn by "
                                 "-comw weight. Skills may repeat between characters")
    commands.add_argument("-comru", "--commands-random-unique", type = str, default = None, metavar = "F.M.I",
                          help = "Like -comr, but skills are unique: none is dealt twice until every "
                                 "allowed skill has been dealt. Weights then set each skill's share of the "
                                 "seed's skills (a seed with more skill slots than its likelier skills can "
                                 "fill gives the rest to the less likely ones)")
    commands.add_argument("-comw", "--command-weights", type = str, default = None,
                          metavar = "GROUP:WEIGHT,...",
                          help = "Skill weights for every random draw: comma-separated GROUP:WEIGHT "
                                 "entries, a group being skill names or ids joined by '.' "
                                 "(e.g. 'jump:always,blitz.runic:5,shock.possess:0.1'). Unlisted skills "
                                 "weigh 1; a skill of weight 0.5 is drawn half as often. Weights: any "
                                 "number >= 0, or " + ", ".join(f"{tier} ({weight:g})" for tier, weight in WEIGHT_TIERS.items())
                                 + ", always[:WEIGHT] (at least one character gets it; others draw it at "
                                 "WEIGHT, default 1). 'none' weighs an empty slot (default 0)")
    commands.add_argument("-scc", "--shuffle-commands", action = "store_true", help = "Shuffle selected/randomized commands")
    # legacy single-command exclusions, kept for backward compatibility: each value is a
    # weight of 0 (and the canonical flag string re-emits them in -comw)
    for index in range(1, 7):
        commands.add_argument(f"-rec{index}", f"--random-exclude-command{index}", type = int,
                              choices = RANDOM_EXCLUDE_COMMANDS, metavar = "VALUE", default = NONE_COMMAND,
                              help = "Exclude selected command from random possibilities (legacy: use -comw NAME:0)")
    # retired flags (dev only, replaced by -comr/-comru/-comw): recognized to point at the new form
    for flag, nargs in RETIRED_COMMAND_FLAGS.items():
        commands.add_argument(flag, dest = f"retired_{flag[1:]}", nargs = nargs, default = None,
                              help = argparse.SUPPRESS)

def _process_character_commands(args, tokens):
    # one explicitly selected (or random/none) command id per character slot
    if len(tokens) != 1:
        args.parser.error(f"commands: expected a single value of command ids, got '{' '.join(tokens)}'")

    digits = 2 # number of digits each command id substring is
    value = tokens[0]
    expected_length = digits * len(COMMAND_OPTIONS)
    if not value.isdigit() or len(value) != expected_length:
        args.parser.error(f"commands: '{value}' must be {expected_length} digits "
                          f"({len(COMMAND_OPTIONS)} {digits} digit command ids)")

    args.character_commands = [int(value[index : index + digits]) for index in range(0, len(value), digits)]

    # the ids generation accepts (data/commands.py mod_commands and the
    # composed mod_probability_random_commands use the same rule): the random
    # pool plus Fight anywhere, Leap only in Gau's second slot (index 12).
    allowed = set(name_id[name] for name in RANDOM_POSSIBLE_COMMANDS) | {name_id["Fight"]}
    LEAP_INDEX = 12

    for index, command in enumerate(args.character_commands):
        if command == RANDOM_COMMAND:
            args.command_strings.append("Random")
        elif command == RANDOM_UNIQUE_COMMAND:
            args.command_strings.append("Random Unique")
        elif command == NONE_COMMAND:
            args.command_strings.append("None")
        elif command in allowed or (command == name_id["Leap"] and index == LEAP_INDEX):
            args.command_strings.append(id_name[command])
        else:
            args.parser.error(f"commands: '{command:02}' is not a valid command id for {COMMAND_OPTIONS[index]}")

    args.commands = value

def _parse_percent(args, flag, value):
    try:
        percent = int(value)
    except ValueError:
        args.parser.error(f"{flag}: '{value}' is not a valid percent chance")
    if percent < 0 or percent > 100:
        args.parser.error(f"{flag}: percent chance '{percent}' must be between 0 and 100")
    return percent

def _process_fight_magic_item(args, flag, value):
    # 'FIGHT.MAGIC.ITEM' percent chances for the three common commands, or one for all three
    percents = value.split(".")
    if len(percents) == 1:
        percents = percents * len(COMMON_COMMANDS)
    if len(percents) != len(COMMON_COMMANDS):
        args.parser.error(f"{flag}: '{value}' must be one percent chance or {len(COMMON_COMMANDS)} separated "
                          f"by '.', one each for {', '.join(COMMON_COMMANDS)}")
    return [(name_id[command_name], _parse_percent(args, flag, percent))
            for command_name, percent in zip(COMMON_COMMANDS, percents)]

def skill_key(text):
    # names compare without case, spaces or punctuation ("X Magic" -> "xmagic")
    return "".join(character for character in text.lower() if character.isalnum())

SKILL_BY_KEY = {skill_key(name) : name_id[name] for name in RANDOM_POSSIBLE_COMMANDS}

def _parse_skill(args, text):
    # a skill name or command id; 'none' is the empty slot
    key = skill_key(text)
    if key == "none":
        return NONE_COMMAND
    common = [name_id[name] for name in COMMON_COMMANDS]
    if key.isdigit():
        command = int(key)
        if command in SKILL_BY_KEY.values():
            return command
        if command == NONE_COMMAND:
            return NONE_COMMAND
    elif key in SKILL_BY_KEY:
        return SKILL_BY_KEY[key]
    if key in (skill_key(name) for name in COMMON_COMMANDS) or (key.isdigit() and int(key) in common):
        args.parser.error(f"-comw: '{text}' is a common command; set its chance with -comr/-comru")
    args.parser.error(f"-comw: '{text}' is not a randomizable skill (one of "
                      f"{', '.join(skill_key(name) for name in RANDOM_POSSIBLE_COMMANDS)}, or none)")

def _parse_weight(args, text):
    # a number >= 0 or a tier name; returns (weight, always)
    parts = text.lower().split(":")
    always = parts[0] == ALWAYS
    if always:
        if len(parts) > 2:
            args.parser.error(f"-comw: '{text}' must be always or always:WEIGHT")
        parts = parts[1:] or ["1"]
    elif len(parts) != 1:
        args.parser.error(f"-comw: '{text}' is not a weight")
    value = parts[0]
    if value in WEIGHT_TIERS:
        return WEIGHT_TIERS[value], always
    try:
        weight = float(value)
    except ValueError:
        args.parser.error(f"-comw: '{text}' is not a weight (a number >= 0, "
                          f"{', '.join(WEIGHT_TIERS)}, or always[:WEIGHT])")
    if weight < 0 or weight != weight or weight == float("inf"):
        args.parser.error(f"-comw: weight '{value}' must be a number >= 0")
    return weight, always

def _process_command_weights(args):
    # skill weights (default 1), the always skills, and the empty-slot weight
    weights = {name_id[name] : 1.0 for name in RANDOM_POSSIBLE_COMMANDS}
    weights[NONE_COMMAND] = 0.0
    always = []
    seen = {}

    # legacy -recN exclusions are weight 0
    for index in range(1, 7):
        command = getattr(args, f"random_exclude_command{index}")
        if command != NONE_COMMAND:
            weights[command] = 0.0
            seen[command] = f"-rec{index}"

    if args.command_weights:
        for entry in args.command_weights.split(","):
            group, _, weight_text = entry.partition(":")
            if not group or not weight_text:
                args.parser.error(f"-comw: '{entry}' must be GROUP:WEIGHT (e.g. shock.possess:0.5)")
            weight, is_always = _parse_weight(args, weight_text)
            for skill_text in group.split("."):
                command = _parse_skill(args, skill_text)
                if command in seen:
                    other = seen[command]
                    args.parser.error(f"-comw: '{skill_text}' is given a weight twice"
                                      + (f" (also excluded by {other})" if other.startswith("-rec") else ""))
                seen[command] = "-comw"
                if command == NONE_COMMAND and is_always:
                    args.parser.error("-comw: an empty slot cannot be always")
                weights[command] = weight
                if is_always:
                    always.append(command)

    skills = [command for command in weights if command != NONE_COMMAND]
    if not [command for command in skills if weights[command] > 0 or command in always]:
        args.parser.error("-comw: cannot give every randomly-selectable command a weight of 0")

    args.command_weights_map = weights
    args.command_always = always
    # commands random draws may never deal (weight 0, not always): the old exclusion list
    args.random_exclude_commands = [command for command in skills
                                    if weights[command] == 0 and command not in always]

def weights_value(args):
    # canonical -comw: groups by (always, weight), skills in id order, names compacted
    groups = {}
    for command, weight in args.command_weights_map.items():
        always = command in args.command_always
        default = 0.0 if command == NONE_COMMAND else 1.0
        if weight == default and not always:
            continue
        name = "none" if command == NONE_COMMAND else skill_key(id_name[command])
        groups.setdefault((always, weight), []).append((command, name))
    entries = []
    for (always, weight), members in sorted(groups.items(), key = lambda item: (not item[0][0], -item[0][1])):
        names = ".".join(name for _, name in sorted(members))
        if always:
            value = ALWAYS if weight == 1 else f"{ALWAYS}:{weight:g}"
        else:
            value = f"{weight:g}"
        entries.append(f"{names}:{value}")
    return ",".join(entries)

def process(args):
    for flag in RETIRED_COMMAND_FLAGS:
        if getattr(args, f"retired_{flag[1:]}") is not None:
            replacement = {"-comfr": "-comr", "-comfru": "-comru", "-compr": "-comr/-comru with -comw",
                           "-compru": "-comru with -comw", "-rec": "-comw NAME:0"}[flag]
            args.parser.error(f"commands: {flag} has been replaced; use {replacement} "
                              "(e.g. -comru 90 -comw shock.possess:0.5,slot:0)")

    args.character_commands = []
    args.command_strings = []
    args.command_basics = []

    if args.commands_random is not None and args.commands_random_unique is not None:
        args.parser.error("commands: -comr and -comru are incompatible; pick one")
    args.commands_unique = args.commands_random_unique is not None
    random_value = args.commands_random_unique if args.commands_unique else args.commands_random
    args.commands_probability_mode = random_value is not None

    _process_command_weights(args)

    # traditional -com (composable with -comr/-comru)
    tokens = []
    for value in args.commands or []:
        tokens.extend(value.split())
    if tokens and tokens[0].lower() in RETIRED_COM_MODES:
        args.parser.error(f"commands: '-com {tokens[0].lower()}' has been replaced; "
                          "use -comr/-comru F.M.I with -comw weights")
    if tokens:
        _process_character_commands(args, tokens)
    else:
        args.commands = None

    if args.commands_probability_mode:
        flag = "-comru" if args.commands_unique else "-comr"
        args.command_basics = _process_fight_magic_item(args, flag, random_value)
        percents = [percent for _, percent in args.command_basics]
        args.commands_random_value = (str(percents[0]) if len(set(percents)) == 1
                                      else ".".join(str(percent) for percent in percents))
    else:
        args.commands_random_value = None

    # can a blitz command exist in this configuration? (needed before objectives
    # roll a possible Suplex A Train condition)
    blitz_id = name_id["Blitz"]
    blitz_drawable = args.command_weights_map[blitz_id] > 0 or blitz_id in args.command_always
    blitz_explicit = "Blitz" in args.command_strings
    if args.commands_probability_mode:
        args.blitz_command_possible = blitz_explicit or blitz_drawable
    elif args.commands:
        random_exists = "Random" in args.command_strings or "Random Unique" in args.command_strings
        args.blitz_command_possible = blitz_explicit or (random_exists and blitz_drawable)
    else:
        args.blitz_command_possible = True

def flags(args):
    flags = ""

    if args.commands:
        flags += " -com " + args.commands
    if args.commands_random_value is not None:
        flags += (" -comru " if args.commands_unique else " -comr ") + args.commands_random_value

    weights = weights_value(args)
    if weights:
        flags += " -comw " + weights

    if args.shuffle_commands:
        flags += " -scc"

    return flags

def weight_rows(args):
    # (skill name, weight text) for every skill off the default weight
    rows = []
    for command, weight in args.command_weights_map.items():
        always = command in args.command_always
        default = 0.0 if command == NONE_COMMAND else 1.0
        if weight == default and not always:
            continue
        name = "None" if command == NONE_COMMAND else id_name[command]
        if always:
            text = "Always" if weight == 1 else f"Always {weight:g}"
        elif weight == 0:
            text = "Never"
        else:
            text = f"{weight:g}"
        rows.append((name, text))
    rows.sort(key = lambda row: row[0])
    return rows

def options(args):
    result = []
    if args.commands is None and not args.commands_probability_mode:
        for option in COMMAND_OPTIONS:
            result.append((option, option, option))
    else:
        if args.commands is not None:
            for index, command_string in enumerate(args.command_strings):
                result.append((COMMAND_OPTIONS[index], command_string, COMMAND_OPTIONS[index]))
        if args.commands_probability_mode:
            result.append(("Random Mode", "Unique" if args.commands_unique else "Repeats", "commands_unique"))
            percents = [percent for _, percent in args.command_basics]
            basics = (f"{percents[0]}%" if len(set(percents)) == 1
                      else "/".join(str(percent) for percent in percents))
            result.append(("Fight/Magic/Item", basics, "command_basics"))

    result.append(("Shuffle Commands", args.shuffle_commands, "shuffle_commands"))

    rows = weight_rows(args)
    if not rows:
        result.append(("Skill Weights", "Even", "command_weights"))
    for name, text in rows:
        result.append((f"{name} Weight", text, f"command_weight_{name}"))

    return result

def menu(args):
    # the per-skill weights go to a sub-menu, one line here
    entries = [entry for entry in options(args) if not entry[2].startswith("command_weight_")]
    # -scc only swaps whole command sets between characters under -comr/-comru, whose
    # rolls are already per character: the menu shows it only when it is on (the log keeps it)
    if args.commands_probability_mode and not args.shuffle_commands:
        entries = [entry for entry in entries if entry[2] != "shuffle_commands"]
    rows = weight_rows(args)
    if rows:
        from menus.flags_command_weights import FlagsCommandWeights
        entries.append(("Skill Weights", FlagsCommandWeights(rows), "command_weights"))
    return (name(), entries)

def log(args):
    from log import format_option
    log = [name()]

    entries = options(args)
    for entry in entries:
        log.append(format_option(*entry))

    return log
