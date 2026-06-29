#!/usr/bin/env python3
"""Enrich the enemy dataset with Gamer Corner guide data.

The Gamer Corner FFVI guide (resources/monsters/*.html, saved into the repo)
is the most comprehensive per-monster source.  This script reads those pages
and merges the *non-scaling* combat data the tier-list UI needs onto the
existing ``data/enemies.json`` roster (which keeps its authoritative enemy_id /
include / membership flags from the ROM export):

  * location      - the "Encountered In" area(s)
  * bat_pwr       - Bat.Pwr   (physical attack)
  * mag_pwr       - Mag.Pwr   (magical attack)
  * defense       - Defense   (physical defense)
  * mag_def       - Mag.Def   (magical defense)
  * description   - the guide's short battle strategy note
  * (also: hit_rate, special effect, elemental weaknesses, and the guide's
    normalised 0-1 threat scores, kept for future use)

Match is by slug (ROM short-name), with a normalised/fuzzy fallback.

    python coliseum/tools/build_from_gamercorner.py
"""
import os
import re
import sys
import json
import glob
import html
import difflib
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)            # coliseum/
WC_ROOT = os.path.dirname(PROJECT)         # repo root
MON_DIR = os.path.join(WC_ROOT, "resources", "monsters")
DATA_PATH = os.path.join(PROJECT, "data", "enemies.json")


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


class MonsterPage(HTMLParser):
    """Pull label/value fields, the strategy note, and the page slug/name."""

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.fields = {}            # label -> [values]
        self.slug = None
        self.name = None
        self._cur = None            # 'label' | 'value' | 'note' | 'header'
        self._buf = ""
        self._last_label = None
        self.notes = []
        self._depth_note = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._depth += 1
        if tag in ("script", "style"):
            self.skip += 1
            return
        cls = a.get("class", "")
        if "data-path" in a and "/monsters/" in a["data-path"] and not self.slug:
            self.slug = a["data-path"].rsplit("/", 1)[-1]
        if tag == "span" and cls == "label":
            self._flush()
            self._cur = "label"
            self._buf = ""
        elif tag == "span" and cls == "value":
            self._flush()
            self._cur = "value"
            self._buf = ""
        elif tag == "div" and cls == "label":
            # some labels use div (e.g. section headers) - treat the same
            self._flush()
            self._cur = "label"
            self._buf = ""
        elif tag == "div" and "card-note" in cls and self._depth_note is None:
            self._flush()
            self._cur = "note"
            self._buf = ""
            self._depth_note = self._depth

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
            self._depth -= 1
            return
        if self._cur == "note" and self._depth_note is not None and self._depth <= self._depth_note:
            self.notes.append(re.sub(r"\s+", " ", self._buf).strip())
            self._cur = None
            self._buf = ""
            self._depth_note = None
        self._depth -= 1

    def handle_data(self, d):
        if self.skip or self._cur is None:
            return
        self._buf += d

    def _flush(self):
        if self._cur == "label":
            self._last_label = re.sub(r"\s+", " ", self._buf).strip()
        elif self._cur == "value" and self._last_label is not None:
            v = re.sub(r"\s+", " ", html.unescape(self._buf)).strip()
            if v:
                self.fields.setdefault(self._last_label, []).append(v)
        self._cur = None
        self._buf = ""


