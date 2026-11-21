"""The final boss: who the last tier of the final battle is (-fb).

Every final boss is final Kefka's enemy, in his formation and with his battle script, made over as
another monster: its looks at twice the size, a name, and whatever of his stats, script and attacks
it changes. final_boss/final_boss.py has what they share, and each has a module of its own.

To add one: write its class (final_boss/ultimaro.py is the example), and add its name here.
"""

KEFKA = "kefka"
RANDOM = "random"

def _kefka():
    from final_boss.final_boss import FinalBoss
    return FinalBoss

def _ultimaro():
    from final_boss.ultimaro import Ultimaro
    return Ultimaro

def _uncle_ulty():
    from final_boss.uncle_ulty import UncleUlty
    return UncleUlty

# name (the -fb value) : its class, imported when it is chosen
_FINAL_BOSSES = {
    KEFKA       : _kefka,
    "ultimaro"  : _ultimaro,
    "uncleulty" : _uncle_ulty,
}
NAMES = list(_FINAL_BOSSES)

_final_boss = None

def get():
    # the seed's final boss. the first call chooses it (so that a random one is chosen at the same
    # point of every roll of a seed), which is when the enemies are modified
    global _final_boss
    if _final_boss is None:
        import args
        name = args.final_boss
        if name == RANDOM:
            import random
            name = random.choice(NAMES)
        _final_boss = _FINAL_BOSSES[name]()()
    return _final_boss
