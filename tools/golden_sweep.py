"""Byte-golden regression sweep for door randomization.

Builds a pinned matrix of mode x seed configurations and compares the
SHA256 of each output ROM and spoiler log (normalized: the Generated
timestamp line dropped) against tools/golden_manifest.json. Builds are
deterministic and machine-independent by design, so the manifest is
committed; any refactor of planning or realization must leave it
unchanged unless the change is deliberate (then re-record with --update
and say why in the commit message).

Usage:
    python3 tools/golden_sweep.py -i <vanilla rom> [--update] [--only ruin1,drdc1]

Runtime: ~10-15 minutes for the full matrix.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'tools', 'golden_manifest.json')

# name -> flag string (seed included; -sl always added)
CONFIGS = {
    'vanilla1':  '-s 1001',
    'ruin1':     '-ruin -s 424242',
    'ruin2':     '-ruin -s 1002',
    'ruin3':     '-ruin -s 1003',
    'ruinopen':  '-ruin -open -s 1004',
    'ruinsep':   '-ruin -maze sep -s 1005',
    'drdc1':     '-drdc -s 12345',
    'drdc2':     '-drdc -s 1006',
    'dre1':      '-dre -s 999',
    'dra1':      '-dra -s 555',
    'drx1':      '-drx -s 666',
    'dremaps':   '-dre -maps -s 777',
    'mapx1':     '-mapx -s 888',
    'indiv1':    '-dru -drun -drem -s 111',
    'drunb1':    '-drunb -s 1007',
}


def build_and_hash(rom, name, flags, workdir):
    out = os.path.join(workdir, name + '.smc')
    log = os.path.join(workdir, name + '.txt')
    cmd = [sys.executable, os.path.join(ROOT, 'wc.py'),
           '-i', rom, '-o', out, '-sl'] + flags.split()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          timeout=1200)
    if proc.returncode != 0:
        return None, (proc.stdout + proc.stderr)[-800:]
    rom_hash = hashlib.sha256(open(out, 'rb').read()).hexdigest()
    spoiler = b''.join(l for l in open(log, 'rb').read().splitlines(True)
                       if not l.startswith(b'Generated'))
    log_hash = hashlib.sha256(spoiler).hexdigest()
    return {'rom': rom_hash, 'spoiler': log_hash}, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', dest='rom', required=True, help='vanilla ROM path')
    ap.add_argument('--update', action='store_true',
                    help='record current hashes as the new manifest')
    ap.add_argument('--only', default='',
                    help='comma-separated config names to run')
    opts = ap.parse_args()

    manifest = {}
    if os.path.exists(MANIFEST):
        manifest = json.load(open(MANIFEST))

    only = set(filter(None, opts.only.split(',')))
    names = [n for n in CONFIGS if not only or n in only]

    failures = []
    with tempfile.TemporaryDirectory() as workdir:
        for name in names:
            got, err = build_and_hash(opts.rom, name, CONFIGS[name], workdir)
            if got is None:
                print(f'{name}: BUILD FAILED\n{err}')
                failures.append(name)
                continue
            if opts.update:
                manifest[name] = got
                print(f'{name}: recorded')
            elif name not in manifest:
                print(f'{name}: NOT IN MANIFEST (run --update)')
                failures.append(name)
            elif manifest[name] != got:
                what = [k for k in got if manifest[name].get(k) != got[k]]
                print(f'{name}: MISMATCH ({", ".join(what)})')
                failures.append(name)
            else:
                print(f'{name}: ok')

    if opts.update:
        json.dump(manifest, open(MANIFEST, 'w'), indent=1, sort_keys=True)
        print(f'\nManifest written: {MANIFEST}')
    if failures:
        print(f'\n{len(failures)}/{len(names)} configs FAILED')
        sys.exit(1)
    print(f'\nAll {len(names)} configs match the golden manifest.')


if __name__ == '__main__':
    main()
