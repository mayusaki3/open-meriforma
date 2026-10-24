"""66-G timeout and fresh-fixture recovery regression."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy
from forma_concurrent_operations import FormaConcurrentOperations
from forma_receiver_integration import FormaReceiverIntegration
from forma_transport_boundary import FormaTransportBoundary
from forma_timed_recovery import FormaTimedRecovery

def make(fid, gen="g1"):
    s = FormaMaintenanceState(fid, gen)
    p = FormaSafetyPolicy(actuators={"thumb": {"position": (0, 20)}},
                          clearance_conditions=("guard",))
    return FormaConcurrentOperations(s, p, costs={"thumb": 1}, max_load=2)

scope = dict(actuator="thumb", control_mode="position", minimum=0, maximum=10)
left, right = make("left"), make("right")
r = FormaReceiverIntegration({"left": left, "right": right})
t = FormaTimedRecovery(FormaTransportBoundary(r), timeout=5)
assert t.connect("left", "g1") and t.connect("right", "g1")
assert r.enter_maintenance("left") and left.approve_clearance({"guard": True})
assert t.receive(forma_id="left", generation="g1", request_id="a",
                 action="authorize", operation_id="op", scope=scope)
assert t.receive(forma_id="left", generation="g1", request_id="b",
                 action="start", operation_id="op", scope=scope)
print("PASS 66-G-01 active operation in connected session")
assert t.tick(4) and t.heartbeat("left", "g1")
assert not left.halted
print("PASS 66-G-02 heartbeat extends deadline")
assert t.tick(5) and right.halted and not left.halted
print("PASS 66-G-03 timed-out Forma stopped independently")
assert t.tick(9) and left.halted and not left.active
print("PASS 66-G-04 timeout stops active operation")
assert not t.heartbeat("left", "g1")
assert not t.receive(forma_id="left", generation="g1", request_id="c",
                     action="authorize", operation_id="other", scope=scope)
print("PASS 66-G-05 late traffic cannot revive timed-out link")
assert t.connect("left", "g1")
assert not t.receive(forma_id="left", generation="g1", request_id="d",
                     action="authorize", operation_id="other", scope=scope)
print("PASS 66-G-06 reconnect cannot unlatch")
assert t.boundary.disconnect("left")
assert not t.recover("left", make("left", "g2"), "g2", {"guard": False})
assert r._unit("left") is left
print("PASS 66-G-07 failed safety evidence cannot replace stopped unit")
assert not t.recover("left", make("left", "g1"), "g1", {"guard": True})
print("PASS 66-G-08 old generation cannot recover")
new = make("left", "g2")
assert t.recover("left", new, "g2", {"guard": True})
assert left.halted and r._unit("left") is new and not new.halted
print("PASS 66-G-09 fresh unit and new generation explicitly recovered")
assert not t.receive(forma_id="left", generation="g1", request_id="x",
                     action="authorize", operation_id="old", scope=scope)
print("PASS 66-G-10 stale generation rejected after recovery")
assert not t.receive(forma_id="left", generation="g2", request_id="a",
                     action="start", operation_id="op", scope=scope)
print("PASS 66-G-11 old operation grant not restored")
assert t.receive(forma_id="left", generation="g2", request_id="fresh",
                 action="authorize", operation_id="fresh-op", scope=scope)
assert t.receive(forma_id="left", generation="g2", request_id="start",
                 action="start", operation_id="fresh-op", scope=scope)
print("PASS 66-G-12 fresh operation authorization required")
assert not t.tick(8) and not t.tick(float("nan"))
print("PASS 66-G-13 nonmonotonic and invalid clock rejected")
assert not t.recover("left", make("left", "g3"), "g3", {"guard": True})
print("PASS 66-G-14 cannot recover connected live unit")
print("PASS all 14 suite 66-G synthetic checks")
