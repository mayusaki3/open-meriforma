"""Suite 41: explicit authority after multi-Forma causal transport recovery.

Synthetic authorization only. No physical STOP, CAN hardware or motor I/O.
"""
from causal_integrated_can import CausalIntegratedCan


def setup():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    return model


def heartbeat(model, unit, *, sequence=0, now=0.001, deadline=0.04):
    assert model.submit(unit, sequence, now=now, deadline=deadline)


def deliver_pair(model, *, now=0.001, forward_until=0.02, ack_until=0.04):
    for unit in ("left", "right"):
        heartbeat(model, unit, now=now, deadline=ack_until)
    model.advance(until=forward_until)
    model.deliver_acks(until=ack_until)
    assert model.status()["pending"] == 0
    assert not model.link.invalidated


model = setup()
assert not model.link.authorize(explicit=False, now=0.0)
deliver_pair(model)
assert not model.link.fault.protocol.sessions.authorized
assert not model.link.authorize(explicit=False, now=0.04)
assert model.link.authorize(explicit=True, now=0.04)
assert model.link.eligible(now=0.04)
assert not model.status()["motor_command_issued"]
print("PASS two fresh ready peers require explicit authorization")

model = setup()
heartbeat(model, "left")
model.advance(until=0.02)
assert model.link.invalidated
assert not model.link.authorize(explicit=True, now=0.02)
assert not model.link.eligible(now=0.02)
print("PASS missing required peer cannot authorize")

model = setup()
deliver_pair(model)
assert model.link.authorize(explicit=True, now=0.04)
model.bus.bus_off()
assert model.link.invalidated
assert not model.link.authorize(explicit=True, now=0.04)
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.05)
assert not model.link.fault.protocol.sessions.authorized
assert not model.link.fault.protocol.links.authorized
assert not model.link.authorize(explicit=True, now=0.05)
for unit in ("left", "right"):
    heartbeat(model, unit, now=0.051, deadline=0.09)
model.advance(until=0.065)
model.deliver_acks(until=0.08)
assert model.status()["pending"] == 0
assert not model.link.fault.protocol.sessions.authorized
assert not model.link.authorize(explicit=False, now=0.08)
assert model.link.authorize(explicit=True, now=0.08)
assert model.link.eligible(now=0.08)
assert not model.status()["automatic_resume"]
assert not model.status()["motor_command_issued"]
assert not model.status()["physical_safety_verified"]
print("PASS new generation and fresh peers need a new explicit authorization")

model = setup()
deliver_pair(model)
assert model.link.authorize(explicit=True, now=0.04)
assert model.link.fault.protocol.establish(
    "right", forma_boot="right-newboot", main_boot="M1",
    challenge="C1", session="right-newsession"
)
assert not model.link.fault.protocol.sessions.authorized
assert not model.link.authorize(explicit=True, now=0.04)
print("PASS peer session replacement revokes prior authorization")

print("PASS all multi-forma-authority checks")
