"""Suite 66-A: synthetic per-Forma maintenance clearance state model.

Not firmware, authentication, a hardware interlock, or motor actuation.
Clearance is not an operation permit. Every transition starts drive-denied.
"""

class FormaMaintenanceState:
    def __init__(self, forma_id, generation):
        if not isinstance(forma_id, str) or not forma_id or not isinstance(generation, str) or not generation:
            raise ValueError("invalid identity or generation")
        self.forma_id = forma_id
        self.generation = generation
        self.mode = "normal"
        self.session = 0
        self.clearance = None
        self.clearance_revision = 0
        self.drive_enabled = False
        self.group_authorized = False
        self.faulted = False

    def enter_maintenance(self):
        if self.faulted or self.mode != "normal":
            return False
        self.group_authorized = False
        self.drive_enabled = False
        self.clearance = None
        self.session += 1
        self.mode = "maintenance"
        return True

    def approve_clearance(self, *, conditions_ok, generation, session):
        if (self.faulted or self.mode != "maintenance" or
                conditions_ok is not True or generation != self.generation or
                type(session) is not int or session != self.session or
                self.clearance is not None):
            return False
        self.clearance_revision += 1
        self.clearance = (self.forma_id, self.generation, self.session)
        return True

    def can_drive(self):
        # 66-A has no operation grants or physical drive output.
        return False

    def exit_maintenance(self):
        if self.mode != "maintenance":
            return False
        self.clearance = None
        self.drive_enabled = False
        self.group_authorized = False
        self.mode = "normal"
        return True

    def invalidate(self, *, generation=None, fault=False):
        self.clearance = None
        self.drive_enabled = False
        self.group_authorized = False
        if generation is not None:
            if not isinstance(generation, str) or not generation:
                raise ValueError("invalid generation")
            self.generation = generation
        if fault:
            self.faulted = True
        return True

    def reboot(self):
        self.clearance = None
        self.drive_enabled = False
        self.group_authorized = False
        self.mode = "normal"
        self.faulted = False
        self.session += 1

    def recover_fault(self):
        if not self.faulted:
            return False
        self.faulted = False
        self.clearance = None
        self.drive_enabled = False
        return True
