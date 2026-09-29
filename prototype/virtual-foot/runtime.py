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
        for resource in [key for key, value in self.owners.items() if value == owner]:
            del self.owners[resource]

    def transfer(self, from_owner: str, to_owner: str, resources: list[str]) -> None:
        for resource in resources:
            current = self.owners.get(resource)
            if current != from_owner:
                raise RuntimeError(
                    f"resource transfer mismatch: {resource} is owned by {current!r}, "
                    f"expected {from_owner!r}"
                )
        for resource in resources:
            self.owners[resource] = to_owner

    def release_resources(self, owner: str, resources: list[str]) -> None:
        for resource in resources:
            if self.owners.get(resource) == owner:
                del self.owners[resource]


class VirtualUnitRuntime:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.ownership = ResourceOwnership()
        self.active_groups: set[str] = set()

    def group(self, name: str) -> dict:
        return self.definition["functional_groups"][name]

    def activate(self, name: str) -> None:
        group = self.group(name)
        self.ownership.acquire(group["owner"], list(group.get("resources", [])))
        self.active_groups.add(name)

    def deactivate(self, name: str) -> None:
        if name not in self.active_groups:
            return
        self.ownership.release(self.group(name)["owner"])
        self.active_groups.remove(name)

    def deactivate_all(self) -> None:
        for name in list(self.active_groups):
            self.deactivate(name)

    def owner_summary(self) -> str:
        if not self.ownership.owners:
            return "-"
        return ",".join(
            f"{resource}:{owner}"
            for resource, owner in sorted(self.ownership.owners.items())
        )
