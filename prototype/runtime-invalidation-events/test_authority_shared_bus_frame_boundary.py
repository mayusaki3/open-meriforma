"""Suite 48: per-control-fragment synthetic revocation checks.

No hardware TX, atomic cancellation, or physical motor STOP is asserted.
"""
from causal_integrated_can import CausalIntegratedCan
from authority_shared_bus import AuthoritySharedBus


class FrameBoundaryBus(AuthoritySharedBus):
    def __init__(self, link, *, inject):
        super().__init__(link)
        self.inject = inject
        self.seen = 0

    def _before_control_frame(self, *, until, key):
        self.seen += 1
        self.inject(self.link, self.seen)


def setup(inject):
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    bus = FrameBoundaryBus(model.link, inject=inject)
    bus.now = 0.04
    bus.available_at = 0.04
    assert bus.enqueue_control("left", b"left", now=0.041, deadline=0.09)
    assert bus.enqueue_control("right", b"right", now=0.041, deadline=0.09)
    return bus


def run(inject, *, blocked):
    bus = setup(inject)
    events = bus.dispatch(until=0.06)
    sent = [event for event in events if event[0] == "background"]
    denied = [event for event in events if event[0] == "blocked"]
    assert len(sent) == (1 if blocked else 2), events
    assert len(denied) == (1 if blocked else 0), events
    assert bus.seen == 2, events
    if blocked:
        assert bus.control_revoked
        assert not bus.queue
        assert not bus.enqueue_control("left", b"replay", now=0.061, deadline=0.09)
    return bus


run(lambda link, index: None, blocked=False)
print("PASS both controls dispatch when authority remains valid")


def ready_false(link, index):
    if index == 2:
        assert link.fault.protocol.receive(dict(
            kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
            forma_boot="right-boot", session="right-session", sequence=1,
            ready=False), now=0.05)


run(ready_false, blocked=True)
print("PASS Ready=false between control frames blocks second frame")


def bus_off(link, index):
    if index == 2:
        link.bus_off_event()


run(bus_off, blocked=True)
print("PASS bus-off between control frames blocks second frame")


def generation_change(link, index):
    if index == 2:
        link.generation = "M2:C2"


run(generation_change, blocked=True)
print("PASS generation change between control frames blocks second frame")
print("PASS all authority-shared-bus-frame-boundary checks")
