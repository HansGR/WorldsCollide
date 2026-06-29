"""Append-only vote storage.

The app keeps no server-side rating state: it stores a chronological **vote
log** and recomputes ratings by replaying it (Glicko replay over N votes is a
few milliseconds).  That makes every backend interchangeable and unlocks the
calibration leaderboard, since each individual vote is preserved.

Backends (selected by environment):
  * Google Sheets  - ``SHEETS_WEBAPP_URL`` set. A one-off, zero-infrastructure
                     store: an Apps Script web app appends/serves rows. See
                     coliseum/sheets/SETUP.md.
  * Postgres       - ``POSTGRES_URL`` / ``DATABASE_URL`` set. Durable.
  * SQLite         - default; local dev.

Interface: ``append_vote(voter, name, winner, loser)`` and ``get_votes()`` ->
list of ``{"voter","name","winner","loser"}`` in chronological order.
"""
import os
import json
import time
import sqlite3
import urllib.request


class SQLiteStore:
    def __init__(self, path):
        self.path = path
        with self._c() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter TEXT, name TEXT, winner TEXT, loser TEXT,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    def _c(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def append_vote(self, voter, name, winner, loser):
        with self._c() as c:
            c.execute("INSERT INTO votes(voter, name, winner, loser) VALUES (?,?,?,?)",
                      (voter, name, winner, loser))

    def get_votes(self):
        with self._c() as c:
            return [dict(r) for r in c.execute(
                "SELECT voter, name, winner, loser FROM votes ORDER BY id")]


class PostgresStore:
    def __init__(self, dsn):
        self.dsn = dsn
        with self._c() as c, c.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS votes (
                id SERIAL PRIMARY KEY, voter TEXT, name TEXT,
                winner TEXT, loser TEXT, ts TIMESTAMPTZ DEFAULT now())""")
            c.commit()

    def _c(self):
        import psycopg
        return psycopg.connect(self.dsn)

    def append_vote(self, voter, name, winner, loser):
        with self._c() as c, c.cursor() as cur:
            cur.execute("INSERT INTO votes(voter, name, winner, loser) VALUES (%s,%s,%s,%s)",
                        (voter, name, winner, loser))
            c.commit()

    def get_votes(self):
        with self._c() as c, c.cursor() as cur:
            cur.execute("SELECT voter, name, winner, loser FROM votes ORDER BY id")
            return [{"voter": r[0], "name": r[1], "winner": r[2], "loser": r[3]}
                    for r in cur.fetchall()]


class SheetsStore:
    """Talks to a Google Apps Script web app backed by a Sheet.

    Reads are cached for ``SHEETS_TTL`` seconds so ``/api/pair`` doesn't hit the
    sheet on every request; a fresh vote is also appended to the local cache so
    the voter sees it immediately.
    """

    def __init__(self, url, token, ttl=15):
        self.url = url
        self.token = token
        self.ttl = ttl
        self._cache = None
        self._fetched = 0.0

    def _request(self, payload=None):
        if payload is None:                       # GET
            url = self.url + ("&" if "?" in self.url else "?") + "action=votes"
            if self.token:
                url += "&token=" + urllib.parse.quote(self.token)
            req = urllib.request.Request(url, headers={"User-Agent": "ff6-coliseum"})
        else:                                     # POST
            data = json.dumps(payload).encode()
            req = urllib.request.Request(self.url, data=data,
                                         headers={"Content-Type": "application/json",
                                                  "User-Agent": "ff6-coliseum"})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            resp = json.loads(raw)
        except ValueError:
            # Apps Script returned HTML (usually a Google sign-in page) instead
            # of JSON -- almost always "Who has access" is not set to "Anyone".
            raise RuntimeError(
                "Sheets web app did not return JSON (got HTML). Re-deploy the "
                "Apps Script web app with 'Who has access: Anyone'. First bytes: "
                + raw.strip()[:120])
        if isinstance(resp, dict) and resp.get("ok") is False:
            raise RuntimeError("Sheets web app rejected the request: "
                               + str(resp.get("error", "unknown")) +
                               " (check SHEETS_TOKEN matches the Script Property TOKEN)")
        return resp

    def append_vote(self, voter, name, winner, loser):
        row = {"voter": voter, "name": name, "winner": winner, "loser": loser}
        self._request({"action": "vote", "token": self.token, **row})
        if self._cache is not None:
            self._cache.append(row)

    def get_votes(self):
        if self._cache is not None and (time.time() - self._fetched) < self.ttl:
            return self._cache
        resp = self._request()
        self._cache = resp.get("votes", []) if isinstance(resp, dict) else (resp or [])
        self._fetched = time.time()
        return self._cache

    def write_tierlist(self, values):
        """Overwrite the Sheet's 'TierList' tab with a 2-D table (owner-private)."""
        self._request({"action": "tierlist", "token": self.token, "values": values})


def get_store():
    url = os.environ.get("SHEETS_WEBAPP_URL")
    if url:
        return SheetsStore(url, os.environ.get("SHEETS_TOKEN", ""),
                           ttl=int(os.environ.get("SHEETS_TTL", "15")))
    dsn = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if dsn:
        return PostgresStore(dsn.replace("postgres://", "postgresql://", 1))
    path = os.environ.get("COLISEUM_DB")
    if not path:
        on_vercel = os.environ.get("VERCEL") == "1"
        path = "/tmp/votes.db" if on_vercel else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "votes.db")
    return SQLiteStore(path)


import urllib.parse  # noqa: E402  (used in SheetsStore._request)
