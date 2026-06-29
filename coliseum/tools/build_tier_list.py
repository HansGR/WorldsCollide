#!/usr/bin/env python3
"""Export the crowd-sourced ranking as a tier list.

Reads votes through whichever backend the app uses (Sheets / Postgres / SQLite),
replays them via ``core`` to get the live Glicko ratings + tiers, and writes:

    data/tier_list.json   - ordered list with rating, rd, tier
    data/tier_list.md     - human-readable S/A/B/... table

Tiers are bottom-heavy (see core.TIER_PROPORTIONS): most enemies aren't that
dangerous, so the lower tiers are the largest.

    python tools/build_tier_list.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, PROJECT)

import json
import core

PROVISIONAL_RD = 150.0   # above this deviation the placement is not yet settled


def main():
    data = core.standings()
    rows = data["standings"]
    total_votes = data["total_votes"]
    if not rows:
        raise SystemExit("No enemies found. Check data/enemies.json.")

    ordered = []
    for e in rows:
        ordered.append({
            "rank": e["rank"], "slug": e["slug"], "name": e["name"], "tier": e["tier"],
            "rating": e["rating"], "rd": e["rd"], "comparisons": e["comparisons"],
            "provisional": e["rd"] > PROVISIONAL_RD,
            "atk": e["atk"], "matk": e["matk"], "dfn": e["dfn"], "mdef": e["mdef"],
            "location": e["location"], "coliseum": e["coliseum"],
        })

    json.dump({"total_votes": total_votes, "enemies": ordered},
              open(os.path.join(PROJECT, "data", "tier_list.json"), "w"),
              ensure_ascii=False, indent=2)

    lines = ["# FF6 Coliseum Tier List", "",
             f"_Based on {total_votes} head-to-head votes. "
             f"\\* = provisional (still uncertain)._", ""]
    for label, _ in core.TIER_PROPORTIONS:
        members = [e for e in ordered if e["tier"] == label]
        if not members:
            continue
        lines += [f"## {label} Tier", "",
                  "| Rank | Enemy | Rating | ± | Votes | ATK | M.ATK | DEF | M.DEF | Found |",
                  "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|"]
        for e in members:
            star = "\\*" if e["provisional"] else ""
            cell = lambda v: "" if v is None else v
            lines.append(
                f"| {e['rank']} | {e['name']}{star} | {e['rating']} | {e['rd']} | "
                f"{e['comparisons']} | {cell(e['atk'])} | {cell(e['matk'])} | "
                f"{cell(e['dfn'])} | {cell(e['mdef'])} | {e['location']} |")
        lines.append("")
    open(os.path.join(PROJECT, "data", "tier_list.md"), "w").write("\n".join(lines))

    print(f"Exported {len(ordered)} enemies across "
          f"{len({e['tier'] for e in ordered})} tiers from {total_votes} votes.")
    print("  -> data/tier_list.json\n  -> data/tier_list.md")


if __name__ == "__main__":
    main()
