# Runtime Invalidation Events — Worklog

Updated: 2026-10-18 (JST)
Repository: mayusaki3/open-meriforma
Branch: develop
Status: active technical validation; this Worklog is the authoritative work-state record.

## Current phase
- Completed: synthetic validation suites 1–46. User confirmed suite 44 and suite 43 regression PASS on 2026-10-17.
- Suite 45 confirmed: authority-gated control frames on the SharedCanBus synthetic queue, with pre-dispatch cancellation and bus-off generation fencing. Mixed heartbeat/ACK/control priority remains untested.
- Suite 45 user-confirmed PASS on 2026-10-17: 4/4 checks; suites 44 and 43 regressions 4/4 each PASS.
- Do not equate 46/46 suite PASS with hardware safety certification or comprehensive regression.

## Latest authoritative artifacts
- prototype/runtime-invalidation-events/authority_can_scheduler.py
- prototype/runtime-invalidation-events/test_authority_can_scheduler.py
- prototype/runtime-invalidation-events/authority_command_gate.py
- prototype/runtime-invalidation-events/test_authority_command_race.py
- prototype/runtime-invalidation-events/VALIDATION.md
- prototype/runtime-invalidation-events/README.md
- prototype/runtime-invalidation-events/ARCHITECTURE.md (provisional implementation overview)

## Verified results
- Suite 46: 4/4 PASS; suites 45/44/43 regression 12/12 PASS, reported by user on 2026-10-18.
- Suite 45: 4/4 PASS, with suites 44 and 43 regressions (8/8 PASS), reported by user on 2026-10-17.
- Suite 44: 4/4 checks PASS, plus suite 43 regression 4/4 PASS, reported by user.
- Suite 43: 4/4 checks PASS; suite 42 regression 4/4 PASS, reported by user.
- Suites 1–42: previously user-confirmed PASS in this validation campaign; see VALIDATION.md for detailed evidence and limitations.
- All tests synthetic Python. No real CAN controller, real-time timing, motor output or physical STOP verified.

## Decisions
- Required Forma peers are jointly gated; missing/unready/stale peer denies group authority.
- Reauthorization is explicit, not automatic on recovery.
- Invalidation discards queued synthetic control commands; old generation must not replay.
- Existing suite 44 adapter is a separate scheduler, not SharedCanBus control-path integration.
- HLDocS stable reference is v0.6.1 (HLDocS main); v0.7.0 develop is under reconstruction.
- Maintain Worklog as the source of truth for work continuity, rather than chat memory.

## Pending
- Suite 46 mixed heartbeat/ACK/control priority and cancellation: user-confirmed 4/4 PASS on 2026-10-18; suites 45, 44 and 43 regressions also 4/4 each PASS (16/16 total). Earlier clock regression resolved by processing queued protocol frames before advancing authority time; no hardware timing guarantees. Suites 45 and 44 regressions passed.
- Review prototype boundaries and create HLDocS-compliant spec/testspec and traceability documents after checking the complete template/prompt and document-type prerequisites; this Worklog is an operational state record, not a declaration of document compliance.
- Align outdated introductory status text in VALIDATION.md after the documentation consolidation.
- Real hardware integration, authenticated peers, physical STOP, timing, watchdog, CAN bus-off and actuator inhibition remain unverified.

## Next action
1. Read this Worklog and the latest code/VALIDATION.md from develop.
2. Confirm suite 44 user PASS and update validation documentation at the next appropriate checkpoint.
3. Design next validation for revocation between shared-bus protocol dispatch and control transmit boundary; test fail-closed semantics and preserve regressions.
4. Continue HLDocS spec/testspec preparation after checking templates/prompts; keep synthetic and hardware validation separate.
