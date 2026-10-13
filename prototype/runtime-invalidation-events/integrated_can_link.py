"""Synthetic Main-to-Forma pipeline. No CAN controller or motor output.

Scheduler dispatch completion is used as a simulated arrival time. Complete
envelopes alone reach the session monitor; scheduler and transport faults both
revoke authorization. Recovery requires a new challenge and fresh observations.
"""
from can_scheduler import CanScheduler
from can_fault_supervisor import CanFaultSupervisor
from wire_envelope import encode


class IntegratedCanLink:
    def __init__(self, units, *, heartbeat_timeout=0.05, max_queue=128):
        self.units = tuple(units)
        if not self.units or len(set(self.units)) != len(self.units):
            raise ValueError("invalid required units")
        self.heartbeat_timeout = heartbeat_timeout
        self.max_queue = max_queue
        self.fault = CanFaultSupervisor(self.units, heartbeat_timeout=heartbeat_timeout)
        self.scheduler = self._scheduler()
        self.frames = {}
        self.events = []
        self.invalidated = False

    def _scheduler(self):
        result = CanScheduler(heartbeat_deadline=self.heartbeat_timeout,
                              max_queue=self.max_queue)
        for unit in self.units:
            result.register(unit)
        return result

    def start_main(self, *, boot_id, challenge, now):
        if self.fault.bus_off:
            raise ValueError("bus still off")
        self.fault._now(now)
        self.fault.start_main(boot_id=boot_id, challenge=challenge)
        self.scheduler = self._scheduler()
        self.scheduler._time(now)
        self.scheduler.reset_authority(now=now)
        self.frames.clear()
        self.invalidated = False

    def establish(self, unit, *, forma_boot, main_boot, challenge, session):
        return self.fault.establish(unit, forma_boot=forma_boot, main_boot=main_boot,
                                    challenge=challenge, session=session)

    def submit(self, message, *, now, kind="heartbeat", deadline=None):
        if self.fault.bus_off or self.fault.recovery_required or self.invalidated:
            return False
        if message["unit"] not in self.units:
            raise ValueError("unknown unit")
        if kind != "heartbeat" or message["kind"] != "heartbeat":
            raise ValueError("integration currently supports heartbeat only")
        transfer_id, frames = self.fault.queue(encode(message), now=now)
        for index, frame in enumerate(frames):
            if not self.scheduler.enqueue(kind, unit=message["unit"],
                                           size=len(frame), now=now, deadline=deadline):
                self.frames.clear()
                self.fault.pending.clear()
                self._invalidate()
                return False
            self.frames[(message["unit"], transfer_id, index)] = frame
        return True

    def _invalidate(self):
        self.invalidated = True
        self.fault.protocol.sessions.authorized = False
        self.fault.protocol.links.authorized = False
        self.scheduler.authorized = False

    def dispatch(self, *, until, drop=None):
        """drop is an optional set of (unit, transfer_id, fragment_index)."""
        if self.fault.bus_off or self.fault.recovery_required:
            return []
        dropped = drop if drop is not None else set()
        if type(dropped) is not set:
            raise ValueError("invalid drop set")
        output = []
        # One scheduling item corresponds to one submitted fragment; FIFO
        # within each priority and peer is recovered from the submission log.
        for record in self.scheduler.dispatch(until=until):
            unit = record["unit"]
            matching = next((key for key in self.frames if key[0] == unit), None)
            if matching is None:
                self._invalidate()
                raise ValueError("missing scheduled fragment")
            frame = self.frames.pop(matching)
            if matching in dropped:
                output.append(("dropped", matching))
                continue
            try:
                accepted = self.fault.receive(frame, source=unit, now=record["finish"])
            except ValueError:
                self._invalidate()
                raise
            output.append(("received", matching, accepted))
            if accepted is True:
                self.fault.acknowledge(matching[1])
        if self.scheduler.invalidated or not all(
                self.fault.protocol.links._fresh(item, until)
                for item in self.fault.protocol.links.units.values()
        ):
            self._invalidate()
        self.events.extend(output)
        return output

    def authorize(self, *, explicit, now):
        if self.invalidated or self.scheduler.invalidated:
            return False
        if not self.fault.authorize(explicit=explicit, now=now):
            return False
        if not self.scheduler.authorize(explicit=explicit, now=now):
            self._invalidate()
            return False
        return True

    def eligible(self, *, now):
        if self.invalidated or self.scheduler.invalidated:
            return False
        if not self.scheduler.check_timeout(now=now):
            self._invalidate()
            return False
        if not self.fault.eligible(now=now):
            self._invalidate()
            return False
        return self.scheduler.authorized

    def bus_off_event(self):
        self.fault.bus_off_event()
        self.frames.clear()
        self.scheduler.queue.clear()
        self._invalidate()

    def bus_recovered(self):
        self.fault.bus_recovered()

    def status(self, *, now):
        return {"eligible": self.eligible(now=now), "invalidated": self.invalidated,
                "bus_off": self.fault.bus_off,
                "automatic_resume": False, "motor_command_issued": False,
                "physical_safety_verified": False}
