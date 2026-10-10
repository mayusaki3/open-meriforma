"""Storage-neutral read-only adapter for atomic snapshots.

The store needs only read(key) -> None or {revision: int, records: dict}.
No persisted snapshot can attest current physical safety or restore authority.
"""
from restart_reconciliation import evaluate_records


class SnapshotReconciliation:
    def __init__(self, store):
        self.store = store

    def reconcile(self, key, *, expected_revision, current_generation):
        snapshot = self.store.read(key)
        reasons = []
        if snapshot is None:
            reasons.append("missing_snapshot")
            records = {}
        elif not isinstance(snapshot, dict):
            reasons.append("invalid_snapshot")
            records = {}
        else:
            records = snapshot.get("records")
            if not isinstance(records, dict):
                reasons.append("invalid_snapshot_records")
                records = {}
            revision = snapshot.get("revision")
            if type(revision) is not int or revision < 1:
                reasons.append("invalid_snapshot_revision")
            if (type(expected_revision) is not int or expected_revision < 1
                    or revision != expected_revision):
                reasons.append("stale_or_untrusted_snapshot_revision")
        result = evaluate_records(records, current_generation=current_generation)
        if reasons:
            result["reasons"] = sorted(set(result["reasons"] + reasons))
            result["status"] = "unknown"
        return result
