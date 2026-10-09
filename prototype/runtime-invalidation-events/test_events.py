import importlib.util
import json
from pathlib import Path

from events import InvalidationEvents, PolicyInbox

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


body = load("body_runtime", ROOT / "virtual-body-graph" / "runtime.py")
world = load("world_runtime", ROOT / "external-object-relation" / "runtime.py")
external = load("external_execution", ROOT / "external-object-relation" / "execution.py")
use = load("external_use", ROOT / "external-object-relation" / "object_use.py")

events = InvalidationEvents()
policy = PolicyInbox()

# Body topology loss: use the existing BodyGraph and its real execution lifecycle.
body_def = {
    "units": {
        "leg": {"ports": ["foot"], "resources": ["knee"]},
        "foot": {"ports": ["leg"], "resources": ["ankle"]},
    },
    "connections": [{"id": "leg_foot", "a": {"unit": "leg", "port": "foot"},
                     "b": {"unit": "foot", "port": "leg"}}],
    "capabilities": {
        "stance": {"declared": True, "required_units": ["leg", "foot"],
                   "required_resources": ["leg:knee", "foot:ankle"],
                   "control_resources": ["leg:knee", "foot:ankle"]}
    },
}
graph = body.BodyGraph(body_def)
stance = body.CapabilityExecution(graph, "stance", "stance_controller")
stance.start()
assert stance.validate()
graph.disconnect("leg_foot")
assert stance.validate() is False
body_event = events.observe("body_graph", "stance_01", {
    "state": stance.state, "reasons": stance.reasons
})
assert body_event["event_id"] == 1
assert "unreachable_unit:foot" in body_event["reasons"]
assert set(graph.ownership.owners) == {"leg:knee", "foot:ankle"}
print("PASS body graph topology loss emits event without releasing control")

# External relation loss: use the existing BodyWorldGraph and execution lifecycle.
world_def = json.loads((ROOT / "external-object-relation" / "model.json").read_text(encoding="utf-8"))
world_graph = world.BodyWorldGraph(world_def)
world_graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
leases = external.ResourceLeases(world_def)
rights = use.ExternalObjectUse(world_graph.world_entities)
cane = external.CapabilityExecution(world_graph, "cane_controlled_use", leases, rights)
assert cane.start()
world_graph.remove_relation("grasp")
assert cane.validate()["state"] == "invalidated"
world_event = events.observe("world_interaction", "cane_01", cane.validate())
assert world_event["event_id"] == 2
assert any(reason.startswith("required_relation_missing:") for reason in world_event["reasons"])
assert leases.holders.get("hand_01:gripper") is cane
assert rights.holds(cane.object_requests(), cane)
print("PASS world relation loss emits event without releasing body or object rights")

assert events.observe("body_graph", "stance_01", {"state": stance.state, "reasons": stance.reasons}) is None
assert events.observe("world_interaction", "cane_01", cane.validate()) is None
assert len(events.pending) == 2
print("PASS repeated validation does not duplicate invalidation events")

# Policy decisions and acknowledgment do not execute physical safety actions.
policy.decide(body_event, "request_stop")
policy.decide(world_event, "request_handoff")
assert policy.decisions == {1: "request_stop", 2: "request_handoff"}
assert len(events.pending) == 2
assert graph.ownership.owners and leases.holders
events.acknowledge(1)
assert 1 not in events.pending and 2 in events.pending
assert graph.ownership.owners and leases.holders
print("PASS policy decision and event acknowledgment do not mutate ownership")

# Recovery cannot resurrect invalidated execution; explicit finish is independent.
graph.connect(body_def["connections"][0])
world_graph.add_relation("grasp", "hand_01", "grasp", "cane_01")
assert stance.state == "invalidated"
assert cane.validate()["state"] == "invalidated"
events.acknowledge(2)
stance.finish()
cane.finish()
assert not graph.ownership.owners and not leases.holders and not rights.holders
assert all(item["acknowledged"] for item in events.history)
print("PASS recovery requires explicit lifecycle cleanup, independent of event acknowledgment")
print("PASS all runtime-invalidation-events checks")
