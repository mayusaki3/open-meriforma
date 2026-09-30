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

print("PASS all virtual-body-graph checks")
