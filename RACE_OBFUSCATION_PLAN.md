# Race ROM Obfuscation — Design Plan

*Status: proposal for discussion (2026-08).  Nothing here is implemented.*

Goal: make race seeds resistant to spoiler extraction — tools or scripts
that read the ROM file and reveal chest contents, check rewards, shop
stock, door maps, etc. before or during a race — while remaining fully
playable on real SNES hardware and every mainstream emulator.

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
| T3 | Expert: full de-obfuscator built from WC source + in-ROM nonce, or emulator automation (savestate, open every chest) | — | **Cannot be stopped.** Cost raised to real per-seed engineering; complemented by process measures (§7) |

The honest goal: *price out casual cheating, mislead lazy cheating, and
make serious cheating expensive, detectable, and socially risky.*  The
community should understand this framing before we invest — anyone
promising more than this on SNES hardware is mistaken.

A second honest point: WC is open source and deterministic.  Any scheme
we write is public.  Per-seed randomness (a nonce) is what keeps a
public algorithm useful: the attacker's tool must faithfully
reimplement our decoder, and must chase us every time the scheme
changes.  That treadmill is the mechanism, not secrecy.

---

## 2. Ground rules

1. **Hardware-safe.** Plain 65816 code and data only.  No timing
   tricks, no open-bus reads, no anti-emulator behavior — those punish
   legitimate players on flashcarts and niche emulators.  Decode work
   happens at event-driven moments (chest opened, shop entered, reward
   granted), never in per-frame hot paths.
2. **Deterministic and auditable.** All obfuscation is keyed by a nonce
   derived from `hash(seed + flags)`, drawn from a **dedicated RNG
   stream** so gameplay randomization is bit-for-bit unaffected.  Same
   seed + flags + version → byte-identical ROM.  Post-race, the seed is
   revealed and anyone can regenerate the ROM and the spoiler log; this
   is the audit mechanism and must never be weakened.
3. **Opt-in.** A `-race` (or `-obf`) flag gates everything.  Non-race
   builds stay byte-identical to today (golden manifest untouched).
4. **Decoys over deletion.** Wherever real data moves away from a
   vanilla address, *plausible fake data* takes its place — generated
   by running the same randomization code with a decoy-seeded RNG.  A
   tool that "works" and lies quietly poisons the well for cheaters; a
   tool that errors invites fixing.
5. **Every reader shim is harness-verified.** The single biggest risk
   in this project is not attackers — it is missing one of the places
   the 30-year-old engine reads a table we moved.  Every phase ships
   with an automated headless-harness sweep (open every chest, read
   every shop, collect rewards) comparing in-game results against the
   generation plan.

Prerequisite already satisfied (verified 2026-08): the seed string is
**not** embedded in the ROM (it only feeds the RNG), and `-hf` already
suppresses the spoiler log and blanks the in-game flags menu.  Race
seeds must always be generated with `-hf` and a hub-held secret seed;
without that, an attacker regenerates the spoiler locally and nothing
else matters.

---

## 3. Spoiler surface survey

High-value targets, where they live today, and exposure (to be
completed/confirmed as Phase 0):

| Data | Location today | Format | Read by | Race spoiler value | Exposed to |
|---|---|---|---|---|---|
| Chest contents | vanilla table, in place (`0x2D82F4` ptrs / `0x2D8634` data) | vanilla | field chest-open code | High | T1 |
| Shop stock | vanilla table, in place (`0x47AC0`) | vanilla | shop menu loader (+ WC `-sli` machinery) | High | T1 |
| Esper spell teachings | vanilla table, in place (`0x186E00`) | vanilla | menu/level-up code | Medium | T1 |
| Enemy steals/drops | vanilla table, in place (`0xF3000`) | vanilla | battle engine | Medium | T1 |
| Check rewards (characters/espers/items) | operands inside event scripts at WC-allocated addresses | WC event code | event interpreter | **Highest** | T2 (opcode pattern scan) |
| Door / entrance map (`-drdc`, `-ruin`) | exit tables + event-exit runtime data | vanilla + WC | field transition code | **Highest** in door races | T1/T2 |
| Dragons, encounters, formations | vanilla tables, in place | vanilla | battle setup | Low–Medium | T1 |
| Objectives, starting party, commands | various | — | — | None (visible in-game at start) | — |

Phase 0 must also inventory **all readers** per table (the engine often
has more than one — e.g. anything that counts, previews, or re-reads
records) and survey the community's actual current tools so we can
demonstrate each one failing/deceived afterward.

---

## 4. The layered plan

Ordered by value ÷ effort.  Each layer is independently shippable and
independently testable; later layers assume earlier ones.

### L1 — Relocate + decoy (chests, shops, espers, enemy loot)

Move the real tables to nonce-derived addresses in expanded-ROM free
space; patch each reader's pointer/absolute address (WC already owns
patching machinery for all of these areas); write **decoy tables at the
vanilla addresses**, generated by re-running the same randomization
with `RNG(nonce ‖ "decoy")` so the fake data has exactly the right
format and plausible distribution.

- Kills: every T1 tool, silently (they display the decoy).
- Effort: moderate — mostly reader inventory + address parameterization.
  Chests and shops first (highest value; WC already has custom ASM in
  both areas), then espers, then enemy loot.
- Note: relocation targets must come from the dedicated obfuscation RNG
  and the space must be reserved before normal allocation so `-race`
  builds don't shift non-race allocations.

### L2 — Mask the relocated tables

Store relocated tables XORed with a position-dependent keystream
(cheap PRNG over `nonce ‖ address`; a 256-byte substitution box is an
equally good alternative).  Each reader shim decodes on access —
per-record, at open/buy/grant frequency, so the runtime cost is a few
dozen cycles at moments where the game is already doing menu/dialog
work.

