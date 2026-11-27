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
| sequence | anti-replay/order | monotonic per authenticated sender + logical destination + session/epoch; rollover policy required (Section 9) |
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

## 8. Approved shared state reconciliation (2026-11-24)

When continuity or consistency of upper-owned state cannot be established, the lower unit queries its authoritative upper controller. Triggers include detected message gaps (using authenticated sequence/continuity evidence), link recovery, upper epoch change, local restart and detected state mismatch. This is shared by normal and maintenance operation, not a maintenance-specific lease.

- Mark affected state unconfirmed and deny dependent operations until authenticated reconciliation completes. Invalidate affected grants and re-evaluate running operations under the existing local safety policy; if impact cannot be isolated, apply the existing conservative stop policy. A gap is not automatically equivalent to a watchdog timeout.
- Query/response must be authenticated, fresh, correlated and bound to the applicable peer, epoch and state scope. Missing/invalid/stale responses cannot establish validity. Reconciliation must not accept a stale snapshot over a newer change.
- State reconciliation does not reset STOP, restore old grants, bypass K2 or replace watchdog enforcement. No user-driven periodic renewal is required.
- Message scope, sequence-gap semantics, response versioning, concurrent changes, retries and encoding remain open design details.

Maintenance example: Main owns session validity; Forma queries it when uncertain. Same confirmed session may retain BENCH; ended/replaced session clears old BENCH. Forma restart never restores old BENCH. Local clearance and final operation authorization remain Forma-local.

## 9. Approved sequence scope (option B, 2026-11-25)

Sequence continuity is managed independently per authenticated sender, logical destination and applicable session/epoch. Opposite directions are independent. Unicast, group and broadcast logical destinations have distinct sequence scopes; message types do not subdivide a scope. A message to another destination must not create a false gap. Apply Section 8 when continuity is lost. Request-ID uniqueness remains unchanged.

Initial sequence baseline, group membership changes, terminal missing messages and heartbeat continuity evidence (resolved in principle by Section 10), wrap/exhaustion, and exact gap/reordering semantics remain open; a heartbeat in another scope alone cannot prove continuity. No wire encoding or implementation is approved here.

## 10. Approved heartbeat continuity evidence (option B, 2026-11-25)

Reuse the individual authenticated heartbeat to carry the latest transmitted sequence watermark for each relevant logical destination scope (including group and broadcast). Compare against the receiver's established continuity state for the same scope/session/epoch. Evidence of a missing message triggers the shared reconciliation mechanism in Section 8, including when no further message is sent in that scope. Separate periodic heartbeat per logical destination and acknowledgement of every state-change notification are not mandatory.

A watermark is evidence of sender progress, not proof of receipt or state validity. A stale watermark cannot roll back receiver state or establish reconciliation. Scope membership, initial baseline, ordering between heartbeat and data, precise watermark semantics, bounded payload and timing remain open. Authentication, local watchdog and STOP/K2 requirements remain unchanged. No implementation or test execution.

## 11. Approved initial sequence baseline (option A, 2026-11-25)

Use the shared upper/lower state reconciliation mechanism (Section 8) to establish the initial sequence baseline at startup, reconnect, group entry, detected gap or epoch change. Obtain authoritative current state and its corresponding sequence baseline for the applicable logical destination/session/epoch. Do not infer the baseline from the first received message or require a separate initialization notification. Until state and baseline consistency is established, dependent operations remain denied. A baseline does not restore grants or release STOP/K2. Exact snapshot consistency, concurrent updates, ordering and membership transition mechanics remain open.

## 12. Approved reconciliation during concurrent state changes (option A, 2026-11-25)

The upper authority obtains a consistent snapshot of current state and corresponding sequence baseline(s). The lower unit compares authenticated, correlated snapshot responses and observed change notifications within their respective logical destination/session/epoch scopes. Apply only when consistency can be established; never roll back a newer observed state or treat a known outstanding gap as resolved by an older snapshot. If consistency cannot be established, query again and maintain dependent-operation restrictions. No dedicated notification buffer or suspension of upper state changes is mandatory. Snapshot application does not restore grants or release STOP/K2. Cross-scope consistency, exact comparison rules, retry bounds and timing remain open; no implementation or test execution.

## 13. Approved reconciliation retry policy (option B, 2026-11-25)

Progressively increase the reconciliation retry interval up to a bounded maximum, then continue at that interval while reconciliation remains necessary. No retry-count cutoff or operator action is required for context reconciliation itself. Maintain dependent-operation restrictions until consistency is established; watchdog, STOP and K2 remain independent. Reconciliation never automatically rearms drive. Initial interval, increase algorithm, maximum interval and quantitative timing remain subject to communication performance and safety validation. No implementation or test execution.

## 14. Approved deferral of generic state revision (option A, 2026-11-27)

Do not introduce a generic state revision at this stage. Preserve existing clearance revision, session, epoch, generation, sequence and request-ID responsibilities. Use existing local mode/authorization gates and shared reconciliation for uncertainty. Reconsider a state revision only when a concrete functional requirement cannot be satisfied by existing mechanisms. Cross-destination sequence numbers are not directly comparable; this decision does not establish ordering of conflicting writes across destinations. Such cases require explicit functional design before being allowed. No implementation or test execution.

## 15. Approved heartbeat/data ordering (option B, 2026-11-27)

When an authenticated heartbeat watermark indicates missing data in a matching scope/session/epoch, immediately mark affected state unconfirmed and apply Section 8 restrictions, grant invalidation and running-operation safety evaluation. Allow a bounded short wait for in-flight data before initiating reconciliation queries. If authenticated contiguous data arrives and establishes consistency within the wait, a query is unnecessary; otherwise initiate shared reconciliation and apply Section 13 retry policy. The wait must not delay independent watchdog, STOP or K2, or restore invalidated grants or automatically rearm. Quantitative wait duration and scheduling bounds remain open pending communication and safety validation. No implementation or test execution.
