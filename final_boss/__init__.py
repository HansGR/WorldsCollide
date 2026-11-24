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

def _grampaluma():
    from final_boss.grampaluma import Grampaluma
    return Grampaluma

def _king_pug():
    from final_boss.king_pug import KingPug
    return KingPug

def _czar_dragon():
    from final_boss.czar_dragon import CzarDragon
    return CzarDragon

def _juggernaut():
    from final_boss.juggernaut import Juggernaut
    return Juggernaut

# name (the -fb value) : its class, imported when it is chosen
_FINAL_BOSSES = {
    KEFKA       : _kefka,
    "ultimaro"  : _ultimaro,
    "uncleulty" : _uncle_ulty,
    "grampaluma": _grampaluma,
    "kingpug"   : _king_pug,
    "czardragon": _czar_dragon,
    "juggernaut": _juggernaut,
}
NAMES = list(_FINAL_BOSSES)

# the attacks only final kefka has, which the other final bosses change
OWN_ABILITIES = ("HyperDrive", "Goner")

_final_boss = None

def own_abilities():
    # with -fb (any final boss but the default: a random one may be kefka), the final boss's attacks
    # are his alone: no other enemy gets them from ability scaling (they are taken out of its tiers,
    # data/enemy_script_custom_commands.py, which would otherwise tell a random final boss apart
    # before the battle), and with -sfb his own are not scaled into others
    # (data/enemy_script_abilities.py)
    import args
    return OWN_ABILITIES if args.final_boss != KEFKA else ()

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
