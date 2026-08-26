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
| Esper spell teachings | **relocated (Phase 2)**: vanilla `0x186E00` holds a decoy | C3/59F6, C3/59FD, C3/5A2B, C3/5B7C, C3/5B8A (menu); C2/6032, C2/603C (spell + learn rate at battle end), C2/60E9 (level-up bonus) — 8 sites, all patched | `data/espers.py`; `-emi`'s mastered-icon code reads the table dynamically and takes `table_address()` | Medium |
| Enemy steals/drops | **relocated (Phase 2)**: vanilla `0xF3000` holds a decoy | C2/2C41 battle-init steal-slot load; C2/5F2D battle-end drop roll — 2 sites, both patched | `data/enemies.py` (`mod_loot()` extracted so the decoy re-runs exactly the loot pipeline) | Medium |
| Coliseum matches | **relocated (Phase 2)**: vanilla `0x1FB600` holds a decoy | C3/B237/B23E/B245 (opponent, reward, hide flag) — 3 sites, all patched; the battle receives the opponent through RAM | `data/coliseum.py`; `-crm`'s rewards-menu code reads the table dynamically and takes `table_address()` | Medium-High |
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

### L2 — Mask the relocated tables — **done (Phase 2b)**

Store relocated tables XORed with a position-dependent keystream
(from the per-purpose stream); each reader shim decodes on access —
per-record, at open/buy/grant frequency, a few dozen cycles at moments
where the game is already doing menu/dialog work.

- Kills: T2 scripts that find the moved tables by pointer-following but
  assume plaintext; forces a faithful decoder reimplementation.

Implementation notes (`obfuscation/mask.py`, `obfuscation/relocate.py`):

- Every relocated table gets an equal-size **pad** (`mask.pad_bytes`,
  domain-separated per table), placed independently inside the claim by
  the layout shuffle; the table is stored XORed with it.  One masking
  pass at the end of `Data.write()` transforms all six tables.
- All 28 vanilla reader sites are the 4-byte `LDA long,X`, so each is
  replaced by a same-size `JSL` to a shared per-(table, delta) shim:
  `LDA table+d,X : EOR pad+d,X : RTL` — X preserved, either accumulator
  width works, and the final EOR leaves exactly the N/Z flags a
  plaintext load would have set.  Shims live in bank F0.
- WC's own dynamically written readers decode inline via
  `relocate.read_asm()` (LDA+EOR), or `read_call_asm()` (space-neutral
  4-byte JSL) where the code sits in a fixed-size region (the `-crm`
  coliseum menu).
- **Chest pointer sentinel**: the map-load reader fetches one entry
  past the pointer table for the final map's end bound (contiguous
  data in vanilla, arbitrary claim neighbors after relocation).  The
  relocated table carries two extra bytes that decode to the final
  map's start bound, i.e. "no chests" — closing a latent Phase 1 edge
  case at the same time.
- Decoys at the vanilla addresses **stay plaintext by design** — their
  job is to be read.
- The pad is not cryptography and is not meant to be: an attacker who
  follows the JSL to the shim, extracts both operands, and XORs the
  two regions has decoded the table — but that attacker has written a
  faithful reimplementation of the game's reader, which is the L2
  bar.  Layout and keystream rotate per seed and per release.
  `tools/verify_race_build.py` implements exactly this attack as its
  verification path.

### L3 — Check-reward indirection — **items done (Phase 3a)**

The biggest prize for a cheater is "which check gives what."  Today the
information is operand bytes inside event scripts — greppable by opcode
pattern.  Route reward grants through a **single custom opcode** carrying
only an opaque index; the actual reward lives in one encoded table
(masked as in L2) and is decoded at grant time by one shared routine.
Phase it: items-at-checks first, then characters/espers.

Implemented (Phases 3a-3d).  The design point that matters most is that
**items and espers are deliberately indistinguishable**: knowing *which
checks hold espers* is most of the routing value even without knowing
which esper, so they share one table, one grant command and one
name-rendering control code, each dispatching on a kind byte decoded at
runtime.

- **One masked reward table** (`obfuscation/rewards.py`, claim entry
  `rewards`): 2 bytes per slot, `(kind, id)`.  Scripts carry only the
  opaque slot.
- **One grant command** `AddCheckReward` (`$9E`): decodes `(kind, id)`
  and runs either the vanilla add-inventory routine (`C0/ACFC`) or the
  vanilla AddEsper handler (`C0/ADB8`), so the owned-esper bit and the
  ESPERS_FOUND counter behave exactly as normal.  It also leaves the
  slot in `$0584` for a dialog that follows the grant.
