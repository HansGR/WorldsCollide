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


@app.route("/api/pair")
def api_pair():
    pair = core.get_pair()
    return (jsonify(pair) if pair else (jsonify({"error": "not enough enemies"}), 500))


@app.route("/api/vote", methods=["POST"])
def api_vote():
    p = request.get_json(force=True, silent=True) or {}
    result = core.cast_vote(p.get("winner"), p.get("loser"))
    return jsonify(result) if result else (jsonify({"error": "invalid pair"}), 400)


@app.route("/api/standings")
def api_standings():
    return jsonify(core.standings())


@app.route("/api/stats")
def api_stats():
    return jsonify(core.stats())


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
