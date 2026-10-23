"""Suite 66-A: ten synthetic maintenance/clearance checks."""
from forma_maintenance_state import FormaMaintenanceState

def unit():
    return FormaMaintenanceState("finger", "gen-1")

def maintenance():
    u = unit()
    assert u.enter_maintenance()
    return u

u = unit()
u.group_authorized = True
assert u.enter_maintenance() and not u.group_authorized
print("PASS 66-A-01 group authority invalidated on maintenance entry")

assert not u.drive_enabled and not u.can_drive()
print("PASS 66-A-02 drive denied on entry")

u = maintenance()
assert not u.approve_clearance(conditions_ok=False, generation="gen-1", session=u.session)
assert u.clearance is None
print("PASS 66-A-03 unsafe clearance rejected")

assert u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
assert u.clearance == ("finger", "gen-1", u.session)
print("PASS 66-A-04 valid clearance recorded")

assert not u.can_drive() and not u.drive_enabled
print("PASS 66-A-05 clearance alone never enables drive")

assert u.exit_maintenance() and u.clearance is None and not u.can_drive()
print("PASS 66-A-06 maintenance exit revokes clearance")

u = maintenance()
assert u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
u.invalidate(generation="gen-2")
assert u.clearance is None
assert not u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
print("PASS 66-A-07 link/generation invalidation")

u = maintenance()
assert u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
old_session = u.session
u.reboot()
assert u.clearance is None and u.mode == "normal" and u.session != old_session
print("PASS 66-A-08 reboot never restores clearance")

u = maintenance()
assert u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
u.invalidate(fault=True)
assert u.clearance is None and u.faulted and not u.can_drive()
print("PASS 66-A-09 safety fault invalidates clearance")

assert not u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
assert u.recover_fault()
assert u.approve_clearance(conditions_ok=True, generation="gen-1", session=u.session)
print("PASS 66-A-10 fresh approval required after invalidation")

print("PASS all 10 suite 66-A synthetic checks")
