# Suite 63 — Coordinator restart boundary (synthetic)

Two child-process crash windows are injected: after the first peer has committed its local reservation, and after both peers have committed but before any modeled group authorization. On restart, both local SQLite histories and plain-file witnesses are re-opened; a newly created coordinator has no receiver instance and its group enabled flag remains false. An untouched provisioned group is likewise not implicitly authorized.

**Important limitation:** this demonstrates only a *volatile coordinator flag*. It does not establish peer-local enforcement of group-commit proof, nor a durable authenticated group-commit record. A local Forma receiver created before the crash could behave differently in real firmware; that failure mode is NOT covered by these tests. A future suite must model each peer's independent group-commit gate and reject stale, partial, replayed or mismatched proofs.

No distributed atomic commit, authenticated messages, real power-loss storage behavior, CAN-FD traffic, actuator inhibit, or physical STOP is demonstrated.
