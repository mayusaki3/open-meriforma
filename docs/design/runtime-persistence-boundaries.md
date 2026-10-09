# Runtime Persistence Boundaries — Candidate Design

Status: **design clarification, not a storage standard or implementation mandate** (2026-10-09).

## Purpose and evidence

The [Runtime Invalidation Events prototype](../../prototype/runtime-invalidation-events/VALIDATION.md) has user-confirmed PASS results for eleven test suites, including local SQLite delivery, leases, process termination, restart reconciliation, and atomic snapshots. These results establish properties of **those reference implementations only**, not universal runtime guarantees.

## Storage technology is not a protocol requirement

- SQLite is a **PC-hosted reference implementation / test fixture** for local persistence and crash injection.
- No Forma Unit, Main Controller, Forma Controller, Meridim endpoint, or compliant host is required to use SQLite.
- Persistence is a separate implementation boundary; candidate operations include storing a versioned snapshot, retrieving it, recording event/ACK state, and validating a generation/revision. These are conceptual responsibilities, **not standardized APIs**.
- RAM, append-only files, Flash, FRAM and other stores may be appropriate; endurance, atomic-write granularity, corruption detection and power-loss behavior require target-specific verification.

## Responsibility candidates by environment

| Environment | Candidate persistent information | Safety and timing boundary |
| --- | --- | --- |
| PC / SBC host | Event history, ACK/retry state, action reports, diagnostics, historical evidence and reconciliation snapshots | Persistence may be asynchronous; an ACK or completed report is not proof of physical STOP |
| Main Controller MCU | Minimal configuration, identity/version, calibration or recovery metadata where needed | Deterministic control and safety response must not wait for a database, filesystem or host availability |
| Forma Controller MCU | Necessary local configuration/calibration and device identity, subject to hardware capability | Loss of communication or persistence must not bypass locally required safe behavior |
| Virtual Unit / MuJoCo | Test state, snapshots, trace and replay data | Simulation history does not establish current physical safety |

These assignments are **candidates**, not a decision that every device must persist each item. In particular, event logs need not be stored in every MCU.

## Runtime invariants

1. **Safety actions and real-time control are independent of persistence completion.** A failed, delayed or absent write cannot inhibit an independently required STOP/limp response.
2. **A persisted state is historical evidence, not live authority.** Reboot never automatically restores an active Execution, control lease, handoff, or permission to move.
3. **Missing, inconsistent, stale or unverifiable state fails closed** for safety-relevant recovery decisions. `unknown` must not be interpreted as safe.
4. **Event acknowledgment, action completion report, safety verification, and explicit lease cleanup remain separate.**
5. **Local atomicity is not distributed atomicity.** SQLite transaction success cannot atomically commit a motor action, bus command or remote controller state.
6. **Clock, identity, schema migration and replay protection need target-specific rules.** A caller-provided logical timestamp or generation is not authenticated by these prototypes.

## Validated vs not yet validated

Validated in the PC prototype: local SQLite atomic commit/rollback around five record kinds, optimistic revision rejection, delivery lease fencing, process termination at selected boundaries, and read-only restart reconciliation. Each was tested with disposable databases and synthetic data.

Not validated: physical power loss, flash wear, corruption recovery, cross-device coordination, clock reset/skew, persistent authority reconstruction, real hardware STOP, and any implementation-independent storage API. `AtomicState` and `RestartReconciliation` currently use separate representations; integration is a future experiment.

## Next design/validation steps

1. Test an adapter between atomic snapshots and read-only reconciliation **without** assuming SQLite in the domain-level API.
2. Specify minimum persistent fields and reboot recovery decisions separately for PC/SBC, Main Controller and Forma Controller.
3. Evaluate failure modes of each target storage medium and its timing impact before selecting a production implementation.

Related synthesis: [Forma Unit cross-prototype boundaries](forma-unit-cross-prototype-boundaries.md).
