def name():
    return "Audio"

def parse(parser):
    audio = parser.add_argument_group("Audio")
    audio.add_argument("-restoretheme", "--restore-character-check-themes", action = "store_true",
                        help = "A number of checks that would play a found character's theme now play the found character's theme if the check contains a character.")
    audio.add_argument('-restoreult2theme', '--restore-ultros2-boss-theme', action = "store_true",
                       help = "The boss in the Ultros 2 location (Opera House) will now play it's regular battle theme instead of being disabled for the Grand Finale.")

def process(args):
    args.disable_ultros2_boss_theme = not args.restore_ultros2_boss_theme
    args.replace_character_check_themes = not args.restore_character_check_themes

def flags(args):
    flags = ""
    if args.restore_ultros2_boss_theme:
        flags += " -restoreult2theme"
    if args.restore_character_check_themes:
        flags += " -restoreult2theme"

    return flags

def options(args):
    char_themes = "Original" if args.restore_character_check_themes else "Updated"
    u2_battle_theme = "Original" if args.restore_ultros2_boss_theme else "Fixed"
    return [
        ("Check Themes", char_themes),
        ("Opera Boss Theme", u2_battle_theme),
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
