from __future__ import annotations

import json
import math
import time
from pathlib import Path

import mujoco
import mujoco.viewer

from runtime import VirtualUnitRuntime

ROOT = Path(__file__).resolve().parent
UNIT_PATH = ROOT / "unit.json"
MODEL_PATH = ROOT / "model.xml"


def load_unit_definition() -> dict:
    with UNIT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def require_id(model: mujoco.MjModel, obj_type: mujoco.mjtObj, name: str) -> int:
    obj_id = mujoco.mj_name2id(model, obj_type, name)
    if obj_id < 0:
        raise RuntimeError(f"MuJoCo object not found: {name}")
    return obj_id


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def main() -> None:
    unit = load_unit_definition()
    runtime = VirtualUnitRuntime(unit)
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)

    mappings = {
        name: element["mapping"]
        for name, element in unit["elements"].items()
        if "mapping" in element
    }

    actuator_a_id = require_id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, mappings["joint_a"]["mujoco_actuator"]
    )
    actuator_b_id = require_id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, mappings["joint_b"]["mujoco_actuator"]
    )
    joint_a_id = require_id(
        model, mujoco.mjtObj.mjOBJ_JOINT, mappings["joint_a"]["mujoco_joint"]
    )
    joint_b_id = require_id(
        model, mujoco.mjtObj.mjOBJ_JOINT, mappings["joint_b"]["mujoco_joint"]
    )
    light_site_id = require_id(
        model, mujoco.mjtObj.mjOBJ_SITE, mappings["indicator_light"]["mujoco_site"]
    )

    qpos_a = model.jnt_qposadr[joint_a_id]
    qpos_b = model.jnt_qposadr[joint_b_id]

    mode_duration = 4.0
    transition_duration = 1.0
    cycle_duration = mode_duration * 2 + transition_duration * 2

    previous_mode = None
    transition_start_a = 0.0
    transition_start_b = 0.0
    constraint_hits = 0

    print(f"Definition : {unit['definition_id']}")
    print("Runtime    : explicit resource ownership + constraints")
    print("Clock      : MuJoCo simulation time")
    print("Close the MuJoCo viewer to stop.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        last_report = -1

        while viewer.is_running():
            frame_start = time.monotonic()
            elapsed = data.time
            phase = elapsed % cycle_duration

            if phase < mode_duration:
                mode = "coordinated"
            elif phase < mode_duration + transition_duration:
                mode = "transition_to_independent"
            elif phase < mode_duration * 2 + transition_duration:
                mode = "joint_a_independent"
            else:
                mode = "transition_to_coordinated"

            if mode != previous_mode:
                if mode.startswith("transition_"):
                    transition_start_a = data.qpos[qpos_a]
                    transition_start_b = data.qpos[qpos_b]
                    runtime.deactivate()
                elif mode == "coordinated":
                    runtime.activate("coordinated_motion")
                elif mode == "joint_a_independent":
                    runtime.activate("joint_a_independent")
                previous_mode = mode

            if mode == "coordinated":
                t = phase
                target_a = math.radians(35.0) * math.sin(t * 1.3)
                target_b = math.radians(50.0) * math.sin(t * 1.3)
                model.site_rgba[light_site_id] = (0.2, 0.8, 0.25, 1.0)

            elif mode == "transition_to_independent":
                blend = smoothstep((phase - mode_duration) / transition_duration)
                target_a = transition_start_a * (1.0 - blend)
                target_b = transition_start_b * (1.0 - blend)
                model.site_rgba[light_site_id] = (0.9, 0.65, 0.1, 1.0)

            elif mode == "joint_a_independent":
                t = phase - mode_duration - transition_duration
                target_a = math.radians(55.0) * math.sin(t * 1.8)
                target_b = 0.0
                model.site_rgba[light_site_id] = (0.2, 0.45, 1.0, 1.0)

            else:
                blend = smoothstep(
                    (phase - (mode_duration * 2 + transition_duration))
                    / transition_duration
                )
                target_a = transition_start_a * (1.0 - blend)
                target_b = transition_start_b * (1.0 - blend)
                model.site_rgba[light_site_id] = (0.9, 0.65, 0.1, 1.0)

            target_a, limited_a = runtime.constraints.clamp_target("joint_a", target_a)
            target_b, limited_b = runtime.constraints.clamp_target("joint_b", target_b)
            if limited_a or limited_b:
                constraint_hits += 1

            data.ctrl[actuator_a_id] = target_a
            data.ctrl[actuator_b_id] = target_b

            mujoco.mj_step(model, data)
            viewer.sync()

            report_second = int(elapsed)
            if report_second != last_report:
                last_report = report_second
                print(
                    f"{elapsed:6.1f}s  {mode:28s} "
                    f"A={math.degrees(data.qpos[qpos_a]):7.2f} deg "
                    f"B={math.degrees(data.qpos[qpos_b]):7.2f} deg "
                    f"owner=[{runtime.owner_summary()}] "
                    f"constraint_hits={constraint_hits}"
                )

            remaining = model.opt.timestep - (time.monotonic() - frame_start)
            if remaining > 0:
                time.sleep(remaining)


if __name__ == "__main__":
    main()
