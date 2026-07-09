"""The DoorPlan artifact (rewrite Stage E).

Every planner returns the same object (plan section 3): the door/oneway
matching plus, when ruination is active, a RuinPlan view carrying the
abstract reward plan and party. Data constructs the plan (one contiguous
RNG window) and owns it on Doors.plan; Events receives it and binds the
live Reward objects (event/ruination_bind.py) -- one planning site (F5).

Everything here is ROM-free: RuinPlan wraps the solved (pure) RuinPlanner
for structural queries; nothing references ROM objects.
"""


class DoorPlan:
    def __init__(self, door_pairs, oneways, ruination=None):
        self.door_pairs = [list(m) for m in door_pairs]
        self.oneways = [list(m) for m in oneways]
        self.ruination = ruination          # RuinPlan | None

    def as_map(self):
        """The legacy Doors.map shape: [[door pairs], [oneways]]."""
        return [[list(m) for m in self.door_pairs],
                [list(m) for m in self.oneways]]


class RuinPlan:
    """The ruination view of a DoorPlan: starting party, abstract reward
    plan (names/kinds from the planner's reward_log), and the solved
    planner for structural queries (areas actually used, spoiler data)."""

    def __init__(self, planner, party_names, party_ids):
        self.planner = planner              # solved RuinPlanner (pure)
        self.party = list(party_names)      # starting party, slot order
        self.party_ids = list(party_ids)
        self.planned_characters = list(planner.planned_characters)
        self.requested = list(planner.Requested)
        self.reward_log = planner.reward_log
        self.assignments = planner.assignments
        self.accessible_shops = list(planner.accessible_shops)
        self.dead_check_restrictions = dict(planner.dead_check_restrictions)
