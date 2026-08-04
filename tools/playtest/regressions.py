"""Phase 3 regression scenarios: behavioral tests for recent fixes.

Each scenario builds the seed(s) it needs from a vanilla ROM, boots them
headless, and asserts on live game state -- turning "I verified the bytes"
into "I verified the behavior."

Usage:
    python3 tools/playtest/regressions.py <vanilla.smc> [--keep] [shot_dir]

Exit code is nonzero if any scenario fails. The minecart-camera scenario is
scaffolded and skipped until a plan-driven route to the Esper-Mountain
minecart pitfall exists.
"""

import os
import sys
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
from tools.playtest import navigate, route, reform
import data.event_bit as event_bit
import data.direction as direction

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The default -ruin flagset provides objectives A and B, so the explicit
# start bonuses passed by the scenarios below (-oc/-od) land in slots 2/3.
OBJ_MAXHP = event_bit.OBJECTIVE2
OBJ_HEAL = event_bit.OBJECTIVE3


def build(vanilla, out, flags, seed=1002):
    """Build a seed with wc.py; return the .smc path."""
    cmd = [sys.executable, os.path.join(ROOT, "wc.py"),
           "-i", vanilla, "-o", out, "-sl", "-s", str(seed)] + flags.split()
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
    """The +100 Max HP start objective (-oc 74.100.100) raises max HP by
    exactly 100.

    Before/after within one build: the start party (and its max HP) is set
    early in the start script, well before CheckObjectives fires the
    objective. Reading slot-0 max HP just before the objective bit sets vs
    just after isolates the boost with the same character -- no RNG
    divergence from a flag change."""
    rom = build(vanilla, os.path.join(workdir, "mhp.smc"),
                "-ruin -oc 74.100.100.0.0")
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
    """The Full Heal start objective (-od 55) leaves the party at full HP.

    Full Heal applies only to current-party members (ApplyToParty), and the
    harness's HP accessors index character data blocks -- so read the party
    membership bits and check exactly those characters."""
    rom = build(vanilla, os.path.join(workdir, "heal.smc"),
                "-ruin -oc 74.100.100.0.0 -od 55.0.0")
    h = at_objective_start(rom)
    h.run_until(lambda h: h.event_bit(OBJ_HEAL), timeout=10000, step=10)
    h.run(120)
    current_party = h.core.read_u8(0x1a6d)
    members = [c for c in range(14)
               if h.core.read_u8(0x1850 + c) & current_party]
    assert members, "no characters in the current party"
    for c in members:
        cur, mx = h.cur_hp(c), h.max_hp(c)
        assert cur == mx, f"character {c} not full: {cur}/{mx}"
    return f"party characters {members} at full HP after start"


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


def scenario_rc_school_reform(vanilla, workdir):
    """-rc required characters at the ruination hub: party formation must
    complete with a locked, pre-placed required character.

    '-ruin -rc terra' starts terra plus two rolled characters. Two-party
    reform: terra is pre-placed into party 1 and locked (unmovable), so the
    roster shows only the two rolled characters; place them and finalize.
    Then a fresh boot with all four characters required
    ('-rc terra locke celes sabin') forms THREE parties with no player
    placement at all -- the round-robin pre-placement fills every group
    (this path was guarded/impossible before the ruination -rc wiring)."""
    from reform import GHOST_TALK_XY, choose, place, finalize

    def to_school(rom):
        h = Harness(rom)
        h.boot_to_game_start()
        navigate.wait_for_control(h)
        route.step_door(h, route.ESPER_GATE_TILE)
        navigate.wait_for_control(h)
        assert h.map_id == reform.SCHOOL_MAP, f"not in school: {h.map_id:#x}"
        h.set_party_xy(*GHOST_TALK_XY); h.run(6)
        h.hold('RIGHT', frames=2)
        h.press('A', hold=6, wait=90)
        return h

    def party_of(h, c):
        return h.core.read_u8(0x1850 + c) & 0x07

    # Two parties, one required character.
    rom = build(vanilla, os.path.join(workdir, "rc2p.smc"), "-ruin -rc terra")
    h = to_school(rom)
    choose(h, 0); h.run(40)      # "Reform parties."
    choose(h, 1); h.run(120)     # "2 parties"
    assert party_of(h, 0) == 1, "terra not pre-placed into party 1"
    # terra is locked out of the roster: LOCKE and GOGO are columns 0 and 1
    place(h, 0, 1, 1)            # LOCKE -> party 1 (slot 0 is terra)
    place(h, 1, 2, 0)            # GOGO  -> party 2
    ok = finalize(h)
    h.run(90)
    assert ok, "2-party reform with -rc did not finalize"
    assert party_of(h, 0) == 1, "terra left party 1"
    assigned = {c: party_of(h, c) for c in range(14) if party_of(h, c)}
    assert sorted(set(assigned.values())) == [1, 2], f"two parties not formed: {assigned}"
    two = f"2p: terra locked P1, assignments {assigned}"

    # Three parties, every character required: pre-placement alone fills all
    # three groups (round-robin), finalize with zero player moves.
    rom = build(vanilla, os.path.join(workdir, "rc3p.smc"),
                "-ruin -rc terra locke celes sabin")
    h = to_school(rom)
    choose(h, 0); h.run(40)
    choose(h, 2); h.run(120)     # "3 parties"
    ok = finalize(h)
    h.run(90)
    assert ok, "3-party reform with all-required -rc did not finalize"
    groups = [party_of(h, c) for c in (0, 1, 6, 5)]
    assert sorted(set(groups)) == [1, 2, 3], f"three parties not formed: {groups}"
    return f"{two}; 3p all-required groups {groups}"


