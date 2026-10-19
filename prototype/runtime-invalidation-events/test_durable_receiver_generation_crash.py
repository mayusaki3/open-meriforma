"""Suite 55: forced process exit before/after generation-history commit.

SQLite process crash simulation, not sudden power loss or authenticated epoch.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

from durable_receiver_generation_registry import DurableReceiverGenerationRegistry

WORKER = Path(__file__).with_name("durable_receiver_crash_worker.py")


def crash(path, phase):
    result = subprocess.run([sys.executable, str(WORKER), str(path), phase],
                            capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 71, (phase, result.returncode, result.stderr)


def history(path):
    # sqlite3.Connection context manager commits/rolls back but does NOT close.
    # Explicitly close before TemporaryDirectory cleanup on Windows.
    with closing(sqlite3.connect(path)) as db:
        return [row[0] for row in db.execute("SELECT generation FROM generations ORDER BY generation")]


with TemporaryDirectory() as folder:
    path = Path(folder) / "before.sqlite"
    store = DurableReceiverGenerationRegistry(str(path), initialize=True)
    store.close()
    crash(path, "before_commit")
    assert history(path) == []
    reopened = DurableReceiverGenerationRegistry(str(path))
    reopened.close()
    print("PASS abrupt exit before COMMIT rolls back uncommitted generation")

with TemporaryDirectory() as folder:
    path = Path(folder) / "after.sqlite"
    store = DurableReceiverGenerationRegistry(str(path), initialize=True)
    store.close()
    crash(path, "after_commit")
    assert history(path) == ["M1:C1"]
    reopened = DurableReceiverGenerationRegistry(str(path))
    reopened.close()
    print("PASS abrupt exit after COMMIT retains generation")

with TemporaryDirectory() as folder:
    path = Path(folder) / "repeat.sqlite"
    store = DurableReceiverGenerationRegistry(str(path), initialize=True)
    store.close()
    crash(path, "after_commit")
    result = subprocess.run([sys.executable, str(WORKER), str(path), "after_commit"],
                            capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode != 71
    assert "generation already used" in result.stderr
    assert history(path) == ["M1:C1"]
    print("PASS restart cannot bind previously committed generation")

with TemporaryDirectory() as folder:
    path = Path(folder) / "fresh.sqlite"
    store = DurableReceiverGenerationRegistry(str(path), initialize=True)
    store.close()
    crash(path, "before_commit")
    crash(path, "after_commit")
    assert history(path) == ["M1:C1"]
    print("PASS uncommitted generation can be committed by a later authorized run")

print("PASS all durable-receiver-generation-crash checks")
