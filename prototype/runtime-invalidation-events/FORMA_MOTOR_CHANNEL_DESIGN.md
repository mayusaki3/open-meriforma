Open MeriForma > Runtime Invalidation Events > Suite 66-L > Motor Channel Design

# Suite 66-L — Per-Forma motor channel descriptor (design proposal)

Status: PER-LOOP OWNERSHIP AND EXPLICIT DISABLED POLICY APPROVED (2026-11-05); remaining descriptor fields and test expectations are PROPOSALS. No implementation or test PASS.
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

Unit-test coverage target: 100% of specified descriptor-validation branches, with separate instrumented integration and fault-injection evidence for electrical/mechanical stop. Test numbers are proposed, not PASS claims.

## 5. Approved decisions and next design gate

**Approved 2026-11-05:** Within each Forma, A/B control modes may differ per channel. Each channel independently declares ownership of its **current, velocity and position** control loops as Forma MCU or driver/controller IC, limited to the actual verified hardware capabilities. Mixed ownership within one channel is permitted (e.g., driver current loop, Forma MCU velocity and position loops). An unsupported, missing, ambiguous or conflicting loop owner must be rejected, without silent fallback or drive arming. No specific loop rates, motor counts, MCU or driver IC are approved.

**Approved 2026-11-05:** An intentionally unused current, velocity or position loop is explicitly declared `DISABLED`. All three loop-owner fields must be present; an omitted field is an invalid descriptor, not an alias for `DISABLED`. A disabled loop must not accept a command for that control mode. A hardware driver may still implement internal protection or regulation not exposed as a selectable application control loop; this must be documented separately and must never bypass Forma safety checks.

**Next gate:** specify which command modes remain valid when one or more loops are `DISABLED`, including open-loop requests, and define compatibility constraints between upstream/downstream loop ownership. Do not freeze schema or implement tests until this is reviewed.

---
Open MeriForma > Runtime Invalidation Events > Suite 66-L > Motor Channel Design
