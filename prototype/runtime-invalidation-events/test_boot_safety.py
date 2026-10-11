from boot_safety import BootGate


def prepare(gate, peer="peer-a", peer_epoch=1):
    gate.validate_configuration(kind="configuration", valid=True,
                                compatible=True, bound_to_device=True)
    gate.validate_configuration(kind="calibration", valid=True,
                                compatible=True, bound_to_device=True)
    gate.establish_peer(peer, peer_epoch)
    for name in ("local_safety", "communication", "fresh_observation"):
        gate.observe(name, True)


for role in ("main", "forma"):
    gate = BootGate(role)
    assert not gate.status()["authorization_eligible"]
    assert not gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                          peer_epoch=1, explicit=True)
    prepare(gate)
    assert not gate.status()["authorization_eligible"]
    assert not gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                          peer_epoch=1, explicit=False)
    assert gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                      peer_epoch=1, explicit=True)
    assert gate.status()["authorization_eligible"]
    assert not gate.status()["motor_command_issued"]
    print(f"PASS {role} requires complete fresh checks and explicit authorization")

    gate.peer_lost()
    assert not gate.status()["authorization_eligible"]
    gate.establish_peer("peer-a", 2)
    gate.observe("communication", True)
    assert not gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                          peer_epoch=2, explicit=True)
    gate.observe("fresh_observation", True)
    assert gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                      peer_epoch=2, explicit=True)
    print(f"PASS {role} communication loss and peer reboot revoke authorization")

    old_epoch = gate.epoch
    gate.boot()
    assert gate.epoch == old_epoch + 1
    assert not gate.status()["authorization_eligible"]
    prepare(gate, peer_epoch=3)
    assert not gate.request_authorization(epoch=old_epoch, peer_identity="peer-a",
                                          peer_epoch=3, explicit=True)
    assert gate.request_authorization(epoch=gate.epoch, peer_identity="peer-a",
                                      peer_epoch=3, explicit=True)
    gate.validate_configuration(kind="calibration", valid=False,
                                compatible=True, bound_to_device=True)
    assert not gate.status()["authorization_eligible"]
    print(f"PASS {role} restart and invalid calibration fail closed")

for invalid in ("host", "", None):
    try:
        BootGate(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid role accepted")
gate = BootGate("main")
for fn in (lambda: gate.establish_peer("", 1),
           lambda: gate.establish_peer("peer", True),
           lambda: gate.observe("communication", 1),
           lambda: gate.validate_configuration(kind="configuration",
                     valid=1, compatible=True, bound_to_device=True)):
    try:
        fn()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
print("PASS invalid role, peer epoch and observation inputs rejected")
print("PASS all boot-safety checks")
