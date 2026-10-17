"""Synthetic CAN control scheduler with authority checked at queue and dispatch.

No CAN driver, bus arbitration or actuator output. Scheduler dispatch is
simulated completion, not an atomic hardware transmit authorization.
"""
from can_scheduler import CanScheduler


class AuthorityCanScheduler:
    def __init__(self, link):
        self.link = link
        self.scheduler = CanScheduler(heartbeat_deadline=link.heartbeat_timeout)
        for unit in link.units:
            self.scheduler.register(unit)
        self.queue_generation = link.generation
        self.revoked = False

    def _revoke(self):
        self.revoked = True
        self.scheduler.queue.clear()
        self.scheduler.authorized = False

    def _allowed(self, now):
        if (self.revoked or self.link.generation != self.queue_generation
                or not self.link.eligible(now=now)):
            self._revoke()
            return False
        return True

    def stage(self, unit, *, size, now, deadline):
        if unit not in self.link.units:
            raise ValueError("unknown unit")
        if not self._allowed(now):
            return False
        return self.scheduler.enqueue(
            "control", unit=unit, size=size, now=now, deadline=deadline
        )

    def dispatch(self, *, until):
        # Check before calling CanScheduler.dispatch, since that scheduler
        # checks heartbeat expiry after its dispatch loop.
        if not self._allowed(until):
            return []
        events = self.scheduler.dispatch(until=until)
        if not self._allowed(until) or any(e["late"] for e in events):
            self._revoke()
            return []
        return events
