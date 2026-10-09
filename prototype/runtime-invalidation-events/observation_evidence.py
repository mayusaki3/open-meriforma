"""Synthetic STOP observation evidence: freshness, scope, integrity and duration.

All timestamps are caller-supplied monotonic seconds. Integrity is a simulated
upstream flag, not cryptographic authentication or sensor fault detection.
"""
import math


class StopEvidenceVerifier:
    def __init__(self, required_joints: set[str], *,
                 max_age_s: float = 0.2, min_stable_s: float = 0.5,
                 max_velocity: float = 0.01):
        if not required_joints or any(not isinstance(j, str) or not j for j in required_joints):
            raise ValueError("required_joints must be nonempty valid IDs")
        if not all(math.isfinite(x) and x >= 0 for x in (max_age_s, min_stable_s, max_velocity)):
            raise ValueError("invalid thresholds")
        self.required_joints = frozenset(required_joints)
        self.max_age_s = max_age_s
        self.min_stable_s = min_stable_s
        self.max_velocity = max_velocity

    def verify(self, action: dict, samples: list[dict], now_s: float) -> dict:
        if action["kind"] != "request_stop":
            raise ValueError("only STOP actions supported")
        reasons = []
        if action["state"] != "completed":
            reasons.append("action_not_completed")
        if not isinstance(now_s, (int, float)) or not math.isfinite(now_s):
            reasons.append("invalid_clock")
        if not samples:
            reasons.append("observation_missing")
        timestamps = []
        for sample in samples:
            ts = sample.get("timestamp_s")
            velocities = sample.get("joint_velocities")
            if not isinstance(ts, (int, float)) or not math.isfinite(ts):
                reasons.append("invalid_timestamp")
                continue
            timestamps.append(ts)
            if not isinstance(now_s, (int, float)) or not math.isfinite(now_s) or ts > now_s:
                reasons.append("future_or_invalid_timestamp")
            if sample.get("integrity_ok") is not True:
                reasons.append("integrity_unconfirmed")
            if type(sample.get("drive_disabled")) is not bool:
                reasons.append("drive_state_unknown")
            if not isinstance(velocities, dict) or not self.required_joints.issubset(velocities):
                reasons.append("scope_incomplete")
            elif any(type(velocities[j]) not in (float, int) or not math.isfinite(velocities[j])
                     for j in self.required_joints):
                reasons.append("velocity_invalid")
        if timestamps:
            if any(b <= a for a, b in zip(timestamps, timestamps[1:])):
                reasons.append("timestamp_not_increasing")
            if isinstance(now_s, (int, float)) and math.isfinite(now_s):
                if now_s - timestamps[-1] > self.max_age_s:
                    reasons.append("stale_observation")
            if timestamps[-1] - timestamps[0] < self.min_stable_s:
                reasons.append("stability_window_short")
        if reasons:
            return {"status": "unknown", "reasons": sorted(set(reasons))}
        unsafe = []
        for sample in samples:
            if sample["drive_disabled"] is False:
                unsafe.append("drive_enabled")
            if any(abs(sample["joint_velocities"][j]) > self.max_velocity
                   for j in self.required_joints):
                unsafe.append("joint_moving")
        if unsafe:
            return {"status": "not_verified", "reasons": sorted(set(unsafe))}
        return {"status": "verified", "reasons": []}
