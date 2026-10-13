from can_burst_probe import simulate_burst
from can_scheduler import CanScheduler

def row(kind, unit, size=64, at=0, deadline=0.04):
    return dict(kind=kind, unit=unit, size=size, at=at, deadline=deadline)

units = ("left", "right")
traffic = [row("diagnostic", "left") for _ in range(8)]
traffic += [row("control", "right") for _ in range(8)]
traffic += [row("heartbeat", u, 16, deadline=0.01) for u in units]
traffic += [row("safety", "left", 8, deadline=0.005)]
r = simulate_burst(units, traffic)
assert [v["kind"] for v in r["sent"][:3]] == ["safety", "heartbeat", "heartbeat"]
assert not r["invalidated"]
print("PASS simultaneous mixed-priority burst dispatches safety first")

s = CanScheduler()
duration = s.duration(64)
r = simulate_burst(units, [row("control", "left", deadline=0.0001),
                           row("heartbeat", "right", 16, deadline=0.00001)],
                   until=0.01)
assert r["by_kind"]["heartbeat"]["missed_deadlines"] == 1
assert r["invalidated"]
print("PASS heartbeat deadline miss revokes scheduler authority")

r = simulate_burst(units, [row("diagnostic", "left") for _ in range(20)]
                   + [row("safety", "right", 8)], max_queue=4)
assert r["rejected_count"] > 0
assert r["sent"][0]["kind"] == "safety"
assert r["by_kind"]["diagnostic"]["sent"] <= 3
print("PASS queue overload sheds lower-priority traffic")

r = simulate_burst(units, [row("diagnostic", "left") for _ in range(50)]
                   + [row("heartbeat", "right", 16)], until=0.001)
assert r["queued"] > 0
assert r["sent"][0]["kind"] == "heartbeat"
assert not r["hardware_timing_verified"] and not r["physical_safety_verified"]
print("PASS bounded dispatch window leaves backlog without hardware timing claims")

for bad in (
    [dict(kind="bogus", unit="left", size=8, at=0, deadline=1)],
    [dict(kind="heartbeat", unit="absent", size=8, at=0, deadline=1)],
    [dict(kind="heartbeat", unit="left", size=65, at=0, deadline=1)],
):
    try:
        simulate_burst(units, bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid burst input accepted")
print("PASS malformed burst inputs rejected")
print("PASS all can-burst-probe checks")
