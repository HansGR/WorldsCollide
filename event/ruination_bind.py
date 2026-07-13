"""v2 ruination binding (rewrite Stage E).

Events-side realization of the DoorPlan's ruination view. Planning already
happened in the Data phase (Doors.mod -> doors/plan/ruination/plan.py); the
plan arrives here as doors.plan.ruination -- an abstract reward plan:
reward name -> kind (character/esper/item) and, for characters, the
character name. bind_ruin_plan() *realizes* it against the ROM objects --
binding the live Reward slots, claiming characters and picking esper/item
ids from their pools, and recording the character dependency paths -- then
presents a `ruination_map`-shaped surface (`V2RuinMap`) so
events.ruination_mod and its downstream consumers (area clues, dried meat,
ferry, spoiler) read it unchanged.

No snapshot/rollback of external pools exists here: a failed plan never
reaches binding (the planner's retry loop is pure and Data-phase), so
there is nothing to roll back -- the F5 promise.
"""

from event.event_reward import RewardType
from data import ruin_constants as RC

CHARACTER, ESPER, ITEM = RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM


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


def bind_ruin_plan(plan, characters, espers, items, events, verbose=False):
    """Realize a DoorPlan's ruination view: bind Reward slots and pools.
    Returns the V2RuinMap adapter for the downstream consumers."""
    rp = plan.ruination
    name_to_slot = build_name_to_slot(events)
    ruin_map = V2RuinMap(rp.planner, plan.as_map(), rp.party, verbose=verbose)
    ruin_map.bind(name_to_slot, characters, espers, items)
    return ruin_map


