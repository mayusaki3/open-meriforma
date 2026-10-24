# Suite 66-I — Forma communication protocol requirements (design review)

Status: PROVISIONAL / DESIGN ONLY (2026-10-24). No implementation or 66-I PASS claim.
Scope: Main/Receiver ↔ Forma control/maintenance boundary, drawing on suites 50–65 and 66-A–H.
Reference: HLDocS v0.6.1; this review note is **not** a formal HLDocS specification or testspec.

## 1. Safety and authority boundaries
- Each Forma independently validates maintenance state, clearance, operation scope, mechanical interference, aggregate load, active generation and local faults. Main/Receiver may request, never override.
- Normal group control and maintenance control are distinct mutually exclusive modes. Maintenance entry revokes group authority and denies normal drive. Maintenance exit invalidates maintenance clearance and all outstanding grants.
- Suite 65 receiver group gate is optional for legacy compatibility; this is a **bypass risk**. Production paths MUST require the applicable group gate; no absent-gate permissive default.
- Logical acceptance of a command, a stop request, or a timeout does **not** prove actuator power has been removed. A Forma-local watchdog/drive-inhibit path must be verified independently of Main.

## 2. Provisional wire envelope (not frozen)
| Field | Purpose | Mandatory constraint |
| --- | --- | --- |
| protocol_version | reject incompatible peers | exact supported version; fail closed |
| source_id, destination_forma_id | explicit routing/identity | authenticated and bound to configured peer |
| boot_epoch / session_generation | separate restart and link generations | unique, authenticated, rollback-resistant lifecycle |
| message_type | heartbeat, maintenance entry/exit, clearance, authorize/start/finish, stop, ack, fault | strict allowlist; mode-specific |
| request_id | correlate one-shot request and response | unique per sender+epoch, bounded history |
| sequence | anti-replay/order | monotonic per authenticated sender+epoch; rollover policy required |
| operation_id, scope | scoped authorization | target/mode/bounds; policy-specific additional constraints |
| deadline / freshness | reject delayed commands | monotonic local receive clock; bounded skew assumptions |
| authorization_reference | bind start to issued approval | binds Forma, epoch, session, clearance revision, operation and scope |
| integrity/authentication | prevent spoof/tampering | verify **before** state transitions or heartbeat refresh |
| response_status | accepted/rejected/invalidated and reason | ACK is not evidence of physical actuation/stop |

No encoding, bit width, CAN-FD frame fragmentation, cryptographic primitive, key management, or wire compatibility is selected here.

## 3. Message processing order (normative design intent)
1. Validate frame length, version, fragmentation/reassembly completeness and message schema.
2. Authenticate source, destination, generation and integrity; reject unauthenticated messages **without refreshing liveness**.
3. Check Forma-local watchdog deadline using monotonic receive time; at exact deadline, timeout wins.
4. Check generation/session and replay/sequence/request-ID ledger; reject stale or duplicate messages.
5. Check mode-specific authority: normal group gate **or** maintenance clearance plus scoped one-shot grant.
6. Evaluate Forma-local limits and runtime safety evidence; only then consider control execution.
7. Record result and audit evidence. ACK means protocol decision only, not motor feedback.

### Fragmentation
- A partial CAN-FD transfer is never a command. Bind every fragment to source, generation, transfer ID, fragment index/count and payload length/integrity.
- Expired, conflicting, duplicated or incomplete reassembly is discarded; a late final fragment must not revive it.
- Resource exhaustion must fail closed (bounded buffer, per-source quota, timeout).

## 4. Failure and recovery policy
| Condition | Required behavior |
| --- | --- |
| Missing heartbeat / bus-off / link loss | Forma-local watchdog invalidates grants, stops applicable drive; no Main-only dependency |
| Delayed, duplicated, reordered message | reject stale/replayed operation; never extend liveness on invalid traffic |
| Authentication failure / bad integrity | reject without extending watchdog or consuming valid grant |
| Peer restart / epoch change | invalidate old grants; require explicit rebind and clearance |
| Safety evidence lost / unknown telemetry | stop affected operations only if Forma can prove isolation; otherwise all |
| Stop-latched unit reconnects | remain stopped; reconnection cannot reset latch |
| Safe recovery | physical stop confirmation, fault diagnosis, operator/service policy, fresh authenticated epoch, fresh clearance and new operation grants; no automatic rearm |
| Coherent rollback of ordinary storage | not solved by SQLite integrity checks; requires independent trusted monotonic witness or equivalent trust anchor |

## 5. Gaps found in synthetic prototypes
- 66-F/G/H use caller-supplied strings and counters, no authentication, key rollover, or trusted monotonic epoch.
- 66-H uses strictly increasing integer sequence numbers without wrap handling; its queue is unbounded and its event loop is serialized.
- 66-G's `recover()` swaps in a fresh in-memory fixture after evidence checks. This is **not** a physical recovery protocol, verified drive-inhibit reset, or attestation.
- 66-G `receive()` refreshes activity for successful operations only, while heartbeat has separate handling; the production liveness definition must be explicit.
- 66-F reserves rejected request IDs in a process-local unbounded set; durable/bounded replay policy and epoch scope are unresolved.
- 66-H packets do not model authenticated ACK, malicious sources, fragmentation, bus arbitration, bus-off or concurrency.
- Suites 50–65 explore receiver fragments, replay, generation registry, durable witness, group commit; suite 65 gate is optional. Integration into one mandatory production command path is not verified.
- Some runtime controls are checked only at authorize/start; continuous local enforcement and actual motor inhibit need independent tests.

## 6. Design gates before wire/firmware implementation
- [ ] Define topology: Main ↔ Receiver ↔ Forma, trust zones, independent watchdog ownership, power-cut responsibility.
- [ ] Select transport (including CAN-FD bus loading and fragmentation) and maximum payload size.
- [ ] Define authenticated peer enrollment, provisioning, key storage, rotation, revocation and anti-rollback epoch ownership.
- [ ] Define numeric protocol fields, byte order, serialization, length bounds, error codes, replay window and wrap/exhaustion.
- [ ] Establish quantitative watchdog/heartbeat/deadline budgets from measured worst-case bus and scheduling delays.
- [ ] Define local safety state machine, verified STOP feedback, independent power inhibit, service recovery authorization.
- [ ] Make normal group and maintenance gates mandatory and non-bypassable in the production receiver.
- [ ] Map suites 50–65 and 66-A–H to a unified end-to-end traceability matrix.
- [ ] Add fault-injection tests for malformed/authenticated packets, reassembly, replay exhaustion, concurrency, bus-off, brownout, reboot and real hardware stop.
- [ ] Review HLDocS v0.6.1 prerequisites and create formal spec/testspec only after architecture choices are approved.

## 7. Next
66-J should be a **design gate**, not automatic implementation: decide transport/topology, authenticated session ownership and watchdog/STOP responsibilities first. No physical safety or cryptographic security claim from 98/98 synthetic PASS.
