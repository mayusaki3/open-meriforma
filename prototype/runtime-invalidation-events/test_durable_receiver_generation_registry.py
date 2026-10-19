"""Suite 54: synthetic durable generation history and fail-closed recovery."""
from pathlib import Path
from tempfile import TemporaryDirectory

from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from durable_receiver_generation_registry import DurableReceiverGenerationRegistry as Registry


def ready(boot="M1", challenge="C1", authorize=True):
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id=boot, challenge=challenge)
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    if authorize:
        assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def rejects(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected fail-closed refusal")


with TemporaryDirectory() as temp:
    path = str(Path(temp) / "generations.db")
    link = ready()
    store = Registry(path, initialize=True)
    rx = store.bind(link, now=0.04)
    assert rx.receive(fragment(b"ok", transfer_id=1)[0], source="left",
                      generation=link.generation, deadline=0.2, now=0.05) is True
    store.close()
    assert rx.revoked
    restored = Registry(path)
    rejects(lambda: restored.bind(link, now=0.04))
    assert restored.current is None
    print("PASS committed generation remains fenced after registry reopen")

    new_link = ready("M2", "C2", authorize=False)
    rejects(lambda: restored.bind(new_link, now=0.04))
    assert restored.current is None
    assert new_link.authorize(explicit=True, now=0.04)
    new_rx = restored.bind(new_link, now=0.04)
    assert new_rx.receive(fragment(b"new", transfer_id=1)[0], source="left",
                          generation=new_link.generation, deadline=0.2, now=0.05) is True
    restored.close()
    again = Registry(path)
    rejects(lambda: again.bind(new_link, now=0.04))
    again.close()
    print("PASS fresh generation needs explicit authorization and is persisted")

with TemporaryDirectory() as temp:
    path = str(Path(temp) / "missing.db")
    rejects(lambda: Registry(path))
    assert not Path(path).exists() or Path(path).stat().st_size == 0
    print("PASS missing history cannot silently reinitialize")

with TemporaryDirectory() as temp:
    path = Path(temp) / "broken.db"
    path.write_bytes(b"not a sqlite database")
    rejects(lambda: Registry(str(path)))
    print("PASS corrupt history fails closed")

with TemporaryDirectory() as temp:
    path = str(Path(temp) / "schema.db")
    store = Registry(path, initialize=True)
    store.close()
    import sqlite3
    db = sqlite3.connect(path)
    db.execute("DROP TABLE generations")
    db.commit()
    db.close()
    rejects(lambda: Registry(path))
    print("PASS missing schema fails closed")

print("PASS all durable-receiver-generation-registry checks")