class V2RuinMap:
    """`ruination_map`-shaped adapter over a solved v2 RuinPlanner."""

    def __init__(self, planner, full_map, party_names, verbose=False):
        self.planner = planner
        self.full_map = full_map
        self.PARTY = list(party_names)
        self.planned_characters = list(planner.planned_characters)
        self.accessible_shops = list(planner.accessible_shops)
        self.verbose = verbose
        self._name_to_slot = {}   # stashed by bind() for the spoiler log

    # ------------------------------------------------------------------
    # Realization: abstract plan -> ROM Reward slots / pools / paths

    def bind(self, name_to_slot, characters, espers, items):
        planner = self.planner
        self._name_to_slot = name_to_slot
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
        """Legacy-parity ruination spoiler (-sl): starting party, obtainable
        character rewards with the shortest hub->room route, other obtainable
        rewards, and the shortest hub->terminus route per branch.

        "Obtainable" is the legacy semantics, which can differ from the
        planned reward list in both directions: rewards backfilled after
        planning (rooms attached in finalize, filled by the events.py safety
        pass) are captured from the live slots, and rewards that are
        physically unreachable or character-gated beyond the starting-party
        closure (circular gating) are dropped."""
        from doors.atlas import exit_description as door_name
        from data import ruin_constants as RC

        planner = self.planner
        cfg = planner.config
        w = planner.world

        def room_of(element):
            h = w._owner.get(element)
            return w.room_ids[h] if h is not None else None

        # Room adjacency over the final assembled map (door pairs two-way,
        # trap->pit one-way), with the connecting elements as edge payload.
        adj = {}

        def add_edge(r1, r2, payload):
            if r1 is not None and r2 is not None:
                adj.setdefault(r1, []).append((r2, payload))

        for d1, d2 in self.full_map[0]:
            r1, r2 = room_of(d1), room_of(d2)
            add_edge(r1, r2, ('door', d1, d2))
            add_edge(r2, r1, ('door', d2, d1))
        for t, p in self.full_map[1]:
            add_edge(room_of(t), room_of(p), ('trap', t, p))

        def bfs_path(src, dst):
            """[(room, payload, next_room), ...] along a shortest src->dst
            route, or None. Empty list when src == dst."""
            if src == dst:
                return []
            prev = {src: None}
            queue = [src]
            i = 0
            while i < len(queue):
                r = queue[i]
                i += 1
                for nxt, payload in adj.get(r, ()):
                    if nxt in prev:
                        continue
                    prev[nxt] = (r, payload)
                    if nxt == dst:
                        steps = []
                        node = dst
                        while prev[node] is not None:
                            r0, pl = prev[node]
                            steps.append((r0, pl, node))
                            node = r0
                        return list(reversed(steps))
                    queue.append(nxt)
            return None

        def format_path(hub_room, target):
            if target == hub_room:
                return ["  (in hub)"]
            steps = bfs_path(hub_room, target)
            if steps is None:
                return ["  (no path found)"]
            lines = [f"  Path: {len(steps) + 1} rooms"]
            for r0, (kind, e1, e2), _r1 in steps:
                if kind == 'door':
                    conn = f"{e1} ({door_name(e1)}) <--> {e2} ({door_name(e2)})"
                else:
                    conn = f"TRAP {e1} ({door_name(e1)}) --> PIT {e2} ({door_name(e2)})"
                lines.append(f"    {r0}: {conn}")
            lines.append(f"    {target}: (destination)")
            return lines

        room_branch = {}
        for i, b in enumerate(planner.branches):
            for r in b.rooms:
                room_branch.setdefault(r, i)
        hub_of_branch = [b.hub_room for b in planner.branches]

        # Capture rewards assigned after planning (rooms attached in
        # finalize, filled by the events.py safety pass): any bound slot
        # whose check the planner never claimed.
        entries = [dict(e) for e in planner.reward_log]
        logged = {e['name'] for e in entries}
        for rid, rewards in RC.ROOM_REWARD.items():
            for name in rewards:
                if name in logged:
                    continue
                slot = self._name_to_slot.get(name)
                if slot is None or slot.id is None or slot.type is None:
                    continue
                room = cfg.check_room_of(name)
                if room is None:
                    room = rid
                entries.append({
                    'order': len(entries) + 1, 'name': name,
                    'branch': room_branch.get(room, -1), 'kind': slot.type,
                    'character': (characters.DEFAULT_NAME[slot.id]
                                  if slot.type == CHARACTER else None),
                    'reward_room': room, 'slot_id': slot.id})

        # Physical reachability: a path of doors exists from the branch hub
        # to the reward room. Necessary but not sufficient (gating below).
        reach_cache = {}

        def physically_reachable(entry):
            room, bid = entry.get('reward_room'), entry['branch']
            if room is None or bid < 0:
                return False
            if (bid, room) not in reach_cache:
                hub = hub_of_branch[bid]
                reach_cache[(bid, room)] = (
                    room == hub or bfs_path(hub, room) is not None)
            return reach_cache[(bid, room)]

        # Character-gating fixpoint (same semantics as legacy): seed the
        # keychain with the starting party, repeatedly admit any physically
        # reachable reward whose REWARD_OWNERS / locked-by gates are all
        # satisfied, feeding newly-obtained characters back in. This drops
        # circularly-gated characters from the log.
        def gates_satisfied(entry, keychain):
            locker = cfg.rewards_locked_by_character.get(entry['name'])
            if locker is not None and locker not in keychain:
                return False
            owners = cfg.reward_owners.get(entry['name'])
            if owners is not None and not any(o in keychain for o in owners):
                return False
            return True

        keychain = set(self.PARTY)
        if cfg.open_world:
            keychain.update(RC.ALL_CHARACTERS)
        candidates = [e for e in entries if physically_reachable(e)]
        accessible = set()
        changed = True
        while changed:
            changed = False
            for e in candidates:
                if id(e) in accessible or not gates_satisfied(e, keychain):
                    continue
                accessible.add(id(e))
                changed = True
                if e['kind'] == CHARACTER and e['character'] is not None:
                    keychain.add(e['character'])

        char_rewards = [e for e in entries
                        if e['kind'] == CHARACTER and id(e) in accessible]
        other_rewards = [e for e in entries
                         if e['kind'] != CHARACTER and id(e) in accessible]

        def reward_name(entry):
            if entry['kind'] == CHARACTER:
                return characters.get_name(
                    characters.DEFAULT_NAME.index(entry['character']))
            slot_id = entry.get('slot_id')
            if slot_id is None:
                return '?'
            return (espers.get_name(slot_id) if entry['kind'] == ESPER
                    else items.get_name(slot_id))

        type_label = {CHARACTER: 'Char', ESPER: 'Esper', ITEM: 'Item'}

        # --- Build the log output (legacy section layout) ---
        log_lines = []
        log_lines.append(f"Starting Party: {', '.join(self.PARTY)}")
        log_lines.append(f"Planned characters: {', '.join(self.planned_characters)}")
        log_lines.append(f"Requested: {planner.Requested[0]} characters, "
                         f"{planner.Requested[1]} espers")
        log_lines.append("")

        log_lines.append("Character Rewards:")
        log_lines.append(f"  {'#':<4} {'Character':<14} {'Branch':<8} {'Check':<28}")
        char_number = len(self.PARTY) + 1
        for entry in char_rewards:
            log_lines.append(f"  {char_number:<4} {reward_name(entry):<14} "
                             f"{entry['branch']:<8} {entry['name']:<28}")
            log_lines.extend(format_path(hub_of_branch[entry['branch']],
                                         entry['reward_room']))
            char_number += 1
        log_lines.append("")

        log_lines.append("Other Rewards:")
        log_lines.append(f"  {'#':<4} {'Type':<8} {'Reward':<20} {'Branch':<8} {'Check':<28}")
        for entry in other_rewards:
            log_lines.append(
                f"  {entry['order']:<4} {type_label.get(entry['kind'], '?'):<8} "
                f"{reward_name(entry):<20} {entry['branch']:<8} {entry['name']:<28}")
        log_lines.append("")

        log_lines.append("Areas used (area -> branch):")
        for area, branch_id in sorted(self.compute_actual_areas_used().items()):
            log_lines.append(f"  {area}: branch {branch_id}")
        log_lines.append("")

        log_lines.append("Branch Terminus Routes:")
        for branch_id, branch in enumerate(planner.branches):
            log_lines.append(f"  Branch {branch_id} terminus: {branch.terminus}")
            if branch.terminus is None:
                log_lines.append("    (no terminus)")
                continue
            log_lines.extend(format_path(hub_of_branch[branch_id],
                                         branch.terminus))
        return log_lines

    def generate_map_image(self, *args, **kwargs):
        """Graphical map export is not ported to v2; skip cleanly."""
        return None
