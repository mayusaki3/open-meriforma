Open MeriForma > Runtime Invalidation Events > Suite 66-L > Motor Channel Design

# Suite 66-L — Per-Forma motor channel descriptor (design proposal)

Status: PER-LOOP OWNERSHIP, EXPLICIT DISABLED, AND COMMAND-CAPABILITY VALIDATION POLICIES APPROVED (2026-11-05); detailed compatibility matrix and test expectations remain PROPOSALS. No implementation or test PASS.
Parent: FORMA_MCU_SELECTION_REQUIREMENTS.md. Not a formal HLDocS v0.6.1 specification.

## 1. Scope and boundaries

Each Forma declares its own channel count and may combine:
- A: Forma MCU closes relevant motor-control loops and commands a power stage.
- B: Forma MCU delegates explicitly supported low-level control to a driver/controller IC.
- No particular motor, encoder, driver IC, pin assignment, control period, power rail or channel count is selected.
- Both paths remain subject to the Forma-local operation authority, external watchdog K2 and physically verified inhibit. Driver communication success never counts as physical stop feedback.

## 2. Proposed logical channel descriptor

| Field | Type / meaning | Constraint |
| --- | --- | --- |
| forma_type_id | stable Forma hardware type | versioned; no inferred defaults |
| descriptor_version | configuration schema revision | reject unsupported version |
| channel_id | stable channel-local identifier | unique within Forma |
| control_mode | A_DIRECT or B_DRIVER_ASSISTED | explicit per channel |
| actuator_kind | brushed DC, BLDC, stepper, servo, etc. | supported capability only; examples not selections |
| command_capabilities | supported duty/current/velocity/position/torque requests | strict allowlist; not all drivers implement all |
| control_loop_owner | `FORMA_MCU`, `DRIVER_IC`, or `DISABLED`, **independently for current, velocity and position loops** | approved policy; all three keys required, no implicit default; reject unsupported/conflicting ownership |
| pwm_timer_resources | timer outputs, complementary PWM, dead-time if needed | required only for actual chosen power stage |
| feedback_resources | ADC current, encoder, Hall, absolute position, temperature, fault | state source, rate, resolution and fault validity |
| driver_interface | PWM/GPIO, SPI, I2C, UART, other local interface | physical pin mapping separately verified |
| update_periods | control/feedback/supervision deadlines | derived from plant and worst-case execution; no default numbers |
| electrical_limits | supply/current/temperature bounds | hardware ratings and verified limits |
| mechanical_limits | travel, velocity, torque, interference and load bounds | hardware- and application-specific |
| inhibit_route | electrical stop path and its default-off behavior | independent external watchdog/latch path required |
| stop_feedback | observable physical/electrical stop evidence | distinguish enable feedback from actual motor/joint state |
| recovery_policy_ref | operator/service recovery rules | stop latch not cleared by reconnect |
| descriptor_integrity | authenticated/verified configuration binding | reject invalid, mismatched or rollback-prone descriptors |

**Resource accounting rule:** compute pin/timer/ADC/DMA/interrupt/memory budgets from each channel's actual capabilities; do not assume B uses zero MCU resources or A uses a fixed number of PWM channels. Validate collisions across all channels, CAN-FD, external watchdog and security pins.

## 3. Proposed initialization and runtime gates
1. Start in drive-inhibited state; verify authenticated descriptor version, Forma identity and hardware compatibility.
2. Reject duplicate channel IDs, impossible pin mux, missing required feedback, incompatible driver capability or resource overcommit; do not partially arm an invalid Forma.
3. Require authenticated communication session and applicable normal-group or maintenance authorization.
4. For each operation, verify channel-specific limits, concurrency and fresh scoped grant; maintain continuous monitoring while active.
5. For either A or B, any timeout, watchdog failure, driver fault or invalid safety evidence must trigger the appropriate local stop policy. If isolation cannot be proved, stop the Forma.
6. Do not re-enable drives solely due to reconnect, firmware restart, descriptor reload or cleared protocol error.

## 4. Test-case proposal (NOT implemented)

