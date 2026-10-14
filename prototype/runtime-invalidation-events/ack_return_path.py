"""Synthetic Forma-to-Main ACK return path, not a physical CAN driver.

ACK frames are fragmented, priority scheduled, and reassembled before delivery
to IntegratedCanLink.receive_ack. No authenticated peer identity is supplied.
"""
from canfd_fragments import Reassembler, fragment
from fragment_scheduler import FragmentScheduler
from ack_wire import decode_ack


class AckReturnPath:
    def __init__(self, link, *, max_queue=128, timeout=0.2):
        self.link = link
        self.scheduler = FragmentScheduler(max_queue=max_queue)
        self.timeout = timeout
        self.reassembly = Reassembler(timeout=timeout)
        self.generation = None
        self.next_transfer = 0
        self.sent = {}
        self.failed = False

    def begin(self):
        if self.link.generation is None or self.link.invalidated:
            raise ValueError("Main generation not ready")
        if self.generation == self.link.generation:
            raise ValueError("generation unchanged")
        self.generation = self.link.generation
        self.scheduler.begin(self.generation)
        self.reassembly = Reassembler(timeout=self.timeout)
        self.sent.clear()
        self.next_transfer = 0
        self.failed = False

    def queue_ack(self, *, unit, transfer_id, now, deadline):
        if self.failed or self.link.invalidated or self.link.generation != self.generation:
            return False
        if unit not in self.link.units:
            raise ValueError("unknown Forma")
        # Only a completed transfer may cause the simulated Forma to emit ACK.
        if (self.generation, unit, transfer_id) not in self.link.completed_transfers:
            return False
        data = self.link.make_ack(transfer_id, source=unit)
        tid = self.next_transfer
        self.next_transfer += 1
        if tid > 65535:
            self.failed = True
            return False
        frames = fragment(data, transfer_id=tid)
        for frame in frames:
            if not self.scheduler.enqueue("heartbeat", unit, frame,
                                          generation=self.generation,
                                          now=now, deadline=deadline):
                self.failed = True
                self.scheduler.queue.clear()
                return False
        self.sent[(unit, tid)] = transfer_id
        return True

    def dispatch(self, *, until, drop=None):
        dropped = set() if drop is None else drop
        if type(dropped) is not set:
            raise ValueError("invalid drop set")
        if self.failed or self.link.invalidated or self.link.generation != self.generation:
            return []
        output = []
        for record in self.scheduler.dispatch(until=until):
            generation, source, tid, index = record["key"]
            key = (source, tid, index)
            if record["late"] or generation != self.generation:
                self.failed = True
                self.reassembly.active.clear()
                break
            if key in dropped:
                output.append(("dropped", key))
                continue
            data = self.reassembly.accept(record["frame"], source=source,
                                          now=record["finish"])
            if data is None:
                output.append(("partial", key))
                continue
            ack = decode_ack(data)
            if ack["transfer_id"] != self.sent.get((source, tid)):
                self.failed = True
                self.reassembly.active.clear()
                break
            accepted = self.link.receive_ack(data, source=source)
            output.append(("ack", key, accepted))
        if self.scheduler.invalidated:
            self.failed = True
            self.reassembly.active.clear()
        return output

    def status(self):
        return {"failed": self.failed, "queued": len(self.scheduler.queue),
                "incomplete": len(self.reassembly.active),
                "automatic_resume": False, "motor_command_issued": False,
                "physical_safety_verified": False}
