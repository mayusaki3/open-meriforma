class CapabilityExecution:
    """Prototype lifecycle only: no resource leasing or safety actuation."""

    def __init__(self, graph, capability: str) -> None:
        self.graph = graph
        self.capability = capability
        self.state = "idle"
        self.reasons: list[str] = []

    def start(self) -> bool:
        if self.state != "idle":
            raise RuntimeError(f"cannot start execution from {self.state}")
        evaluation = self.graph.evaluate_capability(self.capability)
        self.reasons = list(evaluation["reasons"])
        self.state = "active" if evaluation["available"] else "rejected"
        return self.state == "active"

    def validate(self) -> dict:
        if self.state != "active":
            return {"state": self.state, "reasons": list(self.reasons)}
        evaluation = self.graph.evaluate_capability(self.capability)
        if not evaluation["available"]:
            self.state = "invalidated"
            self.reasons = list(evaluation["reasons"])
        return {"state": self.state, "reasons": list(self.reasons)}

    def finish(self) -> None:
        if self.state not in {"active", "invalidated", "rejected"}:
            raise RuntimeError(f"cannot finish execution from {self.state}")
        self.state = "finished"
