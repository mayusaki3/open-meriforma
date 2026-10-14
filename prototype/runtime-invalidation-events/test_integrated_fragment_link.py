"""Suite 28: integrated fragment identity and fail-closed recovery."""
from integrated_can_link import IntegratedCanLink
from wire_envelope import encode
from canfd_fragments import fragment


def msg(unit, seq=0, *, main="M1", challenge="C1", session=None):
    return dict(kind="heartbeat", unit=unit, main_boot=main,
                challenge=challenge, forma_boot=unit + "-boot",
                session=session or unit + "-session", sequence=seq, ready=True)


def ready(link, *, main="M1", challenge="C1", suffix="session"):
    for unit in ("left", "right"):
        assert link.establish(unit, forma_boot=unit + "-boot",
                              main_boot=main, challenge=challenge,
                              session=unit + "-" + suffix)


link = IntegratedCanLink(("left", "right"))
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001, deadline=0.01)
assert link.submit(msg("right"), now=0.001, deadline=0.01)
keys = [item[-2] for item in link.fragments.queue]
assert len(keys) == len(set(keys))
assert all(key[0] == "M1:C1" for key in keys)
out = link.dispatch(until=0.01)
assert sum(row[-1] is True for row in out) == 2
assert link.authorize(explicit=True, now=0.01)
assert link.eligible(now=0.01)
print("PASS integrated exact fragment identities and two-peer authorization")

link = IntegratedCanLink(("left", "right"))
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001, deadline=0.01)
first = link.fragments.queue[0][-2]
assert link.submit(msg("left", 1), now=0.001, deadline=0.01)
second = link.fragments.queue[-1][-2]
assert first[2] != second[2]
out = link.dispatch(until=0.01)
assert {row[1][1] for row in out} == {first[2], second[2]}
print("PASS overlapping transfers from same peer retain distinct transfer IDs")

link = IntegratedCanLink(("left", "right"))
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001, deadline=0.00001 + 0.001)
link.dispatch(until=0.01)
assert link.invalidated and not link.authorize(explicit=True, now=0.01)
assert link.fragments.status()["queued"] == 0
print("PASS integrated fragment deadline failure blocks authorization")

link = IntegratedCanLink(("left", "right"), max_queue=1)
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001)
assert link.fragments.status()["queued"] == 1
assert not link.submit(msg("right"), now=0.001)
assert link.invalidated and link.fragments.status()["queued"] == 0
assert not link.authorize(explicit=True, now=0.002)
print("PASS incomplete transfer on queue overflow fails closed")

link = IntegratedCanLink(("left", "right"))
link.start_main(boot_id="M1", challenge="C1", now=0)
ready(link)
assert link.submit(msg("left"), now=0.001)
old_frame = link.fragments.queue[0][4]
link.bus_off_event()
link.bus_recovered()
link.start_main(boot_id="M2", challenge="C2", now=0.01)
ready(link, main="M2", challenge="C2", suffix="new")
assert not link.fragments.enqueue("heartbeat", "left", old_frame,
                                  generation="M1:C1", now=0.011, deadline=0.02)
assert link.submit(msg("left", main="M2", challenge="C2", session="left-new"),
                   now=0.011, deadline=0.02)
assert link.submit(msg("right", main="M2", challenge="C2", session="right-new"),
                   now=0.011, deadline=0.02)
assert sum(row[-1] is True for row in link.dispatch(until=0.02)) == 2
assert link.authorize(explicit=True, now=0.02)
assert not link.status(now=0.02)["physical_safety_verified"]
print("PASS bus-off recovery rejects stale-generation fragments")
print("PASS all integrated-fragment-link checks")
