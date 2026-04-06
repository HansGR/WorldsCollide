"""
Argument preprocessor for -ruin meta-flag.

This module handles expanding the -ruin flag into a full set of default flags,
and provides mechanisms for users to override or disable specific defaults.
"""

import sys

# Global flag to track if preprocessing has been done
_preprocessing_done = False

# Mutually exclusive flag groups from argparse definitions.
# When a user specifies a flag from one of these groups, any default ruin flag
# in the same group must be removed to avoid argparse conflicts.
MUTUALLY_EXCLUSIVE_GROUPS = [
    # settings.py - mode
    {'-open', '-cg'},
    # scaling.py - level scaling
    {'-lsa', '-lsh', '-lsce', '-lsced', '-lsc', '-lsbd', '-lst'},
    # scaling.py - hp/mp scaling
    {'-hma', '-hmh', '-hmce', '-hmced', '-hmc', '-hmt', '-hmbd'},
    # scaling.py - xp/gp scaling
    {'-xga', '-xgh', '-xgce', '-xgced', '-xgc', '-xgt', '-xgbd'},
    # scaling.py - ability scaling
    {'-ase', '-asr'},
    # bosses.py - boss battles
    {'-bbs', '-bbr'},
    # bosses.py - dragons
    {'-drloc', '-bmbd'},
    # bosses.py - statues
    {'-stloc'},
    # encounters.py - random encounters
    {'-res', '-rer', '-rechu'},
    # encounters.py - fixed encounters
    {'-fer'},
    # encounters.py - escapable
    {'-escr'},
    # espers.py - esper spells
    {'-esrr', '-ess', '-essrr', '-esr', '-esrt'},
    # espers.py - esper learn rates
    {'-elr', '-elrt'},
    # espers.py - esper bonuses
    {'-ebs', '-ebr'},
    # espers.py - esper mp
    {'-emps', '-emprv', '-emprp'},
    # espers.py - esper equipable
    {'-eer', '-eebr'},
    # lores.py - lores mp
    {'-lmps', '-lmprv', '-lmprp'},
    # misc_magic.py - magic mp
    {'-mmps', '-mmprv', '-mmprp'},
    # items.py - item equipable
    {'-ier', '-iebr', '-ietr', '-ieor', '-iesr'},
    # items.py - item equipable relic
    {'-ierr', '-ierbr', '-iertr', '-ieror', '-iersr'},
    # shops.py - shop inventory
    {'-sisr', '-sirt', '-sie'},
    # shops.py - shop prices
    {'-sprv', '-sprp'},
    # shops.py - shop sell fraction
    {'-ssf4', '-ssf8', '-ssf0'},
    # chests.py - chest contents
    {'-ccsr', '-ccrt', '-ccrs', '-cce'},
    # coliseum.py - coliseum opponents
    {'-cor', '-cosr'},
    # coliseum.py - coliseum rewards
    {'-crr', '-crsr'},
    # steal.py - steal chances
    {'-sch', '-sca'},
    # graphics.py - flash removal
    {'-frw', '-frm'},
    # challenges.py - ultima
    {'-nu', '-u254'},
    # misc.py - event timers
    {'-etr', '-etn'},
    # misc.py - y npc
    {'-ymascot', '-ycreature', '-yimperial', '-ymain', '-yreflect',
     '-ystone', '-yvxz', '-ysketch', '-yrandom', '-yremove'},
]

# Build a lookup: flag -> set of all flags in its exclusive group
_FLAG_TO_GROUP = {}
for group in MUTUALLY_EXCLUSIVE_GROUPS:
    for flag in group:
        _FLAG_TO_GROUP[flag] = group

