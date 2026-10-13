# Main–Forma CAN-FD Prototype Review

Status: **design review / provisional** (2026-10-13). Source: `prototype/runtime-invalidation-events/`, especially `VALIDATION.md`. All 23 Python test suites have user-confirmed PASS; this is not hardware verification or a finalized wire standard.

## 1. Established prototype observations

| Boundary | Demonstrated in Python | Not established |
|---|---|---|
| Logical envelope | Version, kind, sequence, identifiers, CRC32 and strict length checking | Authentication, stable interoperable protocol |
| Fragmentation | Up to 64 bytes per synthetic frame; 9-byte header, 55-byte data; out-of-order and duplicate handling | CAN arbitration IDs, DLC/padding, hardware driver |
| Delivery | Synthetic whole-transfer retry/ACK, bounded retry count, transfer ID nonreuse per session | Interoperable ACK format, late ACK/replay behavior across resets |
| Scheduling | Safety > heartbeat > control > diagnostic; approximate airtime; two-unit 100 Hz workload | Worst-case CAN bus latency, stuffing, contention, ISR jitter |
| Sessions | Main boot/challenge and Forma boot/session/sequence checks | Authenticated peer identity, boot-unique challenge guarantee |
| Safety | Advisory eligibility revoked on synthetic timeout, queue overflow and bus-off; no automatic resume | Actual actuator inhibit, independent watchdog, physical STOP evidence |
| Persistence | PC-side SQLite reference and storage-neutral snapshot policies | MCU flash endurance/atomicity, cross-controller transactions |

The integrated pipeline presently supports **heartbeat messages only**. Priority classes other than heartbeat are exercised in the isolated scheduler, not end-to-end.

## 2. Candidate protocol decisions — NOT FINAL

- CAN-FD is a candidate Main–Forma bus. RS485 remains a possible alternative; no physical comparison has been validated.
- Provisional example bitrates: nominal 500 kbit/s, data 2 Mbit/s. These are **model inputs**, not proven board settings.
- Logical envelope max 256 bytes; CRC32 detects accidental corruption only.
- Synthetic fragment header is 9 bytes with 16-bit transfer ID; maximum synthetic payload is 55 bytes per fragment.
- Priority order: safety, heartbeat, control, diagnostic. Safety traffic priority does not itself guarantee safe motor behavior.
- Meridim 100 Hz is a system-level reference target, not proof that every Forma must send a 100 Hz fragmented logical envelope.
- Synthetic heartbeat timeout defaults vary by prototype (0.02–0.5 s); no production deadline is selected.
- Required peer loss revokes coordinated authority. A transport recovery is not authorization recovery; new sessions and explicit reauthorization are required.

## 3. Open decisions and risks

| ID | Decision required | Why it matters | Next evidence |
|---|---|---|---|
| CAN-01 | Standard vs extended CAN IDs, node addressing, message-class bit allocation | Arbitration, compatibility, filtering | CAN-ID allocation table and collision tests |
| CAN-02 | Required/optional Forma count and worst-case traffic matrix | Bandwidth and heartbeat capacity | Per-unit frame rates and utilization worksheet |
| CAN-03 | Frame DLC and padding policy; fragmentation metadata | Hardware interoperability | Real controller loopback |
| CAN-04 | Transfer ID rollover, late fragments, ACK semantics, dedup lifetime | Cross-session replay and mixed transfers | Long-running wraparound/fault injection |
| CAN-05 | Control and safety message schemas and semantics | Integrated pipeline only validates heartbeat | End-to-end message schema tests |
| CAN-06 | Per-unit heartbeat period, freshness window, deadlines and jitter | False timeouts vs delayed fault detection | Hardware latency measurements |
| CAN-07 | Bus-off detection, backoff, recovery and power-cycle handling | Controller behavior differs by device | Hardware fault injection |
| CAN-08 | Peer identity, challenge uniqueness and replay fencing | CRC32 is not authentication | Threat model and security design |
| CAN-09 | Main and Forma local safety actions, watchdog and motor-inhibit wiring | Advisory revocation cannot stop motors | Hardware-in-loop STOP evidence |
| CAN-10 | Scheduler handling of fragmented transfers and queue preemption | Priority inversion or partial transfer stalls | Fragment-level mixed-priority load test |
| CAN-11 | Authority lifecycle and reboot-state restoration | Persisted history must not restore control | Multi-controller restart tests |

## 4. Responsibility boundary

**Main Controller candidate responsibilities:** robot-wide required-peer inventory, coordinated eligibility, control authority arbitration, session challenge and global invalidation; never treat historical evidence or transport recovery as permission to resume.

**Forma Controller candidate responsibilities:** local actuator and sensor health, independent local inhibit/watchdog policy, current local readiness, peer-session fencing and immediate local response to communication loss. The actual hardware outputs and response deadlines remain unspecified.

**PC/SBC reference environment:** simulations, persistence experiments, trace capture and validation. SQLite is not imposed on an MCU and must not be in a real-time safety-critical path.

## 5. Recommended validation sequence

1. Define and test an explicit CAN-ID allocation and message taxonomy without locking down production IDs.
2. Model fragment-level scheduling with bounded in-flight work, stale transfer cleanup, mixed traffic and wraparound.
3. Produce a traffic matrix for plausible Forma counts and frame rates, then compute utilization bounds with conservative timing assumptions.
4. Specify Main and Forma local failure responses, followed by controller-in-the-loop and hardware STOP verification.

## 6. Review caveats

- The 23 PASS results confirm the tested Python fixtures, **not** system safety, bus timing or production readiness.
- Current integration may need further edge-case work on fragment-to-scheduler correlation, stale in-flight frames after reboots, and partial-message timeouts. These are unverified, not resolved by existing PASS results.
- Do not promote provisional constants, message fields or API names to a normative standard without an explicit design decision and associated test cases.
