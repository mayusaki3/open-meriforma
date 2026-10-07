import json
from pathlib import Path

from runtime import BodyWorldGraph

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
graph = BodyWorldGraph(definition)

assert "hand_01" in graph.body_entities
assert "tool_01" in graph.world_entities
assert "tool_01" not in graph.body_entities
print("PASS body and world entities keep separate graph membership")

assert graph.evaluate_capability("tool_use")["available"] is False
assert graph.evaluate_capability("supported_stance")["available"] is False
print("PASS relation-dependent capabilities start unavailable")

graph.add_relation("hand_tool_grasp", "hand_01", "grasp", "tool_01")
assert graph.evaluate_capability("tool_use")["available"] is True
assert graph.evaluate_capability("supported_stance")["available"] is False
print("PASS grasp relation enables only its dependent capability")

graph.add_relation("foot_floor_support", "foot_01", "support", "floor_01")
assert graph.evaluate_capability("tool_use")["available"] is True
assert graph.evaluate_capability("supported_stance")["available"] is True
print("PASS independent interaction relations can coexist")

removed = graph.remove_relation("hand_tool_grasp")
assert removed == {
    "body": "hand_01",
    "relation": "grasp",
    "world": "tool_01",
}
assert graph.evaluate_capability("tool_use")["available"] is False
assert graph.evaluate_capability("supported_stance")["available"] is True
assert "tool_01" in graph.world_entities
assert "tool_01" not in graph.body_entities
print("PASS removing interaction removes dependency without deleting world object")

graph.add_relation("hand_tool_contact", "hand_01", "contact", "tool_01")
graph.add_relation("hand_tool_grasp", "hand_01", "grasp", "tool_01")
assert len(graph.relations) == 3
assert graph.evaluate_capability("tool_use")["available"] is True
print("PASS one external object can participate in multiple relations")

try:
    graph.add_relation("invalid_body", "missing_hand", "grasp", "tool_01")
except RuntimeError as exc:
    print(f"PASS invalid body endpoint rejected: {exc}")
else:
    raise AssertionError("invalid body endpoint accepted")

try:
    graph.add_relation("invalid_world", "hand_01", "grasp", "missing_tool")
except RuntimeError as exc:
    print(f"PASS invalid world endpoint rejected: {exc}")
else:
    raise AssertionError("invalid world endpoint accepted")

print("PASS all external-object-relation checks")
