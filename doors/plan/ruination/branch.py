"""RuinBranch: one branch of the ruination world as a view over the shared
WorldModel (rewrite Stage D).

Legacy runs three separate Network instances plus hand-managed reserve
bookkeeping to keep rooms from being placed twice; here all branches share
one WorldModel, so element/room uniqueness is enforced by the model's owner
map and adding a room to any branch removes it from contention everywhere.
The keychain is global on the model - equivalent to legacy, which fans every
applied key out to all three branches.

Check rooms are tracked by their own room ids for the life of the plan:
classes never rename rooms (flaw F2), so the legacy compound-id re-pointing
that RuinationBranch.compress_loop performs (check_rooms surgery plus the
_compound_check_rooms map) has no v2 counterpart. Ask the model which class
a check room is in when you need its current location.

Branch-side bookkeeping (membership, cooldowns, check rooms) is NOT
journaled: the legacy growth loop never backtracks branch state - extension
validates candidates before connecting, and failures regenerate the whole
map - so only the model-level walk (KT lanes etc.) needs rollback.
"""

from data.ruin_constants import ROOM_REWARD, RUIN_TERMINI, WARP_ROOMS, TOWN_ROOMS
from doors.model import DOOR, TRAP, PIT

WARP_COOLDOWN_INITIAL = 5
TOWN_COOLDOWN_INITIAL = 4


class StuckReason:
    """Why a branch cannot make progress; drives smart area distribution."""
    NONE = 'none'                    # Not stuck
    NO_EXITS = 'no_exits'            # No exits available at all
    NO_SAFE_EXITS = 'no_safe_exits'  # All exits filtered (would strand pits)
    NEED_PIDO = 'need_pido'          # Need pit-in, door-out room to receive trap
    NEED_PITS = 'need_pits'          # Have traps but no pits to receive them
    NEED_DOORS = 'need_doors'        # Have doors but no door entrances available
    NO_HUB = 'no_hub'                # No hub rooms available

# Trichotomy labels for level(): where a room sits relative to the hub.
HUB, UPSTREAM, DOWNSTREAM, UNPLACED = 'hub', 'upstream', 'downstream', 'unplaced'


class RuinBranch:
    def __init__(self, world, hub_room, rooms=()):
        """`hub_room` and every id in `rooms` must already be in `world`;
        rooms added later go through self.add_room so membership and
        classification stay in sync."""
        self.world = world
        self.hub_room = hub_room
        self.rooms = []              # insertion order: deterministic RNG feeds
        self.dead_ends = []
        self.check_rooms = []        # ROOM_REWARD rooms with pending checks
        self.terminus = None
        self.last_stuck_reason = StuckReason.NONE
        self.warp_cooldown = WARP_COOLDOWN_INITIAL
        self.town_cooldown = TOWN_COOLDOWN_INITIAL
        self._classify(hub_room)
        for rid in rooms:
            self._classify(rid)

    # ------------------------------------------------------------------
    # Membership

    def add_room(self, room_id, spec):
        """Add a room to the shared model on behalf of this branch."""
        self.world.add_room(room_id, spec)
        self._classify(room_id)

    def _classify(self, room_id):
        """Legacy RuinationBranch.classify_rooms, per room, at add time."""
        self.rooms.append(room_id)
        if room_id in RUIN_TERMINI:
            self.terminus = room_id
        if self._is_dead_end(room_id):
            self.dead_ends.append(room_id)
        if room_id in ROOM_REWARD:
            self.check_rooms.append(room_id)

    def _is_dead_end(self, room_id):
        """Exactly one door, no traps/pits, no locked items (keys allowed) -
        legacy Network.is_dead_end at add time (no edges exist yet)."""
        h = self.world._index[room_id]
        e = self.world.elements[h]
        if (len(e[DOOR]), len(e[TRAP]), len(e[PIT])) != (1, 0, 0):
            return False
        return not any(self.world.locks[h].values())

    def __contains__(self, room_id):
        return room_id in set(self.rooms)

    # ------------------------------------------------------------------
    # Hub topology (all live queries against the model; nothing cached)

    def hub_class(self):
        return self.world.class_of_room(self.hub_room)

    def downstream_classes(self):
        """Classes reached from the hub by falling through traps."""
        return self.world.downstream(self.hub_class())

    def upstream_classes(self):
        """Classes that flow INTO the hub (their traps land hubward)."""
        return self.world.upstream(self.hub_class())

    def level(self, room_id):
        """Trichotomy of a member room relative to the hub: HUB (mutually
        reachable with it), UPSTREAM, DOWNSTREAM, or UNPLACED (not yet
        wired to the hub component)."""
        c = self.world.class_of_room(room_id)
        hub = self.hub_class()
        if c == hub:
            return HUB
        if c in self.world.downstream(hub):
            return DOWNSTREAM
        if c in self.world.upstream(hub):
            return UPSTREAM
        return UNPLACED

    def placed_rooms(self):
        """Member rooms wired to the hub component, insertion order."""
        return [r for r in self.rooms if self.level(r) is not UNPLACED]

    def unplaced_rooms(self):
        return [r for r in self.rooms if self.level(r) is UNPLACED]

    def has_a_hub(self):
        """True if some placed non-dead-end room retains 3+ door/trap exits
        (legacy has_a_hub, on live element counts)."""
        for rid in self.placed_rooms():
            if rid in self.dead_ends:
                continue
            h = self.world._index[rid]
            e = self.world.elements[h]
            if len(e[DOOR]) + len(e[TRAP]) >= 3:
                return True
        return False

    # ------------------------------------------------------------------
    # Reward / cooldown bookkeeping

    def pending_checks(self):
        """Check rooms whose rewards have not been claimed yet."""
        return list(self.check_rooms)

    def claim_check(self, room_id):
        self.check_rooms.remove(room_id)

    def rewards_found(self):
        """How many of this branch's check rooms have been claimed (feeds
        the less-extended-branch weighting)."""
        return sum(1 for r in self.rooms
                   if r in ROOM_REWARD and r not in self.check_rooms)

    def update_cooldowns(self, mapped_room_id):
        """Tick anti-clustering counters after an unplaced room is mapped;
        mapping a warp/town room resets its own counter."""
        if self.warp_cooldown > 0:
            self.warp_cooldown -= 1
        if self.town_cooldown > 0:
            self.town_cooldown -= 1
        if mapped_room_id in WARP_ROOMS:
            self.warp_cooldown = WARP_COOLDOWN_INITIAL
        if mapped_room_id in TOWN_ROOMS:
            self.town_cooldown = TOWN_COOLDOWN_INITIAL
