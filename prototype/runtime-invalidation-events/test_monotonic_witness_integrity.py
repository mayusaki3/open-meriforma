"""Suite 60: malformed witness refusal and ambiguous rollback boundary.

Plain-file witness is NOT authenticated, durable hardware, or a trusted counter.
"""
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from monotonic_generation_crash_worker import FileWitness
from monotonic_generation_guard import MonotonicGenerationGuard as Guard


def refuses(path, witness_path):
    try:
        guard = Guard(str(path), FileWitness(witness_path))
    except ValueError:
        return
    guard.close()
    raise AssertionError("invalid witness or anchor accepted")


with TemporaryDirectory() as folder:
    path = Path(folder) / "history.sqlite"
    witness_path = Path(folder) / "witness.txt"
    witness_path.write_bytes(b"0")
    guard = Guard(str(path), FileWitness(witness_path), initialize=True)
    guard.close()

    witness_path.unlink()
    refuses(path, witness_path)
    print("PASS missing witness refuses startup")

    for raw in (b"", b"abc", b"-1", b" 0", b"0\n", b"00", b"1.0",
                b"99999999999999999999", b"\xff"):
        witness_path.write_bytes(raw)
        refuses(path, witness_path)
    print("PASS malformed witness encodings refuse startup")

    witness_path.write_bytes(b"1")
    refuses(path, witness_path)
    print("PASS witness-ahead mismatch refuses startup")

    witness_path.write_bytes(b"0")
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE generation_anchor SET sequence=1 WHERE id=1")
        db.commit()
    refuses(path, witness_path)
    print("PASS witness-behind mismatch refuses startup")

with TemporaryDirectory() as folder:
    path = Path(folder) / "history.sqlite"
    witness_path = Path(folder) / "witness.txt"
    snapshot = Path(folder) / "snapshot.sqlite"
    witness_snapshot = Path(folder) / "witness_snapshot.txt"
    witness_path.write_bytes(b"0")
    guard = Guard(str(path), FileWitness(witness_path), initialize=True)
    guard.close()
    shutil.copy2(path, snapshot)
    shutil.copy2(witness_path, witness_snapshot)

    # A coherent rollback of BOTH untrusted stores cannot be detected locally.
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO generations(generation) VALUES (?)", ("M1:C1",))
        db.execute("UPDATE generation_anchor SET sequence=1 WHERE id=1")
        db.commit()
    witness_path.write_bytes(b"1")
    guard = Guard(str(path), FileWitness(witness_path))
    guard.close()
    shutil.copy2(snapshot, path)
    shutil.copy2(witness_snapshot, witness_path)
    guard = Guard(str(path), FileWitness(witness_path))
    guard.close()
    print("PASS coherent rollback of both untrusted stores remains undetectable")

print("PASS all monotonic-witness-integrity checks")
