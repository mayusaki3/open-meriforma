"""Experimental SQLite delivery reservations with fencing tokens.

Not a distributed safety controller. Caller supplies a consistent clock.
"""
import json
import sqlite3

from durable_delivery import valid_time


class DeliveryLeases:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, timeout=3.0, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=3000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS leased_outbox (
            event_key TEXT PRIMARY KEY, payload TEXT NOT NULL,
            acknowledged INTEGER NOT NULL DEFAULT 0,
            owner TEXT, lease_until REAL,
            generation INTEGER NOT NULL DEFAULT 0)""")

    def close(self):
        self.db.close()

    def enqueue(self, key: str, payload: dict) -> bool:
        if not isinstance(key, str) or not key:
            raise ValueError("invalid event key")
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        cur = self.db.execute(
            "INSERT OR IGNORE INTO leased_outbox(event_key,payload) VALUES (?,?)",
            (key, encoded))
        return cur.rowcount == 1

    def claim(self, owner: str, now_s: float, lease_s: float) -> dict | None:
        valid_time(now_s)
        valid_time(lease_s)
        if lease_s <= 0 or not isinstance(owner, str) or not owner:
            raise ValueError("invalid owner or lease")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                """SELECT event_key,payload,generation FROM leased_outbox
                WHERE acknowledged=0 AND (lease_until IS NULL OR lease_until<=?)
                ORDER BY rowid LIMIT 1""", (now_s,)).fetchone()
            if row is None:
                self.db.execute("COMMIT")
                return None
            key, payload, generation = row
            token = generation + 1
            self.db.execute(
                """UPDATE leased_outbox SET owner=?,lease_until=?,generation=?
                WHERE event_key=?""", (owner, now_s + lease_s, token, key))
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        return {"event_key": key, "payload": json.loads(payload),
                "owner": owner, "generation": token}

    def acknowledge(self, key: str, owner: str, generation: int,
                    now_s: float) -> bool:
        valid_time(now_s)
        if type(generation) is not int or generation < 1:
            raise ValueError("invalid generation")
        cur = self.db.execute(
            """UPDATE leased_outbox SET acknowledged=1
            WHERE event_key=? AND owner=? AND generation=?
            AND acknowledged=0 AND lease_until>?""",
            (key, owner, generation, now_s))
        return cur.rowcount == 1

    def is_acknowledged(self, key: str) -> bool:
        row = self.db.execute(
            "SELECT acknowledged FROM leased_outbox WHERE event_key=?",
            (key,)).fetchone()
        return bool(row and row[0])
