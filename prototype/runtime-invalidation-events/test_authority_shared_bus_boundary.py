"""Suite 47: revocation between protocol dispatch and control authorization.

Synthetic deterministic injection only; not a real atomic CAN transmit gate.
"""
from causal_integrated_can import CausalIntegratedCan
from authority_shared_bus import AuthoritySharedBus


class BoundaryBus(AuthoritySharedBus):
    def __init__(self, link, *, inject):
        super().__init__(link)
        self.inject = inject
        self.injected = 0

    def _before_control_gate(self, *, until):
        self.injected += 1
        self.inject(self.link, until)


def ready(inject):
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    model.bus = BoundaryBus(model.link, inject=inject)
    model.bus.now = 0.04
    model.bus.available_at = 0.04
    return model


def run(inject, *, expect_sent):
    model = ready(inject)
    bus = model.bus
    assert bus.enqueue_control("left", b"control", now=0.041, deadline=0.09)
    assert bus.enqueue_control("right", b"control", now=0.041, deadline=0.09)
    events = bus.dispatch(until=0.06)
    controls = [e for e in events if e[0] == "background"]
    assert bool(controls) is expect_sent, events
    assert bus.injected == 1
    if not expect_sent:
        assert not bus.queue and bus.control_revoked
        assert not bus.enqueue_control("left", b"replay", now=0.061, deadline=0.09)
    return model


run(lambda link, until: None, expect_sent=True)
print("PASS valid authority allows control at boundary")


def revoke_ready(link, until):
    assert link.fault.protocol.receive(dict(
        kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
        forma_boot="right-boot", session="right-session", sequence=1,
        ready=False), now=0.05)


run(revoke_ready, expect_sent=False)
print("PASS Ready=false at boundary cancels both controls")


def revoke_bus(link, until):
    link.bus_off_event()


run(revoke_bus, expect_sent=False)
print("PASS bus-off at boundary cancels both controls")


def revoke_generation(link, until):
    link.generation = "M2:C2"


run(revoke_generation, expect_sent=False)
print("PASS generation mismatch at boundary cancels both controls")
print("PASS all authority-shared-bus-boundary checks")
