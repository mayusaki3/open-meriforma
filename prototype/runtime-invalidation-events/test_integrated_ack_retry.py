"""Suite 29: synthetic application-level ACK and bounded retry."""
from integrated_can_link import IntegratedCanLink


def msg(unit, seq=0, *, main="M1", challenge="C1", session=None):
    return dict(kind="heartbeat", unit=unit, main_boot=main,
                challenge=challenge, forma_boot=unit + "-boot",
                session=session or unit + "-session", sequence=seq, ready=True)


def setup():
    link = IntegratedCanLink(("left", "right"), heartbeat_timeout=0.5)
    link.start_main(boot_id="M1", challenge="C1", now=0)
    for unit in ("left", "right"):
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot="M1", challenge="C1",
                              session=unit + "-session")
    return link


link = setup()
assert link.submit(msg("left"), now=0.001, deadline=0.05)
tid = next(iter(link.fault.pending))
assert link.dispatch(until=0.05)[-1][-1] is True
assert tid not in link.fault.pending
assert link.retry_due(now=0.2) == []
print("PASS completed transfer receives application ACK and needs no retry")

link = setup()
assert link.submit(msg("left"), now=0.001, deadline=0.05)
tid = next(iter(link.fault.pending))
assert link.dispatch(until=0.05, ack_drop={tid})[-1][-1] is True
assert tid in link.fault.pending
assert link.retry_due(now=0.11, deadline=0.2) == [tid]
assert link.dispatch(until=0.2)[-1][-1] is True
assert tid not in link.fault.pending
assert len([k for k in link.completed_transfers if k[2] == tid]) == 1
print("PASS lost ACK triggers duplicate-safe retry without replaying heartbeat")

link = setup()
assert link.submit(msg("left"), now=0.001, deadline=0.05)
tid = next(iter(link.fault.pending))
link.dispatch(until=0.05, ack_drop={tid})
assert link.retry_due(now=0.11, deadline=0.2) == [tid]
link.dispatch(until=0.2, ack_drop={tid})
assert link.retry_due(now=0.22, deadline=0.3) == [tid]
link.dispatch(until=0.3, ack_drop={tid})
assert link.retry_due(now=0.33, deadline=0.4) == []
assert tid not in link.fault.pending
print("PASS bounded retries exhaust without implicit transfer ACK")

link = setup()
assert link.submit(msg("left"), now=0.001, deadline=0.05)
tid = next(iter(link.fault.pending))
link.dispatch(until=0.05, ack_drop={tid})
link.bus_off_event()
link.bus_recovered()
assert link.retry_due(now=0.11) == []
link.start_main(boot_id="M2", challenge="C2", now=0.12)
assert link.retry_due(now=0.23) == []
assert not link.fault.pending
assert not link.completed_transfers
print("PASS session restart fences old ACK/retry state")

link = setup()
assert link.submit(msg("left"), now=0.001, deadline=0.05)
try:
    link.dispatch(until=0.05, ack_drop=[])
except ValueError:
    pass
else:
    raise AssertionError("invalid ACK-drop input accepted")
assert not link.status(now=0.05)["motor_command_issued"]
assert not link.status(now=0.05)["physical_safety_verified"]
print("PASS malformed ACK-loss input rejected without physical safety claims")
print("PASS all integrated-ack-retry checks")
