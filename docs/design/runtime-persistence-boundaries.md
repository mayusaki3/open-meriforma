# Runtime Persistence Boundaries — Candidate Design

Status: **design clarification, not a storage standard or implementation mandate** (2026-10-09).

## Purpose and evidence

The [Runtime Invalidation Events prototype](../../prototype/runtime-invalidation-events/VALIDATION.md) has user-confirmed PASS results for twenty-two test suites, including local SQLite delivery, leases, process termination, restart reconciliation, and atomic snapshots. These results establish properties of **those reference implementations only**, not universal runtime guarantees.

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

Not validated: physical power loss, flash wear, corruption recovery, cross-device coordination, clock reset/skew, persistent authority reconstruction, real hardware STOP, and any implementation-independent storage API. `AtomicState` and `RestartReconciliation` retain separate storage representations; a storage-neutral `SnapshotReconciliation` adapter now evaluates atomic snapshots with an extracted pure evaluator. The adapter is prototype-level and is not a standardized persistence API.

## Next design/validation steps

1. Specify minimum persistent fields and reboot recovery decisions separately for PC/SBC, Main Controller and Forma Controller.
2. Test the provisional classification and reboot decisions with a storage-neutral model, including invalid/corrupt/stale configuration and authority records.
3. Evaluate failure modes of each target storage medium and its timing impact before selecting a production implementation.

Related synthesis: [Forma Unit cross-prototype boundaries](forma-unit-cross-prototype-boundaries.md).

## Candidate information classification and reboot decisions (2026-10-11)

These are **design candidates**, not a mandated storage schema. “Persistent” means an implementation *may* retain a record; it does not mean it is valid or authoritative after restart.

| Information | PC / SBC | Main Controller MCU | Forma Controller MCU | After restart |
| --- | --- | --- | --- | --- |
| Device identity, hardware configuration, compatible firmware/schema version | Candidate persistent | Candidate persistent | Candidate persistent | Check identity, schema and hardware compatibility before use |
| Calibration, mechanical limits and local device parameters | Candidate persistent if owned | Candidate persistent where owned | Candidate persistent where owned | Validate integrity, range, device binding and version; otherwise reject/require recalibration |
| Event/ACK, delivery retry and action reports | Candidate persistent for diagnostics/delivery | Optional minimal diagnostic record | Not required by default | History only; revalidate current identity, delivery state and time assumptions; never infer STOP |
| Verification samples and STOP evidence | Candidate persistent history | Optional bounded diagnostics | Optional local diagnostics | Historical only; new physical observation required for current safety |
| Execution activity, active control ownership, resource/object-use Lease | May log historical state | Volatile live authority | Volatile live authority | **Never restore as active**; require fresh discovery, checks and explicit authorization |
| Health, graph reachability, observation freshness and current constraints | Cached for diagnosis | Volatile | Volatile | **Reobserve/recompute**; old “healthy” or “reachable” status is not current |
| Runtime clock, generation/fencing and replay/dedup state | Candidate persistent with explicit epoch design | Target-dependent | Target-dependent | Old timestamps/epochs are untrusted until clock, boot epoch and peer identity are re-established |

### Minimum candidate interface boundary

- **SnapshotReader**: `read(key)` returns missing, a versioned snapshot, or an explicit read error. A snapshot includes an integrity-checked record and a revision; how that integrity is established is implementation-specific.
- **SnapshotWriter** (only when required): compare-and-write with an expected revision, returning a committed revision or a conflict/error. Crash atomicity must be verified for the target medium; do not assume SQLite semantics for Flash/FRAM.
- **RuntimeReconciler**: pure interpretation of records plus *current* identity, generation, compatibility and observations; returns historical assessment and requirements for fresh validation, **not control commands**.
- **Safety controller**: independent of SnapshotReader/Writer availability or latency. It never waits for persistent I/O to initiate a required safe response.

A common abstract operation does not require every MCU to implement it. In particular, no generic “restore authority” or “resume execution” operation belongs in the persistence interface.

### Candidate boot sequence

1. Enter the device-specific non-actuating/controlled safe startup behavior, independent of persistent I/O.
2. Read and validate only locally needed configuration and calibration; reject missing/corrupt/incompatible values.
3. Establish fresh boot epoch, device identity, communication and actual hardware/graph/Health/Constraint observations.
4. Treat persisted Execution/Lease/STOP verification as **historical only**; do not reinstate command authority.
5. Require explicit higher-level authorization and live readiness/safety checks before any new execution.

**Unresolved:** exactly which identity/calibration fields each controller owns, safe startup behavior for each actuator, power-fail storage guarantees, write frequency/wear, clock continuity, firmware migration, authenticated peer epochs and distributed recovery. These require hardware-specific decisions and tests.

## Candidate Main / Forma boot authorization model (2026-10-11)

The [Boot Safety prototype](../../prototype/runtime-invalidation-events/README.md)
models separate `main` and `forma` boot gates, without hardware actuation.
Both begin without command eligibility. A candidate authorization requires
validated configuration and calibration, local safety checks, communication,
peer identity and boot epoch, fresh observations and an explicit request.
Restart, communication loss, peer epoch change or failed calibration invalidates
eligibility; previous execution rights and leases are never reinstated.

