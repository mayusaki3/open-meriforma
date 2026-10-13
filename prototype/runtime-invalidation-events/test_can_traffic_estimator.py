from can_traffic_estimator import estimate_traffic
from can_scheduler import CanScheduler

units = ("left", "right")
rows = [
    {"kind": "heartbeat", "rate_hz": 100, "bytes": 16},
    {"kind": "control", "rate_hz": 100, "bytes": 64},
    {"kind": "safety", "rate_hz": 10, "bytes": 8},
    {"kind": "diagnostic", "rate_hz": 2, "bytes": 64},
]
result = estimate_traffic(units, rows)
s = CanScheduler()
expected = sum(s.duration(row["bytes"]) * row["rate_hz"] * len(units) for row in rows)
assert abs(result["utilization"] - expected) < 1e-12
assert result["unit_count"] == 2 and result["within_limit"]
assert abs(sum(result["by_kind"].values()) - expected) < 1e-12
print("PASS two-Forma mixed-traffic utilization matches scheduler model")

three = estimate_traffic(("left", "right", "head"), rows)
assert abs(three["utilization"] - 1.5 * result["utilization"]) < 1e-12
subset = estimate_traffic(("left", "right", "head"), [
    {"kind": "heartbeat", "rate_hz": 100, "bytes": 16, "units": ["left", "right"]}])
assert abs(subset["utilization"] - 200 * s.duration(16)) < 1e-12
print("PASS multi-Forma scaling and per-row target selection")

high = estimate_traffic(tuple(str(n) for n in range(20)), [
    {"kind": "control", "rate_hz": 1000, "bytes": 64}], utilization_limit=0.7)
assert high["over_capacity"] and not high["within_limit"]
assert high["utilization"] > 1
print("PASS overloaded traffic flagged without pretending to schedule it")

low_rate = estimate_traffic(units, rows, data_bps=500_000)
assert low_rate["utilization"] > result["utilization"]
assert not result["hardware_timing_verified"] and not result["physical_safety_verified"]
print("PASS bitrate sensitivity and explicit model-only limits")

invalid = [
    lambda: estimate_traffic((), rows),
    lambda: estimate_traffic(("a", "a"), rows),
    lambda: estimate_traffic(units, []),
    lambda: estimate_traffic(units, [{"kind": "unknown", "rate_hz": 1, "bytes": 8}]),
    lambda: estimate_traffic(units, [{"kind": "heartbeat", "rate_hz": -1, "bytes": 8}]),
    lambda: estimate_traffic(units, [{"kind": "heartbeat", "rate_hz": True, "bytes": 8}]),
    lambda: estimate_traffic(units, [{"kind": "heartbeat", "rate_hz": 1, "bytes": 65}]),
    lambda: estimate_traffic(units, [{"kind": "heartbeat", "rate_hz": 1, "bytes": 8, "units": ["missing"]}]),
    lambda: estimate_traffic(units, rows, utilization_limit=0),
]
for fn in invalid:
    try:
        fn()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid estimator input accepted")
print("PASS malformed traffic matrix rejected")
print("PASS all can-traffic-estimator checks")
