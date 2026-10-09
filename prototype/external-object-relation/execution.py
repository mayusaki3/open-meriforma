class ResourceLeases:
    """Exclusive body control resource leases, independent of World relations."""

    def __init__(self, definition: dict) -> None:
        self.known = {
            f"{unit}:{resource}"
            for unit, data in definition["body"]["units"].items()
            for resource in data.get("resources", [])
        }
        self.holders: dict[str, object] = {}

    def acquire(self, resources: list[str], lease: object) -> bool:
        if any(resource not in self.known for resource in resources):
            raise RuntimeError("unknown body control resource")
        if any(resource in self.holders and self.holders[resource] is not lease for resource in resources):
            return False
        for resource in resources:
            self.holders[resource] = lease
        return True

    def release(self, lease: object) -> None:
        for resource in list(self.holders):
            if self.holders[resource] is lease:
                del self.holders[resource]


class CapabilityExecution:
    """Execution lifecycle with explicit body resource lease release; no safety actuation."""

    def __init__(self, graph, capability: str, leases: ResourceLeases | None = None, object_use=None) -> None:
        self.graph = graph
        self.capability = capability
        self.leases = leases
        self.object_use = object_use
        self.state = "idle"
        self.reasons: list[str] = []

    def control_resources(self) -> list[str]:
        capability = self.graph.capabilities.get(self.capability, {})
        realization = self.graph.realizations.get(capability.get("realization"), {})
        return list(realization.get("control_resources", capability.get("control_resources", [])))

    def object_requests(self) -> list[dict]:
        capability = self.graph.capabilities.get(self.capability, {})
        realization = self.graph.realizations.get(capability.get("realization"), {})
        return list(realization.get("object_use", capability.get("object_use", [])))

    def start(self) -> bool:
        if self.state != "idle":
            raise RuntimeError(f"cannot start execution from {self.state}")
        evaluation = self.graph.evaluate_capability(self.capability)
        self.reasons = list(evaluation["reasons"])
        if not evaluation["available"]:
            self.state = "rejected"
            return False
        resources = self.control_resources()
        if resources and self.leases is None:
            self.reasons = ["resource_leases_not_configured"]
            self.state = "rejected"
            return False
        if self.leases is not None and not self.leases.acquire(resources, self):
            self.reasons = ["resource_lease_conflict"]
            self.state = "rejected"
            return False
        requests = self.object_requests()
        if requests and self.object_use is None:
            if self.leases is not None:
                self.leases.release(self)
            self.reasons = ["object_use_not_configured"]
            self.state = "rejected"
            return False
        if self.object_use is not None and not self.object_use.acquire(requests, self):
            if self.leases is not None:
                self.leases.release(self)
            self.reasons = ["object_use_conflict"]
            self.state = "rejected"
            return False
        self.state = "active"
        return True

    def validate(self) -> dict:
        if self.state != "active":
            return {"state": self.state, "reasons": list(self.reasons)}
        evaluation = self.graph.evaluate_capability(self.capability)
        if not evaluation["available"]:
            self.state = "invalidated"
            self.reasons = list(evaluation["reasons"])
        elif self.leases is not None and any(
            self.leases.holders.get(resource) is not self for resource in self.control_resources()
        ):
            self.state = "invalidated"
            self.reasons = ["resource_lease_lost"]
        return {"state": self.state, "reasons": list(self.reasons)}

    def finish(self) -> None:
        if self.state not in {"active", "invalidated", "rejected"}:
            raise RuntimeError(f"cannot finish execution from {self.state}")
        if self.leases is not None:
            self.leases.release(self)
        if self.object_use is not None:
            self.object_use.release(self)
        self.state = "finished"
