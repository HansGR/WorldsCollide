"""Generated mode x event manifest.

"What does -drdc change?" This tool derives the answer from the code
itself -- which lifecycle hooks each
event file defines, which derived predicates it computes, and which raw
mode flags it still tests -- so the table never goes stale.

Usage: python3 tools/mode_manifest.py [--markdown]
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

HOOKS = ('door_rando_mod', 'dungeon_crawl_mod', 'ruination_mod')
MODE_FLAG_PREFIXES = ('door_randomize', 'map_shuffle', 'ruination_mode',
                      'open_world', 'character_gating', 'no_free_heals')
SKIP = ('events.py', 'event.py', '__init__.py')


def scan_file(path):
    """(hooks defined, predicates assigned, raw mode-flag attrs tested)."""
    tree = ast.parse(open(path).read())
    hooks, predicates, flags = [], set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in HOOKS:
            hooks.append(node.name)
        if isinstance(node, ast.Attribute):
            # self.DOOR_RANDOMIZE / self.MAP_SHUFFLE assignments or reads
            if node.attr in ('DOOR_RANDOMIZE', 'MAP_SHUFFLE'):
                predicates.add(node.attr)
            # args.<mode flag> tests
            if any(node.attr.startswith(p) for p in MODE_FLAG_PREFIXES):
                base = node.value
                if isinstance(base, ast.Attribute) and base.attr == 'args':
                    flags.add(node.attr)
                elif isinstance(base, ast.Name) and base.id == 'args':
                    flags.add(node.attr)
    return hooks, predicates, flags


def main(markdown=False):
    event_dir = os.path.join(ROOT, 'event')
    rows = []
    for fn in sorted(os.listdir(event_dir)):
        if not fn.endswith('.py') or fn in SKIP:
            continue
        hooks, predicates, flags = scan_file(os.path.join(event_dir, fn))
        if hooks or predicates or flags:
            rows.append((fn[:-3], hooks, sorted(predicates), sorted(flags)))

    if markdown:
        print('| event | hooks | predicates | raw mode flags |')
        print('|---|---|---|---|')
        for name, hooks, preds, flags in rows:
            print(f"| {name} | {', '.join(hooks) or '-'} "
                  f"| {', '.join(preds) or '-'} | {', '.join(flags) or '-'} |")
    else:
        w = max(len(r[0]) for r in rows)
        for name, hooks, preds, flags in rows:
            print(f'{name:{w}s}  hooks[{", ".join(hooks) or "-"}]  '
                  f'predicates[{", ".join(preds) or "-"}]  '
                  f'flags[{", ".join(flags) or "-"}]')
    n_hooks = sum(len(r[1]) for r in rows)
    print(f'\n{len(rows)} event files with mode-conditioned code; '
          f'{n_hooks} lifecycle hooks defined '
          f'(framework-dispatched unless invoked inline).')


if __name__ == '__main__':
    main(markdown='--markdown' in sys.argv)
