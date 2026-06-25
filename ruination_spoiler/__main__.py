"""Command line entry point.

    python -m ruination_spoiler <spoiler.txt> [-o map.png] [--no-image]

Parses a ruination-mode spoiler log, prints a per-branch reachability /
softlock report, and (unless ``--no-image``) renders the branch map to PNG.
"""

import argparse
import os
import sys

from .parser import parse_spoiler
from .reconstruct import build_branches
from .analyze import analyze_branch, format_report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ruination_spoiler",
                                 description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spoiler", help="path to the ruination spoiler log (.txt)")
    ap.add_argument("-o", "--output", default=None,
                    help="output PNG path (default: <spoiler>_branch_map.png)")
    ap.add_argument("--no-image", action="store_true",
                    help="only print the text report, do not render a PNG")
    args = ap.parse_args(argv)

    log = parse_spoiler(args.spoiler)
    if not log.is_ruination():
        print("warning: this log does not look like a ruination seed "
              "(no -ruin flag); attempting anyway.", file=sys.stderr)
    if not log.has_verbose:
        print("warning: no 'Debug Verbose Diagnostics' section found; branch "
              "reconstruction relies on it. Re-run the seed with -debug-verbose "
              "for a complete map.", file=sys.stderr)

    branches = build_branches(log)
    reports = [analyze_branch(b) for b in branches]

    print("Seed: %s" % log.seed)
    print("Starting party: %s" % ", ".join(log.starting_party))
    print()
    print(format_report(reports))

    if not args.no_image:
        out = args.output
        if out is None:
            base = os.path.splitext(args.spoiler)[0]
            out = base + "_branch_map.png"
        try:
            from .render import render_branches
        except ImportError as exc:  # pragma: no cover
            print("\ncannot render image (%s); install networkx and matplotlib "
                  "or pass --no-image." % exc, file=sys.stderr)
            return 1
        render_branches(branches, log, out, reports=reports)
        print("\nBranch map written to %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
