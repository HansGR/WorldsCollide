"""Vercel serverless entry point (Python runtime).

Vercel detects the module-level WSGI ``app`` and serves it.  ``vercel.json``
rewrites every ``/api/*`` request here; the static frontend (``public/``) is
served directly by Vercel's CDN.

The core modules live at the project root, so add it to ``sys.path`` and make
sure they (plus the dataset) are bundled via ``includeFiles`` in vercel.json.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

import core

app = Flask(__name__)


def _owner_ok():
    """Gate ranking endpoints. If SHEETS_TOKEN is configured (production), a
    matching ?token=... is required; with no token set (local dev), allow."""
    secret = os.environ.get("SHEETS_TOKEN")
    return (not secret) or request.args.get("token") == secret


@app.route("/api/pair")
def api_pair():
    pair = core.get_pair()
    return (jsonify(pair) if pair else (jsonify({"error": "not enough enemies"}), 500))


@app.route("/api/vote", methods=["POST"])
def api_vote():
    p = request.get_json(force=True, silent=True) or {}
    result = core.cast_vote(p.get("winner"), p.get("loser"),
                            voter=p.get("voter", ""), name=p.get("name", ""))
    if result is None:
        return jsonify({"error": "invalid pair"}), 400
    if not result.get("ok"):
        return jsonify(result), 502          # storage failed
    return jsonify(result)


@app.route("/api/standings")
def api_standings():
    if not _owner_ok():
        return jsonify({"error": "forbidden"}), 403
    return jsonify(core.standings())


@app.route("/api/tierlist")
def api_tierlist():
    # Owner-only: view the ranking and (with ?write=1) push it to the Sheet.
    if not _owner_ok():
        return jsonify({"error": "forbidden"}), 403
    return jsonify(core.export_tierlist(write=request.args.get("write") in ("1", "true")))


@app.route("/api/stats")
def api_stats():
    return jsonify(core.stats())


@app.route("/api/leaderboard")
def api_leaderboard():
    return jsonify(core.leaderboard())


@app.route("/api/health")
def api_health():
    return jsonify(core.health(write_test=request.args.get("write") in ("1", "true")))


def _normalize_path(wsgi_app):
    """Make routing independent of how Vercel rewrites the request.

    Depending on whether the deployment uses Root Directory = ``coliseum``
    (rewrites) or = ``./`` (repo-root ``vercel.json`` builds/routes), the
    function may receive ``/api/pair`` or a prefixed variant. Normalise so Flask
    always sees the path from ``/api/`` onward.
    """
    def wrapped(environ, start_response):
        path = environ.get("PATH_INFO", "")
        idx = path.find("/api/")
        if idx > 0:
            environ["PATH_INFO"] = path[idx:]
        return wsgi_app(environ, start_response)
    return wrapped


app.wsgi_app = _normalize_path(app.wsgi_app)
