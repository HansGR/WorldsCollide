"""Directed-reachability checks over reconstructed branches.

A branch is meant to be traversed from its hub to its terminus, picking up
rewards along the way (some sit in side pockets you can return from). A
*softlock* is a place you can walk into but not out of: typically a one-way
trap/pit drops you into a pocket from which neither the hub nor the terminus
can be reached again. These checks surface exactly that, plus rewards/termini
that cannot be reached from the hub at all.
"""

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class BranchReport:
    index: int
    rooms: int
    terminus: object
    terminus_reachable: bool
    unreachable_rewards: List = field(default_factory=list)
    softlock_pockets: List[List] = field(default_factory=list)
    one_way_edges: List = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (self.terminus_reachable
                and not self.unreachable_rewards
                and not self.softlock_pockets)


def analyze_branch(branch) -> BranchReport:
    import networkx as nx

    g = branch.graph
    hub = branch.hub
    report = BranchReport(index=branch.index, rooms=g.number_of_nodes(),
                          terminus=branch.terminus, terminus_reachable=False)

    if hub not in g:
        return report

    reachable: Set = set(nx.descendants(g, hub)) | {hub}

    if branch.terminus is not None:
        report.terminus_reachable = branch.terminus in reachable

    for room in sorted(branch.reward_rooms, key=str):
        if room not in reachable:
            report.unreachable_rewards.append(room)

    # one-way edges (for reporting / drawing emphasis)
    report.one_way_edges = [(u, v) for u, v, d in g.edges(data=True)
                            if d.get("kind") == "oneway"]

    # Softlock pockets: rooms you can reach from the hub but from which you can
    # get back to neither the hub nor the terminus.
    terminus = branch.terminus
    dead: Set = set()
    for room in reachable:
        if room == hub or room == terminus:
            continue
        downstream = set(nx.descendants(g, room))
        can_return = hub in downstream
        can_finish = terminus is not None and terminus in downstream
        if not can_return and not can_finish:
            dead.add(room)

    if dead:
        sub = g.subgraph(dead).to_undirected()
        for comp in nx.connected_components(sub):
            report.softlock_pockets.append(sorted(comp, key=str))

    return report


def format_report(reports: List[BranchReport]) -> str:
    lines = ["Ruination branch reachability", "=" * 60]
    for r in reports:
        status = "OK" if r.ok else "CHECK"
        lines.append("")
        lines.append("Branch %d  [%s]  (%d rooms, terminus %s)"
                     % (r.index, status, r.rooms, r.terminus))
        lines.append("  terminus reachable from hub: %s"
                     % ("yes" if r.terminus_reachable else "NO"))
        if r.unreachable_rewards:
            lines.append("  rewards NOT reachable from hub: %s"
                         % ", ".join(str(x) for x in r.unreachable_rewards))
        if r.softlock_pockets:
            lines.append("  POSSIBLE SOFTLOCK pockets (enter but cannot reach "
                         "hub or terminus):")
            for pocket in r.softlock_pockets:
                lines.append("    - " + ", ".join(str(x) for x in pocket))
        if r.ok:
            lines.append("  no softlocks detected")
    return "\n".join(lines)
