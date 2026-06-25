"""Tools for parsing a Ruination-mode spoiler log and rebuilding the
per-branch door map, including a renderer that reproduces the graphical
branch map that ruination mode emits during generation.

See ``ruination_spoiler/README.md`` for usage.

Public surface:
    from ruination_spoiler import parse_spoiler, build_branches, render_branches
"""

from .parser import parse_spoiler, SpoilerLog
from .reconstruct import build_branches, Branch

__all__ = [
    "parse_spoiler",
    "SpoilerLog",
    "build_branches",
    "Branch",
]