# Default flags for -ruin mode, organized by category
RUIN_DEFAULT_FLAGS = {
    'settings': ['-cg'],
    'objectives': ['-oa', '2.2.2.2.6.6.4.9.9'],

    # Party flags
    'starting_chars': ['-sc1', 'random', '-sc2', 'random', '-sc3', 'random'],
    'party': ['-sal', '-eu', '-csrp', '80', '125'],

    # Command flags
    'commands': [
        '-fst', '-brl', '-slr', '3', '5', '-lmprp', '75', '125', '-lel',
        '-srr', '25', '35', '-rnl', '-rnc', '-sdr', '1', '2', '-das', '-dda',
        '-dns', '-sch', '-scis', '-com', '98989898989898989898989898',
        '-rec1', '28', '-rec2', '27'
    ],

    # Battle flags
    'battle': [
        '-xpm', '3', '-mpm', '5', '-gpm', '0', '-nxppd', '-lsced', '2', '-hmced', '2',
        '-xgced', '2', '-ase', '2', '-msl', '40', '-sed', '-bbs',
        '-drloc', 'shuffle', '-stloc', 'mix', '-be', '-bnu', '-res',
        '-fer', '0', '-escr', '100', '-dgne', '-wnz', '-mmnu', '-cmd'
    ],

    # Magic flags
    'magic': [
        '-esr', '2', '5', '-elrt', '-ebr', '82', '-emprp', '75', '125',
        '-nm1', 'random', '-rnl1', '-rns1', '-nm2', 'random', '-rnl2',
        '-rns2', '-nmmi', '-mmprp', '75', '125'
    ],

    # Item flags
    'items': [
        '-gp', '5000', '-smc', '3', '-sto', '1', '-ieor', '33', '-ieror', '33',
        '-ir', 'stronger', '-csb', '6', '14', '-mca', '-stra', '-saw',
        '-sisr', '20', '-sprp', '75', '125', '-sdm', '4', '-npi', '-sebr', '-seri',
        '-snsb', '-snee', '-snil', '-ccsr', '20', '-chrm', '5', '0', '-cms'
    ],

    # Other flags
    'other': [
        '-frw', '-wmhc', '-cor', '100', '-crr', '100', '-crvr', '150', '200',
        '-crm', '-ari', '-anca', '-adeh', '-ame', '1', '-nmc', '-noshoes',
        '-u254', '-nfps', '-fs', '-fe', '-fvd', '-fr', '-fj', '-fbs',
        '-fedc', '-fc', '-ond', '-etn', '-move', 'bd', '-sl', '-maze', 'iso',
    ]
}

# Flags that have arguments (used for proper flag removal)
FLAGS_WITH_ARGS = {
    '-gpm': 1, '-oa': 1, '-sc1': 1, '-sc2': 1, '-sc3': 1, '-csrp': 2,
    '-slr': 2, '-lmprp': 2, '-srr': 2, '-sdr': 2, '-com': 1, '-rec1': 1, '-rec2': 1,
    '-xpm': 1, '-mpm': 1, '-lsced': 1, '-hmced': 1, '-xgced': 1, '-ase': 1,
    '-msl': 1, '-drloc': 1, '-stloc': 1, '-fer': 1, '-escr': 1,
    '-esr': 2, '-ebr': 1, '-emprp': 2, '-nm1': 1, '-nm2': 1, '-mmprp': 2,
    '-gp': 1, '-smc': 1, '-sto': 1, '-ieor': 1, '-ieror': 1, '-ir': 1,
    '-csb': 2, '-sisr': 1, '-sprp': 2, '-sdm': 1, '-ccsr': 1, '-chrm': 2,
    '-cor': 1, '-crr': 1, '-crvr': 2, '-ame': 1, '-move': 1,
}

# Starting character related flags that should be removed together
STARTING_CHAR_FLAGS = ['-sc1', '-sc2', '-sc3']

def get_all_default_flags():
    """Returns a flat list of all default flags for -ruin mode."""
    flags = []
    for category in RUIN_DEFAULT_FLAGS.values():
        flags.extend(category)
    return flags

def find_flag_indices(argv, flag):
    """
    Find all indices where a flag appears in argv.
    Returns list of (index, num_args) tuples.
    """
    indices = []
    i = 0
    while i < len(argv):
        if argv[i] == flag:
            num_args = FLAGS_WITH_ARGS.get(flag, 0)
            indices.append((i, num_args))
            i += num_args + 1
        else:
            i += 1
    return indices

def remove_flag_from_list(argv, flag):
    """
    Remove all occurrences of a flag and its arguments from argv.
    Returns the modified list.
    """
    num_args = FLAGS_WITH_ARGS.get(flag, 0)

    while flag in argv:
        idx = argv.index(flag)
        # Remove flag and its arguments
        for _ in range(num_args + 1):
            if idx < len(argv):
                argv.pop(idx)

    return argv

