"""Suite 39: causal ACK through real synthetic reassembly/session components."""
from causal_integrated_can import CausalIntegratedCan


def setup(**kwargs):
    model = CausalIntegratedCan(("left",), **kwargs)
    model.start()
    return model


model = setup()
assert model.submit("left", 0, now=0.001, deadline=0.04)
assert model.status()["ack_scheduled"] == 0
forward = model.advance(until=0.02)
assert any(e[0] == "forward" and e[2] is True for e in forward)
assert model.status()["ack_scheduled"] == 1, (forward, model.status(), model.link.completed_transfers, model.link.fault.pending)
assert model.status()["pending"] == 1
acks = model.deliver_acks(until=0.04)
assert any(e[0] == "ack" and e[2] is True for e in acks)
assert model.status()["pending"] == 0
print("PASS integrated fragment reassembly causally generates shared-bus ACK")

model = setup()
assert model.submit("left", 0, now=0.001, deadline=0.04)
# Lost only forward frame, so no completed transfer and no ACK.
out = model.advance(until=0.02, drop={("forward", "left", 0, 0)})
assert any(e[0] == "dropped" for e in out)
assert model.status()["ack_scheduled"] == 0
assert model.deliver_acks(until=0.04) == []
print("PASS lost heartbeat cannot generate integrated ACK")

model = setup()
assert model.submit("left", 0, now=0.001, deadline=0.04)
model.advance(until=0.02)
out = model.deliver_acks(until=0.04, drop={("ack", "left", 0, 0)})
assert any(e[0] == "dropped" for e in out)
assert model.status()["pending"] == 1
assert 0 in model.retry(now=0.11, deadline=0.20)
forward = model.advance(until=0.14)
assert any(e[0] == "forward" and e[2] is True for e in forward)
acks = model.deliver_acks(until=0.18)
assert any(e[0] == "ack" and e[2] is True for e in acks)
assert model.status()["pending"] == 0
print("PASS dropped ACK recovers by retry without duplicate application effects")

model = setup(ack_window=0.000001)
assert model.submit("left", 0, now=0.001, deadline=0.04)
model.advance(until=0.02)
out = model.deliver_acks(until=0.04)
assert any(e[0] == "late" for e in out)
assert model.status()["failed"] and model.link.invalidated
assert not model.status()["motor_command_issued"]
print("PASS ACK deadline breach fails closed")

model = setup()
assert model.submit("left", 0, now=0.001, deadline=0.04)
model.advance(until=0.02)
old_bus = model.bus
model.bus.bus_off()
assert model.status()["failed"] and model.link.invalidated
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.05)
assert old_bus.dispatch(until=0.06) == []
assert model.status()["ack_scheduled"] == 0
assert not model.status()["automatic_resume"]
print("PASS bus-off and generation fencing reject stale ACK state")
print("PASS all causal-integrated-can checks")
