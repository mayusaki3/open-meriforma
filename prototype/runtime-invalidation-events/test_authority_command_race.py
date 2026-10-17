"""Suite 43: command staging versus multi-Forma authority invalidation.

The gate is a synthetic staging adapter, not CAN frame or motor output.
"""
from causal_integrated_can import CausalIntegratedCan
from authority_command_gate import AuthorityCommandGate


def ready_pair():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in ("left", "right"):
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model, AuthorityCommandGate(model.link)


model, gate = ready_pair()
assert gate.stage("left", "C1", now=0.041)
assert gate.dispatch(now=0.042) == [("left", "C1")]
assert not gate.revoked
print("PASS valid command staging requires live explicit authority")

model, gate = ready_pair()
assert gate.stage("left", "C1", now=0.041)
assert gate.stage("right", "C2", now=0.041)
assert len(gate.queue) == 2
assert not model.link.eligible(now=0.55)
assert gate.dispatch(now=0.55) == []
assert gate.revoked and not gate.queue
assert gate.delivered == []
print("PASS timeout between enqueue and dispatch discards both queued commands")

model, gate = ready_pair()
assert gate.stage("left", "C1", now=0.041)
assert gate.stage("right", "C2", now=0.041)
protocol = model.link.fault.protocol
assert protocol.receive(dict(
    kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
    forma_boot="right-boot", session="right-session",
    sequence=1, ready=False
), now=0.042)
assert gate.dispatch(now=0.043) == []
assert gate.revoked and not gate.queue
assert not gate.stage("left", "C3", now=0.044)
print("PASS one peer Ready=false blocks all queued and new commands")

model, gate = ready_pair()
assert gate.stage("left", "C1", now=0.041)
model.bus.bus_off()
assert gate.dispatch(now=0.042) == []
model.link.bus_recovered()
model.start(boot_id="M2", challenge="C2", now=0.05)
for unit in ("left", "right"):
    assert model.submit(unit, 0, now=0.051, deadline=0.09)
model.advance(until=0.065)
model.deliver_acks(until=0.08)
assert not model.link.eligible(now=0.08)
assert gate.dispatch(now=0.08) == []
assert not gate.queue and not gate.delivered
assert model.link.authorize(explicit=True, now=0.08)
assert not gate.stage("left", "C2", now=0.08)
new_gate = AuthorityCommandGate(model.link)
assert new_gate.stage("left", "C3", now=0.081)
assert new_gate.dispatch(now=0.082) == [("left", "C3")]
assert not model.status()["motor_command_issued"]
assert not model.status()["physical_safety_verified"]
print("PASS bus-off and generation change forbid stale command replay")
print("PASS all authority-command-race checks")
