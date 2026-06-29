#!/usr/bin/env python3
"""Export the crowd-sourced ratings as an ordered tier list.

Reads the live ratings from ``votes.db`` (written by app.py) and the display
data from ``data/enemies.json``, then emits:

    data/tier_list.json   - ordered list with rating, rd, tier
    data/tier_list.md     - human-readable S/A/B/... table

Tiers are cut on the Glicko rating.  Enemies that have not yet received enough
comparisons (high rating deviation) are flagged ``provisional`` so they are not
mistaken for settled placements.

Usage:
    python tools/build_tier_list.py
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, PROJECT)
DATA_PATH = os.path.join(PROJECT, "data", "enemies.json")

# (label, minimum rating).  Mirror the thresholds used in the web UI.
TIERS = [("S", 1750), ("A", 1600), ("B", 1480), ("C", 1360), ("D", 1240), ("E", 0)]
PROVISIONAL_RD = 150.0   # above this deviation the placement is not yet settled


def tier_for(rating):
    for label, lo in TIERS:
        if rating >= lo:
            return label
    return TIERS[-1][0]


def main():
    names = {e["slug"]: e for e in json.load(open(DATA_PATH, encoding="utf-8"))["enemies"]}

    # Read ratings from whichever backend the app uses (SQLite or Postgres).
    from storage import get_store
    store = get_store()
    ratings = store.all_ratings()
    if not ratings:
        raise SystemExit("No ratings found. Run app.py and collect votes first.")
    total_votes = store.vote_count()

    ordered = []
    for rank, slug in enumerate(sorted(ratings, key=lambda s: ratings[s]["rating"], reverse=True), 1):
        r = ratings[slug]
        meta = names.get(slug, {})
        ordered.append({
            "rank": rank,
            "slug": slug,
            "name": meta.get("name", slug),
            "tier": tier_for(r["rating"]),
            "rating": round(r["rating"]),
            "rd": round(r["rd"]),
            "comparisons": r["n"],
            "provisional": r["rd"] > PROVISIONAL_RD,
            "location": meta.get("location", ""),
            "atk": meta.get("bat_pwr"),
            "matk": meta.get("mag_pwr"),
            "dfn": meta.get("defense"),
            "mdef": meta.get("magic_def"),
            "coliseum": meta.get("coliseum", False),
        })

    json.dump(
        {"total_votes": total_votes, "enemies": ordered},
        open(os.path.join(PROJECT, "data", "tier_list.json"), "w"),
        ensure_ascii=False, indent=2,
    )

    # Markdown
    lines = [f"# FF6 Coliseum Tier List", "",
             f"_Based on {total_votes} head-to-head votes. "
             f"\\* = provisional (still uncertain)._", ""]
    for label, _ in TIERS:
        members = [e for e in ordered if e["tier"] == label]
        if not members:
            continue
        lines.append(f"## {label} Tier")
        lines.append("")
        lines.append("| Rank | Enemy | Rating | ± | Votes | ATK | M.ATK | DEF | M.DEF | Found |")
        lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for e in members:
            star = "\\*" if e["provisional"] else ""
            def s(v):
                return "" if v is None else v
            lines.append(
                f"| {e['rank']} | {e['name']}{star} | {e['rating']} | {e['rd']} | "
                f"{e['comparisons']} | {s(e['atk'])} | {s(e['matk'])} | {s(e['dfn'])} | "
                f"{s(e['mdef'])} | {e['location']} |"
            )
        lines.append("")
    open(os.path.join(PROJECT, "data", "tier_list.md"), "w").write("\n".join(lines))

    print(f"Exported {len(ordered)} enemies across "
          f"{len({e['tier'] for e in ordered})} tiers from {total_votes} votes.")
    print("  -> data/tier_list.json")
    print("  -> data/tier_list.md")


if __name__ == "__main__":
    main()
