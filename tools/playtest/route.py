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
from tools.playtest import navigate

# Facings to try when stepping into a door (down, up, right, left)
_FACINGS = [2, 0, 1, 3]


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


def step_door(h, door_id, timeout=160):
    """Teleport to a door by id and step through it, trying each facing.
    Returns the new map id, or None if no facing produced a transition."""
    pos = atlas.exit_position(door_id)
    if pos is None:
        return None
    x, y = pos
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
