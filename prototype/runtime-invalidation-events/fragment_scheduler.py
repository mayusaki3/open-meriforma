"""Synthetic fragment-aware priority queue; no physical CAN bus.

Every scheduled item carries immutable (generation, source, transfer ID, index).
Generation changes discard all pending fragments. No actuator control.
"""
import heapq
from can_scheduler import CanScheduler, PRIORITY
from canfd_fragments import parse


class FragmentScheduler:
    def __init__(self, *, max_queue=128, nominal_bps=500_000, data_bps=2_000_000):
        self.airtime = CanScheduler(max_queue=max_queue, nominal_bps=nominal_bps,
                                    data_bps=data_bps)
        self.max_queue = max_queue
        self.queue = []
        self.serial = 0
        self.generation = None
        self.now = 0.0
        self.available_at = 0.0
        self.invalidated = False
        self.dropped = 0

    def begin(self, generation):
        if type(generation) is not str or not generation or generation == self.generation:
            raise ValueError("new nonempty generation required")
        self.generation = generation
        self.queue.clear()
        self.invalidated = False
        self.available_at = self.now

    def enqueue(self, kind, source, frame, *, generation, now, deadline):
        self._time(now)
        if generation != self.generation or self.invalidated:
            return False
        if kind not in PRIORITY or type(source) is not str or not source:
            raise ValueError("invalid kind/source")
        tid, index, _, _, _ = parse(frame)
        self.airtime.duration(len(frame))
        if deadline is not None and (type(deadline) not in (int, float) or
                                     deadline < now):
            raise ValueError("invalid deadline")
        key = (generation, source, tid, index)
        if any(item[-2] == key for item in self.queue):
            raise ValueError("duplicate queued fragment")
        item = (PRIORITY[kind], self.serial, kind, source, frame, now, deadline, key, len(frame))
        self.serial += 1
        if len(self.queue) >= self.max_queue:
            worst = max(self.queue)
            if item[0] >= worst[0]:
                self.dropped += 1
                return False
            self.queue.remove(worst)
            heapq.heapify(self.queue)
            self.dropped += 1
            # Evicting any fragment invalidates this generation's transfer set.
            self.invalidated = True
            self.queue.clear()
            return False
        heapq.heappush(self.queue, item)
        return True

    def _time(self, now):
        from can_scheduler import finite
        now = finite(now)
        if now < self.now:
            raise ValueError("clock moved backwards")
        self.now = now
        return now

    def dispatch(self, *, until):
        until = self._time(until)
        if self.invalidated:
            return []
        output = []
        while self.queue:
            item = self.queue[0]
            _, _, kind, source, frame, queued, deadline, key, _ = item
            start = max(self.available_at, queued)
            finish = start + self.airtime.duration(len(frame))
            if finish > until:
                break
            heapq.heappop(self.queue)
            self.available_at = finish
            late = deadline is not None and finish > deadline
            if late:
                self.invalidated = True
                self.queue.clear()
            output.append({"key": key, "kind": kind, "source": source,
                           "frame": frame, "start": start, "finish": finish,
                           "late": late})
            if late:
                break
        return output

    def expire(self, *, now):
        self._time(now)
        if any(item[6] is not None and now > item[6] for item in self.queue):
            self.invalidated = True
            self.queue.clear()
        return not self.invalidated

    def status(self):
        return {"generation": self.generation, "queued": len(self.queue),
                "invalidated": self.invalidated, "dropped": self.dropped,
                "automatic_resume": False, "motor_command_issued": False,
                "physical_safety_verified": False}
