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
    # characters.py - starting level: a user -stlr replaces the injected -stl
    {'-stl', '-stlr'},
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
    # commands.py - skill weights: a user -comw (or a legacy -recN exclusion, a
    # weight of 0) replaces the default weights
    {'-comw', '-rec1', '-rec2', '-rec3', '-rec4', '-rec5', '-rec6'},
    # commands.py - command flags: a user command flag of any family replaces
    # the default -comru (the families compose, but the injected default should
    # not silently combine with an explicit user choice)
    {'-com', '-comr', '-comru'},
]

# Build a lookup: flag -> set of all flags in its exclusive group
_FLAG_TO_GROUP = {}
for group in MUTUALLY_EXCLUSIVE_GROUPS:
    for flag in group:
        _FLAG_TO_GROUP[flag] = group

# Default flags for -ruin mode, organized by category.
# This is the shared base: a bare '-ruin' expands to exactly this set, while
# '-ruin hard' (the roguelike difficulty) swaps the values in
# RUIN_HARD_OVERRIDES and injects RUIN_HARD_EXTRAS below, and '-ruin easy'
# (the relaxed difficulty) swaps the values in RUIN_EASY_OVERRIDES and then
# injects RUIN_EASY_EXTRAS.
RUIN_DEFAULT_FLAGS = {
    'settings': ['-cg'],
    'objectives': [
                   # map size comes from -rce: characters, and espers + item
                   # rewards (not an objective; KT-unlock objectives are
                   # unused in ruination mode)
                   '-rce', '6.9',
                   # item rewards on character/esper checks only as a rare
                   # surprise (1%); the boss item-only rewards supply items
                   '-rirc', '1',
                   # at least 55 treasure chests (MIAB included, Kefka's Tower
                   # not counted) in the rooms the map wires in
                   '-rrtc', '55',
                   '-oa', '59.3.3.11.29.11.30.11.31.10.12.12',
                   '-ob', '30.8.8.3.3.11.6.11.7.11.8.10.12.12',
                   # silent start bonuses: +100 max HP for all, full heal
                   #'-oc', '74.100.100.0.0',
                   #'-od', '55.0.0',
                   ],

    # Party flags
    'starting_chars': ['-sc1', 'random', '-sc2', 'random', '-sc3', 'random'],
    'party': ['-sal', '-eu', '-csrp', '80', '125', '-stl', '6'],

    # Command flags
    'commands': [
        '-fst', '-brl', '-slr', '3', '5', '-lmprp', '75', '125', '-lel',
        '-srr', '25', '35', '-rnl', '-rnc', '-sdr', '1', '2', '-das', '-dda',
        '-dns', '-sch', '-scis',
        # seed-wide unique skills: Fight/Magic/Item 90% per character, Shock and
        # Possess at half weight, so in half as many seeds as the other skills
        # (~41% vs ~82%)
        '-comru', '90',
        '-comw', 'shock.possess:0.5',
    ],

    # Battle flags
    'battle': [
        # soft level cap at 48 (width 10); easy drops it and hard makes it a hard cap
        '-xpm', '8', '-mpm', '5', '-gpm', '0', '-lc', '48', '10', '-lsced', '2', '-hmced', '2',
        '-xgced', '2', '-ase', '2', '-msl', '40', '-sed', '-bbs',
        '-drloc', 'shuffle', '-stloc', 'mix', '-be', '-bnu', '-res',
        '-fer', '0', '-escr', '100', '-dgne', '-wnz', '-mmnu', '-cmd'
    ],

    # Magic flags
    'magic': [
        '-esr', '3', '5', '-elrt', '-ebr', '88', '-emprp', '75', '125',
        '-nm1', 'random', '-rnl1', '-rns1', '-nm2', 'random', '-rnl2',
        '-rns2', '-nmmi', '-mmprp', '75', '125', '-emi'
    ],

    # Item flags
    'items': [
        '-gp', '6000', '-smc', '3', '-sto', '1', '-ieor', '33', '-ieror', '33',
        '-ir', 'ruin', '-csb', '10', '18', '-mca', '-stra', '-saw',
        '-sisr', '20', '-sprp', '75', '125', '-sdm', '4', '-npi', '-sebr', '-sli', '-ssf4',
        '-snsb', '-snee', '-snil', '-ccsr', '20', '-chrm', '7', '0', '-cms', '-nee'
    ],

    # Other flags
    'other': [
        '-frw', '-wmhc', '-cor', '100', '-crr', '100', '-crvr', '50', '100',
        '-crm', '-ari', '-anca', '-adeh', '-ame', '1', '-nmc', '-noshoes',
        '-u254', '-nfps', '-fs', '-fe', '-fvd', '-fr', '-fj', '-fbs',
        '-fedc', '-fc', '-ond', '-etn', '-move', 'bd', '-maze', 'iso',
        '-nfh', '-rkt', '-oss'
    ]
}