| Test ID | Test intent | Expected result |
| --- | --- | --- |
| 66-L-CH-001 | Forma with A-only channels | Valid compatible descriptor accepted, resources counted |
| 66-L-CH-002 | Forma with B-only channels | Supported delegated capabilities accepted, MCU interface resources counted |
| 66-L-CH-003 | Mixed A+B channels | Both modes independently validated under shared resource budget |
| 66-L-CH-004 | Duplicate channel ID | Descriptor rejected; drive remains inhibited |
| 66-L-CH-005 | Conflicting timer/pin/DMA assignment | Descriptor rejected; drive remains inhibited |
| 66-L-CH-006 | B driver lacks requested control loop | Command rejected; no silent fallback |
| 66-L-CH-007 | Missing required feedback | Operation rejected or stopped according to local fault policy |
| 66-L-CH-008 | A/B channel fault during simultaneous operations | Isolate only with demonstrated safety independence; otherwise stop Forma |
| 66-L-CH-009 | Invalid descriptor signature/version or Forma mismatch | Descriptor rejected, no drive rearm |
| 66-L-CH-010 | Reboot or link recovery | Grants not restored; external inhibit remains engaged |
| 66-L-CH-011 | Hardware watchdog timeout under stalled MCU | External inhibit engages (requires instrumented hardware test) |
| 66-L-CH-012 | Inhibit command vs actual physical stop | Protocol ACK alone never reported as physical stop (hardware feedback test) |
| 66-L-CH-013 | Explicitly DISABLED loop | Descriptor accepted only if requested command capabilities remain compatible; disabled loop receives no control request |
| 66-L-CH-014 | Missing loop-owner field | Descriptor rejected; omission never defaults to DISABLED |
| 66-L-CH-015 | Command targets DISABLED loop | Command rejected; no implicit fallback or drive enable |
| 66-L-CH-016 | Position command with position loop DISABLED | Descriptor command capability rejected, and runtime position request rejected |
| 66-L-CH-017 | Declared command capability exceeds driver or feedback support | Descriptor rejected before arming |
| 66-L-CH-018 | Current loop DISABLED with independent verified drive/protection mechanism | Accept only when the chosen hardware provides documented compatible drive and protection; otherwise reject |

Unit-test coverage target: 100% of specified descriptor-validation branches, with separate instrumented integration and fault-injection evidence for electrical/mechanical stop. Test numbers are proposed, not PASS claims.

## 5. Approved decisions and next design gate

**Approved 2026-11-05:** Within each Forma, A/B control modes may differ per channel. Each channel independently declares ownership of its **current, velocity and position** control loops as Forma MCU or driver/controller IC, limited to the actual verified hardware capabilities. Mixed ownership within one channel is permitted (e.g., driver current loop, Forma MCU velocity and position loops). An unsupported, missing, ambiguous or conflicting loop owner must be rejected, without silent fallback or drive arming. No specific loop rates, motor counts, MCU or driver IC are approved.

**Approved 2026-11-05:** An intentionally unused current, velocity or position loop is explicitly declared `DISABLED`. All three loop-owner fields must be present; an omitted field is an invalid descriptor, not an alias for `DISABLED`. A disabled loop must not accept a command for that control mode. A hardware driver may still implement internal protection or regulation not exposed as a selectable application control loop; this must be documented separately and must never bypass Forma safety checks.

**Approved 2026-11-05:** Every exposed command mode must have explicitly declared and verified supporting control capability. A command requiring a disabled or unsupported control loop is invalid at descriptor validation and must also be rejected at runtime. For example, a position command requires an enabled position loop. No implicit control-mode fallback is permitted. A disabled current loop does not by itself prohibit operation if an independent, documented and verified drive/protection mechanism meets the channel's electrical and safety requirements; absence of such evidence prohibits arming.

## 6. Proposed command/loop compatibility model (not yet approved)

| Requested command | Minimum logical requirement | Additional unresolved conditions |
| --- | --- | --- |
| Position | Position loop owner is FORMA_MCU or DRIVER_IC | Valid position feedback or supported estimator, downstream drive path and verified limits |
| Velocity | Velocity loop owner is FORMA_MCU or DRIVER_IC | Valid speed feedback/estimator, downstream drive path and verified limits |
| Current | Current loop owner is FORMA_MCU or DRIVER_IC | Verified current sensing/regulation and driver capability |
| Duty / open-loop | Explicitly supported open-loop command path | Electrical limits, hardware protection and acceptable hazard behavior; not inferred from DISABLED loops |
| Torque | Explicit torque-command capability and verified actuator-specific conversion/control | **Not** automatically equivalent to current control; torque sensing/estimation and calibration are open |

