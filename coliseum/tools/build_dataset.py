#!/usr/bin/env python3
"""Build the FF6 Coliseum enemy dataset from a saved Caves of Narshe bestiary.

Input  : a directory of the "Save Page As (complete)" HTML dump of
         https://www.cavesofnarshe.com/ff6/enemies.php?ff6mode=snes
         (the 14 ``*.htm`` pages plus their ``*_files`` asset folders).
Output : coliseum/data/enemies.json   - structured, web-ready enemy records
         coliseum/static/sprites/*.png - one sprite per enemy

This is the *draft* data path so the site runs without a ROM.  For the
authoritative roster (which enemies are truly random encounters / coliseum
opponents in a given WC build) use ``tools/export_from_rom.py`` instead, which
reads the same fields straight out of the game data.

Usage:
    python tools/build_dataset.py /path/to/FF6_enemies
"""
import os, re, sys, json, glob, html, shutil
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)

# ----------------------------------------------------------------------------
# Curated default roster decisions.
#
# The Caves of Narshe bestiary contains "every enemy and boss", so we drop the
# clear bosses / scripted-event / un-fightable entries that are NOT part of the
# random-encounter or coliseum pools.  Everything else defaults to included.
#
# These are intentionally easy to edit: flip ``include`` in enemies.json, or
# regenerate authoritatively from a ROM with export_from_rom.py.
# ----------------------------------------------------------------------------
DEFAULT_EXCLUDE = {
    "Guardian (Invincible)": "invincible scripted boss",
    "Doom Drgn":             "dragon-tier boss",
    "Leader":                "scripted Imperial boss",
    "Merchant":              "scripted event enemy (Mt. Koltz)",
    "Naughty":               "boss",
    "Piranha":               "scripted boss (Lete River)",
    "Zone Eater":            "special swallow enemy, not a normal fight",
    "Siegfried":             "scripted event NPC (the coliseum Siegfried is 'Siegfried (2)')",
}

# Coliseum-flavoured opponents present in the bestiary that we want to KEEP and
# tag, even though they read boss-ish.  (Authoritative tagging comes from the
# ROM exporter; this is a best-effort hint for the draft.)
COLISEUM_HINTS = {"Chupon (Colosseum)", "Siegfried (2)", "Dark Force"}

STAT_KEYS = [
    "type", "level", "hp", "mp", "gil", "exp",
    "strength", "magic_atk", "evasion", "defense", "magic_def", "magic_evade",
]


class BestiaryParser(HTMLParser):
    """Linearise the page into an ordered event stream we can segment."""

    def __init__(self):
        super().__init__()
        self.events = []
        self.capture = None
        self.buf = ""
        self.div_stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            cls = a.get("class", "")
            self.div_stack.append(cls)
            if cls in ("tabletitletext", "tabletoptext", "tablemaintext"):
                self.capture = cls
                self.buf = ""
        elif tag == "img":
            self.events.append((
                "img",
                a.get("src", ""),
                a.get("data-original", ""),
                a.get("title", "") or a.get("alt", ""),
            ))
        elif tag == "br" and self.capture:
            self.buf += " / "

    def handle_data(self, data):
        if self.capture:
            self.buf += data

    def handle_endtag(self, tag):
        if tag == "div" and self.div_stack:
            cls = self.div_stack.pop()
            if self.capture and cls == self.capture:
                self.events.append((self.capture, re.sub(r"\s+", " ", self.buf).strip()))
                self.capture = None
                self.buf = ""


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def to_int(s, default=0):
    m = re.search(r"-?\d+", s or "")
    return int(m.group()) if m else default


def parse_pages(src_dir):
    parser = BestiaryParser()
    pages = sorted(glob.glob(os.path.join(src_dir, "*.htm")),
                   key=lambda f: to_int(re.search(r"_(\d+)\.htm", f).group(1)))
    if not pages:
        sys.exit(f"No *.htm pages found under {src_dir!r}")
    for pg in pages:
        parser.feed(open(pg, encoding="utf-8", errors="replace").read())

    ev = parser.events
    title_idx = [i for i, e in enumerate(ev) if e[0] == "tabletitletext"]

    records = []
    seen = {}
    for n, ti in enumerate(title_idx):
        block = ev[ti:title_idx[n + 1] if n + 1 < len(title_idx) else len(ev)]
        name = html.unescape(block[0][1])

        # The enemy sprite is the first lazyloaded img (data-original -> /bestiary/).
        sprite_src = sprite_cdn = None
        for e in block:
            if e[0] == "img" and "bestiary" in (e[2] or ""):
                sprite_src = os.path.basename(e[1].replace("%20", " "))
                sprite_cdn = e[2]
                break

        vals = [e[1] for e in block if e[0] == "tablemaintext"]
        stat_vals = vals[:12]
        rec = {"name": name}
        for key, raw in zip(STAT_KEYS, stat_vals):
            rec[key] = raw if key == "type" else to_int(raw)

        # Disambiguate duplicate names (the two "Soldier" entries).
        slug = slugify(name)
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 1
        rec["slug"] = slug
        rec["_sprite_src"] = sprite_src
        rec["sprite_cdn"] = sprite_cdn
        records.append(rec)
    return records, src_dir


