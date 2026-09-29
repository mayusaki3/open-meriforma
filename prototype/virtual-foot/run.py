from __future__ import annotations

import json
import math
import time
from pathlib import Path

import mujoco
import mujoco.viewer

from runtime import VirtualUnitRuntime

ROOT = Path(__file__).resolve().parent


def require_id(model, kind, name):
    result = mujoco.mj_name2id(model, kind, name)
    if result < 0:
        raise RuntimeError(f"MuJoCo object not found: {name}")
    return result


def main():
    unit = json.loads((ROOT / "unit.json").read_text(encoding="utf-8"))
    runtime = VirtualUnitRuntime(unit)
    model = mujoco.MjModel.from_xml_path(str(ROOT / "model.xml"))
    data = mujoco.MjData(model)

    joints = {}
    actuators = {}
    joint_resources = ("ankle_pitch", "ankle_roll", "toe_left", "toe_right")
    for name in joint_resources:
        mapping = unit["elements"][name]["mapping"]
        jid = require_id(model, mujoco.mjtObj.mjOBJ_JOINT, mapping["mujoco_joint"])
        aid = require_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, mapping["mujoco_actuator"])
        joints[name] = model.jnt_qposadr[jid]
        actuators[name] = aid

    light = require_id(
        model, mujoco.mjtObj.mjOBJ_SITE,
        unit["elements"]["indicator_light"]["mapping"]["mujoco_site"]
    )
    sensor = require_id(
        model, mujoco.mjtObj.mjOBJ_SENSOR,
        unit["elements"]["sole_contact"]["mapping"]["mujoco_sensor"]
    )
    sensor_adr = model.sensor_adr[sensor]

    previous_phase = None
    last_report = -1
    transition_owner = "transition_controller"

    print(f"Definition : {unit['definition_id']}")
    print("Scenario   : support -> support + toe_grip -> handoff -> foot_motion -> handoff")
    print("Clock      : MuJoCo simulation time")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            frame_start = time.monotonic()
            t = data.time
            phase_time = t % 14.0

            if phase_time < 4.0:
                phase = "support"
            elif phase_time < 8.0:
                phase = "support+toe_grip"
            elif phase_time < 9.0:
                phase = "handoff_to_foot_motion"
            elif phase_time < 13.0:
                phase = "foot_motion"
            else:
                phase = "handoff_to_support"

            if phase != previous_phase:
                if phase == "support":
                    if previous_phase == "handoff_to_support":
                        runtime.ownership.release_resources(transition_owner, joint_resources)
                    runtime.deactivate_all()
                    runtime.activate("support")

                elif phase == "support+toe_grip":
                    # Preserve support ownership; only add the disjoint toe resources.
                    runtime.activate("toe_grip")

                elif phase == "handoff_to_foot_motion":
                    # Transfer currently controlled resources to a temporary handoff owner.
                    runtime.ownership.transfer(
                        unit["functional_groups"]["support"]["owner"],
                        transition_owner,
                        ["ankle_pitch", "ankle_roll"],
                    )
                    runtime.ownership.transfer(
                        unit["functional_groups"]["toe_grip"]["owner"],
                        transition_owner,
                        ["toe_left", "toe_right"],
                    )
                    runtime.relinquish_group_control("support")
                    runtime.relinquish_group_control("toe_grip")

                elif phase == "foot_motion":
                    runtime.ownership.release_resources(transition_owner, joint_resources)
                    runtime.activate("foot_motion")

                elif phase == "handoff_to_support":
                    runtime.ownership.transfer(
                        unit["functional_groups"]["foot_motion"]["owner"],
                        transition_owner,
                        list(joint_resources),
                    )
                    runtime.relinquish_group_control("foot_motion")

                previous_phase = phase

            if phase == "support":
                data.ctrl[actuators["ankle_pitch"]] = math.radians(6) * math.sin(t * 1.2)
                data.ctrl[actuators["ankle_roll"]] = math.radians(4) * math.sin(t * 0.9)
                data.ctrl[actuators["toe_left"]] = 0
                data.ctrl[actuators["toe_right"]] = 0
                model.site_rgba[light] = (0.2, 0.8, 0.25, 1)

            elif phase == "support+toe_grip":
                data.ctrl[actuators["ankle_pitch"]] = math.radians(5) * math.sin(t * 1.0)
                data.ctrl[actuators["ankle_roll"]] = math.radians(3) * math.sin(t * 0.8)
                grip = math.radians(35) * (0.5 + 0.5 * math.sin(t * 2.0))
                data.ctrl[actuators["toe_left"]] = grip
                data.ctrl[actuators["toe_right"]] = grip
                model.site_rgba[light] = (0.6, 0.3, 1.0, 1)

            elif phase.startswith("handoff_"):
                # Transition Controller owns every moving joint and drives it to
                # a known neutral handoff pose before the next controller starts.
                for aid in actuators.values():
                    data.ctrl[aid] = 0
                model.site_rgba[light] = (0.9, 0.65, 0.1, 1)

            else:
                data.ctrl[actuators["ankle_pitch"]] = math.radians(12) * math.sin(t * 1.3)
                data.ctrl[actuators["ankle_roll"]] = math.radians(8) * math.sin(t * 1.1)
                toe = math.radians(18) * (0.5 + 0.5 * math.sin(t * 1.7))
                data.ctrl[actuators["toe_left"]] = toe
                data.ctrl[actuators["toe_right"]] = toe
                model.site_rgba[light] = (0.2, 0.45, 1.0, 1)

            mujoco.mj_step(model, data)
            viewer.sync()

            contact_value = float(data.sensordata[sensor_adr])
            support_declared = bool(unit["capabilities"]["support"]["declared"])
            support_observable = "support" in runtime.observers.get("sole_contact", set())
            support_available = (
                support_declared
                and support_observable
                and contact_value > 0.001
            )

            second = int(t)
            if second != last_report:
                last_report = second
                print(
                    f"{t:6.1f}s {phase:22s} "
                    f"pitch={math.degrees(data.qpos[joints['ankle_pitch']]):6.2f} "
                    f"roll={math.degrees(data.qpos[joints['ankle_roll']]):6.2f} "
                    f"toeL={math.degrees(data.qpos[joints['toe_left']]):6.2f} "
                    f"toeR={math.degrees(data.qpos[joints['toe_right']]):6.2f} "
                    f"contact={contact_value:.3f} "
                    f"support=declared:{str(support_declared).lower()}"
                    f"/observable:{str(support_observable).lower()}"
                    f"/available:{str(support_available).lower()} "
                    f"owner=[{runtime.owner_summary()}] "
                    f"observe=[{runtime.observation_summary()}]"
                )

            remaining = model.opt.timestep - (time.monotonic() - frame_start)
            if remaining > 0:
                time.sleep(remaining)


if __name__ == "__main__":
    main()
