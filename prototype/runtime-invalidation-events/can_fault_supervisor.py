"""Synthetic transport fault supervisor; no CAN controller or motor I/O.

Transport faults invalidate sessions and discard incomplete transfers.
Recovery requires a new Main challenge, fresh peer sessions and authorization.
"""
import math
from canfd_fragments import Reassembler, fragment
from wire_envelope import decode
from protocol_boundary import ProtocolBoundary


def clock(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time")
    return float(value)


class CanFaultSupervisor:
    def __init__(self, units, *, heartbeat_timeout=0.5, fragment_timeout=0.2,
                 retry_interval=0.1, max_retries=2):
        if clock(retry_interval) <= 0 or type(max_retries) is not int or max_retries < 0:
            raise ValueError("invalid retry policy")
        self.protocol = ProtocolBoundary(units, timeout=heartbeat_timeout)
        self.fragment_timeout = fragment_timeout
        self.reassembly = Reassembler(timeout=fragment_timeout)
        self.retry_interval = float(retry_interval)
        self.max_retries = max_retries
        self.last_now = 0.0
        self.bus_off = False
        self.recovery_required = False
        self.pending = {}
        self.next_transfer = 0
        self.used_transfers = set()

    def _now(self, now):
        now = clock(now)
        if now < self.last_now:
            raise ValueError("clock moved backwards")
        self.last_now = now
        return now

    def start_main(self, *, boot_id, challenge):
        self.protocol.start_main(boot_id=boot_id, challenge=challenge)
        self.reassembly = Reassembler(timeout=self.fragment_timeout)
        self.pending.clear()
        self.used_transfers.clear()
        self.next_transfer = 0
        self.recovery_required = False

    def establish(self, unit, *, forma_boot, main_boot, challenge, session):
        if self.bus_off or self.recovery_required:
            return False
        return self.protocol.establish(unit, forma_boot=forma_boot, main_boot=main_boot,
                                       challenge=challenge, session=session)

    def bus_off_event(self):
        self.bus_off = True
        self.recovery_required = True
        self.protocol.sessions.authorized = False
        self.protocol.links.authorized = False
        self.reassembly.active.clear()
        self.pending.clear()

    def bus_recovered(self):
        if not self.bus_off:
            raise ValueError("bus was not off")
        self.bus_off = False
        # Recovery remains blocked until a fresh start_main call.

    def receive(self, frame, *, source, now):
        now = self._now(now)
        if self.bus_off or self.recovery_required:
            return False
        result = self.reassembly.accept(frame, source=source, now=now)
        if result is None:
            return None
        decoded = decode(result)
        if decoded["unit"] != source:
            raise ValueError("source/unit mismatch")
        return self.protocol.receive(decoded, now=now)

    def authorize(self, *, explicit, now):
        now = self._now(now)
        if self.bus_off or self.recovery_required:
            return False
        return self.protocol.authorize(explicit=explicit, now=now)

    def eligible(self, *, now):
        now = self._now(now)
        if self.bus_off or self.recovery_required:
            return False
        return self.protocol.eligible(now=now)

    def queue(self, payload, *, now):
        now = self._now(now)
        if self.bus_off or self.recovery_required:
            raise ValueError("transport unavailable")
        if len(self.used_transfers) == 65536:
            raise ValueError("transfer ID space exhausted; start a new session")
        while self.next_transfer in self.used_transfers:
            self.next_transfer = (self.next_transfer + 1) % 65536
        tid = self.next_transfer
        self.used_transfers.add(tid)
        self.next_transfer = (tid + 1) % 65536
        frames = fragment(payload, transfer_id=tid)
        self.pending[tid] = {"frames": frames, "last": now, "retries": 0}
        return tid, frames

    def retry_due(self, *, now):
        now = self._now(now)
        if self.bus_off or self.recovery_required:
            return []
        due = []
        for tid, entry in list(self.pending.items()):
            if now - entry["last"] < self.retry_interval:
                continue
            if entry["retries"] >= self.max_retries:
                del self.pending[tid]
                continue
            entry["retries"] += 1
            entry["last"] = now
            due.append((tid, entry["frames"]))
        return due

    def acknowledge(self, transfer_id):
        if type(transfer_id) is not int:
            raise ValueError("invalid transfer ID")
        return self.pending.pop(transfer_id, None) is not None

    def status(self, *, now):
        return {"eligible": self.eligible(now=now), "bus_off": self.bus_off,
                "recovery_required": self.recovery_required,
                "automatic_resume": False, "motor_command_issued": False,
                "physical_safety_verified": False}
