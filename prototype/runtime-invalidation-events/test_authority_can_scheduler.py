"""Suite 44: authority revocation at synthetic CAN control dispatch."""
from causal_integrated_can import CausalIntegratedCan
from authority_can_scheduler import AuthorityCanScheduler


def setup():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in ("left", "right"):
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model, AuthorityCanScheduler(model.link)


model, control = setup()
assert control.stage("left", size=8, now=0.041, deadline=0.09)
assert control.stage("right", size=8, now=0.041, deadline=0.09)
events = control.dispatch(until=0.06)
assert len(events) == 2 and all(e["kind"] == "control" and not e["late"] for e in events)
print("PASS authorized control frames reach synthetic scheduler dispatch")

model, control = setup()
assert control.stage("left", size=8, now=0.041, deadline=0.8)
assert control.stage("right", size=8, now=0.041, deadline=0.8)
assert control.dispatch(until=0.55) == []
assert control.revoked and not control.scheduler.queue
assert not control.stage("left", size=8, now=0.56, deadline=0.8)
print("PASS heartbeat expiry blocks queued CAN control before dispatch")

model, control = setup()
assert control.stage("left", size=8, now=0.041, deadline=0.09)
assert control.stage("right", size=8, now=0.041, deadline=0.09)
assert model.link.fault.protocol.receive(dict(
    kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
    forma_boot="right-boot", session="right-session", sequence=1,
    ready=False
), now=0.042)
assert control.dispatch(until=0.05) == []
assert control.revoked and not control.scheduler.queue
print("PASS one peer Ready=false cancels both peers queued CAN control")

model, control = setup()
assert control.stage("left", size=8, now=0.041, deadline=0.09)
model.bus.bus_off()
assert control.dispatch(until=0.05) == []
assert control.revoked and not control.scheduler.queue
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.06)
for unit in ("left", "right"):
    assert model.submit(unit, 0, now=0.061, deadline=0.10)
model.advance(until=0.08)
model.deliver_acks(until=0.10)
assert not model.link.eligible(now=0.10)
assert model.link.authorize(explicit=True, now=0.10)
assert not control.stage("left", size=8, now=0.101, deadline=0.15)
fresh = AuthorityCanScheduler(model.link)
assert fresh.stage("left", size=8, now=0.101, deadline=0.15)
assert len(fresh.dispatch(until=0.12)) == 1
assert not model.status()["motor_command_issued"]
assert not model.status()["physical_safety_verified"]
print("PASS bus-off generation fencing blocks stale scheduled controls")

print("PASS all authority-can-scheduler checks")
