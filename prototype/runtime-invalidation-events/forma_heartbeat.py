"""Synthetic multi-Forma heartbeat and authorization monitor; no motor I/O.

Caller supplies monotonic time. Boot epochs are trusted synthetic inputs.
"""
import math


def _time(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid monotonic time")
    return float(value)


class FormaLinkMonitor:
    def __init__(self, required_units, *, timeout):
        units = tuple(required_units)
        if not units or len(set(units)) != len(units) or any(not isinstance(x, str) or not x for x in units):
            raise ValueError("invalid required units")
        if _time(timeout) <= 0:
            raise ValueError("invalid timeout")
        self.timeout = float(timeout)
        self.units = {name: {"epoch": None, "sequence": -1, "last_seen": None,
                             "ready": False} for name in units}
        self.main_epoch = 1
        self.authorized = False
        self.last_now = 0.0

    def _clock(self, now):
        now = _time(now)
        if now < self.last_now:
            self.authorized = False
            raise ValueError("clock moved backwards")
        self.last_now = now
        return now

    def _fresh(self, item, now):
        return (item["last_seen"] is not None and item["ready"]
                and now - item["last_seen"] <= self.timeout)

    def heartbeat(self, unit, *, epoch, sequence, ready, now):
        now = self._clock(now)
        if unit not in self.units or type(epoch) is not int or epoch < 1 or type(sequence) is not int or sequence < 0 or type(ready) is not bool:
            raise ValueError("invalid heartbeat")
        item = self.units[unit]
        if item["last_seen"] is not None and now - item["last_seen"] > self.timeout:
            self.authorized = False
            item["ready"] = False
        if item["epoch"] is not None and epoch < item["epoch"]:
            return False
        if epoch == item["epoch"] and sequence <= item["sequence"]:
            return False
        if epoch != item["epoch"]:
            self.authorized = False
            item["ready"] = False
            item["sequence"] = -1
        item.update(epoch=epoch, sequence=sequence, last_seen=now, ready=ready)
        if not ready:
            self.authorized = False
        return True

    def eligible(self, *, now):
        now = self._clock(now)
        if not all(self._fresh(item, now) for item in self.units.values()):
            self.authorized = False
        return self.authorized and all(self._fresh(item, now) for item in self.units.values())

    def authorize(self, *, explicit, now):
        now = self._clock(now)
        if type(explicit) is not bool:
            raise ValueError("explicit must be bool")
        self.eligible(now=now)
        if not explicit or not all(self._fresh(item, now) for item in self.units.values()):
            self.authorized = False
            return False
        self.authorized = True
        return True

    def restart_main(self):
        self.main_epoch += 1
        self.authorized = False
        for item in self.units.values():
            item["ready"] = False
            item["last_seen"] = None
            item["sequence"] = -1
            item["epoch"] = None

    def status(self, *, now):
        eligible = self.eligible(now=now)
        return {"coordinated_eligible": eligible,
                "required_units": tuple(self.units),
                "main_epoch": self.main_epoch,
                "automatic_resume": False, "motor_command_issued": False,
                "current_physical_safety_verified": False}
