"""Render reconstructed branches to a PNG, mirroring the figure that
``Ruination.generate_map_image`` produces during generation.

Each branch is a subplot:

* nodes are rooms, coloured by area (``RUIN_ROOM_SETS``);
* the hub is a gold hexagon, the terminus a pink diamond, reward rooms are
  stars, warp points are triangles and towns are enlarged circles;
* two-way door connections are solid grey lines, one-way trap/pit
  connections are dashed red arrows.

Requires ``networkx`` and ``matplotlib`` (only imported here, so the parser
stays dependency-free).
"""

from typing import List, Optional

from .ruin_data import get_reference, normalize_room
from .parser import SpoilerLog
from .reconstruct import Branch

# Area palette - copied from Ruination.generate_map_image so the two figures
# read the same.
AREA_COLORS = {
    'Narshe': '#4A90D9', 'Doma': '#D94A4A', 'DreamMaze': '#E06666',
    'UmarosCave': '#7B68EE', 'EsperMountain': '#2ECC71', 'PhantomTrain': '#8B4513',
    'SealedGate': '#FF6347', 'SouthFigaroCave': '#DAA520', 'ReturnersHideout': '#3CB371',
    'AncientCastle': '#CD853F', 'Jidoor': '#DDA0DD', 'VeldtCave': '#556B2F',
    'CrescentMtn': '#4682B4', 'BarenFalls': '#00CED1', 'Vector': '#DC143C',
    'DarylsTomb': '#9370DB', 'ZoneEater': '#FF8C00', 'MtKolts': '#6B8E23',
    'Zozo': '#B8860B', 'ZozoTower': '#BDB76B', 'MtZozo': '#808000',
    'BurningHouse': '#FF4500', 'SouthFigaro': '#F4A460', 'GauFatherHouse': '#8FBC8F',
    'Thamasa': '#E9967A', 'Kohlingen': '#87CEEB', 'Cid': '#ADD8E6',
    'Mobliz': '#98FB98', 'Maranda': '#FFB6C1', 'FanaticsTower': '#BA55D3',
    'OperaHouse': '#FF69B4', 'EbotsRock': '#A0522D', 'Coliseum': '#C0C0C0',
    'Tzen': '#FFDEAD', 'Albrook': '#B0E0E6', 'Veldt': '#9ACD32',
    'Nikeah': '#5F9EA0', 'PhoenixCave': '#FF7F50', 'FloatingContinent': '#6495ED',
    'ImperialCamp': '#DB7093', 'FigaroCastle': '#F0E68C', 'ImperialCastle': '#778899',
}
_DEFAULT_COLOR = '#AAAAAA'
_HUB_COLOR = '#FFD700'
_TERMINUS_COLOR = '#FF1493'


def _node_area(ref, node):
    if isinstance(node, str) and 'ruin_hub' in node:
        return 'Hub'
    return ref.room_to_area.get(node, 'Unknown')


def _node_color(ref, node):
    if isinstance(node, str) and 'ruin_hub' in node:
        return _HUB_COLOR
    return AREA_COLORS.get(_node_area(ref, node), _DEFAULT_COLOR)


def _reward_label_lookup(log: SpoilerLog, ref):
    """room -> list of "Reward (Check)" strings actually granted this seed."""
    check_to_reward = {}
    for r in list(log.character_rewards) + list(log.other_rewards):
        if r.check:
            check_to_reward[r.check] = r.reward_name
    out = {}
    for room, checks in ref.room_reward_checks.items():
        labels = []
        for check in checks:
            reward = check_to_reward.get(check)
            labels.append("%s (%s)" % (reward, check) if reward else check)
        out[normalize_room(room)] = labels
    return out


