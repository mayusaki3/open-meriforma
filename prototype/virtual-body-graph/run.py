import json
from pathlib import Path

from runtime import BodyGraph

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "body.json").read_text(encoding="utf-8"))
graph = BodyGraph(definition)
connection = definition["connections"][0]

print(f"Body       : {definition['body_id']}")
print(f"Connection : {graph.summary()}")
print(f"stance     : {graph.capability_available('stance')}")

graph.disconnect("leg_foot")
print("-- disconnect leg_foot --")
print(f"Connection : {graph.summary()}")
print(f"stance     : {graph.capability_available('stance')}")

graph.connect(connection)
print("-- reconnect leg_foot --")
print(f"Connection : {graph.summary()}")
print(f"stance     : {graph.capability_available('stance')}")
