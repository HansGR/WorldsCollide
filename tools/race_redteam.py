"""Red-team the L1+L2 race obfuscation: run each attack tier from the
plan against a race ROM and report what it actually recovers.

Attacks, weakest to strongest:
  T1a fixed-offset scan   - read the vanilla addresses (naive tool)
  T1b contiguity follow   - follow the pointer operand, assume records
                            sit contiguously after (the FF6LE model)
  T2  operand-follow      - follow every reader operand to the moved
                            table, read it as plaintext
  T3  shim-follow decode  - follow the reader JSL to its shim, extract
                            table+pad operands, XOR-decode (a faithful
                            reader reimplementation)
Plus two structural checks:
  cross-seed: do two seeds mask/relocate differently?
  known-plaintext: does a leaked plaintext record recover the pad, and
                   how far does that pad reach?

Usage: build two -race ROMs of the same flags but different seeds, then
  python3 tools/race_redteam.py <race_rom_A> <race_rom_B>
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.item_names import id_name

if len(sys.argv) != 3:
    raise SystemExit("usage: race_redteam.py <race_rom_A> <race_rom_B>"
                     " (two -race builds, same flags, different seeds)")
A = open(sys.argv[1], 'rb').read()
B = open(sys.argv[2], 'rb').read()

CHEST_PTRS, CHEST_DATA = 0x2d82f4, 0x2d8634
MAPS = (0x2d8633 - 0x2d82f4 + 1) // 2
# a set of Narshe chest ids with known real contents from the spoiler log
# (we read the truth from the control's own relocated+decoded table)

def op(rom, o): return int.from_bytes(rom[o:o+3], "little")

def follow_shim(rom, site, van_base):
    shim = op(rom, site) - 0xc00000
    assert rom[shim] == 0xbf and rom[shim+4] == 0x5f and rom[shim+8] == 0x6b
    return op(rom, shim+1) - 0xc00000, op(rom, shim+5) - 0xc00000

def truth_chest_records(rom):
    """ground truth: decode the real chest table via the shims."""
    pb, pp = follow_shim(rom, 0x015e4, 0xed82f4)
    db, dp = follow_shim(rom, 0x015f2, 0xed8634)
    ptrs = bytes(x ^ y for x, y in zip(rom[pb:pb+0x342], rom[pp:pp+0x342]))
    data = bytes(x ^ y for x, y in zip(rom[db:db+0x827], rom[dp:dp+0x827]))
    recs = []
    for m in range(MAPS):
        s = int.from_bytes(ptrs[2*m:2*m+2], "little")
        e = int.from_bytes(ptrs[2*(m+1):2*(m+1)+2], "little") if m+1 < MAPS else s
        for off in range(s, e, 5):
            recs.append((m, off, data[off:off+5]))
    return recs

def contents(rec):
    t = rec[3] & 0xfe
    return ("item", id_name.get(rec[4], rec[4])) if t == 0x40 else \
           ("gold", rec[4]*100) if t == 0x80 else \
           ("monster", rec[4]) if t == 0x20 else ("empty", 0)

truth = {(m, off): rec for m, off, rec in truth_chest_records(A)}
truth_contents = {k: contents(v) for k, v in truth.items()}
total = len(truth)

def score(label, got):
    """got: {(m,off): 5-byte record as seen by the attack}"""
    right = sum(1 for k in truth if k in got and contents(got[k]) == truth_contents[k])
    print(f"  {label:<42} recovered {right:>3}/{total} real chest contents "
          f"({100*right//total:>3}%)")
    return right

print(f"L1+L2 race ROM, {total} real chests.  How many does each attack recover?\n")

# T1a: fixed-offset scan at the vanilla addresses (reads the decoy)
def read_at(rom, ptrs_base, data_base):
    got = {}
    for m in range(MAPS):
        s = int.from_bytes(rom[ptrs_base+2*m:ptrs_base+2*m+2], "little")
        e = int.from_bytes(rom[ptrs_base+2*(m+1):ptrs_base+2*(m+1)+2], "little") if m+1 < MAPS else s
        for off in range(s, e, 5):
            got[(m, off)] = rom[data_base+off:data_base+off+5]
    return got
score("T1a fixed-offset scan (vanilla addr = decoy)", read_at(A, CHEST_PTRS, CHEST_DATA))

# T1b: follow the pointer operand to the moved pointer table, but assume
# records are contiguous at +0x340 (the FF6LE failure mode)
pb, _ = follow_shim(A, 0x015e4, 0xed82f4)
score("T1b contiguity-follow (FF6LE model)", read_at(A, pb, pb + 0x340))

# T2: operand-follow assuming plaintext.  the reader site is now a JSL,
# not a LDA, so a tool that only knows the old LDA-operand shape reads
# the JSL's target bytes as if they were an address - garbage.  model
# the strongest T2 that still assumes plaintext: it follows to the true
# table base but does NOT decode
db, dp = follow_shim(A, 0x015f2, 0xed8634)
score("T2 operand-follow, no decode (masked bytes)", read_at(A, pb, db))

# T3: follow the shim and XOR-decode
score("T3 shim-follow + XOR decode (real reader reimpl)", truth)

print("\nStructural properties:")
# cross-seed: two seeds must relocate and mask differently
pbA = follow_shim(A, 0x015f2, 0xed8634)
pbB = follow_shim(B, 0x015f2, 0xed8634)
print(f"  chest_data table base A=0x{pbA[0]:06x}  B=0x{pbB[0]:06x}  "
      f"{'DIFFER' if pbA[0] != pbB[0] else 'SAME'}")
print(f"  chest_data pad  base A=0x{pbA[1]:06x}  B=0x{pbB[1]:06x}  "
      f"{'DIFFER' if pbA[1] != pbB[1] else 'SAME'}")
maskedA = A[pbA[0]:pbA[0]+0x827]
maskedB = B[pbB[0]:pbB[0]+0x827]
print(f"  masked chest bytes identical across seeds? "
      f"{'yes' if maskedA == maskedB else 'no'}")

# known-plaintext: a cheater who knows ONE real record (e.g. sees an item
# in play) recovers the pad at that offset.  how far does that reach?
db, dp = follow_shim(A, 0x015f2, 0xed8634)
# leak the first real 5-byte record; recover 5 pad bytes; can we decode
# the neighbour?  (only if the pad repeats - it must not)
first = next(iter(truth.values()))
off0 = next(off for (m, off) in truth if truth[(m, off)] is first)
pad_frag = bytes(A[db+off0+i] ^ first[i] for i in range(5))
# does this 5-byte pad fragment appear again anywhere in the pad region?
padregion = A[dp:dp+0x827]
repeats = sum(1 for i in range(len(padregion)-5) if padregion[i:i+5] == pad_frag)
print(f"  known-plaintext: 5 leaked pad bytes recur in the pad region "
      f"{repeats} time(s) (1 = only where they came from; no reuse)")
