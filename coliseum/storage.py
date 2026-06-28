"""Pluggable vote/rating storage.

The app is **stateless**: every request reads the current ratings from the
store and writes back updates, so it behaves correctly across multiple
serverless instances (Vercel) as well as a single local process.

Two backends:
  * SQLite  - default; great for local dev. On Vercel the only writable path is
              ``/tmp`` and it is ephemeral/per-instance, so use it only for a
              throwaway demo.
  * Postgres - used automatically when ``POSTGRES_URL`` / ``DATABASE_URL`` is
               set (e.g. Vercel Postgres / Neon). Durable; the right choice for
               real crowd-sourcing.

Both expose the same small interface (see :class:`Store`).
"""
import os
import sqlite3


def _pair_key(a, b):
    return (a, b) if a <= b else (b, a)


class Store:
    """Interface + shared helpers."""

    def ensure_seed(self, seeds):
        """Insert any missing ratings. ``seeds`` maps slug -> (rating, rd, vol)."""
        raise NotImplementedError

    def all_ratings(self):
        """Return dict slug -> {'rating','rd','vol','n'}."""
        raise NotImplementedError

    def pair_counts(self):
        """Return dict frozenset({a,b}) -> times shown together."""
        raise NotImplementedError

    def record_vote(self, winner, loser, new_w, new_l):
        """Persist a vote and the two updated ratings atomically.

        ``new_*`` are dicts with keys rating/rd/vol/n.
        """
        raise NotImplementedError

    def vote_count(self):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------
class SQLiteStore(Store):
    DDL = """
        CREATE TABLE IF NOT EXISTS ratings (
            slug TEXT PRIMARY KEY, rating REAL, rd REAL, vol REAL, n INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner TEXT, loser TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pairs (
            a TEXT, b TEXT, n INTEGER DEFAULT 0, PRIMARY KEY (a, b)
        );
    """

    def __init__(self, path):
        self.path = path
        with self._conn() as c:
            c.executescript(self.DDL)

    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_seed(self, seeds):
        with self._conn() as c:
            have = {r["slug"] for r in c.execute("SELECT slug FROM ratings")}
            rows = [(s, v[0], v[1], v[2]) for s, v in seeds.items() if s not in have]
            if rows:
                c.executemany(
                    "INSERT INTO ratings(slug, rating, rd, vol, n) VALUES (?,?,?,?,0)", rows)

    def all_ratings(self):
        with self._conn() as c:
            return {r["slug"]: {"rating": r["rating"], "rd": r["rd"],
                                "vol": r["vol"], "n": r["n"]}
                    for r in c.execute("SELECT * FROM ratings")}

    def pair_counts(self):
        with self._conn() as c:
            return {frozenset((r["a"], r["b"])): r["n"]
                    for r in c.execute("SELECT a, b, n FROM pairs")}

    def record_vote(self, winner, loser, new_w, new_l):
        a, b = _pair_key(winner, loser)
        with self._conn() as c:
            c.execute("BEGIN")
            for slug, nr in ((winner, new_w), (loser, new_l)):
                c.execute("UPDATE ratings SET rating=?, rd=?, vol=?, n=? WHERE slug=?",
                          (nr["rating"], nr["rd"], nr["vol"], nr["n"], slug))
            c.execute("INSERT INTO votes(winner, loser) VALUES (?,?)", (winner, loser))
            c.execute(
                "INSERT INTO pairs(a, b, n) VALUES (?,?,1) "
                "ON CONFLICT(a, b) DO UPDATE SET n = n + 1", (a, b))
            c.commit()

    def vote_count(self):
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) c FROM votes").fetchone()["c"]


# ---------------------------------------------------------------------------
# Postgres (psycopg 3) - used when POSTGRES_URL / DATABASE_URL is set
# ---------------------------------------------------------------------------
class PostgresStore(Store):
    DDL = """
        CREATE TABLE IF NOT EXISTS ratings (
            slug TEXT PRIMARY KEY, rating DOUBLE PRECISION, rd DOUBLE PRECISION,
            vol DOUBLE PRECISION, n INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS votes (
            id SERIAL PRIMARY KEY, winner TEXT, loser TEXT,
            ts TIMESTAMPTZ DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS pairs (
            a TEXT, b TEXT, n INTEGER DEFAULT 0, PRIMARY KEY (a, b)
        );
    """

    def __init__(self, dsn):
        self.dsn = dsn
        with self._conn() as c, c.cursor() as cur:
            cur.execute(self.DDL)
            c.commit()

    def _conn(self):
        import psycopg
        return psycopg.connect(self.dsn)

    def ensure_seed(self, seeds):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT slug FROM ratings")
            have = {r[0] for r in cur.fetchall()}
            rows = [(s, v[0], v[1], v[2]) for s, v in seeds.items() if s not in have]
            if rows:
                cur.executemany(
                    "INSERT INTO ratings(slug, rating, rd, vol, n) "
                    "VALUES (%s,%s,%s,%s,0) ON CONFLICT (slug) DO NOTHING", rows)
            c.commit()

    def all_ratings(self):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT slug, rating, rd, vol, n FROM ratings")
            return {r[0]: {"rating": r[1], "rd": r[2], "vol": r[3], "n": r[4]}
                    for r in cur.fetchall()}

    def pair_counts(self):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT a, b, n FROM pairs")
            return {frozenset((r[0], r[1])): r[2] for r in cur.fetchall()}

    def record_vote(self, winner, loser, new_w, new_l):
        a, b = _pair_key(winner, loser)
        with self._conn() as c, c.cursor() as cur:
            for slug, nr in ((winner, new_w), (loser, new_l)):
                cur.execute("UPDATE ratings SET rating=%s, rd=%s, vol=%s, n=%s WHERE slug=%s",
                            (nr["rating"], nr["rd"], nr["vol"], nr["n"], slug))
            cur.execute("INSERT INTO votes(winner, loser) VALUES (%s,%s)", (winner, loser))
            cur.execute("INSERT INTO pairs(a, b, n) VALUES (%s,%s,1) "
                        "ON CONFLICT (a, b) DO UPDATE SET n = pairs.n + 1", (a, b))
            c.commit()

    def vote_count(self):
        with self._conn() as c, c.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM votes")
            return cur.fetchone()[0]


def get_store():
    dsn = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if dsn:
        # Vercel sometimes provides a non-standard scheme prefix.
        dsn = dsn.replace("postgres://", "postgresql://", 1)
        return PostgresStore(dsn)
    path = os.environ.get("COLISEUM_DB")
    if not path:
        # On Vercel only /tmp is writable; locally use a file beside the app.
        on_vercel = os.environ.get("VERCEL") == "1"
        path = "/tmp/votes.db" if on_vercel else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "votes.db")
    return SQLiteStore(path)
