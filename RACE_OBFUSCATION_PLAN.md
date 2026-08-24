# Race ROM Obfuscation — Design Plan

*Status: Phase 0 implemented on `feature/race-obfuscation` (2026-08).
Later phases are proposals.*

Goal: make race seeds resistant to spoiler extraction — tools or scripts
that read the ROM file and reveal chest contents, check rewards, shop
stock, etc. before or during a race — while remaining fully playable on
real SNES hardware and every mainstream emulator.

Threat-model ground truth for real races (per community practice):
**the flags are public** (events use fixed, announced flagsets), **full
ROMs are distributed**, and **the seed is the only secret**, revealed
after the race.

---

## 1. What is achievable (read this first)

The SNES must be able to decode everything in the ROM with information
that is itself in the ROM.  Therefore **any obfuscation scheme is
reversible by a sufficiently determined attacker**, always.  There is no
cryptographic win available on an open platform with an open-source
generator.  What obfuscation *can* do is shift the cost curve:

| Tier | Attacker | Today | Achievable |
|---|---|---|---|
| T1 | Off-the-shelf tools (FF3usME, chest/shop viewers, generic FF6 editors) reading fixed vanilla addresses | Full spoilers in seconds | **Eliminated** — tools show plausible *wrong* data (decoys) |
| T2 | WC-aware script author: reads our source, pattern-scans for opcodes, follows pointers | Full spoilers with an evening's scripting | **Priced up** — must reimplement WC's per-seed decoder; per-release maintenance treadmill |
| T3 | Expert: full de-obfuscator built from WC source + in-ROM key material, or emulator automation (savestate, open every chest) | — | **Cannot be stopped.** Cost raised to real per-seed engineering; complemented by process measures (§7) |

The honest goal: *price out casual cheating, mislead lazy cheating, and
make serious cheating expensive, detectable, and socially risky.*  The
expectation (shared by the community discussion so far) is that almost
nobody exceeds T1 — which is why the plan starts simple and only adds
hardening if the red-team exercise (§6) shows it is needed.

Because WC is open source and deterministic, the scheme itself is
public.  Per-seed randomness is what keeps a public algorithm useful:
an attacker's tool must faithfully reimplement our decoder and chase us
across releases.  That treadmill is the mechanism, not secrecy.

Seed secrecy is sufficient key material: seeds are 12 characters of
`[a-z0-9]` (~2^62 possibilities) and each guess costs a full generation
run, so brute-forcing a seed from a ROM is not a realistic attack.
Nothing may ever write the seed (or anything derived from it that is
cheaply invertible) into the ROM in recoverable form.

---

## 2. Ground rules

1. **Hardware-safe.** Plain 65816 code and data only.  No timing
   tricks, no open-bus reads, no anti-emulator behavior — those punish
   legitimate players on flashcarts and niche emulators.  Decode work
   happens at event-driven moments (chest opened, shop entered, reward
   granted), never in per-frame hot paths.
2. **Deterministic and auditable.** All obfuscation is keyed by nonces
   derived from `hash(version, purpose, seed, flags)` via dedicated
   `random.Random` streams (see `obfuscation/`), so gameplay
   randomization is bit-for-bit unaffected by `-race`.  Same seed +
   flags + version → byte-identical ROM.  Post-race, the seed is
   revealed and anyone can regenerate the ROM and the spoiler log; this
   is the audit mechanism and must never be weakened.  Flags being
   public is assumed and costs nothing: the nonce is secret exactly as
   long as the seed is.
3. **Opt-in.** The `-race` flag gates everything.  Builds without it
   are byte-identical to a build without this feature.
4. **Decoys over deletion.** Wherever real data moves away from a
   vanilla address, *plausible fake data* takes its place — generated
   by running the same randomization code with a decoy-seeded RNG
   (domain-separated so it cannot correlate with the real layout).  A
   tool that "works" and lies quietly poisons the well for cheaters; a
   tool that errors invites fixing.  Space cost: zero — decoys occupy
   the bytes the real data vacated (measured budget in §5).
5. **Every reader shim is harness-verified.** The biggest risk is not
   attackers — it is missing one of the places the engine reads a table
   we moved.  Every phase ships with an automated headless-harness
   sweep (open chests, read shops, collect rewards) comparing in-game
   results against the generation plan.

---

## 3. Spoiler surface survey (Phase 0 findings)

Vanilla-engine readers below were located in the commented bank
disassemblies and are cited by SNES address; each needs its base
address parameterized (L1) and its value path shimmed (L2).

