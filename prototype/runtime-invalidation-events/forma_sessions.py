"""Synthetic reboot-safe session fencing using fresh Main challenges.

Trusted caller-supplied boot IDs; no authentication or hardware safety.
"""
class SessionMonitor:
    def __init__(self, required_units):
        units = tuple(required_units)
        if not units or any(type(u) is not str or not u for u in units) or len(set(units)) != len(units):
            raise ValueError("invalid units")
        self.units = {u: {"boot": None, "session": None, "sequence": -1, "ready": False} for u in units}
        self.main_boot = None
        self.challenge = None
        self.authorized = False

    def start_main(self, *, boot_id, challenge):
        self._valid_token(boot_id)
        self._valid_token(challenge)
        if (boot_id, challenge) == (self.main_boot, self.challenge):
            raise ValueError("session challenge must change")
        self.main_boot, self.challenge = boot_id, challenge
        self.authorized = False
        for unit in self.units.values():
            unit.update(boot=None, session=None, sequence=-1, ready=False)

    @staticmethod
    def _valid_token(value):
        if type(value) is not str or not value:
            raise ValueError("invalid identifier")

    def establish(self, unit, *, forma_boot, main_boot, challenge, session):
        self._valid_token(forma_boot)
        self._valid_token(main_boot)
        self._valid_token(challenge)
        self._valid_token(session)
        if unit not in self.units:
            raise ValueError("unknown unit")
        if self.main_boot is None or (main_boot, challenge) != (self.main_boot, self.challenge):
            return False
        entry = self.units[unit]
        # Re-establishment always revokes prior authorization, including a
        # changed session on the same Forma boot.
        self.authorized = False
        entry.update(boot=forma_boot, session=session, sequence=-1, ready=False)
        return True

    def receive(self, unit, *, forma_boot, main_boot, challenge, session, sequence, ready):
        if unit not in self.units or type(sequence) is not int or sequence < 0 or type(ready) is not bool:
            raise ValueError("invalid message")
        for token in (forma_boot, main_boot, challenge, session):
            self._valid_token(token)
        entry = self.units[unit]
        if ((main_boot, challenge) != (self.main_boot, self.challenge)
                or (forma_boot, session) != (entry["boot"], entry["session"])
                or sequence <= entry["sequence"]):
            return False
        entry["sequence"] = sequence
        entry["ready"] = ready
        if not ready:
            self.authorized = False
        return True

    def authorize(self, *, explicit):
        if type(explicit) is not bool:
            raise ValueError("invalid authorization")
        self.authorized = bool(explicit and self.main_boot and all(
            e["boot"] and e["session"] and e["ready"] and e["sequence"] >= 0
            for e in self.units.values()))
        return self.authorized

    def eligible(self):
        return self.authorized and all(e["ready"] for e in self.units.values())

    def status(self):
        return {"eligible": self.eligible(), "automatic_resume": False,
                "motor_command_issued": False, "physical_safety_verified": False}
