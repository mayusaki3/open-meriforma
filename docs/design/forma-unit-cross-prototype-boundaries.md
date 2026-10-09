# Forma Unit — Cross-Prototype Concept and Runtime Boundary Review

Status: **design synthesis / candidate concepts only**. No schema, API names, state names, or protocols are standardized by this document.

## Evidence base

- [Virtual Foot](../../prototype/virtual-foot/VALIDATION.md): internal Elements, Functional Groups, Control vs Observation, handoff, declaration vs availability.
- [Virtual Body Graph](../../prototype/virtual-body-graph/VALIDATION.md): peer connections, multi-hop reachability, cross-unit capabilities, readiness, execution lease, structured conditions, Health and Constraint.
- [Physical–Virtual Mapping](../../prototype/physical-virtual-mapping/VALIDATION.md): independent endpoints, partial/non-1:1 mapping, authority, freshness/skew/generation.
- [External Object Relation](../../prototype/external-object-relation/VALIDATION.md): separate World Graph, interaction relations, realizations, object-use arbitration and execution invalidation.
- [Runtime Invalidation Events](../../prototype/runtime-invalidation-events/VALIDATION.md): user-confirmed five-suite PASS for cross-domain invalidation events, policy actions, synthetic STOP verification/evidence and advisory recovery policy.

## Candidate separation of responsibilities

| Domain | Relatively stable description / definition | Dynamic Runtime state |
| --- | --- | --- |
| Unit structure | Unit / Element / Port / declared resources | Installed connections, graph reachability |
| Capability | Capability declaration, realization requirements | Availability and structured reasons |
| Control | Declared control resources / profiles | Controller ownership, execution-scoped leases, handoff |
| Observation | Declared sources and consumers | Source availability, subscriptions, sample validity |
| Execution | Required resources, relations, constraints | Readiness, atomic local acquire, active/invalidated/finished |
| World interaction | Body/World entity identities, relation vocabulary | Observed relations, object-use rights, invalidation |
| Twin | Physical and Virtual endpoint identities, mapping configuration | Endpoint usability, authority, alignment/comparability |
| Health / Constraint | Condition definitions and safety boundaries | Current Health and Constraint evaluation |
| Invalidation event | Candidate event vocabulary | Emitted/pending/acknowledged notification, lifecycle-scoped deduplication |
| Policy action | Candidate request and report vocabulary | Requested/accepted/executing/completed/failed, independent of execution and leases |
| Safety verification | Candidate STOP evidence requirements | Synthetic verified/not_verified/unknown with freshness/scope/integrity/duration checks |
| Recovery policy | Candidate escalation and reauthorization rules | Advisory hold/escalate/reobserve recommendation; no automatic resume |

A Unit need not contain electronics; a Host need not itself be a Unit. The graph need not be a humanoid parent-child tree. Physical/Virtual is independent of implementation class; a Twin is a mapping relationship.

## Candidate runtime sequence

```text
Definition / Instance / Graph / World / Twin mapping
                  |
                  v
        Capability Declaration
                  |
                  v
   Availability + structured condition results
                  |
                  v
   Readiness (requester / execution scoped)
                  |
                  v
   Acquire required control/object-use rights
                  |
                  v
             Active Execution
                  |
                  v
   Continuous condition + authority validation
           /                 \
        valid              invalid
          |                   |
       continue          Invalidated
                              |
                    explicit policy / finish
```

The local body-resource acquire is atomic in its prototype. Body leases and external-object rights are separate managers; their combined acquisition with rollback is **not** a distributed transaction. Readiness does not reserve resources. Invalidation does not automatically STOP, release, hand off, or restart.

## Candidate API boundaries (not signatures)

