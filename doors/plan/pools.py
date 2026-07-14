"""Pool loading: room specs for the planners.

Builds WorldModel room specs from the data tables: copies each room's
element lists out of data.rooms.room_data (never mutating them), strips
shared-exit sibling tiles so only the canonical tile of each shared
group is planned, and returns specs plus the pool's forced connections.
"""

from data.rooms import room_data, shared_exits, forced_connections


def load_pool(pool_rooms, shared=None, drop=()):
    """{room_id: spec} for WorldModel, from pristine room_data.

    `shared` is the shared-exits view to strip with (defaults to the
    full table; -drdc/-ruin pass a view with the split exits removed)."""
    if shared is None:
        shared = shared_exits
    drop = set(drop)
    specs = {}
    for rid in pool_rooms:
        rd = room_data[rid]
        doors = [d for d in rd[0] if d not in drop]
        traps, pits = list(rd[1]), list(rd[2])
        keys, locks = [], {}
        if len(rd) == 6:
            keys = list(rd[3])
            locks = {k: list(v) for k, v in rd[4].items()}
        # A room holding the canonical
        # tile of a shared doorway drops the sibling tiles. The canonical
        # tile may itself be LOCKED (Phantom Train 493 behind pt1), and the
        # siblings may live inside lock lists - scan those and
        # removes from anywhere, so both must be covered here.
        locked_items = [i for items in locks.values() for i in items
                        if not isinstance(i, str)]
        shared_siblings = {s for d in list(doors) + locked_items
                           if d in shared for s in shared[d]}
        if shared_siblings:
            doors = [d for d in doors if d not in shared_siblings]
            traps = [t for t in traps if t not in shared_siblings]
            pits = [p for p in pits if p not in shared_siblings]
            locks = {k: [i for i in v if i not in shared_siblings]
                     for k, v in locks.items()}
        specs[rid] = {'doors': doors, 'traps': traps, 'pits': pits,
                      'keys': keys, 'locks': locks}
    return specs


def pool_forcing(specs):
    """Forced connections relevant to this pool (read-only view of
    data.rooms.forced_connections).

    Forcing ids are protected globally, so a pool
    pit that is the target of an out-of-pool forced trap must still be
    excluded as a walk target: include entries where either side is in
    the pool (the walk only connects when both are)."""
    elements = {e for s in specs.values() for kind in ('doors', 'traps', 'pits')
                for e in s[kind]}
    return {d: list(t) for d, t in forced_connections.items()
            if d in elements or any(x in elements for x in t)}
