"""Suite 45: control-frame gating on the synthetic shared bus."""
from causal_integrated_can import CausalIntegratedCan
from authority_shared_bus import AuthoritySharedBus


def ready():
    m = CausalIntegratedCan(("left", "right"))
    m.start()
    for unit in m.link.units:
        assert m.submit(unit, 0, now=0.001, deadline=0.04)
    m.advance(until=0.02)
    m.deliver_acks(until=0.04)
    assert m.link.authorize(explicit=True, now=0.04)
    m.bus = AuthoritySharedBus(m.link)
    return m


m = ready()
assert m.bus.enqueue_control("left", b"control-left", now=0.041, deadline=0.09)
assert m.bus.enqueue_control("right", b"control-right", now=0.041, deadline=0.09)
events = m.bus.dispatch(until=0.06)
assert len(events) == 2 and all(e[0] == "background" for e in events)
assert not m.status()["motor_command_issued"]
print("PASS explicitly authorized controls traverse synthetic shared queue")

m = ready()
assert m.bus.enqueue_control("left", b"control", now=0.041, deadline=0.8)
assert m.bus.dispatch(until=0.55) == []
assert m.bus.control_revoked and not m.bus.queue
assert not m.bus.enqueue_control("left", b"retry", now=0.56, deadline=0.8)
print("PASS expired heartbeat cancels control before shared dispatch")

m = ready()
assert m.bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
assert m.link.fault.protocol.receive(dict(
    kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
    forma_boot="right-boot", session="right-session", sequence=1, ready=False
), now=0.042)
assert m.bus.dispatch(until=0.05) == []
assert m.bus.control_revoked and not m.bus.queue
print("PASS Ready=false cancels shared-bus control")

m = ready()
assert m.bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
old = m.bus
old.bus_off()
assert old.dispatch(until=0.05) == []
assert not old.queue
m.link.bus_recovered()
m.start(boot_id="M2", challenge="C2", now=0.06)
assert old.dispatch(until=0.07) == []
assert old.failed
print("PASS bus-off fences old shared-bus control generation")
print("PASS all authority-shared-bus checks")
