"""Audit the vanilla exit-half event-bit writes that a randomized arrival loses.

    python3 tools/oneway_bit_audit.py

In vanilla a trap and its landing (or an event-tile door and its partner)
are one script, so the EXIT half may set up state the ARRIVAL depends on.
Door randomization keeps only the landing's load when a pit is reached
from a different trap, so that setup is lost unless data/event_exit_patches
require_event_bit re-applies it on arrival (pits are keyed by their TRAP
id: EventExit(pit - 1000); doors by the arrival tile id).

For every trap (2000-2999) and event-tile door (1500-1999) with event
info, this decompiles the exit half [addr, addr+split) from
claude_reference/EventScriptTxt.txt, lists its Set/Clear event bit ops
and says whether the arrival side has a require_event_bit entry.  An
UNCOVERED line is a candidate, not a bug: judge whether the bits are
source-side cleanup (fine to lose), map-local, handled by WC's own event
code, or arrival-side setup (needs an entry).  The 2026-09 review of the
list is in ARCHIVE.md "Phantom Train Car Bits on One-Way Landings".
ROM-free (reads the repo and the decompile only).
"""
import re, sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.event_exit_data import event_exit_info
from data.map_exit_extra import exit_data

dec = {}
pat = re.compile(r'^C([A-F])/([0-9A-F]{4}): ([0-9A-F]{2})\s+(.*)$')
for line in open('claude_reference/EventScriptTxt.txt', encoding='utf-8', errors='replace'):
    m = pat.match(line.rstrip())
    if m:
        bank = int(m.group(1), 16)          # A..F -> 0xa0000..
        off = (bank - 0xA) * 0x10000 + 0xa0000 + int(m.group(2), 16)
        dec[off] = (m.group(3), m.group(4))

src = open('data/event_exit_patches.py').read()
_s = src.index('require_event_bit = {'); reb_section = src[_s:src.index('room_require_event_bit', _s)]
covered = set(int(k) for k in re.findall(r'^\s*(\d+):\s*\{', reb_section, re.M))

def bit_ops(start, end):
    ops = []
    for a in range(start, end):
        if a in dec and re.match(r'(Set|Clear) event bit', dec[a][1]):
            ops.append(dec[a][1].split('[')[0].strip())
    return ops

rows = []
for eid, info in event_exit_info.items():
    if not isinstance(eid, int) or not (1500 <= eid < 3000):
        continue
    addr, length, split = info[0], info[1], info[2]
    if not addr:
        continue
    ops = bit_ops(addr, addr + split)
    if not ops:
        continue
    if eid >= 2000:
        arrival_key, kind = eid, 'trap'
    else:
        partner = exit_data.get(eid, [None])[0]
        arrival_key, kind = partner, f'door (partner {partner})'
    rows.append((eid, kind, info[4], ops, arrival_key in covered if arrival_key is not None else None))

for eid, kind, desc, ops, cov in sorted(rows):
    flag = 'covered' if cov else ('UNCOVERED' if cov is False else 'n/a')
    print(f'{eid} {kind:22s} {desc[:48]:48s} {flag:9s} {"; ".join(ops)}')
print(len(rows), 'scripts set bits in their exit half;', sum(1 for r in rows if r[4] is False), 'uncovered')
