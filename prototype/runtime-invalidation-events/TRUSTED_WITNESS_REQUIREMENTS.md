# Suite 61 — Trusted generation witness and recovery requirements (design gate)

Status: **requirements draft / review pending**. This is not a verified hardware implementation. Builds on suites 54–60; especially the demonstrated coherent two-store rollback vulnerability.

## Safety objective and trust boundary

A receiver must not accept a generation already authorized before restart, database replacement, or reprovisioning. The trusted witness must provide freshness that cannot be rolled back together with the host SQLite database. Merely matching two ordinary files, hashes, or copies is insufficient. The current boot/challenge generation string is not an authenticated or ordered monotonic identifier.

The **safety action** of any missing, invalid, uncertain or mismatched witness state is: deny generation binding and command acceptance; keep actuation inhibited by a separately verified hardware mechanism. The Python receiver model only demonstrates the software decision, not physical inhibition.

## Candidate trust anchors (not selected)

| Candidate | Required evidence / unresolved concern |
| --- | --- |
| MCU protected nonvolatile monotonic counter | Hardware write/erase endurance, anti-rollback protection, brownout atomicity, access control, secure boot interaction |
| Secure element monotonic counter | Authentic command channel, lifecycle/provisioning, counter exhaustion, power-loss semantics, failure handling |
| TPM / protected platform monotonic service | Platform availability and attachment to the correct Forma, reset/replacement behavior, interface latency |
| Host ordinary file or SQLite-only anchor | **Rejected as sole trust anchor**: coherent rollback of both stores is undetectable (suite 60) |

A protected counter alone does not authenticate Main, Forma, or the binding of a generation to the correct device. Device identity, message authentication, anti-replay, key storage and firmware trust must be separately specified.

## Required contract (proposed)

- **WIT-001 Freshness:** read the authenticated witness state; it cannot be decreased or reset by an ordinary host process or restore.
- **WIT-002 Scope:** identify which Forma/device and provisioning domain the counter belongs to. Prevent cross-device or cloned-history acceptance.
- **WIT-003 Ordering:** monotonic sequence is a separate integer from the current boot/challenge string. Define exhaustion and wrap policy (never silently wrap).
- **WIT-004 Advance:** each generation reservation advances witness before permitting receiver activation. On witness advance failure, deny.
- **WIT-005 Durable match:** persist the generation-to-sequence binding and SQLite anchor; permit receiver activation only after matching committed state is verified.
- **WIT-006 Mismatch:** if witness is ahead, behind, missing, malformed, or untrusted, deny startup/bind; no automatic repair, decrement or silent reinitialization.
- **WIT-007 Crash semantics:** distinguish 'advance definitely not performed', 'definitely performed', and 'outcome unknown'; unknown must deny until authenticated recovery.
- **WIT-008 Authority:** require authenticated Main-to-Forma authorization, explicit reauthorization, and independent receiver enforcement; counter agreement alone never grants authority.
- **WIT-009 Physical inhibit:** separately demonstrate motor output remains inhibited across boot, restart, link loss, witness failure, and recovery. Software-only checks do not satisfy this.
- **WIT-010 Provisioning:** initialization is explicit, authenticated, bound to device identity, auditable, and not available from normal command flow.
- **WIT-011 Recovery:** no reuse of previously authorized generations, including when a witness is ahead of SQLite. If safe recovery cannot be proven, remain inhibited and require service replacement/rekey procedure.
- **WIT-012 Resource limits:** measure endurance, wear, latency, counter capacity, flash use and memory budget on selected hardware.

## Recovery state matrix (proposed)

| Observed state | Automatic startup / bind | Required action |
| --- | --- | --- |
| Witness and committed anchor match; authenticated device and generation | Eligible for normal explicit authorization checks only | Continue normal gating; never auto-authorize |
| Witness ahead of anchor | Deny | Authenticated service investigation; do not decrement witness |
| Witness behind anchor | Deny | Treat as possible rollback or compromised witness |
| Witness unavailable, corrupt, or authenticity uncertain | Deny | Diagnose hardware / key / transport failure |
| Witness advance outcome unknown after interruption | Deny | Authenticated recovery protocol or replacement |
| Both untrusted stores restored coherently | Not detectable by present fixture | Requires protected independent witness |
| Device replaced or factory reset | Deny previous identity and history | Authenticated fresh provisioning domain and key lifecycle |

## Verification evidence required before hardware safety claims

1. Select concrete hardware and threat model: adversary capabilities, device physical access, host privileges, cloning, firmware replacement and rollback.
2. Vendor specification or measured evidence for protected monotonicity, write atomicity, endurance, reset semantics, authenticated read/advance, and secure boot/key storage.
3. Hardware-in-the-loop tests for brownout during advance and database commit, reboot and storage replacement, identity mismatch, counter exhaustion, and authenticated recovery.
4. Actual CAN-FD authentication/authority validation and actuator inhibit/STOP verification under faults.
5. Formal HLDocS specification, test specification, traceability and acceptance review after checking the applicable templates.

## Open design decisions

- Which component owns the authoritative counter: each Forma, Main, or an independent module? What is the multi-Forma consistency rule?
- Can a witness advance be proven committed when a request times out? What is the safe resynchronization protocol?
- What identity/key rollover and device replacement rules prevent reuse of an old generation?
- How are service credentials, operator approval, audit logs, and recovery authorization protected?
- Is counter endurance sufficient for expected generation churn and service lifetime?

No production witness, secure key infrastructure, authenticated recovery, or real hardware STOP is implemented by this document.
