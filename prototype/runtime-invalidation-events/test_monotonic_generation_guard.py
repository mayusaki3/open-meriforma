"""Suite 58: trusted-counter assumptions and fail-closed mismatch tests."""
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from causal_integrated_can import CausalIntegratedCan
from monotonic_generation_guard import MonotonicGenerationGuard as Guard, SimulatedWitness


def ready(boot, challenge):
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id=boot, challenge=challenge)
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected fail-closed rejection")


with TemporaryDirectory() as folder:
    path = Path(folder) / "history.sqlite"
    snapshot = Path(folder) / "snapshot.sqlite"
    witness = SimulatedWitness()
    guard = Guard(str(path), witness, initialize=True)
    guard.bind(ready("M1", "C1"), now=0.04)
    assert witness.value == 1
    guard.close()
    shutil.copy2(path, snapshot)
    guard = Guard(str(path), witness)
    guard.bind(ready("M2", "C2"), now=0.04)
    assert witness.value == 2
    guard.close()
    print("PASS independent witness advances with committed generation")

    shutil.copy2(snapshot, path)
    rejects(lambda: Guard(str(path), witness))
    print("PASS coherent SQLite rollback refused against newer witness")

    stale = SimulatedWitness(0)
    rejects(lambda: Guard(str(path), stale))
    print("PASS stale witness rejected when database anchor is newer")

    # Even a clean DB cannot recover a witness advanced before its own COMMIT.
    witness.value = 2
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE generation_anchor SET sequence=1")
        db.commit()
    rejects(lambda: Guard(str(path), witness))
    print("PASS witness-ahead interrupted commit refuses automatic recovery")

with TemporaryDirectory() as folder:
    path = Path(folder) / "history.sqlite"
    witness = SimulatedWitness()
    guard = Guard(str(path), witness, initialize=True)
    guard.bind(ready("M1", "C1"), now=0.04)
    rejects(lambda: guard.bind(ready("M1", "C1"), now=0.04))
    assert witness.value == 2
    assert guard.registry.current.revoked
    rejects(lambda: guard.bind(ready("M2", "C2"), now=0.04))
    guard.close()
    print("PASS failed duplicate reservation strands witness ahead and revokes receiver")

print("PASS all monotonic-generation-guard checks")