# Extra defaults for '-ruin hard' (the roguelike difficulty): permadeath with
# a small Fenix Down reserve, ironmog-lite saves, and the strongest recovery
# spells removed from learnable sources.  A bare '-ruin' skips these, keeping
# the base flagset.  Both variants honor '-no <flag>' removal.
# The -rls value uses numeric spell ids (53 = Life 3, 42 = Warp, 50 = Antdot,
# 51 = Remedy) because spell names contain spaces, which would break
# flag-string round-trips.
RUIN_HARD_EXTRAS = {
    'hard': ['-pd', '-sfd', '3', '-rls', '53,42,50,51', '-nosaves', 'mid'],
}
RUIN_HARD_OVERRIDES = {
    '-lc': ['-lc', '48'],               # hard level cap at 48 (base: soft cap 48, width 10)
}

# '-ruin easy' (the relaxed difficulty): a tutorial for ruination maps - the
# standard flow and mechanics (character gating, the same starting level) made
# softer, rather than a separate fast mode.  The base flagset with these values
# swapped - a base flag listed here is replaced by the tokens given (an empty
# list drops it) - and RUIN_EASY_EXTRAS injected after it.  Both are subject to
# '-no <flag>' removal and to the mutually exclusive groups like every other
# default.  (Reworked 2026-10 from playtesting: no longer -open, no starting
# espers, -stl back to the base 6.)
RUIN_EASY_OVERRIDES = {
    '-rce': ['-rce', '6.6'],            # smaller map: 6 characters + 6 espers/items
    '-sc3': ['-sc3', 'random', '-sc4', 'random'],  # four starting characters: early offense
    '-lsced': ['-lsced', '1.5'],        # gentler enemy level scaling (base 2)
    '-hmced': ['-hmced', '1.5'],        # gentler enemy hp/mp scaling (base 2); exp/gp stays 2
    '-esr': ['-esr', '5', '5'],         # every esper teaches five spells
    '-ebr': ['-ebr', '100'],            # every esper gives a level-up bonus
    '-gp': ['-gp', '12000'],            # double starting gp
    '-ssf4': [],                        # standard 1/2 sell prices instead of 1/4
    '-chrm': ['-chrm', '2', '0'],       # rare monsters-in-a-box (base 7%)
    '-lc': [],                          # no level cap
}
RUIN_EASY_EXTRAS = {
    'easy': [
        '-si', '233.6.6',               # six Potions (item 233)
        '-sws', '10',                   # ten Warp Stones
        '-sfd', '3',                    # three Fenix Downs
        '-sj', '12',                    # twelve starting junk items
        '-rrt',                         # a shop town on every branch
        # High Tier Item rewards at 3 and 6 espers obtained
        '-oc', '58.1.1.4.3.3',
        '-od', '58.1.1.4.6.6',
    ],
}

