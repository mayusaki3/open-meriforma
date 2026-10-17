"""Synthetic authority-gated command staging, not a CAN or actuator sender.

Both enqueue and dispatch recheck the existing integrated link's authority.
Revocation discards all queued commands; there is no automatic replay.
"""
from collections import deque


class AuthorityCommandGate:
    def __init__(self, link):
        self.link = link
        self.queue = deque()
        self.revoked = False
        self.delivered = []

    def _allowed(self, now):
        if self.revoked or not self.link.eligible(now=now):
            self.revoke()
            return False
        return True

    def revoke(self):
        self.revoked = True
        self.queue.clear()

    def stage(self, unit, command_id, *, now):
        if unit not in self.link.units:
            raise ValueError("unknown unit")
        if not self._allowed(now):
            return False
        self.queue.append((self.link.generation, unit, command_id))
        return True

    def dispatch(self, *, now):
        if not self._allowed(now):
            return []
        # Validate again for every item: never trust authority at enqueue.
        sent = []
        while self.queue:
            if not self._allowed(now):
                return sent
            generation, unit, command_id = self.queue.popleft()
            if generation != self.link.generation:
                self.revoke()
                return sent
            sent.append((unit, command_id))
        self.delivered.extend(sent)
        return sent
