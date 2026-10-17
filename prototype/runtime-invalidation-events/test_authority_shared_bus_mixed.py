"""Suite 46: mixed synthetic heartbeat/ACK/control queue and revocation.

This is not a hardware transmit, physical arbitration, or actuator test.
"""
from causal_integrated_can import CausalIntegratedCan
from authority_shared_bus import AuthoritySharedBus


def setup():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    model.bus = AuthoritySharedBus(model.link)
    return model


model = setup()
bus = model.bus
assert bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
boot, challenge = model.link.generation.split(":", 1)
message = dict(kind="heartbeat", unit="right", main_boot=boot,
               challenge=challenge, forma_boot="right-boot",
               session="right-session", sequence=1, ready=True)
assert model.link.submit(message, now=0.041, deadline=0.09)
assert bus.import_forward()
assert bus.enqueue_ack(source="left", transfer_id=0, now=0.041, deadline=0.09)
events = bus.dispatch(until=0.06)
directions = [event[0] for event in events]
assert "forward" in directions and "ack" in directions and "background" in directions, events
assert directions.index("background") > directions.index("forward"), events
assert directions.index("background") > directions.index("ack"), events
assert not bus.failed
print("PASS heartbeat and ACK outrank control on shared synthetic bus")

model = setup()
bus = model.bus
assert bus.enqueue_control("left", b"control", now=0.041, deadline=0.8)
assert bus.enqueue_ack(source="right", transfer_id=0, now=0.041, deadline=0.8)
events = bus.dispatch(until=0.55)
assert not any(event[0] == "background" for event in events)
assert bus.control_revoked
assert not any(item[2] == "background" and item[0] == 2 for item in bus.queue)
print("PASS heartbeat expiry prevents queued control amid ACK traffic")

model = setup()
bus = model.bus
assert bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
assert bus.enqueue_ack(source="right", transfer_id=0, now=0.041, deadline=0.09)
assert model.link.fault.protocol.receive(dict(
    kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
    forma_boot="right-boot", session="right-session", sequence=1,
    ready=False), now=0.042)
events = bus.dispatch(until=0.05)
assert not any(event[0] == "background" for event in events)
assert bus.control_revoked
print("PASS Ready=false prevents queued control amid ACK traffic")

model = setup()
bus = model.bus
assert bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
assert bus.enqueue_ack(source="left", transfer_id=0, now=0.041, deadline=0.09)
bus.bus_off()
assert bus.dispatch(until=0.05) == []
assert not bus.queue
print("PASS bus-off clears mixed synthetic queue")

print("PASS all authority-shared-bus-mixed checks")
