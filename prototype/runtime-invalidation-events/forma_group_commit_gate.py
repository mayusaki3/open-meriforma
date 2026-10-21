"""Suite 64: peer-local synthetic group-commit gate (NOT authentication).

A peer must have a local reservation and explicitly installed, exact group
commit tuple. This model deliberately does not grant motor authority.
"""


class FormaGroupCommitGate:
    def __init__(self, *, peer, required_peers, group_epoch, generation, sequence):
        if (type(peer) is not str or not peer
                or type(group_epoch) is not str or not group_epoch
                or type(generation) is not str or not generation
                or type(sequence) is not int or sequence <= 0
                or not isinstance(required_peers, (tuple, list))
                or not required_peers or any(type(p) is not str or not p for p in required_peers)
                or len(set(required_peers)) != len(required_peers)
                or peer not in required_peers):
            raise ValueError("invalid local reservation")
        self.peer = peer
        self.required = frozenset(required_peers)
        self.group_epoch = group_epoch
        self.generation = generation
        self.sequence = sequence
        self.committed = False
        self.revoked = False

    def install(self, proof):
        if self.revoked or self.committed:
            return False
        # Deliberately require a complete peer set and exact local sequence.
        # This is structural matching only; the proof is forgeable.
        if type(proof) is not dict or set(proof) != {
                "peer", "required_peers", "group_epoch", "generation", "sequence",
                "committed_peers"}:
            return False
        peers = proof["required_peers"]
        committed = proof["committed_peers"]
        if (not isinstance(peers, (tuple, list))
                or not isinstance(committed, (tuple, list))
                or any(type(p) is not str for p in peers + committed)
                or len(set(peers)) != len(peers)
                or len(set(committed)) != len(committed)
                or frozenset(peers) != self.required
                or frozenset(committed) != self.required
                or proof["peer"] != self.peer
                or proof["group_epoch"] != self.group_epoch
                or proof["generation"] != self.generation
                or type(proof["sequence"]) is not int
                or proof["sequence"] != self.sequence):
            return False
        self.committed = True
        return True

    def eligible(self, *, generation, sequence, group_epoch):
        return (self.committed and not self.revoked
                and generation == self.generation
                and type(sequence) is int and sequence == self.sequence
                and group_epoch == self.group_epoch)

    def deny(self):
        self.revoked = True
        self.committed = False
