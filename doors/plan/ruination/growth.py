"""Ruination growth orchestrator (rewrite Stage D milestone 3).

Port of ruination_map's setup + generate_map_with_characters onto the shared
WorldModel: pre-planning, area distribution, the pick-branch / extend /
connect / check-rewards loop, reward processing with character keys and
banked (locked) rewards, and the reserve rescue paths. Finalization, the
dream-maze internals and KT lanes are separate modules (later milestones).

Structural changes vs legacy, with equivalence arguments:

- All tables are COPIES held on RuinConfig, with -maze adjustments applied
  at construction. Nothing module-level is mutated, so the legacy
  _reset_ruination_tables machinery has no v2 counterpart (plan flaw F3);
  a retry just builds a fresh planner.

- One shared WorldModel hosts all branches; the keychain is global.
  Legacy applies character keys to every branch explicitly, and every
  non-character key's lock lives in the same area as the key (areas are
  distributed atomically, forced_same_branch covers cross-area pairs), so
  a key found on one branch never has a lock to open on another - the
  global chain is behaviorally identical.

- Forced connections are wired per branch (both elements' rooms must be
  members of the SAME branch), mirroring legacy's branch-local
  ForceConnections; with a shared model an unscoped wiring could merge
  branches.

- The planner deals in reward KINDS and character NAMES: assignments map
  check name -> ('CHARACTER', name) | ('ESPER', None) | ('ITEM', None).
  Esper/item identities don't influence the map, so Events binds them at
  slot-binding time; only the pool COUNTS (which gate kind choice) are
  modeled here.
"""

import copy

from data.rooms import room_data, forced_connections, ruination_dont_force
from data import ruin_constants as RC
from data.ruin_areas import RUIN_ROOM_SETS
from doors.model import WorldModel, DOOR, TRAP, PIT
from doors.plan.pools import load_pool
from doors.plan.modes import split_shared_view
from doors.plan.ruination.branch import RuinBranch, StuckReason
from doors.plan.ruination.extend import extend_branch
from event.event_reward import RewardType

CHARACTER, ESPER, ITEM = RewardType.CHARACTER, RewardType.ESPER, RewardType.ITEM


class RuinPlanError(Exception):
    """Map generation failed in a way the caller should retry or report."""


def possible_flags(type_list):
    """Combine a ROOM_REWARD possible-types list into one Flag value."""
    out = RewardType.NONE
    for t in type_list:
        out |= t
    return out


