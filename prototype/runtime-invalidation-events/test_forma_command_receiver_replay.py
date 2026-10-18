"""Suite 51: synthetic receiver replay and incomplete-transfer expiry."""
from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from forma_command_receiver import FormaCommandReceiver


def ready():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


link = ready()
rx = FormaCommandReceiver(link)
frame = fragment(b"once", transfer_id=20)[0]
assert rx.receive(frame, source="left", generation=link.generation,
                  deadline=0.2, now=0.05) is True
assert rx.receive(frame, source="left", generation=link.generation,
                  deadline=0.2, now=0.06) is False
assert rx.accepted == [("left", b"once")]
print("PASS completed command replay rejected without duplicate acceptance")

link = ready()
rx = FormaCommandReceiver(link, timeout=0.01)
first, last = fragment(bytes(range(110)), transfer_id=21)
assert rx.receive(first, source="left", generation=link.generation,
                  deadline=0.2, now=0.05) is None
assert rx.receive(last, source="left", generation=link.generation,
                  deadline=0.2, now=0.07) is False
assert not rx.accepted
assert (link.generation, "left", 21) in rx.expired_transfers
print("PASS late final fragment cannot resurrect timed-out partial command")

link = ready()
rx = FormaCommandReceiver(link, timeout=0.01)
first, last = fragment(bytes(range(110)), transfer_id=22)
assert rx.receive(first, source="left", generation=link.generation,
                  deadline=0.2, now=0.05) is None
assert rx.receive(first, source="left", generation=link.generation,
                  deadline=0.2, now=0.07) is False
assert rx.receive(last, source="left", generation=link.generation,
                  deadline=0.2, now=0.08) is False
assert not rx.accepted
print("PASS expired transfer ID cannot restart reassembly")

link = ready()
rx = FormaCommandReceiver(link)
old = fragment(b"old", transfer_id=23)[0]
assert rx.receive(old, source="left", generation="M0:C0",
                  deadline=0.2, now=0.05) is False
assert rx.revoked and not rx.accepted
print("PASS old-generation retransmission rejected")

link = ready()
rx = FormaCommandReceiver(link)
a = fragment(b"left", transfer_id=24)[0]
b = fragment(b"right", transfer_id=24)[0]
assert rx.receive(a, source="left", generation=link.generation,
                  deadline=0.2, now=0.05) is True
assert rx.receive(b, source="right", generation=link.generation,
                  deadline=0.2, now=0.06) is True
assert rx.accepted == [("left", b"left"), ("right", b"right")]
print("PASS replay IDs scoped independently to each source")
print("PASS all forma-command-receiver-replay checks")
