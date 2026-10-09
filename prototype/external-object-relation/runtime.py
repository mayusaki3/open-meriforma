class BodyWorldGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.body_entities = set(definition.get("body", {}).get("units", {}))
        self.world_entities = set(definition.get("world", {}).get("objects", {}))
        self.capabilities = definition.get("capabilities", {})
        self.relations: dict[str, dict] = {}
        self.realizations = definition.get("realizations", {})
        self.constraints = set(definition.get("constraints", {}))
        self.constraint_states: dict[str, bool | None] = {}

    def add_relation(
        self,
        relation_id: str,
        body: str,
        relation: str,
        world: str,
    ) -> None:
        if body not in self.body_entities:
            raise RuntimeError(f"unknown body entity: {body}")
        if world not in self.world_entities:
            raise RuntimeError(f"unknown world entity: {world}")
        if relation_id in self.relations:
            raise RuntimeError(f"relation already exists: {relation_id}")
        self.relations[relation_id] = {
            "body": body,
            "relation": relation,
            "world": world,
        }

    def add_world_relation(self, relation_id: str, source: str, relation: str, target: str) -> None:
        if source not in self.world_entities or target not in self.world_entities:
            raise RuntimeError("unknown world relation endpoint")
        if relation_id in self.relations:
            raise RuntimeError(f"relation already exists: {relation_id}")
        self.relations[relation_id] = {"source": source, "relation": relation, "target": target}

    def set_constraint_state(self, name: str, satisfied: bool | None) -> None:
        if name not in self.constraints:
            raise RuntimeError(f"constraint not declared: {name}")
        if satisfied is not None and not isinstance(satisfied, bool):
            raise ValueError("constraint state must be True, False, or None")
        self.constraint_states[name] = satisfied

    def evaluate_realization(self, name: str) -> dict:
        realization = self.realizations.get(name)
        if realization is None:
            return {"available": False, "reasons": ["realization_not_declared"]}
        missing = [r for r in realization.get("requires_relations", []) if not self.has_relation(r)]
        reasons = [
            "required_relation_missing:" + ":".join(str(v) for v in r.values())
            for r in missing
        ]
        for constraint in realization.get("requires_constraints", []):
            if constraint not in self.constraints:
                reasons.append(f"constraint_not_declared:{constraint}")
            elif self.constraint_states.get(constraint) is None:
                reasons.append(f"constraint_unknown:{constraint}")
            elif self.constraint_states[constraint] is False:
                reasons.append(f"constraint_unsatisfied:{constraint}")
        return {"available": not reasons, "reasons": reasons}

    def remove_relation(self, relation_id: str) -> dict:
        if relation_id not in self.relations:
            raise RuntimeError(f"unknown relation: {relation_id}")
        return self.relations.pop(relation_id)

    def has_relation(self, required: dict) -> bool:
        return any(
            all(relation.get(k) == v for k, v in required.items())
            for relation in self.relations.values()
        )

    def evaluate_capability(self, name: str) -> dict:
        capability = self.capabilities.get(name)
        if capability is None:
            return {
                "available": False,
                "reasons": ["capability_not_declared"],
            }

        realization_name = capability.get("realization")
        if realization_name is not None:
            return self.evaluate_realization(realization_name)

        missing = [
            required
            for required in capability.get("requires_relations", [])
            if not self.has_relation(required)
        ]
        return {
            "available": not missing,
            "reasons": [
                "required_relation_missing:"
                f"{item['body']}:{item['relation']}:{item['world']}"
                for item in missing
            ],
        }
