"""Ruination planner (rewrite Stage D).

Plans the three-branch ruination world on a single shared WorldModel:
branches are RuinBranch views anchored at their hub rooms, the reserve is
just rooms not yet added to the model, and the keychain is global (legacy
fans every key out to all three branch networks, so one chain is
equivalent). Layers, mirroring plan section 3.3:

- branch.py     RuinBranch view: membership, hub topology, check rooms,
                dead ends, warp/town cooldowns, stuck reasons
- (later)       topology/extension rules, growth orchestrator, finalize,
                kefka_tower, dream_maze
"""
