"""Suite 31: scheduled Forma-to-Main ACK return path."""
from integrated_can_link import IntegratedCanLink
from ack_return_path import AckReturnPath


def setup():
    link = IntegratedCanLink(("left", "right"), heartbeat_timeout=0.5)
    link.start_main(boot_id="M1", challenge="C1", now=0)
    for unit in ("left", "right"):
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot="M1", challenge="C1",
                              session=unit + "-session")
        message = dict(kind="heartbeat", unit=unit, main_boot="M1",
                       challenge="C1", forma_boot=unit + "-boot",
                       session=unit + "-session", sequence=0, ready=True)
        assert link.submit(message, now=0.001, deadline=0.05)
    left = next(tid for tid, unit in link.transfer_owners.items() if unit == "left")
    right = next(tid for tid, unit in link.transfer_owners.items() if unit == "right")
    link.dispatch(until=0.05, ack_drop={left, right})
    assert left in link.fault.pending and right in link.fault.pending
    path = AckReturnPath(link)
    path.begin()
    return link, path, left, right


link, path, left, right = setup()
assert path.queue_ack(unit="right", transfer_id=right, now=0.05, deadline=0.1)
assert path.queue_ack(unit="left", transfer_id=left, now=0.05, deadline=0.1)
out = path.dispatch(until=0.1)
assert sum(row[0] == "ack" and row[-1] is True for row in out) == 2
assert not link.fault.pending
print("PASS two Forma ACKs scheduled and reassembled in return-path order")

link, path, left, right = setup()
assert path.queue_ack(unit="left", transfer_id=left, now=0.05, deadline=0.1)
drop = {("left", 0, 0)}
out = path.dispatch(until=0.1, drop=drop)
assert any(row[0] == "dropped" for row in out)
assert left in link.fault.pending
assert not link.receive_ack(link.make_ack(left, source="left"), source="right")
print("PASS dropped return fragment does not acknowledge pending transfer")

link, path, left, right = setup()
assert path.queue_ack(unit="left", transfer_id=left, now=0.05, deadline=0.050001)
assert not any(row[0] == "ack" for row in path.dispatch(until=0.1))
assert path.status()["failed"] and left in link.fault.pending
print("PASS late ACK return frame fails closed without transfer completion")

link, path, left, right = setup()
assert path.queue_ack(unit="left", transfer_id=left, now=0.05, deadline=0.1)
link.bus_off_event()
link.bus_recovered()
link.start_main(boot_id="M2", challenge="C2", now=0.06)
assert path.dispatch(until=0.1) == []
assert not path.queue_ack(unit="left", transfer_id=left, now=0.1, deadline=0.2)
assert not link.fault.pending
print("PASS Main generation change fences old ACK return traffic")

link, path, left, right = setup()
assert not path.queue_ack(unit="left", transfer_id=65535, now=0.05, deadline=0.1)
assert not path.status()["motor_command_issued"]
assert not path.status()["physical_safety_verified"]
print("PASS unknown transfer cannot emit ACK; no physical safety claims")
print("PASS all ack-return-path checks")
