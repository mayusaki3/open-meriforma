"""Child-only fault injection for temporary test databases."""
import os
import sys
from atomic_state import AtomicState

path, phase = sys.argv[1:]
store = AtomicState(path)
current = store.read("case")
assert current and current["revision"] == 1
updated = {kind: dict(value, marker="new") for kind, value in current["records"].items()}
if phase == "before_commit":
    store.db.execute("BEGIN IMMEDIATE")
    store.db.execute(
        "UPDATE atomic_snapshots SET revision=2,payload=? WHERE snapshot_key='case'",
        (__import__("json").dumps(updated),))
elif phase == "after_commit":
    assert store.write("case", updated, expected_revision=1) == 2
else:
    raise ValueError(phase)
os._exit(71)
