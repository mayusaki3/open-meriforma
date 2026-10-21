# Runtime Invalidation Events — Worklog

Updated: 2026-10-19 (JST)
Repository: mayusaki3/open-meriforma
Branch: develop
Status: active technical validation; this Worklog is the authoritative work-state record.

## Current phase
- Completed: synthetic validation suites 1–60 and 62 (61 is a design-only review). User confirmed suite 44 and suite 43 regression PASS on 2026-10-17.
- Suites 45–46 confirmed: authority-gated SharedCanBus synthetic queue and mixed heartbeat/ACK/control priority.
- Suite 45 user-confirmed PASS on 2026-10-17: 4/4 checks; suites 44 and 43 regressions 4/4 each PASS.
- Do not equate synthetic suite PASS with hardware safety certification or comprehensive regression.

## Latest authoritative artifacts
- prototype/runtime-invalidation-events/authority_can_scheduler.py
- prototype/runtime-invalidation-events/test_authority_can_scheduler.py
- prototype/runtime-invalidation-events/authority_command_gate.py
- prototype/runtime-invalidation-events/test_authority_command_race.py
- prototype/runtime-invalidation-events/VALIDATION.md
- prototype/runtime-invalidation-events/README.md
- prototype/runtime-invalidation-events/ARCHITECTURE.md (provisional implementation overview)

