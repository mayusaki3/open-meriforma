from can_fault_supervisor import CanFaultSupervisor
from canfd_fragments import fragment
from wire_envelope import encode


def message(unit, seq=0, *, main="M1", challenge="C1", session=None):
    return dict(kind="heartbeat", unit=unit, main_boot=main,
                challenge=challenge, forma_boot=unit + "-boot",
                session=session or unit + "-session", sequence=seq, ready=True)


def establish(s, *, main="M1", challenge="C1", suffix="session"):
    for u in ("left", "right"):
        assert s.establish(u, forma_boot=u + "-boot", main_boot=main,
                           challenge=challenge, session=u + "-" + suffix)


s = CanFaultSupervisor(("left", "right"))
s.start_main(boot_id="M1", challenge="C1")
establish(s)
for u in ("left", "right"):
    for f in fragment(encode(message(u)), transfer_id=1):
        result = s.receive(f, source=u, now=0.1)
    assert result is True
assert s.authorize(explicit=True, now=0.1)
print("PASS two peers ready through fragment transport")

tid, frames = s.queue(encode(message("left", seq=1)), now=0.2)
assert s.retry_due(now=0.25) == []
assert len(s.retry_due(now=0.31)) == 1
assert len(s.retry_due(now=0.42)) == 1
assert s.retry_due(now=0.53) == []
assert not s.pending
assert tid in s.used_transfers
print("PASS bounded retransmission and no transfer-ID reuse in session")

tid2, frames2 = s.queue(encode(message("right", seq=1)), now=0.6)
assert tid2 != tid
assert s.acknowledge(tid2)
assert not s.acknowledge(tid2)
s.next_transfer = tid
tid3, _ = s.queue(encode(message("left", seq=2)), now=0.7)
assert tid3 not in (tid, tid2)
print("PASS ACK and transfer-ID collision avoidance")

s.bus_off_event()
assert s.status(now=0.71)["bus_off"]
assert not s.eligible(now=0.71)
assert not s.authorize(explicit=True, now=0.71)
assert not s.reassembly.active and not s.pending
s.bus_recovered()
assert not s.eligible(now=0.72)
assert not s.establish("left", forma_boot="left-boot", main_boot="M1",
                       challenge="C1", session="left-session")
print("PASS bus-off clears pending work and recovery never auto-resumes")

s.start_main(boot_id="M2", challenge="C2")
establish(s, main="M2", challenge="C2", suffix="new")
for u in ("left", "right"):
    for f in fragment(encode(message(u, main="M2", challenge="C2",
                                      session=u + "-new")), transfer_id=2):
        result = s.receive(f, source=u, now=0.8)
    assert result is True
assert not s.eligible(now=0.8)
assert s.authorize(explicit=True, now=0.8)
print("PASS fresh sessions and explicit reauthorization after bus recovery")

try:
    for f in fragment(encode(message("left", seq=3, main="M2",
                                     challenge="C2", session="left-new")), transfer_id=3):
        s.receive(f, source="right", now=0.9)
except ValueError:
    pass
else:
    raise AssertionError("source mismatch accepted")
assert s.eligible(now=0.9)
assert not s.eligible(now=1.4)
print("PASS source mismatch rejected and timeout revokes multi-Forma authority")

for invalid in (lambda: s.queue(b"", now=1.5),
                lambda: s.retry_due(now=1.0),
                lambda: s.acknowledge(True)):
    try:
        invalid()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
assert not s.status(now=1.5)["motor_command_issued"]
print("PASS malformed inputs rejected without motor or safety claims")
print("PASS all can-fault-supervisor checks")
