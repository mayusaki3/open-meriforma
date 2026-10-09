class ExternalObjectUse:
    """Prototype-only object-use arbitration; separate from body control leases."""

    def __init__(self, objects: set[str]) -> None:
        self.objects = set(objects)
        self.holders: dict[str, dict[object, tuple[str, str | None]]] = {}

    def acquire(self, requests: list[dict], lease: object) -> bool:
        for request in requests:
            obj, mode = request["object"], request["mode"]
            group = request.get("group")
            if obj not in self.objects:
                raise RuntimeError(f"unknown world object: {obj}")
            if mode not in {"observe", "exclusive", "coordinated"}:
                raise ValueError(f"unknown use mode: {mode}")
            if mode == "coordinated" and not group:
                raise ValueError("coordinated use requires group")
        for request in requests:
            obj, mode, group = request["object"], request["mode"], request.get("group")
            for holder, (other_mode, other_group) in self.holders.get(obj, {}).items():
                if holder is lease or mode == "observe" or other_mode == "observe":
                    continue
                if mode == "coordinated" and other_mode == "coordinated" and group == other_group:
                    continue
                return False
        for request in requests:
            self.holders.setdefault(request["object"], {})[lease] = (
                request["mode"], request.get("group")
            )
        return True

    def release(self, lease: object) -> None:
        for obj in list(self.holders):
            self.holders[obj].pop(lease, None)
            if not self.holders[obj]:
                del self.holders[obj]

    def holds(self, requests: list[dict], lease: object) -> bool:
        return all(
            self.holders.get(request["object"], {}).get(lease)
            == (request["mode"], request.get("group"))
            for request in requests
        )
