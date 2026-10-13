"""Synthetic burst-delay probe using CanScheduler's non-preemptive frame model.

This is not worst-case physical CAN-FD timing or arbitration simulation.
"""
from can_scheduler import CanScheduler, PRIORITY


def simulate_burst(units, traffic, *, nominal_bps=500_000, data_bps=2_000_000,
                   max_queue=128, until=0.05, heartbeat_deadline=0.05):
    if type(units) not in (tuple, list) or not units or len(set(units)) != len(units):
        raise ValueError("invalid units")
    if type(traffic) not in (tuple, list):
        raise ValueError("invalid traffic")
    scheduler = CanScheduler(nominal_bps=nominal_bps, data_bps=data_bps,
                             max_queue=max_queue, heartbeat_deadline=heartbeat_deadline)
    for unit in units:
        scheduler.register(unit)
    accepted = []
    rejected = []
    for row in traffic:
        if type(row) is not dict or set(row) != {"kind", "unit", "size", "at", "deadline"}:
            raise ValueError("invalid traffic row")
        if row["kind"] not in PRIORITY or row["unit"] not in units:
            raise ValueError("invalid traffic kind or unit")
        ok = scheduler.enqueue(row["kind"], unit=row["unit"], size=row["size"],
                               now=row["at"], deadline=row["deadline"])
        (accepted if ok else rejected).append(row)
    sent = scheduler.dispatch(until=until)
    by_kind = {}
    for kind in PRIORITY:
        rows = [r for r in sent if r["kind"] == kind]
        by_kind[kind] = {
            "sent": len(rows),
            "max_frame_duration": max((r["finish"] - r["start"] for r in rows), default=0.0),
            "missed_deadlines": sum(r["late"] for r in rows),
        }
    return {"sent": sent, "accepted_count": len(accepted),
            "rejected_count": len(rejected), "queued": len(scheduler.queue),
            "invalidated": scheduler.invalidated, "by_kind": by_kind,
            "model_only": True, "hardware_timing_verified": False,
            "physical_safety_verified": False}
