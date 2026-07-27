"""Build test-only ROMs with a forced door map.

For playtesting specific door mechanics it is often easier to force a
connection than to roll seeds until the planner happens to place it.
`build_override_rom` builds a normal seed but rewires chosen door pairs
AFTER the planner (and its softlock verifier) have run: the resulting map
would not validate as a real seed, but every mechanical layer downstream
(realization, exit events, gating) is exercised exactly as in a real build.

Example -- connect Narshe School doors straight to the two Magitek boss
doors so their rooms can be entered 'backwards' from the hub:

    build_override_rom(vanilla, out, rewires=[(393, 715), (394, 706)])

Each rewire (a, b) detaches b from its planned pair (if placed) and marries
it to a; the two orphaned ex-partners are paired with each other so the pair
list stays well-formed. Works by monkeypatching doors.plan.modes.plan_for_args
for the duration of one wc.main() run, so it must own the process (the wc
build machinery is import-once); run it in a fresh interpreter per ROM.

CLI: python3 tools/playtest/override.py <vanilla.smc> <out.smc> a:b [c:d ...]
     [-- extra wc.py flags, default: -sl -s 1002 -ruin]
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

DEFAULT_FLAGS = ["-sl", "-s", "1002", "-ruin"]


def build_override_rom(vanilla, out, rewires, flags=None):
    """Build `out` from `vanilla` with the given [(door, target), ...] rewires
    applied to the planned door pairs. Must be the first and only build in
    this process."""
    os.chdir(ROOT)
    sys.argv = ["wc.py", "-i", vanilla, "-o", out] + list(flags or DEFAULT_FLAGS)

    import doors.plan.modes as modes
    real = modes.plan_for_args

    def patched(args, rng, characters=None):
        plan = real(args, rng, characters=characters)
        for door, target in rewires:
            _repartner(plan, door, target)
        return plan

    modes.plan_for_args = patched
    try:
        import wc
        wc.main()
    finally:
        modes.plan_for_args = real
    return out


def _repartner(plan, door, target):
    """Rewire `door`'s pair to point at `target`, keeping the pair list
    well-formed (each id in at most one pair)."""
    orphan = None
    for p in list(plan.door_pairs):
        if target in p:
            orphan = p[0] if p[1] == target else p[1]
            plan.door_pairs.remove(p)
            break
    for p in plan.door_pairs:
        if door in p:
            i = p.index(door)
            old_partner = p[1 - i]
            p[1 - i] = target
            if orphan is not None:
                plan.door_pairs.append([old_partner, orphan])
            print(f"[OVERRIDE] {door} <-> {target} "
                  f"(old partner {old_partner}, orphan {orphan})")
            return
    raise RuntimeError(f"door {door} not found in the planned pairs")


def main():
    argv = sys.argv[1:]
    if "--" in argv:
        split = argv.index("--")
        argv, flags = argv[:split], argv[split + 1:]
    else:
        flags = None
    vanilla, out = argv[0], argv[1]
    rewires = [tuple(int(v) for v in spec.split(":")) for spec in argv[2:]]
    if not rewires:
        raise SystemExit("no rewires given (expected a:b pairs)")
    build_override_rom(vanilla, out, rewires, flags)
    print("override ROM built:", out)


if __name__ == "__main__":
    main()
