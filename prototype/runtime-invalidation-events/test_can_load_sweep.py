"""Suite 34: parameter sweep of estimated CAN-FD load limits."""
from can_load_sweep import simulate_load, sweep

low = simulate_load(units=2, period_ms=20, diagnostic_frames=0, cycles=40)
high = simulate_load(units=16, period_ms=10, diagnostic_frames=16, cycles=40)
assert low["frames"] == 160 and low["deadline_misses"] == 0
assert high["frames"] == 1920
assert high["utilization"] > low["utilization"]
assert high["max_wait_ms"] >= low["max_wait_ms"]
print("PASS unit count and diagnostic load increase modeled bus utilization")

slow = simulate_load(units=8, period_ms=10, diagnostic_frames=8,
                     nominal_bps=250_000, data_bps=1_000_000, cycles=40)
fast = simulate_load(units=8, period_ms=10, diagnostic_frames=8,
                     nominal_bps=1_000_000, data_bps=4_000_000, cycles=40)
assert slow["utilization"] > fast["utilization"]
assert slow["deadline_misses"] >= fast["deadline_misses"]
print("PASS nominal/data bitrate parameters affect modeled load")

over = simulate_load(units=62, period_ms=1, diagnostic_frames=32, cycles=20)
assert over["utilization"] > 1
assert over["deadline_misses"] > 0
assert over["backlog_clear_ms"] > 0
print("PASS overload reports deadline misses and residual backlog")

rows = sweep(unit_counts=(2, 4), periods_ms=(10, 20),
             diagnostic_frames=(0, 4), cycles=20)
assert len(rows) == 8
assert all(r["frames"] == 20 * (2 * r["units"] + r["diagnostic_frames"])
           for r in rows)
assert all(r["model_only"] and not r["hardware_timing_verified"]
           and not r["physical_safety_verified"] for r in rows)
print("PASS sweep produces comparable metrics with explicit model limitations")

for kwargs in ({"units": 0}, {"units": 63}, {"period_ms": 0},
               {"diagnostic_frames": -1}, {"cycles": 0},
               {"nominal_bps": 0}):
    try:
        simulate_load(**dict({"units": 2, "period_ms": 10, "diagnostic_frames": 0}, **kwargs))
    except (ValueError, TypeError):
        pass
    else:
        raise AssertionError(f"accepted invalid configuration: {kwargs}")
print("PASS invalid sweep configurations rejected")
print("PASS all can-load-sweep checks")
