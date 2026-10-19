"""Suite 58: synthetic trusted monotonic witness contract.

The witness is supplied by the test harness. It is NOT secure hardware, and
the SQLite history and witness do not form an atomic cross-device transaction.
"""
import sqlite3

from durable_receiver_generation_registry import DurableReceiverGenerationRegistry


class SimulatedWitness:
    """Independent, non-rollbackable *by assumption* counter for this fixture."""

    def __init__(self, value=0):
        self.value = value

    def advance(self, expected):
        if self.value != expected:
            raise ValueError("witness changed")
        self.value += 1
        return self.value


class MonotonicGenerationGuard:
    def __init__(self, path, witness, *, initialize=False):
        self.registry = DurableReceiverGenerationRegistry(path, initialize=initialize)
        self.witness = witness
        try:
            if initialize:
                if witness.value != 0:
                    raise ValueError("provisioning requires zero witness")
                self.registry.db.execute(
                    "CREATE TABLE generation_anchor (id INTEGER PRIMARY KEY CHECK(id=1), sequence INTEGER NOT NULL)")
                self.registry.db.execute(
                    "INSERT INTO generation_anchor(id, sequence) VALUES (1, 0)")
            self.verify()
        except (sqlite3.DatabaseError, ValueError):
            self.registry.close()
            raise ValueError("generation witness mismatch or invalid anchor") from None

    def verify(self):
        self.registry._validate()
        try:
            rows = self.registry.db.execute(
                "SELECT id, sequence, typeof(sequence) FROM generation_anchor").fetchall()
            if (len(rows) != 1 or rows[0][0] != 1 or rows[0][2] != "integer"
                    or type(rows[0][1]) is not int or rows[0][1] < 0
                    or rows[0][1] != self.witness.value):
                raise ValueError("generation witness mismatch")
        except sqlite3.DatabaseError:
            raise ValueError("generation anchor unavailable") from None

    def bind(self, link, *, now, max_transfer_ids=65536):
        self.verify()
        if not link.eligible(now=now):
            raise ValueError("explicit authorization required")
        # Advance the independent witness first. Failure to persist the matching
        # anchor thereafter strands the registry closed, not silently reused.
        prior = self.witness.value
        self.witness.advance(prior)
        try:
            self.registry.db.execute("BEGIN IMMEDIATE")
            # Registry.bind would start its own transaction. Implement the same
            # one-time generation reservation and anchor update atomically here.
            from forma_command_receiver import FormaCommandReceiver
            candidate = FormaCommandReceiver(link, max_transfer_ids=max_transfer_ids)
            generation = link.generation
            if type(generation) is not str or not generation:
                raise ValueError("invalid generation")
            self.registry.db.execute(
                "INSERT INTO generations(generation) VALUES (?)", (generation,))
            self.registry.db.execute(
                "UPDATE generation_anchor SET sequence=? WHERE id=1 AND sequence=?",
                (prior + 1, prior))
            if self.registry.db.execute("SELECT changes()").fetchone()[0] != 1:
                raise ValueError("anchor update failed")
            self.registry.db.execute("COMMIT")
        except (sqlite3.DatabaseError, ValueError):
            if self.registry.db.in_transaction:
                self.registry.db.execute("ROLLBACK")
            raise ValueError("generation reservation failed; witness may be ahead") from None
        if self.registry.current is not None:
            self.registry.current._deny()
        self.registry.current = candidate
        return candidate

    def close(self):
        self.registry.close()
