"""Pure candidate reboot classification; does not perform device control or I/O."""

CONFIG_KINDS = frozenset({"identity", "configuration", "calibration"})
HISTORY_KINDS = frozenset({"event", "ack", "action_report", "verification"})
LIVE_KINDS = frozenset({"execution", "control_lease", "object_use_lease",
                        "health", "reachability", "observation", "constraint"})


def classify(kind, *, valid=False, compatible=False, bound_to_device=False):
    """Return an advisory boot disposition, never an actuation instruction.

    Caller-provided checks are provisional evidence, not cryptographic attestation.
    """
    if kind in CONFIG_KINDS:
        if valid and compatible and bound_to_device:
            return "candidate_reusable"
        return "reject_and_revalidate"
    if kind in HISTORY_KINDS:
        return "historical_only"
    if kind in LIVE_KINDS:
        return "discard_live_authority" if kind in {
            "execution", "control_lease", "object_use_lease"} else "reobserve"
    return "unknown_reject"


def boot_assessment(items):
    """Classify supplied records without reconstituting active control authority."""
    if not isinstance(items, dict):
        raise ValueError("items must be a dictionary")
    dispositions = {}
    for kind, checks in items.items():
        if not isinstance(checks, dict):
            raise ValueError("checks must be dictionaries")
        if any(type(value) is not bool for value in checks.values()):
            raise ValueError("checks must be booleans")
        if set(checks) - {"valid", "compatible", "bound_to_device"}:
            raise ValueError("unknown check")
        dispositions[kind] = classify(kind, **checks)
    return {
        "dispositions": dispositions,
        "automatic_resume": False,
        "lease_mutation": False,
        "current_physical_safety_verified": False,
    }
