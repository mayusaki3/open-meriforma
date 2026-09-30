import json
from pathlib import Path

from runtime import BodyGraph

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
