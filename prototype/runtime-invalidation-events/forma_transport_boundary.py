"""66-F synthetic receiver transport session boundary, not network security.

Serialized requests only. Link loss invalidates per-Forma authority and latches
its 66-D stop. Reconnection alone cannot clear the latch. No physical STOP.
"""
from forma_receiver_integration import FormaReceiverIntegration

class FormaTransportBoundary:
    def __init__(self, receiver):
        if not isinstance(receiver, FormaReceiverIntegration):
            raise ValueError("invalid receiver")
        self.receiver = receiver
        self.links = {}
        self.seen = set()

    def connect(self, forma_id, generation):
        unit = self.receiver._unit(forma_id)
        if (unit is None or type(generation) is not str or not generation
                or forma_id in self.links and self.links[forma_id]["connected"]):
            return False
        if generation != unit.state.generation:
            return False
        self.links[forma_id] = {"generation": generation, "connected": True}
        return True

    def disconnect(self, forma_id):
        link = self.links.get(forma_id)
        if link is None or not link["connected"]:
            return False
        link["connected"] = False
        self.receiver.invalidate(forma_id)
        return True

    def receive(self, *, forma_id, generation, request_id, action,
                operation_id=None, scope=None):
        if (type(forma_id) is not str or type(generation) is not str
                or type(request_id) is not str or not request_id
                or type(action) is not str):
            return False
        link = self.links.get(forma_id)
        if (link is None or not link["connected"]
                or generation != link["generation"]
                or generation != self.receiver._unit(forma_id).state.generation):
            return False
        key = (forma_id, generation, request_id)
        if key in self.seen:
            return False
        # Reserve IDs even when the operation is rejected: never retry by replay.
        self.seen.add(key)
        if action == "authorize":
            return self.receiver.request_authorize(forma_id, operation_id, scope)
        if action == "start":
            return self.receiver.request_start(forma_id, operation_id, scope)
        if action == "finish":
            return self.receiver.request_finish(forma_id, operation_id)
        return False
