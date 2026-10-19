"""Suite 56: startup refusal for malformed durable generation history."""
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from durable_receiver_generation_registry import DurableReceiverGenerationRegistry as Registry


def refuses(path):
    try:
        store = Registry(str(path))
    except ValueError:
        return
    store.close()
    raise AssertionError("invalid durable history accepted")


def prepared(folder, name):
    path = Path(folder) / name
    store = Registry(str(path), initialize=True)
    store.close()
    return path


with TemporaryDirectory() as folder:
    path = prepared(folder, "empty.sqlite")
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO generations VALUES (?)", ("",))
        db.commit()
    refuses(path)
    print("PASS empty persisted generation refuses startup")

with TemporaryDirectory() as folder:
    path = prepared(folder, "blob.sqlite")
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO generations VALUES (?)", (sqlite3.Binary(b"opaque"),))
        db.commit()
    refuses(path)
    print("PASS non-text persisted generation refuses startup")

with TemporaryDirectory() as folder:
    path = prepared(folder, "truncated.sqlite")
    data = path.read_bytes()
    path.write_bytes(data[:100])
    refuses(path)
    print("PASS truncated SQLite history refuses startup")

with TemporaryDirectory() as folder:
    path = prepared(folder, "schema.sqlite")
    with closing(sqlite3.connect(path)) as db:
        db.execute("DROP TABLE generations")
        db.execute("CREATE TABLE generations (generation BLOB PRIMARY KEY)")
        db.commit()
    refuses(path)
    print("PASS incompatible history schema refuses startup")

with TemporaryDirectory() as folder:
    path = prepared(folder, "valid.sqlite")
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO generations VALUES (?)", ("M1:C1",))
        db.commit()
    store = Registry(str(path))
    store.close()
    print("PASS valid existing history remains loadable")

print("PASS all durable-receiver-generation-integrity checks")
