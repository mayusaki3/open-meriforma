"""Suite 55 child: abrupt process exit at SQLite generation-history boundaries.

Only disposable SQLite files. Exit 71 is deliberate; not a power-loss test.
"""
import os
import sqlite3
import sys

from causal_integrated_can import CausalIntegratedCan
from durable_receiver_generation_registry import DurableReceiverGenerationRegistry

path, phase = sys.argv[1:]
generation = "M1:C1"

if phase == "before_commit":
    # Exercise the same BEGIN/INSERT boundary as registry.bind, without COMMIT.
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("BEGIN IMMEDIATE")
    db.execute("INSERT INTO generations(generation) VALUES (?)", (generation,))
    os._exit(71)

if phase == "after_commit":
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id="M1", challenge="C1")
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    store = DurableReceiverGenerationRegistry(path)
    store.bind(model.link, now=0.04)
    os._exit(71)

raise ValueError("unknown phase")
