"""Suite 65: optional synthetic peer-local group gate in command receiver."""
from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from forma_command_receiver import FormaCommandReceiver
from forma_group_commit_gate import FormaGroupCommitGate


def ready():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def gate(link):
    return FormaGroupCommitGate(peer="left", required_peers=("left", "right"),
                                group_epoch="group-1", generation=link.generation,
                                sequence=1)


def proof(link):
    return dict(peer="left", required_peers=("left", "right"),
                committed_peers=("left", "right"), group_epoch="group-1",
                generation=link.generation, sequence=1)


def send(rx, link, frame, now=0.05):
    return rx.receive(frame, source="left", generation=link.generation,
                      deadline=0.15, now=now)


link = ready()
g = gate(link)
rx = FormaCommandReceiver(link, group_gate=g)
assert send(rx, link, fragment(b"command", transfer_id=1)[0]) is False
assert rx.revoked and not rx.accepted and g.revoked
print("PASS command before group proof revokes local receiver")

link = ready()
g = gate(link)
assert g.install(proof(link))
rx = FormaCommandReceiver(link, group_gate=g)
assert send(rx, link, fragment(b"command", transfer_id=2)[0]) is True
assert rx.accepted == [("left", b"command")]
print("PASS matching group proof allows synthetic command acceptance")

link = ready()
g = gate(link)
assert not g.install(dict(proof(link), committed_peers=("left",)))
rx = FormaCommandReceiver(link, group_gate=g)
assert send(rx, link, fragment(b"command", transfer_id=3)[0]) is False
assert rx.revoked and not rx.accepted
print("PASS incomplete group proof rejects command")

link = ready()
g = gate(link)
assert g.install(proof(link))
rx = FormaCommandReceiver(link, group_gate=g)
frames = fragment(bytes(range(110)), transfer_id=4)
assert send(rx, link, frames[0]) is None
g.deny()
assert send(rx, link, frames[1], now=0.06) is False
assert rx.revoked and not rx.accepted and not rx.parts.active
print("PASS group revocation between fragments blocks completion")

link = ready()
g = gate(link)
assert g.install(proof(link))
rx = FormaCommandReceiver(link, group_gate=g)
g.deny()
assert send(rx, link, fragment(b"command", transfer_id=5)[0]) is False
assert not rx.accepted
print("PASS revoked group proof cannot be reused")

link = ready()
g = gate(link)
assert g.install(proof(link))
try:
    FormaCommandReceiver(ready(), group_gate=FormaGroupCommitGate(
        peer="left", required_peers=("left", "right"),
        group_epoch="group-1", generation="old:epoch", sequence=1))
except ValueError:
    pass
else:
    raise AssertionError("mismatched generation must fail")
print("PASS receiver construction rejects mismatched gate generation")

print("PASS all forma-receiver-group-gate checks")
