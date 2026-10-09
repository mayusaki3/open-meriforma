"""Synthetic STOP evidence verification, not physical safety certification."""


class StopVerifier:
    """Assess a completed STOP action from an explicit observation snapshot.

    The prototype threshold is illustrative, not a safety standard.
    """

    def __init__(self, max_abs_velocity: float = 0.01) -> None:
        if max_abs_velocity < 0:
            raise ValueError("negative velocity threshold")
        self.max_abs_velocity = max_abs_velocity
        self.results: dict[int, dict] = {}

    def verify(self, action: dict, observation: dict | None) -> dict:
        if action["kind"] != "request_stop":
            raise ValueError("only STOP actions supported")
        action_id = action["action_id"]
        if action_id in self.results:
            raise RuntimeError("verification already recorded for action")
        reasons = []
        if action["state"] != "completed":
            status = "unknown"
            reasons.append("action_not_completed")
        elif observation is None:
            status = "unknown"
            reasons.append("observation_missing")
        elif (not isinstance(observation.get("drive_disabled"), bool)
              or not isinstance(observation.get("joint_velocities"), list)
              or not observation["joint_velocities"]
              or any(type(v) not in (float, int) or not (-float("inf") < v < float("inf"))
                     for v in observation["joint_velocities"])):
            status = "unknown"
            reasons.append("observation_incomplete_or_invalid")
        elif observation["drive_disabled"] is False or any(
            abs(v) > self.max_abs_velocity for v in observation["joint_velocities"]
        ):
            status = "not_verified"
            if observation["drive_disabled"] is False:
                reasons.append("drive_enabled")
            if any(abs(v) > self.max_abs_velocity for v in observation["joint_velocities"]):
                reasons.append("joint_moving")
        else:
            status = "verified"
        result = {
            "action_id": action_id,
            "status": status,
            "reasons": reasons,
            "evidence_type": "synthetic_snapshot",
        }
        self.results[action_id] = result
        return result
