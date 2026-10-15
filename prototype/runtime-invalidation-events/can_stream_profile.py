"""Suite 37: independently configurable synthetic CAN-FD traffic streams.

Stream offsets are periodic, including ACKs; no causal ACK dependency is modeled.
"""
import heapq
import math
from can_scheduler import CanScheduler, PRIORITY, finite

ALLOWED_KINDS = frozenset(PRIORITY)


def _positive(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite and positive")
    try:
        result = finite(value, minimum=0.000001)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"invalid {name}") from exc
    return result


def simulate_profile(*, units, streams, horizon_ms=1000,
                     nominal_bps=500_000, data_bps=2_000_000):
    """Simulate fixed release schedules on one non-preemptive priority bus.

    Each stream: name, kind, payload_bytes (0..64), period_ms, offset_ms,
    deadline_ms, per_unit (bool), frames_per_release (positive int).
    All timestamps are synthetic and independent of actual packet receipt.
    """
    if type(units) is not int or not 1 <= units <= 62:
        raise ValueError("units must be 1..62")
    horizon = _positive(horizon_ms, "horizon_ms") / 1000
    if type(streams) not in (list, tuple) or not streams:
        raise ValueError("streams must be a nonempty list")
    bus = CanScheduler(nominal_bps=nominal_bps, data_bps=data_bps)
    validated = []
    names = set()
    for stream in streams:
        if type(stream) is not dict or set(stream) != {
            "name", "kind", "payload_bytes", "period_ms", "offset_ms",
            "deadline_ms", "per_unit", "frames_per_release"
        }:
            raise ValueError("invalid stream fields")
        name, kind = stream["name"], stream["kind"]
        if type(name) is not str or not name or name in names or kind not in ALLOWED_KINDS:
            raise ValueError("invalid stream name or kind")
        names.add(name)
        size = stream["payload_bytes"]
        frames = stream["frames_per_release"]
        if type(size) is not int or not 0 <= size <= 64:
            raise ValueError("invalid payload_bytes")
        if type(frames) is not int or not 1 <= frames <= 1000:
            raise ValueError("invalid frames_per_release")
        if type(stream["per_unit"]) is not bool:
            raise ValueError("per_unit must be boolean")
        period = _positive(stream["period_ms"], "period_ms") / 1000
        deadline = _positive(stream["deadline_ms"], "deadline_ms") / 1000
        offset = stream["offset_ms"]
        if isinstance(offset, bool) or not isinstance(offset, (int, float)) or not math.isfinite(offset) or offset < 0:
            raise ValueError("invalid offset_ms")
        validated.append((name, kind, size, period, offset / 1000, deadline,
                          units if stream["per_unit"] else 1, frames))
    releases = []
    serial = 0
    for name, kind, size, period, offset, deadline, multiplicity, frames in validated:
        if offset >= horizon:
            continue
        count = math.ceil((horizon - offset) / period - 1e-12)
        if count < 0:
            count = 0
        if count * multiplicity * frames + len(releases) > 250_000:
            raise ValueError("profile generates too many frames")
        for cycle in range(count):
            release = offset + cycle * period
            for _ in range(multiplicity * frames):
                heapq.heappush(releases, (release, serial, name, kind, size,
                                          release + deadline))
                serial += 1
    ready = []
    clock = busy = max_wait = last_finish = 0.0
    by_stream = {name: {"frames": 0, "deadline_misses": 0,
                        "max_wait_ms": 0.0} for name, *_ in validated}
    while releases or ready:
        if not ready:
            clock = max(clock, releases[0][0])
        while releases and releases[0][0] <= clock + 1e-12:
            release, order, name, kind, size, due = heapq.heappop(releases)
            heapq.heappush(ready, (PRIORITY[kind], order, release, name, size, due))
        if not ready:
            continue
        _, _, release, name, size, due = heapq.heappop(ready)
        wait = max(0.0, clock - release) * 1000
        max_wait = max(max_wait, wait)
        stats = by_stream[name]
        stats["max_wait_ms"] = max(stats["max_wait_ms"], wait)
        stats["frames"] += 1
        clock += bus.duration(size)
        busy += bus.duration(size)
        last_finish = clock
        if clock > due + 1e-12:
            stats["deadline_misses"] += 1
    return {
        "units": units, "horizon_ms": horizon_ms,
        "nominal_bps": nominal_bps, "data_bps": data_bps,
        "frames": sum(s["frames"] for s in by_stream.values()),
        "utilization": busy / horizon, "max_wait_ms": max_wait,
        "deadline_misses": sum(s["deadline_misses"] for s in by_stream.values()),
        "backlog_clear_ms": max(0.0, last_finish - horizon) * 1000,
        "by_stream": by_stream, "model_only": True,
        "hardware_timing_verified": False, "physical_safety_verified": False,
        "ack_causally_modeled": False,
    }


def example_streams():
    """Illustrative rates/sizes, NOT actual Forma protocol requirements."""
    return [
        dict(name="heartbeat", kind="heartbeat", payload_bytes=64,
             period_ms=10, offset_ms=0, deadline_ms=10,
             per_unit=True, frames_per_release=1),
        dict(name="ack", kind="heartbeat", payload_bytes=48,
             period_ms=10, offset_ms=5, deadline_ms=10,
             per_unit=True, frames_per_release=1),
        dict(name="control", kind="control", payload_bytes=32,
             period_ms=10, offset_ms=1, deadline_ms=10,
             per_unit=True, frames_per_release=1),
        dict(name="diagnostic", kind="diagnostic", payload_bytes=64,
             period_ms=50, offset_ms=0, deadline_ms=50,
             per_unit=False, frames_per_release=2),
    ]
