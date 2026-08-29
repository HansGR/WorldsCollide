# WC Race ROM Obfuscation — Overview

*What the `-race` flag does, for the admin team.  The full design
history and rationale live in `RACE_OBFUSCATION_PLAN.md`; this is the
"where it landed" summary.*

## What this is

Race seeds are played with **public flags, distributed ROMs, and a
secret seed**.  Under those rules the weak point has always been the
ROM file itself: anyone with a hex editor, an FF6 editor, or a small
script could read chest contents, shop stock, and check rewards out of
the file in seconds, because WC wrote them at well-known addresses in
plain form.

The `-race` flag closes that hole.  In a race build, every
spoiler-valuable table and reward is **moved, scrambled with a
per-seed mask, and replaced at its old address by a plausible decoy**.
The game decodes the real data at the moment it needs it (opening a
chest, entering a shop, collecting a check), so play is completely
normal — but the file no longer answers questions.  A tool that reads
the old addresses gets a complete, internally consistent, *wrong*
spoiler list; a tool that finds the new addresses gets scrambled
bytes.

Two properties are non-negotiable and preserved:

- **Without `-race`, nothing changes.**  Normal builds are verified
  byte-identical to builds made before this feature existed.
- **Races stay auditable.**  The same seed + flags + version always
  regenerates the byte-identical ROM and full spoiler log.  Revealing
  the seed after the race restores complete transparency.

## What it protects

| Data | Protection |
|---|---|
| Chest contents | moved + masked, decoy chest list at the old address |
| Shop stock | moved + masked, decoy shops at the old address |
| Esper spell teachings | moved + masked, decoy at the old address |
| Enemy steals & drops | moved + masked, decoy at the old address |
| Coliseum matches | moved + masked, decoy at the old address |
| Check rewards — items, espers, **and characters** | the biggest change: reward identities no longer appear in event scripts at all (see below) |
| The seed itself | hidden from the in-game menu; never written to the ROM in recoverable form |

Check rewards were the hardest and most valuable target.  In a normal
build, "this check gives Terra" is baked into the check's event script
in a dozen ways: the recruit command's operand, the NPC's sprite and
palette in the map data, the theme song that plays, the dialog text
that names the reward, and per-kind differences in the script's very
shape (a character check and an item check used to compile to visibly
different code).  In a race build every check compiles to **one
identical script regardless of what it holds**, carrying only an
opaque slot number into the same masked table.  The script contains
both the "recruit a character" scene and the "receive an esper/item"
scene and picks between them at runtime; names in dialogs are rendered
at display time; NPC appearances are applied at map load.  Two seeds
with different rewards at a check produce byte-identical bytes there
except for the meaningless slot number.

## What cheating it prevents — and what it cannot

Red-teamed against our own builds (effort tiers, measured):

| Attacker | Result |
|---|---|
| **Off-the-shelf tools** (FF6 editors, chest/shop viewers) reading the known addresses | Defeated — and worse for the cheater: they see the decoy, a plausible wrong answer, with no signal that it is wrong |
| **Script author** who finds the relocated tables and dumps them | Defeated — the bytes are masked with a per-seed, non-repeating pad; a leaked known value decodes only itself, not its neighbours |
| **Expert** who reimplements WC's own decode logic from source (find the patched reader, follow it to table + pad, XOR them, per seed and per release) | **Succeeds — unavoidably.**  The console must be able to decode the ROM, so a faithful reimplementation of the console's steps always works.  This is obfuscation, not encryption. |

So the honest claim is: casual and lazy cheating are eliminated or
actively misled; serious cheating is priced up from "run a tool" to
"maintain a per-release reverse-engineering project", and remains
detectable socially (a caught cheater cannot claim accident) and
procedurally (post-race seed reveal + regeneration audit).  Publicly
documenting that race ROMs contain decoys is part of the design: a
cheater who cannot trust what a tool tells them has lost most of the
value of cheating.

Out of scope, by design:

