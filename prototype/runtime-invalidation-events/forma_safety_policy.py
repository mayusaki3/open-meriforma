"""Suite 66-C: synthetic unit-specific safety policy, NOT physical safety.

The configured bounds are fixture data, not real actuator safety limits.
"""
import math

class FormaSafetyPolicy:
    def __init__(self, *, actuators, clearance_conditions):
        if (type(actuators) is not dict or not actuators
                or type(clearance_conditions) not in (tuple, list)
                or not clearance_conditions
                or any(type(x) is not str or not x for x in clearance_conditions)):
            raise ValueError("invalid policy")
        self.clearance_conditions = frozenset(clearance_conditions)
        self.actuators = {}
        for actuator, modes in actuators.items():
            if (type(actuator) is not str or not actuator or type(modes) is not dict
                    or not modes):
                raise ValueError("invalid actuator")
            accepted = {}
            for mode, bounds in modes.items():
                if (mode not in ("position", "velocity", "torque")
                        or type(mode) is not str or type(bounds) not in (tuple, list)
                        or len(bounds) != 2
                        or any(type(x) not in (int, float) or not math.isfinite(x)
                               for x in bounds)
                        or bounds[0] > bounds[1]):
                    raise ValueError("invalid bounds")
                accepted[mode] = tuple(bounds)
            self.actuators[actuator] = accepted

    def evaluate_clearance(self, observed):
        if type(observed) is not dict or set(observed) != self.clearance_conditions:
            return False, "invalid_clearance_evidence"
        if not all(v is True for v in observed.values()):
            return False, "clearance_condition_failed"
        return True, "ok"

    def evaluate_operation(self, scope):
        if type(scope) is not dict or set(scope) != {
                "actuator", "control_mode", "minimum", "maximum"}:
            return False, "invalid_scope"
        actuator, mode = scope["actuator"], scope["control_mode"]
        if type(actuator) is not str or type(mode) is not str:
            return False, "invalid_scope"
        bounds = self.actuators.get(actuator, {}).get(mode)
        if bounds is None:
            return False, "unsupported_operation"
        lo, hi = scope["minimum"], scope["maximum"]
        if (type(lo) not in (int, float) or type(hi) not in (int, float)
                or not math.isfinite(lo) or not math.isfinite(hi) or lo > hi):
            return False, "invalid_scope"
        if lo < bounds[0] or hi > bounds[1]:
            return False, "outside_unit_limits"
        return True, "ok"

class PolicyGuardedOperations:
    """Fail-closed adapter; 66-B remains the final one-shot grant ledger."""
    def __init__(self, state, policy):
        from forma_operation_authorization import FormaOperationAuthorization
        self.state = state
        self.policy = policy
        self.operations = FormaOperationAuthorization(state)

    def approve_clearance(self, observed):
        try:
            allowed, _ = self.policy.evaluate_clearance(observed)
        except Exception:
            return False
        if allowed is not True:
            return False
        return self.state.approve_clearance(
            conditions_ok=True, generation=self.state.generation,
            session=self.state.session)

    def authorize(self, operation_id, scope):
        try:
            allowed, _ = self.policy.evaluate_operation(scope)
        except Exception:
            return False
        return allowed is True and self.operations.authorize(operation_id, scope)

    def start(self, operation_id, scope):
        try:
            allowed, _ = self.policy.evaluate_operation(scope)
        except Exception:
            return False
        return allowed is True and self.operations.start(operation_id, scope)

    def finish(self, operation_id):
        return self.operations.finish(operation_id)
