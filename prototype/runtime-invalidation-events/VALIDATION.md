# Runtime Invalidation Events — Validation

Status: cross-domain event foundation **user-confirmed PASS** (2026-10-09); policy action lifecycle **user-confirmed PASS** (2026-10-09); safety-state verification **user-confirmed PASS** (2026-10-09); observation evidence extension **user-confirmed PASS** (2026-10-09); recovery policy **user-confirmed PASS** (2026-10-09). All thirty-nine test suites user-confirmed PASS (2026-10-16). Suite 40 (multi-Forma causal CAN) awaits local execution.

## Confirmed: `python .\\test_events.py`

- Body Graph topology loss emits event without releasing control: PASS.
- World Relation loss emits event without releasing Body/Object rights: PASS.
- Repeated validation does not duplicate invalidation events: PASS.
- Policy decision and acknowledgment do not mutate ownership: PASS.
- Recovery requires explicit lifecycle cleanup: PASS.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_actions.py`

- Explicit requested/accepted/executing/completed/failed transitions.
- Completed status is a report, not verified physical safety.
- Failed action does not release Body Lease or External Object rights.
- Acknowledgment does not complete actions; duplicate request rejected.
- Invalid and terminal transitions rejected.
- Explicit Execution finish independently releases rights.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_safety_verification.py`

- Synthetic STOP evidence assessed independently from Action completed report.
- Enabled drive or moving joint is not_verified.
- Missing, incomplete, or non-finite evidence is unknown (fail closed).
- Unfinished Action cannot be verified from observation alone.
- Handoff actions cannot use STOP verification; verification result cannot be silently overwritten.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_observation_evidence.py`

- Freshness, complete joint coverage, simulated integrity, and stability window.
- Unknown on stale/incomplete/invalid/untrusted evidence.
- Not verified if any valid observation reports motion or enabled drive.
- Uses caller-supplied monotonic timestamps; no sensor authenticity or clock synchronization.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_recovery_policy.py`

- verified: hold for explicit recovery; never auto-resume.
- not_verified: request stop escalation (advisory only).
- unknown: request evidence or safe fallback (advisory only).
- Decisions do not release control or external object rights.
- Reject duplicate decisions, action mismatches, and handoff actions.
- Relation restoration does not auto-resume; explicit finish releases rights.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_correlation.py`

- Link Event ID, Action ID, Execution lifecycle identity, and evidence generation.
- Reject cross-action, cross-event, cross-execution, stale lifecycle/generation results.
- Reject incomplete STOP actions, invalid generations, and duplicate evidence generation.
- Accept correlated verification for advisory policy only; no automatic resume or lease changes.
- Current identity/generation are trusted caller inputs in this prototype; no cryptographic proof, durable replay protection, or distributed sequencing.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_durable_delivery.py`

- SQLite local outbox with stable event keys and at-least-once polling.
- Missing ACK triggers retry after interval; ACK and dedup survive process restart.
- Action deadlines transition to timed_out once; late completion cannot overwrite terminal timeout.
- Tests use caller-supplied logical timestamps and a temporary local SQLite database.
- Not a distributed exactly-once delivery guarantee, authenticated transport, physical STOP, or safety watchdog.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_delivery_leases.py`

- BEGIN IMMEDIATE serializes local SQLite reservations across connections.
- Lease expiry allows reclaim with incremented fencing generation.
- Stale ACK is rejected by owner, generation and unexpired lease checks.
- Reopen preserves acknowledged/pending work; uncommitted writes roll back.
- Two simultaneous workers must not both obtain the same active reservation.
- Uses synthetic logical time; no process-kill, network partition, or hardware safety guarantee.
- Entire test suite completed: PASS (after test fixture isolation fix).

## Confirmed: `python .\\test_process_crash.py`

- Spawn a separate Python process and terminate it with `os._exit(71)`.
- Before transaction commit: SQLite must roll back uncommitted claim changes.
- After committed claim / before ACK: reservation remains until expiry; recovery increments fencing generation.
- After committed ACK: acknowledged event remains suppressed after child process exit.
- Uses isolated temporary databases and caller-supplied logical timestamps.
- Does not simulate power loss, disk corruption, network partitions, or a real-time watchdog.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_restart_reconciliation.py`

