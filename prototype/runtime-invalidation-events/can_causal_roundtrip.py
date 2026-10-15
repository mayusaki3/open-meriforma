"""Suite 38: synthetic causal heartbeat -> ACK round trips on one bus.

Application-level simplified model. Never issues actuator commands or grants authority.
"""
import heapq
from can_scheduler import CanScheduler, PRIORITY, finite


def simulate_roundtrips(*, units=2, cycles=5, period_ms=20,
                        heartbeat_bytes=64, ack_bytes=48, ack_delay_ms=1,
                        deadline_ms=15, diagnostic_frames=0,
                        nominal_bps=500_000, data_bps=2_000_000,
                        drop_heartbeat=(), drop_ack=(), retry_once=True):
    if type(units) is not int or not 1 <= units <= 62:
        raise ValueError("invalid units")
    if type(cycles) is not int or not 1 <= cycles <= 1000:
        raise ValueError("invalid cycles")
    if type(diagnostic_frames) is not int or not 0 <= diagnostic_frames <= 100:
        raise ValueError("invalid diagnostic_frames")
    for size in (heartbeat_bytes, ack_bytes):
        if type(size) is not int or not 0 <= size <= 64:
            raise ValueError("invalid frame size")
    period = finite(period_ms, minimum=0.000001) / 1000
    delay = finite(ack_delay_ms, minimum=0) / 1000
    deadline = finite(deadline_ms, minimum=0.000001) / 1000
    if type(retry_once) is not bool:
        raise ValueError("invalid retry_once")
    valid_ids = {(cycle, unit) for cycle in range(cycles) for unit in range(units)}
    for drops in (drop_heartbeat, drop_ack):
        if not isinstance(drops, (tuple, list, set, frozenset)) or not set(drops) <= valid_ids:
            raise ValueError("invalid drop ids")
    missing_heartbeat, missing_ack = set(drop_heartbeat), set(drop_ack)
    bus = CanScheduler(nominal_bps=nominal_bps, data_bps=data_bps)
    queue = []
    serial = 0
    def add(at, kind, key, attempt=0):
        nonlocal serial
        heapq.heappush(queue, (at, serial, kind, key, attempt))
        serial += 1
    state = {}
    for cycle in range(cycles):
        for unit in range(units):
            key = (cycle, unit)
            start = cycle * period
            state[key] = {"release": start, "deadline": start + deadline,
                          "completed": False, "heartbeat_deliveries": 0,
                          "ack_generated": 0, "ack_delivered": 0,
                          "retries": 0}
            add(start, "heartbeat", key)
        for i in range(diagnostic_frames):
            add(cycle * period, "diagnostic", (cycle, i))
    clock = 0.0
    busy = 0.0
    events = []
    while queue:
        at, _, kind, key, attempt = heapq.heappop(queue)
        clock = max(clock, at)
        # Drain arrivals before choosing next frame: priority ordering for ready traffic.
        ready = [(kind, key, attempt, at)]
        while queue and queue[0][0] <= clock + 1e-12:
            t, _, k, ident, a = heapq.heappop(queue)
            ready.append((k, ident, a, t))
        ready.sort(key=lambda x: (PRIORITY["diagnostic" if x[0] == "diagnostic" else "heartbeat"], x[3]))
        kind, key, attempt, at = ready.pop(0)
        for k, ident, a, t in ready:
            add(t, k, ident, a)
        if kind != "diagnostic" and (state[key]["completed"] or clock > state[key]["deadline"]):
            continue
        size = heartbeat_bytes if kind == "heartbeat" else ack_bytes if kind == "ack" else 64
        clock += bus.duration(size)
        busy += bus.duration(size)
        if kind == "diagnostic":
            events.append(("diagnostic", key, clock))
            continue
        st = state[key]
        if clock > st["deadline"] + 1e-12:
            events.append(("late", kind, key, clock))
            continue
        if kind == "heartbeat":
            if key in missing_heartbeat and attempt == 0:
                events.append(("heartbeat_dropped", key, clock))
                if retry_once:
                    st["retries"] += 1
                    add(clock, "heartbeat", key, 1)
                continue
            st["heartbeat_deliveries"] += 1
            events.append(("heartbeat_received", key, clock))
            st["ack_generated"] += 1
            add(clock + delay, "ack", key, attempt)
        else:
            if key in missing_ack and attempt == 0:
                events.append(("ack_dropped", key, clock))
                if retry_once:
                    st["retries"] += 1
                    add(clock, "heartbeat", key, 1)
                continue
            st["ack_delivered"] += 1
            st["completed"] = True
            st["roundtrip_ms"] = (clock - st["release"]) * 1000
            events.append(("ack_received", key, clock))
    completed = sum(st["completed"] for st in state.values())
    return {"total": len(state), "completed": completed,
            "timed_out": len(state) - completed,
            "retries": sum(st["retries"] for st in state.values()),
            "max_roundtrip_ms": max((st.get("roundtrip_ms", 0) for st in state.values()), default=0),
            "utilization": busy / (cycles * period),
            "events": events, "states": state,
            "model_only": True, "ack_causally_modeled": True,
            "motor_command_issued": False, "physical_safety_verified": False,
            "automatic_resume": False}
