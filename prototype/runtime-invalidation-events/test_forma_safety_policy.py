"""Suite 66-C: ten synthetic Forma-specific safety policy checks."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy, PolicyGuardedOperations

def setup(bounds=(-30, 30)):
    s = FormaMaintenanceState("hand", "gen-1")
    assert s.enter_maintenance()
    p = FormaSafetyPolicy(
        actuators={"finger": {"position": bounds}},
        clearance_conditions=("guard_closed", "operator_confirmed"))
    return s, p, PolicyGuardedOperations(s, p)

def scope(lo=-10, hi=10, actuator="finger", mode="position"):
    return dict(actuator=actuator, control_mode=mode, minimum=lo, maximum=hi)

s, p, g = setup()
assert not g.approve_clearance({"guard_closed": True, "operator_confirmed": False})
print("PASS 66-C-01 failed clearance condition denies approval")

assert not g.approve_clearance({"guard_closed": True})
print("PASS 66-C-02 incomplete evidence denied")

assert g.approve_clearance({"guard_closed": True, "operator_confirmed": True})
print("PASS 66-C-03 matching evidence permits synthetic clearance")

assert g.authorize("op-1", scope()) and g.start("op-1", scope())
assert g.finish("op-1") and not s.can_drive()
print("PASS 66-C-04 in-range operation and one-shot grant")

assert not g.authorize("op-2", scope(-31, 10))
print("PASS 66-C-05 outside unit limits denied")

assert not g.authorize("op-3", scope(actuator="other"))
assert not g.authorize("op-4", scope(mode="torque"))
print("PASS 66-C-06 unknown actuator and mode denied")

s2, p2, g2 = setup(bounds=(-5, 5))
assert g.authorize("op-5", scope(-10, 10))
assert g2.approve_clearance({"guard_closed": True, "operator_confirmed": True})
assert not g2.authorize("op-5", scope(-10, 10))
print("PASS 66-C-07 distinct Forma limits applied")

assert not g.authorize("op-6", scope(float("nan"), 10))
assert not g.authorize("op-7", scope(10, -10))
print("PASS 66-C-08 invalid numeric scope denied")

class FailingPolicy:
    def evaluate_clearance(self, evidence):
        raise RuntimeError("sensor unavailable")
    def evaluate_operation(self, operation):
        raise RuntimeError("sensor unavailable")

s3 = FormaMaintenanceState("hand", "gen-1")
assert s3.enter_maintenance()
bad = PolicyGuardedOperations(s3, FailingPolicy())
assert not bad.approve_clearance({})
assert not bad.authorize("op", scope())
print("PASS 66-C-09 policy exceptions fail closed")

assert g.authorize("op-8", scope())
s.invalidate(fault=True)
assert not g.start("op-8", scope())
print("PASS 66-C-10 state invalidation overrides policy approval")

print("PASS all 10 suite 66-C synthetic checks")
