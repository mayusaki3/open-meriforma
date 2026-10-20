"""Suite 62: synthetic partial group reservation failures."""
from pathlib import Path
from tempfile import TemporaryDirectory

from causal_integrated_can import CausalIntegratedCan
from monotonic_generation_guard import MonotonicGenerationGuard as Guard, SimulatedWitness
from multi_forma_generation_group import MultiFormaGenerationGroup


def ready(boot, challenge):
    model = CausalIntegratedCan(("left", "right"))
    model.start(boot_id=boot, challenge=challenge)
    for unit in model.link.units:
        assert model.submit(unit, 0, now=0.001, deadline=0.04)
    model.advance(until=0.02)
    model.deliver_acks(until=0.04)
    assert model.link.authorize(explicit=True, now=0.04)
    return model.link


def setup(folder):
    group = MultiFormaGenerationGroup(("left", "right"))
    guards = {}
    witnesses = {}
    for peer in group.required:
        witness = SimulatedWitness()
        guard = Guard(str(Path(folder) / (peer + ".sqlite")), witness, initialize=True)
        group.attach(peer, guard)
        guards[peer] = guard
        witnesses[peer] = witness
    return group, guards, witnesses


def close(guards):
    for guard in guards.values():
        guard.close()


with TemporaryDirectory() as folder:
    group, guards, witnesses = setup(folder)
    assert group.reserve({"left": ready("M1", "C1"), "right": ready("M1", "C1")}, now=0.04)
    assert group.enabled
    assert all(w.value == 1 for w in witnesses.values())
    group.deny()
    assert not group.enabled
    assert all(g.registry.current.revoked for g in guards.values())
    close(guards)
    print("PASS all peers reserve before synthetic group enable and revoke together")

with TemporaryDirectory() as folder:
    group, guards, witnesses = setup(folder)
    assert not group.reserve({"left": ready("M1", "C1")}, now=0.04)
    assert not group.enabled
    assert all(w.value == 0 for w in witnesses.values())
    close(guards)
    print("PASS missing required peer prevents any reservation")

with TemporaryDirectory() as folder:
    group, guards, witnesses = setup(folder)
    # Right link lacks explicit authorization; left reservation already committed.
    bad = CausalIntegratedCan(("left", "right"))
    bad.start(boot_id="M1", challenge="C1")
    assert not group.reserve({"left": ready("M1", "C1"), "right": bad.link}, now=0.04)
    assert not group.enabled and group.poisoned
    assert witnesses["left"].value == 1 and witnesses["right"].value == 0
    assert guards["left"].registry.current.revoked
    assert not group.reserve({"left": ready("M2", "C2"), "right": ready("M2", "C2")}, now=0.04)
    close(guards)
    print("PASS partial committed reservation revokes receiver and forbids same-group retry")

with TemporaryDirectory() as folder:
    group, guards, witnesses = setup(folder)
    witnesses["right"].value = 1
    assert not group.reserve({"left": ready("M1", "C1"), "right": ready("M1", "C1")}, now=0.04)
    assert group.poisoned and not group.enabled
    assert guards["left"].registry.current.revoked
    assert witnesses["left"].value == 1 and witnesses["right"].value == 1
    close(guards)
    print("PASS witness mismatch in one Forma denies group after peer reservation")

with TemporaryDirectory() as folder:
    group, guards, witnesses = setup(folder)
    assert not group.reserve({"left": ready("M1", "C1"), "right": ready("M1", "C1"), "extra": ready("M1", "C1")}, now=0.04)
    assert all(w.value == 0 for w in witnesses.values())
    close(guards)
    print("PASS mismatched required peer set cannot enable group")

print("PASS all multi-forma-generation-group checks")