def _brief(text, max_len=200):
    """Trim a strategy blurb to the first sentence or two (<= ~max_len chars)."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for s in sentences:
        if out and len(out) + len(s) + 1 > max_len:
            break
        out = (out + " " + s).strip()
    if not out:                       # one very long sentence: hard cut on a word
        out = text[:max_len].rsplit(" ", 1)[0] + "…"
    return out


def first_int(values):
    for v in values:
        m = re.search(r"-?\d+", v.replace(",", ""))
        if m:
            return int(m.group())
    return None


def parse_page(path):
    p = MonsterPage()
    p.feed(open(path, encoding="utf-8", errors="replace").read())
    f = p.fields

    # Strategy note: the FIRST substantial blurb is the monster's own note
    # (later notes are walkthrough/compare cards, sometimes from other games),
    # trimmed to a brief 1-2 sentences for the card UI.
    note = ""
    for n in p.notes:
        if len(n) > 25:
            note = _brief(n)
            break

    raw = open(path, encoding="utf-8", errors="replace").read()

    # Gamer Corner's normalised 0-1 threat bars (HP, Physical Damage, Physical
    # Defense, Magic Defense) - a curated difficulty signal we use to seed.
    scores = {}
    mbars = re.search(r'data-bars="([^"]+)"', raw)
    if mbars:
        try:
            bars = json.loads(html.unescape(mbars.group(1)))
            for b in bars:
                name, h = b.get("name", ""), b.get("height")
                if h is None:
                    continue
                if name.endswith("HP"):
                    scores["hp"] = round(h, 3)
                elif name == "Physical Damage":
                    scores["phys_dmg"] = round(h, 3)
                elif name == "Physical Defense":
                    scores["phys_def"] = round(h, 3)
                elif name == "Magic Defense":
                    scores["mag_def"] = round(h, 3)
        except Exception:
            pass

    # Location: pull only the area-link texts from the "Encountered In" field,
    # so stray table text inside the field can't leak in (e.g. Cactrot).
    location = ""
    m = re.search(r'Encountered In</(?:span|div)>(.*?)</div>', raw, re.S)
    if m:
        areas = re.findall(r'/ffvi/areas/[^"]*"[^>]*>([^<]+)</a>', m.group(1))
        if not areas:  # plain-text areas (e.g. "World Map") with no link
            areas = [re.sub(r"<[^>]+>", "", m.group(1)).strip()]
        seen = []
        for a in areas:
            a = html.unescape(a).strip()
            if a and a not in seen:
                seen.append(a)
        location = "; ".join(seen)

    return {
        "slug": p.slug or os.path.splitext(os.path.basename(path))[0],
        "name": (f.get("__name__") or [None])[0],
        "location": location,
        "bat_pwr": first_int(f.get("Bat.Pwr", [])),
        "mag_pwr": first_int(f.get("Mag.Pwr", [])),
        "gc_defense": first_int(f.get("Defense", [])),
        "gc_mag_def": first_int(f.get("Mag.Def", [])),
        "hit_rate": first_int(f.get("Hit Rate", [])),
        "special": (f.get("Special", [None])[0]),
        "effect": (f.get("Effect", [None])[0]),
        "description": note,
        "scores": scores,
    }


# Multi-form monsters live in subdirectories (chupon/1.html, ...) whose pages
# only carry a "1"/"2" slug, so map our roster slugs to the right file by hand.
OVERRIDES = {
    "siegfried": "siegfried/2.html",     # the tough coliseum Siegfried
    "chupon": "chupon/1.html",
    "mag-roader": "mag-roader/1.html",
    "mag-roader-2": "mag-roader/2.html",
    "mag-roader-3": "mag-roader/3.html",
    "mag-roader-4": "mag-roader/4.html",
    "whelk-head": "whelk/2.html",
}


def _reseed(enemies):
    """Compute seed_rating from Gamer Corner's curated 0-1 threat scores.

    These (offense, durability, tankiness) are a much better starting point
    than enemy level. Magic offense isn't in the guide's bars, so we fold in a
    normalised Mag.Pwr so casters aren't undersold. Enemies the guide didn't
    cover keep their ROM-derived seed.
    """
    inc = [e for e in enemies if e.get("include")]
    mags = [e.get("mag_pwr") or 0 for e in inc]
    mmax = max(mags) if mags else 1

    def score01(e):
        s = e.get("gc_scores") or {}
        if not s:
            return None
        offense = s.get("phys_dmg", 0.0)
        magic_off = (e.get("mag_pwr") or 0) / mmax if mmax else 0.0
        durability = s.get("hp", 0.0)
        tankiness = (s.get("phys_def", 0.0) + s.get("mag_def", 0.0)) / 2.0
        return (0.34 * offense + 0.18 * magic_off +
                0.28 * durability + 0.20 * tankiness)

    scored = [(e, score01(e)) for e in inc]
    vals = [v for _, v in scored if v is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 1.0)
    for e, v in scored:
        if v is None:
            continue  # keep ROM-derived seed_rating from export_from_rom
        norm = (v - lo) / (hi - lo) if hi > lo else 0.5
        e["seed_rating"] = round(1250 + 600 * norm, 1)
        e["seed_power"] = round(v, 4)


WORLD_LABEL = {
    "World of Balance": "World of Balance",
    "World of Ruin": "World of Ruin",
    "WOB + WOR": "World of Balance & Ruin",
}


def _worldify(location, world):
    """Replace the guide's vague "World Map" with the WoB/WoR designation from
    the ROM's zone data (which world's overworld the enemy roams)."""
    if "World Map" not in location:
        return location
    label = WORLD_LABEL.get(world)
    if not label:
        return location                       # no ROM world info; leave as-is
    return location.replace("World Map", label)


def _fill_fallbacks(e):
    """Backfill display fields for enemies the guide didn't cover, using the
    ROM-derived stats already on the record."""
    if e.get("bat_pwr") is None:
        e["bat_pwr"] = e.get("strength")
    if e.get("mag_pwr") is None:
        e["mag_pwr"] = e.get("magic_atk")
    if not e.get("location"):
        if e.get("coliseum"):
            e["location"] = "Colosseum"
        elif e.get("world"):
            e["location"] = e["world"]
        elif e.get("random_encounter"):
            e["location"] = "Random encounter"
    if not e.get("description"):
        e["description"] = ""


def main():
    pages = {}
    for path in glob.glob(os.path.join(MON_DIR, "*.html")):   # top-level only
        rec = parse_page(path)
        pages[_norm(rec["slug"])] = rec

    data = json.load(open(DATA_PATH, encoding="utf-8"))
    page_keys = list(pages)

    matched = 0
    unmatched = []
    for e in data["enemies"]:
        key = _norm(e["slug"])
        if e["slug"] in OVERRIDES:
            rec = parse_page(os.path.join(MON_DIR, OVERRIDES[e["slug"]]))
        else:
            rec = pages.get(key) or pages.get(_norm(e["name"]))
            if not rec:
                close = difflib.get_close_matches(key, page_keys, n=1, cutoff=0.86)
                rec = pages[close[0]] if close else None
        if not rec:
            if e.get("include"):
                unmatched.append(e["name"])
                _fill_fallbacks(e)   # still give it ROM-derived stats + a label
            continue
        matched += 1
        e["location"] = rec["location"]
        e["bat_pwr"] = rec["bat_pwr"]
        e["mag_pwr"] = rec["mag_pwr"]
        _fill_fallbacks(e)
        # Prefer guide values for the displayed defenses; fall back to ROM.
        if rec["gc_defense"] is not None:
            e["defense"] = rec["gc_defense"]
        if rec["gc_mag_def"] is not None:
            e["magic_def"] = rec["gc_mag_def"]
        e["description"] = rec["description"]
        e["special"] = rec["special"] or rec["effect"] or ""
        e["gc_scores"] = rec["scores"]

    for e in data["enemies"]:
        if e.get("include"):
            e["location"] = _worldify(e.get("location", ""), e.get("world", ""))

    _reseed(data["enemies"])

    tag = " + Gamer Corner guide enrichment"
    if tag not in data.get("source", ""):
        data["source"] = data.get("source", "") + tag
    json.dump(data, open(DATA_PATH, "w"), ensure_ascii=False, indent=2)

    inc = [e for e in data["enemies"] if e.get("include")]
    have_loc = sum(1 for e in inc if e.get("location"))
    have_desc = sum(1 for e in inc if e.get("description"))
    print(f"Parsed {len(pages)} guide pages.")
    print(f"Matched {matched} enemies; included={len(inc)}, "
          f"with location={have_loc}, with description={have_desc}")
    if unmatched:
        print(f"Unmatched included enemies ({len(unmatched)}): {unmatched}")


if __name__ == "__main__":
    main()
