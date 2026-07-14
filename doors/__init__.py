"""Worlds Collide door randomization.

This package implements all door randomization features, as described in
DOOR_RANDO_GUIDE.md. Door randomization is structured in nested layers,
and the layers only point downward:

    atlas/       Static data about every exit: partners, coordinates,
                 one-way records, room names. The database (compiled.py)
                 is generated and consistency-checked by
                 tools/compile_atlas.py; manual specification lives in
                 curation.py.
    model.py     World model used by the planners to represent rooms --
                 their contents (exits, trapdoors, keys, locked items)
                 and the connections between them. Connected rooms merge
                 into clusters; one-way drops form a directed graph
                 between clusters. Every change is journaled so a planner
                 can back out of a dead end (checkpoint/rollback).
    plan/        Tools for constructing a map. Planners follow a
                 procedure to connect a map (the "walk": grow outward
                 from a start room, connect exits to random entrances,
                 backtrack when the map can no longer be completed).
                 modes.py assembles the room pools for each flag and is
                 the single entry point (plan_for_args); ruination has
                 its own planner package (plan/ruination/). Every mode
                 returns the same DoorPlan artifact (plan/artifact.py).
    validate/    Acceptance checks a finished plan must pass regardless
                 of which planner produced it.
    realize/     Writing a finished plan into the ROM: exit connections,
                 one-way transition scripts, event-tile runtime data.
                 Functions take the live Maps object at call time.

Two properties are load-bearing and worth protecting:

- The whole package imports and runs WITHOUT a ROM and WITHOUT argv
  (no `args` globals). This is what makes the offline tests
  (tests/doors/) and study harnesses (tools/) possible. If new code
  here wants a fact from the ROM or the arg parser, pass it in as data.
- Planning happens ONCE, in the Data phase (Doors.mod calls
  plan.modes.plan_for_args), in one contiguous window of the seeded
  global RNG -- this is what makes seeds deterministic and
  machine-independent. The Events phase receives the finished DoorPlan
  and only binds rewards to it (event/ruination_bind.py); it never
  plans.

Development history and key milestones: doors/HISTORY.md.
"""