def seed_power(rec):
    """A transparent vanilla 'threat' estimate used only to seed the ranking.

    Deliberately a blend of level, durability and offence -- NOT level alone --
    because some enemies (Orog, Outsider, Intangir, ...) punch far above their
    level.  Crowd votes are expected to dominate this seed (it ships with a
    large rating deviation), so the exact weights are not critical.
    """
    import math
    hp = max(rec["hp"], 1)
    durability = math.log10(hp) * 200                      # ~0..940
    offence = rec["strength"] * 4 + rec["magic_atk"] * 4   # raw attack power
    defence = rec["defense"] + rec["magic_def"]
    lvl = rec["level"] * 8
    return durability + offence + defence + lvl


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if not src_dir or not os.path.isdir(src_dir):
        sys.exit("Usage: python tools/build_dataset.py /path/to/saved/FF6_enemies")

    records, src_dir = parse_pages(src_dir)

    # Copy sprites and finalise records.
    sprite_dir = os.path.join(PROJECT, "static", "sprites")
    os.makedirs(sprite_dir, exist_ok=True)
    files_dirs = sorted(glob.glob(os.path.join(src_dir, "*_files")))

    powers = [seed_power(r) for r in records]
    pmin, pmax = min(powers), max(powers)

    enemies = []
    missing_sprites = []
    for rec, power in zip(records, powers):
        sprite_out = None
        if rec["_sprite_src"]:
            found = None
            for d in files_dirs:
                cand = os.path.join(d, rec["_sprite_src"])
                if os.path.exists(cand):
                    found = cand
                    break
            if found:
                ext = os.path.splitext(found)[1] or ".png"
                sprite_out = f"{rec['slug']}{ext}"
                shutil.copyfile(found, os.path.join(sprite_dir, sprite_out))
            else:
                missing_sprites.append(rec["name"])

        excluded = rec["name"] in DEFAULT_EXCLUDE
        enemy = {
            "slug": rec["slug"],
            "name": rec["name"],
            "sprite": sprite_out,
            "sprite_cdn": rec["sprite_cdn"],
            "type": rec["type"],
            "level": rec["level"],
            "hp": rec["hp"],
            "mp": rec["mp"],
            "exp": rec["exp"],
            "gil": rec["gil"],
            "strength": rec["strength"],
            "magic_atk": rec["magic_atk"],
            "defense": rec["defense"],
            "magic_def": rec["magic_def"],
            "evasion": rec["evasion"],
            "magic_evade": rec["magic_evade"],
            "location": "",  # not in bestiary; populated by export_from_rom.py
            "coliseum": rec["name"] in COLISEUM_HINTS,
            "include": not excluded,
            "exclude_reason": DEFAULT_EXCLUDE.get(rec["name"], ""),
            # Seed rating: map normalised power onto a Glicko-ish 1200..1900 band.
            "seed_power": round(power, 1),
            "seed_rating": round(1200 + 700 * (power - pmin) / (pmax - pmin), 1),
        }
        enemies.append(enemy)

    out = {
        "source": "Caves of Narshe FF6 bestiary (SNES) + WorldsCollide curation",
        "count": len(enemies),
        "included": sum(1 for e in enemies if e["include"]),
        "enemies": enemies,
    }
    out_path = os.path.join(PROJECT, "data", "enemies.json")
    json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=2)

    print(f"Wrote {out_path}: {len(enemies)} enemies, {out['included']} included")
    print(f"Sprites -> {sprite_dir}")
    if missing_sprites:
        print(f"WARNING: {len(missing_sprites)} sprites not found: {missing_sprites[:8]}...")


if __name__ == "__main__":
    main()
