"""Phase 4 route chaining: reach an arbitrary map by walking a seed's
realized door connectivity.

Two graphs meet here:
  - the door-rando graph, parsed from the spoiler log's "Map:" section
    (each realized exit->entrance connection), which describes branch-
    internal connectivity; and
  - the overworld hub (Esper World, map 217 in ruination), whose doors
    are the branch entrances -- discovered empirically in the emulator.

execute_route drives the teleport-and-step navigation primitive along a
hop list. build_graph + reachable_from give the offline BFS used to pick
which branch entrance to take and how to cross a branch.
"""

import os
import re
import sys
from collections import deque, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import doors.atlas as atlas
from data.event_exit_data import event_exit_info
from tools.playtest import navigate

# Facings to try when stepping into a door (down, up, right, left)
_FACINGS = [2, 0, 1, 3]


def door_position(door_id):
    """(map, x, y) of a door/tile by id, from the atlas for normal exits or
    event_exit_info for event tiles acting as doors (1500-1999). Ruination
    routes use both; the atlas alone misses the event tiles."""
    rec = atlas.exit_record(door_id)
    if rec and rec.get('map') is not None:
        return rec['map'], rec['x'], rec['y']
    info = event_exit_info.get(door_id)
    if info and info[5] and info[5][1] is not None:
        map_id, x, y = info[5]
        return map_id, x, y
    return None


def parse_spoiler_map(spoiler_path):
    """Return {exit_id: entrance_id} from a spoiler log's Map: section."""
    lines = open(spoiler_path).read().splitlines()
    try:
        i = lines.index('Map:')
    except ValueError:
        return {}
    edges = {}
    for ln in lines[i + 1:]:
        m = re.match(r'^\s*(\d+)\s*-->\s*(\d+)', ln)
        if not m:
            if ln.strip() and not ln[0].isspace():
                break          # left the section
            continue
        edges[int(m.group(1))] = int(m.group(2))
    return edges


def _door_map(door_id):
    rec = atlas.exit_record(door_id)
    return rec['map'] if rec else None


def build_graph(edges):
    """Map-level adjacency {map: [(next_map, door_id), ...]}.

    Two-way doors (id < 2000) add the reverse edge; traps/pits (>= 2000)
    stay one-way.
    """
    adj = defaultdict(list)
    for a, b in edges.items():
        ma, mb = _door_map(a), _door_map(b)
        if ma is None or mb is None:
            continue
        adj[ma].append((mb, a))
        if a < 2000 and b < 2000:
            adj[mb].append((ma, b))
    return adj


def bfs(adj, start_map, target_map):
    """Shortest hop list [(map, door_id, next_map), ...] or None."""
    seen = {start_map}
    q = deque([(start_map, [])])
    while q:
        mp, path = q.popleft()
        if mp == target_map:
            return path
        for nm, door in adj.get(mp, []):
            if nm not in seen:
                seen.add(nm)
                q.append((nm, path + [(mp, door, nm)]))
    return None


def reachable_from(adj, target_map):
    """Set of maps from which target_map is reachable (reverse closure)."""
    radj = defaultdict(list)
    for mp, nbrs in adj.items():
        for nm, door in nbrs:
            radj[nm].append(mp)
    seen = {target_map}
    q = deque([target_map])
    while q:
        mp = q.popleft()
        for pm in radj.get(mp, []):
            if pm not in seen:
                seen.add(pm)
                q.append(pm)
    return seen


START_MAP = 218          # Esper Gate (ruination game start)
ESPER_GATE_TILE = 1562   # event tile: Esper Gate -> Narshe School
SCHOOL_MAP = 104         # Narshe School (ruination hub)


def parse_spoiler_descriptions(spoiler_path):
    """Return {exit_id: 'exit desc --> entrance desc'} from the Map:
    section, for locating a target door by name."""
    lines = open(spoiler_path).read().splitlines()
    try:
        i = lines.index('Map:')
    except ValueError:
        return {}
    out = {}
    for ln in lines[i + 1:]:
        m = re.match(r'^\s*(\d+)\s*-->\s*\d+\((.*)\)\s*$', ln)
        if not m:
            if ln.strip() and not ln[0].isspace():
                break
            continue
        out[int(m.group(1))] = m.group(2)
    return out


def route_from_start(spoiler_path, target_substring):
    """Full door-id hop list from the ruination game start to the door
    whose spoiler description contains target_substring.

    Chains: start -> ESPER_GATE_TILE -> Narshe School -> (BFS across the
    branch) -> target door. Returns a list of door ids to step through in
    order, or None if the target isn't reachable."""
    edges = parse_spoiler_map(spoiler_path)
    descs = parse_spoiler_descriptions(spoiler_path)
    target_door = next((d for d, desc in descs.items()
                        if target_substring.lower() in desc.lower()), None)
    if target_door is None:
        return None
    pos = door_position(target_door)
    if pos is None:
        return None
    approach_map = pos[0]

    adj = build_graph(edges)
    hops = bfs(adj, SCHOOL_MAP, approach_map)
    if hops is None:
        return None
    return [ESPER_GATE_TILE] + [door for _, door, _ in hops] + [target_door]


def step_door(h, door_id, timeout=160):
    """Teleport to a door/tile by id and step onto it, trying each facing.
    Handles both atlas exits and event tiles acting as doors. Returns the
    new map id, or None if no facing produced a transition."""
    pos = door_position(door_id)
    if pos is None:
        return None
    _, x, y = pos
    start_map = h.map_id
    for facing in _FACINGS:
        snap = h.save_state()
        try:
            nm = navigate.step_through(h, x, y, facing, timeout=timeout)
            if nm != start_map:
                return nm
        except TimeoutError:
            pass
        h.load_state(snap)
    return None


def execute_route(h, hops):
    """Drive a hop list [(map, door_id, next_map), ...]. Returns True if
    every hop transitioned to its expected map."""
    for mp, door, nm in hops:
        if h.map_id != mp:
            return False
        got = step_door(h, door)
        h.run(20)
        if got != nm:
            return False
    return True
