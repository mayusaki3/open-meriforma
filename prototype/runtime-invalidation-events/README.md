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
