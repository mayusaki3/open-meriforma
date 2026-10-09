"""Local SQLite atomic snapshots; no atomicity with robot or external services."""
import json
import sqlite3

KINDS = ("execution", "event", "action", "verification", "correlation")


class AtomicState:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=3.0, isolation_level=None)
        self.db.execute("PRAGMA busy_timeout=3000")
        self.db.execute("""CREATE TABLE IF NOT EXISTS atomic_snapshots (
            snapshot_key TEXT PRIMARY KEY, revision INTEGER NOT NULL,
            payload TEXT NOT NULL)""")

    def close(self):
        self.db.close()

    def read(self, key):
        row = self.db.execute(
            "SELECT revision,payload FROM atomic_snapshots WHERE snapshot_key=?",
            (key,)).fetchone()
        return None if row is None else {"revision": row[0], "records": json.loads(row[1])}

    def write(self, key, records, expected_revision=None):
        if not isinstance(key, str) or not key:
            raise ValueError("invalid snapshot key")
        if not isinstance(records, dict) or set(records) != set(KINDS):
            raise ValueError("snapshot requires all five record kinds")
        if any(not isinstance(records[kind], dict) for kind in KINDS):
            raise ValueError("record payload must be an object")
        if expected_revision is not None and (
                type(expected_revision) is not int or expected_revision < 1):
            raise ValueError("invalid expected revision")
        encoded = json.dumps(records, sort_keys=True, allow_nan=False)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute(
                "SELECT revision FROM atomic_snapshots WHERE snapshot_key=?",
                (key,)).fetchone()
            actual = row[0] if row else None
            if actual != expected_revision:
                raise RuntimeError("stale snapshot revision")
            revision = 1 if actual is None else actual + 1
            self.db.execute(
                """INSERT INTO atomic_snapshots(snapshot_key,revision,payload)
                VALUES (?,?,?) ON CONFLICT(snapshot_key) DO UPDATE SET
                revision=excluded.revision,payload=excluded.payload""",
                (key, revision, encoded))
            self.db.execute("COMMIT")
            return revision
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
