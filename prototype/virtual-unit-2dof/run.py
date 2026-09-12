from __future__ import annotations

import json
import math
import time
from pathlib import Path

import mujoco
import mujoco.viewer

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


def main() -> None:
    unit = load_unit_definition()
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)

    joint_a = unit["elements"]["joint_a"]["mapping"]
    joint_b = unit["elements"]["joint_b"]["mapping"]
    light = unit["elements"]["indicator_light"]["mapping"]

    actuator_a_id = require_id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, joint_a["mujoco_actuator"]
    )
    actuator_b_id = require_id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, joint_b["mujoco_actuator"]
    )
    joint_a_id = require_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_a["mujoco_joint"])
    joint_b_id = require_id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_b["mujoco_joint"])
    light_site_id = require_id(model, mujoco.mjtObj.mjOBJ_SITE, light["mujoco_site"])

    qpos_a = model.jnt_qposadr[joint_a_id]
    qpos_b = model.jnt_qposadr[joint_b_id]

    print(f"Definition : {unit['definition_id']}")
    print("Mode cycle : coordinated -> transition -> joint_a_independent")
    print("Close the MuJoCo viewer to stop.")

    mode_duration = 4.0
    transition_duration = 1.0
    cycle_duration = mode_duration * 2 + transition_duration * 2

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.monotonic()
        last_report = -1

        while viewer.is_running():
            frame_start = time.monotonic()
            elapsed = frame_start - start
            phase = elapsed % cycle_duration

            if phase < mode_duration:
                mode = "coordinated"
                t = phase
                data.ctrl[actuator_a_id] = math.radians(35.0) * math.sin(t * 1.3)
                data.ctrl[actuator_b_id] = math.radians(50.0) * math.sin(t * 1.3 + 0.8)
                model.site_rgba[light_site_id] = (0.2, 0.8, 0.25, 1.0)

            elif phase < mode_duration + transition_duration:
                mode = "transition_to_independent"
                data.ctrl[actuator_a_id] = data.qpos[qpos_a]
                data.ctrl[actuator_b_id] = data.qpos[qpos_b]
                model.site_rgba[light_site_id] = (0.9, 0.65, 0.1, 1.0)

            elif phase < mode_duration * 2 + transition_duration:
                mode = "joint_a_independent"
                t = phase - mode_duration - transition_duration
                data.ctrl[actuator_a_id] = math.radians(55.0) * math.sin(t * 1.8)
                data.ctrl[actuator_b_id] = 0.0
                model.site_rgba[light_site_id] = (0.2, 0.45, 1.0, 1.0)

            else:
                mode = "transition_to_coordinated"
                data.ctrl[actuator_a_id] = data.qpos[qpos_a]
                data.ctrl[actuator_b_id] = data.qpos[qpos_b]
                model.site_rgba[light_site_id] = (0.9, 0.65, 0.1, 1.0)

            mujoco.mj_step(model, data)
            viewer.sync()

            report_second = int(elapsed)
            if report_second != last_report:
                last_report = report_second
                print(
                    f"{elapsed:6.1f}s  {mode:28s} "
                    f"A={math.degrees(data.qpos[qpos_a]):7.2f} deg "
                    f"B={math.degrees(data.qpos[qpos_b]):7.2f} deg"
                )

            remaining = model.opt.timestep - (time.monotonic() - frame_start)
            if remaining > 0:
                time.sleep(remaining)


if __name__ == "__main__":
    main()
