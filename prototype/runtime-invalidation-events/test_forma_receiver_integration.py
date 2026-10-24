"""Suite 66-E: synthetic receiver routing; Forma is final authority."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy
from forma_concurrent_operations import FormaConcurrentOperations
from forma_receiver_integration import FormaReceiverIntegration

def scope(a="thumb", lo=0, hi=10):
    return dict(actuator=a, control_mode="position", minimum=lo, maximum=hi)

def make(fid):
    state = FormaMaintenanceState(fid, "gen1")
    policy = FormaSafetyPolicy(actuators={"thumb": {"position": (0, 20)}},
                               clearance_conditions=("guard",))
    ops = FormaConcurrentOperations(state, policy, costs={"thumb": 2}, max_load=3)
    return state, ops

s1, o1 = make("left")
s2, o2 = make("right")
r = FormaReceiverIntegration({"left": o1, "right": o2})
assert not r.request_authorize("left", "op", scope())
print("PASS 66-E-01 receiver cannot bypass maintenance clearance")
assert r.enter_maintenance("left") and o1.approve_clearance({"guard": True})
assert r.request_authorize("left", "op", scope())
assert r.request_start("left", "op", scope())
print("PASS 66-E-02 receiver routes request but Forma grants final start")
assert not r.request_start("left", "op", scope())
print("PASS 66-E-03 replay rejected")
assert not r.request_authorize("right", "op", scope())
assert not r.request_start("right", "op", scope())
print("PASS 66-E-04 no cross-Forma authorization")
assert not r.request_authorize("left", "out", scope(hi=21))
print("PASS 66-E-05 Forma-specific bounds prevail")
assert not r.request_start("missing", "op", scope())
print("PASS 66-E-06 unknown destination rejected")
assert r.invalidate("left", generation="gen2")
assert not r.request_start("left", "op", scope())
assert o1.halted and not o1.active
print("PASS 66-E-07 generation invalidation fails closed")
assert not r.request_authorize("left", "new", scope())
print("PASS 66-E-08 halted Forma cannot be reauthorized")
assert r.enter_maintenance("right") and o2.approve_clearance({"guard": True})
assert r.request_authorize("right", "right-op", scope())
assert r.request_start("right", "right-op", scope())
print("PASS 66-E-09 other Forma independent")
assert r.exit_maintenance("right")
assert not r.request_authorize("right", "late", scope())
assert not r.request_start("right", "right-op", scope())
print("PASS 66-E-10 exit revokes authority")
assert r.request_finish("right", "right-op") is False
print("PASS 66-E-11 cannot finish stale operation")
assert r.invalidate("right", fault=True)
assert not r.request_authorize("right", "after-fault", scope())
print("PASS 66-E-12 fault fail closed")
print("PASS all 12 suite 66-E synthetic checks")
