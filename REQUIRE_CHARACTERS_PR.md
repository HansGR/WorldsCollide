# Add `-rc` / `--require-characters` challenge flag

Forces 1–4 specified characters to stay in the party at all times.

```
-rc, --require-characters CHAR [CHAR ...]
```

## Behavior

* Accepts 1–4 characters from the playable roster; included in the seed flags.
* **Starting party:** required characters merge with `-sc1`..`-sc4`. Any not
  already a starting character are added; if none are given, the required
  characters become the starting party. More than four total fails the compile.
* **Every party select:** required characters are marked unmovable and pre-placed
  into a party (an unmovable character must already be in a party or it can't be
  placed). For multi-party events:
  * **Two parties** (Narshe Battle, Phoenix Cave): all required go to party 1,
    unless every available character is required, in which case the last one goes
    to party 2 so neither party is empty.
  * **Kefka Tower** (three parties): distributed by entrance — normal `[3,1,2,3]`,
    skip `[2,3,1,2]`.

## Implementation

Pre-placement lives in the shared select-party subroutines
(`instruction/field/functions.py`), so every caller — including
`RecruitAndSelectParty` and the `RemoveAll`→select events (Narshe Battle end,
Moogle Defense) — is handled in one place and can't softlock. Supporting helpers
are in the new `instruction/field/required_characters.py`; the unmovable mask and
starting-party merge are in `args/`. `-rc` is freed from the deprecated
`--random-clock` (still usable by long name).

## Testing

Built against `FFIII US v1.0`; decoded the generated event code to verify the
unmovable masks, party distributions, the two-party split (including the
all-required edge case), and a clean failure on overflow. Suggested in-game
checks: Narshe Battle end, Moogle Defense, and a recruitment with a required
character active.
