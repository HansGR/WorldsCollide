"""Print the reward-slot map of a race build: which check (or which
anonymous grant/dialog) each slot belongs to and what it holds.

    python3 tools/race_slot_map.py -i vanilla.smc -s SEED [wc flags...]

Takes exactly the flags wc.py takes (-race is added if missing; -o is
ignored - the rom goes to a temp file).  Builds the seed in-process with
the reward registry instrumented, so what is printed is the same data
that went into the rom's masked table.  Uses:

  - the post-race audit: regenerate any race seed and read its rewards;
  - playtest planning: see which checks hold characters in a seed;
  - debugging a conversion: confirm a check's slot and the anonymous
    registrations (item grants, receive dialogs) around it.

Slot numbering is a build artifact - registration order - so never
assume it is stable across seeds or versions; always read it from the
build in question (see obfuscation/rewards.py).
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHARACTERS = ["TERRA", "LOCKE", "CYAN", "SHADOW", "EDGAR", "SABIN", "CELES",
              "STRAGO", "RELM", "SETZER", "MOG", "GAU", "GOGO", "UMARO"]


def main():
    user_args = sys.argv[1:]
    if "-i" not in user_args or "-s" not in user_args:
        raise SystemExit(__doc__)
    if "-race" not in user_args:
        user_args.append("-race")
    if "-o" in user_args:
        at = user_args.index("-o")
        del user_args[at:at + 2]
    tmp = tempfile.mkdtemp(prefix="race_slot_map_")
    sys.argv = ["wc.py", *user_args, "-o", os.path.join(tmp, "race.smc")]

    from obfuscation import rewards
    from event.event_reward import RewardType

    owners = {}
    original = rewards.register_check

    def instrumented(reward):
        slot = original(reward)
        kinds = [name for flag, name in ((RewardType.CHARACTER, "character"),
                                         (RewardType.ESPER, "esper"),
                                         (RewardType.ITEM, "item"))
                 if reward.possible_types & flag]
        owners[slot] = f"{reward.event.name()} ({'/'.join(kinds)})"
        return slot
    rewards.register_check = instrumented

    import wc
    wc.main()

    from data.item_names import id_name
    from data.espers import Espers
    kind_names = {rewards.KIND_ITEM: "item", rewards.KIND_ESPER: "esper",
                  rewards.KIND_CHARACTER: "character"}

    def value_name(kind, value):
        if kind == rewards.KIND_ITEM:
            return id_name.get(value, str(value))
        if kind == rewards.KIND_ESPER:
            return Espers.esper_names[value] if value < len(Espers.esper_names) else str(value)
        return CHARACTERS[value] if value < len(CHARACTERS) else str(value)

    print(f"{'slot':>4}  {'kind':<9} {'reward':<14} check")
    for slot, (kind, value) in enumerate(rewards._rewards):
        owner = owners.get(slot, "-")
        print(f"{slot:>4}  {kind_names.get(kind, kind):<9} "
              f"{value_name(kind, value):<14} {owner}")
    print(f"\n{len(rewards._rewards)} slots, {len(owners)} checks")


if __name__ == "__main__":
    main()
