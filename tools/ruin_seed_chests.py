"""List the treasure chests a ruination seed makes available, with contents.

usage: python3 tools/ruin_seed_chests.py -i VANILLA.smc -ruin [flags] -s SEED [--json OUT]

Builds the seed in-process up to the data phase (no ROM is written), then
reports doors/plan/ruination/chests.py seed_chests(): per branch the
reachable rooms and their chests, and per Kefka's Tower lane its rooms and
chests, each chest with its seed contents (data.chests.all_chests[id]).
Gold chests hold contents x 100 GP. The flags must be the seed's flags
(including -sl if the seed was rolled with it: it changes the RNG)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def main():
    out_json = None
    if '--json' in sys.argv:
        i = sys.argv.index('--json')
        out_json = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    sys.argv += ['-nro']

    import args
    from memory.memory import Memory
    memory = Memory()
    from data.data import Data
    data = Data(memory.rom, args)
    plan = data.maps.doors.plan
    if plan is None or plan.ruination is None:
        sys.exit('not a ruination seed (-ruin)')

    from data.chest import Chest
    from constants.items import id_name
    from doors.plan.ruination.chests import seed_chests
    chests = data.maps.chests.all_chests

    def describe(chest_id):
        chest = chests[chest_id]
        entry = {'id': chest_id, 'type': chest.get_type_string()}
        if chest.type == Chest.ITEM:
            entry['item'] = id_name.get(chest.contents, hex(chest.contents))
        elif chest.type == Chest.GOLD:
            entry['gp'] = chest.contents * 100
        elif chest.type == Chest.MONSTER:
            entry['pack'] = chest.contents
        return entry

    found = seed_chests(plan)
    report = {'branches': {}, 'kefka_tower': {}, 'kefka_tower_after_switches': {},
              'kefka_tower_back': {'back': {room: [describe(c) for c in ids]
                                            for room, ids in found['kefka_tower_back'].items()}},
              'pending': found['pending']}
    for group, key in (('branches', 'branches'), ('kefka_tower', 'kefka_tower'),
                       ('kefka_tower_after_switches', 'kefka_tower_after_switches')):
        for part, rooms in found[key].items():
            report[group][str(part)] = {room: [describe(c) for c in ids] for room, ids in rooms.items()}

    def summary(rooms):
        entries = [e for ids in rooms.values() for e in ids]
        items = [e for e in entries if e['type'] == 'Item']
        return (f"{len(entries)} chests: {len(items)} items, "
                f"{sum(e.get('gp', 0) for e in entries)} GP in "
                f"{sum(1 for e in entries if e['type'] == 'Gold')} gold chests, "
                f"{sum(1 for e in entries if e['type'] == 'Monster')} MIAB, "
                f"{sum(1 for e in entries if e['type'] == 'Empty')} empty")

    for group, title in (('branches', 'Branch'), ('kefka_tower', "Kefka's Tower lane"),
                         ('kefka_tower_after_switches', "Kefka's Tower, after the switches, lane"),
                         ('kefka_tower_back', "Kefka's Tower")):
        for part, rooms in report[group].items():
            print(f"{title} {part}: {summary(rooms)}")
            for room, entries in rooms.items():
                text = ', '.join(e.get('item') or (f"{e['gp']} GP" if 'gp' in e else e['type'])
                                 for e in entries)
                print(f"    {room}: {text}")
    if report['pending']:
        print(f"Kefka's Tower chests not yet placed in a room: {report['pending']}")
    if out_json:
        with open(out_json, 'w') as f:
            json.dump(report, f, indent=1)


if __name__ == '__main__':
    main()