- SQLite persists separate Execution/Event/Action/Verification/Correlation snapshots.
- Missing or mismatched records and stale generation fail closed to unknown.
- Consistent historical verification is labeled historical, never current physical safety.
- No automatic execution resume or lease mutation.
- Snapshot ingestion is not transactional across components; no trusted clock or cryptographic evidence.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_atomic_state.py`

- Five record kinds stored together in a single SQLite snapshot transaction.
- Reject incomplete snapshots and stale optimistic revision updates.
- Forced child exit before commit must preserve the old complete snapshot.
- Forced child exit after commit must preserve the new complete snapshot.
- Snapshot storage is independent of earlier reconciliation table; no automatic integration or external/hardware atomicity.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_snapshot_reconciliation.py`

- Extract pure historical-record evaluation from the existing SQLite reconciliation wrapper.
- Adapt AtomicState snapshots via a minimal read(key) interface, with no SQLite dependency in the adapter.
- Validate snapshot Revision separately from evidence Generation; inconsistent but atomically committed data remains unknown.
- Verify reopened SQLite snapshots and a memory-only store; no automatic resume or lease mutation.
- This does not validate current physical safety, authenticated generations, or cross-device atomicity.
- Entire test suite completed: PASS; existing restart reconciliation regression also PASS.

## Confirmed: `python .\\test_reboot_state_policy.py`

- Pure classification of reusable configuration, historical-only records, discarded active authority and reobserved runtime state.
- Invalid or unrecognized input fails closed; no automatic resume, lease mutation or current physical safety claim.
- Candidate policy only; no MCU boot sequence, physical actuator, storage driver or power-loss test.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_boot_safety.py`

- Main/Forma boot gates require configuration, calibration, local checks, communication, peer identity/epoch, fresh observations and explicit authorization.
- Communication loss, peer restart, local restart and invalid calibration revoke eligibility.
- Eligibility is advisory only: no physical motor command, STOP output, watchdog or safety guarantee.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_main_forma_boot.py`

- Main readiness cannot override unready Forma; coordinated eligibility requires fresh checks and explicit authorization on both sides.
- Local safety loss, communication loss, and either peer restart invalidate the coordinated state.
- Synthetic pair model only: no actual CAN-FD handshake, motor output, watchdog, or distributed atomic authorization.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_forma_heartbeat.py`

- Synthetic monotonic clock, required-unit heartbeat freshness, sequence and epoch rejection, and explicit reauthorization after timeout.
- All required Forma units must be ready; any missing/unready/timed-out unit invalidates coordinated eligibility.
- Epochs and timestamps are trusted local inputs; no physical watchdog, network delivery, clock synchronization, authenticated identity or real motor inhibition.
- Main restart resets observations; anti-replay across Main reboot is not guaranteed without a durable or authenticated peer-epoch protocol.
- Entire test suite completed: PASS (after invalid epoch test expectation fix).

## Confirmed: `python .\\test_forma_sessions.py`

- Separates Main boot ID, Main challenge, Forma boot ID and session ID; rejects old-session messages and duplicate sequences.
- Requires all required Forma peers to re-establish readiness and explicit authorization after restart or session change.
- Main challenge uniqueness across real restarts and authenticity of messages are **assumed**, not implemented; no cryptographic handshake or motor control.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_protocol_boundary.py`

- Transport-neutral strict message dictionary schema connects SessionMonitor and FormaLinkMonitor.
- Duplicate/out-of-order messages, stale sessions, missing required peers, timeout, readiness loss and restarts must not restore authorization automatically.
- Synthetic dictionary API, not a CAN-FD/RS485 frame encoding, cryptographic authentication, real-time transport or motor safety implementation.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_wire_envelope.py`

- Versioned binary envelope with magic, kind, sequence, readiness, payload length, five length-prefixed UTF-8 identifiers and CRC32.
- Round trip, truncation, corruption, invalid header, field bounds, and integration with ProtocolBoundary.
- Max frame 256 bytes is an experimental logical limit, **not** a CAN-FD frame size; segmentation and reassembly are not implemented.
- CRC32 is not authentication or protection against deliberate forgery.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_canfd_fragments.py`

- Fragment logical envelopes into at most 64-byte payloads using a provisional 9-byte fragment header.
- Reassemble out-of-order fragments, allow identical duplicates, reject conflicting duplicates and malformed headers.
- Bound active transfers and expire incomplete transfers using synthetic monotonic time.
- Separate transfers by trusted source and 16-bit transfer ID; reassembled messages must pass envelope CRC and session validation.
- No actual CAN identifiers, transport drivers, authentication, transfer-ID wraparound policy, or physical safety guarantee.
- Entire test suite completed: PASS (after fixture was extended to span multiple fragments).