- **One dialog command** `RewardDialog` (`$EE`): three bytes, so it drops
  onto a vanilla `Dialog` with no script shifting.  Its side-table entry
  holds the reward slot **and both wordings** — the "Received “X”!" and
  the "Received the Magicite “X.”" dialog ids — and the handler shows
  whichever matches the kind.  That keeps vanilla's two receive texts
  while making the *command* identical for either kind.  It decodes the
  reward itself, so it works whether the event grants before or after
  showing the text (both orders occur).
- **One control code pair**: `$1C <reward>` renders the reward whose slot
  is in `$0584`; `$1D <reward2>` renders the *next* slot, for the one
  dialog naming two rewards (the Narshe WOR choice, whose pair is
  registered consecutively — so no second ram byte is needed).  Both
  dispatch on kind to the esper name table (8-byte entries) or the item
  name table (13-byte, skipping the icon byte), the latter a faithful
  clone of vanilla's own `<item>` handler.
  `$0584` is "Spell Index for Dialog Window Display", documented unused
  in the US release; `$0583` is deliberately untouched because vanilla's
  `<item>` code and the chest-opening path use it.
- **Bespoke dialogs** that named a reward (Narshe WOR choice, Mobliz WOB
  injured lad, Mobliz WOR child lines, Lone Wolf taunt and "Got X!",
  Daryl's tomb inscription) all render at display time now.  Narshe WOR's
  wording is neutral in race builds ("Leave it “X”" for either kind) so
  the text does not betray the kind either; other builds keep the
  original line.
- **Start items are not obfuscated** (`AddItem(..., spoiler=False)`):
  the player has them before the first check, so hiding them buys
  nothing and they would crowd the one-byte slot space.
- Verified: an esper reward and an item reward at the *same* check
  produce byte-identical command bytes; the verifier additionally asserts
  that no per-kind opcode is installed at all (1623 checks).  Non-race
  output byte-identical; race builds boot and grant correctly.

- **Bespoke reward-naming dialogs — closed.**  Several events wrote
  their own text naming a reward (Narshe WOR choice, Mobliz WOB injured
  lad, Mobliz WOR child lines, Lone Wolf taunt and "Got X!", Daryl's
  tomb inscription).  All render at display time now, via `RewardDialog`
  where the dialog runs before the grant.  Lone Wolf's second reward was
  additionally granted by a *vanilla* `$80 AddItem` whose operand WC
  merely patched — a bare item id at a fixed address — now the opaque
  command.  Narshe WOR's wording is neutral in race builds so the text
  does not betray the kind either.  *Cosmetic*: Daryl's inscription is
  uppercase in vanilla; the runtime name uses the item's own casing.

- **Auction house — closed.**  Its tree held three leaks, two of them
  kind tells:
  1. the announcement named the reward *and* used a different wording per
     kind ("The Magicite, “X”!" against "“X”!").  Race builds use one
     wording and render the name at display time, at all four announce
     sites (reward1/reward2 × WOB/WOR).
  2. the receive subroutines were already closed by the unified grant and
     dialog commands — both kinds emit the same six commands.
  3. **the chest swap**: WC replaces the auction's magicite with a
     treasure chest *only for item rewards*, so simply diffing the event
     against vanilla said which kind an auction held.  Confirmed
     empirically (an esper seed left `C0/B532C` vanilla while an item
     seed patched in `Call(show_chest)`).  Race builds present every
     auction reward in a chest — the chest dialog is generic and the
     grant is a separate patch, so an esper reward works unchanged.
     *Visible change*: an esper won at auction arrives in a chest.

  Both kinds register the same number of reward slots, so slot numbering
  cannot shift by kind either.  The non-check auction items (Cherub Down,
  Cure Ring, Hero Ring, Zephyr Cape) render their names at display time
  too — no kind leak there, but they are randomized.

- **Veldt — surveyed, not yet built.**  It names its esper through
  `set_multi_line_battle_text`, i.e. the **battle** message engine.  A
  `<reward>` there is feasible and would closely mirror the field one:

  - Battle text has its own substitution mechanism: byte `$12` followed
    by a sub-code, dispatched at `C1/5EED` by `JMP ($5EF0,X)` over a
    four-entry table (actor / item / attack / command), each entry
    reading its parameter from ram `$2F35`.
  - Bank C1 already contains **both** printers such a code would need:
    item names at `C1/6048` and **esper names at `C1/5FEF`** (8 chars
    from `$E6F6E1`, entered with the esper id + `$36`, the same
    convention the field AddEsper handler uses).  The new sub-code is
    little more than "decode the slot, jump to the printer for its kind".
  - **Space constraint**: bank C1 has exactly **27 free bytes**
    (measured), and the `-fc` multisteal fix already writes there, so
    relocating the dispatch table into C1 would likely break `-fc`
    builds.  Zero-cost alternative: overwrite the existing 3-byte
    `JMP ($5EF0,X)` with a 4-byte `JML` into bank F0 (the fourth byte
    lands on the then-dead table), dispatch and decode in F0, and `JML`
    back to the vanilla printers — no C1 free space consumed.

  **What it would and would not buy.**  Veldt's reward is CHARACTER or
  ESPER — never an item.  Rendering the name hides *which* esper but not
  *that* it is one: the battle event picks dialog 182 for an esper
  against 254 for a character, and the two grant paths differ wholesale.
  The esper grant also bakes the id into ASM operands (`LDA #bit` /
  `TSB byte`, which together identify it) — a separate leak with its own
  fix.  Veldt therefore only closes fully alongside the character
  question, and is best done with it.

- **Character-at-check grants** — planned in detail below (§L3-C).

### L3-C — Characters at checks — **plan (Phase 3f, awaiting approval)**

Goal: hide *which character* each check grants from ROM inspection,
using the same unified reward machinery.  Player-visible behaviour is
unchanged — the check NPC still looks like the character you will get,
because the update happens at map load instead of at build time.
Scouting a check by walking up to it stays exactly as it is today;
what disappears is reading the placement out of the ROM bytes.

**The tells (survey, 2026-08).**  About 40 events can hold a
character.  Every one of them leaks identity through several channels
at once:

1. **Map NPC records** (`data/npc.py`): character checks bake
   `npc.sprite = character` and `npc.palette = get_palette(character)`
   into the map's NPC data block.  This is also a **kind tell** in the
   other direction: esper/item rewards at the same checks bake a
   *random* sprite from {Soldier, Imp, Merchant, Ghost}, so
   `sprite < 16` at a check NPC says "character here" with exact id.
2. **Script operands**: `RecruitCharacter` (`$76 xx`),
   `AddCharacterToParty`/`RemoveCharacterFromParties` (`$3F xx pp`),
   `SetName` (`$7F xx nn`), `SetProperties` (`$40 xx dd`),
   `CreateEntity` (`$3D xx`), `ShowEntity`/`HideEntity` (`$41/$42 xx`),
   `SetSprite`/`SetPalette` (`$37/$43`), and the entity **action
   queues**, whose opcode *is* the entity id (`$00-$34`) — for party
   characters the entity id equals the character id.  Several events
   additionally patch **raw id bytes into vanilla script addresses**
   (e.g. Mt. Kolts pokes eight single bytes so the vanilla Vargas
   scene animates the reward character).
3. **Dialog text**: a few events bake `get_name(character)` into
   dialog strings (Daryl's tomb inscription, Mobliz WOR lines).
   (Vanilla's own `<TERRA>`-style codes `$02-$0F` are *not* a leak —
   they render at runtime from WRAM `$1602` — but the code choice is,
   where WC picks it per reward.)
4. **Character theme**: `StartSong(get_character_theme(character))`
   bakes the song id; the char→song map is public knowledge, so the
   operand identifies the character.
5. **Veldt (battle side)**: picks battle dialog 182 (esper) vs 254
   (character), names the reward through battle text, and its esper
   grant bakes `LDA #bit / TSB byte` operands.  Surveyed above; closes
   together with this phase.
6. **Adjacent, decided separately**: character *gating* operands
   (`BranchIfEventBit(character_recruited(gate))`) reveal the gate
   assignment — different information (where a character is *required*,
   not obtained), cheap to note, separate decision.  **Starting
   characters stay plain** (mirror of the start-items rule: shown to
   the player in the first seconds, hiding them buys nothing).

**Design** (Hans's NPC-updater proposal, folded into the unified
reward table):

- **Kind `0x02` = character** in the one masked reward table
  (`obfuscation/rewards.py`); value = character id 0-15.  Same slot
  space, same registration discipline (equal slot counts per kind at
  multi-kind checks).
- **Grant**: a third branch in `AddCheckReward` (`$9E`): decode id →
  `STA $eb` → `JSL c0.recruit_character` — which already takes its
  argument in `$eb`, the same convention the esper branch uses.  The
  existing recruit path (recruited/available bits, `-sal` average
  level, magic/skill update) runs unchanged.
  `RecruitAndSelectParty` is already `RecruitCharacter` + a `Call` to
  a *shared, character-independent* party-select function, so only the
  `$76` operand needs replacing there.
- **Decoded-entity scratch + reward-entity command family.**  One new
  opcode `SetRewardEntity(slot)` decodes the slot's character id into
  a scratch RAM byte (candidate `$0585`, next to our `$0584`; confirm
  documented-unused first).  A small family of commands then reads the
  scratch byte where today's commands carry an id operand:
  - `UpdateRewardNpc(npc_id)` — **the NPC updater**: sets the map
    NPC's sprite and palette at runtime from the decoded id, palette
    via a char→palette table in ROM (public vanilla knowledge, fine in
    plaintext).  Runs in the map entrance event before fade-in, so the
    NPC looks exactly as it does today.
  - `CreateRewardEntity` / `ShowRewardEntity` / `HideRewardEntity` /
    `DeleteRewardEntity` — substitute the scratch id and jump into the
    vanilla `$3D/$41/$42/$3E` handlers.
  - `RewardEntityAct(queue...)` — vanilla dispatches action queues on
    the opcode itself; the new command loads the scratch id and enters
    that dispatch, replacing both WC-written queues and the raw-byte
    patches into vanilla scenes.
  - `AddRewardToParty(party)`, `SetRewardProperties`, `SetRewardName`
    — for `$3F/$40/$7F`, whose id-valued operands (character and, for
    these, the data/name index equal to it) both come from the scratch
    byte.
  - `PlayRewardTheme` — char→song table in ROM (public), decode →
    vanilla play-song path.
- **Names in text**: a kind-`0x02` branch in `<reward>`/`<reward2>`
  renders 6 chars from WRAM `$1602 + 37×id` — a clone of vanilla's own
  `$02-$0F` name-code handler (`C0/82CC`), so renamed characters
  render correctly for free.  Events that bake `get_name(character)`
  switch to `dialog_name()` like the item/esper events did.
- **NPC records**: character checks get the *same* build-time
  treatment as esper/item checks — a random sprite from the same pool
  — plus the runtime update.  That closes the identity tell and the
  `sprite < 16` kind tell in one move.

**Kind visibility — the honest limit and the decision to make.**
The per-kind scene *shapes* differ wholesale (recruit + party select
vs fade-out/grant/dialog), so a script diff still says *which checks
hold characters* even with every id hidden.  Two tiers:

- **Tier 1 (identity)**: everything above.  A cheater learns "this
  check is a character" but not which.
- **Tier 2 (kind)**: emit *both* scene fragments in every seed and
  select at runtime with a new `BranchIfRewardKind(slot, kind, dest)`
  command (decode-driven branch, same masked table).  Costs script
  space in banks CA-CC per event and real per-event surgery.

Recommendation: build the machinery Tier-2-capable from the start
(the branch command is small), convert **three archetypes first** —
Figaro Castle WOB (simple NPC + recruit), Mt. Kolts (raw-id-heavy
vanilla scene), one `RecruitAndSelectParty` event — measuring the
space and effort of full unification on each, then decide with that
data whether the remaining ~35 events get Tier 2 or Tier 1.  Single
pass per event either way; no planned rework.

**Veldt closes with this phase**: the battle `<reward>` sub-code
(`JML` to F0 over the dead dispatch table, per the survey above), one
shared battle dialog for both kinds, and the esper grant's baked
`LDA #bit / TSB` operands replaced by table-decoded code.

**Verification additions**: (a) same-check different-reward proof —
two seeds, same flags, character A vs character B (and, Tier 2,
character vs esper) at the same check produce byte-identical event
bytes and NPC records for that check; (b) verifier: no check NPC
record with `sprite < 16`, no `$76/$3F/$7F/$40` with id operands
inside converted events, scratch-byte commands installed; (c) the
usual non-race byte-identity A/B; (d) playtest kit for Hans: open
world, `-debug`, moogle charm, a recruit at each converted archetype.

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

### 6a. Red-team results (2026-08, `tools/verify_race_build.py`
attack path + scratch red-team script)

Against an L1+L2 race ROM, 296 real chests, how much each attack tier
recovers:

| Attack | What it does | Recovered |
|---|---|---|
| T1a fixed-offset scan | reads the vanilla addresses | **8%** — and that 8% is *noise, not signal*: 11 monster-in-a-box chests (these flags never randomize those, so real==decoy) plus ~12 accidental same-item collisions from the equal-distribution decoy. A naive tool sees a complete, plausible, mostly-wrong list. |
| T1b contiguity-follow (the FF6LE model) | follows the pointer operand, assumes records contiguous at +0x340 | **0%** — lands on masked neighbours/padding, obvious garbage |
| T2 operand-follow, no decode | follows to the true relocated table but reads it as plaintext | **0%** — the bytes are masked |
| T3 shim-follow + XOR decode | follows the reader JSL to its shim, extracts table+pad operands, XORs | **100%** — but this attacker has written a faithful reimplementation of the game's reader |

Structural properties confirmed:
- **Per-seed**: two seeds put the chest table and its pad at different
  claim offsets and produce non-identical masked bytes.  Nothing about
  the layout or keystream is fixed across ROMs.
- **No keystream reuse**: a leaked 5-byte plaintext record recovers 5
  pad bytes that appear nowhere else in the pad region — so a
  known-plaintext leak decodes only the record it came from, not its
  neighbours.  (The pad is a per-table PRNG stream, not a repeating
  key.)

**Interpretation.** The scheme does exactly what the threat model
claims and no more.  Everything below a full reader-reimplementation
(T1–T2) recovers nothing usable; the decoy actively feeds wrong data to
the laziest tools.  T3 succeeds by construction — any obfuscation the
CPU itself decodes can be decoded by an attacker who reimplements the
CPU's steps, and we deliberately chose not to fight that (no
anti-emulator tricks, no real crypto).  The security is the *cost* of
getting to T3 (find the JSL, follow it, model the shim, track table and
pad separately, per seed and per release) plus the process measures
(secret seed, post-race audit).

