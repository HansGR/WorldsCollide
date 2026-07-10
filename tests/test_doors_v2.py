"""CI wrapper for the door-rando v2 test scripts in tests/doors/.

Those scripts are standalone (run directly: `python3 tests/doors/test_X.py`)
because they insert the repo root on sys.path themselves. They must NOT be
collected by unittest discovery: discovery puts tests/ first on sys.path, so
a tests/doors package would shadow the real top-level doors/ package.
tests/doors therefore has no __init__.py, and this module runs each script
in a subprocess instead (with small seed counts to keep CI fast).
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOORS_TESTS = os.path.join(ROOT, 'tests', 'doors')

# (script, extra argv) - the growth/finalize scripts take a seed count.
SCRIPTS = [
    ('test_atlas.py', []),
    ('test_model.py', []),
    ('test_walk.py', []),
    ('test_ruin_branch.py', []),
    ('test_ruin_extend.py', []),
    ('test_ruin_submaps.py', []),
    ('test_ruin_growth.py', ['10']),
    ('test_ruin_finalize.py', ['10']),
]


class DoorsV2Scripts(unittest.TestCase):
    pass


def _make_test(script, args):
    def test(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(DOORS_TESTS, script)] + args,
            cwd=ROOT, capture_output=True, text=True, timeout=600)
        self.assertEqual(
            proc.returncode, 0,
            f'{script} failed:\n--- stdout ---\n{proc.stdout}'
            f'\n--- stderr ---\n{proc.stderr}')
    return test


for _script, _args in SCRIPTS:
    _name = 'test_' + _script[:-3].replace('test_', '', 1)
    setattr(DoorsV2Scripts, _name, _make_test(_script, _args))


if __name__ == '__main__':
    unittest.main()
