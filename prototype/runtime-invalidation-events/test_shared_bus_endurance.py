"""Suite 33: synthetic periodic shared-bus load and deadline validation.

Finite deterministic simulation; not real-time hardware or CAN arbitration proof.
"""
from canfd_fragments import fragment
from integrated_can_link import IntegratedCanLink
from shared_can_bus import SharedCanBus


def setup(*, heartbeat_timeout=0.5, capacity=128):
    link = IntegratedCanLink(("left", "right"), heartbeat_timeout=heartbeat_timeout)
    link.start_main(boot_id="M1", challenge="C1", now=0)
    for unit in link.units:
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot="M1", challenge="C1",
                              session=unit + "-session")
    return link, SharedCanBus(link, max_queue=capacity)


def heartbeat(unit, seq):
    return dict(kind="heartbeat", unit=unit, main_boot="M1", challenge="C1",
                forma_boot=unit + "-boot", session=unit + "-session",
                sequence=seq, ready=True)


link, bus = setup()
ack_count = 0
background_count = 0
for cycle in range(15):
    t = cycle * 0.02 + 0.001
    for unit in link.units:
        assert link.submit(heartbeat(unit, cycle), now=t, deadline=t + 0.008)
    assert bus.import_forward()
    for frame in fragment(b"diagnostic" * 10, transfer_id=cycle):
        assert bus.enqueue(direction="background", source="left", frame=frame,
                           kind="diagnostic", now=t, deadline=t + 0.016)
    forward = bus.dispatch(until=t + 0.008)
    assert sum(x[0] == "forward" and x[2] is True for x in forward) == 2
    ids = {unit: max(tid for tid, owner in link.transfer_owners.items()
                     if owner == unit) for unit in link.units}
    for unit, tid in ids.items():
        assert bus.enqueue_ack(source=unit, transfer_id=tid,
                               now=t + 0.008, deadline=t + 0.016)
    returned = bus.dispatch(until=t + 0.016)
    ack_count += sum(x[0] == "ack" and x[2] is True for x in returned)
    background_count += sum(x[0] == "background" for x in forward + returned)
    assert not bus.failed and not link.fault.pending
assert ack_count == 30 and background_count == 30
assert all(a[-1] <= b[-1] for a, b in zip(bus.history, bus.history[1:]))
print("PASS 15 periodic cycles: 30 heartbeats, 30 ACKs and 30 diagnostic fragments")

link, bus = setup()
for unit in link.units:
    assert link.submit(heartbeat(unit, 0), now=0.001, deadline=0.03)
assert bus.import_forward()
for frame in fragment(b"background" * 20, transfer_id=50):
    assert bus.enqueue(direction="background", source="left", frame=frame,
                       kind="diagnostic", now=0.001, deadline=0.04)
events = bus.dispatch(until=0.04)
forward_finish = [e[-1] for e in events if e[0] == "forward"]
background_finish = [e[-1] for e in events if e[0] == "background"]
assert len(forward_finish) == 2 and background_finish
assert max(forward_finish) < min(background_finish)
print("PASS heartbeat priority precedes queued diagnostic load")

link, bus = setup()
for unit in link.units:
    assert link.submit(heartbeat(unit, 0), now=0.001, deadline=0.03)
assert bus.import_forward()
bus.dispatch(until=0.03)
tid = next(tid for tid, owner in link.transfer_owners.items() if owner == "left")
assert bus.enqueue_ack(source="left", transfer_id=tid,
                       now=0.03, deadline=0.030001)
events = bus.dispatch(until=0.04)
assert any(e[0] == "late" for e in events)
assert bus.failed and link.invalidated and tid in link.fault.pending
print("PASS ACK deadline under contention fails closed, without false completion")

link, bus = setup(capacity=128)
for unit in link.units:
    assert link.submit(heartbeat(unit, 0), now=0.001, deadline=0.04)
assert bus.import_forward()
bus.max_queue = len(bus.queue)
assert not bus.enqueue(direction="background", source="left",
                       frame=fragment(b"x", transfer_id=90)[0],
                       kind="diagnostic", now=0.001, deadline=0.04)
assert bus.failed and link.invalidated and not bus.queue
print("PASS sustained-load queue capacity breach clears shared traffic")

link, bus = setup()
for unit in link.units:
    assert link.submit(heartbeat(unit, 0), now=0.001, deadline=0.04)
assert bus.import_forward()
bus.bus_off()
assert not bus.queue and bus.failed
link.bus_recovered()
link.start_main(boot_id="M2", challenge="C2", now=0.01)
assert bus.dispatch(until=0.02) == []
assert not bus.status()["motor_command_issued"]
assert not bus.status()["physical_safety_verified"]
print("PASS bus-off and generation fencing preserve no-actuation boundary")
print("PASS all shared-bus-endurance checks")