# '-ruin fast' (2026-10-28): the standard flagset on easy's smaller map, with
# easy's two High Tier Item objectives and a few of its comforts (four
# starting characters, easy's esper spells/bonuses, no level cap, a shop town
# on every branch, the twelve starting junk items), 10x experience and
# steeper enemy scaling (2.5 per character/esper/dragon for levels, hp/mp
# and exp/gp: the smaller map has fewer of each).  Gp, sell prices,
# monster-in-a-box odds and the other starting items stay standard.
RUIN_FAST_OVERRIDES = {
    '-rce': ['-rce', '6.6'],            # smaller map: 6 characters + 6 espers/items
    '-sc3': ['-sc3', 'random', '-sc4', 'random'],  # four starting characters
    '-esr': ['-esr', '5', '5'],         # every esper teaches five spells
    '-ebr': ['-ebr', '100'],            # every esper gives a level-up bonus
    '-lc': [],                          # no level cap
    '-xpm': ['-xpm', '10'],             # 10x experience (base 8)
    '-lsced': ['-lsced', '2.5'],        # enemy level scaling (base 2)
    '-hmced': ['-hmced', '2.5'],        # enemy hp/mp scaling (base 2)
    '-xgced': ['-xgced', '2.5'],        # enemy exp/gp scaling (base 2)
}
RUIN_FAST_EXTRAS = {
    'fast': [
        '-sj', '12',                    # twelve starting junk items
        '-rrt',                         # a shop town on every branch
        # High Tier Item rewards at 3 and 6 espers obtained
        '-oc', '58.1.1.4.3.3',
        '-od', '58.1.1.4.6.6',
    ],
}
RUIN_MODE_EXTRAS = {**RUIN_HARD_EXTRAS, **RUIN_EASY_EXTRAS, **RUIN_FAST_EXTRAS}
RUIN_MODE_OVERRIDES = {'easy': RUIN_EASY_OVERRIDES, 'hard': RUIN_HARD_OVERRIDES,
                       'fast': RUIN_FAST_OVERRIDES}

# Flags that have arguments (used for proper flag removal).
#
# Multi-token default values are fine -- list each token as its own entry
# (e.g. '-csrp', '80', '125') and set this count to the number of value
# tokens the DEFAULT uses. Variable-arity flags like -com take whatever
# count matches the injected form (1 for an id string, 2 for 'fr X.Y.Z').
# The only hard rule is that a single value token must not contain a space
# (spell names like "Life 3" -- use ids instead): the logged flag string
# has no quoting, so a spaced value would re-parse as two tokens.
FLAGS_WITH_ARGS = {
    '-ob': 1, '-oc': 1, '-od': 1, '-oe': 1, '-rls': 1, '-sfd': 1, '-nosaves': 1,
    '-stl': 1, '-stlr': 2, '-stesp': 2, '-si': 1, '-sws': 1, '-sj': 1,
    '-gpm': 1, '-lc': 2, '-oa': 1, '-rce': 1, '-rirc': 1, '-rrtc': 1, '-sc1': 1, '-sc2': 1, '-sc3': 1, '-sc4': 1, '-csrp': 2,
    '-slr': 2, '-lmprp': 2, '-srr': 2, '-sdr': 2, '-com': 1, '-comr': 1, '-comru': 1,
    '-comw': 1, '-rec1': 1, '-rec2': 1,
    '-xpm': 1, '-mpm': 1, '-lsced': 1, '-hmced': 1, '-xgced': 1, '-ase': 1,
    '-msl': 1, '-drloc': 1, '-stloc': 1, '-fer': 1, '-escr': 1,
    '-esr': 2, '-ebr': 1, '-emprp': 2, '-nm1': 1, '-nm2': 1, '-mmprp': 2,
    '-gp': 1, '-smc': 1, '-sto': 1, '-ieor': 1, '-ieror': 1, '-ir': 1,
    '-csb': 2, '-sisr': 1, '-sprp': 2, '-sdm': 1, '-ccsr': 1, '-chrm': 2,
    '-cor': 1, '-crr': 1, '-crvr': 2, '-ame': 1, '-move': 1,
}

def value_count(flags, i):
    """
    The number of value tokens after the flag at flags[i]: its FLAGS_WITH_ARGS
    count, cut short at the next flag token, so a flag can be given fewer values
    than its most (hard's one-value '-lc 48' against the base '-lc 48 10').
    """
    count = 0
    for token in flags[i + 1:i + 1 + FLAGS_WITH_ARGS.get(flags[i], 0)]:
        if token.startswith('-'):
            break
        count += 1
    return count

# Starting character related flags that should be removed together
STARTING_CHAR_FLAGS = ['-sc1', '-sc2', '-sc3', '-sc4']

def get_all_default_flags():
    """Returns a flat list of all default flags for -ruin mode."""
    flags = []
    for category in RUIN_DEFAULT_FLAGS.values():
        flags.extend(category)
    return flags

