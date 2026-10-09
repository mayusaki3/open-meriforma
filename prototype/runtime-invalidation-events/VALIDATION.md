# Runtime Invalidation Events — Validation

Status: cross-domain event foundation **user-confirmed PASS** (2026-10-09); policy action lifecycle **user-confirmed PASS** (2026-10-09); safety-state verification **user-confirmed PASS** (2026-10-09); observation evidence extension **user-confirmed PASS** (2026-10-09); recovery policy **user-confirmed PASS** (2026-10-09). All ten test suites user-confirmed PASS; atomic state persistence **awaiting local execution**.

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

## New phase: `python .\\test_atomic_state.py` — pending

- Five record kinds stored together in a single SQLite snapshot transaction.
- Reject incomplete snapshots and stale optimistic revision updates.
- Forced child exit before commit must preserve the old complete snapshot.
- Forced child exit after commit must preserve the new complete snapshot.
- Snapshot storage is independent of earlier reconciliation table; no automatic integration or external/hardware atomicity.

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
