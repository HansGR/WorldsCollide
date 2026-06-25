"""Reference data needed to turn spoiler-log door ids into the rooms and
areas that ruination mode actually uses.

Why this module exists
-----------------------
A door id in the spoiler log (e.g. ``150``) is not enough on its own to know
which *room* it belongs to: ``data/rooms.py`` deliberately lists some doors in
several candidate rooms, only one of which is part of the ruination room pool.
``RUIN_ROOM_SETS`` (in ``event/ruination.py``) is the authoritative list of
rooms ruination uses, so we restrict the door->room index to those rooms. This
removes the ambiguity (every door then maps to exactly one ruination room).

``room_data`` imports cleanly with no ROM, but ``event.ruination`` pulls in the
whole event/ROM stack (and triggers argparse at import time), so we *read* the
handful of literal tables we need straight from its source with ``ast`` instead
of importing it.
"""

import ast
import os
import re

from data.rooms import room_data

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUINATION_SRC = os.path.join(_REPO_ROOT, "event", "ruination.py")

# Meta rooms created by ruination on top of RUIN_ROOM_SETS.
META_ROOMS = [
    "ruin_hub",
    "ruin_terminus_1",
    "ruin_terminus_2",
    "ruin_terminus_3",
]

# The three branch hub doors (Narshe School entrances) all live in the single
# static ``ruin_hub`` room; ruination splits them one-per-branch at run time.
HUB_DOOR_BRANCH = {393: 0, 394: 1, 395: 2}


def _read_literal_assignment(source, name):
    """Return ``ast.literal_eval`` of the top-level ``name = <literal>``.

    Returns ``None`` if the value is not a pure literal (e.g. it references
    ``RewardType``), in which case the caller should fall back to a regex.
    """
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return None


def _read_room_reward_checks(source):
    """room_id -> sorted list of check names, parsed from ROOM_REWARD.

    ROOM_REWARD's values reference ``RewardType`` so it cannot be
    ``literal_eval``'d wholesale; we only need the room ids (keys) and the
    human check names (the ``"..."`` dict keys), which we pull with a regex
    over the dict body.
    """
    m = re.search(r"^ROOM_REWARD\s*=\s*\{", source, re.M)
    if not m:
        return {}
    i = m.end() - 1
    depth = 0
    end = None
    for j in range(i, len(source)):
        if source[j] == "{":
            depth += 1
        elif source[j] == "}":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    body = source[i:end]
    result = {}
    # Match `KEY: { "check name" ... }` entries (KEY is int or 'string').
    entry = re.compile(
        r"(?m)^\s*(?P<key>\d+|'[^']+')\s*:\s*\{(?P<val>[^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
    )
    for em in entry.finditer(body):
        key = em.group("key")
        room = int(key) if key.isdigit() else key.strip("'")
        checks = re.findall(r'"([^"]+)"', em.group("val"))
        if checks:
            result[room] = sorted(set(checks))
    return result


class RuinReference:
    """Bundled reference tables, loaded once."""

    def __init__(self):
        with open(_RUINATION_SRC, encoding="utf-8") as f:
            source = f.read()

        self.room_sets = _read_literal_assignment(source, "RUIN_ROOM_SETS") or {}
        self.warp_rooms = set(_read_literal_assignment(source, "WARP_ROOMS") or [])
        self.town_rooms = set(_read_literal_assignment(source, "TOWN_ROOMS") or [])
        self.termini = list(_read_literal_assignment(source, "RUIN_TERMINI") or [])
        self.room_reward_checks = _read_room_reward_checks(source)

        # Universe of rooms ruination actually uses.
        self.ruin_rooms = set(META_ROOMS)
        for rooms in self.room_sets.values():
            self.ruin_rooms.update(rooms)

        # room id -> area name (for colouring), from RUIN_ROOM_SETS.
        self.room_to_area = {}
        for area, rooms in self.room_sets.items():
            for rid in rooms:
                self.room_to_area.setdefault(rid, area)

        # door/trap/pit element -> ruination room (ambiguity removed by
        # restricting to ruin_rooms; verified 0 conflicts on real logs).
        self.element_to_room = {}
        for rid in self.ruin_rooms:
            data = room_data.get(rid)
            if not data:
                continue
            for idx in (0, 1, 2):  # doors, traps, pits
                if len(data) > idx:
                    for element in data[idx]:
                        self.element_to_room.setdefault(element, rid)

    def reward_rooms(self):
        """Set of room ids that hold a reward check."""
        return set(self.room_reward_checks.keys())


_REFERENCE = None


def get_reference():
    """Return the shared :class:`RuinReference` (lazily constructed)."""
    global _REFERENCE
    if _REFERENCE is None:
        _REFERENCE = RuinReference()
    return _REFERENCE


def element_type(element_id):
    """Classify an element id the same way ``data/walks.py`` does.

    Returns one of ``"door"`` (two-way), ``"trap"`` (one-way out),
    ``"pit"`` (one-way in), or ``"key"``.
    """
    if isinstance(element_id, str):
        return "key"
    if element_id < 2000 or (4000 <= element_id < 6000):
        return "door"
    if 2000 <= element_id < 3000:
        return "trap"
    if 3000 <= element_id < 4000 or 6000 <= element_id < 8000:
        return "pit"
    return "door"


def normalize_room(room):
    """Normalise a room label so int ids and their string form unify.

    Spoiler text uses ``'44'`` while ``room_data`` uses ``44``; collapse the
    purely-numeric strings to ints so they are the same graph node.
    """
    if isinstance(room, str) and room.isdigit():
        return int(room)
    return room
