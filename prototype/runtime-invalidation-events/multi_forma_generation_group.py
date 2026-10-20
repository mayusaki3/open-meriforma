"""Suite 62: synthetic all-peers generation reservation gate.

This model is not authenticated distributed commit or physical motor inhibit.
"""
from monotonic_generation_guard import MonotonicGenerationGuard


class MultiFormaGenerationGroup:
    def __init__(self, peers):
        if not peers or len(set(peers)) != len(peers):
            raise ValueError("required peers must be nonempty and unique")
        self.required = tuple(peers)
        self.guards = {}
        self.enabled = False

    def attach(self, peer, guard):
        if peer not in self.required or peer in self.guards:
            raise ValueError("unknown or duplicate peer")
        if not isinstance(guard, MonotonicGenerationGuard):
            raise ValueError("invalid guard")
        self.guards[peer] = guard

    def reserve(self, links, *, now):
        self.enabled = False
        if set(self.guards) != set(self.required) or set(links) != set(self.required):
            return False
        # A failed or ambiguous reservation poisons this group instance.
        # A fresh group instance does not itself establish authentication.
        reserved = []
        try:
            for peer in self.required:
                self.guards[peer].bind(links[peer], now=now)
                reserved.append(peer)
        except (ValueError, KeyError, OSError):
            for guard in self.guards.values():
                if guard.registry.current is not None:
                    guard.registry.current._deny()
            return False
        self.enabled = True
        return True

    def deny(self):
        self.enabled = False
        for guard in self.guards.values():
            if guard.registry.current is not None:
                guard.registry.current._deny()
