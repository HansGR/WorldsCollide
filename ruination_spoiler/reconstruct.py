"""Rebuild the three ruination branch graphs from a parsed spoiler log.

The output mirrors what ``Ruination.generate_map_image`` draws in-process:
one directed graph per branch whose nodes are ruination rooms and whose edges
are door connections (two-way) and trap/pit connections (one-way).

Resolution strategy (see the package docstrings for the full reasoning):

* **door -> room** — a door is mapped to the room ruination finally placed it
  in, preferring the spoiler's own room names (reward/terminus paths, then the
  verbose ``Selected ... (room R)`` mentions) and falling back to the
  ``RUIN_ROOM_SETS``-restricted static index. The three hub doors are split
  one-per-branch. Numeric room labels are normalised so ``'44'`` and ``44``
  unify.
* **connection -> branch** — every connection from the global ``Map:`` is
  attributed to a branch by the branch that *used* its door (the per-branch
  ``Making connection`` lists), which is unambiguous and avoids the shared
  world-map leaking rooms between branches.
* **propagation** — connections whose doors were never explicitly attributed
  (dead-end attachments, forced one-ways) are added to the unique branch that
  already contains one of their rooms.
* **island attachment** — anything still unplaced is attached via the rooms
  the verbose section listed under each branch (e.g. the Lone Wolf reward,
  which is reached by a scripted fall rather than a door).
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .ruin_data import (
    HUB_DOOR_BRANCH,
    element_type,
    get_reference,
    normalize_room,
)
from .parser import SpoilerLog

_ATOMIC_UNDERSCORE = [
    "ruin_hub_0", "ruin_hub_1", "ruin_hub_2",
    "ruin_terminus_1", "ruin_terminus_2", "ruin_terminus_3",
]


def _split_compound(label: str) -> List[str]:
    """Split a ``compress_loop`` compound (``'A_B_C'``) into member room ids,
    treating ``ruin_hub_N`` / ``ruin_terminus_N`` as atomic."""
    tmp = label
    holders = {}
    for i, atom in enumerate(_ATOMIC_UNDERSCORE):
        ph = "\0%d\0" % i
        tmp = tmp.replace(atom, ph)
        holders[ph] = atom
    return [holders.get(p, p) for p in tmp.split("_") if p]


def _is_compound(label) -> bool:
    return isinstance(label, str) and len(_split_compound(label)) > 1


@dataclass
class Branch:
    """A reconstructed branch."""

    index: int
    graph: "object"  # networkx.DiGraph
    hub: str
    terminus: Optional[str] = None
    reward_rooms: Set = field(default_factory=set)
    # room -> set of edge kinds touching it, for convenience
    door_room: Dict[int, object] = field(default_factory=dict)


class _Reconstructor:
    def __init__(self, log: SpoilerLog):
        self.log = log
        self.ref = get_reference()
        self.auth: Dict[Tuple[int, int], object] = {}
        self.door_branch: Dict[int, int] = {}
        self.room_branch: Dict[object, int] = {}
        self._build_indices()

    # --- door/room/branch indices ------------------------------------------

    def _set_auth(self, branch: int, door: int, room: str):
        if room and not _is_compound(room):
            self.auth.setdefault((branch, door), normalize_room(room))

    def _build_indices(self):
        log = self.log

        # Authoritative door->room from the verbose "Selected ... (room R)"
        # mentions and key-room additions (parser already filtered to the
        # right branch; we drop compound labels here).
        for (branch, door), room in log.door_room.items():
            self._set_auth(branch, door, room)

        # door->branch and door->room from the per-branch Making-connection
        # lists.
        for branch, conns in log.making_connections.items():
            for d1, d2 in conns:
                self.door_branch.setdefault(d1, branch)
                self.door_branch.setdefault(d2, branch)

        # Reward / terminus paths: authoritative final room names + branch.
        for reward in log.character_rewards:
            self._index_path(reward.branch, reward.path)
        for route in log.terminus_routes:
            self._index_path(route.branch, route.path)

        # room->branch from explicit verbose room mentions (last resort).
        for branch, mentions in log.branch_room_mentions.items():
            for label in mentions:
                for member in _split_compound(label):
                    self.room_branch.setdefault(normalize_room(member), branch)

    def _index_path(self, branch: Optional[int], path):
        if branch is None:
            return
        for i, step in enumerate(path):
            self.room_branch.setdefault(normalize_room(step.room), branch)
            conn = step.connection
            if conn is None:
                continue
            nxt = path[i + 1].room if i + 1 < len(path) else None
            self._set_auth(branch, conn.door_a, step.room)
            if nxt is not None:
                self._set_auth(branch, conn.door_b, nxt)
            self.door_branch.setdefault(conn.door_a, branch)
            self.door_branch.setdefault(conn.door_b, branch)

    # --- lookups ------------------------------------------------------------

    def room_of(self, door: int):
        if door in HUB_DOOR_BRANCH:
            return "ruin_hub_%d" % HUB_DOOR_BRANCH[door]
        for branch in (0, 1, 2):
            if (branch, door) in self.auth:
                return self.auth[(branch, door)]
        if door in self.log.extra_door_room:
            return normalize_room(self.log.extra_door_room[door])
        room = self.ref.element_to_room.get(door)
        if room is None and 4000 <= door < 6000:
            room = self.ref.element_to_room.get(door - 4000)  # logical WOR door
        return normalize_room(room) if room is not None else None

    def branch_of_connection(self, a: int, b: int) -> Optional[int]:
        if a in HUB_DOOR_BRANCH:
            return HUB_DOOR_BRANCH[a]
        if b in HUB_DOOR_BRANCH:
            return HUB_DOOR_BRANCH[b]
        if a in self.door_branch:
            return self.door_branch[a]
        return self.door_branch.get(b)

    # --- graph construction -------------------------------------------------

    def build(self) -> List[Branch]:
        import networkx as nx

        graphs = {b: nx.DiGraph() for b in (0, 1, 2)}

        def add_edge(branch, a, b):
            ra, rb = self.room_of(a), self.room_of(b)
            # Hub pits (3039/3097/3098/3099 - the logical returns from Kefka's
            # Tower / Lete River) resolve to the un-split 'ruin_hub'; pin them
            # to this branch's hub so they don't form a phantom node.
            ra = "ruin_hub_%d" % branch if ra == "ruin_hub" else ra
            rb = "ruin_hub_%d" % branch if rb == "ruin_hub" else rb
            if ra is None or rb is None or ra == rb:
                return False
            g = graphs[branch]
            if element_type(a) == "door":
                g.add_edge(ra, rb, kind="door")
                g.add_edge(rb, ra, kind="door")
            else:  # trap / pit one-way
                g.add_edge(ra, rb, kind="oneway")
            return True

        # Complete connection pool: the realized Map plus any forced one-ways
        # not already present there.
        pool = list(self.log.map_connections)
        seen = set(pool)
        for a, b in self.log.forced_connections:
            if (a, b) not in seen:
                pool.append((a, b))
                seen.add((a, b))

        deferred = []
        for a, b in pool:
            branch = self.branch_of_connection(a, b)
            if branch is None:
                deferred.append((a, b))
            else:
                add_edge(branch, a, b)

        # Propagate: attach deferred connections to the unique branch already
        # containing one of their rooms.
        changed = True
        while changed and deferred:
            changed = False
            still = []
            for a, b in deferred:
                ra, rb = self.room_of(a), self.room_of(b)
                if ra is None or rb is None:
                    continue
                owners = [bx for bx in (0, 1, 2)
                          if ra in graphs[bx] or rb in graphs[bx]]
                if len(set(owners)) == 1:
                    add_edge(owners[0], a, b)
                    changed = True
                else:
                    still.append((a, b))
            deferred = still

        # Island attachment: connections whose rooms are known to belong to a
        # branch via the verbose mentions (e.g. scripted reward areas).
        for a, b in deferred:
            ra, rb = self.room_of(a), self.room_of(b)
            branch = self.room_branch.get(ra)
            if branch is None:
                branch = self.room_branch.get(rb)
            if branch is not None:
                add_edge(branch, a, b)

        return [self._finalize(b, graphs[b]) for b in (0, 1, 2)]

    def _finalize(self, index: int, graph) -> Branch:
        hub = "ruin_hub_%d" % index
        terminus = None
        for route in self.log.terminus_routes:
            if route.branch == index:
                terminus = normalize_room(route.terminus)
        reward_rooms = {normalize_room(r) for r in self.ref.reward_rooms()
                        if normalize_room(r) in graph}
        # character-reward destination rooms are also reward rooms
        for reward in self.log.character_rewards:
            if reward.branch == index and reward.path:
                dest = normalize_room(reward.path[-1].room)
                if dest in graph:
                    reward_rooms.add(dest)
        return Branch(index=index, graph=graph, hub=hub,
                      terminus=terminus, reward_rooms=reward_rooms)


def build_branches(log: SpoilerLog) -> List[Branch]:
    """Reconstruct the three branches from a parsed :class:`SpoilerLog`."""
    return _Reconstructor(log).build()
