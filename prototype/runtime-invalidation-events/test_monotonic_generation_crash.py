"""Suite 59: synthetic cross-store crash windows and restart refusal.

The witness is a normal file used only to survive test subprocess exits. It is
NOT trusted storage and does not simulate physical power-loss durability.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

from monotonic_generation_guard import MonotonicGenerationGuard as Guard
from monotonic_generation_crash_worker import FileWitness


WORKER = Path(__file__).with_name("monotonic_generation_crash_worker.py")


def refuses(path, witness):
    try:
        guard = Guard(str(path), FileWitness(witness))
    except ValueError:
        return
    guard.close()
    raise AssertionError("inconsistent cross-store state accepted")


def state(path):
    with closing(sqlite3.connect(path)) as db:
        sequence = db.execute("SELECT sequence FROM generation_anchor WHERE id=1").fetchone()[0]
        generations = db.execute("SELECT generation FROM generations").fetchall()
        return sequence, generations


def run(mode):
    with TemporaryDirectory() as folder:
        db_path = Path(folder) / "history.sqlite"
        witness_path = Path(folder) / "witness.txt"
        witness_path.write_text("0", encoding="ascii")
        guard = Guard(str(db_path), FileWitness(witness_path), initialize=True)
        guard.close()
        proc = subprocess.run(
            [sys.executable, str(WORKER), str(db_path), str(witness_path), mode],
            check=False, capture_output=True, text=True,
        )
        assert proc.returncode == 71, (mode, proc.returncode, proc.stdout, proc.stderr)
        return mode, int(witness_path.read_text(encoding="ascii")), state(db_path), db_path, witness_path


with TemporaryDirectory() as folder:
    # Use a separate fixture per mode, keeping the database alive during checks.
    for mode in ("before_witness", "after_witness", "after_commit"):
        db_path = Path(folder) / (mode + ".sqlite")
        witness_path = Path(folder) / (mode + ".txt")
        witness_path.write_text("0", encoding="ascii")
        guard = Guard(str(db_path), FileWitness(witness_path), initialize=True)
        guard.close()
        proc = subprocess.run(
            [sys.executable, str(WORKER), str(db_path), str(witness_path), mode],
            check=False, capture_output=True, text=True,
        )
        assert proc.returncode == 71, (mode, proc.returncode, proc.stdout, proc.stderr)
        witness_value = int(witness_path.read_text(encoding="ascii"))
        sequence, generations = state(db_path)
        if mode == "before_witness":
            assert (witness_value, sequence, generations) == (0, 0, [])
            reopened = Guard(str(db_path), FileWitness(witness_path))
            reopened.close()
            print("PASS crash before witness advance preserves consistent empty history")
        elif mode == "after_witness":
            assert (witness_value, sequence, generations) == (1, 0, [])
            refuses(db_path, witness_path)
            print("PASS crash after witness advance refuses restart with witness ahead")
        else:
            assert (witness_value, sequence, generations) == (1, 1, [("M1:C1",)])
            reopened = Guard(str(db_path), FileWitness(witness_path))
            reopened.close()
            print("PASS crash after SQLite COMMIT preserves matching generation and witness")

print("PASS all monotonic-generation-crash checks")
