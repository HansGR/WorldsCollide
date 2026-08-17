"""Data-phase entry point for ruination planning.

plan_ruination() is called from plan_for_args inside Doors.mod: it resolves
the starting party from args.start_chars (same explicit-first-then-random
semantics as Start.init_rewards, WITHOUT mutating the character pool -- the
Start event consumes the planned party later), then runs the pure planner
with an internal retry loop (a failed plan is discarded and re-rolled; no
rollback exists because nothing external was touched).

The party is resolved ONCE and held fixed across retries: the player's
party choice is a fact of the seed, not something to re-roll when a map
attempt fails.

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
        maptest = getattr(args, 'maptest_rooms', None)
        if maptest:
            _apply_maptest(full_map, maptest)
        return DoorPlan(full_map[0], full_map[1],
                        ruination=RuinPlan(planner, party_names, party_ids),
                        gates=gates, shared_exits=config._shared,
                        forcing=config.forcing)
    raise last_error


def _apply_maptest(full_map, maptest_rooms):
    """TESTING ONLY (-maptest): rewire the first branch's hub door straight
    into the listed rooms, chained in order via each room's first two doors.
    The original partner of the hub door is left dangling and no rules or
    verifiers re-run -- the resulting seed is likely uncompletable and
    exists purely to reach a room's events without routing a full seed."""
    from data.rooms import room_data
    hub_door = room_data['HUB50-ruin'][0][0]        # branch 0's hub door
    pairs = full_map[0]

    def doors_of(rid):
        return [d for d in room_data[rid][0] if isinstance(d, int)]

    # point the hub door at the first room's first door
    target = doors_of(maptest_rooms[0])[0]
    pairs[:] = [p for p in pairs if target not in p]
    for p in pairs:
        if p[0] == hub_door:
            p[1] = target
            break
        if p[1] == hub_door:
            p[0] = target
            break
    else:
        pairs.append([hub_door, target])

    # chain any further rooms: room[i] second door <-> room[i+1] first door
    for a, b in zip(maptest_rooms, maptest_rooms[1:]):
        d_out, d_in = doors_of(a)[1], doors_of(b)[0]
        pairs[:] = [p for p in pairs if d_out not in p and d_in not in p]
        pairs.append([d_out, d_in])
