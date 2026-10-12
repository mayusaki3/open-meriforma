from can_scheduler import CanScheduler

s = CanScheduler()
s.register("left")
s.register("right")
for kind in ("diagnostic", "control", "heartbeat", "safety"):
    assert s.enqueue(kind, unit="left", size=64, now=0)
out = s.dispatch(until=0.01)
assert [v["kind"] for v in out] == ["safety", "heartbeat", "control", "diagnostic"]
assert all(v["finish"] > v["start"] for v in out)
print("PASS safety-first scheduling and frame airtime accounting")

s = CanScheduler(max_queue=2)
s.register("left")
assert s.enqueue("diagnostic", unit="left", size=64, now=0)
assert s.enqueue("control", unit="left", size=64, now=0)
assert s.enqueue("safety", unit="left", size=8, now=0)
assert not s.enqueue("diagnostic", unit="left", size=64, now=0)
assert [v["kind"] for v in s.dispatch(until=0.01)] == ["safety", "control"]
assert s.status()["dropped"] == 2
print("PASS bounded queue and low-priority shedding")

s = CanScheduler(heartbeat_deadline=0.025)
s.register("left")
s.register("right")
assert s.authorize(explicit=True, now=0)
for step in range(1, 4):
    t = step * 0.01
    for unit in ("left", "right"):
        s.enqueue("heartbeat", unit=unit, size=16, now=t, deadline=t + 0.005)
    out = s.dispatch(until=t + 0.005)
    assert len(out) == 2 and all(not v["late"] for v in out)
    assert s.status()["authorized"]
print("PASS synthetic 100Hz heartbeat traffic for two Forma units")

s = CanScheduler(heartbeat_deadline=0.02)
s.register("left")
s.register("right")
assert s.authorize(explicit=True, now=0)
s.enqueue("heartbeat", unit="left", size=64, now=0.01, deadline=0.011)
s.enqueue("heartbeat", unit="right", size=64, now=0.01, deadline=0.01001)
s.dispatch(until=0.012)
assert s.status()["invalidated"] and not s.status()["authorized"]
assert not s.authorize(explicit=True, now=0.013)
s.reset_authority(now=0.014)
assert not s.status()["authorized"]
assert s.authorize(explicit=True, now=0.015)
print("PASS deadline miss invalidates authority; no automatic reauthorization")

s = CanScheduler(heartbeat_deadline=0.02)
s.register("left")
s.register("right")
assert s.authorize(explicit=True, now=0)
s.dispatch(until=0.021)
assert s.status()["invalidated"]
assert not s.authorize(explicit=True, now=0.022)
print("PASS missing peer heartbeat invalidates multi-unit authority")

s = CanScheduler(nominal_bps=500_000, data_bps=2_000_000)
s.register("left")
for i in range(100):
    s.enqueue("diagnostic", unit="left", size=64, now=0)
assert len(s.dispatch(until=0.01)) < 100
assert len(s.queue) > 0
print("PASS deterministic bandwidth-limited transmission")

for fn in (lambda: s.enqueue("heartbeat", unit="unknown", size=8, now=0.01),
           lambda: s.enqueue("control", unit="left", size=65, now=0.01),
           lambda: CanScheduler(data_bps=0),
           lambda: CanScheduler(max_queue=0)):
    try:
        fn()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
print("PASS invalid parameters rejected")
print("PASS all can-scheduler checks")
