"""Suite 50: test-only receiver rejects complete but unauthorized commands."""
from canfd_fragments import fragment
from causal_integrated_can import CausalIntegratedCan
from forma_command_receiver import FormaCommandReceiver


def ready():
    model = CausalIntegratedCan(("left", "right"))
    model.start()
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def test_valid():
    link = ready()
    receiver = FormaCommandReceiver(link)
    frames = fragment(bytes(range(110)), transfer_id=10)
    assert receiver.receive(frames[0], source="left", generation=link.generation,
                            deadline=0.09, now=0.05) is None
    assert not receiver.accepted
    assert receiver.receive(frames[1], source="left", generation=link.generation,
                            deadline=0.09, now=0.06) is True
    assert receiver.accepted == [("left", bytes(range(110)))]
    print("PASS complete valid command accepted only after final fragment")


def test_expired():
    link = ready()
    receiver = FormaCommandReceiver(link)
    frame = fragment(b"command", transfer_id=11)[0]
    assert receiver.receive(frame, source="left", generation=link.generation,
                            deadline=0.049, now=0.05) is False
    assert receiver.revoked and not receiver.accepted
    print("PASS expired complete command rejected")


def test_generation():
    link = ready()
    receiver = FormaCommandReceiver(link)
    frame = fragment(b"command", transfer_id=12)[0]
    assert receiver.receive(frame, source="left", generation="M0:C0",
                            deadline=0.09, now=0.05) is False
    assert receiver.revoked and not receiver.accepted
    print("PASS stale generation command rejected")


def test_ready_false():
    link = ready()
    receiver = FormaCommandReceiver(link)
    frame = fragment(b"command", transfer_id=13)[0]
    assert link.fault.protocol.receive(dict(
        kind="heartbeat", unit="right", main_boot="M1", challenge="C1",
        forma_boot="right-boot", session="right-session", sequence=1,
        ready=False), now=0.05)
    assert receiver.receive(frame, source="left", generation=link.generation,
                            deadline=0.09, now=0.06) is False
    assert receiver.revoked and not receiver.accepted
    print("PASS Ready=false rejects complete command")


def test_no_authority():
    link = ready()
    receiver = FormaCommandReceiver(link)
    frame = fragment(b"command", transfer_id=14)[0]
    link.bus_off_event()
    assert receiver.receive(frame, source="left", generation=link.generation,
                            deadline=0.09, now=0.05) is False
    assert receiver.revoked and not receiver.accepted
    print("PASS bus-off rejects complete command")


test_valid()
test_expired()
test_generation()
test_ready_false()
test_no_authority()
print("PASS all forma-command-receiver checks")
