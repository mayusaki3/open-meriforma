"""Suite 42: continuous revocation after explicit multi-Forma authorization.

Synthetic protocol/scheduler safety checks; no physical STOP or motor I/O.
"""
from causal_integrated_can import CausalIntegratedCan


def authorized_pair():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in ("left", "right"):
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.status()["pending"] == 0
    assert model.link.authorize(explicit=True, now=0.04)
    assert model.link.eligible(now=0.04)
    return model


model = authorized_pair()
assert not model.link.eligible(now=0.051)
assert model.link.invalidated
assert not model.link.authorize(explicit=True, now=0.051)
assert not model.link.fault.protocol.sessions.authorized
print("PASS scheduler heartbeat timeout revokes all authority")

model = authorized_pair()
protocol = model.link.fault.protocol
assert protocol.receive(dict(
    kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
    forma_boot="right-boot", session="right-session", sequence=1, ready=False
), now=0.041)
assert not protocol.sessions.authorized
assert not protocol.links.authorized
assert not model.link.eligible(now=0.041)
assert not model.status()["automatic_resume"]
print("PASS one peer Ready=false revokes group authority")

model = authorized_pair()
protocol = model.link.fault.protocol
assert protocol.establish(
    "right", forma_boot="right-boot-2", main_boot="M1",
    challenge="C1", session="right-session-2"
)
assert not protocol.sessions.authorized
assert not model.link.eligible(now=0.041)
assert not model.link.authorize(explicit=True, now=0.041)
print("PASS one peer session replacement requires new observations")

model = authorized_pair()
model.bus.bus_off()
assert model.link.invalidated
assert not model.link.authorize(explicit=True, now=0.04)
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.05)
for unit in ("left", "right"):
    assert model.submit(unit, 0, now=0.051, deadline=0.09)
model.advance(until=0.065)
model.deliver_acks(until=0.08)
assert model.status()["pending"] == 0
assert not model.link.fault.protocol.sessions.authorized
assert not model.link.eligible(now=0.08)
assert not model.link.authorize(explicit=False, now=0.08)
assert model.link.authorize(explicit=True, now=0.08)
assert model.link.eligible(now=0.08)
assert not model.status()["motor_command_issued"]
assert not model.status()["physical_safety_verified"]
print("PASS recovery does not automatically restore authority")
print("PASS all multi-forma-authority-monitor checks")
