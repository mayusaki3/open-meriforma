"""Prototype event boundary: detection and policy are separate from physical action."""


class InvalidationEvents:
    def __init__(self) -> None:
        self.next_id = 1
        self.pending: dict[int, dict] = {}
        self.history: list[dict] = []
        self.emitted: set[tuple[str, str]] = set()

    def observe(self, domain: str, execution_id: str, result: dict) -> dict | None:
        """Emit only the first invalidation per domain/execution lifecycle."""
        if result["state"] != "invalidated":
            return None
        key = (domain, execution_id)
        if key in self.emitted:
            return None
        event = {
            "event_id": self.next_id,
            "domain": domain,
            "execution_id": execution_id,
            "kind": "execution_invalidated",
            "reasons": list(result["reasons"]),
            "acknowledged": False,
        }
        self.next_id += 1
        self.emitted.add(key)
        self.pending[event["event_id"]] = event
        self.history.append(event)
        return event

    def acknowledge(self, event_id: int) -> dict:
        if event_id not in self.pending:
            raise RuntimeError(f"event not pending: {event_id}")
        event = self.pending.pop(event_id)
        event["acknowledged"] = True
        return event


class PolicyInbox:
    """Policy records an explicit recommendation, never actuates or releases."""

    def __init__(self) -> None:
        self.decisions: dict[int, str] = {}

    def decide(self, event: dict, decision: str) -> None:
        if decision not in {"review", "request_stop", "request_handoff"}:
            raise ValueError("unsupported prototype decision")
        if event["acknowledged"]:
            raise RuntimeError("cannot decide after acknowledgment")
        self.decisions[event["event_id"]] = decision
