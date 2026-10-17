# Runtime Invalidation Events — Provisional Prototype Architecture

Status: implementation-derived technical overview, not an approved HLDocS specification or safety assurance.
Source of truth for observed behavior: code on develop, plus user-confirmed test outcomes in VALIDATION.md and LLM_Workspace/Worklog/runtime-invalidation-events.md.

## Purpose and scope
Synthetic Python reference exercises invalidation, evidence, recovery, restart reconciliation, Main/Forma session and heartbeat, CAN-FD-sized fragmentation, ACK/retry, shared bus behavior, and control authority revocation. It does not operate real actuators.

## Functional boundaries
- Event/action/recovery layer: event invalidation and acknowledgement are distinct from actual STOP and explicit lifecycle cleanup. A reported completed action does not prove physical safety.
- Evidence/persistence layer: synthetic safety evidence and SQLite-based PC reference tests; historical records cannot restore live authority.
- Session/protocol layer: forma_sessions.py, forma_heartbeat.py, protocol_boundary.py and wire_envelope.py track required peers, generation, Ready, sequence, and explicit authorization. Caller-supplied identity is not cryptographically authenticated.
- CAN transport layer: canfd_fragments.py, can_fault_supervisor.py, can_scheduler.py, integrated_can_link.py, shared_can_bus.py and causal_integrated_can.py simulate fragmented heartbeat, retry/ACK and a shared bus. Simulated airtime does not prove physical arbitration/timing.
- Control gating experiments: authority_command_gate.py (suite 43) stages synthetic commands; authority_can_scheduler.py (suite 44) gates a separate synthetic CanScheduler. Neither is integrated with SharedCanBus control dispatch or hardware.

## Safety-relevant invariants tested
- All required Forma peers must be fresh, Ready and in valid sessions before explicit authority is granted.
- Timeout, Ready=false, session replacement or bus-off can revoke coordinated authority.
- Recovered communication does not automatically reauthorize control.
- Pending synthetic commands are discarded after authority invalidation; stale generations must not replay.
- Test PASS proves only the enumerated simulated scenarios.

## Known limitations
No actual CAN controller, authenticated sender, MCU boot sequence, hard real-time scheduling, physical watchdog, motor drive inhibition, STOP actuation or independently verified physical safe state. SharedCanBus control-frame integration is not yet implemented.

## Test entry points
Run Python tests from this directory on Windows PowerShell. For current stage:
- python .\\test_authority_can_scheduler.py
- python .\\test_authority_command_race.py
- python .\\test_multi_forma_authority_monitor.py
- python .\\test_multi_forma_authority.py
Refer to VALIDATION.md for the broader suite history.

## Next work
Suite 45 should integrate control-frame gating with SharedCanBus's shared synthetic queue and verify pre-dispatch revocation, peer failure, bus-off fencing and heartbeat/ACK/control priority. Do not report this integration as completed until implemented and locally tested.

## Documentation status
This is a minimal provisional explanation to restore continuity. Formal HLDocS v0.6.1 spec/testspec structure, traceability and validation remain a separate pending task.
