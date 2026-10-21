"""Suite 63: coordinator crashes cannot imply group authority after restart.

This tests absence of a durable group-commit proof, not real Forma firmware.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

from monotonic_generation_crash_worker import FileWitness
from monotonic_generation_guard import MonotonicGenerationGuard as Guard
from multi_forma_generation_group import MultiFormaGenerationGroup

WORKER = Path(__file__).with_name("multi_forma_crash_worker.py")


def initialize(root):
    for peer in ("left", "right"):
        path = root / (peer + ".sqlite")
        witness_path = root / (peer + ".txt")
        witness_path.write_text("0", encoding="ascii")
        guard = Guard(str(path), FileWitness(witness_path), initialize=True)
        guard.close()


def sequence(root, peer):
    with closing(sqlite3.connect(root / (peer + ".sqlite"))) as db:
        return db.execute("SELECT sequence FROM generation_anchor WHERE id=1").fetchone()[0]


def restart(root):
    group = MultiFormaGenerationGroup(("left", "right"))
    guards = []
    for peer in group.required:
        guard = Guard(str(root / (peer + ".sqlite")), FileWitness(root / (peer + ".txt")))
        guards.append(guard)
        group.attach(peer, guard)
    return group, guards


with TemporaryDirectory() as folder:
    root = Path(folder)
    initialize(root)
    proc = subprocess.run([sys.executable, str(WORKER), folder, "after_left"],
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 71, (proc.returncode, proc.stderr)
    assert (sequence(root, "left"), sequence(root, "right")) == (1, 0)
    group, guards = restart(root)
    assert not group.enabled
    assert all(guard.registry.current is None for guard in guards)
    for guard in guards:
        guard.close()
    print("PASS crash after first peer reservation leaves group disabled on restart")

with TemporaryDirectory() as folder:
    root = Path(folder)
    initialize(root)
    proc = subprocess.run([sys.executable, str(WORKER), folder, "after_both"],
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 71, (proc.returncode, proc.stderr)
    assert (sequence(root, "left"), sequence(root, "right")) == (1, 1)
    group, guards = restart(root)
    assert not group.enabled
    assert all(guard.registry.current is None for guard in guards)
    for guard in guards:
        guard.close()
    print("PASS crash after both peer reservations does not restore group authority")

with TemporaryDirectory() as folder:
    root = Path(folder)
    initialize(root)
    group, guards = restart(root)
    assert not group.enabled
    assert all(guard.registry.current is None for guard in guards)
    for guard in guards:
        guard.close()
    print("PASS fresh coordinator cannot infer authorization from matching empty histories")

print("PASS all multi-forma-crash-recovery checks")
