"""Suite 54: SQLite-backed synthetic generation anti-reuse across process restarts.

Local durable reference only: not authenticated, power-loss tested, or MCU storage.
"""
import sqlite3

from forma_command_receiver import FormaCommandReceiver


class DurableReceiverGenerationRegistry:
    def __init__(self, path, *, initialize=False):
        self.current = None
        self.db = sqlite3.connect(path, isolation_level=None)
        try:
            if initialize:
                # Explicit provisioning only; never silently recreate missing state.
                self.db.execute("CREATE TABLE generations (generation TEXT PRIMARY KEY NOT NULL)")
            self._validate()
        except (sqlite3.DatabaseError, ValueError):
            self.db.close()
            raise ValueError("generation history unavailable or corrupt") from None

    def _validate(self):
        try:
            rows = self.db.execute("PRAGMA table_info(generations)").fetchall()
            if (len(rows) != 1 or rows[0][1] != "generation"
                    or rows[0][2].upper() != "TEXT" or rows[0][5] != 1):
                raise ValueError("invalid history schema")
            check = self.db.execute("PRAGMA quick_check").fetchone()
            if check != ("ok",):
                raise ValueError("corrupt history")
        except sqlite3.DatabaseError:
            raise ValueError("history unavailable") from None

    def bind(self, link, *, now, max_transfer_ids=65536):
        self._validate()
        if not link.eligible(now=now):
            raise ValueError("generation requires explicit live authorization")
        generation = link.generation
        if type(generation) is not str or not generation:
            raise ValueError("invalid generation")
        # Validate receiver configuration before consuming the epoch.
        candidate = FormaCommandReceiver(link, max_transfer_ids=max_transfer_ids)
        try:
            self.db.execute("BEGIN IMMEDIATE")
            self.db.execute("INSERT INTO generations(generation) VALUES (?)", (generation,))
            self.db.execute("COMMIT")
        except sqlite3.DatabaseError:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise ValueError("generation already used or history write failed") from None
        if self.current is not None:
            self.current._deny()
        self.current = candidate
        return candidate

    def close(self):
        if self.current is not None:
            self.current._deny()
        self.db.close()
