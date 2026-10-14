"""Synthetic half-duplex shared CAN-FD bus for both directions.

Uses a single airtime clock and priority queue. Not physical arbitration,
CAN controller behavior, authentication, or motor safety verification.
"""
import heapq
from can_scheduler import CanScheduler, PRIORITY, finite
from canfd_fragments import parse, Reassembler
from ack_wire import decode_ack


class SharedCanBus:
    def __init__(self, link, *, max_queue=128, ack_timeout=0.2):
        self.link = link
        self.generation = link.generation
        self.airtime = CanScheduler(max_queue=max_queue)
        self.max_queue = max_queue
        self.queue = []
        self.serial = 0
        self.now = 0.0
        self.available_at = 0.0
        self.failed = False
        self.acks = Reassembler(timeout=ack_timeout)
        self.next_ack_tid = 0
        self.history = []

    def enqueue(self, *, direction, source, frame, kind, now, deadline):
        now = finite(now)
        if now < self.now:
            raise ValueError("clock moved backwards")
        self.now = now
        if direction not in ("forward", "ack", "background") or kind not in PRIORITY:
            raise ValueError("invalid direction/priority")
        if type(source) is not str or not source or source not in self.link.units:
            raise ValueError("invalid peer")
        if self.failed or self.link.invalidated or self.link.generation != self.generation:
            return False
        tid, index, _, _, _ = parse(frame)
        if deadline is not None and finite(deadline) < now:
            raise ValueError("invalid deadline")
        if len(self.queue) >= self.max_queue:
            self._fail()
            return False
        heapq.heappush(self.queue, (PRIORITY[kind], self.serial, direction,
                                    source, frame, now, deadline, tid, index))
        self.serial += 1
        return True

    def enqueue_ack(self, *, source, transfer_id, now, deadline):
        from canfd_fragments import fragment
        if (self.generation, source, transfer_id) not in self.link.completed_transfers:
            return False
        if self.next_ack_tid > 65535:
            self._fail()
            return False
        ack_tid = self.next_ack_tid
        self.next_ack_tid += 1
        frames = fragment(self.link.make_ack(transfer_id, source=source),
                          transfer_id=ack_tid)
        for frame in frames:
            if not self.enqueue(direction="ack", source=source, frame=frame,
                                kind="heartbeat", now=now, deadline=deadline):
                return False
        return True

    def import_forward(self):
        """Move queued Main-to-Forma frames onto the one shared bus."""
        pending = list(self.link.fragments.queue)
        for item in sorted(pending, key=lambda x: x[1]):
            _, _, kind, source, frame, queued, deadline, key, _ = item
            if key[0] != self.generation:
                self._fail()
                return False
            if not self.enqueue(direction="forward", source=source, frame=frame,
                                kind=kind, now=max(self.now, queued),
                                deadline=deadline):
                return False
        self.link.fragments.queue.clear()
        return True

    def _fail(self):
        self.failed = True
        self.queue.clear()
        self.acks.active.clear()
        self.link._invalidate()

    def dispatch(self, *, until, drop=None):
        until = finite(until)
        if until < self.now:
            raise ValueError("clock moved backwards")
        self.now = until
        if self.failed or self.link.invalidated or self.link.generation != self.generation:
            self._fail()
            return []
        dropped = set() if drop is None else drop
        if type(dropped) is not set:
            raise ValueError("invalid drop set")
        output = []
        while self.queue:
            priority, serial, direction, source, frame, queued, deadline, tid, index = self.queue[0]
            start = max(self.available_at, queued)
            finish = start + self.airtime.duration(len(frame))
            if finish > until:
                break
            heapq.heappop(self.queue)
            self.available_at = finish
            key = (direction, source, tid, index)
            if deadline is not None and finish > deadline:
                self._fail()
                output.append(("late", key, finish))
                break
            if key in dropped:
                output.append(("dropped", key, finish))
                continue
            if direction == "background":
                output.append(("background", key, True, finish))
            elif direction == "forward":
                transfer_key = (self.generation, source, tid)
                if transfer_key in self.link.completed_transfers:
                    accepted = True
                else:
                    accepted = self.link.fault.receive(frame, source=source, now=finish)
                    if accepted is True:
                        self.link.completed_transfers.add(transfer_key)
                output.append(("forward", key, accepted, finish))
            else:
                data = self.acks.accept(frame, source=source, now=finish)
                accepted = None if data is None else self.link.receive_ack(data, source=source)
                output.append(("ack", key, accepted, finish))
        self.history.extend(output)
        if not self.failed and not all(
                self.link.fault.protocol.links._fresh(item, until)
                for item in self.link.fault.protocol.links.units.values()):
            self._fail()
        return output

    def bus_off(self):
        self.link.bus_off_event()
        self._fail()

    def status(self):
        return dict(failed=self.failed, queued=len(self.queue),
                    generation=self.generation, automatic_resume=False,
                    motor_command_issued=False, physical_safety_verified=False)
