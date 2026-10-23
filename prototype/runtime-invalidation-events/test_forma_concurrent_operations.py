"""Suite 66-D: synthetic concurrent operation and stop-scope checks."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy
from forma_concurrent_operations import FormaConcurrentOperations

def scope(a):
    return dict(actuator=a, control_mode="position", minimum=0, maximum=10)

def setup(*, limit=6, conflicts=(), isolated=()):
    s = FormaMaintenanceState("hand", "g1")
    assert s.enter_maintenance()
    p = FormaSafetyPolicy(actuators={
        a: {"position": (0, 30)} for a in ("thumb", "index", "middle")},
        clearance_conditions=("guard",))
    c = FormaConcurrentOperations(s, p, costs={"thumb": 2, "index": 3, "middle": 4},
                                 max_load=limit, conflicts=conflicts, isolated=isolated)
    assert c.approve_clearance({"guard": True})
    return s, c

def launch(c, op, actuator):
    assert c.authorize(op, scope(actuator))
    return c.start(op, scope(actuator))

s, c = setup()
assert launch(c, "a", "thumb") and launch(c, "b", "index")
assert set(c.active) == {"a", "b"}
print("PASS 66-D-01 independent concurrent operations")

assert c.authorize("dup", scope("thumb"))
assert not c.start("dup", scope("thumb"))
assert set(c.active) == {"a", "b"}
print("PASS 66-D-02 duplicate actuator rejected")

assert c.authorize("over", scope("middle"))
assert not c.start("over", scope("middle"))
print("PASS 66-D-03 aggregate load limit")

s, c = setup(conflicts=(("thumb", "index"),))
assert launch(c, "a", "thumb")
assert c.authorize("b", scope("index")) and not c.start("b", scope("index"))
print("PASS 66-D-04 mechanical interference denied")

s, c = setup()
assert launch(c, "a", "thumb")
assert launch(c, "b", "index")
assert c.finish("a") and "a" not in c.active and "b" in c.active
assert not c.start("a", scope("thumb"))
print("PASS 66-D-05 finish releases capacity, not grant")

s, c = setup(isolated=(("thumb", "index"),))
assert launch(c, "a", "thumb") and launch(c, "b", "index")
assert c.local_fault("thumb") and set(c.active) == {"b"}
assert not c.start("a", scope("thumb"))
print("PASS 66-D-06 local fault isolates safe independent operation")

s, c = setup()
assert launch(c, "a", "thumb") and launch(c, "b", "index")
assert c.local_fault("thumb") and not c.active
print("PASS 66-D-07 unknown isolation stops all")

s, c = setup()
assert launch(c, "a", "thumb") and launch(c, "b", "index")
assert not c.recheck_runtime(measured_load=7) and not c.active
print("PASS 66-D-08 runtime load over limit stops all")

s, c = setup()
assert launch(c, "a", "thumb")
s.invalidate(generation="g2")
assert not c.recheck_runtime(measured_load=1) and not c.active
print("PASS 66-D-09 generation invalidation stops all")

s, c = setup()
assert launch(c, "a", "thumb")
assert s.exit_maintenance()
assert not c.recheck_runtime(measured_load=1) and not c.active
print("PASS 66-D-10 maintenance exit stops all")

s, c = setup()
assert launch(c, "a", "thumb")
assert not c.recheck_runtime(measured_load=None) and not c.active
print("PASS 66-D-11 unknown runtime telemetry fails closed")

s, c = setup()
assert launch(c, "a", "thumb")
assert c.recheck_runtime(measured_load=2) and set(c.active) == {"a"}
print("PASS 66-D-12 valid runtime load preserves operation")

print("PASS all 12 suite 66-D synthetic checks")
