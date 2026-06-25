# ruination_spoiler

Parse a Ruination-mode spoiler log, rebuild the per-branch door map, and
reproduce the graphical branch map that ruination mode draws during
generation (`Ruination.generate_map_image`). Handy for inspecting a finished
seed for mapping problems (e.g. a suspected softlock) without re-running the
randomizer.

## Usage

```sh
# Text report + PNG (writes <spoiler>_branch_map.png next to the log)
python -m ruination_spoiler path/to/ruin_seed.txt

# Choose the image path
python -m ruination_spoiler ruin_seed.txt -o tests/branch_map.png

# Report only, no image (no networkx/matplotlib needed)
python -m ruination_spoiler ruin_seed.txt --no-image
```

The log must be a Ruination seed generated with `-debug-verbose` (or `-dv`):
the branch reconstruction reads the per-branch connection trace from the
"Debug Verbose Diagnostics" section. The reward tables and the global door
map are read from the normal spoiler sections.

## As a library

```python
from ruination_spoiler import parse_spoiler, build_branches
from ruination_spoiler.analyze import analyze_branch, format_report
from ruination_spoiler.render import render_branches

log = parse_spoiler("ruin_seed.txt")
branches = build_branches(log)                 # list of 3 Branch objects
reports = [analyze_branch(b) for b in branches]
print(format_report(reports))
render_branches(branches, log, "branch_map.png", reports=reports)
```

Each `Branch` carries a `networkx.DiGraph` (`branch.graph`) whose edges are
tagged `kind="door"` (two-way) or `kind="oneway"` (trap/pit). `branch.hub`,
`branch.terminus` and `branch.reward_rooms` mark the special rooms.

## How it works (and its limits)

* **door -> room** is resolved by preferring the spoiler's own room names
  (reward/terminus paths and the verbose `Selected ... (room R)` mentions),
  then falling back to a static index restricted to `RUIN_ROOM_SETS` — this is
  what disambiguates doors that `data/rooms.py` lists in several candidate
  rooms (only one of which ruination uses). The three Narshe-School hub doors
  are split one per branch.
* **connection -> branch** uses the door each branch *used* in its
  `Making connection` trace, which avoids the shared world map leaking rooms
  between branches.
* The directed report flags rooms reachable from the hub that can reach
  neither the hub nor the terminus again ("softlock pockets"). Note that a
  few ruination areas are entered/left by *scripted* events rather than doors
  (the Lone Wolf reward fall, the Lete River raft, waking from the Doma
  dream). Those legitimately show up as door-graph dead-ends; treat such flags
  as "worth a look", not proof of a softlock.

## Files

| File            | Purpose                                              |
|-----------------|------------------------------------------------------|
| `parser.py`     | Text -> `SpoilerLog` (standard library only).        |
| `ruin_data.py`  | Loads `RUIN_ROOM_SETS` etc. and the door->room index.|
| `reconstruct.py`| Builds the three branch `DiGraph`s.                  |
| `analyze.py`    | Directed reachability / softlock report.             |
| `render.py`     | PNG renderer (needs networkx + matplotlib).          |
| `__main__.py`   | CLI.                                                  |
