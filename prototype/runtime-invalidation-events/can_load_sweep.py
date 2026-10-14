"""Suite 34 reference: deterministic CAN-FD load sweep, not hardware proof."""
import heapq
from can_scheduler import CanScheduler, PRIORITY, finite


def simulate_load(*, units, period_ms, diagnostic_frames, nominal_bps=500_000,
                  data_bps=2_000_000, cycles=100, deadline_ms=None):
    """Release periodic bursts; single non-preemptive bus; earliest ready priority.

    One 64-byte heartbeat and one 48-byte ACK per unit per cycle.
    Diagnostics: 64-byte frames per cycle, lower priority.
    ACK release is a synthetic periodic assumption, not dependent on delivery.
    """
    if type(units) is not int or not 1 <= units <= 62:
        raise ValueError("units must be 1..62")
    if type(cycles) is not int or not 1 <= cycles <= 10000:
        raise ValueError("invalid cycles")
    if type(diagnostic_frames) is not int or not 0 <= diagnostic_frames <= 1000:
        raise ValueError("invalid diagnostics")
    period = finite(period_ms, minimum=0.000001) / 1000
    deadline = period if deadline_ms is None else finite(deadline_ms, minimum=0.000001) / 1000
    bus = CanScheduler(nominal_bps=nominal_bps, data_bps=data_bps)
    releases = []
    serial = 0
    for cycle in range(cycles):
        base = cycle * period
        for unit in range(units):
            for kind, size, offset in (("heartbeat", 64, 0.0),
                                       ("heartbeat", 48, period * 0.5)):
                heapq.heappush(releases, (base + offset, serial, kind, size,
                                          base + offset + deadline))
                serial += 1
        for _ in range(diagnostic_frames):
            heapq.heappush(releases, (base, serial, "diagnostic", 64,
                                      base + period))
            serial += 1
    ready = []
    clock = 0.0
    busy = 0.0
    maximum_wait = 0.0
    misses = 0
    by_kind = {"heartbeat": 0, "diagnostic": 0}
    last_finish = 0.0
    while releases or ready:
        if not ready and releases:
            clock = max(clock, releases[0][0])
        while releases and releases[0][0] <= clock + 1e-12:
            release, order, kind, size, due = heapq.heappop(releases)
            heapq.heappush(ready, (PRIORITY[kind], order, release, kind, size, due))
        if not ready:
            continue
        _, order, release, kind, size, due = heapq.heappop(ready)
        maximum_wait = max(maximum_wait, clock - release)
        duration = bus.duration(size)
        clock += duration
        busy += duration
        last_finish = clock
        by_kind[kind] += 1
        if clock > due + 1e-12:
            misses += 1
    horizon = cycles * period
    return {"units": units, "period_ms": period_ms,
            "diagnostic_frames": diagnostic_frames,
            "nominal_bps": nominal_bps, "data_bps": data_bps,
            "cycles": cycles, "frames": sum(by_kind.values()),
            "utilization": busy / horizon,
            "max_wait_ms": maximum_wait * 1000,
            "deadline_misses": misses,
            "backlog_clear_ms": max(0.0, last_finish - horizon) * 1000,
            "by_kind": by_kind,
            "model_only": True, "hardware_timing_verified": False,
            "physical_safety_verified": False}


def sweep(*, unit_counts=(2, 4, 8, 16), periods_ms=(10, 20),
          diagnostic_frames=(0, 4, 16), nominal_bps=500_000,
          data_bps=2_000_000, cycles=100):
    return [simulate_load(units=u, period_ms=p, diagnostic_frames=d,
                          nominal_bps=nominal_bps, data_bps=data_bps, cycles=cycles)
            for u in unit_counts for p in periods_ms for d in diagnostic_frames]
