"""Subprocess crash injection only. Never invoke with production databases."""
import os
import sqlite3
import sys

from delivery_leases import DeliveryLeases

path, phase = sys.argv[1:]
store = DeliveryLeases(path)
key = "crash_event"
if phase == "uncommitted_claim":
    store.db.execute("BEGIN IMMEDIATE")
    store.db.execute(
        """UPDATE leased_outbox SET owner='crashed', lease_until=100,
           generation=generation+1 WHERE event_key=?""", (key,))
elif phase in {"after_claim", "before_ack", "after_ack"}:
    claim = store.claim("crashed", 10.0, 5.0)
    assert claim is not None and claim["event_key"] == key
    if phase == "after_ack":
        assert store.acknowledge(key, "crashed", claim["generation"], 11.0)
else:
    raise ValueError(phase)
# Simulates abrupt interpreter termination without closing the SQLite connection.
os._exit(71)