A command's primary loop is necessary but not sufficient. For cascaded loops, validate that output of each upstream loop is consumable by the downstream loop or driver and that rates, feedback and fault propagation are compatible. Any unverified interface makes the command capability unavailable. Safety-critical hardware protection is separate from an application-exposed current loop.

**Next gate:** choose whether command capabilities are derived automatically from verified loop/driver capabilities, explicitly allowlisted in the descriptor, or require both (recommended: both, with mismatch rejected). No implementation or tests until the rule is approved.

## 7. Approved command capability intersection (2026-11-06)

A command mode is available only when it is explicitly present in the per-channel allowlist AND supported by verified hardware capabilities, including loop ownership, driver interfaces, feedback and protective mechanisms. Unsupported allowlisted commands and unlisted hardware-supported commands must not be enabled automatically. Hardware identity, firmware or descriptor changes require capability revalidation. Runtime authorization and K2 inhibit remain separate mandatory gates.

Proposed test additions (not implemented): 66-L-CH-019 allowlisted but unsupported command rejected; 66-L-CH-020 supported but not allowlisted command rejected; 66-L-CH-021 runtime authorization revoked despite both gates passing; 66-L-CH-022 hardware change requires revalidation. Total proposed tests: 22.

Next decision: should any unsupported allowlisted command invalidate the entire Forma descriptor, or only the affected channel? Recommended: entire descriptor, to avoid partial arming of an inconsistent configuration.

## 8. Approved separation of environment, Forma state and channel state (2026-11-06)

**Approved policy:** operating environment, Forma safety state and per-channel availability are independent dimensions. An environment label does not itself authorize motor power, bypass a stop latch or prove mechanical support.

| Dimension | Initial vocabulary | Meaning |
| --- | --- | --- |
| Operating environment | `BENCH`, `SUPPORTED`, `FREE_STANDING` | Evidence about fixtures, external support and balance requirements; not an authorization token |
| Forma safety state | `NORMAL`, `DEGRADED`, `PROTECTIVE_ACTION`, `INHIBITED` | Overall operating posture; transitions and priorities require separate approval |
| Channel state | `AVAILABLE`, `UNAVAILABLE`, `FAULTED` | Per-channel capability/health; does not alone determine safe joint motion |

- In `BENCH`, a channel with unsupported configuration can be excluded while independent channels are tested in `DEGRADED`, **only** with verified fixture retention, load, travel and collision constraints, service authorization, physical emergency stop and K2 inhibit. `BENCH` is not an override.
- In `FREE_STANDING`, loss of a joint may require a prevalidated whole-body protective maneuver rather than indiscriminate drive removal. This is a design objective, **not** evidence that balance recovery is currently possible or safe.
- `PROTECTIVE_ACTION` may use unaffected channels only with an approved, bounded recovery policy, valid sensors and actuator authority. Forma-local hardware inhibit and stop latches always take precedence when applicable.
- If failure isolation or protective behavior is unverified, reject the relevant motion; `INHIBITED` must retain diagnostics, communication and configuration repair where safe. A disabled channel is not automatically a reason to disable unrelated diagnostic functions.
- The earlier Section 7 recommendation to reject an entire Forma for any unsupported allowlisted command is **superseded as a recommendation**, not adopted. Define per-channel isolation versus Forma-wide inhibition using verified safety dependencies; an inconsistent descriptor cannot silently arm a channel.
- Main-coordinated whole-body protection versus Forma-local protective action, sensor validity, transition priority, fixture evidence and recovery behavior remain **design proposals**, not approved implementation details.

### Proposed tests (not implemented)
- 66-L-CH-023: `BENCH` with one unsupported channel and verified independence: affected channel inhibited; authorized independent channel remains testable.
- 66-L-CH-024: `BENCH` without fixture/safety evidence: environment flag alone does not enable drives.
- 66-L-CH-025: `FREE_STANDING` with failed load-bearing joint: ordinary motion blocked; only verified protective policy may request unaffected joints.
- 66-L-CH-026: `INHIBITED` maintains safe read-only diagnostics and configuration repair while motor power remains disabled.
- 66-L-CH-027: Changing environment/state does not clear stop latch, restore expired grants or defeat external inhibit.

Total proposed channel test IDs: 27; none implemented or executed.

**Next approval gate:** define who supplies and validates operating-environment evidence (fixture interlock/sensor/operator declaration), and what is mandatory for `BENCH` drive eligibility. Do not infer fixture safety from a software mode switch alone.

---
Open MeriForma > Runtime Invalidation Events > Suite 66-L > Motor Channel Design
