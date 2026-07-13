"""Isolated dream maze randomizer (-maze iso).

Random door/trap matchings over
the nine Stooges Maze rooms, rejection-sampled against an exact
solvability check (every room reaches the boss room; both stooge key
rooms are round-trippable from it). The chosen entry pit
is RETURNED instead of written into room_data - the caller records it as
a spec override on RuinConfig.
"""

from data.rooms import room_data

MAZE_ROOMS = [421, 422, 423, 424, 425, 426, 427, 428, 429]
STOOGE_ROOMS = [423, 427]     # rooms holding the stooge keys cd1 / cd2
END_ROOM = 429                # boss room (locked exit 2070 needs cd1+cd2)
# Entry pits exclude the two stooge rooms (6847/423, 6852/427) and the
# west room (6844/422) so the party never starts inside a key room.
ENTRY_PITS = [6845, 6846, 6854, 3069, 6849, 6843, 6848, 6853]
MAX_TRIES = 20000


def randomize_isolated_maze(rng):
    """Returns ([door pairs, trap->pit pairs], entry_pit)."""
    door_room, trap_room, pit_room = {}, {}, {}
    for r in MAZE_ROOMS:
        for d in room_data[r][0]:
            door_room[d] = r
        for t in room_data[r][1]:
            trap_room[t] = r
        for p in room_data[r][2]:
            pit_room[p] = r
    doors, traps, pits = list(door_room), list(trap_room), list(pit_room)

    def reachable(door_pairs, trap_pits, start):
        adj = {r: set() for r in MAZE_ROOMS}
        for d1, d2 in door_pairs:                    # doors: two-way
            adj[door_room[d1]].add(door_room[d2])
            adj[door_room[d2]].add(door_room[d1])
        for t, p in trap_pits:                       # traps: one-way
            adj[trap_room[t]].add(pit_room[p])
        seen, stack = {start}, [start]
        while stack:
            for n in adj[stack.pop()]:
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        return seen

    def solvable(door_pairs, trap_pits):
        if any(END_ROOM not in reachable(door_pairs, trap_pits, r)
               for r in MAZE_ROOMS):
            return False
        from_end = reachable(door_pairs, trap_pits, END_ROOM)
        return all(s in from_end for s in STOOGE_ROOMS)

    entry_pit = door_pairs = trap_pits = None
    for _ in range(MAX_TRIES):
        entry_pit = rng.choice(ENTRY_PITS)
        ds = doors[:]
        rng.shuffle(ds)
        door_pairs = [[ds[i], ds[i + 1]] for i in range(0, len(ds), 2)]
        avail = [p for p in pits if p != entry_pit]
        rng.shuffle(avail)
        trap_pits = [[traps[i], avail[i]] for i in range(len(traps))]
        if any(trap_room[t] == pit_room[p] for t, p in trap_pits):
            continue                                 # trap into its own room
        if solvable(door_pairs, trap_pits):
            break
    return [door_pairs, trap_pits], entry_pit
