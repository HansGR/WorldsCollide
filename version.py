__version__ = "1.4.4d"


def git_commit():
    """Short commit id of the generating checkout, or None when
    unavailable (release archives, missing git binary, not a repo).
    Logged next to the version so any seed can be re-rolled at the exact
    code state that produced it: the RNG stream is deterministic per
    seed + flags, but the map also depends on the code consuming it."""
    import os
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=here, capture_output=True, text=True, timeout=5)
        if out.returncode != 0 or not out.stdout.strip():
            return None
        commit = out.stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=here, capture_output=True, text=True, timeout=5)
        if dirty.returncode == 0 and dirty.stdout.strip():
            commit += "+"      # uncommitted changes: not re-rollable as-is
        return commit
    except Exception:
        return None
