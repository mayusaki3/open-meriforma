# Suite 66-J — Communication and safety responsibility architecture

Status: PROPOSED DESIGN BASELINE; decisions requiring hardware/protocol evidence remain OPEN.
Date: 2026-10-26. Design-only, no 66-J tests or hardware implementation.
Related: FORMA_COMMUNICATION_PROTOCOL_REQUIREMENTS.md (66-I); suites 50–65 and 66-A–H.
This is a working design note, not an HLDocS v0.6.1-compliant formal spec.

## 1. Functional topology and trust boundaries

```text
Main Controller (motion planning / user command / group coordination)
    |
    | authenticated logical requests; no direct motor authority
    v
Receiver / transport boundary (routing, reassembly, peer admission,
    anti-replay, generation checks, mandatory normal/maintenance gating)
    |
    | candidate CAN-FD physical bus; NOT YET SELECTED/VERIFIED
    +-----------+------------+-------------+
    v           v            v
Forma A      Forma B       Forma N
 [local policy + operation ledger + local watchdog + STOP latch]
    |           |            |
    v           v            v
 actuator drivers / independent drive-inhibit (physical design OPEN)
```

A Receiver may be logically co-located with Main or distributed in each Forma. It is **not** assumed to be an independently trusted safety controller merely because it is drawn as a separate block. No network failure may cause a Forma to continue indefinitely on stale authority.

## 2. Decision authority (proposed)
| Responsibility | Main | Receiver | Forma | External hardware/service |
| --- | --- | --- | --- | --- |
| Group intent / requested movement | owns | forwards | validates | — |
| Peer enrollment / session admission | requests | validates | independently validates | trusted credential/epoch anchor TBD |
| Fragment assembly / routing | — | owns where implemented | independently validates completed command | — |
| Normal group authority | coordinates | mandatory gate | mandatory local verification | — |
| Maintenance clearance | requests | must not bypass | **final decision** | safety evidence sensors TBD |
| Per-operation scope and concurrent limits | requests | checks envelope | **final decision and continuous checks** | — |
| Link/watchdog timeout | may monitor | may monitor | **independent mandatory monitor** | independent inhibit TBD |
| STOP / latch | may request | forwards | **locally triggers** | **physical inhibit** TBD |
| Restart/recovery | coordinates | new authenticated session | **local re-evaluation** | operator/service authorization TBD |

Receiver ACCEPT/ACK is only a protocol decision; a separate sensor or drive feedback is required to claim physical stop. Main power loss must not disable the local watchdog or safety inhibit.

## 3. Proposed session and generation ownership
- Distinguish **device identity**, **boot epoch**, **authenticated link session**, and **operation/clearance revision**. Do not reuse a single untrusted string as all four.
- A trusted provisioned identity is bound to each Forma and its designated authorized Main/Receiver peers. Enrollment and replacement/revocation require an explicit service policy.
- The Forma must not accept a generation asserted by Main as authentic without local verification. Boot epochs must be unique and rollback-resistant within the threat model; the protected monotonic witness in suites 58–61 is an unimplemented hardware dependency.
- A session handshake must bind both peers' identities, protocol version, fresh nonces/epochs, negotiated capabilities, and authorization policy to authenticated messages. Cryptographic mechanism and key lifecycle are OPEN; no algorithm selected.
- Reboot, peer identity change, timeout, bus-off, generation change, or detected rollback invalidates outstanding grants and enters STOP/inhibited mode.
- Request IDs and sequence numbers are per authenticated sender+session, bounded; exhaustion or wrap without approved rollover handshake **fails closed**.
- Session establishment means *communication ready*, not *drive authorized*. Clearance and each operation authorization remain separate.

