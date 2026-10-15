"""Suite 38: synthetic causal ACK timing, loss, retry and timeout."""
from can_causal_roundtrip import simulate_roundtrips

normal = simulate_roundtrips(units=2, cycles=3)
assert normal["completed"] == 6 and normal["timed_out"] == 0
assert all(s["ack_generated"] >= 1 for s in normal["states"].values())
for event in normal["events"]:
    if event[0] == "ack_received":
        key = event[1]
        assert any(e[0] == "heartbeat_received" and e[1] == key and e[2] < event[2]
                   for e in normal["events"])
print("PASS ACK follows delivered heartbeat on shared airtime clock")

congested = simulate_roundtrips(units=24, cycles=2, period_ms=10,
                                deadline_ms=2, diagnostic_frames=20)
assert congested["timed_out"] > 0
assert congested["completed"] + congested["timed_out"] == congested["total"]
print("PASS congestion produces end-to-end deadline failures")

lost_heartbeat = simulate_roundtrips(units=1, cycles=1,
                                     drop_heartbeat={(0, 0)}, retry_once=False)
assert lost_heartbeat["completed"] == 0
assert lost_heartbeat["states"][(0, 0)]["ack_generated"] == 0
print("PASS missing heartbeat cannot cause an ACK")

lost_ack = simulate_roundtrips(units=1, cycles=1,
                               drop_ack={(0, 0)}, retry_once=False)
assert lost_ack["completed"] == 0
assert lost_ack["states"][(0, 0)]["ack_generated"] == 1
assert lost_ack["states"][(0, 0)]["ack_delivered"] == 0
print("PASS missing ACK cannot complete a roundtrip")

recovered = simulate_roundtrips(units=1, cycles=1, drop_ack={(0, 0)})
assert recovered["completed"] == 1 and recovered["retries"] == 1
assert recovered["states"][(0, 0)]["heartbeat_deliveries"] == 2
assert not recovered["motor_command_issued"] and not recovered["automatic_resume"]
print("PASS single retry completes without actuation or automatic authority")

late = simulate_roundtrips(units=1, cycles=1, ack_delay_ms=10,
                           deadline_ms=1)
assert late["timed_out"] == 1 and late["completed"] == 0
print("PASS ACK beyond end-to-end deadline is rejected")

for args in ({"units": 0}, {"heartbeat_bytes": 65},
             {"drop_ack": {(100, 0)}}, {"retry_once": 1}):
    try:
        simulate_roundtrips(**args)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid inputs accepted")
print("PASS invalid simulation configurations rejected")
print("PASS all can-causal-roundtrip checks")
