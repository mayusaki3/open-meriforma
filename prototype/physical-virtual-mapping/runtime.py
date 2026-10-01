class TwinMappingGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.physical_units = set(definition.get("physical_units", {}))
        self.virtual_units = set(definition.get("virtual_units", {}))
        self.mappings: dict[str, dict] = {}
        for mapping in definition.get("mappings", []):
            self.add_mapping(mapping)

    def add_mapping(self, mapping: dict) -> None:
        mapping_id = mapping["id"]
        physical = mapping["physical"]
        virtual = mapping["virtual"]
        if physical not in self.physical_units:
            raise RuntimeError(f"unknown physical unit: {physical}")
        if virtual not in self.virtual_units:
            raise RuntimeError(f"unknown virtual unit: {virtual}")
        if mapping_id in self.mappings:
            raise RuntimeError(f"mapping already exists: {mapping_id}")
        self.mappings[mapping_id] = mapping

    def remove_mapping(self, mapping_id: str) -> dict:
        if mapping_id not in self.mappings:
            raise RuntimeError(f"unknown mapping: {mapping_id}")
        return self.mappings.pop(mapping_id)

    def mapping(self, mapping_id: str) -> dict | None:
        return self.mappings.get(mapping_id)

    def mappings_for_physical(self, unit_id: str) -> list[dict]:
        return [
            item for item in self.mappings.values()
            if item["physical"] == unit_id
        ]

    def mappings_for_virtual(self, unit_id: str) -> list[dict]:
        return [
            item for item in self.mappings.values()
            if item["virtual"] == unit_id
        ]


    def command_authority_conflicts(self) -> dict[str, list[str]]:
        authorities: dict[str, list[str]] = {}
        for mapping in self.mappings.values():
            scope = mapping.get("scope", [])
            for channel in mapping.get("channels", []):
                if channel.get("direction") != "virtual_to_physical":
                    continue
                if channel.get("authority") != "command":
                    continue
                for subject in scope:
                    key = f"{mapping['physical']}:{subject}"
                    authorities.setdefault(key, []).append(mapping["id"])
        return {
            subject: mapping_ids
            for subject, mapping_ids in authorities.items()
            if len(mapping_ids) > 1
        }
