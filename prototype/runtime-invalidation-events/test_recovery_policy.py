import importlib.util
import json
from pathlib import Path

from actions import PolicyActions
from recovery_policy import RecoveryPolicy

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


world = load("world_recovery", ROOT / "external-object-relation" / "runtime.py")
execution = load("execution_recovery", ROOT / "external-object-relation" / "execution.py")
use = load("use_recovery", ROOT / "external-object-relation" / "object_use.py")
definition = json.loads((ROOT / "external-object-relation" / "model.json").read_text(encoding="utf-8"))
graph = world.BodyWorldGraph(definition)
graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
leases = execution.ResourceLeases(definition)
rights = use.ExternalObjectUse(graph.world_entities)
active = execution.CapabilityExecution(graph, "cane_controlled_use", leases, rights)
assert active.start()
graph.remove_relation("grasp")
assert active.validate()["state"] == "invalidated"

actions = PolicyActions()
policy = RecoveryPolicy()


def make_action(event_id):
    action = actions.request({"event_id": event_id}, "request_stop")
    actions.transition(action["action_id"], "accepted")
    actions.transition(action["action_id"], "executing")
    actions.transition(action["action_id"], "completed", completion_report="synthetic stop reported")
    return action


for event_id, status, expected in [
    (1, "verified", "hold_for_explicit_recovery"),
    (2, "not_verified", "request_stop_escalation"),
    (3, "unknown", "request_evidence_or_safe_fallback"),
]:
    action = make_action(event_id)
    result = policy.assess(action, {"action_id": action["action_id"], "status": status})
    assert result["recommendation"] == expected
    assert result["automatic_resume"] is False and result["lease_mutation"] is False
    assert active.state == "invalidated"
    assert leases.holders["hand_01:gripper"] is active
    assert rights.holds(active.object_requests(), active)
    print(f"PASS {status} policy recommendation does not resume or release authority")

try:
    policy.assess(actions.actions[1], {"action_id": 1, "status": "verified"})
except RuntimeError:
    pass
else:
    raise AssertionError("duplicate policy decision accepted")
try:
    policy.assess(actions.actions[2], {"action_id": 999, "status": "verified"})
except ValueError:
    pass
else:
    raise AssertionError("mismatched verification accepted")
handoff = actions.request({"event_id": 4}, "request_handoff")
try:
    policy.assess(handoff, {"action_id": handoff["action_id"], "status": "verified"})
except ValueError:
    pass
else:
    raise AssertionError("handoff assessed by STOP policy")
print("PASS duplicate, mismatched, and wrong-action recovery decisions rejected")

graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
assert active.validate()["state"] == "invalidated"
assert leases.holders["hand_01:gripper"] is active
active.finish()
assert not leases.holders and not rights.holders
assert all(not item["automatic_resume"] for item in policy.decisions.values())
print("PASS relation restoration does not auto-resume and explicit finish releases rights")
print("PASS all recovery-policy checks")
