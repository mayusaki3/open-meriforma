from __future__ import annotations

import json
import math
from pathlib import Path

from runtime import VirtualUnitRuntime

ROOT = Path(__file__).resolve().parent
UNIT_PATH = ROOT / "unit.json"


def load_definition() -> dict:
    with UNIT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_ownership_conflict() -> None:
    runtime = VirtualUnitRuntime(load_definition())
    runtime.activate("coordinated_motion")

    try:
        runtime.ownership.acquire("intruder_controller", ["joint_a"])
    except RuntimeError as exc:
        print(f"PASS ownership conflict rejected: {exc}")
        return

    raise AssertionError("ownership conflict was not rejected")


def test_constraint_limit() -> None:
    runtime = VirtualUnitRuntime(load_definition())

    target = math.radians(120.0)
    limited, hit = runtime.constraints.clamp_target("joint_a", target)

    assert hit, "out-of-range target was not detected"
    assert math.isclose(math.degrees(limited), 80.0, abs_tol=1e-9)
    print(
        "PASS constraint detected: "
        f"joint_a requested=120.0 deg limited={math.degrees(limited):.1f} deg"
    )


def test_valid_target_unchanged() -> None:
    runtime = VirtualUnitRuntime(load_definition())

    target = math.radians(55.0)
    limited, hit = runtime.constraints.clamp_target("joint_a", target)

    assert not hit, "valid target was incorrectly limited"
    assert math.isclose(limited, target, abs_tol=1e-12)
    print("PASS valid target unchanged: joint_a requested=55.0 deg")


def main() -> None:
    test_ownership_conflict()
    test_constraint_limit()
    test_valid_target_unchanged()
    print("PASS all runtime checks")


if __name__ == "__main__":
    main()
