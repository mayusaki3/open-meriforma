"""66-G synthetic timeout and explicit replacement-based recovery.

Logical clock only. No wall-clock timing, physical safety reset or firmware.
A stopped instance is never unlatched; recovery uses a fresh validated fixture.
"""
import math
from forma_transport_boundary import FormaTransportBoundary

class FormaTimedRecovery:
    def __init__(self, boundary, *, timeout):
        if (not isinstance(boundary, FormaTransportBoundary)
                or type(timeout) not in (int, float)
                or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError("invalid timeout boundary")
        self.boundary = boundary
        self.timeout = timeout
        self.now = 0
        self.last_seen = {}

    def connect(self, forma_id, generation):
        if not self.boundary.connect(forma_id, generation):
            return False
        self.last_seen[forma_id] = self.now
        return True

    def tick(self, now):
        if (type(now) not in (int, float) or not math.isfinite(now)
                or now < self.now):
            return False
        self.now = now
        for fid, link in list(self.boundary.links.items()):
            if (link["connected"] and fid in self.last_seen
                    and self.now - self.last_seen[fid] >= self.timeout):
                self.boundary.disconnect(fid)
        return True

    def heartbeat(self, forma_id, generation):
        link = self.boundary.links.get(forma_id)
        if (link is None or not link["connected"]
                or generation != link["generation"]
                or self.boundary.receiver._unit(forma_id).state.generation != generation
                or self.now - self.last_seen.get(forma_id, -math.inf) >= self.timeout):
            return False
        self.last_seen[forma_id] = self.now
        return True

    def receive(self, **request):
        fid = request.get("forma_id")
        link = self.boundary.links.get(fid) if type(fid) is str else None
        if (link is None or not link["connected"]
                or self.now - self.last_seen.get(fid, -math.inf) >= self.timeout):
            return False
        accepted = self.boundary.receive(**request)
        # Only valid transport/session requests count as activity, not denied operations.
        if accepted:
            self.last_seen[fid] = self.now
        return accepted

    def recover(self, forma_id, new_unit, generation, observed):
        old = self.boundary.receiver._unit(forma_id)
        link = self.boundary.links.get(forma_id)
        if (old is None or link is None or link["connected"]
                or not old.halted or old.active
                or new_unit is old or new_unit is None
                or new_unit.state.forma_id != forma_id
                or type(generation) is not str or not generation
                or generation == old.state.generation
                or new_unit.state.generation != generation
                or new_unit.halted or new_unit.active
                or new_unit.guard.operations.grants
                or new_unit.state.mode != "normal"
                or new_unit.state.clearance is not None
                or new_unit.state.faulted):
            return False
        # Validate the fresh unit before making it visible to the receiver.
        if not new_unit.state.enter_maintenance():
            return False
        if not new_unit.approve_clearance(observed):
            return False
        self.boundary.receiver.units[forma_id] = new_unit
        self.boundary.links[forma_id] = {"generation": generation, "connected": True}
        self.last_seen[forma_id] = self.now
        return True
