"""Property tests for doors.model.WorldModel (rewrite Stage B).

The model's contract: every mutating operation is journaled, and
rollback(mark) restores the exact pre-checkpoint state (verified by full
snapshot fingerprint); door connections merge classes; one-way cycles
merge every class on the cycle (the class graph is always a DAG); key
application unlocks per legacy semantics and cascades.

Run: python3 tests/doors/test_model.py
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from doors.model import WorldModel, DOOR, TRAP, PIT


def tiny_world():
    """Four rooms: A(2 doors, key k1) B(door, trap) C(pit, door)
    D(door locked behind k1, key k2 behind k1)."""
    return WorldModel({
        'A': {'doors': [1, 2], 'keys': ['k1']},
        'B': {'doors': [3], 'traps': [2001]},
        'C': {'doors': [4], 'pits': [3001]},
        'D': {'doors': [5], 'locks': {('k1',): [6, 'k2']}},
    })


def test_connect_and_rollback():
    w = tiny_world()
    base = w.snapshot()
    m = w.checkpoint()
    c = w.connect_door(1, 3)                       # A + B merge
    assert w.class_of_room('A') == w.class_of_room('B') == c
    assert w.door_pairs == [(1, 3)]
    assert sorted(w.class_elements(c, DOOR)) == [2]
    w.rollback(m)
    assert w.snapshot() == base
    print('PASS: connect_door + rollback roundtrip')


def test_oneway_cycle_merges():
    w = tiny_world()
    w.connect_door(1, 3)                           # A+B
    cAB = w.class_of_room('A')
    w.connect_oneway(2001, 3001)                   # A+B --> C
    assert w.class_of_room('C') in w.downstream(cAB)
    m = w.checkpoint()
    # Close the loop: C's door to A+B's remaining door -> everything merges
    # (a two-way connection makes the trap cycle mutually traversable).
    c = w.connect_door(4, 2)
    assert w.class_of_room('C') == w.class_of_room('A') == c
    assert w.downstream(c) == [] and w.upstream(c) == []   # DAG-clean
    w.rollback(m)
    assert w.class_of_room('C') != w.class_of_room('A')
    print('PASS: cycle closure merges classes, rollback splits them')


def test_key_unlock_cascade():
    w = tiny_world()
    base = w.snapshot()
    m = w.checkpoint()
    released = w.apply_key('k1')
    assert released == ['k2']
    assert 6 in w.class_elements(w.class_of_room('D'), DOOR)
    assert 6 in w.initially_locked_exits
    assert 'k2' in w.class_keys(w.class_of_room('D'))
    # k1 held in A is consumed
    assert 'k1' not in w.class_keys(w.class_of_room('A'))
    w.rollback(m)
    assert w.snapshot() == base
    print('PASS: apply_key unlock cascade + rollback')


def test_fuzz_rollback():
    """Randomized ops with nested checkpoints: every rollback must restore
    the exact snapshot taken at its checkpoint."""
    rng = random.Random(1234)
    for trial in range(200):
        n = rng.randint(3, 8)
        rooms = {}
        eid = 1
        for i in range(n):
            spec = {'doors': [], 'traps': [], 'pits': []}
            for _ in range(rng.randint(1, 3)):
                spec['doors'].append(eid); eid += 1
            if rng.random() < 0.5:
                spec['traps'].append(2000 + eid); eid += 1
            if rng.random() < 0.5:
                spec['pits'].append(3000 + eid); eid += 1
            if rng.random() < 0.3:
                spec['keys'] = [f'key{i}']
            if rng.random() < 0.3 and i > 0:
                spec['locks'] = {(f'key{rng.randrange(i)}',): [eid]}
                eid += 1
            rooms[f'r{i}'] = spec
        w = WorldModel(rooms)
        stack = []
        for _ in range(rng.randint(5, 25)):
            roll = rng.random()
            if roll < 0.25 or not stack and roll < 0.5:
                stack.append((w.checkpoint(), w.snapshot()))
            elif roll < 0.5 and stack:
                mark, snap = stack.pop()
                w.rollback(mark)
                assert w.snapshot() == snap, f'trial {trial}: rollback mismatch'
            else:
                doors = [e for h in range(n) for e in w.elements[h][DOOR]]
                traps = [e for h in range(n) for e in w.elements[h][TRAP]]
                pits = [e for h in range(n) for e in w.elements[h][PIT]]
                keys = [k for h in range(n) for k in w.keys[h]]
                choices = []
                if len(doors) >= 2:
                    choices.append('door')
                if traps and pits:
                    choices.append('oneway')
                if keys:
                    choices.append('key')
                if not choices:
                    continue
                op = rng.choice(choices)
                if op == 'door':
                    d1, d2 = rng.sample(doors, 2)
                    w.connect_door(d1, d2)
                elif op == 'oneway':
                    w.connect_oneway(rng.choice(traps), rng.choice(pits))
                else:
                    w.apply_key(rng.choice(keys))
        while stack:
            mark, snap = stack.pop()
            w.rollback(mark)
            assert w.snapshot() == snap, f'trial {trial}: final rollback mismatch'
    print('PASS: 200-trial randomized rollback fuzz')


def test_dag_invariant():
    """After any sequence of connections the class graph has no cycles."""
    rng = random.Random(99)
    for trial in range(100):
        n = rng.randint(4, 10)
        rooms = {f'r{i}': {'doors': [i * 10 + 1, i * 10 + 2],
                           'traps': [2000 + i], 'pits': [3000 + i]}
                 for i in range(n)}
        w = WorldModel(rooms)
        for _ in range(rng.randint(3, 15)):
            traps = [e for h in range(n) for e in w.elements[h][TRAP]]
            pits = [e for h in range(n) for e in w.elements[h][PIT]]
            doors = [e for h in range(n) for e in w.elements[h][DOOR]]
            if rng.random() < 0.5 and traps and pits:
                w.connect_oneway(rng.choice(traps), rng.choice(pits))
            elif len(doors) >= 2:
                d1, d2 = rng.sample(doors, 2)
                w.connect_door(d1, d2)
        for c in w.classes():
            down = w.downstream(c)
            assert c not in down, f'trial {trial}: cycle through {c}'
            up = set(w.upstream(c))
            assert not (set(down) & up), f'trial {trial}: un-merged cycle at {c}'
    print('PASS: 100-trial DAG invariant')


if __name__ == '__main__':
    test_connect_and_rollback()
    test_oneway_cycle_merges()
    test_key_unlock_cascade()
    test_fuzz_rollback()
    test_dag_invariant()
    print('\nAll model tests passed.')
