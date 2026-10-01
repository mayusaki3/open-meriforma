import json
from pathlib import Path

from runtime import BodyGraph, CapabilityExecution

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "body.json").read_text(encoding="utf-8"))
graph = BodyGraph(definition)
graph.set_observation_source_available("foot:sole_contact", True)
graph.set_health_state("foot:ankle_pitch", "ok")
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
assert graph.ownership.owners == {}
print("PASS reconnect restores ownership reachability")
print("PASS scenario cleanup releases ownership before next evaluation")

evaluation = graph.evaluate_capability("stance")
assert evaluation["available"] is True
assert evaluation["reasons"] == []
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

execution = CapabilityExecution(graph, "stance", "stance_execution")
execution.start()
assert execution.state == "active"
assert graph.ownership.owners["thigh:hip_pitch"] == "stance_execution"
assert graph.ownership.owners["foot:ankle_roll"] == "stance_execution"
print("PASS capability execution atomically acquires cross-unit control resources")

assert execution.validate() is True
graph.disconnect("leg_foot")
assert execution.validate() is False
assert execution.state == "invalidated"
assert "unreachable_unit:foot" in execution.reasons
assert graph.ownership.owners["foot:ankle_pitch"] == "stance_execution"
print(f"PASS active execution detects topology invalidation: {execution.reasons}")
print("PASS invalidation does not silently release owned resources")

graph.connect(connections["leg_foot"])
assert execution.state == "invalidated"
print("PASS topology recovery does not silently reactivate invalidated execution")
execution.finish()
assert execution.state == "finished"
assert graph.ownership.owners == {}
print("PASS explicit finish releases execution resources")

blocked_owner = "foot_motion_controller"
graph.acquire_resources(blocked_owner, ["foot:ankle_pitch"])
rejected = CapabilityExecution(graph, "stance", "blocked_stance")
try:
    rejected.start()
except RuntimeError as exc:
    assert rejected.state == "rejected"
    print(f"PASS execution request rejected when not ready: {exc}")
else:
    raise AssertionError("blocked execution unexpectedly started")
graph.release_resources(blocked_owner)

race = CapabilityExecution(graph, "stance", "race_stance")
precheck = graph.evaluate_capability_readiness("stance", "race_stance")
assert precheck["available"] is True and precheck["ready"] is True
graph.acquire_resources("late_controller", ["foot:ankle_pitch"])
try:
    race.start()
except RuntimeError as exc:
    assert race.state == "rejected"
    assert any(reason.startswith("resource_owned:") for reason in race.reasons)
    print(f"PASS start rechecks readiness after stale external precheck: {exc}")
else:
    raise AssertionError("execution started after resource changed following precheck")
graph.release_resources("late_controller")

original_acquire = graph.acquire_resources
injected = {"done": False}

def acquire_with_interleaving(owner: str, resources: list[str]) -> None:
    if owner == "atomic_stance" and not injected["done"]:
        injected["done"] = True
        original_acquire("interleaving_controller", ["foot:ankle_pitch"])
    original_acquire(owner, resources)

graph.acquire_resources = acquire_with_interleaving
atomic = CapabilityExecution(graph, "stance", "atomic_stance")
try:
    atomic.start()
except RuntimeError as exc:
    assert atomic.state == "rejected"
    assert any(reason.startswith("acquire_failed:") for reason in atomic.reasons)
    assert "thigh:hip_pitch" not in graph.ownership.owners
    assert graph.ownership.owners["foot:ankle_pitch"] == "interleaving_controller"
    print(f"PASS atomic acquire is final execution-start commit point: {exc}")
else:
    raise AssertionError("execution started despite acquire-time ownership conflict")
finally:
    graph.acquire_resources = original_acquire
    graph.release_resources("interleaving_controller")

observation_execution = CapabilityExecution(
    graph, "stance", "observation_stance"
)
observation_execution.start()
assert observation_execution.state == "active"
graph.set_observation_source_available("foot:sole_contact", False)
assert observation_execution.validate() is False
assert observation_execution.state == "invalidated"
assert "observation_unavailable:foot:sole_contact" in observation_execution.reasons
assert graph.ownership.owners["foot:ankle_pitch"] == "observation_stance"
print(
    "PASS generic execution validation detects observation condition loss: "
    f"{observation_execution.reasons}"
)
graph.set_observation_source_available("foot:sole_contact", True)
assert observation_execution.state == "invalidated"
print("PASS observation recovery does not silently reactivate execution")
observation_execution.finish()
assert graph.ownership.owners == {}

graph.set_observation_source_available("foot:sole_contact", False)
observation_eval = graph.evaluate_capability("stance")
assert observation_eval["available"] is False
assert "observation_unavailable:foot:sole_contact" in observation_eval["reasons"]
print(f"PASS capability availability reports observation reason: {observation_eval}")
graph.set_observation_source_available("foot:sole_contact", True)

structured = graph.evaluate_capability("stance")
categories = {item["category"] for item in structured["conditions"]}
assert {"resource", "topology", "observation"}.issubset(categories)
assert all(item["satisfied"] for item in structured["conditions"])
print(f"PASS capability evaluation exposes structured condition categories: {sorted(categories)}")

graph.disconnect("leg_foot")
graph.set_observation_source_available("foot:sole_contact", False)
multi_failure = graph.evaluate_capability("stance")
failed = [item for item in multi_failure["conditions"] if not item["satisfied"]]
failed_categories = {item["category"] for item in failed}
assert "topology" in failed_categories
assert "observation" in failed_categories
assert "unreachable_unit:foot" in multi_failure["reasons"]
assert "observation_unavailable:foot:sole_contact" in multi_failure["reasons"]
print(
    "PASS one evaluation preserves multiple failed condition categories: "
    f"{sorted(failed_categories)}"
)
graph.connect(connections["leg_foot"])
graph.set_observation_source_available("foot:sole_contact", True)

graph.set_health_state("foot:ankle_pitch", "degraded")
degraded = graph.evaluate_capability("stance")
assert degraded["available"] is True
health_condition = next(
    item for item in degraded["conditions"] if item["category"] == "health"
)
assert health_condition["state"] == "degraded"
assert health_condition["satisfied"] is True
print("PASS degraded health remains distinguishable while capability stays available")

health_execution = CapabilityExecution(graph, "stance", "health_stance")
health_execution.start()
graph.set_health_state("foot:ankle_pitch", "unavailable")
assert health_execution.validate() is False
assert health_execution.state == "invalidated"
assert "health_not_usable:foot:ankle_pitch:unavailable" in health_execution.reasons
print(
    "PASS generic execution validation detects runtime health loss: "
    f"{health_execution.reasons}"
)
graph.set_health_state("foot:ankle_pitch", "ok")
assert health_execution.state == "invalidated"
health_execution.finish()

graph.set_health_state("foot:ankle_pitch", "unknown")
unknown_health = graph.evaluate_capability("stance")
assert unknown_health["available"] is False
assert "health_not_usable:foot:ankle_pitch:unknown" in unknown_health["reasons"]
print("PASS unknown health is not silently treated as usable")
graph.set_health_state("foot:ankle_pitch", "ok")

print("PASS all virtual-body-graph checks")