| Data | ROM location today | Vanilla readers (SNES) | WC-side readers/writers | Spoiler value |
|---|---|---|---|---|
| Chest contents | in place: ptrs `0x2D82F4`, records `0x2D8634` | C0/15D7 (map-load pass over the map's records, from C0/BF6A); C0/4BD4 (chest interaction: position match + contents/type read) | `data/chests.py`, `data/chests_asm.py` | High |
| Shop stock | in place: `0x47AC0` | C3/B9AF (item), C3/BA32 (flags), C3/BFF3 (flags) | `data/shops.py`; WC also writes fresh code each build that reads the table (empty-shop guard, `-sli` compaction in `data/shops.py` + `menus/buy.py`) — these take `obfuscation.relocate.shop_data_address()` so they follow the real table, and `-sli`'s hook replaces the C3/B9AF site outright (skipped by the reader patch) | High |
| Esper spell teachings | in place: `0x186E00` | C3/59F6, C3/59FD, C3/5A2B, C3/5B7C, C3/5B8A (menu + level-up screens); one C2 site (learn-rate at battle end) | `data/espers.py` | Medium |
| Enemy steals/drops | in place: `0xF3000` | C2 battle-init steal-slot load (→ `$3308`); C2 battle-end drop roll (`$CF3002/3`) | `data/enemies.py` | Medium |
| Coliseum matches | in place: `0x1FB600` | C3/B237 (opponent/prize display); battle-setup reader to confirm in Phase 1 | `data/coliseum.py` | Medium-High |
| Check rewards (characters/espers/items) | operands inside event scripts at WC-allocated addresses | event interpreter | event modules | **Highest** |
| Door / entrance maps | vanilla exit tables + WC data | field transition code | fork door modules | High, **deferred** — races currently don't use door randomization |
| Objectives, starting party, commands | various | — | — | None (visible in-game at start) |

Notes: the chest map-load pass appears to consume only
position/flag bytes; the contents/type bytes appear to be read only by
the interaction path — to be confirmed in Phase 1, since it decides how
few shims chest masking needs.  Phase 1 must also re-derive each
reader's *full* operand list (each routine references the table base
several times).

## Phase 0 status (implemented on this branch)

- **`-race` flag** (`args/settings.py`): included in the canonical flag
  string like any other flag (race flags are public); masks the seed as
  `hidden` in the in-game flags menu and the log settings section.
  (The seed was previously embedded as menu text in every non-`-hf`
  build — with public-flags races that alone would have defeated
  everything.)
- **`obfuscation/` module**: nonce derivation
  (domain- and length-prefixed SHA-256 over version, purpose, seed,
  flags) and dedicated per-purpose `random.Random` streams, plus
  decoy-stream derivation.  Unit-tested (`tests/test_obfuscation.py`),
  including that obfuscation streams never perturb the global gameplay
  RNG.
- **Space budget measured**: a maximal-flags build uses ~22 KB of the
  1024 KB expanded region (banks F0+); the tables slated for relocation
  total under 4 KB, and decoys reuse vacated bytes.  Space is a
  non-issue.
- **Reader inventory**: table above.

---

## 4. The layered plan

Ordered by value ÷ effort.  Each layer is independently shippable and
independently testable; later layers assume earlier ones.

### L1 — Relocate + decoy (chests, shops, espers, enemy loot, coliseum)

Move the real tables to nonce-derived addresses in expanded-ROM free
space; patch each reader's base-address operands (all reader sites are
inventoried in §3); write **decoy tables at the vanilla addresses**,
generated by re-running the same randomization with the decoy stream so
the fake data has exactly the right format and plausible distribution.

- Kills: every T1 tool, silently (they display the decoy).
- Chests and shops first, then espers, enemy loot, coliseum.
- Relocation targets come from the dedicated obfuscation RNG; the space
  is reserved up front so `-race` never shifts non-race allocations.

**Phase 1 status (chests + shops, implemented on this branch):**

- **Explicit space claim** (`obfuscation/claim.py`): a single reserved
  expanded-ROM range (`0x340000`–`0x343fff`, 16 KB; ~4 KB used) that all
  relocated tables live inside, every placement computed relative to
  `CLAIM_START`.  Per Hans's guidance re. collisions with the door
  randomizer's event pointers and external music randomizers, moving the
  claim is a one-line change and `Reserve()` makes any overlap with
  another feature fail loudly at build time.  Table order and offsets
  inside the claim are nonce-shuffled per seed.
- **Relocation** (`data/structures.py` `relocate()`; wired in
  `data/chests.py`, `data/shops.py`): the real chest pointer+data tables
  and the shop table move into the claim; the twelve chest reader
  operands (C0/15D7, C0/4BD4) and three shop reader operands (C3) are
  repatched via `obfuscation/relocate.py`, which asserts the exact
  vanilla operand bytes before overwriting.
- **Decoys**: a scratch data instance re-runs the *real* randomization
  under the decoy RNG (`run_with_decoy_rng`, which saves/restores the
  gameplay RNG state so not one gameplay draw is perturbed) and writes
  plausible fake tables at the vanilla addresses.  Decoys reuse the
  vacated bytes — zero net space.
- **Verification** (`tools/verify_race_build.py`): builds a control ROM
  and two race ROMs and runs 1278 assertions reading the ROM exactly as
  the C0/C3 hardware readers do — determinism (race builds byte-
  identical), control untouched (vanilla operands, empty claim), race
  operands agree on one relocated base inside the claim, relocated
  tables structurally match the control's fixed fields, and decoys parse
  identically but diverge in contents (268/296 chest records, most
  shops).  A build without `-race` is byte-identical to the branch base.
