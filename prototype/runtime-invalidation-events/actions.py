"""In-memory policy action tracking; no physical actuator or safety guarantee."""


class PolicyActions:
    TRANSITIONS = {
        "requested": {"accepted", "failed"},
        "accepted": {"executing", "failed"},
        "executing": {"completed", "failed"},
        "completed": set(),
        "failed": set(),
    }

    def __init__(self) -> None:
        self.next_id = 1
        self.actions: dict[int, dict] = {}
        self.by_event: dict[int, int] = {}

    def request(self, event: dict, kind: str) -> dict:
        if kind not in {"request_stop", "request_handoff"}:
            raise ValueError("unsupported action request")
        event_id = event["event_id"]
        if event_id in self.by_event:
            raise RuntimeError("action already requested for event")
        action = {
            "action_id": self.next_id,
            "event_id": event_id,
            "kind": kind,
            "state": "requested",
            "failure_reason": None,
            "completion_report": None,
        }
        self.next_id += 1
        self.actions[action["action_id"]] = action
        self.by_event[event_id] = action["action_id"]
        return action

    def transition(self, action_id: int, state: str, *,
                   failure_reason: str | None = None,
                   completion_report: str | None = None) -> dict:
        action = self.actions[action_id]
        if state not in self.TRANSITIONS[action["state"]]:
            raise RuntimeError(f"invalid action transition: {action['state']} -> {state}")
        if state == "failed":
            if not failure_reason:
                raise ValueError("failure requires reason")
            if completion_report is not None:
                raise ValueError("failed action cannot carry completion report")
        elif failure_reason is not None:
            raise ValueError("failure reason only valid for failed action")
        if state == "completed":
            if not completion_report:
                raise ValueError("completion requires report")
        elif completion_report is not None:
            raise ValueError("completion report only valid for completed action")
        action["state"] = state
        if state == "failed":
            action["failure_reason"] = failure_reason
        if state == "completed":
            action["completion_report"] = completion_report
        return action