class RuinConfig:
    """Immutable-per-plan copies of the ruination tables, with mode
    adjustments applied at construction (legacy: _configure_dream_maze and
    -open mutate the module tables in place)."""

    def __init__(self, party, char_range=(3, 3), esper_range=(0, 0),
                 open_world=False, maze=None, blitz_characters=(),
                 espers_available=27):
        self.party = list(party)
        self.char_range = char_range
        self.esper_range = esper_range
        self.open_world = open_world
        self.maze = maze
        self.blitz_characters = list(blitz_characters)
        self.espers_available = espers_available

        self.character_areas = copy.deepcopy(RC.CHARACTER_AREAS)
        self.room_sets = copy.deepcopy(RUIN_ROOM_SETS)
        self.warp_rooms = set(RC.WARP_ROOMS)
        self.town_rooms = set(RC.TOWN_ROOMS)
        self.forced_same_branch = copy.deepcopy(RC.forced_same_branch)
        self.reward_owners = dict(RC.REWARD_OWNERS)
        self.area_shops = {k: list(v) for k, v in RC.AREA_SHOPS.items()}
        self.termini = list(RC.RUIN_TERMINI)
        # name -> combined Flag (the planner's abstract view of a check)
        self.room_reward = {rid: {name: possible_flags(types)
                                  for name, types in rewards.items()}
                            for rid, rewards in RC.ROOM_REWARD.items()}
        if open_world:
            self.character_locked_rewards = {}
            self.rewards_locked_by_character = {}
        else:
            self.character_locked_rewards = copy.deepcopy(RC.CHARACTER_LOCKED_REWARDS)
            self.rewards_locked_by_character = dict(RC.REWARDS_LOCKED_BY_CHARACTER)

        # -maze adjustments (legacy _configure_dream_maze)
        if maze == 'sep':
            if 'DreamMaze' in self.character_areas['CYAN']:
                self.character_areas['CYAN'].remove('DreamMaze')
            if 'DreamMaze' not in self.character_areas['ALL']:
                self.character_areas['ALL'].append('DreamMaze')
        elif maze == 'iso':
            self.room_sets['DreamMaze'] = ['ruin-stooge-maze']
            self.warp_rooms.discard(424)
            self.warp_rooms.add('ruin-stooge-maze')
            if 429 in self.room_reward:
                self.room_reward['ruin-stooge-maze'] = self.room_reward.pop(429)
            self._couple_doma_dream_maze()
        else:
            self._couple_doma_dream_maze()

        self._shared = split_shared_view()
        # Forcing view: ruination drops the ruination_dont_force entries and
        # the final-room->sealed-gate pair (legacy pops both from the global
        # table: Doors.__init__ pops 1079, generate_map pops dont_force).
        skip = set(ruination_dont_force) | {1079}
        self.forcing = {k: list(v) for k, v in forced_connections.items()
                        if k not in skip}

    def _couple_doma_dream_maze(self):
        self.forced_same_branch['Doma'] = (
            self.forced_same_branch.get('Doma', set()) | {'DreamMaze'})
        self.forced_same_branch['DreamMaze'] = (
            self.forced_same_branch.get('DreamMaze', set()) | {'Doma'})

    def spec_for(self, rid):
        """WorldModel spec for one room, shared-exit-stripped."""
        return load_pool([rid], shared=self._shared)[rid]

    def check_flags(self, reward_name):
        for rewards in self.room_reward.values():
            if reward_name in rewards:
                return rewards[reward_name]
        raise KeyError(reward_name)

    def check_room_of(self, reward_name):
        for rid, rewards in self.room_reward.items():
            if reward_name in rewards:
                return rid
        return None


def _area_connectors(config, area_name):
    """has_pido / has_hub analysis of an area's raw rooms (legacy
    _analyze_area_connectors on room_data)."""
    out = {'has_pido': False, 'has_hub': False}
    for rid in config.room_sets.get(area_name, ()):
        rd = room_data.get(rid)
        if not rd:
            continue
        doors, traps, pits = len(rd[0]), len(rd[1]), len(rd[2])
        if pits > 0 and doors > 0:
            out['has_pido'] = True
        if doors + traps >= 3:
            out['has_hub'] = True
    return out


