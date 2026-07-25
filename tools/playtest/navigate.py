"""Phase 2 navigation: teleport-and-step through doors.

FF6 loads a new map only when the engine runs a real transition (walking
into a door/event tile or an event LoadMap); poking WRAM coordinates
moves the party only within the loaded map. So cross-map travel here is:
teleport the party (via Harness.set_party_xy) onto a walkable tile beside
a door on the current map, then hold the facing direction until the
engine runs its own transition -- which also resyncs the camera, exactly
the path the minecart-camera regression needs.

Door locations come from the atlas (doors.atlas.exit_map / exit_position):
a door's own (map, x, y) is a physical tile, stable across seeds even
though its *destination* is randomized.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import doors.atlas as atlas
import data.direction as direction

# Tile step deltas per facing (matches data.direction values)
_STEP = {
    direction.UP: (0, -1),
    direction.DOWN: (0, 1),
    direction.LEFT: (-1, 0),
    direction.RIGHT: (1, 0),
}
_BUTTON = {
    direction.UP: 'UP',
    direction.DOWN: 'DOWN',
    direction.LEFT: 'LEFT',
    direction.RIGHT: 'RIGHT',
}


def wait_for_control(h, timeout=12000, step=30):
    """Advance until the start cinematic ends and the player has control.

    Heuristic: the party leader is idle (position stable across a short
    window) with the screen not held. Robust to cinematic length.
    """
    h.run(step)
    last = h.party_xy
    stable = 0
    for _ in range(0, timeout, step):
        h.run(step)
        now = h.party_xy
        if now == last and not h.screen_held:
            stable += step
            if stable >= 120:      # ~2s of stillness with camera free
                return
        else:
            stable = 0
        last = now
    raise TimeoutError("player never gained control")


def doors_on_map(map_id, max_id=1281):
    """List (door_id, (x, y)) for vanilla two-way exits on a map."""
    out = []
    for eid in range(max_id):
        if atlas.exit_map(eid) == map_id:
            out.append((eid, atlas.exit_position(eid)))
    return out


def step_through(h, x, y, facing, approach=1, timeout=240):
    """Teleport beside the door tile (x, y) and walk into it.

    Places the party `approach` tiles away on the `facing` side, then
    holds `facing` until the map id changes. Returns the new map id.
    Raises TimeoutError if no transition occurs.
    """
    dx, dy = _STEP[facing]
    h.set_party_xy(x - dx * approach, y - dy * approach)
    h.run(4)
    start_map = h.map_id
    button = _BUTTON[facing]
    for _ in range(0, timeout, 8):
        h.hold(button, frames=8)
        if h.map_id != start_map:
            h.run(30)   # let the landing settle (camera, fade-in)
            return h.map_id
    raise TimeoutError(f"no transition stepping into ({x},{y}) facing {facing}")


def walk(h, button, tiles, frames_per_tile=16):
    """Hold a direction for approximately `tiles` tiles of movement."""
    h.hold(button, frames=frames_per_tile * tiles)
