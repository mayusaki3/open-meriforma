from forma_sessions import SessionMonitor

m = SessionMonitor(("left", "right"))
m.start_main(boot_id="main-A", challenge="challenge-A")
assert m.establish("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L1")
assert m.establish("right", forma_boot="right-A", main_boot="main-A", challenge="challenge-A", session="R1")
assert m.receive("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L1", sequence=0, ready=True)
assert not m.authorize(explicit=True)
assert m.receive("right", forma_boot="right-A", main_boot="main-A", challenge="challenge-A", session="R1", sequence=0, ready=True)
assert not m.authorize(explicit=False)
assert m.authorize(explicit=True)
print("PASS required peers and explicit authorization")

assert not m.receive("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L1", sequence=0, ready=True)
assert m.eligible()
assert m.establish("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L2")
assert not m.eligible()
assert not m.receive("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L1", sequence=100, ready=True)
assert m.receive("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L2", sequence=0, ready=True)
assert not m.eligible()
assert m.authorize(explicit=True)
print("PASS old session and duplicate messages rejected")

assert m.establish("right", forma_boot="right-B", main_boot="main-A", challenge="challenge-A", session="R2")
assert not m.eligible()
assert not m.receive("right", forma_boot="right-A", main_boot="main-A", challenge="challenge-A", session="R1", sequence=5, ready=True)
assert m.receive("right", forma_boot="right-B", main_boot="main-A", challenge="challenge-A", session="R2", sequence=0, ready=True)
assert m.authorize(explicit=True)
print("PASS one Forma reboot revokes all coordinated eligibility")

m.start_main(boot_id="main-B", challenge="challenge-B")
assert not m.eligible()
assert not m.establish("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L3")
assert m.establish("left", forma_boot="left-A", main_boot="main-B", challenge="challenge-B", session="L3")
assert m.establish("right", forma_boot="right-B", main_boot="main-B", challenge="challenge-B", session="R3")
assert not m.receive("left", forma_boot="left-A", main_boot="main-A", challenge="challenge-A", session="L2", sequence=999, ready=True)
assert m.receive("left", forma_boot="left-A", main_boot="main-B", challenge="challenge-B", session="L3", sequence=0, ready=True)
assert m.receive("right", forma_boot="right-B", main_boot="main-B", challenge="challenge-B", session="R3", sequence=0, ready=True)
assert not m.eligible()
assert m.authorize(explicit=True)
print("PASS Main reboot rejects previous challenge and requires reauthorization")

assert m.receive("right", forma_boot="right-B", main_boot="main-B", challenge="challenge-B", session="R3", sequence=1, ready=False)
assert not m.eligible()
assert m.receive("right", forma_boot="right-B", main_boot="main-B", challenge="challenge-B", session="R3", sequence=2, ready=True)
assert not m.eligible()
print("PASS readiness recovery never auto-resumes")

for invalid in (lambda: SessionMonitor(("x", "x")),
                lambda: m.start_main(boot_id="", challenge="C"),
                lambda: m.receive("left", forma_boot="left-A", main_boot="main-B", challenge="challenge-B", session="L3", sequence=True, ready=True),
                lambda: m.authorize(explicit=1)):
    try:
        invalid()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
assert not m.status()["motor_command_issued"]
print("PASS malformed inputs rejected; no motor or physical safety claims")
print("PASS all forma-session checks")
