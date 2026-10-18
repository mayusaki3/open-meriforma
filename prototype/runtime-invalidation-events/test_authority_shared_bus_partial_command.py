"""Suite 49: synthetic multi-fragment control and receiver-side discard.

Receiver here is a test-only reassembly model, NOT a Forma firmware implementation.
No motor output, CAN controller, or authenticated command execution.
"""
from canfd_fragments import Reassembler, parse
from causal_integrated_can import CausalIntegratedCan
from authority_shared_bus import AuthoritySharedBus

PAYLOAD = bytes(range(110))  # exactly two 55-byte CAN-FD payload chunks


class PartialBus(AuthoritySharedBus):
    def __init__(self, link, *, fault):
        super().__init__(link)
        self.fault_inject = fault
        self.seen = 0
        self.receiver = Reassembler(timeout=0.2)
        self.applied = []
        self.partial = 0
        self.blocked = 0

    def _before_control_frame(self, *, until, key):
        self.seen += 1
        if self.seen == 2:
            self.fault_inject(self.link)

    def _before_background_frame(self, *, until, key):
        if not super()._before_background_frame(until=until, key=key):
            self.receiver.active.clear()
            self.blocked += 1
            return False
        return True

    def dispatch(self, *, until, drop=None):
        events = super().dispatch(until=until, drop=drop)
        # Model delivery only of frames actually dispatched by the shared bus.
        # This intentionally never interprets a fragment as an executable command.
        for event in events:
            if event[0] != "background":
                continue
            _, source, tid, index = event[1]
            # Retain an immutable copy of the transmitted fragments from the fixture.
            frame = self.frames[(source, tid, index)]
            result = self.receiver.accept(frame, source=source, now=event[3])
            if result is None:
                self.partial += 1
            else:
                self.applied.append(result)
        if self.control_revoked or self.failed:
            self.receiver.active.clear()
        return events


def setup(fault):
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    bus = PartialBus(model.link, fault=fault)
    bus.now = bus.available_at = 0.04
    assert bus.enqueue_control("left", PAYLOAD, now=0.041, deadline=0.09)
    controls = [item for item in bus.queue if item[2] == "background"]
    assert len(controls) == 2
    assert [parse(item[4])[1] for item in controls] == [0, 1]
    bus.frames = {(item[3], item[7], item[8]): item[4] for item in controls}
    return bus


def run(fault, *, revoked):
    bus = setup(fault)
    events = bus.dispatch(until=0.06)
    sent = [event for event in events if event[0] == "background"]
    if revoked:
        assert len(sent) == 1, events
        assert bus.partial == 1 and not bus.applied
        assert bus.blocked == 1 and bus.control_revoked
        assert not bus.queue and not bus.receiver.active
        assert not bus.enqueue_control("left", b"replay", now=0.061, deadline=0.09)
    else:
        assert len(sent) == 2, events
        assert bus.partial == 1 and bus.applied == [PAYLOAD]
        assert not bus.receiver.active and bus.blocked == 0
    return bus


run(lambda link: None, revoked=False)
print("PASS complete two-fragment command reconstructs only after final fragment")


def ready_false(link):
    assert link.fault.protocol.receive(dict(
        kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
        forma_boot="right-boot", session="right-session", sequence=1,
        ready=False), now=0.06)


run(ready_false, revoked=True)
print("PASS Ready=false blocks final fragment and discards receiver partial")


def bus_off(link):
    link.bus_off_event()


run(bus_off, revoked=True)
print("PASS bus-off blocks final fragment and discards receiver partial")


def generation_change(link):
    link.generation = "M2:C2"


run(generation_change, revoked=True)
print("PASS generation change blocks final fragment and discards receiver partial")
print("PASS all authority-shared-bus-partial-command checks")