- **Playing ahead.**  Nothing stops someone privately playing the
  distributed ROM (or savestate-scumming through it) — that costs the
  same time as racing and is a race-procedure matter, not a file
  format one.
- **No anti-emulator or timing tricks.**  Race ROMs run on real
  hardware, flashcarts, and every mainstream emulator, exactly like
  normal builds.
- **Not hidden**: flags (public anyway), objectives, starting party
  and commands (all visible in-game within seconds), the debug room
  (`-debug` is a test flag), and door randomization (races don't use
  it; the same techniques apply if that changes).

## What players see in a race build

Almost nothing different — that was the bar.  Specifically:

- **Scouting works exactly as today.**  Walk up to a check and it
  looks right: a character check shows that character's sprite, an
  esper check shows the magicite shard, an item check shows the item
  object.  (The look is applied as the map loads instead of being
  baked into the file — indistinguishable in play, and confirmed
  pixel-identical in emulator tests.)
- Receive windows, recruit scenes, names, and party joins behave as
  in normal builds.
- The seed line is absent from the menu, and the generation log omits
  spoilers.

The complete list of *actual* gameplay-visible differences, all
cosmetic, all approved during development:

1. Four checks whose scenes only had room for a fixed song keep a
   vanilla/neutral song instead of the reward character's theme:
   Owzer's Mansion, Fanatic's Tower, Lone Wolf; the Opera House plays
   Setzer's theme for every reward.
2. Mobliz (WOR) does not have the reward character fight Phunbaba
   solo.
3. Mt. Zozo's letter to Lola is unsigned for every reward.
4. Trivia-level wording/pacing differences at a few checks (e.g. the
   Umaro carving uses one wording per reward kind selected at
   runtime).

## Shared resources this feature claims

For anyone planning future WC features — these are now taken (race
builds only, except where noted):

- **Field event opcodes `$9E`, `$EC`, `$EE`** (previously unused by
  vanilla, WC, and the fork).  `$9E` grants a reward from a slot,
  `$EE` shows a reward-naming dialog, and `$EC` is an umbrella command
  with 15 sub-commands covering everything a check scene does to a
  reward character (create/show/hide, sprite, palette, name, theme,
  party, action queues, a runtime kind-branch, and the special
  magicite/item-object look).  `$ED`, `$FC`, `$FF` remain free.
- **Dialog control codes `$1C`/`$1D`** repurposed as runtime
  reward-name substitutions in dialog text.
- **Battle-text substitution sub-codes 4 and 5** (of the `$12`
  substitution opcode), freed by relocating a small data block the
  battle text engine kept next to its dispatch table.
- **ROM space**: a 32 KB claim at file `0x340000–0x347FFF` (expanded
  area) for the relocated tables and their masks; handler code in the
  usual WC free space in banks C0/C2/F0; 16 bytes of bank C1's small
  free pool; event-script space in CA–CC for the rewritten check
  scenes.
