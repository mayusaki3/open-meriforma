"""Synthetic CAN-FD utilization estimator, not a physical bus guarantee."""
from can_scheduler import CanScheduler, PRIORITY


def estimate_traffic(units, traffic, *, nominal_bps=500_000, data_bps=2_000_000,
                     utilization_limit=0.7):
    """Traffic rows: kind, frames_per_unit_per_second, payload_bytes, optional unit names.

    Uses the existing scheduler's provisional airtime approximation. Periodic
    averages do not predict arbitration, correlated bursts or deadline misses.
    """
    if type(units) not in (list, tuple) or not units or any(
            type(u) is not str or not u for u in units) or len(set(units)) != len(units):
        raise ValueError("invalid unit inventory")
    if type(traffic) not in (list, tuple) or not traffic:
        raise ValueError("invalid traffic matrix")
    if type(utilization_limit) not in (int, float) or isinstance(utilization_limit, bool) or not 0 < utilization_limit <= 1:
        raise ValueError("invalid utilization limit")
    scheduler = CanScheduler(nominal_bps=nominal_bps, data_bps=data_bps)
    totals = {kind: 0.0 for kind in PRIORITY}
    breakdown = []
    for row in traffic:
        if type(row) is not dict or set(row) not in (
                {"kind", "rate_hz", "bytes"}, {"kind", "rate_hz", "bytes", "units"}):
            raise ValueError("invalid traffic row")
        kind, rate, size = row["kind"], row["rate_hz"], row["bytes"]
        if kind not in PRIORITY or type(rate) not in (int, float) or not 0 <= rate < float("inf"):
            raise ValueError("invalid traffic kind or rate")
        duration = scheduler.duration(size)
        targets = row.get("units", units)
        if type(targets) not in (list, tuple) or not targets or any(
                type(u) is not str or u not in units for u in targets) or len(set(targets)) != len(targets):
            raise ValueError("invalid traffic targets")
        load = duration * rate * len(targets)
        totals[kind] += load
        breakdown.append({"kind": kind, "units": len(targets),
                          "frames_per_second": rate * len(targets),
                          "airtime_seconds_per_second": load})
    utilization = sum(totals.values())
    return {"utilization": utilization, "within_limit": utilization <= utilization_limit,
            "over_capacity": utilization > 1, "by_kind": totals,
            "breakdown": breakdown, "unit_count": len(units),
            "nominal_bps": nominal_bps, "data_bps": data_bps,
            "model_only": True, "hardware_timing_verified": False,
            "physical_safety_verified": False}
