"""66-H deterministic delay/loss/reorder checks."""
from forma_maintenance_state import FormaMaintenanceState
from forma_safety_policy import FormaSafetyPolicy
from forma_concurrent_operations import FormaConcurrentOperations
from forma_receiver_integration import FormaReceiverIntegration
from forma_transport_boundary import FormaTransportBoundary
from forma_timed_recovery import FormaTimedRecovery
from forma_packet_simulator import FormaPacketSimulator

def make(fid, gen="g1"):
    state = FormaMaintenanceState(fid, gen)
    policy = FormaSafetyPolicy(actuators={"thumb": {"position": (0, 20)}},
                               clearance_conditions=("guard",))
    return FormaConcurrentOperations(state, policy, costs={"thumb": 1}, max_load=2)

scope = dict(actuator="thumb", control_mode="position", minimum=0, maximum=10)
left, right = make("left"), make("right")
r = FormaReceiverIntegration({"left": left, "right": right})
t = FormaTimedRecovery(FormaTransportBoundary(r), timeout=5)
s = FormaPacketSimulator(t)
assert t.connect("left", "g1") and t.connect("right", "g1")
assert r.enter_maintenance("left") and left.approve_clearance({"guard": True})
def send(at, seq, kind="heartbeat", fid="left", **kw):
    return s.send(arrival=at, forma_id=fid, generation="g1",
                  sequence=seq, kind=kind, **kw)
assert send(1, 1) and s.advance(1) and s.results[-1] == (1, True)
print("PASS 66-H-01 timely heartbeat accepted")
assert send(2, 3) and send(3, 2) and s.advance(3)
assert s.results[-2:] == [(3, True), (2, False)]
print("PASS 66-H-02 reordered old sequence rejected")
assert send(4, 3) and s.advance(4) and s.results[-1] == (3, False)
print("PASS 66-H-03 duplicate sequence rejected")
assert send(4, 4, kind="request", request_id="auth", action="authorize",
            operation_id="op", scope=scope)
assert s.advance(4) and s.results[-1] == (4, True)
print("PASS 66-H-04 request routed on arrival")
assert send(4, 5, kind="request", request_id="start", action="start",
            operation_id="op", scope=scope)
assert s.advance(4) and s.results[-1] == (5, True)
print("PASS 66-H-05 operation starts through packet model")
assert send(5, 6, lost=True) and s.advance(5)
assert not left.halted
print("PASS 66-H-06 lost heartbeat does not extend deadline")
assert send(9, 7) and s.advance(9)
assert left.halted and s.results[-1] == (7, False)
print("PASS 66-H-07 packet arriving at timeout boundary cannot revive")
assert not left.active and not left.guard.operations.grants
print("PASS 66-H-08 timeout revokes active and pending grants")
assert send(10, 8) and s.advance(10) and s.results[-1] == (8, False)
print("PASS 66-H-09 delayed packet after timeout rejected")
assert send(11, 9, kind="request", request_id="late", action="authorize",
            operation_id="late", scope=scope)
assert s.advance(11) and s.results[-1] == (9, False)
print("PASS 66-H-10 late request cannot reauthorize")
assert send(12, 1, fid="right") and s.advance(12)
assert right.halted and s.results[-1] == (1, False)
print("PASS 66-H-11 independent Forma times out without heartbeat")
assert not s.advance(10) and not send(float("nan"), 10)
print("PASS 66-H-12 invalid and regressive times rejected")
assert not send(13, True) and not send(13, -1)
print("PASS 66-H-13 invalid sequence rejected")
assert not s.send(arrival=13, forma_id="left", generation="g1",
                  sequence=10, kind="bogus")
print("PASS 66-H-14 invalid packet kind rejected")
print("PASS all 14 suite 66-H synthetic checks")
