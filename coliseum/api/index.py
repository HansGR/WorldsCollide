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
