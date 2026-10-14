"""Synthetic Main-to-Forma pipeline. No CAN controller or motor output.

Scheduler dispatch completion is used as a simulated arrival time. Complete
envelopes alone reach the session monitor; scheduler and transport faults both
revoke authorization. Recovery requires a new challenge and fresh observations.
"""
from can_scheduler import CanScheduler
from fragment_scheduler import FragmentScheduler
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
        self.fragments = FragmentScheduler(max_queue=max_queue)
        self.generation = None
        self.completed_transfers = set()
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
        self.generation = f'{boot_id}:{challenge}'
        self.fragments.begin(self.generation)
        self.completed_transfers.clear()
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
        for frame in frames:
            if not self.fragments.enqueue(kind, message["unit"], frame,
                                          generation=self.generation, now=now,
                                          deadline=deadline):
                self.fault.pending.clear()
                self._invalidate()
                return False
        return True

    def _invalidate(self):
        self.invalidated = True
        self.fault.protocol.sessions.authorized = False
        self.fault.protocol.links.authorized = False
        self.scheduler.authorized = False
        self.fragments.invalidated = True
        self.fragments.queue.clear()

    def dispatch(self, *, until, drop=None, ack_drop=None):
        """drop is an optional set of (unit, transfer_id, fragment_index)."""
        if self.fault.bus_off or self.fault.recovery_required:
            return []
        dropped = drop if drop is not None else set()
        if type(dropped) is not set:
            raise ValueError("invalid drop set")
        missing_acks = ack_drop if ack_drop is not None else set()
        if type(missing_acks) is not set:
            raise ValueError("invalid ACK-drop set")
        output = []
        for record in self.fragments.dispatch(until=until):
            generation, unit, transfer_id, index = record["key"]
            matching = (unit, transfer_id, index)
            if generation != self.generation or record["late"]:
                self._invalidate()
                break
            if matching in dropped:
                output.append(("dropped", matching))
                continue
            transfer_key = (generation, unit, transfer_id)
            if transfer_key in self.completed_transfers:
                # Duplicate application transfer: do not replay protocol effects.
                accepted = True
            else:
                try:
                    accepted = self.fault.receive(record["frame"], source=unit,
                                                  now=record["finish"])
                except ValueError:
                    self._invalidate()
                    raise
                if accepted is True:
                    self.completed_transfers.add(transfer_key)
            output.append(("received", matching, accepted))
            if accepted is True and transfer_id not in missing_acks:
                self.fault.acknowledge(transfer_id)
        if self.fragments.invalidated or not all(
                self.fault.protocol.links._fresh(item, until)
                for item in self.fault.protocol.links.units.values()
        ):
            self._invalidate()
        self.events.extend(output)
        return output

    def retry_due(self, *, now, deadline=None):
        """Requeue application-level unacknowledged transfers, never resume authority."""
        if self.invalidated or self.fault.bus_off or self.fault.recovery_required:
            return []
        due = self.fault.retry_due(now=now)
        submitted = []
        for tid, frames in due:
            # Transfer ownership is retained by the original logical message.
            # A transfer ID is unique within this generation.
            owner = next((key[1] for key in self.completed_transfers
                          if key[0] == self.generation and key[2] == tid), None)
            if owner is None:
                self._invalidate()
                return submitted
            for frame in frames:
                if not self.fragments.enqueue("heartbeat", owner, frame,
                                              generation=self.generation,
                                              now=now, deadline=deadline):
                    self._invalidate()
                    return submitted
            submitted.append(tid)
        return submitted

    def authorize(self, *, explicit, now):
        if self.invalidated or self.fragments.invalidated or self.scheduler.invalidated:
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
        # A healthy but not-yet-authorized fresh session is not a fault.
        # ProtocolBoundary.eligible() also returns False before the first
        # explicit authorization, so do not latch invalidation here.
        return self.fault.eligible(now=now) and self.scheduler.authorized

    def bus_off_event(self):
        self.fault.bus_off_event()
        self.fragments.queue.clear()
        self.fragments.invalidated = True
        self.scheduler.queue.clear()
        self._invalidate()

    def bus_recovered(self):
        self.fault.bus_recovered()

    def status(self, *, now):
        return {"eligible": self.eligible(now=now), "invalidated": self.invalidated,
                "bus_off": self.fault.bus_off,
                "automatic_resume": False, "motor_command_issued": False,
                "physical_safety_verified": False}