class RuinPlanner:
    def __init__(self, config, rng):
        self.config = config
        self.rng = rng
        self.verbose = False

        self.world = WorldModel({})
        # Protect every forcing id up front (legacy ForceConnections
        # protects all pairs on its first run, present or not).
        for k, v in config.forcing.items():
            self.world.protected.add(k)
            self.world.protected.update(v)

        self.keychain = set(config.party)
        if config.open_world:
            self.keychain.update(RC.ALL_CHARACTERS)
        self.AreasUsed = {}
        self.branch_checks = [[], [], []]
        self.RewardsAvailable = [0, 0]
        self.RewardsObtained = [0, 0]
        self.branch_rewards_found = [0, 0, 0]
        self.LockedRewards = {}
        self.stuck_branches = {}
        self.accessible_shops = []
        self.assignments = {}        # reward name -> (kind, char_name or None)
        self.reward_log = []         # acquisition order, for spoilers/parity
        self.espers_left = config.espers_available

        # Requested counts (legacy rolls these from the arg ranges)
        c_lo, c_hi = config.char_range
        e_lo, e_hi = config.esper_range
        self.Requested = [rng.randint(max(c_lo, 3), max(c_hi, 3)),
                          rng.randint(e_lo, e_hi)]

        (self.planned_characters, self.reserve_characters,
         self.dead_checks_allowed) = self._pre_plan()

        # Duncan's House: 50% inclusion when a Blitz character is in the
        # starting party or planned list (legacy order: party first).
        self.include_duncan_house = False
        self.duncan_house_character = None
        blitz = [c for c in config.party if c in config.blitz_characters]
        blitz += [c for c in self.planned_characters
                  if c in config.blitz_characters]
        if blitz and rng.random() < 0.5:
            self.include_duncan_house = True
            self.duncan_house_character = blitz[0]

        # Branch creation: synthetic one-door hubs + shuffled termini.
        hub_doors = list(room_data['ruin_hub'][0])
        termini = list(config.termini)
        rng.shuffle(termini)
        self.branches = []
        for i, door_id in enumerate(hub_doors):
            hub_id = f'ruin_hub_{i}'
            self.world.add_room(hub_id, {'doors': [door_id]})
            terminus = termini.pop()
            self.world.add_room(terminus, config.spec_for(terminus))
            self.branches.append(RuinBranch(
                self.world, hub_id, [terminus],
                warp_rooms=config.warp_rooms, town_rooms=config.town_rooms,
                check_ids=set(config.room_reward), termini=set(config.termini)))

        # Initial areas from the starting party (+ Duncan's House if its
        # character starts in the party).
        initial_areas = set()
        for ch in config.party:
            initial_areas.update(config.character_areas.get(ch, []))
        if self.include_duncan_house and self.duncan_house_character in config.party:
            initial_areas.add('DuncanHouse')
        self.distribute_areas(initial_areas)

        # Apply the starting keychain everywhere (sorted for determinism).
        for k in sorted(self.keychain):
            self.apply_key(k)

    # ------------------------------------------------------------------
    # Pre-planning

    def _pre_plan(self):
        """Legacy pre_plan_character_acquisition: choose planned characters
        and verify the implied areas have enough esper-capable slots."""
        cfg = self.config
        obtainable = [c for c in RC.ALL_CHARACTERS if c not in cfg.party]
        self.rng.shuffle(obtainable)
        needed = max(0, self.Requested[0] - len(cfg.party))
        planned = obtainable[:needed]
        remaining = obtainable[needed:]

        planned_areas = set()
        for ch in list(cfg.party) + planned:
            planned_areas.update(cfg.character_areas.get(ch, []))
        planned_areas.update(cfg.character_areas.get('ALL', []))

        def slots_in(area_names):
            chars = espers = checks = 0
            for area in area_names:
                for rid in cfg.room_sets.get(area, ()):
                    for flags in cfg.room_reward.get(rid, {}).values():
                        checks += 1
                        if flags & CHARACTER:
                            chars += 1
                        if flags & ESPER:
                            espers += 1
            return chars, espers, checks

        _, esper_slots, checks = slots_in(planned_areas)
        while esper_slots < self.Requested[1] + len(planned) and remaining:
            new_char = remaining.pop(0)
            planned.append(new_char)
            for area in cfg.character_areas.get(new_char, []):
                if area not in planned_areas and area in cfg.room_sets:
                    planned_areas.add(area)
                    _, e2, c2 = slots_in([area])
                    esper_slots += e2
                    checks += c2
        dead = checks - len(planned) - self.Requested[1]
        return planned, remaining, max(0, dead)

    # ------------------------------------------------------------------
    # Membership plumbing

    def _member_rooms(self):
        out = set()
        for b in self.branches:
            out.update(b.rooms)
        return out

    def _branch_of_room(self, rid):
        for i, b in enumerate(self.branches):
            if rid in b:
                return i
        return None

    def _add_room_to_branch(self, branch, rid):
        branch.add_room(rid, self.config.spec_for(rid))
        # Custom handler: returning from Lete River lands in the hub.
        if rid == 'LeteRiver3':
            self.world.add_element(branch.hub_room, PIT, 3039)

    # ------------------------------------------------------------------
    # Keys and reward accessibility

    def _is_reward_accessible(self, reward_name):
        cfg = self.config
        if reward_name in cfg.rewards_locked_by_character:
            if cfg.rewards_locked_by_character[reward_name] not in self.keychain:
                return False
        if reward_name in cfg.reward_owners:
            if not any(c in self.keychain for c in cfg.reward_owners[reward_name]):
                return False
        return True

    def _add_check(self, branch_id, reward_name):
        """Register a newly available check + RewardsAvailable counts."""
        if reward_name in self.branch_checks[branch_id]:
            return False
        self.branch_checks[branch_id].append(reward_name)
        flags = self.config.check_flags(reward_name)
        if flags & CHARACTER:
            self.RewardsAvailable[0] += 1
        if flags & ESPER:
            self.RewardsAvailable[1] += 1
        return True

    def apply_key(self, key):
        """Global key application + check bookkeeping (legacy
        ruination_map.apply_key; branch fan-out is implicit in the shared
        model)."""
        cfg = self.config
        self.keychain.add(key)
        self.world.apply_key(key)

        # In-game character locks released by this key.
        for reward_name in cfg.character_locked_rewards.get(key, []):
            rid = cfg.check_room_of(reward_name)
            if rid is None:
                continue
            branch_id = self._branch_of_room(rid)
            if branch_id is not None and self._is_reward_accessible(reward_name):
                self._add_check(branch_id, reward_name)

        # Area-level locks: rewards owned by this character.
        if key in RC.ALL_CHARACTERS:
            for rid, rewards in cfg.room_reward.items():
                for reward_name in rewards:
                    if (reward_name in cfg.reward_owners
                            and key in cfg.reward_owners[reward_name]
                            and self._is_reward_accessible(reward_name)):
                        branch_id = self._branch_of_room(rid)
                        if branch_id is not None:
                            self._add_check(branch_id, reward_name)

    # ------------------------------------------------------------------
    # Forced connections (branch-scoped)

    def _force_connections(self, branch):
        """Wire every forcing pair whose two elements are live in THIS
        branch (legacy ForceConnections per branch turn; idempotent since
        connected elements leave the live lists)."""
        w = self.world
        members = set(branch.rooms)

        def live_in_branch(e):
            h = w._owner.get(e)
            if h is None or w.room_ids[h] not in members:
                return None
            for kind in (DOOR, TRAP, PIT):
                if e in w.elements[h][kind]:
                    return kind
            return None

        for d, targets in self.config.forcing.items():
            kind = live_in_branch(d)
            if kind is None:
                continue
            df = targets[0]
            fkind = live_in_branch(df)
            if fkind is None:
                continue
            if kind == DOOR:
                w.connect_door(d, df)
            else:
                w.connect_oneway(d, df)

    # ------------------------------------------------------------------
    # Area distribution

    def _forced_same_branch_index(self, area):
        for partner in self.config.forced_same_branch.get(area, ()):
            if partner in self.AreasUsed:
                return self.AreasUsed[partner]
        return None

    def _assign_area(self, area, branch_id):
        self.AreasUsed[area] = branch_id
        for shop_id in self.config.area_shops.get(area, []):
            if shop_id not in self.accessible_shops:
                self.accessible_shops.append(shop_id)

    def distribute_areas(self, areas, method='random'):
        """Legacy distribute_areas: stuck-branch priority, standalone-town
        spreading, then random/shortest dispatch; expands areas to rooms,
        registers checks, and adds rooms to branches."""
        cfg = self.config
        rng = self.rng
        branch_areas = [set(), set(), set()]
        areas = sorted((a for a in areas if a not in self.AreasUsed), key=str)

        # Priority: send stuck branches areas with the connectors they need.
        if self.stuck_branches:
            remaining = list(areas)
            for branch_id, reason in list(self.stuck_branches.items()):
                want = {'has_pido': reason == StuckReason.NEED_PIDO,
                        'has_hub': reason == StuckReason.NO_HUB}
                key = 'has_pido' if want['has_pido'] else (
                    'has_hub' if want['has_hub'] else None)
                if key is None:
                    continue
                for area in remaining:
                    forced_idx = self._forced_same_branch_index(area)
                    if forced_idx is not None and forced_idx != branch_id:
                        continue
                    if _area_connectors(cfg, area)[key]:
                        branch_areas[branch_id].add(area)
                        self._assign_area_pre(area, branch_id)
                        remaining.remove(area)
                        break
            areas = remaining

        # Standalone towns spread to the branch with fewest mapped towns.
        towns = [a for a in areas if a in RC.STANDALONE_TOWNS]
        if towns:
            town_set = set(RC.AREA_TYPES['TOWNS'])
            rng.shuffle(towns)
            placed = []
            for town in towns:
                if self._forced_same_branch_index(town) is not None:
                    continue
                counts = [sum(1 for a, bid in self.AreasUsed.items()
                              if bid == i and a in town_set) for i in range(3)]
                low = min(counts)
                idx = rng.choice([i for i, c in enumerate(counts) if c == low])
                branch_areas[idx].add(town)
                self._assign_area_pre(town, idx)
                placed.append(town)
            areas = [a for a in areas if a not in placed]

        if method == 'random':
            for area in areas:
                idx = self._forced_same_branch_index(area)
                if idx is None:
                    idx = rng.randint(0, 2)
                branch_areas[idx].add(area)
                self._assign_area_pre(area, idx)
        elif method == 'shortest':
            num_rooms = [len(b.rooms) for b in self.branches]
            areas = list(areas)
            rng.shuffle(areas)
            for area in areas:
                idx = self._forced_same_branch_index(area)
                if idx is None:
                    idx = num_rooms.index(min(num_rooms))
                branch_areas[idx].add(area)
                self._assign_area_pre(area, idx)
                num_rooms[idx] += len(cfg.room_sets[area])
        else:                                        # pragma: no cover
            raise ValueError(f'unknown method {method!r}')

        # Expand to rooms; track shops; register accessible checks.
        branch_rooms = [set(), set(), set()]
        for i, ba in enumerate(branch_areas):
            for area in sorted(ba, key=str):
                branch_rooms[i].update(cfg.room_sets[area])
                for shop_id in cfg.area_shops.get(area, []):
                    if shop_id not in self.accessible_shops:
                        self.accessible_shops.append(shop_id)

        for rid, rewards in cfg.room_reward.items():
            which = next((i for i in range(3) if rid in branch_rooms[i]), -1)
            if which >= 0:
                for reward_name in rewards:
                    if self._is_reward_accessible(reward_name):
                        self._add_check(which, reward_name)

        existing = self._member_rooms()
        for i, branch in enumerate(self.branches):
            for rid in sorted(branch_rooms[i], key=str):
                if rid not in existing:
                    self._add_room_to_branch(branch, rid)
                    existing.add(rid)

        # New areas may unstick a branch (legacy post-distribution check).
        for i, branch in enumerate(self.branches):
            if i in self.stuck_branches and branch_rooms[i]:
                reason = self.stuck_branches[i]
                unstick = False
                if reason == StuckReason.NEED_PIDO:
                    unstick = any(
                        len(room_data[r][2]) > 0 and len(room_data[r][0]) > 0
                        for r in branch_rooms[i] if r in room_data)
                elif reason == StuckReason.NO_HUB:
                    unstick = any(
                        len(room_data[r][0]) + len(room_data[r][1]) >= 3
                        for r in branch_rooms[i] if r in room_data)
                else:
                    unstick = branch.has_a_hub()
                if unstick:
                    self.stuck_branches.pop(i, None)

    def _assign_area_pre(self, area, branch_id):
        """AreasUsed entry during dispatch (shop tracking happens in the
        room-expansion pass, as in legacy)."""
        self.AreasUsed[area] = branch_id

    # ------------------------------------------------------------------
    # Reserve rescue

    def get_reserve_area_rooms(self):
        """(area, rooms) for unused reserve-character + EXTRA areas, best
        hub potential (then size) first."""
        cfg = self.config

        def hub_potential(rooms):
            n = 0
            for rid in rooms:
                rd = room_data.get(rid)
                if rd and len(rd[0]) + len(rd[1]) >= 2:
                    n += 1
            return n

        out = []
        seen = set()
        for char in self.reserve_characters:
            for area in cfg.character_areas.get(char, []):
                if area in self.AreasUsed or area not in cfg.room_sets:
                    continue
                if area in seen:
                    continue
                seen.add(area)
                rooms = list(cfg.room_sets[area])
                out.append((area, rooms, hub_potential(rooms), len(rooms)))
        for area in cfg.character_areas.get('EXTRA', []):
            if area in self.AreasUsed or area not in cfg.room_sets or area in seen:
                continue
            seen.add(area)
            rooms = list(cfg.room_sets[area])
            out.append((area, rooms, hub_potential(rooms), len(rooms)))
        out.sort(key=lambda x: (x[2], x[3]), reverse=True)
        return [(a, r) for a, r, _, _ in out]

    def _unstick_with_reserve(self, branch_id):
        """Legacy no-viable-branches path: pull the best reserve (or EXTRA)
        area onto the branch and reset its active room to the hub."""
        branch = self.branches[branch_id]
        reserve_areas = self.get_reserve_area_rooms()
        existing = self._member_rooms()
        if reserve_areas:
            new_area, new_rooms = reserve_areas[0]
            self.AreasUsed[new_area] = branch_id
            for rid in new_rooms:
                if rid not in existing:
                    self._add_room_to_branch(branch, rid)
                    existing.add(rid)
            for rid in new_rooms:
                for reward_name in self.config.room_reward.get(rid, {}):
                    if self._is_reward_accessible(reward_name):
                        self._add_check(branch_id, reward_name)
        else:
            extra = self.config.character_areas.get('EXTRA', [])
            if not extra:
                raise RuinPlanError(
                    f'No reserve areas available to unstick branch {branch_id} '
                    f'(stuck: {self.stuck_branches})')
            new_area = extra.pop()
            self.AreasUsed[new_area] = branch_id
            for rid in self.config.room_sets[new_area]:
                if rid not in existing:
                    self._add_room_to_branch(branch, rid)
                    existing.add(rid)
        self.stuck_branches.pop(branch_id, None)
        branch.active = branch.hub_room

    # ------------------------------------------------------------------
    # Rewards

    def check_for_rewards(self, branch, this_conn):
        """Check rooms newly reached by connecting `this_conn`: the target
        class first, else the first downstream class holding one; claims
        every check room in that class (legacy compound components)."""
        w = self.world
        c = w.owner_class(this_conn)
        found = [r for r in branch.check_rooms if w.class_of_room(r) == c]
        if not found:
            for dc in w.downstream(c):
                found = [r for r in branch.check_rooms
                         if w.class_of_room(r) == dc]
                if found:
                    break
        if not found:
            return None
        rewards = []
        for rid in found:
            branch.claim_check(rid)
            for name, flags in self.config.room_reward[rid].items():
                rewards.append((name, flags))
        return rewards

    def _choose_kind(self, flags, force_character=False):
        """Legacy choose_reward/_choose_reward_with_exclusion: shuffled type
        order, first available wins, item as fallback. Returns (kind,
        character_name or None) and consumes the pools."""
        rng = self.rng
        # Granted characters enter the keychain immediately, so the pool is
        # simply planned-minus-keychain (legacy: available minus excluded).
        chars_left = [c for c in self.planned_characters
                      if c not in self.keychain]
        if force_character:
            return CHARACTER, rng.choice(chars_left)
        all_types = list(RewardType)
        rng.shuffle(all_types)
        item_possible = False
        for t in all_types:
            if t & flags:
                if t == CHARACTER and chars_left:
                    return CHARACTER, rng.choice(chars_left)
                if t == ESPER and self.espers_left > 0:
                    return ESPER, None
                if t == ITEM:
                    item_possible = True
        assert item_possible
        return ITEM, None

    def process_rewards(self, rewards, branch_id):
        """Assign kinds to found checks; characters cascade: key to all
        branches, areas distributed, banked rewards re-processed (legacy
        process_rewards, minus the ROM slot binding)."""
        cfg = self.config
        for reward_name, flags in rewards:
            remaining_chars = len(self.planned_characters) - self.RewardsObtained[0]
            force_char = (remaining_chars >= 1 and self.RewardsAvailable[0] == 1
                          and bool(flags & CHARACTER))
            kind, char_name = self._choose_kind(flags, force_character=force_char)

            if kind is CHARACTER:
                self.RewardsObtained[0] += 1
                # Gate sanity (legacy uses the event's character_gate; the
                # data-level locks must already be satisfied here).
                locker = cfg.rewards_locked_by_character.get(reward_name)
                if locker is not None and locker not in self.keychain:
                    raise RuinPlanError(
                        f'got {char_name} at {reward_name} before its '
                        f'locking character {locker} was recruited')
                self.assignments[reward_name] = ('CHARACTER', char_name)
                self.apply_key(char_name)
                new_areas = list(cfg.character_areas.get(char_name, []))
                for area, cond in RC.CONDITIONAL_AREAS.items():
                    if area in self.AreasUsed or area in new_areas:
                        continue
                    if cond(self, char_name):
                        new_areas.append(area)
                self.distribute_areas(new_areas, method='shortest')
                # Ebot's Rock character reward: the party is diverted to
                # Thamasa - inject the forced one-way exit.
                if reward_name in cfg.room_reward.get('ms-wor-78', {}):
                    if 2085 not in self.world._owner:
                        self.world.add_element('ms-wor-78', TRAP, 2085)
            elif kind is ESPER:
                self.RewardsObtained[1] += 1
                self.espers_left -= 1
                self.assignments[reward_name] = ('ESPER', None)
            else:
                self.assignments[reward_name] = ('ITEM', None)

            if flags & CHARACTER:
                self.RewardsAvailable[0] -= 1
            if flags & ESPER:
                self.RewardsAvailable[1] -= 1

            self.reward_log.append({
                'order': len(self.reward_log) + 1, 'name': reward_name,
                'branch': branch_id, 'kind': kind,
                'character': char_name,
                'reward_room': cfg.check_room_of(reward_name)})
            self.branch_checks[branch_id].remove(reward_name)

            # Recruit-unlock cascade: banked rewards this character frees.
            if kind is CHARACTER:
                if char_name in self.LockedRewards:
                    for entry_branch, entry_rewards in self.LockedRewards.pop(char_name):
                        for r in entry_rewards:
                            self._add_check(entry_branch, r[0])
                        self.process_rewards(entry_rewards, entry_branch)
                # Area-lock scan: entries banked under other characters that
                # this recruit's shared-area ownership now satisfies.
                for other in list(self.LockedRewards):
                    still, unlock = [], []
                    for entry in self.LockedRewards[other]:
                        if all(self._is_reward_accessible(r[0]) for r in entry[1]):
                            unlock.append(entry)
                        else:
                            still.append(entry)
                    if unlock:
                        if still:
                            self.LockedRewards[other] = still
                        else:
                            del self.LockedRewards[other]
                        for entry_branch, entry_rewards in unlock:
                            for r in entry_rewards:
                                self._add_check(entry_branch, r[0])
                            self.process_rewards(entry_rewards, entry_branch)

    # ------------------------------------------------------------------
    # The growth loop

    def grow(self):
        """generate_map_with_characters' main loop: grow branches until the
        planned characters and requested espers are all placed."""
        cfg = self.config
        rng = self.rng
        max_retries = 3

        while (self.RewardsObtained[0] < len(self.planned_characters)
               or self.RewardsObtained[1] < self.Requested[1]):
            viable = [b.has_a_hub() for b in self.branches]
            candidates = [i for i in range(3)
                          if self.branch_checks[i] and viable[i]
                          and i not in self.stuck_branches]
            if candidates:
                total = sum(self.branch_rewards_found)
                weights = [1 + total - self.branch_rewards_found[i]
                           for i in candidates]
                branch_id = rng.choices(candidates, weights=weights, k=1)[0]
            else:
                checkable = [i for i in range(3) if self.branch_checks[i]]
                if not checkable:
                    raise RuinPlanError(
                        f'No branches have remaining checks '
                        f'(stuck: {self.stuck_branches}, viable: {viable})')
                branch_id = checkable[0]
                self._unstick_with_reserve(branch_id)
            branch = self.branches[branch_id]

            self._force_connections(branch)

            found_reward = False
            accessible = []
            retries = 0
            while not found_reward:
                exit_id, target = extend_branch(branch, cfg.forcing, rng)
                if exit_id is None:
                    retries += 1
                    if retries >= max_retries:
                        self.stuck_branches[branch_id] = branch.last_stuck_reason
                        break
                    continue

                # Identify whether the target room was already wired (ticks
                # cooldowns only for freshly mapped rooms).
                w = self.world
                target_room = w.owner_room(target)
                target_class = w.class_of_room(target_room)
                target_was_connected = any(
                    w.find(h1) == target_class or w.find(h2) == target_class
                    for h1, h2 in w.edges)

                self._connect(branch, exit_id, target)

                rewards = self.check_for_rewards(branch, target)
                if rewards is not None:
                    accessible = []
                    for r in rewards:
                        name = r[0]
                        locker = cfg.rewards_locked_by_character.get(name)
                        if locker is not None and locker not in self.keychain:
                            self.LockedRewards.setdefault(locker, []).append(
                                (branch_id, [r]))
                            continue
                        owners = cfg.reward_owners.get(name)
                        if owners is not None and not any(
                                c in self.keychain for c in owners):
                            locker = sorted(owners - self.keychain)[0]
                            self.LockedRewards.setdefault(locker, []).append(
                                (branch_id, [r]))
                            continue
                        accessible.append(r)
                        found_reward = True

                if not target_was_connected:
                    branch.update_cooldowns(target_room)

            if found_reward and accessible:
                self.process_rewards(accessible, branch_id)
                self.branch_rewards_found[branch_id] += len(accessible)

        if self.RewardsObtained[0] < len(self.planned_characters):
            raise RuinPlanError('insufficient characters after main loop')
        if self.RewardsObtained[1] < self.Requested[1]:
            raise RuinPlanError('insufficient espers after main loop')

        # ALL areas (Coliseum etc.): shuffled, spread across shuffled branches.
        all_areas = list(cfg.character_areas.get('ALL', []))
        rng.shuffle(all_areas)
        branch_order = [0, 1, 2]
        rng.shuffle(branch_order)
        existing = self._member_rooms()
        for i, area in enumerate(all_areas):
            if area in self.AreasUsed or area not in cfg.room_sets:
                continue
            target_branch = branch_order[i % 3]
            if rng.random() < 1:                     # ADD_ALL_PERCENT
                branch = self.branches[target_branch]
                for rid in cfg.room_sets[area]:
                    if rid not in existing:
                        self._add_room_to_branch(branch, rid)
                        existing.add(rid)
                self._assign_area(area, target_branch)
        return self

    def _connect(self, branch, exit_id, target):
        """Perform the chosen connection, move the active position, and
        apply the target class's keys (legacy Network.connect tail).

        Kind comes from list membership (live_kind), as in legacy: id
        arithmetic misclassifies door-as-trap exits (door-range ids in a
        trap list, e.g. 182 in room 61)."""
        w = self.world
        kind = w.live_kind(exit_id)
        if kind == DOOR:
            c = w.connect_door(exit_id, target)
        else:
            c = w.connect_oneway(exit_id, target)
        branch.active = w.owner_room(target)
        for k in list(w.class_keys(w.class_of_room(branch.active))):
            self.apply_key(k)
