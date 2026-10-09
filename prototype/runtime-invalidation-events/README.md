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
