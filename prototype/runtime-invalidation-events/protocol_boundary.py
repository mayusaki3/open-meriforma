"""Transport-neutral synthetic message boundary for session + heartbeat state.

No serialization standard, authenticated sender, CAN-FD driver or motor I/O.
"""
from forma_sessions import SessionMonitor
from forma_heartbeat import FormaLinkMonitor, _time

KINDS = frozenset({"heartbeat", "ready"})
FIELDS = frozenset({"kind", "unit", "main_boot", "challenge",
                    "forma_boot", "session", "sequence", "ready"})


class ProtocolBoundary:
    def __init__(self, required_units, *, timeout):
        self.sessions = SessionMonitor(required_units)
        self.links = FormaLinkMonitor(required_units, timeout=timeout)

    def start_main(self, *, boot_id, challenge):
        self.sessions.start_main(boot_id=boot_id, challenge=challenge)
        self.links.restart_main()

    def establish(self, unit, *, forma_boot, main_boot, challenge, session):
        accepted = self.sessions.establish(
            unit, forma_boot=forma_boot, main_boot=main_boot,
            challenge=challenge, session=session)
        if accepted:
            # An old link's heartbeat must never satisfy the new session.
            self.links.peer_lost(unit) if hasattr(self.links, "peer_lost") else self._clear_link(unit)
        return accepted

    def _clear_link(self, unit):
        link = self.links.units[unit]
        link.update(epoch=None, sequence=-1, last_seen=None, ready=False)
        self.links.authorized = False

    def receive(self, message, *, now):
        now = _time(now)
        # Check elapsed time before accepting an incoming recovery message.
        self.links.eligible(now=now)
        if type(message) is not dict or set(message) != FIELDS:
            raise ValueError("invalid message schema")
        if message["kind"] not in KINDS:
            raise ValueError("unsupported message kind")
        unit = message["unit"]
        if type(unit) is not str or unit not in self.sessions.units:
            raise ValueError("unknown unit")
        accepted = self.sessions.receive(
            unit, forma_boot=message["forma_boot"],
            main_boot=message["main_boot"], challenge=message["challenge"],
            session=message["session"], sequence=message["sequence"],
            ready=message["ready"])
        if not accepted:
            return False
        # Session's strictly increasing sequence is the ordering authority;
        # heartbeat epoch is an in-process generation for this link only.
        link = self.links.units[unit]
        epoch = 1 if link["epoch"] is None else link["epoch"]
        if not self.links.heartbeat(
                unit, epoch=epoch, sequence=message["sequence"],
                ready=message["ready"], now=now):
            self.sessions.authorized = False
            return False
        if not self.links.authorized:
            self.sessions.authorized = False
        if not message["ready"]:
            self.sessions.authorized = False
        return True

    def authorize(self, *, explicit, now):
        if type(explicit) is not bool:
            raise ValueError("explicit must be bool")
        if not self.links.authorize(explicit=explicit, now=now):
            self.sessions.authorized = False
            return False
        if not self.sessions.authorize(explicit=explicit):
            self.links.authorized = False
            return False
        return self.eligible(now=now)

    def eligible(self, *, now):
        fresh = self.links.eligible(now=now)
        if not fresh:
            self.sessions.authorized = False
        return fresh and self.sessions.eligible()

    def status(self, *, now):
        return {"eligible": self.eligible(now=now), "automatic_resume": False,
                "motor_command_issued": False, "physical_safety_verified": False}
