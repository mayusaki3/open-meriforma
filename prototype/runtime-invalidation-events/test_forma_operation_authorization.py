"""Suite 66-B: synthetic per-operation authorization tests; no motor drive."""
from forma_maintenance_state import FormaMaintenanceState
from forma_operation_authorization import FormaOperationAuthorization

SCOPE = dict(actuator="finger-1", control_mode="position", minimum=0, maximum=30)
OTHER = dict(actuator="finger-2", control_mode="position", minimum=0, maximum=30)

def ready():
    state = FormaMaintenanceState("hand", "gen-1")
    assert state.enter_maintenance()
    assert state.approve_clearance(conditions_ok=True, generation="gen-1", session=state.session)
    return state, FormaOperationAuthorization(state)

s = FormaMaintenanceState("hand", "gen-1")
ops = FormaOperationAuthorization(s)
assert not ops.authorize("op-1", SCOPE)
print("PASS 66-B-01 reject without clearance")

s, ops = ready()
assert ops.authorize("op-1", SCOPE)
assert not s.can_drive() and not s.drive_enabled
print("PASS 66-B-02 issue scoped grant without drive")

assert ops.start("op-1", SCOPE)
print("PASS 66-B-03 exact operation starts synthetically")

assert not ops.start("op-1", SCOPE)
print("PASS 66-B-04 start cannot be replayed")

assert ops.finish("op-1") and not ops.start("op-1", SCOPE)
print("PASS 66-B-05 completed grant cannot be reused")

s, ops = ready()
assert ops.authorize("op-2", SCOPE)
assert not ops.start("op-2", OTHER)
assert ops.start("op-2", SCOPE)
print("PASS 66-B-06 mismatched scope denied without consuming grant")

s, ops = ready()
assert ops.authorize("op-3", SCOPE)
assert not ops.authorize("op-3", SCOPE)
assert not ops.authorize("op-4", dict(SCOPE, maximum=0, minimum=10))
print("PASS 66-B-07 duplicate and invalid range denied")

s, ops = ready()
assert ops.authorize("op-5", SCOPE)
s.invalidate(generation="gen-2")
assert not ops.start("op-5", SCOPE) and not ops.authorize("op-6", SCOPE)
print("PASS 66-B-08 generation change revokes grants")

s, ops = ready()
assert ops.authorize("op-7", SCOPE)
assert s.exit_maintenance()
assert not ops.start("op-7", SCOPE)
assert s.enter_maintenance()
assert s.approve_clearance(conditions_ok=True, generation="gen-1", session=s.session)
assert not ops.start("op-7", SCOPE)
print("PASS 66-B-09 old maintenance session grant rejected")

s, ops = ready()
assert ops.authorize("op-8", SCOPE)
s.invalidate(fault=True)
assert not ops.start("op-8", SCOPE)
assert s.recover_fault()
assert not ops.authorize("op-9", SCOPE)
print("PASS 66-B-10 fault revokes grant and requires fresh clearance")

s, ops = ready()
assert ops.authorize("op-10", SCOPE)
s.invalidate()
assert s.approve_clearance(conditions_ok=True, generation="gen-1", session=s.session)
assert not ops.start("op-10", SCOPE)
print("PASS 66-B-11 clearance renewal cannot revive stale grant")

print("PASS all 11 suite 66-B synthetic checks")
