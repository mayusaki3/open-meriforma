import json
from pathlib import Path

from runtime import BodyWorldGraph
from execution import CapabilityExecution

definition = json.loads((Path(__file__).resolve().parent / "model.json").read_text(encoding="utf-8"))
graph = BodyWorldGraph(definition)

rejected = CapabilityExecution(graph, "assisted_stance")
assert rejected.start() is False and rejected.state == "rejected"
rejected.finish()
print("PASS execution rejects unavailable realization without starting")

graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
graph.add_world_relation("contact", "cane_01", "contact", "floor_01")
graph.add_relation("support", "foot_01", "support", "floor_01")
graph.set_constraint_state("cane_load_capacity", True)
graph.set_constraint_state("contact_stability", True)
execution = CapabilityExecution(graph, "assisted_stance")
assert execution.start() is True
assert execution.validate()["state"] == "active"
print("PASS execution starts when realization is available")

graph.remove_relation("contact")
result = execution.validate()
assert result["state"] == "invalidated"
assert any(reason.startswith("required_relation_missing:") for reason in result["reasons"])
print("PASS relation loss invalidates active execution")

graph.add_world_relation("contact", "cane_01", "contact", "floor_01")
assert graph.evaluate_capability("assisted_stance")["available"] is True
assert execution.validate()["state"] == "invalidated"
print("PASS relation recovery does not automatically reactivate execution")
execution.finish()
assert execution.state == "finished"
new_execution = CapabilityExecution(graph, "assisted_stance")
assert new_execution.start() is True
new_execution.finish()
print("PASS explicit new execution can start after recovery")

constraint_execution = CapabilityExecution(graph, "assisted_stance")
assert constraint_execution.start() is True
graph.set_constraint_state("contact_stability", None)
result = constraint_execution.validate()
assert result["state"] == "invalidated"
assert "constraint_unknown:contact_stability" in result["reasons"]
graph.set_constraint_state("contact_stability", True)
assert constraint_execution.validate()["state"] == "invalidated"
constraint_execution.finish()
print("PASS unknown constraint invalidates without automatic restart")

print("PASS all external-object execution checks")