**Recommendation on L3/L4.** L3 (reward-script indirection) still buys
something L1/L2 do not: check rewards currently live in event-script
operands, a *different* data path this layer never touched, so they are
still greppable by opcode pattern and are the single highest-value
target.  L3 is worth doing.  L4 (per-seed allocation shuffle) is a
uniform multiplier on T3 effort — modest marginal value now that T3
already requires per-seed reverse engineering; recommend deferring it
until/unless a real T3 tool appears.  This matches ground rule "start
simple": ship L1+L2+L3, hold L4+ pending evidence.

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
- **In-play verification recipe** (for building test seeds): always add
  `-open` (open world) and `-smc 1` (a starting Moogle Charm) — open
  world lets any check be reached with whatever characters the seed
  started, instead of being blocked by character gating, and the charm
  skips encounters on the way there.  Then: use
  `-ccrt`/`-sirt` (records are runtime truth, unlike the runtime-scaled
  `-ccsr`); add `-stesp 21 21` to check every esper's spells in the
  menu; grant coliseum wager items with `-si <id.1.1...>` so matches can
  actually be bet (rewards need `-crm`; hidden ones still show `?`);
  there is no drop-rate flag, so use `-sca` (steal-always) to make the
  steal half of the loot table checkable and `-ss`/`-sd 100` to
  randomize; always add `-debug` so validation battles stay manageable.
  `-debug` also routes six item grants through the AddCheckItem opcode
  in the start event, so a harness boot smoke on a `-debug` race build
  dynamically exercises the L3 decode path at new game — run the boot
  smoke on a `-debug` build, not a plain one (a plain build booted fine
  while a register-width bug in the opcode handler crashed every
  `-debug`/start-item build at new game).

---

## 8. Sequencing

| Phase | Contents | Status |
|---|---|---|
| 0 | Reader inventory, tool census, nonce/RNG plumbing, `-race` skeleton, seed-in-menu fix, space budget | **done** (this branch) |
| 1 | L1 chests + shops (relocate + decoy) + in-game verification | **done** (verified in play 2026-08-24) |
| 2 | L2 masking; L1 extended to espers, enemy loot, coliseum | **done** (claim grown to 32 KB for the pads) |
| 2 (red-team) | attack L1+L2, document effort per tier (§6a) | **done** — T1/T2 recover nothing usable, T3 = reader reimpl; recommend ship L3, defer L4 |
| 3 | L3 reward indirection (items first, then characters/espers) | items, espers, kind-hiding, bespoke dialogs and the auction house **done** (3a-3e); characters + Veldt planned in §L3-C (Phase 3f, awaiting approval) |
| 4 | L4 allocation shuffle; community messaging | deferred pending a real T3 tool |
