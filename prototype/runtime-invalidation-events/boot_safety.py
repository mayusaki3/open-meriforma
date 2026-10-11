"""Synthetic boot authorization gate; never controls motors or safety outputs.

The gate is a candidate policy, not a real hardware safety mechanism.
Each restart/peer epoch change invalidates authorization.
"""
from reboot_state_policy import classify

ROLES = frozenset({"main", "forma"})
CHECKS = frozenset({"config", "calibration", "local_safety", "communication",
                    "peer_identity", "peer_epoch", "fresh_observation"})


class BootGate:
    def __init__(self, role):
        if role not in ROLES:
            raise ValueError("unknown controller role")
        self.role = role
        self.boot()

    def boot(self):
        self.epoch = getattr(self, "epoch", 0) + 1
        self.checks = {name: False for name in CHECKS}
        self.authorization = None
        self.peer = None
        self.hold_reason = "boot_requires_validation"

    def validate_configuration(self, *, kind, valid, compatible, bound_to_device):
        if kind not in {"configuration", "calibration"}:
            raise ValueError("unsupported configuration kind")
        if any(type(x) is not bool for x in (valid, compatible, bound_to_device)):
            raise ValueError("invalid configuration checks")
        accepted = classify(kind, valid=valid, compatible=compatible,
                            bound_to_device=bound_to_device) == "candidate_reusable"
        self.checks["config" if kind == "configuration" else "calibration"] = accepted
        self._revoke("configuration_changed")
        return accepted

    def observe(self, name, ok):
        if name not in CHECKS - {"config", "calibration", "peer_identity", "peer_epoch"}:
            raise ValueError("unsupported observation")
        if type(ok) is not bool:
            raise ValueError("invalid observation")
        self.checks[name] = ok
        self._revoke("observations_changed")

    def establish_peer(self, identity, epoch):
        if not isinstance(identity, str) or not identity or type(epoch) is not int or epoch < 1:
            raise ValueError("invalid peer identity/epoch")
        if self.peer != (identity, epoch):
            self._revoke("peer_changed")
            self.checks["fresh_observation"] = False
            self.checks["communication"] = False
        self.peer = (identity, epoch)
        self.checks["peer_identity"] = True
        self.checks["peer_epoch"] = True

    def peer_lost(self):
        self.peer = None
        for name in ("communication", "peer_identity", "peer_epoch", "fresh_observation"):
            self.checks[name] = False
        self._revoke("peer_lost")

    def _revoke(self, reason):
        self.authorization = None
        self.hold_reason = reason

    def request_authorization(self, *, epoch, peer_identity, peer_epoch, explicit):
        if type(explicit) is not bool or type(epoch) is not int:
            raise ValueError("invalid authorization")
        if not explicit or epoch != self.epoch or self.peer != (peer_identity, peer_epoch):
            self._revoke("authorization_rejected")
            return False
        if not all(self.checks.values()):
            self._revoke("checks_incomplete")
            return False
        self.authorization = (epoch, peer_identity, peer_epoch)
        self.hold_reason = None
        return True

    def status(self):
        # Advisory eligibility, not proof of physical safe state or motor enable.
        eligible = (self.authorization is not None
                    and self.authorization == (self.epoch, *(self.peer or (None, None)))
                    and all(self.checks.values()))
        return {"role": self.role, "boot_epoch": self.epoch,
                "authorization_eligible": eligible,
                "checks": dict(self.checks), "hold_reason": self.hold_reason,
                "motor_command_issued": False, "automatic_resume": False,
                "current_physical_safety_verified": False}