## Verified results
- Suite 60: 5/5 PASS, with suites 59/58/57 regressions 13/13 PASS, reported by user on 2026-10-20. Coherent rollback of both untrusted stores remains undetectable.
- Suite 59: 3/3 PASS, with suites 58/57/56 regressions 15/15 PASS, reported by user on 2026-10-20. Subprocess crash boundaries only, not physical power-loss testing.
- Suite 58: 5/5 PASS, with suites 57/56/55 regressions 14/14 PASS, reported by user on 2026-10-20. Simulated monotonic witness detects rollback mismatch; no hardware trust demonstrated.
- Suite 57: 5/5 PASS, with suites 56/55/54 regressions 14/14 PASS, reported by user on 2026-10-19. Demonstrated coherent history rollback vulnerability; this PASS does not establish anti-rollback protection.
- Suite 56: 5/5 PASS, with suites 55/54/53 regressions 14/14 PASS, reported by user on 2026-10-19.
- Suite 55: 4/4 PASS after Windows SQLite connection-close fix, reported by user on 2026-10-19; suites 54/53/52 regressions 15/15 PASS in preceding run.
- Suite 54: 5/5 PASS, with suites 53/52/51 regressions 15/15 PASS, reported by user on 2026-10-19.
- Suite 53: 5/5 PASS, with suites 52/51/50 regressions 15/15 PASS, reported by user on 2026-10-18.
- Suite 52: 5/5 PASS, with suites 51/50/49 regressions 14/14 PASS, reported by user on 2026-10-18.
- Suite 51: 5/5 PASS, with suites 50/49/48 regressions 13/13 PASS, reported by user on 2026-10-18.
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
- Suite 51 synthetic receiver replay and partial timeout test user-confirmed PASS (5/5) on 2026-10-18, with suites 50/49/48 regressions PASS (13/13). Completed transfer IDs and expired partial IDs are retained per receiver instance, with no persistence, wraparound strategy, or real firmware protection claimed.
- Suite 52 bounded replay-history / ID-wrap / fresh-generation receiver test user-confirmed PASS (5/5) on 2026-10-18, with suites 51/50/49 regressions PASS (14/14). No eviction within generation; exhausted receiver denies new commands until a new generation and receiver instance. Default cap 65536 entries; bounded but memory budget and embedded implementation unverified.
- Receiver ID lifecycle review added at prototype/runtime-invalidation-events/RECEIVER_ID_LIFECYCLE.md (2026-10-18). Identified shared global 65536-key budget, per-source namespace, theoretical bitmap sizing, required explicit reauthorization and unverified epoch authenticity. Suite 53 implementation pending design gate.
- Suite 53 receiver_generation_registry.py and test_receiver_generation_registry.py user-confirmed PASS (5/5) on 2026-10-18, with suites 52/51/50 regressions PASS (15/15). Process-local generation registry prevents same-generation history reset, requires explicit authorization before fresh bind, and tests global capacity across two sources. Registry itself is volatile and does not authenticate or persist generations.
- Suite 54 SQLite-backed durable_receiver_generation_registry.py and test_durable_receiver_generation_registry.py user-confirmed PASS (5/5) on 2026-10-19, with suites 53/52/51 regressions PASS (15/15). Explicit initialization, committed generation insert before receiver activation, reopen reuse denial, missing/corrupt schema fail-closed. No physical power-loss durability or cryptographic epoch authenticity verified.
- Suite 55 test_durable_receiver_generation_crash.py user-confirmed PASS (4/4) after contextlib.closing fix on 2026-10-19. Windows WinError 32 during temporary-file cleanup resolved. Forced child exit tests cover before/after SQLite COMMIT and replay refusal after reopen; no physical power-loss or fsync durability claim.
- Suite 56 integrity checks in test_durable_receiver_generation_integrity.py user-confirmed PASS (5/5) on 2026-10-19, with suites 55/54/53 regressions PASS (14/14). Startup validation refuses empty or non-TEXT stored generation values; fixtures also cover truncated database, incompatible schema and valid existing history. SQLite quick_check and schema checks are not a cryptographic anti-rollback guarantee.
- Suite 57 coherent rollback reproduction (test_durable_receiver_generation_rollback.py, GENERATION_ROLLBACK_BOUNDARY.md) user-confirmed PASS (5/5) on 2026-10-19, with suites 56/55/54 regressions PASS (14/14). Restored coherent snapshot passes SQLite validation and permits old generation rebind. Independent witness is a test oracle only, not a production security mechanism.
- Suite 58 simulated independent monotonic witness and guard (monotonic_generation_guard.py, test_monotonic_generation_guard.py) user-confirmed PASS (5/5), with suites 57/56/55 regressions PASS (14/14). Witness advances before SQLite generation+anchor commit; a failed reservation strands the system closed. Fixture witness is assumed independent/non-rollbackable, not trusted hardware; no automatic recovery.
- Suite 59 subprocess crash-window fixture (monotonic_generation_crash_worker.py, test_monotonic_generation_crash.py, MONOTONIC_WITNESS_CRASH_BOUNDARY.md) user-confirmed PASS (3/3), with suites 58/57/56 regressions PASS (15/15). FileWitness is untrusted, process exit is not physical power loss; recovery remains fail-closed and manual policy unspecified.
- Suite 60 witness file validation, malformed/missing/mismatched witness checks, and coherent two-store rollback limitation (test_monotonic_witness_integrity.py, WITNESS_INTEGRITY_BOUNDARY.md) user-confirmed PASS (5/5), with suites 59/58/57 regressions PASS (13/13). Ordinary file witness is not trusted anti-rollback storage.
- Suite 61 requirements draft (TRUSTED_WITNESS_REQUIREMENTS.md) expanded with provisional per-Forma protected witness ownership and all-required-peers group authorization (MULTI_FORMA_WITNESS_DESIGN.md). Hardware feasibility, authentication, group-commit protocol, and service recovery require review; **not** an implemented/tested 61st suite. Suites 1–60 remain the last user-confirmed validation count.
- Suite 62 synthetic multi-Forma group reservation prototype user-confirmed PASS (5/5), with suites 60/59/58 regressions PASS (13/13) on Windows 2026-10-21. This is not authenticated distributed group commit or physical motor inhibition.
- Suite 63 subprocess coordinator crash windows added (multi_forma_crash_worker.py, test_multi_forma_crash_recovery.py, MULTI_FORMA_CRASH_BOUNDARY.md): crash after first and after both local reservations; restart has no group authority. Windows validation pending. **Does not test peer-local group-commit enforcement.**
- Review prototype boundaries and create HLDocS-compliant spec/testspec and traceability documents after checking the complete template/prompt and document-type prerequisites; this Worklog is an operational state record, not a declaration of document compliance.
- Align outdated introductory status text in VALIDATION.md after the documentation consolidation.
- Real hardware integration, authenticated peers, physical STOP, timing, watchdog, CAN bus-off and actuator inhibition remain unverified.

## Next action
1. Read this Worklog and the latest code/VALIDATION.md from develop.
2. Preserve suite 47 PASS and the regression evidence.
3. Run suite 63 coordinator crash tests plus suites 62/60/59 regressions on Windows. Then design independent peer-local group-commit enforcement and authenticated proof model.
4. Continue HLDocS spec/testspec preparation after checking templates/prompts; keep synthetic and hardware validation separate.