- **In-game verification (done, 2026-08-24)**: manual play verification
  on a `-race` build (seed NARSHEPROOF): all four Narshe shops and ~12
  opened chests matched the real (relocated) tables, cross-checked
  against the spoiler log and a ROM-side extraction via the patched
  operands.  Static verification and a dynamic boot smoke (the patched
  C0/15D7 reader on emulated hardware) also pass.
- **Tool census data point**: FF6LE on a race ROM shows the right chest
  *counts* per map but garbage records (random x/y/contents, many
  `0xFF`).  Signature analysis: it follows the game's pointer-table
  operand (so it finds the relocated pointer table) but assumes the
  records sit contiguously after it at +0x340, which vanilla satisfies
  and the shuffled claim layout doesn't.  The decoy at the vanilla
  addresses is provably well-formed (byte-identical to a control build
  in every fixed field), so fixed-address readers see the decoy, while
  half-smart operand-followers see obvious garbage — either way T1 is
  disabled.  Full operand-following yields real data until L2 masking
  lands.

### L2 — Mask the relocated tables

Store relocated tables XORed with a position-dependent keystream
(from the per-purpose stream); each reader shim decodes on access —
per-record, at open/buy/grant frequency, a few dozen cycles at moments
where the game is already doing menu/dialog work.

- Kills: T2 scripts that find the moved tables by pointer-following but
  assume plaintext; forces a faithful decoder reimplementation.

### L3 — Check-reward indirection

The biggest prize for a cheater is "which check gives what."  Today the
information is operand bytes inside event scripts — greppable by opcode
pattern.  Plan: route reward grants through a **single custom opcode**
carrying only an opaque index; the actual reward lives in one encoded
table (masked as in L2) and is decoded at grant time by one shared
routine.  Phase it: items-at-checks first, then characters/espers.

### L4 — Per-seed allocation shuffle

Randomize WC's free-space allocation layout per seed (within banks;
bank assignments unchanged) so all WC-generated code and data sit at
seed-dependent addresses — including L1's relocated tables and shims.

### L5 — Door map protection (**deferred**)

Races currently don't use door randomization.  Revisit if that changes;
the L1/L2 pattern applies to the exit tables when it does.

### L6 — Optional hardening (**not planned**)

Per community guidance, start simple: almost nobody is expected to
exceed T1.  Scheme families, record-order indirection, and split
storage stay in the back pocket; the red-team exercise (§6) decides if
any of it is ever worth building.  Note that keying includes the
generator version, so the concrete layout already rotates every release
for free.

---

## 5. What we deliberately will NOT do

- **Anti-emulator / timing tricks** — breaks legitimate players.
- **Encrypt code** — the CPU executes in place; 128KB WRAM cannot hold
  decrypted banks, and FF6 uses nearly all of it already.
- **Coprocessor carts (SA-1 etc.)** — changes the hardware target and
  fragments compatibility.
- **Real cryptography** — the generator is open source; AES buys
  nothing over XOR here.  The security is the per-seed nonce plus the
  reimplementation treadmill, either way.
- **Obfuscate hot-path data** (per-frame battle stats) or data visible
  in the first minute of play (starting party, objectives) — cost
  without benefit.
- **Rely on flag secrecy** — race flags are public.

---

## 6. Verification & red-team

1. **No-op isolation**: `-race` off → byte-identical output to a build
   of the same code without the feature; enforced by build comparison
   in CI/tests as the layers land.
2. **Harness sweeps** (per phase): scripted headless-emulator runs that
   open every chest, enter every shop, trigger sampled checks on a
   `-race` build, and diff observed results against the generation
   plan.
3. **Red-team milestone** (after L2): attack our own scheme — fixed
   offset scan, pointer-following, known-plaintext keystream recovery,
   WC-source-assisted decode — and document the effort each layer
   actually imposes.  Decides whether anything beyond L4 is worth it.
4. **Tool census**: demonstrate the actual community tools failing (or
   being deceived) on a race ROM, before/after.

---

## 7. Process measures that complete the picture

- **Seed secrecy discipline** (exists): hub-generated race seeds; seed
  and spoiler log withheld until race end.  Flags stay public as they
  are today.
- **Post-race audit** (exists, preserved by ground rule 2): reveal the
  seed; anyone regenerates the byte-identical ROM and full spoiler log.
- **Build identity**: the title-screen sprite hash already fingerprints
  seed+flags+version visually and is considered sufficient for stream
  auditing until proven otherwise.
- **Deterrence by uncertainty**: once shipped, document publicly that
  race ROMs contain per-seed obfuscation *and decoy data*.  A cheater
  who cannot trust the tool's output has lost most of the value of
  cheating.

---

## 8. Sequencing

| Phase | Contents | Status |
|---|---|---|
| 0 | Reader inventory, tool census, nonce/RNG plumbing, `-race` skeleton, seed-in-menu fix, space budget | **done** (this branch) |
| 1 | L1 chests + shops (relocate + decoy) + in-game verification | **done** (verified in play 2026-08-24) |
| 2 | L2 masking; L1 extended to espers, enemy loot, coliseum | next |
| 3 | L3 reward indirection (items first, then characters/espers) | |
| 4 | L4 allocation shuffle; red-team exercise; community messaging | |
