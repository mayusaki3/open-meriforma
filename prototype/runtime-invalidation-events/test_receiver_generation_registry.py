"""Suite 53: synthetic lifecycle, global capacity and no same-epoch reset."""
from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from receiver_generation_registry import ReceiverGenerationRegistry


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


def send(rx, link, tid, source, now):
    return rx.receive(fragment(b"x", transfer_id=tid)[0], source=source,
                      generation=link.generation, deadline=0.2, now=now)


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected refusal")


registry = ReceiverGenerationRegistry()
link = ready()
rx = registry.bind(link, now=0.04, max_transfer_ids=2)
assert send(rx, link, 1, "left", 0.05) is True
assert send(rx, link, 1, "right", 0.06) is True
assert send(rx, link, 2, "left", 0.07) is False
assert rx.revoked and len(rx.reserved_transfers) == 2
print("PASS global capacity shared across sources fails closed")

rejects(lambda: registry.bind(link, now=0.08, max_transfer_ids=2))
assert rx.revoked
print("PASS rebuilding receiver cannot erase same-generation replay history")

new_link = ready("M2", "C2", authorize=False)
rejects(lambda: registry.bind(new_link, now=0.04, max_transfer_ids=2))
assert registry.current is rx
print("PASS new generation without explicit authorization rejected")

assert new_link.authorize(explicit=True, now=0.04)
new_rx = registry.bind(new_link, now=0.04, max_transfer_ids=2)
assert rx.revoked
assert send(new_rx, new_link, 1, "left", 0.05) is True
assert send(new_rx, new_link, 1, "left", 0.06) is False
assert new_rx.accepted == [("left", b"x")]
print("PASS fresh authorized generation creates new history and fences old receiver")

rejects(lambda: registry.bind(link, now=0.08))
rejects(lambda: registry.bind(new_link, now=0.08))
assert registry.current is new_rx
print("PASS previously used generations cannot be rebound")
print("PASS all receiver-generation-registry checks")