- Kills: T2 scripts that find the moved tables by pointer-following but
  assume plaintext; forces a faithful decoder reimplementation.
- Effort: small once L1's shims exist — the decode drops into the same
  hook points.

### L3 — Check-reward indirection

The biggest prize for a cheater is "which check gives what."  Today the
information is operand bytes inside event scripts — greppable by opcode
pattern (T2).  Plan: route reward grants through a **single custom
opcode** carrying only an opaque index; the actual reward lives in one
encoded table (masked as in L2) and is decoded at grant time by one
shared routine.

- Kills: opcode-pattern scanning; concentrates the secret in one table
  with one decoder.
- Side benefit: a unified reward table simplifies future features and
  spoiler-log generation.  Ruination mode already has unified `Reward`
  slots — L3 generalizes that pattern to the open-world modes.
- Effort: the largest single item; touches many event files, but
  mechanically (replace inline grants with the opcode).  Phase it:
  items-at-checks first, then characters/espers.

### L4 — Per-seed allocation shuffle

Randomize WC's own free-space allocation layout per seed (shuffle
placement *within* each bank; bank assignments unchanged).  Every piece
of WC-generated code and data then sits at seed-dependent addresses.

- Kills: "meta-tools" that hardcode *WC's* layout per release —
  including tools that would try to find L1's relocated tables by
  looking where WC "usually" puts them, and tools that pattern-match
  our shim code to follow its operands.  (Pattern-matching code bodies
  still works — see §1; this raises effort, not a wall.)
- Effort: small-to-moderate, contained in `memory/`: permute free
  ranges / randomize start offsets from the obfuscation RNG.  Risk:
  reveals any latent assumptions about allocation adjacency — which the
  full test battery will catch, and which are worth flushing out
  anyway.

### L5 — Door map protection (`-drdc` / `-ruin` races)

Door destinations are the entire spoiler for door-rando races.  The
exit tables are vanilla-format and in place today.  Apply L1+L2 to the
exit/entrance tables and the event-exit connection data.  This is the
most entangled area (runtime event-exit updates, WoR copies, one-way
tables) and should come after the pattern is proven on chests/shops.

### L6 — Optional hardening (decide after red-team)

Only if the red-team exercise (§6) shows they're worth it:

- **Scheme families**: several mask/permutation variants; the nonce
  selects one per table.  A de-obfuscator must implement all variants.
- **Record-order shuffle with indirection**: store records in
  nonce-permuted order with an encoded index (chests within maps, shops
  within the table).
- **Split storage**: interleave record fields across distant regions.

Each adds shim complexity for diminishing returns; none changes the
tier-T3 ceiling.

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

---

## 6. Verification & red-team

1. **Golden isolation**: `-race` off → byte-identical to today; the
   16-config golden manifest never includes `-race`.
2. **Harness sweeps** (per phase, in `tools/playtest/`): scripted runs
   that open every chest, enter every shop, trigger sampled checks and
   doors on a `-race` build, and diff the observed results against the
   generation plan.  These become part of the standing regression gate
   for race builds.
3. **Red-team milestone**: after L2, we attack our own scheme — write
   the best meta-tool we can (fixed-offset scan, pointer-following,
   known-plaintext keystream recovery, WC-source-assisted decode) and
   document the effort each layer actually imposes.  L6 decisions and
   the community-facing honesty statement both come from this.
4. **Tool census**: before/after demonstration against the actual
   community tools identified in Phase 0.

---

## 7. Process measures that complete the picture

Obfuscation only covers the ROM file.  These cost little and multiply
its value:

- **Hidden seed discipline** (exists): hub-generated race seeds, seed
  and spoiler withheld until race end, `-hf` mandatory.  Never accept a
  player-supplied flag string for a race.
- **Post-race audit** (mostly exists): reveal seed + flags; anyone
  regenerates the byte-identical ROM and full spoiler log.
- **Build identity on screen**: WC's title sprite hash already gives a
  visual build fingerprint; ensure race builds surface it (and/or a
  short nonce-derived code on the pregame screen) so a moderator can
  match a player's stream against the issued seed at a glance.
- **Deterrence by uncertainty**: publicly document that race ROMs
  contain per-seed obfuscation *and decoy data*.  A cheater who cannot
  trust the tool's output has lost most of the value of cheating —
  this psychological layer is arguably the strongest one and costs a
  forum post.

---

## 8. Suggested sequencing

| Phase | Contents | Ships when |
|---|---|---|
| 0 | Survey: reader inventory per table, community tool census, nonce/RNG plumbing, `-race` flag skeleton | short |
| 1 | L1 chests + shops (relocate + decoy) + harness sweeps | first visible win: all T1 tools defeated |
| 2 | L2 masking; L1 extended to espers + enemy loot | |
| 3 | L3 reward indirection (items first, then characters/espers) | biggest prize protected |
| 4 | L4 allocation shuffle; red-team exercise; honesty statement to community | |
| 5 | L5 door tables (door-rando races) | |
| 6 | L6 hardening, only as justified by red-team findings | |

## 9. Open questions (for Hans / community)

1. Which modes actually race enough to matter?  (Decides L5 priority.)
2. Distribution format for race seeds — full ROM vs BPS patch?  (Decoys
   and relocation grow patches somewhat; no blocker either way.)
3. Is a visible pregame "race code" wanted for stream auditing, or is
   the existing sprite hash sufficient?
4. Appetite for the maintenance treadmill: are we content updating the
   scheme per release, or should scheme-family selection (L6) be built
   in early?
5. Should the decoy spoiler be *deliberately discoverable* wrong data,
   or should we keep silent about which layer a given tool is hitting?
   (Both are defensible; affects the community messaging.)
