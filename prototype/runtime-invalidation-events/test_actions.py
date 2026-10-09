import importlib.util
import json
from pathlib import Path

from actions import PolicyActions
from events import InvalidationEvents

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


world = load("world_runtime_actions", ROOT / "external-object-relation" / "runtime.py")
execution = load("external_execution_actions", ROOT / "external-object-relation" / "execution.py")
use = load("external_use_actions", ROOT / "external-object-relation" / "object_use.py")
definition = json.loads((ROOT / "external-object-relation" / "model.json").read_text(encoding="utf-8"))
graph = world.BodyWorldGraph(definition)
graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
leases = execution.ResourceLeases(definition)
rights = use.ExternalObjectUse(graph.world_entities)
active = execution.CapabilityExecution(graph, "cane_controlled_use", leases, rights)
assert active.start()
graph.remove_relation("grasp")
assert active.validate()["state"] == "invalidated"
events = InvalidationEvents()
event = events.observe("world_interaction", "cane_action_01", active.validate())
assert event is not None

actions = PolicyActions()
stop = actions.request(event, "request_stop")
assert stop["state"] == "requested"
assert leases.holders["hand_01:gripper"] is active
assert rights.holds(active.object_requests(), active)
print("PASS action request leaves existing execution authority intact")

actions.transition(stop["action_id"], "accepted")
actions.transition(stop["action_id"], "executing")
actions.transition(stop["action_id"], "completed", completion_report="executor reported stop")
assert stop["state"] == "completed"
assert active.state == "invalidated"
assert leases.holders["hand_01:gripper"] is active
print("PASS action completion report is not proof of safety or automatic lease release")

events.acknowledge(event["event_id"])
assert stop["state"] == "completed"
assert active.state == "invalidated"
try:
    actions.request(event, "request_stop")
except RuntimeError:
    pass
else:
    raise AssertionError("duplicate action request accepted")
print("PASS event acknowledgment and action lifecycle are independent")

other_event = {"event_id": 999, "acknowledged": False}
failed = actions.request(other_event, "request_handoff")
actions.transition(failed["action_id"], "accepted")
actions.transition(failed["action_id"], "failed", failure_reason="executor unavailable")
assert failed["state"] == "failed"
assert failed["failure_reason"] == "executor unavailable"
assert leases.holders["hand_01:gripper"] is active
assert rights.holds(active.object_requests(), active)
print("PASS failed action retains control and object-use rights")

for target in ("completed", "executing", "requested"):
    try:
        actions.transition(failed["action_id"], target)
    except RuntimeError:
        pass
    else:
        raise AssertionError(f"illegal transition allowed: failed -> {target}")
try:
    actions.transition(stop["action_id"], "failed", failure_reason="late failure")
except RuntimeError:
    pass
else:
    raise AssertionError("terminal action changed")
print("PASS terminal states and illegal transitions are enforced")

active.finish()
assert not leases.holders and not rights.holders
assert stop["state"] == "completed" and failed["state"] == "failed"
print("PASS explicit execution finish independently releases retained rights")
print("PASS all policy-action-lifecycle checks")
