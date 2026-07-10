"""Ruination planner (rewrite Stages D-E).

Plans the three-branch ruination world on a single shared WorldModel:
branches are RuinBranch views anchored at their hub rooms, the reserve is
just rooms not yet added to the model, and the keychain is global (legacy
fans every key out to all three branch networks, so one chain is
equivalent). Modules, mirroring plan section 3.3:

- plan.py         Data-phase entry point: resolves the starting party,
                  runs the pure retry loop, returns the DoorPlan
- growth.py       RuinConfig (per-plan table copies) + RuinPlanner: the
                  pick-branch / extend / connect / check-rewards loop,
                  area distribution, reward processing, reserve rescue
- branch.py       RuinBranch view: membership, hub topology, check rooms,
                  dead ends, warp/town cooldowns, stuck reasons
- extend.py       one extension step: the location-aware target validity
                  rules (never strand the branch, never orphan the hub)
- finalize.py     the six-step branch closer, map assembly, and the
                  character-gated-softlock verifier
- kefka_tower.py  -rkt lane randomizer (joint three-party verification)
- dream_maze.py   -maze iso internals (rejection-sampled solvable maze)

The plan is bound to ROM Reward objects in event/ruination_bind.py.
"""
