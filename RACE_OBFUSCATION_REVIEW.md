# Race Obfuscation — Code Review (end of L3 phase)

*A review of the `-race` work on `feature/race-obfuscation`, written once
the functionality was playtest-clean.  Goal: simplify, make the design
more transparent, and reduce what the feature claims from WC's shared
resources — without making anything simpler than it can be.  Each item
states its effort, its risk, and what re-verification it needs.*

**Status.**  Everything in this review is now applied.  Batch 2 (the
resource reductions, landed after the first playtest pass): the reward
dialog is vanilla's `$4B` with operand bit 13 (`$EE` freed); the grant
and umbrella moved to `$E6`/`$FC`, the two-branch-free bytes; every
handler runs in bank F0 behind five 4-byte C0 stubs (~660 bytes of C0
returned); the claim is sized from its tables (~20 KB); Figaro WOB
uses the shared entrance repaint; the auction house registers one slot
per reward instead of six; `_bump_src` is one shared F0 routine.
Verified by the verifier and in-emulator (character and esper/item
paths through the new handlers), then re-playtested.

The byte-neutral items were applied first (§2.1 one slot-index
routine, §2.3 `obfuscation.reset_build()`, §2.4 event-layer helpers and
the Whelk entrance, §2.5 `instruction/field/race.py` +
`obfuscation/veldt_battle.py`, the slot-map tool and the developer
recipe from §2.2) — verified byte-identical against two race seeds and
the non-race build.  The resource reductions in §1 (fold `$EE` into a
`$4B` operand bit, run the handlers from bank F0, right-size the claim)
change the race ROM and wait for playtest sign-off.  Figaro Castle
WOB's hand-rolled entrance repaint is also left for that batch: its
block returns instead of chaining to the map's entrance, so unifying
it is not byte-neutral (and worth a look — see §2.4).

The branch is 45 commits, ~12 KB of source in `obfuscation/` plus
~900 lines in `instruction/field/race.py`, a 568-line verifier, and
race paths in 40 event files.  Structure is sound: keying → claim →
relocate → mask → reward table → three field opcodes → per-event
conversions → verifier.  The recommendations below are mostly
consolidation, not redesign.

---

## 1. Shared resources: what is claimed, and what could be given back

| Resource | Claimed today | Could be | How |
|---|---|---|---|
| Field opcodes | 3: `$9E` grant, `$EC` umbrella, `$EE` reward dialog | **2** | fold `$EE` into vanilla's `$4B` dialog via an unused operand bit (§1.1) |
| Bank C0 free space | ~700 bytes of handlers + 2 tables | **~40 bytes** | run handlers from bank F0 behind 4-byte C0 trampolines (§1.2) |
| Expanded-ROM claim | 32 KB at `0x340000` | **~20 KB**, or self-sized | tables + pads total 16.5 KB; the slack only randomises placement (§1.3) |
| Dialog control codes | `$1C` `<reward>`, `$1D` `<reward2>` | 2 (keep) | `<reward2>` is one branch of the same handler; folding it into an operand form buys nothing |
| Battle-text sub-codes | 4 and 5 (of `$12`) | 2 (keep) | the renderer's `<line>` is an engine code between them; merging would mean emitting line breaks from inside a handler |
| Bank C1 | 16 bytes of stubs | 16 (keep) | the `$12` dispatch table holds 16-bit C1 pointers, so entry points must be in C1 — this is already the minimum |
| RAM | `$0584` (one byte) | keep | documented unused since FF6j; the alternative is a WC scratch byte with its own lifetime rules |
| Event bits | multipurpose bit 0 | keep | that is what the multipurpose bits are for |
| Event-script space (CA–CC) | one relocated block per converted check | keep, trim (§2.4) | mostly irreducible; the receive triple is repeated ~35 times |

### 1.1 Fold `$EE` into `$4B` (frees an opcode)

`RewardDialog` exists as its own opcode only because it has to be
**three bytes** to drop onto a vanilla `$4B xx xx` site without shifting
the script.  Vanilla's `$4B` operand is a 16-bit word whose bits 14–15
carry the display flags and whose remaining 14 bits are the dialog id.
WC's highest dialog id is around 3000 (`0x0BB8`), so **bit 13
(`0x2000`) is never set** by any real dialog.  A four-instruction hook
at the head of the `$4B` handler (C0/A4BC) — `LDA $EC : AND #$20 : BNE
reward_path` — routes flagged operands to today's `$EE` code, which
already ends by jumping into that same handler.  Same size, same
semantics, no new opcode, and the verifier check that "$EE is
installed" becomes "the `$4B` hook is installed".

Effort: small (one hook, `RewardDialog` emits `4B` with bit 13 set,
side-table index moves into the low byte).  Risk: low — every reward
dialog already passes through `$4B`; the hook adds a two-instruction
test to every vanilla dialog.  Re-verify: verifier §7/§10 plus one
dialog of each kind in-emulator.

