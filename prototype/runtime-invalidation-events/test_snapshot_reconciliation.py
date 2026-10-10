import tempfile
from pathlib import Path

from atomic_state import AtomicState
from snapshot_reconciliation import SnapshotReconciliation


def records(status="verified", generation=2):
    return {
        "execution": {"domain": "body", "execution_id": "e1", "state": "invalidated"},
        "event": {"event_id": 3, "domain": "body", "execution_id": "e1"},
        "action": {"action_id": 8, "event_id": 3, "kind": "request_stop", "state": "completed"},
        "verification": {"action_id": 8, "status": status},
        "correlation": {"event_id": 3, "action_id": 8, "domain": "body",
                        "execution_id": "e1", "generation": generation},
    }


with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "atomic.sqlite")
    db = AtomicState(path)
    adapter = SnapshotReconciliation(db)
    missing = adapter.reconcile("case", expected_revision=1, current_generation=2)
    assert missing["status"] == "unknown" and "missing_snapshot" in missing["reasons"]
    assert db.write("case", records()) == 1
    db.close()

    db = AtomicState(path)
    adapter = SnapshotReconciliation(db)
    good = adapter.reconcile("case", expected_revision=1, current_generation=2)
    assert good["status"] == "historically_verified"
    assert not good["automatic_resume"] and not good["lease_mutation"]
    assert not good["current_physical_safety_verified"]
    print("PASS atomic snapshot is reconciled after reopen without authorizing resume")

    stale_revision = adapter.reconcile("case", expected_revision=2, current_generation=2)
    assert stale_revision["status"] == "unknown"
    assert "stale_or_untrusted_snapshot_revision" in stale_revision["reasons"]
    stale_generation = adapter.reconcile("case", expected_revision=1, current_generation=3)
    assert stale_generation["status"] == "unknown"
    assert "untrusted_or_stale_generation" in stale_generation["reasons"]
    print("PASS snapshot revision and evidence generation checked independently")

    broken = records()
    broken["verification"]["action_id"] = 99
    assert db.write("case", broken, expected_revision=1) == 2
    mismatch = adapter.reconcile("case", expected_revision=2, current_generation=2)
    assert mismatch["status"] == "unknown"
    assert "verification_action_mismatch" in mismatch["reasons"]
    print("PASS atomically committed inconsistent data still fails closed")

    assert db.write("case", records("not_verified"), expected_revision=2) == 3
    unsafe = adapter.reconcile("case", expected_revision=3, current_generation=2)
    assert unsafe["status"] == "historically_not_verified"
    assert not unsafe["automatic_resume"]
    db.close()
    print("PASS historical unsafe status cannot authorize execution")

    class MemoryStore:
        def read(self, key):
            return {"revision": 1, "records": records()} if key == "case" else None

    memory_result = SnapshotReconciliation(MemoryStore()).reconcile(
        "case", expected_revision=1, current_generation=2)
    assert memory_result["status"] == "historically_verified"
    print("PASS adapter also works without SQLite-backed storage")

print("PASS all snapshot-reconciliation checks")
