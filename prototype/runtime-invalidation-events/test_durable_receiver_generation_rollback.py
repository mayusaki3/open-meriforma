"""Suite 57: demonstrate coherent SQLite snapshot rollback and external anchor boundary.

A copied SQLite snapshot can pass integrity checks while omitting later generations.
The optional anchor below is an independent test oracle, NOT trusted hardware.
"""
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from durable_receiver_generation_registry import DurableReceiverGenerationRegistry as Registry
from causal_integrated_can import CausalIntegratedCan


def insert(path, generation):
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO generations(generation) VALUES (?)", (generation,))
        db.commit()


def generations(path):
    with closing(sqlite3.connect(path)) as db:
        return {row[0] for row in db.execute("SELECT generation FROM generations")}


def anchored_check(path, expected):
    # Simulates an independently preserved, trusted high-watermark witness.
    # This is not part of the production registry and cannot prove authenticity.
    if not expected.issubset(generations(path)):
        raise ValueError("history rollback detected by external witness")


with TemporaryDirectory() as folder:
    live = Path(folder) / "history.sqlite"
    backup = Path(folder) / "old_snapshot.sqlite"
    store = Registry(str(live), initialize=True)
    store.close()
    insert(live, "M1:C1")
    shutil.copy2(live, backup)
    insert(live, "M2:C2")
    assert generations(live) == {"M1:C1", "M2:C2"}
    print("PASS newer generation exists before snapshot rollback")

    # Replace the complete DB with an earlier coherent snapshot.
    shutil.copy2(backup, live)
    restored = Registry(str(live))
    restored.close()
    assert generations(live) == {"M1:C1"}
    print("PASS coherent old snapshot passes SQLite integrity and registry startup")

    try:
        anchored_check(live, {"M1:C1", "M2:C2"})
    except ValueError:
        pass
    else:
        raise AssertionError("external witness failed to detect missing generation")
    print("PASS independent witness detects missing committed generation")

    anchored_check(live, {"M1:C1"})
    print("PASS stale witness cannot detect a newer missing generation")

    # Without an external witness, a lost generation is available for reuse.
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id="M2", challenge="C2")
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    assert model.link.generation == "M2:C2"
    reopened = Registry(str(live))
    receiver = reopened.bind(model.link, now=0.04)
    assert receiver is reopened.current
    reopened.close()
    assert generations(live) == {"M1:C1", "M2:C2"}
    print("PASS registry can rebind lost generation after coherent rollback")

print("PASS all durable-receiver-generation-rollback checks")
