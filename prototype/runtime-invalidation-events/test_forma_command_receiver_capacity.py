"""Suite 52: bounded replay history, ID wrap boundary and generation reset.

Synthetic receiver only; exhaustion deliberately fails closed.
"""
from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from forma_command_receiver import FormaCommandReceiver


def ready(boot="M1", challenge="C1"):
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id=boot, challenge=challenge)
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def deliver(rx, link, tid, now, source="left"):
    return rx.receive(fragment(bytes([tid % 256]), transfer_id=tid)[0],
                      source=source, generation=link.generation,
                      deadline=0.2, now=now)


link = ready()
rx = FormaCommandReceiver(link, max_transfer_ids=2)
assert deliver(rx, link, 1, 0.05) is True
assert deliver(rx, link, 1, 0.06) is False
assert deliver(rx, link, 2, 0.07) is True
assert len(rx.reserved_transfers) == 2
assert deliver(rx, link, 3, 0.08) is False
assert rx.revoked and len(rx.accepted) == 2
print("PASS bounded ID history exhausts closed without eviction or replay")

link = ready()
rx = FormaCommandReceiver(link, max_transfer_ids=2)
assert deliver(rx, link, 65535, 0.05) is True
assert deliver(rx, link, 0, 0.06) is True
assert deliver(rx, link, 65535, 0.07) is False
assert deliver(rx, link, 1, 0.08) is False
assert rx.revoked and len(rx.accepted) == 2
print("PASS 16-bit wrap boundary never reuses completed ID in same generation")

link = ready()
rx = FormaCommandReceiver(link, max_transfer_ids=2, timeout=0.01)
first, last = fragment(bytes(range(110)), transfer_id=10)
assert rx.receive(first, source="left", generation=link.generation,
                  deadline=0.2, now=0.05) is None
assert deliver(rx, link, 11, 0.07) is True
assert rx.receive(last, source="left", generation=link.generation,
                  deadline=0.2, now=0.08) is False
assert deliver(rx, link, 12, 0.09) is False
assert rx.revoked and len(rx.reserved_transfers) == 2
print("PASS expired partial ID consumes capacity and cannot be evicted")

old_link = ready()
old_rx = FormaCommandReceiver(old_link, max_transfer_ids=1)
assert deliver(old_rx, old_link, 7, 0.05) is True
assert deliver(old_rx, old_link, 8, 0.06) is False
new_link = ready("M2", "C2")
new_rx = FormaCommandReceiver(new_link, max_transfer_ids=1)
assert deliver(new_rx, new_link, 7, 0.05) is True
assert old_rx.receive(fragment(b"old", transfer_id=7)[0], source="left",
                      generation=new_link.generation, deadline=0.2, now=0.07) is False
assert new_rx.accepted == [("left", bytes([7]))]
print("PASS new generation requires fresh receiver; old instance remains fenced")

try:
    FormaCommandReceiver(ready(), max_transfer_ids=0)
except ValueError:
    pass
else:
    raise AssertionError("zero history capacity accepted")
print("PASS invalid capacity rejected")
print("PASS all forma-command-receiver-capacity checks")
