import tempfile
from pathlib import Path
from restart_reconciliation import RestartReconciliation


def populate(db):
    db.record("execution", "case", {"domain":"body", "execution_id":"e1", "state":"invalidated"})
    db.record("event", "case", {"event_id":3, "domain":"body", "execution_id":"e1"})
    db.record("action", "case", {"action_id":8, "event_id":3, "kind":"request_stop", "state":"completed"})
    db.record("verification", "case", {"action_id":8, "status":"verified"})
    db.record("correlation", "case", {"event_id":3, "action_id":8, "domain":"body",
                                       "execution_id":"e1", "generation":2})


with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "restart.sqlite")
    db = RestartReconciliation(path)
    assert db.reconcile("case", current_generation=2)["status"] == "unknown"
    print("PASS missing records fail closed")
    populate(db)
    db.close()

    db = RestartReconciliation(path)
    result = db.reconcile("case", current_generation=2)
    assert result["status"] == "historically_verified"
    assert result["automatic_resume"] is False
    assert result["current_physical_safety_verified"] is False
    print("PASS complete historical chain survives restart without authorizing resume")

    result = db.reconcile("case", current_generation=3)
    assert result["status"] == "unknown"
    assert "untrusted_or_stale_generation" in result["reasons"]
    print("PASS stale generation rejected")

    db.record("verification", "case", {"action_id":99, "status":"verified"})
    result = db.reconcile("case", current_generation=2)
    assert result["status"] == "unknown"
    assert "verification_action_mismatch" in result["reasons"]
    print("PASS mismatched verification rejected")

    db.record("verification", "case", {"action_id":8, "status":"not_verified"})
    result = db.reconcile("case", current_generation=2)
    assert result["status"] == "historically_not_verified"
    assert not result["automatic_resume"]
    print("PASS historical unsafe result does not authorize recovery")

    db.record("verification", "case", {"action_id":8, "status":"unknown"})
    assert db.reconcile("case", current_generation=2)["status"] == "unknown"
    db.close()
    print("PASS unknown evidence remains unknown after restart")

print("PASS all restart-reconciliation checks")
