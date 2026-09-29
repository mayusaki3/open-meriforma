from __future__ import annotations

import json
from pathlib import Path

from runtime import VirtualUnitRuntime

ROOT = Path(__file__).resolve().parent
definition = json.loads((ROOT / "unit.json").read_text(encoding="utf-8"))

runtime = VirtualUnitRuntime(definition)
runtime.activate("support")
runtime.activate("toe_grip")

assert runtime.active_groups == {"support", "toe_grip"}
assert runtime.ownership.owners["ankle_pitch"] == "support_controller"
assert runtime.ownership.owners["toe_left"] == "toe_grip_controller"
print("PASS support + toe_grip concurrent activation")
print(f"     owner=[{runtime.owner_summary()}]")

try:
    runtime.activate("foot_motion")
except RuntimeError as exc:
    print(f"PASS conflicting foot_motion rejected: {exc}")
else:
    raise AssertionError("foot_motion conflict was not rejected")

runtime.deactivate("toe_grip")
assert "support" in runtime.active_groups
assert "toe_left" not in runtime.ownership.owners
print("PASS partial group release keeps support active")

runtime.deactivate("support")
runtime.activate("foot_motion")
assert runtime.active_groups == {"foot_motion"}
print("PASS foot_motion activates after resources are released")
print("PASS all virtual-foot runtime checks")
