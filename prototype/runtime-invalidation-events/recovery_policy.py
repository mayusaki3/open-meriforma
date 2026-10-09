"""Advisory recovery decisions only; no authority to actuate or release leases."""


class RecoveryPolicy:
    """Decide next review/escalation from a STOP verification result.

    All decisions are recommendations. 'verified' is not permission to resume.
    """

    DECISIONS = {
        "verified": "hold_for_explicit_recovery",
        "not_verified": "request_stop_escalation",
        "unknown": "request_evidence_or_safe_fallback",
    }

    def __init__(self):
        self.decisions: dict[int, dict] = {}

    def assess(self, action: dict, verification: dict) -> dict:
        if action.get("kind") != "request_stop":
            raise ValueError("recovery policy expects STOP action")
        action_id = action["action_id"]
        if verification.get("action_id") != action_id:
            raise ValueError("verification action mismatch")
        if action_id in self.decisions:
            raise RuntimeError("recovery decision already recorded")
        status = verification.get("status")
        if status not in self.DECISIONS:
            raise ValueError("unsupported verification status")
        decision = {
            "action_id": action_id,
            "verification_status": status,
            "recommendation": self.DECISIONS[status],
            "automatic_resume": False,
            "lease_mutation": False,
        }
        self.decisions[action_id] = decision
        return decision
