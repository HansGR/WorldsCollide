"""Phase 3 regression scenarios: behavioral tests for recent fixes.

Each scenario builds the seed(s) it needs from a vanilla ROM, boots them
headless, and asserts on live game state -- turning "I verified the bytes"
into "I verified the behavior."

Usage:
    python3 tools/playtest/regressions.py <vanilla.smc> [--keep] [shot_dir]

Exit code is nonzero if any scenario fails. Scenarios that require
route-chaining through a seed's dungeon (minecart camera, phoenix cave
collision) are scaffolded and skipped until Phase 4 navigation lands.
"""

import os
import sys
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
from tools.playtest import navigate
import data.event_bit as event_bit
import data.direction as direction

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# In ruination the -oa objective (Unlock Final Kefka) is filtered before
# .id assignment, so the -od/-oe start bonuses reindex down to slots 2/3.
OBJ_MAXHP = event_bit.OBJECTIVE2
OBJ_HEAL = event_bit.OBJECTIVE3


def build(vanilla, out, flags):
    """Build a seed with wc.py; return the .smc path."""
    cmd = [sys.executable, os.path.join(ROOT, "wc.py"),
           "-i", vanilla, "-o", out, "-sl", "-s", "1002"] + flags.split()
    subprocess.run(cmd, cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def at_objective_start(rom):
    """Boot a seed to the point its start objectives have fired."""
    h = Harness(rom)
    h.boot_to_game_start()
    h.run_until(lambda h: h.event_bit(OBJ_MAXHP), timeout=30000, step=10)
    return h


# --- scenarios ------------------------------------------------------------

def scenario_maxhp_objective(vanilla, workdir):
    """The +100 Max HP start objective (-od 74.100.100) raises max HP by
    exactly 100.

    Before/after within one build: the start party (and its max HP) is set
    early in the start script, well before CheckObjectives fires the
    objective. Reading slot-0 max HP just before the objective bit sets vs
    just after isolates the boost with the same character -- no RNG
    divergence from a flag change."""
    rom = build(vanilla, os.path.join(workdir, "mhp.smc"), "-ruin")
    h = Harness(rom)
    h.boot_to_game_start()

    # The start party's max HP is set (base) hundreds of frames before the
    # objective applies the +100, so detect the boost via the max-HP change
    # itself -- no race with the objective bit, and the same character.
    h.run_until(lambda h: h.max_hp(0) > 0, timeout=10000, step=10)
    base = h.max_hp(0)
    h.run_until(lambda h: h.max_hp(0) != base, timeout=30000, step=10)
    boosted = h.max_hp(0)
    assert h.event_bit(OBJ_MAXHP), "max HP changed but objective bit not set"
    assert boosted - base == 100, \
        f"max HP boost {boosted}-{base}={boosted-base}, expected +100"
    return f"slot0 max HP {base} -> {boosted} (+100)"


def scenario_full_heal_objective(vanilla, workdir):
    """The Full Heal start objective (-oe 55) leaves the party at full HP."""
    rom = build(vanilla, os.path.join(workdir, "heal.smc"), "-ruin")
    h = at_objective_start(rom)
    h.run_until(lambda h: h.event_bit(OBJ_HEAL), timeout=10000, step=10)
    h.run(120)
    for slot in range(3):
        cur, mx = h.cur_hp(slot), h.max_hp(slot)
        if mx == 0:
            continue  # empty slot
        assert cur == mx, f"slot {slot} not full: {cur}/{mx}"
    return "all party members at full HP after start"


def scenario_camera_after_transition(vanilla, workdir):
    """A normal door transition must not leave the camera held.

    This is the invariant behind the reported camera-hold bugs: a HoldScreen
    (0x38) that outlives its transition pins the camera across maps. Here we
    step through a reachable door and assert the scroll-hold flag is clear
    on the far side."""
    rom = build(vanilla, os.path.join(workdir, "cam.smc"), "-ruin")
    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)
    start_map = h.map_id
    doors = navigate.doors_on_map(start_map)
    assert doors, f"no atlas door on map {start_map:#x}"
    door_id, (x, y) = doors[0]
    new_map = navigate.step_through(h, x, y, direction.DOWN)
    assert new_map != start_map, "no transition occurred"
    assert not h.screen_held, "camera left held after a normal transition"
    return f"door {door_id}: {start_map:#x}->{new_map:#x}, camera free"


# Route-dependent scenarios: need Phase 4 plan-driven navigation to reach
# the specific dungeon locations. Scaffolded so they run once that lands.
def scenario_minecart_camera(vanilla, workdir):
    """REQUIRES PHASE 4: reach the minecart landing (pit 3028) via an
    Esper Mtn pitfall with DEFEATED_CRANES set, take it a second time, and
    assert the camera is not held on arrival in Vector."""
    raise NotImplementedError("needs plan-driven route to the minecart pitfall")


def scenario_phoenix_collision(vanilla, workdir):
    """Enter Phoenix Cave with a second party after the first declined to
    split, and assert the falling party completes its animation (no
    collision soft-lock).

    Route-chaining (tools/playtest/route.py) can BFS to Phoenix's approach
    map and chain door hops, but two blockers remain before this runs:
      1. Branch entry is gated by the ruination away-party deployment flow
         at the Narshe School (interactive party formation, not a door
         step), so the world-map branch entrances (overworld doors
         1219-1222) do not trigger from a fresh start.
      2. The bug needs two parties deployed, one left on the Phoenix
         landing tile -- a second deployment on top of (1).
    Both are the Narshe School hub mechanic; automating it is the next
    step. See route_test.py for the validated routing that is in place."""
    raise NotImplementedError(
        "needs the Narshe School branch-deployment flow (see docstring)")


SCENARIOS = [
    scenario_maxhp_objective,
    scenario_full_heal_objective,
    scenario_camera_after_transition,
    scenario_minecart_camera,
    scenario_phoenix_collision,
]


def main():
    vanilla = sys.argv[1]
    keep = "--keep" in sys.argv
    workdir = tempfile.mkdtemp(prefix="wc_regress_")

    passed = failed = skipped = 0
    for scenario in SCENARIOS:
        name = scenario.__name__.replace("scenario_", "")
        try:
            detail = scenario(vanilla, workdir)
            print(f"  PASS  {name}: {detail}")
            passed += 1
        except NotImplementedError as e:
            print(f"  SKIP  {name}: {e}")
            skipped += 1
        except Exception as e:
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    if keep:
        print(f"seeds kept in {workdir}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
