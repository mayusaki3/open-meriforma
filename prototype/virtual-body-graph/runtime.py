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

    def release(self, owner: str) -> None:
        for resource in [key for key, value in self.owners.items() if value == owner]:
            del self.owners[resource]


class BodyGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.connections = {item["id"]: item for item in definition.get("connections", [])}
        self.ownership = ResourceOwnership()

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

    def acquire_resources(self, owner: str, resources: list[str]) -> None:
        missing = [item for item in resources if not self.resource_exists(item)]
        if missing:
            raise RuntimeError(f"unknown resources: {missing}")
        self.ownership.acquire(owner, resources)

    def release_resources(self, owner: str) -> None:
        self.ownership.release(owner)

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

    def capability_available(self, name: str) -> bool:
        capability = self.definition["capabilities"][name]
        if not capability.get("declared", False):
            return False
        if not all(self.resource_exists(item) for item in capability["required_resources"]):
            return False
        required_units = capability.get("required_units", [])
        if len(required_units) > 1:
            root = required_units[0]
            if not all(self.reachable(root, other) for other in required_units[1:]):
                return False
        return True

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