def render_branches(branches: List[Branch], log: SpoilerLog, out_path: str,
                    reports=None) -> str:
    """Draw the branches to ``out_path`` (PNG). Returns ``out_path``."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    import networkx as nx

    ref = get_reference()
    reward_labels = _reward_label_lookup(log, ref)
    softlock_nodes = set()
    if reports:
        for rep in reports:
            for pocket in rep.softlock_pockets:
                softlock_nodes.update((rep.index, n) for n in pocket)

    branch_titles = ["Branch 0 (Left)", "Branch 1 (Center)", "Branch 2 (Right)"]
    fig, axes = plt.subplots(1, 3, figsize=(30, 18))
    fig.suptitle("Ruination Mode - Room Network Map  (seed %s)" % log.seed,
                 fontsize=20, fontweight="bold", y=0.98)

    areas_used = set()

    for branch in branches:
        ax = axes[branch.index]
        g = branch.graph

        # drop nodes with no edges (matches generate_map_image)
        connected = {n for e in g.edges() for n in e}
        g = g.subgraph(connected).copy()

        if g.number_of_nodes() == 0:
            ax.set_title("%s\n(empty)" % branch_titles[branch.index])
            ax.axis("off")
            continue

        try:
            pos = nx.kamada_kawai_layout(g)
        except Exception:
            pos = nx.spring_layout(g, k=2.0, iterations=100, seed=42)

        for n in g.nodes:
            areas_used.add(_node_area(ref, n))

        def is_hub(n):
            return isinstance(n, str) and "ruin_hub" in n

        def is_terminus(n):
            return n == branch.terminus or (isinstance(n, str) and "terminus" in n)

        hub_nodes = [n for n in g.nodes if is_hub(n)]
        term_nodes = [n for n in g.nodes if is_terminus(n)]
        reward_nodes = [n for n in g.nodes if n in branch.reward_rooms
                        and n not in hub_nodes and n not in term_nodes]
        regular = [n for n in g.nodes if n not in hub_nodes
                   and n not in term_nodes and n not in reward_nodes]

        warp = ref.warp_rooms
        town = ref.town_rooms
        plain = [n for n in regular if n not in warp and n not in town]
        town_only = [n for n in regular if n in town and n not in warp]
        warp_only = [n for n in regular if n in warp and n not in town]
        warp_town = [n for n in regular if n in warp and n in town]

        door_edges = [(u, v) for u, v, d in g.edges(data=True)
                      if d.get("kind") == "door"]
        oneway_edges = [(u, v) for u, v, d in g.edges(data=True)
                        if d.get("kind") == "oneway"]
        # dedup two-way door pairs
        seen = set()
        door_dedup = []
        for u, v in door_edges:
            key = tuple(sorted((str(u), str(v))))
            if key not in seen:
                seen.add(key)
                door_dedup.append((u, v))

        if door_dedup:
            nx.draw_networkx_edges(g, pos, edgelist=door_dedup, ax=ax,
                                   edge_color="#555555", width=1.5,
                                   arrows=False, alpha=0.7)
        if oneway_edges:
            nx.draw_networkx_edges(g, pos, edgelist=oneway_edges, ax=ax,
                                   edge_color="#CC0000", width=2.0, style="dashed",
                                   arrows=True, arrowstyle="->", arrowsize=20,
                                   alpha=0.85, connectionstyle="arc3,rad=0.1")

        def draw(nodes, size, shape):
            if nodes:
                nx.draw_networkx_nodes(
                    g, pos, nodelist=nodes, ax=ax,
                    node_color=[_node_color(ref, n) for n in nodes],
                    node_size=size, node_shape=shape,
                    edgecolors="black", linewidths=1.0)

        draw(plain, 300, "o")
        draw(town_only, 600, "o")
        draw(warp_only, 300, "^")
        draw(warp_town, 600, "^")
        draw(reward_nodes, 600, "*")
        if hub_nodes:
            nx.draw_networkx_nodes(g, pos, nodelist=hub_nodes, ax=ax,
                                   node_color=_HUB_COLOR, node_size=800,
                                   node_shape="H", edgecolors="black", linewidths=2.0)
        if term_nodes:
            nx.draw_networkx_nodes(g, pos, nodelist=term_nodes, ax=ax,
                                   node_color=_TERMINUS_COLOR, node_size=700,
                                   node_shape="D", edgecolors="black", linewidths=2.0)

        # highlight softlock-pocket rooms with a red ring
        pocket = [n for n in g.nodes if (branch.index, n) in softlock_nodes]
        if pocket:
            nx.draw_networkx_nodes(g, pos, nodelist=pocket, ax=ax,
                                   node_color="none", node_size=950,
                                   node_shape="o", edgecolors="red", linewidths=2.5)

        ys = [p[1] for p in pos.values()]
        offset = (max(ys) - min(ys)) * 0.025 if len(ys) > 1 else 0.05
        for n in g.nodes:
            x, y = pos[n]
            if is_hub(n):
                line1 = "HUB"
            elif is_terminus(n):
                line1 = "TERMINUS"
            elif n in branch.reward_rooms:
                line1 = _node_area(ref, n)
            else:
                area = _node_area(ref, n)
                line1 = area if area != "Unknown" else ""
            lines = [line1, str(n)] if line1 else [str(n)]
            if n in reward_labels and n in branch.reward_rooms:
                lines.append(", ".join(reward_labels[n]))
            ax.text(x, y - offset, "\n".join(lines), fontsize=7, fontweight="bold",
                    ha="center", va="top", multialignment="center")

        ax.set_title("%s\n%d rooms, %d rewards, %d doors, %d one-ways"
                     % (branch_titles[branch.index], g.number_of_nodes(),
                        len(reward_nodes), len(door_dedup), len(oneway_edges)),
                     fontsize=13, fontweight="bold")
        ax.axis("off")

    handles = [
        mlines.Line2D([], [], color=_HUB_COLOR, marker="H", linestyle="None",
                      markersize=12, markeredgecolor="black", label="Hub"),
        mlines.Line2D([], [], color=_TERMINUS_COLOR, marker="D", linestyle="None",
                      markersize=10, markeredgecolor="black", label="Terminus"),
        mlines.Line2D([], [], color="white", marker="*", linestyle="None",
                      markersize=14, markeredgecolor="black", label="Reward"),
        mlines.Line2D([], [], color="white", marker="^", linestyle="None",
                      markersize=10, markeredgecolor="black", label="Warp point"),
        mlines.Line2D([], [], color="white", marker="o", linestyle="None",
                      markersize=14, markeredgecolor="black", label="Town"),
        mlines.Line2D([], [], color="#555555", linestyle="solid",
                      linewidth=2, label="Door (two-way)"),
        mlines.Line2D([], [], color="#CC0000", linestyle="dashed",
                      linewidth=2, label="Trap/Pit (one-way)"),
        mlines.Line2D([], [], color="none", marker="o", linestyle="None",
                      markersize=14, markeredgecolor="red", label="Softlock pocket"),
        mlines.Line2D([], [], linestyle="None", label=""),
    ]
    for area in sorted(areas_used):
        if area in ("Hub", "Unknown"):
            continue
        handles.append(mpatches.Patch(
            facecolor=AREA_COLORS.get(area, _DEFAULT_COLOR),
            edgecolor="black", label=area))

    fig.legend(handles=handles, loc="lower center", ncol=6, fontsize=9,
               frameon=True, fancybox=True, shadow=True, bbox_to_anchor=(0.5, 0.0))
    plt.tight_layout(rect=[0, 0.08, 1, 0.96])
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    return out_path
