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
