"""Oracle harness: legacy get_valid_pit/door_targets vs v2 extension rules
(rewrite Stage D milestone 2).

Wraps the legacy RuinationBranch validity methods so that every real call
during a -ruin build ALSO reconstructs the branch state as a WorldModel
(one room per legacy node - a legacy compound node is exactly a v2 class,
so singleton classes are faithful; net edges are injected directly) and
runs the v2 counterpart on it. Target sets are compared as sorted lists;
mismatches are logged with full context. The legacy result is always
returned, so the build itself is untouched.

Known benign mismatch sources (documented divergences in extend.py):
- warp/town cooldown gating on compound nodes containing a warp/town room
  (legacy tests the node id and misses those).

Usage (one seed per process - a second in-process build is unsupported):
    python3 tools/ruin_extend_oracle.py <rom> <seed>
"""

import atexit
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ROM = sys.argv[1]
SEED = sys.argv[2] if len(sys.argv) > 2 else 'oracle001'

STATS = {'pit_calls': 0, 'door_calls': 0, 'mismatches': 0, 'errors': 0}


def _report():
    print(f"\n[oracle] pit calls: {STATS['pit_calls']}, "
          f"door calls: {STATS['door_calls']}, "
          f"mismatches: {STATS['mismatches']}, errors: {STATS['errors']}")


atexit.register(_report)


def build_v2_branch(legacy):
    """Reconstruct the legacy branch's current state as (WorldModel, RuinBranch)."""
    from doors.model import WorldModel
    from doors.plan.ruination.branch import RuinBranch

    specs = {}
    for node_id in legacy.net.nodes:
        room = legacy.rooms.get_room(node_id)
        if room is None:
            continue
        specs[node_id] = {
            'doors': list(room.doors), 'traps': list(room.traps),
            'pits': list(room.pits), 'keys': list(room.keys),
            'locks': {k: list(v) for k, v in room.locks.items()},
        }
    w = WorldModel(specs)
    w.protected = set(legacy.protected or ())
    w.initially_locked_exits = set(legacy.initially_locked_exits)
    for u, v in legacy.net.edges:
        if u != v and u in w._index and v in w._index:
            w.edges.append((w._index[u], w._index[v]))

    hub = legacy.get_hub_id()
    others = [n for n in specs if n != hub]
    b = RuinBranch(w, hub, others)
    b.terminus = legacy.terminus
    b.check_rooms = list(legacy.check_rooms)
    b.warp_cooldown = legacy.warp_cooldown
    b.town_cooldown = legacy.town_cooldown
    return w, b


def compare(kind, legacy, exit_id, exit_room_id, legacy_result):
    from doors.plan.ruination import extend as ext
    try:
        w, b = build_v2_branch(legacy)
        topo = ext.topology(b)
        exit_class = w.class_of_room(exit_room_id)
        if kind == 'pit':
            v2 = ext.valid_pit_targets(b, exit_id, exit_class, topo)
        else:
            v2 = ext.valid_door_targets(b, exit_id, exit_class, topo)
    except Exception as e:                          # noqa: BLE001 - log & continue
        STATS['errors'] += 1
        print(f'[oracle] ERROR reconstructing for {kind} exit {exit_id}: {e!r}')
        return
    a = sorted(legacy_result, key=str)
    bres = sorted(v2, key=str)
    if a != bres:
        STATS['mismatches'] += 1
        print(f'[oracle] MISMATCH {kind} exit {exit_id} from {exit_room_id}: '
              f'legacy={a} v2={bres}')


def install():
    import event.ruination as er

    orig_pit = er.RuinationBranch.get_valid_pit_targets
    orig_door = er.RuinationBranch.get_valid_door_targets

    def pit(self, trap_exit, exit_room_id, topology):
        result = orig_pit(self, trap_exit, exit_room_id, topology)
        STATS['pit_calls'] += 1
        compare('pit', self, trap_exit, exit_room_id, result)
        return result

    def door(self, door_exit, exit_room_id, topology, **kw):
        result = orig_door(self, door_exit, exit_room_id, topology, **kw)
        STATS['door_calls'] += 1
        compare('door', self, door_exit, exit_room_id, result)
        return result

    er.RuinationBranch.get_valid_pit_targets = pit
    er.RuinationBranch.get_valid_door_targets = door


def main():
    out = os.path.join(os.path.dirname(ROM), f'oracle_{SEED}.smc')
    print(f'[oracle] === seed {SEED} ===')
    sys.argv = ['wc.py', '-i', ROM, '-o', out, '-s', SEED, '-ruin']
    # wc.main()'s sequence, with install() spliced in after Memory exists
    # (event.ruination allocates ROM space at import, so it cannot be
    # imported before Memory) and before Events runs the generator.
    import args
    import log  # noqa: F401 - parses argv / opens the log, as wc.main does
    from memory.memory import Memory
    memory = Memory()
    from data.data import Data
    data = Data(memory.rom, args)
    install()
    from event.events import Events
    Events(memory.rom, args, data)
    data.write()
    memory.write()


if __name__ == '__main__':
    main()