`$9E` cannot be folded the same way: it must be **two** bytes to
replace vanilla `$80 xx` / `$86 xx` in place, and neither operand space
has a free bit (items use all 255 ids).  `$EC` stays as the umbrella.
Net: 3 → 2 opcodes.

**Which two bytes — a collision found in review.**  "Unused by vanilla,
WC dev and the fork" was checked against the wrong branch: on this
branch `$9E` is also `SetYNPCGraphics` (`instruction/field/y_npc/`), so
`-race` with `-ymascot`/`-ycreature` fails the build with an opcode-table
space conflict today (loudly, thanks to `_set_opcode_address`'s
`Reserve`); and on `door_rando_ruin_rewrite`, the branch this feature
merges into, `$EC`/`$ED` are the ruination branch-recruit hooks.  Of the
21 vanilla-unused opcodes only **`$E6`, `$EE`, `$FC`, `$FF`** are free on
both branches.  So the opcode work is: fold the dialog into `$4B`
(frees `$EE`), then move the grant and the umbrella onto two of that
set — e.g. `$E6` grant, `$FC` umbrella — and update the verifier's
"not installed" list accordingly.  Lands with the other ROM-changing
items.

### 1.2 Move the handlers out of bank C0

Bank C0 free space is the scarcest thing in WC (dev, this fork and the
door randomiser all allocate there).  The race feature puts every field
handler in C0 because field opcodes dispatch through 16-bit C0
pointers.  But only the *entry* must be in C0: a 4-byte `JML` per
opcode (three) plus the name-code hook can trampoline into bank F0,
and the handlers already end in absolute jumps (`JMP $9B5C`,
`JMP $ADB8`, …) that become `JML $C0xxxx` unchanged in meaning.  The
handlers use direct-page (`$EB`–`$ED`) and bank-0 absolute addressing
(`$0584`, `$088C`, `$1EDC`…), which the data bank register still
resolves correctly from F0.  The two 16-byte lookup tables and the
`$EC` dispatch table move with them (the dispatch becomes
`JMP (table,X)` in F0).

Effort: medium — mechanical, but every `JMP abs` into vanilla becomes
a `JML`, and `_bump_src`/`_decode_*` are shared by all subs.  Risk:
medium, because it touches every reward command at once; the verifier
already follows each handler by address and would need its bank
assumptions updated.  Payoff: ~660 bytes of C0 returned.

While there: `_bump_src` is inlined into each of a dozen sub-handlers
(~10 bytes each).  A single shared "advance script pointer by 1"
subroutine called with `JSR` halves that even if the code stays in C0.

### 1.3 Right-size the claim

`claim.py` sums to 8,425 bytes of tables, doubled by the pads: 16.5 KB
inside a 32 KB reservation.  The 15.5 KB of slack exists only to
randomise each table's offset per seed, which defeats fixed-offset
tools; that property does not weaken with less slack.  Recommend
deriving `CLAIM_END` from the table total plus a fixed slack (4 KB is
plenty for 16 blocks), or simply setting it to `0x344fff` (20 KB).
Effort: one line.  Risk: none beyond re-running the verifier's claim
bounds check.  Note it *is* a behaviour change to the built race ROM
(placement changes), so it should land with the other rebuild items.

---

## 2. Simplifications and transparency

### 2.1 One slot-index routine (the B-high-byte rule in one place)

The `slot → X` sequence — `LDA slot : REP #$20 : AND #$00FF : ASL : TAX
: SEP #$20 : TDC` — is written out **four times**: `name_codes()`, the
`$9E` handler, the `$EE` handler, and `_slot_to_x_src()`.  The `TDC`
at its tail is the fix for the one serious playtest bug (slots ≥ 0x80
corrupting the vanilla handlers), and the verifier guards only the
`$9E` copy.  Have the three inline copies call `_slot_to_x_src()`, so
the invariant lives in one function and one verifier check covers
every consumer.  Effort: trivial.  Risk: none (byte-identical output).

### 2.2 Slot registration is a side effect of building instructions

`AddItem()`, `AddEsper()`, `AddItems()`, `reward_dialog()`,
`get_receive_dialog()` and `get_receive_esper_dialog()` all register a
reward slot at instruction-construction time.  That is what lets ~60
item/esper sites become opaque with no per-site code — the right
trade — but it is also exactly how the Lone Wolf slot-drift bug arose
(a kind-conditional build path registered "invisibly"), and it means
a slot number depends on Python evaluation order.  Two things make
this transparent without giving up the convenience:

- Keep the verifier's equal-count tripwire (added), and add a
  **slot map tool** (`tools/race_slot_map.py`, the instrumented-build
  script used to generate the playtest coverage list) so anyone can
  print `slot → (check, kind, id)` for a seed.  This is also the
  post-race audit tool the admin overview promises.
- Document in `obfuscation/rewards.py` that registration happens at
  construction time and that registering inside any kind- or
  seed-conditional path is forbidden.

