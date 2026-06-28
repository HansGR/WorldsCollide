#!/usr/bin/env python3
"""Authoritative enemy export straight from a FF6 / WorldsCollide ROM.

The bundled ``data/enemies.json`` is seeded from the Caves of Narshe vanilla
bestiary (see ``build_dataset.py``).  This script instead reads the *actual*
game data through the WorldsCollide data classes, so the roster, stats and
membership flags stay correct for any ROM (including a randomized seed):

  * stats              - read from the enemy data table
  * is_boss            - from data/bosses.py
  * random_encounter   - the enemy appears in a formation reachable from a
                         random-encounter zone pack
  * coliseum           - the enemy is a coliseum opponent
  * world              - WOB / WOR / both (a coarse "where encountered" hint)

An enemy is ``include``d when it is a random encounter or a coliseum opponent
and is not a boss -- exactly the pool the tier list is meant to cover.

Run from the WorldsCollide repo root (so the data modules import):

    python coliseum/tools/export_from_rom.py /path/to/ff3.smc \
        --out coliseum/data/enemies.json
"""
import os
import sys
import json
import math
import argparse
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)            # coliseum/
WC_ROOT = os.path.dirname(PROJECT)         # repo root
sys.path.insert(0, WC_ROOT)


def slugify(name):
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def seed_power(e):
    durability = math.log10(max(e.hp, 1)) * 200
    offence = (e.vigor + e.magic) * 4
    defence = e.defense + e.magic_defense
    return durability + offence + defence + e.level * 8


def build(rom_path):
    from memory.rom import ROM
    from data.enemies import Enemies
    from data.enemy_packs import EnemyPacks
    import data.bosses as bosses

    rom = ROM(rom_path)
    # Only ``doom_gaze_no_escape`` is read during construction (everything else
    # lives in mod()); a tiny stub is enough to load all the data read-only.
    args = SimpleNamespace(doom_gaze_no_escape=False)
    enemies = Enemies(rom, args, items=[])

    # --- random-encounter enemy ids -------------------------------------
    random_ids = set()
    for zone in enemies.zones.zones:
        for pack_id, rate in zip(zone.packs, zone.encounter_rates):
            if pack_id in (0, EnemyPacks.VELDT, EnemyPacks.ZONE_EATER):
                continue
            pack = enemies.packs.packs[pack_id]
            for fid in pack.formations:
                formation = enemies.formations.formations[fid]
                for i, eid in enumerate(formation.enemy_ids):
                    if (formation.enemy_slots >> i) & 1:
                        random_ids.add(eid)

    # --- world (WOB / WOR) presence -------------------------------------
    def ids_in_zones(zone_slice):
        ids = set()
        for zone in zone_slice:
            for pack_id in zone.packs:
                if pack_id in (0, EnemyPacks.VELDT, EnemyPacks.ZONE_EATER):
                    continue
                for fid in enemies.packs.packs[pack_id].formations:
                    f = enemies.formations.formations[fid]
                    for i, eid in enumerate(f.enemy_ids):
                        if (f.enemy_slots >> i) & 1:
                            ids.add(eid)
        return ids

    z = enemies.zones.zones
    wob_ids = ids_in_zones(z[:enemies.zones.WOB_COUNT])
    wor_ids = ids_in_zones(z[enemies.zones.WOB_COUNT:enemies.zones.WOB_COUNT + enemies.zones.WOR_COUNT])

    # --- coliseum opponents (read the match table directly) -------------
    from data.match import Match
    COLISEUM_START, COLISEUM_COUNT = 0x1fb600, 256
    coliseum_ids = set()
    for i in range(COLISEUM_COUNT):
        match = Match(rom.get_bytes(COLISEUM_START + i * Match.DATA_SIZE, Match.DATA_SIZE))
        coliseum_ids.add(match.opponent)

    boss_ids = set(bosses.enemy_name) - set(bosses.removed_enemy_name)

    # --- carry sprites/locations over from the existing dataset ---------
    # ROM names use terse SNES labels ("Necromancr", "Areneid") that often
    # differ from the Caves of Narshe display names, so match exactly first,
    # then on a normalised key, then on a close fuzzy match.
    import difflib

    def normkey(s):
        import re
        return re.sub(r"[^a-z0-9]", "", s.lower())

    prior = {}
    prior_norm = {}
    existing = os.path.join(PROJECT, "data", "enemies.json")
    if os.path.exists(existing):
        for e in json.load(open(existing, encoding="utf-8")).get("enemies", []):
            if e.get("sprite") or e.get("sprite_cdn"):
                prior[e["name"]] = e
                prior_norm[normkey(e["name"])] = e
    norm_keys = list(prior_norm)

    def find_sprite(name):
        if name in prior:
            return prior[name]
        nk = normkey(name)
        if nk in prior_norm:
            return prior_norm[nk]
        close = difflib.get_close_matches(nk, norm_keys, n=1, cutoff=0.84)
        if close:
            return prior_norm[close[0]]
        if len(nk) >= 4:  # e.g. ROM "Chupon" -> CoN "Chupon (Colosseum)"
            for k in norm_keys:
                if k.startswith(nk) or nk.startswith(k):
                    return prior_norm[k]
        return {}

    records = []
    powers = []
    for e in enemies.enemies:
        if not e.name.strip():
            continue
        powers.append(seed_power(e))
    pmin, pmax = (min(powers), max(powers)) if powers else (0, 1)

    seen = {}
    for e in enemies.enemies:
        if not e.name.strip():
            continue
        is_boss = e.id in boss_ids
        is_random = e.id in random_ids
        is_coliseum = e.id in coliseum_ids
        if e.id in wob_ids and e.id in wor_ids:
            world = "WOB + WOR"
        elif e.id in wob_ids:
            world = "World of Balance"
        elif e.id in wor_ids:
            world = "World of Ruin"
        else:
            world = ""

        slug = slugify(e.name)
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 1

        p = seed_power(e)
        carry = find_sprite(e.name)
        records.append({
            "slug": slug,
            "name": e.name,
            "enemy_id": e.id,
            "sprite": carry.get("sprite"),
            "sprite_cdn": carry.get("sprite_cdn"),
            "type": "",
            "level": e.level,
            "hp": e.hp,
            "mp": e.mp,
            "exp": e.exp,
            "gil": e.gold,
            "strength": e.vigor,
            "magic_atk": e.magic,
            "defense": e.defense,
            "magic_def": e.magic_defense,
            "evasion": e.evasion,
            "magic_evade": e.magic_evasion,
            "location": world,
            "world": world,
            "is_boss": is_boss,
            "random_encounter": is_random,
            "coliseum": is_coliseum,
            "include": (is_random or is_coliseum) and not is_boss,
            "exclude_reason": "boss" if is_boss else ("" if (is_random or is_coliseum) else "not a random/coliseum enemy"),
            "seed_power": round(p, 1),
            "seed_rating": round(1200 + 700 * (p - pmin) / (pmax - pmin), 1) if pmax > pmin else 1500.0,
        })
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", help="path to a FF6 / WorldsCollide ROM")
    ap.add_argument("--out", default=os.path.join(PROJECT, "data", "enemies.json"))
    a = ap.parse_args()

    records = build(a.rom)
    out = {
        "source": f"WorldsCollide ROM export ({os.path.basename(a.rom)})",
        "count": len(records),
        "included": sum(1 for r in records if r["include"]),
        "enemies": records,
    }
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=2)
    print(f"Wrote {a.out}: {out['count']} enemies, {out['included']} included "
          f"(random/coliseum, non-boss)")


if __name__ == "__main__":
    main()
