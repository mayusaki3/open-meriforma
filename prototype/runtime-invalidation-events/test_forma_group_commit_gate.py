"""Suite 64: local group-commit matching, no cryptographic verification."""
from forma_group_commit_gate import FormaGroupCommitGate


def gate():
    return FormaGroupCommitGate(peer="left", required_peers=("left", "right"),
                                group_epoch="group-1", generation="M1:C1", sequence=1)


def proof(**changes):
    value = dict(peer="left", required_peers=("left", "right"),
                 group_epoch="group-1", generation="M1:C1", sequence=1,
                 committed_peers=("left", "right"))
    value.update(changes)
    return value


g = gate()
assert not g.eligible(generation="M1:C1", sequence=1, group_epoch="group-1")
print("PASS local receiver remains denied before group proof")

g = gate()
assert g.install(proof())
assert g.eligible(generation="M1:C1", sequence=1, group_epoch="group-1")
assert not g.install(proof())
print("PASS exact all-peer proof enables only matching local reservation")

for wrong in (
    proof(peer="right"),
    proof(required_peers=("left",)),
    proof(committed_peers=("left",)),
    proof(group_epoch="group-old"),
    proof(generation="M0:C0"),
    proof(sequence=0),
    proof(sequence=True),
    proof(committed_peers=("left", "left")),
    proof(required_peers=("left", "right", "extra")),
    proof(committed_peers=["left", "extra"]),
    {"peer": "left"},
):
    g = gate()
    assert not g.install(wrong), wrong
    assert not g.eligible(generation="M1:C1", sequence=1, group_epoch="group-1")
print("PASS missing, partial, mismatched and malformed proof rejected")

g = gate()
assert g.install(proof())
assert not g.eligible(generation="M0:C0", sequence=1, group_epoch="group-1")
assert not g.eligible(generation="M1:C1", sequence=2, group_epoch="group-1")
assert not g.eligible(generation="M1:C1", sequence=1, group_epoch="group-old")
g.deny()
assert not g.eligible(generation="M1:C1", sequence=1, group_epoch="group-1")
assert not g.install(proof())
print("PASS stale execution context and revocation deny local authority")

g = gate()  # process restart: no persisted group commit or automatic restore
assert not g.eligible(generation="M1:C1", sequence=1, group_epoch="group-1")
assert not g.install(proof(sequence=2))
print("PASS restart does not restore prior group authorization")

print("PASS all forma-group-commit-gate checks")
