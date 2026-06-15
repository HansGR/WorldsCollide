# Add `-rc` / `--require-characters` challenge flag

## Summary

Adds a challenge flag that forces 1–4 specified characters to remain in the party
at all times.

```
-rc, --require-characters CHAR [CHAR ...]
```

## Behavior

### Flag

* Accepts 1 to 4 characters, validated against the playable roster
  (`terra, locke, cyan, shadow, edgar, sabin, celes, strago, relm, setzer, mog,
  gau, gogo, umaro`).
* Required characters are added to the seed flag string and participate in
  seeding.

### Interaction with the starting party (`-sc1`..`-sc4`)

Required characters are merged with the starting-character flags:

* A required character that is **not** already a starting character is added as
  an additional starting character.
* If no starting characters are specified, the required characters **constitute**
  the starting party.
* If the combined starting + required characters exceed four, the compile fails
  with a clear error.

The merged party is reflected back into the starting-character values, so menus,
logs, and the flag string all show the party that will actually start. The flag
string round-trips reproducibly.

### Forced into every party

Required characters are marked "unmovable" on every party-select screen. Per the
event-engine semantics, an unmovable character must already be placed in a party
or the player cannot place them — so required characters are also pre-placed into
a valid party before each select. Where more than one party is formed:

* **Two-party events (Narshe Battle, Phoenix Cave).** If at least one
  non-required character is available to fill the second party, all required
  characters go to party 1. If *every* available character is required, the last
  required character is placed in party 2 so neither party is forced empty
  (decided at runtime).
* **Kefka Tower (three parties).** Required characters are distributed across the
  three parties by entrance:
  * Normal entrance — party order `[3, 1, 2, 3]` for required characters 1–4.
  * Switches ("skip") entrance — party order `[2, 3, 1, 2]`.

## Implementation

* **`args/challenges.py`** — defines `-rc`, resolves names to ids, de-duplicates
  (preserving order), and computes the `SelectParties` "unmovable" bitmask.
* **`args/starting_party.py`** — merges required characters into the starting
  party (rules above).
* **`args/misc.py`** — frees the `-rc` short option, which had been an alias of
  the deprecated, always-on `--random-clock` (still available by its long name).
* **`instruction/field/instructions.py`** — `SelectParties`' default unmovable
  mask is derived from the required characters.
* **`instruction/field/required_characters.py`** *(new)* — helpers that generate
  the pre-placement event code (one-party, two-party split, three-party
  distribution). Located under `instruction.field` so the shared select-party
  subroutines can use it without a circular import.
* **`instruction/field/functions.py`** — the shared select-party subroutines now
  pre-place required characters:
  * `REFRESH_CHARACTERS_AND_SELECT_PARTY` and
    `REFRESH_CHARACTERS_AND_SELECT_TWO_PARTIES` pre-place before selecting.
  * The unused `REFRESH_CHARACTERS_AND_SELECT_THREE_PARTIES` is guarded so it
    fails loudly if ever used while characters are required (Kefka Tower performs
    its own distribution via raw `SelectParties`).
* **`event/airship.py`, `event/narshe_battle.py`, `event/phoenix_cave.py`,
  `event/kefka_tower.py`** — use the placement helpers / shared subroutines.

### Party-select pre-placement

`REMOVE_ALL_CHARACTERS_FROM_ALL_PARTIES` followed by a party select (e.g. the end
of the Narshe Battle, Narshe Moogle Defense, and every recruit-and-select event
via `RecruitAndSelectParty`) would leave required characters unmovable but outside
any party, which can softlock the party-select screen. Handling the pre-placement
inside the shared subroutines covers every current and future caller in one place
— 15 `REFRESH_CHARACTERS_AND_SELECT_PARTY` call sites in the ROM route through it.

## Testing

Built against `FFIII US v1.0` and decoded the generated event code:

* All configurations build: a single required character, required + starting
  characters, required-only full party, four required characters, and the no-flag
  default (unchanged output).
* The overflow case (starting + required > 4) fails cleanly.
* Verified `SelectParties` unmovable masks, the Kefka Tower normal/skip
  distributions, and the two-party split (including the single-required edge
  case and the "all available are required" branch).
* Verified the shared subroutines now embed pre-placement, and that the
  three-party guard raises when used.

Recommended in-game spot checks: the Narshe Battle end, Narshe Moogle Defense,
and a normal character recruitment with a required character active.