- **RAM/flags**: one scratch byte (`$0584`, next to vanilla's dialog
  scratch) holding "the reward slot being processed"; WC's
  multipurpose event bit 0 as the runtime kind-branch flag; existing
  event bits (e.g. the Veldt's reward-obtained bit) reused with
  unchanged meaning.  No save-file (SRAM) changes.
- Two small **plaintext lookup tables** (character → palette,
  character → theme song).  Both are public information derivable
  from flags, so they leak nothing.

## Confidence

- `tools/verify_race_build.py`: ~1,700 automated checks per run —
  determinism, decoy plausibility, mask quality (no keystream reuse),
  every patched reader followed, per-check byte-identity between two
  seeds after blanking slot numbers, and regression guards for bugs
  found in playtesting.
- Non-race byte-identity is re-verified on every change.
- The unit test suite covers the obfuscation bookkeeping.
- In-emulator playtests (automated harness + human) cover chests,
  shops, esper/item/character check rewards of all kinds, the Veldt's
  in-battle grant, and the runtime NPC looks.

---

## Appendix: how each layer works (technical)

**Layer 1 — relocate + decoy.**  At build time the chest, shop, esper
teaching, enemy loot, and coliseum tables are written into the 32 KB
claim at per-seed offsets.  Every engine routine that read them (all
located and cited by SNES address in the plan document) is patched to
the new base.  The vacated vanilla addresses are refilled by running
the *same randomization code* with a decoy RNG stream, domain-separated
from the real one — so the decoy is statistically indistinguishable
from a real layout and cannot be correlated with it.

**Layer 2 — masking.**  Each relocated table is XORed with a pad of
equal length drawn from a per-seed, per-table RNG stream (nonces are
`hash(version, purpose, seed, flags)`; the seed never appears in the
ROM).  Readers go through small decode shims: load byte, XOR with the
pad byte, continue.  Decoding happens only at event-driven moments
(chest opened, shop entered, reward granted) — never per frame — so
there is no performance or hardware-compatibility impact.

**Layer 3 — check-reward indirection.**  All ~60 check rewards live as
`(kind, id)` pairs in one masked reward table; scripts reference them
by slot number only.  The `$9E` opcode decodes a slot and dispatches:
item → vanilla add-item, esper → vanilla add-esper, character → WC's
recruit routine.  The `$EE` opcode shows the right receive wording for
the decoded kind, and dialog codes `$1C`/`$1D` copy the decoded
reward's name (item name from ROM, esper name from ROM, character name
from save RAM so renames render) into the text as it draws.  The `$EC`
umbrella lets one script perform every character-scene action against
"the reward of slot N" without naming a character: its sub-commands
decode the id and jump into the corresponding vanilla handler with the
id placed where that handler's own operand would be.  A runtime
kind-branch sub-command drives vanilla's ordinary event-bit branches,
which is how one script carries both the character scene and the
esper/item scene.

**NPC appearance at runtime.**  A check's NPC record in the map data
is kind-neutral (a random generic sprite, or the vanilla object where
vanilla already had one).  As the map loads — before fade-in — the
entrance event repaints it: character rewards get the real character
sprite and palette decoded from the table; esper rewards get the
magicite shard; item rewards get the item object.  The shard/object
looks need one state byte the map loader normally derives from a
record flag, so an `$EC` sub-command pokes the equivalent state into
the live object.  Two checks (Doom Gaze, Tritoch) create their object
mid-scene rather than at map load, which resets it to the record's
look; their repaint runs between the scene's create and show commands
instead.

**The Veldt (battle side).**  The Veldt grants its reward inside a
battle, and battle event scripts have no conditionals — so the "fed
Dried Meat" battle event shows one fixed dialog whose text is just two
new battle-text substitution codes.  Their handlers decode the reward
table at display time and print either the magicite wording plus the
esper's name, or the character's "Uwaoo~!!", through the battle text
engine's own renderer.  The wild creature's sprite loader and the
recruit routine similarly decode kind and id at runtime; a character
joins the party through the same vanilla code a character build uses.

**Where code lives.**  Field-side handlers and the two plaintext
lookup tables sit in WC's normal bank C0 free space; the Veldt's
battle-side logic in bank C2; larger relocated handlers and the battle
dialog renderers in expanded bank F0, entered and exited through tiny
stubs in bank C1 (the battle program's bank, whose free space is
scarce).  All allocation goes through WC's existing managed free-space
system, so conflicts with future features fail the build loudly
instead of silently overwriting.

**Known sharp edges (for future developers).**

- Reward slot numbers are one byte and routinely exceed 128; any new
  handler computing `slot * 2` in 16-bit mode must clear the
  accumulator's high byte before running vanilla code (a missed clear
  here caused the one serious bug found in playtesting; the verifier
  now guards the pattern).
- The reward table entry order is `(kind, id)` — kind first.
- If a scene *creates* its reward NPC (`$3D`), any runtime repaint
  must happen after that create, not at map entrance.  Likewise, a
  scripted map load with the entrance-event flag off skips entrance
  events entirely — a scene entered that way needs its repaint inline
  after the load.
- Scripts that reserve over vanilla bytes must re-emit the fades those
  bytes performed (battles end faded out).
