from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResourceOwnership:
    owners: dict[str, str] = field(default_factory=dict)

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
        for resource in [
            resource for resource, current in self.owners.items() if current == owner
        ]:
            del self.owners[resource]


class ConstraintSet:
    def __init__(self, definition: dict) -> None:
        self.constraints = definition.get("constraints", [])

    def clamp_target(self, element: str, target: float) -> tuple[float, bool]:
        import math

        result = target
        limited = False
        for constraint in self.constraints:
            if constraint.get("kind") != "joint_range":
                continue
            if element not in constraint.get("scope", []):
                continue
            minimum = math.radians(float(constraint["min_deg"]))
            maximum = math.radians(float(constraint["max_deg"]))
            bounded = max(minimum, min(maximum, result))
            limited = limited or bounded != result
            result = bounded
        return result, limited


class VirtualUnitRuntime:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.ownership = ResourceOwnership()
        self.constraints = ConstraintSet(definition)
        self.active_group: str | None = None

    def group(self, name: str) -> dict:
        return self.definition["functional_groups"][name]

    def activate(self, name: str) -> None:
        group = self.group(name)
        owner = group["owner"]
        resources = list(group.get("resources", []))
        self.ownership.acquire(owner, resources)
        self.active_group = name

    def deactivate(self) -> None:
        if self.active_group is None:
            return
        owner = self.group(self.active_group)["owner"]
        self.ownership.release(owner)
        self.active_group = None

    def owner_summary(self) -> str:
        if not self.ownership.owners:
            return "-"
        return ",".join(
            f"{resource}:{owner}"
            for resource, owner in sorted(self.ownership.owners.items())
        )
