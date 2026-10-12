"""Deterministic, synthetic CAN-FD scheduling model; not bus timing proof.

Frame airtime is a configurable conservative approximation, not CAN bit stuffing
or arbitration simulation. Safety/heartbeat frames outrank control/diagnostics.
"""
import heapq
import math

PRIORITY = {"safety": 0, "heartbeat": 1, "control": 2, "diagnostic": 3}


def finite(value, *, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise ValueError("invalid numeric parameter")
    return float(value)


class CanScheduler:
    def __init__(self, *, nominal_bps=500_000, data_bps=2_000_000,
                 max_queue=128, heartbeat_deadline=0.05):
        self.nominal_bps = finite(nominal_bps, minimum=1)
        self.data_bps = finite(data_bps, minimum=1)
        self.heartbeat_deadline = finite(heartbeat_deadline, minimum=0.000001)
        if type(max_queue) is not int or not 1 <= max_queue <= 10000:
            raise ValueError("invalid queue capacity")
        self.max_queue = max_queue
        self.queue = []
        self.counter = 0
        self.available_at = 0.0
        self.now = 0.0
        self.last_heartbeat = {}
        self.required = set()
        self.authorized = False
        self.invalidated = False
        self.history = []
        self.dropped = 0

    def register(self, unit, *, now=0):
        if type(unit) is not str or not unit or unit in self.required:
            raise ValueError("invalid or duplicate unit")
        self._time(now)
        self.required.add(unit)
        self.last_heartbeat[unit] = float(now)
        self.authorized = False

    def _time(self, now):
        now = finite(now)
        if now < self.now:
            raise ValueError("clock moved backwards")
        self.now = now
        return now

    def duration(self, payload_bytes):
        if type(payload_bytes) is not int or not 0 <= payload_bytes <= 64:
            raise ValueError("CAN-FD payload outside 0..64")
        # Provisional nominal-rate arbitration overhead and data-rate payload.
        return 80 / self.nominal_bps + (payload_bytes * 8 + 40) / self.data_bps

    def enqueue(self, kind, *, unit, size, now, deadline=None):
        now = self._time(now)
        if kind not in PRIORITY or type(unit) is not str or not unit:
            raise ValueError("invalid message")
        if kind == "heartbeat" and unit not in self.required:
            raise ValueError("unknown heartbeat unit")
        self.duration(size)
        if deadline is not None:
            deadline = finite(deadline)
            if deadline < now:
                raise ValueError("deadline before enqueue")
        item = (PRIORITY[kind], self.counter, kind, unit, size, now, deadline)
        self.counter += 1
        if len(self.queue) >= self.max_queue:
            worst = max(self.queue)
            if item[0] >= worst[0]:
                self.dropped += 1
                return False
            self.queue.remove(worst)
            heapq.heapify(self.queue)
            self.dropped += 1
        heapq.heappush(self.queue, item)
        return True

    def authorize(self, *, explicit, now):
        self._time(now)
        self.check_timeout(now=now)
        if type(explicit) is not bool:
            raise ValueError("explicit must be bool")
        if not explicit or self.invalidated or not self.required:
            return False
        if any(self.now - t >= self.heartbeat_deadline for t in self.last_heartbeat.values()):
            return False
        self.authorized = True
        return True

    def check_timeout(self, *, now):
        now = self._time(now)
        if any(now - t >= self.heartbeat_deadline for t in self.last_heartbeat.values()):
            self.invalidated = True
            self.authorized = False
        return not self.invalidated

    def reset_authority(self, *, now):
        self._time(now)
        self.authorized = False
        self.invalidated = False
        for unit in self.required:
            self.last_heartbeat[unit] = self.now

    def dispatch(self, *, until):
        until = self._time(until)
        sent = []
        while self.queue and self.available_at <= until:
            priority, index, kind, unit, size, queued, deadline = heapq.heappop(self.queue)
            start = max(self.available_at, queued)
            finish = start + self.duration(size)
            if finish > until:
                heapq.heappush(self.queue, (priority, index, kind, unit, size, queued, deadline))
                break
            self.available_at = finish
            expired = deadline is not None and finish > deadline
            record = {"kind": kind, "unit": unit, "start": start,
                      "finish": finish, "late": expired}
            self.history.append(record)
            sent.append(record)
            if kind == "heartbeat":
                if expired:
                    self.invalidated = True
                    self.authorized = False
                else:
                    self.last_heartbeat[unit] = finish
        self.check_timeout(now=until)
        return sent

    def status(self):
        return {"authorized": self.authorized and not self.invalidated,
                "invalidated": self.invalidated, "queued": len(self.queue),
                "dropped": self.dropped, "automatic_resume": False,
                "physical_safety_verified": False}
