"""Suite 32: shared synthetic CAN-FD airtime for forward + ACK traffic."""
from integrated_can_link import IntegratedCanLink
from shared_can_bus import SharedCanBus


def message(unit, seq=0):
    return dict(kind="heartbeat", unit=unit, main_boot="M1", challenge="C1",
                forma_boot=unit + "-boot", session=unit + "-session",
                sequence=seq, ready=True)


def setup(*, capacity=128):
    link = IntegratedCanLink(("left", "right"), heartbeat_timeout=0.5)
    link.start_main(boot_id="M1", challenge="C1", now=0)
    for unit in link.units:
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot="M1", challenge="C1",
                              session=unit + "-session")
        assert link.submit(message(unit), now=0.001, deadline=0.05)
    bus = SharedCanBus(link, max_queue=capacity)
    assert bus.import_forward()
    events = bus.dispatch(until=0.05)
    assert sum(x[0] == "forward" and x[2] is True for x in events) == 2
    ids = {unit: next(tid for tid, owner in link.transfer_owners.items()
                      if owner == unit) for unit in link.units}
    return link, bus, ids


link, bus, ids = setup()
assert bus.enqueue_ack(source="right", transfer_id=ids["right"], now=0.05, deadline=0.1)
assert bus.enqueue_ack(source="left", transfer_id=ids["left"], now=0.05, deadline=0.1)
assert link.submit(message("left", 1), now=0.051, deadline=0.1)
assert bus.import_forward()
out = bus.dispatch(until=0.1)
assert sum(x[0] == "ack" and x[2] is True for x in out) == 2
assert any(x[0] == "forward" for x in out)
assert all(x[-1] <= 0.1 for x in out)
assert not bus.failed
print("PASS forward heartbeat and reverse ACK share one airtime clock")

link, bus, ids = setup()
assert bus.enqueue_ack(source="left", transfer_id=ids["left"], now=0.05, deadline=0.1)
out = bus.dispatch(until=0.1, drop={("ack", "left", 0, 0)})
assert any(x[0] == "dropped" for x in out)
assert ids["left"] in link.fault.pending
assert link.retry_due(now=0.11, deadline=0.2) == [ids["left"]]
assert bus.import_forward()
assert bus.enqueue_ack(source="left", transfer_id=ids["left"], now=0.11, deadline=0.2)
out = bus.dispatch(until=0.2)
assert any(x[0] == "ack" and x[2] is True for x in out)
assert ids["left"] not in link.fault.pending
print("PASS lost ACK, retransmission and ACK recovery on shared bus")

link, bus, ids = setup()
assert bus.enqueue_ack(source="left", transfer_id=ids["left"],
                       now=0.05, deadline=0.050001)
out = bus.dispatch(until=0.1)
assert any(x[0] == "late" for x in out)
assert bus.failed and link.invalidated
assert ids["left"] in link.fault.pending
print("PASS shared-bus ACK deadline violation invalidates authority")

link, bus, ids = setup(capacity=1)
assert bus.enqueue_ack(source="left", transfer_id=ids["left"], now=0.05, deadline=0.1)
assert not bus.enqueue_ack(source="right", transfer_id=ids["right"],
                           now=0.05, deadline=0.1)
assert bus.failed and link.invalidated and bus.status()["queued"] == 0
print("PASS shared-bus queue saturation fails closed")

link, bus, ids = setup()
assert bus.enqueue_ack(source="left", transfer_id=ids["left"], now=0.05, deadline=0.1)
bus.bus_off()
assert bus.failed and link.invalidated and bus.status()["queued"] == 0
link.bus_recovered()
link.start_main(boot_id="M2", challenge="C2", now=0.06)
assert bus.dispatch(until=0.1) == []
assert not bus.status()["motor_command_issued"]
assert not bus.status()["physical_safety_verified"]
print("PASS bus-off flushes both directions; new generation rejects old bus")
print("PASS all shared-can-bus checks")
