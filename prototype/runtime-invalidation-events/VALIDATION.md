# Runtime Invalidation Events — Validation

Status: cross-domain event foundation **user-confirmed PASS** (2026-10-09); policy action lifecycle **user-confirmed PASS** (2026-10-09); safety-state verification **user-confirmed PASS** (2026-10-09); observation evidence extension **user-confirmed PASS** (2026-10-09); recovery policy **user-confirmed PASS** (2026-10-09). All twenty-eight test suites user-confirmed PASS (2026-10-14). Suite 29 (integrated ACK/retry) awaits local execution.

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

## New phase: `python .\\test_integrated_ack_retry.py` — pending local validation

- Synthetic application-level transfer completion ACK, independently from hardware CAN ACK.
- Simulated lost ACK triggers bounded retry of the same transfer ID; completed logical transfer is deduplicated without replaying protocol effects.
- Retry exhaustion leaves transfer unacknowledged; bus-off and new Main generation discard stale pending/ACK state.
- This models an ACK-loss test switch, **not** an encoded wire ACK frame, authenticated remote ACK, hardware retry, or proof of physical safety.

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
