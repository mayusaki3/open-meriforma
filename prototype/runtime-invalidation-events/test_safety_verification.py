from actions import PolicyActions
from safety_verification import StopVerifier


def completed(actions, event_id):
    action = actions.request({"event_id": event_id}, "request_stop")
    actions.transition(action["action_id"], "accepted")
    actions.transition(action["action_id"], "executing")
    actions.transition(action["action_id"], "completed", completion_report="executor reported stop")
    return action


actions = PolicyActions()
verifier = StopVerifier()
stopped = completed(actions, 1)
assert verifier.verify(stopped, {"drive_disabled": True, "joint_velocities": [0.0, 0.005]})["status"] == "verified"
assert stopped["state"] == "completed"
print("PASS synthetic complete stop evidence is verified separately from action completion")

moving = completed(actions, 2)
result = verifier.verify(moving, {"drive_disabled": True, "joint_velocities": [0.0, 0.1]})
assert result["status"] == "not_verified" and "joint_moving" in result["reasons"]
enabled = completed(actions, 3)
result = verifier.verify(enabled, {"drive_disabled": False, "joint_velocities": [0.0]})
assert result["status"] == "not_verified" and "drive_enabled" in result["reasons"]
print("PASS completed action with unsafe observations is not verified")

missing = completed(actions, 4)
assert verifier.verify(missing, None)["status"] == "unknown"
incomplete = completed(actions, 5)
assert verifier.verify(incomplete, {"drive_disabled": True, "joint_velocities": []})["status"] == "unknown"
invalid = completed(actions, 6)
assert verifier.verify(invalid, {"drive_disabled": True, "joint_velocities": [float("nan")]})["status"] == "unknown"
print("PASS missing, incomplete, and invalid evidence fail closed as unknown")

pending = actions.request({"event_id": 7}, "request_stop")
assert verifier.verify(pending, {"drive_disabled": True, "joint_velocities": [0.0]})["status"] == "unknown"
print("PASS observations alone cannot verify an unfinished action")

try:
    verifier.verify(stopped, {"drive_disabled": True, "joint_velocities": [0.0]})
except RuntimeError:
    pass
else:
    raise AssertionError("verification overwritten")
handoff = actions.request({"event_id": 8}, "request_handoff")
try:
    verifier.verify(handoff, {"drive_disabled": True, "joint_velocities": [0.0]})
except ValueError:
    pass
else:
    raise AssertionError("handoff incorrectly accepted as STOP")
print("PASS verification result is not silently overwritten or applied to handoff")

assert all(action["state"] == "completed" for action in [stopped, moving, enabled, missing, incomplete, invalid])
assert verifier.results[moving["action_id"]]["status"] == "not_verified"
print("PASS action lifecycle and verification state remain independent")
print("PASS all safety-state-verification checks")