def scenario_lite_save_markers(vanilla, workdir):
    """-nosaves lite: every battle must be won, not merely survived.

    The SRAM validity markers ($30:7FF8/FFA/FFC/FFE, magic $E41B) are zeroed
    the moment a battle starts and rewritten only on victory, so resetting
    mid-battle (or after fleeing, until the next save) leaves no loadable
    file. Routes into a cave on a '-ruin -nosaves lite' seed, seeds the
    markers as if the player had saved, then checks: battle start corrupts
    them; winning restores them; fleeing a second battle leaves them
    corrupted."""
    import ctypes as C
    from core import RETRO_MEMORY_SAVE_RAM

    rom = build(vanilla, os.path.join(workdir, "lite.smc"), "-ruin -nosaves lite")
    spoiler = rom[:-4] + ".txt"
    hops = route.route_from_start(spoiler, "cave")
    assert hops, "no routable cave in this seed"

    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)
    for door in hops:
        got = route.step_door(h, door)
        h.run(20)
        assert got is not None, f"stuck at door {door}"
    navigate.wait_for_control(h)

    sram = (C.c_ubyte * h.core.lib.retro_get_memory_size(RETRO_MEMORY_SAVE_RAM)).from_address(
        h.core.lib.retro_get_memory_data(RETRO_MEMORY_SAVE_RAM))
    def markers():
        return [sram[0x1ff8 + i] | (sram[0x1ff9 + i] << 8) for i in (0, 2, 4, 6)]
    def seed_markers():
        for i in (0, 2, 4, 6):
            sram[0x1ff8 + i] = 0x1b
            sram[0x1ff9 + i] = 0xe4

    import random as _random
    rng = _random.Random(9)
    def find_battle():
        for _ in range(800):
            h.hold(rng.choice(['UP', 'DOWN', 'LEFT', 'RIGHT']), frames=14)
            if markers()[0] != 0xe41b:
                return True
        return False

    def win_battle():
        # mash attack; keep the party topped up and pin every monster at 1 HP
        # so any hit kills (battle actor HP words at $3BF4: chars 0-3, monsters 4-9)
        for _ in range(6000):
            h.press('A', hold=4, wait=8)
            for s in range(4):
                mx = h.core.read_u16(0x3c1c + 2*s)
                if mx:
                    h.core.write_u8(0x3bf4 + 2*s, mx & 0xff)
                    h.core.write_u8(0x3bf5 + 2*s, (mx >> 8) & 0xff)
            for s in range(4, 10):
                if h.core.read_u16(0x3c1c + 2*s) and h.core.read_u16(0x3bf4 + 2*s) > 1:
                    h.core.write_u8(0x3bf4 + 2*s, 1)
                    h.core.write_u8(0x3bf5 + 2*s, 0)
            if markers()[0] == 0xe41b:
                return True
        return False

    # 1. battle start corrupts; victory restores (retry once in case a battle
    #    resolves strangely, e.g. the mash flees a pincer)
    won = False
    for _ in range(2):
        seed_markers()
        assert find_battle(), "no encounter found"
        assert markers() == [0, 0, 0, 0], f"start corruption partial: {markers()}"
        if win_battle():
            won = True
            break
    assert won, f"victory did not restore markers: {markers()}"

    # 2. fleeing leaves the markers corrupted
    assert find_battle(), "no second encounter found"
    fled = False
    for _ in range(200):
        h.hold('L', 'R', frames=30)
        before = h.party_xy
        h.hold('DOWN', frames=10)
        if h.party_xy != before:
            fled = True
            break
    assert fled, "could not flee"
    assert markers() == [0, 0, 0, 0], f"flee must not restore markers: {markers()}"
    return "battle start corrupts, victory restores, flee leaves corrupted"


# Route-dependent scenarios: need Phase 4 plan-driven navigation to reach
# the specific dungeon locations. Scaffolded so they run once that lands.
def scenario_minecart_camera(vanilla, workdir):
    """REQUIRES PHASE 4: reach the minecart landing (pit 3028) via an
    Esper Mtn pitfall with DEFEATED_CRANES set, take it a second time, and
    assert the camera is not held on arrival in Vector."""
    raise NotImplementedError("needs plan-driven route to the minecart pitfall")


