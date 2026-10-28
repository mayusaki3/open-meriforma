# Suite 66-K — Forma hardware boundary and trust-anchor options

Status: DESIGN OPTIONS / PROVISIONAL (2026-10-29). No component selected, circuit built, timing measured, or safety certified.
Parent: FORMA_COMMUNICATION_ARCHITECTURE.md (66-J), FORMA_COMMUNICATION_PROTOCOL_REQUIREMENTS.md (66-I).
Working design review only; not a formal HLDocS v0.6.1 specification.

## 1. Placement and physical bus

| Option | Physical layout | Strengths | Risks / unresolved |
| --- | --- | --- | --- |
| A — Main hosts Receiver gateway, shared CAN-FD bus to Forma MCUs | Main [logical Receiver] → shared bus → each Forma local receiver + policy | Simple gateway; per-Forma final authority; aligns with prototype | Shared bus-off/common-cause fault, arbitration latency, Main compromise; gateway not a safety controller |
| B — dedicated gateway between Main and CAN-FD Forma bus | Main → gateway → shared bus → Forma MCUs | Independent routing, diagnostics and traffic shaping; clearer fault isolation from Main | Extra power/firmware, gateway itself can fail; cannot substitute for Forma-local watchdog |
| C — segmented CAN-FD branches / gateways | Main → gateways → groups of Forma | Bus fault domains, scaling | More complexity, cross-group synchronization, additional latency |

**Provisional baseline: A for initial prototype**, with an explicitly replaceable gateway boundary. B/C are retained as scalability and fault-containment alternatives. CAN-FD is a **candidate**, not an approved electrical design; wiring, termination, isolation, EMC, bus load and fault handling require measurement. Receiver functionality exists both at the Main-side routing boundary and Forma-local command acceptance; Main-side routing does not confer motor authority.

## 2. Forma controller and safety-stop hardware options

| Option | Watchdog / drive-inhibit architecture | Advantages | Critical limitations |
| --- | --- | --- | --- |
| K1 — single MCU software watchdog + driver enable | MCU software monitors and drives enable | Low component count | A stuck MCU, common power failure or firmware defect can defeat both detection and inhibit; not an independent safety mechanism |
| K2 — MCU + independent external watchdog/latch + default-off driver enable | External circuit demands valid periodic health signal and independently removes driver enable on failure | Independent from Main and main task; inspectable electrical inhibit path | Health signal must not be trivially toggled by failed firmware; inhibit pin and driver failure modes need fault analysis |
| K3 — MCU + dedicated safety controller + redundant inhibit / feedback | Safety controller evaluates watchdog, interlocks, feedback and dual-path drive inhibit | Better fault containment and diagnostic potential | Cost/complexity; safety integrity still depends on component choices and verification |

**Provisional baseline: K2 as minimum architecture to investigate, not as proof of functional safety.** K1 may be used only for nonhazardous bench simulations with motor power physically isolated. Escalate to K3 if hazard analysis requires redundancy/diagnostic coverage. Do not claim external watchdog alone proves safe torque off (STO).

### Power and stop boundary
- Boot, MCU reset, brownout, missing heartbeat, bus-off, fault and power-domain faults must default to *drive inhibited* wherever physically feasible.
- A motor driver enable pin is **not automatically a certified STO interface**. Distinguish command disable, torque removal, braking and holding force; a falling humanoid or gravity-loaded joint can remain hazardous after torque removal.
- Define independent inhibit path, its safe electrical polarity, pull resistors, latch persistence, hardware feedback, diagnostic fault detection and manual/service rearm.
- Measure electrical disable time, mechanical stopping/holding behavior, power-loss response and fault injection per joint/load. No physical STOP claims until measured.
- Separate communication watchdog (Forma-local authenticated liveness) from hardware supervisor (MCU health); both must be required for drive eligibility.

## 3. Credentials and boot epoch / anti-rollback

| Option | Trust anchor | Trade-off |
| --- | --- | --- |
| T1 — plain flash/file key + software counter | Cheap and flexible | Cloneable/rollback-prone; insufficient against storage rollback or physical access threat |
| T2 — MCU secure boot + protected key storage / monotonic counter where supported | Fewer components; hardware-dependent | Actual counter semantics, write endurance, rollback resistance, recovery policy and toolchain must be validated |
| T3 — external secure element / TPM-class device with protected identity and monotonic witness capability | Key isolation and potentially independent trust | Cost, provisioning, availability, bus interface, actual counter support and transaction ordering need validation |

**Provisional evaluation priority: T2 vs T3**, subject to threat model. A secure element with key storage does **not** necessarily supply a trustworthy monotonic counter; verify the exact part. Existing SQLite + file witness from suites 54–60 does not solve coherent rollback.

Session design shall authenticate both sides, bind identity + boot epoch + nonces + protocol version + policy, reject replay, and require fresh operation grants. Credential rotation, Forma replacement and offline service recovery remain open.

## 4. Candidate requirements for MCU selection
- CAN-FD controller and transceiver compatibility, receive filters, error counters, bus-off detection/recovery.
- Timer capable of local monotonic deadlines; independent watchdog/clock domain availability.
- Boot-time drive inhibit defaults; GPIO and brownout/reset behavior; external watchdog and feedback I/O.
- Secure boot, device identity and protected key/epoch support (or compatible external trust anchor).
- Memory for bounded fragmentation/replay state, diagnostics and maintenance policy.
- Deterministic worst-case scheduling under mixed heartbeat/control traffic.
- Hardware debugging and production provisioning, firmware upgrade/rollback policy.
- No MCU model or price is selected by this note.

## 5. Preliminary interface and verification matrix

| Boundary | Required check | Evidence still needed |
| --- | --- | --- |
| Main → Forma | Authenticated command source, protocol version, session, replay | Attack/fault-injection test on real transport |
| CAN-FD bus | Arbitration, fragmentation, bus-off, termination and EMC | Load/latency/fault measurements |
| Forma MCU → inhibit | Reset/brownout/watchdog removes drive enable | Oscilloscope and physical driver tests |
| Inhibit → motor/joint | Torque removal/holding/braking as hazard demands | Instrumented joint stop tests |
| Forma trust anchor | Protected identity, epoch advance, rollback resistance | Vendor evidence + rollback fault tests |
| Recovery | Physical stop confirmed; operator/service permission; fresh session/clearance/grant | Service recovery and power-cycle tests |
| Cross-Forma group | No partial actuation on peer failure | Multi-node fault injection and group-commit validation |

## 6. Decisions requiring explicit approval
1. **Topology**: start with A shared CAN-FD + Main gateway, or choose B/C.
2. **Stop architecture**: evaluate K2 external watchdog + default-off inhibit as baseline, or require K3 from outset.
3. **Trust anchor**: compare T2 MCU protected key/epoch vs T3 external secure element; do not assume monotonic witness exists.
4. **Safety objective**: define hazardous loads, acceptable stop behavior, and required fault tolerance before selecting driver and timing.
5. **Next stage 66-L**: produce measurable electrical/interface requirements and a test plan after these choices; keep software simulation separate from actual safety evidence.

No tests are added for suite 66-K. Last user-confirmed synthetic results: suites 66-A–H, 98/98 PASS.
