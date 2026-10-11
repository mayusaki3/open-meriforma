from reboot_state_policy import boot_assessment, classify

assert classify("calibration", valid=True, compatible=True, bound_to_device=True) == "candidate_reusable"
for checks in (
    {"valid": False, "compatible": True, "bound_to_device": True},
    {"valid": True, "compatible": False, "bound_to_device": True},
    {"valid": True, "compatible": True, "bound_to_device": False},
    {},
):
    assert classify("calibration", **checks) == "reject_and_revalidate"
print("PASS configuration and calibration require validity compatibility and device binding")

for kind in ("execution", "control_lease", "object_use_lease"):
    assert classify(kind, valid=True, compatible=True, bound_to_device=True) == "discard_live_authority"
for kind in ("health", "reachability", "observation", "constraint"):
    assert classify(kind) == "reobserve"
print("PASS active authority discarded and volatile observations recomputed")

for kind in ("event", "ack", "action_report", "verification"):
    assert classify(kind, valid=True, compatible=True, bound_to_device=True) == "historical_only"
assert classify("unrecognized") == "unknown_reject"
print("PASS event and STOP evidence history cannot become live authority")

result = boot_assessment({
    "identity": {"valid": True, "compatible": True, "bound_to_device": True},
    "execution": {"valid": True},
    "verification": {"valid": True},
    "health": {},
    "unknown_kind": {},
})
assert result["dispositions"]["identity"] == "candidate_reusable"
assert result["dispositions"]["execution"] == "discard_live_authority"
assert result["dispositions"]["verification"] == "historical_only"
assert result["dispositions"]["health"] == "reobserve"
assert result["dispositions"]["unknown_kind"] == "unknown_reject"
assert not result["automatic_resume"]
assert not result["lease_mutation"]
assert not result["current_physical_safety_verified"]
print("PASS reboot assessment never authorizes motion or mutates leases")

for invalid in (None, [], {"identity": None}, {"identity": {"valid": 1}},
                {"identity": {"unexpected": True}}):
    try:
        boot_assessment(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(f"invalid input accepted: {invalid!r}")
print("PASS invalid classification inputs rejected")
print("PASS all reboot-state-policy checks")
