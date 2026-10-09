from actions import PolicyActions
from observation_evidence import StopEvidenceVerifier

actions = PolicyActions()
action = actions.request({"event_id": 1}, "request_stop")
actions.transition(action["action_id"], "accepted")
actions.transition(action["action_id"], "executing")
actions.transition(action["action_id"], "completed", completion_report="stop reported")
verifier = StopEvidenceVerifier({"left", "right"})


def sample(t, **overrides):
    value = {"timestamp_s": t, "integrity_ok": True, "drive_disabled": True,
             "joint_velocities": {"left": 0.0, "right": 0.0}}
    value.update(overrides)
    return value


good = [sample(10.0), sample(10.3), sample(10.6)]
assert verifier.verify(action, good, 10.7)["status"] == "verified"
print("PASS fresh full-scope stable synthetic evidence is verified")

assert "stale_observation" in verifier.verify(action, good, 11.0)["reasons"]
assert "stability_window_short" in verifier.verify(action, [sample(10.5), sample(10.6)], 10.7)["reasons"]
print("PASS stale and insufficient-duration observations are unknown")

assert "scope_incomplete" in verifier.verify(
    action, [sample(10.0, joint_velocities={"left": 0.0}), sample(10.6)], 10.7)["reasons"]
assert "integrity_unconfirmed" in verifier.verify(
    action, [sample(10.0, integrity_ok=False), sample(10.6)], 10.7)["reasons"]
print("PASS missing joint coverage and untrusted evidence are unknown")

assert "timestamp_not_increasing" in verifier.verify(
    action, [sample(10.6), sample(10.0)], 10.7)["reasons"]
assert "future_or_invalid_timestamp" in verifier.verify(
    action, [sample(10.0), sample(10.8)], 10.7)["reasons"]
assert "velocity_invalid" in verifier.verify(
    action, [sample(10.0, joint_velocities={"left": float("nan"), "right": 0.0}), sample(10.6)], 10.7)["reasons"]
print("PASS malformed time ordering, future data, and invalid velocity are unknown")

moving = [sample(10.0), sample(10.3, joint_velocities={"left": 0.1, "right": 0.0}), sample(10.6)]
assert verifier.verify(action, moving, 10.7)["status"] == "not_verified"
enabled = [sample(10.0), sample(10.3, drive_disabled=False), sample(10.6)]
assert verifier.verify(action, enabled, 10.7)["status"] == "not_verified"
print("PASS movement or enabled drive anywhere in evidence window is not_verified")

unfinished = actions.request({"event_id": 2}, "request_stop")
assert verifier.verify(unfinished, good, 10.7)["status"] == "unknown"
print("PASS action completion remains required")
print("PASS all observation-evidence checks")