**Responsibility distinction:** Main Controller is a candidate coordinator of
robot-wide readiness and command authority; each Forma Controller is responsible
for its own local startup checks and actuator-specific safe behavior. Main's
readiness report must not substitute for Forma's local checks, and Forma's local
readiness alone must not grant robot-wide authority. The prototype currently
checks the same abstract predicates for both roles; the actual ownership,
communication timeout, watchdog, power stage behavior, and inter-controller
handshake remain to be designed and verified on hardware.

## Candidate Main–Forma coordinated boot (2026-10-11)

The [coordinated boot prototype](../../prototype/runtime-invalidation-events/README.md)
requires both Main and Forma boot gates to validate their local predicates,
observe each other's boot epoch and obtain explicit authorization before
reporting *advisory* coordinated eligibility. Either controller's local safety
loss, communication loss or restart invalidates the pair. An eligible Main
alone cannot override an unready Forma. The prototype is a single-process
model; it does not provide distributed atomic handshakes, watchdog timing,
a physical motor-inhibit signal or real CAN-FD delivery guarantees.

## Candidate multi-Forma heartbeat monitor (2026-10-11)

A new synthetic [heartbeat prototype](../../prototype/runtime-invalidation-events/README.md)
checks all required Forma peers, heartbeat age, per-peer boot epoch and
monotonically increasing message sequence. Timeout or local readiness loss
invalidates coordinated eligibility; receiving new heartbeats does **not**
automatically reauthorize execution. Main reboot clears its local peer history.

Limitations: caller-provided time/epochs and `ready` flags are not authenticated;
old messages could be replayed after Main loses its peer history. The monitor
is not a physical watchdog or real-time bus implementation. Production design
must specify peer-epoch continuity, authenticated identity or replay fencing,
clock reset handling, deadlines and behavior for optional vs required units.

## Candidate reboot-fenced communication sessions (2026-10-12)

The [session prototype](../../prototype/runtime-invalidation-events/README.md)
separates Main boot identity/challenge from Forma boot identity and a
per-link session identifier. A new Main challenge invalidates messages from
prior sessions; a single Forma session change invalidates coordinated
eligibility until explicit reauthorization. The model assumes challenge
uniqueness and trustworthy peer identities; an actual implementation needs
cryptographic authentication or equivalent trusted replay fencing and a
specified boot-ID persistence/reset policy. No physical STOP is verified.

## Candidate transport-neutral message boundary (2026-10-12)

The [protocol boundary prototype](../../prototype/runtime-invalidation-events/README.md)
passes strictly validated synthetic messages into separate session and
heartbeat monitors. The receiving side checks peer/session identity and
monotonic sequence, while link freshness gates advisory authorization.
A timeout must invalidate authority **before** a recovery heartbeat can
be considered. This is an in-process Python dictionary interface, not a
standard wire schema or an implementation of CAN-FD, RS485, authenticated
messages, network timing, or physical safety outputs.

## Candidate binary message envelope (2026-10-12)

The [binary envelope prototype](../../prototype/runtime-invalidation-events/README.md)
serializes a versioned, transport-neutral logical message. It validates
identifier lengths, sequence range, total payload length and CRC32 before
passing a decoded dictionary to the existing protocol boundary. The 256-byte
limit is provisional and exceeds one CAN-FD data frame; transport-specific
fragmentation/reassembly, per-frame timing, bus identifiers, arbitration,
RS485 framing, message authentication and safety behavior remain unimplemented.
CRC32 detects accidental corruption, not malicious modification.

## Candidate CAN-FD fragmentation boundary (2026-10-12)

The [fragment adapter](../../prototype/runtime-invalidation-events/README.md)
uses a provisional 9-byte header and up to 55 bytes of data in each 64-byte
CAN-FD-sized payload. Transfer identity combines a trusted peer/source and
16-bit transfer ID. Reassembly is bounded and timed out; complete envelopes
are still subject to CRC32 and session/heartbeat checks. CAN arbitration IDs,
DLC encoding, retransmission, bus-off handling, transfer-ID reuse/wraparound,
source authentication and physical motor control are not implemented.

## Candidate CAN transport fault supervision (2026-10-12)

The [fault supervisor prototype](../../prototype/runtime-invalidation-events/README.md)
models bounded whole-transfer retry, in-session transfer-ID nonreuse and
synthetic bus-off/recovery. Bus-off invalidates coordinated authorization and
clears in-flight transfers. Recovery does not restore authority: fresh Main
challenge, Forma sessions, heartbeat observations and explicit authorization
are required. This is not hardware bus-off handling, an interoperable retry
protocol, cryptographic replay protection or verified physical STOP.

## Candidate CAN scheduling boundary (2026-10-12)

The [synthetic scheduler](../../prototype/runtime-invalidation-events/README.md)
models priority ordering (safety > heartbeat > control > diagnostics), bounded
queue shedding, approximate two-phase bitrate airtime and 100 Hz heartbeat
traffic. Missing/deadline-late heartbeat invalidates authorization. Bit stuffing,
arbitration contention, real DLC encoding, ISR latency and hardware STOP
behavior remain outside this prototype; the approximate timings are not
physical bus-capacity evidence.

## Integrated synthetic Main–Forma transport boundary (2026-10-12)

The [integrated pipeline](../../prototype/runtime-invalidation-events/README.md)
connects binary heartbeat envelopes, synthetic CAN-FD fragmentation,
priority-based dispatch, reassembly and peer session checks. A queue overflow,
heartbeat timeout or synthetic bus-off revokes authorization; new Main
challenge, peer sessions and explicit reauthorization are required after
bus-off. This does not verify hardware timing, bus-level interoperability,
actuator shutdown or a physical safe state.
