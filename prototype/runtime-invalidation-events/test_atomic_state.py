"""Local atomic snapshot tests with disposable child-process crashes."""
import subprocess
import sys
import tempfile
from pathlib import Path

from atomic_state import AtomicState

WORKER = Path(__file__).with_name("atomic_crash_worker.py")


def records(marker):
    return {
        "execution": {"state": "invalidated", "marker": marker},
        "event": {"event_id": 3, "marker": marker},
        "action": {"action_id": 8, "marker": marker},
        "verification": {"status": "unknown", "marker": marker},
        "correlation": {"generation": 2, "marker": marker},
    }


def run_crash(path, phase):
    result = subprocess.run(
        [sys.executable, str(WORKER), path, phase],
        capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 71, (phase, result.returncode, result.stderr)


with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "normal.sqlite")
    store = AtomicState(path)
    assert store.write("case", records("old")) == 1
    assert store.write("case", records("new"), expected_revision=1) == 2
    snapshot = store.read("case")
    assert snapshot["revision"] == 2
    assert all(v["marker"] == "new" for v in snapshot["records"].values())
    print("PASS all five records commit as one snapshot")

    try:
        store.write("case", records("stale"), expected_revision=1)
        raise AssertionError("stale revision was accepted")
    except RuntimeError as error:
        assert str(error) == "stale snapshot revision"
    assert store.read("case") == snapshot
    print("PASS stale revision cannot overwrite newer snapshot")

    try:
        store.write("case", {"execution": {}}, expected_revision=2)
        raise AssertionError("partial snapshot was accepted")
    except ValueError:
        pass
    assert store.read("case") == snapshot
    store.close()
    print("PASS incomplete batch rejected without mutation")

    for phase, expected_revision, expected_marker in (
            ("before_commit", 1, "old"),
            ("after_commit", 2, "new")):
        path = str(Path(directory) / (phase + ".sqlite"))
        store = AtomicState(path)
        assert store.write("case", records("old")) == 1
        store.close()
        run_crash(path, phase)
        restored = AtomicState(path)
        snapshot = restored.read("case")
        assert snapshot["revision"] == expected_revision
        assert all(v["marker"] == expected_marker
                   for v in snapshot["records"].values())
        restored.close()
        print(f"PASS forced exit {phase} preserves complete snapshot")

print("PASS all atomic-state-persistence checks")
