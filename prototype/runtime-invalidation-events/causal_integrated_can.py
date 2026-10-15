"""Suite 39: causal ACK generation from integrated protocol receive events.

Uses existing IntegratedCanLink and SharedCanBus; no hardware or motor control.
"""
from integrated_can_link import IntegratedCanLink
from shared_can_bus import SharedCanBus


class CausalIntegratedCan:
    def __init__(self, units=("left", "right"), *, heartbeat_timeout=0.5,
                 max_queue=128, ack_delay=0.001, ack_window=0.05):
        if ack_delay < 0 or ack_window <= 0:
            raise ValueError("invalid ACK timing")
        self.link = IntegratedCanLink(units, heartbeat_timeout=heartbeat_timeout,
                                      max_queue=max_queue)
        self.bus = None
        self.ack_delay = ack_delay
        self.ack_window = ack_window
        self.ack_scheduled = set()

    def start(self, *, boot_id="M1", challenge="C1", now=0):
        self.link.start_main(boot_id=boot_id, challenge=challenge, now=now)
        self.bus = SharedCanBus(self.link, max_queue=self.link.max_queue)
        self.ack_scheduled.clear()
        for unit in self.link.units:
            if not self.link.establish(unit, forma_boot=unit + "-boot",
                                       main_boot=boot_id, challenge=challenge,
                                       session=unit + "-session"):
                raise ValueError("failed to establish session")

    def submit(self, unit, sequence, *, now, deadline):
        if self.bus is None:
            raise ValueError("start first")
        boot, challenge = self.link.generation.split(":", 1)
        message = dict(kind="heartbeat", unit=unit, main_boot=boot,
                       challenge=challenge, forma_boot=unit + "-boot",
                       session=unit + "-session", sequence=sequence, ready=True)
        if not self.link.submit(message, now=now, deadline=deadline):
            return False
        return self.bus.import_forward()

    def advance(self, *, until, drop=None):
        """Dispatch then schedule ACK only for completed application transfers.

        ACKs are queued after a receive event, never before; dispatch again
        to process any ACKs whose release and airtime fit in the interval.
        """
        if self.bus is None:
            raise ValueError("start first")
        events = self.bus.dispatch(until=until, drop=drop)
        if self.bus.failed:
            return events
        for event in events:
            if event[0] != "forward" or event[2] is not True:
                continue
            _, source, transfer_id, _ = event[1]
            key = (self.link.generation, source, transfer_id)
            if key in self.ack_scheduled:
                continue
            received_at = event[-1]
            enqueue_at = max(until, received_at + self.ack_delay)
            ack_deadline = received_at + self.ack_window
            if enqueue_at > ack_deadline:
                # An expired ACK cannot be queued. Fail closed rather than
                # leaking a ValueError or silently extending the deadline.
                self.bus._fail()
                break
            self.ack_scheduled.add(key)
            if not self.bus.enqueue_ack(source=source, transfer_id=transfer_id,
                                        now=enqueue_at, deadline=ack_deadline):
                if not self.bus.failed:
                    self.bus._fail()
                break
        return events

    def deliver_acks(self, *, until, drop=None):
        if self.bus is None:
            raise ValueError("start first")
        return self.bus.dispatch(until=until, drop=drop)

    def retry(self, *, now, deadline):
        ids = self.link.retry_due(now=now, deadline=deadline)
        for tid in ids:
            owner = self.link.transfer_owners.get(tid)
            self.ack_scheduled.discard((self.link.generation, owner, tid))
        if ids and not self.bus.import_forward():
            return []
        return ids

    def status(self):
        return dict(self.bus.status(), pending=len(self.link.fault.pending),
                    ack_scheduled=len(self.ack_scheduled),
                    automatic_resume=False, motor_command_issued=False,
                    physical_safety_verified=False)
