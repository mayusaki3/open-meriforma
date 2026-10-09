"""Fail-closed in-memory identity/generation gate before advisory recovery policy.

Caller must supply trusted current lifecycle and evidence generation; this
prototype does not establish their authenticity or persistence.
"""


class CorrelationGate:
    def __init__(self):
        self.accepted: set[tuple[str, str, int]] = set()

    def check(self, *, event: dict, action: dict, verification: dict,
              evidence: dict, current: dict) -> dict:
        reasons = []
        domain = event.get("domain")
        execution_id = event.get("execution_id")
        event_id = event.get("event_id")
        action_id = action.get("action_id")
        generation = evidence.get("generation")
        identity = (domain, execution_id, generation)

        if not isinstance(domain, str) or not domain or not isinstance(execution_id, str) or not execution_id:
            reasons.append("invalid_execution_identity")
        if type(event_id) is not int or event_id < 1 or type(action_id) is not int or action_id < 1:
            reasons.append("invalid_event_or_action_id")
        if action.get("event_id") != event_id:
            reasons.append("event_action_mismatch")
        if verification.get("action_id") != action_id:
            reasons.append("action_verification_mismatch")
        if evidence.get("event_id") != event_id or evidence.get("action_id") != action_id:
            reasons.append("evidence_chain_mismatch")
        if evidence.get("domain") != domain or evidence.get("execution_id") != execution_id:
            reasons.append("evidence_execution_mismatch")
        if type(generation) is not int or generation < 0:
            reasons.append("invalid_generation")
        if current.get("domain") != domain or current.get("execution_id") != execution_id:
            reasons.append("stale_execution_lifecycle")
        if current.get("generation") != generation or type(current.get("generation")) is not int:
            reasons.append("stale_evidence_generation")
        if action.get("kind") != "request_stop" or action.get("state") != "completed":
            reasons.append("action_not_completed_stop")
        if verification.get("status") not in {"verified", "not_verified", "unknown"}:
            reasons.append("invalid_verification_status")
        if not reasons and identity in self.accepted:
            reasons.append("duplicate_evidence_generation")

        if reasons:
            return {"accepted": False, "reasons": sorted(set(reasons))}
        self.accepted.add(identity)
        return {"accepted": True, "reasons": []}
