"""v2 ruination binding (rewrite Stage E).

The ROM-free planner (doors/plan/ruination) decides the map and an abstract
reward plan: reward name -> kind (character/esper/item) and, for characters,
the character name. This module *realizes* that plan against the ROM objects
the rest of Events needs -- binding the live Reward slots, claiming
characters and picking esper/item ids from their pools, and recording the
character dependency paths -- then presents a `ruination_map`-shaped surface
(`V2RuinMap`) so events.ruination_mod and its downstream consumers
(area clues, dried meat, ferry, spoiler) read it unchanged.

Determinism: the planner is driven by a private RNG seeded once off the
shared global stream, so the same input seed yields the same plan; the
binding then draws esper/item ids from the same global stream in a fixed
(reward_log) order. No snapshot/rollback of external pools is needed -- a
failed attempt never touches the ROM pools (binding only runs after a plan
succeeds), which is why the legacy retry machinery has no v2 counterpart.
"""

import random

from event.event_reward import RewardType
from doors.plan.ruination.growth import RuinConfig, RuinPlanner, RuinPlanError
from doors.plan.ruination.finalize import finalize_plan
from data import ruin_constants as RC

CHARACTER, ESPER, ITEM = RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM

MAX_ATTEMPTS = 10


def build_name_to_slot(events):
    """reward_name -> live Reward slot object.

    Same name -> slot resolution the legacy events.ruination_mod does: a
    plain name binds the event's first reward; a numeric suffix ("Auction
    House_2") binds the (1-based) reward at that index."""
    name_to_slot = {}
    for room, rewards in RC.ROOM_REWARD.items():
        for name in rewards:
            if '_' in name and name.rsplit('_', 1)[1].isdigit():
                base_name = name.rsplit('_', 1)[0]
            else:
                base_name = name
            event = [e for e in events if e.name() == base_name]
            if not event:
                continue
            if '_' not in name:
                name_to_slot[name] = event[0].rewards[0]
            else:
                reward_index = int(name[name.find('_') + 1:])
                name_to_slot[name] = event[0].rewards[reward_index - 1]
    return name_to_slot


def build_v2_ruin_map(args, party_names, characters, espers, items, events,
                      verbose=False):
    """Plan ruination with the v2 planner (retrying on failure) and bind its
    rewards. Returns a V2RuinMap, or raises the last RuinPlanError."""
    name_to_slot = build_name_to_slot(events)
    blitz = [characters.DEFAULT_NAME[c]
             for c in characters.get_characters_with_command("Blitz")]
    base = random.random()          # one deterministic draw off the seeded stream
    last_error = None
    for attempt in range(MAX_ATTEMPTS):
        rng = random.Random(f'{base}:{attempt}')
        config = RuinConfig(
            party_names,
            char_range=tuple(args.ruin_characters_required),
            esper_range=tuple(args.ruin_espers_required),
            open_world=bool(getattr(args, 'open_world', False)),
            maze=getattr(args, 'ruin_dream_maze', None),
            kefka_tower=bool(getattr(args, 'ruin_kefka_tower', False)),
            blitz_characters=blitz,
            espers_available=espers.available(),
        )
        try:
            planner = RuinPlanner(config, rng)
            planner.grow()
            full_map = finalize_plan(planner)
        except RuinPlanError as e:
            last_error = e
            if getattr(args, 'debug', False):
                print(f'v2 ruination attempt {attempt + 1}/{MAX_ATTEMPTS} '
                      f'failed; retrying. ({str(e)[:80]})')
            continue
        ruin_map = V2RuinMap(planner, full_map, party_names, verbose=verbose)
        ruin_map.bind(name_to_slot, characters, espers, items)
        if attempt > 0 and getattr(args, 'debug', False):
            print(f'v2 ruination map generated on attempt {attempt + 1}')
        return ruin_map
    raise last_error


