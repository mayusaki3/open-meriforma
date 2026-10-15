"""Suite 37 tests: independent stream rates, sizes, priorities and overload."""
from can_stream_profile import simulate_profile, example_streams

base = example_streams()
result = simulate_profile(units=2, streams=base, horizon_ms=100)
assert result["by_stream"]["heartbeat"]["frames"] == 20
assert result["by_stream"]["ack"]["frames"] == 20
assert result["by_stream"]["control"]["frames"] == 20
assert result["by_stream"]["diagnostic"]["frames"] == 4
assert result["frames"] == 64
assert not result["ack_causally_modeled"]
print("PASS independent per-stream periods and per-unit multiplicity")

fewer = simulate_profile(units=1, streams=base, horizon_ms=100)
more = simulate_profile(units=8, streams=base, horizon_ms=100)
assert fewer["utilization"] < more["utilization"]
assert fewer["by_stream"]["diagnostic"]["frames"] == more["by_stream"]["diagnostic"]["frames"]
print("PASS per-unit load scales without multiplying global diagnostics")

large = simulate_profile(units=2, streams=base, horizon_ms=100)
small_streams = [dict(stream, payload_bytes=8) for stream in base]
small = simulate_profile(units=2, streams=small_streams, horizon_ms=100)
assert large["utilization"] > small["utilization"]
assert large["frames"] == small["frames"]
print("PASS independently adjustable frame sizes affect utilization")

over = simulate_profile(units=32, streams=base, horizon_ms=100,
                        nominal_bps=250_000, data_bps=1_000_000)
assert over["deadline_misses"] > 0 and over["backlog_clear_ms"] > 0
assert sum(x["deadline_misses"] for x in over["by_stream"].values()) == over["deadline_misses"]
print("PASS overload produces per-stream deadline misses and backlog")

bad = [
    [dict(base[0], payload_bytes=65)],
    [dict(base[0], period_ms=0)],
    [dict(base[0], offset_ms=-1)],
    [dict(base[0], frames_per_release=0)],
    [dict(base[0], per_unit=1)],
    [base[0], base[0]],
]
for streams in bad:
    try:
        simulate_profile(units=2, streams=streams)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid stream accepted")
print("PASS invalid stream specifications rejected")
print("PASS all can-stream-profile checks")
