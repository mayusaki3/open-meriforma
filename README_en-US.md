[日本語](./README.md) | [English](./README_en-US.md)

# Open MeriForma

**An open, modular Physical AI robot platform**

Open MeriForma is an open-source hardware project for a small humanoid / doll-scale robot intended to work with the Meridian Project.

The name **MeriForma** combines *Meri(dian)* and *Forma*: a physical form or body taken by Meridian.

Rather than defining a single finished robot, the project aims to provide a platform whose body can be built, repaired, modified, and reconfigured by combining interchangeable modules.

---

## Project Goals

- Open-source hardware
- Primarily manufacturable with 3D printing
- Low-cost and accessible to individual builders
- Modular and repairable body structure
- Replaceable actuators, joints, sensors, shells, hands, feet, and other modules
- Independent sensing of actual joint state where practical
- Multiple body and mobility configurations
- AI interaction through conversation, expression, gestures, and movement
- Learning and adaptation to individual hardware and aging
- Health monitoring to assist maintenance and part replacement
- Independent real-time safety protection

---

## Modular Body

Open MeriForma does not assume one fixed body configuration.

Possible modules include:

- simple, display-based, or mechanically expressive heads
- fixed, simple, or five-finger hands
- standard or advanced legs
- normal feet or deployable wheeled feet
- normal hands or wheeled hands

High-function configurations may explore gear-driven differential fingers, scapula-like shoulder motion, articulated toes, mechanical facial expressions, and deployable wheels.

The project favors separating load-bearing joint mechanisms from replaceable drive actuators so that maintenance and actuator changes do not require redesigning the entire limb.

---

## Multiple Forms of Mobility

Mobility is determined by the capabilities provided by the currently installed body modules rather than by a fixed robot classification.

Examples include:

- biped walking
- crawling using the hands and feet as four support limbs
- two-wheel mobility using deployable foot wheels
- four-wheel mobility using wheeled hands and feet
- combinations of walking and wheeled movement

The AI can select an appropriate method according to available capabilities, body Health, environment, stability, and intended behavior.

---

## AI and Behavior

AI is used for more than learning.

Its intended roles include:

- conversation with people
- perception of people and surroundings
- reactions and expressive behavior
- selection of gestures and movement
- behavior planning based on the current body configuration and condition
- learning and adaptation
- interpretation and presentation of robot Health

High-level intent is separated from concrete joint motion.

For example, when the intended behavior is to wave goodbye, the robot should not be tied to always using a particular arm. If one arm is unavailable or degraded, it can use the healthier arm or choose another expression such as a bow or spoken farewell.

---

## Learning and Adaptation

Learning may be performed using:

- the physical robot
- simulation
- a combination of both

MuJoCo is currently envisioned as the simulation environment.

Learning results should be converted into forms that can run on the real-time robot controller, such as:

- equations and control parameters
- motions
- motion corrections
- expected sensor feedback
- expected operating ranges
- state and correction logic

The large AI model is therefore not required to directly control every joint in real time.

When actual behavior frequently leaves the learned expected range, the robot reports the deviation to the human operator. If the operator accepts the changed condition, the robot can relearn and adapt its expected behavior.

This allows adaptation to component variation, sensor drift, actuator aging, replacement parts, and configuration changes.

---

## Health and Maintenance

Relearning must not erase the historical reference state.

Open MeriForma aims to retain the baseline, current learned state, and learning history so that aging and other changes remain observable even when the controller has adapted to them.

Deviation from the reference state can be visualized by body part, for example using colors. This information can help a human decide when inspection or component replacement is appropriate.

Health information can also influence behavior. A degraded but still usable limb may be avoided when a healthier alternative is available.

---

## Safety

Immediate safety protection is independent from adaptive learning and high-level AI behavior.

Examples include:

- overcurrent protection
- overtemperature protection
- fall prevention / fall-risk handling
- other conditions requiring immediate restriction or shutdown

Adaptive learning must not automatically expand these safety limits.

---

## Architecture Principle

Open MeriForma combines:

**an interchangeable body**

with

**AI that observes, learns, understands, and acts according to that body's current capabilities and condition.**

The goal is a repairable and modifiable Physical AI platform that can adapt to component changes and aging while continuing to interact naturally with people.

---

## Documentation

- [Documentation Table of Contents (Japanese)](./docs/ja-JP/目次.md)

English technical documentation will be added as the project structure develops.

---

## Project Status

Open MeriForma is currently in the concept and requirements-definition stage.

Specific actuator models, degrees of freedom, joint mechanisms, sensor models, Health formulas, learning algorithms, and module interfaces are not yet fixed.

These will be evaluated individually without unnecessarily constraining the basic principles described above.

---

## License

The project license has not yet been finalized.
