"""Forced child-process exits against disposable SQLite databases."""
import subprocess
import sys
import tempfile
from pathlib import Path

from delivery_leases import DeliveryLeases

WORKER = Path(__file__).with_name("crash_worker.py")


def crash(path, phase):
    result = subprocess.run(
        [sys.executable, str(WORKER), path, phase],
        capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 71, (phase, result.returncode, result.stderr)


def setup(path):
    store = DeliveryLeases(path)
    assert store.enqueue("crash_event", {"kind": "execution_invalidated"})
    store.close()


with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "uncommitted.sqlite")
    setup(path)
    crash(path, "uncommitted_claim")
    store = DeliveryLeases(path)
    claim = store.claim("recovery", 11.0, 5.0)
    assert claim and claim["generation"] == 1
    assert store.acknowledge("crash_event", "recovery", 1, 12.0)
    store.close()
    print("PASS forced exit before transaction commit rolls back reservation")

    for phase in ("after_claim", "before_ack"):
        path = str(Path(directory) / (phase + ".sqlite"))
        setup(path)
        crash(path, phase)
        store = DeliveryLeases(path)
        assert store.claim("early", 14.0, 5.0) is None
        assert not store.acknowledge("crash_event", "crashed", 1, 15.0)
        claim = store.claim("recovery", 15.0, 5.0)
        assert claim and claim["generation"] == 2
        assert not store.acknowledge("crash_event", "crashed", 1, 16.0)
        assert store.acknowledge("crash_event", "recovery", 2, 16.0)
        store.close()
        print(f"PASS {phase} forced exit retains lease until expiry and fences old ACK")

    path = str(Path(directory) / "after_ack.sqlite")
    setup(path)
    crash(path, "after_ack")
    store = DeliveryLeases(path)
    assert store.is_acknowledged("crash_event")
    assert store.claim("recovery", 15.0, 5.0) is None
    assert not store.acknowledge("crash_event", "crashed", 1, 15.0)
    store.close()
    print("PASS forced exit after committed ACK does not redeliver")

print("PASS all process-crash-recovery checks")