1. **Definition/Instance queries**: inspect identity, declared structure, interfaces, capabilities, and installed configuration; preserve unknown vs absent.
2. **Graph operations**: attach/detach ports, inspect reachability; report changes without silently changing control ownership.
3. **Capability evaluation**: report declaration, availability, conditions/reasons independently of active execution.
4. **Runtime authority**: request/release execution-scoped control leases; manage observation subscriptions separately; explicit handoff.
5. **Execution lifecycle**: start/validate/invalidate/finish with explicit cleanup and higher-level safety policy.
6. **World interaction**: add/remove Body–World and World–World relations; evaluate realization constraints; arbitrate object use separately from Body control.
7. **Twin mapping**: configure mappings, assess endpoint/sample usability, evaluate divergence, and explicitly transfer command authority.
8. **Safety and recovery policy**: consume invalidation/Health/Constraint signals and decide stop, limp, retry, or transition. Prototype state changes do not implement these actions.
9. **Invalidation event delivery**: translate execution invalidation into a lifecycle-scoped notification, acknowledge separately from physical action or cleanup.
10. **Policy action tracking**: represent requested/accepted/executing/completed/failed as an advisory action lifecycle; a completion report does not prove safety.
11. **Safety evidence evaluation**: separately assess synthetic STOP observations, including freshness, scope, simulated integrity and time window; unknown is not verified.
12. **Recovery recommendation**: hold after verified STOP, escalate not_verified, seek evidence/fallback for unknown; never silently resume, hand off or release authority.

## Cross-prototype consistency observations

- Graph/Relation existence and runtime authority are independent in Body Graph, Twin Mapping, and World Interaction.
- A lost prerequisite invalidates an active execution/authority but does not automatically release ownership.
- Recovery of a prerequisite does not automatically reactivate execution or transfer authority.
- Control and observation have different sharing semantics.
- Capability availability, resource readiness, and execution activity are not synonyms.
- Physical contact/support must be measured; a named functional group alone does not prove support.
- Structured condition results were explored in Body Graph; External Object prototype currently uses string reasons. A shared reason schema is **not yet validated**.

## Persistence and safety boundary

[Runtime persistence boundaries](runtime-persistence-boundaries.md) clarify that SQLite is a PC reference implementation, not a Forma Unit or MCU requirement. Persistence must not block real-time safety actions, and historical snapshots cannot reauthorize execution after restart. Eleven runtime-invalidation test suites have user-confirmed PASS results; physical safety and cross-device atomicity remain unverified.

## Open design / validation work

- A common event boundary was demonstrated for Body Graph and World Interaction, but one consistent typed event/reason schema across graph, object use, Health, Twin, and Safety is **not yet validated**.
- Explicit transaction boundary, rollback, timeout, stale-lease detection and distributed arbitration.
- External-object partial scope, contact geometry, multiple manipulators and shared load constraints.
- Observation subscriptions and freshness for world relations; confidence and stale relation handling.
- Safe physical control transitions, STOP/Limp semantics and authority-loss recovery.
- Identity, persistence, Definition/Instance versioning and schema compatibility.
- Real hardware, timing, CAN/CAN-FD transport and fault injection.
- Formal specification and test cases only after conceptual boundary review.

## Completed next-prototype review: Runtime Invalidation Events

The [Runtime Invalidation Events](../../prototype/runtime-invalidation-events/VALIDATION.md) prototype completed five user-confirmed PASS suites (2026-10-09): event emission/deduplication, policy action lifecycle, synthetic STOP verification, observation evidence and advisory recovery policy. It validates separation of detection, event acknowledgment, action completion report, evidence assessment, recovery recommendation and explicit lease cleanup. It does **not** establish physical STOP, physical sensor integrity, durable event delivery, distributed arbitration or safe automatic recovery.

## Recommended next validation

Review **end-to-end action/verification correlation and failure handling** across event IDs, action IDs, evidence generation and execution lifecycle; then evaluate durable delivery/timeout and explicit safe reauthorization with injected faults. Keep physical actuation and formal safety guarantees out of scope until the required hardware and fault model are defined.
