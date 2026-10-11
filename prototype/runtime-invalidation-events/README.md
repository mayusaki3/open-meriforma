# Runtime Invalidation Events — cross-prototype concept test

This test imports existing **Virtual Body Graph** and **External Object Relation**
runtime implementations, rather than copying their lifecycle rules.

Purpose: validate a common **event delivery boundary** across different
invalidation sources while keeping detection, policy choice, event acknowledgment,
and resource cleanup distinct.

Run from this directory:

```powershell
python .\test_events.py
```

Expected: six PASS lines ending with `PASS all runtime-invalidation-events checks`.

Prototype assumptions:
- One event per domain/execution ID; IDs are supplied by caller and must identify a lifecycle.
- Pending events are in memory only; no timestamps, persistence, retry, transport, or crash recovery.
- Acknowledgment means the event was handled by the consumer, **not** that the
  robot stopped or a control lease was released.
- Policy decisions are recorded as strings only; they do not actuate.
- Real-world safety action, control handoff, distributed event ordering,
  and event delivery guarantees remain unvalidated.

## Policy action lifecycle (next phase)

Run `python .\\test_actions.py` to check `requested → accepted → executing → completed/failed`.
A completed action is only a **reported completion**; it is not proof of physical STOP or safe state.
Event acknowledgment, action status, and explicit execution finish remain separate.
No real action executor is implemented.

## Synthetic safety-state verification (next phase)

Run `python .\\test_safety_verification.py` after the two existing tests.
The STOP verifier compares **synthetic** drive-disabled and joint-velocity observations
with a provisional threshold. Results: `verified`, `not_verified`, `unknown`.
An Action's `completed` report is independent from the verification result.
This is not physical STOP verification: freshness, sensor integrity, scope,
redundancy, and real safety policy remain unimplemented.

## Observation evidence extension

Run `python .\\test_observation_evidence.py` to check freshness, joint scope,
simulated integrity and continuous sample-window duration. All samples are synthetic.
The `integrity_ok` flag is **not** cryptographic or physical integrity verification.
The sample-window check cannot establish continuous physical behavior between samples;
real safety requirements need explicit sensor, timing and fault models.

## Recovery policy (next phase)

Run `python .\\test_recovery_policy.py` to check advisory recovery decisions
for STOP verification results. Recommendations do not invoke a motor stop,
change resource ownership, or authorize automatic resumption. Escalation and
safe fallback remain **requests**, not implemented physical actions.

## End-to-end correlation (next phase)

Run `python .\\test_correlation.py` to check Event ID, Action ID,
Execution lifecycle ID and evidence generation before advisory recovery.
The caller supplies the authoritative current lifecycle/generation; this
prototype cannot authenticate them. Replay protection is in-memory only.

## Durable delivery / timeout (next phase)

Run `python .\\test_durable_delivery.py` for SQLite-backed local outbox
retries, ACK/replay behavior across process restart, and action deadline
handling. Tests use a temporary SQLite database and synthetic logical time.
This does **not** implement distributed exactly-once delivery, a real-time
safety watchdog, or physical STOP. The producer must provide stable unique
keys; the consumer must deduplicate deliveries. Caller clocks must remain
consistent across restarts.

## Delivery lease / crash recovery (next phase)

Run `python .\\test_delivery_leases.py` for competing SQLite connections,
reservation expiration, fencing-token ACK checks, reopen/rollback and a
simultaneous-thread race. This separate experimental API does not replace
`DurableDelivery.deliver()`; callers must migrate to the lease API to
avoid duplicate active reservations. No real process kill, network partition,
clock synchronization or hardware safety is tested.

## Forced process-exit crash recovery (next phase)

Run `python .\\test_process_crash.py`. The parent starts disposable child
Python processes that call `os._exit(71)` at selected transaction/ACK
boundaries. This does not terminate the test runner or modify production DBs.
The test uses temporary SQLite files and synthetic logical time; it is not a
power-loss, filesystem durability, network-partition, or hardware-safety test.

## Restart state reconciliation (next phase)

Run `python .\\test_restart_reconciliation.py`. This read-only assessment
reopens SQLite snapshots for Execution/Event/Action/Verification/Correlation,
checks identities and caller-supplied generation, and reports historical
verification only. Missing or inconsistent data becomes `unknown`.
It cannot infer current physical safety, resume execution, or modify leases.

## Atomic state persistence (next phase)

Run `python .\\test_atomic_state.py` for complete five-kind SQLite
snapshots, optimistic revision conflict handling, incomplete-batch rejection,
and child-process termination before/after commit. Uses temporary files only.
This separate snapshot format is not yet wired to `RestartReconciliation` or
live controllers; it cannot make database writes atomic with hardware actions.

## Persistence technology boundary

SQLite is used **only as the PC reference/test implementation**, not a required
Open MeriForma runtime dependency or wire protocol. MCU persistence may use
other media or none, depending on its responsibilities. Safety actions must not
wait for a storage transaction, and persisted history cannot authorize motion.
See [runtime persistence boundaries](../../docs/design/runtime-persistence-boundaries.md).

## Atomic snapshot and reconciliation integration

Run `python .\\test_snapshot_reconciliation.py`. A storage-neutral adapter
accepts a store with `read(key)`, checks snapshot Revision independently from
Correlation Generation, and invokes the pure historical record evaluator.
The test covers SQLite reopen and an in-memory store. Atomic commit does not
prove data correctness or current physical safety; no automatic resume or
lease changes occur. Run `test_restart_reconciliation.py` again as regression.

## Candidate reboot state classification

Run `python .\\test_reboot_state_policy.py` to validate a pure, storage-independent
classification of persistent configuration, historical records and volatile live
authority. Valid configuration is only **candidate reusable**; actual startup
requires device-specific checks and explicit authorization. The policy cannot
actuate, restore a lease or prove current physical safety. See
[runtime persistence boundaries](../../docs/design/runtime-persistence-boundaries.md).
