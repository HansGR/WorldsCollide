"""Phase 4 test: route-chaining infrastructure.

Validates the two halves that work today:
  1. Offline: the spoiler door graph + BFS finds a route to Phoenix Cave's
     map (3 hops deep inside its branch).
  2. Live: the teleport-and-step executor chains real maps in the emulator
     (the ungated Esper-World overworld: 218 -> 217 -> 219).

Reaching Phoenix Cave itself additionally requires crossing the ruination
branch-deployment gate at the Narshe School (the away-party formation
flow), which is interactive rather than a door step -- see the note in
regressions.scenario_phoenix_collision.

Usage: python3 tools/playtest/route_test.py <ruin_seed.smc> <spoiler.txt>
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.harness import Harness
from tools.playtest import navigate, route

PHOENIX_APPROACH_MAP = 377   # holds door 1263 -> Phoenix Cave (this seed)
IN_BRANCH_HUB = 104          # Narshe School, branch-internal hub


def main():
    rom, spoiler = sys.argv[1], sys.argv[2]

    # 1) Offline graph + BFS
    edges = route.parse_spoiler_map(spoiler)
    assert edges, "no door connections parsed from spoiler"
    adj = route.build_graph(edges)
    hops = route.bfs(adj, IN_BRANCH_HUB, PHOENIX_APPROACH_MAP)
    assert hops is not None, "BFS failed to route to Phoenix approach map"
    print(f"offline route {IN_BRANCH_HUB} -> {PHOENIX_APPROACH_MAP}: "
          f"{len(hops)} hops " + " -> ".join(str(nm) for _, _, nm in hops))
    reach = route.reachable_from(adj, PHOENIX_APPROACH_MAP)
    assert IN_BRANCH_HUB in reach

    # 2) Live executor on the ungated overworld
    h = Harness(rom)
    h.boot_to_game_start()
    navigate.wait_for_control(h)
    assert h.map_id == 218, f"expected Esper Gate 218, got {h.map_id}"

    m1 = route.step_door(h, 594)          # Esper Gate -> overworld
    h.run(20)
    assert m1 == 217, f"expected overworld 217, got {m1}"
    m2 = route.step_door(h, 1218)         # overworld -> adjacent overworld
    h.run(20)
    assert m2 == 219, f"expected 219, got {m2}"
    print(f"live executor chained 218 -> {m1} -> {m2} (camera held={h.screen_held})")
    assert not h.screen_held, "camera left held after chained transitions"

    print("PHASE 4 ROUTE TEST OK")


if __name__ == "__main__":
    main()
