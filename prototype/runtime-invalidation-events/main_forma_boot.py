"""Synthetic Main–Forma coordinated eligibility, without hardware control.

No cached ready bit may survive a peer epoch or authorization change.
"""
from boot_safety import BootGate


class MainFormaBoot:
    def __init__(self):
        self.main = BootGate("main")
        self.forma = BootGate("forma")
        self._linked = None

    def _current_pair(self):
        return (self.main.epoch, self.forma.epoch)

    def pair(self):
        """Establish observed peer identities; invalidate stale local checks."""
        self._linked = self._current_pair()
        self.main.establish_peer("forma", self.forma.epoch)
        self.forma.establish_peer("main", self.main.epoch)

    def authorize(self, *, explicit):
        if type(explicit) is not bool:
            raise ValueError("explicit must be bool")
        if not explicit or self._linked != self._current_pair():
            return False
        if not all(self.main.checks.values()) or not all(self.forma.checks.values()):
            return False
        # No authorization is issued unless both sides have already passed checks.
        a = self.main.request_authorization(
            epoch=self.main.epoch, peer_identity="forma",
            peer_epoch=self.forma.epoch, explicit=True)
        b = self.forma.request_authorization(
            epoch=self.forma.epoch, peer_identity="main",
            peer_epoch=self.main.epoch, explicit=True)
        return a and b and self.eligible()

    def eligible(self):
        return (self._linked == self._current_pair()
                and self.main.peer == ("forma", self.forma.epoch)
                and self.forma.peer == ("main", self.main.epoch)
                and self.main.status()["authorization_eligible"]
                and self.forma.status()["authorization_eligible"])

    def communication_lost(self):
        self._linked = None
        self.main.peer_lost()
        self.forma.peer_lost()

    def restart(self, role):
        if role == "main":
            self.main.boot()
        elif role == "forma":
            self.forma.boot()
        else:
            raise ValueError("unknown role")
        self._linked = None
        self.main.peer_lost()
        self.forma.peer_lost()

    def status(self):
        return {"coordinated_eligible": self.eligible(),
                "main_eligible": self.main.status()["authorization_eligible"],
                "forma_eligible": self.forma.status()["authorization_eligible"],
                "motor_command_issued": False, "automatic_resume": False,
                "current_physical_safety_verified": False}
