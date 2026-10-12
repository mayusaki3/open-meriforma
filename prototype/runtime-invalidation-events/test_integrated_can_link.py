from integrated_can_link import IntegratedCanLink
from wire_envelope import encode
from canfd_fragments import fragment


def msg(unit, seq=0, *, main="M1", challenge="C1", session=None):
    return dict(kind="heartbeat", unit=unit, main_boot=main,
                challenge=challenge, forma_boot=unit + "-boot",
                session=session or unit + "-session", sequence=seq, ready=True)


def ready(link, *, main="M1", challenge="C1", session_suffix="session"):
    for unit in ("left", "right"):
        assert link.establish(unit, forma_boot=unit + "-boot", main_boot=main,
                              challenge=challenge, session=unit + "-" + session_suffix)


link = IntegratedCanLink(("left", "right"))
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
for unit in ("left", "right"):
    assert link.submit(msg(unit), now=0.001, deadline=0.01)
result = link.dispatch(until=0.01)
assert len(result) >= 2
assert sum(row[-1] is True for row in result) == 2
assert link.authorize(explicit=True, now=0.01)
assert link.eligible(now=0.01)
print("PASS envelope through fragments, scheduling and two Forma sessions")

assert link.submit(msg("left", 1), now=0.015, deadline=0.025)
assert link.submit(msg("right", 1), now=0.015, deadline=0.025)
link.dispatch(until=0.025)
assert link.eligible(now=0.025)
print("PASS successive integrated heartbeat cycles")

link.bus_off_event()
assert not link.status(now=0.026)["eligible"]
assert not link.authorize(explicit=True, now=0.027)
link.bus_recovered()
assert not link.eligible(now=0.028)
link.start_main(boot_id="M2", challenge="C2", now=0.03)
ready(link, main="M2", challenge="C2", session_suffix="new")
for unit in ("left", "right"):
    assert link.submit(msg(unit, main="M2", challenge="C2", session=unit + "-new"),
                       now=0.031, deadline=0.04)
link.dispatch(until=0.04)
assert not link.eligible(now=0.04)
assert link.authorize(explicit=True, now=0.04)
print("PASS bus-off requires new challenge, sessions and explicit authorization")

link = IntegratedCanLink(("left", "right"), heartbeat_timeout=0.02)
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
for unit in ("left", "right"):
    link.submit(msg(unit), now=0.001, deadline=0.01)
link.dispatch(until=0.01)
assert link.authorize(explicit=True, now=0.01)
assert not link.eligible(now=0.031)
assert not link.authorize(explicit=True, now=0.032)
print("PASS missing heartbeat invalidates whole pipeline")

link = IntegratedCanLink(("left", "right"), max_queue=1)
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001)
assert not link.submit(msg("right"), now=0.001)
assert link.status(now=0.002)["invalidated"]
print("PASS queue saturation fails closed")

assert not link.status(now=0.002)["motor_command_issued"]
assert not link.status(now=0.002)["physical_safety_verified"]
print("PASS no physical safety or motor control claims")
print("PASS all integrated-can-link checks")