def mode_categories(mode):
    """
    The (category, flags) list a '-ruin <mode>' expands to, before '-no' and
    mutually-exclusive suppression: the base categories with the mode's
    overrides applied, then the mode's extras.  mode is None for a bare -ruin.
    """
    overrides = RUIN_MODE_OVERRIDES.get(mode, {})
    categories = []
    for category, flags in RUIN_DEFAULT_FLAGS.items():
        result = []
        i = 0
        while i < len(flags):
            flag = flags[i]
            num_args = value_count(flags, i)
            if flag in overrides:
                result.extend(overrides[flag])
            else:
                result.extend(flags[i:i + num_args + 1])
            i += num_args + 1
        categories.append((category, result))
    if mode in RUIN_MODE_EXTRAS:
        categories.append((mode, list(RUIN_MODE_EXTRAS[mode])))
    return categories

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
    Returns True if any -sc1..-sc4 is found after the ruin index.
    """
    for flag in STARTING_CHAR_FLAGS:
        for i in range(ruin_index + 1, len(argv)):
            if argv[i] == flag:
                return True
    return False

def count_required_characters(argv, ruin_index):
    """
    Count the character values given to -rc/--require-characters after -ruin.
    Required characters join the starting party (see args/starting_party.py), so
    each one consumes a default '-scN random' slot: '-ruin -rc terra' keeps the
    default party size of 3 (random, random, terra) instead of growing to 4.
    """
    count = 0
    for i in range(ruin_index + 1, len(argv)):
        if argv[i] in ('-rc', '--require-characters'):
            j = i + 1
            while j < len(argv) and not argv[j].startswith('-'):
                count += 1
                j += 1
    return count

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
    - If followed by 'custom', don't inject defaults
    - If followed by 'hard', inject the base defaults with RUIN_HARD_OVERRIDES
      applied, plus RUIN_HARD_EXTRAS
    - If followed by 'easy', inject the base defaults with RUIN_EASY_OVERRIDES
      applied, plus RUIN_EASY_EXTRAS
    - If followed by 'fast', likewise with RUIN_FAST_OVERRIDES / RUIN_FAST_EXTRAS
    - Otherwise (default), inject the base default flags only
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

    # Check for a mode value ('custom'/'hard'/'easy'/'fast') following -ruin
    next_arg = argv[ruin_index + 1] if ruin_index + 1 < len(argv) else None

    if next_arg == 'custom':
        # Don't inject defaults, but keep 'custom' for the argument parser
        return argv

    mode = next_arg if next_arg in RUIN_MODE_EXTRAS else None
    # Keep the mode token adjacent to -ruin: inject after it
    insert_index = ruin_index + 2 if mode else ruin_index + 1

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

    # Build list of default flags to inject (excluding disabled and conflicting ones)
    categories = mode_categories(mode)

    # -rc required characters consume default starting-party slots (drop the
    # trailing '-scN random' defaults the mode injects, one per required
    # character: -sc3 on a three-character start, -sc4 on easy's four)
    required_char_count = count_required_characters(argv, ruin_index)
    if required_char_count and not user_specified_chars:
        party_tokens = [token for category, flags in categories if category == 'starting_chars'
                        for token in flags]
        default_slots = [flag for flag in STARTING_CHAR_FLAGS if flag in party_tokens]
        for flag in default_slots[len(default_slots) - min(required_char_count, len(default_slots)):]:
            flags_to_disable.add(flag)

    # Find default flags that conflict with user-specified mutually exclusive flags
    exclusive_suppressed = get_user_exclusive_flags(argv, ruin_index)

    defaults_to_inject = []
    for category, flags in categories:
        # Skip starting_chars if user specified their own
        if category == 'starting_chars' and user_specified_chars:
            continue

        # Add flags from this category, skipping disabled and conflicting ones
        i = 0
        while i < len(flags):
            flag = flags[i]
            if flag not in flags_to_disable and flag not in exclusive_suppressed:
                # Add the flag and its values
                num_args = value_count(flags, i)
                defaults_to_inject.extend(flags[i:i + num_args + 1])
                i += num_args + 1
            else:
                # Skip this flag and its values
                i += value_count(flags, i) + 1

    # Insert defaults right after -ruin (and its mode value, if present)
    for i, flag in enumerate(defaults_to_inject):
        argv.insert(insert_index + i, flag)

    return argv

def preprocess_arguments():
    """
    Main entry point for argument preprocessing.
    Call this before ArgumentParser.parse_args().
    """
    preprocess_ruin_flag(sys.argv)
