"""Data-phase entry point for ruination planning.

plan_ruination() is called from plan_for_args inside Doors.mod: it resolves
the starting party from args.start_chars (same explicit-first-then-random
semantics as Start.init_rewards, WITHOUT mutating the character pool -- the
Start event consumes the planned party later), then runs the pure planner
with an internal retry loop (a failed plan is discarded and re-rolled; no
rollback exists because nothing external was touched -- F5).

The party is resolved ONCE and held fixed across retries, matching
(the party is chosen before ruination_map is ever built).

`characters` is the Data-phase Characters object, used read-only (names,
ids, command lookup); keeping it a duck-typed parameter preserves the
doors/ package's ROM-free importability.
"""

import random as _random

from doors.plan.artifact import DoorPlan, RuinPlan
from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
from doors.plan.ruination.finalize import finalize_plan

MAX_ATTEMPTS = 10


def resolve_party(start_chars, characters, rng):
    """args.start_chars -> concrete character ids, in slot order.

    Mirrors Start.init_rewards: explicit characters claim their slots
    first (so a trailing explicit pick can't be stolen by an earlier
    'random'), then random slots draw uniformly from the remainder
    ('randomngu' excludes Gogo/Umaro). Read-only on `characters`."""
    party = [None] * len(start_chars)
    taken = set()
    for i, sc in enumerate(start_chars):
        if sc not in ('random', 'randomngu'):
            cid = characters.get_by_name(sc).id
            party[i] = cid
            taken.add(cid)
    gogo_umaro = {characters.GOGO, characters.UMARO}
    for i, sc in enumerate(start_chars):
        if sc in ('random', 'randomngu'):
            pool = [c for c in characters.available_characters
                    if c not in taken
                    and (sc == 'random' or c not in gogo_umaro)]
            cid = rng.choice(pool)
            party[i] = cid
            taken.add(cid)
    return party


def plan_ruination(args, rng, characters):
    """Plan the whole ruination map + reward plan. Returns a DoorPlan with
    .ruination set, or raises the last RuinPlanError after MAX_ATTEMPTS."""
    party_ids = resolve_party(args.start_chars, characters, rng)
    party_names = [characters.DEFAULT_NAME[c] for c in party_ids]
    blitz = [characters.DEFAULT_NAME[c]
             for c in characters.get_characters_with_command("Blitz")]

    # One draw off the shared stream keys the whole retry sequence, so the
    # planning window stays contiguous and deterministic per seed.
    base = rng.random()
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        attempt_rng = _random.Random(f'{base}:{attempt}')
        config = RuinConfig(
            party_names,
            char_range=tuple(args.ruin_characters_required),
            esper_range=tuple(args.ruin_espers_required),
            open_world=bool(getattr(args, 'open_world', False)),
            maze=getattr(args, 'ruin_dream_maze', None),
            kefka_tower=bool(getattr(args, 'ruin_kefka_tower', False)),
            blitz_characters=blitz,
            # The esper pool is untouched at planning time (ruination is its
            # first consumer), so the full pool size is the truth here.
        )
        try:
            planner = RuinPlanner(config, attempt_rng)
            planner.grow()
            full_map = finalize_plan(planner)
        except RuinPlanError as e:
            last_error = e
            if getattr(args, 'debug', False):
                print(f'ruination plan attempt {attempt + 1}/{MAX_ATTEMPTS} '
                      f'failed; re-rolling. ({str(e)[:80]})')
            continue
        if attempt > 0 and getattr(args, 'debug', False):
            print(f'ruination plan succeeded on attempt {attempt + 1}')
        # Unified gate table over the rooms actually placed (their spec
        # lock dicts -- the same locks the planner honored while walking).
        from doors.plan.modes import gates_from_specs
        from data.rooms import room_data
        gates = gates_from_specs({
            rid: config.spec_for(rid) for rid in planner.world.room_ids
            if rid in room_data or rid in config.spec_overrides})
        return DoorPlan(full_map[0], full_map[1],
                        ruination=RuinPlan(planner, party_names, party_ids),
                        gates=gates)
    raise last_error
