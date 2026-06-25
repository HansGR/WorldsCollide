"""Parse a ruination-mode spoiler log into structured data.

This is pure text processing (standard library only) so it can be used
without networkx/matplotlib. Three groups of information are extracted:

1. Human-facing rewards: starting party, character rewards, other rewards
   and the branch terminus routes (the "Ruination Rewards" section).
2. The realized door map: every ``A --> B`` connection (the "Door Rando"
   ``Map:`` section) plus the forced trap/pit connections.
3. Reconstruction hints from the "Debug Verbose Diagnostics" section: the
   per-branch ``Making connection`` lists and ``Selected ... (room R)``
   door->room mentions. These let us attribute the door map to branches and
   resolve each door to the room ruination finally placed it in.

The verbose section is required to attribute the map to branches. If a log
was produced without ``-debug-verbose`` the parser still returns the reward
data and the global map, and :mod:`ruination_spoiler.reconstruct` falls back
to the (less complete) reward-route attribution.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# --- regexes -----------------------------------------------------------------

_SECTION = re.compile(r"^-{5,}\s*(.*?)\s*-{5,}\s*$")
_HEADER_KV = re.compile(r"^(Version|Generated|Input|Output|Log|Seed|Flags|Hash)\s+(.*)$")

_CONN_TWO = re.compile(r"(\d+)\s+\((.*?)\)\s+<-->\s+(\d+)\s+\((.*?)\)")
_CONN_ONEWAY = re.compile(r"TRAP\s+(\d+)\s+\((.*?)\)\s+-->\s+PIT\s+(\d+)\s+\((.*?)\)")

_PATH_LINE = re.compile(r"^\s+(\S+):\s+(.*)$")
_CHAR_ROW = re.compile(r"^\s+(\d+)\s+(\S+)\s+(\d+)\s+(.*?)\s*$")
_OTHER_ROW = re.compile(r"^\s+(\d+)\s+(\S+)\s+(.+?)\s+(\d+)\s+(.*?)\s*$")
_TERMINUS = re.compile(r"^\s+Branch (\d+) terminus:\s+(\S+)")

_MAP_CONN = re.compile(r"^(\d+)\s+-->\s+(\d+)\(")
_FORCED = re.compile(r"^(\d+)\s+-->\s+\[(\d+)\]")

_WORKING = re.compile(r"^Working on branch (\d+)")
_SELECTED = re.compile(r"^\s*Selected:\s+(\d+)\s+-->\s+(\d+)\s+\(room\s+(.+?)\)\s*$")
_MAKING = re.compile(r"^Making connection:\s+(\d+)\s+-->\s+(\d+)")
_KEYROOM = re.compile(r"Applying key:.*in room (\S+)")
_ADD_ELEM = re.compile(r"adding a (?:trap|door)\.\.\.\s+(\d+)")
_ACTIVE = re.compile(r"^\s*Active room:\s+(\S+)\s+\(level")
_STATUS_ROOMS = re.compile(r"^status:\s+(?:check rooms|dead ends|terminus)\s+(.+)$")
_MAZE_ENTRY = re.compile(r"^Dreamscape maze: entry pit (\d+) -> start room (\S+)")
_MAZE_EDGE = re.compile(
    r"^\s*(door|trap):\s+(\d+)\s+(?:<->|->)\s+(\d+)\s+\(room\s+(\S+)\s+(?:<->|->)\s+(\S+)\)")


# --- data structures ---------------------------------------------------------

@dataclass
class Connection:
    """One door-to-door connection inside a reward/terminus path."""

    door_a: int
    door_b: int
    name_a: str
    name_b: str
    one_way: bool  # True for TRAP->PIT


@dataclass
class PathStep:
    """One line of a reward/terminus path: ``room`` plus the connection that
    leaves it toward the next room (``None`` on the destination line)."""

    room: str
    connection: Optional[Connection]


@dataclass
class Reward:
    number: Optional[int]
    branch: Optional[int]
    check: str
    kind: str = ""            # "Character"/"Esper"/"Item" for "other" rewards
    reward_name: str = ""     # the actual character/esper/item granted
    path: List[PathStep] = field(default_factory=list)


@dataclass
class TerminusRoute:
    branch: int
    terminus: str
    path: List[PathStep] = field(default_factory=list)


@dataclass
class SpoilerLog:
    header: Dict[str, str] = field(default_factory=dict)
    starting_party: List[str] = field(default_factory=list)
    character_rewards: List[Reward] = field(default_factory=list)
    other_rewards: List[Reward] = field(default_factory=list)
    terminus_routes: List[TerminusRoute] = field(default_factory=list)

    # Realized door map.
    map_connections: List[Tuple[int, int]] = field(default_factory=list)
    forced_connections: List[Tuple[int, int]] = field(default_factory=list)

    # Verbose reconstruction hints.
    making_connections: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict)
    door_room: Dict[Tuple[int, int], str] = field(default_factory=dict)  # (branch, door) -> room
    branch_room_mentions: Dict[int, List[str]] = field(default_factory=dict)  # branch -> room labels
    # Branch-agnostic door -> room from the "Dreamscape maze" diagnostics,
    # which name the room for special 6xxx maze pit ids the static index lacks.
    extra_door_room: Dict[int, str] = field(default_factory=dict)
    has_verbose: bool = False

    @property
    def seed(self) -> str:
        return self.header.get("Seed", "")

    @property
    def flags(self) -> str:
        return self.header.get("Flags", "")

    def is_ruination(self) -> bool:
        return "-ruin" in self.flags.split()


def _parse_connection(text: str) -> Optional[Connection]:
    m = _CONN_ONEWAY.search(text)
    if m:
        return Connection(int(m.group(1)), int(m.group(3)),
                          m.group(2), m.group(4), one_way=True)
    m = _CONN_TWO.search(text)
    if m:
        return Connection(int(m.group(1)), int(m.group(3)),
                          m.group(2), m.group(4), one_way=False)
    return None


def _collect_path_blocks(lines: List[str], start: int, end: int):
    """Yield consecutive runs of path lines within ``lines[start:end]``."""
    block: List[PathStep] = []
    for l in lines[start:end]:
        m = _PATH_LINE.match(l)
        if m and ("<-->" in l or "TRAP" in l or "(destination)" in l):
            block.append(PathStep(m.group(1), _parse_connection(m.group(2))))
        else:
            if block:
                yield block
                block = []
    if block:
        yield block


def _branch_of_path(block: List[PathStep]) -> Optional[int]:
    for step in block:
        m = re.match(r"ruin_hub_(\d)", step.room)
        if m:
            return int(m.group(1))
    return None


def parse_spoiler(path_or_text: str) -> SpoilerLog:
    """Parse a spoiler log given a file path or its full text."""
    if "\n" in path_or_text:
        text = path_or_text
    else:
        with open(path_or_text, encoding="utf-8", errors="replace") as f:
            text = f.read()
    lines = text.splitlines()
    log = SpoilerLog()

    # --- header ---
    for l in lines[:12]:
        m = _HEADER_KV.match(l)
        if m:
            log.header[m.group(1)] = m.group(2).strip()

    # --- locate sections ---
    sections: Dict[str, Tuple[int, int]] = {}
    marks: List[Tuple[int, str]] = []
    for i, l in enumerate(lines):
        m = _SECTION.match(l)
        if m and m.group(1):
            marks.append((i, m.group(1)))
    for idx, (i, name) in enumerate(marks):
        nxt = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        sections.setdefault(name, (i, nxt))

    _parse_rewards(lines, sections, log)
    _parse_door_map(lines, sections, log)
    _parse_verbose(lines, sections, log)
    return log


def _parse_rewards(lines, sections, log: SpoilerLog):
    if "Ruination Rewards" not in sections:
        return
    start, end = sections["Ruination Rewards"]
    region = lines[start:end]

    for l in region:
        if l.startswith("Starting Party:"):
            log.starting_party = [p.strip() for p in
                                  l.split(":", 1)[1].split(",") if p.strip()]
            break

    # Character rewards: rows like "  4    TERRA   2   Phoenix Cave" each
    # followed by a "Path:" block. Match a header row then attach the next path.
    blocks = list(_collect_path_blocks(lines, start, end))
    block_iter = iter(blocks)

    mode = None
    pending = None  # the path block following the most recent header row

    def attach_path(reward: Reward):
        nonlocal pending
        if pending is not None:
            reward.path = pending
            pending = None

    # We need path blocks in order; pair them with header rows as we walk.
    block_pos = 0
    for raw in region:
        if raw.strip().startswith("Character Rewards"):
            mode = "char"
            continue
        if raw.strip().startswith("Other Rewards"):
            mode = "other"
            continue
        if raw.strip().startswith("Branch Terminus Routes"):
            mode = "terminus"
            continue

        if mode == "char":
            m = _CHAR_ROW.match(raw)
            if m and m.group(2).isupper():
                reward = Reward(number=int(m.group(1)), branch=int(m.group(3)),
                                check=m.group(4).strip(), kind="Character",
                                reward_name=m.group(2))
                # the path block immediately after this row
                if block_pos < len(blocks) and _branch_of_path(blocks[block_pos]) is not None:
                    reward.path = blocks[block_pos]
                    block_pos += 1
                log.character_rewards.append(reward)
        elif mode == "other":
            m = _OTHER_ROW.match(raw)
            if m and not raw.strip().startswith("#"):
                log.other_rewards.append(Reward(
                    number=int(m.group(1)), kind=m.group(2),
                    reward_name=m.group(3).strip(), branch=int(m.group(4)),
                    check=m.group(5).strip()))
        elif mode == "terminus":
            m = _TERMINUS.match(raw)
            if m:
                route = TerminusRoute(branch=int(m.group(1)), terminus=m.group(2))
                if block_pos < len(blocks) and _branch_of_path(blocks[block_pos]) is not None:
                    route.path = blocks[block_pos]
                    block_pos += 1
                log.terminus_routes.append(route)


def _parse_door_map(lines, sections, log: SpoilerLog):
    # "Door Rando:" section header text varies ("Door Rando:  "); find by prefix.
    name = next((n for n in sections if n.startswith("Door Rando")), None)
    if name is None:
        return
    start, end = sections[name]
    in_map = False
    for l in lines[start:end]:
        if l.strip() == "Map:":
            in_map = True
            continue
        fm = _FORCED.match(l.strip())
        if fm and not in_map:
            log.forced_connections.append((int(fm.group(1)), int(fm.group(2))))
        if in_map:
            mm = _MAP_CONN.match(l.strip())
            if mm:
                log.map_connections.append((int(mm.group(1)), int(mm.group(2))))


def _parse_verbose(lines, sections, log: SpoilerLog):
    name = next((n for n in sections if n.startswith("Debug Verbose")), None)
    if name is None:
        return
    start, end = sections[name]
    log.has_verbose = True
    branch = None
    last_key_room = None

    def mention(room_label):
        if branch is not None and room_label:
            log.branch_room_mentions.setdefault(branch, []).append(room_label)

    for l in lines[start:end]:
        em = _MAZE_ENTRY.match(l)
        if em:
            log.extra_door_room.setdefault(int(em.group(1)), em.group(2))
            continue
        # Dreamscape maze edges name the room for each door/pit directly.
        # (Skip Kefka's Tower, whose rooms start with "KT" and are not part
        # of the three branches.)
        xm = _MAZE_EDGE.match(l)
        if xm and not xm.group(4).startswith("KT"):
            log.extra_door_room.setdefault(int(xm.group(2)), xm.group(4))
            log.extra_door_room.setdefault(int(xm.group(3)), xm.group(5))
            continue
        m = _WORKING.match(l)
        if m:
            branch = int(m.group(1))
            continue
        km = _KEYROOM.search(l)
        if km:
            last_key_room = km.group(1)
        if branch is not None:
            sm = _SELECTED.match(l)
            if sm:
                log.door_room.setdefault((branch, int(sm.group(2))), sm.group(3))
                mention(sm.group(3))
                continue
            mk = _MAKING.match(l)
            if mk:
                log.making_connections.setdefault(branch, []).append(
                    (int(mk.group(1)), int(mk.group(2))))
                continue
            av = _ACTIVE.match(l)
            if av:
                mention(av.group(1))
                continue
            st = _STATUS_ROOMS.match(l.strip())
            if st:
                for tok in re.findall(r"'[^']+'|\d+", st.group(1)):
                    mention(tok.strip("'"))
                continue
        am = _ADD_ELEM.search(l)
        if am and last_key_room and branch is not None:
            # A trap/door added to a room when a character key was applied
            # (e.g. STRAGO unlocking the Burning House); record its room.
            log.door_room.setdefault((branch, int(am.group(1))), last_key_room)
