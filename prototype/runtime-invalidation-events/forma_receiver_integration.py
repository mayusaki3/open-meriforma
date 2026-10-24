"""Suite 66-E: synthetic receiver-to-Forma request boundary.

Receiver only routes; per-Forma maintenance, policy and grant ledger decide.
No authenticated transport, physical drive, or hardware receiver.
"""
class FormaReceiverIntegration:
    def __init__(self, units):
        if type(units) is not dict or not units or any(
                type(k) is not str or not k or v is None for k, v in units.items()):
            raise ValueError("invalid units")
        self.units = dict(units)

    def _unit(self, forma_id):
        return self.units.get(forma_id) if type(forma_id) is str else None

    def enter_maintenance(self, forma_id):
        unit = self._unit(forma_id)
        return unit is not None and unit.state.enter_maintenance()

    def exit_maintenance(self, forma_id):
        unit = self._unit(forma_id)
        if unit is None:
            return False
        changed = unit.state.exit_maintenance()
        if changed:
            unit._stop_all()
        return changed

    def invalidate(self, forma_id, *, generation=None, fault=False):
        unit = self._unit(forma_id)
        if unit is None:
            return False
        unit.state.invalidate(generation=generation, fault=fault)
        unit._stop_all()
        return True

    def request_authorize(self, forma_id, operation_id, scope):
        unit = self._unit(forma_id)
        return unit is not None and unit.authorize(operation_id, scope)

    def request_start(self, forma_id, operation_id, scope):
        unit = self._unit(forma_id)
        return unit is not None and unit.start(operation_id, scope)

    def request_finish(self, forma_id, operation_id):
        unit = self._unit(forma_id)
        return unit is not None and unit.finish(operation_id)
