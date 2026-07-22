"""The DoorPlan artifact.

Every planner returns the same object: the door/oneway matching plus,
when ruination is active, a RuinPlan view carrying the abstract reward
plan and party. The Data phase constructs the plan (one contiguous RNG
window) and owns it on Doors.plan; the Events phase receives it and
binds the live Reward objects (event/ruination_bind.py) -- one planning
site.

Everything here is ROM-free: RuinPlan wraps the solved (pure) RuinPlanner
for structural queries; nothing references ROM objects.
"""


class DoorPlan:
    def __init__(self, door_pairs, oneways, ruination=None, gates=None,
                 shared_exits=None, forcing=None):
        self.door_pairs = [list(m) for m in door_pairs]
        self.oneways = [list(m) for m in oneways]
        self.ruination = ruination          # RuinPlan | None
        # The mode-adjusted table views this plan was built with (the
        # shared data tables themselves are never mutated): shared_exits
        # has the town split applied for -drdc/-ruin; forcing has the
        # ruination exclusions applied. Realization and the spoiler read
        # these instead of the data/rooms.py tables.
        self.shared_exits = {k: list(v) for k, v in (shared_exits or {}).items()}
        self.forcing = {k: list(v) for k, v in (forcing or {}).items()}
        # The unified gate table: exit id -> key tuple (character names
        # and/or named keys like 'dtboss'), derived
        # from the walked pools' room lock dicts -- the same source the
        # planner honors. Query with plan.gates / plan.gate_of(exit_id);
        # character_gates() filters to character keys.
        self.gates = dict(gates or {})
        self._dest = None                   # lazy exit -> partner index

    def as_map(self):
        """The Doors.map shape: [[door pairs], [oneways]]."""
        return [[list(m) for m in self.door_pairs],
                [list(m) for m in self.oneways]]

    # ------------------------------------------------------------------
    # Consumer query API: event-side code asks the plan
    # rather than walking raw pair lists. NOTE: these answer at PLAN level
    # (as-planned pairs). Realization-level truth (the postprocessed
    # maps.door_map with its +4000 destination ids and shared-exit
    # resolution) lives on Maps (postprocess_door_map).

    def gate_of(self, exit_id):
        """Key tuple locking this exit, or None if it is ungated."""
        return self.gates.get(exit_id)

    def character_gates(self):
        """{exit id: (character names,)} -- the gates whose keys are
        characters (the local-character-gating subset of self.gates)."""
        from data.ruin_constants import ALL_CHARACTERS
        chars = set(ALL_CHARACTERS)
        out = {}
        for exit_id, keys in self.gates.items():
            gating = tuple(k for k in keys if k in chars)
            if gating:
                out[exit_id] = gating
        return out

    def destination_of(self, exit_id):
        """The planned partner of an exit: the other side of its door pair,
        or the pit its trap feeds. None if the plan does not touch it."""
        if self._dest is None:
            self._dest = {}
            for a, b in self.door_pairs:
                self._dest.setdefault(a, b)
                self._dest.setdefault(b, a)
            for t, p in self.oneways:
                self._dest.setdefault(t, p)
        return self._dest.get(exit_id)

    def description_of(self, exit_id):
        """Human name for an exit id (atlas naming chain)."""
        from doors.atlas import exit_description
        return exit_description(exit_id)

    def location_name(self, exit_id):
        """Id of the ROOM that owns the exit (room ids are the room
        names), never assuming the partner is a world-map door (a door
        can legally lead to another interior). None if unowned."""
        from data.rooms import room_data
        for rid, spec in room_data.items():
            if exit_id in spec[0] or exit_id in spec[1] or exit_id in spec[2]:
                return rid
        return None


class RuinPlan:
    """The ruination view of a DoorPlan: the starting party and the
    solved planner. Everything else (reward_log, assignments, areas
    used, spoiler data) is queried through .planner."""

    def __init__(self, planner, party_names, party_ids):
        self.planner = planner              # solved RuinPlanner (pure)
        self.party = list(party_names)      # starting party, slot order
        self.party_ids = list(party_ids)
