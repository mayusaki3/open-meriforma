import json
from pathlib import Path

from runtime import BodyGraph

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "body.json").read_text(encoding="utf-8"))
graph = BodyGraph(definition)
connections = {item["id"]: item for item in definition["connections"]}

assert graph.connected("thigh", "leg")
assert graph.connected("leg", "foot")
assert not graph.connected("thigh", "foot")
assert graph.reachable("thigh", "foot")
assert graph.capability_available("stance")
print("PASS three-unit chain provides cross-unit stance capability")
print("PASS thigh and foot are reachable without direct connection")

graph.disconnect("leg_foot")
assert graph.connected("thigh", "leg")
assert not graph.reachable("thigh", "foot")
assert not graph.capability_available("stance")
print("PASS middle-chain disconnect splits body component and removes stance")

graph.connect(connections["leg_foot"])
assert graph.reachable("thigh", "foot")
assert graph.capability_available("stance")
print("PASS reconnect restores body component and stance")

bad = {
    "id": "bad",
    "a": {"unit": "leg", "port": "missing"},
    "b": {"unit": "foot", "port": "proximal"},
}
try:
    graph.connect(bad)
except RuntimeError as exc:
    print(f"PASS invalid port rejected: {exc}")
else:
    raise AssertionError("invalid port was accepted")

stance_resources = [
    "thigh:hip_pitch",
    "leg:knee_pitch",
    "foot:ankle_pitch",
    "foot:ankle_roll",
]
graph.acquire_resources("stance_controller", stance_resources)
assert all(graph.ownership.owners[item] == "stance_controller" for item in stance_resources)
print("PASS one controller owns resources across three units")

try:
    graph.acquire_resources("foot_motion_controller", ["foot:ankle_pitch"])
except RuntimeError as exc:
    print(f"PASS cross-unit ownership conflict rejected: {exc}")
else:
    raise AssertionError("ownership conflict was accepted")

graph.release_resources("stance_controller")
graph.acquire_resources(
    "foot_motion_controller", ["foot:ankle_pitch", "foot:ankle_roll"]
)
assert graph.ownership.owners["foot:ankle_pitch"] == "foot_motion_controller"
print("PASS released cross-unit resources can be reacquired by another controller")

graph.release_resources("foot_motion_controller")
graph.acquire_resources("stance_controller", stance_resources)
graph.disconnect("leg_foot")
isolated = graph.disconnected_owned_resources("stance_controller", "thigh")
assert isolated == ["foot:ankle_pitch", "foot:ankle_roll"]
assert graph.ownership.owners["foot:ankle_pitch"] == "stance_controller"
print(f"PASS graph disconnect detects isolated owned resources: {isolated}")
print("PASS detection does not silently release ownership")
graph.connect(connections["leg_foot"])
assert graph.disconnected_owned_resources("stance_controller", "thigh") == []
graph.release_resources("stance_controller")
print("PASS reconnect restores ownership reachability")

assert graph.evaluate_capability("stance") == {
    "available": True,
    "reasons": [],
}
graph.disconnect("leg_foot")
evaluation = graph.evaluate_capability("stance")
assert evaluation["available"] is False
assert "unreachable_unit:foot" in evaluation["reasons"]
print(f"PASS capability reports topology reason: {evaluation}")
graph.connect(connections["leg_foot"])
assert graph.evaluate_capability("stance")["available"] is True
print("PASS capability reason clears after topology recovery")

ready = graph.evaluate_capability_readiness("stance", "stance_controller")
assert ready["available"] is True
assert ready["ready"] is True
assert ready["blocked_resources"] == {}
print("PASS available capability is ready when required resources are free")

graph.acquire_resources(
    "foot_motion_controller", ["foot:ankle_pitch", "foot:ankle_roll"]
)
blocked = graph.evaluate_capability_readiness("stance", "stance_controller")
assert blocked["available"] is True
assert blocked["ready"] is False
assert blocked["blocked_resources"] == {
    "foot:ankle_pitch": "foot_motion_controller",
    "foot:ankle_roll": "foot_motion_controller",
}
print(f"PASS resource contention blocks readiness without removing availability: {blocked}")

same_owner = graph.evaluate_capability_readiness("stance", "foot_motion_controller")
assert same_owner["available"] is True
assert same_owner["ready"] is True
print("PASS resources already owned by requester do not block readiness")
graph.release_resources("foot_motion_controller")

print("PASS all virtual-body-graph checks")
