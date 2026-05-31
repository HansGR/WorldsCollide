"""Vercel serverless function: patch an uploaded FF6 ROM in memory.

The browser POSTs a ``multipart/form-data`` body with two fields:

  * ``rom``    -- the raw .smc/.sfc bytes of an already-WC-patched ROM
  * ``config`` -- the ``ff6config.json`` text the configurator builds
                  (optional ``filename`` field names the download)

We run the same patching code path as ``ff6_config.py`` entirely in RAM and
stream the patched ROM straight back as the response body.  The uploaded ROM
is never written to disk and nothing is retained after the request returns --
the function is stateless and its filesystem is ephemeral regardless.

Vercel runs this via the ``handler`` BaseHTTPRequestHandler convention; the
shared ``config/`` package and ``ff6_config.py`` at the repo root are bundled
through the ``includeFiles`` entry in ``vercel.json``.
"""

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler

# The patching library lives at the repository root, one level up from /api.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ff6_config  # noqa: E402  (after sys.path tweak)

# Hard ceiling on the uploaded body.  Vercel's own request-body limit (4.5 MB
# on current plans) is stricter, but we guard here too so an oversized upload
# fails fast with a clear message instead of a generic platform error.  An FF6
# ROM is 3-4 MiB; 8 MiB leaves comfortable headroom for any expansion.
MAX_BODY_BYTES = 8 * 1024 * 1024


def _parse_multipart(content_type, body):
    """Split a multipart/form-data body into ``{name: bytes}``.

    Hand-rolled on the boundary bytes so binary ROM data survives intact
    (the stdlib's text-oriented parsers can mangle it).
    """
    m = re.search(r'boundary=("?)([^";]+)\1', content_type or "")
    if not m:
        raise ValueError("not a multipart/form-data upload")
    boundary = b"--" + m.group(2).encode("latin-1")

    fields = {}
    for segment in body.split(boundary):
        # Skip the preamble, the closing "--", and empty separators.
        segment = segment.strip(b"\r\n")
        if not segment or segment == b"--":
            continue
        head, sep, data = segment.partition(b"\r\n\r\n")
        if not sep:
            continue
        head_text = head.decode("latin-1", "replace")
        name = re.search(r'name="([^"]*)"', head_text)
        if not name:
            continue
        fields[name.group(1)] = data
    return fields


def _safe_filename(name, default="ff6_config.smc"):
    """Turn an uploaded ROM name into ``<base>_config.smc`` for the download."""
    if not name:
        return default
    base = os.path.basename(name)
    for ext in (".smc", ".sfc"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._") or "ff6"
    return f"{base}_config.smc"


class handler(BaseHTTPRequestHandler):
    # ---- helpers ----------------------------------------------------

    def _send_error(self, status, message):
        body = (message + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # ---- methods ----------------------------------------------------

    def do_OPTIONS(self):
        # CORS preflight (same-origin in normal use, but harmless to allow).
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self._send_error(
            405,
            "POST a multipart/form-data body with 'rom' (the .smc bytes) and "
            "'config' (ff6config.json) to patch a ROM.")

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send_error(400, "bad Content-Length")
        if length <= 0:
            return self._send_error(400, "empty request body")
        if length > MAX_BODY_BYTES:
            return self._send_error(
                413, f"upload too large ({length} bytes; max {MAX_BODY_BYTES})")

        body = self.rfile.read(length)

        try:
            fields = _parse_multipart(self.headers.get("Content-Type"), body)
        except ValueError as e:
            return self._send_error(400, f"could not read upload: {e}")

        rom_bytes = fields.get("rom")
        if not rom_bytes:
            return self._send_error(400, "missing 'rom' file in upload")

        config = None
        raw_config = fields.get("config")
        if raw_config:
            try:
                config = json.loads(raw_config.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as e:
                return self._send_error(400, f"invalid config JSON: {e}")
            if not isinstance(config, dict):
                return self._send_error(400, "config must be a JSON object")

        try:
            patched = ff6_config.patch_rom_bytes(rom_bytes, config)
        except ff6_config.ConfigError as e:
            return self._send_error(400, f"could not patch ROM: {e}")
        except Exception:  # pragma: no cover - unexpected, keep it a 500
            return self._send_error(500, "internal error patching ROM")

        filename = _safe_filename(
            (fields.get("filename") or b"").decode("utf-8", "replace"))

        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header(
            "Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(patched)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(patched)
