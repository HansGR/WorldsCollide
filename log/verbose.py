"""Verbose diagnostic logging for ruin mode.

Provides vprint() for diagnostic output produced by data.doors, data.maps,
data.transitions, data.walks, data.warps, and event.ruination.

Destinations are chosen by init():
    -debug           -> stdout (legacy behaviour)
    -debug-verbose   -> temporary file that is appended to the spoiler log
                        at the end of the compile

Both flags may be combined. When neither is set, vprint() is a no-op.
"""

import os
import tempfile

_to_stdout = False
_to_file = False
_temp_file = None
_temp_path = None


def init(to_stdout=False, to_file=False):
    """Configure verbose destinations. Safe to call more than once."""
    global _to_stdout, _to_file, _temp_file, _temp_path
    _to_stdout = bool(to_stdout)
    _to_file = bool(to_file)
    if _to_file and _temp_file is None:
        _temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt",
            prefix="wc_debug_verbose_",
            encoding="utf-8",
        )
        _temp_path = _temp_file.name


def is_enabled():
    return _to_stdout or _to_file


def vprint(*args, **kwargs):
    """Print verbose diagnostic output to the configured destinations."""
    if _to_stdout:
        print(*args, **kwargs)
    if _to_file and _temp_file is not None:
        kwargs.pop("file", None)
        print(*args, file=_temp_file, **kwargs)
        _temp_file.flush()


def get_temp_path():
    return _temp_path


def finalize_and_append_to_log():
    """Close the temp file and append its contents to the spoiler log.

    Called at the end of the compile. No-op if the temp file was never
    created (e.g. -debug-verbose was not set).

    Writes via the ``logging`` module so the output is routed to whichever
    destination the log handler is configured with (file or stdout).
    """
    global _temp_file, _temp_path
    if _temp_file is None:
        return

    try:
        _temp_file.flush()
    except Exception:
        pass
    try:
        _temp_file.close()
    except Exception:
        pass

    path = _temp_path
    _temp_file = None
    _temp_path = None

    if path is None:
        return

    content = ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        content = ""
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if not content:
        return

    import logging
    header = " Debug Verbose Diagnostics "
    logging.info("")
    logging.info("-" * 120)
    logging.info(header.center(120, "-"))
    logging.info("-" * 120)
    # logging.info writes one record per call but embeds whatever string we
    # hand it - including newlines - so a single call with the full temp
    # file contents preserves the original line breaks.
    logging.info(content.rstrip("\n"))
