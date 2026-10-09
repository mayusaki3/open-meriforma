"""SQLite-backed local outbox prototype, not a distributed safety transport.

Caller supplies monotonic logical time across process restarts. Delivery is
at-least-once by polling; consumers must deduplicate by event identity.
"""
import json
import math
import sqlite3


def valid_time(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("time must be a nonnegative finite number")


class DurableDelivery:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA busy_timeout=3000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS outbox (
            event_key TEXT PRIMARY KEY, payload TEXT NOT NULL,
            acknowledged INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0, last_sent REAL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS action_watch (
            action_key TEXT PRIMARY KEY, deadline REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','completed','timed_out')))""")
        self.db.commit()

    def close(self):
        self.db.close()

    def enqueue(self, event_key: str, payload: dict) -> bool:
        if not isinstance(event_key, str) or not event_key:
            raise ValueError("invalid event key")
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        with self.db:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO outbox(event_key,payload) VALUES (?,?)",
                (event_key, encoded))
        return cur.rowcount == 1

    def deliver(self, now_s: float, retry_after_s: float = 1.0) -> list[dict]:
        valid_time(now_s)
        valid_time(retry_after_s)
        with self.db:
            rows = self.db.execute(
                """SELECT event_key,payload,attempts FROM outbox
                WHERE acknowledged=0 AND (last_sent IS NULL OR last_sent+?<=?)
                ORDER BY rowid""", (retry_after_s, now_s)).fetchall()
            for key, _, _ in rows:
                self.db.execute(
                    "UPDATE outbox SET attempts=attempts+1,last_sent=? WHERE event_key=?",
                    (now_s, key))
        return [{"event_key":key,"payload":json.loads(payload),"attempt":attempts+1}
                for key,payload,attempts in rows]

    def acknowledge(self, event_key: str) -> bool:
        with self.db:
            cur = self.db.execute(
                "UPDATE outbox SET acknowledged=1 WHERE event_key=? AND acknowledged=0",
                (event_key,))
        return cur.rowcount == 1

    def watch_action(self, action_key: str, deadline_s: float) -> bool:
        valid_time(deadline_s)
        if not isinstance(action_key, str) or not action_key:
            raise ValueError("invalid action key")
        with self.db:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO action_watch VALUES (?,?,'pending')",
                (action_key, deadline_s))
        return cur.rowcount == 1

    def complete_action(self, action_key: str, now_s: float) -> bool:
        valid_time(now_s)
        with self.db:
            cur = self.db.execute(
                """UPDATE action_watch SET status='completed'
                WHERE action_key=? AND status='pending' AND deadline>=?""",
                (action_key, now_s))
        return cur.rowcount == 1

    def expired_actions(self, now_s: float) -> list[str]:
        valid_time(now_s)
        with self.db:
            rows = self.db.execute(
                "SELECT action_key FROM action_watch WHERE status='pending' AND deadline<?",
                (now_s,)).fetchall()
            self.db.executemany(
                "UPDATE action_watch SET status='timed_out' WHERE action_key=?",
                rows)
        return [row[0] for row in rows]

    def action_status(self, action_key: str) -> str | None:
        row = self.db.execute(
            "SELECT status FROM action_watch WHERE action_key=?", (action_key,)).fetchone()
        return row[0] if row else None
