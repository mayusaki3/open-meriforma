"""Suite 40: multiple required Forma peers share one fail-closed causal bus.

Synthetic protocol checks only; no physical safety or motor I/O.
"""
from causal_integrated_can import CausalIntegratedCan


def setup(**kwargs):
    model = CausalIntegratedCan(("left", "right"), **kwargs)
    model.start()
    return model


def send_both(model, *, seq=0, at=0.001, deadline=0.04):
    for unit in ("left", "right"):
        assert model.submit(unit, seq, now=at, deadline=deadline)


model = setup()
send_both(model)
forward = model.advance(until=0.02)
assert sum(e[0] == "forward" and e[2] is True for e in forward) == 2
assert model.status()["ack_scheduled"] == 2
assert model.status()["pending"] == 2
acks = model.deliver_acks(until=0.04)
assert sum(e[0] == "ack" and e[2] is True for e in acks) == 2
assert model.status()["pending"] == 0
assert not model.link.invalidated
print("PASS both required Forma peers complete heartbeat and causal ACK")

model = setup()
assert model.submit("left", 0, now=0.001, deadline=0.04)
forward = model.advance(until=0.02)
assert any(e[0] == "forward" and e[2] is True for e in forward)
assert model.status()["failed"] and model.link.invalidated
assert model.status()["ack_scheduled"] == 0
assert not model.link.fault.protocol.links.authorized
print("PASS missing required peer fails closed for the whole group")

model = setup()
send_both(model)
model.advance(until=0.02)
lost = model.deliver_acks(until=0.04, drop={("ack", "right", 1, 0)})
assert any(e[0] == "dropped" and e[1][1] == "right" for e in lost)
assert model.status()["pending"] == 1
assert 1 in model.retry(now=0.11, deadline=0.20)
forward = model.advance(until=0.14)
assert any(e[0] == "forward" and e[1][1] == "right" for e in forward)
acks = model.deliver_acks(until=0.18)
assert any(e[0] == "ack" and e[2] is True for e in acks)
assert model.status()["pending"] == 0 and not model.link.invalidated
print("PASS one peer ACK loss recovers without resending other peer")

model = setup(ack_window=0.000001)
send_both(model)
model.advance(until=0.02)
assert model.status()["failed"] and model.link.invalidated
assert not model.status()["automatic_resume"]
print("PASS shared ACK deadline fault revokes group authority")

model = setup()
send_both(model)
model.advance(until=0.02)
model.deliver_acks(until=0.04)
old_bus = model.bus
model.bus.bus_off()
assert model.link.invalidated and model.status()["failed"]
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.05)
assert old_bus.generation != model.bus.generation
assert old_bus.failed
assert not model.link.fault.protocol.links.authorized
assert not model.status()["automatic_resume"]
send_both(model, at=0.061, deadline=0.1)
model.advance(until=0.08)
model.deliver_acks(until=0.1)
assert model.status()["pending"] == 0
assert not model.link.fault.protocol.links.authorized
assert not model.status()["motor_command_issued"]
assert not model.status()["physical_safety_verified"]
print("PASS all peers reestablish after bus-off without automatic authority")
print("PASS all multi-forma-causal checks")
