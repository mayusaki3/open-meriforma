# Runtime Invalidation Events — Worklog

Updated: 2026-10-18 (JST)
Repository: mayusaki3/open-meriforma
Branch: develop
Status: active technical validation; this Worklog is the authoritative work-state record.

## Current phase
- Completed: synthetic validation suites 1–50. User confirmed suite 44 and suite 43 regression PASS on 2026-10-17.
- Suites 45–46 confirmed: authority-gated SharedCanBus synthetic queue and mixed heartbeat/ACK/control priority.
- Suite 45 user-confirmed PASS on 2026-10-17: 4/4 checks; suites 44 and 43 regressions 4/4 each PASS.
- Do not equate 50/50 suite PASS with hardware safety certification or comprehensive regression.

## Latest authoritative artifacts
- prototype/runtime-invalidation-events/authority_can_scheduler.py
- prototype/runtime-invalidation-events/test_authority_can_scheduler.py
- prototype/runtime-invalidation-events/authority_command_gate.py
- prototype/runtime-invalidation-events/test_authority_command_race.py
- prototype/runtime-invalidation-events/VALIDATION.md
- prototype/runtime-invalidation-events/README.md
- prototype/runtime-invalidation-events/ARCHITECTURE.md (provisional implementation overview)

## Verified results
- Suite 50: 5/5 PASS, with suites 49/48/47 regressions 12/12 PASS, reported by user on 2026-10-18.
- Suite 49: 4/4 PASS, with suites 48/47/46 regressions 12/12 PASS, reported by user on 2026-10-18.
- Suite 48: 4/4 PASS, with suites 47 and 46 regression 8/8 PASS, reported by user on 2026-10-18.
- Suite 47: 4/4 PASS, with suites 46/45/44/43 regression 16/16 PASS, reported by user on 2026-10-18.
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
- Suite 47 deterministic boundary-injection test user-confirmed PASS (4/4) on 2026-10-18, with four preceding suites PASS (16/16). Injection occurs between protocol dispatch and control eligibility check, not at actual hardware transmit.
- Suite 48 per-control-frame synthetic revocation test user-confirmed PASS (4/4) on 2026-10-18, with suites 47 and 46 regression PASS (8/8). Earlier injection clock regression corrected to 0.06. An already dispatched frame is not retractable; no physical CAN atomicity is claimed.
- Suite 49 test_authority_shared_bus_partial_command.py user-confirmed PASS (4/4) on 2026-10-18, with suites 48/47/46 regressions PASS (12/12). A test-only Reassembler represents the receiver, not actual Forma firmware. It checks complete 110-byte payload versus interrupted two-fragment transfer and partial-buffer discard.
- Suite 50 FormaCommandReceiver test-only model user-confirmed PASS (5/5) on 2026-10-18, with suites 49/48/47 regressions PASS (12/12). It gates each fragment and completed command on generation, deadline, and current link authority; acceptance is abstract and never motor execution.
- Suite 51 synthetic receiver replay and partial timeout test added; pending local validation. Completed transfer IDs and expired partial IDs are retained per receiver instance, with no persistence, wraparound strategy, or real firmware protection claimed.
- Review prototype boundaries and create HLDocS-compliant spec/testspec and traceability documents after checking the complete template/prompt and document-type prerequisites; this Worklog is an operational state record, not a declaration of document compliance.
- Align outdated introductory status text in VALIDATION.md after the documentation consolidation.
- Real hardware integration, authenticated peers, physical STOP, timing, watchdog, CAN bus-off and actuator inhibition remain unverified.

## Next action
1. Read this Worklog and the latest code/VALIDATION.md from develop.
2. Preserve suite 47 PASS and the regression evidence.
3. Run suite 51 test_forma_command_receiver_replay.py and regressions suite 50/49; report results.
4. Continue HLDocS spec/testspec preparation after checking templates/prompts; keep synthetic and hardware validation separate.
