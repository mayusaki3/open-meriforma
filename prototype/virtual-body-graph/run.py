import json
from pathlib import Path

from runtime import BodyGraph, CapabilityExecution

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "body.json").read_text(encoding="utf-8"))
graph = BodyGraph(definition)
connections = {item["id"]: item for item in definition["connections"]}

print(f"Body       : {definition['body_id']}")
print(f"Connection : {graph.summary()}")
print(f"direct thigh-foot : {graph.connected('thigh', 'foot')}")
print(f"reach  thigh-foot : {graph.reachable('thigh', 'foot')}")
print(f"stance            : {graph.capability_available('stance')}")

graph.disconnect("leg_foot")
print("-- disconnect leg_foot --")
print(f"Connection        : {graph.summary()}")
print(f"reach  thigh-foot : {graph.reachable('thigh', 'foot')}")
print(f"stance            : {graph.capability_available('stance')}")

graph.connect(connections["leg_foot"])
print("-- reconnect leg_foot --")
print(f"Connection        : {graph.summary()}")
print(f"reach  thigh-foot : {graph.reachable('thigh', 'foot')}")
print(f"stance            : {graph.capability_available('stance')}")

print("-- cross-unit resource ownership --")
stance_resources = [
    "thigh:hip_pitch",
    "leg:knee_pitch",
    "foot:ankle_pitch",
    "foot:ankle_roll",
]
graph.acquire_resources("stance_controller", stance_resources)
print(f"owner              : {graph.ownership_summary()}")
try:
    graph.acquire_resources("foot_motion_controller", ["foot:ankle_pitch"])
except RuntimeError as exc:
    print(f"conflict           : {exc}")
graph.release_resources("stance_controller")
graph.acquire_resources("foot_motion_controller", ["foot:ankle_pitch", "foot:ankle_roll"])
print(f"after release      : {graph.ownership_summary()}")

graph.release_resources("foot_motion_controller")
graph.acquire_resources("stance_controller", stance_resources)
graph.disconnect("leg_foot")
print("-- disconnect while stance owns resources --")
print(f"owner              : {graph.ownership_summary()}")
print(
    "isolated           : "
    + str(graph.disconnected_owned_resources("stance_controller", "thigh"))
)
graph.connect(connections["leg_foot"])
print(
    "after reconnect    : "
    + str(graph.disconnected_owned_resources("stance_controller", "thigh"))
)
graph.release_resources("stance_controller")
print(f"after cleanup       : {graph.ownership_summary()}")

print("-- capability evaluation reason --")
print(f"evaluation          : {graph.evaluate_capability('stance')}")
graph.disconnect("leg_foot")
print(f"after disconnect    : {graph.evaluate_capability('stance')}")
graph.connect(connections["leg_foot"])
print(f"after reconnect     : {graph.evaluate_capability('stance')}")

print("-- availability vs resource readiness --")
print(
    "free resources      : "
    + str(graph.evaluate_capability_readiness("stance", "stance_controller"))
)
graph.acquire_resources(
    "foot_motion_controller", ["foot:ankle_pitch", "foot:ankle_roll"]
)
print(
    "owned by other      : "
    + str(graph.evaluate_capability_readiness("stance", "stance_controller"))
)
print(
    "same requester      : "
    + str(graph.evaluate_capability_readiness("stance", "foot_motion_controller"))
)
graph.release_resources("foot_motion_controller")

print("-- capability execution lifecycle --")
execution = CapabilityExecution(graph, "stance", "stance_execution")
execution.start()
print(f"started             : state={execution.state}")
print(f"owner               : {graph.ownership_summary()}")
print(f"validate            : {execution.validate()}")

graph.disconnect("leg_foot")
print(f"after disconnect    : valid={execution.validate()} state={execution.state}")
print(f"reasons             : {execution.reasons}")
print(f"owner retained      : {graph.ownership_summary()}")

graph.connect(connections["leg_foot"])
print(f"after reconnect     : state={execution.state}")
execution.finish()
print(f"after finish        : state={execution.state} owner={graph.ownership_summary()}")

graph.acquire_resources("foot_motion_controller", ["foot:ankle_pitch"])
blocked = CapabilityExecution(graph, "stance", "blocked_stance")
try:
    blocked.start()
except RuntimeError as exc:
    print(f"blocked start       : state={blocked.state} error={exc}")
graph.release_resources("foot_motion_controller")
