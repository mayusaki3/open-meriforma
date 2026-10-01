from __future__ import annotations


class ResourceOwnership:
    def __init__(self) -> None:
        self.owners: dict[str, str] = {}

    def acquire(self, owner: str, resources: list[str]) -> None:
        conflicts = {
            resource: self.owners[resource]
            for resource in resources
            if resource in self.owners and self.owners[resource] != owner
        }
        if conflicts:
            raise RuntimeError(f"resource ownership conflict: {conflicts}")
        for resource in resources:
            self.owners[resource] = owner

    def release(self, owner: str, resources: list[str] | None = None) -> None:
        if resources is None:
            resources = [
                key for key, value in self.owners.items() if value == owner
            ]
        for resource in resources:
            if self.owners.get(resource) == owner:
                del self.owners[resource]


class CapabilityExecution:
    def __init__(self, graph: "BodyGraph", capability: str, controller: str) -> None:
        self.graph = graph
        self.capability = capability
        self.controller = controller
        self.state = "idle"
        self.reasons: list[str] = []
        self.acquired_resources: list[str] = []

    def start(self) -> None:
        readiness = self.graph.evaluate_capability_readiness(
            self.capability, self.controller
        )
        if not readiness["available"] or not readiness["ready"]:
            self.state = "rejected"
            self.reasons = list(readiness["reasons"])
            raise RuntimeError(
                f"capability execution rejected: {self.capability}: {self.reasons}"
            )

        resources = self.graph.definition["capabilities"][self.capability].get(
            "control_resources",
            self.graph.definition["capabilities"][self.capability].get(
                "required_resources", []
            ),
        )
        try:
            self.graph.acquire_resources(self.controller, resources)
        except RuntimeError as exc:
            self.state = "rejected"
            self.reasons = [f"acquire_failed:{exc}"]
            raise RuntimeError(
                f"capability execution acquire failed: "
                f"{self.capability}: {self.reasons}"
            ) from exc

        self.acquired_resources = list(resources)
        self.state = "active"
        self.reasons = []

    def validate(self) -> bool:
        if self.state != "active":
            return self.state == "active"
        lost_ownership = [
            resource
            for resource in self.acquired_resources
            if self.graph.ownership.owners.get(resource) != self.controller
        ]
        if lost_ownership:
            self.state = "invalidated"
            self.reasons = [
                f"ownership_lost:{resource}" for resource in lost_ownership
            ]
            return False

        evaluation = self.graph.evaluate_capability(self.capability)
        if not evaluation["available"]:
            self.state = "invalidated"
            self.reasons = list(evaluation["reasons"])
            return False
        return True

    def finish(self) -> None:
        if self.state not in {"active", "invalidated"}:
            raise RuntimeError(f"cannot finish execution in state: {self.state}")
        self.graph.release_resources(self.controller, self.acquired_resources)
        self.acquired_resources = []
        self.state = "finished"


class BodyGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.connections = {item["id"]: item for item in definition.get("connections", [])}
        self.ownership = ResourceOwnership()
        self.observation_sources: dict[str, bool] = {}
        self.health_states: dict[str, str] = {}

    def connect(self, connection: dict) -> None:
        if connection["id"] in self.connections:
            raise RuntimeError(f"connection already exists: {connection['id']}")
        self._validate_endpoint(connection["a"])
        self._validate_endpoint(connection["b"])
        self.connections[connection["id"]] = connection

    def disconnect(self, connection_id: str) -> None:
        self.connections.pop(connection_id, None)

    def _validate_endpoint(self, endpoint: dict) -> None:
        unit = self.definition["units"].get(endpoint["unit"])
        if unit is None:
            raise RuntimeError(f"unknown unit: {endpoint['unit']}")
        if endpoint["port"] not in unit.get("ports", []):
            raise RuntimeError(
                f"unknown port: {endpoint['unit']}:{endpoint['port']}"
            )

    def connected(self, unit_a: str, unit_b: str) -> bool:
        for item in self.connections.values():
            units = {item["a"]["unit"], item["b"]["unit"]}
            if units == {unit_a, unit_b}:
                return True
        return False

    def reachable(self, start: str, target: str) -> bool:
        if start == target:
            return True
        visited = {start}
        pending = [start]
        while pending:
            current = pending.pop()
            for item in self.connections.values():
                a = item["a"]["unit"]
                b = item["b"]["unit"]
                if a == current:
                    neighbor = b
                elif b == current:
                    neighbor = a
                else:
                    continue
                if neighbor == target:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        return False

    def resource_exists(self, qualified: str) -> bool:
        unit_name, resource = qualified.split(":", 1)
        unit = self.definition["units"].get(unit_name)
        return unit is not None and resource in unit.get("resources", [])

    def set_health_state(self, qualified: str, state: str) -> None:
        if not self.resource_exists(qualified):
            raise RuntimeError(f"unknown health subject: {qualified}")
        if state not in {"ok", "degraded", "unavailable", "unknown"}:
            raise RuntimeError(f"unknown health state: {state}")
        self.health_states[qualified] = state

    def health_state(self, qualified: str) -> str:
        return self.health_states.get(qualified, "unknown")

    def set_observation_source_available(self, qualified: str, available: bool) -> None:
        if not self.resource_exists(qualified):
            raise RuntimeError(f"unknown observation source: {qualified}")
        self.observation_sources[qualified] = available

    def observation_source_available(self, qualified: str) -> bool:
        return self.observation_sources.get(qualified, False)

    def acquire_resources(self, owner: str, resources: list[str]) -> None:
        missing = [item for item in resources if not self.resource_exists(item)]
        if missing:
            raise RuntimeError(f"unknown resources: {missing}")
        self.ownership.acquire(owner, resources)

    def release_resources(
        self, owner: str, resources: list[str] | None = None
    ) -> None:
        self.ownership.release(owner, resources)

    def owned_resources(self, owner: str) -> list[str]:
        return [
            resource
            for resource, current_owner in self.ownership.owners.items()
            if current_owner == owner
        ]

    def disconnected_owned_resources(self, owner: str, anchor_unit: str) -> list[str]:
        disconnected: list[str] = []
        for qualified in self.owned_resources(owner):
            unit_name, _ = qualified.split(":", 1)
            if not self.reachable(anchor_unit, unit_name):
                disconnected.append(qualified)
        return sorted(disconnected)

    def evaluate_capability(self, name: str) -> dict:
        capability = self.definition["capabilities"].get(name)
        if capability is None or not capability.get("declared", False):
            condition_results = [
                {
                    "category": "declaration",
                    "condition": "declared",
                    "subject": name,
                    "satisfied": False,
                    "reason": "not_declared",
                }
            ]
            return {
                "available": False,
                "reasons": ["not_declared"],
                "conditions": condition_results,
            }

        condition_results: list[dict] = []

        for item in capability.get("required_resources", []):
            exists = self.resource_exists(item)
            condition_results.append(
                {
                    "category": "resource",
                    "condition": "exists",
                    "subject": item,
                    "satisfied": exists,
                    "reason": None if exists else f"missing_resource:{item}",
                }
            )

        required_units = capability.get("required_units", [])
        if len(required_units) > 1:
            anchor = required_units[0]
            for unit_name in required_units[1:]:
                reachable = self.reachable(anchor, unit_name)
                condition_results.append(
                    {
                        "category": "topology",
                        "condition": "reachable",
                        "subject": unit_name,
                        "satisfied": reachable,
                        "reason": (
                            None if reachable else f"unreachable_unit:{unit_name}"
                        ),
                    }
                )

        for observation in capability.get("required_observations", []):
            source_available = self.observation_source_available(observation)
            condition_results.append(
                {
                    "category": "observation",
                    "condition": "source_available",
                    "subject": observation,
                    "satisfied": source_available,
                    "reason": (
                        None
                        if source_available
                        else f"observation_unavailable:{observation}"
                    ),
                }
            )

        for subject in capability.get("required_health", []):
            state = self.health_state(subject)
            satisfied = state in {"ok", "degraded"}
            condition_results.append(
                {
                    "category": "health",
                    "condition": "usable",
                    "subject": subject,
                    "satisfied": satisfied,
                    "state": state,
                    "reason": (
                        None if satisfied else f"health_not_usable:{subject}:{state}"
                    ),
                }
            )

        reasons = [
            item["reason"]
            for item in condition_results
            if not item["satisfied"] and item["reason"] is not None
        ]
        return {
            "available": not reasons,
            "reasons": reasons,
            "conditions": condition_results,
        }

    def capability_available(self, name: str) -> bool:
        return self.evaluate_capability(name)["available"]

    def evaluate_capability_readiness(self, name: str, requester: str) -> dict:
        evaluation = self.evaluate_capability(name)
        if not evaluation["available"]:
            return {
                "available": False,
                "ready": False,
                "reasons": list(evaluation["reasons"]),
                "blocked_resources": {},
            }

        capability = self.definition["capabilities"][name]
        blocked = {
            resource: self.ownership.owners[resource]
            for resource in capability.get("required_resources", [])
            if resource in self.ownership.owners
            and self.ownership.owners[resource] != requester
        }
        reasons = [
            f"resource_owned:{resource}:{owner}"
            for resource, owner in sorted(blocked.items())
        ]
        return {
            "available": True,
            "ready": not blocked,
            "reasons": reasons,
            "blocked_resources": blocked,
        }

    def summary(self) -> str:
        if not self.connections:
            return "-"
        return ",".join(
            f"{c['a']['unit']}:{c['a']['port']}<->{c['b']['unit']}:{c['b']['port']}"
            for c in self.connections.values()
        )

    def ownership_summary(self) -> str:
        if not self.ownership.owners:
            return "-"
        return ",".join(
            f"{resource}:{owner}"
            for resource, owner in sorted(self.ownership.owners.items())
        )
