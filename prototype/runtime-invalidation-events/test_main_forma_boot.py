from main_forma_boot import MainFormaBoot


def prepare(gate):
    for kind in ("configuration", "calibration"):
        assert gate.validate_configuration(
            kind=kind, valid=True, compatible=True, bound_to_device=True)
    for name in ("local_safety", "communication", "fresh_observation"):
        gate.observe(name, True)


pair = MainFormaBoot()
assert not pair.eligible()
pair.pair()
prepare(pair.main)
assert not pair.authorize(explicit=True)
assert not pair.eligible()
print("PASS Main ready cannot override unready Forma")

prepare(pair.forma)
assert not pair.authorize(explicit=False)
assert pair.authorize(explicit=True)
assert pair.eligible()
assert not pair.status()["motor_command_issued"]
print("PASS both peers require checks and explicit coordinated authorization")

pair.forma.observe("local_safety", False)
assert not pair.eligible()
assert not pair.authorize(explicit=True)
print("PASS Forma local safety loss invalidates coordinated eligibility")

pair.forma.observe("local_safety", True)
assert not pair.eligible()
assert pair.authorize(explicit=True)
pair.communication_lost()
assert not pair.eligible()
assert not pair.status()["main_eligible"]
assert not pair.status()["forma_eligible"]
print("PASS communication loss invalidates both peers")

pair.pair()
prepare(pair.main)
prepare(pair.forma)
assert pair.authorize(explicit=True)
pair.restart("forma")
assert not pair.eligible()
pair.pair()
prepare(pair.main)
prepare(pair.forma)
assert not pair.eligible()
assert pair.authorize(explicit=True)
print("PASS Forma reboot requires fresh pairing checks and authorization")

pair.restart("main")
assert not pair.eligible()
pair.pair()
prepare(pair.main)
prepare(pair.forma)
assert pair.authorize(explicit=True)
pair.main.validate_configuration(
    kind="calibration", valid=False, compatible=True, bound_to_device=True)
assert not pair.eligible()
assert not pair.authorize(explicit=True)
print("PASS Main reboot and invalid calibration revoke coordinated eligibility")

for invalid in ("host", None):
    try:
        pair.restart(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid role accepted")
try:
    pair.authorize(explicit=1)
except ValueError:
    pass
else:
    raise AssertionError("non-boolean authorization accepted")
assert not pair.status()["automatic_resume"]
assert not pair.status()["current_physical_safety_verified"]
print("PASS invalid requests rejected and no physical safety claim")
print("PASS all main-forma-boot checks")
