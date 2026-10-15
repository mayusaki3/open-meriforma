"""Suite 35: compare modeled CAN-FD configurations and screening limits."""
from can_configuration_review import review_configuration, compare_configurations

baseline = review_configuration(period_ms=10, nominal_bps=500_000,
                                data_bps=2_000_000, max_units=24, cycles=20)
assert baseline["max_passing_units"] > 0
assert all(row["screening_pass"] == (row["utilization"] <= 0.70
                                    and row["deadline_misses"] == 0)
           for row in baseline["rows"])
assert baseline["selected"]["units"] == baseline["max_passing_units"]
print("PASS maximum screened unit count respects both utilization and deadlines")

with_diag = review_configuration(period_ms=10, nominal_bps=500_000,
                                 data_bps=2_000_000, diagnostic_frames=16,
                                 max_units=24, cycles=20)
assert with_diag["max_passing_units"] <= baseline["max_passing_units"]
assert with_diag["rows"][0]["utilization"] > baseline["rows"][0]["utilization"]
assert with_diag["rows"][0]["utilization_headroom"] < baseline["rows"][0]["utilization_headroom"]
print("PASS diagnostic traffic reduces modeled headroom")

candidates = [
    dict(name="standard", period_ms=10, nominal_bps=500_000,
         data_bps=2_000_000, diagnostic_frames=4),
    dict(name="fast", period_ms=10, nominal_bps=1_000_000,
         data_bps=4_000_000, diagnostic_frames=4),
    dict(name="slow", period_ms=10, nominal_bps=250_000,
         data_bps=1_000_000, diagnostic_frames=4),
]
report = compare_configurations(candidates, max_units=24, cycles=20)
capacity = {r["name"]: r["max_passing_units"] for r in report["ranked"]}
assert capacity["fast"] >= capacity["standard"] >= capacity["slow"]
assert report["preferred"] == "fast"
assert all(not r["hardware_timing_verified"] for r in report["ranked"])
print("PASS candidate ranking is deterministic and labels estimates")

over = review_configuration(period_ms=0.1, nominal_bps=250_000,
                            data_bps=1_000_000, diagnostic_frames=30,
                            max_units=4, cycles=10)
assert over["max_passing_units"] == 0 and over["selected"] is None
assert all(not r["screening_pass"] for r in over["rows"])
print("PASS no-feasible-configuration case is explicit")

for invalid in (
    lambda: review_configuration(period_ms=10, nominal_bps=500_000,
                                 data_bps=2_000_000, max_units=0),
    lambda: review_configuration(period_ms=10, nominal_bps=500_000,
                                 data_bps=2_000_000, utilization_limit=1.1),
    lambda: compare_configurations([]),
    lambda: compare_configurations([candidates[0], candidates[0]]),
):
    try:
        invalid()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid configuration accepted")
print("PASS invalid and duplicate candidate inputs rejected")
print("PASS all can-configuration-review checks")
