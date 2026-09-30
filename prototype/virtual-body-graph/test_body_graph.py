import json
from pathlib import Path

from runtime import BodyGraph

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "body.json").read_text(encoding="utf-8"))
graph = BodyGraph(definition)
connection = definition["connections"][0]

assert graph.connected("leg", "foot")
assert graph.capability_available("stance")
print("PASS connected leg + foot provides cross-unit stance capability")

graph.disconnect("leg_foot")
assert not graph.connected("leg", "foot")
assert not graph.capability_available("stance")
print("PASS disconnect removes cross-unit stance availability")

graph.connect(connection)
assert graph.connected("leg", "foot")
assert graph.capability_available("stance")
print("PASS reconnect restores cross-unit stance availability")

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
