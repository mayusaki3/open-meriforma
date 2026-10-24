"""66-H deterministic packet-delay/loss/reorder simulation.

Arrival-time clock, no real transport, authenticated packets or physical stop.
A sequence is monotonic per Forma/generation; delivery after timeout is denied.
"""
import math
from forma_timed_recovery import FormaTimedRecovery

class FormaPacketSimulator:
    def __init__(self, timed):
        if not isinstance(timed, FormaTimedRecovery):
            raise ValueError("invalid timed boundary")
        self.timed = timed
        self.queue = []
        self.last_sequence = {}
        self.results = []

    def send(self, *, arrival, forma_id, generation, sequence, kind,
             request_id=None, action=None, operation_id=None, scope=None,
             lost=False):
        if (type(arrival) not in (int, float) or not math.isfinite(arrival)
                or arrival < self.timed.now
                or type(forma_id) is not str or not forma_id
                or type(generation) is not str or not generation
                or type(sequence) is not int or sequence < 0
                or kind not in ("heartbeat", "request")
                or type(lost) is not bool):
            return False
        if not lost:
            self.queue.append((arrival, len(self.queue), dict(
                forma_id=forma_id, generation=generation, sequence=sequence,
                kind=kind, request_id=request_id, action=action,
                operation_id=operation_id, scope=scope)))
        return True

    def advance(self, now):
        if (type(now) not in (int, float) or not math.isfinite(now)
                or now < self.timed.now):
            return False
        pending = sorted((x for x in self.queue if x[0] <= now),
                         key=lambda x: (x[0], x[1]))
        self.queue = [x for x in self.queue if x[0] > now]
        for arrival, _, packet in pending:
            # Timeouts are processed before packets at the same timestamp.
            self.timed.tick(arrival)
            self.results.append((packet["sequence"], self._deliver(packet)))
        self.timed.tick(now)
        return True

    def _deliver(self, packet):
        fid, gen, seq = (packet["forma_id"], packet["generation"],
                         packet["sequence"])
        link = self.timed.boundary.links.get(fid)
        if (link is None or not link["connected"]
                or link["generation"] != gen
                or self.timed.boundary.receiver._unit(fid).state.generation != gen):
            return False
        key = (fid, gen)
        if seq <= self.last_sequence.get(key, -1):
            return False
        # Consume sequence even if Forma rejects an operation.
        self.last_sequence[key] = seq
        if packet["kind"] == "heartbeat":
            return self.timed.heartbeat(fid, gen)
        return self.timed.receive(
            forma_id=fid, generation=gen, request_id=packet["request_id"],
            action=packet["action"], operation_id=packet["operation_id"],
            scope=packet["scope"])
