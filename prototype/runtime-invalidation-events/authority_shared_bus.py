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

    def _before_control_gate(self, *, until):
        """Test seam after protocol dispatch, before control authorization."""
        pass

    def dispatch(self, *, until, drop=None):
        # Process earlier-priority protocol traffic before checking authority
        # at the control transmit boundary. eligible(now=until) advances the
        # supervisor clock, so calling it before receiving queued heartbeats
        # would make their earlier arrival timestamps run backwards.
        controls = [item for item in self.queue
                    if item[2] == "background" and item[0] == 2]
        if not controls:
            return super().dispatch(until=until, drop=drop)
        self.queue = [item for item in self.queue
                      if not (item[2] == "background" and item[0] == 2)]
        heapq.heapify(self.queue)
        protocol_events = super().dispatch(until=until, drop=drop)
        if not self.failed:
            self._before_control_gate(until=until)
        if (self.failed or self.control_revoked
                or self.control_generation != self.link.generation
                or not self.link.eligible(now=until)):
            self.control_revoked = True
            return protocol_events
        for item in controls:
            heapq.heappush(self.queue, item)
        return protocol_events + super().dispatch(until=until, drop=drop)
