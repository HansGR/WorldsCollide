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


ENCOUNTERS_OFF = 0x20   # $1EB9 bit 5: random encounters disabled (field engine)


def step_through(h, x, y, facing, approach=1, timeout=240, rise=0):
    """step_through_door with random encounters off for the walk (restored after),
    so a battle on the step tile can't stall the transition"""
    previous = h.core.wram[0x1eb9] & ENCOUNTERS_OFF
    h.core.wram[0x1eb9] |= ENCOUNTERS_OFF
    try:
        return _step_through(h, x, y, facing, approach, timeout, rise)
    finally:
        h.core.wram[0x1eb9] = (h.core.wram[0x1eb9] & ~ENCOUNTERS_OFF & 0xff) | previous


def _step_through(h, x, y, facing, approach=1, timeout=240, rise=0):
    """Teleport beside the door tile (x, y) and walk into it.

    Places the party `approach` tiles away on the `facing` side, then
    holds `facing` until the map id changes -- or, for an exit that lands on
    the same map (Owzer's painting-room stairs, 581), until the party jumps
    away from the door. Returns the map id after the transition.
    Raises TimeoutError if no transition occurs. `rise` shifts the start a
    row up (-1) or down (+1): a door at the foot of diagonal stairs is
    reached by a horizontal step from the stair tile beside it, one row off.
    """
    dx, dy = _STEP[facing]
    start_x, start_y = x - dx * approach, y - dy * approach + rise
    if start_x < 0 or start_y < 0:
        raise TimeoutError(f"no approach to ({x},{y}) facing {facing}: off the map")
    h.set_party_xy(start_x, start_y)
    h.run(4)
    start_map = h.map_id
    button = _BUTTON[facing]
    battles = 0
    elapsed = 0
    while elapsed < timeout:
        h.hold(button, frames=8)
        elapsed += 8
        if elapsed >= timeout and battles < 3:
            # a random encounter takes about a second to start: let it show itself
            for _ in range(10):
                h.run(12)
                if in_battle(h) or h.map_id != start_map:
                    break
        if in_battle(h):
            # a random encounter interrupted the step: win it, then step again
            battles += 1
            clear_battle(h)
            h.set_party_xy(start_x, start_y)
            h.run(4)
            elapsed = 0
            continue
        if h.map_id != start_map or jumped(h, start_x, start_y, approach + 3):
            h.run(30)   # let the landing settle (camera, fade-in)
            return h.map_id
    raise TimeoutError(f"no transition stepping into ({x},{y}) facing {facing}")


def in_battle(h):
    """True during a battle ($3ED8 holds the battle id; $FF on the field)."""
    return h.core.wram[0x3ed8] != 0xff


def clear_battle(h, timeout=6000):
    """Win the battle in progress: every monster is marked KO ($3BF4 HP words,
    $3EE4 bit 7 for actors 4-9) and A is mashed until the field returns."""
    for _ in range(0, timeout, 20):
        if not in_battle(h):
            break
        for slot in range(4, 10):
            if h.core.read_u16(0x3bf4 + 2 * slot) not in (0, 0xffff):
                h.core.write_u16(0x3bf4 + 2 * slot, 0)
                h.core.wram[0x3ee4 + 2 * slot] |= 0x80
        h.press('A', hold=4, wait=16)
    for _ in range(40):                 # the victory banners and fade back to the field
        h.press('A', hold=4, wait=12)
    wait_for_control(h)


def jumped(h, x, y, distance=4):
    """True once the party stands well away from where it started walking at
    (x, y): a same-map exit moved it (walking into a door can't carry it that far)."""
    px, py = h.party_xy
    return abs(px - x) + abs(py - y) > distance


def walk(h, button, tiles, frames_per_tile=16):
    """Hold a direction for approximately `tiles` tiles of movement."""
    h.hold(button, frames=frames_per_tile * tiles)