def scenario_phoenix_entry(vanilla, workdir):
    """Route-chain from game start to Phoenix Cave and confirm the entry
    falling animation completes without a soft-lock (single party).

    The route is computed from the seed's own spoiler: start -> Esper Gate
    event tile 1562 -> Narshe School -> branch door -> ... -> the Phoenix
    door. This exercises the ruination Phoenix entry event (where the
    collision fix lives) end to end for one party."""
    # Seed choice: the ruination map must place Phoenix Cave on a routable
    # branch; not every seed does (1002 doesn't with the current defaults).
    rom = build(vanilla, os.path.join(workdir, "phx.smc"), "-ruin", seed=1005)
    spoiler = rom[:-4] + ".txt"
    hops = route.route_from_start(spoiler, "Phoenix cave")
    assert hops, "could not compute a route to Phoenix Cave from the spoiler"

    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)
    for door in hops:
        got = route.step_door(h, door)
        h.run(20)
        assert got is not None, f"stuck stepping door {door} (route {hops})"

    # Arrived at the Phoenix entry: the falling animation holds the screen.
    assert h.screen_held, "expected the entry falling animation (screen held)"
    # It must resolve (party lands, screen released) -- no soft-lock.
    h.run_until(lambda h: not h.screen_held, timeout=1200, step=30)
    return f"routed to Phoenix (map {h.map_id:#x}), falling animation resolved"


def scenario_phoenix_two_party_collision(vanilla, workdir):
    """Reproduce the exact soft-lock the collision fix addresses: a first party
    declines the Phoenix split and stays in the fall column, then a second
    party enters and must complete its fall *through* the first.

    Flow: reform the ruination hub into two parties at the Narshe School,
    route party 1 to Phoenix and decline the split (it lands at (8,7), in the
    fall column x=8/y0-7), Y-switch to party 2, and route it to the same
    Phoenix entrance. Party 2 falls from (8,0) with a blocking Move down 7 --
    which the fix lets pass through party 1 (DisableEntityCollision around the
    fall). The assertion is that party 2's fall resolves (screen released)
    rather than deadlocking."""
    PHX = 0x13e
    # Same seed constraint as scenario_phoenix_entry.
    rom = build(vanilla, os.path.join(workdir, "phx2.smc"), "-ruin", seed=1005)
    spoiler = rom[:-4] + ".txt"
    hops = route.route_from_start(spoiler, "Phoenix cave")
    assert hops, "could not compute a route to Phoenix Cave from the spoiler"
    school_hops = hops[1:]   # already in the school after the reform

    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)
    route.step_door(h, route.ESPER_GATE_TILE)
    navigate.wait_for_control(h)
    assert h.map_id == reform.SCHOOL_MAP, f"not in school: {h.map_id:#x}"

    # Two parties: {c0,c1} -> party 1 (size 2, so it is offered the split),
    # {c2} -> party 2.
    reform.reform_two_parties(h, plan=(1, 1, 2))

    def route_to_phoenix():
        for door in school_hops:
            got = route.step_door(h, door)
            h.run(20)
            assert got is not None, f"stuck at door {door} (map {h.map_id:#x})"

    # Party 1 falls in, declines the split, and stays in the fall column.
    route_to_phoenix()
    assert h.map_id == PHX, f"party1 not at phoenix: {h.map_id:#x}"
    h.run_until(lambda hh: not hh.screen_held, timeout=1200, step=20)
    h.run(40)
    reform.choose(h, 1)          # "Split the party to proceed?" -> No
    h.run(60)
    px, py = h.party_xy
    assert h.map_id == PHX and px == 8 and 0 <= py <= 7, \
        f"party1 not standing in the fall column: {(px, py)} map {h.map_id:#x}"

    # Y-switch to party 2 (loads its map, the school).
    active = h.core.wram[0x1a6d]
    h.press('Y', hold=4, wait=30)
    h.run(60)
    navigate.wait_for_control(h)
    assert h.core.wram[0x1a6d] != active, "Y-switch did not change active party"
    assert h.map_id == reform.SCHOOL_MAP, f"party2 not in school: {h.map_id:#x}"

    # Party 2 enters the same Phoenix entrance; its fall must pass through
    # party 1 and complete (no deadlock).
    route_to_phoenix()
    assert h.map_id == PHX, f"party2 not at phoenix: {h.map_id:#x}"
    assert h.screen_held, "expected party2 falling animation (screen held)"
    h.run_until(lambda hh: not hh.screen_held, timeout=1500, step=30)
    return (f"party1 declined at ({px},{py}); party2 fell through and landed "
            f"at {h.party_xy} (no soft-lock)")


SCENARIOS = [
    scenario_maxhp_objective,
    scenario_full_heal_objective,
    scenario_camera_after_transition,
    scenario_phoenix_entry,
    scenario_minecart_camera,
    scenario_phoenix_two_party_collision,
    scenario_rc_school_reform,
    scenario_lite_save_markers,
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
