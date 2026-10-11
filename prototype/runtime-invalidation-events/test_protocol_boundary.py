from protocol_boundary import ProtocolBoundary


def msg(unit, *, seq, session, ready=True, main="M1", challenge="C1", boot=None):
    return dict(kind="heartbeat", unit=unit, main_boot=main,
                challenge=challenge, forma_boot=boot or unit + "-B1",
                session=session, sequence=seq, ready=ready)


p = ProtocolBoundary(("left", "right"), timeout=0.5)
p.start_main(boot_id="M1", challenge="C1")
for u in ("left", "right"):
    assert p.establish(u, forma_boot=u + "-B1", main_boot="M1",
                       challenge="C1", session=u + "-S1")
assert p.receive(msg("left", seq=0, session="left-S1"), now=0.1)
assert not p.authorize(explicit=True, now=0.1)
assert p.receive(msg("right", seq=0, session="right-S1"), now=0.1)
assert p.authorize(explicit=True, now=0.1)
print("PASS transport-neutral schema feeds coordinated readiness")

assert not p.receive(msg("left", seq=0, session="left-S1"), now=0.2)
assert not p.receive(msg("left", seq=99, session="left-OLD"), now=0.2)
assert p.eligible(now=0.2)
assert p.receive(msg("right", seq=1, session="right-S1", ready=False), now=0.3)
assert not p.eligible(now=0.3)
assert p.receive(msg("right", seq=2, session="right-S1"), now=0.4)
assert not p.eligible(now=0.4)
print("PASS duplicate, stale session and unready messages cannot grant authority")

assert p.authorize(explicit=True, now=0.4)
assert not p.eligible(now=0.91)
assert p.receive(msg("left", seq=1, session="left-S1"), now=0.92)
assert p.receive(msg("right", seq=3, session="right-S1"), now=0.92)
assert not p.eligible(now=0.92)
assert p.authorize(explicit=True, now=0.92)
print("PASS timeout invalidates authority before recovery heartbeat")

assert p.establish("left", forma_boot="left-B2", main_boot="M1",
                   challenge="C1", session="left-S2")
assert not p.eligible(now=0.93)
assert not p.receive(msg("left", seq=100, session="left-S1"), now=0.94)
assert p.receive(msg("left", seq=0, session="left-S2", boot="left-B2"), now=0.95)
assert not p.eligible(now=0.95)
assert p.authorize(explicit=True, now=0.95)
print("PASS partial Forma reboot and session replacement require reauthorization")

p.start_main(boot_id="M2", challenge="C2")
assert not p.receive(msg("left", seq=101, session="left-S2", boot="left-B2"), now=1.0)
for u, boot, session in (("left", "left-B2", "left-S3"),
                         ("right", "right-B1", "right-S2")):
    assert p.establish(u, forma_boot=boot, main_boot="M2",
                       challenge="C2", session=session)
    assert p.receive(msg(u, seq=0, session=session, boot=boot,
                         main="M2", challenge="C2"), now=1.01)
assert not p.eligible(now=1.01)
assert p.authorize(explicit=True, now=1.01)
print("PASS Main restart rejects prior challenge and requires new sessions")

for invalid in (lambda: p.receive({"kind": "heartbeat"}, now=1.02),
                lambda: p.receive(dict(msg("left", seq=1, session="left-S3",
                                           boot="left-B2", main="M2", challenge="C2"),
                                       kind="command"), now=1.02),
                lambda: p.authorize(explicit=1, now=1.02)):
    try:
        invalid()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid message accepted")
assert not p.status(now=1.02)["motor_command_issued"]
print("PASS malformed schema rejected without hardware actuation")
print("PASS all protocol-boundary checks")
