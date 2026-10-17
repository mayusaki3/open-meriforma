"""Suite 45 adapter: gated control frames on the existing synthetic SharedCanBus.

Control frames use background direction to avoid interpreting payloads as
heartbeat protocol messages. No actual CAN control wire format or motor output.
"""
import heapq
from canfd_fragments import fragment
from shared_can_bus import SharedCanBus


class AuthoritySharedBus(SharedCanBus):
    def __init__(self, link, *, max_queue=128):
        super().__init__(link, max_queue=max_queue)
        self.control_generation = link.generation
        self.control_revoked = False
        self.next_control_tid = 0

    def _drop_control(self):
        self.control_revoked = True
        self.queue = [item for item in self.queue if item[2] != "background"
                      or item[0] != 2]
        heapq.heapify(self.queue)

    def enqueue_control(self, unit, payload, *, now, deadline):
        if unit not in self.link.units:
            raise ValueError("unknown unit")
        if (self.control_revoked or self.control_generation != self.link.generation
                or not self.link.eligible(now=now)):
            self._drop_control()
            return False
        if self.next_control_tid > 65535:
            self._drop_control()
            return False
        tid = self.next_control_tid
        self.next_control_tid += 1
        frames = fragment(payload, transfer_id=tid)
        for frame in frames:
            if not self.enqueue(direction="background", source=unit, frame=frame,
                                kind="control", now=now, deadline=deadline):
                self._drop_control()
                return False
        return True

    def dispatch(self, *, until, drop=None):
        # Fail closed for queued control frames before the shared dispatch.
        # This is a simulated pre-dispatch check, not an atomic hardware gate.
        if any(item[2] == "background" and item[0] == 2 for item in self.queue):
            if (self.control_revoked or self.control_generation != self.link.generation
                    or not self.link.eligible(now=until)):
                self._drop_control()
        return super().dispatch(until=until, drop=drop)
