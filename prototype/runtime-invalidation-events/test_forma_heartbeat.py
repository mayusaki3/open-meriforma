from forma_heartbeat import FormaLinkMonitor

m = FormaLinkMonitor(("left", "right"), timeout=0.5)
assert not m.authorize(explicit=True, now=0)
assert m.heartbeat("left", epoch=1, sequence=0, ready=True, now=0.1)
assert not m.authorize(explicit=True, now=0.1)
assert m.heartbeat("right", epoch=1, sequence=0, ready=True, now=0.1)
assert not m.eligible(now=0.1)
assert m.authorize(explicit=True, now=0.1)
assert m.eligible(now=0.4)
print("PASS required Forma units must all be ready and explicitly authorized")

assert not m.eligible(now=0.61)
assert m.heartbeat("left", epoch=1, sequence=1, ready=True, now=0.62)
assert m.heartbeat("right", epoch=1, sequence=1, ready=True, now=0.62)
assert not m.eligible(now=0.62)
assert m.authorize(explicit=True, now=0.62)
print("PASS timeout revokes eligibility and recovery never auto-resumes")

assert not m.heartbeat("left", epoch=1, sequence=1, ready=True, now=0.63)
try:
    m.heartbeat("left", epoch=0, sequence=9, ready=True, now=0.64)
except ValueError:
    pass
else:
    raise AssertionError("invalid epoch accepted")
assert m.eligible(now=0.64)
assert m.heartbeat("left", epoch=2, sequence=0, ready=True, now=0.65)
assert not m.eligible(now=0.65)
assert not m.heartbeat("left", epoch=1, sequence=999, ready=True, now=0.66)
assert not m.eligible(now=0.66)
assert m.authorize(explicit=True, now=0.66)
print("PASS stale sequence and old epoch rejected; peer reboot revokes authorization")

assert m.heartbeat("right", epoch=1, sequence=2, ready=False, now=0.67)
assert not m.eligible(now=0.67)
assert m.heartbeat("right", epoch=1, sequence=3, ready=True, now=0.68)
assert not m.eligible(now=0.68)
assert m.authorize(explicit=True, now=0.68)
print("PASS one unready Forma revokes multi-unit eligibility")

m.restart_main()
assert not m.eligible(now=0.69)
assert m.heartbeat("left", epoch=2, sequence=1, ready=True, now=0.7)
assert m.heartbeat("right", epoch=1, sequence=4, ready=True, now=0.7)
assert not m.eligible(now=0.7)
assert m.authorize(explicit=True, now=0.7)
assert not m.status(now=0.7)["motor_command_issued"]
print("PASS Main restart requires new heartbeat observations and authorization")

for bad in (
    lambda: FormaLinkMonitor(("left", "left"), timeout=1),
    lambda: FormaLinkMonitor(("left",), timeout=0),
    lambda: m.heartbeat("left", epoch=True, sequence=2, ready=True, now=0.8),
    lambda: m.heartbeat("left", epoch=2, sequence=2, ready=True, now=float("nan")),
    lambda: m.authorize(explicit=1, now=0.8),
    lambda: m.eligible(now=0.6),
):
    try:
        bad()
    except ValueError:
        pass
    else:
        raise AssertionError("invalid input accepted")
print("PASS malformed inputs and backward clock rejected")
print("PASS all forma-heartbeat checks")
