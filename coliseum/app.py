#!/usr/bin/env python3
"""FF6 Coliseum - local development server.

Serves the static frontend from ``public/`` and the JSON API from ``core``.
In production on Vercel the static files are served by the CDN and the API by
``api/index.py``; both share the same ``core`` logic, so this file is only for
running locally:

    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:5000
"""
import os

from flask import Flask, jsonify, request, send_from_directory

import core

PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
app = Flask(__name__, static_folder=PUBLIC, static_url_path="")


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/api/pair")
def api_pair():
    pair = core.get_pair()
    return (jsonify(pair) if pair else (jsonify({"error": "not enough enemies"}), 500))


@app.route("/api/vote", methods=["POST"])
def api_vote():
    p = request.get_json(force=True, silent=True) or {}
    result = core.cast_vote(p.get("winner"), p.get("loser"),
                            voter=p.get("voter", ""), name=p.get("name", ""))
    return jsonify(result) if result else (jsonify({"error": "invalid pair"}), 400)


@app.route("/api/standings")
def api_standings():
    return jsonify(core.standings())


@app.route("/api/stats")
def api_stats():
    return jsonify(core.stats())


@app.route("/api/leaderboard")
def api_leaderboard():
    return jsonify(core.leaderboard())


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=True)
