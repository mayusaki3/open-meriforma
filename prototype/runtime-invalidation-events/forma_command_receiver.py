"""Suite 50: test-only Forma-side command acceptance boundary.

This is not firmware, an authenticated wire format, or motor actuation.
Transport metadata is passed explicitly by the fixture, not decoded from CAN.
"""
from canfd_fragments import Reassembler, parse


class FormaCommandReceiver:
    def __init__(self, link, *, timeout=0.2, max_transfer_ids=65536, group_gate=None):
        if type(max_transfer_ids) is not int or not 1 <= max_transfer_ids <= 65536:
            raise ValueError('invalid transfer ID capacity')
        if group_gate is not None:
            from forma_group_commit_gate import FormaGroupCommitGate
            if not isinstance(group_gate, FormaGroupCommitGate):
                raise ValueError('invalid group gate')
            if group_gate.generation != link.generation:
                raise ValueError('group gate generation mismatch')
        self.group_gate = group_gate
        self.max_transfer_ids = max_transfer_ids
        self.link = link
        self.generation = link.generation
        self.parts = Reassembler(timeout=timeout)
        self.accepted = []
        self.revoked = False
        self.seen_transfers = set()
        self.expired_transfers = set()
        self.reserved_transfers = set()

    def _deny(self):
        self.parts.active.clear()
        self.revoked = True
        if self.group_gate is not None:
            self.group_gate.deny()
        return False

    def receive(self, frame, *, source, generation, deadline, now):
        if self.revoked:
            return False
        if (self.group_gate is not None
                and not self.group_gate.eligible(
                    generation=self.generation, sequence=self.group_gate.sequence,
                    group_epoch=self.group_gate.group_epoch)):
            return self._deny()
        # Authority and deadline are checked on EVERY fragment, not just
        # when a message becomes complete. The fixture clock is monotonic.
        if (generation != self.generation or self.link.generation != self.generation
                or deadline is None or now > deadline
                or source not in self.link.units or not self.link.eligible(now=now)):
            return self._deny()
        try:
            tid, _, _, _, _ = parse(frame)
            key = (generation, source, tid)
            if key in self.seen_transfers or key in self.expired_transfers:
                return False
            # Retain expired transfer IDs so late fragments cannot begin a
            # fresh assembly under the same ID after timeout.
            expired = [k for k, entry in self.parts.active.items()
                       if now - entry['last'] > self.parts.timeout]
            self.expired_transfers.update((generation, *k) for k in expired)
            if key in self.expired_transfers:
                return False
            # Never evict old IDs: eviction would enable replay. Once the
            # bounded history fills, fail closed until a new generation.
            if key not in self.reserved_transfers:
                if len(self.reserved_transfers) >= self.max_transfer_ids:
                    return self._deny()
                self.reserved_transfers.add(key)
            payload = self.parts.accept(frame, source=source, now=now)
        except ValueError:
            return self._deny()
        if payload is None:
            return None
        # Recheck at the execution-permission boundary. This is an abstract
        # acceptance event only, never a motor command.
        if (self.link.generation != self.generation
                or not self.link.eligible(now=now)
                or (self.group_gate is not None and not self.group_gate.eligible(
                    generation=self.generation, sequence=self.group_gate.sequence,
                    group_epoch=self.group_gate.group_epoch))):
            return self._deny()
        self.seen_transfers.add(key)
        self.accepted.append((source, payload))
        return True
