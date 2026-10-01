import json
from pathlib import Path

from runtime import TwinMappingGraph

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "mapping.json").read_text(encoding="utf-8"))
graph = TwinMappingGraph(definition)

foot = graph.mapping("foot_twin")
assert foot is not None
assert foot["physical"] == "physical_foot_01"
assert foot["virtual"] == "virtual_foot_sim"
print("PASS physical and virtual units keep independent identities")

assert graph.mappings_for_virtual("virtual_test_only") == []
print("PASS virtual unit can exist without physical mapping")

removed = graph.remove_mapping("foot_twin")
assert removed["physical"] == "physical_foot_01"
assert graph.mappings_for_physical("physical_foot_01") == []
assert "physical_foot_01" in graph.physical_units
assert "virtual_foot_sim" in graph.virtual_units
print("PASS removing mapping does not remove either unit")

graph.add_mapping(removed)
assert graph.mapping("foot_twin") is not None
print("PASS mapping can be restored independently of unit identity")

channels = {item["name"]: item["direction"] for item in foot["channels"]}
assert channels["joint_state"] == "physical_to_virtual"
assert channels["command_preview"] == "virtual_to_physical"
print("PASS synchronization direction is mapping metadata, not unit type")

try:
    graph.add_mapping({
        "id": "invalid",
        "physical": "missing_physical",
        "virtual": "virtual_foot_sim",
        "channels": [],
    })
except RuntimeError as exc:
    print(f"PASS invalid mapping endpoint rejected: {exc}")
else:
    raise AssertionError("invalid mapping endpoint accepted")

print("PASS all physical-virtual-mapping checks")
