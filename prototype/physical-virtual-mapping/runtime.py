class TwinMappingGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.physical_units = set(definition.get("physical_units", {}))
        self.virtual_units = set(definition.get("virtual_units", {}))
        self.mappings: dict[str, dict] = {}
        self.active_command_authority: dict[str, str] = {}
        self.endpoint_available: dict[str, bool | None] = {}
        self.mapping_state_samples: dict[str, dict[str, dict]] = {}
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
        removed = self.mappings.pop(mapping_id)
        for subject, active_mapping in list(self.active_command_authority.items()):
            if active_mapping == mapping_id:
                del self.active_command_authority[subject]
        return removed

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


    def command_subjects(self, mapping_id: str) -> list[str]:
        mapping = self.mapping(mapping_id)
        if mapping is None:
            raise RuntimeError(f"unknown mapping: {mapping_id}")
        has_command_channel = any(
            channel.get("direction") == "virtual_to_physical"
            and channel.get("authority") == "command"
            for channel in mapping.get("channels", [])
        )
        if not has_command_channel:
            return []
        return [
            f"{mapping['physical']}:{subject}"
            for subject in mapping.get("scope", [])
        ]

    def activate_command_authority(self, mapping_id: str) -> None:
        subjects = self.command_subjects(mapping_id)
        if not subjects:
            raise RuntimeError(f"mapping has no command authority: {mapping_id}")
        conflicts = {
            subject: self.active_command_authority[subject]
            for subject in subjects
            if subject in self.active_command_authority
            and self.active_command_authority[subject] != mapping_id
        }
        if conflicts:
            raise RuntimeError(f"active command authority conflict: {conflicts}")
        for subject in subjects:
            self.active_command_authority[subject] = mapping_id

    def deactivate_command_authority(self, mapping_id: str) -> None:
        for subject, active_mapping in list(self.active_command_authority.items()):
            if active_mapping == mapping_id:
                del self.active_command_authority[subject]

    def handoff_command_authority(self, source: str, target: str) -> None:
        target_subjects = set(self.command_subjects(target))
        source_subjects = set(self.command_subjects(source))
        overlap = target_subjects & source_subjects
        if not overlap:
            raise RuntimeError(
                f"command authority handoff has no overlapping scope: {source}->{target}"
            )
        if any(
            self.active_command_authority.get(subject) != source
            for subject in overlap
        ):
            raise RuntimeError(
                f"source does not own overlapping command scope: {source}"
            )
        blocking = {
            subject: owner
            for subject, owner in self.active_command_authority.items()
            if subject in target_subjects and owner not in {source, target}
        }
        if blocking:
            raise RuntimeError(f"command authority handoff blocked: {blocking}")
        for subject in overlap:
            del self.active_command_authority[subject]
        for subject in target_subjects:
            current = self.active_command_authority.get(subject)
            if current is not None and current != target:
                raise RuntimeError(f"command authority handoff blocked: {subject}={current}")
        for subject in target_subjects:
            self.active_command_authority[subject] = target


    def set_endpoint_available(self, unit_id: str, available: bool | None) -> None:
        if unit_id not in self.physical_units and unit_id not in self.virtual_units:
            raise RuntimeError(f"unknown unit: {unit_id}")
        self.endpoint_available[unit_id] = available

    def evaluate_mapping(self, mapping_id: str) -> dict:
        mapping = self.mapping(mapping_id)
        if mapping is None:
            return {
                "configured": False,
                "usable": False,
                "reasons": ["mapping_not_configured"],
            }

        reasons: list[str] = []
        for endpoint_type in ("physical", "virtual"):
            unit_id = mapping[endpoint_type]
            state = self.endpoint_available.get(unit_id)
            if state is False:
                reasons.append(f"{endpoint_type}_endpoint_unavailable:{unit_id}")
            elif state is None:
                reasons.append(f"{endpoint_type}_endpoint_unknown:{unit_id}")

        return {
            "configured": True,
            "usable": not reasons,
            "reasons": reasons,
        }


    def invalid_active_command_authority(self) -> dict[str, dict]:
        invalid: dict[str, dict] = {}
        for subject, mapping_id in self.active_command_authority.items():
            evaluation = self.evaluate_mapping(mapping_id)
            if evaluation["usable"]:
                continue
            invalid[subject] = {
                "mapping": mapping_id,
                "reasons": list(evaluation["reasons"]),
            }
        return invalid



    def set_state_sample(
        self,
        mapping_id: str,
        side: str,
        subject: str,
        value: float,
        sample_time: float,
    ) -> None:
        if self.mapping(mapping_id) is None:
            raise RuntimeError(f"unknown mapping: {mapping_id}")
        if side not in {"physical", "virtual"}:
            raise RuntimeError(f"unknown mapping side: {side}")
        samples = self.mapping_state_samples.setdefault(mapping_id, {})
        samples.setdefault(subject, {})[side] = {
            "value": value,
            "sample_time": sample_time,
        }

    def evaluate_state_alignment(
        self,
        mapping_id: str,
        subject: str,
        now: float,
        max_age: float,
        tolerance: float,
    ) -> dict:
        mapping = self.mapping(mapping_id)
        if mapping is None:
            return {
                "comparable": False,
                "aligned": None,
                "reasons": ["mapping_not_configured"],
            }

        subject_samples = self.mapping_state_samples.get(mapping_id, {}).get(
            subject, {}
        )
        reasons: list[str] = []
        for side in ("physical", "virtual"):
            sample = subject_samples.get(side)
            if sample is None:
                reasons.append(f"{side}_sample_missing:{subject}")
                continue
            age = now - sample["sample_time"]
            if age < 0:
                reasons.append(f"{side}_sample_from_future:{subject}")
            elif age > max_age:
                reasons.append(f"{side}_sample_stale:{subject}")

        if reasons:
            return {
                "comparable": False,
                "aligned": None,
                "reasons": reasons,
            }

        physical = subject_samples["physical"]["value"]
        virtual = subject_samples["virtual"]["value"]
        aligned = abs(physical - virtual) <= tolerance
        return {
            "comparable": True,
            "aligned": aligned,
            "difference": virtual - physical,
            "reasons": [] if aligned else [f"state_diverged:{subject}"],
        }