## 4. Forma-local safety state proposal
```text
UNBOUND / BOOT_SAFE  -- authenticated session --> CONNECTED_INHIBITED
CONNECTED_INHIBITED -- explicit maintenance entry --> MAINTENANCE_DENIED
MAINTENANCE_DENIED -- local verified clearance --> MAINTENANCE_CLEARED
MAINTENANCE_CLEARED -- scoped grant --> OPERATION_ELIGIBLE
OPERATION_ELIGIBLE -- local final checks --> RUNNING
ANY ACTIVE -- fault / timeout / peer change --> STOP_LATCHED
STOP_LATCHED -- verified physical stop + service recovery --> CONNECTED_INHIBITED
```
- All active transitions must recheck watchdog, local policy, measured limits, mode and authorization immediately before actuation and while running.
- Local isolation is permitted only with positive proof that other operations remain safe; unknown fault impact stops the entire Forma.
- The STOP_LATCHED -> CONNECTED_INHIBITED transition is **not implemented** by 66-G's fixture replacement. Actual latch reset authority, electrical inhibit design and physical confirmation are OPEN.
- Normal group operation is a separate mutually exclusive branch from maintenance, with mandatory group authorization at Receiver **and** Forma. Do not treat clearance as permission to run motors.

## 5. Communication-loss timing budget (not numerical yet)
Define: T_frame (arbitration/fragmentation), T_queue (bounded priority delay), T_verify (auth+parse), T_schedule (worst-case task jitter), T_detect (Forma-local watchdog), T_inhibit (drive-disable propagation), T_mechanical (verified safe physical response).

Safety assessment must bound worst-case T_detect + T_inhibit + T_mechanical against hazard-specific limits; request-to-action latency must bound T_frame + T_queue + T_verify + T_schedule. No fixed timeout is chosen before measurements and hazard analysis. A delayed but authenticated heartbeat must not reset a timer after expiration; deadline equality is expired. Monotonic receive time is authoritative; do not depend on wall-clock synchronization for local timeout.

## 6. Cross-suite integration requirements
- Suites 50–52: reassembly and replay must be enforced on *every* production command path, including maintenance.
- Suites 53–60: epoch persistence and coherent rollback are security boundaries, not solved by SQLite or a plain file witness.
- Suites 62–65: peer-local group commitment must be mandatory in production; optional legacy group gate is a bypass.
- Suites 66-A–D: maintenance state, scoped grants, interference/load limits and stop scope remain Forma-local.
- Suites 66-E–H: routing, link generation, heartbeat and packet ordering are synthetic; integrate only after authenticated session and watchdog design.
- The exact wire payload, fragmentation, message authentication, bus scheduling, retry policy and boot/recovery handshakes are deferred until transport choice.

## 7. Architecture decisions and gates
| ID | Decision | State |
| --- | --- | --- |
| 66-J-D01 | Main requests, Forma decides locally; Receiver never overrides | PROPOSED BASELINE |
| 66-J-D02 | Normal group and maintenance gates mandatory and mutually exclusive | PROPOSED BASELINE |
| 66-J-D03 | Forma-local watchdog and latched STOP, independent of Main | PROPOSED BASELINE |
| 66-J-D04 | Authenticated peer/session and rollback-resistant boot epoch | REQUIRED, TRUST ANCHOR OPEN |
| 66-J-D05 | CAN-FD for Forma bus | CANDIDATE, NOT SELECTED |
| 66-J-D06 | Physical inhibit circuitry and STOP confirmation | OPEN HARDWARE GATE |
| 66-J-D07 | Quantitative timing/timeout limits | OPEN MEASUREMENT GATE |
| 66-J-D08 | Cryptographic protocol, keys, provisioning and replacement | OPEN SECURITY GATE |
| 66-J-D09 | STOP latch recovery requiring independent confirmation | REQUIRED, RECOVERY POLICY OPEN |

## 8. Next design gate: 66-K
Choose (a) physical topology and Receiver placement, (b) Forma controller/watchdog/inhibit hardware assumptions, (c) authentication/epoch trust anchor options. Only then define protocol encoding and formal HLDocS documents. No claim of verified STOP, authenticated wire authority, or real-time performance.