class V2RuinMap:
    """`ruination_map`-shaped adapter over a solved v2 RuinPlanner."""

    def __init__(self, planner, full_map, party_names, verbose=False):
        self.planner = planner
        self.full_map = full_map
        self.PARTY = list(party_names)
        self.planned_characters = list(planner.planned_characters)
        self.accessible_shops = list(planner.accessible_shops)
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Realization: abstract plan -> ROM Reward slots / pools / paths

    def bind(self, name_to_slot, characters, espers, items):
        planner = self.planner
        for entry in planner.reward_log:
            name, kind = entry['name'], entry['kind']
            slot = name_to_slot.get(name)
            if slot is None:
                continue
            if kind is CHARACTER:
                char_id = characters.DEFAULT_NAME.index(entry['character'])
                slot.id = char_id
                slot.type = CHARACTER
                if char_id in characters.available_characters:
                    characters.set_unavailable(char_id)
                # Record the dependency path exactly as legacy process_rewards
                # does (per-event gate); the planner already ordered rewards so
                # the gate is recruited first.
                characters.set_character_path(char_id, slot.event.character_gate())
            elif kind is ESPER:
                slot.id = espers.get_random_esper()
                slot.type = ESPER
            else:
                slot.id = items.get_good_random()
                slot.type = ITEM
            entry['slot_id'] = slot.id     # for the spoiler log
        # Ebot's Rock reaching finalize as a dead end restricts its (unclaimed)
        # reward to esper/item so the events.ruination_mod safety pass can't
        # backfill a character into a leaking Thamasa.
        for name, flags in planner.dead_check_restrictions.items():
            slot = name_to_slot.get(name)
            if slot is not None and slot.id is None:
                slot.possible_types &= flags

    # ------------------------------------------------------------------
    # Downstream-consumer surface (matches legacy ruination_map)

    def compute_actual_areas_used(self):
        """area_name -> branch_id for areas with a reachable room (a room is
        reachable iff its class is the branch's hub class after finalize).
        For split areas, the branch holding the most reachable rooms wins."""
        planner = self.planner
        w = planner.world
        hub_of = [b.hub_class() for b in planner.branches]
        result = {}
        for area_name, room_ids in planner.config.room_sets.items():
            counts = [0, 0, 0]
            for r in room_ids:
                if r not in w._index:
                    continue
                c = w.class_of_room(r)
                for i, hub in enumerate(hub_of):
                    if c == hub:
                        counts[i] += 1
                        break
            max_count = max(counts)
            if max_count > 0:
                result[area_name] = counts.index(max_count)
        return result

    def get_non_veldt_gated_shops(self, characters):
        """Shops NOT gated behind the Veldt character (dried meat must be
        buyable before Gau is recruited). Port of legacy, reading the bound
        character paths and the plan's assignments."""
        planner = self.planner
        all_game = set(self.PARTY) | set(self.planned_characters)
        if 'GAU' not in all_game:
            return self.accessible_shops[:]

        veldt = planner.assignments.get('Veldt')
        if not veldt or veldt[0] != 'CHARACTER':
            return self.accessible_shops[:]
        veldt_char_id = characters.DEFAULT_NAME.index(veldt[1])

        veldt_gated_chars = {
            cid for cid in range(len(characters.DEFAULT_NAME))
            if veldt_char_id in characters.character_paths[cid]
        }
        veldt_gated_areas = set()
        for cid in veldt_gated_chars:
            veldt_gated_areas.update(
                planner.config.character_areas.get(characters.DEFAULT_NAME[cid], []))
        veldt_gated_shops = set()
        for area in veldt_gated_areas:
            veldt_gated_shops.update(RC.AREA_SHOPS.get(area, []))

        non_veldt = [s for s in self.accessible_shops
                     if s not in veldt_gated_shops]
        if not non_veldt and 'GAU' in all_game:
            print('WARNING: No non-Veldt-gated shops available for dried meat!')
            return self.accessible_shops[:]
        return non_veldt

    def generate_spoiler_log(self, characters, espers, items):
        """A functional ruination spoiler from the plan's reward log and
        branch structure (v2 replacement for the legacy path-reconstructing
        version)."""
        planner = self.planner
        w = planner.world

        def reward_desc(entry):
            kind = entry['kind']
            if kind is CHARACTER:
                return f"CHARACTER: {entry['character']}"
            slot_id = entry.get('slot_id')
            if kind is ESPER:
                return f"ESPER: {espers.get_name(slot_id) if slot_id is not None else '?'}"
            return f"ITEM: {items.get_name(slot_id) if slot_id is not None else '?'}"

        lines = []
        lines.append(f"Starting party: {', '.join(self.PARTY)}")
        lines.append(f"Planned characters: {', '.join(self.planned_characters)}")
        lines.append(f"Requested: {planner.Requested[0]} characters, "
                     f"{planner.Requested[1]} espers")
        lines.append("")
        lines.append("Rewards obtained (in order):")
        for entry in planner.reward_log:
            lines.append(f"  {entry['order']:2d}. [branch {entry['branch']}] "
                         f"{entry['name']} -> {reward_desc(entry)}")

        lines.append("")
        lines.append("Areas used (area -> branch):")
        for area, branch_id in sorted(self.compute_actual_areas_used().items()):
            lines.append(f"  {area}: branch {branch_id}")

        lines.append("")
        lines.append("Branch termini:")
        for i, branch in enumerate(planner.branches):
            merged = w.class_of_room(branch.terminus) == branch.hub_class()
            lines.append(f"  branch {i}: {branch.terminus} "
                         f"({'merged into hub' if merged else 'SEPARATE'})")
        return lines

    def generate_map_image(self, *args, **kwargs):
        """Graphical map export is not ported to v2; skip cleanly."""
        return None
