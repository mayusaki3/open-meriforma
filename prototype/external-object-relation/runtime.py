class BodyWorldGraph:
    def __init__(self, definition: dict) -> None:
        self.definition = definition
        self.body_entities = set(definition.get("body", {}).get("units", {}))
        self.world_entities = set(definition.get("world", {}).get("objects", {}))
        self.capabilities = definition.get("capabilities", {})
        self.relations: dict[str, dict] = {}

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

    def remove_relation(self, relation_id: str) -> dict:
        if relation_id not in self.relations:
            raise RuntimeError(f"unknown relation: {relation_id}")
        return self.relations.pop(relation_id)

    def has_relation(self, required: dict) -> bool:
        return any(
            relation["body"] == required["body"]
            and relation["relation"] == required["relation"]
            and relation["world"] == required["world"]
            for relation in self.relations.values()
        )

    def evaluate_capability(self, name: str) -> dict:
        capability = self.capabilities.get(name)
        if capability is None:
            return {
                "available": False,
                "reasons": ["capability_not_declared"],
            }

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
