# External Object Relation — Validation Record

Status: prototype concept validation; **not a finalized standard**.

## Scope
- Body Graph and World Graph remain separate; Interaction Relations connect them.
- Capability / Realization requirements evaluate Relations and Constraints independently.
- CapabilityExecution uses explicit start, validate, finish lifecycle; invalidation does not automatically restart.
- Body control leases and External Object Use rights are separate runtime domains.
- Observation may coexist with exclusive use; coordinated use shares only within the same prototype group.

## User-confirmed results (all foundation stages)
- Body–World and World–World relations, including loss and recovery: PASS.
- Constraint satisfied / unsatisfied / unknown (unknown fails closed): PASS.
- Execution rejection, invalidation, explicit finish, no automatic restart: PASS.
- Atomic body resource lease, conflict, retained lease until finish: PASS.
- Concurrent observation and control of the same external object: PASS.
- External object observe / exclusive / coordinated conflict rules: PASS.
- Independent object-use release and body resource lease release: PASS.

## Final user-confirmed tests
- Loss of object-use right invalidates active execution without releasing body control lease: PASS.
- Reacquiring object-use right does not reactivate invalidated execution: PASS.
- Simultaneous Relation loss and object-use loss produce distinct reasons: PASS.
- Explicit finish releases retained leases and object-use rights: PASS.
- Regression tests `test_external_relation.py` and `test_execution.py`: PASS (user run, 2026-10-09).

**Foundation validation status: COMPLETE.** This is a conceptual prototype milestone, not hardware, distributed arbitration, or safety validation.

Run:
```powershell
python .\test_external_relation.py
python .\test_execution.py
```

## Prototype-only choices and limits
- Modes `observe`, `exclusive`, `coordinated` and coordination group names are provisional.
- Object-use rights are runtime bookkeeping, **not** physical enforcement, safety action, or proof of object ownership.
- Revocation in tests is explicit manager release; distributed failure detection and timeouts are not implemented.
- Body and object-use acquisition is sequential with rollback on ordinary conflicts; not a distributed atomic transaction.
- Observation resources are declarative, not a real subscription or sensor-data pipeline.
- Object use is indexed by world-object ID; finer-grained contact, subobject, and shared load cases remain open.
- No automatic STOP, emergency handling, or ownership transfer is implied by invalidation.