def check_user_specified_starting_chars(argv, ruin_index):
    """
    Check if user specified any starting character flags after -ruin.
    Returns True if any -sc1, -sc2, or -sc3 are found after the ruin index.
    """
    for flag in STARTING_CHAR_FLAGS:
        for i in range(ruin_index + 1, len(argv)):
            if argv[i] == flag:
                return True
    return False

def get_user_exclusive_flags(argv, ruin_index):
    """
    Scan user-specified args (after -ruin) for flags belonging to mutually
    exclusive groups. Returns the set of all default flags that must be
    suppressed to avoid argparse conflicts.
    """
    flags_to_suppress = set()
    user_args = set(arg for arg in argv[ruin_index + 1:] if arg.startswith('-'))

    for user_flag in user_args:
        group = _FLAG_TO_GROUP.get(user_flag)
        if group is None:
            continue
        # Suppress all OTHER flags in this group (the user's flag wins)
        for group_flag in group:
            if group_flag != user_flag:
                flags_to_suppress.add(group_flag)

    return flags_to_suppress

def preprocess_ruin_flag(argv=None):
    """
    Preprocess command-line arguments to expand -ruin meta-flag.

    If -ruin is present:
    - If followed by 'minimum', don't inject defaults
    - Otherwise, inject all default flags
    - Process -no flags to remove specific defaults
    - If user specifies starting character flags, remove default starting chars

    Modifies argv in place and returns it.
    """
    global _preprocessing_done

    if argv is None:
        argv = sys.argv

    # Check if preprocessing has already been done
    if _preprocessing_done:
        return argv

    # Find -ruin flag
    if '-ruin' not in argv:
        return argv

    ruin_index = argv.index('-ruin')

    # Mark that we've preprocessed
    _preprocessing_done = True

    # Check for 'custom' option
    next_arg_is_custom = (
        ruin_index + 1 < len(argv) and
        argv[ruin_index + 1] == 'custom'
    )

    if next_arg_is_custom:
        # Don't inject defaults, but keep 'custom' for the argument parser
        return argv

    # Collect flags to disable via -no and remove -no from argv FIRST
    # Handle multiple -no groups: e.g. "-no flag1 -no flag2" or "-no flag1 flag2"
    flags_to_disable = set()
    while '-no' in argv:
        no_index = argv.index('-no')
        argv.pop(no_index)  # Remove -no itself first
        # Collect and remove all following non-flag arguments
        while no_index < len(argv) and not argv[no_index].startswith('-'):
            flag_name = argv.pop(no_index)
            flags_to_disable.add('-' + flag_name)

    # Check if user specified any starting character flags
    user_specified_chars = check_user_specified_starting_chars(argv, ruin_index)

    # Find default flags that conflict with user-specified mutually exclusive flags
    exclusive_suppressed = get_user_exclusive_flags(argv, ruin_index)

    # Build list of default flags to inject (excluding disabled and conflicting ones)
    defaults_to_inject = []
    for category, flags in RUIN_DEFAULT_FLAGS.items():
        # Skip starting_chars if user specified their own
        if category == 'starting_chars' and user_specified_chars:
            continue

        # Add flags from this category, skipping disabled and conflicting ones
        i = 0
        while i < len(flags):
            flag = flags[i]
            if flag not in flags_to_disable and flag not in exclusive_suppressed:
                # Add the flag
                defaults_to_inject.append(flag)
                # Add its arguments if any
                num_args = FLAGS_WITH_ARGS.get(flag, 0)
                for j in range(num_args):
                    if i + 1 + j < len(flags):
                        defaults_to_inject.append(flags[i + 1 + j])
                i += num_args + 1
            else:
                # Skip this flag and its arguments
                num_args = FLAGS_WITH_ARGS.get(flag, 0)
                i += num_args + 1

    # Insert defaults right after -ruin flag
    for i, flag in enumerate(defaults_to_inject):
        argv.insert(ruin_index + 1 + i, flag)

    return argv

def preprocess_arguments():
    """
    Main entry point for argument preprocessing.
    Call this before ArgumentParser.parse_args().
    """
    preprocess_ruin_flag(sys.argv)
