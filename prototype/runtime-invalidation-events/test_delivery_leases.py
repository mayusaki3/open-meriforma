import sqlite3
import tempfile
import threading
from pathlib import Path

from delivery_leases import DeliveryLeases

with tempfile.TemporaryDirectory() as directory:
    path = str(Path(directory) / "leases.sqlite")
    a = DeliveryLeases(path)
    b = DeliveryLeases(path)
    assert a.enqueue("event:1", {"kind": "execution_invalidated"})
    assert not b.enqueue("event:1", {"kind": "execution_invalidated"})
    first = a.claim("worker_a", 10.0, 5.0)
    assert first and first["generation"] == 1
    assert b.claim("worker_b", 11.0, 5.0) is None
    print("PASS concurrent connections cannot claim active lease")

    second = b.claim("worker_b", 15.0, 5.0)
    assert second and second["generation"] == 2
    assert not a.acknowledge("event:1", "worker_a", 1, 15.0)
    assert not a.acknowledge("event:1", "worker_b", 1, 15.0)
    assert b.acknowledge("event:1", "worker_b", 2, 16.0)
    assert not b.acknowledge("event:1", "worker_b", 2, 16.0)
    assert a.claim("worker_a", 20.0, 5.0) is None
    print("PASS expired lease is reclaimed with fencing generation; stale ACK rejected")

    a.enqueue("event:2", {"kind": "other"})
    a.close()
    b.close()
    reopened = DeliveryLeases(path)
    assert reopened.is_acknowledged("event:1")
    assert reopened.claim("worker_c", 21.0, 3.0)["event_key"] == "event:2"
    reopened.close()
    print("PASS acknowledged state and pending work persist across restart")

    db = sqlite3.connect(path, isolation_level=None)
    db.execute("BEGIN IMMEDIATE")
    db.execute("INSERT INTO leased_outbox(event_key,payload) VALUES ('uncommitted','{}')")
    db.close()  # SQLite rolls back uncommitted transaction on connection close.
    restored = DeliveryLeases(path)
    assert restored.db.execute(
        "SELECT COUNT(*) FROM leased_outbox WHERE event_key='uncommitted'").fetchone()[0] == 0
    restored.close()
    print("PASS interrupted uncommitted write is rolled back")

    setup = DeliveryLeases(path)
    assert setup.enqueue("event:race", {"kind": "race"})
    setup.close()
    barrier = threading.Barrier(2)
    results = []
    errors = []

    def contender(owner):
        connection = DeliveryLeases(path)
        try:
            barrier.wait(timeout=5)
            results.append(connection.claim(owner, 30.0, 10.0))
        except Exception as exc:
            errors.append(exc)
        finally:
            connection.close()

    threads = [threading.Thread(target=contender, args=(owner,))
               for owner in ("worker_x", "worker_y")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert not errors, errors
    assert len(results) == 2
    assert len([result for result in results if result is not None]) == 1
    print("PASS simultaneous workers produce exactly one active reservation")
print("PASS all delivery-lease checks")