## Confirmed: `python .\\test_can_fault_supervisor.py`

- Synthetic bus-off revokes eligibility and discards pending transfers and incomplete reassembly.
- Bus recovery alone cannot resume: new Main boot/challenge, peer sessions, fresh heartbeats and explicit authorization are required.
- Bounded retry intervals, ACK cleanup, no transfer ID reuse within a synthetic session, and two-peer coordination.
- No actual CAN controller, bus-off electrical detection, authenticated transport, retransmission protocol or physical motor inhibition.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_can_scheduler.py`

- Synthetic priority scheduling: safety, heartbeat, control, diagnostics.
- Configurable nominal/data bitrate approximation and bounded priority queue.
- 100 Hz synthetic heartbeat workload across two Forma peers.
- Deadline misses and missing peer heartbeat revoke authority; recovery requires explicit authorization.
- No CAN arbitration, real CAN-FD timing, bit stuffing, hardware timing or physical safety validation.
- Entire test suite completed: PASS.

## Confirmed: `python .\\test_integrated_can_link.py`

- Encoded heartbeat through fragmentation, priority scheduling, reassembly, session/heartbeat validation across two Forma peers.
- Bus-off revokes authorization; recovery requires new Main challenge, new peer sessions and explicit authorization.
- Missing heartbeat and queue saturation fail closed.
- No CAN hardware, actuator output or verified physical STOP. This prototype currently integrates heartbeat only.
- Entire test suite completed: PASS (2026-10-13).


## Confirmed: `python .\\test_can_id_allocation.py` local validation

- Provisional standard 11-bit identifier: priority bits 10..9, class bits 8..6, node bits 5..0.
- Four candidate classes: safety (0), heartbeat (1), control (2), diagnostic (3); reserved combinations rejected.
- Node addresses 1..62, address 0 and 63 reserved. Deterministic inventory allocation is a local prototype, **not** distributed discovery or persistent assignment.
- Roundtrip, collision-free mapping, cross-node arbitration priority, malformed/reserved ID rejection.
- No physical CAN controller, standardization decision, security, bus-load verification or physical safety guarantee.
- Entire test suite completed: PASS (2026-10-13).


## Confirmed: `python .\\test_can_traffic_estimator.py`

- Average synthetic CAN-FD utilization for multiple Forma peers, per-class frame rates and payload sizes.
- Uses the same approximate frame duration as `can_scheduler.py`; configurable nominal/data bitrate and utilization threshold.
- Supports per-row peer subsets, overload flagging and input rejection.
- Does **not** predict burst latency, arbitration contention, retransmission load, worst-case response time, actual CAN-FD timing, or physical safety.
- Entire test suite completed: PASS (2026-10-13).

## Confirmed: `python .\\test_can_burst_probe.py`

- Synthetic simultaneous safety/heartbeat/control/diagnostic frame bursts and priority ordering.
- Deadline-miss invalidation, bounded queue shedding and residual backlog within a dispatch window.
- Reports simulated frame duration, **not** verified end-to-end latency or physical worst-case timing.
- Uses existing scheduler's simplified non-preemptive priority model; no arbitration, bit stuffing, driver ISR, retry or physical STOP verification.
- Entire test suite completed: PASS (2026-10-13).

## Confirmed: `python .\\test_fragment_scheduler.py`

- Fragment-aware queue tracks (generation, source, transfer ID, fragment index) without relying on source-only FIFO matching.
- Mixed-priority dispatch, deadline-miss invalidation, whole-queue fail-closed eviction, expiry and new-session fencing.
- A new generation explicitly discards queued old-session fragments; no automatic authority restoration.
- Suite 27 user-confirmed PASS (2026-10-14).
- The standalone scheduler is now wired into IntegratedCanLink for suite 28; this does not prove real CAN arbitration, physical STOP or transfer-level ACK semantics.

## Confirmed: `python .\\test_integrated_fragment_link.py`

- IntegratedCanLink now dispatches exact (generation, source, transfer ID, fragment index) records rather than source-only FIFO matching.
- Regression checks: two-peer heartbeat authorization, concurrent same-peer transfers, fragment deadline failure, queue overflow, and bus-off recovery with old-generation rejection.
- Entire suite user-confirmed PASS (2026-10-14), after correcting the queue-overflow test setup.
- Still synthetic: no physical CAN controller, real arbitration, actuator control or physical STOP verification.

## Confirmed: `python .\\test_integrated_ack_retry.py`

- Synthetic application-level transfer completion ACK, independently from hardware CAN ACK.
- Simulated lost ACK triggers bounded retry of the same transfer ID; completed logical transfer is deduplicated without replaying protocol effects.
- Retry exhaustion leaves transfer unacknowledged; bus-off and new Main generation discard stale pending/ACK state.
- Entire suite user-confirmed PASS (2026-10-14).
- This models an ACK-loss test switch, **not** authenticated remote ACK, hardware retry, or proof of physical safety.

## Confirmed: `python .\\test_ack_wire_integration.py`

- Application ACK wire envelope: version, transfer ID, source, destination, generation, CRC32 and exact-length checks.
- Integrated pending-transfer correlation, duplicate rejection, generation fencing and stopping retries after matching ACK.
- Entire suite user-confirmed PASS (2026-10-14).
- Synthetic source argument is **not authenticated**. CRC32 is only accidental corruption detection. No hardware CAN ACK or actual peer ACK transmission is modeled.

## Persistence technology boundary

- SQLite is a PC reference/test implementation, not a mandatory Main Controller or Forma Controller dependency.
- Safety control must not block on persistence; historical evidence never grants automatic execution resume.
- See [runtime persistence boundaries](../../docs/design/runtime-persistence-boundaries.md) for environment-specific candidate responsibilities and unverified assumptions.

## Candidate API and responsibility boundaries

1. Execution validation detects prerequisite/authority loss and invalidates execution; it does not actuate.
2. InvalidationEvents emits one in-memory event per supplied domain/execution lifecycle ID; acknowledgment does not stop or release.
3. PolicyInbox records a recommendation; PolicyActions tracks requested/accepted/executing/completed/failed independently.
4. Action completion is an executor **report**, not a verified physical safe state.
5. StopVerifier and StopEvidenceVerifier assess synthetic STOP observations separately; unknown means verification cannot be established, not safe.
6. RecoveryPolicy records advisory hold/escalate/reobserve recommendations; it cannot resume execution or release leases.
7. ResourceLeases and ExternalObjectUse remain independently owned; explicit execution finish releases rights.

No API name, state vocabulary, threshold, or message schema is standardized by these prototypes.

## Limitations

- In-memory event/action state, no durable queue or distributed ordering.
- No physical executor, motor stop, safety-state sensor, or handoff controller.
- Acknowledgment only tracks notification handling.
- Completion report does not attest safe state.
- No automatic lease release or execution restart.
- State names and interfaces are provisional, not standard.
- Synthetic integrity flag is not proof of sensor integrity; sample-window duration does not prove continuous physical stability.
- No physical stop/fallback, actual executor, hardware confirmation, retry policy, or safe reauthorization workflow.
- No persistence, durable event acknowledgment, deduplication across restarts, delivery guarantees, or distributed ordering.
- No atomic distributed lease/authority transfer, real-time deadline, fault injection, or hardware safety certification.

## Confirmed: `python .\\test_ack_return_path.py`

- Synthetic Forma-to-Main ACK return path: ACK bytes -> CAN-FD-sized fragments -> priority scheduler -> reassembly -> IntegratedCanLink.receive_ack.
- Checks reverse-order peer completion, dropped ACK fragments, ACK deadline failure, and generation fencing.
- Entire suite user-confirmed PASS (2026-10-14).
- No physical CAN controller, authenticated sender, real bus arbitration, actuator command, or verified physical STOP.

## Confirmed: `python .\\test_shared_can_bus.py`

- Shared synthetic airtime clock and priority queue for Main-to-Forma heartbeat and Forma-to-Main ACK frames.
- ACK loss/retry, shared deadlines, queue saturation, and bus-off/generation fencing.
- Forward frames are imported from the existing IntegratedCanLink queue. ACKs are explicitly queued after application transfer completion; this is not an autonomous peer implementation.
- Entire suite user-confirmed PASS (2026-10-14).
- No real CAN arbitration, controller timings, cryptographic authentication, motor commands, or physical STOP verification.

## Confirmed: `python .\\test_shared_bus_endurance.py`

- Finite deterministic 15-cycle shared-bus simulation with two Forma heartbeat streams, reverse ACKs, and diagnostic fragments.
- Tests heartbeat priority ahead of diagnostics, ACK deadline failure, queue saturation, and bus-off/generation fencing.
- Synthetic background traffic consumes bus airtime but does not enter the application protocol or reassembly path.
- Entire suite user-confirmed PASS (2026-10-15).
- This is not long-duration soak testing, physical bus arbitration, authenticated ACK, or a hardware timing guarantee.

## Confirmed: `python .\\test_can_load_sweep.py`

- Parametric synthetic load sweep: Forma count, heartbeat/ACK period, diagnostic frames, nominal/data bitrates.
- Measures modeled utilization, maximum queue waiting time, deadline misses, and backlog clear time.
- ACKs are assumed to release halfway through each cycle, independent of heartbeat delivery; not an end-to-end integrated ACK exchange.
- Entire suite user-confirmed PASS (2026-10-15).
- No bit stuffing, real arbitration, fault retransmission, hardware timing verification, or safety certification. Load limits are comparative estimates only.

## Confirmed: `python .\\test_can_configuration_review.py`

- Compares candidate nominal/data rates, periods, diagnostics and modeled Forma unit capacity.
- Screening requires both zero modeled deadline misses and utilization at or below the configured threshold (default 70%).
- Reports highest passing unit count, utilization headroom, ranked candidates and explicitly infeasible configurations.
- Entire suite user-confirmed PASS (2026-10-15).
- Capacity is an **estimate**, not a validated hardware limit or recommended production configuration; ranking ignores cost, transceiver/controller capabilities, wiring, arbitration details and real safety constraints.

## Confirmed: `python .\\test_can_configuration_report.py`

- Deterministic JSON and Markdown reports of candidate capacity, modeled utilization, headroom, wait and deadline misses.
- Includes explicit no-feasible-candidate output and simulation limitations; never interprets these as hardware certification.
- CLI: `python .\\can_configuration_report.py --output-dir .\\validation-output` (optional `--candidates path.json`).
- Entire suite user-confirmed PASS (2026-10-15); CLI sample report generation also succeeded.
- Generated files are local outputs, not committed design decisions; no physical bus timing, controller support, wiring, cost or safety verification.

## Confirmed: `python .\\test_can_stream_profile.py`

- Independently configurable heartbeat, ACK, control and diagnostic periodic streams: name, kind, bytes (0..64), period, offset, deadline, per-unit multiplier, and frames per release.
- One non-preemptive shared bus with existing synthetic priority/airtime model; reports per-stream counts, waits and misses, plus overall utilization/backlog.
- `example_streams()` is illustrative and is **not** the validated Forma protocol traffic profile. ACK release remains time-based, not causally dependent on heartbeat delivery.
- Entire suite user-confirmed PASS (2026-10-15).
- No real arbitration, bit stuffing, retransmission overhead, actual bus timing, or physical safety verification.

## Confirmed: `python .\\test_can_causal_roundtrip.py`

- Synthetic heartbeat arrival triggers ACK creation after configured processing delay; a lost heartbeat never creates an ACK.
- Simulates heartbeat loss, ACK loss, one optional heartbeat retransmission, shared bus contention and end-to-end deadlines.
- Simplified independent messages; no integration with the authenticated session/fragment reassembler, no real CAN arbitration, no hardware retry behavior or physical safety verification.
- Entire suite user-confirmed PASS (2026-10-15).
- Does not authorize control or issue motor commands. Retry does not automatically restore authority.

## Confirmed: `python .\\test_causal_integrated_can.py`

- Integrates existing IntegratedCanLink fragment/session completion with SharedCanBus ACK frames. ACK scheduling occurs only after a completed forward transfer.
- Covers dropped heartbeat, dropped ACK followed by retry, ACK deadline failure, bus-off and generation fencing.
- Synthetic integration only; ACKs remain unauthenticated, no real CAN controller, physical STOP, or motor output. ACKs are enqueued after the explicit forward dispatch boundary, which adds simulation scheduling delay.

- Entire suite user-confirmed PASS (2026-10-16), including corrected missing-peer fixture and pre-enqueue ACK deadline failure.

## Confirmed: `python .\\test_multi_forma_causal.py`

- Two required Forma peers: both heartbeat/ACK paths, missing-peer fail-closed, single-peer ACK loss and retry, shared ACK deadline failure, bus-off and fresh generation without automatic authority.
- Tests synthetic shared-bus and protocol states, not authenticated hardware peers, actual CAN arbitration, physical STOP or motor control.

- Entire suite user-confirmed PASS (2026-10-17), including two required peers, missing-peer invalidation, per-peer ACK retry, deadline fault and bus-off recovery without automatic authority.

## Confirmed: `python .\\test_multi_forma_authority.py`

- Requires fresh ready observations from both required peers and explicit authorization; checks missing peer, bus-off/new generation and peer session replacement.
- Authorization is synthetic protocol state only, not motor enablement, hardware STOP validation or an authenticated CAN peer.

- Entire suite user-confirmed PASS (2026-10-17), including fresh Ready peers, explicit grant, bus-off recovery and peer session replacement.

## Confirmed: `python .\\test_multi_forma_authority_monitor.py`

- Synthetic continuous authority revocation: scheduler timeout, one peer Ready=false, one peer session replacement, and bus-off recovery with fresh explicit authorization.
- The scheduler timeout uses its configured deadline; this is not physical heartbeat timing, actuator inhibit or physical STOP verification.

- Entire suite user-confirmed PASS (2026-10-17), including timeout, Ready=false, session replacement and bus-off recovery.

## Confirmed: `python .\\test_authority_command_race.py`

- Synthetic authority-gated command staging with checks at enqueue and dispatch, fail-closed queue discard after timeout, Ready=false and bus-off/generation change.
- The adapter is intentionally not wired to CAN control frames or actuators. Its dispatch result is a simulated accepted command, not a motor command. A revoked gate requires explicit recreation after recovery; this is a prototype policy, not a verified physical safety mechanism.

- Entire suite user-confirmed PASS (2026-10-17), including pre-dispatch timeout, Ready=false, bus-off and generation fencing.

## Confirmed: `python .\\test_authority_can_scheduler.py`

- Integrates existing CanScheduler with IntegratedCanLink authority checks at control enqueue and before simulated dispatch. Tests two-peer normal scheduling, timeout, one-peer Ready=false, and bus-off generation fencing.
- This adapter is a separate synthetic control scheduler, not the SharedCanBus physical transmit path; it does not prove race-free hardware sends, CAN arbitration or motor inhibition.

- Entire suite user-confirmed PASS (2026-10-17), with suite 43 regression PASS. This confirms only the synthetic separate CanScheduler adapter, not SharedCanBus control transport or physical actuation.

## Confirmed: `python .\\test_authority_shared_bus.py`

- User-confirmed PASS (2026-10-17): 4/4 checks for authorized shared-queue control, heartbeat timeout cancellation, Ready=false cancellation and bus-off generation fencing.
- Suite 44 and 43 regressions also PASS (4/4 each). These tests use synthetic background-direction control payloads, not an actual control protocol or motor output. Mixed heartbeat/ACK/control priority is not yet validated.

## Confirmed: `python .\\test_authority_shared_bus_mixed.py`

- User-confirmed PASS (2026-10-18): 4/4 checks for Heartbeat/ACK priority over control, heartbeat expiry, Ready=false and bus-off queue clearing.
- Regression checks also PASS: suite 45 (`test_authority_shared_bus.py`) 4/4, suite 44 (`test_authority_can_scheduler.py`) 4/4, suite 43 (`test_authority_command_race.py`) 4/4; 16/16 checks total.
- The initial suite 46 monotonic-clock failure was corrected by processing queued protocol frames before the control authorization check. No real CAN arbitration, physical motor inhibit or mid-transmission revocation is verified.

## Confirmed: `python .\\test_authority_shared_bus_boundary.py`

- User-confirmed PASS (2026-10-18): 4/4 checks for authorized control at boundary, Ready=false revocation, bus-off revocation and generation mismatch revocation.
- Suites 46/45/44/43 regression checks also user-confirmed PASS (4/4 each); 20/20 checks in this run.
- Boundary injection is deterministic synthetic behavior before eligibility checking, not physical CAN transmission or motor inhibition.

## Confirmed: `python .\\test_authority_shared_bus_frame_boundary.py`

- User-confirmed PASS (2026-10-18): 4/4 checks for both controls dispatched while authorized, Ready=false between frames, bus-off between frames and generation change between frames.
- Suites 47 and 46 regression checks also PASS (4/4 each), 12/12 checks in this run.
- The earlier test injection timestamp 0.05 caused a clock regression; corrected to 0.06 before the successful run. Synthetic per-frame checks do not retract already dispatched frames or verify hardware motor inhibition.

## Confirmed: `python .\\test_authority_shared_bus_partial_command.py`

- User-confirmed PASS (2026-10-18): 4/4 checks for complete two-fragment reconstruction and cancellation/partial-buffer discard on Ready=false, bus-off and generation change.
- Suites 48, 47 and 46 regression checks also PASS (4/4 each), 16/16 checks in this run.
- Receiver is a test-only Reassembler, not Forma firmware; successful synthetic reconstruction does not establish actuator command execution safety.
