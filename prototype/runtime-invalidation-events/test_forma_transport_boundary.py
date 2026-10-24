"""66-F synthetic transport-boundary regression."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy
from forma_concurrent_operations import FormaConcurrentOperations
from forma_receiver_integration import FormaReceiverIntegration
from forma_transport_boundary import FormaTransportBoundary

def make(fid):
    state = FormaMaintenanceState(fid, "g1")
    policy = FormaSafetyPolicy(actuators={"thumb": {"position": (0, 20)}},
                               clearance_conditions=("guard",))
    ops = FormaConcurrentOperations(state, policy, costs={"thumb": 1}, max_load=2)
    return ops

def req(boundary, fid, rid, action, op="op", gen="g1", scope=None):
    return boundary.receive(forma_id=fid, generation=gen, request_id=rid,
                            action=action, operation_id=op, scope=scope)

scope = {"actuator": "thumb", "control_mode": "position",
         "minimum": 0, "maximum": 10}
left, right = make("left"), make("right")
r = FormaReceiverIntegration({"left": left, "right": right})
b = FormaTransportBoundary(r)
assert not req(b, "left", "a", "authorize", scope=scope)
print("PASS 66-F-01 disconnected request rejected")
assert b.connect("left", "g1")
assert not b.connect("left", "g1")
print("PASS 66-F-02 explicit session and duplicate connect rejected")
assert r.enter_maintenance("left") and left.approve_clearance({"guard": True})
assert req(b, "left", "a", "authorize", scope=scope)
assert not req(b, "left", "a", "authorize", scope=scope)
print("PASS 66-F-03 request ID cannot replay")
assert req(b, "left", "b", "start", scope=scope)
assert not req(b, "left", "b", "start", scope=scope)
print("PASS 66-F-04 operation start cannot replay")
assert not req(b, "left", "c", "finish", gen="old")
assert "c" not in {key[2] for key in b.seen}
print("PASS 66-F-05 stale generation rejected before reservation")
assert b.disconnect("left")
assert left.halted and not left.active and not left.guard.operations.grants
print("PASS 66-F-06 link loss revokes active and pending authority")
assert not req(b, "left", "d", "authorize", scope=scope)
print("PASS 66-F-07 disconnected requests rejected")
assert b.connect("left", "g1")
assert not req(b, "left", "e", "authorize", scope=scope)
assert left.halted
print("PASS 66-F-08 reconnect cannot restore clearance or halt")
assert not req(b, "left", "a", "authorize", scope=scope)
print("PASS 66-F-09 old request ID remains consumed")
assert not b.connect("missing", "g1")
assert not req(b, "missing", "x", "start", scope=scope)
print("PASS 66-F-10 unknown Forma rejected")
assert b.connect("right", "g1")
assert r.enter_maintenance("right") and right.approve_clearance({"guard": True})
assert req(b, "right", "a", "authorize", scope=scope)
assert req(b, "right", "b", "start", scope=scope)
print("PASS 66-F-11 other Forma independent and IDs scoped")
assert not req(b, "right", "invalid", "bogus", scope=scope)
assert not req(b, "right", "invalid", "start", scope=scope)
print("PASS 66-F-12 rejected request ID is reserved")
assert b.disconnect("right")
assert right.halted
print("PASS 66-F-13 disconnect stops second Forma independently")
print("PASS all 13 suite 66-F synthetic checks")
