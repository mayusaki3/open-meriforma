# Suite 61 — Multi-Forma witness ownership review

Status: **provisional architecture decision / review required**, not a hardware validation or security implementation. Read with TRUSTED_WITNESS_REQUIREMENTS.md.

## Provisional decision

**Each Forma owns and checks its own protected generation witness**; Main coordinates a *group authorization* but is not the sole anti-rollback trust anchor. An ordinary Main-side SQLite history is a diagnostic/cache, never the authoritative witness. Selection of a specific MCU, secure element, or counter implementation remains open pending hardware evidence and cost analysis.

Rationale: a Forma must be able to refuse stale generations independently if Main restarts, loses state, or is replaced. A single Main witness cannot by itself establish each Forma's local freshness. Independent counters avoid making the entire group depend on a shared writable host file.

## Identity and generation tuple

A future authenticated reservation must bind at least:
- immutable Forma device identity and provisioning-domain identity;
- Main controller identity and authorized group/session identity;
- **Forma-local** monotonic sequence (not the existing boot/challenge string);
- a unique generation nonce/challenge and a cryptographically authenticated authorization transcript;
- the set of required Forma peers and the group authorization epoch.

The exact encoding, cryptography, key ownership and wire format are **not selected**. Current suite 58 SimulatedWitness and boot/challenge strings do not provide these guarantees.

## Group coordination rule (proposed)

1. Each required Forma independently verifies its own witness, identity, and explicit authorization. A local success does not authorize the group.
2. Main gathers acknowledgments tied to the *same* proposed group generation and required peer set.
3. Group authority is permitted only when **all** required Forma peers have successfully committed their local generation reservation and the receiver-side group-commit proof is validated.
4. Missing, stale, mismatched, timed-out or failed peers keep the **entire group denied**. No partial motion or implicit peer exclusion.
5. A peer that advanced its witness but did not commit its local history stays denied until an authenticated service recovery process. Other peers may have advanced; their counters must **never** be decremented to match.
6. Reattempting the same group generation after ambiguous failure is not automatically allowed. Start a fresh, authenticated group generation only if each required peer's local state and policy allow it; otherwise require service intervention.
7. Authority revocation and physical actuator inhibit must be enforced locally at every Forma. A Main broadcast alone is insufficient.

This is a proposed protocol contract. No distributed atomic commit is claimed: partial reservations and stranded counters are expected failure states.

## Failure-state matrix

| Scenario | Local Forma | Group |
| --- | --- | --- |
| All peers authenticated, committed and fresh | Each may become eligible after explicit group authorization | Eligible |
| One peer witness ahead of local history | That peer denied | Denied |
| One peer witness behind or unavailable | That peer denied | Denied |
| One peer reservation times out after witness advance | Outcome uncertain; peer denied | Denied |
| Main loses history / restarts | No automatic local reauthorization | Denied until fresh explicit authorization |
| One Forma replaced / rekeyed | Old identity and generation not accepted | Denied pending authenticated re-provision and new group generation |
| Peer list differs between acknowledgments | Reject group transcript | Denied |
| Group authorization is revoked | Every receiver independently denies | Denied |

## Acceptance gates before hardware selection

- Confirm whether each Forma can host a genuinely protected monotonic primitive with acceptable cost, endurance, reset behavior and write latency.
- Specify group membership and identity lifecycle; define what counts as a required peer and how membership changes are authorized.
- Specify an authenticated reservation/ack/group-commit transcript, replay limits, and timeout/retry semantics.
- Measure simultaneous startup, power-loss during counter advance, missing peer, bus-off, and physical output inhibition on hardware.
- Define secure service recovery, key rotation, device replacement, counter exhaustion, and operator audit.

## Current limitations

This document does not implement a multi-Forma protocol, hardware monotonicity, cryptographic identity, authenticated acknowledgments, physical CAN-FD arbitration, or motor STOP. Suites 1–60 are synthetic; suite 61 is a design review artifact only.
