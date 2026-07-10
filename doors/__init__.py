"""Worlds Collide door randomization, v2 (the `-d2` planner).

This package is the ground-up rewrite of the door-randomization core
(DOOR_RANDO_REWRITE_PLAN.md). It is deliberately layered, and the layers
only point downward:

    atlas/       WHAT EXISTS.  Static, generated truth about every exit:
                 partners, coordinates, one-way records, room names.
                 Regenerated + consistency-checked by tools/compile_atlas.py.
    model.py     WHAT IS CONNECTED.  The mutable world state a planner
                 explores: rooms merged into mutually-reachable classes,
                 one-way edges, keys/locks, and the growing matching.
                 Every mutation is journaled, so backtracking is
                 checkpoint()/rollback() instead of deepcopy.
    plan/        WHAT TO CONNECT.  Pure, RNG-consuming planners: the
                 backtracking walk + prune rules, per-mode pool assembly
                 (modes.py), and the ruination planner (plan/ruination/).
                 Every mode returns the same DoorPlan artifact
                 (plan/artifact.py); ruination is a view on it.
    validate/    IS IT RIGHT.  Structural acceptance gates a solved plan
                 must pass regardless of which planner produced it.

Two properties are load-bearing and worth protecting:

- The whole package imports and runs WITHOUT a ROM and WITHOUT argv
  (no `args` coupling). This is what makes the offline harnesses in
  tools/ (parity, oracles, stats) and tests/doors/ possible.
- Planning happens ONCE, in the Data phase (Doors.mod calls
  plan.modes.plan_for_args), in one contiguous window of the seeded
  global RNG. Events receives the finished DoorPlan and only *binds* it
  (event/ruination_bind.py) -- it never plans.

Realization (writing the plan into the ROM: exits, transitions, event
tiles) still lives in the legacy modules (data/maps.py postprocess and
friends) until the Stage F cutover.
"""
