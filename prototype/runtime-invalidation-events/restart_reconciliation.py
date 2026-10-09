"""Read-only restart reconciliation of trusted snapshot records.

This prototype does not reconstruct physical authority or prove STOP safety.
"""
import json
import sqlite3


class RestartReconciliation:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS restart_records (
            record_kind TEXT NOT NULL, record_key TEXT NOT NULL,
            payload TEXT NOT NULL, PRIMARY KEY(record_kind,record_key))""")
        self.db.commit()

    def close(self):
        self.db.close()

    def record(self, kind, key, value):
        if kind not in {"execution", "event", "action", "verification", "correlation"}:
            raise ValueError("unsupported record kind")
        if not isinstance(key, str) or not key or not isinstance(value, dict):
            raise ValueError("invalid record")
        encoded = json.dumps(value, allow_nan=False, sort_keys=True)
        with self.db:
            self.db.execute("""INSERT INTO restart_records VALUES (?,?,?)
                ON CONFLICT(record_kind,record_key) DO UPDATE SET payload=excluded.payload""",
                (kind, key, encoded))

    def reconcile(self, key, *, current_generation=None):
        rows = self.db.execute(
            "SELECT record_kind,payload FROM restart_records WHERE record_key=?",
            (key,)).fetchall()
        records = {kind: json.loads(payload) for kind, payload in rows}
        reasons = []
        for kind in ("execution", "event", "action", "verification", "correlation"):
            if kind not in records:
                reasons.append("missing_" + kind)
        execution = records.get("execution", {})
        event = records.get("event", {})
        action = records.get("action", {})
        verification = records.get("verification", {})
        correlation = records.get("correlation", {})
        if execution and execution.get("state") not in {"invalidated", "finished"}:
            reasons.append("execution_not_invalidated_or_finished")
        if event and (event.get("domain") != execution.get("domain")
                      or event.get("execution_id") != execution.get("execution_id")):
            reasons.append("event_execution_mismatch")
        if action and action.get("event_id") != event.get("event_id"):
            reasons.append("action_event_mismatch")
        if action and (action.get("kind") != "request_stop"
                       or action.get("state") != "completed"):
            reasons.append("stop_action_not_completed")
        if verification and verification.get("action_id") != action.get("action_id"):
            reasons.append("verification_action_mismatch")
        if correlation and (correlation.get("event_id") != event.get("event_id")
                            or correlation.get("action_id") != action.get("action_id")
                            or correlation.get("domain") != execution.get("domain")
                            or correlation.get("execution_id") != execution.get("execution_id")):
            reasons.append("correlation_identity_mismatch")
        generation = correlation.get("generation")
        if (type(generation) is not int or generation < 0
                or type(current_generation) is not int
                or generation != current_generation):
            reasons.append("untrusted_or_stale_generation")
        status = verification.get("status")
        if status not in {"verified", "not_verified", "unknown"}:
            reasons.append("missing_or_invalid_verification")
        if reasons:
            result = "unknown"
        elif status == "verified":
            result = "historically_verified"
        elif status == "not_verified":
            result = "historically_not_verified"
        else:
            result = "unknown"
        return {"status": result, "reasons": sorted(set(reasons)),
                "automatic_resume": False, "lease_mutation": False,
                "current_physical_safety_verified": False}