### 2.3 Module-level build state

`rewards._rewards/_dialogs`, `claim._layout`, `relocate._shims`,
`custom._reward_entity_handler/_add_check_reward_handler/
_reward_dialog_handler/_name_codes/_character_palette_table`, and
`battle_reward` all hold once-per-build singletons.  Only
`rewards.reset()` exists.  A normal `wc.py` run is one process, so this
is harmless in production, but every in-process tool (tests, the slot
map tool, any future multi-seed generator) has to know the list.  Add
one `obfuscation.reset_build()` that clears all of them and is called
from `Data.__init__` where `rewards.reset()` is today.  Effort: small.

### 2.4 Event-layer boilerplate

Forty events carry the same three fragments.  None is wrong; together
they are ~150 lines that could be ~50 and, more importantly, they would
give each conversion one obvious shape:

- `from obfuscation import rewards; slot = rewards.register_check(
  self.reward)` — 40 sites, five of which had to move to the top of
  `mod()` because an earlier mod needed the slot.  A memoised
  `Event.race_slot(reward)` (register on first call, return the same
  slot after) removes the ordering hazard entirely.
- `npc.sprite = get_random_esper_item_sprite(); npc.palette =
  get_palette(npc.sprite); self.race_repaint_npc_entrance(map, id,
  slot)` — 26 sites.  A `race_decoy_npc(map_id, npc_id, slot, **arms)`
  helper does the three lines and reads as intent.
- Whelk and Figaro WOB (the first two conversions) hand-roll the
  entrance repaint with `UpdateRewardNpc` + `set_entrance_event`; every
  later event uses `race_repaint_npc_entrance`.  Convert the two
  originals so there is one way.
- `AddCheckReward(slot), PlaySoundEffect(141),
  receive_reward_dialog(slot)` — ~35 sites.  A
  `field.ReceiveCheckReward(slot)` triple.

The two-arm script itself (`BranchIfRewardKindNot … ESPER_ITEM`)
should **stay explicit** in each event: the arms differ in fades,
branch targets and displaced bytes, and hiding that behind a helper
would make the conversions harder to audit, not easier.

### 2.5 Naming and placement

- `obfuscation/veldt_battle.py` is Veldt-specific; `veldt_battle.py`
  says so.
- `custom.py` is 1,427 lines, of which the race part is ~870.  Moving
  the three opcodes and the name codes into `instruction/field/race.py`
  (re-exported through `field`) keeps `custom.py` as the WC-generic
  opcode module it was.
- `RACE_OBFUSCATION_PLAN.md` (796 lines) is the design history and
  should stay as such; the admin-facing `RACE_OBFUSCATION_OVERVIEW.md`
  is current.  What is missing is a **developer recipe**: "converting a
  check" as a checklist (register slot → decoy record → entrance
  repaint → two-arm script → what to look for: create-wipes-repaint,
  entrance-event flag, fades, kind-conditional registration) plus the
  verification steps.  Half of it already exists as the overview's
  sharp-edges list; it belongs in one developer section.

---

## 3. Things reviewed and deliberately left alone

- **XOR masking rather than anything stronger.**  Documented and
  correct: the decoder ships in the ROM, so nothing stronger buys
  anything against a faithful reimplementation, and the per-seed pads
  already defeat known-plaintext beyond the leaked bytes.
- **Decoys generated by the real randomisers under a separate RNG
  stream.**  The best part of the design; keep.
- **The `$EC` umbrella instead of one opcode per command.**  Vanilla
  has four free opcode bytes left; this is the only workable shape.
- **Plaintext palette and theme tables.**  Both are public knowledge.
- **`RewardDialogId(int)` smuggling the slot through existing
  `get_receive_dialog` callers.**  Slightly magical, but it is the
  reason zero non-race call sites changed; the docstring explains it.
- **Per-event race paths rather than a generic converter.**  Every
  check's vanilla script is different; the explicit arms are the
  audit trail.
- **The verifier's hard-coded addresses.**  A verifier *should* pin
  the addresses it checks.
- **Daryl's Tomb centring on the real name's width** leaks the
  reward name's *length* in the dialog spacing.  Narrow, but it is the
  one remaining static byte that varies with the reward.  Fixed-width
  centring costs a slightly off-centre inscription; worth deciding
  consciously rather than by default.

---

## 4. Suggested order

1. **Byte-neutral cleanups** (no rebuild needed for playtest): §2.1,
   §2.3, §2.4, §2.5.  Non-race identity and the verifier prove them.
2. **Resource reductions that change the race ROM**: §1.3 claim size,
   §1.1 `$EE` → `$4B` flag, then §1.2 handlers to F0.  Land together
   after playtest sign-off, with one more playtest pass over a few
   checks of each kind and the Veldt (the only battle-side path).
3. **Tooling**: the slot map tool and the developer recipe, alongside
   the release.
