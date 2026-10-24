"""Suite 66-D: synthetic per-Forma concurrency gate, NOT motor control.

Single-threaded serialized fixture only; no locking, authenticated transport,
actual loads, physical STOP or runtime safety assurance.
"""
import math
from forma_safety_policy import PolicyGuardedOperations

class FormaConcurrentOperations:
    def __init__(self, state, policy, *, costs, max_load, conflicts=(), isolated=()):
        if (type(costs) is not dict or not costs or
                type(max_load) not in (int, float) or not math.isfinite(max_load)
                or max_load <= 0 or any(type(k) is not str or not k or
                type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for k, v in costs.items())):
            raise ValueError("invalid load model")
        self.guard = PolicyGuardedOperations(state, policy)
        self.state = state
        self.costs = dict(costs)
        self.max_load = max_load
        self.conflicts = self._pairs(conflicts)
        self.isolated = self._pairs(isolated)
        self.active = {}
        self.blocked = set()
        self.halted = False

    @staticmethod
    def _pairs(pairs):
        result = set()
        for pair in pairs:
            if (type(pair) not in (tuple, list) or len(pair) != 2
                    or any(type(x) is not str or not x for x in pair)
                    or pair[0] == pair[1]):
                raise ValueError("invalid pair")
            result.add(frozenset(pair))
        return result

    def approve_clearance(self, observed):
        return self.guard.approve_clearance(observed)

    def authorize(self, operation_id, scope):
        return self._context_ok() and self.guard.authorize(operation_id, scope)

    def _stop_all(self):
        self.guard.operations.grants.clear()
        self.active.clear()
        self.halted = True
        return False

    def start(self, operation_id, scope):
        # All checks and ledger consumption are serialized in this fixture.
        if not self._context_ok():
            return self._stop_all()
        if type(scope) is not dict:
            return False
        actuator = scope.get("actuator")
        if (type(actuator) is not str or actuator not in self.costs
                or actuator in self.blocked or
                any(other["actuator"] == actuator or
                    frozenset((actuator, other["actuator"])) in self.conflicts
                    for other in self.active.values())):
            return False
        if sum(self.costs[x["actuator"]] for x in self.active.values()) + self.costs[actuator] > self.max_load:
            return False
        if not self.guard.start(operation_id, scope):
            return False
        self.active[operation_id] = dict(scope)
        return True

    def _context_ok(self):
        return not self.halted and self.guard.operations._context() is not None

    def finish(self, operation_id):
        if not self._context_ok():
            return self._stop_all()
        if operation_id not in self.active:
            return False
        if not self.guard.finish(operation_id):
            return self._stop_all()
        del self.active[operation_id]
        return True

    def local_fault(self, actuator):
        if not self._context_ok():
            return self._stop_all()
        affected = {op for op, scope in self.active.items()
                    if scope["actuator"] == actuator}
        remaining = {scope["actuator"] for op, scope in self.active.items()
                     if op not in affected}
        if not affected or any(frozenset((actuator, other)) not in self.isolated
                               for other in remaining):
            return self._stop_all()
        for op in affected:
            self.guard.operations.grants.pop(op, None)
            del self.active[op]
        self.blocked.add(actuator)
        return True

    def recheck_runtime(self, *, measured_load):
        if not self._context_ok():
            return self._stop_all()
        if (type(measured_load) not in (int, float)
                or not math.isfinite(measured_load)
                or measured_load < 0 or measured_load > self.max_load):
            return self._stop_all()
        return True
