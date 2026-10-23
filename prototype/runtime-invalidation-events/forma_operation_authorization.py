"""Suite 66-B: one-shot synthetic per-operation authorization.

Not authenticated, not firmware, not motor actuation or a safety controller.
Concurrency, unit-specific limits and runtime monitoring are out of scope.
"""

class FormaOperationAuthorization:
    def __init__(self, state):
        self.state = state
        self.grants = {}

    @staticmethod
    def _scope(scope):
        if type(scope) is not dict or set(scope) != {
                "actuator", "control_mode", "minimum", "maximum"}:
            return None
        if (type(scope["actuator"]) is not str or not scope["actuator"]
                or scope["control_mode"] not in ("position", "velocity", "torque")
                or type(scope["control_mode"]) is not str
                or type(scope["minimum"]) not in (int, float)
                or type(scope["maximum"]) not in (int, float)):
            return None
        import math
        if (not math.isfinite(scope["minimum"]) or not math.isfinite(scope["maximum"])
                or scope["minimum"] > scope["maximum"]):
            return None
        return (scope["actuator"], scope["control_mode"],
                scope["minimum"], scope["maximum"])

    def _context(self):
        s = self.state
        if (s.mode != "maintenance" or s.faulted or s.clearance is None
                or s.clearance != (s.forma_id, s.generation, s.session)):
            return None
        return (s.forma_id, s.generation, s.session, s.clearance)

    def authorize(self, operation_id, scope):
        context = self._context()
        parsed = self._scope(scope)
        if (context is None or parsed is None or type(operation_id) is not str
                or not operation_id or operation_id in self.grants):
            return False
        self.grants[operation_id] = (context, parsed, "granted")
        return True

    def start(self, operation_id, scope):
        context = self._context()
        parsed = self._scope(scope)
        grant = self.grants.get(operation_id)
        if (context is None or parsed is None or grant is None
                or grant != (context, parsed, "granted")):
            return False
        self.grants[operation_id] = (context, parsed, "running")
        return True

    def finish(self, operation_id):
        grant = self.grants.get(operation_id)
        if grant is None or grant[2] != "running":
            return False
        self.grants[operation_id] = (grant[0], grant[1], "finished")
        return True
