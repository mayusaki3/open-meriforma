# Suite 59 — Cross-store crash boundaries (synthetic)

The witness and SQLite database are separate persistence domains. No atomic transaction spans both. This suite injects abrupt subprocess exits at three explicit boundaries.

| Exit point | Witness | SQLite anchor/history | Expected restart |
| --- | --- | --- | --- |
| Before witness advance | 0 | 0 / empty | Allowed |
| After witness advance, before SQLite transaction | 1 | 0 / empty | Refused: witness ahead |
| After SQLite COMMIT | 1 | 1 / M1:C1 | Allowed |

The test's FileWitness persists its value to a plain text file using os.replace so a subprocess restart can observe it. It is **not** an independently trusted monotonic counter. The process exit is **not** a power interruption and does not prove storage flush ordering, atomicity across devices, filesystem crash consistency, or protection against rollback/tampering.

## Fail-closed recovery boundary

If the witness is ahead of SQLite, refuse startup and generation binding. Do not automatically decrement the witness, overwrite the anchor, replay an assumed lost generation, or reinitialize the history. Recovery needs a separately specified and authenticated reprovisioning procedure that cannot reauthorize stale generations. That procedure is not implemented.

This test does not cover every instruction boundary within SQLite COMMIT or witness storage update. A real design must account for witness failure modes, flash endurance, brownout behavior, authenticated identity and operational recovery.
