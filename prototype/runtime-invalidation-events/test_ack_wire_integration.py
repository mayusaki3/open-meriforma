"""Suite 30: synthetic application ACK wire validation."""
from ack_wire import encode_ack, decode_ack
from integrated_can_link import IntegratedCanLink


def msg(unit):
    return dict(kind="heartbeat", unit=unit, main_boot="M1", challenge="C1",
                forma_boot=unit + "-boot", session=unit + "-session",
                sequence=0, ready=True)


def setup():
    link = IntegratedCanLink(("left", "right"), heartbeat_timeout=0.5)
    link.start_main(boot_id="M1", challenge="C1", now=0)
    for unit in ("left", "right"):
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot="M1", challenge="C1",
                              session=unit + "-session")
        assert link.submit(msg(unit), now=0.001, deadline=0.05)
    tid = next(tid for tid, owner in link.transfer_owners.items() if owner == "left")
    link.dispatch(until=0.05, ack_drop={tid})
    assert tid in link.fault.pending
    return link, tid


wire = encode_ack(transfer_id=42, source="left", destination="main",
                  generation="M1:C1")
assert decode_ack(wire) == dict(transfer_id=42, source="left",
                                destination="main", generation="M1:C1")
for bad in (wire[:-1], wire + b"x", wire[:7] + bytes([wire[7] ^ 1]) + wire[8:]):
    try:
        decode_ack(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("malformed ACK accepted")
print("PASS binary ACK roundtrip, exact length and CRC corruption detection")

link, tid = setup()
assert not link.receive_ack(link.make_ack(tid, source="left"), source="right")
assert not link.receive_ack(encode_ack(transfer_id=tid, source="left",
                                       destination="other", generation="M1:C1"),
                            source="left")
assert not link.receive_ack(encode_ack(transfer_id=tid, source="left",
                                       destination="main", generation="old"),
                            source="left")
assert not link.receive_ack(link.make_ack(tid + 100, source="left"), source="left")
assert tid in link.fault.pending
print("PASS source, destination, generation and transfer identity fencing")

ack = link.make_ack(tid, source="left")
assert link.receive_ack(ack, source="left")
assert not link.receive_ack(ack, source="left")
assert tid not in link.fault.pending
assert link.retry_due(now=0.2) == []
print("PASS valid ACK stops retry and duplicate ACK is rejected")

link, tid = setup()
old = link.make_ack(tid, source="left")
link.bus_off_event()
link.bus_recovered()
link.start_main(boot_id="M2", challenge="C2", now=0.1)
assert not link.receive_ack(old, source="left")
assert not link.fault.pending
print("PASS old-session ACK cannot acknowledge a new generation")

link, tid = setup()
for invalid in (None, b"", "not bytes"):
    try:
        link.receive_ack(invalid, source="left")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid ACK accepted")
assert not link.status(now=0.05)["motor_command_issued"]
assert not link.status(now=0.05)["physical_safety_verified"]
print("PASS invalid ACK rejected without motor or physical safety claims")
print("PASS all ack-wire-integration checks")
