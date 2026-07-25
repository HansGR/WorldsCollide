"""Phase 0 spike: prove the emulation stack end to end.

Boots a ROM headless, frame-steps, reads WRAM, exercises input,
savestates, determinism, and dumps screenshots.

Usage: python3 tools/playtest/spike.py <rom.smc> [screenshot_dir]
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.playtest.core import Core


def main():
    rom = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."

    t0 = time.time()
    core = Core(rom_path=rom)
    print(f"core loaded, fps={core.fps:.2f}, wram={core.wram_size:#x} bytes")
    assert core.wram_size == 0x20000, "expected 128KB SNES WRAM"

    # 1) boot 600 frames (~10s), measure speed
    t1 = time.time()
    core.run(600)
    dt = time.time() - t1
    print(f"600 frames in {dt:.2f}s = {600/dt:.0f} fps ({600/dt/60.1:.1f}x realtime)")

    nonzero = sum(1 for i in range(0, core.wram_size, 64) if core.wram[i])
    print(f"wram sampled nonzero bytes: {nonzero}")
    assert nonzero > 10, "WRAM looks empty -- emulation not running?"

    core.screenshot(os.path.join(outdir, "boot_600.png"))

    # 2) press START a few times to get past title
    for _ in range(4):
        core.buttons = {'START'}
        core.run(10)
        core.buttons = set()
        core.run(50)
    core.run(300)
    core.screenshot(os.path.join(outdir, "after_start.png"))

    # 3) savestate round-trip + determinism:
    #    save, run N frames, snapshot wram; load, run N frames, compare
    state = core.save_state()
    print(f"savestate size: {len(state):#x} bytes")

    core.run(120)
    wram_a = bytes(core.wram)

    core.load_state(state)
    core.run(120)
    wram_b = bytes(core.wram)

    if wram_a == wram_b:
        print("determinism: WRAM identical after state reload + 120 frames")
    else:
        diff = sum(1 for x, y in zip(wram_a, wram_b) if x != y)
        print(f"determinism: {diff} WRAM bytes differ after reload (investigate)")

    core.screenshot(os.path.join(outdir, "final.png"))
    print(f"total wall time: {time.time()-t0:.2f}s")
    print("PHASE 0 SPIKE OK")


if __name__ == "__main__":
    main()
