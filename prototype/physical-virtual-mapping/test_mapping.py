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
assert graph.mapping("foot_twin") is None
assert len(graph.mappings_for_physical("physical_foot_01")) == 3
assert "physical_foot_01" in graph.physical_units
assert "virtual_foot_sim" in graph.virtual_units
print("PASS removing mapping removes only that relation and keeps both units")

graph.add_mapping(removed)
assert graph.mapping("foot_twin") is not None
assert len(graph.mappings_for_physical("physical_foot_01")) == 4
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

physical_foot_mappings = graph.mappings_for_physical("physical_foot_01")
assert len(physical_foot_mappings) == 4
assert {
    item["virtual"] for item in physical_foot_mappings
} == {
    "virtual_foot_sim",
    "virtual_foot_observer",
    "virtual_lower_body",
    "virtual_foot_calibration",
}
print("PASS one physical unit can map to multiple virtual units")

lower_body_mappings = graph.mappings_for_virtual("virtual_lower_body")
assert len(lower_body_mappings) == 2
assert {
    item["physical"] for item in lower_body_mappings
} == {"physical_foot_01", "physical_leg_01"}
print("PASS multiple physical units can map to one aggregate virtual unit")

observer = graph.mapping("foot_observer_mapping")
lower_foot = graph.mapping("foot_lower_body_mapping")
lower_leg = graph.mapping("leg_lower_body_mapping")
assert observer is not None and observer["scope"] == ["sole_contact"]
assert lower_foot is not None and lower_foot["scope"] == ["ankle_pitch", "ankle_roll"]
assert lower_leg is not None and lower_leg["scope"] == ["knee_pitch"]
print("PASS mappings can describe different partial scopes")

removed_observer = graph.remove_mapping("foot_observer_mapping")
assert graph.mapping("foot_observer_mapping") is None
assert graph.mapping("foot_twin") is not None
assert graph.mapping("foot_lower_body_mapping") is not None
assert "physical_foot_01" in graph.physical_units
assert "virtual_foot_observer" in graph.virtual_units
print("PASS removing one relation does not disturb parallel mappings or units")
graph.add_mapping(removed_observer)

conflicts = graph.command_authority_conflicts()
assert conflicts == {
    "physical_foot_01:ankle_pitch": [
        "foot_twin",
        "foot_calibration_command",
    ]
}
print(f"PASS overlapping command authority is detected: {conflicts}")

graph.remove_mapping("foot_calibration_command")
assert graph.command_authority_conflicts() == {}
assert graph.mapping("foot_twin") is not None
print("PASS removing competing command relation clears authority conflict")

calibration_mapping = next(
    item
    for item in definition["mappings"]
    if item["id"] == "foot_calibration_command"
)
graph.add_mapping(calibration_mapping)
assert "physical_foot_01:ankle_pitch" in graph.command_authority_conflicts()
print("PASS competing command candidate can coexist again before runtime selection")

observer_mappings = [
    item
    for item in graph.mappings_for_physical("physical_foot_01")
    if any(
        channel.get("direction") == "physical_to_virtual"
        for channel in item.get("channels", [])
    )
]
assert len(observer_mappings) >= 2
assert graph.command_authority_conflicts() == {
    "physical_foot_01:ankle_pitch": [
        "foot_twin",
        "foot_calibration_command",
    ]
}
print("PASS multiple physical-to-virtual observers do not add command conflicts")

graph.activate_command_authority("foot_twin")
assert graph.active_command_authority["physical_foot_01:ankle_pitch"] == "foot_twin"
assert graph.active_command_authority["physical_foot_01:ankle_roll"] == "foot_twin"
print("PASS one mapping can become active command authority for its scope")

try:
    graph.activate_command_authority("foot_calibration_command")
except RuntimeError as exc:
    print(f"PASS parallel command candidate cannot seize active authority: {exc}")
else:
    raise AssertionError("parallel command authority was activated without handoff")

graph.handoff_command_authority("foot_twin", "foot_calibration_command")
assert (
    graph.active_command_authority["physical_foot_01:ankle_pitch"]
    == "foot_calibration_command"
)
assert "physical_foot_01:ankle_roll" not in graph.active_command_authority
print("PASS explicit handoff transfers overlapping command authority")

graph.remove_mapping("foot_calibration_command")
assert "physical_foot_01:ankle_pitch" not in graph.active_command_authority
print("PASS removing active mapping clears its runtime command authority")

print("PASS all physical-virtual-mapping checks")
